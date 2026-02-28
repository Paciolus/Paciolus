"""
Tests for industry-specific ratio calculations.

Sprint 35: Industry Ratio Foundation
Sprint 36: Industry Ratio Expansion (Professional Services)

Tests cover:
- ManufacturingRatioCalculator
- RetailRatioCalculator
- ProfessionalServicesRatioCalculator
- GenericIndustryCalculator
- Factory functions and industry mapping
"""

import pytest

from industry_ratios import (
    INDUSTRY_CALCULATOR_MAP,
    GenericIndustryCalculator,
    IndustryRatioResult,
    IndustryTotals,
    IndustryType,
    ManufacturingRatioCalculator,
    RetailRatioCalculator,
    calculate_industry_ratios,
    get_available_industries,
    get_industry_calculator,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def manufacturing_totals():
    """Sample manufacturing company totals."""
    return IndustryTotals(
        total_assets=1000000,
        current_assets=400000,
        inventory=200000,
        total_liabilities=400000,
        current_liabilities=150000,
        total_equity=600000,
        total_revenue=1200000,
        cost_of_goods_sold=800000,
        total_expenses=1000000,
        operating_expenses=150000,
    )


@pytest.fixture
def retail_totals():
    """Sample retail company totals."""
    return IndustryTotals(
        total_assets=500000,
        current_assets=300000,
        inventory=150000,
        total_liabilities=200000,
        current_liabilities=100000,
        total_equity=300000,
        total_revenue=1500000,
        cost_of_goods_sold=1000000,
        total_expenses=1300000,
        operating_expenses=250000,
    )


@pytest.fixture
def zero_inventory_totals():
    """Totals with zero inventory for edge case testing."""
    return IndustryTotals(
        total_assets=500000,
        current_assets=200000,
        inventory=0,
        total_revenue=600000,
        cost_of_goods_sold=400000,
    )


@pytest.fixture
def zero_cogs_totals():
    """Totals with zero COGS (service company)."""
    return IndustryTotals(
        total_assets=500000,
        current_assets=200000,
        inventory=100000,
        total_revenue=600000,
        cost_of_goods_sold=0,
    )


# =============================================================================
# IndustryTotals Tests
# =============================================================================


class TestIndustryTotals:
    """Tests for IndustryTotals dataclass."""

    def test_to_dict(self, manufacturing_totals):
        """Test serialization to dictionary."""
        result = manufacturing_totals.to_dict()

        assert result["total_assets"] == 1000000
        assert result["inventory"] == 200000
        assert result["cost_of_goods_sold"] == 800000
        assert "average_inventory" in result

    def test_from_category_totals(self):
        """Test creating IndustryTotals from CategoryTotals dict."""
        category_dict = {
            "total_assets": 500000,
            "inventory": 100000,
            "cost_of_goods_sold": 300000,
        }

        result = IndustryTotals.from_category_totals(category_dict)

        assert result.total_assets == 500000
        assert result.inventory == 100000
        assert result.cost_of_goods_sold == 300000
        # Missing fields should default to 0
        assert result.total_equity == 0
        assert result.operating_expenses == 0

    def test_average_inventory_fallback(self, manufacturing_totals):
        """Test that average_inventory falls back to current inventory."""
        assert manufacturing_totals.average_inventory is None
        result = manufacturing_totals.to_dict()
        # Should use inventory value when average_inventory is None
        assert result["average_inventory"] == 200000


# =============================================================================
# ManufacturingRatioCalculator Tests
# =============================================================================


class TestManufacturingRatioCalculator:
    """Tests for manufacturing industry ratios."""

    def test_get_ratio_names(self, manufacturing_totals):
        """Test that ratio names are returned."""
        calc = ManufacturingRatioCalculator(manufacturing_totals)
        names = calc.get_ratio_names()

        assert "inventory_turnover" in names
        assert "days_inventory_outstanding" in names
        assert "asset_turnover" in names
        assert len(names) == 3

    def test_inventory_turnover_calculation(self, manufacturing_totals):
        """Test inventory turnover formula: COGS / Inventory."""
        calc = ManufacturingRatioCalculator(manufacturing_totals)
        result = calc.calculate_inventory_turnover()

        # 800000 / 200000 = 4.0
        assert result.is_calculable
        assert result.value == 4.0
        assert result.display_value == "4.00x"
        assert result.threshold_status == "above_threshold"
        assert result.industry == "Manufacturing"

    def test_inventory_turnover_zero_inventory(self, zero_inventory_totals):
        """Test inventory turnover with zero inventory."""
        calc = ManufacturingRatioCalculator(zero_inventory_totals)
        result = calc.calculate_inventory_turnover()

        assert not result.is_calculable
        assert result.value is None
        assert result.display_value == "N/A"
        assert "No inventory" in result.interpretation

    def test_inventory_turnover_zero_cogs(self, zero_cogs_totals):
        """Test inventory turnover with zero COGS."""
        calc = ManufacturingRatioCalculator(zero_cogs_totals)
        result = calc.calculate_inventory_turnover()

        assert not result.is_calculable
        assert result.value is None
        assert "No COGS" in result.interpretation

    def test_inventory_turnover_health_levels(self):
        """Test different health status thresholds."""
        # Excellent (>= 8)
        totals = IndustryTotals(inventory=100, cost_of_goods_sold=1000)
        result = ManufacturingRatioCalculator(totals).calculate_inventory_turnover()
        assert result.value == 10.0
        assert result.threshold_status == "above_threshold"
        assert "Excellent" in result.interpretation

        # Warning (2-4)
        totals = IndustryTotals(inventory=100, cost_of_goods_sold=300)
        result = ManufacturingRatioCalculator(totals).calculate_inventory_turnover()
        assert result.value == 3.0
        assert result.threshold_status == "at_threshold"

        # Concern (< 2)
        totals = IndustryTotals(inventory=100, cost_of_goods_sold=100)
        result = ManufacturingRatioCalculator(totals).calculate_inventory_turnover()
        assert result.value == 1.0
        assert result.threshold_status == "below_threshold"

    def test_days_inventory_outstanding(self, manufacturing_totals):
        """Test DIO formula: 365 / Inventory Turnover."""
        calc = ManufacturingRatioCalculator(manufacturing_totals)
        result = calc.calculate_days_inventory_outstanding()

        # Turnover = 4.0, DIO = 365 / 4 = 91.25
        assert result.is_calculable
        assert result.value == 91.2  # Rounded to 1 decimal
        assert "days" in result.display_value
        assert result.threshold_status == "at_threshold"  # 90-120 days

    def test_days_inventory_outstanding_excellent(self):
        """Test DIO with excellent turnover."""
        totals = IndustryTotals(inventory=100, cost_of_goods_sold=1200)  # 12x turnover
        calc = ManufacturingRatioCalculator(totals)
        result = calc.calculate_days_inventory_outstanding()

        # DIO = 365 / 12 = 30.4 days
        assert result.is_calculable
        assert result.value == 30.4
        assert result.threshold_status == "above_threshold"
        assert "very fast" in result.interpretation.lower()

    def test_asset_turnover(self, manufacturing_totals):
        """Test asset turnover: Revenue / Total Assets."""
        calc = ManufacturingRatioCalculator(manufacturing_totals)
        result = calc.calculate_asset_turnover()

        # 1200000 / 1000000 = 1.2
        assert result.is_calculable
        assert result.value == 1.2
        assert result.display_value == "1.20x"
        assert result.threshold_status == "above_threshold"

    def test_asset_turnover_zero_assets(self):
        """Test asset turnover with zero assets."""
        totals = IndustryTotals(total_assets=0, total_revenue=100000)
        calc = ManufacturingRatioCalculator(totals)
        result = calc.calculate_asset_turnover()

        assert not result.is_calculable
        assert result.value is None
        assert "No assets" in result.interpretation

    def test_asset_turnover_zero_revenue(self):
        """Test asset turnover with zero revenue."""
        totals = IndustryTotals(total_assets=100000, total_revenue=0)
        calc = ManufacturingRatioCalculator(totals)
        result = calc.calculate_asset_turnover()

        assert not result.is_calculable
        assert "No revenue" in result.interpretation

    def test_calculate_all(self, manufacturing_totals):
        """Test that calculate_all returns all ratios."""
        calc = ManufacturingRatioCalculator(manufacturing_totals)
        results = calc.calculate_all()

        assert "inventory_turnover" in results
        assert "days_inventory_outstanding" in results
        assert "asset_turnover" in results
        assert len(results) == 3

        # All should be IndustryRatioResult
        for result in results.values():
            assert isinstance(result, IndustryRatioResult)

    def test_to_dict_serialization(self, manufacturing_totals):
        """Test complete serialization."""
        calc = ManufacturingRatioCalculator(manufacturing_totals)
        result = calc.to_dict()

        assert result["industry"] == "Manufacturing"
        assert result["industry_type"] == "manufacturing"
        assert "ratios" in result
        assert len(result["ratios"]) == 3


# =============================================================================
# RetailRatioCalculator Tests
# =============================================================================


class TestRetailRatioCalculator:
    """Tests for retail industry ratios."""

    def test_get_ratio_names(self, retail_totals):
        """Test retail ratio names."""
        calc = RetailRatioCalculator(retail_totals)
        names = calc.get_ratio_names()

        assert "inventory_turnover" in names
        assert "gmroi" in names
        assert len(names) == 2

    def test_inventory_turnover_retail_benchmarks(self, retail_totals):
        """Test that retail uses higher benchmark thresholds."""
        calc = RetailRatioCalculator(retail_totals)
        result = calc.calculate_inventory_turnover()

        # 1000000 / 150000 = 6.67
        assert result.is_calculable
        assert result.value == 6.67
        # 6.67 is below retail benchmark of 8-12, so warning
        assert result.threshold_status == "at_threshold"
        assert "Retail benchmark" in result.benchmark_note

    def test_inventory_turnover_excellent_retail(self):
        """Test excellent retail turnover (>= 12)."""
        totals = IndustryTotals(inventory=100, cost_of_goods_sold=1500)
        calc = RetailRatioCalculator(totals)
        result = calc.calculate_inventory_turnover()

        assert result.value == 15.0
        assert result.threshold_status == "above_threshold"
        assert "Excellent" in result.interpretation

    def test_gmroi_calculation(self, retail_totals):
        """Test GMROI formula: (Revenue - COGS) / Inventory."""
        calc = RetailRatioCalculator(retail_totals)
        result = calc.calculate_gmroi()

        # Gross Margin = 1500000 - 1000000 = 500000
        # GMROI = 500000 / 150000 = 3.33
        assert result.is_calculable
        assert result.value == 3.33
        assert "$" in result.display_value  # GMROI shows as currency
        assert result.threshold_status == "above_threshold"

    def test_gmroi_zero_inventory(self, zero_inventory_totals):
        """Test GMROI with zero inventory."""
        calc = RetailRatioCalculator(zero_inventory_totals)
        result = calc.calculate_gmroi()

        assert not result.is_calculable
        assert result.value is None
        assert "No inventory" in result.interpretation

    def test_gmroi_marginal_return(self):
        """Test GMROI with marginal return (1.0-2.0)."""
        totals = IndustryTotals(
            inventory=200000,
            total_revenue=400000,
            cost_of_goods_sold=100000,
        )
        calc = RetailRatioCalculator(totals)
        result = calc.calculate_gmroi()

        # Gross margin = 300000, GMROI = 300000/200000 = 1.5
        assert result.value == 1.5
        assert result.threshold_status == "at_threshold"

    def test_gmroi_poor_return(self):
        """Test GMROI with poor return (< 1.0)."""
        totals = IndustryTotals(
            inventory=200000,
            total_revenue=250000,
            cost_of_goods_sold=150000,
        )
        calc = RetailRatioCalculator(totals)
        result = calc.calculate_gmroi()

        # Gross margin = 100000, GMROI = 100000/200000 = 0.5
        assert result.value == 0.5
        assert result.threshold_status == "below_threshold"

    def test_calculate_all(self, retail_totals):
        """Test calculate_all for retail."""
        calc = RetailRatioCalculator(retail_totals)
        results = calc.calculate_all()

        assert len(results) == 2
        assert "inventory_turnover" in results
        assert "gmroi" in results


# =============================================================================
# ProfessionalServicesRatioCalculator Tests
# =============================================================================


class TestProfessionalServicesRatioCalculator:
    """Tests for professional services industry ratios."""

    @pytest.fixture
    def services_totals(self):
        """Sample professional services company totals."""
        return IndustryTotals(
            total_assets=500000,
            total_revenue=2000000,
            total_expenses=1600000,
            employee_count=10,
            billable_hours=15000,
            total_hours=20000,
        )

    def test_get_ratio_names(self, services_totals):
        """Test professional services ratio names."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        calc = ProfessionalServicesRatioCalculator(services_totals)
        names = calc.get_ratio_names()

        assert "revenue_per_employee" in names
        assert "utilization_rate" in names
        assert "revenue_per_billable_hour" in names
        assert len(names) == 3

    def test_revenue_per_employee_calculation(self, services_totals):
        """Test revenue per employee formula."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        calc = ProfessionalServicesRatioCalculator(services_totals)
        result = calc.calculate_revenue_per_employee()

        # 2000000 / 10 = 200000
        assert result.is_calculable
        assert result.value == 200000
        assert "$200,000" in result.display_value
        assert result.threshold_status == "above_threshold"
        assert result.industry == "Professional Services"

    def test_revenue_per_employee_missing_data(self):
        """Test revenue per employee without employee count."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        totals = IndustryTotals(total_revenue=1000000, employee_count=None)
        calc = ProfessionalServicesRatioCalculator(totals)
        result = calc.calculate_revenue_per_employee()

        assert not result.is_calculable
        assert result.display_value == "Data Required"
        assert "employee_count" in result.interpretation.lower()
        assert result.threshold_status == "neutral"

    def test_revenue_per_employee_zero_employees(self):
        """Test revenue per employee with zero employees."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        totals = IndustryTotals(total_revenue=1000000, employee_count=0)
        calc = ProfessionalServicesRatioCalculator(totals)
        result = calc.calculate_revenue_per_employee()

        assert not result.is_calculable
        assert result.value is None
        assert "Zero employees" in result.interpretation

    def test_revenue_per_employee_health_levels(self):
        """Test different health status thresholds."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        # Excellent (>= 300000)
        totals = IndustryTotals(total_revenue=600000, employee_count=2)
        result = ProfessionalServicesRatioCalculator(totals).calculate_revenue_per_employee()
        assert result.value == 300000
        assert result.threshold_status == "above_threshold"
        assert "Excellent" in result.interpretation

        # Warning (50000-100000)
        totals = IndustryTotals(total_revenue=150000, employee_count=2)
        result = ProfessionalServicesRatioCalculator(totals).calculate_revenue_per_employee()
        assert result.value == 75000
        assert result.threshold_status == "at_threshold"

        # Concern (< 50000)
        totals = IndustryTotals(total_revenue=80000, employee_count=2)
        result = ProfessionalServicesRatioCalculator(totals).calculate_revenue_per_employee()
        assert result.value == 40000
        assert result.threshold_status == "below_threshold"

    def test_utilization_rate_calculation(self, services_totals):
        """Test utilization rate formula."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        calc = ProfessionalServicesRatioCalculator(services_totals)
        result = calc.calculate_utilization_rate()

        # 15000 / 20000 * 100 = 75%
        assert result.is_calculable
        assert result.value == 75.0
        assert "75.0%" in result.display_value
        assert result.threshold_status == "above_threshold"

    def test_utilization_rate_missing_data(self):
        """Test utilization rate without hours data."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        totals = IndustryTotals(billable_hours=None, total_hours=None)
        calc = ProfessionalServicesRatioCalculator(totals)
        result = calc.calculate_utilization_rate()

        assert not result.is_calculable
        assert result.display_value == "Data Required"
        assert "billable_hours" in result.interpretation.lower()

    def test_utilization_rate_zero_total_hours(self):
        """Test utilization rate with zero total hours."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        totals = IndustryTotals(billable_hours=100, total_hours=0)
        calc = ProfessionalServicesRatioCalculator(totals)
        result = calc.calculate_utilization_rate()

        assert not result.is_calculable
        assert "Zero total hours" in result.interpretation

    def test_utilization_rate_capped_at_100(self):
        """Test utilization rate is capped at 100%."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        # Data entry error: billable > total
        totals = IndustryTotals(billable_hours=150, total_hours=100)
        calc = ProfessionalServicesRatioCalculator(totals)
        result = calc.calculate_utilization_rate()

        assert result.is_calculable
        assert result.value == 100.0  # Capped

    def test_utilization_rate_health_levels(self):
        """Test utilization rate health thresholds."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        # Excellent (>= 85%)
        totals = IndustryTotals(billable_hours=90, total_hours=100)
        result = ProfessionalServicesRatioCalculator(totals).calculate_utilization_rate()
        assert result.value == 90.0
        assert result.threshold_status == "above_threshold"
        assert "Excellent" in result.interpretation

        # Warning (50-65%)
        totals = IndustryTotals(billable_hours=55, total_hours=100)
        result = ProfessionalServicesRatioCalculator(totals).calculate_utilization_rate()
        assert result.value == 55.0
        assert result.threshold_status == "at_threshold"

        # Concern (< 50%)
        totals = IndustryTotals(billable_hours=40, total_hours=100)
        result = ProfessionalServicesRatioCalculator(totals).calculate_utilization_rate()
        assert result.value == 40.0
        assert result.threshold_status == "below_threshold"

    def test_revenue_per_billable_hour_calculation(self, services_totals):
        """Test revenue per billable hour formula."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        calc = ProfessionalServicesRatioCalculator(services_totals)
        result = calc.calculate_revenue_per_billable_hour()

        # 2000000 / 15000 = 133.33
        assert result.is_calculable
        assert result.value == 133.33
        assert "$133.33/hr" in result.display_value
        assert result.threshold_status == "above_threshold"

    def test_revenue_per_billable_hour_missing_data(self):
        """Test revenue per billable hour without hours data."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        totals = IndustryTotals(total_revenue=1000000, billable_hours=None)
        calc = ProfessionalServicesRatioCalculator(totals)
        result = calc.calculate_revenue_per_billable_hour()

        assert not result.is_calculable
        assert result.display_value == "Data Required"

    def test_revenue_per_billable_hour_zero_hours(self):
        """Test revenue per billable hour with zero billable hours."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        totals = IndustryTotals(total_revenue=1000000, billable_hours=0)
        calc = ProfessionalServicesRatioCalculator(totals)
        result = calc.calculate_revenue_per_billable_hour()

        assert not result.is_calculable
        assert "Zero billable hours" in result.interpretation

    def test_calculate_all(self, services_totals):
        """Test calculate_all returns all ratios."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        calc = ProfessionalServicesRatioCalculator(services_totals)
        results = calc.calculate_all()

        assert len(results) == 3
        assert "revenue_per_employee" in results
        assert "utilization_rate" in results
        assert "revenue_per_billable_hour" in results

    def test_to_dict_serialization(self, services_totals):
        """Test complete serialization."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        calc = ProfessionalServicesRatioCalculator(services_totals)
        result = calc.to_dict()

        assert result["industry"] == "Professional Services"
        assert result["industry_type"] == "professional_services"
        assert "ratios" in result
        assert len(result["ratios"]) == 3


# =============================================================================
# GenericIndustryCalculator Tests
# =============================================================================


class TestGenericIndustryCalculator:
    """Tests for generic fallback calculator."""

    def test_default_industry_name(self):
        """Test default industry name is 'General'."""
        totals = IndustryTotals(total_assets=100000, total_revenue=150000)
        calc = GenericIndustryCalculator(totals)

        assert calc.industry_name == "General"

    def test_custom_industry_name(self):
        """Test custom industry name override."""
        totals = IndustryTotals(total_assets=100000, total_revenue=150000)
        calc = GenericIndustryCalculator(totals, industry_name="Hospitality")

        assert calc.industry_name == "Hospitality"

    def test_asset_turnover_only(self):
        """Test that generic calculator only provides asset turnover."""
        totals = IndustryTotals(total_assets=100000, total_revenue=150000)
        calc = GenericIndustryCalculator(totals)
        names = calc.get_ratio_names()

        assert names == ["asset_turnover"]

    def test_asset_turnover_calculation(self):
        """Test generic asset turnover."""
        totals = IndustryTotals(total_assets=100000, total_revenue=150000)
        calc = GenericIndustryCalculator(totals)
        result = calc.calculate_asset_turnover()

        assert result.is_calculable
        assert result.value == 1.5
        assert result.threshold_status == "neutral"  # Generic is neutral

    def test_asset_turnover_missing_data(self):
        """Test generic calculator with missing data."""
        totals = IndustryTotals(total_assets=0, total_revenue=0)
        calc = GenericIndustryCalculator(totals)
        result = calc.calculate_asset_turnover()

        assert not result.is_calculable
        assert result.value is None


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestFactoryFunctions:
    """Tests for factory functions and industry mapping."""

    def test_get_industry_calculator_manufacturing(self):
        """Test factory returns ManufacturingRatioCalculator."""
        totals = IndustryTotals()
        calc = get_industry_calculator("manufacturing", totals)

        assert isinstance(calc, ManufacturingRatioCalculator)

    def test_get_industry_calculator_retail(self):
        """Test factory returns RetailRatioCalculator."""
        totals = IndustryTotals()
        calc = get_industry_calculator("retail", totals)

        assert isinstance(calc, RetailRatioCalculator)

    def test_get_industry_calculator_professional_services(self):
        """Test factory returns ProfessionalServicesRatioCalculator."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        totals = IndustryTotals()
        calc = get_industry_calculator("professional_services", totals)

        assert isinstance(calc, ProfessionalServicesRatioCalculator)

    def test_get_industry_calculator_case_insensitive(self):
        """Test factory is case-insensitive."""
        totals = IndustryTotals()

        calc1 = get_industry_calculator("MANUFACTURING", totals)
        calc2 = get_industry_calculator("Manufacturing", totals)
        calc3 = get_industry_calculator("manufacturing", totals)

        assert isinstance(calc1, ManufacturingRatioCalculator)
        assert isinstance(calc2, ManufacturingRatioCalculator)
        assert isinstance(calc3, ManufacturingRatioCalculator)

    def test_get_industry_calculator_unknown(self):
        """Test factory returns GenericCalculator for unknown industries."""
        totals = IndustryTotals()
        calc = get_industry_calculator("aerospace", totals)

        assert isinstance(calc, GenericIndustryCalculator)
        assert calc.industry_name == "Aerospace"

    def test_get_industry_calculator_invalid_string(self):
        """Test factory handles invalid strings gracefully."""
        totals = IndustryTotals()
        calc = get_industry_calculator("not_an_industry", totals)

        assert isinstance(calc, GenericIndustryCalculator)

    def test_calculate_industry_ratios_end_to_end(self):
        """Test complete calculation flow."""
        totals_dict = {
            "total_assets": 1000000,
            "inventory": 200000,
            "cost_of_goods_sold": 800000,
            "total_revenue": 1200000,
        }

        result = calculate_industry_ratios("manufacturing", totals_dict)

        assert result["industry"] == "Manufacturing"
        assert result["industry_type"] == "manufacturing"
        assert "ratios" in result
        assert "inventory_turnover" in result["ratios"]
        assert result["ratios"]["inventory_turnover"]["value"] == 4.0

    def test_get_available_industries(self):
        """Test available industries list."""
        available = get_available_industries()

        assert len(available) >= 3  # Manufacturing, retail, and professional services

        industry_values = [ind["value"] for ind in available]
        assert "manufacturing" in industry_values
        assert "retail" in industry_values
        assert "professional_services" in industry_values

        # Each should have ratio count
        for ind in available:
            assert "ratio_count" in ind
            assert ind["ratio_count"] > 0


# =============================================================================
# IndustryType Enum Tests
# =============================================================================


class TestIndustryType:
    """Tests for IndustryType enum."""

    def test_all_industries_defined(self):
        """Test that all expected industries are defined."""
        expected = [
            "technology",
            "healthcare",
            "financial_services",
            "manufacturing",
            "retail",
            "professional_services",
            "real_estate",
            "construction",
            "hospitality",
            "nonprofit",
            "education",
            "other",
        ]

        for industry in expected:
            assert IndustryType(industry) is not None

    def test_string_value(self):
        """Test that IndustryType values are strings."""
        assert IndustryType.MANUFACTURING.value == "manufacturing"
        assert IndustryType.RETAIL.value == "retail"


# =============================================================================
# IndustryRatioResult Tests
# =============================================================================


class TestIndustryRatioResult:
    """Tests for IndustryRatioResult dataclass."""

    def test_to_dict(self):
        """Test result serialization."""
        result = IndustryRatioResult(
            name="Test Ratio",
            value=1.5,
            display_value="1.50x",
            is_calculable=True,
            interpretation="Test interpretation",
            threshold_status="above_threshold",
            industry="Test",
            benchmark_note="Test benchmark",
        )

        d = result.to_dict()

        assert d["name"] == "Test Ratio"
        assert d["value"] == 1.5
        assert d["display_value"] == "1.50x"
        assert d["is_calculable"] is True
        assert d["threshold_status"] == "above_threshold"
        assert d["benchmark_note"] == "Test benchmark"

    def test_optional_benchmark_note(self):
        """Test result without benchmark note."""
        result = IndustryRatioResult(
            name="Test",
            value=1.0,
            display_value="1.00",
            is_calculable=True,
            interpretation="Test",
            threshold_status="neutral",
            industry="Test",
        )

        d = result.to_dict()
        assert d["benchmark_note"] is None


# =============================================================================
# Industry Calculator Map Tests
# =============================================================================


class TestIndustryCalculatorMap:
    """Tests for industry-to-calculator mapping."""

    def test_manufacturing_mapped(self):
        """Test manufacturing is in the map."""
        assert IndustryType.MANUFACTURING in INDUSTRY_CALCULATOR_MAP
        assert INDUSTRY_CALCULATOR_MAP[IndustryType.MANUFACTURING] == ManufacturingRatioCalculator

    def test_retail_mapped(self):
        """Test retail is in the map."""
        assert IndustryType.RETAIL in INDUSTRY_CALCULATOR_MAP
        assert INDUSTRY_CALCULATOR_MAP[IndustryType.RETAIL] == RetailRatioCalculator

    def test_professional_services_mapped(self):
        """Test professional services is in the map."""
        from industry_ratios import ProfessionalServicesRatioCalculator

        assert IndustryType.PROFESSIONAL_SERVICES in INDUSTRY_CALCULATOR_MAP
        assert INDUSTRY_CALCULATOR_MAP[IndustryType.PROFESSIONAL_SERVICES] == ProfessionalServicesRatioCalculator

    def test_unmapped_industries(self):
        """Test that unmapped industries are not in the map."""
        # These are planned for future sprints
        assert IndustryType.TECHNOLOGY not in INDUSTRY_CALCULATOR_MAP
        assert IndustryType.HEALTHCARE not in INDUSTRY_CALCULATOR_MAP


# =============================================================================
# Average Inventory Tests
# =============================================================================


class TestAverageInventory:
    """Tests for average inventory handling."""

    def test_uses_average_when_provided(self):
        """Test that average_inventory is used when provided."""
        totals = IndustryTotals(
            inventory=100,
            average_inventory=150,  # Should use this
            cost_of_goods_sold=600,
        )
        calc = ManufacturingRatioCalculator(totals)
        result = calc.calculate_inventory_turnover()

        # Should use 150, not 100: 600 / 150 = 4.0
        assert result.value == 4.0

    def test_falls_back_to_current_inventory(self):
        """Test fallback to current inventory when average not provided."""
        totals = IndustryTotals(
            inventory=200,
            average_inventory=None,
            cost_of_goods_sold=600,
        )
        calc = ManufacturingRatioCalculator(totals)
        result = calc.calculate_inventory_turnover()

        # Should use 200: 600 / 200 = 3.0
        assert result.value == 3.0
