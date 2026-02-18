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
        assert result.health_status == "healthy"
        assert "Strong liquidity" in result.interpretation

    def test_current_ratio_struggling_company(self, struggling_company_totals):
        """Test current ratio for a company with weak liquidity."""
        engine = RatioEngine(struggling_company_totals)
        result = engine.calculate_current_ratio()

        assert result.is_calculable is True
        # 50,000 / 200,000 = 0.25
        assert result.value == pytest.approx(0.25, rel=0.01)
        assert result.health_status == "concern"
        assert "liquidity risk" in result.interpretation.lower()

    def test_current_ratio_zero_liabilities(self, zero_values_totals):
        """Test current ratio when current liabilities are zero."""
        engine = RatioEngine(zero_values_totals)
        result = engine.calculate_current_ratio()

        assert result.is_calculable is False
        assert result.value is None
        assert result.display_value == "N/A"
        assert "Cannot calculate" in result.interpretation
        assert result.health_status == "neutral"

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
        assert result.health_status == "healthy"
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
        assert result.health_status == "warning"


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
        assert result.health_status == "healthy"

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
        assert result.health_status == "concern"

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
        assert result.health_status == "healthy"


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
        assert result.health_status == "healthy"
        assert "Conservative" in result.interpretation

    def test_debt_to_equity_high_leverage(self, struggling_company_totals):
        """Test D/E for a highly leveraged company."""
        engine = RatioEngine(struggling_company_totals)
        result = engine.calculate_debt_to_equity()

        assert result.is_calculable is True
        # 450,000 / 50,000 = 9.0
        assert result.value == pytest.approx(9.0, rel=0.01)
        assert result.health_status == "concern"
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
        assert result.health_status == "healthy"


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
        assert result.health_status == "healthy"
        assert "Strong" in result.interpretation

    def test_gross_margin_low(self, struggling_company_totals):
        """Test gross margin for a company with thin margins."""
        engine = RatioEngine(struggling_company_totals)
        result = engine.calculate_gross_margin()

        assert result.is_calculable is True
        # (100,000 - 90,000) / 100,000 * 100 = 10%
        assert result.value == pytest.approx(10.0, rel=0.1)
        assert result.health_status == "concern"
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
        assert result.health_status == "healthy"
        assert "Excellent" in result.interpretation

    def test_net_profit_margin_low(self, struggling_company_totals):
        """Test net profit margin for a company with thin profits."""
        engine = RatioEngine(struggling_company_totals)
        result = engine.calculate_net_profit_margin()

        assert result.is_calculable is True
        # (100,000 - 95,000) / 100,000 * 100 = 5%
        assert result.value == pytest.approx(5.0, rel=0.1)
        assert result.health_status == "warning"

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
        assert result.health_status == "concern"
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
        assert result.health_status == "warning"

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
        assert result.health_status == "healthy"


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
        assert result.health_status == "healthy"

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
        assert result.health_status == "warning"

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
        assert result.health_status == "concern"
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
        assert result.health_status == "healthy"


# =============================================================================
# RatioEngine Tests - Return on Assets (Sprint 27)
# =============================================================================

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
        assert result.health_status == "healthy"
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
        assert result.health_status == "healthy"
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
        assert result.health_status == "healthy"

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
        assert result.health_status == "warning"

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
        assert result.health_status == "concern"
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
        assert result.health_status == "healthy"
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
        assert result.health_status == "healthy"
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
        assert result.health_status == "healthy"

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
        assert result.health_status == "warning"

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
        assert result.health_status == "concern"
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
        assert result.health_status == "concern"


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
        assert result.health_status == "healthy"

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
        assert result.health_status == "warning"

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
        assert result.health_status == "concern"

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
        assert result.health_status == "healthy"

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
        assert "return_on_assets" in ratios  # Sprint 27
        assert "return_on_equity" in ratios  # Sprint 27
        assert "dso" in ratios  # Sprint 53
        assert "dpo" in ratios  # Sprint 293
        assert "dio" in ratios  # Sprint 293
        assert "ccc" in ratios  # Sprint 293
        assert len(ratios) == 12  # Sprint 293: 12 ratios (added DPO, DIO, CCC)

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
        assert len(result) == 12  # Sprint 293: 12 ratios (added DPO, DIO, CCC)
        for key, ratio_dict in result.items():
            assert isinstance(ratio_dict, dict)
            assert "name" in ratio_dict
            assert "value" in ratio_dict
            assert "display_value" in ratio_dict
            assert "is_calculable" in ratio_dict
            assert "interpretation" in ratio_dict
            assert "health_status" in ratio_dict


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
        assert result.health_status == "concern"
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
        """COGS > total_expenses in malformed TB — derived opex is negative.

        operating_exp = total_expenses - COGS = 95000 - 200000 = -105000
        operating_income = revenue - COGS - operating_exp = 500000 - 200000 - (-105000) = 405000
        margin = 405000/500000 * 100 = 81%
        """
        totals = CategoryTotals(
            total_revenue=500_000.0,
            cost_of_goods_sold=200_000.0,
            total_expenses=95_000.0,  # COGS > total_expenses (malformed)
            operating_expenses=0.0,   # Forces fallback derivation
        )
        engine = RatioEngine(totals)
        result = engine.calculate_operating_margin()

        assert result.is_calculable is True
        # Should not crash — just returns whatever the math gives
        assert result.value is not None
        assert isinstance(result.value, float)

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
        assert result.health_status == "neutral"

    def test_all_zero_calculate_all_ratios(self):
        """All-zero totals — all ratios should be N/A, no crashes."""
        totals = CategoryTotals()
        engine = RatioEngine(totals)
        ratios = engine.calculate_all_ratios()

        for name, result in ratios.items():
            assert result.is_calculable is False, f"{name} should not be calculable with all zeros"
            assert result.value is None, f"{name} should have None value"
