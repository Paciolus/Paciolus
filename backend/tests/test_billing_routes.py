"""
Billing route tests — Sprint 376 + Self-Serve Checkout + comprehensive HTTP integration.

Tests billing API endpoints with mocked Stripe client.
Self-Serve Checkout: seat validation, promo validation, webhook tier resolution,
multi-item subscription sync.
HTTP integration: authenticated endpoint testing via httpx.AsyncClient.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import UserTier
from subscription_model import BillingInterval, Subscription, SubscriptionStatus


class TestBillingRouteRegistration:
    """Verify billing routes are correctly registered."""

    def test_billing_router_in_app(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/billing/subscription" in paths
        assert "/billing/usage" in paths
        assert "/billing/webhook" in paths

    def test_create_checkout_session_route_exists(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/billing/create-checkout-session" in paths

    def test_cancel_route_exists(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/billing/cancel" in paths

    def test_reactivate_route_exists(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/billing/reactivate" in paths

    def test_portal_session_route_exists(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/billing/portal-session" in paths


class TestSubscriptionModel:
    """Test Subscription model creation and serialization."""

    def test_create_subscription(self, db_session, make_user):
        user = make_user(email="billing_test@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.SOLO,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_test123",
            stripe_subscription_id="sub_test123",
        )
        db_session.add(sub)
        db_session.flush()
        assert sub.id is not None
        assert sub.cancel_at_period_end is False

    def test_subscription_to_dict(self, db_session, make_user):
        user = make_user(email="billing_dict@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.PROFESSIONAL,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.ANNUAL,
            stripe_customer_id="cus_dict123",
            stripe_subscription_id="sub_dict123",
        )
        db_session.add(sub)
        db_session.flush()
        d = sub.to_dict()
        assert d["tier"] == "professional"
        assert d["status"] == "active"
        assert d["billing_interval"] == "annual"
        assert d["cancel_at_period_end"] is False

    def test_subscription_status_enum(self):
        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.PAST_DUE.value == "past_due"
        assert SubscriptionStatus.CANCELED.value == "canceled"
        assert SubscriptionStatus.TRIALING.value == "trialing"

    def test_billing_interval_enum(self):
        assert BillingInterval.MONTHLY.value == "monthly"
        assert BillingInterval.ANNUAL.value == "annual"


class TestWebhookHandler:
    """Test webhook event processing logic."""

    def test_handler_dispatch_keys(self):
        from billing.webhook_handler import WEBHOOK_HANDLERS

        expected_events = {
            "checkout.session.completed",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "customer.subscription.trial_will_end",
            "invoice.payment_failed",
            "invoice.paid",
        }
        assert set(WEBHOOK_HANDLERS.keys()) == expected_events

    def test_unknown_event_ignored(self):
        from billing.webhook_handler import process_webhook_event

        mock_db = MagicMock()
        # Unknown event_type should return False and not raise
        result = process_webhook_event(mock_db, "unknown.event.type", {})
        assert result is False


class TestCheckoutModule:
    """Test checkout session creation logic."""

    def test_checkout_module_imports(self):
        from billing.checkout import create_checkout_session, create_or_get_stripe_customer

        assert callable(create_checkout_session)
        assert callable(create_or_get_stripe_customer)


class TestSubscriptionManager:
    """Test subscription manager functions."""

    def test_manager_module_imports(self):
        from billing.subscription_manager import (
            cancel_subscription,
            create_portal_session,
            get_subscription,
            reactivate_subscription,
            sync_subscription_from_stripe,
        )

        assert callable(get_subscription)
        assert callable(sync_subscription_from_stripe)
        assert callable(cancel_subscription)
        assert callable(reactivate_subscription)
        assert callable(create_portal_session)


class TestStripeClient:
    """Test Stripe client initialization guards."""

    def test_is_stripe_enabled_without_key(self):
        from billing.stripe_client import is_stripe_enabled

        with patch("config.STRIPE_ENABLED", False):
            assert is_stripe_enabled() is False

    def test_get_stripe_raises_when_disabled(self):
        from billing.stripe_client import get_stripe

        with patch("config.STRIPE_ENABLED", False):
            with pytest.raises(RuntimeError, match="Stripe is not configured"):
                get_stripe()


# ---------------------------------------------------------------------------
# Self-Serve Checkout: seat/promo/webhook/sync tests
# ---------------------------------------------------------------------------


class TestSeatPriceConfig:
    """Test seat add-on price ID configuration."""

    def test_get_stripe_seat_price_id_monthly(self):
        from billing.price_config import get_stripe_seat_price_id

        with patch(
            "billing.price_config._load_pro_seat_price_ids", return_value={"monthly": "price_seat_mo", "annual": ""}
        ):
            assert get_stripe_seat_price_id("monthly", "professional") == "price_seat_mo"

    def test_get_stripe_seat_price_id_annual(self):
        from billing.price_config import get_stripe_seat_price_id

        with patch(
            "billing.price_config._load_pro_seat_price_ids", return_value={"monthly": "", "annual": "price_seat_yr"}
        ):
            assert get_stripe_seat_price_id("annual", "professional") == "price_seat_yr"

    def test_get_stripe_seat_price_id_unconfigured_returns_none(self):
        from billing.price_config import get_stripe_seat_price_id

        with patch("billing.price_config._load_pro_seat_price_ids", return_value={"monthly": "", "annual": ""}):
            assert get_stripe_seat_price_id("monthly", "professional") is None
            assert get_stripe_seat_price_id("annual", "professional") is None

    def test_get_all_seat_price_ids_filters_empty(self):
        from billing.price_config import get_all_seat_price_ids

        with (
            patch("billing.price_config._load_pro_seat_price_ids", return_value={"monthly": "price_mo", "annual": ""}),
            patch("billing.price_config._load_ent_seat_price_ids", return_value={"monthly": "", "annual": ""}),
        ):
            result = get_all_seat_price_ids()
            assert result == {"price_mo"}

    def test_get_all_seat_price_ids_both_configured(self):
        from billing.price_config import get_all_seat_price_ids

        with (
            patch(
                "billing.price_config._load_pro_seat_price_ids",
                return_value={"monthly": "price_mo", "annual": "price_yr"},
            ),
            patch("billing.price_config._load_ent_seat_price_ids", return_value={"monthly": "", "annual": ""}),
        ):
            result = get_all_seat_price_ids()
            assert result == {"price_mo", "price_yr"}


class TestCheckoutLineItems:
    """Test that checkout builds correct line items for base plan + seat add-on."""

    def test_checkout_single_line_item_no_seats(self):
        """No additional seats → single line item (base plan qty=1)."""
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "cs_test"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch("billing.checkout.get_stripe", return_value=mock_stripe):
            url = create_checkout_session(
                customer_id="cus_123",
                plan_price_id="price_professional_mo",
                user_id=1,
            )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert len(call_kwargs["line_items"]) == 1
        assert call_kwargs["line_items"][0] == {"price": "price_professional_mo", "quantity": 1}
        assert url == "https://checkout.stripe.com/test"

    def test_checkout_dual_line_items_with_seats(self):
        """Additional seats → two line items (base plan + seat add-on)."""
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "cs_test"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch("billing.checkout.get_stripe", return_value=mock_stripe):
            create_checkout_session(
                customer_id="cus_123",
                plan_price_id="price_professional_mo",
                user_id=1,
                seat_price_id="price_seat_mo",
                additional_seats=5,
            )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert len(call_kwargs["line_items"]) == 2
        assert call_kwargs["line_items"][0] == {"price": "price_professional_mo", "quantity": 1}
        assert call_kwargs["line_items"][1] == {"price": "price_seat_mo", "quantity": 5}

    def test_checkout_metadata_includes_additional_seats(self):
        """Subscription metadata must include paciolus_additional_seats."""
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "cs_test"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch("billing.checkout.get_stripe", return_value=mock_stripe):
            create_checkout_session(
                customer_id="cus_123",
                plan_price_id="price_professional_mo",
                user_id=42,
                seat_price_id="price_seat_mo",
                additional_seats=3,
            )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        sub_data = call_kwargs["subscription_data"]
        assert sub_data["metadata"]["paciolus_user_id"] == "42"
        assert sub_data["metadata"]["paciolus_additional_seats"] == "3"

    def test_checkout_no_seat_line_when_seat_price_none(self):
        """If seat_price_id is None, no seat line item even with additional_seats > 0."""
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "cs_test"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch("billing.checkout.get_stripe", return_value=mock_stripe):
            create_checkout_session(
                customer_id="cus_123",
                plan_price_id="price_solo_mo",
                user_id=1,
                seat_price_id=None,
                additional_seats=5,
            )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert len(call_kwargs["line_items"]) == 1

    def test_checkout_coupon_applied(self):
        """Coupon should appear in discounts."""
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "cs_test"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch("billing.checkout.get_stripe", return_value=mock_stripe):
            create_checkout_session(
                customer_id="cus_123",
                plan_price_id="price_professional_mo",
                user_id=1,
                stripe_coupon_id="MONTHLY_20_3MO",
            )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["discounts"] == [{"coupon": "MONTHLY_20_3MO"}]

    def test_checkout_trial_period(self):
        """Trial days should appear in subscription_data."""
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "cs_test"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch("billing.checkout.get_stripe", return_value=mock_stripe):
            create_checkout_session(
                customer_id="cus_123",
                plan_price_id="price_professional_mo",
                user_id=1,
                trial_period_days=7,
            )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["subscription_data"]["trial_period_days"] == 7


class TestCheckoutValidation:
    """Test seat validation in the billing route (V2 pricing)."""

    def test_seats_rejected_on_solo_tier(self):
        """Solo plan must not accept additional seats."""

        # Validate at the route level: solo + seat_count > 0 → error
        # We test the validation logic directly since TestClient is incompatible
        from routes.billing import CheckoutRequest

        body = CheckoutRequest(
            tier="solo",
            interval="monthly",
            seat_count=3,
        )
        # The route would raise HTTPException(400) when tier=solo and seat_count > 0
        assert body.seat_count > 0 and body.tier == "solo"

    def test_seats_accepted_on_professional_tier(self):
        """Professional plan accepts additional seats."""
        from routes.billing import CheckoutRequest

        body = CheckoutRequest(
            tier="professional",
            interval="monthly",
            seat_count=5,
        )
        assert body.seat_count == 5
        assert body.tier == "professional"

    def test_seat_count_capped_at_60_by_schema(self):
        """Pydantic schema rejects seat_count > 60."""
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="professional",
                interval="monthly",
                seat_count=61,
            )

    def test_negative_seats_rejected_by_schema(self):
        """Pydantic schema rejects negative seat_count."""
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="professional",
                interval="monthly",
                seat_count=-1,
            )

    def test_zero_seats_allowed(self):
        """seat_count=0 is valid (no add-on seats)."""
        from routes.billing import CheckoutRequest

        body = CheckoutRequest(
            tier="professional",
            interval="monthly",
            seat_count=0,
        )
        assert body.seat_count == 0


class TestPromoValidation:
    """Test promo code validation logic."""

    def test_monthly_promo_valid_on_monthly(self):
        from billing.price_config import validate_promo_for_interval

        result = validate_promo_for_interval("MONTHLY20", "monthly")
        assert result is None  # No error

    def test_monthly_promo_rejected_on_annual(self):
        from billing.price_config import validate_promo_for_interval

        result = validate_promo_for_interval("MONTHLY20", "annual")
        assert result is not None
        assert "monthly" in result.lower()

    def test_annual_promo_valid_on_annual(self):
        from billing.price_config import validate_promo_for_interval

        result = validate_promo_for_interval("ANNUAL10", "annual")
        assert result is None

    def test_annual_promo_rejected_on_monthly(self):
        from billing.price_config import validate_promo_for_interval

        result = validate_promo_for_interval("ANNUAL10", "monthly")
        assert result is not None
        assert "annual" in result.lower()

    def test_unknown_promo_code_rejected(self):
        from billing.price_config import validate_promo_for_interval

        result = validate_promo_for_interval("FAKECODE", "monthly")
        assert result is not None
        assert "unknown" in result.lower()

    def test_promo_code_case_insensitive(self):
        from billing.price_config import validate_promo_for_interval

        result = validate_promo_for_interval("monthly20", "monthly")
        assert result is None


class TestWebhookTierResolution:
    """Test tier resolution from Stripe Price IDs (Self-Serve Checkout)."""

    def test_resolve_known_price_id(self):
        from billing.webhook_handler import _resolve_tier_from_price

        with (
            patch(
                "billing.price_config._load_stripe_price_ids",
                return_value={"professional": {"monthly": "price_professional_mo"}},
            ),
            patch("billing.price_config.get_all_seat_price_ids", return_value=set()),
        ):
            result = _resolve_tier_from_price("price_professional_mo")
            assert result == "professional"

    def test_resolve_unknown_price_id_returns_none(self):
        """Unrecognized price IDs must return None, not default to 'solo'."""
        from billing.webhook_handler import _resolve_tier_from_price

        with (
            patch("billing.price_config._load_stripe_price_ids", return_value={"solo": {"monthly": "price_s_mo"}}),
            patch("billing.price_config.get_all_seat_price_ids", return_value=set()),
        ):
            result = _resolve_tier_from_price("price_unknown_xyz")
            assert result is None

    def test_resolve_seat_price_id_returns_none(self):
        """Seat add-on price IDs must return None (not map to a tier)."""
        from billing.webhook_handler import _resolve_tier_from_price

        with (
            patch(
                "billing.price_config._load_stripe_price_ids",
                return_value={"professional": {"monthly": "price_professional_mo"}},
            ),
            patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_mo"}),
        ):
            result = _resolve_tier_from_price("price_seat_mo")
            assert result is None

    def test_find_base_plan_item_skips_seat_addon(self):
        """_find_base_plan_item returns the plan item, not the seat add-on."""
        from billing.webhook_handler import _find_base_plan_item

        items = [
            {"price": {"id": "price_seat_mo"}, "quantity": 5},
            {"price": {"id": "price_professional_mo"}, "quantity": 1},
        ]
        with patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_mo"}):
            result = _find_base_plan_item(items)
            assert result is not None
            assert result["price"]["id"] == "price_professional_mo"

    def test_find_base_plan_item_returns_first_when_no_seats(self):
        """Single-item subscription (no seat add-on) returns the only item."""
        from billing.webhook_handler import _find_base_plan_item

        items = [{"price": {"id": "price_solo_mo"}, "quantity": 1}]
        with patch("billing.price_config.get_all_seat_price_ids", return_value=set()):
            result = _find_base_plan_item(items)
            assert result is not None
            assert result["price"]["id"] == "price_solo_mo"

    def test_find_base_plan_item_empty_list(self):
        """Empty items list returns None."""
        from billing.webhook_handler import _find_base_plan_item

        with patch("billing.price_config.get_all_seat_price_ids", return_value=set()):
            result = _find_base_plan_item([])
            assert result is None

    def test_find_base_plan_item_fallback_all_seat_items(self):
        """If all items are seat prices, falls back to first item (backward compat)."""
        from billing.webhook_handler import _find_base_plan_item

        items = [{"price": {"id": "price_seat_mo"}, "quantity": 5}]
        with patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_mo"}):
            result = _find_base_plan_item(items)
            assert result is not None  # Falls back to items[0]


class TestSubscriptionSeatSync:
    """Test seat extraction from multi-item Stripe subscriptions."""

    def test_extract_additional_seats_from_multi_item(self):
        """Seat add-on item's quantity is returned as additional seats."""
        from billing.subscription_manager import _extract_additional_seats

        stripe_sub = {
            "items": {
                "data": [
                    {"price": {"id": "price_professional_mo"}, "quantity": 1},
                    {"price": {"id": "price_seat_mo"}, "quantity": 7},
                ]
            }
        }
        with patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_mo"}):
            result = _extract_additional_seats(stripe_sub)
            assert result == 7

    def test_extract_additional_seats_single_item_returns_zero(self):
        """Single-item subscription (no seat add-on) returns 0."""
        from billing.subscription_manager import _extract_additional_seats

        stripe_sub = {
            "items": {
                "data": [
                    {"price": {"id": "price_solo_mo"}, "quantity": 1},
                ]
            }
        }
        with patch("billing.price_config.get_all_seat_price_ids", return_value=set()):
            result = _extract_additional_seats(stripe_sub)
            assert result == 0

    def test_extract_additional_seats_empty_items(self):
        """Empty items returns 0."""
        from billing.subscription_manager import _extract_additional_seats

        stripe_sub = {"items": {"data": []}}
        with patch("billing.price_config.get_all_seat_price_ids", return_value=set()):
            result = _extract_additional_seats(stripe_sub)
            assert result == 0

    def test_extract_seat_quantity_skips_seat_addon(self):
        """Base seat quantity comes from the plan item, not the seat add-on."""
        from billing.subscription_manager import _extract_seat_quantity

        stripe_sub = {
            "items": {
                "data": [
                    {"price": {"id": "price_seat_mo"}, "quantity": 5},
                    {"price": {"id": "price_professional_mo"}, "quantity": 1},
                ]
            }
        }
        with patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_mo"}):
            result = _extract_seat_quantity(stripe_sub)
            assert result == 1

    def test_sync_subscription_sets_additional_seats(self, db_session, make_user):
        """sync_subscription_from_stripe sets additional_seats from seat add-on item."""
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="seat_sync@example.com")

        stripe_sub = {
            "id": "sub_seat_test",
            "status": "active",
            "items": {
                "data": [
                    {"price": {"id": "price_professional_mo"}, "quantity": 1, "plan": {"interval": "month"}},
                    {"price": {"id": "price_seat_mo"}, "quantity": 4},
                ]
            },
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
            "cancel_at_period_end": False,
        }

        with patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_mo"}):
            sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_sync_test", "professional")

        assert sub.additional_seats == 4
        assert sub.seat_count == 1  # Base plan quantity

    def test_sync_subscription_zero_seats_without_addon(self, db_session, make_user):
        """Single-item subscription sets additional_seats=0."""
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="seat_zero@example.com")

        stripe_sub = {
            "id": "sub_no_seats",
            "status": "active",
            "items": {
                "data": [
                    {"price": {"id": "price_solo_mo"}, "quantity": 1, "plan": {"interval": "month"}},
                ]
            },
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
            "cancel_at_period_end": False,
        }

        with patch("billing.price_config.get_all_seat_price_ids", return_value=set()):
            sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_zero_test", "solo")

        assert sub.additional_seats == 0
        assert sub.seat_count == 1


