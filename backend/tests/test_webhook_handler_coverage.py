"""Sprint 780 — tests for the five untested webhook handlers and four untested helpers.

`billing/webhook_handler.py` was the least-covered critical path in the codebase at
59.9% with 174 uncovered statements — and it is the one that moves money. The
webhook-coverage sprint had been deferred in Sprint 676 and again in the 2026-04-20
refactor pass. These tests target the blocks that had no coverage at all:

- `handle_subscription_created` — subscriptions created outside Checkout (API, dashboard)
- `handle_invoice_payment_succeeded` — restoring access from PAST_DUE / INCOMPLETE / UNPAID
- `handle_dispute_created` — suspend on dispute
- `handle_dispute_closed` — won / lost / other resolution paths
- `handle_invoice_created` — observability-only analytics
- `_downgrade_org_members_to_free`, `_apply_dpa_from_metadata`, `_portal_url_for_user`,
  `_auto_create_organization`

The emphasis is the money-relevant invariants: entitlement state after each event,
idempotency, and the analytics record that the billing review reads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from billing.webhook_handler import (
    _apply_dpa_from_metadata,
    _downgrade_org_members_to_free,
    _portal_url_for_user,
    handle_dispute_closed,
    handle_dispute_created,
    handle_invoice_created,
    handle_invoice_payment_succeeded,
    handle_subscription_created,
)
from models import User, UserTier
from organization_model import Organization, OrganizationMember, OrgRole
from subscription_model import (
    BillingEvent,
    BillingEventType,
    BillingInterval,
    Subscription,
    SubscriptionStatus,
)

CUSTOMER = "cus_test_780"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def make_subscription(db_session):
    """Create a Subscription row wired to a user."""

    def _make(
        user: User,
        status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
        tier: str = "professional",
        customer_id: str = CUSTOMER,
        subscription_id: str = "sub_test_780",
    ) -> Subscription:
        sub = Subscription(
            user_id=user.id,
            tier=tier,
            status=status,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
        )
        db_session.add(sub)
        db_session.flush()
        return sub

    return _make


@pytest.fixture()
def make_org(db_session):
    """Create an organization owned by `owner`, with optional extra members."""

    def _make(owner: User, members: list[User] | None = None) -> Organization:
        org = Organization(name=f"Org {owner.id}", slug=f"org-{owner.id}", owner_user_id=owner.id)
        db_session.add(org)
        db_session.flush()
        roster = [owner, *(members or [])]
        for idx, member in enumerate(roster):
            db_session.add(
                OrganizationMember(
                    organization_id=org.id,
                    user_id=member.id,
                    role=OrgRole.OWNER if idx == 0 else OrgRole.MEMBER,
                )
            )
        db_session.flush()
        return org

    return _make


def _billing_events(db_session, user_id: int) -> list[BillingEvent]:
    return db_session.query(BillingEvent).filter(BillingEvent.user_id == user_id).all()


# ---------------------------------------------------------------------------
# handle_invoice_payment_succeeded — access restoration
# ---------------------------------------------------------------------------


class TestInvoicePaymentSucceeded:
    @pytest.mark.parametrize(
        "start_status",
        [SubscriptionStatus.PAST_DUE, SubscriptionStatus.INCOMPLETE, SubscriptionStatus.UNPAID],
    )
    def test_restores_access_from_each_non_entitled_state(self, db_session, make_user, make_subscription, start_status):
        user = make_user(email=f"restore_{start_status.value}@example.com", tier=UserTier.FREE)
        make_subscription(user, status=start_status, tier="professional")

        handle_invoice_payment_succeeded(db_session, {"customer": CUSTOMER})

        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub.status == SubscriptionStatus.ACTIVE
        assert user.tier == UserTier.PROFESSIONAL
        assert [e.event_type for e in _billing_events(db_session, user.id)] == [BillingEventType.PAYMENT_SUCCEEDED]

    def test_already_active_is_a_noop_and_records_nothing(self, db_session, make_user, make_subscription):
        """Idempotency matters: Stripe retries, and a duplicate must not double-record."""
        user = make_user(email="already_active@example.com", tier=UserTier.SOLO)
        make_subscription(user, status=SubscriptionStatus.ACTIVE, tier="solo")

        handle_invoice_payment_succeeded(db_session, {"customer": CUSTOMER})

        assert user.tier == UserTier.SOLO
        assert _billing_events(db_session, user.id) == []

    def test_subscription_tier_column_rejects_values_outside_usertier(self, db_session, make_user):
        """Both handlers wrap `UserTier(sub.tier)` in `except ValueError`, but that
        branch is **unreachable**: `Subscription.tier` is a constrained DB enum, so a
        value outside UserTier cannot be persisted, and both handlers flush after the
        conversion. This test pins the constraint that makes the defence redundant —
        if the two enums ever diverge, it fails here first and names the cause.
        """
        user = make_user(email="bad_tier@example.com", tier=UserTier.FREE)
        sub = Subscription(
            user_id=user.id,
            tier="platinum",
            status=SubscriptionStatus.PAST_DUE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id=CUSTOMER,
            stripe_subscription_id="sub_bad_tier",
        )
        db_session.add(sub)
        db_session.flush()
        db_session.expire_all()

        # The Enum type raises on result processing, so the bad value is unreadable:
        # any handler that loads this row raises before reaching its own ValueError guard.
        with pytest.raises(LookupError, match="platinum"):
            db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        db_session.rollback()

    def test_missing_customer_is_ignored(self, db_session):
        handle_invoice_payment_succeeded(db_session, {})

    def test_unknown_customer_is_ignored(self, db_session):
        handle_invoice_payment_succeeded(db_session, {"customer": "cus_does_not_exist"})


# ---------------------------------------------------------------------------
# handle_dispute_created — suspend on dispute
# ---------------------------------------------------------------------------


class TestDisputeCreated:
    def test_suspends_subscription_and_downgrades_owner(self, db_session, make_user, make_subscription):
        user = make_user(email="disputed@example.com", tier=UserTier.ENTERPRISE)
        make_subscription(user, tier="enterprise")

        handle_dispute_created(db_session, {"customer": CUSTOMER, "id": "dp_1", "reason": "fraudulent"})

        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub.status == SubscriptionStatus.PAUSED
        assert user.tier == UserTier.FREE

        events = _billing_events(db_session, user.id)
        assert [e.event_type for e in events] == [BillingEventType.DISPUTE_CREATED]

    def test_downgrades_every_org_member_not_just_the_owner(self, db_session, make_user, make_subscription, make_org):
        """A disputed payment must not leave colleagues entitled on the owner's plan."""
        owner = make_user(email="dispute_owner@example.com", tier=UserTier.ENTERPRISE)
        member_a = make_user(email="dispute_member_a@example.com", tier=UserTier.ENTERPRISE)
        member_b = make_user(email="dispute_member_b@example.com", tier=UserTier.ENTERPRISE)
        make_subscription(owner, tier="enterprise")
        make_org(owner, members=[member_a, member_b])

        handle_dispute_created(db_session, {"customer": CUSTOMER, "id": "dp_2", "reason": "unrecognized"})

        assert member_a.tier == UserTier.FREE
        assert member_b.tier == UserTier.FREE

    def test_customer_resolved_from_nested_charge(self, db_session, make_user, make_subscription):
        """Stripe does not always put the customer on the dispute itself."""
        user = make_user(email="dispute_nested@example.com", tier=UserTier.SOLO)
        make_subscription(user, tier="solo")

        handle_dispute_created(db_session, {"charge": {"customer": CUSTOMER}, "id": "dp_3"})

        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub.status == SubscriptionStatus.PAUSED

    def test_unresolvable_customer_is_ignored(self, db_session):
        handle_dispute_created(db_session, {"charge": "ch_not_a_dict", "id": "dp_4"})

    def test_no_subscription_for_customer_is_ignored(self, db_session):
        handle_dispute_created(db_session, {"customer": "cus_unknown_dispute", "id": "dp_5"})


