"""
Tests for Phase X Follow-Up Items: Model, Manager, Routes, Auto-Population, Zero-Storage.

Sprint 99: Follow-Up Items Tracker (Backend)
~51 tests covering schema, CRUD, filtering, aggregation, auto-population, and zero-storage.
"""

import sys
from datetime import datetime, UTC
from pathlib import Path

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, str(Path(__file__).parent.parent))

from follow_up_items_model import (
    FollowUpItem,
    FollowUpSeverity,
    FollowUpDisposition,
)
from follow_up_items_manager import FollowUpItemsManager
from engagement_model import (
    Engagement,
    ToolRun,
    EngagementStatus,
    ToolName,
    ToolRunStatus,
)
from engagement_manager import EngagementManager
from models import User, Client


# ===========================================================================
# TestFollowUpItemSchema — Model structure, enums, to_dict, guardrail checks
# ===========================================================================


class TestFollowUpItemSchema:
    """Verify model structure and enum definitions."""

    def test_severity_values(self):
        assert FollowUpSeverity.HIGH.value == "high"
        assert FollowUpSeverity.MEDIUM.value == "medium"
        assert FollowUpSeverity.LOW.value == "low"

    def test_disposition_values(self):
        assert FollowUpDisposition.NOT_REVIEWED.value == "not_reviewed"
        assert FollowUpDisposition.INVESTIGATED_NO_ISSUE.value == "investigated_no_issue"
        assert FollowUpDisposition.INVESTIGATED_ADJUSTMENT_POSTED.value == "investigated_adjustment_posted"
        assert FollowUpDisposition.INVESTIGATED_FURTHER_REVIEW.value == "investigated_further_review"
        assert FollowUpDisposition.IMMATERIAL.value == "immaterial"

    def test_follow_up_item_to_dict(self, make_follow_up_item):
        item = make_follow_up_item(description="Test narrative", tool_source="ap_testing")
        d = item.to_dict()
        assert d["id"] == item.id
        assert d["description"] == "Test narrative"
        assert d["tool_source"] == "ap_testing"
        assert d["severity"] == "medium"
        assert d["disposition"] == "not_reviewed"
        assert d["auditor_notes"] is None
        assert "created_at" in d
        assert "updated_at" in d

    def test_follow_up_item_to_dict_with_notes(self, make_follow_up_item):
        item = make_follow_up_item(auditor_notes="Investigated, no issue found")
        d = item.to_dict()
        assert d["auditor_notes"] == "Investigated, no issue found"

    def test_follow_up_item_repr(self, make_follow_up_item):
        item = make_follow_up_item()
        r = repr(item)
        assert "FollowUpItem" in r
        assert str(item.id) in r

    def test_follow_up_table_has_no_prohibited_columns(self, db_engine):
        """Guardrail 2: no account_number, amount, transaction_id, or PII columns."""
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("follow_up_items")}
        prohibited = {
            "account_number", "account_name",
            "amount", "debit", "credit",
            "transaction_id", "entry_id",
            "vendor_name", "employee_name",
        }
        assert columns.isdisjoint(prohibited), f"Prohibited columns found: {columns & prohibited}"

    def test_follow_up_table_has_expected_columns(self, db_engine):
        """Verify expected columns exist."""
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("follow_up_items")}
        expected = {
            "id", "engagement_id", "tool_run_id",
            "description", "tool_source", "severity",
            "disposition", "auditor_notes",
            "created_at", "updated_at",
        }
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_severity_enum_has_three_levels(self):
        assert len(FollowUpSeverity) == 3

    def test_disposition_enum_has_five_states(self):
        assert len(FollowUpDisposition) == 5


# ===========================================================================
# TestFollowUpItemCRUD — Create, Read, Update, Delete, List
# ===========================================================================


