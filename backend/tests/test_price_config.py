"""
Price configuration tests — Phase LIX Sprint A.
Updated Sprint 452: Proposal C "Audit Maturity" restructure.

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
        paid_tiers = {"solo", "team", "organization"}
        for tier in paid_tiers:
            assert tier in PRICE_TABLE, f"Missing tier: {tier}"

    def test_professional_not_in_price_table(self):
        """Professional tier removed from pricing — no purchase path."""
        assert "professional" not in PRICE_TABLE

    def test_all_intervals_present(self):
        for tier, intervals in PRICE_TABLE.items():
            assert "monthly" in intervals, f"Missing monthly for {tier}"
            assert "annual" in intervals, f"Missing annual for {tier}"

    def test_no_variant_nesting(self):
        """Price table should be flat: tier → interval → cents (no A/B variant layer)."""
        for tier, intervals in PRICE_TABLE.items():
            for key, value in intervals.items():
                assert isinstance(value, int), (
                    f"Expected int for {tier}/{key}, got {type(value).__name__}. "
                    "Price table should be flat (no variant nesting)."
                )

    def test_paid_prices_are_positive(self):
        """Paid tiers (solo, team, organization) must have positive prices."""
        paid_tiers = {"solo", "team", "organization"}
        for tier in paid_tiers:
            for interval, cents in PRICE_TABLE[tier].items():
                assert cents > 0, f"Non-positive price for {tier}/{interval}"

    def test_free_prices_are_zero(self):
        for interval, cents in PRICE_TABLE["free"].items():
            assert cents == 0, f"Expected 0 for free/{interval}"

    def test_annual_cheaper_than_12x_monthly(self):
        """Annual price should be less than 12x monthly for paid tiers."""
        paid_tiers = {"solo", "team", "organization"}
        for tier in paid_tiers:
            monthly_12 = PRICE_TABLE[tier]["monthly"] * 12
            annual = PRICE_TABLE[tier]["annual"]
            assert annual < monthly_12, f"Annual ({annual}) not cheaper than 12x monthly ({monthly_12}) for {tier}"

    def test_exact_solo_prices(self):
        """Solo plan: $50/mo, $500/yr."""
        assert PRICE_TABLE["solo"]["monthly"] == 5000
        assert PRICE_TABLE["solo"]["annual"] == 50000

    def test_exact_team_prices(self):
        """Team plan: $150/mo, $1,500/yr."""
        assert PRICE_TABLE["team"]["monthly"] == 15000
        assert PRICE_TABLE["team"]["annual"] == 150000

    def test_enterprise_not_in_price_table(self):
        """Enterprise tier removed — not in price table."""
        assert "enterprise" not in PRICE_TABLE

    def test_exact_organization_prices(self):
        """Organization plan: $450/mo, $4,500/yr."""
        assert PRICE_TABLE["organization"]["monthly"] == 45000
        assert PRICE_TABLE["organization"]["annual"] == 450000


class TestGetPriceCents:
    """Test get_price_cents helper."""

    def test_solo_monthly(self):
        price = get_price_cents("solo", "monthly")
        assert price == 5000  # $50

    def test_solo_annual(self):
        price = get_price_cents("solo", "annual")
        assert price == 50000  # $500

    def test_team_monthly(self):
        price = get_price_cents("team", "monthly")
        assert price == 15000  # $150

    def test_team_annual(self):
        price = get_price_cents("team", "annual")
        assert price == 150000  # $1,500

    def test_organization_monthly(self):
        price = get_price_cents("organization", "monthly")
        assert price == 45000  # $450

    def test_organization_annual(self):
        price = get_price_cents("organization", "annual")
        assert price == 450000  # $4,500

    def test_enterprise_returns_zero(self):
        """Enterprise removed — should return 0."""
        price = get_price_cents("enterprise", "monthly")
        assert price == 0

    def test_unknown_tier_returns_zero(self):
        price = get_price_cents("unknown_tier", "monthly")
        assert price == 0

    def test_free_tier_returns_zero(self):
        price = get_price_cents("free", "monthly")
        assert price == 0

    def test_default_interval_is_monthly(self):
        price = get_price_cents("solo")
        assert price == 5000

    def test_professional_returns_zero(self):
        """Professional removed from price table — should return 0."""
        price = get_price_cents("professional", "monthly")
        assert price == 0


class TestAnnualSavings:
    """Test get_annual_savings_percent helper."""

    def test_solo_savings(self):
        savings = get_annual_savings_percent("solo")
        # $50*12=$600, annual=$500 → ~16.7%
        assert 16 <= savings <= 17

    def test_team_savings(self):
        savings = get_annual_savings_percent("team")
        # $150*12=$1800, annual=$1500 → ~16.7%
        assert 16 <= savings <= 17

    def test_organization_savings(self):
        savings = get_annual_savings_percent("organization")
        # $450*12=$5400, annual=$4500 → ~16.7%
        assert 16 <= savings <= 17

    def test_enterprise_savings_returns_zero(self):
        """Enterprise removed — should return 0."""
        savings = get_annual_savings_percent("enterprise")
        assert savings == 0

    def test_unknown_tier_returns_zero(self):
        savings = get_annual_savings_percent("unknown")
        assert savings == 0

    def test_free_returns_zero(self):
        savings = get_annual_savings_percent("free")
        assert savings == 0


class TestMaxSelfServeSeats:
    """Test get_max_self_serve_seats helper."""

    def test_team_max_seats(self):
        assert get_max_self_serve_seats("team") == 25

    def test_organization_max_seats(self):
        assert get_max_self_serve_seats("organization") == 75

    def test_solo_max_seats(self):
        assert get_max_self_serve_seats("solo") == 25

    def test_unknown_tier_defaults_to_team(self):
        assert get_max_self_serve_seats("unknown") == 25
