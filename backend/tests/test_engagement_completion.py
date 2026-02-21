"""
Tests for Sprint 359: Engagement Completion Gate.

Covers:
- EngagementStatus.COMPLETED value
- VALID_ENGAGEMENT_TRANSITIONS map
- validate_engagement_transition() helper
- InvalidEngagementTransitionError
- Completion gate: unresolved follow-up items block completion
- completed_at / completed_by metadata set on completion
- archive from COMPLETED state
- to_dict includes completion fields
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engagement_manager import EngagementManager
from engagement_model import (
    EngagementStatus,
    InvalidEngagementTransitionError,
    VALID_ENGAGEMENT_TRANSITIONS,
    validate_engagement_transition,
)
from follow_up_items_model import FollowUpDisposition, FollowUpItem


# =============================================================================
# TRANSITION MAP & VALIDATION
# =============================================================================


class TestEngagementTransitions:
    """Tests for VALID_ENGAGEMENT_TRANSITIONS and validate_engagement_transition()."""

    def test_completed_status_exists(self):
        assert EngagementStatus.COMPLETED.value == "completed"

    def test_active_can_transition_to_completed(self):
        validate_engagement_transition(EngagementStatus.ACTIVE, EngagementStatus.COMPLETED)

    def test_active_can_transition_to_archived(self):
        validate_engagement_transition(EngagementStatus.ACTIVE, EngagementStatus.ARCHIVED)

    def test_completed_can_transition_to_archived(self):
        validate_engagement_transition(EngagementStatus.COMPLETED, EngagementStatus.ARCHIVED)

    def test_archived_is_terminal(self):
        with pytest.raises(InvalidEngagementTransitionError, match="terminal"):
            validate_engagement_transition(EngagementStatus.ARCHIVED, EngagementStatus.ACTIVE)

    def test_archived_cannot_transition_to_completed(self):
        with pytest.raises(InvalidEngagementTransitionError, match="terminal"):
            validate_engagement_transition(EngagementStatus.ARCHIVED, EngagementStatus.COMPLETED)

    def test_completed_cannot_transition_to_active(self):
        with pytest.raises(InvalidEngagementTransitionError, match="Allowed transitions"):
            validate_engagement_transition(EngagementStatus.COMPLETED, EngagementStatus.ACTIVE)

    def test_active_cannot_transition_to_active(self):
        with pytest.raises(InvalidEngagementTransitionError):
            validate_engagement_transition(EngagementStatus.ACTIVE, EngagementStatus.ACTIVE)

    def test_transition_map_completeness(self):
        """Every status value has an entry in the map."""
        for status in EngagementStatus:
            assert status in VALID_ENGAGEMENT_TRANSITIONS

    def test_error_message_includes_allowed(self):
        with pytest.raises(InvalidEngagementTransitionError, match="archived"):
            validate_engagement_transition(EngagementStatus.COMPLETED, EngagementStatus.ACTIVE)


# =============================================================================
# COMPLETION GATE (follow-up item resolution)
# =============================================================================


class TestCompletionGate:
    """Tests for the completion gate in EngagementManager."""

    def test_complete_engagement_no_follow_ups(self, db_session, make_user, make_client):
        """Engagement with no follow-up items can be completed."""
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        result = mgr.complete_engagement(user.id, eng.id)
        assert result.status == EngagementStatus.COMPLETED

    def test_complete_engagement_all_reviewed(self, db_session, make_user, make_client):
        """Engagement with all follow-up items reviewed can be completed."""
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        # Add reviewed follow-up items
        for disp in [FollowUpDisposition.INVESTIGATED_NO_ISSUE, FollowUpDisposition.IMMATERIAL]:
            item = FollowUpItem(
                engagement_id=eng.id,
                description="Test item",
                tool_source="trial_balance",
                disposition=disp,
            )
            db_session.add(item)
        db_session.flush()

        result = mgr.complete_engagement(user.id, eng.id)
        assert result.status == EngagementStatus.COMPLETED

    def test_complete_blocked_by_unresolved_items(self, db_session, make_user, make_client):
        """Completion blocked when follow-up items have NOT_REVIEWED disposition."""
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        # Add unresolved follow-up item
        item = FollowUpItem(
            engagement_id=eng.id,
            description="Unresolved anomaly",
            tool_source="ap_testing",
            disposition=FollowUpDisposition.NOT_REVIEWED,
        )
        db_session.add(item)
        db_session.flush()

        with pytest.raises(ValueError, match="1 follow-up item.*not_reviewed"):
            mgr.complete_engagement(user.id, eng.id)

        # Status should remain ACTIVE
        db_session.refresh(eng)
        assert eng.status == EngagementStatus.ACTIVE

    def test_complete_blocked_multiple_unresolved(self, db_session, make_user, make_client):
        """Error message shows count of unresolved items."""
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        for _ in range(3):
            db_session.add(FollowUpItem(
                engagement_id=eng.id,
                description="Unresolved",
                tool_source="revenue_testing",
                disposition=FollowUpDisposition.NOT_REVIEWED,
            ))
        db_session.flush()

        with pytest.raises(ValueError, match="3 follow-up item"):
            mgr.complete_engagement(user.id, eng.id)

    def test_archived_items_not_counted(self, db_session, make_user, make_client):
        """Archived (soft-deleted) follow-up items don't block completion."""
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        # Add an archived NOT_REVIEWED item — should not block
        item = FollowUpItem(
            engagement_id=eng.id,
            description="Archived anomaly",
            tool_source="ap_testing",
            disposition=FollowUpDisposition.NOT_REVIEWED,
            archived_at=datetime.now(UTC),
            archived_by=user.id,
            archive_reason="No longer relevant",
        )
        db_session.add(item)
        db_session.flush()

        result = mgr.complete_engagement(user.id, eng.id)
        assert result.status == EngagementStatus.COMPLETED

    def test_mixed_reviewed_and_unresolved(self, db_session, make_user, make_client):
        """Completion blocked even if some items are reviewed but one remains NOT_REVIEWED."""
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        # 2 reviewed, 1 not
        db_session.add(FollowUpItem(
            engagement_id=eng.id, description="Reviewed 1", tool_source="tb",
            disposition=FollowUpDisposition.INVESTIGATED_NO_ISSUE,
        ))
        db_session.add(FollowUpItem(
            engagement_id=eng.id, description="Reviewed 2", tool_source="tb",
            disposition=FollowUpDisposition.IMMATERIAL,
        ))
        db_session.add(FollowUpItem(
            engagement_id=eng.id, description="Not reviewed", tool_source="tb",
            disposition=FollowUpDisposition.NOT_REVIEWED,
        ))
        db_session.flush()

        with pytest.raises(ValueError, match="1 follow-up item"):
            mgr.complete_engagement(user.id, eng.id)


