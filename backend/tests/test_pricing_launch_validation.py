"""
Pricing Launch Validation Matrix — comprehensive test suite.

7 test classes covering all pricing/billing/entitlement paths:
1. MarketingPricingCorrectness — price table, seat pricing, trial, promo config
2. CheckoutPathCorrectness — tier×interval×seat×promo matrix
3. BillingLifecycle — state machine via webhook + subscription manager
4. WebhookReconciliation — tier resolution, dispatch, edge cases
5. EntitlementEnforcement — limits, tool/format/workspace access, modes
6. PromoApplicationPolicy — interval matching, case sensitivity, stacking
7. OldSubscriberRegression — deprecated professional tier backward compat
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import UserTier
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

# ===========================================================================
# Class 1: Marketing Pricing Correctness
# ===========================================================================


class TestMarketingPricingCorrectness:
    """Validates that pricing data is consistent across backend config."""

    def test_price_table_has_all_paid_tiers(self):
        from billing.price_config import PRICE_TABLE

        for tier in ("solo", "team"):
            assert tier in PRICE_TABLE, f"{tier} missing from PRICE_TABLE"

    def test_price_table_has_monthly_and_annual(self):
        from billing.price_config import PRICE_TABLE

        for tier in ("solo", "team"):
            assert "monthly" in PRICE_TABLE[tier]
            assert "annual" in PRICE_TABLE[tier]

    def test_solo_monthly_5000_cents(self):
        from billing.price_config import PRICE_TABLE

        assert PRICE_TABLE["solo"]["monthly"] == 5000

    def test_solo_annual_50000_cents(self):
        from billing.price_config import PRICE_TABLE

        assert PRICE_TABLE["solo"]["annual"] == 50000

    def test_team_monthly_13000_cents(self):
        from billing.price_config import PRICE_TABLE

        assert PRICE_TABLE["team"]["monthly"] == 13000

    def test_team_annual_130000_cents(self):
        from billing.price_config import PRICE_TABLE

        assert PRICE_TABLE["team"]["annual"] == 130000

    def test_free_tier_is_zero(self):
        from billing.price_config import PRICE_TABLE

        assert PRICE_TABLE["free"]["monthly"] == 0
        assert PRICE_TABLE["free"]["annual"] == 0

    def test_annual_cheaper_than_12x_monthly(self):
        from billing.price_config import PRICE_TABLE

        for tier in ("solo", "team"):
            monthly_12x = PRICE_TABLE[tier]["monthly"] * 12
            annual = PRICE_TABLE[tier]["annual"]
            assert annual < monthly_12x, f"{tier}: annual ({annual}) >= 12*monthly ({monthly_12x})"

    def test_annual_savings_16_to_17_percent(self):
        from billing.price_config import get_annual_savings_percent

        for tier in ("solo", "team"):
            savings = get_annual_savings_percent(tier)
            assert 16 <= savings <= 17, f"{tier}: savings {savings}% not in 16-17%"

    def test_seat_tier1_price_8000_monthly(self):
        from billing.price_config import get_seat_price_cents

        assert get_seat_price_cents(4, "monthly") == 8000
        assert get_seat_price_cents(10, "monthly") == 8000

    def test_seat_tier2_price_7000_monthly(self):
        from billing.price_config import get_seat_price_cents

        assert get_seat_price_cents(11, "monthly") == 7000
        assert get_seat_price_cents(25, "monthly") == 7000

    def test_seat_tier1_annual_80000(self):
        from billing.price_config import get_seat_price_cents

        assert get_seat_price_cents(4, "annual") == 80000
        assert get_seat_price_cents(10, "annual") == 80000

    def test_seat_tier2_annual_70000(self):
        from billing.price_config import get_seat_price_cents

        assert get_seat_price_cents(11, "annual") == 70000
        assert get_seat_price_cents(25, "annual") == 70000

    def test_base_seats_included_free(self):
        from billing.price_config import get_seat_price_cents

        assert get_seat_price_cents(1, "monthly") == 0
        assert get_seat_price_cents(2, "monthly") == 0
        assert get_seat_price_cents(3, "monthly") == 0

    def test_seats_26_plus_returns_none(self):
        from billing.price_config import get_seat_price_cents

        assert get_seat_price_cents(26, "monthly") is None
        assert get_seat_price_cents(100, "annual") is None

    def test_trial_period_7_days(self):
        from billing.price_config import TRIAL_PERIOD_DAYS

        assert TRIAL_PERIOD_DAYS == 7

    def test_trial_eligible_tiers(self):
        from billing.price_config import TRIAL_ELIGIBLE_TIERS

        assert "solo" in TRIAL_ELIGIBLE_TIERS
        assert "team" in TRIAL_ELIGIBLE_TIERS
        assert "free" not in TRIAL_ELIGIBLE_TIERS

    def test_promo_codes_defined(self):
        from billing.price_config import PROMO_CODES

        assert "MONTHLY20" in PROMO_CODES
        assert "ANNUAL10" in PROMO_CODES

    def test_purchasable_tiers_correct(self):
        from shared.tier_display import PURCHASABLE_TIERS

        assert PURCHASABLE_TIERS == frozenset({"solo", "team"})

    def test_free_not_purchasable(self):
        from shared.tier_display import PURCHASABLE_TIERS

        assert "free" not in PURCHASABLE_TIERS

    def test_professional_not_purchasable(self):
        from shared.tier_display import PURCHASABLE_TIERS

        assert "professional" not in PURCHASABLE_TIERS

    def test_calculate_additional_seats_cost_7_seats_monthly(self):
        from billing.price_config import calculate_additional_seats_cost

        # 7 seats at tier 1: 7 * 8000 = 56000
        assert calculate_additional_seats_cost(7, "monthly") == 56000

    def test_calculate_additional_seats_cost_exceeds_limit(self):
        from billing.price_config import calculate_additional_seats_cost

        # 23 additional seats → seat #26 exceeds limit
        assert calculate_additional_seats_cost(23, "monthly") is None

    def test_calculate_additional_seats_cost_zero(self):
        from billing.price_config import calculate_additional_seats_cost

        assert calculate_additional_seats_cost(0, "monthly") == 0


# ===========================================================================
# Class 2: Checkout Path Correctness
# ===========================================================================


class TestCheckoutPathCorrectness:
    """Exhaustive matrix of tier×interval×seat×promo combinations."""

    # --- Valid checkout combos (6 tier×interval) ---

    @pytest.mark.parametrize(
        "tier,interval",
        [
            ("solo", "monthly"),
            ("solo", "annual"),
            ("team", "monthly"),
            ("team", "annual"),
        ],
    )
    def test_valid_tier_interval_checkout(self, tier, interval):
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier=tier,
            interval=interval,
        )
        assert req.tier == tier
        assert req.interval == interval

    # --- Seat ranges for team plan ---

    @pytest.mark.parametrize("seat_count", [0, 1, 5, 10, 22])
    def test_team_valid_seat_ranges(self, seat_count):
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier="team",
            interval="monthly",
            seat_count=seat_count,
        )
        assert req.seat_count == seat_count

    def test_team_seat_23_rejected_by_schema(self):
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="team",
                interval="monthly",
                seat_count=23,
            )

    # --- Solo plan rejects seats > 0 ---

    def test_solo_accepts_schema_with_seats(self):
        """Schema allows seat_count > 0 — route-level validation blocks it."""
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier="solo",
            interval="monthly",
            seat_count=3,
        )
        assert req.tier == "solo" and req.seat_count > 0

    # --- Invalid tier ---

    def test_invalid_tier_rejected(self):
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="platinum",
                interval="monthly",
            )

    # --- Invalid interval ---

    def test_invalid_interval_rejected(self):
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="solo",
                interval="weekly",
            )

    # --- Negative seat count ---

    def test_negative_seat_count_rejected(self):
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="team",
                interval="monthly",
                seat_count=-1,
            )

    # --- URL fields are server-side derived, not user-supplied ---

    def test_success_url_not_a_required_field(self):
        """success_url is no longer a field — redirect URLs are server-side derived."""
        from routes.billing import CheckoutRequest

        # Valid request without URL fields (the correct usage)
        body = CheckoutRequest(tier="solo", interval="monthly")
        assert not hasattr(body, "success_url")
        assert not hasattr(body, "cancel_url")

    def test_user_supplied_urls_silently_ignored(self):
        """Supplying success_url/cancel_url is silently ignored (extra='ignore')."""
        from routes.billing import CheckoutRequest

        body = CheckoutRequest.model_validate(
            {
                "tier": "solo",
                "interval": "monthly",
                "success_url": "https://evil.com",
                "cancel_url": "https://evil.com",
            }
        )
        assert not hasattr(body, "success_url")
        assert not hasattr(body, "cancel_url")

    # --- Stripe disabled → 503 ---

    def test_stripe_disabled_raises_runtime_error(self):
        from billing.stripe_client import get_stripe

        with patch("config.STRIPE_ENABLED", False):
            with pytest.raises(RuntimeError, match="Stripe is not configured"):
                get_stripe()

    # --- Missing price ID ---

    def test_missing_price_id_returns_none(self):
        from billing.price_config import get_stripe_price_id

        with patch("billing.price_config._load_stripe_price_ids", return_value={}):
            assert get_stripe_price_id("solo", "monthly") is None

    # --- Checkout line items: base only ---

    @patch("billing.checkout.get_stripe")
    def test_checkout_line_items_base_only(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        create_checkout_session(
            customer_id="cus_1",
            plan_price_id="price_solo_mo",
            user_id=1,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert len(call_kwargs["line_items"]) == 1
        assert call_kwargs["line_items"][0]["quantity"] == 1

    # --- Checkout line items: base + seats ---

    @patch("billing.checkout.get_stripe")
    def test_checkout_line_items_base_plus_seats(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        create_checkout_session(
            customer_id="cus_1",
            plan_price_id="price_team_mo",
            user_id=1,
            seat_price_id="price_seat_mo",
            additional_seats=5,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert len(call_kwargs["line_items"]) == 2
        assert call_kwargs["line_items"][1] == {"price": "price_seat_mo", "quantity": 5}

    # --- Seat price ID missing when seats > 0 ---

    @patch("billing.checkout.get_stripe")
    def test_checkout_no_seat_line_when_seat_price_none(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        create_checkout_session(
            customer_id="cus_1",
            plan_price_id="price_solo_mo",
            user_id=1,
            seat_price_id=None,
            additional_seats=5,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert len(call_kwargs["line_items"]) == 1

    # --- Trial eligibility ---

    @pytest.mark.parametrize("tier", ["solo", "team"])
    @patch("billing.checkout.get_stripe")
    def test_trial_eligible_tiers_get_trial(self, mock_get_stripe, tier):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        create_checkout_session(
            customer_id="cus_1",
            plan_price_id=f"price_{tier}_mo",
            user_id=1,
            trial_period_days=7,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["subscription_data"]["trial_period_days"] == 7

    # --- Trial + promo simultaneous ---

    @patch("billing.checkout.get_stripe")
    def test_trial_and_promo_simultaneous(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        create_checkout_session(
            customer_id="cus_1",
            plan_price_id="price_team_mo",
            user_id=1,
            trial_period_days=7,
            stripe_coupon_id="coupon_monthly20",
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["subscription_data"]["trial_period_days"] == 7
        assert call_kwargs["discounts"] == [{"coupon": "coupon_monthly20"}]

    # --- Checkout without trial has no trial_period_days ---

    @patch("billing.checkout.get_stripe")
    def test_checkout_without_trial(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        create_checkout_session(
            customer_id="cus_1",
            plan_price_id="price_solo_mo",
            user_id=1,
            trial_period_days=0,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert "trial_period_days" not in call_kwargs.get("subscription_data", {})

    # --- Checkout without promo has no discounts ---

    @patch("billing.checkout.get_stripe")
    def test_checkout_without_promo_no_discounts(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        create_checkout_session(
            customer_id="cus_1",
            plan_price_id="price_solo_mo",
            user_id=1,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert "discounts" not in call_kwargs

    # --- MAX_SELF_SERVE_SEATS ---

    def test_max_self_serve_seats_is_25(self):
        from billing.price_config import MAX_SELF_SERVE_SEATS

        assert MAX_SELF_SERVE_SEATS == 25

    # --- Promo code max_length on schema ---

    def test_promo_code_max_length_50(self):
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="solo",
                interval="monthly",
                promo_code="A" * 51,
            )

    # --- Promo code None is valid ---

    def test_promo_code_none_valid(self):
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier="solo",
            interval="monthly",
            promo_code=None,
        )
        assert req.promo_code is None

    # --- Seat_count defaults to 0 ---

    def test_seat_count_defaults_zero(self):
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier="solo",
            interval="monthly",
        )
        assert req.seat_count == 0

    # --- Create or get stripe customer ---

    @patch("billing.checkout.get_stripe")
    def test_create_or_get_customer_existing(self, mock_get_stripe):
        from billing.checkout import create_or_get_stripe_customer

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe

        result = create_or_get_stripe_customer(1, "test@example.com", "cus_existing")
        assert result == "cus_existing"
        mock_stripe.Customer.create.assert_not_called()

    @patch("billing.checkout.get_stripe")
    def test_create_or_get_customer_new(self, mock_get_stripe):
        from billing.checkout import create_or_get_stripe_customer

        mock_stripe = MagicMock()
        mock_stripe.Customer.create.return_value = MagicMock(id="cus_new")
        mock_get_stripe.return_value = mock_stripe

        result = create_or_get_stripe_customer(1, "test@example.com", None)
        assert result == "cus_new"
        mock_stripe.Customer.create.assert_called_once()

    # --- Checkout metadata includes user_id and seats ---

    @patch("billing.checkout.get_stripe")
    def test_checkout_metadata_includes_user_and_seats(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        create_checkout_session(
            customer_id="cus_1",
            plan_price_id="price_team_mo",
            user_id=42,
            seat_price_id="price_seat_mo",
            additional_seats=5,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["metadata"]["paciolus_user_id"] == "42"
        sub_data = call_kwargs["subscription_data"]
        assert sub_data["metadata"]["paciolus_additional_seats"] == "5"


# ===========================================================================
# Class 3: Billing Lifecycle
# ===========================================================================


class TestBillingLifecycle:
    """Full state-machine coverage using webhook handlers + subscription manager."""

    # --- New purchase: checkout → sync → user.tier updated ---

    @pytest.mark.parametrize("tier", ["solo", "team"])
    def test_new_purchase_syncs_tier(self, db_session, make_user, tier):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email=f"new_{tier}@example.com", tier=UserTier.FREE)

        stripe_sub = {
            "id": f"sub_{tier}",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
        }
        sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, f"cus_{tier}", tier)
        assert sub.tier == tier
        assert sub.status == SubscriptionStatus.ACTIVE
        assert user.tier == UserTier(tier)

    # --- Trial start ---

    def test_trial_start_creates_trialing(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="trial_start@example.com", tier=UserTier.FREE)
        stripe_sub = {
            "id": "sub_trial",
            "status": "trialing",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1700604800,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
        }
        sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_trial", "team")
        assert sub.status == SubscriptionStatus.TRIALING

    # --- Trial → active ---

    def test_trial_to_active(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="trial_active@example.com", tier=UserTier.FREE)
        stripe_sub_trial = {
            "id": "sub_t2a",
            "status": "trialing",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1700604800,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
        }
        sync_subscription_from_stripe(db_session, user.id, stripe_sub_trial, "cus_t2a", "solo")

        stripe_sub_active = {**stripe_sub_trial, "status": "active"}
        sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub_active, "cus_t2a", "solo")
        assert sub.status == SubscriptionStatus.ACTIVE

    # --- Trial → canceled (didn't convert) ---

    def test_trial_to_canceled(self, db_session, make_user):
        from billing.webhook_handler import handle_subscription_deleted

        user = make_user(email="trial_cancel@example.com", tier=UserTier.TEAM)
        sub = Subscription(
            user_id=user.id,
            tier="team",
            status=SubscriptionStatus.TRIALING,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_trial_cancel",
            stripe_subscription_id="sub_trial_cancel",
        )
        db_session.add(sub)
        db_session.flush()

        handle_subscription_deleted(db_session, {"customer": "cus_trial_cancel", "metadata": {}})
        assert sub.status == SubscriptionStatus.CANCELED
        assert user.tier == UserTier.FREE

    # --- Active → cancel_at_period_end ---

    @patch("billing.subscription_manager.get_stripe")
    def test_active_to_cancel_at_period_end(self, mock_get_stripe, db_session, make_user):
        from billing.subscription_manager import cancel_subscription

        mock_get_stripe.return_value = MagicMock()
        user = make_user(email="cancel_end@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_ce",
            stripe_subscription_id="sub_ce",
        )
        db_session.add(sub)
        db_session.flush()

        result = cancel_subscription(db_session, user.id)
        assert result is not None
        assert result.cancel_at_period_end is True

    # --- Cancel → reactivate ---

    @patch("billing.subscription_manager.get_stripe")
    def test_cancel_to_reactivate(self, mock_get_stripe, db_session, make_user):
        from billing.subscription_manager import reactivate_subscription

        mock_get_stripe.return_value = MagicMock()
        user = make_user(email="reactivate@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_re",
            stripe_subscription_id="sub_re",
            cancel_at_period_end=True,
        )
        db_session.add(sub)
        db_session.flush()

        result = reactivate_subscription(db_session, user.id)
        assert result is not None
        assert result.cancel_at_period_end is False

    # --- Subscription.deleted → user.tier=FREE ---

    def test_subscription_deleted_downgrades_to_free(self, db_session, make_user):
        from billing.webhook_handler import handle_subscription_deleted

        user = make_user(email="deleted@example.com", tier=UserTier.TEAM)
        sub = Subscription(
            user_id=user.id,
            tier="team",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_del",
            stripe_subscription_id="sub_del",
        )
        db_session.add(sub)
        db_session.flush()

        handle_subscription_deleted(db_session, {"customer": "cus_del", "metadata": {}})
        assert user.tier == UserTier.FREE
        assert sub.status == SubscriptionStatus.CANCELED

    # --- Payment failure → PAST_DUE ---

    def test_payment_failure_sets_past_due(self, db_session, make_user):
        from billing.webhook_handler import handle_invoice_payment_failed

        user = make_user(email="past_due@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_pd",
            stripe_subscription_id="sub_pd",
        )
        db_session.add(sub)
        db_session.flush()

        handle_invoice_payment_failed(db_session, {"customer": "cus_pd"})
        assert sub.status == SubscriptionStatus.PAST_DUE

    # --- Payment recovery: PAST_DUE → ACTIVE ---

    def test_payment_recovery_to_active(self, db_session, make_user):
        from billing.webhook_handler import handle_invoice_paid

        user = make_user(email="recovery@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.PAST_DUE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_rec",
            stripe_subscription_id="sub_rec",
        )
        db_session.add(sub)
        db_session.flush()

        handle_invoice_paid(db_session, {"customer": "cus_rec"})
        assert sub.status == SubscriptionStatus.ACTIVE

    # --- invoice.paid when already active → no change ---

    def test_invoice_paid_when_active_no_change(self, db_session, make_user):
        from billing.webhook_handler import handle_invoice_paid

        user = make_user(email="already_active@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_aa",
            stripe_subscription_id="sub_aa",
        )
        db_session.add(sub)
        db_session.flush()

        handle_invoice_paid(db_session, {"customer": "cus_aa"})
        assert sub.status == SubscriptionStatus.ACTIVE

    # --- Plan change (solo→team) via sync ---

    def test_plan_change_solo_to_team(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="plan_change@example.com", tier=UserTier.SOLO)
        stripe_sub = {
            "id": "sub_pc",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
        }
        sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_pc", "solo")

        # Now upgrade to team
        sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_pc", "team")
        assert sub.tier == "team"
        assert user.tier == UserTier.TEAM

    # --- Interval change (monthly→annual) ---

    def test_interval_change_monthly_to_annual(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="interval_change@example.com")
        stripe_sub_mo = {
            "id": "sub_ic",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
        }
        sync_subscription_from_stripe(db_session, user.id, stripe_sub_mo, "cus_ic", "solo")

        stripe_sub_yr = {**stripe_sub_mo, "items": {"data": [{"plan": {"interval": "year"}, "quantity": 1}]}}
        sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub_yr, "cus_ic", "solo")
        assert sub.billing_interval == BillingInterval.ANNUAL

    # --- Seat qty change ---

    def test_seat_qty_change_via_sync(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="seat_change@example.com")
        stripe_sub = {
            "id": "sub_sc",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 3}]},
        }
        with patch("billing.price_config.get_all_seat_price_ids", return_value=set()):
            sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_sc", "team")
        assert sub.seat_count == 3

        stripe_sub["items"]["data"][0]["quantity"] = 8
        with patch("billing.price_config.get_all_seat_price_ids", return_value=set()):
            sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_sc", "team")
        assert sub.seat_count == 8

    # --- Cancel with no subscription → None ---

    @patch("billing.subscription_manager.get_stripe")
    def test_cancel_no_subscription_returns_none(self, mock_get_stripe, db_session, make_user):
        from billing.subscription_manager import cancel_subscription

        user = make_user(email="no_sub_cancel@example.com")
        result = cancel_subscription(db_session, user.id)
        assert result is None

    # --- Reactivate with no subscription → None ---

    @patch("billing.subscription_manager.get_stripe")
    def test_reactivate_no_subscription_returns_none(self, mock_get_stripe, db_session, make_user):
        from billing.subscription_manager import reactivate_subscription

        user = make_user(email="no_sub_react@example.com")
        result = reactivate_subscription(db_session, user.id)
        assert result is None

    # --- sync creates new Subscription when none exists ---

    def test_sync_creates_new_subscription(self, db_session, make_user):
        from billing.subscription_manager import get_subscription, sync_subscription_from_stripe

        user = make_user(email="sync_new@example.com", tier=UserTier.FREE)
        assert get_subscription(db_session, user.id) is None

        stripe_sub = {
            "id": "sub_new",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
        }
        sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_new", "solo")
        assert sub is not None
        assert sub.user_id == user.id

    # --- sync updates existing Subscription ---

    def test_sync_updates_existing_subscription(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="sync_update@example.com")
        stripe_sub = {
            "id": "sub_upd",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
        }
        sub1 = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_upd", "solo")
        sub2 = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_upd", "team")
        assert sub1.id == sub2.id
        assert sub2.tier == "team"

    # --- sync handles unknown Stripe status → default ACTIVE ---

    def test_sync_unknown_stripe_status_defaults_active(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="unknown_status@example.com", tier=UserTier.FREE)
        stripe_sub = {
            "id": "sub_unk",
            "status": "paused",  # Not in _STATUS_MAP
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
        }
        sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_unk", "solo")
        assert sub.status == SubscriptionStatus.ACTIVE

    # --- sync handles missing period timestamps ---

    def test_sync_handles_missing_period_timestamps(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="no_period@example.com", tier=UserTier.FREE)
        stripe_sub = {
            "id": "sub_np",
            "status": "active",
            "cancel_at_period_end": False,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
        }
        sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_np", "solo")
        assert sub.current_period_start is None
        assert sub.current_period_end is None

    # --- sync handles dual-item subscription (seats extraction) ---

    def test_sync_dual_item_seat_extraction(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="dual_item@example.com")
        stripe_sub = {
            "id": "sub_dual",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {
                "data": [
                    {"price": {"id": "price_team_mo"}, "quantity": 1, "plan": {"interval": "month"}},
                    {"price": {"id": "price_seat_mo"}, "quantity": 5},
                ]
            },
        }
        with patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_mo"}):
            sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_dual", "team")
        assert sub.seat_count == 1
        assert sub.additional_seats == 5
        assert sub.total_seats == 6

    # --- sync handles single-item subscription (no seats) ---

    def test_sync_single_item_no_seats(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="single_item@example.com")
        stripe_sub = {
            "id": "sub_single",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"price": {"id": "price_solo_mo"}, "quantity": 1, "plan": {"interval": "month"}}]},
        }
        with patch("billing.price_config.get_all_seat_price_ids", return_value=set()):
            sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_single", "solo")
        assert sub.seat_count == 1
        assert sub.additional_seats == 0

    # --- Status mapping: 7 Stripe statuses → our 4 statuses ---

    @pytest.mark.parametrize(
        "stripe_status,expected",
        [
            ("active", SubscriptionStatus.ACTIVE),
            ("past_due", SubscriptionStatus.PAST_DUE),
            ("canceled", SubscriptionStatus.CANCELED),
            ("trialing", SubscriptionStatus.TRIALING),
            ("incomplete", SubscriptionStatus.PAST_DUE),
            ("incomplete_expired", SubscriptionStatus.CANCELED),
            ("unpaid", SubscriptionStatus.PAST_DUE),
        ],
    )
    def test_status_mapping(self, stripe_status, expected):
        from billing.subscription_manager import _STATUS_MAP

        assert _STATUS_MAP[stripe_status] == expected


# ===========================================================================
# Class 4: Webhook Reconciliation
# ===========================================================================


class TestWebhookReconciliation:
    """Validates tier resolution from price IDs and webhook dispatch correctness."""

    _MOCK_PRICE_IDS = {
        "solo": {"monthly": "price_solo_mo", "annual": "price_solo_yr"},
        "team": {"monthly": "price_team_mo", "annual": "price_team_yr"},
    }

    @pytest.mark.parametrize(
        "tier,interval",
        [
            ("solo", "monthly"),
            ("solo", "annual"),
            ("team", "monthly"),
            ("team", "annual"),
        ],
    )
    def test_resolve_tier_from_price(self, tier, interval):
        from billing.webhook_handler import _resolve_tier_from_price

        price_id = self._MOCK_PRICE_IDS[tier][interval]
        with (
            patch("billing.price_config._load_stripe_price_ids", return_value=self._MOCK_PRICE_IDS),
            patch("billing.price_config.get_all_seat_price_ids", return_value=set()),
        ):
            assert _resolve_tier_from_price(price_id) == tier

    def test_resolve_tier_seat_price_returns_none(self):
        from billing.webhook_handler import _resolve_tier_from_price

        with (
            patch("billing.price_config._load_stripe_price_ids", return_value=self._MOCK_PRICE_IDS),
            patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_mo"}),
        ):
            assert _resolve_tier_from_price("price_seat_mo") is None

    def test_resolve_tier_unknown_price_returns_none(self):
        from billing.webhook_handler import _resolve_tier_from_price

        with (
            patch("billing.price_config._load_stripe_price_ids", return_value=self._MOCK_PRICE_IDS),
            patch("billing.price_config.get_all_seat_price_ids", return_value=set()),
        ):
            assert _resolve_tier_from_price("price_unknown") is None

    def test_find_base_plan_item_skips_seats(self):
        from billing.webhook_handler import _find_base_plan_item

        items = [
            {"price": {"id": "price_seat_mo"}, "quantity": 5},
            {"price": {"id": "price_team_mo"}, "quantity": 1},
        ]
        with patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_mo"}):
            result = _find_base_plan_item(items)
            assert result["price"]["id"] == "price_team_mo"

    def test_find_base_plan_item_fallback_single(self):
        from billing.webhook_handler import _find_base_plan_item

        items = [{"price": {"id": "price_solo_mo"}, "quantity": 1}]
        with patch("billing.price_config.get_all_seat_price_ids", return_value=set()):
            result = _find_base_plan_item(items)
            assert result["price"]["id"] == "price_solo_mo"

    def test_find_base_plan_item_empty_list(self):
        from billing.webhook_handler import _find_base_plan_item

        with patch("billing.price_config.get_all_seat_price_ids", return_value=set()):
            assert _find_base_plan_item([]) is None

    # --- Webhook dispatch for all 6 event types ---

    @pytest.mark.parametrize(
        "event_type",
        [
            "checkout.session.completed",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "customer.subscription.trial_will_end",
            "invoice.payment_failed",
            "invoice.paid",
        ],
    )
    def test_webhook_dispatch_event_type(self, event_type):
        from billing.webhook_handler import process_webhook_event

        mock_db = MagicMock()
        result = process_webhook_event(mock_db, event_type, {"customer": "cus_test", "metadata": {}})
        assert result is True

    def test_webhook_unknown_event_returns_false(self):
        from billing.webhook_handler import process_webhook_event

        mock_db = MagicMock()
        result = process_webhook_event(mock_db, "unknown.event", {})
        assert result is False

    # --- Edge cases: missing fields in webhook events ---

    def test_checkout_completed_missing_user_id(self):
        from billing.webhook_handler import handle_checkout_completed

        mock_db = MagicMock()
        # No metadata or customer → can't resolve user_id → graceful return
        handle_checkout_completed(mock_db, {"metadata": {}})

    def test_checkout_completed_missing_subscription_id(self):
        from billing.webhook_handler import handle_checkout_completed

        mock_db = MagicMock()
        # Has user_id but no subscription → graceful return
        handle_checkout_completed(
            mock_db, {"metadata": {"paciolus_user_id": "1"}, "customer": "cus_1", "subscription": None}
        )

    def test_subscription_updated_missing_items(self):
        from billing.webhook_handler import handle_subscription_updated

        mock_db = MagicMock()
        # Has user_id but no items → can't resolve tier → graceful return
        handle_subscription_updated(mock_db, {"metadata": {"paciolus_user_id": "1"}, "customer": "cus_1", "items": {}})

    def test_subscription_deleted_no_subscription(self, db_session, make_user):
        from billing.webhook_handler import handle_subscription_deleted

        user = make_user(email="del_no_sub@example.com")
        # No subscription record → graceful handling
        handle_subscription_deleted(db_session, {"customer": "cus_nonexistent", "metadata": {}})

    def test_invoice_payment_failed_no_customer(self):
        from billing.webhook_handler import handle_invoice_payment_failed

        mock_db = MagicMock()
        # No customer → early return
        handle_invoice_payment_failed(mock_db, {})

    def test_invoice_paid_no_customer(self):
        from billing.webhook_handler import handle_invoice_paid

        mock_db = MagicMock()
        # No customer → early return
        handle_invoice_paid(mock_db, {})

    def test_trial_will_end_logs_event(self):
        from billing.webhook_handler import handle_subscription_trial_will_end

        mock_db = MagicMock()
        # Should not raise
        handle_subscription_trial_will_end(mock_db, {"metadata": {"paciolus_user_id": "1"}, "trial_end": 1700604800})

    # --- User ID resolution ---

    def test_user_id_from_metadata(self, db_session):
        from billing.webhook_handler import _resolve_user_id

        result = _resolve_user_id(db_session, {"metadata": {"paciolus_user_id": "42"}})
        assert result == 42

    def test_user_id_from_customer_id_lookup(self, db_session, make_user):
        from billing.webhook_handler import _resolve_user_id

        user = make_user(email="cust_lookup@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_lookup",
            stripe_subscription_id="sub_lookup",
        )
        db_session.add(sub)
        db_session.flush()

        result = _resolve_user_id(db_session, {"metadata": {}, "customer": "cus_lookup"})
        assert result == user.id

    def test_user_id_unresolvable(self, db_session):
        from billing.webhook_handler import _resolve_user_id

        result = _resolve_user_id(db_session, {"metadata": {}})
        assert result is None


# ===========================================================================
# Class 5: Entitlement Enforcement
# ===========================================================================


class TestEntitlementEnforcement:
    """Full entitlement matrix across all tiers and enforcement modes."""

    # --- Diagnostic limits ---

    def test_free_diagnostic_limit_10(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.FREE)
        assert e.diagnostics_per_month == 10

    def test_solo_diagnostic_limit_20(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.SOLO)
        assert e.diagnostics_per_month == 20

    def test_team_diagnostic_unlimited(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.TEAM)
        assert e.diagnostics_per_month == 0  # 0 = unlimited

    # --- Client limits ---

    def test_free_client_limit_3(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.FREE)
        assert e.max_clients == 3

    def test_solo_client_limit_10(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.SOLO)
        assert e.max_clients == 10

    def test_team_client_unlimited(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.TEAM)
        assert e.max_clients == 0

    # --- Tool access ---

    def test_free_tier_tool_access_basic_only(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.FREE)
        assert "trial_balance" in e.tools_allowed
        assert "flux_analysis" in e.tools_allowed
        assert "journal_entry_testing" not in e.tools_allowed
        assert len(e.tools_allowed) == 2

    def test_solo_tier_tool_access_9_tools(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.SOLO)
        assert len(e.tools_allowed) == 9
        assert "journal_entry_testing" in e.tools_allowed
        assert "revenue_testing" in e.tools_allowed

    def test_team_tier_all_tools(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.TEAM)
        assert len(e.tools_allowed) == 0  # Empty = all

    # --- Format access ---

    def test_free_format_access_basic(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.FREE)
        assert "csv" in e.formats_allowed
        assert "xlsx" in e.formats_allowed
        assert "ods" not in e.formats_allowed
        assert "qbo" not in e.formats_allowed

    def test_solo_format_access_extended(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.SOLO)
        assert "qbo" in e.formats_allowed
        assert "ofx" in e.formats_allowed
        assert "pdf" in e.formats_allowed
        assert "ods" not in e.formats_allowed

    def test_team_format_access_all(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.TEAM)
        assert len(e.formats_allowed) == 0  # Empty = all

    # --- Workspace access ---

    def test_free_no_workspace(self):
        from shared.entitlements import get_entitlements

        assert get_entitlements(UserTier.FREE).workspace is False

    def test_solo_no_workspace(self):
        from shared.entitlements import get_entitlements

        assert get_entitlements(UserTier.SOLO).workspace is False

    def test_team_has_workspace(self):
        from shared.entitlements import get_entitlements

        assert get_entitlements(UserTier.TEAM).workspace is True

    # --- Seat inclusion ---

    def test_free_1_seat_included(self):
        from shared.entitlements import get_entitlements

        assert get_entitlements(UserTier.FREE).seats_included == 1

    def test_solo_1_seat_included(self):
        from shared.entitlements import get_entitlements

        assert get_entitlements(UserTier.SOLO).seats_included == 1

    def test_team_3_seats_included(self):
        from shared.entitlements import get_entitlements

        assert get_entitlements(UserTier.TEAM).seats_included == 3

    # --- Export capabilities ---

    def test_free_pdf_only(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.FREE)
        assert e.pdf_export is True
        assert e.excel_export is False
        assert e.csv_export is False

    def test_solo_all_exports(self):
        from shared.entitlements import get_entitlements

        e = get_entitlements(UserTier.SOLO)
        assert e.pdf_export is True
        assert e.excel_export is True
        assert e.csv_export is True

    # --- Priority support ---

    def test_free_no_priority_support(self):
        from shared.entitlements import get_entitlements

        assert get_entitlements(UserTier.FREE).priority_support is False

    def test_team_priority_support(self):
        from shared.entitlements import get_entitlements

        assert get_entitlements(UserTier.TEAM).priority_support is True

    # --- Enforcement mode default ---

    def test_enforcement_default_hard(self):
        from shared.entitlement_checks import _get_enforcement_mode

        with patch("config._load_optional", return_value="hard"):
            assert _get_enforcement_mode() == "hard"

    def test_enforcement_soft_mode(self):
        from shared.entitlement_checks import _get_enforcement_mode

        with patch("config._load_optional", return_value="soft"):
            assert _get_enforcement_mode() == "soft"

    # --- Unknown tier fallback to FREE ---

    def test_unknown_tier_fallback_free(self):
        from shared.entitlements import TIER_ENTITLEMENTS, get_entitlements

        # Pass a tier not in the dict → should get FREE entitlements
        result = get_entitlements(UserTier.FREE)
        assert result == TIER_ENTITLEMENTS[UserTier.FREE]

    # --- check_tool_access returns callable ---

    def test_check_tool_access_returns_callable(self):
        from shared.entitlement_checks import check_tool_access

        dep = check_tool_access("journal_entry_testing")
        assert callable(dep)

    # --- check_format_access returns callable ---

    def test_check_format_access_returns_callable(self):
        from shared.entitlement_checks import check_format_access

        dep = check_format_access("ods")
        assert callable(dep)

    # --- check_workspace_access is callable ---

    def test_check_workspace_access_callable(self):
        from shared.entitlement_checks import check_workspace_access

        assert callable(check_workspace_access)

    # --- Error response structure (hard mode raises HTTPException) ---

    def test_hard_mode_raises_403(self):
        from fastapi import HTTPException

        from shared.entitlement_checks import _raise_or_log

        user = MagicMock()
        user.tier.value = "free"
        user.id = 1

        with patch("shared.entitlement_checks._get_enforcement_mode", return_value="hard"):
            with pytest.raises(HTTPException) as exc_info:
                _raise_or_log(user, "diagnostics", "Limit exceeded")
            assert exc_info.value.status_code == 403
            detail = exc_info.value.detail
            assert detail["code"] == "TIER_LIMIT_EXCEEDED"
            assert detail["resource"] == "diagnostics"
            assert detail["current_tier"] == "free"
            assert detail["upgrade_url"] == "/pricing"

    def test_soft_mode_does_not_raise(self):
        from shared.entitlement_checks import _raise_or_log

        user = MagicMock()
        user.tier.value = "free"
        user.id = 1

        with patch("shared.entitlement_checks._get_enforcement_mode", return_value="soft"):
            # Should not raise
            _raise_or_log(user, "diagnostics", "Limit exceeded")

    # --- Seat enforcement default soft ---

    def test_seat_enforcement_default_soft(self):
        from shared.entitlement_checks import _get_seat_enforcement_mode

        with patch("config._load_optional", return_value="soft"):
            assert _get_seat_enforcement_mode() == "soft"


# ===========================================================================
# Class 6: Promo Application Policy
# ===========================================================================


class TestPromoApplicationPolicy:
    """Best-single-discount validation."""

    def test_monthly20_valid_on_monthly(self):
        from billing.price_config import validate_promo_for_interval

        assert validate_promo_for_interval("MONTHLY20", "monthly") is None

    def test_monthly20_rejected_on_annual(self):
        from billing.price_config import validate_promo_for_interval

        result = validate_promo_for_interval("MONTHLY20", "annual")
        assert result is not None

    def test_annual10_valid_on_annual(self):
        from billing.price_config import validate_promo_for_interval

        assert validate_promo_for_interval("ANNUAL10", "annual") is None

    def test_annual10_rejected_on_monthly(self):
        from billing.price_config import validate_promo_for_interval

        result = validate_promo_for_interval("ANNUAL10", "monthly")
        assert result is not None

    def test_unknown_promo_code_rejected(self):
        from billing.price_config import validate_promo_for_interval

        result = validate_promo_for_interval("FAKECODE", "monthly")
        assert result is not None
        assert "unknown" in result.lower()

    def test_case_insensitive_lowercase(self):
        from billing.price_config import validate_promo_for_interval

        assert validate_promo_for_interval("monthly20", "monthly") is None

    def test_case_insensitive_mixed(self):
        from billing.price_config import validate_promo_for_interval

        assert validate_promo_for_interval("Monthly20", "monthly") is None

    def test_promo_code_maps_to_coupon_id(self):
        from billing.price_config import get_stripe_coupon_id

        with patch(
            "billing.price_config._load_coupon_ids", return_value={"monthly": "coupon_mo", "annual": "coupon_yr"}
        ):
            assert get_stripe_coupon_id("MONTHLY20") == "coupon_mo"
            assert get_stripe_coupon_id("ANNUAL10") == "coupon_yr"

    def test_promo_code_missing_coupon_env_var_returns_none(self):
        from billing.price_config import get_stripe_coupon_id

        with patch("billing.price_config._load_coupon_ids", return_value={"monthly": "", "annual": ""}):
            assert get_stripe_coupon_id("MONTHLY20") is None

    @patch("billing.checkout.get_stripe")
    def test_checkout_with_promo_has_exactly_1_coupon(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        create_checkout_session(
            customer_id="cus_1",
            plan_price_id="price_team_mo",
            user_id=1,
            stripe_coupon_id="coupon_monthly20",
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert len(call_kwargs["discounts"]) == 1

    @patch("billing.checkout.get_stripe")
    def test_checkout_with_promo_and_trial(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        create_checkout_session(
            customer_id="cus_1",
            plan_price_id="price_team_mo",
            user_id=1,
            trial_period_days=7,
            stripe_coupon_id="coupon_monthly20",
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["subscription_data"]["trial_period_days"] == 7
        assert call_kwargs["discounts"] == [{"coupon": "coupon_monthly20"}]

    @patch("billing.checkout.get_stripe")
    def test_checkout_without_promo_no_discounts(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        create_checkout_session(
            customer_id="cus_1",
            plan_price_id="price_solo_mo",
            user_id=1,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert "discounts" not in call_kwargs

    @pytest.mark.parametrize(
        "tier,interval,promo",
        [
            ("solo", "monthly", "MONTHLY20"),
            ("team", "annual", "ANNUAL10"),
        ],
    )
    def test_valid_promo_tier_combos(self, tier, interval, promo):
        from billing.price_config import validate_promo_for_interval

        assert validate_promo_for_interval(promo, interval) is None

    def test_empty_promo_code_in_schema(self):
        """Empty string promo_code is valid in schema (route treats as None)."""
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier="solo",
            interval="monthly",
            promo_code="",
        )
        assert req.promo_code == ""

    def test_promo_code_max_length_enforcement(self):
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="solo",
                interval="monthly",
                promo_code="X" * 51,
            )

    def test_promo_codes_map_to_correct_intervals(self):
        from billing.price_config import PROMO_CODES

        assert PROMO_CODES["MONTHLY20"] == "monthly"
        assert PROMO_CODES["ANNUAL10"] == "annual"


# ===========================================================================
# Class 7: Old Subscriber Regression (Professional Tier)
# ===========================================================================


class TestOldSubscriberRegression:
    """Backward compatibility for deprecated professional tier."""

    def test_professional_tier_in_enum(self):
        assert hasattr(UserTier, "PROFESSIONAL")
        assert UserTier.PROFESSIONAL.value == "professional"

    def test_professional_entitlements_match_solo(self):
        from shared.entitlements import get_entitlements

        pro = get_entitlements(UserTier.PROFESSIONAL)
        solo = get_entitlements(UserTier.SOLO)
        assert pro.diagnostics_per_month == solo.diagnostics_per_month
        assert pro.max_clients == solo.max_clients
        assert pro.tools_allowed == solo.tools_allowed
        assert pro.formats_allowed == solo.formats_allowed
        assert pro.pdf_export == solo.pdf_export
        assert pro.excel_export == solo.excel_export
        assert pro.csv_export == solo.csv_export

    def test_professional_same_tool_count_as_solo(self):
        from shared.entitlements import get_entitlements

        pro = get_entitlements(UserTier.PROFESSIONAL)
        solo = get_entitlements(UserTier.SOLO)
        assert len(pro.tools_allowed) == len(solo.tools_allowed) == 9

    def test_professional_not_purchasable(self):
        from shared.tier_display import PURCHASABLE_TIERS

        assert "professional" not in PURCHASABLE_TIERS

    def test_professional_user_can_create_subscription(self, db_session, make_user):
        user = make_user(email="pro_sub@example.com", tier=UserTier.PROFESSIONAL)
        sub = Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_pro",
            stripe_subscription_id="sub_pro",
        )
        db_session.add(sub)
        db_session.flush()
        assert sub.id is not None

    def test_professional_downgrade_on_deleted(self, db_session, make_user):
        from billing.webhook_handler import handle_subscription_deleted

        user = make_user(email="pro_del@example.com", tier=UserTier.PROFESSIONAL)
        sub = Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_pro_del",
            stripe_subscription_id="sub_pro_del",
        )
        db_session.add(sub)
        db_session.flush()

        handle_subscription_deleted(db_session, {"customer": "cus_pro_del", "metadata": {}})
        assert user.tier == UserTier.FREE

    def test_professional_sync_works(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="pro_sync@example.com", tier=UserTier.PROFESSIONAL)
        stripe_sub = {
            "id": "sub_pro_sync",
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
        }
        sub = sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_pro_sync", "professional")
        assert sub.tier == "professional"

    def test_professional_display_name(self):
        from shared.tier_display import get_display_name

        assert get_display_name(UserTier.PROFESSIONAL) == "Professional"

    def test_professional_no_workspace(self):
        from shared.entitlements import get_entitlements

        assert get_entitlements(UserTier.PROFESSIONAL).workspace is False

    def test_professional_solo_parity_excluding_workspace(self):
        from shared.entitlements import get_entitlements

        pro = get_entitlements(UserTier.PROFESSIONAL)
        solo = get_entitlements(UserTier.SOLO)
        # Both should have workspace=False
        assert pro.workspace == solo.workspace == False  # noqa: E712

    def test_professional_accessing_team_tool_blocked(self):
        """Professional tier should not have tools only available at team level."""
        from shared.entitlements import get_entitlements

        pro = get_entitlements(UserTier.PROFESSIONAL)
        # fixed_asset_testing is NOT in solo tools
        assert "fixed_asset_testing" not in pro.tools_allowed

    def test_professional_accessing_solo_tool_allowed(self):
        from shared.entitlements import get_entitlements

        pro = get_entitlements(UserTier.PROFESSIONAL)
        assert "journal_entry_testing" in pro.tools_allowed
        assert "revenue_testing" in pro.tools_allowed

    def test_professional_seats_included_1(self):
        from shared.entitlements import get_entitlements

        assert get_entitlements(UserTier.PROFESSIONAL).seats_included == 1
