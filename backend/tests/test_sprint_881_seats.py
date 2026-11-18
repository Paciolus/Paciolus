"""Sprint 881 — included seats come from the plan (AZ-07).

Checkout sends the base plan with ``quantity: 1`` and sync stored that 1 as the plan's
included seats, so a Professional firm synced as 1 seat instead of 7 and an Enterprise firm
as 1 instead of 20. Included seats now come from the plan (``shared/entitlements.py``);
only the seat add-on item's quantity is added on top, and seats are bought on that item.

Fixtures are shaped like real Stripe ``subscription`` objects (API ``2025-03-31.basil``
and later: the billing period lives on each item).
"""

import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import UserTier
from organization_model import (
    INVITE_EXPIRY_HOURS,
    InviteStatus,
    Organization,
    OrganizationInvite,
    OrganizationMember,
    OrgRole,
)

# Price IDs as they would be configured on Render (test mode shape).
PRO_MONTHLY = "price_1QpRoMonthly0000000000aa"
ENT_MONTHLY = "price_1QpEnMonthly0000000000aa"
PRO_SEAT_MONTHLY = "price_1QpRoSeatMonthly000000aa"
ENT_SEAT_MONTHLY = "price_1QpEnSeatMonthly000000aa"


@pytest.fixture(autouse=True)
def _price_ids():
    # Patch the loaders, not the environment: the secrets manager caches the first
    # value it reads, so a developer's backend/.env would otherwise win.
    with (
        patch(
            "billing.price_config._load_stripe_price_ids",
            return_value={"professional": {"monthly": PRO_MONTHLY}, "enterprise": {"monthly": ENT_MONTHLY}},
        ),
        patch(
            "billing.price_config._load_pro_seat_price_ids", return_value={"monthly": PRO_SEAT_MONTHLY, "annual": ""}
        ),
        patch(
            "billing.price_config._load_ent_seat_price_ids", return_value={"monthly": ENT_SEAT_MONTHLY, "annual": ""}
        ),
    ):
        yield


def _price(price_id: str, unit_amount: int) -> dict:
    return {
        "id": price_id,
        "object": "price",
        "active": True,
        "currency": "usd",
        "livemode": False,
        "recurring": {"interval": "month", "interval_count": 1, "usage_type": "licensed"},
        "type": "recurring",
        "unit_amount": unit_amount,
    }


def _item(item_id: str, price_id: str, unit_amount: int, quantity: int, start: int, end: int) -> dict:
    return {
        "id": item_id,
        "object": "subscription_item",
        "price": _price(price_id, unit_amount),
        "plan": {"id": price_id, "object": "plan", "interval": "month", "amount": unit_amount},
        "quantity": quantity,
        "current_period_start": start,
        "current_period_end": end,
    }


def stripe_subscription(
    plan_price: str, plan_amount: int, seat_price: str | None, seat_amount: int, add_on_seats: int, status="active"
) -> dict:
    """A Stripe ``subscription`` object as Checkout creates it: base plan qty 1, seat add-on qty N."""
    start = int(time.time()) - 86400
    end = start + 30 * 86400
    items = [_item("si_base000000000001", plan_price, plan_amount, 1, start, end)]
    if seat_price and add_on_seats:
        items.append(_item("si_seat000000000001", seat_price, seat_amount, add_on_seats, start, end))
    return {
        "id": "sub_1QpTestSubscription00001",
        "object": "subscription",
        "customer": "cus_QpTestCustomer0001",
        "status": status,
        "cancel_at_period_end": False,
        "livemode": False,
        "metadata": {},
        "items": {"object": "list", "data": items, "has_more": False},
    }


def _sync(db_session, user, tier, stripe_sub):
    from billing.subscription_manager import sync_subscription_from_stripe

    return sync_subscription_from_stripe(db_session, user.id, stripe_sub, stripe_sub["customer"], tier)


def _org_for(db_session, owner, sub, slug):
    org = Organization(name=slug, slug=slug, owner_user_id=owner.id, subscription_id=sub.id)
    db_session.add(org)
    db_session.flush()
    db_session.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER))
    owner.organization_id = org.id
    db_session.flush()
    return org


def _add_members(db_session, make_user, org, count, prefix):
    for i in range(count):
        member = make_user(email=f"{prefix}{i}@example.com")
        db_session.add(OrganizationMember(organization_id=org.id, user_id=member.id, role=OrgRole.MEMBER))
    db_session.flush()


def _pending_invite(db_session, org, email, inviter):
    invite = OrganizationInvite(
        organization_id=org.id,
        invite_token_hash=email.encode().hex()[:64].ljust(64, "0"),
        invitee_email=email,
        role=OrgRole.MEMBER,
        status=InviteStatus.PENDING,
        invited_by_user_id=inviter.id,
        expires_at=datetime.now(UTC) + timedelta(hours=INVITE_EXPIRY_HOURS),
    )
    db_session.add(invite)
    db_session.flush()
    return invite


def _hard():
    return patch("shared.entitlement_checks._get_seat_enforcement_mode", return_value="hard")


# ---------------------------------------------------------------------------
# 6A (AZ-07): included seats come from the plan
# ---------------------------------------------------------------------------