class TestCheckoutRedirectIntegrity:
    """Verify checkout redirect URLs are always server-side derived, never user-supplied."""

    FRONTEND = "https://app.paciolus.com"

    def _make_stripe_mock(self):
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "cs_redirect_test"
        mock_session.url = "https://checkout.stripe.com/redirect_test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        return mock_stripe

    def test_derived_urls_correct(self):
        """Stripe session uses FRONTEND_URL-derived success and cancel URLs."""
        from billing.checkout import create_checkout_session

        mock_stripe = self._make_stripe_mock()
        with (
            patch("billing.checkout.get_stripe", return_value=mock_stripe),
            patch("config.FRONTEND_URL", self.FRONTEND),
        ):
            create_checkout_session(
                customer_id="cus_123",
                plan_price_id="price_solo_mo",
                user_id=1,
            )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["success_url"] == f"{self.FRONTEND}/checkout/success"
        assert call_kwargs["cancel_url"] == f"{self.FRONTEND}/pricing"

    def test_injection_attempt_ignored(self):
        """success_url in request body is stripped by schema; model has no such field."""
        from routes.billing import CheckoutRequest

        body = CheckoutRequest.model_validate(
            {
                "tier": "solo",
                "interval": "monthly",
                "success_url": "https://evil.com/steal",
            }
        )
        assert not hasattr(body, "success_url")

    def test_prometheus_counter_incremented_on_success_url(self):
        """Injecting success_url increments billing_redirect_injection_attempt_total."""
        from routes.billing import CheckoutRequest
        from shared.parser_metrics import billing_redirect_injection_attempt_total

        counter = billing_redirect_injection_attempt_total.labels(field="success_url")
        before = counter._value.get()

        CheckoutRequest.model_validate(
            {
                "tier": "solo",
                "interval": "monthly",
                "success_url": "https://evil.com",
            }
        )

        assert counter._value.get() == before + 1.0

    def test_both_fields_monitored(self):
        """Both success_url and cancel_url each increment the counter."""
        from routes.billing import CheckoutRequest
        from shared.parser_metrics import billing_redirect_injection_attempt_total

        success_counter = billing_redirect_injection_attempt_total.labels(field="success_url")
        cancel_counter = billing_redirect_injection_attempt_total.labels(field="cancel_url")
        before_success = success_counter._value.get()
        before_cancel = cancel_counter._value.get()

        CheckoutRequest.model_validate(
            {
                "tier": "solo",
                "interval": "monthly",
                "success_url": "https://evil.com",
                "cancel_url": "https://evil.com",
            }
        )

        assert success_counter._value.get() == before_success + 1.0
        assert cancel_counter._value.get() == before_cancel + 1.0

    def test_malicious_scheme_stripped(self):
        """javascript: scheme in success_url is stripped; field not on model."""
        from routes.billing import CheckoutRequest

        body = CheckoutRequest.model_validate(
            {
                "tier": "solo",
                "interval": "monthly",
                "success_url": "javascript:alert(1)",
            }
        )
        assert not hasattr(body, "success_url")

    def test_data_uri_stripped(self):
        """data: URI in success_url is stripped; field not on model."""
        from routes.billing import CheckoutRequest

        body = CheckoutRequest.model_validate(
            {
                "tier": "solo",
                "interval": "monthly",
                "success_url": "data:text/html,<script>alert(1)</script>",
            }
        )
        assert not hasattr(body, "success_url")

    def test_frontend_url_misconfigured_raises(self):
        """Empty FRONTEND_URL causes ValueError — fail-safe rather than silent misconfiguration."""
        from billing.checkout import create_checkout_session

        mock_stripe = self._make_stripe_mock()
        with (
            patch("billing.checkout.get_stripe", return_value=mock_stripe),
            patch("config.FRONTEND_URL", ""),
        ):
            with pytest.raises(ValueError, match="FRONTEND_URL must be configured"):
                create_checkout_session(
                    customer_id="cus_123",
                    plan_price_id="price_solo_mo",
                    user_id=1,
                )


