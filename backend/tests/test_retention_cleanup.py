"""
Tests for Retention Cleanup — Packet 8

Validates:
- Deletes records older than cutoff
- Keeps records newer than cutoff
- Boundary behavior at exact cutoff timestamp
- Idempotent repeated runs (second call deletes nothing)
- run_retention_cleanup aggregates both tables
- Startup lifespan integration (import wiring)
"""

import sys
from datetime import datetime, UTC, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from retention_cleanup import (
    cleanup_expired_activity_logs,
    cleanup_expired_diagnostic_summaries,
    run_retention_cleanup,
    RETENTION_DAYS,
)
from models import ActivityLog, DiagnosticSummary


# =============================================================================
# Helpers
# =============================================================================


def _make_activity_log(db_session, user, *, timestamp=None):
    """Insert an ActivityLog row with a given timestamp."""
    log = ActivityLog(
        user_id=user.id,
        filename_hash="abcdef1234567890",
        record_count=10,
        total_debits=1000.0,
        total_credits=1000.0,
        materiality_threshold=100.0,
        was_balanced=True,
    )
    db_session.add(log)
    db_session.flush()
    if timestamp is not None:
        # Direct UPDATE to bypass default timestamp
        db_session.execute(
            ActivityLog.__table__.update()
            .where(ActivityLog.id == log.id)
            .values(timestamp=timestamp)
        )
        db_session.flush()
        db_session.expire(log)
    return log


def _make_diagnostic_summary(db_session, user, client, *, timestamp=None):
    """Insert a DiagnosticSummary row with a given timestamp."""
    ds = DiagnosticSummary(
        client_id=client.id,
        user_id=user.id,
    )
    db_session.add(ds)
    db_session.flush()
    if timestamp is not None:
        db_session.execute(
            DiagnosticSummary.__table__.update()
            .where(DiagnosticSummary.id == ds.id)
            .values(timestamp=timestamp)
        )
        db_session.flush()
        db_session.expire(ds)
    return ds


# =============================================================================
# Activity Log Retention
# =============================================================================


class TestActivityLogCleanup:
    """Retention cleanup for activity_logs table."""

    def test_deletes_old_records(self, db_session, make_user):
        user = make_user(email="ret_al_old@test.com")
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 30)
        _make_activity_log(db_session, user, timestamp=old_ts)

        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
        deleted = cleanup_expired_activity_logs(db_session, cutoff=cutoff)
        assert deleted == 1
        assert db_session.query(ActivityLog).filter_by(user_id=user.id).count() == 0

    def test_keeps_recent_records(self, db_session, make_user):
        user = make_user(email="ret_al_new@test.com")
        recent_ts = datetime.now(UTC) - timedelta(days=10)
        _make_activity_log(db_session, user, timestamp=recent_ts)

        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
        deleted = cleanup_expired_activity_logs(db_session, cutoff=cutoff)
        assert deleted == 0
        assert db_session.query(ActivityLog).filter_by(user_id=user.id).count() == 1

    def test_boundary_exact_cutoff_kept(self, db_session, make_user):
        """Record at exactly the cutoff timestamp should NOT be deleted (< cutoff, not <=)."""
        user = make_user(email="ret_al_boundary@test.com")
        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
        _make_activity_log(db_session, user, timestamp=cutoff)

        deleted = cleanup_expired_activity_logs(db_session, cutoff=cutoff)
        assert deleted == 0

    def test_idempotent_repeated_run(self, db_session, make_user):
        """Second cleanup run with same cutoff deletes nothing."""
        user = make_user(email="ret_al_idem@test.com")
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 30)
        _make_activity_log(db_session, user, timestamp=old_ts)

        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
        first = cleanup_expired_activity_logs(db_session, cutoff=cutoff)
        assert first == 1
        second = cleanup_expired_activity_logs(db_session, cutoff=cutoff)
        assert second == 0

    def test_mixed_old_and_new(self, db_session, make_user):
        """Only old records are deleted; recent ones survive."""
        user = make_user(email="ret_al_mixed@test.com")
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 60)
        recent_ts = datetime.now(UTC) - timedelta(days=5)
        _make_activity_log(db_session, user, timestamp=old_ts)
        _make_activity_log(db_session, user, timestamp=recent_ts)

        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
        deleted = cleanup_expired_activity_logs(db_session, cutoff=cutoff)
        assert deleted == 1
        assert db_session.query(ActivityLog).filter_by(user_id=user.id).count() == 1


# =============================================================================
# Diagnostic Summary Retention
# =============================================================================


