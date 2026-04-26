"""
Sprint 728a — Engagement-completion gate integration with ISA 520 expectations.

Pins the completion-gate behavior added in engagement_manager.py:
  - Engagements with no expectations: gate is unaffected (skipped).
  - Engagements with all expectations evaluated: gate passes.
  - Engagements with one or more NOT_EVALUATED expectations: gate blocks.
  - Archived expectations don't count against the gate.
  - Gate co-exists with the prior follow-up-item disposition gate.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from analytical_expectations_manager import AnalyticalExpectationsManager
from analytical_expectations_model import ExpectationTargetType
from engagement_manager import EngagementManager
from engagement_model import EngagementStatus
from follow_up_items_model import FollowUpDisposition, FollowUpItem


def _setup(db_session, make_user, make_client):
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


class TestCompletionGate:
    def test_completion_passes_when_no_expectations(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
        result = EngagementManager(db_session).complete_engagement(user.id, eng.id)
        assert result.status == EngagementStatus.COMPLETED

    def test_completion_blocks_when_expectation_unevaluated(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
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
        with pytest.raises(ValueError, match="ISA 520"):
            EngagementManager(db_session).complete_engagement(user.id, eng.id)

    def test_completion_passes_when_all_expectations_evaluated(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
        ae_mgr = AnalyticalExpectationsManager(db_session)
        e1 = ae_mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )
        e2 = ae_mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.RATIO,
            procedure_target_label="Current",
            expected_value=2.0,
            precision_threshold_percent=10.0,
            corroboration_basis_text="Industry",
            corroboration_tags=["industry_data"],
        )
        ae_mgr.update_expectation(user_id=user.id, expectation_id=e1.id, result_actual_value=1010.0)
        ae_mgr.update_expectation(user_id=user.id, expectation_id=e2.id, result_actual_value=2.5)
        result = EngagementManager(db_session).complete_engagement(user.id, eng.id)
        assert result.status == EngagementStatus.COMPLETED

    def test_archived_expectation_does_not_block(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
        ae_mgr = AnalyticalExpectationsManager(db_session)
        e = ae_mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )
        ae_mgr.archive_expectation(user.id, e.id, reason="superseded")
        result = EngagementManager(db_session).complete_engagement(user.id, eng.id)
        assert result.status == EngagementStatus.COMPLETED

    def test_follow_up_gate_runs_before_expectation_gate(self, db_session, make_user, make_client):
        """Follow-up disposition gate is checked first; ISA 520 gate only fires
        once that gate has passed."""
        user, eng = _setup(db_session, make_user, make_client)

        item = FollowUpItem(
            engagement_id=eng.id,
            description="Anomaly",
            tool_source="trial_balance",
            disposition=FollowUpDisposition.NOT_REVIEWED,
        )
        db_session.add(item)
        db_session.flush()

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

        with pytest.raises(ValueError, match="follow-up item"):
            EngagementManager(db_session).complete_engagement(user.id, eng.id)
