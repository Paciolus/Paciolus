"""
Sprint 728a — AnalyticalExpectationsManager: CRUD, validation, evaluate_status.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from analytical_expectations_manager import (
    AnalyticalExpectationsManager,
    evaluate_status,
)
from analytical_expectations_model import (
    ExpectationResultStatus,
    ExpectationTargetType,
)
from engagement_manager import EngagementManager

# =============================================================================
# evaluate_status (pure function — no DB)
# =============================================================================


class TestEvaluateStatus:
    def test_within_amount_threshold(self):
        v, s = evaluate_status(actual_value=105, expected_value=100, precision_threshold_amount=10)
        assert s == ExpectationResultStatus.WITHIN_THRESHOLD
        assert v == Decimal("5.00")

    def test_exceeds_amount_threshold(self):
        v, s = evaluate_status(actual_value=120, expected_value=100, precision_threshold_amount=10)
        assert s == ExpectationResultStatus.EXCEEDS_THRESHOLD
        assert v == Decimal("20.00")

    def test_signed_negative_variance_within(self):
        v, s = evaluate_status(actual_value=95, expected_value=100, precision_threshold_amount=10)
        assert s == ExpectationResultStatus.WITHIN_THRESHOLD
        assert v == Decimal("-5.00")

    def test_signed_negative_variance_exceeds(self):
        v, s = evaluate_status(actual_value=80, expected_value=100, precision_threshold_amount=10)
        assert s == ExpectationResultStatus.EXCEEDS_THRESHOLD
        assert v == Decimal("-20.00")

    def test_within_percent_threshold(self):
        # 5% of 100 = 5; actual=104 → variance=4, within
        v, s = evaluate_status(actual_value=104, expected_value=100, precision_threshold_percent=5)
        assert s == ExpectationResultStatus.WITHIN_THRESHOLD

    def test_exceeds_percent_threshold(self):
        # 5% of 100 = 5; actual=110 → variance=10, exceeds
        v, s = evaluate_status(actual_value=110, expected_value=100, precision_threshold_percent=5)
        assert s == ExpectationResultStatus.EXCEEDS_THRESHOLD

    def test_in_range_no_variance(self):
        v, s = evaluate_status(
            actual_value=105,
            expected_range_low=100,
            expected_range_high=110,
            precision_threshold_amount=10,
        )
        assert s == ExpectationResultStatus.WITHIN_THRESHOLD
        assert v == Decimal("0.00")

    def test_below_range_signed(self):
        v, s = evaluate_status(
            actual_value=95,
            expected_range_low=100,
            expected_range_high=110,
            precision_threshold_amount=10,
        )
        assert v == Decimal("-5.00")
        assert s == ExpectationResultStatus.WITHIN_THRESHOLD

    def test_above_range_exceeds(self):
        v, s = evaluate_status(
            actual_value=130,
            expected_range_low=100,
            expected_range_high=110,
            precision_threshold_amount=10,
        )
        assert v == Decimal("20.00")
        assert s == ExpectationResultStatus.EXCEEDS_THRESHOLD

    def test_percent_against_zero_expected_raises(self):
        with pytest.raises(ValueError, match="zero reference"):
            evaluate_status(actual_value=5, expected_value=0, precision_threshold_percent=10)


# =============================================================================
# Manager — Create, Read, List, Update, Archive
# =============================================================================


def _create_engagement_with_user(db_session, make_user, make_client):
    user = make_user()
    client = make_client(user=user)
    eng_mgr = EngagementManager(db_session)
    eng = eng_mgr.create_engagement(
        user.id,
        client.id,
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 12, 31, tzinfo=UTC),
        materiality_amount=100000.0,
    )
    return user, eng


class TestCreate:
    def test_create_with_value_and_amount_threshold(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)

        exp = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior-period growth",
            corroboration_tags=["prior_period"],
        )
        assert exp.id is not None
        assert exp.engagement_id == eng.id
        assert exp.expected_value == Decimal("1000.00")
        assert exp.precision_threshold_amount == Decimal("50.00")
        assert exp.result_status == ExpectationResultStatus.NOT_EVALUATED

    def test_create_with_range_and_percent_threshold(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        exp = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.RATIO,
            procedure_target_label="Current ratio",
            expected_range_low=1.5,
            expected_range_high=2.5,
            precision_threshold_percent=10.0,
            corroboration_basis_text="Industry median",
            corroboration_tags=["industry_data"],
        )
        assert exp.expected_range_low == Decimal("1.50")
        assert exp.expected_range_high == Decimal("2.50")
        assert exp.precision_threshold_percent == 10.0

    def test_create_rejects_both_value_and_range(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        with pytest.raises(ValueError, match="either expected_value or expected_range"):
            mgr.create_expectation(
                user_id=user.id,
                engagement_id=eng.id,
                procedure_target_type=ExpectationTargetType.ACCOUNT,
                procedure_target_label="Revenue",
                expected_value=1000.0,
                expected_range_low=900.0,
                expected_range_high=1100.0,
                precision_threshold_amount=50.0,
                corroboration_basis_text="Prior-period",
                corroboration_tags=["prior_period"],
            )

    def test_create_rejects_neither_value_nor_range(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        with pytest.raises(ValueError, match="expected_value or expected_range"):
            mgr.create_expectation(
                user_id=user.id,
                engagement_id=eng.id,
                procedure_target_type=ExpectationTargetType.ACCOUNT,
                procedure_target_label="Revenue",
                precision_threshold_amount=50.0,
                corroboration_basis_text="Prior-period",
                corroboration_tags=["prior_period"],
            )

    def test_create_rejects_both_thresholds(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        with pytest.raises(ValueError, match="amount or percent, not both"):
            mgr.create_expectation(
                user_id=user.id,
                engagement_id=eng.id,
                procedure_target_type=ExpectationTargetType.ACCOUNT,
                procedure_target_label="Revenue",
                expected_value=1000.0,
                precision_threshold_amount=50.0,
                precision_threshold_percent=5.0,
                corroboration_basis_text="Prior-period",
                corroboration_tags=["prior_period"],
            )

    def test_create_rejects_neither_threshold(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        with pytest.raises(ValueError, match="precision threshold"):
            mgr.create_expectation(
                user_id=user.id,
                engagement_id=eng.id,
                procedure_target_type=ExpectationTargetType.ACCOUNT,
                procedure_target_label="Revenue",
                expected_value=1000.0,
                corroboration_basis_text="Prior-period",
                corroboration_tags=["prior_period"],
            )

    def test_create_rejects_inverted_range(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        with pytest.raises(ValueError, match="greater than"):
            mgr.create_expectation(
                user_id=user.id,
                engagement_id=eng.id,
                procedure_target_type=ExpectationTargetType.RATIO,
                procedure_target_label="Quick ratio",
                expected_range_low=2.5,
                expected_range_high=1.5,
                precision_threshold_amount=0.1,
                corroboration_basis_text="Industry",
                corroboration_tags=["industry_data"],
            )

    def test_create_rejects_unknown_tag(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        with pytest.raises(ValueError, match="unknown corroboration tag"):
            mgr.create_expectation(
                user_id=user.id,
                engagement_id=eng.id,
                procedure_target_type=ExpectationTargetType.ACCOUNT,
                procedure_target_label="Revenue",
                expected_value=1000.0,
                precision_threshold_amount=50.0,
                corroboration_basis_text="Prior",
                corroboration_tags=["totally_made_up"],
            )

    def test_create_rejects_empty_tags(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        with pytest.raises(ValueError, match="at least one corroboration_tag"):
            mgr.create_expectation(
                user_id=user.id,
                engagement_id=eng.id,
                procedure_target_type=ExpectationTargetType.ACCOUNT,
                procedure_target_label="Revenue",
                expected_value=1000.0,
                precision_threshold_amount=50.0,
                corroboration_basis_text="Prior",
                corroboration_tags=[],
            )

    def test_create_rejects_other_user_engagement(self, db_session, make_user, make_client):
        user_a, eng_a = _create_engagement_with_user(db_session, make_user, make_client)
        user_b = make_user(email="other@example.com")
        mgr = AnalyticalExpectationsManager(db_session)
        with pytest.raises(ValueError, match="access denied"):
            mgr.create_expectation(
                user_id=user_b.id,
                engagement_id=eng_a.id,
                procedure_target_type=ExpectationTargetType.ACCOUNT,
                procedure_target_label="Revenue",
                expected_value=1000.0,
                precision_threshold_amount=50.0,
                corroboration_basis_text="Prior",
                corroboration_tags=["prior_period"],
            )


class TestListAndGet:
    def test_list_filters_by_status(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        e1 = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )
        e2 = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.RATIO,
            procedure_target_label="Quick",
            expected_value=1.5,
            precision_threshold_percent=5.0,
            corroboration_basis_text="Industry",
            corroboration_tags=["industry_data"],
        )
        # Set e1 to within
        mgr.update_expectation(user_id=user.id, expectation_id=e1.id, result_actual_value=1010.0)

        unevaluated, total = mgr.list_expectations(
            user_id=user.id,
            engagement_id=eng.id,
            result_status=ExpectationResultStatus.NOT_EVALUATED,
        )
        assert total == 1
        assert unevaluated[0].id == e2.id

    def test_list_filters_by_target_type(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )
        mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.RATIO,
            procedure_target_label="Quick",
            expected_value=1.5,
            precision_threshold_percent=5.0,
            corroboration_basis_text="Industry",
            corroboration_tags=["industry_data"],
        )
        items, total = mgr.list_expectations(
            user_id=user.id,
            engagement_id=eng.id,
            target_type=ExpectationTargetType.RATIO,
        )
        assert total == 1
        assert items[0].procedure_target_type == ExpectationTargetType.RATIO


class TestUpdate:
    def test_capture_actual_recomputes_status_within(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        exp = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )
        updated = mgr.update_expectation(user_id=user.id, expectation_id=exp.id, result_actual_value=1030.0)
        assert updated.result_status == ExpectationResultStatus.WITHIN_THRESHOLD
        assert updated.result_variance_amount == Decimal("30.00")
        assert updated.result_actual_value == Decimal("1030.00")

    def test_capture_actual_recomputes_status_exceeds(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        exp = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )
        updated = mgr.update_expectation(user_id=user.id, expectation_id=exp.id, result_actual_value=1100.0)
        assert updated.result_status == ExpectationResultStatus.EXCEEDS_THRESHOLD
        assert updated.result_variance_amount == Decimal("100.00")

    def test_clear_result_resets_to_not_evaluated(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        exp = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )
        mgr.update_expectation(user_id=user.id, expectation_id=exp.id, result_actual_value=1100.0)
        cleared = mgr.update_expectation(user_id=user.id, expectation_id=exp.id, clear_result=True)
        assert cleared.result_status == ExpectationResultStatus.NOT_EVALUATED
        assert cleared.result_actual_value is None
        assert cleared.result_variance_amount is None

    def test_update_other_user_returns_none(self, db_session, make_user, make_client):
        user_a, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        exp = mgr.create_expectation(
            user_id=user_a.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )
        user_b = make_user(email="other@example.com")
        result = mgr.update_expectation(user_id=user_b.id, expectation_id=exp.id, result_actual_value=1010.0)
        assert result is None


class TestArchiveAndCount:
    def test_archive_excludes_from_list_and_count(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        e1 = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )
        e2 = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.RATIO,
            procedure_target_label="Quick",
            expected_value=1.5,
            precision_threshold_percent=5.0,
            corroboration_basis_text="Industry",
            corroboration_tags=["industry_data"],
        )

        assert mgr.count_unevaluated(eng.id) == 2
        mgr.archive_expectation(user.id, e2.id, reason="superseded")

        items, total = mgr.list_expectations(user_id=user.id, engagement_id=eng.id)
        assert total == 1
        assert items[0].id == e1.id
        assert mgr.count_unevaluated(eng.id) == 1

    def test_count_unevaluated_excludes_within(self, db_session, make_user, make_client):
        user, eng = _create_engagement_with_user(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)
        e1 = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )
        mgr.update_expectation(user_id=user.id, expectation_id=e1.id, result_actual_value=1010.0)
        assert mgr.count_unevaluated(eng.id) == 0
