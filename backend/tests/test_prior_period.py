"""
Tests for Sprint 51 Prior Period Comparison.

Tests cover:
- Variance calculation for categories
- Ratio variance calculation
- Full period comparison
- Period label generation
- Significance flagging
"""

from datetime import date, datetime, timezone

import pytest

from prior_period_comparison import (
    CategoryVariance,
    PeriodComparison,
    RatioVariance,
    calculate_ratio_variance,
    calculate_variance,
    compare_periods,
    generate_period_label,
)

# =============================================================================
# VARIANCE CALCULATION TESTS
# =============================================================================

class TestCalculateVariance:
    """Tests for calculate_variance function."""

    def test_simple_increase(self):
        """Increase should show positive variance."""
        dollar, percent, is_sig, direction = calculate_variance(150, 100)
        assert dollar == 50
        assert percent == 50.0
        assert direction == "increase"

    def test_simple_decrease(self):
        """Decrease should show negative variance."""
        dollar, percent, is_sig, direction = calculate_variance(80, 100)
        assert dollar == -20
        assert percent == -20.0
        assert direction == "decrease"

    def test_no_change(self):
        """Same values should show unchanged."""
        dollar, percent, is_sig, direction = calculate_variance(100, 100)
        assert dollar == 0
        assert percent == 0.0
        assert direction == "unchanged"

    def test_zero_prior(self):
        """Zero prior should return None for percent (no meaningful base)."""
        dollar, percent, is_sig, direction = calculate_variance(100, 0)
        assert dollar == 100
        assert percent is None
        assert direction == "increase"

    def test_near_zero_prior_returns_none(self):
        """Near-zero prior (below NEAR_ZERO threshold) returns None percent."""
        dollar, percent, is_sig, direction = calculate_variance(100, 0.001)
        assert dollar == pytest.approx(99.999)
        assert percent is None
        assert direction == "increase"

    def test_zero_both(self):
        """Both zero should be unchanged with None percent."""
        dollar, percent, is_sig, direction = calculate_variance(0, 0)
        assert dollar == 0
        assert percent is None
        assert direction == "unchanged"

    def test_significant_by_percent(self):
        """Variance > threshold percent should be significant."""
        dollar, percent, is_sig, direction = calculate_variance(115, 100)
        assert percent == 15.0
        assert is_sig is True  # 15% > 10% threshold

    def test_not_significant_by_percent(self):
        """Variance < threshold percent should not be significant."""
        dollar, percent, is_sig, direction = calculate_variance(105, 100)
        assert percent == 5.0
        assert is_sig is False  # 5% < 10% threshold, and $5 < $10K

    def test_significant_by_amount(self):
        """Variance > threshold amount should be significant."""
        dollar, percent, is_sig, direction = calculate_variance(110000, 100000)
        assert dollar == 10000
        assert is_sig is True  # $10K >= threshold

    def test_negative_values(self):
        """Handle negative values correctly."""
        dollar, percent, is_sig, direction = calculate_variance(-50, -100)
        assert dollar == 50  # -50 - (-100) = 50
        assert percent == 50.0  # 50 / abs(-100) = 50% (improved from -100 to -50)
        assert direction == "increase"


class TestCalculateRatioVariance:
    """Tests for calculate_ratio_variance function."""

    def test_ratio_increase(self):
        """Ratio increase should show positive point change."""
        change, is_sig, direction = calculate_ratio_variance(2.5, 2.0)
        assert change == 0.5
        assert direction == "increase"

    def test_ratio_decrease(self):
        """Ratio decrease should show negative point change."""
        change, is_sig, direction = calculate_ratio_variance(1.8, 2.0)
        assert change == pytest.approx(-0.2)
        assert direction == "decrease"

    def test_ratio_unchanged(self):
        """Similar ratios should show unchanged."""
        change, is_sig, direction = calculate_ratio_variance(2.0, 2.005)
        assert direction == "unchanged"

    def test_none_current(self):
        """None current should return unchanged."""
        change, is_sig, direction = calculate_ratio_variance(None, 2.0)
        assert change is None
        assert direction == "unchanged"

    def test_none_prior(self):
        """None prior should return unchanged."""
        change, is_sig, direction = calculate_ratio_variance(2.0, None)
        assert change is None
        assert direction == "unchanged"

    def test_both_none(self):
        """Both None should return unchanged."""
        change, is_sig, direction = calculate_ratio_variance(None, None)
        assert change is None
        assert direction == "unchanged"

    def test_significant_ratio_change(self):
        """Large ratio change should be significant."""
        change, is_sig, direction = calculate_ratio_variance(2.5, 2.0)
        assert change == 0.5
        assert is_sig is True  # 0.5 > 0.1 threshold


# =============================================================================
# PERIOD COMPARISON TESTS
# =============================================================================

