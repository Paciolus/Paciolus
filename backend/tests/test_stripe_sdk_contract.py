"""
Stripe SDK contract tests — Sprint 786b (stripe 15 -> 16).

Every other billing test replaces the ``stripe`` module with a ``MagicMock``,
so none of them can notice an SDK major changing a class name, the shape of a
``StripeObject`` or the API version it pins. These tests exercise the *real*
installed SDK, offline: no API key is used and no request is sent.

What they pin down:
- the SDK major and the API version it sends, so the next major bump fails
  here first and gets a deliberate review;
- ``Webhook.construct_event`` + ``stripe.error.SignatureVerificationError``,
  the exact names ``routes/billing.py`` uses;
- that a real ``StripeObject`` (not a plain dict) flows through the handlers'
  ``.get(...)`` access pattern;
- the basil-and-later Subscription shape (billing period on the items, not the
  subscription), which ``Subscription.retrieve`` returns under the pinned API;
- the Checkout Session params accepted by ``2026-09-30.endive``.
"""

import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
import stripe

from models import UserTier
from subscription_model import BillingInterval

_WEBHOOK_SECRET = "whsec_FAKE_SECRET_FOR_CONTRACT_TESTS"
# Relative to now, never hardcoded (see the inventory wall-clock time bomb).
_PERIOD_START = int(time.time()) - 86_400
_PERIOD_END = _PERIOD_START + 30 * 86_400
# A different period, so a test can tell which source the sync read.
_LEGACY_START = _PERIOD_START - 7 * 86_400
_LEGACY_END = _LEGACY_START + 30 * 86_400


def _epoch(dt: datetime) -> int:
    """SQLite drops tzinfo; the stored value is UTC."""
    return int((dt if dt.tzinfo else dt.replace(tzinfo=UTC)).timestamp())


def _sign(payload: str, secret: str = _WEBHOOK_SECRET, ts: int | None = None) -> str:
    ts = int(time.time()) if ts is None else ts
    mac = hmac.new(secret.encode(), f"{ts}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={mac}"


def _basil_subscription(**overrides) -> dict:
    """A Subscription as API >= 2025-03-31.basil renders it: no top-level period."""
    sub = {
        "id": "sub_contract",
        "object": "subscription",
        "status": "active",
        "customer": "cus_contract",
        "cancel_at_period_end": False,
        "items": {
            "object": "list",
            "data": [
                {
                    "id": "si_base",
                    "object": "subscription_item",
                    "quantity": 1,
                    "current_period_start": _PERIOD_START,
                    "current_period_end": _PERIOD_END,
                    "price": {
                        "id": "price_base_contract",
                        "object": "price",
                        "recurring": {"interval": "year", "interval_count": 1},
                    },
                    "plan": {"id": "price_base_contract", "object": "plan", "interval": "year"},
                }
            ],
        },
    }
    sub.update(overrides)
    return sub


class TestSdkPin:
    def test_sdk_major_is_16(self):
        assert stripe.VERSION.split(".")[0] == "16"

    def test_pinned_api_version_is_endive(self):
        # The code never sets stripe.api_version, so every request carries the
        # SDK's pinned version. A change here changes response shapes: re-run
        # the Sprint 786b review (current_period_*, Checkout params) before
        # updating this literal.
        assert stripe.api_version == "2026-09-30.endive"

    def test_signature_error_reachable_where_route_catches_it(self):
        assert stripe.error.SignatureVerificationError is stripe.SignatureVerificationError


class TestConstructEvent:
    def test_valid_signature_event_supports_handler_access_after_conversion(self):
        payload = json.dumps(
            {
                "id": "evt_contract",
                "object": "event",
                "type": "customer.subscription.updated",
                "created": 1790000000,
                "data": {"object": _basil_subscription()},
            }
        )
        from billing.stripe_client import to_plain_dict

        raw = stripe.Webhook.construct_event(payload, _sign(payload), _WEBHOOK_SECRET)
        assert isinstance(raw, stripe.Event)
        event = to_plain_dict(raw)

        # The exact access chain routes/billing.py and webhook_handler.py use.
        assert event.get("id") == "evt_contract"
        assert event.get("type") == "customer.subscription.updated"
        obj = event.get("data", {}).get("object", {})
        assert obj.get("customer") == "cus_contract"
        items = obj.get("items", {}).get("data", [])
        assert items[0].get("price", {}).get("id", "") == "price_base_contract"

    def test_bad_signature_raises_the_class_the_route_catches(self):
        payload = json.dumps({"id": "evt_x", "object": "event", "type": "x", "data": {"object": {}}})
        with pytest.raises(stripe.error.SignatureVerificationError):
            stripe.Webhook.construct_event(payload, _sign(payload, secret="whsec_wrong"), _WEBHOOK_SECRET)

    def test_malformed_json_raises_value_error(self):
        payload = "not json"
        with pytest.raises(ValueError):
            stripe.Webhook.construct_event(payload, _sign(payload), _WEBHOOK_SECRET)

    @pytest.mark.asyncio
    async def test_route_with_real_sdk_rejects_bad_signature(self):
        import httpx

        from main import app

        payload = b'{"id": "evt_route", "object": "event", "type": "x", "data": {"object": {}}}'
        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=stripe),
            patch("config.STRIPE_WEBHOOK_SECRET", _WEBHOOK_SECRET),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=payload,
                    headers={
                        "stripe-signature": _sign(payload.decode(), secret="whsec_wrong"),
                        "content-type": "application/json",
                    },
                )
        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_route_with_real_sdk_accepts_valid_event(self):
        """A correctly signed event must reach dispatch and return 200.

        On stripe >= 15, ``construct_event`` returns a ``stripe.Event`` with no
        ``.get``; before Sprint 786b the route's ``event.get("id")`` raised
        AttributeError and every genuine webhook was answered with a 500.
        """
        import httpx

        from main import app

        payload = json.dumps(
            {
                "id": f"evt_contract_route_{time.time_ns()}",
                "object": "event",
                "type": "contract.test.unhandled",
                "created": int(time.time()),
                "data": {"object": {"id": "obj_x", "object": "unknown"}},
            }
        )
        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=stripe),
            patch("config.STRIPE_WEBHOOK_SECRET", _WEBHOOK_SECRET),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=payload.encode(),
                    headers={"stripe-signature": _sign(payload), "content-type": "application/json"},
                )
        assert response.status_code == 200


