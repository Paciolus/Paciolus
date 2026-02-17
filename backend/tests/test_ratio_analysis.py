"""Test suite for ratio_engine.py — analytics and structural analysis.

Covers: CommonSizeAnalyzer, VarianceAnalyzer, CategoryTotals,
ExtractCategoryTotals, CalculateAnalytics.
"""

import pytest

from ratio_engine import (
    CategoryTotals,
    CommonSizeAnalyzer,
    TrendDirection,
    VarianceAnalyzer,
    calculate_analytics,
    extract_category_totals,
)

# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def healthy_company_totals():
    """A company with healthy financial ratios."""
    return CategoryTotals(
        total_assets=1000000.0,
        current_assets=400000.0,
        inventory=100000.0,
        total_liabilities=300000.0,
        current_liabilities=150000.0,
        total_equity=700000.0,
        total_revenue=500000.0,
        cost_of_goods_sold=200000.0,
        total_expenses=350000.0,
    )


@pytest.fixture
def struggling_company_totals():
    """A company with concerning financial ratios."""
    return CategoryTotals(
        total_assets=500000.0,
        current_assets=50000.0,
        inventory=30000.0,
        total_liabilities=450000.0,
        current_liabilities=200000.0,
        total_equity=50000.0,
        total_revenue=100000.0,
        cost_of_goods_sold=90000.0,
        total_expenses=95000.0,
    )


@pytest.fixture
def zero_values_totals():
    """Company with zero values to test division-by-zero handling."""
    return CategoryTotals(
        total_assets=100000.0,
        current_assets=50000.0,
        inventory=10000.0,
        total_liabilities=0.0,
        current_liabilities=0.0,
        total_equity=0.0,
        total_revenue=0.0,
        cost_of_goods_sold=0.0,
        total_expenses=0.0,
    )


@pytest.fixture
def empty_totals():
    """Company with all zeros."""
    return CategoryTotals()


# =============================================================================
# CommonSizeAnalyzer Tests
# =============================================================================

class TestCommonSizeAnalyzer:
    """Test cases for Common-Size analysis."""

    def test_balance_sheet_percentages(self, healthy_company_totals):
        """Test balance sheet common-size percentages."""
        analyzer = CommonSizeAnalyzer(healthy_company_totals)
        result = analyzer.balance_sheet_percentages()

        # Current assets: 400,000 / 1,000,000 = 40%
        assert result["current_assets_pct"] == pytest.approx(40.0, rel=0.1)
        # Inventory: 100,000 / 1,000,000 = 10%
        assert result["inventory_pct"] == pytest.approx(10.0, rel=0.1)
        # Total liabilities: 300,000 / 1,000,000 = 30%
        assert result["total_liabilities_pct"] == pytest.approx(30.0, rel=0.1)

    def test_balance_sheet_zero_assets(self, empty_totals):
        """Test balance sheet percentages with zero total assets."""
        analyzer = CommonSizeAnalyzer(empty_totals)
        result = analyzer.balance_sheet_percentages()

        assert result == {}  # Returns empty dict when base is zero

    def test_income_statement_percentages(self, healthy_company_totals):
        """Test income statement common-size percentages."""
        analyzer = CommonSizeAnalyzer(healthy_company_totals)
        result = analyzer.income_statement_percentages()

        # COGS: 200,000 / 500,000 = 40%
        assert result["cogs_pct"] == pytest.approx(40.0, rel=0.1)
        # Gross profit: 300,000 / 500,000 = 60%
        assert result["gross_profit_pct"] == pytest.approx(60.0, rel=0.1)

    def test_income_statement_zero_revenue(self, zero_values_totals):
        """Test income statement percentages with zero revenue."""
        analyzer = CommonSizeAnalyzer(zero_values_totals)
        result = analyzer.income_statement_percentages()

        assert result == {}  # Returns empty dict when base is zero


# =============================================================================
# VarianceAnalyzer Tests
# =============================================================================