class TestFollowUpItemCRUD:
    """CRUD operations via FollowUpItemsManager."""

    def test_create_item(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        item = mgr.create_item(
            user_id=user.id,
            engagement_id=eng.id,
            description="Round amount entries detected: 47 entries flagged",
            tool_source="journal_entry_testing",
            severity=FollowUpSeverity.HIGH,
        )

        assert item.id is not None
        assert item.engagement_id == eng.id
        assert item.description == "Round amount entries detected: 47 entries flagged"
        assert item.tool_source == "journal_entry_testing"
        assert item.severity == FollowUpSeverity.HIGH
        assert item.disposition == FollowUpDisposition.NOT_REVIEWED

    def test_create_item_with_tool_run(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        tr = eng_mgr.record_tool_run(eng.id, ToolName.AP_TESTING, ToolRunStatus.COMPLETED, 85.0)

        mgr = FollowUpItemsManager(db_session)
        item = mgr.create_item(
            user_id=user.id,
            engagement_id=eng.id,
            description="Duplicate payments flagged",
            tool_source="ap_testing",
            tool_run_id=tr.id,
        )

        assert item.tool_run_id == tr.id

    def test_create_item_with_auditor_notes(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        item = mgr.create_item(
            user_id=user.id,
            engagement_id=eng.id,
            description="Suspense account with balance",
            tool_source="trial_balance",
            auditor_notes="Reviewed — balance relates to year-end accrual",
        )

        assert item.auditor_notes == "Reviewed — balance relates to year-end accrual"

    def test_create_item_wrong_user_rejected(self, db_session, make_user, make_client):
        user1 = make_user(email="owner@test.com")
        user2 = make_user(email="intruder@test.com")
        client = make_client(user=user1)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user1.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="Engagement not found"):
            mgr.create_item(
                user_id=user2.id,
                engagement_id=eng.id,
                description="Should not be created",
                tool_source="trial_balance",
            )

    def test_create_item_empty_description_rejected(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="Description is required"):
            mgr.create_item(
                user_id=user.id,
                engagement_id=eng.id,
                description="   ",
                tool_source="trial_balance",
            )

    def test_create_item_empty_tool_source_rejected(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="Tool source is required"):
            mgr.create_item(
                user_id=user.id,
                engagement_id=eng.id,
                description="Valid description",
                tool_source="",
            )

    def test_create_item_invalid_tool_run_rejected(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="Tool run not found"):
            mgr.create_item(
                user_id=user.id,
                engagement_id=eng.id,
                description="Valid description",
                tool_source="trial_balance",
                tool_run_id=99999,
            )

    def test_get_items(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        for i in range(3):
            mgr.create_item(user.id, eng.id, f"Item {i}", "trial_balance")

        items, total = mgr.get_items(user.id, eng.id)
        assert len(items) == 3
        assert total == 3

    def test_update_item_disposition(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        item = mgr.create_item(user.id, eng.id, "Test item", "ap_testing")
        updated = mgr.update_item(user.id, item.id, disposition=FollowUpDisposition.INVESTIGATED_NO_ISSUE)

        assert updated is not None
        assert updated.disposition == FollowUpDisposition.INVESTIGATED_NO_ISSUE

    def test_update_item_notes(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        item = mgr.create_item(user.id, eng.id, "Test item", "payroll_testing")
        updated = mgr.update_item(user.id, item.id, auditor_notes="Reviewed and cleared")

        assert updated.auditor_notes == "Reviewed and cleared"

    def test_update_item_severity(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        item = mgr.create_item(user.id, eng.id, "Test item", "trial_balance", severity=FollowUpSeverity.LOW)
        updated = mgr.update_item(user.id, item.id, severity=FollowUpSeverity.HIGH)

        assert updated.severity == FollowUpSeverity.HIGH

    def test_update_item_not_found(self, db_session, make_user):
        user = make_user()
        mgr = FollowUpItemsManager(db_session)
        assert mgr.update_item(user.id, 99999, disposition=FollowUpDisposition.IMMATERIAL) is None

    def test_delete_item(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        item = mgr.create_item(user.id, eng.id, "To be deleted", "bank_reconciliation")
        assert mgr.delete_item(user.id, item.id) is True

        # Verify deleted
        items, total = mgr.get_items(user.id, eng.id)
        assert len(items) == 0
        assert total == 0

    def test_delete_item_not_found(self, db_session, make_user):
        user = make_user()
        mgr = FollowUpItemsManager(db_session)
        assert mgr.delete_item(user.id, 99999) is False

    def test_delete_item_wrong_user(self, db_session, make_user, make_client):
        user1 = make_user(email="owner@test.com")
        user2 = make_user(email="intruder@test.com")
        client = make_client(user=user1)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user1.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        item = mgr.create_item(user1.id, eng.id, "Owner's item", "trial_balance")
        assert mgr.delete_item(user2.id, item.id) is False


# ===========================================================================
# TestFollowUpItemFiltering — Filter by severity, disposition, tool_source
# ===========================================================================


class TestFollowUpItemFiltering:
    """Filtering queries on follow-up items."""

    def _setup(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        mgr = FollowUpItemsManager(db_session)

        mgr.create_item(user.id, eng.id, "High AP item", "ap_testing", FollowUpSeverity.HIGH)
        mgr.create_item(user.id, eng.id, "Medium JE item", "journal_entry_testing", FollowUpSeverity.MEDIUM)
        mgr.create_item(user.id, eng.id, "Low TB item", "trial_balance", FollowUpSeverity.LOW)
        item4 = mgr.create_item(user.id, eng.id, "Reviewed AP item", "ap_testing", FollowUpSeverity.HIGH)
        mgr.update_item(user.id, item4.id, disposition=FollowUpDisposition.INVESTIGATED_NO_ISSUE)

        return user, eng, mgr

    def test_filter_by_severity_high(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id, severity=FollowUpSeverity.HIGH)
        assert len(items) == 2
        assert total == 2
        assert all(i.severity == FollowUpSeverity.HIGH for i in items)

    def test_filter_by_severity_low(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id, severity=FollowUpSeverity.LOW)
        assert len(items) == 1

    def test_filter_by_disposition(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id, disposition=FollowUpDisposition.NOT_REVIEWED)
        assert len(items) == 3

    def test_filter_by_disposition_investigated(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id, disposition=FollowUpDisposition.INVESTIGATED_NO_ISSUE)
        assert len(items) == 1

    def test_filter_by_tool_source(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id, tool_source="ap_testing")
        assert len(items) == 2

    def test_filter_by_tool_source_single(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id, tool_source="trial_balance")
        assert len(items) == 1

    def test_combined_filter_severity_and_tool(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id, severity=FollowUpSeverity.HIGH, tool_source="ap_testing")
        assert len(items) == 2

    def test_no_results_filter(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id, tool_source="payroll_testing")
        assert len(items) == 0


# ===========================================================================
# TestFollowUpItemPagination — Limit/offset behavior
# ===========================================================================


class TestFollowUpItemPagination:
    """Pagination via limit/offset on get_items."""

    def _setup(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        mgr = FollowUpItemsManager(db_session)
        for i in range(10):
            mgr.create_item(user.id, eng.id, f"Item {i}", "trial_balance")
        return user, eng, mgr

    def test_default_returns_all_within_limit(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id)
        assert total == 10
        assert len(items) == 10

    def test_limit_returns_subset(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id, limit=3)
        assert total == 10
        assert len(items) == 3

    def test_offset_skips_items(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id, limit=3, offset=7)
        assert total == 10
        assert len(items) == 3

    def test_offset_beyond_results(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        items, total = mgr.get_items(user.id, eng.id, limit=50, offset=20)
        assert total == 10
        assert len(items) == 0

    def test_pagination_with_filter(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        mgr = FollowUpItemsManager(db_session)
        for i in range(5):
            mgr.create_item(user.id, eng.id, f"High {i}", "ap_testing", FollowUpSeverity.HIGH)
        for i in range(3):
            mgr.create_item(user.id, eng.id, f"Low {i}", "ap_testing", FollowUpSeverity.LOW)

        items, total = mgr.get_items(user.id, eng.id, severity=FollowUpSeverity.HIGH, limit=2)
        assert total == 5
        assert len(items) == 2

    def test_total_reflects_filter_not_full_set(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        mgr = FollowUpItemsManager(db_session)
        mgr.create_item(user.id, eng.id, "AP item", "ap_testing")
        mgr.create_item(user.id, eng.id, "JE item", "journal_entry_testing")

        items, total = mgr.get_items(user.id, eng.id, tool_source="ap_testing")
        assert total == 1


# ===========================================================================
# TestFollowUpItemAggregation — Summary counts
# ===========================================================================


class TestFollowUpItemAggregation:
    """Summary/aggregation queries."""

    def _setup(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        mgr = FollowUpItemsManager(db_session)

        mgr.create_item(user.id, eng.id, "Item 1", "ap_testing", FollowUpSeverity.HIGH)
        mgr.create_item(user.id, eng.id, "Item 2", "ap_testing", FollowUpSeverity.HIGH)
        mgr.create_item(user.id, eng.id, "Item 3", "journal_entry_testing", FollowUpSeverity.MEDIUM)
        mgr.create_item(user.id, eng.id, "Item 4", "trial_balance", FollowUpSeverity.LOW)
        item5 = mgr.create_item(user.id, eng.id, "Item 5", "payroll_testing", FollowUpSeverity.MEDIUM)
        mgr.update_item(user.id, item5.id, disposition=FollowUpDisposition.IMMATERIAL)

        return user, eng, mgr

    def test_summary_total_count(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        summary = mgr.get_summary(user.id, eng.id)
        assert summary["total_count"] == 5

    def test_summary_by_severity(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        summary = mgr.get_summary(user.id, eng.id)
        assert summary["by_severity"]["high"] == 2
        assert summary["by_severity"]["medium"] == 2
        assert summary["by_severity"]["low"] == 1

    def test_summary_by_disposition(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        summary = mgr.get_summary(user.id, eng.id)
        assert summary["by_disposition"]["not_reviewed"] == 4
        assert summary["by_disposition"]["immaterial"] == 1

    def test_summary_by_tool_source(self, db_session, make_user, make_client):
        user, eng, mgr = self._setup(db_session, make_user, make_client)
        summary = mgr.get_summary(user.id, eng.id)
        assert summary["by_tool_source"]["ap_testing"] == 2
        assert summary["by_tool_source"]["journal_entry_testing"] == 1
        assert summary["by_tool_source"]["trial_balance"] == 1
        assert summary["by_tool_source"]["payroll_testing"] == 1

    def test_summary_empty_engagement(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        summary = mgr.get_summary(user.id, eng.id)
        assert summary["total_count"] == 0
        assert summary["by_severity"] == {}
        assert summary["by_disposition"] == {}
        assert summary["by_tool_source"] == {}

    def test_summary_wrong_user_rejected(self, db_session, make_user, make_client):
        user1 = make_user(email="owner@test.com")
        user2 = make_user(email="other@test.com")
        client = make_client(user=user1)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user1.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="Engagement not found"):
            mgr.get_summary(user2.id, eng.id)

    def test_summary_all_dispositions(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        mgr = FollowUpItemsManager(db_session)
        dispositions = [
            FollowUpDisposition.NOT_REVIEWED,
            FollowUpDisposition.INVESTIGATED_NO_ISSUE,
            FollowUpDisposition.INVESTIGATED_ADJUSTMENT_POSTED,
            FollowUpDisposition.INVESTIGATED_FURTHER_REVIEW,
            FollowUpDisposition.IMMATERIAL,
        ]
        for i, disp in enumerate(dispositions):
            item = mgr.create_item(user.id, eng.id, f"Item {i}", "trial_balance")
            mgr.update_item(user.id, item.id, disposition=disp)

        summary = mgr.get_summary(user.id, eng.id)
        assert summary["total_count"] == 5
        assert len(summary["by_disposition"]) == 5


# ===========================================================================
# TestAutoPopulation — Tool run → follow-up items creation
# ===========================================================================


class TestAutoPopulation:
    """Auto-population of follow-up items from tool run findings."""

    def _setup(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        tr = eng_mgr.record_tool_run(eng.id, ToolName.AP_TESTING, ToolRunStatus.COMPLETED, 72.5)
        return user, eng, tr

    def test_auto_populate_creates_items(self, db_session, make_user, make_client):
        user, eng, tr = self._setup(db_session, make_user, make_client)
        mgr = FollowUpItemsManager(db_session)

        findings = [
            {"description": "Duplicate payments detected: 12 potential duplicates", "severity": "high"},
            {"description": "Round amount payments: 34 flagged", "severity": "medium"},
        ]

        items = mgr.auto_populate_from_tool_run(eng.id, tr.id, "ap_testing", findings)
        assert len(items) == 2
        assert items[0].tool_run_id == tr.id
        assert items[0].tool_source == "ap_testing"
        assert items[0].disposition == FollowUpDisposition.NOT_REVIEWED

    def test_auto_populate_severity_mapping(self, db_session, make_user, make_client):
        user, eng, tr = self._setup(db_session, make_user, make_client)
        mgr = FollowUpItemsManager(db_session)

        findings = [
            {"description": "High severity finding", "severity": "high"},
            {"description": "Medium severity finding", "severity": "medium"},
            {"description": "Low severity finding", "severity": "low"},
        ]

        items = mgr.auto_populate_from_tool_run(eng.id, tr.id, "ap_testing", findings)
        assert items[0].severity == FollowUpSeverity.HIGH
        assert items[1].severity == FollowUpSeverity.MEDIUM
        assert items[2].severity == FollowUpSeverity.LOW

    def test_auto_populate_invalid_severity_defaults_medium(self, db_session, make_user, make_client):
        user, eng, tr = self._setup(db_session, make_user, make_client)
        mgr = FollowUpItemsManager(db_session)

        findings = [{"description": "Unknown severity", "severity": "critical"}]
        items = mgr.auto_populate_from_tool_run(eng.id, tr.id, "ap_testing", findings)
        assert items[0].severity == FollowUpSeverity.MEDIUM

    def test_auto_populate_empty_description_skipped(self, db_session, make_user, make_client):
        user, eng, tr = self._setup(db_session, make_user, make_client)
        mgr = FollowUpItemsManager(db_session)

        findings = [
            {"description": "Valid finding", "severity": "high"},
            {"description": "", "severity": "medium"},
            {"description": "  ", "severity": "low"},
        ]

        items = mgr.auto_populate_from_tool_run(eng.id, tr.id, "ap_testing", findings)
        assert len(items) == 1

    def test_auto_populate_empty_findings(self, db_session, make_user, make_client):
        user, eng, tr = self._setup(db_session, make_user, make_client)
        mgr = FollowUpItemsManager(db_session)

        items = mgr.auto_populate_from_tool_run(eng.id, tr.id, "ap_testing", [])
        assert len(items) == 0

    def test_auto_populate_missing_severity_defaults(self, db_session, make_user, make_client):
        user, eng, tr = self._setup(db_session, make_user, make_client)
        mgr = FollowUpItemsManager(db_session)

        findings = [{"description": "Finding without severity"}]
        items = mgr.auto_populate_from_tool_run(eng.id, tr.id, "ap_testing", findings)
        assert items[0].severity == FollowUpSeverity.MEDIUM

    def test_auto_populate_strips_description_whitespace(self, db_session, make_user, make_client):
        user, eng, tr = self._setup(db_session, make_user, make_client)
        mgr = FollowUpItemsManager(db_session)

        findings = [{"description": "  Padded description  ", "severity": "high"}]
        items = mgr.auto_populate_from_tool_run(eng.id, tr.id, "ap_testing", findings)
        assert items[0].description == "Padded description"

    def test_auto_populate_multiple_tools(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        eng_mgr = EngagementManager(db_session)
        eng = eng_mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        tr1 = eng_mgr.record_tool_run(eng.id, ToolName.AP_TESTING, ToolRunStatus.COMPLETED)
        tr2 = eng_mgr.record_tool_run(eng.id, ToolName.PAYROLL_TESTING, ToolRunStatus.COMPLETED)

        mgr = FollowUpItemsManager(db_session)
        mgr.auto_populate_from_tool_run(eng.id, tr1.id, "ap_testing", [
            {"description": "AP finding", "severity": "high"},
        ])
        mgr.auto_populate_from_tool_run(eng.id, tr2.id, "payroll_testing", [
            {"description": "Payroll finding", "severity": "medium"},
        ])

        items = db_session.query(FollowUpItem).filter(
            FollowUpItem.engagement_id == eng.id
        ).all()
        assert len(items) == 2
        sources = {i.tool_source for i in items}
        assert sources == {"ap_testing", "payroll_testing"}

    def test_auto_populate_large_batch(self, db_session, make_user, make_client):
        user, eng, tr = self._setup(db_session, make_user, make_client)
        mgr = FollowUpItemsManager(db_session)

        findings = [
            {"description": f"Finding {i}", "severity": "medium"}
            for i in range(25)
        ]

        items = mgr.auto_populate_from_tool_run(eng.id, tr.id, "ap_testing", findings)
        assert len(items) == 25

    def test_auto_populate_preserves_engagement_link(self, db_session, make_user, make_client):
        user, eng, tr = self._setup(db_session, make_user, make_client)
        mgr = FollowUpItemsManager(db_session)

        findings = [{"description": "Linked finding", "severity": "high"}]
        items = mgr.auto_populate_from_tool_run(eng.id, tr.id, "ap_testing", findings)
        assert items[0].engagement_id == eng.id
        assert items[0].tool_run_id == tr.id


# ===========================================================================
# TestZeroStorageCompliance — Prohibited fields, narrative-only enforcement
# ===========================================================================


class TestZeroStorageCompliance:
    """Verify Zero-Storage compliance for follow-up items."""

    def test_no_account_number_column(self, db_engine):
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("follow_up_items")}
        assert "account_number" not in columns

    def test_no_amount_column(self, db_engine):
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("follow_up_items")}
        assert "amount" not in columns

    def test_no_transaction_id_column(self, db_engine):
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("follow_up_items")}
        assert "transaction_id" not in columns

    def test_no_vendor_name_column(self, db_engine):
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("follow_up_items")}
        assert "vendor_name" not in columns

    def test_no_employee_name_column(self, db_engine):
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("follow_up_items")}
        assert "employee_name" not in columns


# ===========================================================================
# TestFollowUpCascade — FK behaviors
# ===========================================================================


class TestFollowUpCascade:
    """ON DELETE CASCADE (engagement) and SET NULL (tool_run) behaviors."""

    def test_engagement_delete_cascades_follow_up_items(self, db_session, make_engagement, make_follow_up_item):
        eng = make_engagement()
        item = make_follow_up_item(engagement=eng)
        item_id = item.id

        db_session.delete(eng)
        db_session.flush()

        assert db_session.query(FollowUpItem).filter(FollowUpItem.id == item_id).first() is None

    def test_tool_run_delete_sets_null(self, db_session, make_engagement, make_tool_run, make_follow_up_item):
        eng = make_engagement()
        tr = make_tool_run(engagement=eng)
        item = make_follow_up_item(engagement=eng, tool_run=tr)

        db_session.delete(tr)
        db_session.flush()
        db_session.refresh(item)

        assert item.tool_run_id is None

    def test_follow_up_requires_valid_engagement(self, db_session):
        item = FollowUpItem(
            engagement_id=99999,
            description="Invalid engagement",
            tool_source="trial_balance",
            severity=FollowUpSeverity.LOW,
            disposition=FollowUpDisposition.NOT_REVIEWED,
        )
        db_session.add(item)
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    def test_multiple_items_cascade_on_engagement_delete(self, db_session, make_engagement, make_follow_up_item):
        eng = make_engagement()
        for i in range(5):
            make_follow_up_item(engagement=eng, description=f"Item {i}")

        eng_id = eng.id
        db_session.delete(eng)
        db_session.flush()

        remaining = db_session.query(FollowUpItem).filter(FollowUpItem.engagement_id == eng_id).count()
        assert remaining == 0


# ===========================================================================
# TestRouteRegistration — Routes registered in app
# ===========================================================================


class TestRouteRegistration:
    """Verify follow-up item routes are registered in the FastAPI app."""

    def test_follow_up_routes_registered(self):
        from main import app

        route_paths = {r.path for r in app.routes if hasattr(r, "path")}

        expected_paths = {
            "/engagements/{engagement_id}/follow-up-items",
            "/engagements/{engagement_id}/follow-up-items/summary",
            "/engagements/{engagement_id}/follow-up-items/my-items",
            "/engagements/{engagement_id}/follow-up-items/unassigned",
            "/follow-up-items/{item_id}",
        }
        for path in expected_paths:
            assert path in route_paths, f"Missing route: {path}"


# ===========================================================================
# TestAssignment — Sprint 113: assigned_to column, my_items, unassigned
# ===========================================================================


class TestAssignment:
    """Test follow-up item assignment feature."""

    def test_item_has_assigned_to_column(self, db_engine):
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("follow_up_items")}
        assert "assigned_to" in columns

    def test_new_item_assigned_to_is_null(self, make_follow_up_item):
        item = make_follow_up_item()
        assert item.assigned_to is None

    def test_to_dict_includes_assigned_to(self, make_follow_up_item):
        item = make_follow_up_item()
        d = item.to_dict()
        assert "assigned_to" in d
        assert d["assigned_to"] is None

    def test_assign_item_via_update(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="assign@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        updated = manager.update_item(
            user_id=user.id,
            item_id=item.id,
            assigned_to=user.id,
        )
        assert updated is not None
        assert updated.assigned_to == user.id

    def test_unassign_item(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="unassign@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        manager.update_item(user_id=user.id, item_id=item.id, assigned_to=user.id)
        updated = manager.update_item(user_id=user.id, item_id=item.id, assigned_to=None)
        assert updated is not None
        assert updated.assigned_to is None

    def test_assign_to_nonexistent_user_raises(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="assignbad@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="Assigned user not found"):
            manager.update_item(user_id=user.id, item_id=item.id, assigned_to=99999)

    def test_default_assigned_to_unchanged(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        """assigned_to=-1 (default) should leave the field unchanged."""
        user = make_user(email="nochange@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        # Assign first
        manager.update_item(user_id=user.id, item_id=item.id, assigned_to=user.id)
        # Update disposition only — assigned_to should remain
        updated = manager.update_item(
            user_id=user.id, item_id=item.id,
            disposition=FollowUpDisposition.INVESTIGATED_NO_ISSUE,
        )
        assert updated.assigned_to == user.id

    def test_get_my_items(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="myitems@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item1 = make_follow_up_item(engagement=eng, description="Mine")
        item2 = make_follow_up_item(engagement=eng, description="Not mine")

        manager = FollowUpItemsManager(db_session)
        manager.update_item(user_id=user.id, item_id=item1.id, assigned_to=user.id)

        my_items = manager.get_my_items(user_id=user.id, engagement_id=eng.id)
        assert len(my_items) == 1
        assert my_items[0].description == "Mine"

    def test_get_my_items_empty(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="myempty@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        my_items = manager.get_my_items(user_id=user.id, engagement_id=eng.id)
        assert len(my_items) == 0

    def test_get_my_items_wrong_user_raises(self, db_session, make_user, make_client, make_engagement):
        owner = make_user(email="myowner@test.com")
        other = make_user(email="myother@test.com")
        client = make_client(user=owner)
        eng = make_engagement(client=client)

        manager = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="not found or access denied"):
            manager.get_my_items(user_id=other.id, engagement_id=eng.id)

    def test_get_unassigned_items(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="unassigned@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item1 = make_follow_up_item(engagement=eng, description="Assigned")
        item2 = make_follow_up_item(engagement=eng, description="Free")

        manager = FollowUpItemsManager(db_session)
        manager.update_item(user_id=user.id, item_id=item1.id, assigned_to=user.id)

        unassigned = manager.get_unassigned_items(user_id=user.id, engagement_id=eng.id)
        assert len(unassigned) == 1
        assert unassigned[0].description == "Free"

    def test_get_unassigned_all_assigned(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="allassigned@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        manager.update_item(user_id=user.id, item_id=item.id, assigned_to=user.id)

        unassigned = manager.get_unassigned_items(user_id=user.id, engagement_id=eng.id)
        assert len(unassigned) == 0

    def test_get_unassigned_wrong_user_raises(self, db_session, make_user, make_client, make_engagement):
        owner = make_user(email="unowner@test.com")
        other = make_user(email="unother@test.com")
        client = make_client(user=owner)
        eng = make_engagement(client=client)

        manager = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="not found or access denied"):
            manager.get_unassigned_items(user_id=other.id, engagement_id=eng.id)

    def test_assigned_to_in_to_dict(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="dictassign@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        manager.update_item(user_id=user.id, item_id=item.id, assigned_to=user.id)

        d = item.to_dict()
        assert d["assigned_to"] == user.id

    def test_assignment_routes_registered(self):
        from main import app

        route_paths = {r.path for r in app.routes if hasattr(r, "path")}
        assert "/engagements/{engagement_id}/follow-up-items/my-items" in route_paths
        assert "/engagements/{engagement_id}/follow-up-items/unassigned" in route_paths
