"""
Price configuration tests — Phase LIX Sprint A.
Updated Pricing v3: 4-tier system (Free/Solo/Professional/Enterprise).

Validates price table structure, discount math, and tier pricing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from billing.price_config import (
    PRICE_TABLE,
    get_annual_savings_percent,
    get_max_self_serve_seats,
    get_price_cents,
)


class TestPriceTable:
    """Validate the PRICE_TABLE structure."""

    def test_all_paid_tiers_present(self):
        paid_tiers = {"solo", "professional", "enterprise"}
        for tier in paid_tiers:
            assert tier in PRICE_TABLE, f"Missing tier: {tier}"

    def test_team_not_in_price_table(self):
        """Team tier removed from pricing — no purchase path."""
        assert "team" not in PRICE_TABLE

    def test_organization_not_in_price_table(self):
        """Organization tier removed from pricing — no purchase path."""
        assert "organization" not in PRICE_TABLE

    def test_all_intervals_present(self):
        for tier, intervals in PRICE_TABLE.items():
            assert "monthly" in intervals, f"Missing monthly for {tier}"
            assert "annual" in intervals, f"Missing annual for {tier}"

    def test_no_variant_nesting(self):
        """Price table should be flat: tier -> interval -> cents (no A/B variant layer)."""
        for tier, intervals in PRICE_TABLE.items():
            for key, value in intervals.items():
                assert isinstance(value, int), (
                    f"Expected int for {tier}/{key}, got {type(value).__name__}. "
                    "Price table should be flat (no variant nesting)."
                )

    def test_paid_prices_are_positive(self):
        """Paid tiers (solo, professional, enterprise) must have positive prices."""
        paid_tiers = {"solo", "professional", "enterprise"}
        for tier in paid_tiers:
            for interval, cents in PRICE_TABLE[tier].items():
                assert cents > 0, f"Non-positive price for {tier}/{interval}"

    def test_free_prices_are_zero(self):
        for interval, cents in PRICE_TABLE["free"].items():
            assert cents == 0, f"Expected 0 for free/{interval}"

    def test_annual_cheaper_than_12x_monthly(self):
        """Annual price should be less than 12x monthly for paid tiers."""
        paid_tiers = {"solo", "professional", "enterprise"}
        for tier in paid_tiers:
            monthly_12 = PRICE_TABLE[tier]["monthly"] * 12
            annual = PRICE_TABLE[tier]["annual"]
            assert annual < monthly_12, f"Annual ({annual}) not cheaper than 12x monthly ({monthly_12}) for {tier}"

    def test_exact_solo_prices(self):
        """Solo plan: $100/mo, $1,000/yr."""
        assert PRICE_TABLE["solo"]["monthly"] == 10000
        assert PRICE_TABLE["solo"]["annual"] == 100000

    def test_exact_professional_prices(self):
        """Professional plan: $500/mo, $5,000/yr."""
        assert PRICE_TABLE["professional"]["monthly"] == 50000
        assert PRICE_TABLE["professional"]["annual"] == 500000

    def test_exact_enterprise_prices(self):
        """Enterprise plan: $1,000/mo, $10,000/yr."""
        assert PRICE_TABLE["enterprise"]["monthly"] == 100000
        assert PRICE_TABLE["enterprise"]["annual"] == 1000000


class TestGetPriceCents:
    """Test get_price_cents helper."""

    def test_solo_monthly(self):
        price = get_price_cents("solo", "monthly")
        assert price == 10000  # $100

    def test_solo_annual(self):
        price = get_price_cents("solo", "annual")
        assert price == 100000  # $1,000

    def test_professional_monthly(self):
        price = get_price_cents("professional", "monthly")
        assert price == 50000  # $500

    def test_professional_annual(self):
        price = get_price_cents("professional", "annual")
        assert price == 500000  # $5,000

    def test_enterprise_monthly(self):
        price = get_price_cents("enterprise", "monthly")
        assert price == 100000  # $1,000

    def test_enterprise_annual(self):
        price = get_price_cents("enterprise", "annual")
        assert price == 1000000  # $10,000

    def test_team_returns_zero(self):
        """Team removed — should return 0."""
        price = get_price_cents("team", "monthly")
        assert price == 0

    def test_organization_returns_zero(self):
        """Organization removed — should return 0."""
        price = get_price_cents("organization", "monthly")
        assert price == 0

    def test_unknown_tier_returns_zero(self):
        price = get_price_cents("unknown_tier", "monthly")
        assert price == 0

    def test_free_tier_returns_zero(self):
        price = get_price_cents("free", "monthly")
        assert price == 0

    def test_default_interval_is_monthly(self):
        price = get_price_cents("solo")
        assert price == 10000


class TestAnnualSavings:
    """Test get_annual_savings_percent helper."""

    def test_solo_savings(self):
        savings = get_annual_savings_percent("solo")
        # $100*12=$1200, annual=$1000 -> ~16.7%
        assert 16 <= savings <= 17

    def test_professional_savings(self):
        savings = get_annual_savings_percent("professional")
        # $500*12=$6000, annual=$5000 -> ~16.7%
        assert 16 <= savings <= 17

    def test_enterprise_savings(self):
        savings = get_annual_savings_percent("enterprise")
        # $1000*12=$12000, annual=$10000 -> ~16.7%
        assert 16 <= savings <= 17

    def test_team_savings_returns_zero(self):
        """Team removed — should return 0."""
        savings = get_annual_savings_percent("team")
        assert savings == 0

    def test_unknown_tier_returns_zero(self):
        savings = get_annual_savings_percent("unknown")
        assert savings == 0

    def test_free_returns_zero(self):
        savings = get_annual_savings_percent("free")
        assert savings == 0


class TestMaxSelfServeSeats:
    """Test get_max_self_serve_seats helper."""

    def test_professional_max_seats(self):
        assert get_max_self_serve_seats("professional") == 20

    def test_enterprise_max_seats(self):
        assert get_max_self_serve_seats("enterprise") == 100

    def test_solo_max_seats(self):
        assert get_max_self_serve_seats("solo") == 1

    def test_unknown_tier_defaults_to_1(self):
        assert get_max_self_serve_seats("unknown") == 1