class TestVarianceAnalyzer:
    """Test cases for Variance analysis."""

    def test_variance_calculation_increase(self):
        """Test variance calculation for an increase."""
        current = CategoryTotals(total_assets=120000.0)
        previous = CategoryTotals(total_assets=100000.0)

        analyzer = VarianceAnalyzer(current, previous)
        variances = analyzer.calculate_variances()

        assert "total_assets" in variances
        result = variances["total_assets"]

        assert result.current_value == 120000.0
        assert result.previous_value == 100000.0
        assert result.change_amount == 20000.0
        assert result.change_percent == pytest.approx(20.0, rel=0.1)
        assert result.direction == TrendDirection.POSITIVE

    def test_variance_calculation_decrease(self):
        """Test variance calculation for a decrease."""
        current = CategoryTotals(total_revenue=80000.0)
        previous = CategoryTotals(total_revenue=100000.0)

        analyzer = VarianceAnalyzer(current, previous)
        variances = analyzer.calculate_variances()

        result = variances["total_revenue"]

        assert result.change_amount == -20000.0
        assert result.change_percent == pytest.approx(-20.0, rel=0.1)
        assert result.direction == TrendDirection.NEGATIVE

    def test_variance_neutral_small_change(self):
        """Test that small changes are marked as neutral."""
        current = CategoryTotals(total_assets=100500.0)
        previous = CategoryTotals(total_assets=100000.0)  # 0.5% change

        analyzer = VarianceAnalyzer(current, previous)
        variances = analyzer.calculate_variances()

        result = variances["total_assets"]
        assert result.direction == TrendDirection.NEUTRAL

    def test_variance_no_previous_data(self):
        """Test variance analysis without previous data."""
        current = CategoryTotals(total_assets=100000.0)

        analyzer = VarianceAnalyzer(current, None)
        variances = analyzer.calculate_variances()

        assert variances == {}

    def test_variance_liabilities_higher_is_bad(self):
        """Test that increased liabilities are marked negative."""
        current = CategoryTotals(total_liabilities=150000.0)
        previous = CategoryTotals(total_liabilities=100000.0)

        analyzer = VarianceAnalyzer(current, previous)
        variances = analyzer.calculate_variances()

        result = variances["total_liabilities"]
        # Liabilities increase = negative trend
        assert result.direction == TrendDirection.NEGATIVE

    def test_variance_from_zero(self):
        """Test variance when previous value was zero."""
        current = CategoryTotals(total_assets=100000.0)
        previous = CategoryTotals(total_assets=0.0)

        analyzer = VarianceAnalyzer(current, previous)
        variances = analyzer.calculate_variances()

        result = variances["total_assets"]
        assert result.change_percent == 100.0  # 100% change from zero


# =============================================================================
# CategoryTotals Tests
# =============================================================================

class TestCategoryTotals:
    """Test cases for CategoryTotals dataclass."""

    def test_default_values(self):
        """Test that CategoryTotals initializes with zero defaults."""
        totals = CategoryTotals()

        assert totals.total_assets == 0.0
        assert totals.current_assets == 0.0
        assert totals.inventory == 0.0
        assert totals.total_liabilities == 0.0
        assert totals.current_liabilities == 0.0
        assert totals.total_equity == 0.0
        assert totals.total_revenue == 0.0
        assert totals.cost_of_goods_sold == 0.0
        assert totals.total_expenses == 0.0
        assert totals.operating_expenses == 0.0  # Sprint 26

    def test_to_dict_rounding(self):
        """Test that to_dict rounds values to 2 decimal places."""
        totals = CategoryTotals(
            total_assets=100000.1234,
            current_assets=50000.5678,
            operating_expenses=25000.9999,
        )
        result = totals.to_dict()

        assert result["total_assets"] == 100000.12
        assert result["current_assets"] == 50000.57
        assert result["operating_expenses"] == 25001.0  # Sprint 26

    def test_from_dict_creation(self):
        """Test creating CategoryTotals from a dictionary."""
        data = {
            "total_assets": 100000.0,
            "current_assets": 50000.0,
            "inventory": 10000.0,
            "operating_expenses": 15000.0,  # Sprint 26
        }
        totals = CategoryTotals.from_dict(data)

        assert totals.total_assets == 100000.0
        assert totals.current_assets == 50000.0
        assert totals.inventory == 10000.0
        assert totals.operating_expenses == 15000.0  # Sprint 26
        assert totals.total_liabilities == 0.0  # Missing keys default to 0

    def test_from_dict_missing_keys(self):
        """Test from_dict handles missing keys gracefully."""
        data = {}
        totals = CategoryTotals.from_dict(data)

        assert totals.total_assets == 0.0
        assert totals.total_revenue == 0.0
        assert totals.operating_expenses == 0.0  # Sprint 26


# =============================================================================
# extract_category_totals Tests
# =============================================================================

