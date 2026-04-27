"""
Sprint 729a — Engagement-completion gate integration with the ISA 450 SUM rules.

Pins:
  - Engagement with no misstatements: gate passes.
  - Engagement with NOT_YET_REVIEWED items: gate blocks.
  - Engagement with all-dispositioned non-MATERIAL items: gate passes.
  - Engagement with MATERIAL aggregate but no notes: gate blocks (override required).
  - Engagement with MATERIAL aggregate + a documented override: gate passes.
  - Archived items don't count.
  - Gate ordering: follow-up gate → ISA 520 gate → ISA 450 gate.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engagement_manager import EngagementManager
from engagement_model import EngagementStatus
from uncorrected_misstatements_manager import UncorrectedMisstatementsManager
from uncorrected_misstatements_model import (
    MisstatementClassification,
    MisstatementDisposition,
    MisstatementSourceType,
)


def _setup(db_session, make_user, make_client, materiality=100000.0):
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


_MINOR = {
    "source_type": MisstatementSourceType.KNOWN_ERROR,
    "source_reference": "Cutoff",
    "description": "Minor cutoff difference",
    "accounts_affected": [{"account": "Revenue", "debit_credit": "CR", "amount": 1000}],
    "classification": MisstatementClassification.FACTUAL,
    "fs_impact_net_income": Decimal("-1000.00"),
    "fs_impact_net_assets": Decimal("-1000.00"),
}

_MATERIAL = {
    "source_type": MisstatementSourceType.KNOWN_ERROR,
    "source_reference": "Major",
    "description": "Aggregate exceeds materiality",
    "accounts_affected": [{"account": "Cash", "debit_credit": "DR", "amount": 200000}],
    "classification": MisstatementClassification.FACTUAL,
    "fs_impact_net_income": Decimal("-200000.00"),
    "fs_impact_net_assets": Decimal("-200000.00"),
}


class TestSumGate:
    def test_completion_passes_with_no_misstatements(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
        result = EngagementManager(db_session).complete_engagement(user.id, eng.id)
        assert result.status == EngagementStatus.COMPLETED

    def test_blocks_when_disposition_pending(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
        UncorrectedMisstatementsManager(db_session).create_misstatement(user_id=user.id, engagement_id=eng.id, **_MINOR)
        with pytest.raises(ValueError, match="ISA 450"):
            EngagementManager(db_session).complete_engagement(user.id, eng.id)

    def test_passes_when_minor_items_dispositioned(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        m = mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_MINOR)
        mgr.update_misstatement(
            user_id=user.id,
            misstatement_id=m.id,
            cpa_disposition=MisstatementDisposition.AUDITOR_ACCEPTS_AS_IMMATERIAL,
        )
        result = EngagementManager(db_session).complete_engagement(user.id, eng.id)
        assert result.status == EngagementStatus.COMPLETED

    def test_blocks_when_material_aggregate_no_override(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client, materiality=100000.0)
        mgr = UncorrectedMisstatementsManager(db_session)
        m = mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_MATERIAL)
        # disposition set, but no notes override
        mgr.update_misstatement(
            user_id=user.id,
            misstatement_id=m.id,
            cpa_disposition=MisstatementDisposition.AUDITOR_ACCEPTS_AS_IMMATERIAL,
        )
        with pytest.raises(ValueError, match="MATERIAL"):
            EngagementManager(db_session).complete_engagement(user.id, eng.id)

    def test_passes_with_material_aggregate_and_documented_override(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client, materiality=100000.0)
        mgr = UncorrectedMisstatementsManager(db_session)
        m = mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_MATERIAL)
        mgr.update_misstatement(
            user_id=user.id,
            misstatement_id=m.id,
            cpa_disposition=MisstatementDisposition.AUDITOR_ACCEPTS_AS_IMMATERIAL,
            cpa_notes="TCWG informed per ISA 450 §11; corrections deferred to next period.",
        )
        result = EngagementManager(db_session).complete_engagement(user.id, eng.id)
        assert result.status == EngagementStatus.COMPLETED

    def test_archived_misstatement_excluded(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)
        m = mgr.create_misstatement(user_id=user.id, engagement_id=eng.id, **_MINOR)
        mgr.archive_misstatement(user.id, m.id, reason="duplicate")
        result = EngagementManager(db_session).complete_engagement(user.id, eng.id)
        assert result.status == EngagementStatus.COMPLETED

    def test_isa_520_gate_runs_before_isa_450_gate(self, db_session, make_user, make_client):
        from analytical_expectations_manager import AnalyticalExpectationsManager
        from analytical_expectations_model import ExpectationTargetType

        user, eng = _setup(db_session, make_user, make_client)
        # Create unevaluated expectation (520) AND unreviewed misstatement (450)
        AnalyticalExpectationsManager(db_session).create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )
        UncorrectedMisstatementsManager(db_session).create_misstatement(user_id=user.id, engagement_id=eng.id, **_MINOR)

        # 520 gate fires first because it appears earlier in update_engagement
        with pytest.raises(ValueError, match="ISA 520"):
            EngagementManager(db_session).complete_engagement(user.id, eng.id)
