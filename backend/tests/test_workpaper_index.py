"""
Tests for Workpaper Index Generator — Sprint 100
Phase X: Engagement Layer

Covers:
- TestWorkpaperIndexGenerator: document register, follow-up summary, sign-off, access control
- TestWorkpaperIndexWithToolRuns: grouping by tool, multiple runs
- TestWorkpaperIndexFollowUpSummary: severity/disposition/tool_source aggregation
- TestWorkpaperIndexEndpoint: route registration
"""

import sys
from pathlib import Path
from datetime import datetime, UTC

import pytest
from sqlalchemy.orm import Session

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workpaper_index_generator import WorkpaperIndexGenerator, TOOL_LABELS, TOOL_LEAD_SHEET_REFS
from engagement_model import ToolName, ToolRunStatus
from follow_up_items_model import FollowUpItem, FollowUpSeverity, FollowUpDisposition


class TestWorkpaperIndexGenerator:
    """Basic workpaper index generation tests."""

    def test_generate_empty_engagement(self, db_session, make_engagement):
        """Index for engagement with no tool runs returns all tools as not_started."""
        eng = make_engagement()
        gen = WorkpaperIndexGenerator(db_session)

        user_id = eng.created_by
        result = gen.generate(user_id, eng.id)

        assert result["engagement_id"] == eng.id
        assert result["client_name"] == "Acme Corp"
        assert len(result["document_register"]) == 8  # All 8 tools
        assert all(e["status"] == "not_started" for e in result["document_register"])
        assert all(e["run_count"] == 0 for e in result["document_register"])
        assert result["follow_up_summary"]["total_count"] == 0

    def test_sign_off_is_blank(self, db_session, make_engagement):
        """Sign-off fields must be blank by design."""
        eng = make_engagement()
        gen = WorkpaperIndexGenerator(db_session)

        result = gen.generate(eng.created_by, eng.id)

        assert result["sign_off"]["prepared_by"] == ""
        assert result["sign_off"]["reviewed_by"] == ""
        assert result["sign_off"]["date"] == ""

    def test_generated_at_is_present(self, db_session, make_engagement):
        """Index includes a generated_at timestamp."""
        eng = make_engagement()
        gen = WorkpaperIndexGenerator(db_session)

        result = gen.generate(eng.created_by, eng.id)

        assert result["generated_at"]
        # Should be parseable
        datetime.fromisoformat(result["generated_at"])

    def test_period_dates_in_result(self, db_session, make_engagement):
        """Index includes period start and end."""
        eng = make_engagement(
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 12, 31, tzinfo=UTC),
        )
        gen = WorkpaperIndexGenerator(db_session)

        result = gen.generate(eng.created_by, eng.id)

        assert "2025" in result["period_start"]
        assert "2025" in result["period_end"]

    def test_access_denied_for_wrong_user(self, db_session, make_engagement, make_user):
        """User cannot access another user's engagement workpaper index."""
        eng = make_engagement()
        other_user = make_user(email="other@example.com")
        gen = WorkpaperIndexGenerator(db_session)

        with pytest.raises(ValueError, match="not found or access denied"):
            gen.generate(other_user.id, eng.id)

    def test_nonexistent_engagement(self, db_session, make_user):
        """Nonexistent engagement raises ValueError."""
        user = make_user()
        gen = WorkpaperIndexGenerator(db_session)

        with pytest.raises(ValueError, match="not found or access denied"):
            gen.generate(user.id, 9999)

    def test_all_tools_in_register(self, db_session, make_engagement):
        """Document register contains all tools."""
        eng = make_engagement()
        gen = WorkpaperIndexGenerator(db_session)

        result = gen.generate(eng.created_by, eng.id)

        tool_names = [e["tool_name"] for e in result["document_register"]]
        expected = [t.value for t in ToolName]
        assert sorted(tool_names) == sorted(expected)

    def test_tool_labels_present(self, db_session, make_engagement):
        """Each entry has a human-readable tool_label."""
        eng = make_engagement()
        gen = WorkpaperIndexGenerator(db_session)

        result = gen.generate(eng.created_by, eng.id)

        for entry in result["document_register"]:
            assert entry["tool_label"]
            assert len(entry["tool_label"]) > 3

    def test_lead_sheet_refs_present(self, db_session, make_engagement):
        """Each entry has lead_sheet_refs."""
        eng = make_engagement()
        gen = WorkpaperIndexGenerator(db_session)

        result = gen.generate(eng.created_by, eng.id)

        for entry in result["document_register"]:
            assert isinstance(entry["lead_sheet_refs"], list)
            assert len(entry["lead_sheet_refs"]) > 0