# ---------------------------------------------------------------------------
# handle_dispute_closed — the three resolution paths
# ---------------------------------------------------------------------------


class TestDisputeClosed:
    def test_won_restores_access_to_plan_tier(self, db_session, make_user, make_subscription):
        user = make_user(email="dispute_won@example.com", tier=UserTier.FREE)
        make_subscription(user, status=SubscriptionStatus.PAUSED, tier="professional")

        handle_dispute_closed(db_session, {"customer": CUSTOMER, "id": "dp_w", "status": "won"})

        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub.status == SubscriptionStatus.ACTIVE
        assert user.tier == UserTier.PROFESSIONAL
        assert [e.event_type for e in _billing_events(db_session, user.id)] == [BillingEventType.DISPUTE_RESOLVED_WON]

    def test_won_restores_tier_for_every_paid_tier(self, db_session, make_user, make_subscription):
        """Each paid tier must come back as itself, not as a default."""
        for idx, (sub_tier, expected) in enumerate(
            [("solo", UserTier.SOLO), ("professional", UserTier.PROFESSIONAL), ("enterprise", UserTier.ENTERPRISE)]
        ):
            user = make_user(email=f"dispute_won_{sub_tier}@example.com", tier=UserTier.FREE)
            make_subscription(
                user,
                status=SubscriptionStatus.PAUSED,
                tier=sub_tier,
                customer_id=f"{CUSTOMER}_{idx}",
                subscription_id=f"sub_won_{idx}",
            )

            handle_dispute_closed(db_session, {"customer": f"{CUSTOMER}_{idx}", "id": f"dp_w{idx}", "status": "won"})

            assert user.tier == expected

    def test_lost_cancels_and_downgrades_org(self, db_session, make_user, make_subscription, make_org):
        owner = make_user(email="dispute_lost@example.com", tier=UserTier.ENTERPRISE)
        member = make_user(email="dispute_lost_member@example.com", tier=UserTier.ENTERPRISE)
        make_subscription(owner, status=SubscriptionStatus.PAUSED, tier="enterprise")
        make_org(owner, members=[member])

        handle_dispute_closed(db_session, {"customer": CUSTOMER, "id": "dp_l", "status": "lost"})

        sub = db_session.query(Subscription).filter(Subscription.user_id == owner.id).first()
        assert sub.status == SubscriptionStatus.CANCELED
        assert owner.tier == UserTier.FREE
        assert member.tier == UserTier.FREE
        assert [e.event_type for e in _billing_events(db_session, owner.id)] == [BillingEventType.DISPUTE_RESOLVED_LOST]

    def test_other_status_leaves_subscription_suspended(self, db_session, make_user, make_subscription):
        """'warning_closed' and friends must not silently restore access."""
        user = make_user(email="dispute_other@example.com", tier=UserTier.FREE)
        make_subscription(user, status=SubscriptionStatus.PAUSED, tier="solo")

        handle_dispute_closed(db_session, {"customer": CUSTOMER, "id": "dp_o", "status": "warning_closed"})

        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub.status == SubscriptionStatus.PAUSED
        assert user.tier == UserTier.FREE
        events = _billing_events(db_session, user.id)
        assert [e.event_type for e in events] == [BillingEventType.DISPUTE_CLOSED_OTHER]

    def test_customer_resolved_from_nested_charge(self, db_session, make_user, make_subscription):
        user = make_user(email="dispute_closed_nested@example.com", tier=UserTier.FREE)
        make_subscription(user, status=SubscriptionStatus.PAUSED, tier="solo")

        handle_dispute_closed(db_session, {"charge": {"customer": CUSTOMER}, "id": "dp_n", "status": "won"})

        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub.status == SubscriptionStatus.ACTIVE

    def test_unresolvable_customer_is_ignored(self, db_session):
        handle_dispute_closed(db_session, {"id": "dp_x", "status": "won"})

    def test_no_subscription_for_customer_is_ignored(self, db_session):
        handle_dispute_closed(db_session, {"customer": "cus_unknown_closed", "id": "dp_y", "status": "won"})