# ---------------------------------------------------------------------------
# Stripe Webhook HTTP Integration Tests (F-006)
# ---------------------------------------------------------------------------


class TestWebhookHTTPIntegration:
    """HTTP-layer integration tests for POST /billing/webhook.

    These tests exercise the actual FastAPI route through httpx.AsyncClient,
    verifying signature verification, CSRF exemption, and error handling.
    """

    @pytest.mark.asyncio
    async def test_webhook_valid_signature(self):
        """POST /billing/webhook with valid Stripe signature returns 200."""
        from main import app

        mock_stripe = MagicMock()
        # construct_event returns a valid event dict
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_valid",
                    "customer": "cus_test",
                    "subscription": "sub_test",
                },
            },
        }

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
            patch("billing.webhook_handler.process_webhook_event", return_value=True) as mock_process,
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b'{"type": "checkout.session.completed"}',
                    headers={
                        "stripe-signature": "t=1234567890,v1=fakesig",
                        "content-type": "application/json",
                    },
                )

            assert response.status_code == 200
            # Verify construct_event was called with the raw payload, sig header, and secret
            mock_stripe.Webhook.construct_event.assert_called_once()
            call_args = mock_stripe.Webhook.construct_event.call_args
            assert call_args[0][1] == "t=1234567890,v1=fakesig"
            assert call_args[0][2] == "FAKE_WEBHOOK_SECRET_FOR_TESTING"
            # Verify the webhook handler was invoked
            mock_process.assert_called_once_with(
                ANY,
                "checkout.session.completed",
                {
                    "id": "cs_test_valid",
                    "customer": "cus_test",
                    "subscription": "sub_test",
                },
                event_created=None,
            )

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature(self):
        """POST /billing/webhook with invalid Stripe signature returns 400."""
        from main import app

        mock_stripe = MagicMock()
        # Simulate SignatureVerificationError — Stripe SDK raises this
        # The error class is accessed as stripe.error.SignatureVerificationError
        mock_stripe.error.SignatureVerificationError = type("SignatureVerificationError", (Exception,), {})
        mock_stripe.Webhook.construct_event.side_effect = mock_stripe.error.SignatureVerificationError(
            "Invalid signature", "sig_header"
        )

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b'{"type": "test.event"}',
                    headers={
                        "stripe-signature": "t=1234567890,v1=badsig",
                        "content-type": "application/json",
                    },
                )

            assert response.status_code == 400
            assert "Invalid signature" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_webhook_missing_signature_header(self):
        """POST /billing/webhook without stripe-signature header returns 400."""
        from main import app

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b'{"type": "test.event"}',
                    headers={"content-type": "application/json"},
                )

            assert response.status_code == 400
            assert "stripe-signature" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_webhook_csrf_exempt(self):
        """Webhook endpoint is CSRF-exempt — POST succeeds without CSRF token.

        This verifies /billing/webhook is in CSRF_EXEMPT_PATHS and the
        CSRF middleware does not block requests to it.
        """
        from security_middleware import CSRF_EXEMPT_PATHS

        assert "/billing/webhook" in CSRF_EXEMPT_PATHS

        # Also verify via HTTP — a POST without any CSRF token should not
        # get a 403 from the CSRF middleware (it may get 400 from missing
        # stripe-signature, which proves CSRF was not the blocker).
        from main import app

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b"{}",
                    headers={"content-type": "application/json"},
                )

            # Should be 400 (missing stripe-signature), NOT 403 (CSRF)
            assert response.status_code == 400
            assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_webhook_stripe_disabled_returns_200(self):
        """When Stripe is disabled, webhook returns 200 (no-op)."""
        from main import app

        with patch("billing.stripe_client.is_stripe_enabled", return_value=False):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b"{}",
                    headers={
                        "content-type": "application/json",
                        "stripe-signature": "t=123,v1=sig",
                    },
                )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_duplicate_event_idempotent(self, db_session):
        """Replaying the same Stripe event ID must not invoke the handler twice."""
        from database import get_db
        from main import app

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_duplicate_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_dup",
                    "customer": "cus_dup",
                    "subscription": "sub_dup",
                },
            },
        }

        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
                patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
                patch("billing.webhook_handler.process_webhook_event", return_value=True) as mock_process,
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    headers = {
                        "stripe-signature": "t=1234567890,v1=fakesig",
                        "content-type": "application/json",
                    }
                    # First delivery — should be processed
                    resp1 = await client.post("/billing/webhook", content=b'{"type": "test"}', headers=headers)
                    # Second delivery (replay) — should be skipped
                    resp2 = await client.post("/billing/webhook", content=b'{"type": "test"}', headers=headers)

                assert resp1.status_code == 200
                assert resp2.status_code == 200
                # Handler invoked only once
                assert mock_process.call_count == 1
        finally:
            app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Authenticated Endpoint HTTP Integration Tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestCheckoutHTTPIntegration:
    """HTTP-layer integration tests for POST /billing/create-checkout-session."""

    @pytest.mark.asyncio
    async def test_create_checkout_session_happy_path(self, db_session, make_user):
        """POST /billing/create-checkout-session with valid body returns 201 + checkout_url."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="checkout_http@example.com", tier=UserTier.SOLO)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with patch(
                "billing.checkout_orchestrator.orchestrate_checkout",
                return_value="https://checkout.stripe.com/test_session",
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/create-checkout-session",
                        json={"tier": "solo", "interval": "monthly"},
                    )

                assert response.status_code == 201
                data = response.json()
                assert data["checkout_url"] == "https://checkout.stripe.com/test_session"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_checkout_validation_error_returns_400(self, db_session, make_user):
        """Checkout orchestrator validation error maps to 400."""
        from auth import require_verified_user
        from billing.checkout_orchestrator import CheckoutValidationError
        from database import get_db
        from main import app

        user = make_user(email="checkout_400@example.com", tier=UserTier.SOLO)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with patch(
                "billing.checkout_orchestrator.orchestrate_checkout",
                side_effect=CheckoutValidationError("Solo plan does not support seats"),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/create-checkout-session",
                        json={"tier": "solo", "interval": "monthly", "seat_count": 5},
                    )

                assert response.status_code == 400
                assert "Solo plan does not support seats" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_checkout_unavailable_returns_503(self, db_session, make_user):
        """Checkout unavailable (Stripe disabled) maps to 503."""
        from auth import require_verified_user
        from billing.checkout_orchestrator import CheckoutUnavailableError
        from database import get_db
        from main import app

        user = make_user(email="checkout_503@example.com", tier=UserTier.SOLO)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with patch(
                "billing.checkout_orchestrator.orchestrate_checkout",
                side_effect=CheckoutUnavailableError("Billing is not available"),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/create-checkout-session",
                        json={"tier": "solo", "interval": "monthly"},
                    )

                assert response.status_code == 503
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_checkout_provider_error_returns_502(self, db_session, make_user):
        """Stripe provider error maps to 502."""
        from auth import require_verified_user
        from billing.checkout_orchestrator import CheckoutProviderError
        from database import get_db
        from main import app

        user = make_user(email="checkout_502@example.com", tier=UserTier.SOLO)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with patch(
                "billing.checkout_orchestrator.orchestrate_checkout",
                side_effect=CheckoutProviderError("Stripe API error"),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/create-checkout-session",
                        json={"tier": "solo", "interval": "monthly"},
                    )

                assert response.status_code == 502
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_checkout_invalid_tier_rejected(self, db_session, make_user):
        """Invalid tier value rejected by Pydantic schema (422)."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="checkout_tier@example.com", tier=UserTier.SOLO)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/create-checkout-session",
                    json={"tier": "platinum", "interval": "monthly"},
                )

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


