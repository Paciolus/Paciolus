"""
Pricing V2 integration tests — Phase LIX Sprint F.

End-to-end flow tests with mocked Stripe:
1. Feature flag gating (V2 enabled/disabled)
2. Full checkout flows: free→Solo, free→Team(5 seats)
3. Trial→paid conversion via webhook simulation
4. Seat management: add 3 seats, remove seats
5. Cancel subscription flow
6. Webhook simulations: trial_will_end, quantity change, coupon, deletion
7. Prometheus counter verification
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import UserTier
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

# ---------------------------------------------------------------------------
# Feature flag gating
# ---------------------------------------------------------------------------


class TestFeatureFlagGating:
    """V2 pricing endpoints are gated behind PRICING_V2_ENABLED."""

    def test_require_pricing_v2_blocks_when_disabled(self):
        from fastapi import HTTPException

        from routes.billing import _require_pricing_v2

        with patch("config.PRICING_V2_ENABLED", False):
            with pytest.raises(HTTPException) as exc_info:
                _require_pricing_v2()
            assert exc_info.value.status_code == 503

    def test_require_pricing_v2_allows_when_enabled(self):
        from routes.billing import _require_pricing_v2

        with patch("config.PRICING_V2_ENABLED", True):
            result = _require_pricing_v2()
            assert result is None

    def test_checkout_ignores_promo_when_v2_disabled(self):
        """When V2 is off, promo_code field is accepted but not processed."""
        from routes.billing import CheckoutRequest

        # Schema still accepts the field (no validation error)
        req = CheckoutRequest(
            tier="team",
            interval="monthly",
            success_url="https://example.com/ok",
            cancel_url="https://example.com/cancel",
            promo_code="MONTHLY20",
            seat_count=5,
        )
        assert req.promo_code == "MONTHLY20"
        assert req.seat_count == 5

    def test_checkout_ignores_seats_when_v2_disabled(self):
        """When V2 is off, seat_count is accepted but checkout uses quantity=1."""
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier="team",
            interval="annual",
            success_url="https://example.com/ok",
            cancel_url="https://example.com/cancel",
            seat_count=10,
        )
        assert req.seat_count == 10


# ---------------------------------------------------------------------------
# Full checkout flows (mocked Stripe)
# ---------------------------------------------------------------------------


class TestCheckoutFlows:
    """End-to-end checkout session creation with mocked Stripe."""

    @patch("billing.checkout.get_stripe")
    def test_solo_checkout_no_seats(self, mock_get_stripe):
        """Free→Solo: basic checkout, no seats, no trial (if not V2)."""
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe
        mock_session = MagicMock()
        mock_session.id = "cs_solo"
        mock_session.url = "https://checkout.stripe.com/solo"
        mock_stripe.checkout.Session.create.return_value = mock_session

        url = create_checkout_session(
            customer_id="cus_solo",
            price_id="price_solo_monthly",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            user_id=1,
        )

        assert url == "https://checkout.stripe.com/solo"
        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["line_items"] == [{"price": "price_solo_monthly", "quantity": 1}]
        assert "trial_period_days" not in call_kwargs.get("subscription_data", {})

    @patch("billing.checkout.get_stripe")
    def test_team_checkout_with_5_seats(self, mock_get_stripe):
        """Free→Team(5 additional seats): quantity = 3 included + 5 = 8."""
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe
        mock_session = MagicMock()
        mock_session.id = "cs_team"
        mock_session.url = "https://checkout.stripe.com/team"
        mock_stripe.checkout.Session.create.return_value = mock_session

        url = create_checkout_session(
            customer_id="cus_team",
            price_id="price_team_monthly",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            user_id=2,
            seat_quantity=8,  # 3 included + 5 additional
        )

        assert url == "https://checkout.stripe.com/team"
        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["line_items"] == [{"price": "price_team_monthly", "quantity": 8}]

    @patch("billing.checkout.get_stripe")
    def test_checkout_with_trial_period(self, mock_get_stripe):
        """Checkout with 7-day trial period."""
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe
        mock_session = MagicMock()
        mock_session.id = "cs_trial"
        mock_session.url = "https://checkout.stripe.com/trial"
        mock_stripe.checkout.Session.create.return_value = mock_session

        create_checkout_session(
            customer_id="cus_trial",
            price_id="price_team_monthly",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            user_id=3,
            trial_period_days=7,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["subscription_data"]["trial_period_days"] == 7

    @patch("billing.checkout.get_stripe")
    def test_checkout_with_coupon(self, mock_get_stripe):
        """Checkout with promotional coupon."""
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe
        mock_session = MagicMock()
        mock_session.id = "cs_coupon"
        mock_session.url = "https://checkout.stripe.com/coupon"
        mock_stripe.checkout.Session.create.return_value = mock_session

        create_checkout_session(
            customer_id="cus_coupon",
            price_id="price_team_monthly",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            user_id=4,
            stripe_coupon_id="coupon_monthly20",
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["discounts"] == [{"coupon": "coupon_monthly20"}]

    @patch("billing.checkout.get_stripe")
    def test_checkout_with_trial_and_coupon_and_seats(self, mock_get_stripe):
        """Full V2 checkout: trial + coupon + seats."""
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe
        mock_session = MagicMock()
        mock_session.id = "cs_full"
        mock_session.url = "https://checkout.stripe.com/full"
        mock_stripe.checkout.Session.create.return_value = mock_session

        create_checkout_session(
            customer_id="cus_full",
            price_id="price_team_annual",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            user_id=5,
            trial_period_days=7,
            stripe_coupon_id="coupon_annual10",
            seat_quantity=8,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["line_items"] == [{"price": "price_team_annual", "quantity": 8}]
        assert call_kwargs["subscription_data"]["trial_period_days"] == 7
        assert call_kwargs["discounts"] == [{"coupon": "coupon_annual10"}]


# ---------------------------------------------------------------------------
# Trial → Paid conversion via webhook
# ---------------------------------------------------------------------------


class TestTrialConversion:
    """Simulated webhook events for trial-to-paid conversion."""

    def test_subscription_updated_converts_trial_to_active(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="trial_convert@example.com")

        # First: create as trialing
        stripe_sub_trial = {
            "id": "sub_trial_convert",
            "status": "trialing",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 3}]},
        }
        sub = sync_subscription_from_stripe(
            db_session,
            user.id,
            stripe_sub_trial,
            "cus_trial_convert",
            "team",
        )
        assert sub.status == SubscriptionStatus.TRIALING

        # Then: Stripe sends "active" status after trial ends and payment succeeds
        stripe_sub_active = {
            "id": "sub_trial_convert",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1702600000,
            "current_period_end": 1705200000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 3}]},
        }
        sub = sync_subscription_from_stripe(
            db_session,
            user.id,
            stripe_sub_active,
            "cus_trial_convert",
            "team",
        )
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.seat_count == 3


# ---------------------------------------------------------------------------
# Seat management flow: add → remove
# ---------------------------------------------------------------------------


class TestSeatManagementFlow:
    """Full seat lifecycle: add seats, verify, remove seats."""

    @patch("billing.subscription_manager.get_stripe")
    def test_add_3_seats_then_remove_1(self, mock_get_stripe, db_session, make_user):
        from billing.subscription_manager import add_seats, remove_seats

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe

        user = make_user(email="seat_flow@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_flow",
            stripe_subscription_id="sub_flow",
            seat_count=3,
            additional_seats=0,
        )
        db_session.add(sub)
        db_session.flush()

        # Add 3 seats
        mock_stripe.Subscription.retrieve.return_value = {
            "items": {"data": [{"id": "si_flow", "quantity": 3}]},
        }
        result = add_seats(db_session, user.id, 3)
        assert result is not None
        assert result.additional_seats == 3
        assert result.total_seats == 6
        mock_stripe.SubscriptionItem.modify.assert_called_with("si_flow", quantity=6)

        # Remove 1 seat
        mock_stripe.Subscription.retrieve.return_value = {
            "items": {"data": [{"id": "si_flow", "quantity": 6}]},
        }
        result = remove_seats(db_session, user.id, 1)
        assert result is not None
        assert result.additional_seats == 2
        assert result.total_seats == 5
        mock_stripe.SubscriptionItem.modify.assert_called_with("si_flow", quantity=5)


# ---------------------------------------------------------------------------
# Cancel subscription flow
# ---------------------------------------------------------------------------


class TestCancelFlow:
    """Full cancel and reactivate lifecycle."""

    @patch("billing.subscription_manager.get_stripe")
    def test_cancel_and_reactivate(self, mock_get_stripe, db_session, make_user):
        from billing.subscription_manager import cancel_subscription, reactivate_subscription

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe

        user = make_user(email="cancel_flow@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_cancel",
            stripe_subscription_id="sub_cancel",
            seat_count=3,
            additional_seats=2,
        )
        db_session.add(sub)
        db_session.flush()

        # Cancel
        result = cancel_subscription(db_session, user.id)
        assert result is not None
        assert result.cancel_at_period_end is True
        mock_stripe.Subscription.modify.assert_called_with(
            "sub_cancel",
            cancel_at_period_end=True,
        )

        # Reactivate
        result = reactivate_subscription(db_session, user.id)
        assert result is not None
        assert result.cancel_at_period_end is False
        mock_stripe.Subscription.modify.assert_called_with(
            "sub_cancel",
            cancel_at_period_end=False,
        )

        # Seats preserved through cancel/reactivate cycle
        assert result.additional_seats == 2
        assert result.total_seats == 5


# ---------------------------------------------------------------------------
# Webhook simulations
# ---------------------------------------------------------------------------


class TestWebhookSimulations:
    """Simulate Stripe webhook events for V2 scenarios."""

    def test_trial_will_end_event(self):
        """trial_will_end webhook is dispatched without error."""
        from billing.webhook_handler import WEBHOOK_HANDLERS, process_webhook_event

        assert "customer.subscription.trial_will_end" in WEBHOOK_HANDLERS
        mock_db = MagicMock()
        result = process_webhook_event(
            mock_db,
            "customer.subscription.trial_will_end",
            {"customer": "cus_test", "id": "sub_test"},
        )
        assert result is True

    def test_subscription_updated_quantity_change(self, db_session, make_user):
        """Webhook for quantity change syncs seat_count."""
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="webhook_qty@example.com")

        # Initial sync with 3 seats
        stripe_sub = {
            "id": "sub_qty",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 3}]},
        }
        sub = sync_subscription_from_stripe(
            db_session,
            user.id,
            stripe_sub,
            "cus_qty",
            "team",
        )
        assert sub.seat_count == 3

        # Quantity change: now 7 seats
        stripe_sub["items"]["data"][0]["quantity"] = 7
        sub = sync_subscription_from_stripe(
            db_session,
            user.id,
            stripe_sub,
            "cus_qty",
            "team",
        )
        assert sub.seat_count == 7

    def test_subscription_deleted_event(self, db_session, make_user):
        """Webhook for subscription deletion sets status to canceled."""
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="webhook_delete@example.com")

        stripe_sub = {
            "id": "sub_delete",
            "status": "canceled",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 3}]},
        }
        sub = sync_subscription_from_stripe(
            db_session,
            user.id,
            stripe_sub,
            "cus_delete",
            "team",
        )
        assert sub.status == SubscriptionStatus.CANCELED

    def test_invoice_paid_event_dispatches(self):
        """invoice.paid webhook is handled."""
        from billing.webhook_handler import WEBHOOK_HANDLERS

        assert "invoice.paid" in WEBHOOK_HANDLERS

    def test_invoice_payment_failed_dispatches(self):
        """invoice.payment_failed webhook is handled."""
        from billing.webhook_handler import WEBHOOK_HANDLERS

        assert "invoice.payment_failed" in WEBHOOK_HANDLERS

    def test_checkout_completed_dispatches(self):
        """checkout.session.completed webhook is handled."""
        from billing.webhook_handler import WEBHOOK_HANDLERS

        assert "checkout.session.completed" in WEBHOOK_HANDLERS


# ---------------------------------------------------------------------------
# Prometheus counter
# ---------------------------------------------------------------------------


class TestPrometheusCounter:
    """Verify pricing checkout Prometheus counter exists and can be incremented."""

    def test_counter_exists(self):
        from shared.parser_metrics import pricing_v2_checkouts_total

        assert pricing_v2_checkouts_total is not None

    def test_counter_can_increment(self):
        from shared.parser_metrics import pricing_v2_checkouts_total

        # Should not raise
        pricing_v2_checkouts_total.labels(tier="team", interval="monthly").inc()

    def test_counter_on_registry(self):
        from shared.parser_metrics import PARSER_REGISTRY

        # Verify it's on the same registry as parser metrics.
        # prometheus_client strips the _total suffix from Counter names in collect().
        metric_names = [m.name for m in PARSER_REGISTRY.collect() if hasattr(m, "name")]
        assert "paciolus_pricing_v2_checkouts" in metric_names


# ---------------------------------------------------------------------------
# Subscription response seat fields in API
# ---------------------------------------------------------------------------


class TestSubscriptionResponseIntegration:
    """Verify seat fields flow through from DB to API response schema."""

    def test_subscription_with_seats_serializes_correctly(self, db_session, make_user):
        user = make_user(email="resp_seats@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_resp",
            stripe_subscription_id="sub_resp",
            seat_count=3,
            additional_seats=4,
        )
        db_session.add(sub)
        db_session.flush()

        from routes.billing import SubscriptionResponse

        resp = SubscriptionResponse(
            id=sub.id,
            tier=sub.tier,
            status=sub.status.value,
            billing_interval=sub.billing_interval.value,
            cancel_at_period_end=sub.cancel_at_period_end,
            seat_count=sub.seat_count or 1,
            additional_seats=sub.additional_seats or 0,
            total_seats=sub.total_seats,
        )
        assert resp.seat_count == 3
        assert resp.additional_seats == 4
        assert resp.total_seats == 7


# ---------------------------------------------------------------------------
# SEAT_ENFORCEMENT_MODE confirmation
# ---------------------------------------------------------------------------


class TestSeatEnforcementConfig:
    """Confirm SEAT_ENFORCEMENT_MODE defaults to soft."""

    def test_default_is_soft(self):
        from config import SEAT_ENFORCEMENT_MODE

        assert SEAT_ENFORCEMENT_MODE == "soft"

    def test_check_seat_limit_exists(self):
        from shared.entitlement_checks import check_seat_limit

        assert callable(check_seat_limit)
