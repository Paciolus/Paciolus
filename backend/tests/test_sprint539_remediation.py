"""
Sprint 539: Comprehensive remediation tests.

Covers: seat enforcement, post-cancellation entitlement, refresh token race,
webhook idempotency, event ordering, DPA timestamp, org-first lifecycle,
org member shared access, subscription linkage backfill.
"""

import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Client, UserTier
from organization_model import (
    Organization,
    OrganizationMember,
    OrgRole,
)
from subscription_model import (
    ProcessedWebhookEvent,
    Subscription,
    SubscriptionStatus,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_org_with_sub(db, owner, tier="professional", status=SubscriptionStatus.ACTIVE):
    """Create an org with a linked subscription."""
    sub = Subscription(
        user_id=owner.id,
        tier=tier,
        status=status,
        stripe_customer_id=f"cus_{secrets.token_hex(6)}",
        stripe_subscription_id=f"sub_{secrets.token_hex(6)}",
        seat_count=7,
        additional_seats=0,
    )
    db.add(sub)
    db.flush()

    org = Organization(
        name="Test Org",
        slug=f"test-org-{secrets.token_hex(3)}",
        owner_user_id=owner.id,
        subscription_id=sub.id,
    )
    db.add(org)
    db.flush()

    membership = OrganizationMember(
        organization_id=org.id,
        user_id=owner.id,
        role=OrgRole.OWNER,
    )
    db.add(membership)
    owner.organization_id = org.id
    owner.tier = UserTier(tier)
    db.flush()

    return org, sub


def _add_org_member(db, org, user, role=OrgRole.MEMBER, tier=None):
    """Add a user as a member of an org."""
    membership = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=role,
    )
    db.add(membership)
    user.organization_id = org.id
    if tier:
        user.tier = UserTier(tier)
    db.flush()
    return membership


# ===========================================================================
# SECTION 1: Seat Enforcement
# ===========================================================================


class TestSeatEnforcement:
    """Seat limit enforcement via org subscription context."""

    @pytest.fixture(autouse=True)
    def _force_hard_seat_enforcement(self):
        """Force hard enforcement mode for seat tests."""
        with patch("shared.entitlement_checks._get_seat_enforcement_mode", return_value="hard"):
            yield

    def test_owner_invite_at_cap_blocked(self, db_session, make_user):
        """Owner invites when org is at seat cap — should be blocked."""
        from shared.entitlement_checks import check_seat_limit_for_org

        owner = make_user(email="owner_cap@example.com", tier=UserTier.PROFESSIONAL)
        org, sub = _make_org_with_sub(db_session, owner)
        sub.seat_count = 1  # Cap at 1 seat
        sub.additional_seats = 0
        db_session.flush()

        # Owner is already member (1 seat used), so should be blocked
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            check_seat_limit_for_org(db_session, org.id)
        assert exc_info.value.status_code == 403

    def test_admin_invite_at_cap_blocked(self, db_session, make_user):
        """Admin with no personal subscription still blocked via org context."""
        from shared.entitlement_checks import check_seat_limit_for_org

        owner = make_user(email="owner_admin@example.com", tier=UserTier.PROFESSIONAL)
        org, sub = _make_org_with_sub(db_session, owner)
        sub.seat_count = 2
        sub.additional_seats = 0
        db_session.flush()

        admin = make_user(email="admin_nosub@example.com", tier=UserTier.PROFESSIONAL)
        _add_org_member(db_session, org, admin, role=OrgRole.ADMIN)

        # 2 members, 2 seats — at cap, should block next invite
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            check_seat_limit_for_org(db_session, org.id)
        assert exc_info.value.status_code == 403

    def test_admin_no_personal_sub_still_blocked(self, db_session, make_user):
        """Admin who has NO personal subscription row — enforcement via org context."""
        from shared.entitlement_checks import check_seat_limit_for_org

        owner = make_user(email="owner_solo@example.com", tier=UserTier.PROFESSIONAL)
        org, sub = _make_org_with_sub(db_session, owner)
        sub.seat_count = 1
        db_session.flush()

        # Only owner, cap is 1 — should be at limit
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            check_seat_limit_for_org(db_session, org.id)