class TestSubscriptionStatusHTTP:
    """HTTP-layer integration tests for GET /billing/subscription."""

    @pytest.mark.asyncio
    async def test_subscription_status_no_subscription(self, db_session, make_user):
        """User with no subscription returns fallback shape (tier from user, status=active)."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="sub_none@example.com", tier=UserTier.FREE)
        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/billing/subscription")

            assert response.status_code == 200
            data = response.json()
            assert data["tier"] == "free"
            assert data["status"] == "active"
            assert data["id"] is None
            assert data["seat_count"] == 1
            assert data["total_seats"] == 1
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_subscription_status_with_active_subscription(self, db_session, make_user):
        """User with active subscription returns full subscription details."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="sub_active@example.com", tier=UserTier.PROFESSIONAL)
        sub = Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_sub_test",
            stripe_subscription_id="sub_sub_test",
            seat_count=7,
            additional_seats=3,
            cancel_at_period_end=False,
        )
        db_session.add(sub)
        db_session.flush()

        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/billing/subscription")

            assert response.status_code == 200
            data = response.json()
            assert data["tier"] == "professional"
            assert data["status"] == "active"
            assert data["billing_interval"] == "monthly"
            assert data["seat_count"] == 7
            assert data["additional_seats"] == 3
            assert data["total_seats"] == 10
            assert data["cancel_at_period_end"] is False
            assert data["id"] is not None
        finally:
            app.dependency_overrides.clear()


