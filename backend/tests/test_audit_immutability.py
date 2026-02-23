"""
Tests for Audit History Immutability — Phase XLVI, Sprint 349.

Validates:
1. ORM deletion guard blocks db.delete() on protected models
2. ORM deletion guard allows db.delete() on non-protected models
3. Soft-delete behavior (archived_at/archived_by/archive_reason set correctly)
4. Read-path exclusion (archived records invisible to queries)
5. Immutability proof (archived records physically exist, row count never decreases)
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from follow_up_items_model import (
    FollowUpItemComment,
)
from models import ActivityLog, DiagnosticSummary, RefreshToken, User
from retention_cleanup import (
    RETENTION_DAYS,
    cleanup_expired_activity_logs,
    cleanup_expired_diagnostic_summaries,
)
from shared.soft_delete import (
    AuditImmutabilityError,
    active_only,
    soft_delete,
    soft_delete_bulk,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_activity_log(db_session, user, *, timestamp=None):
    """Insert an ActivityLog row with an optional backdated timestamp."""
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
        db_session.execute(
            ActivityLog.__table__.update()
            .where(ActivityLog.id == log.id)
            .values(timestamp=timestamp)
        )
        db_session.flush()
        db_session.expire(log)
    return log


def _make_diagnostic_summary(db_session, user, client, *, timestamp=None):
    """Insert a DiagnosticSummary row with an optional backdated timestamp."""
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
# 1. ORM Guard Tests — db.delete() blocked on protected models
# =============================================================================


class TestOrmDeletionGuard:
    """Verify db.delete() raises AuditImmutabilityError on protected models."""

    def test_delete_activity_log_blocked(self, db_session, make_user):
        user = make_user(email="guard_al@test.com")
        log = _make_activity_log(db_session, user)
        with pytest.raises(AuditImmutabilityError, match="ActivityLog"):
            db_session.delete(log)
            db_session.flush()

    def test_delete_diagnostic_summary_blocked(self, db_session, make_user, make_client):
        user = make_user(email="guard_ds@test.com")
        client = make_client(user=user)
        ds = _make_diagnostic_summary(db_session, user, client)
        with pytest.raises(AuditImmutabilityError, match="DiagnosticSummary"):
            db_session.delete(ds)
            db_session.flush()

    def test_delete_tool_run_blocked(self, db_session, make_tool_run):
        tr = make_tool_run()
        with pytest.raises(AuditImmutabilityError, match="ToolRun"):
            db_session.delete(tr)
            db_session.flush()

    def test_delete_follow_up_item_blocked(self, db_session, make_follow_up_item):
        item = make_follow_up_item()
        with pytest.raises(AuditImmutabilityError, match="FollowUpItem"):
            db_session.delete(item)
            db_session.flush()

    def test_delete_follow_up_item_comment_blocked(self, db_session, make_comment):
        comment = make_comment()
        with pytest.raises(AuditImmutabilityError, match="FollowUpItemComment"):
            db_session.delete(comment)
            db_session.flush()

    def test_delete_non_protected_user_allowed(self, db_session):
        """Non-protected models (User) can still be physically deleted."""
        user = User(
            email="guard_unprotected@test.com",
            hashed_password="$2b$12$fakehashvalue",
        )
        db_session.add(user)
        db_session.flush()
        db_session.delete(user)
        db_session.flush()  # Should NOT raise
        assert db_session.query(User).filter_by(email="guard_unprotected@test.com").first() is None

    def test_delete_refresh_token_allowed(self, db_session, make_refresh_token):
        """Security tokens can still be physically deleted."""
        _, rt = make_refresh_token()
        rt_id = rt.id
        db_session.delete(rt)
        db_session.flush()  # Should NOT raise
        assert db_session.query(RefreshToken).filter_by(id=rt_id).first() is None


# =============================================================================
# 2. Soft-Delete Behavior Tests
# =============================================================================


class TestSoftDeleteBehavior:
    """Verify soft_delete and soft_delete_bulk set correct fields."""

    def test_soft_delete_sets_fields(self, db_session, make_user):
        user = make_user(email="sd_fields@test.com")
        log = _make_activity_log(db_session, user)
        assert log.archived_at is None

        soft_delete(db_session, log, user.id, "test_reason")
        db_session.expire(log)

        assert log.archived_at is not None
        assert log.archived_by == user.id
        assert log.archive_reason == "test_reason"

    def test_soft_delete_bulk_sets_fields(self, db_session, make_user):
        user = make_user(email="sd_bulk@test.com")
        _make_activity_log(db_session, user)
        _make_activity_log(db_session, user)

        count = soft_delete_bulk(
            db_session,
            db_session.query(ActivityLog).filter(
                ActivityLog.user_id == user.id,
                ActivityLog.archived_at.is_(None),
            ),
            user_id=user.id,
            reason="bulk_test",
        )
        assert count == 2

        logs = db_session.query(ActivityLog).filter_by(user_id=user.id).all()
        for log in logs:
            assert log.archived_at is not None
            assert log.archived_by == user.id
            assert log.archive_reason == "bulk_test"

    def test_soft_delete_bulk_system_no_user(self, db_session, make_user, make_client):
        """System retention archival sets archived_by=NULL."""
        user = make_user(email="sd_sys@test.com")
        client = make_client(user=user)
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 30)
        _make_diagnostic_summary(db_session, user, client, timestamp=old_ts)

        count = cleanup_expired_diagnostic_summaries(db_session)
        assert count == 1

        ds = db_session.query(DiagnosticSummary).filter_by(user_id=user.id).first()
        assert ds.archived_at is not None
        assert ds.archived_by is None  # System retention — no user
        assert ds.archive_reason == "retention_policy"

    def test_follow_up_item_delete_archives_children(
        self, db_session, make_user, make_engagement, make_follow_up_item, make_comment
    ):
        """Archiving a follow-up item also archives its child comments."""
        from follow_up_items_manager import FollowUpItemsManager

        user = make_user(email="sd_cascade@test.com")
        engagement = make_engagement(user=user)
        item = make_follow_up_item(engagement=engagement)
        comment = make_comment(follow_up_item=item, user=user)
        comment_id = comment.id

        manager = FollowUpItemsManager(db_session)
        result = manager.delete_item(user.id, item.id)
        assert result is True

        # Item archived
        db_session.expire(item)
        assert item.archived_at is not None
        assert item.archive_reason == "user_deletion"

        # Child comment also archived
        db_session.expire(comment)
        c = db_session.query(FollowUpItemComment).filter_by(id=comment_id).first()
        assert c.archived_at is not None
        assert c.archive_reason == "parent_archived"

    def test_comment_delete_archives_replies(
        self, db_session, make_user, make_engagement, make_follow_up_item, make_comment
    ):
        """Archiving a comment also archives its child replies."""
        from follow_up_items_manager import FollowUpItemsManager

        user = make_user(email="sd_reply@test.com")
        engagement = make_engagement(user=user)
        item = make_follow_up_item(engagement=engagement)
        parent_comment = make_comment(follow_up_item=item, user=user, comment_text="parent")
        reply = make_comment(
            follow_up_item=item,
            user=user,
            comment_text="reply",
            parent_comment_id=parent_comment.id,
        )
        reply_id = reply.id

        manager = FollowUpItemsManager(db_session)
        result = manager.delete_comment(user.id, parent_comment.id)
        assert result is True

        # Parent archived
        db_session.expire(parent_comment)
        assert parent_comment.archived_at is not None
        assert parent_comment.archive_reason == "user_deletion"

        # Reply also archived
        r = db_session.query(FollowUpItemComment).filter_by(id=reply_id).first()
        assert r.archived_at is not None
        assert r.archive_reason == "parent_archived"

    def test_activity_clear_archives_all(self, db_session, make_user):
        """Activity clear endpoint archives all records for the user."""
        user = make_user(email="sd_clear@test.com")
        _make_activity_log(db_session, user)
        _make_activity_log(db_session, user)

        count = soft_delete_bulk(
            db_session,
            db_session.query(ActivityLog).filter(
                ActivityLog.user_id == user.id,
                ActivityLog.archived_at.is_(None),
            ),
            user_id=user.id,
            reason="user_clear_history",
        )
        assert count == 2

        active = db_session.query(ActivityLog).filter(
            ActivityLog.user_id == user.id,
            ActivityLog.archived_at.is_(None),
        ).count()
        assert active == 0

    def test_retention_archives_old_activity_logs(self, db_session, make_user):
        """Retention cleanup archives (not deletes) old activity logs."""
        user = make_user(email="sd_ret_al@test.com")
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 30)
        _make_activity_log(db_session, user, timestamp=old_ts)

        archived = cleanup_expired_activity_logs(db_session)
        assert archived == 1

        # Record still physically exists
        total = db_session.query(ActivityLog).filter_by(user_id=user.id).count()
        assert total == 1

        log = db_session.query(ActivityLog).filter_by(user_id=user.id).first()
        assert log.archived_at is not None
        assert log.archive_reason == "retention_policy"


# =============================================================================
# 3. Read Path Exclusion Tests
# =============================================================================


class TestReadPathExclusion:
    """Verify archived records are excluded from standard read queries."""

    def test_active_only_helper(self, db_session, make_user):
        user = make_user(email="rp_helper@test.com")
        log1 = _make_activity_log(db_session, user)
        log2 = _make_activity_log(db_session, user)

        # Archive one
        soft_delete(db_session, log1, user.id, "test")

        query = active_only(
            db_session.query(ActivityLog).filter(ActivityLog.user_id == user.id),
            ActivityLog,
        )
        results = query.all()
        assert len(results) == 1
        assert results[0].id == log2.id

    def test_archived_activity_excluded_from_history(self, db_session, make_user):
        user = make_user(email="rp_hist@test.com")
        log = _make_activity_log(db_session, user)
        soft_delete(db_session, log, user.id, "test")

        active = db_session.query(ActivityLog).filter(
            ActivityLog.user_id == user.id,
            ActivityLog.archived_at.is_(None),
        ).count()
        assert active == 0

    def test_archived_diagnostic_excluded_from_history(self, db_session, make_user, make_client):
        user = make_user(email="rp_ds@test.com")
        client = make_client(user=user)
        ds = _make_diagnostic_summary(db_session, user, client)
        soft_delete(db_session, ds, user.id, "test")

        active = db_session.query(DiagnosticSummary).filter(
            DiagnosticSummary.user_id == user.id,
            DiagnosticSummary.archived_at.is_(None),
        ).count()
        assert active == 0

    def test_archived_follow_up_item_excluded_from_list(
        self, db_session, make_user, make_engagement, make_follow_up_item
    ):
        from follow_up_items_manager import FollowUpItemsManager

        user = make_user(email="rp_fui@test.com")
        engagement = make_engagement(user=user)
        item = make_follow_up_item(engagement=engagement)

        manager = FollowUpItemsManager(db_session)
        items, total = manager.get_items(user.id, engagement.id)
        assert total == 1

        soft_delete(db_session, item, user.id, "test")
        items, total = manager.get_items(user.id, engagement.id)
        assert total == 0

    def test_archived_tool_run_excluded_from_engagement(
        self, db_session, make_engagement, make_tool_run
    ):
        from engagement_manager import EngagementManager

        engagement = make_engagement()
        tr = make_tool_run(engagement=engagement)

        em = EngagementManager(db_session)
        runs = em.get_tool_runs(engagement.id)
        assert len(runs) == 1

        soft_delete(db_session, tr, None, "test")
        runs = em.get_tool_runs(engagement.id)
        assert len(runs) == 0

    def test_archived_comment_excluded_from_list(
        self, db_session, make_user, make_engagement, make_follow_up_item, make_comment
    ):
        from follow_up_items_manager import FollowUpItemsManager

        user = make_user(email="rp_comment@test.com")
        engagement = make_engagement(user=user)
        item = make_follow_up_item(engagement=engagement)
        comment = make_comment(follow_up_item=item, user=user)

        manager = FollowUpItemsManager(db_session)
        comments = manager.get_comments(user.id, item.id)
        assert len(comments) == 1

        soft_delete(db_session, comment, user.id, "test")
        comments = manager.get_comments(user.id, item.id)
        assert len(comments) == 0


# =============================================================================
# 4. Immutability Proof Tests
# =============================================================================


class TestImmutabilityProof:
    """Prove archived records are retained — row count never decreases."""

    def test_archived_records_physically_exist(self, db_session, make_user):
        """Archived records remain in the DB — unfiltered query returns them."""
        user = make_user(email="proof_exist@test.com")
        _make_activity_log(db_session, user)
        _make_activity_log(db_session, user)

        soft_delete_bulk(
            db_session,
            db_session.query(ActivityLog).filter(
                ActivityLog.user_id == user.id,
                ActivityLog.archived_at.is_(None),
            ),
            user_id=user.id,
            reason="proof_test",
        )

        # Unfiltered query: all 2 records still exist
        total = db_session.query(ActivityLog).filter_by(user_id=user.id).count()
        assert total == 2

        # Active-only query: 0 active
        active = db_session.query(ActivityLog).filter(
            ActivityLog.user_id == user.id,
            ActivityLog.archived_at.is_(None),
        ).count()
        assert active == 0

    def test_row_count_never_decreases(self, db_session, make_user, make_client):
        """Row count stays the same or increases after archive operations."""
        user = make_user(email="proof_count@test.com")
        client = make_client(user=user)

        _make_diagnostic_summary(db_session, user, client)
        _make_diagnostic_summary(db_session, user, client)
        before_count = db_session.query(DiagnosticSummary).filter_by(user_id=user.id).count()
        assert before_count == 2

        soft_delete_bulk(
            db_session,
            db_session.query(DiagnosticSummary).filter(
                DiagnosticSummary.user_id == user.id,
                DiagnosticSummary.archived_at.is_(None),
            ),
            user_id=user.id,
            reason="count_test",
        )

        after_count = db_session.query(DiagnosticSummary).filter_by(user_id=user.id).count()
        assert after_count >= before_count

    def test_archived_at_timestamp_accurate(self, db_session, make_user):
        """archived_at timestamp is within a few seconds of current time."""
        user = make_user(email="proof_ts@test.com")
        log = _make_activity_log(db_session, user)

        before = datetime.now(UTC)
        soft_delete(db_session, log, user.id, "ts_test")
        after = datetime.now(UTC)

        db_session.expire(log)
        # Handle timezone-naive datetimes from SQLite
        archived_at = log.archived_at
        if archived_at.tzinfo is None:
            from datetime import timezone
            archived_at = archived_at.replace(tzinfo=timezone.utc)

        assert before <= archived_at <= after


# =============================================================================
# 5. Retention Cleanup — Soft-Delete Verification
# =============================================================================


class TestRetentionSoftDelete:
    """Verify retention cleanup uses soft-delete instead of hard-delete."""

    def test_activity_log_retention_archives(self, db_session, make_user):
        user = make_user(email="ret_sd_al@test.com")
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 30)
        log = _make_activity_log(db_session, user, timestamp=old_ts)
        log_id = log.id

        archived = cleanup_expired_activity_logs(db_session)
        assert archived == 1

        # Still exists physically
        found = db_session.query(ActivityLog).filter_by(id=log_id).first()
        assert found is not None
        assert found.archived_at is not None
        assert found.archive_reason == "retention_policy"

    def test_diagnostic_summary_retention_archives(self, db_session, make_user, make_client):
        user = make_user(email="ret_sd_ds@test.com")
        client = make_client(user=user)
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 30)
        ds = _make_diagnostic_summary(db_session, user, client, timestamp=old_ts)
        ds_id = ds.id

        archived = cleanup_expired_diagnostic_summaries(db_session)
        assert archived == 1

        found = db_session.query(DiagnosticSummary).filter_by(id=ds_id).first()
        assert found is not None
        assert found.archived_at is not None
        assert found.archive_reason == "retention_policy"

    def test_retention_idempotent(self, db_session, make_user, make_client):
        """Second retention run archives nothing (already archived)."""
        user = make_user(email="ret_sd_idem@test.com")
        client = make_client(user=user)
        old_ts = datetime.now(UTC) - timedelta(days=RETENTION_DAYS + 30)
        _make_activity_log(db_session, user, timestamp=old_ts)
        _make_diagnostic_summary(db_session, user, client, timestamp=old_ts)

        from retention_cleanup import run_retention_cleanup
        first = run_retention_cleanup(db_session)
        assert sum(first.values()) == 2

        second = run_retention_cleanup(db_session)
        assert sum(second.values()) == 0
