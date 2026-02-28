"""
Tests for Expense Category Analytical Procedures — Sprint 289
"""

import math

import pytest

from expense_category_engine import (
    CAT_COGS,
    CAT_DEPRECIATION,
    CAT_INTEREST_TAX,
    CAT_PAYROLL,
    CATEGORY_ORDER,
    ExpenseCategoryReport,
    _classify_expense_subcategory,
    compute_expense_categories,
    run_expense_category_analytics,
)

# ═══════════════════════════════════════════════════════════════
# Test Sub-Category Classification
# ═══════════════════════════════════════════════════════════════


class TestSubCategoryClassification:
    """Verify keyword priority: COGS > Payroll > Depreciation > Interest/Tax > Other."""

    def test_cogs_keyword(self):
        assert _classify_expense_subcategory("Cost of Goods Sold") == CAT_COGS

    def test_cogs_variations(self):
        assert _classify_expense_subcategory("COGS") == CAT_COGS
        assert _classify_expense_subcategory("Cost of Sales") == CAT_COGS
        assert _classify_expense_subcategory("Direct Material Costs") == CAT_COGS

    def test_payroll_keyword(self):
        assert _classify_expense_subcategory("Salaries Expense") == CAT_PAYROLL
        assert _classify_expense_subcategory("Payroll Tax") == CAT_PAYROLL
        assert _classify_expense_subcategory("Employee Benefits") == CAT_PAYROLL

    def test_depreciation_keyword(self):
        assert _classify_expense_subcategory("Depreciation Expense") == CAT_DEPRECIATION
        assert _classify_expense_subcategory("Amortization of Intangibles") == CAT_DEPRECIATION

    def test_interest_tax_keyword(self):
        assert _classify_expense_subcategory("Interest Expense") == CAT_INTEREST_TAX
        assert _classify_expense_subcategory("Income Tax Expense") == CAT_INTEREST_TAX

    def test_priority_cogs_over_payroll(self):
        """COGS keywords take priority even if payroll keywords also match."""
        # "Direct Labor" matches COGS (direct), not payroll
        assert _classify_expense_subcategory("Direct Labor Costs") == CAT_COGS

    def test_non_expense_returns_none(self):
        """Accounts without any matching keyword return None."""
        assert _classify_expense_subcategory("Cash in Bank") is None
        assert _classify_expense_subcategory("Accounts Receivable") is None
        assert _classify_expense_subcategory("Revenue") is None
        assert _classify_expense_subcategory("Office Supplies") is None


# ═══════════════════════════════════════════════════════════════
# Test compute_expense_categories
# ═══════════════════════════════════════════════════════════════