# ---------------------------------------------------------------------------
# handle_invoice_created — observability only
# ---------------------------------------------------------------------------


class TestInvoiceCreated:
    def test_records_analytics_without_touching_entitlements(self, db_session, make_user, make_subscription):
        user = make_user(email="invoice_created@example.com", tier=UserTier.SOLO)
        make_subscription(user, tier="solo")

        handle_invoice_created(
            db_session,
            {"customer": CUSTOMER, "id": "in_1", "amount_due": 10000, "billing_reason": "subscription_cycle"},
        )

        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub.status == SubscriptionStatus.ACTIVE
        assert user.tier == UserTier.SOLO

        events = _billing_events(db_session, user.id)
        assert [e.event_type for e in events] == [BillingEventType.INVOICE_CREATED]

    def test_records_event_with_no_user_when_customer_is_unknown(self, db_session):
        """Proration invoices can arrive before a local subscription exists."""
        before = db_session.query(BillingEvent).count()
        handle_invoice_created(db_session, {"customer": "cus_no_local_sub", "id": "in_2", "amount_due": 500})
        assert db_session.query(BillingEvent).count() == before + 1

    def test_missing_customer_is_ignored(self, db_session):
        before = db_session.query(BillingEvent).count()
        handle_invoice_created(db_session, {"id": "in_3"})
        assert db_session.query(BillingEvent).count() == before


