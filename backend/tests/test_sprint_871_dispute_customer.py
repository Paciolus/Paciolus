"""Sprint 871 (#273): Stripe dispute webhooks must find the customer.

Stripe's Dispute object carries no ``customer`` and a webhook delivers
``charge`` as a ``ch_...`` string. The handlers read ``customer`` and only
looked inside ``charge`` when it was an expanded dict, so every real dispute
logged "could not resolve customer_id" and returned: no suspension on open, no
restore/cancel on close, no DISPUTE_* billing events.

These tests use real ``stripe.Dispute`` / ``stripe.Charge`` / ``PaymentIntent``
objects (offline, ``construct_from``) so the shape is the SDK's, not ours.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest
import stripe

from billing.stripe_client import to_plain_dict
from billing.webhook_handler import handle_dispute_closed, handle_dispute_created
from models import UserTier
from subscription_model import (
    BillingEvent,
    BillingEventType,
    BillingInterval,
    ProcessedWebhookEvent,
    Subscription,
    SubscriptionStatus,
)

CUSTOMER = "cus_sprint871"
CHARGE = "ch_sprint871"
PAYMENT_INTENT = "pi_sprint871"


def _dispute(**fields) -> dict:
    """A Dispute as the webhook delivers it, through the real SDK object."""
    payload = {
        "id": "dp_sprint871",
        "object": "dispute",
        "amount": 10000,
        "charge": CHARGE,
        "payment_intent": PAYMENT_INTENT,
        "reason": "fraudulent",
        "status": "needs_response",
        **fields,
    }
    return to_plain_dict(stripe.Dispute.construct_from(payload, None))


def _fake_stripe(charge_customer=CUSTOMER, pi_customer=None, charge_error=None) -> MagicMock:
    fake = MagicMock()
    if charge_error is not None:
        fake.Charge.retrieve.side_effect = charge_error
    else:
        fake.Charge.retrieve.return_value = stripe.Charge.construct_from(
            {"id": CHARGE, "object": "charge", "customer": charge_customer}, None
        )
    fake.PaymentIntent.retrieve.return_value = stripe.PaymentIntent.construct_from(
        {"id": PAYMENT_INTENT, "object": "payment_intent", "customer": pi_customer}, None
    )
    return fake


@pytest.fixture()
def subscribed_user(db_session, make_user):
    user = make_user(email="sprint871@example.com", tier=UserTier.SOLO)
    sub = Subscription(
        user_id=user.id,
        tier="solo",
        status=SubscriptionStatus.ACTIVE,
        billing_interval=BillingInterval.MONTHLY,
        stripe_customer_id=CUSTOMER,
        stripe_subscription_id="sub_sprint871",
    )
    db_session.add(sub)
    db_session.flush()
    return user, sub


def _events(db_session, user_id):
    return [e.event_type for e in db_session.query(BillingEvent).filter(BillingEvent.user_id == user_id).all()]


def test_real_dispute_shape_has_no_customer():
    """The premise of #273, pinned against the installed SDK's object."""
    dispute = _dispute()
    assert "customer" not in dispute
    assert dispute["charge"] == CHARGE


def test_created_resolves_customer_through_the_charge(db_session, subscribed_user):
    user, sub = subscribed_user
    fake = _fake_stripe()
    with patch("billing.stripe_client.get_stripe", return_value=fake):
        handle_dispute_created(db_session, _dispute())

    fake.Charge.retrieve.assert_called_once_with(CHARGE)
    assert sub.status == SubscriptionStatus.PAUSED
    assert user.tier == UserTier.FREE
    assert _events(db_session, user.id) == [BillingEventType.DISPUTE_CREATED]


