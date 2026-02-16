"""
Tests for Phase X Engagement Layer: Models, Manager, and Route Registration.

Sprint 97: Engagement Model + Materiality Cascade
~50 tests covering schema, CRUD, cascade, validation, materiality, tool runs.
"""

import sys
from datetime import datetime, UTC, timedelta
from pathlib import Path

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, str(Path(__file__).parent.parent))

from engagement_model import (
    Engagement,
    ToolRun,
    EngagementStatus,
    MaterialityBasis,
    ToolName,
    ToolRunStatus,
)
from engagement_manager import EngagementManager
from models import User, Client


# ===========================================================================
# TestEngagementSchema — Model structure, enums, to_dict, guardrail checks
# ===========================================================================


class TestEngagementSchema:
    """Verify model structure and enum definitions."""

    def test_engagement_status_values(self):
        assert EngagementStatus.ACTIVE.value == "active"
        assert EngagementStatus.ARCHIVED.value == "archived"

    def test_materiality_basis_values(self):
        assert MaterialityBasis.REVENUE.value == "revenue"
        assert MaterialityBasis.ASSETS.value == "assets"
        assert MaterialityBasis.MANUAL.value == "manual"

    def test_tool_name_has_all_tools(self):
        expected = {
            "trial_balance", "multi_period", "journal_entry_testing",
            "ap_testing", "bank_reconciliation", "payroll_testing",
            "three_way_match", "revenue_testing", "ar_aging",
            "fixed_asset_testing", "inventory_testing", "statistical_sampling",
        }
        actual = {t.value for t in ToolName}
        assert actual == expected

    def test_tool_run_status_values(self):
        assert ToolRunStatus.COMPLETED.value == "completed"
        assert ToolRunStatus.FAILED.value == "failed"

    def test_engagement_to_dict(self, make_engagement):
        eng = make_engagement(materiality_amount=50000.0, materiality_basis=MaterialityBasis.REVENUE)
        d = eng.to_dict()
        assert d["id"] == eng.id
        assert d["client_id"] == eng.client_id
        assert d["status"] == "active"
        assert d["materiality_amount"] == 50000.0
        assert d["materiality_basis"] == "revenue"
        assert d["performance_materiality_factor"] == 0.75
        assert d["trivial_threshold_factor"] == 0.05
        assert "period_start" in d
        assert "period_end" in d
        assert "created_by" in d

    def test_engagement_table_has_no_prohibited_columns(self, db_engine):
        """Guardrail: no risk_level, audit_opinion, or control_effectiveness columns."""
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("engagements")}
        prohibited = {"risk_level", "audit_opinion", "control_effectiveness"}
        assert columns.isdisjoint(prohibited), f"Prohibited columns found: {columns & prohibited}"

    def test_tool_run_to_dict(self, db_session, make_engagement):
        eng = make_engagement()
        tr = ToolRun(
            engagement_id=eng.id,
            tool_name=ToolName.AP_TESTING,
            run_number=1,
            status=ToolRunStatus.COMPLETED,
            composite_score=85.5,
        )
        db_session.add(tr)
        db_session.flush()
        d = tr.to_dict()
        assert d["tool_name"] == "ap_testing"
        assert d["run_number"] == 1
        assert d["status"] == "completed"
        assert d["composite_score"] == 85.5

    def test_engagement_repr(self, make_engagement):
        eng = make_engagement()
        r = repr(eng)
        assert "Engagement" in r
        assert str(eng.id) in r


# ===========================================================================
# TestEngagementCRUD — Create/Read/Update/Archive, ownership, filtering
# ===========================================================================


