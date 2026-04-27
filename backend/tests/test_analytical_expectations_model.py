"""
Sprint 728a — AnalyticalExpectation model schema, defaults, soft-delete, to_dict.

Mirrors the shape of test_follow_up_items.py::TestFollowUpItemSchema.
"""

import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import inspect as sa_inspect

sys.path.insert(0, str(Path(__file__).parent.parent))

from analytical_expectations_model import (
    VALID_CORROBORATION_TAGS,
    AnalyticalExpectation,
    ExpectationCorroborationTag,
    ExpectationResultStatus,
    ExpectationTargetType,
)


class TestEnumValues:
    def test_target_type_values(self):
        assert ExpectationTargetType.ACCOUNT.value == "account"
        assert ExpectationTargetType.BALANCE.value == "balance"
        assert ExpectationTargetType.RATIO.value == "ratio"
        assert ExpectationTargetType.FLUX_LINE.value == "flux_line"

    def test_result_status_values(self):
        assert ExpectationResultStatus.NOT_EVALUATED.value == "not_evaluated"
        assert ExpectationResultStatus.WITHIN_THRESHOLD.value == "within_threshold"
        assert ExpectationResultStatus.EXCEEDS_THRESHOLD.value == "exceeds_threshold"

    def test_corroboration_tag_values(self):
        assert ExpectationCorroborationTag.INDUSTRY_DATA.value == "industry_data"
        assert ExpectationCorroborationTag.PRIOR_PERIOD.value == "prior_period"
        assert ExpectationCorroborationTag.BUDGET.value == "budget"
        assert ExpectationCorroborationTag.REGRESSION_MODEL.value == "regression_model"
        assert ExpectationCorroborationTag.OTHER.value == "other"

    def test_valid_tag_set_matches_enum(self):
        assert VALID_CORROBORATION_TAGS == {t.value for t in ExpectationCorroborationTag}


class TestSchema:
    def test_table_has_expected_columns(self, db_engine):
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("analytical_expectations")}
        expected = {
            "id",
            "engagement_id",
            "procedure_target_type",
            "procedure_target_label",
            "expected_value",
            "expected_range_low",
            "expected_range_high",
            "precision_threshold_amount",
            "precision_threshold_percent",
            "corroboration_basis_text",
            "corroboration_tags_json",
            "cpa_notes",
            "result_actual_value",
            "result_variance_amount",
            "result_status",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
            "archived_at",
            "archived_by",
            "archive_reason",
        }
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_no_prohibited_transactional_columns(self, db_engine):
        """Zero-storage guardrail: no raw transactional columns."""
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("analytical_expectations")}
        prohibited = {
            "account_number",
            "transaction_id",
            "vendor_name",
            "employee_name",
            "debit",
            "credit",
        }
        assert columns.isdisjoint(prohibited), f"Prohibited transactional columns found: {columns & prohibited}"


class TestDefaultsAndDict:
    def _make_minimal(self, db_session, make_engagement):
        engagement = make_engagement()
        exp = AnalyticalExpectation(
            engagement_id=engagement.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=Decimal("1000.00"),
            precision_threshold_amount=Decimal("50.00"),
            corroboration_basis_text="Prior-period comparison",
            corroboration_tags_json='["prior_period"]',
            created_by=engagement.created_by,
        )
        db_session.add(exp)
        db_session.flush()
        return exp

    def test_default_status_is_not_evaluated(self, db_session, make_engagement):
        exp = self._make_minimal(db_session, make_engagement)
        assert exp.result_status == ExpectationResultStatus.NOT_EVALUATED

    def test_to_dict_round_trip(self, db_session, make_engagement):
        exp = self._make_minimal(db_session, make_engagement)
        d = exp.to_dict()
        assert d["engagement_id"] == exp.engagement_id
        assert d["procedure_target_type"] == "account"
        assert d["procedure_target_label"] == "Revenue"
        assert d["expected_value"] == "1000.00"
        assert d["precision_threshold_amount"] == "50.00"
        assert d["corroboration_tags"] == ["prior_period"]
        assert d["result_status"] == "not_evaluated"
        assert d["archived_at"] is None
        assert d["created_at"] is not None

    def test_to_dict_handles_malformed_tags_json(self, db_session, make_engagement):
        exp = self._make_minimal(db_session, make_engagement)
        exp.corroboration_tags_json = "{malformed"
        db_session.flush()
        d = exp.to_dict()
        # to_dict must not raise on a corrupt JSON column — it returns []
        assert d["corroboration_tags"] == []

    def test_repr_includes_id_and_status(self, db_session, make_engagement):
        exp = self._make_minimal(db_session, make_engagement)
        r = repr(exp)
        assert "AnalyticalExpectation" in r
        assert str(exp.id) in r
        assert "not_evaluated" in r


class TestSoftDeleteMixin:
    def test_archive_sets_archived_at(self, db_session, make_engagement, make_user):
        engagement = make_engagement()
        archiver = make_user(email="archiver@example.com")

        exp = AnalyticalExpectation(
            engagement_id=engagement.id,
            procedure_target_type=ExpectationTargetType.RATIO,
            procedure_target_label="Current ratio",
            expected_value=Decimal("2.00"),
            precision_threshold_percent=10.0,
            corroboration_basis_text="Industry median",
            corroboration_tags_json='["industry_data"]',
            created_by=engagement.created_by,
        )
        db_session.add(exp)
        db_session.flush()

        from shared.soft_delete import soft_delete

        soft_delete(db_session, exp, user_id=archiver.id, reason="superseded")

        assert exp.archived_at is not None
        assert exp.archived_by == archiver.id
        assert exp.archive_reason == "superseded"


class TestCascadeBehavior:
    def test_engagement_relationship_back_populates(self, db_session, make_engagement):
        engagement = make_engagement()
        exp = AnalyticalExpectation(
            engagement_id=engagement.id,
            procedure_target_type=ExpectationTargetType.BALANCE,
            procedure_target_label="Cash and equivalents",
            expected_range_low=Decimal("100000.00"),
            expected_range_high=Decimal("125000.00"),
            precision_threshold_amount=Decimal("5000.00"),
            corroboration_basis_text="Budget review",
            corroboration_tags_json='["budget"]',
            created_by=engagement.created_by,
        )
        db_session.add(exp)
        db_session.flush()
        db_session.refresh(engagement)

        assert exp in engagement.analytical_expectations
        assert exp.engagement.id == engagement.id