class TestExtractCategoryTotals:
    """Test cases for extracting category totals from account balances."""

    def test_extract_basic_accounts(self):
        """Test extracting totals from basic account balances."""
        account_balances = {
            "Cash": {"debit": 50000.0, "credit": 0.0},
            "Accounts Receivable": {"debit": 30000.0, "credit": 0.0},
            "Accounts Payable": {"debit": 0.0, "credit": 20000.0},
        }
        classified_accounts = {
            "Cash": "asset",
            "Accounts Receivable": "asset",
            "Accounts Payable": "liability",
        }

        totals = extract_category_totals(account_balances, classified_accounts)

        assert totals.total_assets == 80000.0  # Cash + AR
        assert totals.total_liabilities == 20000.0  # AP

    def test_extract_with_inventory(self):
        """Test that inventory accounts are properly identified."""
        account_balances = {
            "Inventory - Raw Materials": {"debit": 25000.0, "credit": 0.0},
            "Inventory - Finished Goods": {"debit": 35000.0, "credit": 0.0},
        }
        classified_accounts = {
            "Inventory - Raw Materials": "asset",
            "Inventory - Finished Goods": "asset",
        }

        totals = extract_category_totals(account_balances, classified_accounts)

        assert totals.inventory == 60000.0
        assert totals.current_assets == 60000.0

    def test_extract_revenue_and_expenses(self):
        """Test extracting revenue and expense totals."""
        account_balances = {
            "Sales Revenue": {"debit": 0.0, "credit": 100000.0},
            "Cost of Goods Sold": {"debit": 40000.0, "credit": 0.0},
            "Rent Expense": {"debit": 10000.0, "credit": 0.0},
        }
        classified_accounts = {
            "Sales Revenue": "revenue",
            "Cost of Goods Sold": "expense",
            "Rent Expense": "expense",
        }

        totals = extract_category_totals(account_balances, classified_accounts)

        assert totals.total_revenue == 100000.0
        assert totals.cost_of_goods_sold == 40000.0
        assert totals.total_expenses == 50000.0  # COGS + Rent

    def test_extract_operating_expenses(self):
        """Test extracting operating expenses separately (Sprint 26)."""
        account_balances = {
            "Sales Revenue": {"debit": 0.0, "credit": 200000.0},
            "Cost of Goods Sold": {"debit": 80000.0, "credit": 0.0},
            "Salary Expense": {"debit": 50000.0, "credit": 0.0},
            "Rent Expense": {"debit": 20000.0, "credit": 0.0},
            "Utilities Expense": {"debit": 5000.0, "credit": 0.0},
            "Interest Expense": {"debit": 10000.0, "credit": 0.0},  # Non-operating
        }
        classified_accounts = {
            "Sales Revenue": "revenue",
            "Cost of Goods Sold": "expense",
            "Salary Expense": "expense",
            "Rent Expense": "expense",
            "Utilities Expense": "expense",
            "Interest Expense": "expense",
        }

        totals = extract_category_totals(account_balances, classified_accounts)

        assert totals.total_revenue == 200000.0
        assert totals.cost_of_goods_sold == 80000.0
        # Operating expenses: Salary + Rent + Utilities = 75,000
        # (Interest is non-operating and excluded)
        assert totals.operating_expenses == 75000.0
        # Total expenses includes everything: COGS + Salary + Rent + Utilities + Interest
        assert totals.total_expenses == 165000.0

    def test_extract_excludes_non_operating(self):
        """Test that non-operating expenses are excluded from operating_expenses."""
        account_balances = {
            "Tax Expense": {"debit": 25000.0, "credit": 0.0},
            "Income Tax Payable Adjustment": {"debit": 5000.0, "credit": 0.0},
            "Loss on Sale of Equipment": {"debit": 15000.0, "credit": 0.0},
            "Advertising Expense": {"debit": 10000.0, "credit": 0.0},  # Operating
        }
        classified_accounts = {
            "Tax Expense": "expense",
            "Income Tax Payable Adjustment": "expense",
            "Loss on Sale of Equipment": "expense",
            "Advertising Expense": "expense",
        }

        totals = extract_category_totals(account_balances, classified_accounts)

        # Only Advertising is operating expense
        assert totals.operating_expenses == 10000.0
        # Total includes all
        assert totals.total_expenses == 55000.0


# =============================================================================
# calculate_analytics Integration Tests
# =============================================================================

class TestCalculateAnalytics:
    """Integration tests for the calculate_analytics function."""

    def test_analytics_without_previous(self, healthy_company_totals):
        """Test analytics calculation without previous data."""
        result = calculate_analytics(healthy_company_totals, previous_totals=None)

        assert "category_totals" in result
        assert "ratios" in result
        assert "common_size" in result
        assert "variances" in result
        assert result["has_previous_data"] is False
        assert result["variances"] == {}

    def test_analytics_with_previous(self, healthy_company_totals, struggling_company_totals):
        """Test analytics calculation with previous data for variance."""
        result = calculate_analytics(healthy_company_totals, previous_totals=struggling_company_totals)

        assert result["has_previous_data"] is True
        assert len(result["variances"]) > 0

    def test_analytics_structure(self, healthy_company_totals):
        """Test the structure of analytics output."""
        result = calculate_analytics(healthy_company_totals)

        # Check ratios structure
        assert "current_ratio" in result["ratios"]
        assert "quick_ratio" in result["ratios"]
        assert "debt_to_equity" in result["ratios"]
        assert "gross_margin" in result["ratios"]

        # Check common_size structure
        assert "balance_sheet" in result["common_size"]
        assert "income_statement" in result["common_size"]
