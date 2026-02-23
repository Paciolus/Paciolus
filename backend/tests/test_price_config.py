"""
Price configuration tests — Sprint 376.

Validates price table structure, discount math, and variant switching.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from billing.price_config import (
    PRICE_TABLE,
    PriceVariant,
    get_annual_savings_percent,
    get_price_cents,
)


class TestPriceTable:
    """Validate the PRICE_TABLE structure."""

    def test_all_paid_tiers_present(self):
        paid_tiers = {"starter", "professional", "team"}
        for tier in paid_tiers:
            assert tier in PRICE_TABLE, f"Missing tier: {tier}"

    def test_all_variants_present(self):
        for tier, variants in PRICE_TABLE.items():
            for variant in PriceVariant:
                assert variant.value in variants, f"Missing variant {variant.value} for tier {tier}"

    def test_all_intervals_present(self):
        for tier, variants in PRICE_TABLE.items():
            for variant_name, intervals in variants.items():
                assert "monthly" in intervals, f"Missing monthly for {tier}/{variant_name}"
                assert "annual" in intervals, f"Missing annual for {tier}/{variant_name}"

    def test_paid_prices_are_positive(self):
        """Paid tiers (starter, professional, team) must have positive prices."""
        paid_tiers = {"starter", "professional", "team"}
        for tier in paid_tiers:
            for variant_name, intervals in PRICE_TABLE[tier].items():
                for interval, cents in intervals.items():
                    assert cents > 0, f"Non-positive price for {tier}/{variant_name}/{interval}"

    def test_free_and_enterprise_prices_are_zero(self):
        for tier in ("free", "enterprise"):
            for variant_name, intervals in PRICE_TABLE[tier].items():
                for interval, cents in intervals.items():
                    assert cents == 0, f"Expected 0 for {tier}/{variant_name}/{interval}"

    def test_annual_cheaper_than_12x_monthly(self):
        """Annual price should be less than 12x monthly for paid tiers."""
        paid_tiers = {"starter", "professional", "team"}
        for tier in paid_tiers:
            for variant_name, intervals in PRICE_TABLE[tier].items():
                monthly_12 = intervals["monthly"] * 12
                annual = intervals["annual"]
                assert annual < monthly_12, (
                    f"Annual ({annual}) not cheaper than 12x monthly ({monthly_12}) "
                    f"for {tier}/{variant_name}"
                )


class TestGetPriceCents:
    """Test get_price_cents helper."""

    def test_control_starter_monthly(self):
        price = get_price_cents("starter", "control", "monthly")
        assert price == 4900  # $49

    def test_control_professional_annual(self):
        price = get_price_cents("professional", "control", "annual")
        assert price == 130900  # $1,309

    def test_experiment_starter_monthly(self):
        price = get_price_cents("starter", "experiment", "monthly")
        assert price == 5900  # $59

    def test_unknown_tier_returns_zero(self):
        price = get_price_cents("unknown_tier", "control", "monthly")
        assert price == 0

    def test_free_tier_returns_zero(self):
        price = get_price_cents("free", "control", "monthly")
        assert price == 0


class TestAnnualSavings:
    """Test get_annual_savings_percent helper."""

    def test_starter_control_savings(self):
        savings = get_annual_savings_percent("starter", "control")
        # $49*12=$588, annual=$499 → ~15.1%
        assert 15 <= savings <= 16

    def test_professional_control_savings(self):
        savings = get_annual_savings_percent("professional", "control")
        # $129*12=$1548, annual=$1309 → ~15.4%
        assert 15 <= savings <= 16

    def test_team_control_savings(self):
        savings = get_annual_savings_percent("team", "control")
        assert 15 <= savings <= 17

    def test_unknown_tier_returns_zero(self):
        savings = get_annual_savings_percent("unknown", "control")
        assert savings == 0


class TestPriceVariant:
    """Test PriceVariant enum."""

    def test_control_value(self):
        assert PriceVariant.CONTROL.value == "control"

    def test_experiment_value(self):
        assert PriceVariant.EXPERIMENT.value == "experiment"

    def test_has_exactly_two_variants(self):
        assert len(PriceVariant) == 2
