"""Test suite for ratio_engine.py financial calculations."""

import pytest
from ratio_engine import (
    RatioEngine,
    RatioResult,
    CategoryTotals,
    CommonSizeAnalyzer,
    VarianceAnalyzer,
    VarianceResult,
    TrendDirection,
    extract_category_totals,
    calculate_analytics,
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
        assert len(ratios) == 8

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
        assert len(result) == 8  # Sprint 27: 8 ratios
        for key, ratio_dict in result.items():
            assert isinstance(ratio_dict, dict)
            assert "name" in ratio_dict
            assert "value" in ratio_dict
            assert "display_value" in ratio_dict
            assert "is_calculable" in ratio_dict
            assert "interpretation" in ratio_dict
            assert "health_status" in ratio_dict


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
