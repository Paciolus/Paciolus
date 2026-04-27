"""
Sprint 728c — expectation_evaluation helper + tool extractors.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analytical_expectations_manager import AnalyticalExpectationsManager
from analytical_expectations_model import (
    ExpectationResultStatus,
    ExpectationTargetType,
)
from engagement_manager import EngagementManager
from shared.expectation_evaluation import (
    evaluate_expectations_against_measurements,
    extract_flux_measurements,
    extract_multi_period_measurements,
    extract_ratio_measurements,
)

# =============================================================================
# Pure extractors
# =============================================================================


class TestExtractFluxMeasurements:
    def test_emits_balance_account_and_flux_line_for_each_item(self):
        flux_dict = {
            "items": [
                {"account": "Revenue", "current": 1000.0, "delta_amount": 200.0},
                {"account": "Cash", "current": 5000.0, "delta_amount": -100.0},
            ]
        }
        out = extract_flux_measurements(flux_dict)
        # Each item produces: BALANCE + ACCOUNT + FLUX_LINE = 3 triples
        assert len(out) == 6
        triples_by_label = {(t.value, label): val for t, label, val in out}
        assert triples_by_label[("balance", "Revenue")] == 1000.0
        assert triples_by_label[("account", "Revenue")] == 1000.0
        assert triples_by_label[("flux_line", "Revenue")] == 200.0
        assert triples_by_label[("flux_line", "Cash")] == -100.0

    def test_skips_items_without_account_name(self):
        flux_dict = {
            "items": [
                {"account": None, "current": 1000.0, "delta_amount": 200.0},
                {"current": 5000.0, "delta_amount": -100.0},  # no account at all
            ]
        }
        assert extract_flux_measurements(flux_dict) == []

    def test_handles_account_name_alias(self):
        flux_dict = {"items": [{"account_name": "Revenue", "current_balance": 100.0}]}
        out = extract_flux_measurements(flux_dict)
        assert any(label == "Revenue" and val == 100.0 for _, label, val in out)


class TestExtractMultiPeriodMeasurements:
    def test_emits_balance_and_account_for_each_movement(self):
        result = {
            "movements": [
                {"account": "Inventory", "current_balance": 50000.0},
                {"account": "AP", "current": 25000.0},
            ]
        }
        out = extract_multi_period_measurements(result)
        labels = {(t.value, label): val for t, label, val in out}
        assert labels[("balance", "Inventory")] == 50000.0
        assert labels[("balance", "AP")] == 25000.0


class TestExtractRatioMeasurements:
    def test_dict_form(self):
        out = extract_ratio_measurements({"current_ratio": 2.0, "quick_ratio": 1.5})
        labels = {label: val for _, label, val in out}
        assert labels == {"current_ratio": 2.0, "quick_ratio": 1.5}

    def test_list_form(self):
        out = extract_ratio_measurements(
            [{"name": "current_ratio", "value": 2.0}, {"label": "quick_ratio", "value": 1.5}]
        )
        labels = {label: val for _, label, val in out}
        assert labels == {"current_ratio": 2.0, "quick_ratio": 1.5}

    def test_nested_value(self):
        out = extract_ratio_measurements({"x": {"value": 3.5, "benchmark": 2.0}})
        assert (ExpectationTargetType.RATIO, "x", 3.5) in out


# =============================================================================
# Evaluator (with DB)
# =============================================================================


def _seed_engagement_with_expectation(db_session, make_user, make_client, **kwargs):
    user = make_user()
    client = make_client(user=user)
    eng = EngagementManager(db_session).create_engagement(
        user.id,
        client.id,
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 12, 31, tzinfo=UTC),
        materiality_amount=100000.0,
    )
    defaults = {
        "procedure_target_type": ExpectationTargetType.ACCOUNT,
        "procedure_target_label": "Revenue",
        "expected_value": 1000.0,
        "precision_threshold_amount": 50.0,
        "corroboration_basis_text": "Prior",
        "corroboration_tags": ["prior_period"],
    }
    defaults.update(kwargs)
    exp = AnalyticalExpectationsManager(db_session).create_expectation(
        user_id=user.id, engagement_id=eng.id, **defaults
    )
    return user, eng, exp


class TestEvaluateExpectationsAgainstMeasurements:
    def test_within_threshold_match(self, db_session, make_user, make_client):
        user, eng, exp = _seed_engagement_with_expectation(db_session, make_user, make_client)
        out = evaluate_expectations_against_measurements(
            db=db_session,
            user_id=user.id,
            engagement_id=eng.id,
            measurements=[
                (ExpectationTargetType.ACCOUNT, "Revenue", 1020.0),
            ],
        )
        assert len(out) == 1
        assert out[0]["status"] == "within_threshold"
        assert out[0]["expectation_id"] == exp.id
        # Persisted
        db_session.refresh(exp)
        assert exp.result_status == ExpectationResultStatus.WITHIN_THRESHOLD

    def test_exceeds_threshold_match(self, db_session, make_user, make_client):
        user, eng, exp = _seed_engagement_with_expectation(db_session, make_user, make_client)
        out = evaluate_expectations_against_measurements(
            db=db_session,
            user_id=user.id,
            engagement_id=eng.id,
            measurements=[
                (ExpectationTargetType.ACCOUNT, "Revenue", 1500.0),
            ],
        )
        assert out[0]["status"] == "exceeds_threshold"

    def test_label_match_is_case_insensitive(self, db_session, make_user, make_client):
        user, eng, exp = _seed_engagement_with_expectation(db_session, make_user, make_client)
        out = evaluate_expectations_against_measurements(
            db=db_session,
            user_id=user.id,
            engagement_id=eng.id,
            measurements=[
                (ExpectationTargetType.ACCOUNT, "REVENUE", 1020.0),
            ],
        )
        assert len(out) == 1

    def test_target_type_mismatch_does_not_evaluate(self, db_session, make_user, make_client):
        user, eng, exp = _seed_engagement_with_expectation(db_session, make_user, make_client)
        # Expectation is on ACCOUNT; we pass FLUX_LINE → no match
        out = evaluate_expectations_against_measurements(
            db=db_session,
            user_id=user.id,
            engagement_id=eng.id,
            measurements=[
                (ExpectationTargetType.FLUX_LINE, "Revenue", 1020.0),
            ],
        )
        assert out == []
        db_session.refresh(exp)
        assert exp.result_status == ExpectationResultStatus.NOT_EVALUATED

    def test_already_evaluated_expectation_is_not_re_run(self, db_session, make_user, make_client):
        user, eng, exp = _seed_engagement_with_expectation(db_session, make_user, make_client)
        # First run
        evaluate_expectations_against_measurements(
            db=db_session,
            user_id=user.id,
            engagement_id=eng.id,
            measurements=[(ExpectationTargetType.ACCOUNT, "Revenue", 1020.0)],
        )
        # Second run with new value should be a no-op (still within from before)
        out = evaluate_expectations_against_measurements(
            db=db_session,
            user_id=user.id,
            engagement_id=eng.id,
            measurements=[(ExpectationTargetType.ACCOUNT, "Revenue", 9999.0)],
        )
        assert out == []
        db_session.refresh(exp)
        assert exp.result_actual_value == Decimal("1020.00")

    def test_no_engagement_id_match_returns_empty(self, db_session, make_user, make_client):
        user, _eng, _exp = _seed_engagement_with_expectation(db_session, make_user, make_client)
        # A different engagement_id with no items
        out = evaluate_expectations_against_measurements(
            db=db_session,
            user_id=user.id,
            engagement_id=99999,
            measurements=[(ExpectationTargetType.ACCOUNT, "Revenue", 1020.0)],
        )
        assert out == []

    def test_other_user_cannot_evaluate(self, db_session, make_user, make_client):
        user_a, eng, _exp = _seed_engagement_with_expectation(db_session, make_user, make_client)
        user_b = make_user(email="other-728c@example.com")
        out = evaluate_expectations_against_measurements(
            db=db_session,
            user_id=user_b.id,
            engagement_id=eng.id,
            measurements=[(ExpectationTargetType.ACCOUNT, "Revenue", 1020.0)],
        )
        assert out == []

    def test_multiple_measurements_first_match_wins(self, db_session, make_user, make_client):
        user, eng, exp = _seed_engagement_with_expectation(db_session, make_user, make_client)
        out = evaluate_expectations_against_measurements(
            db=db_session,
            user_id=user.id,
            engagement_id=eng.id,
            measurements=[
                (ExpectationTargetType.ACCOUNT, "Revenue", 1020.0),
                (ExpectationTargetType.ACCOUNT, "Revenue", 9999.0),  # ignored
            ],
        )
        assert len(out) == 1
        assert out[0]["actual"] == 1020.0