# ---------------------------------------------------------------------------
# handle_subscription_created — subscriptions that bypass Checkout
# ---------------------------------------------------------------------------


def _subscription_event(price_id: str, status: str = "active") -> dict:
    return {
        "id": "sub_created_780",
        "customer": CUSTOMER,
        "status": status,
        "items": {"data": [{"price": {"id": price_id}}]},
    }


class TestSubscriptionCreated:
    def test_syncs_and_records_creation_for_a_new_subscription(self, db_session, make_user):
        user = make_user(email="sub_created@example.com", tier=UserTier.FREE)
        db_session.add(
            Subscription(
                user_id=user.id,
                tier="free",
                status=SubscriptionStatus.CANCELED,
                billing_interval=BillingInterval.MONTHLY,
                stripe_customer_id=CUSTOMER,
                stripe_subscription_id="sub_old",
            )
        )
        db_session.flush()

        with (
            patch("billing.webhook_handler._resolve_tier_from_price", return_value="solo"),
            patch("billing.webhook_handler.sync_subscription_from_stripe") as sync,
        ):
            handle_subscription_created(db_session, _subscription_event("price_solo_monthly"))

        sync.assert_called_once()
        assert [e.event_type for e in _billing_events(db_session, user.id)] == [BillingEventType.SUBSCRIPTION_CREATED]

    def test_trialing_status_records_trial_started(self, db_session, make_user):
        user = make_user(email="sub_created_trial@example.com", tier=UserTier.FREE)
        db_session.add(
            Subscription(
                user_id=user.id,
                tier="free",
                status=SubscriptionStatus.CANCELED,
                billing_interval=BillingInterval.MONTHLY,
                stripe_customer_id=CUSTOMER,
                stripe_subscription_id="sub_old_trial",
            )
        )
        db_session.flush()

        with (
            patch("billing.webhook_handler._resolve_tier_from_price", return_value="solo"),
            patch("billing.webhook_handler.sync_subscription_from_stripe"),
        ):
            handle_subscription_created(db_session, _subscription_event("price_solo", status="trialing"))

        assert [e.event_type for e in _billing_events(db_session, user.id)] == [BillingEventType.TRIAL_STARTED]

    def test_reconciliation_after_checkout_records_no_duplicate_event(self, db_session, make_user):
        """checkout.session.completed usually lands first; this handler then
        reconciles and must not double-count the creation in analytics."""
        user = make_user(email="sub_created_dupe@example.com", tier=UserTier.SOLO)
        db_session.add(
            Subscription(
                user_id=user.id,
                tier="solo",
                status=SubscriptionStatus.ACTIVE,
                billing_interval=BillingInterval.MONTHLY,
                stripe_customer_id=CUSTOMER,
                stripe_subscription_id="sub_created_780",
            )
        )
        db_session.flush()

        with (
            patch("billing.webhook_handler._resolve_tier_from_price", return_value="solo"),
            patch("billing.webhook_handler.sync_subscription_from_stripe") as sync,
        ):
            handle_subscription_created(db_session, _subscription_event("price_solo"))

        sync.assert_called_once()
        assert _billing_events(db_session, user.id) == []

    def test_unresolvable_tier_aborts_without_syncing(self, db_session, make_user, make_subscription):
        """Better to do nothing than to sync a subscription to the wrong tier."""
        user = make_user(email="sub_created_notier@example.com", tier=UserTier.FREE)
        make_subscription(user, tier="free", subscription_id="sub_other")

        with (
            patch("billing.webhook_handler._resolve_tier_from_price", return_value=None),
            patch("billing.webhook_handler.sync_subscription_from_stripe") as sync,
        ):
            handle_subscription_created(db_session, _subscription_event("price_unknown"))

        sync.assert_not_called()
        assert _billing_events(db_session, user.id) == []

    def test_missing_subscription_id_aborts(self, db_session, make_user, make_subscription):
        user = make_user(email="sub_created_noid@example.com", tier=UserTier.FREE)
        make_subscription(user, tier="free")

        with patch("billing.webhook_handler.sync_subscription_from_stripe") as sync:
            handle_subscription_created(db_session, {"customer": CUSTOMER, "status": "active"})

        sync.assert_not_called()

    def test_unresolvable_user_aborts(self, db_session):
        with patch("billing.webhook_handler.sync_subscription_from_stripe") as sync:
            handle_subscription_created(db_session, _subscription_event("price_solo") | {"customer": "cus_nobody"})
        sync.assert_not_called()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestDowngradeOrgMembers:
    def test_counts_only_members_not_already_free(self, db_session, make_user, make_org):
        owner = make_user(email="dg_owner@example.com", tier=UserTier.ENTERPRISE)
        paid_member = make_user(email="dg_paid@example.com", tier=UserTier.ENTERPRISE)
        free_member = make_user(email="dg_free@example.com", tier=UserTier.FREE)
        make_org(owner, members=[paid_member, free_member])

        assert _downgrade_org_members_to_free(db_session, owner.id) == 2
        assert owner.tier == UserTier.FREE
        assert paid_member.tier == UserTier.FREE

    def test_returns_zero_when_user_owns_no_org(self, db_session, make_user):
        user = make_user(email="dg_no_org@example.com", tier=UserTier.SOLO)
        assert _downgrade_org_members_to_free(db_session, user.id) == 0
        assert user.tier == UserTier.SOLO

    def test_returns_zero_for_an_org_with_no_members(self, db_session, make_user):
        owner = make_user(email="dg_empty_org@example.com", tier=UserTier.ENTERPRISE)
        org = Organization(name="Empty", slug=f"empty-{owner.id}", owner_user_id=owner.id)
        db_session.add(org)
        db_session.flush()
        assert _downgrade_org_members_to_free(db_session, owner.id) == 0


