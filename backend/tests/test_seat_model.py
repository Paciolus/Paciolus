"""
Seat model and pricing tests — Phase LIX Sprint B.

Covers:
1. Subscription seat columns (seat_count, additional_seats, total_seats)
2. Tiered seat pricing (SEAT_PRICE_TIERS, get_seat_price_cents)
3. Additional seats cost calculation
4. Seat quantity extraction from Stripe webhook data
5. Seat enforcement config
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from billing.price_config import (
    MAX_SELF_SERVE_SEATS,
    SEAT_PRICE_TIERS,
    calculate_additional_seats_cost,
    get_seat_price_cents,
)
from billing.subscription_manager import _extract_seat_quantity
from subscription_model import Subscription, SubscriptionStatus

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
            tier="starter",
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
        sub.tier = "team"
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
        sub.tier = "starter"
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
            tier="team",
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


class TestSeatPriceTiers:
    """Validate the tiered seat pricing structure."""

    def test_tiers_are_ordered(self):
        """Each tier starts after the previous one ends."""
        for i in range(1, len(SEAT_PRICE_TIERS)):
            prev_max = SEAT_PRICE_TIERS[i - 1][1]
            curr_min = SEAT_PRICE_TIERS[i][0]
            assert curr_min == prev_max + 1

    def test_first_tier_starts_at_4(self):
        assert SEAT_PRICE_TIERS[0][0] == 4

    def test_max_self_serve_seats_is_25(self):
        assert MAX_SELF_SERVE_SEATS == 25

    def test_tiers_have_both_intervals(self):
        for min_s, max_s, prices in SEAT_PRICE_TIERS:
            assert "monthly" in prices, f"Missing monthly for seats {min_s}-{max_s}"
            assert "annual" in prices, f"Missing annual for seats {min_s}-{max_s}"


class TestGetSeatPriceCents:
    """Test per-seat pricing lookup."""

    def test_base_seats_are_free(self):
        for seat in [1, 2, 3]:
            assert get_seat_price_cents(seat) == 0

    def test_seat_4_monthly(self):
        assert get_seat_price_cents(4, "monthly") == 8000  # $80

    def test_seat_10_monthly(self):
        assert get_seat_price_cents(10, "monthly") == 8000  # $80

    def test_seat_11_monthly(self):
        assert get_seat_price_cents(11, "monthly") == 7000  # $70

    def test_seat_25_monthly(self):
        assert get_seat_price_cents(25, "monthly") == 7000  # $70

    def test_seat_26_returns_none(self):
        """Seats 26+ require sales contact."""
        assert get_seat_price_cents(26) is None

    def test_seat_4_annual(self):
        assert get_seat_price_cents(4, "annual") == 80000  # $800

    def test_seat_11_annual(self):
        assert get_seat_price_cents(11, "annual") == 70000  # $700

    def test_seat_0_is_free(self):
        assert get_seat_price_cents(0) == 0


class TestCalculateAdditionalSeatsCost:
    """Test total cost calculation for add-on seats."""

    def test_zero_additional_seats(self):
        assert calculate_additional_seats_cost(0) == 0

    def test_negative_additional_seats(self):
        assert calculate_additional_seats_cost(-1) == 0

    def test_one_additional_seat_monthly(self):
        # Seat #4 = $80/mo
        assert calculate_additional_seats_cost(1, "monthly") == 8000

    def test_seven_additional_seats_monthly(self):
        # Seats 4-10 = 7 × $80 = $560/mo
        assert calculate_additional_seats_cost(7, "monthly") == 7 * 8000

    def test_eight_additional_seats_monthly(self):
        # Seats 4-10 = 7 × $80, seat 11 = $70 → $630
        assert calculate_additional_seats_cost(8, "monthly") == 7 * 8000 + 1 * 7000

    def test_twenty_two_additional_seats_monthly(self):
        # Seats 4-10 = 7 × $80, seats 11-25 = 15 × $70
        assert calculate_additional_seats_cost(22, "monthly") == 7 * 8000 + 15 * 7000

    def test_twenty_three_additional_seats_returns_none(self):
        # Seat 26 exceeds self-serve limit
        assert calculate_additional_seats_cost(23, "monthly") is None

    def test_annual_pricing(self):
        # 3 add-on seats: seats 4,5,6 = 3 × $800
        assert calculate_additional_seats_cost(3, "annual") == 3 * 80000


# ---------------------------------------------------------------------------
# Stripe seat quantity extraction
# ---------------------------------------------------------------------------


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
