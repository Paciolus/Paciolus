"""Tests for depreciation_engine (Sprint 626)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from depreciation_engine import (
    AssetConfig,
    BookMethod,
    DepreciationInputError,
    MacrsConvention,
    MacrsSystem,
    generate_depreciation_schedule,
)

# =============================================================================
# Straight-line
# =============================================================================


class TestStraightLine:
    def test_basic_straight_line(self):
        """$10,000 cost, $0 salvage, 5-yr life = $2,000/yr."""
        config = AssetConfig(
            asset_name="Test Asset",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=5,
        )
        result = generate_depreciation_schedule(config)
        assert len(result.book_schedule) == 5
        for entry in result.book_schedule:
            assert entry.depreciation == Decimal("2000.00")
        assert result.book_schedule[-1].ending_book_value == Decimal("0.00")
        assert result.total_book_depreciation == Decimal("10000.00")

    def test_straight_line_with_salvage(self):
        """$10,000 cost, $1,000 salvage, 9-yr life = $1,000/yr."""
        config = AssetConfig(
            asset_name="Test",
            cost=Decimal("10000"),
            salvage_value=Decimal("1000"),
            useful_life_years=9,
        )
        result = generate_depreciation_schedule(config)
        assert all(e.depreciation == Decimal("1000.00") for e in result.book_schedule)
        assert result.book_schedule[-1].ending_book_value == Decimal("1000.00")


# =============================================================================
# Declining balance
# =============================================================================


class TestDecliningBalance:
    def test_double_declining_balance(self):
        """DDB on $10,000 5-yr asset switches to SL and ends at salvage."""
        config = AssetConfig(
            asset_name="Test",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=5,
            book_method=BookMethod.DECLINING_BALANCE,
            db_factor=Decimal("2"),
        )
        result = generate_depreciation_schedule(config)
        # Year 1 = 10000 * 2/5 = 4000
        assert result.book_schedule[0].depreciation == Decimal("4000.00")
        # Year 2 = 6000 * 2/5 = 2400
        assert result.book_schedule[1].depreciation == Decimal("2400.00")
        # Total depreciation = cost - salvage
        assert result.book_schedule[-1].ending_book_value == Decimal("0.00")

    def test_db_does_not_depreciate_below_salvage(self):
        config = AssetConfig(
            asset_name="Test",
            cost=Decimal("10000"),
            salvage_value=Decimal("2000"),
            useful_life_years=5,
            book_method=BookMethod.DECLINING_BALANCE,
            db_factor=Decimal("2"),
        )
        result = generate_depreciation_schedule(config)
        assert result.book_schedule[-1].ending_book_value == Decimal("2000.00")

    def test_150_percent_db(self):
        config = AssetConfig(
            asset_name="Test",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=10,
            book_method=BookMethod.DECLINING_BALANCE,
            db_factor=Decimal("1.5"),
        )
        result = generate_depreciation_schedule(config)
        # Year 1 = 10000 * 1.5/10 = 1500
        assert result.book_schedule[0].depreciation == Decimal("1500.00")
        assert result.book_schedule[-1].ending_book_value == Decimal("0.00")


# =============================================================================
# Sum of Years' Digits
# =============================================================================


class TestSumOfYearsDigits:
    def test_syd_basic(self):
        """SYD on $9,000 / 0 salvage / 3-yr life: sum-of-years = 6.
        Year 1 = 9000*3/6=4500, Year 2 = 9000*2/6=3000, Year 3 = 9000*1/6=1500."""
        config = AssetConfig(
            asset_name="Test",
            cost=Decimal("9000"),
            salvage_value=Decimal("0"),
            useful_life_years=3,
            book_method=BookMethod.SUM_OF_YEARS_DIGITS,
        )
        result = generate_depreciation_schedule(config)
        assert result.book_schedule[0].depreciation == Decimal("4500.00")
        assert result.book_schedule[1].depreciation == Decimal("3000.00")
        assert result.book_schedule[2].depreciation == Decimal("1500.00")
        assert result.total_book_depreciation == Decimal("9000.00")


# =============================================================================
# Units of Production
# =============================================================================


class TestUnitsOfProduction:
    def test_uop_proportional(self):
        """Asset $10,000, 100,000 units, year usage (40k, 30k, 30k)."""
        config = AssetConfig(
            asset_name="Equipment",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=3,
            book_method=BookMethod.UNITS_OF_PRODUCTION,
            units_total=Decimal("100000"),
            units_per_year=[Decimal("40000"), Decimal("30000"), Decimal("30000")],
        )
        result = generate_depreciation_schedule(config)
        # rate = 10000/100000 = 0.1 per unit
        assert result.book_schedule[0].depreciation == Decimal("4000.00")
        assert result.book_schedule[1].depreciation == Decimal("3000.00")
        assert result.book_schedule[-1].ending_book_value == Decimal("0.00")


# =============================================================================
# MACRS GDS Half-Year (200% DB)
# =============================================================================


class TestMacrsHalfYear:
    def test_macrs_5yr_half_year_200db(self):
        """$10,000 5-year property under MACRS HY 200% DB.
        Standard table: 20.00, 32.00, 19.20, 11.52, 11.52, 5.76 (sums to 100)."""
        config = AssetConfig(
            asset_name="Computer",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=5,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
            macrs_convention=MacrsConvention.HALF_YEAR,
        )
        result = generate_depreciation_schedule(config)
        assert len(result.tax_schedule) == 6
        assert result.tax_schedule[0].depreciation == Decimal("2000.00")
        assert result.tax_schedule[1].depreciation == Decimal("3200.00")
        # Final year depreciates remaining basis to zero
        assert result.tax_schedule[-1].ending_book_value == Decimal("0.00")
        # Total tax depreciation = full cost (MACRS ignores salvage)
        assert result.total_tax_depreciation == Decimal("10000.00")

    def test_macrs_7yr_half_year(self):
        config = AssetConfig(
            asset_name="Furniture",
            cost=Decimal("100000"),
            useful_life_years=7,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=7,
            macrs_convention=MacrsConvention.HALF_YEAR,
        )
        result = generate_depreciation_schedule(config)
        # Year 1 = 14.29% of 100k = 14290
        assert result.tax_schedule[0].depreciation == Decimal("14290.00")
        assert len(result.tax_schedule) == 8
        assert result.tax_schedule[-1].ending_book_value == Decimal("0.00")

    def test_macrs_15yr_150db(self):
        """15-year property uses 150% DB tables."""
        config = AssetConfig(
            asset_name="Land Improvements",
            cost=Decimal("100000"),
            useful_life_years=15,
            macrs_system=MacrsSystem.GDS_150,
            macrs_property_class=15,
            macrs_convention=MacrsConvention.HALF_YEAR,
        )
        result = generate_depreciation_schedule(config)
        assert result.tax_schedule[0].depreciation == Decimal("5000.00")  # 5%
        assert result.tax_schedule[-1].ending_book_value == Decimal("0.00")


# =============================================================================
# MACRS Mid-Quarter
# =============================================================================


class TestMacrsMidQuarter:
    def test_mq_q1_5yr(self):
        """5-year asset placed Q1 under mid-quarter convention."""
        config = AssetConfig(
            asset_name="Equipment",
            cost=Decimal("10000"),
            useful_life_years=5,
            placed_in_service_quarter=1,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
            macrs_convention=MacrsConvention.MID_QUARTER,
        )
        result = generate_depreciation_schedule(config)
        # Year 1 Q1 = 35% per IRS Pub 946 Table A-2
        assert result.tax_schedule[0].depreciation == Decimal("3500.00")
        assert result.tax_schedule[-1].ending_book_value == Decimal("0.00")

    def test_mq_q4_5yr(self):
        config = AssetConfig(
            asset_name="Equipment",
            cost=Decimal("10000"),
            useful_life_years=5,
            placed_in_service_quarter=4,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
            macrs_convention=MacrsConvention.MID_QUARTER,
        )
        result = generate_depreciation_schedule(config)
        # Year 1 Q4 = 5% (asset placed late in year gets less Year 1)
        assert result.tax_schedule[0].depreciation == Decimal("500.00")


# =============================================================================
# Book vs Tax comparison
# =============================================================================


class TestBookTaxComparison:
    def test_timing_difference_reverses_to_zero(self):
        """Total timing differences over the asset's life net to zero."""
        config = AssetConfig(
            asset_name="Mixed",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=5,
            book_method=BookMethod.STRAIGHT_LINE,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
            macrs_convention=MacrsConvention.HALF_YEAR,
            tax_rate=Decimal("0.21"),
        )
        result = generate_depreciation_schedule(config)
        assert len(result.book_tax_comparison) >= 5
        timing_total = sum(c.timing_difference for c in result.book_tax_comparison)
        # Both schedules ultimately depreciate the full $10,000
        assert abs(timing_total) <= Decimal("0.01")
        # Cumulative deferred tax should net to zero (or near-zero) at maturity
        final = result.book_tax_comparison[-1]
        assert abs(final.cumulative_deferred_tax) <= Decimal("0.01")

    def test_tax_dep_higher_in_early_years(self):
        """MACRS DB front-loads vs SL — early-year deferred tax should be positive."""
        config = AssetConfig(
            asset_name="Mixed",
            cost=Decimal("10000"),
            useful_life_years=5,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
            macrs_convention=MacrsConvention.HALF_YEAR,
        )
        result = generate_depreciation_schedule(config)
        # Year 1: tax = 2000 (20%), book SL = 2000 → roughly even
        # Year 2: tax = 3200 (32%), book SL = 2000 → tax exceeds book
        year2 = result.book_tax_comparison[1]
        assert year2.timing_difference > Decimal("0")


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    def test_negative_cost_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(AssetConfig(asset_name="x", cost=Decimal("-1"), useful_life_years=5))

    def test_salvage_exceeds_cost_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(
                AssetConfig(
                    asset_name="x",
                    cost=Decimal("100"),
                    salvage_value=Decimal("200"),
                    useful_life_years=5,
                )
            )

    def test_zero_useful_life_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(AssetConfig(asset_name="x", cost=Decimal("100"), useful_life_years=0))

    def test_macrs_without_class_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(
                AssetConfig(
                    asset_name="x",
                    cost=Decimal("100"),
                    useful_life_years=5,
                    macrs_system=MacrsSystem.GDS_200,
                )
            )

    def test_macrs_unsupported_class_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(
                AssetConfig(
                    asset_name="x",
                    cost=Decimal("100"),
                    useful_life_years=5,
                    macrs_system=MacrsSystem.GDS_200,
                    macrs_property_class=4,  # Not a valid class
                )
            )

    def test_uop_without_units_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(
                AssetConfig(
                    asset_name="x",
                    cost=Decimal("100"),
                    useful_life_years=5,
                    book_method=BookMethod.UNITS_OF_PRODUCTION,
                )
            )


# =============================================================================
# Serialization
# =============================================================================


class TestSerialization:
    def test_to_dict_round_trip(self):
        config = AssetConfig(
            asset_name="Asset",
            cost=Decimal("5000"),
            useful_life_years=3,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
        )
        result = generate_depreciation_schedule(config)
        payload = result.to_dict()
        assert "book_schedule" in payload
        assert "tax_schedule" in payload
        assert "book_tax_comparison" in payload
        assert payload["total_book_depreciation"] == str(result.total_book_depreciation)