class TestWorkpaperIndexWithToolRuns:
    """Tests with actual tool run data."""

    def test_single_tool_run(self, db_session, make_engagement, make_tool_run):
        """Tool with a run shows as completed with run_count=1."""
        eng = make_engagement()
        make_tool_run(engagement=eng, tool_name=ToolName.TRIAL_BALANCE)

        gen = WorkpaperIndexGenerator(db_session)
        result = gen.generate(eng.created_by, eng.id)

        tb_entry = next(e for e in result["document_register"] if e["tool_name"] == "trial_balance")
        assert tb_entry["status"] == "completed"
        assert tb_entry["run_count"] == 1
        assert tb_entry["last_run_date"] is not None

    def test_multiple_runs_same_tool(self, db_session, make_engagement, make_tool_run):
        """Multiple runs for same tool shows correct count and latest date."""
        eng = make_engagement()
        make_tool_run(engagement=eng, tool_name=ToolName.AP_TESTING, run_number=1)
        make_tool_run(engagement=eng, tool_name=ToolName.AP_TESTING, run_number=2)
        make_tool_run(engagement=eng, tool_name=ToolName.AP_TESTING, run_number=3)

        gen = WorkpaperIndexGenerator(db_session)
        result = gen.generate(eng.created_by, eng.id)

        ap_entry = next(e for e in result["document_register"] if e["tool_name"] == "ap_testing")
        assert ap_entry["run_count"] == 3
        assert ap_entry["status"] == "completed"

    def test_mixed_tools_completed_and_not(self, db_session, make_engagement, make_tool_run):
        """Some tools completed, others not started."""
        eng = make_engagement()
        make_tool_run(engagement=eng, tool_name=ToolName.TRIAL_BALANCE)
        make_tool_run(engagement=eng, tool_name=ToolName.BANK_RECONCILIATION)

        gen = WorkpaperIndexGenerator(db_session)
        result = gen.generate(eng.created_by, eng.id)

        completed = [e for e in result["document_register"] if e["status"] == "completed"]
        not_started = [e for e in result["document_register"] if e["status"] == "not_started"]
        assert len(completed) == 2
        assert len(not_started) == 6


class TestWorkpaperIndexFollowUpSummary:
    """Tests for follow-up item summary in workpaper index."""

    def test_summary_with_items(self, db_session, make_engagement, make_follow_up_item):
        """Follow-up summary correctly aggregates items."""
        eng = make_engagement()
        make_follow_up_item(engagement=eng, severity=FollowUpSeverity.HIGH, tool_source="trial_balance")
        make_follow_up_item(engagement=eng, severity=FollowUpSeverity.HIGH, tool_source="trial_balance")
        make_follow_up_item(engagement=eng, severity=FollowUpSeverity.MEDIUM, tool_source="ap_testing")
        make_follow_up_item(engagement=eng, severity=FollowUpSeverity.LOW, tool_source="payroll_testing")

        gen = WorkpaperIndexGenerator(db_session)
        result = gen.generate(eng.created_by, eng.id)

        summary = result["follow_up_summary"]
        assert summary["total_count"] == 4
        assert summary["by_severity"]["high"] == 2
        assert summary["by_severity"]["medium"] == 1
        assert summary["by_severity"]["low"] == 1
        assert summary["by_tool_source"]["trial_balance"] == 2
        assert summary["by_tool_source"]["ap_testing"] == 1

    def test_summary_empty(self, db_session, make_engagement):
        """Empty engagement has zero-count summary."""
        eng = make_engagement()
        gen = WorkpaperIndexGenerator(db_session)

        result = gen.generate(eng.created_by, eng.id)

        assert result["follow_up_summary"]["total_count"] == 0
        assert result["follow_up_summary"]["by_severity"] == {}

    def test_summary_by_disposition(self, db_session, make_engagement, make_follow_up_item):
        """Summary groups by disposition."""
        eng = make_engagement()
        make_follow_up_item(engagement=eng, disposition=FollowUpDisposition.NOT_REVIEWED)
        make_follow_up_item(engagement=eng, disposition=FollowUpDisposition.NOT_REVIEWED)
        make_follow_up_item(engagement=eng, disposition=FollowUpDisposition.INVESTIGATED_NO_ISSUE)

        gen = WorkpaperIndexGenerator(db_session)
        result = gen.generate(eng.created_by, eng.id)

        disp = result["follow_up_summary"]["by_disposition"]
        assert disp["not_reviewed"] == 2
        assert disp["investigated_no_issue"] == 1

    def test_items_from_different_engagements_isolated(
        self, db_session, make_engagement, make_follow_up_item, make_user, make_client
    ):
        """Follow-up items from other engagements not included."""
        eng1 = make_engagement()
        user2 = make_user(email="other@example.com")
        client2 = make_client(user=user2, name="Other Corp")
        eng2 = make_engagement(client=client2, user=user2)
        make_follow_up_item(engagement=eng1, severity=FollowUpSeverity.HIGH)
        make_follow_up_item(engagement=eng2, severity=FollowUpSeverity.LOW)

        gen = WorkpaperIndexGenerator(db_session)
        result = gen.generate(eng1.created_by, eng1.id)

        assert result["follow_up_summary"]["total_count"] == 1
        assert result["follow_up_summary"]["by_severity"].get("high") == 1
        assert result["follow_up_summary"]["by_severity"].get("low") is None


class TestWorkpaperIndexEndpoint:
    """Test route registration."""

    def test_workpaper_index_route_registered(self):
        """GET /engagements/{id}/workpaper-index is registered."""
        from main import app

        routes = [route.path for route in app.routes]
        assert "/engagements/{engagement_id}/workpaper-index" in routes