class TestEngagementCRUD:
    """CRUD operations via EngagementManager."""

    def test_create_engagement(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)

        eng = mgr.create_engagement(
            user_id=user.id,
            client_id=client.id,
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 12, 31, tzinfo=UTC),
        )

        assert eng.id is not None
        assert eng.client_id == client.id
        assert eng.created_by == user.id
        assert eng.status == EngagementStatus.ACTIVE

    def test_get_engagement(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user_id=user.id,
            client_id=client.id,
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 12, 31, tzinfo=UTC),
        )
        fetched = mgr.get_engagement(user.id, eng.id)
        assert fetched is not None
        assert fetched.id == eng.id

    def test_get_engagement_wrong_user_returns_none(self, db_session, make_user, make_client):
        user1 = make_user(email="u1@test.com")
        user2 = make_user(email="u2@test.com")
        client = make_client(user=user1)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user_id=user1.id,
            client_id=client.id,
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 12, 31, tzinfo=UTC),
        )
        assert mgr.get_engagement(user2.id, eng.id) is None

    def test_list_engagements(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        for i in range(3):
            mgr.create_engagement(
                user_id=user.id,
                client_id=client.id,
                period_start=datetime(2025, 1, 1, tzinfo=UTC),
                period_end=datetime(2025, 12, 31, tzinfo=UTC),
            )
        engs, total = mgr.get_engagements_for_user(user.id)
        assert total == 3
        assert len(engs) == 3

    def test_list_engagements_filter_by_client(self, db_session, make_user, make_client):
        user = make_user()
        c1 = make_client(name="Client A", user=user)
        c2 = make_client(name="Client B", user=user)
        mgr = EngagementManager(db_session)
        mgr.create_engagement(user.id, c1.id, datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC))
        mgr.create_engagement(user.id, c2.id, datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC))
        engs, total = mgr.get_engagements_for_user(user.id, client_id=c1.id)
        assert total == 1
        assert engs[0].client_id == c1.id

    def test_list_engagements_filter_by_status(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        mgr.create_engagement(user.id, client.id, datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC))
        eng2 = mgr.create_engagement(user.id, client.id, datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 12, 31, tzinfo=UTC))
        mgr.archive_engagement(user.id, eng2.id)
        engs, total = mgr.get_engagements_for_user(user.id, status=EngagementStatus.ACTIVE)
        assert total == 1

    def test_list_engagements_pagination(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        for i in range(5):
            mgr.create_engagement(user.id, client.id, datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC))
        engs, total = mgr.get_engagements_for_user(user.id, limit=2, offset=0)
        assert total == 5
        assert len(engs) == 2

    def test_update_engagement(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(user.id, client.id, datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC))
        updated = mgr.update_engagement(user.id, eng.id, materiality_amount=100000.0)
        assert updated.materiality_amount == 100000.0

    def test_update_engagement_not_found(self, db_session, make_user):
        user = make_user()
        mgr = EngagementManager(db_session)
        result = mgr.update_engagement(user.id, 99999, materiality_amount=1.0)
        assert result is None

    def test_archive_engagement(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(user.id, client.id, datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC))
        archived = mgr.archive_engagement(user.id, eng.id)
        assert archived.status == EngagementStatus.ARCHIVED

    def test_archive_nonexistent_returns_none(self, db_session, make_user):
        user = make_user()
        mgr = EngagementManager(db_session)
        assert mgr.archive_engagement(user.id, 99999) is None

    def test_ownership_isolation_on_create(self, db_session, make_user, make_client):
        user1 = make_user(email="owner@test.com")
        user2 = make_user(email="intruder@test.com")
        client = make_client(user=user1)
        mgr = EngagementManager(db_session)
        with pytest.raises(ValueError, match="Client not found"):
            mgr.create_engagement(
                user_id=user2.id,
                client_id=client.id,
                period_start=datetime(2025, 1, 1, tzinfo=UTC),
                period_end=datetime(2025, 12, 31, tzinfo=UTC),
            )


# ===========================================================================
# TestEngagementCascade — FK behaviors (RESTRICT + CASCADE)
# ===========================================================================