class TestComputeExpenseCategories:
    """Test core expense category computation."""

    def test_empty_input(self):
        result = compute_expense_categories({}, {}, 0.0)
        assert isinstance(result, ExpenseCategoryReport)
        assert result.total_expenses == 0.0
        assert result.category_count == 0
        assert len(result.categories) == 0

    def test_zero_revenue_guard(self):
        """When total revenue is zero, pct_of_revenue should be None."""
        balances = {"Cost of Goods Sold": {"debit": 1000.0, "credit": 0.0}}
        classified = {"Cost of Goods Sold": "Expense"}
        result = compute_expense_categories(balances, classified, 0.0)
        cogs_cat = next(c for c in result.categories if c.key == CAT_COGS)
        assert cogs_cat.pct_of_revenue is None
        assert not result.revenue_available

    def test_five_categories_produced(self):
        """All 5 sub-categories appear in the result."""
        balances = {
            "Cost of Goods Sold": {"debit": 500.0, "credit": 0.0},
            "Salaries Expense": {"debit": 300.0, "credit": 0.0},
            "Depreciation Expense": {"debit": 100.0, "credit": 0.0},
            "Interest Expense": {"debit": 50.0, "credit": 0.0},
            "Office Rent": {"debit": 200.0, "credit": 0.0},
        }
        classified = {k: "Expense" for k in balances}
        result = compute_expense_categories(balances, classified, 2000.0)
        assert len(result.categories) == 5
        keys = [c.key for c in result.categories]
        assert keys == CATEGORY_ORDER

    def test_amounts_sum(self):
        """Total expenses should equal sum of sub-category amounts."""
        balances = {
            "Cost of Goods Sold": {"debit": 500.0, "credit": 0.0},
            "Salaries Expense": {"debit": 300.0, "credit": 0.0},
            "Depreciation Expense": {"debit": 100.0, "credit": 0.0},
            "Interest Expense": {"debit": 50.0, "credit": 0.0},
            "Office Rent": {"debit": 200.0, "credit": 0.0},
        }
        classified = {k: "Expense" for k in balances}
        result = compute_expense_categories(balances, classified, 2000.0)
        cat_sum = math.fsum(c.amount for c in result.categories)
        assert abs(result.total_expenses - cat_sum) < 0.01
        assert abs(result.total_expenses - 1150.0) < 0.01

    def test_pct_of_revenue_calculation(self):
        """Percentage of revenue should be computed correctly."""
        balances = {"Cost of Goods Sold": {"debit": 500.0, "credit": 0.0}}
        classified = {"Cost of Goods Sold": "Expense"}
        result = compute_expense_categories(balances, classified, 1000.0)
        cogs_cat = next(c for c in result.categories if c.key == CAT_COGS)
        assert cogs_cat.pct_of_revenue is not None
        assert abs(cogs_cat.pct_of_revenue - 50.0) < 0.01

    def test_prior_comparison(self):
        """When prior data is provided, dollar_change and exceeds_threshold are set."""
        balances = {"Cost of Goods Sold": {"debit": 600.0, "credit": 0.0}}
        classified = {"Cost of Goods Sold": "Expense"}
        result = compute_expense_categories(
            balances,
            classified,
            1000.0,
            materiality_threshold=50.0,
            prior_cogs=400.0,
            prior_total_expenses=800.0,
            prior_revenue=900.0,
        )
        cogs_cat = next(c for c in result.categories if c.key == CAT_COGS)
        assert cogs_cat.prior_amount == 400.0
        assert cogs_cat.dollar_change == 200.0
        assert cogs_cat.exceeds_threshold is True
        assert result.prior_available is True

    def test_materiality_flag_not_set_when_below(self):
        """Dollar change below materiality should not flag."""
        balances = {"Cost of Goods Sold": {"debit": 410.0, "credit": 0.0}}
        classified = {"Cost of Goods Sold": "Expense"}
        result = compute_expense_categories(
            balances,
            classified,
            1000.0,
            materiality_threshold=50.0,
            prior_cogs=400.0,
            prior_total_expenses=800.0,
        )
        cogs_cat = next(c for c in result.categories if c.key == CAT_COGS)
        assert cogs_cat.exceeds_threshold is False

    def test_non_expense_accounts_excluded(self):
        """Accounts classified as non-expense should not appear in totals."""
        balances = {
            "Cash": {"debit": 5000.0, "credit": 0.0},
            "Revenue": {"debit": 0.0, "credit": 3000.0},
            "Salaries Expense": {"debit": 200.0, "credit": 0.0},
        }
        classified = {
            "Cash": "Asset",
            "Revenue": "Revenue",
            "Salaries Expense": "Expense",
        }
        result = compute_expense_categories(balances, classified, 3000.0)
        assert abs(result.total_expenses - 200.0) < 0.01

    def test_to_dict_structure(self):
        """to_dict() should return the expected shape."""
        balances = {"Cost of Goods Sold": {"debit": 500.0, "credit": 0.0}}
        classified = {"Cost of Goods Sold": "Expense"}
        result = compute_expense_categories(balances, classified, 1000.0, materiality_threshold=100.0)
        d = result.to_dict()
        assert "categories" in d
        assert "total_expenses" in d
        assert "total_revenue" in d
        assert "revenue_available" in d
        assert "prior_available" in d
        assert "materiality_threshold" in d
        assert "category_count" in d
        assert isinstance(d["categories"], list)
        for cat in d["categories"]:
            assert "label" in cat
            assert "key" in cat
            assert "amount" in cat
            assert "pct_of_revenue" in cat

    def test_category_count_excludes_zero_amounts(self):
        """category_count should only count categories with non-zero amounts."""
        balances = {
            "Cost of Goods Sold": {"debit": 500.0, "credit": 0.0},
            "Salaries Expense": {"debit": 300.0, "credit": 0.0},
        }
        classified = {k: "Expense" for k in balances}
        result = compute_expense_categories(balances, classified, 1000.0)
        # Only COGS and Payroll have non-zero amounts
        assert result.category_count == 2


# ═══════════════════════════════════════════════════════════════
# Test run_expense_category_analytics (standalone entry point)
# ═══════════════════════════════════════════════════════════════


class TestRunExpenseCategoryAnalytics:
    """Test the standalone entry point that parses raw data."""

    def test_missing_columns(self):
        """Should return empty report when columns can't be detected."""
        result = run_expense_category_analytics(
            column_names=["foo", "bar"],
            rows=[{"foo": "x", "bar": 1}],
            filename="test.csv",
        )
        assert isinstance(result, ExpenseCategoryReport)
        assert result.total_expenses == 0.0

    def test_basic_parsed_data(self):
        """Should parse and classify accounts from raw row data."""
        columns = ["Account", "Debit", "Credit"]
        rows = [
            {"Account": "Cost of Goods Sold", "Debit": 500, "Credit": 0},
            {"Account": "Salaries Expense", "Debit": 200, "Credit": 0},
            {"Account": "Revenue", "Debit": 0, "Credit": 1000},
        ]
        result = run_expense_category_analytics(columns, rows, "test.csv")
        assert result.total_expenses > 0
        assert len(result.categories) == 5


# ═══════════════════════════════════════════════════════════════
# Test Route Registration
# ═══════════════════════════════════════════════════════════════


class TestRouteRegistration:
    """Verify that new routes are registered on the app."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        from main import app

        self.routes = [r.path for r in app.routes if hasattr(r, "path")]

    def test_expense_category_analytics_route(self):
        assert "/audit/expense-category-analytics" in self.routes

    def test_expense_category_memo_route(self):
        assert "/export/expense-category-memo" in self.routes

    def test_expense_category_csv_route(self):
        assert "/export/csv/expense-category-analytics" in self.routes
