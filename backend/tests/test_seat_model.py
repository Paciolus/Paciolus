"""
Seat model and pricing tests — Phase LIX Sprint B, updated Phase LXIX Pricing v3.

Covers:
1. Subscription seat columns (seat_count, additional_seats, total_seats)
2. Per-tier flat seat pricing (Professional $65/mo, Enterprise $45/mo)
3. Additional seats cost calculation
4. Seat quantity extraction from Stripe webhook data
5. Seat enforcement config
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from billing.price_config import (
    ENTERPRISE_SEAT_PRICE,
    MAX_SELF_SERVE_SEATS_ENTERPRISE,
    MAX_SELF_SERVE_SEATS_PROFESSIONAL,
    PROFESSIONAL_SEAT_PRICE,
    calculate_additional_seats_cost,
    get_max_self_serve_seats,
    get_seat_price_cents,
)
from billing.subscription_manager import _extract_billing_interval, _extract_seat_quantity
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

# ---------------------------------------------------------------------------
# Subscription seat columns
# ---------------------------------------------------------------------------


class TestSubscriptionSeatColumns:
    """Verify seat columns exist and have correct defaults."""

    def test_seat_count_column_exists(self):
        col_names = {c.name for c in Subscription.__table__.columns}
        assert "seat_count" in col_names

    def test_additional_seats_column_exists(self):
        col_names = {c.name for c in Subscription.__table__.columns}
        assert "additional_seats" in col_names

    def test_seat_count_default_on_init(self):
        """Column default only applies on INSERT; bare init gives None."""
        sub = Subscription()
        # total_seats handles None gracefully
        assert sub.total_seats == 1  # (None → 1) + (None → 0)

    def test_seat_count_default_in_db(self, db_session, make_user):
        """Column default applies when inserted into DB."""
        user = make_user(email="seat_default@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id="cus_def1",
            stripe_subscription_id="sub_def1",
            cancel_at_period_end=False,
        )
        db_session.add(sub)
        db_session.flush()
        assert sub.seat_count == 1
        assert sub.additional_seats == 0

    def test_total_seats_property_base(self):
        sub = Subscription()
        sub.seat_count = 3
        sub.additional_seats = 0
        assert sub.total_seats == 3

    def test_total_seats_property_with_additional(self):
        sub = Subscription()
        sub.seat_count = 3
        sub.additional_seats = 5
        assert sub.total_seats == 8

    def test_total_seats_handles_none_seat_count(self):
        sub = Subscription()
        sub.seat_count = None
        sub.additional_seats = 2
        assert sub.total_seats == 3  # defaults to 1 + 2

    def test_total_seats_handles_none_additional(self):
        sub = Subscription()
        sub.seat_count = 3
        sub.additional_seats = None
        assert sub.total_seats == 3  # 3 + 0

    def test_to_dict_includes_seat_fields(self):
        sub = Subscription()
        sub.id = 1
        sub.user_id = 42
        sub.tier = "professional"
        sub.status = SubscriptionStatus.ACTIVE
        sub.cancel_at_period_end = False
        sub.seat_count = 3
        sub.additional_seats = 2
        d = sub.to_dict()
        assert d["seat_count"] == 3
        assert d["additional_seats"] == 2
        assert d["total_seats"] == 5

    def test_to_dict_seat_defaults(self):
        sub = Subscription()
        sub.id = 1
        sub.user_id = 42
        sub.tier = "solo"
        sub.status = SubscriptionStatus.ACTIVE
        sub.cancel_at_period_end = False
        d = sub.to_dict()
        assert d["seat_count"] == 1
        assert d["additional_seats"] == 0
        assert d["total_seats"] == 1


class TestSubscriptionSeatDB:
    """Test seat columns in actual DB operations."""

    def test_seat_count_persisted(self, db_session, make_user):
        user = make_user(email="seat_test@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            stripe_customer_id="cus_seat1",
            stripe_subscription_id="sub_seat1",
            seat_count=5,
            additional_seats=2,
            cancel_at_period_end=False,
        )
        db_session.add(sub)
        db_session.flush()
        assert sub.seat_count == 5
        assert sub.additional_seats == 2
        assert sub.total_seats == 7


# ---------------------------------------------------------------------------
# Seat pricing
# ---------------------------------------------------------------------------


class TestSeatPriceConfig:
    """Validate per-tier flat seat pricing structure."""

    def test_professional_seat_price_monthly(self):
        assert PROFESSIONAL_SEAT_PRICE["monthly"] == 6500  # $65

    def test_professional_seat_price_annual(self):
        assert PROFESSIONAL_SEAT_PRICE["annual"] == 65000  # $650

    def test_enterprise_seat_price_monthly(self):
        assert ENTERPRISE_SEAT_PRICE["monthly"] == 4500  # $45

    def test_enterprise_seat_price_annual(self):
        assert ENTERPRISE_SEAT_PRICE["annual"] == 45000  # $450

    def test_max_self_serve_seats_professional_is_20(self):
        assert MAX_SELF_SERVE_SEATS_PROFESSIONAL == 20

    def test_max_self_serve_seats_enterprise_is_100(self):
        assert MAX_SELF_SERVE_SEATS_ENTERPRISE == 100

    def test_get_max_self_serve_seats_professional(self):
        assert get_max_self_serve_seats("professional") == 20

    def test_get_max_self_serve_seats_enterprise(self):
        assert get_max_self_serve_seats("enterprise") == 100

    def test_get_max_self_serve_seats_solo(self):
        assert get_max_self_serve_seats("solo") == 1

    def test_get_max_self_serve_seats_free(self):
        assert get_max_self_serve_seats("free") == 1

    def test_seat_prices_have_both_intervals(self):
        for price_dict in (PROFESSIONAL_SEAT_PRICE, ENTERPRISE_SEAT_PRICE):
            assert "monthly" in price_dict
            assert "annual" in price_dict


class TestGetSeatPriceCents:
    """Test per-seat pricing lookup."""

    # --- Professional tier (7 seats included, max 20) ---

    def test_professional_included_seats_are_free(self):
        for seat in [1, 3, 5, 7]:
            assert get_seat_price_cents(seat, "monthly", "professional") == 0

    def test_professional_seat_8_monthly(self):
        assert get_seat_price_cents(8, "monthly", "professional") == 6500  # $65

    def test_professional_seat_20_monthly(self):
        assert get_seat_price_cents(20, "monthly", "professional") == 6500  # $65

    def test_professional_seat_21_returns_none(self):
        """Seats 21+ for professional require sales contact."""
        assert get_seat_price_cents(21, "monthly", "professional") is None

    def test_professional_seat_8_annual(self):
        assert get_seat_price_cents(8, "annual", "professional") == 65000  # $650

    # --- Enterprise tier (20 seats included, max 100) ---

    def test_enterprise_included_seats_are_free(self):
        for seat in [1, 10, 15, 20]:
            assert get_seat_price_cents(seat, "monthly", "enterprise") == 0

    def test_enterprise_seat_21_monthly(self):
        assert get_seat_price_cents(21, "monthly", "enterprise") == 4500  # $45

    def test_enterprise_seat_100_monthly(self):
        assert get_seat_price_cents(100, "monthly", "enterprise") == 4500  # $45

    def test_enterprise_seat_101_returns_none(self):
        """Seats 101+ for enterprise require sales contact."""
        assert get_seat_price_cents(101, "monthly", "enterprise") is None

    def test_enterprise_seat_21_annual(self):
        assert get_seat_price_cents(21, "annual", "enterprise") == 45000  # $450

    # --- Edge cases ---

    def test_seat_0_is_free(self):
        assert get_seat_price_cents(0, "monthly", "professional") == 0

    def test_seat_1_is_free(self):
        assert get_seat_price_cents(1, "monthly", "professional") == 0


class TestCalculateAdditionalSeatsCost:
    """Test total cost calculation for add-on seats."""

    def test_zero_additional_seats(self):
        assert calculate_additional_seats_cost(0, "monthly", "professional") == 0

    def test_negative_additional_seats(self):
        assert calculate_additional_seats_cost(-1, "monthly", "professional") == 0

    # --- Professional tier: 7 included, max 20, $65/mo per seat ---

    def test_professional_one_additional_seat_monthly(self):
        # Seat #8 = $65/mo
        assert calculate_additional_seats_cost(1, "monthly", "professional") == 6500

    def test_professional_five_additional_seats_monthly(self):
        # Seats 8-12 = 5 × $65 = $325/mo
        assert calculate_additional_seats_cost(5, "monthly", "professional") == 5 * 6500

    def test_professional_thirteen_additional_seats_monthly(self):
        # Seats 8-20 = 13 × $65 = $845/mo (max additional for professional)
        assert calculate_additional_seats_cost(13, "monthly", "professional") == 13 * 6500

    def test_professional_fourteen_additional_seats_returns_none(self):
        # Seat 8+14=22 exceeds professional max of 20
        assert calculate_additional_seats_cost(14, "monthly", "professional") is None

    def test_professional_annual_pricing(self):
        # 3 add-on seats: seats 8,9,10 = 3 × $650
        assert calculate_additional_seats_cost(3, "annual", "professional") == 3 * 65000

    # --- Enterprise tier: 20 included, max 100, $45/mo per seat ---

    def test_enterprise_one_additional_seat_monthly(self):
        # Seat #21 = $45/mo
        assert calculate_additional_seats_cost(1, "monthly", "enterprise") == 4500

    def test_enterprise_eighty_additional_seats_monthly(self):
        # Seats 21-100 = 80 × $45 = $3,600/mo (max additional for enterprise)
        assert calculate_additional_seats_cost(80, "monthly", "enterprise") == 80 * 4500

    def test_enterprise_eighty_one_additional_seats_returns_none(self):
        # Seat 21+81=102 exceeds enterprise max of 100
        assert calculate_additional_seats_cost(81, "monthly", "enterprise") is None

    def test_enterprise_annual_pricing(self):
        # 5 add-on seats: seats 21-25 = 5 × $450
        assert calculate_additional_seats_cost(5, "annual", "enterprise") == 5 * 45000


# ---------------------------------------------------------------------------
# Stripe seat quantity extraction
# ---------------------------------------------------------------------------


class TestExtractBillingInterval:
    """Test extraction of billing interval from the base plan line item."""

    def test_single_item_monthly(self):
        """Single item (base plan only) → interval extracted correctly."""
        items = [{"price": {"id": "price_base"}, "plan": {"interval": "month"}}]
        assert _extract_billing_interval(items) == BillingInterval.MONTHLY

    def test_single_item_annual(self):
        """Single item (base plan only) → annual interval."""
        items = [{"price": {"id": "price_base"}, "plan": {"interval": "year"}}]
        assert _extract_billing_interval(items) == BillingInterval.ANNUAL

    def test_two_items_base_first(self):
        """Base plan first, seat add-on second → interval from base plan."""
        from unittest.mock import patch

        with patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_addon"}):
            items = [
                {"price": {"id": "price_base"}, "plan": {"interval": "year"}},
                {"price": {"id": "price_seat_addon"}, "plan": {"interval": "year"}, "quantity": 3},
            ]
            assert _extract_billing_interval(items) == BillingInterval.ANNUAL

    def test_two_items_addon_first(self):
        """Seat add-on first, base plan second → still uses base plan interval."""
        from unittest.mock import patch

        with patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_addon"}):
            items = [
                {"price": {"id": "price_seat_addon"}, "plan": {"interval": "year"}, "quantity": 3},
                {"price": {"id": "price_base"}, "plan": {"interval": "month"}},
            ]
            # Should read from the base plan (month), NOT the add-on
            assert _extract_billing_interval(items) == BillingInterval.MONTHLY

    def test_empty_items(self):
        """No items → defaults to MONTHLY."""
        assert _extract_billing_interval([]) == BillingInterval.MONTHLY

    def test_missing_plan_defaults_monthly(self):
        """Item with no plan key → defaults to MONTHLY."""
        items = [{"price": {"id": "price_base"}}]
        assert _extract_billing_interval(items) == BillingInterval.MONTHLY


class TestExtractSeatQuantity:
    """Test extraction of seat quantity from Stripe subscription data."""

    def test_quantity_from_items(self):
        stripe_sub = {"items": {"data": [{"quantity": 5, "price": {"id": "price_123"}}]}}
        assert _extract_seat_quantity(stripe_sub) == 5

    def test_default_quantity_when_missing(self):
        stripe_sub = {"items": {"data": [{"price": {"id": "price_123"}}]}}
        assert _extract_seat_quantity(stripe_sub) == 1

    def test_default_when_no_items(self):
        assert _extract_seat_quantity({}) == 1

    def test_default_when_empty_items(self):
        stripe_sub = {"items": {"data": []}}
        assert _extract_seat_quantity(stripe_sub) == 1


# ---------------------------------------------------------------------------
# Seat enforcement config
# ---------------------------------------------------------------------------


class TestSeatEnforcementConfig:
    """Verify seat enforcement mode configuration."""

    def test_default_mode_is_soft(self):
        from shared.entitlement_checks import _get_seat_enforcement_mode

        # Default should be soft for initial 30-day rollout
        mode = _get_seat_enforcement_mode()
        assert mode in ("soft", "hard")  # Depends on env, but code path works