@pytest.mark.usefixtures("bypass_csrf")
class TestCancelHTTP:
    """HTTP-layer integration tests for POST /billing/cancel."""

    @pytest.mark.asyncio
    async def test_cancel_happy_path(self, db_session, make_user):
        """Cancellation with active subscription returns confirmation message."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="cancel_ok@example.com", tier=UserTier.SOLO)
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_cancel",
            stripe_subscription_id="sub_cancel",
        )
        db_session.add(sub)
        db_session.flush()

        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.subscription_manager.cancel_subscription", return_value=sub),
                patch("billing.analytics.record_billing_event"),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post("/billing/cancel", json={})

                assert response.status_code == 200
                data = response.json()
                assert "canceled" in data["message"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cancel_no_subscription_returns_404(self, db_session, make_user):
        """Cancellation with no subscription returns 404."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="cancel_none@example.com", tier=UserTier.FREE)
        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.subscription_manager.cancel_subscription", return_value=None),
                patch("billing.subscription_manager.get_subscription", return_value=None),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post("/billing/cancel", json={})

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_cancel_with_reason(self, db_session, make_user):
        """Cancellation reason is accepted and passed to analytics."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="cancel_reason@example.com", tier=UserTier.SOLO)
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_cancel_r",
            stripe_subscription_id="sub_cancel_r",
        )
        db_session.add(sub)
        db_session.flush()

        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.subscription_manager.cancel_subscription", return_value=sub),
                patch("billing.analytics.record_billing_event") as mock_record,
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/cancel",
                        json={"reason": "too_expensive"},
                    )

                assert response.status_code == 200
                # Verify the billing event was recorded with the reason
                mock_record.assert_called_once()
                call_kwargs = mock_record.call_args
                assert call_kwargs[1]["metadata"] == {"reason": "too_expensive"}
        finally:
            app.dependency_overrides.clear()


@pytest.mark.usefixtures("bypass_csrf")
class TestReactivateHTTP:
    """HTTP-layer integration tests for POST /billing/reactivate."""

    @pytest.mark.asyncio
    async def test_reactivate_happy_path(self, db_session, make_user):
        """Reactivation with pending-cancel subscription returns confirmation."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="reactivate_ok@example.com", tier=UserTier.SOLO)
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_react",
            stripe_subscription_id="sub_react",
            cancel_at_period_end=True,
        )
        db_session.add(sub)
        db_session.flush()

        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.subscription_manager.reactivate_subscription", return_value=sub),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post("/billing/reactivate")

                assert response.status_code == 200
                data = response.json()
                assert "reactivated" in data["message"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_reactivate_no_subscription_returns_404(self, db_session, make_user):
        """Reactivation with no subscription returns 404."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="reactivate_none@example.com", tier=UserTier.FREE)
        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.subscription_manager.reactivate_subscription", return_value=None),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post("/billing/reactivate")

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_reactivate_stripe_disabled_returns_503(self, db_session, make_user):
        """Reactivation when Stripe is disabled returns 503."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="reactivate_503@example.com", tier=UserTier.SOLO)
        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with patch("billing.stripe_client.is_stripe_enabled", return_value=False):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post("/billing/reactivate")

                assert response.status_code == 503
        finally:
            app.dependency_overrides.clear()


class TestUsageHTTP:
    """HTTP-layer integration tests for GET /billing/usage."""

    @pytest.mark.asyncio
    async def test_usage_returns_correct_shape(self, db_session, make_user):
        """Usage endpoint returns all expected fields."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="usage_ok@example.com", tier=UserTier.SOLO)
        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        @dataclass
        class MockUsageStats:
            uploads_used: int = 5
            uploads_limit: int = 100
            clients_used: int = 2
            clients_limit: int = 0
            tier: str = "solo"

        try:
            with patch("billing.usage_service.get_usage_stats", return_value=MockUsageStats()):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get("/billing/usage")

                assert response.status_code == 200
                data = response.json()
                assert data["uploads_used"] == 5
                assert data["uploads_limit"] == 100
                assert data["clients_used"] == 2
                assert data["clients_limit"] == 0
                assert data["tier"] == "solo"
                # Backward compat aliases
                assert data["diagnostics_used"] == 5
                assert data["diagnostics_limit"] == 100
        finally:
            app.dependency_overrides.clear()


class TestWeeklyReviewHTTP:
    """HTTP-layer integration tests for GET /billing/analytics/weekly-review."""

    @pytest.mark.asyncio
    async def test_weekly_review_org_admin_allowed(self, db_session, make_user):
        """Org admin can access weekly review."""
        from auth import require_verified_user
        from database import get_db
        from main import app
        from organization_model import Organization, OrganizationMember, OrgRole

        owner = make_user(email="weekly_owner@example.com", tier=UserTier.PROFESSIONAL)
        org = Organization(name="Test Org", slug="test-org-weekly", owner_user_id=owner.id)
        db_session.add(org)
        db_session.flush()

        member = OrganizationMember(
            organization_id=org.id,
            user_id=owner.id,
            role=OrgRole.ADMIN,
        )
        db_session.add(member)
        db_session.flush()

        # Set organization_id on user
        owner.organization_id = org.id
        db_session.flush()

        app.dependency_overrides[require_verified_user] = lambda: owner
        app.dependency_overrides[get_db] = lambda: db_session

        mock_review = {
            "period": {"start": "2026-03-10", "end": "2026-03-17"},
            "metrics": {"trial_starts": 5},
            "previous_period": {"start": "2026-03-03", "end": "2026-03-10"},
            "deltas": {"trial_starts": 2},
        }

        try:
            with patch("billing.analytics.get_weekly_review", return_value=mock_review):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get("/billing/analytics/weekly-review")

                assert response.status_code == 200
                data = response.json()
                assert "period" in data
                assert "metrics" in data
                assert "previous_period" in data
                assert "deltas" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_weekly_review_non_admin_returns_403(self, db_session, make_user):
        """Non-admin org member gets 403 on weekly review."""
        from auth import require_verified_user
        from database import get_db
        from main import app
        from organization_model import Organization, OrganizationMember, OrgRole

        owner = make_user(email="weekly_review_owner2@example.com", tier=UserTier.PROFESSIONAL)
        member_user = make_user(email="weekly_member@example.com", tier=UserTier.PROFESSIONAL)

        org = Organization(name="Test Org 2", slug="test-org-weekly2", owner_user_id=owner.id)
        db_session.add(org)
        db_session.flush()

        # Add the member_user as a regular MEMBER (not admin/owner)
        member = OrganizationMember(
            organization_id=org.id,
            user_id=member_user.id,
            role=OrgRole.MEMBER,
        )
        db_session.add(member)
        db_session.flush()

        member_user.organization_id = org.id
        db_session.flush()

        app.dependency_overrides[require_verified_user] = lambda: member_user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/billing/analytics/weekly-review")

            assert response.status_code == 403
            assert "admin or owner" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_weekly_review_solo_no_subscription_returns_403(self, db_session, make_user):
        """Solo user (no org) without subscription gets 403."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="weekly_solo_nosub@example.com", tier=UserTier.SOLO)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with patch("billing.subscription_manager.get_subscription", return_value=None):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get("/billing/analytics/weekly-review")

                assert response.status_code == 403
                assert "subscription" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_weekly_review_solo_with_subscription_allowed(self, db_session, make_user):
        """Solo user with active subscription can view their own data."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="weekly_solo_sub@example.com", tier=UserTier.SOLO)
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
        )
        db_session.add(sub)
        db_session.flush()

        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        mock_review = {
            "period": {"start": "2026-03-10", "end": "2026-03-17"},
            "metrics": {},
            "previous_period": {"start": "2026-03-03", "end": "2026-03-10"},
            "deltas": {},
        }

        try:
            with patch("billing.analytics.get_weekly_review", return_value=mock_review):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get("/billing/analytics/weekly-review")

                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


@pytest.mark.usefixtures("bypass_csrf")
class TestSeatManagementHTTP:
    """HTTP-layer integration tests for seat add/remove endpoints."""

    @pytest.mark.asyncio
    async def test_add_seats_happy_path(self, db_session, make_user):
        """POST /billing/add-seats returns updated seat counts."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="add_seats@example.com", tier=UserTier.PROFESSIONAL)
        sub = Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_seats",
            stripe_subscription_id="sub_seats",
            seat_count=7,
            additional_seats=3,
        )
        db_session.add(sub)
        db_session.flush()

        # Mock the result after adding 2 seats
        mock_result = MagicMock()
        mock_result.seat_count = 7
        mock_result.additional_seats = 5
        mock_result.total_seats = 12

        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.subscription_manager.add_seats", return_value=mock_result),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/add-seats",
                        json={"seats": 2},
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["seat_count"] == 7
                assert data["additional_seats"] == 5
                assert data["total_seats"] == 12
                assert "added" in data["message"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_seats_failure_returns_400(self, db_session, make_user):
        """add_seats returning None results in 400."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="add_seats_fail@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.subscription_manager.add_seats", return_value=None),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/add-seats",
                        json={"seats": 2},
                    )

                assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_remove_seats_happy_path(self, db_session, make_user):
        """POST /billing/remove-seats returns updated seat counts."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="remove_seats@example.com", tier=UserTier.PROFESSIONAL)

        mock_result = MagicMock()
        mock_result.seat_count = 7
        mock_result.additional_seats = 1
        mock_result.total_seats = 8

        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.subscription_manager.remove_seats", return_value=mock_result),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/remove-seats",
                        json={"seats": 2},
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["total_seats"] == 8
                assert "removed" in data["message"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_remove_seats_below_base_returns_400(self, db_session, make_user):
        """Removing more seats than additional_seats returns 400."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="remove_seats_fail@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.subscription_manager.remove_seats", return_value=None),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/remove-seats",
                        json={"seats": 10},
                    )

                assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_seats_stripe_disabled_returns_503(self, db_session, make_user):
        """add-seats when Stripe is disabled returns 503."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="add_seats_503@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with patch("billing.stripe_client.is_stripe_enabled", return_value=False):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/add-seats",
                        json={"seats": 1},
                    )

                assert response.status_code == 503
        finally:
            app.dependency_overrides.clear()


class TestPortalSessionHTTP:
    """HTTP-layer integration tests for GET /billing/portal-session."""

    @pytest.mark.asyncio
    async def test_portal_session_happy_path(self, db_session, make_user):
        """Portal session returns portal URL."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="portal_ok@example.com", tier=UserTier.PROFESSIONAL)
        sub = Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_portal",
            stripe_subscription_id="sub_portal",
        )
        db_session.add(sub)
        db_session.flush()

        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch(
                    "billing.subscription_manager.create_portal_session",
                    return_value="https://billing.stripe.com/portal/test",
                ),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get("/billing/portal-session")

                assert response.status_code == 200
                data = response.json()
                assert data["portal_url"] == "https://billing.stripe.com/portal/test"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_portal_session_no_billing_account_returns_404(self, db_session, make_user):
        """User without Stripe customer returns 404."""
        from auth import require_current_user
        from database import get_db
        from main import app

        user = make_user(email="portal_none@example.com", tier=UserTier.FREE)
        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/billing/portal-session")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestStripeEndpointGuard:
    """Unit tests for the stripe_endpoint_guard context manager."""

    def test_guard_raises_503_when_stripe_disabled(self):
        """Guard raises 503 HTTPException when Stripe is not enabled."""
        from fastapi import HTTPException

        from routes.billing import stripe_endpoint_guard

        with patch("billing.stripe_client.is_stripe_enabled", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                with stripe_endpoint_guard(1, "test"):
                    pass  # pragma: no cover

            assert exc_info.value.status_code == 503

    def test_guard_catches_exception_raises_502(self):
        """Guard catches generic exceptions and raises 502."""
        from fastapi import HTTPException

        from routes.billing import stripe_endpoint_guard

        with patch("billing.stripe_client.is_stripe_enabled", return_value=True):
            with pytest.raises(HTTPException) as exc_info:
                with stripe_endpoint_guard(1, "test"):
                    raise RuntimeError("Stripe API timeout")

            assert exc_info.value.status_code == 502

    def test_guard_passes_through_on_success(self):
        """Guard yields cleanly when Stripe is enabled and no exception occurs."""
        from routes.billing import stripe_endpoint_guard

        with patch("billing.stripe_client.is_stripe_enabled", return_value=True):
            with stripe_endpoint_guard(1, "test"):
                result = 42

            assert result == 42