# ===========================================================================
# SECTION 1.2: Post-Cancellation Entitlement
# ===========================================================================


class TestPostCancellationEntitlement:
    """Cancel subscription → every org member should be FREE."""

    def test_cancel_downgrades_all_org_members(self, db_session, make_user):
        """Cancel subscription → owner AND members downgraded to FREE."""
        from billing.webhook_handler import handle_subscription_deleted

        owner = make_user(email="cancel_owner@example.com", tier=UserTier.PROFESSIONAL)
        org, sub = _make_org_with_sub(db_session, owner)

        member1 = make_user(email="cancel_m1@example.com", tier=UserTier.PROFESSIONAL)
        _add_org_member(db_session, org, member1, tier="professional")

        member2 = make_user(email="cancel_m2@example.com", tier=UserTier.PROFESSIONAL)
        _add_org_member(db_session, org, member2, tier="professional")

        db_session.commit()

        # Simulate subscription.deleted
        event_data = {"customer": sub.stripe_customer_id, "metadata": {}}
        handle_subscription_deleted(db_session, event_data)

        db_session.refresh(owner)
        db_session.refresh(member1)
        db_session.refresh(member2)

        assert owner.tier == UserTier.FREE
        assert member1.tier == UserTier.FREE
        assert member2.tier == UserTier.FREE


# ===========================================================================
# SECTION 2: Refresh Token Race
# ===========================================================================


class TestRefreshTokenRace:
    """Refresh token rotation with concurrent requests."""

    def test_rotate_refresh_token_cas_guard(self, db_session, make_user, make_refresh_token):
        """Two rotations with the same token — only one succeeds."""
        from fastapi import HTTPException

        from auth import rotate_refresh_token

        user = make_user(email="race_user@example.com")
        raw_token, rt = make_refresh_token(user=user)
        db_session.commit()

        # First rotation should succeed
        access, new_raw, returned_user = rotate_refresh_token(db_session, raw_token)
        assert access is not None
        assert new_raw is not None

        # Second rotation with the SAME original token should fail
        # (the original token is now revoked)
        with pytest.raises(HTTPException) as exc_info:
            rotate_refresh_token(db_session, raw_token)
        assert exc_info.value.status_code == 401


# ===========================================================================
# SECTION 3: Webhook Idempotency
# ===========================================================================


class TestWebhookIdempotency:
    """Webhook deduplication and event ordering."""

    def test_duplicate_event_rejected(self, db_session):
        """Same event ID processed twice — second is rejected via dedup table."""
        event_id = "evt_test_dedup_" + secrets.token_hex(8)

        # First insert should succeed
        db_session.add(ProcessedWebhookEvent(stripe_event_id=event_id))
        db_session.flush()

        # Second insert with same ID should raise IntegrityError
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            db_session.add(ProcessedWebhookEvent(stripe_event_id=event_id))
            db_session.flush()

        db_session.rollback()

    def test_stale_subscription_updated_after_deleted(self, db_session, make_user):
        """subscription.updated (active) after subscription.deleted — final state stays canceled."""
        from billing.webhook_handler import handle_subscription_deleted, handle_subscription_updated

        owner = make_user(email="stale_owner@example.com", tier=UserTier.PROFESSIONAL)
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id=f"cus_{secrets.token_hex(6)}",
            stripe_subscription_id=f"sub_{secrets.token_hex(6)}",
            seat_count=1,
        )
        db_session.add(sub)
        db_session.commit()

        # First: delete the subscription
        handle_subscription_deleted(db_session, {"customer": sub.stripe_customer_id, "metadata": {}})
        db_session.refresh(sub)
        assert sub.status == SubscriptionStatus.CANCELED

        # Now: stale update arrives claiming active
        handle_subscription_updated(
            db_session,
            {
                "customer": sub.stripe_customer_id,
                "status": "active",
                "items": {"data": []},
                "metadata": {},
            },
        )

        db_session.refresh(sub)
        # Should still be CANCELED — the guard rejected the re-activation
        assert sub.status == SubscriptionStatus.CANCELED


