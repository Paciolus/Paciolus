"""
Tests for Sprint 311: Composite Score Trend.

Covers:
- EngagementManager.get_tool_run_trends() logic
- 0 runs → empty list
- 1 run → latest_score set, no delta/direction
- 2 runs improving/degrading/stable
- Null composite_score excluded
- Failed runs excluded
- Route registration
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engagement_manager import EngagementManager
from engagement_model import ToolName, ToolRunStatus


class TestToolRunTrends:
    """Tests for get_tool_run_trends()."""

    @pytest.fixture()
    def setup(self, db_session):
        """Create user, client, engagement, and return manager."""
        from models import Client, User

        user = User(email="trends@test.com", hashed_password="hashed", name="Test")
        db_session.add(user)
        db_session.flush()

        client = Client(user_id=user.id, name="Trends Client")
        db_session.add(client)
        db_session.flush()

        manager = EngagementManager(db_session)
        engagement = manager.create_engagement(
            user_id=user.id,
            client_id=client.id,
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 12, 31, tzinfo=UTC),
        )

        return manager, engagement

    def test_no_runs_returns_empty(self, setup):
        manager, eng = setup
        result = manager.get_tool_run_trends(eng.id)
        assert result == []

    def test_single_run_no_delta(self, setup):
        manager, eng = setup
        manager.record_tool_run(
            engagement_id=eng.id,
            tool_name=ToolName.TRIAL_BALANCE,
            status=ToolRunStatus.COMPLETED,
            composite_score=65.0,
        )

        result = manager.get_tool_run_trends(eng.id)
        assert len(result) == 1
        assert result[0]["tool_name"] == "trial_balance"
        assert result[0]["latest_score"] == 65.0
        assert result[0]["previous_score"] is None
        assert result[0]["score_delta"] is None
        assert result[0]["direction"] is None
        assert result[0]["run_count"] == 1

    def test_two_runs_improving(self, setup):
        """Score decreased (80 → 60): improving (fewer flags)."""
        manager, eng = setup
        manager.record_tool_run(
            engagement_id=eng.id,
            tool_name=ToolName.AP_TESTING,
            status=ToolRunStatus.COMPLETED,
            composite_score=80.0,
        )
        manager.record_tool_run(
            engagement_id=eng.id,
            tool_name=ToolName.AP_TESTING,
            status=ToolRunStatus.COMPLETED,
            composite_score=60.0,
        )

        result = manager.get_tool_run_trends(eng.id)
        ap = next(r for r in result if r["tool_name"] == "ap_testing")
        assert ap["latest_score"] == 60.0
        assert ap["previous_score"] == 80.0
        assert ap["score_delta"] == -20.0
        assert ap["direction"] == "improving"

    def test_two_runs_degrading(self, setup):
        """Score increased (30 → 55): degrading (more flags)."""
        manager, eng = setup
        manager.record_tool_run(
            engagement_id=eng.id,
            tool_name=ToolName.REVENUE_TESTING,
            status=ToolRunStatus.COMPLETED,
            composite_score=30.0,
        )
        manager.record_tool_run(
            engagement_id=eng.id,
            tool_name=ToolName.REVENUE_TESTING,
            status=ToolRunStatus.COMPLETED,
            composite_score=55.0,
        )

        result = manager.get_tool_run_trends(eng.id)
        rev = next(r for r in result if r["tool_name"] == "revenue_testing")
        assert rev["score_delta"] == 25.0
        assert rev["direction"] == "degrading"

    def test_two_runs_stable(self, setup):
        """Score barely changed (45 → 45.5): stable."""
        manager, eng = setup
        manager.record_tool_run(
            engagement_id=eng.id,
            tool_name=ToolName.JOURNAL_ENTRY_TESTING,
            status=ToolRunStatus.COMPLETED,
            composite_score=45.0,
        )
        manager.record_tool_run(
            engagement_id=eng.id,
            tool_name=ToolName.JOURNAL_ENTRY_TESTING,
            status=ToolRunStatus.COMPLETED,
            composite_score=45.5,
        )

        result = manager.get_tool_run_trends(eng.id)
        je = next(r for r in result if r["tool_name"] == "journal_entry_testing")
        assert je["score_delta"] == 0.5
        assert je["direction"] == "stable"

    def test_null_composite_score_excluded(self, setup):
        """Runs with null composite_score are excluded."""
        manager, eng = setup
        manager.record_tool_run(
            engagement_id=eng.id,
            tool_name=ToolName.TRIAL_BALANCE,
            status=ToolRunStatus.COMPLETED,
            composite_score=None,
        )

        result = manager.get_tool_run_trends(eng.id)
        assert result == []

    def test_failed_runs_excluded(self, setup):
        """Failed runs are excluded."""
        manager, eng = setup
        manager.record_tool_run(
            engagement_id=eng.id,
            tool_name=ToolName.TRIAL_BALANCE,
            status=ToolRunStatus.FAILED,
            composite_score=50.0,
        )

        result = manager.get_tool_run_trends(eng.id)
        assert result == []

    def test_sorted_by_tool_name(self, setup):
        """Results are sorted by tool_name."""
        manager, eng = setup
        manager.record_tool_run(
            engagement_id=eng.id,
            tool_name=ToolName.REVENUE_TESTING,
            status=ToolRunStatus.COMPLETED,
            composite_score=50.0,
        )
        manager.record_tool_run(
            engagement_id=eng.id,
            tool_name=ToolName.AP_TESTING,
            status=ToolRunStatus.COMPLETED,
            composite_score=40.0,
        )

        result = manager.get_tool_run_trends(eng.id)
        names = [r["tool_name"] for r in result]
        assert names == sorted(names)


class TestToolRunTrendsRouteRegistration:
    """Verify the endpoint is registered."""

    def test_endpoint_registered(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/tool-run-trends" in paths