class TestEngagementCascade:
    """ON DELETE RESTRICT (client) and ON DELETE CASCADE (tool_runs)."""

    def test_client_delete_blocked_when_engagement_exists(self, db_session, make_user, make_client):
        """Client deletion should fail (RESTRICT) when engagements exist."""
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        mgr.create_engagement(user.id, client.id, datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC))

        # Attempting to delete the client should raise
        db_session.delete(client)
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    def test_engagement_delete_cascades_tool_runs(self, db_session, make_engagement):
        """Deleting engagement should cascade-delete its tool runs."""
        eng = make_engagement()
        tr = ToolRun(
            engagement_id=eng.id,
            tool_name=ToolName.TRIAL_BALANCE,
            run_number=1,
            status=ToolRunStatus.COMPLETED,
        )
        db_session.add(tr)
        db_session.flush()
        tr_id = tr.id

        db_session.delete(eng)
        db_session.flush()

        assert db_session.query(ToolRun).filter(ToolRun.id == tr_id).first() is None

    def test_tool_run_requires_valid_engagement(self, db_session):
        """Tool run with invalid engagement_id should fail FK constraint."""
        tr = ToolRun(
            engagement_id=99999,
            tool_name=ToolName.AP_TESTING,
            run_number=1,
            status=ToolRunStatus.COMPLETED,
        )
        db_session.add(tr)
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    def test_engagement_requires_valid_client(self, db_session, make_user):
        """Engagement with invalid client_id should fail FK constraint."""
        user = make_user()
        eng = Engagement(
            client_id=99999,
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 12, 31, tzinfo=UTC),
            created_by=user.id,
        )
        db_session.add(eng)
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    def test_multiple_tool_runs_survive_independent(self, db_session, make_engagement):
        """Multiple tool runs for same engagement are independent."""
        eng = make_engagement()
        for tool in [ToolName.TRIAL_BALANCE, ToolName.AP_TESTING, ToolName.PAYROLL_TESTING]:
            db_session.add(ToolRun(
                engagement_id=eng.id, tool_name=tool, run_number=1,
                status=ToolRunStatus.COMPLETED,
            ))
        db_session.flush()
        runs = db_session.query(ToolRun).filter(ToolRun.engagement_id == eng.id).all()
        assert len(runs) == 3

    def test_engagement_relationship_to_tool_runs(self, db_session, make_engagement):
        eng = make_engagement()
        db_session.add(ToolRun(
            engagement_id=eng.id, tool_name=ToolName.AP_TESTING,
            run_number=1, status=ToolRunStatus.COMPLETED,
        ))
        db_session.flush()
        db_session.refresh(eng)
        assert len(eng.tool_runs) == 1

    def test_client_delete_works_without_engagements(self, db_session, make_user, make_client):
        """Client without engagements can be deleted normally."""
        user = make_user()
        client = make_client(user=user)
        db_session.delete(client)
        db_session.flush()  # Should not raise

    def test_cascade_deletes_all_runs(self, db_session, make_engagement):
        """All tool runs removed when engagement deleted."""
        eng = make_engagement()
        for i in range(5):
            db_session.add(ToolRun(
                engagement_id=eng.id, tool_name=ToolName.JOURNAL_ENTRY_TESTING,
                run_number=i + 1, status=ToolRunStatus.COMPLETED,
            ))
        db_session.flush()
        eng_id = eng.id
        db_session.delete(eng)
        db_session.flush()
        remaining = db_session.query(ToolRun).filter(ToolRun.engagement_id == eng_id).count()
        assert remaining == 0


# ===========================================================================
# TestEngagementValidation — Date ranges, status transitions, constraints
# ===========================================================================