# ===========================================================================
# SECTION 4: DPA Timestamp
# ===========================================================================


class TestDPATimestampNormalization:
    """DPA timestamp offset-aware normalization."""

    def test_offset_bearing_timestamp_converted_correctly(self, db_session, make_user):
        """Timestamp with +05:30 offset should be stored as correct UTC instant."""
        from billing.webhook_handler import _apply_dpa_from_metadata

        owner = make_user(email="dpa_offset@example.com")
        sub = Subscription(
            user_id=owner.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id=f"cus_{secrets.token_hex(6)}",
            stripe_subscription_id=f"sub_{secrets.token_hex(6)}",
        )
        db_session.add(sub)
        db_session.commit()

        metadata = {
            "dpa_accepted_at": "2024-01-15T10:00:00+05:30",
            "dpa_version": "1.0",
        }
        _apply_dpa_from_metadata(db_session, owner.id, metadata)

        db_session.refresh(sub)
        assert sub.dpa_accepted_at is not None
        # 10:00 +05:30 = 04:30 UTC
        assert sub.dpa_accepted_at.hour == 4
        assert sub.dpa_accepted_at.minute == 30

    def test_negative_offset_timestamp(self, db_session, make_user):
        """-07:00 offset should be stored as correct UTC instant."""
        from billing.webhook_handler import _apply_dpa_from_metadata

        owner = make_user(email="dpa_neg@example.com")
        sub = Subscription(
            user_id=owner.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id=f"cus_{secrets.token_hex(6)}",
            stripe_subscription_id=f"sub_{secrets.token_hex(6)}",
        )
        db_session.add(sub)
        db_session.commit()

        metadata = {
            "dpa_accepted_at": "2024-06-20T14:00:00-07:00",
            "dpa_version": "1.0",
        }
        _apply_dpa_from_metadata(db_session, owner.id, metadata)

        db_session.refresh(sub)
        assert sub.dpa_accepted_at is not None
        # 14:00 -07:00 = 21:00 UTC
        assert sub.dpa_accepted_at.hour == 21
        assert sub.dpa_accepted_at.minute == 0


# ===========================================================================
# SECTION 1.4: Org-First Lifecycle
# ===========================================================================


class TestOrgFirstLifecycle:
    """Create org first → checkout → invite → verify member tier inheritance."""

    def test_org_subscription_linkage_backfill(self, db_session, make_user):
        """Owner has active subscription, org has null subscription_id — linkage is resolved."""
        from shared.entitlement_checks import _resolve_org_subscription

        owner = make_user(email="orgfirst_owner@example.com", tier=UserTier.PROFESSIONAL)

        # Create org WITHOUT subscription linkage
        org = Organization(
            name="Org First Test",
            slug=f"orgfirst-{secrets.token_hex(3)}",
            owner_user_id=owner.id,
            subscription_id=None,  # No linkage
        )
        db_session.add(org)
        db_session.flush()

        membership = OrganizationMember(
            organization_id=org.id,
            user_id=owner.id,
            role=OrgRole.OWNER,
        )
        db_session.add(membership)
        owner.organization_id = org.id
        db_session.flush()

        # Create subscription separately (simulating checkout after org creation)
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id=f"cus_{secrets.token_hex(6)}",
            stripe_subscription_id=f"sub_{secrets.token_hex(6)}",
            seat_count=7,
        )
        db_session.add(sub)
        db_session.flush()

        # _resolve_org_subscription should find the subscription via owner fallback
        resolved_sub, entitlements = _resolve_org_subscription(db_session, org.id)
        assert resolved_sub is not None
        assert resolved_sub.id == sub.id

        # Verify backfill happened
        db_session.refresh(org)
        assert org.subscription_id == sub.id


