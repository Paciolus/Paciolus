"""
Sprint 849 (security review M5) — org members' entitlements follow the owner's live plan.

A member's ``User.tier`` was copied from the owner's subscription when they
joined and then trusted for as long as they had no Subscription row of their
own, which members never have. An owner moving Enterprise -> Solo, going
past_due, or being force-canceled by an admin left every member on the old
paid plan (bulk upload, PDF branding) indefinitely.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import User, UserTier
from organization_model import Organization, OrganizationMember, OrgRole
from shared.entitlements import get_entitlements
from subscription_model import BillingInterval, Subscription, SubscriptionStatus


def _stripe_sub(status: str) -> dict:
    """A minimal Stripe subscription payload with a period around now (no fixed dates)."""
    start = datetime.now(UTC) - timedelta(days=1)
    return {
        "id": "sub_sprint849",
        "status": status,
        "cancel_at_period_end": False,
        "current_period_start": int(start.timestamp()),
        "current_period_end": int((start + timedelta(days=30)).timestamp()),
        "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
    }


@pytest.fixture
def enterprise_org(db_session, make_user):
    """An Enterprise owner with one member who joined through the invite path."""
    from billing.subscription_manager import sync_subscription_from_stripe
    from shared.organization_policy import apply_org_subscription_to_user

    owner = make_user(email="owner849@firm.com", tier=UserTier.FREE)
    sync_subscription_from_stripe(db_session, owner.id, _stripe_sub("active"), "cus_sprint849", "enterprise")

    org = Organization(name="Firm 849", slug="firm-849", owner_user_id=owner.id)
    db_session.add(org)
    db_session.flush()
    db_session.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER))
    owner.organization_id = org.id

    member = make_user(email="member849@firm.com", tier=UserTier.FREE)
    db_session.add(OrganizationMember(organization_id=org.id, user_id=member.id, role=OrgRole.MEMBER))
    member.organization_id = org.id
    apply_org_subscription_to_user(db_session, member, org)
    db_session.flush()

    assert member.tier == UserTier.ENTERPRISE  # the join copied the owner's plan
    return {"owner": owner, "member": member, "org": org}


def _effective(user: User, db_session):
    from shared.entitlement_checks import get_effective_entitlements

    # A fresh session-level cache per check, as each request has its own session.
    db_session.info.pop("_paciolus_subscription_by_user", None)
    return get_effective_entitlements(user, db_session)


class TestMemberFollowsOwner:
    def test_member_starts_with_the_owners_plan(self, db_session, enterprise_org):
        assert _effective(enterprise_org["member"], db_session) == get_entitlements(UserTier.ENTERPRISE)

    def test_owner_downgrade_via_sync_gives_member_solo(self, db_session, enterprise_org):
        from billing.subscription_manager import sync_subscription_from_stripe

        owner, member = enterprise_org["owner"], enterprise_org["member"]
        sync_subscription_from_stripe(db_session, owner.id, _stripe_sub("active"), "cus_sprint849", "solo")

        solo = get_entitlements(UserTier.SOLO)
        assert solo != get_entitlements(UserTier.ENTERPRISE)
        assert _effective(member, db_session) == solo
        assert _effective(member, db_session).bulk_upload is False
        assert _effective(member, db_session).custom_branding is False
        # The display cache (/users/me) follows too.
        assert member.tier == UserTier.SOLO

    def test_entitlements_read_the_owner_live_even_with_a_stale_cache(self, db_session, enterprise_org):
        """No refresh ran (cache still Enterprise): the owner's row still decides."""
        owner, member = enterprise_org["owner"], enterprise_org["member"]
        sub = db_session.query(Subscription).filter(Subscription.user_id == owner.id).one()
        sub.tier = "solo"
        db_session.flush()

        assert member.tier == UserTier.ENTERPRISE
        assert _effective(member, db_session) == get_entitlements(UserTier.SOLO)

    def test_owner_past_due_via_sync_makes_member_free(self, db_session, enterprise_org):
        from billing.subscription_manager import sync_subscription_from_stripe

        owner, member = enterprise_org["owner"], enterprise_org["member"]
        sync_subscription_from_stripe(db_session, owner.id, _stripe_sub("past_due"), "cus_sprint849", "enterprise")

        assert _effective(member, db_session) == get_entitlements(UserTier.FREE)
        assert member.tier == UserTier.FREE

    def test_owner_past_due_without_any_member_refresh_makes_member_free(self, db_session, enterprise_org):
        owner, member = enterprise_org["owner"], enterprise_org["member"]
        sub = db_session.query(Subscription).filter(Subscription.user_id == owner.id).one()
        sub.status = SubscriptionStatus.PAST_DUE
        db_session.flush()

        assert member.tier == UserTier.ENTERPRISE
        assert _effective(member, db_session) == get_entitlements(UserTier.FREE)

    def test_owner_reactivation_restores_the_member(self, db_session, enterprise_org):
        from billing.subscription_manager import sync_subscription_from_stripe

        owner, member = enterprise_org["owner"], enterprise_org["member"]
        sync_subscription_from_stripe(db_session, owner.id, _stripe_sub("past_due"), "cus_sprint849", "enterprise")
        sync_subscription_from_stripe(db_session, owner.id, _stripe_sub("active"), "cus_sprint849", "enterprise")

        assert _effective(member, db_session) == get_entitlements(UserTier.ENTERPRISE)
        assert member.tier == UserTier.ENTERPRISE

    def test_member_of_an_org_with_no_subscription_is_free(self, db_session, enterprise_org):
        owner, member = enterprise_org["owner"], enterprise_org["member"]
        enterprise_org["org"].subscription_id = None
        db_session.flush()
        db_session.query(Subscription).filter(Subscription.user_id == owner.id).delete()
        db_session.flush()

        assert member.tier == UserTier.ENTERPRISE
        assert _effective(member, db_session) == get_entitlements(UserTier.FREE)

    def test_owner_keeps_their_own_rules(self, db_session, enterprise_org):
        assert _effective(enterprise_org["owner"], db_session) == get_entitlements(UserTier.ENTERPRISE)

    def test_refresh_skips_a_member_with_their_own_subscription(self, db_session, enterprise_org, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        owner, org = enterprise_org["owner"], enterprise_org["org"]
        payer = make_user(email="payer849@firm.com", tier=UserTier.ENTERPRISE)
        db_session.add(OrganizationMember(organization_id=org.id, user_id=payer.id, role=OrgRole.MEMBER))
        payer.organization_id = org.id
        db_session.add(
            Subscription(
                user_id=payer.id,
                tier="enterprise",
                status=SubscriptionStatus.ACTIVE,
                billing_interval=BillingInterval.MONTHLY,
            )
        )
        db_session.flush()

        sync_subscription_from_stripe(db_session, owner.id, _stripe_sub("active"), "cus_sprint849", "solo")

        assert payer.tier == UserTier.ENTERPRISE
        assert enterprise_org["member"].tier == UserTier.SOLO


class TestAdminImmediateForceCancel:
    def test_member_is_free_after_immediate_force_cancel(self, db_session, enterprise_org, make_user):
        from billing.admin_customers import admin_force_cancel

        admin = make_user(email="admin849@paciolus.com")
        admin_force_cancel(
            db_session,
            enterprise_org["org"].id,
            reason="Sprint 849",
            immediate=True,
            admin_user_id=admin.id,
        )

        member = enterprise_org["member"]
        assert _effective(member, db_session) == get_entitlements(UserTier.FREE)
        assert member.tier == UserTier.FREE
        assert enterprise_org["owner"].tier == UserTier.FREE

    def test_cancel_at_period_end_leaves_member_paid(self, db_session, enterprise_org, make_user):
        from billing.admin_customers import admin_force_cancel

        admin = make_user(email="admin849b@paciolus.com")
        admin_force_cancel(
            db_session,
            enterprise_org["org"].id,
            reason="Sprint 849",
            immediate=False,
            admin_user_id=admin.id,
        )

        member = enterprise_org["member"]
        assert _effective(member, db_session) == get_entitlements(UserTier.ENTERPRISE)
        assert member.tier == UserTier.ENTERPRISE


class TestSoloUserUnchanged:
    """A user in no organization resolves exactly as before Sprint 849."""

    @pytest.mark.parametrize(
        ("tier", "status", "expected"),
        [
            (UserTier.FREE, None, UserTier.FREE),
            (UserTier.SOLO, None, UserTier.SOLO),  # no row -> trust the tier
            (UserTier.SOLO, SubscriptionStatus.ACTIVE, UserTier.SOLO),
            (UserTier.ENTERPRISE, SubscriptionStatus.TRIALING, UserTier.ENTERPRISE),
            (UserTier.SOLO, SubscriptionStatus.PAST_DUE, UserTier.FREE),
            (UserTier.ENTERPRISE, SubscriptionStatus.CANCELED, UserTier.FREE),
        ],
    )
    def test_solo_user(self, db_session, make_user, tier, status, expected):
        user = make_user(email="solo849@example.com", tier=tier)
        if status is not None:
            db_session.add(
                Subscription(
                    user_id=user.id,
                    tier=tier.value,
                    status=status,
                    billing_interval=BillingInterval.MONTHLY,
                )
            )
            db_session.flush()

        assert user.organization_id is None
        assert _effective(user, db_session) == get_entitlements(expected)