class TestEngagementValidation:
    """Validation rules in EngagementManager."""

    def test_period_end_before_start_rejected(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        with pytest.raises(ValueError, match="period_end must be after period_start"):
            mgr.create_engagement(
                user.id, client.id,
                period_start=datetime(2025, 12, 31, tzinfo=UTC),
                period_end=datetime(2025, 1, 1, tzinfo=UTC),
            )

    def test_period_end_equals_start_rejected(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        same = datetime(2025, 6, 15, tzinfo=UTC)
        with pytest.raises(ValueError, match="period_end must be after period_start"):
            mgr.create_engagement(user.id, client.id, period_start=same, period_end=same)

    def test_negative_materiality_percentage_rejected(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        with pytest.raises(ValueError, match="materiality_percentage cannot be negative"):
            mgr.create_engagement(
                user.id, client.id,
                datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
                materiality_percentage=-1.0,
            )

    def test_negative_materiality_amount_rejected(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        with pytest.raises(ValueError, match="materiality_amount cannot be negative"):
            mgr.create_engagement(
                user.id, client.id,
                datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
                materiality_amount=-500.0,
            )

    def test_pm_factor_out_of_range_rejected(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        with pytest.raises(ValueError, match="performance_materiality_factor"):
            mgr.create_engagement(
                user.id, client.id,
                datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
                performance_materiality_factor=0.0,
            )

    def test_trivial_factor_out_of_range_rejected(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        with pytest.raises(ValueError, match="trivial_threshold_factor"):
            mgr.create_engagement(
                user.id, client.id,
                datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
                trivial_threshold_factor=1.5,
            )

    def test_update_invalid_dates_rejected(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        with pytest.raises(ValueError, match="period_end must be after period_start"):
            mgr.update_engagement(user.id, eng.id, period_end=datetime(2024, 1, 1, tzinfo=UTC))


# ===========================================================================
# TestMaterialityCascade — Revenue/asset/manual basis, PM, trivial
# ===========================================================================


class TestMaterialityCascade:
    """Materiality computation from engagement parameters."""

    def test_basic_cascade(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
            materiality_amount=100000.0,
        )
        result = mgr.compute_materiality(eng)
        assert result["overall_materiality"] == 100000.0
        assert result["performance_materiality"] == 75000.0
        assert result["trivial_threshold"] == 5000.0

    def test_custom_pm_factor(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
            materiality_amount=200000.0,
            performance_materiality_factor=0.50,
        )
        result = mgr.compute_materiality(eng)
        assert result["performance_materiality"] == 100000.0

    def test_custom_trivial_factor(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
            materiality_amount=200000.0,
            trivial_threshold_factor=0.10,
        )
        result = mgr.compute_materiality(eng)
        assert result["trivial_threshold"] == 20000.0

    def test_zero_materiality(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        result = mgr.compute_materiality(eng)
        assert result["overall_materiality"] == 0.0
        assert result["performance_materiality"] == 0.0
        assert result["trivial_threshold"] == 0.0

    def test_revenue_basis_stored(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
            materiality_basis=MaterialityBasis.REVENUE,
            materiality_percentage=1.5,
            materiality_amount=150000.0,
        )
        result = mgr.compute_materiality(eng)
        assert result["materiality_basis"] == "revenue"
        assert result["materiality_percentage"] == 1.5

    def test_assets_basis_stored(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
            materiality_basis=MaterialityBasis.ASSETS,
            materiality_amount=500000.0,
        )
        result = mgr.compute_materiality(eng)
        assert result["materiality_basis"] == "assets"

    def test_manual_basis_stored(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
            materiality_basis=MaterialityBasis.MANUAL,
            materiality_amount=75000.0,
        )
        result = mgr.compute_materiality(eng)
        assert result["materiality_basis"] == "manual"

    def test_cascade_rounding(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
            materiality_amount=333333.33,
        )
        result = mgr.compute_materiality(eng)
        assert result["performance_materiality"] == 250000.0  # 333333.33 * 0.75 = 249999.9975 → 250000.0
        assert result["trivial_threshold"] == 16666.67  # 333333.33 * 0.05 = 16666.6665 → 16666.67

    def test_materiality_factors_in_response(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
            materiality_amount=100000.0,
            performance_materiality_factor=0.60,
            trivial_threshold_factor=0.03,
        )
        result = mgr.compute_materiality(eng)
        assert result["performance_materiality_factor"] == 0.60
        assert result["trivial_threshold_factor"] == 0.03

    def test_update_materiality_recalculates(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
            materiality_amount=100000.0,
        )
        mgr.update_engagement(user.id, eng.id, materiality_amount=200000.0)
        db_session.refresh(eng)
        result = mgr.compute_materiality(eng)
        assert result["overall_materiality"] == 200000.0
        assert result["performance_materiality"] == 150000.0


# ===========================================================================
# TestToolRunRecording — Auto-increment, per-tool independence, to_dict
# ===========================================================================


class TestToolRunRecording:
    """Tool run recording via EngagementManager."""

    def test_record_first_run(self, db_session, make_engagement):
        eng = make_engagement()
        mgr = EngagementManager(db_session)
        tr = mgr.record_tool_run(eng.id, ToolName.TRIAL_BALANCE, ToolRunStatus.COMPLETED)
        assert tr.run_number == 1
        assert tr.tool_name == ToolName.TRIAL_BALANCE

    def test_auto_increment_run_number(self, db_session, make_engagement):
        eng = make_engagement()
        mgr = EngagementManager(db_session)
        tr1 = mgr.record_tool_run(eng.id, ToolName.AP_TESTING, ToolRunStatus.COMPLETED)
        tr2 = mgr.record_tool_run(eng.id, ToolName.AP_TESTING, ToolRunStatus.COMPLETED)
        tr3 = mgr.record_tool_run(eng.id, ToolName.AP_TESTING, ToolRunStatus.FAILED)
        assert tr1.run_number == 1
        assert tr2.run_number == 2
        assert tr3.run_number == 3

    def test_per_tool_independent_numbering(self, db_session, make_engagement):
        eng = make_engagement()
        mgr = EngagementManager(db_session)
        ap1 = mgr.record_tool_run(eng.id, ToolName.AP_TESTING, ToolRunStatus.COMPLETED)
        je1 = mgr.record_tool_run(eng.id, ToolName.JOURNAL_ENTRY_TESTING, ToolRunStatus.COMPLETED)
        ap2 = mgr.record_tool_run(eng.id, ToolName.AP_TESTING, ToolRunStatus.COMPLETED)
        assert ap1.run_number == 1
        assert je1.run_number == 1
        assert ap2.run_number == 2

    def test_composite_score_stored(self, db_session, make_engagement):
        eng = make_engagement()
        mgr = EngagementManager(db_session)
        tr = mgr.record_tool_run(eng.id, ToolName.AP_TESTING, ToolRunStatus.COMPLETED, composite_score=92.5)
        assert tr.composite_score == 92.5

    def test_composite_score_none_for_non_testing_tools(self, db_session, make_engagement):
        eng = make_engagement()
        mgr = EngagementManager(db_session)
        tr = mgr.record_tool_run(eng.id, ToolName.BANK_RECONCILIATION, ToolRunStatus.COMPLETED)
        assert tr.composite_score is None

    def test_failed_run_recorded(self, db_session, make_engagement):
        eng = make_engagement()
        mgr = EngagementManager(db_session)
        tr = mgr.record_tool_run(eng.id, ToolName.PAYROLL_TESTING, ToolRunStatus.FAILED)
        assert tr.status == ToolRunStatus.FAILED

    def test_get_tool_runs_ordered_by_run_at(self, db_session, make_engagement):
        eng = make_engagement()
        mgr = EngagementManager(db_session)
        mgr.record_tool_run(eng.id, ToolName.TRIAL_BALANCE, ToolRunStatus.COMPLETED)
        mgr.record_tool_run(eng.id, ToolName.AP_TESTING, ToolRunStatus.COMPLETED)
        mgr.record_tool_run(eng.id, ToolName.PAYROLL_TESTING, ToolRunStatus.COMPLETED)
        runs = mgr.get_tool_runs(eng.id)
        assert len(runs) == 3
        # Most recent first (desc order)
        for i in range(len(runs) - 1):
            assert runs[i].run_at >= runs[i + 1].run_at

    def test_get_tool_runs_empty_engagement(self, db_session, make_engagement):
        eng = make_engagement()
        mgr = EngagementManager(db_session)
        runs = mgr.get_tool_runs(eng.id)
        assert runs == []


# ===========================================================================
# TestRouteRegistration — Routes registered in app
# ===========================================================================


class TestRouteRegistration:
    """Verify engagement routes are registered in the FastAPI app."""

    def test_engagement_routes_registered(self):
        from main import app

        route_paths = {r.path for r in app.routes if hasattr(r, "path")}

        expected_paths = {
            "/engagements",
            "/engagements/{engagement_id}",
            "/engagements/{engagement_id}/materiality",
            "/engagements/{engagement_id}/tool-runs",
        }
        for path in expected_paths:
            assert path in route_paths, f"Missing route: {path}"