# =============================================================================
# COMPLETION METADATA
# =============================================================================


class TestCompletionMetadata:
    """Tests for completed_at/completed_by fields."""

    def test_completed_at_set(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        before = datetime.now(UTC)
        result = mgr.complete_engagement(user.id, eng.id)
        assert result.completed_at is not None
        # completed_at should be around now (within 5 seconds)
        completed = result.completed_at.replace(tzinfo=None)
        assert completed >= before.replace(tzinfo=None)

    def test_completed_by_set(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        result = mgr.complete_engagement(user.id, eng.id)
        assert result.completed_by == user.id

    def test_to_dict_includes_completion_fields(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )

        # Before completion
        d = eng.to_dict()
        assert d["completed_at"] is None
        assert d["completed_by"] is None

        # After completion
        mgr.complete_engagement(user.id, eng.id)
        db_session.refresh(eng)
        d = eng.to_dict()
        assert d["completed_at"] is not None
        assert d["completed_by"] == user.id

    def test_active_engagement_has_no_completion_metadata(self, make_engagement):
        eng = make_engagement()
        assert eng.completed_at is None
        assert eng.completed_by is None


# =============================================================================
# ARCHIVE FROM COMPLETED
# =============================================================================


class TestArchiveFromCompleted:
    """Tests for archiving a completed engagement."""

    def test_archive_from_completed(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        mgr.complete_engagement(user.id, eng.id)
        archived = mgr.archive_engagement(user.id, eng.id)
        assert archived.status == EngagementStatus.ARCHIVED

    def test_archive_from_active_still_works(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        archived = mgr.archive_engagement(user.id, eng.id)
        assert archived.status == EngagementStatus.ARCHIVED

    def test_archived_cannot_be_reactivated(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        mgr.archive_engagement(user.id, eng.id)
        with pytest.raises(InvalidEngagementTransitionError, match="terminal"):
            mgr.update_engagement(user.id, eng.id, status=EngagementStatus.ACTIVE)

    def test_completed_preserves_metadata_on_archive(self, db_session, make_user, make_client):
        """Archiving a completed engagement should preserve completed_at/completed_by."""
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)
        eng = mgr.create_engagement(
            user.id, client.id,
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC),
        )
        mgr.complete_engagement(user.id, eng.id)
        db_session.refresh(eng)
        completed_at = eng.completed_at

        mgr.archive_engagement(user.id, eng.id)
        db_session.refresh(eng)
        assert eng.status == EngagementStatus.ARCHIVED
        assert eng.completed_at == completed_at
        assert eng.completed_by == user.id


# =============================================================================
# STATUS ENUM IN EXISTING TESTS COMPATIBILITY
# =============================================================================


class TestStatusEnumCompatibility:
    """Ensure the new status doesn't break existing filtering."""

    def test_filter_by_completed_status(self, db_session, make_user, make_client):
        user = make_user()
        client = make_client(user=user)
        mgr = EngagementManager(db_session)

        # Create 3 engagements in different states
        e1 = mgr.create_engagement(user.id, client.id, datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC))
        e2 = mgr.create_engagement(user.id, client.id, datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 12, 31, tzinfo=UTC))
        e3 = mgr.create_engagement(user.id, client.id, datetime(2023, 1, 1, tzinfo=UTC), datetime(2023, 12, 31, tzinfo=UTC))

        mgr.complete_engagement(user.id, e2.id)
        mgr.archive_engagement(user.id, e3.id)

        active, _ = mgr.get_engagements_for_user(user.id, status=EngagementStatus.ACTIVE)
        completed, _ = mgr.get_engagements_for_user(user.id, status=EngagementStatus.COMPLETED)
        archived, _ = mgr.get_engagements_for_user(user.id, status=EngagementStatus.ARCHIVED)

        assert len(active) == 1
        assert len(completed) == 1
        assert len(archived) == 1

    def test_complete_nonexistent_returns_none(self, db_session, make_user):
        user = make_user()
        mgr = EngagementManager(db_session)
        assert mgr.complete_engagement(user.id, 99999) is None
