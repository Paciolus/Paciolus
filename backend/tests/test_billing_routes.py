"""
Billing route tests — Sprint 376.

Tests billing API endpoints with mocked Stripe client.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import User, UserTier
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
            tier=UserTier.STARTER,
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