class TestDiagnosticSummaryCleanup:
    """Retention cleanup for diagnostic_summaries table."""

    def test_deletes_old_records(self, db_session, make_user, make_client):
        user = make_user(email="ret_ds_old@test.com")
        client = make_client(user=user)
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 30)
        _make_diagnostic_summary(db_session, user, client, timestamp=old_ts)

        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
        deleted = cleanup_expired_diagnostic_summaries(db_session, cutoff=cutoff)
        assert deleted == 1

    def test_keeps_recent_records(self, db_session, make_user, make_client):
        user = make_user(email="ret_ds_new@test.com")
        client = make_client(user=user)
        recent_ts = datetime.now(UTC) - timedelta(days=10)
        _make_diagnostic_summary(db_session, user, client, timestamp=recent_ts)

        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
        deleted = cleanup_expired_diagnostic_summaries(db_session, cutoff=cutoff)
        assert deleted == 0

    def test_boundary_exact_cutoff_kept(self, db_session, make_user, make_client):
        user = make_user(email="ret_ds_boundary@test.com")
        client = make_client(user=user)
        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
        _make_diagnostic_summary(db_session, user, client, timestamp=cutoff)

        deleted = cleanup_expired_diagnostic_summaries(db_session, cutoff=cutoff)
        assert deleted == 0

    def test_idempotent_repeated_run(self, db_session, make_user, make_client):
        user = make_user(email="ret_ds_idem@test.com")
        client = make_client(user=user)
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 30)
        _make_diagnostic_summary(db_session, user, client, timestamp=old_ts)

        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
        first = cleanup_expired_diagnostic_summaries(db_session, cutoff=cutoff)
        assert first == 1
        second = cleanup_expired_diagnostic_summaries(db_session, cutoff=cutoff)
        assert second == 0


# =============================================================================
# Combined run_retention_cleanup
# =============================================================================


class TestRunRetentionCleanup:
    """Test the combined run_retention_cleanup entry point."""

    def test_returns_counts_for_both_tables(self, db_session, make_user, make_client):
        user = make_user(email="ret_combined@test.com")
        client = make_client(user=user)
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 30)
        _make_activity_log(db_session, user, timestamp=old_ts)
        _make_diagnostic_summary(db_session, user, client, timestamp=old_ts)

        results = run_retention_cleanup(db_session)
        assert results["activity_logs"] == 1
        assert results["diagnostic_summaries"] == 1

    def test_zero_counts_when_nothing_expired(self, db_session, make_user, make_client):
        user = make_user(email="ret_combined_none@test.com")
        client = make_client(user=user)
        recent_ts = datetime.now(UTC) - timedelta(days=10)
        _make_activity_log(db_session, user, timestamp=recent_ts)
        _make_diagnostic_summary(db_session, user, client, timestamp=recent_ts)

        results = run_retention_cleanup(db_session)
        assert results["activity_logs"] == 0
        assert results["diagnostic_summaries"] == 0

    def test_idempotent(self, db_session, make_user, make_client):
        user = make_user(email="ret_combined_idem@test.com")
        client = make_client(user=user)
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 30)
        _make_activity_log(db_session, user, timestamp=old_ts)
        _make_diagnostic_summary(db_session, user, client, timestamp=old_ts)

        first = run_retention_cleanup(db_session)
        assert sum(first.values()) == 2
        second = run_retention_cleanup(db_session)
        assert sum(second.values()) == 0


# =============================================================================
# Configuration
# =============================================================================


class TestRetentionConfig:
    """Verify retention window is configurable."""

    def test_default_retention_days(self):
        assert RETENTION_DAYS == 365

    def test_retention_days_is_positive_int(self):
        assert isinstance(RETENTION_DAYS, int)
        assert RETENTION_DAYS > 0

    def test_env_example_documents_retention(self):
        env_path = Path(__file__).parent.parent / ".env.example"
        source = env_path.read_text()
        assert "RETENTION_DAYS" in source


# =============================================================================
# Startup Integration
# =============================================================================


class TestStartupIntegration:
    """Verify retention cleanup is wired into app lifespan."""

    def test_run_retention_cleanup_importable_from_module(self):
        """The function must be importable for main.py to use it."""
        from retention_cleanup import run_retention_cleanup
        assert callable(run_retention_cleanup)

    def test_main_imports_retention_cleanup(self):
        """main.py must import and call run_retention_cleanup in lifespan."""
        import ast
        main_path = Path(__file__).parent.parent / "main.py"
        source = main_path.read_text()
        assert "run_retention_cleanup" in source

        tree = ast.parse(source)
        found_import = False
        found_call = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "retention_cleanup":
                for alias in node.names:
                    if alias.name == "run_retention_cleanup":
                        found_import = True
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "run_retention_cleanup":
                    found_call = True
        assert found_import, "main.py must import run_retention_cleanup"
        assert found_call, "main.py must call run_retention_cleanup()"