class TestIncludedSeatsFromPlan:
    @pytest.mark.parametrize(
        ("tier", "plan_price", "amount", "seat_price", "seat_amount", "add_ons", "expected"),
        [
            ("professional", PRO_MONTHLY, 50000, PRO_SEAT_MONTHLY, 6500, 0, 7),
            ("professional", PRO_MONTHLY, 50000, PRO_SEAT_MONTHLY, 6500, 2, 9),
            ("enterprise", ENT_MONTHLY, 100000, ENT_SEAT_MONTHLY, 4500, 0, 20),
            ("enterprise", ENT_MONTHLY, 100000, ENT_SEAT_MONTHLY, 4500, 2, 22),
        ],
    )
    def test_sync_totals(
        self, db_session, make_user, tier, plan_price, amount, seat_price, seat_amount, add_ons, expected
    ):
        user = make_user(email=f"az07_{tier}_{add_ons}@example.com", tier=UserTier(tier))
        sub = _sync(db_session, user, tier, stripe_subscription(plan_price, amount, seat_price, seat_amount, add_ons))
        assert sub.additional_seats == add_ons
        assert sub.total_seats == expected

    def test_resync_keeps_plan_seats(self, db_session, make_user):
        """A second webhook for the same subscription does not fall back to Stripe's quantity."""
        user = make_user(email="az07_resync@example.com")
        payload = stripe_subscription(PRO_MONTHLY, 50000, PRO_SEAT_MONTHLY, 6500, 2)
        _sync(db_session, user, "professional", payload)
        sub = _sync(db_session, user, "professional", payload)
        assert sub.seat_count == 7
        assert sub.total_seats == 9

    @pytest.mark.parametrize(
        ("tier", "plan_price", "amount", "seat_price", "seat_amount", "add_ons", "total"),
        [
            ("professional", PRO_MONTHLY, 50000, PRO_SEAT_MONTHLY, 6500, 0, 7),
            ("professional", PRO_MONTHLY, 50000, PRO_SEAT_MONTHLY, 6500, 2, 9),
            ("enterprise", ENT_MONTHLY, 100000, ENT_SEAT_MONTHLY, 4500, 0, 20),
            ("enterprise", ENT_MONTHLY, 100000, ENT_SEAT_MONTHLY, 4500, 2, 22),
        ],
    )
    def test_invitations_admitted_against_total(
        self, db_session, make_user, tier, plan_price, amount, seat_price, seat_amount, add_ons, total
    ):
        """With total - 1 seats used one more invite is admitted; once it is pending, the next is refused."""
        from shared.entitlement_checks import check_seat_limit_for_org

        prefix = f"az07inv_{tier}_{add_ons}_"
        owner = make_user(email=f"{prefix}owner@example.com", tier=UserTier(tier))
        sub = _sync(db_session, owner, tier, stripe_subscription(plan_price, amount, seat_price, seat_amount, add_ons))
        org = _org_for(db_session, owner, sub, prefix.rstrip("_").replace("_", "-"))
        _add_members(db_session, make_user, org, total - 2, f"{prefix}m")

        with _hard():
            check_seat_limit_for_org(db_session, org.id)  # total - 1 used: one seat left
            _pending_invite(db_session, org, f"{prefix}last@example.com", owner)
            with pytest.raises(HTTPException) as exc:
                check_seat_limit_for_org(db_session, org.id)  # all seats used
        assert exc.value.status_code == 403
        assert f"({total}/{total})" in exc.value.detail["message"]


class TestSeatAddOnNeverChangesThePlanQuantity:
    """The base plan item is one plan. Seats are bought on the seat add-on item only."""

    def _sub(self, db_session, user, additional=0):
        from billing.subscription_manager import sync_subscription_from_stripe

        payload = stripe_subscription(PRO_MONTHLY, 50000, PRO_SEAT_MONTHLY, 6500, additional)
        sub = sync_subscription_from_stripe(db_session, user.id, payload, payload["customer"], "professional")
        return sub, payload

    def test_first_add_on_creates_the_seat_item(self, db_session, make_user):
        from unittest.mock import ANY, MagicMock

        from billing.subscription_manager import add_seats

        user = make_user(email="az07_first_addon@example.com")
        sub, payload = self._sub(db_session, user)
        stripe = MagicMock()
        stripe.Subscription.retrieve.return_value = payload  # base item only
        with patch("billing.subscription_manager.get_stripe", return_value=stripe):
            result = add_seats(db_session, user.id, 2)

        stripe.SubscriptionItem.modify.assert_not_called()
        stripe.SubscriptionItem.create.assert_called_once_with(
            subscription=payload["id"], price=PRO_SEAT_MONTHLY, quantity=2, idempotency_key=ANY
        )
        assert result.additional_seats == 2
        assert result.total_seats == 9

    def test_removing_seats_without_a_seat_item_does_not_touch_the_plan(self, db_session, make_user):
        from unittest.mock import MagicMock

        from billing.subscription_manager import remove_seats

        user = make_user(email="az07_rm_noitem@example.com")
        sub, payload = self._sub(db_session, user)
        sub.additional_seats = 1  # local row says 1 add-on; Stripe has no seat item
        db_session.flush()
        stripe = MagicMock()
        stripe.Subscription.retrieve.return_value = payload
        with patch("billing.subscription_manager.get_stripe", return_value=stripe):
            with pytest.raises(ValueError):
                remove_seats(db_session, user.id, 1)
        stripe.SubscriptionItem.modify.assert_not_called()
        stripe.SubscriptionItem.delete.assert_not_called()

    def test_add_seats_limit_counts_plan_seats(self, db_session, make_user):
        """Professional allows 20 in total: 7 included + 13 add-ons fits, a 14th add-on does not."""
        from unittest.mock import MagicMock

        from billing.subscription_manager import add_seats

        user = make_user(email="az07_limit@example.com")
        self._sub(db_session, user, additional=13)
        stripe = MagicMock()
        with patch("billing.subscription_manager.get_stripe", return_value=stripe):
            assert add_seats(db_session, user.id, 1) is None
        stripe.Subscription.retrieve.assert_not_called()