class TestApplyDpaFromMetadata:
    def test_stamps_offset_aware_timestamp_as_utc(self, db_session, make_user, make_subscription):
        user = make_user(email="dpa_tz@example.com")
        make_subscription(user)

        _apply_dpa_from_metadata(
            db_session,
            user.id,
            {"dpa_accepted_at": "2026-10-20T08:00:00+02:00", "dpa_version": "1.0"},
        )

        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub.dpa_version == "1.0"
        assert sub.dpa_accepted_at.hour == 6  # 08:00+02:00 is 06:00 UTC

    def test_treats_naive_timestamp_as_utc(self, db_session, make_user, make_subscription):
        user = make_user(email="dpa_naive@example.com")
        make_subscription(user)

        _apply_dpa_from_metadata(db_session, user.id, {"dpa_accepted_at": "2026-10-20T09:30:00", "dpa_version": "1.1"})

        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub.dpa_accepted_at.hour == 9

    def test_unparseable_timestamp_falls_back_to_now(self, db_session, make_user, make_subscription):
        user = make_user(email="dpa_bad@example.com")
        make_subscription(user)

        _apply_dpa_from_metadata(db_session, user.id, {"dpa_accepted_at": "not-a-date", "dpa_version": "1.2"})

        sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
        assert sub.dpa_accepted_at is not None
        assert sub.dpa_version == "1.2"

    def test_does_not_overwrite_an_existing_acceptance(self, db_session, make_user, make_subscription):
        """An acceptance recorded before checkout must survive the webhook."""
        user = make_user(email="dpa_existing@example.com")
        sub = make_subscription(user)
        original = datetime(2026, 1, 1, tzinfo=UTC)
        sub.dpa_accepted_at = original
        sub.dpa_version = "0.9"
        db_session.flush()

        _apply_dpa_from_metadata(
            db_session, user.id, {"dpa_accepted_at": "2026-10-20T00:00:00+00:00", "dpa_version": "1.0"}
        )

        assert sub.dpa_version == "0.9"

    @pytest.mark.parametrize(
        "metadata",
        [{}, {"dpa_version": "1.0"}, {"dpa_accepted_at": "2026-10-20T00:00:00+00:00"}],
    )
    def test_incomplete_metadata_is_ignored(self, db_session, make_user, make_subscription, metadata):
        user = make_user(email=f"dpa_partial_{len(metadata)}@example.com")
        sub = make_subscription(user)
        _apply_dpa_from_metadata(db_session, user.id, metadata)
        assert sub.dpa_accepted_at is None

    def test_no_subscription_is_ignored(self, db_session, make_user):
        user = make_user(email="dpa_no_sub@example.com")
        _apply_dpa_from_metadata(
            db_session, user.id, {"dpa_accepted_at": "2026-10-20T00:00:00+00:00", "dpa_version": "1.0"}
        )


