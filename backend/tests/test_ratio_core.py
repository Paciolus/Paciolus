"""Test suite for ratio_engine.py — individual ratio calculations and edge cases.

Covers: CurrentRatio, QuickRatio, DebtToEquity, GrossMargin, NetProfitMargin,
OperatingMargin, ReturnOnAssets, ReturnOnEquity, DaysSalesOutstanding,
CalculateAllRatios, EdgeCases, FinancialEdgeCases.
"""

import pytest

from ratio_engine import (
    CategoryTotals,
    RatioEngine,
    RatioResult,
    VarianceAnalyzer,
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
def negative_equity_totals():
    """Company with negative equity (liabilities exceed assets)."""
    return CategoryTotals(
        total_assets=200000.0,
        current_assets=80000.0,
        inventory=20000.0,
        total_liabilities=300000.0,
        current_liabilities=100000.0,
        total_equity=-100000.0,  # Negative equity
        total_revenue=150000.0,
        cost_of_goods_sold=50000.0,
        total_expenses=140000.0,
    )


# =============================================================================
# RatioEngine Tests - Current Ratio
# =============================================================================


class TestCurrentRatio:
    """Test cases for Current Ratio calculation."""

    def test_current_ratio_healthy_company(self, healthy_company_totals):
        """Test current ratio for a company with strong liquidity."""
        engine = RatioEngine(healthy_company_totals)
        result = engine.calculate_current_ratio()

        assert result.is_calculable is True
        assert result.name == "Current Ratio"
        # 400,000 / 150,000 = 2.67
        assert result.value == pytest.approx(2.67, rel=0.01)
        assert result.threshold_status == "above_threshold"
        assert "Strong liquidity" in result.interpretation

    def test_current_ratio_struggling_company(self, struggling_company_totals):
        """Test current ratio for a company with weak liquidity."""
        engine = RatioEngine(struggling_company_totals)
        result = engine.calculate_current_ratio()

        assert result.is_calculable is True
        # 50,000 / 200,000 = 0.25
        assert result.value == pytest.approx(0.25, rel=0.01)
        assert result.threshold_status == "below_threshold"
        assert "liquidity risk" in result.interpretation.lower()

    def test_current_ratio_zero_liabilities(self, zero_values_totals):
        """Test current ratio when current liabilities are zero."""
        engine = RatioEngine(zero_values_totals)
        result = engine.calculate_current_ratio()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"
        assert "Cannot calculate" in result.interpretation
        assert result.threshold_status == "neutral"

    def test_current_ratio_boundary_adequate(self):
        """Test current ratio at the boundary between adequate and warning."""
        totals = CategoryTotals(
            current_assets=100000.0,
            current_liabilities=100000.0,  # Exactly 1.0 ratio
        )
        engine = RatioEngine(totals)
        result = engine.calculate_current_ratio()

        assert result.is_calculable is True
        assert result.value == pytest.approx(1.0, rel=0.01)
        assert result.threshold_status == "above_threshold"
        assert "Adequate" in result.interpretation

    def test_current_ratio_boundary_warning(self):
        """Test current ratio at warning threshold."""
        totals = CategoryTotals(
            current_assets=70000.0,
            current_liabilities=100000.0,  # 0.7 ratio
        )
        engine = RatioEngine(totals)
        result = engine.calculate_current_ratio()

        assert result.is_calculable is True
        assert result.value == pytest.approx(0.70, rel=0.01)
        assert result.threshold_status == "at_threshold"


# =============================================================================
# RatioEngine Tests - Quick Ratio
# =============================================================================


class TestQuickRatio:
    """Test cases for Quick Ratio (Acid-Test) calculation."""

    def test_quick_ratio_healthy_company(self, healthy_company_totals):
        """Test quick ratio for a company with strong quick liquidity."""
        engine = RatioEngine(healthy_company_totals)
        result = engine.calculate_quick_ratio()

        assert result.is_calculable is True
        assert result.name == "Quick Ratio"
        # (400,000 - 100,000) / 150,000 = 2.0
        assert result.value == pytest.approx(2.0, rel=0.01)
        assert result.threshold_status == "above_threshold"

    def test_quick_ratio_with_high_inventory(self):
        """Test quick ratio when inventory is significant portion of current assets."""
        totals = CategoryTotals(
            current_assets=100000.0,
            inventory=80000.0,  # 80% inventory
            current_liabilities=50000.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_quick_ratio()

        assert result.is_calculable is True
        # (100,000 - 80,000) / 50,000 = 0.4
        assert result.value == pytest.approx(0.4, rel=0.01)
        assert result.threshold_status == "below_threshold"

    def test_quick_ratio_zero_liabilities(self, zero_values_totals):
        """Test quick ratio when current liabilities are zero."""
        engine = RatioEngine(zero_values_totals)
        result = engine.calculate_quick_ratio()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"

    def test_quick_ratio_no_inventory(self):
        """Test quick ratio when there is no inventory (service company)."""
        totals = CategoryTotals(
            current_assets=100000.0,
            inventory=0.0,
            current_liabilities=80000.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_quick_ratio()

        assert result.is_calculable is True
        # Quick ratio equals current ratio when inventory = 0
        assert result.value == pytest.approx(1.25, rel=0.01)
        assert result.threshold_status == "above_threshold"


# =============================================================================
# RatioEngine Tests - Debt-to-Equity
# =============================================================================


class TestDebtToEquity:
    """Test cases for Debt-to-Equity Ratio calculation."""

    def test_debt_to_equity_conservative(self, healthy_company_totals):
        """Test D/E for a conservatively financed company."""
        engine = RatioEngine(healthy_company_totals)
        result = engine.calculate_debt_to_equity()

        assert result.is_calculable is True
        assert result.name == "Debt-to-Equity"
        # 300,000 / 700,000 = 0.43
        assert result.value == pytest.approx(0.43, rel=0.01)
        assert result.threshold_status == "above_threshold"
        assert "Conservative" in result.interpretation

    def test_debt_to_equity_high_leverage(self, struggling_company_totals):
        """Test D/E for a highly leveraged company."""
        engine = RatioEngine(struggling_company_totals)
        result = engine.calculate_debt_to_equity()

        assert result.is_calculable is True
        # 450,000 / 50,000 = 9.0
        assert result.value == pytest.approx(9.0, rel=0.01)
        assert result.threshold_status == "below_threshold"
        assert "High" in result.interpretation

    def test_debt_to_equity_zero_equity(self, zero_values_totals):
        """Test D/E when equity is zero."""
        engine = RatioEngine(zero_values_totals)
        result = engine.calculate_debt_to_equity()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"
        assert "No equity" in result.interpretation

    def test_debt_to_equity_negative_equity(self, negative_equity_totals):
        """Test D/E when equity is negative (technical insolvency)."""
        engine = RatioEngine(negative_equity_totals)
        result = engine.calculate_debt_to_equity()

        assert result.is_calculable is True
        # 300,000 / -100,000 = -3.0
        assert result.value == pytest.approx(-3.0, rel=0.01)
        # Negative D/E indicates technical insolvency

    def test_debt_to_equity_balanced(self):
        """Test D/E when debt equals equity (1:1 ratio)."""
        totals = CategoryTotals(
            total_liabilities=500000.0,
            total_equity=500000.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_debt_to_equity()

        assert result.is_calculable is True
        assert result.value == pytest.approx(1.0, rel=0.01)
        assert result.threshold_status == "above_threshold"


# =============================================================================
# RatioEngine Tests - Gross Margin
# =============================================================================


class TestGrossMargin:
    """Test cases for Gross Margin calculation."""

    def test_gross_margin_healthy(self, healthy_company_totals):
        """Test gross margin for a company with strong margins."""
        engine = RatioEngine(healthy_company_totals)
        result = engine.calculate_gross_margin()

        assert result.is_calculable is True
        assert result.name == "Gross Margin"
        # (500,000 - 200,000) / 500,000 * 100 = 60%
        assert result.value == pytest.approx(60.0, rel=0.1)
        assert result.threshold_status == "above_threshold"
        assert "Strong" in result.interpretation

    def test_gross_margin_low(self, struggling_company_totals):
        """Test gross margin for a company with thin margins."""
        engine = RatioEngine(struggling_company_totals)
        result = engine.calculate_gross_margin()

        assert result.is_calculable is True
        # (100,000 - 90,000) / 100,000 * 100 = 10%
        assert result.value == pytest.approx(10.0, rel=0.1)
        assert result.threshold_status == "below_threshold"
        assert "Low" in result.interpretation

    def test_gross_margin_zero_revenue(self, zero_values_totals):
        """Test gross margin when revenue is zero."""
        engine = RatioEngine(zero_values_totals)
        result = engine.calculate_gross_margin()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"
        assert "No revenue" in result.interpretation

    def test_gross_margin_no_cogs(self):
        """Test gross margin when COGS is zero (100% margin)."""
        totals = CategoryTotals(
            total_revenue=100000.0,
            cost_of_goods_sold=0.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_gross_margin()

        assert result.is_calculable is True
        assert result.value == pytest.approx(100.0, rel=0.1)

    def test_gross_margin_negative(self):
        """Test gross margin when COGS exceeds revenue (negative margin)."""
        totals = CategoryTotals(
            total_revenue=100000.0,
            cost_of_goods_sold=120000.0,  # COGS > Revenue
        )
        engine = RatioEngine(totals)
        result = engine.calculate_gross_margin()

        assert result.is_calculable is True
        # (100,000 - 120,000) / 100,000 * 100 = -20%
        assert result.value == pytest.approx(-20.0, rel=0.1)


# =============================================================================
# RatioEngine Tests - Net Profit Margin (Sprint 26)
# =============================================================================


class TestNetProfitMargin:
    """Test cases for Net Profit Margin calculation (Sprint 26)."""

    def test_net_profit_margin_profitable(self, healthy_company_totals):
        """Test net profit margin for a profitable company."""
        engine = RatioEngine(healthy_company_totals)
        result = engine.calculate_net_profit_margin()

        assert result.is_calculable is True
        assert result.name == "Net Profit Margin"
        # (500,000 - 350,000) / 500,000 * 100 = 30%
        assert result.value == pytest.approx(30.0, rel=0.1)
        assert result.threshold_status == "above_threshold"
        assert "Excellent" in result.interpretation

    def test_net_profit_margin_low(self, struggling_company_totals):
        """Test net profit margin for a company with thin profits."""
        engine = RatioEngine(struggling_company_totals)
        result = engine.calculate_net_profit_margin()

        assert result.is_calculable is True
        # (100,000 - 95,000) / 100,000 * 100 = 5%
        assert result.value == pytest.approx(5.0, rel=0.1)
        assert result.threshold_status == "at_threshold"

    def test_net_profit_margin_loss(self):
        """Test net profit margin when company is at a loss."""
        totals = CategoryTotals(
            total_revenue=100000.0,
            total_expenses=120000.0,  # Loss
        )
        engine = RatioEngine(totals)
        result = engine.calculate_net_profit_margin()

        assert result.is_calculable is True
        # (100,000 - 120,000) / 100,000 * 100 = -20%
        assert result.value == pytest.approx(-20.0, rel=0.1)
        assert result.threshold_status == "below_threshold"
        assert "loss" in result.interpretation.lower()

    def test_net_profit_margin_zero_revenue(self, zero_values_totals):
        """Test net profit margin when revenue is zero."""
        engine = RatioEngine(zero_values_totals)
        result = engine.calculate_net_profit_margin()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"

    def test_net_profit_margin_breakeven(self):
        """Test net profit margin at breakeven (0% margin)."""
        totals = CategoryTotals(
            total_revenue=100000.0,
            total_expenses=100000.0,  # Breakeven
        )
        engine = RatioEngine(totals)
        result = engine.calculate_net_profit_margin()

        assert result.is_calculable is True
        assert result.value == pytest.approx(0.0, abs=0.1)
        assert result.threshold_status == "at_threshold"

    def test_net_profit_margin_boundary_healthy(self):
        """Test net profit margin at healthy threshold (10%)."""
        totals = CategoryTotals(
            total_revenue=100000.0,
            total_expenses=90000.0,  # 10% margin
        )
        engine = RatioEngine(totals)
        result = engine.calculate_net_profit_margin()

        assert result.is_calculable is True
        assert result.value == pytest.approx(10.0, rel=0.1)
        assert result.threshold_status == "above_threshold"


# =============================================================================
# RatioEngine Tests - Operating Margin (Sprint 26)
# =============================================================================


class TestOperatingMargin:
    """Test cases for Operating Margin calculation (Sprint 26)."""

    def test_operating_margin_with_explicit_opex(self):
        """Test operating margin when operating_expenses is explicitly set."""
        totals = CategoryTotals(
            total_revenue=500000.0,
            cost_of_goods_sold=200000.0,
            operating_expenses=150000.0,  # Explicitly set
            total_expenses=400000.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_operating_margin()

        assert result.is_calculable is True
        assert result.name == "Operating Margin"
        # (500,000 - 200,000 - 150,000) / 500,000 * 100 = 30%
        assert result.value == pytest.approx(30.0, rel=0.1)
        assert result.threshold_status == "above_threshold"

    def test_operating_margin_derived_from_totals(self, healthy_company_totals):
        """Test operating margin derived when operating_expenses is 0."""
        # healthy_company_totals has operating_expenses=0, so it derives
        engine = RatioEngine(healthy_company_totals)
        result = engine.calculate_operating_margin()

        assert result.is_calculable is True
        # Operating exp = total_expenses - COGS = 350,000 - 200,000 = 150,000
        # Operating income = 500,000 - 200,000 - 150,000 = 150,000
        # Margin = 150,000 / 500,000 * 100 = 30%
        assert result.value == pytest.approx(30.0, rel=0.1)

    def test_operating_margin_thin(self):
        """Test operating margin for company with thin margins."""
        totals = CategoryTotals(
            total_revenue=100000.0,
            cost_of_goods_sold=60000.0,
            operating_expenses=35000.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_operating_margin()

        assert result.is_calculable is True
        # (100,000 - 60,000 - 35,000) / 100,000 * 100 = 5%
        assert result.value == pytest.approx(5.0, rel=0.1)
        assert result.threshold_status == "at_threshold"

    def test_operating_margin_loss(self):
        """Test operating margin when company has operating loss."""
        totals = CategoryTotals(
            total_revenue=100000.0,
            cost_of_goods_sold=60000.0,
            operating_expenses=50000.0,  # Operating loss
        )
        engine = RatioEngine(totals)
        result = engine.calculate_operating_margin()

        assert result.is_calculable is True
        # (100,000 - 60,000 - 50,000) / 100,000 * 100 = -10%
        assert result.value == pytest.approx(-10.0, rel=0.1)
        assert result.threshold_status == "below_threshold"
        assert "loss" in result.interpretation.lower()

    def test_operating_margin_zero_revenue(self, zero_values_totals):
        """Test operating margin when revenue is zero."""
        engine = RatioEngine(zero_values_totals)
        result = engine.calculate_operating_margin()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"

    def test_operating_margin_service_company(self):
        """Test operating margin for service company (no COGS)."""
        totals = CategoryTotals(
            total_revenue=200000.0,
            cost_of_goods_sold=0.0,  # Service company
            operating_expenses=140000.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_operating_margin()

        assert result.is_calculable is True
        # (200,000 - 0 - 140,000) / 200,000 * 100 = 30%
        assert result.value == pytest.approx(30.0, rel=0.1)
        assert result.threshold_status == "above_threshold"


# =============================================================================
# RatioEngine Tests - Interest Coverage (Sprint 624)
# =============================================================================


class TestInterestCoverage:
    """Test cases for Interest Coverage Ratio (Sprint 624)."""

    def test_interest_coverage_adequate(self):
        """EBIT comfortably above 3.0x threshold."""
        totals = CategoryTotals(
            total_revenue=1_000_000.0,
            cost_of_goods_sold=400_000.0,
            operating_expenses=300_000.0,
            interest_expense=50_000.0,
        )
        result = RatioEngine(totals).calculate_interest_coverage()

        assert result.is_calculable is True
        assert result.name == "Interest Coverage"
        # EBIT = 1,000,000 - 400,000 - 300,000 = 300,000; 300,000 / 50,000 = 6.0x
        assert result.value == pytest.approx(6.0, rel=0.01)
        assert result.threshold_status == "above_threshold"
        assert result.display_value.endswith("x")

    def test_interest_coverage_watch_band(self):
        """1.5x <= coverage < 3.0x is the watch band."""
        totals = CategoryTotals(
            total_revenue=500_000.0,
            cost_of_goods_sold=200_000.0,
            operating_expenses=200_000.0,
            interest_expense=50_000.0,
        )
        result = RatioEngine(totals).calculate_interest_coverage()

        # EBIT = 100,000; coverage = 2.0x
        assert result.value == pytest.approx(2.0, rel=0.01)
        assert result.threshold_status == "at_threshold"
        assert "Watch" in result.interpretation

    def test_interest_coverage_elevated_risk(self):
        """Below 1.5x is elevated risk."""
        totals = CategoryTotals(
            total_revenue=500_000.0,
            cost_of_goods_sold=300_000.0,
            operating_expenses=180_000.0,
            interest_expense=20_000.0,
        )
        result = RatioEngine(totals).calculate_interest_coverage()

        # EBIT = 20,000; coverage = 1.0x
        assert result.value == pytest.approx(1.0, rel=0.01)
        assert result.threshold_status == "below_threshold"

    def test_interest_coverage_negative_ebit(self):
        """Operating loss flags below_threshold regardless of denominator."""
        totals = CategoryTotals(
            total_revenue=200_000.0,
            cost_of_goods_sold=150_000.0,
            operating_expenses=100_000.0,
            interest_expense=10_000.0,
        )
        result = RatioEngine(totals).calculate_interest_coverage()

        # EBIT = -50,000
        assert result.is_calculable is True
        assert result.threshold_status == "below_threshold"
        assert "loss" in result.interpretation.lower()

    def test_interest_coverage_zero_interest(self):
        """No interest-bearing debt returns N/A, not a divide-by-zero."""
        totals = CategoryTotals(
            total_revenue=500_000.0,
            cost_of_goods_sold=200_000.0,
            operating_expenses=150_000.0,
            interest_expense=0.0,
        )
        result = RatioEngine(totals).calculate_interest_coverage()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"
        assert "No interest-bearing debt" in result.interpretation

    def test_interest_coverage_derived_opex(self):
        """When operating_expenses is 0, derive from total_expenses - COGS.

        Sprint 681: fix double-count. ``total_expenses`` captures ALL
        expense-categorised accounts including interest, so the derived
        operating_exp (total_expenses - COGS) also includes interest.
        EBIT must subtract interest out — otherwise coverage is
        systematically under-stated by a factor equal to the interest load.

        Expected math:
          derived_opex = 400,000 - 200,000 = 200,000 (includes 40K interest)
          opex_for_ebit = 200,000 - 40,000 = 160,000 (operating-only)
          EBIT = 600,000 - 200,000 - 160,000 = 240,000
          coverage = 240,000 / 40,000 = 6.0x
        """
        totals = CategoryTotals(
            total_revenue=600_000.0,
            cost_of_goods_sold=200_000.0,
            total_expenses=400_000.0,
            interest_expense=40_000.0,
        )
        result = RatioEngine(totals).calculate_interest_coverage()
        assert result.value == pytest.approx(6.0, rel=0.01)
        assert result.threshold_status == "above_threshold"

    def test_interest_coverage_direct_opex_not_double_subtracted(self):
        """Sprint 681: when operating_expenses is explicitly populated
        (via extract_category_totals, which excludes interest by design),
        the ICR calculation must NOT subtract interest again. This test
        pins the "direct path" branch.

        Expected math (no double subtraction):
          operating_exp = 150,000 (interest-free, direct path)
          opex_for_ebit = 150,000 (unchanged)
          EBIT = 500,000 - 200,000 - 150,000 = 150,000
          coverage = 150,000 / 30,000 = 5.0x
        """
        totals = CategoryTotals(
            total_revenue=500_000.0,
            cost_of_goods_sold=200_000.0,
            operating_expenses=150_000.0,
            interest_expense=30_000.0,
        )
        result = RatioEngine(totals).calculate_interest_coverage()
        assert result.value == pytest.approx(5.0, rel=0.01)

    def test_interest_coverage_in_calculate_all_ratios(self):
        """Wired into calculate_all_ratios output."""
        totals = CategoryTotals(
            total_revenue=500_000.0,
            cost_of_goods_sold=200_000.0,
            operating_expenses=150_000.0,
            interest_expense=30_000.0,
        )
        ratios = RatioEngine(totals).calculate_all_ratios()
        assert "interest_coverage" in ratios
        assert ratios["interest_coverage"].is_calculable is True


class TestInterestExpenseExtraction:
    """Verify extract_category_totals routes interest accounts correctly."""

    def test_interest_expense_extracted_from_tb(self):
        """Interest expense accounts populate CategoryTotals.interest_expense."""
        from ratio_engine import extract_category_totals

        balances = {
            "Interest Expense": {"debit": 50_000, "credit": 0},
            "Salaries Expense": {"debit": 200_000, "credit": 0},
        }
        classified = {
            "Interest Expense": "expense",
            "Salaries Expense": "expense",
        }
        totals = extract_category_totals(balances, classified)
        assert totals.interest_expense == 50_000
        assert totals.total_expenses == 250_000

    def test_interest_income_not_treated_as_expense(self):
        """Account containing 'interest income' must not flow into interest_expense."""
        from ratio_engine import extract_category_totals

        balances = {
            "Interest Income": {"debit": 0, "credit": 5_000},
        }
        classified = {"Interest Income": "revenue"}
        totals = extract_category_totals(balances, classified)
        assert totals.interest_expense == 0


# =============================================================================
# RatioEngine Tests - Return on Assets (Sprint 27)
# =============================================================================


class TestSprint681AverageBalance:
    """Sprint 681: ROA / ROE with optional prior-period totals compute
    using the textbook (beginning + ending) / 2 average-balance formula.

    Falls back to ending-balance with a disclosure note when prior is
    absent (backward-compatible with existing callers).
    """

    def test_roa_uses_average_when_prior_supplied(self):
        """With prior totals, ROA denominator should be the average of
        beginning + ending total assets."""
        current = CategoryTotals(
            total_revenue=500000.0,
            total_expenses=350000.0,
            total_assets=1_200_000.0,
        )
        prior = CategoryTotals(total_assets=800_000.0)
        # Net Income = 150K. Average assets = (800K + 1.2M) / 2 = 1.0M.
        # ROA = 150K / 1.0M = 15.0%
        engine = RatioEngine(current, prior_period_totals=prior)
        result = engine.calculate_return_on_assets()
        assert result.value == pytest.approx(15.0, rel=0.01)
        # Disclosure note should NOT appear when average was used.
        assert "ending total assets" not in result.interpretation

    def test_roa_falls_back_to_ending_without_prior(self):
        """Without prior totals, ROA uses ending assets + attaches disclosure."""
        current = CategoryTotals(
            total_revenue=500000.0,
            total_expenses=350000.0,
            total_assets=1_200_000.0,
        )
        engine = RatioEngine(current)  # no prior
        result = engine.calculate_return_on_assets()
        # 150K / 1.2M = 12.5%
        assert result.value == pytest.approx(12.5, rel=0.01)
        assert "ending total assets" in result.interpretation
        assert "prior-period" in result.interpretation

    def test_roe_uses_average_when_prior_supplied(self):
        current = CategoryTotals(
            total_revenue=500000.0,
            total_expenses=350000.0,
            total_equity=800_000.0,
        )
        prior = CategoryTotals(total_equity=600_000.0)
        # Net Income = 150K. Average equity = 700K. ROE = 21.4%
        engine = RatioEngine(current, prior_period_totals=prior)
        result = engine.calculate_return_on_equity()
        assert result.value == pytest.approx(21.4, rel=0.01)
        assert "ending equity" not in result.interpretation

    def test_roe_partial_prior_falls_back(self):
        """If prior_totals is supplied but prior equity is 0 / missing,
        fall back to ending equity (matches the 'no prior' path)."""
        current = CategoryTotals(
            total_revenue=500000.0,
            total_expenses=350000.0,
            total_equity=800_000.0,
        )
        prior = CategoryTotals()  # all zeros
        engine = RatioEngine(current, prior_period_totals=prior)
        result = engine.calculate_return_on_equity()
        # 150K / 800K = 18.75%
        assert result.value == pytest.approx(18.75, rel=0.01)
        assert "ending equity" in result.interpretation

    def test_dupont_verification_matches_with_isclose(self):
        """Sprint 681: DuPont verification_matches must use math.isclose,
        not a fixed 1e-4 absolute tolerance. Under realistic conditions
        the decomposition should always verify."""
        current = CategoryTotals(
            total_revenue=1_000_000.0,
            total_expenses=800_000.0,
            total_assets=1_500_000.0,
            total_equity=500_000.0,
        )
        result = RatioEngine(current).calculate_dupont()
        assert result is not None
        # Under the old absolute-tolerance check, large ROE values could
        # produce false negatives due to float noise. With math.isclose
        # (rel_tol=1e-6), legitimate decompositions always verify.
        assert result.verification_matches is True


class TestReturnOnAssets:
    """Test cases for Return on Assets (ROA) calculation (Sprint 27)."""

    def test_roa_excellent(self, healthy_company_totals):
        """Test ROA for a company with excellent asset utilization."""
        engine = RatioEngine(healthy_company_totals)
        result = engine.calculate_return_on_assets()

        assert result.is_calculable is True
        assert result.name == "Return on Assets"
        # Net Income = 500,000 - 350,000 = 150,000
        # ROA = 150,000 / 1,000,000 * 100 = 15%
        assert result.value == pytest.approx(15.0, rel=0.1)
        assert result.threshold_status == "above_threshold"
        assert "Excellent" in result.interpretation

    def test_roa_strong(self):
        """Test ROA at strong threshold."""
        totals = CategoryTotals(
            total_assets=1000000.0,
            total_revenue=500000.0,
            total_expenses=400000.0,  # Net Income = 100,000 -> 10% ROA
        )
        engine = RatioEngine(totals)
        result = engine.calculate_return_on_assets()

        assert result.is_calculable is True
        assert result.value == pytest.approx(10.0, rel=0.1)
        assert result.threshold_status == "above_threshold"
        assert "Strong" in result.interpretation

    def test_roa_adequate(self):
        """Test ROA at adequate threshold."""
        totals = CategoryTotals(
            total_assets=1000000.0,
            total_revenue=500000.0,
            total_expenses=450000.0,  # Net Income = 50,000 -> 5% ROA
        )
        engine = RatioEngine(totals)
        result = engine.calculate_return_on_assets()

        assert result.is_calculable is True
        assert result.value == pytest.approx(5.0, rel=0.1)
        assert result.threshold_status == "above_threshold"

    def test_roa_low(self):
        """Test ROA when asset efficiency is low."""
        totals = CategoryTotals(
            total_assets=1000000.0,
            total_revenue=500000.0,
            total_expenses=480000.0,  # Net Income = 20,000 -> 2% ROA
        )
        engine = RatioEngine(totals)
        result = engine.calculate_return_on_assets()

        assert result.is_calculable is True
        assert result.value == pytest.approx(2.0, rel=0.1)
        assert result.threshold_status == "at_threshold"

    def test_roa_negative(self):
        """Test ROA when company is generating losses."""
        totals = CategoryTotals(
            total_assets=1000000.0,
            total_revenue=500000.0,
            total_expenses=600000.0,  # Net Loss = -100,000 -> -10% ROA
        )
        engine = RatioEngine(totals)
        result = engine.calculate_return_on_assets()

        assert result.is_calculable is True
        assert result.value == pytest.approx(-10.0, rel=0.1)
        assert result.threshold_status == "below_threshold"
        assert "losses" in result.interpretation.lower()

    def test_roa_zero_assets(self):
        """Test ROA when total assets is zero."""
        totals = CategoryTotals(
            total_assets=0.0,
            total_revenue=100000.0,
            total_expenses=80000.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_return_on_assets()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"
        assert "No assets" in result.interpretation


# =============================================================================
# RatioEngine Tests - Return on Equity (Sprint 27)
# =============================================================================


class TestReturnOnEquity:
    """Test cases for Return on Equity (ROE) calculation (Sprint 27)."""

    def test_roe_excellent(self, healthy_company_totals):
        """Test ROE for a company with excellent shareholder returns."""
        engine = RatioEngine(healthy_company_totals)
        result = engine.calculate_return_on_equity()

        assert result.is_calculable is True
        assert result.name == "Return on Equity"
        # Net Income = 500,000 - 350,000 = 150,000
        # ROE = 150,000 / 700,000 * 100 = 21.4%
        assert result.value == pytest.approx(21.4, rel=0.1)
        assert result.threshold_status == "above_threshold"
        assert "Excellent" in result.interpretation

    def test_roe_strong(self):
        """Test ROE at strong threshold."""
        totals = CategoryTotals(
            total_equity=500000.0,
            total_revenue=400000.0,
            total_expenses=325000.0,  # Net Income = 75,000 -> 15% ROE
        )
        engine = RatioEngine(totals)
        result = engine.calculate_return_on_equity()

        assert result.is_calculable is True
        assert result.value == pytest.approx(15.0, rel=0.1)
        assert result.threshold_status == "above_threshold"
        assert "Strong" in result.interpretation

    def test_roe_adequate(self):
        """Test ROE at adequate threshold."""
        totals = CategoryTotals(
            total_equity=500000.0,
            total_revenue=400000.0,
            total_expenses=350000.0,  # Net Income = 50,000 -> 10% ROE
        )
        engine = RatioEngine(totals)
        result = engine.calculate_return_on_equity()

        assert result.is_calculable is True
        assert result.value == pytest.approx(10.0, rel=0.1)
        assert result.threshold_status == "above_threshold"

    def test_roe_below_average(self):
        """Test ROE when returns are below average."""
        totals = CategoryTotals(
            total_equity=500000.0,
            total_revenue=400000.0,
            total_expenses=380000.0,  # Net Income = 20,000 -> 4% ROE
        )
        engine = RatioEngine(totals)
        result = engine.calculate_return_on_equity()

        assert result.is_calculable is True
        assert result.value == pytest.approx(4.0, rel=0.1)
        assert result.threshold_status == "at_threshold"

    def test_roe_negative(self):
        """Test ROE when company is generating losses."""
        totals = CategoryTotals(
            total_equity=500000.0,
            total_revenue=400000.0,
            total_expenses=500000.0,  # Net Loss = -100,000 -> -20% ROE
        )
        engine = RatioEngine(totals)
        result = engine.calculate_return_on_equity()

        assert result.is_calculable is True
        assert result.value == pytest.approx(-20.0, rel=0.1)
        assert result.threshold_status == "below_threshold"
        assert "losses" in result.interpretation.lower()

    def test_roe_zero_equity(self, zero_values_totals):
        """Test ROE when equity is zero."""
        engine = RatioEngine(zero_values_totals)
        result = engine.calculate_return_on_equity()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"
        assert "No equity" in result.interpretation

    def test_roe_negative_equity_with_loss(self, negative_equity_totals):
        """Test ROE when equity is negative (technical insolvency)."""
        engine = RatioEngine(negative_equity_totals)
        result = engine.calculate_return_on_equity()

        assert result.is_calculable is True
        # With negative equity, interpretation changes
        assert result.threshold_status == "below_threshold"


# =============================================================================
# RatioEngine Tests - Days Sales Outstanding (DSO) - Sprint 53
# =============================================================================


class TestDaysSalesOutstanding:
    """Test cases for DSO ratio calculation."""

    def test_dso_healthy_collection(self):
        """Test DSO with good collection period."""
        totals = CategoryTotals(
            total_assets=500000,
            current_assets=200000,
            accounts_receivable=41096,  # ~30 days of revenue
            total_revenue=500000,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_dso()

        assert result.is_calculable is True
        assert result.value is not None
        assert result.value == pytest.approx(30, rel=0.1)
        assert "days" in result.display_value
        assert result.threshold_status == "above_threshold"

    def test_dso_warning_level(self):
        """Test DSO with extended collection period."""
        totals = CategoryTotals(
            total_assets=500000,
            current_assets=200000,
            accounts_receivable=82192,  # ~60 days of revenue
            total_revenue=500000,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_dso()

        assert result.is_calculable is True
        assert result.value == pytest.approx(60, rel=0.1)
        assert result.threshold_status == "at_threshold"

    def test_dso_concern_level(self):
        """Test DSO with very slow collection."""
        totals = CategoryTotals(
            total_assets=500000,
            current_assets=200000,
            accounts_receivable=150000,  # ~109.5 days of revenue
            total_revenue=500000,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_dso()

        assert result.is_calculable is True
        assert result.value > 90
        assert result.threshold_status == "below_threshold"

    def test_dso_no_revenue(self):
        """Test DSO when revenue is zero."""
        totals = CategoryTotals(
            total_assets=100000,
            accounts_receivable=50000,
            total_revenue=0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_dso()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"
        assert "No revenue" in result.interpretation

    def test_dso_no_receivables(self):
        """Test DSO when accounts receivable is zero."""
        totals = CategoryTotals(
            total_assets=100000,
            accounts_receivable=0,
            total_revenue=500000,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_dso()

        assert result.is_calculable is True
        assert result.value == 0.0
        assert "cash basis" in result.interpretation.lower()
        assert result.threshold_status == "above_threshold"

    def test_dso_formula_accuracy(self):
        """Test DSO formula: (AR / Revenue) x 365."""
        totals = CategoryTotals(
            accounts_receivable=100000,
            total_revenue=1000000,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_dso()

        # Expected: (100000 / 1000000) x 365 = 36.5 days
        assert result.value == pytest.approx(36.5, rel=0.01)


# =============================================================================
# RatioEngine Tests - calculate_all_ratios
# =============================================================================


class TestCalculateAllRatios:
    """Test cases for the combined ratio calculation method."""

    def test_calculate_all_returns_all_ratios(self, healthy_company_totals):
        """Test that calculate_all_ratios returns all eight ratios (Sprint 27)."""
        engine = RatioEngine(healthy_company_totals)
        ratios = engine.calculate_all_ratios()

        assert "current_ratio" in ratios
        assert "quick_ratio" in ratios
        assert "debt_to_equity" in ratios
        assert "gross_margin" in ratios
        assert "net_profit_margin" in ratios  # Sprint 26
        assert "operating_margin" in ratios  # Sprint 26
        assert "interest_coverage" in ratios  # Sprint 624
        assert "return_on_assets" in ratios  # Sprint 27
        assert "return_on_equity" in ratios  # Sprint 27
        assert "dso" in ratios  # Sprint 53
        assert "dpo" in ratios  # Sprint 293
        assert "dio" in ratios  # Sprint 293
        assert "ccc" in ratios  # Sprint 293
        assert "equity_ratio" in ratios  # Sprint 449
        assert "long_term_debt_ratio" in ratios  # Sprint 449
        assert "asset_turnover" in ratios  # Sprint 449
        assert "inventory_turnover" in ratios  # Sprint 449
        assert "receivables_turnover" in ratios  # Sprint 449
        assert len(ratios) == 18  # Sprint 624: 18 ratios (added interest_coverage)

    def test_calculate_all_returns_ratio_results(self, healthy_company_totals):
        """Test that each ratio is a RatioResult instance."""
        engine = RatioEngine(healthy_company_totals)
        ratios = engine.calculate_all_ratios()

        for key, ratio in ratios.items():
            assert isinstance(ratio, RatioResult)

    def test_to_dict_serialization(self, healthy_company_totals):
        """Test that to_dict produces serializable output."""
        engine = RatioEngine(healthy_company_totals)
        result = engine.to_dict()

        assert isinstance(result, dict)
        assert len(result) == 18  # Sprint 624: 18 ratios (added interest_coverage)
        for key, ratio_dict in result.items():
            assert isinstance(ratio_dict, dict)
            assert "name" in ratio_dict
            assert "value" in ratio_dict
            assert "display_value" in ratio_dict
            assert "is_calculable" in ratio_dict
            assert "interpretation" in ratio_dict
            assert "threshold_status" in ratio_dict


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_numbers(self):
        """Test ratios with very large numbers."""
        totals = CategoryTotals(
            total_assets=1_000_000_000_000.0,  # 1 trillion
            current_assets=500_000_000_000.0,
            current_liabilities=250_000_000_000.0,
            total_liabilities=400_000_000_000.0,
            total_equity=600_000_000_000.0,
            total_revenue=200_000_000_000.0,
            cost_of_goods_sold=100_000_000_000.0,
            total_expenses=180_000_000_000.0,
            inventory=50_000_000_000.0,
            accounts_receivable=30_000_000_000.0,
            accounts_payable=20_000_000_000.0,
            interest_expense=10_000_000_000.0,  # Sprint 624
        )
        engine = RatioEngine(totals)
        ratios = engine.calculate_all_ratios()

        # All ratios should still be calculable
        assert all(r.is_calculable for r in ratios.values())
        assert ratios["current_ratio"].value == pytest.approx(2.0, rel=0.01)

    def test_very_small_numbers(self):
        """Test ratios with very small numbers."""
        totals = CategoryTotals(
            total_assets=1.00,  # Sprint 27: needed for ROA
            current_assets=0.50,
            current_liabilities=0.25,
            total_liabilities=0.30,
            total_equity=0.20,
            total_revenue=1.00,
            cost_of_goods_sold=0.40,
            total_expenses=0.60,  # Sprint 27: needed for ROA/ROE
            inventory=0.10,
            accounts_receivable=0.05,
            accounts_payable=0.03,
            interest_expense=0.02,  # Sprint 624
        )
        engine = RatioEngine(totals)
        ratios = engine.calculate_all_ratios()

        assert all(r.is_calculable for r in ratios.values())
        assert ratios["current_ratio"].value == pytest.approx(2.0, rel=0.01)

    def test_none_values_in_totals(self):
        """Test that CategoryTotals handles initialization correctly."""
        # CategoryTotals uses default values, not None
        totals = CategoryTotals()
        engine = RatioEngine(totals)

        # Zero denominators should result in N/A ratios
        cr = engine.calculate_current_ratio()
        assert cr.is_calculable is False

    def test_ratio_result_to_dict(self, healthy_company_totals):
        """Test RatioResult serialization."""
        engine = RatioEngine(healthy_company_totals)
        result = engine.calculate_current_ratio()
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["name"] == "Current Ratio"
        assert result_dict["is_calculable"] is True
        assert isinstance(result_dict["value"], float)

    def test_variance_result_to_dict(self):
        """Test VarianceResult serialization."""
        current = CategoryTotals(total_assets=120000.0)
        previous = CategoryTotals(total_assets=100000.0)

        analyzer = VarianceAnalyzer(current, previous)
        result = analyzer.to_dict()

        assert isinstance(result, dict)
        assert "total_assets" in result
        assert result["total_assets"]["direction"] == "positive"


# =============================================================================
# Sprint 241: Financial Calculation Edge Cases
# =============================================================================


class TestFinancialEdgeCases:
    """Sprint 241: Targeted edge case tests for financial calculations."""

    def test_extreme_debt_to_equity_trillion_over_one_dollar(self):
        """1T liabilities / $1 equity — verify concern status, no overflow."""
        totals = CategoryTotals(
            total_liabilities=1_000_000_000_000.0,
            total_equity=1.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_debt_to_equity()

        assert result.is_calculable is True
        assert result.value == 1_000_000_000_000.0
        assert result.threshold_status == "below_threshold"
        assert "High financial leverage" in result.interpretation

    def test_ratio_denominator_near_epsilon(self):
        """Current liabilities at 1e-10 — still calculable, extreme ratio."""
        totals = CategoryTotals(
            current_assets=100_000.0,
            current_liabilities=1e-10,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_current_ratio()

        assert result.is_calculable is True
        assert result.value is not None
        # Ratio is astronomically large but should not error
        assert result.value > 1_000_000

    def test_operating_margin_negative_derived_opex(self):
        """COGS > total_expenses in malformed TB — should be not calculable.

        Sprint 492: Negative derived opex (total_expenses < COGS) produces
        economically invalid margins. Now returns N/A instead.
        """
        totals = CategoryTotals(
            total_revenue=500_000.0,
            cost_of_goods_sold=200_000.0,
            total_expenses=95_000.0,  # COGS > total_expenses (malformed)
            operating_expenses=0.0,  # Forces fallback derivation
        )
        engine = RatioEngine(totals)
        result = engine.calculate_operating_margin()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"
        assert "Unable to derive" in result.interpretation

    def test_both_numerator_and_denominator_zero_current_ratio(self):
        """Both current_assets=0 and current_liabilities=0 — N/A, not 0/0."""
        totals = CategoryTotals(
            current_assets=0.0,
            current_liabilities=0.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_current_ratio()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"
        assert result.threshold_status == "neutral"

    def test_all_zero_calculate_all_ratios(self):
        """All-zero totals — all ratios should be N/A, no crashes."""
        totals = CategoryTotals()
        engine = RatioEngine(totals)
        ratios = engine.calculate_all_ratios()

        for name, result in ratios.items():
            assert result.is_calculable is False, f"{name} should not be calculable with all zeros"
            assert result.value is None, f"{name} should have None value"


# =============================================================================
# Sprint 492: Formula Consistency & Efficiency Tests
# =============================================================================


class TestOperatingMarginMalformedInputs:
    """Sprint 492: Edge cases for operating margin derivation."""

    def test_zero_total_expenses_with_revenue_and_cogs(self):
        """total_expenses=0 with COGS > 0: can't derive opex → N/A."""
        totals = CategoryTotals(
            total_revenue=500_000.0,
            cost_of_goods_sold=200_000.0,
            total_expenses=0.0,
            operating_expenses=0.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_operating_margin()
        assert result.is_calculable is False
        assert "Unable to derive" in result.interpretation

    def test_zero_total_expenses_zero_cogs(self):
        """total_expenses=0, COGS=0, no explicit opex: can't derive → N/A."""
        totals = CategoryTotals(
            total_revenue=500_000.0,
            cost_of_goods_sold=0.0,
            total_expenses=0.0,
            operating_expenses=0.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_operating_margin()
        assert result.is_calculable is False

    def test_valid_derivation_still_works(self):
        """Normal fallback derivation (total_expenses > COGS) still works."""
        totals = CategoryTotals(
            total_revenue=500_000.0,
            cost_of_goods_sold=200_000.0,
            total_expenses=350_000.0,  # 150k opex derived
            operating_expenses=0.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_operating_margin()
        assert result.is_calculable is True
        # (500k - 200k - 150k) / 500k * 100 = 30%
        assert result.value == pytest.approx(30.0, rel=0.1)

    def test_explicit_opex_bypasses_derivation(self):
        """When operating_expenses > 0, derivation path is not used."""
        totals = CategoryTotals(
            total_revenue=500_000.0,
            cost_of_goods_sold=200_000.0,
            total_expenses=50_000.0,  # Malformed, but irrelevant
            operating_expenses=100_000.0,  # Explicit opex → used directly
        )
        engine = RatioEngine(totals)
        result = engine.calculate_operating_margin()
        assert result.is_calculable is True
        # (500k - 200k - 100k) / 500k * 100 = 40%
        assert result.value == pytest.approx(40.0, rel=0.1)


class TestCCCNonRedundantComputation:
    """Sprint 492: Verify calculate_all_ratios doesn't double-compute DSO/DPO/DIO."""

    def test_ccc_uses_precomputed_components(self):
        """CCC in calculate_all_ratios matches standalone CCC calculation."""
        totals = CategoryTotals(
            accounts_receivable=20_000,
            inventory=15_000,
            accounts_payable=10_000,
            total_revenue=200_000,
            cost_of_goods_sold=100_000,
        )
        engine = RatioEngine(totals)
        all_ratios = engine.calculate_all_ratios()

        # CCC from calculate_all_ratios should equal standalone calculation
        standalone_ccc = engine.calculate_ccc()
        assert all_ratios["ccc"].value == standalone_ccc.value

        # Individual components should also match
        assert all_ratios["dso"].value == engine.calculate_dso().value
        assert all_ratios["dpo"].value == engine.calculate_dpo().value
        assert all_ratios["dio"].value == engine.calculate_dio().value

    def test_ccc_accepts_precomputed_results(self):
        """calculate_ccc with precomputed components produces same result."""
        totals = CategoryTotals(
            accounts_receivable=20_000,
            inventory=15_000,
            accounts_payable=10_000,
            total_revenue=200_000,
            cost_of_goods_sold=100_000,
        )
        engine = RatioEngine(totals)
        dso = engine.calculate_dso()
        dpo = engine.calculate_dpo()
        dio = engine.calculate_dio()

        precomputed = engine.calculate_ccc(precomputed_dso=dso, precomputed_dpo=dpo, precomputed_dio=dio)
        standalone = engine.calculate_ccc()

        assert precomputed.value == standalone.value
        assert precomputed.is_calculable == standalone.is_calculable


class TestReciprocalMetricZeroCases:
    """Sprint 492: Verify consistent zero-denominator semantics for reciprocal pairs."""

    def test_dso_zero_ar_is_calculable(self):
        """DSO with AR=0: calculable, value=0 (no receivables to collect)."""
        totals = CategoryTotals(accounts_receivable=0, total_revenue=100_000)
        engine = RatioEngine(totals)
        result = engine.calculate_dso()
        assert result.is_calculable is True
        assert result.value == 0.0

    def test_receivables_turnover_zero_ar_not_calculable(self):
        """Receivables Turnover with AR=0: not calculable (division by zero)."""
        totals = CategoryTotals(accounts_receivable=0, total_revenue=100_000)
        engine = RatioEngine(totals)
        result = engine.calculate_receivables_turnover()
        assert result.is_calculable is False
        assert result.value is None

    def test_dio_zero_inventory_is_calculable(self):
        """DIO with inventory=0: calculable, value=0 (no inventory to hold)."""
        totals = CategoryTotals(inventory=0, cost_of_goods_sold=100_000)
        engine = RatioEngine(totals)
        result = engine.calculate_dio()
        assert result.is_calculable is True
        assert result.value == 0.0

    def test_inventory_turnover_zero_inventory_not_calculable(self):
        """Inventory Turnover with inventory=0: not calculable (division by zero)."""
        totals = CategoryTotals(inventory=0, cost_of_goods_sold=100_000)
        engine = RatioEngine(totals)
        result = engine.calculate_inventory_turnover()
        assert result.is_calculable is False
        assert result.value is None

    def test_dso_reciprocal_of_receivables_turnover(self):
        """DSO × Receivables Turnover ≈ 365 when both calculable."""
        totals = CategoryTotals(accounts_receivable=20_000, total_revenue=200_000)
        engine = RatioEngine(totals)
        dso = engine.calculate_dso()
        rt = engine.calculate_receivables_turnover()
        assert dso.is_calculable and rt.is_calculable
        assert dso.value * rt.value == pytest.approx(365, rel=0.01)

    def test_dio_reciprocal_of_inventory_turnover(self):
        """DIO × Inventory Turnover ≈ 365 when both calculable."""
        totals = CategoryTotals(inventory=15_000, cost_of_goods_sold=100_000)
        engine = RatioEngine(totals)
        dio = engine.calculate_dio()
        it = engine.calculate_inventory_turnover()
        assert dio.is_calculable and it.is_calculable
        assert dio.value * it.value == pytest.approx(365, rel=0.01)

    def test_zero_revenue_both_dso_and_rt_not_calculable(self):
        """Zero revenue: both DSO and Receivables Turnover should be N/A."""
        totals = CategoryTotals(accounts_receivable=20_000, total_revenue=0)
        engine = RatioEngine(totals)
        assert engine.calculate_dso().is_calculable is False
        assert engine.calculate_receivables_turnover().is_calculable is False

    def test_zero_cogs_both_dio_and_it_not_calculable(self):
        """Zero COGS: both DIO and Inventory Turnover should be N/A."""
        totals = CategoryTotals(inventory=15_000, cost_of_goods_sold=0)
        engine = RatioEngine(totals)
        assert engine.calculate_dio().is_calculable is False
        assert engine.calculate_inventory_turnover().is_calculable is False