class TestToPlainDict:
    def test_converts_stripe_object_recursively(self):
        from billing.stripe_client import to_plain_dict

        obj = stripe.Subscription.construct_from(_basil_subscription(), "sk_test_unused")
        with pytest.raises(AttributeError):
            obj.get("id")  # the stripe >= 15 behaviour this helper exists for

        plain = to_plain_dict(obj)
        assert type(plain) is dict
        assert type(plain["items"]["data"][0]["price"]) is dict
        assert plain.get("items", {}).get("data", [])[0]["id"] == "si_base"

    def test_dict_passes_through_unchanged(self):
        from billing.stripe_client import to_plain_dict

        d = {"id": "x"}
        assert to_plain_dict(d) is d

    def test_rejects_other_types(self):
        from billing.stripe_client import to_plain_dict

        with pytest.raises(TypeError):
            to_plain_dict("sub_123")


class TestSubscriptionShape:
    def test_checkout_completed_with_real_retrieved_subscription(self, db_session, make_user):
        """handle_checkout_completed reads the retrieved Subscription with .get()."""
        from billing.webhook_handler import handle_checkout_completed

        user = make_user(email="sdk_contract_checkout@example.com", tier=UserTier.FREE)
        fake = MagicMock()
        fake.Subscription.retrieve.return_value = stripe.Subscription.construct_from(
            _basil_subscription(), "sk_test_unused"
        )
        with (
            patch("billing.stripe_client.get_stripe", return_value=fake),
            patch("billing.webhook_handler._resolve_tier_from_price", return_value="solo"),
        ):
            handle_checkout_completed(
                db_session,
                {
                    "id": "cs_contract",
                    "customer": "cus_contract",
                    "subscription": "sub_contract",
                    "metadata": {"paciolus_user_id": str(user.id)},
                },
            )

        from billing.subscription_manager import get_subscription

        sub = get_subscription(db_session, user.id)
        assert sub is not None
        assert sub.tier == "solo"
        assert _epoch(sub.current_period_end) == _PERIOD_END

    def test_sync_reads_period_from_items_on_real_stripe_object(self, db_session, make_user):
        """Subscription.retrieve() under basil+ has no top-level current_period_*.

        Before Sprint 786b the sync read only the top-level fields, so every
        checkout-completed sync stored a NULL billing period.
        """
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="sdk_contract_period@example.com", tier=UserTier.FREE)
        from billing.stripe_client import to_plain_dict

        stripe_sub = to_plain_dict(stripe.Subscription.construct_from(_basil_subscription(), "sk_test_unused"))
        assert "current_period_start" not in stripe_sub  # the basil shape

        sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_contract", "solo")

        assert sub.current_period_start is not None
        assert sub.current_period_end is not None
        assert _epoch(sub.current_period_start) == _PERIOD_START
        assert _epoch(sub.current_period_end) == _PERIOD_END
        assert sub.billing_interval == BillingInterval.ANNUAL

    def test_legacy_top_level_period_still_wins(self, db_session, make_user):
        """A webhook endpoint pinned to a pre-basil version still sends top-level fields."""
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="sdk_contract_legacy@example.com", tier=UserTier.FREE)
        legacy = _basil_subscription(current_period_start=_LEGACY_START, current_period_end=_LEGACY_END)

        sub = sync_subscription_from_stripe(db_session, user.id, legacy, "cus_legacy", "solo")

        assert _epoch(sub.current_period_start) == _LEGACY_START
        assert _epoch(sub.current_period_end) == _LEGACY_END

    def test_period_taken_from_base_item_not_seat_addon(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="sdk_contract_seats@example.com", tier=UserTier.FREE)
        raw = _basil_subscription()
        seat_item = {
            "id": "si_seat",
            "object": "subscription_item",
            "quantity": 3,
            "current_period_start": 1,
            "current_period_end": 2,
            "price": {"id": "price_seat_contract", "object": "price", "recurring": {"interval": "year"}},
        }
        raw["items"]["data"].insert(0, seat_item)

        with patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_contract"}):
            sub = sync_subscription_from_stripe(db_session, user.id, raw, "cus_seats", "professional")

        assert _epoch(sub.current_period_start) == _PERIOD_START
        assert sub.additional_seats == 3


class TestCheckoutParams:
    def test_checkout_uses_allowed_payment_method_types(self):
        """API 2026-09-30.endive 400s on `payment_method_types` for Checkout Sessions."""
        from billing.checkout import create_checkout_session

        fake = MagicMock()
        fake.checkout.Session.create.return_value = MagicMock(id="cs_x", url="https://checkout.example/x")
        with (
            patch("billing.checkout.get_stripe", return_value=fake),
            patch("config.FRONTEND_URL", "https://app.example"),
        ):
            create_checkout_session(customer_id="cus_x", plan_price_id="price_x", user_id=1)

        params = fake.checkout.Session.create.call_args.kwargs
        assert "payment_method_types" not in params
        assert params["allowed_payment_method_types"] == ["card"]