class TestComparePeriods:
    """Tests for compare_periods function."""

    @pytest.fixture
    def current_data(self):
        """Sample current period data."""
        return {
            "total_assets": 500000,
            "current_assets": 200000,
            "inventory": 50000,
            "total_liabilities": 200000,
            "current_liabilities": 80000,
            "total_equity": 300000,
            "total_revenue": 1000000,
            "cost_of_goods_sold": 600000,
            "total_expenses": 300000,
            "operating_expenses": 200000,
            "current_ratio": 2.5,
            "quick_ratio": 1.875,
            "debt_to_equity": 0.667,
            "gross_margin": 0.40,
            "net_profit_margin": 0.10,
            "operating_margin": 0.20,
            "return_on_assets": 0.20,
            "return_on_equity": 0.333,
            "total_debits": 500000,
            "total_credits": 500000,
            "anomaly_count": 5,
            "row_count": 100,
        }

    @pytest.fixture
    def prior_data(self):
        """Sample prior period data."""
        return {
            "period_label": "FY2024",
            "total_assets": 450000,
            "current_assets": 180000,
            "inventory": 45000,
            "total_liabilities": 180000,
            "current_liabilities": 75000,
            "total_equity": 270000,
            "total_revenue": 900000,
            "cost_of_goods_sold": 540000,
            "total_expenses": 280000,
            "operating_expenses": 180000,
            "current_ratio": 2.4,
            "quick_ratio": 1.8,
            "debt_to_equity": 0.667,
            "gross_margin": 0.40,
            "net_profit_margin": 0.089,
            "operating_margin": 0.178,
            "return_on_assets": 0.178,
            "return_on_equity": 0.296,
            "total_debits": 450000,
            "total_credits": 450000,
            "anomaly_count": 8,
            "row_count": 95,
        }

    def test_comparison_returns_period_comparison(self, current_data, prior_data):
        """compare_periods should return PeriodComparison."""
        result = compare_periods(current_data, prior_data, prior_id=1)
        assert isinstance(result, PeriodComparison)

    def test_comparison_labels(self, current_data, prior_data):
        """Comparison should have correct labels."""
        result = compare_periods(
            current_data, prior_data,
            current_label="FY2025",
            prior_id=1
        )
        assert result.current_period_label == "FY2025"
        assert result.prior_period_label == "FY2024"

    def test_balance_sheet_variances(self, current_data, prior_data):
        """Should calculate balance sheet variances."""
        result = compare_periods(current_data, prior_data, prior_id=1)
        assert len(result.balance_sheet_variances) == 6

        # Check total assets variance
        assets_var = next(
            v for v in result.balance_sheet_variances
            if v.category_key == "total_assets"
        )
        assert assets_var.current_value == 500000
        assert assets_var.prior_value == 450000
        assert assets_var.dollar_variance == 50000
        assert assets_var.direction == "increase"

    def test_income_statement_variances(self, current_data, prior_data):
        """Should calculate income statement variances."""
        result = compare_periods(current_data, prior_data, prior_id=1)
        assert len(result.income_statement_variances) == 4

        # Check revenue variance
        revenue_var = next(
            v for v in result.income_statement_variances
            if v.category_key == "total_revenue"
        )
        assert revenue_var.current_value == 1000000
        assert revenue_var.prior_value == 900000
        assert revenue_var.dollar_variance == 100000
        assert revenue_var.direction == "increase"

    def test_ratio_variances(self, current_data, prior_data):
        """Should calculate ratio variances."""
        result = compare_periods(current_data, prior_data, prior_id=1)
        assert len(result.ratio_variances) == 8

        # Check current ratio variance
        cr_var = next(
            v for v in result.ratio_variances
            if v.ratio_key == "current_ratio"
        )
        assert cr_var.current_value == 2.5
        assert cr_var.prior_value == 2.4
        assert cr_var.point_change == pytest.approx(0.1)

    def test_diagnostic_variances(self, current_data, prior_data):
        """Should calculate diagnostic variances."""
        result = compare_periods(current_data, prior_data, prior_id=1)
        assert len(result.diagnostic_variances) == 4

        # Check anomaly count variance (decreased from 8 to 5)
        anomaly_var = next(
            v for v in result.diagnostic_variances
            if v.metric_key == "anomaly_count"
        )
        assert anomaly_var.current_value == 5
        assert anomaly_var.prior_value == 8
        assert anomaly_var.variance == -3
        assert anomaly_var.direction == "decrease"

    def test_significant_variance_count(self, current_data, prior_data):
        """Should count significant variances."""
        result = compare_periods(current_data, prior_data, prior_id=1)
        assert result.significant_variance_count >= 0
        assert result.total_categories_compared > 0

    def test_to_dict(self, current_data, prior_data):
        """Should convert to dictionary correctly."""
        result = compare_periods(current_data, prior_data, prior_id=1)
        result_dict = result.to_dict()

        assert "current_period_label" in result_dict
        assert "prior_period_label" in result_dict
        assert "balance_sheet_variances" in result_dict
        assert "income_statement_variances" in result_dict
        assert "ratio_variances" in result_dict
        assert "significant_variance_count" in result_dict


# =============================================================================
# PERIOD LABEL GENERATION TESTS
# =============================================================================

