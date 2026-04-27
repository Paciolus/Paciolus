"""
Sprint 729a — UncorrectedMisstatementsManager: CRUD, validation,
bucket logic, aggregation, completion-gate helpers.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engagement_manager import EngagementManager
from uncorrected_misstatements_manager import (
    UncorrectedMisstatementsManager,
    compute_materiality_bucket,
)
from uncorrected_misstatements_model import (
    MaterialityBucket,
    MisstatementClassification,
    MisstatementDisposition,
    MisstatementSourceType,
)

# =============================================================================
# Bucket logic — pure function
# =============================================================================


class TestComputeMaterialityBucket:
    """Test boundary conditions explicitly per the docstring contract."""

    overall = Decimal("100000")
    performance = Decimal("75000")
    trivial = Decimal("5000")

    @pytest.mark.parametrize(
        "value,expected",
        [
            (Decimal("0"), MaterialityBucket.CLEARLY_TRIVIAL),
            (Decimal("4999"), MaterialityBucket.CLEARLY_TRIVIAL),
            (Decimal("5000"), MaterialityBucket.CLEARLY_TRIVIAL),  # equal-to is trivial
            (Decimal("5001"), MaterialityBucket.IMMATERIAL),
            (Decimal("75000"), MaterialityBucket.IMMATERIAL),  # equal-to is immaterial
            (Decimal("75001"), MaterialityBucket.APPROACHING_MATERIAL),
            (Decimal("100000"), MaterialityBucket.APPROACHING_MATERIAL),  # equal-to overall
            (Decimal("100001"), MaterialityBucket.MATERIAL),
            (Decimal("500000"), MaterialityBucket.MATERIAL),
        ],
    )
    def test_positive_aggregate(self, value, expected):
        assert compute_materiality_bucket(value, self.overall, self.performance, self.trivial) == expected

    @pytest.mark.parametrize(
        "value",
        [Decimal("-100001"), Decimal("-500000")],
    )
    def test_negative_aggregate_uses_absolute(self, value):
        # Negative aggregates use |value| for the bucket comparison
        assert (
            compute_materiality_bucket(value, self.overall, self.performance, self.trivial)
            == MaterialityBucket.MATERIAL
        )

    def test_zero_is_clearly_trivial(self):
        assert (
            compute_materiality_bucket(Decimal("0"), self.overall, self.performance, self.trivial)
            == MaterialityBucket.CLEARLY_TRIVIAL
        )


# =============================================================================
# Manager — Create, Read, List, Update, Archive
# =============================================================================


def _make_engagement(db_session, make_user, make_client, materiality=100000.0):
    user = make_user()
    client = make_client(user=user)
    eng = EngagementManager(db_session).create_engagement(
        user.id,
        client.id,
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 12, 31, tzinfo=UTC),
        materiality_amount=materiality,
    )
    return user, eng


_FACTUAL_PAYLOAD = {
    "source_type": MisstatementSourceType.KNOWN_ERROR,
    "source_reference": "Revenue cutoff at YE",
    "description": "Dec 31 revenue posted to January",
    "accounts_affected": [{"account": "Revenue", "debit_credit": "CR", "amount": 10000}],
    "classification": MisstatementClassification.FACTUAL,
    "fs_impact_net_income": -10000.0,
    "fs_impact_net_assets": -10000.0,
}


class TestCreate:
    def test_create_minimal(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        m = mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_FACTUAL_PAYLOAD)
        assert m.id is not None
        assert m.classification == MisstatementClassification.FACTUAL
        assert m.fs_impact_net_income == Decimal("-10000.00")
        assert m.cpa_disposition == MisstatementDisposition.NOT_YET_REVIEWED

    def test_create_rejects_empty_accounts(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        bad = {**_FACTUAL_PAYLOAD, "accounts_affected": []}
        with pytest.raises(ValueError, match="at least one account row"):
            mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **bad)

    def test_create_rejects_negative_amount(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        bad = {
            **_FACTUAL_PAYLOAD,
            "accounts_affected": [{"account": "A", "debit_credit": "DR", "amount": -100}],
        }
        with pytest.raises(ValueError, match="amount must be positive"):
            mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **bad)

    def test_create_rejects_bad_debit_credit(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        bad = {
            **_FACTUAL_PAYLOAD,
            "accounts_affected": [{"account": "A", "debit_credit": "MAYBE", "amount": 100}],
        }
        with pytest.raises(ValueError, match="debit_credit must be 'DR' or 'CR'"):
            mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **bad)

    def test_create_rejects_other_users_engagement(self, db_session, make_user, make_client):
        user_a, eng = _make_engagement(db_session, make_user, make_client)
        user_b = make_user(email="other-sum@example.com")
        mgr = UncorrectedMisstatementsManager(db_session)
        with pytest.raises(ValueError, match="access denied"):
            mgr.create_misstatement(user_id=user_b.id, engagement_id=eng.id, **_FACTUAL_PAYLOAD)


class TestListAndFilter:
    def _seed(self, db_session, mgr, user, eng):
        mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_FACTUAL_PAYLOAD)
        mgr.create_misstatement(
            user_id=user.id,
            engagement_id=eng.id,
            source_type=MisstatementSourceType.SAMPLE_PROJECTION,
            source_reference="Inventory test sample, n=100",
            description="Projected error from inventory pricing test",
            accounts_affected=[{"account": "Inventory", "debit_credit": "DR", "amount": 5000}],
            classification=MisstatementClassification.PROJECTED,
            fs_impact_net_income=Decimal("-5000.00"),
            fs_impact_net_assets=Decimal("5000.00"),
        )

    def test_list_filters_by_classification(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        self._seed(db_session, mgr, user, eng)

        items, total = mgr.list_misstatements(
            user_id=user.id,
            engagement_id=eng.id,
            classification=MisstatementClassification.PROJECTED,
        )
        assert total == 1
        assert items[0].classification == MisstatementClassification.PROJECTED

    def test_list_filters_by_source_type(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        self._seed(db_session, mgr, user, eng)

        items, total = mgr.list_misstatements(
            user_id=user.id,
            engagement_id=eng.id,
            source_type=MisstatementSourceType.KNOWN_ERROR,
        )
        assert total == 1
        assert items[0].source_type == MisstatementSourceType.KNOWN_ERROR


class TestUpdate:
    def test_update_disposition(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        m = mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_FACTUAL_PAYLOAD)
        updated = mgr.update_misstatement(
            user_id=user.id,
            misstatement_id=m.id,
            cpa_disposition=MisstatementDisposition.AUDITOR_ACCEPTS_AS_IMMATERIAL,
            cpa_notes="Below performance materiality.",
        )
        assert updated.cpa_disposition == MisstatementDisposition.AUDITOR_ACCEPTS_AS_IMMATERIAL
        assert updated.cpa_notes == "Below performance materiality."

    def test_update_other_users_returns_none(self, db_session, make_user, make_client):
        user_a, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        m = mgr.create_misstatement(user_id=user_a.id, engagement_id=eng.id, **_FACTUAL_PAYLOAD)
        user_b = make_user(email="hacker-sum@example.com")
        result = mgr.update_misstatement(
            user_id=user_b.id,
            misstatement_id=m.id,
            cpa_disposition=MisstatementDisposition.AUDITOR_ACCEPTS_AS_IMMATERIAL,
        )
        assert result is None


class TestArchive:
    def test_archive_excludes_from_list(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        m1 = mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_FACTUAL_PAYLOAD)
        m2 = mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_FACTUAL_PAYLOAD)
        mgr.archive_misstatement(user.id, m2.id, reason="duplicate")

        items, total = mgr.list_misstatements(user_id=user.id, engagement_id=eng.id)
        assert total == 1
        assert items[0].id == m1.id


# =============================================================================
# SUM aggregation
# =============================================================================


class TestSumSchedule:
    def test_empty_schedule_returns_zero_aggregate(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        sched = mgr.compute_sum_schedule(user.id, eng.id)
        assert sched["aggregate"]["net_income"] == Decimal("0.00")
        assert sched["aggregate"]["net_assets"] == Decimal("0.00")
        assert sched["bucket"] == MaterialityBucket.CLEARLY_TRIVIAL.value
        assert sched["unreviewed_count"] == 0

    def test_factual_judgmental_grouped_separately_from_projected(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        # Factual: -10000 income, -10000 assets
        mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_FACTUAL_PAYLOAD)
        # Judgmental: -3000 income, 0 assets
        mgr.create_misstatement(
            user_id=user.id,
            engagement_id=eng.id,
            source_type=MisstatementSourceType.KNOWN_ERROR,
            source_reference="Bad debt allowance estimate",
            description="Management's estimate appears optimistic",
            accounts_affected=[{"account": "Bad Debt Expense", "debit_credit": "DR", "amount": 3000}],
            classification=MisstatementClassification.JUDGMENTAL,
            fs_impact_net_income=Decimal("-3000.00"),
            fs_impact_net_assets=Decimal("0.00"),
        )
        # Projected: -5000 income, 5000 assets
        mgr.create_misstatement(
            user_id=user.id,
            engagement_id=eng.id,
            source_type=MisstatementSourceType.SAMPLE_PROJECTION,
            source_reference="Inventory test, UEL",
            description="Projected pricing error",
            accounts_affected=[{"account": "Inventory", "debit_credit": "DR", "amount": 5000}],
            classification=MisstatementClassification.PROJECTED,
            fs_impact_net_income=Decimal("-5000.00"),
            fs_impact_net_assets=Decimal("5000.00"),
        )

        sched = mgr.compute_sum_schedule(user.id, eng.id)
        sub = sched["subtotals"]
        agg = sched["aggregate"]
        assert sub["factual_judgmental_net_income"] == Decimal("-13000.00")
        assert sub["factual_judgmental_net_assets"] == Decimal("-10000.00")
        assert sub["projected_net_income"] == Decimal("-5000.00")
        assert sub["projected_net_assets"] == Decimal("5000.00")
        assert agg["net_income"] == Decimal("-18000.00")
        assert agg["net_assets"] == Decimal("-5000.00")
        # Driver = max(|net_income|, |net_assets|) = 18000
        assert agg["driver"] == Decimal("18000.00")

    def test_bucket_uses_worst_case_driver(self, db_session, make_user, make_client):
        # materiality=100000 (overall), 75000 (PM), 5000 (trivial).
        # Build a row whose net_assets dwarfs net_income to confirm driver = max.
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        mgr.create_misstatement(
            user_id=user.id,
            engagement_id=eng.id,
            source_type=MisstatementSourceType.KNOWN_ERROR,
            source_reference="Reclass entry",
            description="Asset misclassification",
            accounts_affected=[{"account": "Equipment", "debit_credit": "DR", "amount": 90000}],
            classification=MisstatementClassification.FACTUAL,
            fs_impact_net_income=Decimal("100.00"),
            fs_impact_net_assets=Decimal("90000.00"),
        )
        sched = mgr.compute_sum_schedule(user.id, eng.id)
        # 90000 > performance (75000), <= overall (100000) → APPROACHING_MATERIAL
        assert sched["bucket"] == MaterialityBucket.APPROACHING_MATERIAL.value


# =============================================================================
# Completion-gate helpers
# =============================================================================


class TestGateHelpers:
    def test_count_unreviewed(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        m = mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_FACTUAL_PAYLOAD)
        assert mgr.count_unreviewed(eng.id) == 1
        mgr.update_misstatement(
            user_id=user.id,
            misstatement_id=m.id,
            cpa_disposition=MisstatementDisposition.AUDITOR_ACCEPTS_AS_IMMATERIAL,
        )
        assert mgr.count_unreviewed(eng.id) == 0

    def test_has_material_aggregate_true_when_exceeds_overall(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client, materiality=100000.0)
        mgr = UncorrectedMisstatementsManager(db_session)
        mgr.create_misstatement(
            user_id=user.id,
            engagement_id=eng.id,
            source_type=MisstatementSourceType.KNOWN_ERROR,
            source_reference="x",
            description="big",
            accounts_affected=[{"account": "Cash", "debit_credit": "DR", "amount": 200000}],
            classification=MisstatementClassification.FACTUAL,
            fs_impact_net_income=Decimal("-200000.00"),
            fs_impact_net_assets=Decimal("-200000.00"),
        )
        assert mgr.has_material_aggregate(eng.id, user.id) is True

    def test_has_material_aggregate_false_when_below(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client, materiality=100000.0)
        mgr = UncorrectedMisstatementsManager(db_session)
        mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_FACTUAL_PAYLOAD)
        # _FACTUAL_PAYLOAD is -10000 (well below 100000)
        assert mgr.has_material_aggregate(eng.id, user.id) is False

    def test_has_documented_override(self, db_session, make_user, make_client):
        user, eng = _make_engagement(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        m = mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_FACTUAL_PAYLOAD)
        assert mgr.has_documented_override(eng.id) is False
        mgr.update_misstatement(
            user_id=user.id,
            misstatement_id=m.id,
            cpa_notes="Acceptable per ISA 450 §A15 — TCWG informed.",
        )
        assert mgr.has_documented_override(eng.id) is True