@pytest.mark.parametrize(
    ("status", "expected_status", "expected_tier", "expected_event"),
    [
        ("won", SubscriptionStatus.ACTIVE, UserTier.SOLO, BillingEventType.DISPUTE_RESOLVED_WON),
        ("lost", SubscriptionStatus.CANCELED, UserTier.FREE, BillingEventType.DISPUTE_RESOLVED_LOST),
    ],
)
def test_closed_resolves_customer_through_the_charge(
    db_session, subscribed_user, status, expected_status, expected_tier, expected_event
):
    user, sub = subscribed_user
    sub.status = SubscriptionStatus.PAUSED
    user.tier = UserTier.FREE
    with patch("billing.stripe_client.get_stripe", return_value=_fake_stripe()):
        handle_dispute_closed(db_session, _dispute(status=status))

    assert sub.status == expected_status
    assert user.tier == expected_tier
    assert _events(db_session, user.id) == [expected_event]


def test_falls_back_to_the_payment_intent(db_session, subscribed_user):
    user, sub = subscribed_user
    fake = _fake_stripe(charge_customer=None, pi_customer=CUSTOMER)
    with patch("billing.stripe_client.get_stripe", return_value=fake):
        handle_dispute_created(db_session, _dispute())

    fake.PaymentIntent.retrieve.assert_called_once_with(PAYMENT_INTENT)
    assert sub.status == SubscriptionStatus.PAUSED


def test_expanded_customer_object_is_read_by_id(db_session, subscribed_user):
    _user, sub = subscribed_user
    fake = MagicMock()
    fake.Charge.retrieve.return_value = stripe.Charge.construct_from(
        {"id": CHARGE, "object": "charge", "customer": {"id": CUSTOMER, "object": "customer"}}, None
    )
    with patch("billing.stripe_client.get_stripe", return_value=fake):
        handle_dispute_created(db_session, _dispute())
    assert sub.status == SubscriptionStatus.PAUSED


def test_expanded_charge_needs_no_lookup(db_session, subscribed_user):
    _user, sub = subscribed_user
    fake = _fake_stripe()
    with patch("billing.stripe_client.get_stripe", return_value=fake):
        handle_dispute_created(db_session, _dispute(charge={"id": CHARGE, "object": "charge", "customer": CUSTOMER}))
    fake.Charge.retrieve.assert_not_called()
    assert sub.status == SubscriptionStatus.PAUSED


def test_guest_charge_changes_nothing(db_session, subscribed_user):
    user, sub = subscribed_user
    with patch("billing.stripe_client.get_stripe", return_value=_fake_stripe(charge_customer=None)):
        handle_dispute_created(db_session, _dispute())
    assert sub.status == SubscriptionStatus.ACTIVE
    assert _events(db_session, user.id) == []


def test_stripe_lookup_failure_propagates_not_swallowed(db_session, subscribed_user):
    fake = _fake_stripe(charge_error=stripe.APIConnectionError("network down"))
    with patch("billing.stripe_client.get_stripe", return_value=fake), pytest.raises(stripe.APIConnectionError):
        handle_dispute_created(db_session, _dispute())


@pytest.mark.asyncio
async def test_lookup_failure_returns_500_and_unclaims_the_event(db_session, subscribed_user):
    """Through the route: a Stripe outage must make Stripe redeliver, not drop the dispute."""
    from database import get_db
    from main import app

    fake = _fake_stripe(charge_error=stripe.APIConnectionError("network down"))
    fake.error.SignatureVerificationError = stripe.error.SignatureVerificationError
    fake.Webhook.construct_event.return_value = {
        "id": "evt_sprint871_outage",
        "type": "charge.dispute.created",
        "created": 1_700_000_000,
        "data": {"object": _dispute()},
    }
    with (
        patch("billing.stripe_client.is_stripe_enabled", return_value=True),
        patch("billing.stripe_client.get_stripe", return_value=fake),
        patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
    ):
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b"{}",
                    headers={"stripe-signature": "t=1,v1=sig", "content-type": "application/json"},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 500
    claimed = (
        db_session.query(ProcessedWebhookEvent)
        .filter(ProcessedWebhookEvent.stripe_event_id == "evt_sprint871_outage")
        .first()
    )
    assert claimed is None  # rolled back, so the redelivery is processed
    # The 500 came from the lookup, not from something earlier in the route.
    fake.Charge.retrieve.assert_called_once_with(CHARGE)
