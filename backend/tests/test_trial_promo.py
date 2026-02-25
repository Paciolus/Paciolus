"""
Trial & promo tests — Phase LIX Sprint C.

Covers:
1. TRIAL_PERIOD_DAYS constant and TRIAL_ELIGIBLE_TIERS
2. PROMO_CODES structure and validation
3. get_stripe_coupon_id() resolution
4. validate_promo_for_interval() interval matching
5. create_checkout_session() trial + coupon parameters
6. Webhook handler: trial_will_end event
7. Billing route: promo_code field and validation
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from billing.price_config import (
    PROMO_CODES,
    TRIAL_ELIGIBLE_TIERS,
    TRIAL_PERIOD_DAYS,
    get_stripe_coupon_id,
    validate_promo_for_interval,
)

# ---------------------------------------------------------------------------
# Trial period configuration
# ---------------------------------------------------------------------------


class TestTrialConfig:
    """Verify trial period constants."""

    def test_trial_period_is_7_days(self):
        assert TRIAL_PERIOD_DAYS == 7

    def test_trial_eligible_tiers_are_paid(self):
        assert "solo" in TRIAL_ELIGIBLE_TIERS
        assert "team" in TRIAL_ELIGIBLE_TIERS
        assert "enterprise" in TRIAL_ELIGIBLE_TIERS

    def test_free_tier_not_eligible_for_trial(self):
        assert "free" not in TRIAL_ELIGIBLE_TIERS

    def test_trial_eligible_tiers_is_frozenset(self):
        assert isinstance(TRIAL_ELIGIBLE_TIERS, frozenset)


# ---------------------------------------------------------------------------
# Promo code structure
# ---------------------------------------------------------------------------


class TestPromoCodes:
    """Verify promo code mapping structure."""

    def test_monthly20_maps_to_monthly(self):
        assert PROMO_CODES["MONTHLY20"] == "monthly"

    def test_annual10_maps_to_annual(self):
        assert PROMO_CODES["ANNUAL10"] == "annual"

    def test_exactly_two_promo_codes(self):
        assert len(PROMO_CODES) == 2

    def test_all_values_are_valid_intervals(self):
        for code, interval in PROMO_CODES.items():
            assert interval in ("monthly", "annual"), f"{code} maps to invalid interval: {interval}"


# ---------------------------------------------------------------------------
# Promo validation
# ---------------------------------------------------------------------------


class TestValidatePromoForInterval:
    """Validate promo code / interval compatibility."""

    def test_monthly20_on_monthly_is_valid(self):
        assert validate_promo_for_interval("MONTHLY20", "monthly") is None

    def test_annual10_on_annual_is_valid(self):
        assert validate_promo_for_interval("ANNUAL10", "annual") is None

    def test_monthly20_on_annual_rejected(self):
        error = validate_promo_for_interval("MONTHLY20", "annual")
        assert error is not None
        assert "monthly" in error

    def test_annual10_on_monthly_rejected(self):
        error = validate_promo_for_interval("ANNUAL10", "monthly")
        assert error is not None
        assert "annual" in error

    def test_unknown_promo_code_rejected(self):
        error = validate_promo_for_interval("BADCODE", "monthly")
        assert error is not None
        assert "Unknown" in error

    def test_case_insensitive(self):
        assert validate_promo_for_interval("monthly20", "monthly") is None
        assert validate_promo_for_interval("Annual10", "annual") is None

    def test_empty_promo_code_rejected(self):
        error = validate_promo_for_interval("", "monthly")
        assert error is not None


# ---------------------------------------------------------------------------
# Stripe coupon ID resolution
# ---------------------------------------------------------------------------


class TestGetStripeCouponId:
    """Test resolution of promo code to Stripe Coupon ID."""

    @patch("billing.price_config._load_coupon_ids")
    def test_monthly20_resolves_to_coupon(self, mock_load):
        mock_load.return_value = {
            "monthly": "coupon_monthly_20_abc",
            "annual": "coupon_annual_10_xyz",
        }
        assert get_stripe_coupon_id("MONTHLY20") == "coupon_monthly_20_abc"

    @patch("billing.price_config._load_coupon_ids")
    def test_annual10_resolves_to_coupon(self, mock_load):
        mock_load.return_value = {
            "monthly": "coupon_monthly_20_abc",
            "annual": "coupon_annual_10_xyz",
        }
        assert get_stripe_coupon_id("ANNUAL10") == "coupon_annual_10_xyz"

    @patch("billing.price_config._load_coupon_ids")
    def test_unknown_code_returns_none(self, mock_load):
        mock_load.return_value = {"monthly": "x", "annual": "y"}
        assert get_stripe_coupon_id("BADCODE") is None

    @patch("billing.price_config._load_coupon_ids")
    def test_unconfigured_coupon_returns_none(self, mock_load):
        mock_load.return_value = {"monthly": "", "annual": ""}
        assert get_stripe_coupon_id("MONTHLY20") is None

    @patch("billing.price_config._load_coupon_ids")
    def test_case_insensitive_lookup(self, mock_load):
        mock_load.return_value = {"monthly": "coupon_abc", "annual": ""}
        assert get_stripe_coupon_id("monthly20") == "coupon_abc"


# ---------------------------------------------------------------------------
# Checkout session creation with trial + coupon
# ---------------------------------------------------------------------------


class TestCheckoutSessionTrialAndCoupon:
    """Test create_checkout_session() with trial and coupon parameters."""

    def _mock_stripe(self):
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/cs_test_123"
        mock_stripe.checkout.Session.create.return_value = mock_session
        return mock_stripe

    @patch("billing.checkout.get_stripe")
    def test_no_trial_no_coupon(self, mock_get_stripe):
        mock_stripe = self._mock_stripe()
        mock_get_stripe.return_value = mock_stripe

        from billing.checkout import create_checkout_session

        url = create_checkout_session(
            customer_id="cus_123",
            plan_price_id="price_abc",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            user_id=1,
        )
        assert url == "https://checkout.stripe.com/cs_test_123"

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        sub_data = call_kwargs["subscription_data"]
        assert "trial_period_days" not in sub_data
        assert "discounts" not in call_kwargs

    @patch("billing.checkout.get_stripe")
    def test_with_trial_period(self, mock_get_stripe):
        mock_stripe = self._mock_stripe()
        mock_get_stripe.return_value = mock_stripe

        from billing.checkout import create_checkout_session

        create_checkout_session(
            customer_id="cus_123",
            plan_price_id="price_abc",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            user_id=1,
            trial_period_days=7,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        sub_data = call_kwargs["subscription_data"]
        assert sub_data["trial_period_days"] == 7

    @patch("billing.checkout.get_stripe")
    def test_with_coupon(self, mock_get_stripe):
        mock_stripe = self._mock_stripe()
        mock_get_stripe.return_value = mock_stripe

        from billing.checkout import create_checkout_session

        create_checkout_session(
            customer_id="cus_123",
            plan_price_id="price_abc",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            user_id=1,
            stripe_coupon_id="coupon_monthly_20",
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["discounts"] == [{"coupon": "coupon_monthly_20"}]

    @patch("billing.checkout.get_stripe")
    def test_with_trial_and_coupon(self, mock_get_stripe):
        mock_stripe = self._mock_stripe()
        mock_get_stripe.return_value = mock_stripe

        from billing.checkout import create_checkout_session

        create_checkout_session(
            customer_id="cus_123",
            plan_price_id="price_abc",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            user_id=1,
            trial_period_days=7,
            stripe_coupon_id="coupon_annual_10",
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["subscription_data"]["trial_period_days"] == 7
        assert call_kwargs["discounts"] == [{"coupon": "coupon_annual_10"}]

    @patch("billing.checkout.get_stripe")
    def test_zero_trial_days_not_included(self, mock_get_stripe):
        mock_stripe = self._mock_stripe()
        mock_get_stripe.return_value = mock_stripe

        from billing.checkout import create_checkout_session

        create_checkout_session(
            customer_id="cus_123",
            plan_price_id="price_abc",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            user_id=1,
            trial_period_days=0,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert "trial_period_days" not in call_kwargs["subscription_data"]

    @patch("billing.checkout.get_stripe")
    def test_none_coupon_not_included(self, mock_get_stripe):
        mock_stripe = self._mock_stripe()
        mock_get_stripe.return_value = mock_stripe

        from billing.checkout import create_checkout_session

        create_checkout_session(
            customer_id="cus_123",
            plan_price_id="price_abc",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            user_id=1,
            stripe_coupon_id=None,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert "discounts" not in call_kwargs


# ---------------------------------------------------------------------------
# Webhook: trial_will_end
# ---------------------------------------------------------------------------


class TestTrialWillEndWebhook:
    """Test the trial_will_end webhook handler."""

    def test_handler_registered(self):
        from billing.webhook_handler import WEBHOOK_HANDLERS

        assert "customer.subscription.trial_will_end" in WEBHOOK_HANDLERS

    def test_all_expected_events_registered(self):
        from billing.webhook_handler import WEBHOOK_HANDLERS

        expected = {
            "checkout.session.completed",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "customer.subscription.trial_will_end",
            "invoice.payment_failed",
            "invoice.paid",
        }
        assert set(WEBHOOK_HANDLERS.keys()) == expected

    def test_trial_will_end_with_valid_user(self):
        from billing.webhook_handler import handle_subscription_trial_will_end

        mock_db = MagicMock()
        event_data = {
            "metadata": {"paciolus_user_id": "42"},
            "trial_end": 1700000000,
        }

        # Should not raise — just logs
        handle_subscription_trial_will_end(mock_db, event_data)

    def test_trial_will_end_unknown_user(self):
        from billing.webhook_handler import handle_subscription_trial_will_end

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        event_data = {}

        # Should not raise — gracefully logs warning
        handle_subscription_trial_will_end(mock_db, event_data)

    def test_process_webhook_dispatches_trial_event(self):
        from billing.webhook_handler import process_webhook_event

        mock_db = MagicMock()
        event_data = {
            "metadata": {"paciolus_user_id": "1"},
            "trial_end": 1700000000,
        }

        result = process_webhook_event(mock_db, "customer.subscription.trial_will_end", event_data)
        assert result is True


# ---------------------------------------------------------------------------
# Billing route: CheckoutRequest promo_code field
# ---------------------------------------------------------------------------


class TestCheckoutRequestPromoField:
    """Test that CheckoutRequest accepts promo_code."""

    def test_checkout_request_accepts_promo_code(self):
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier="solo",
            interval="monthly",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            promo_code="MONTHLY20",
        )
        assert req.promo_code == "MONTHLY20"

    def test_checkout_request_promo_code_optional(self):
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier="team",
            interval="annual",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
        )
        assert req.promo_code is None

    def test_checkout_request_promo_code_none_explicit(self):
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier="enterprise",
            interval="monthly",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel",
            promo_code=None,
        )
        assert req.promo_code is None

    def test_checkout_request_promo_code_max_length(self):
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="solo",
                interval="monthly",
                success_url="https://app.com/success",
                cancel_url="https://app.com/cancel",
                promo_code="X" * 51,
            )

    def test_checkout_request_still_validates_tier(self):
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="professional",
                interval="monthly",
                success_url="https://app.com/success",
                cancel_url="https://app.com/cancel",
                promo_code="MONTHLY20",
            )