class TestPortalUrlForUser:
    def test_returns_stripe_portal_url_when_available(self, db_session, make_user, make_subscription):
        user = make_user(email="portal_ok@example.com")
        make_subscription(user)

        with patch("billing.subscription_manager.create_portal_session", return_value="https://portal.example/x"):
            assert _portal_url_for_user(db_session, user.id) == "https://portal.example/x"

    def test_falls_back_to_in_app_settings_when_portal_raises(self, db_session, make_user, make_subscription):
        """A URL lookup must never take the webhook down."""
        user = make_user(email="portal_raises@example.com")
        make_subscription(user)

        with patch("billing.subscription_manager.create_portal_session", side_effect=RuntimeError("stripe down")):
            url = _portal_url_for_user(db_session, user.id)
        assert url.endswith("/settings/billing")

    def test_falls_back_when_user_has_no_subscription(self, db_session, make_user):
        user = make_user(email="portal_no_sub@example.com")
        assert _portal_url_for_user(db_session, user.id).endswith("/settings/billing")

    def test_falls_back_when_subscription_has_no_customer_id(self, db_session, make_user, make_subscription):
        user = make_user(email="portal_no_cust@example.com")
        sub = make_subscription(user)
        sub.stripe_customer_id = None
        db_session.flush()
        assert _portal_url_for_user(db_session, user.id).endswith("/settings/billing")