class TestGeneratePeriodLabel:
    """Tests for generate_period_label function."""

    def test_annual_label(self):
        """Annual period should show FY format."""
        label = generate_period_label(date(2025, 12, 31), "annual")
        assert label == "FY2025"

    def test_quarterly_q1(self):
        """Q1 should be months 1-3."""
        label = generate_period_label(date(2025, 3, 31), "quarterly")
        assert label == "Q1 2025"

    def test_quarterly_q2(self):
        """Q2 should be months 4-6."""
        label = generate_period_label(date(2025, 6, 30), "quarterly")
        assert label == "Q2 2025"

    def test_quarterly_q3(self):
        """Q3 should be months 7-9."""
        label = generate_period_label(date(2025, 9, 30), "quarterly")
        assert label == "Q3 2025"

    def test_quarterly_q4(self):
        """Q4 should be months 10-12."""
        label = generate_period_label(date(2025, 12, 31), "quarterly")
        assert label == "Q4 2025"

    def test_monthly_label(self):
        """Monthly period should show month name."""
        label = generate_period_label(date(2025, 6, 30), "monthly")
        assert label == "Jun 2025"

    def test_monthly_december(self):
        """December should show Dec."""
        label = generate_period_label(date(2025, 12, 31), "monthly")
        assert label == "Dec 2025"

    def test_monthly_january(self):
        """January should show Jan."""
        label = generate_period_label(date(2025, 1, 31), "monthly")
        assert label == "Jan 2025"

    def test_default_format(self):
        """Unknown type should use date format."""
        label = generate_period_label(date(2025, 6, 15), None)
        assert label == "2025-06-15"

    def test_none_date(self):
        """None date should return unknown."""
        label = generate_period_label(None, "annual")
        assert label == "Unknown Period"


# =============================================================================
# DATA CLASS TESTS
# =============================================================================

class TestCategoryVariance:
    """Tests for CategoryVariance dataclass."""

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        variance = CategoryVariance(
            category_key="total_assets",
            category_name="Total Assets",
            current_value=100000,
            prior_value=90000,
            dollar_variance=10000,
            percent_variance=11.11,
            is_significant=True,
            direction="increase",
        )
        result = variance.to_dict()

        assert result["category_key"] == "total_assets"
        assert result["current_value"] == 100000
        assert result["dollar_variance"] == 10000
        assert result["is_significant"] is True


class TestRatioVariance:
    """Tests for RatioVariance dataclass."""

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        variance = RatioVariance(
            ratio_key="current_ratio",
            ratio_name="Current Ratio",
            current_value=2.5,
            prior_value=2.0,
            point_change=0.5,
            is_significant=True,
            direction="increase",
            is_percentage=False,
        )
        result = variance.to_dict()

        assert result["ratio_key"] == "current_ratio"
        assert result["current_value"] == 2.5
        assert result["point_change"] == 0.5
        assert result["is_percentage"] is False


class TestPeriodComparison:
    """Tests for PeriodComparison dataclass."""

    def test_default_values(self):
        """Should have default empty lists."""
        comparison = PeriodComparison(
            current_period_label="FY2025",
            prior_period_label="FY2024",
            prior_period_id=1,
            comparison_timestamp=datetime.now(timezone.utc),
        )

        assert comparison.balance_sheet_variances == []
        assert comparison.income_statement_variances == []
        assert comparison.ratio_variances == []
        assert comparison.significant_variance_count == 0


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases in comparison."""

    def test_missing_current_fields(self):
        """Should handle missing fields in current data."""
        current = {"total_assets": 100000}  # Missing most fields
        prior = {
            "total_assets": 90000,
            "total_liabilities": 50000,
        }

        result = compare_periods(current, prior, prior_id=1)
        assert len(result.balance_sheet_variances) == 6  # All categories included

    def test_missing_prior_fields(self):
        """Should handle missing fields in prior data."""
        current = {
            "total_assets": 100000,
            "total_liabilities": 50000,
        }
        prior = {"total_assets": 90000}  # Missing most fields

        result = compare_periods(current, prior, prior_id=1)
        assert len(result.balance_sheet_variances) == 6

    def test_all_zeros(self):
        """Should handle all zero values."""
        current = {
            "total_assets": 0,
            "total_liabilities": 0,
        }
        prior = {
            "total_assets": 0,
            "total_liabilities": 0,
        }

        result = compare_periods(current, prior, prior_id=1)

        assets_var = next(
            v for v in result.balance_sheet_variances
            if v.category_key == "total_assets"
        )
        assert assets_var.direction == "unchanged"

    def test_very_large_values(self):
        """Should handle very large values."""
        current = {"total_assets": 1_000_000_000_000}  # $1 trillion
        prior = {"total_assets": 900_000_000_000}

        result = compare_periods(current, prior, prior_id=1)

        assets_var = next(
            v for v in result.balance_sheet_variances
            if v.category_key == "total_assets"
        )
        assert assets_var.dollar_variance == 100_000_000_000
        assert assets_var.is_significant is True