# ===========================================================================
# SECTION 1.3: Org Member Shared Access
# ===========================================================================


class TestOrgMemberSharedAccess:
    """Org members can access shared client/engagement resources."""

    def test_org_owner_accesses_own_client(self, db_session, make_user):
        """Owner can access their own client."""
        from client_manager import ClientManager

        owner = make_user(email="access_owner@example.com", tier=UserTier.PROFESSIONAL)
        org, sub = _make_org_with_sub(db_session, owner)
        db_session.flush()

        client = Client(user_id=owner.id, name="Owner Client")
        db_session.add(client)
        db_session.flush()

        manager = ClientManager(db_session)
        result = manager.get_client(owner.id, client.id)
        assert result is not None
        assert result.id == client.id

    def test_org_member_accesses_org_owner_client(self, db_session, make_user):
        """Org member can access the org owner's client."""
        from client_manager import ClientManager

        owner = make_user(email="shared_owner@example.com", tier=UserTier.PROFESSIONAL)
        org, sub = _make_org_with_sub(db_session, owner)

        member = make_user(email="shared_member@example.com", tier=UserTier.PROFESSIONAL)
        _add_org_member(db_session, org, member, tier="professional")

        client = Client(user_id=owner.id, name="Shared Client")
        db_session.add(client)
        db_session.flush()

        manager = ClientManager(db_session)
        result = manager.get_client(member.id, client.id)
        assert result is not None
        assert result.id == client.id

    def test_org_admin_accesses_org_owner_client(self, db_session, make_user):
        """Org admin can access the org owner's client."""
        from client_manager import ClientManager

        owner = make_user(email="admin_access_owner@example.com", tier=UserTier.PROFESSIONAL)
        org, sub = _make_org_with_sub(db_session, owner)

        admin = make_user(email="admin_access@example.com", tier=UserTier.PROFESSIONAL)
        _add_org_member(db_session, org, admin, role=OrgRole.ADMIN, tier="professional")

        client = Client(user_id=owner.id, name="Admin Access Client")
        db_session.add(client)
        db_session.flush()

        manager = ClientManager(db_session)
        result = manager.get_client(admin.id, client.id)
        assert result is not None

    def test_non_member_rejected(self, db_session, make_user):
        """Non-member correctly rejected from accessing org client."""
        from client_manager import ClientManager

        owner = make_user(email="rejected_owner@example.com", tier=UserTier.PROFESSIONAL)
        org, sub = _make_org_with_sub(db_session, owner)

        outsider = make_user(email="outsider@example.com", tier=UserTier.FREE)

        client = Client(user_id=owner.id, name="Private Client")
        db_session.add(client)
        db_session.flush()

        manager = ClientManager(db_session)
        result = manager.get_client(outsider.id, client.id)
        assert result is None

    def test_org_member_accesses_engagement(self, db_session, make_user):
        """Org member can access owner's engagement via org membership."""
        from engagement_manager import EngagementManager
        from engagement_model import Engagement, EngagementStatus

        owner = make_user(email="eng_owner@example.com", tier=UserTier.PROFESSIONAL)
        org, sub = _make_org_with_sub(db_session, owner)

        member = make_user(email="eng_member@example.com", tier=UserTier.PROFESSIONAL)
        _add_org_member(db_session, org, member, tier="professional")

        client = Client(user_id=owner.id, name="Engagement Client")
        db_session.add(client)
        db_session.flush()

        engagement = Engagement(
            client_id=client.id,
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 12, 31, tzinfo=UTC),
            status=EngagementStatus.ACTIVE,
            created_by=owner.id,
        )
        db_session.add(engagement)
        db_session.flush()

        manager = EngagementManager(db_session)
        result = manager.get_engagement(member.id, engagement.id)
        assert result is not None
        assert result.id == engagement.id
