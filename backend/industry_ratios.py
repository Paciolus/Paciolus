"""
Industry-specific financial ratio calculations.

Sprint 35: Industry Ratio Foundation

This module provides industry-specific ratio calculations that supplement
the core financial ratios in ratio_engine.py. Different industries have
different key performance indicators that are most relevant to their
operations.

IFRS/GAAP Compatibility Notes:
-----------------------------
Industry ratios generally use the same underlying data as standard ratios,
so the same framework considerations apply. However, inventory valuation
methods (LIFO vs FIFO) can significantly impact manufacturing ratios.

Zero-Storage Compliance:
-----------------------
All calculations use aggregate totals only. No raw transaction data
is stored or processed beyond what's needed for the calculation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Type
from enum import Enum

from security_utils import log_secure_operation


class IndustryType(str, Enum):
    """Industry classification for ratio selection."""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCIAL_SERVICES = "financial_services"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    PROFESSIONAL_SERVICES = "professional_services"
    REAL_ESTATE = "real_estate"
    CONSTRUCTION = "construction"
    HOSPITALITY = "hospitality"
    NONPROFIT = "nonprofit"
    EDUCATION = "education"
    OTHER = "other"


@dataclass
class IndustryRatioResult:
    """Result of an industry-specific ratio calculation."""
    name: str
    value: Optional[float]
    display_value: str
    is_calculable: bool
    interpretation: str
    health_status: str  # "healthy", "warning", "concern", "neutral"
    industry: str
    benchmark_note: Optional[str] = None  # Industry benchmark context

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "display_value": self.display_value,
            "is_calculable": self.is_calculable,
            "interpretation": self.interpretation,
            "health_status": self.health_status,
            "industry": self.industry,
            "benchmark_note": self.benchmark_note,
        }


@dataclass
class IndustryTotals:
    """
    Extended category totals for industry-specific calculations.

    Includes additional fields beyond the standard CategoryTotals
    that are needed for industry-specific ratios.
    """
    # Standard totals (from CategoryTotals)
    total_assets: float = 0.0
    current_assets: float = 0.0
    inventory: float = 0.0
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    total_equity: float = 0.0
    total_revenue: float = 0.0
    cost_of_goods_sold: float = 0.0
    total_expenses: float = 0.0
    operating_expenses: float = 0.0

    # Extended fields for industry ratios
    average_inventory: Optional[float] = None  # For more accurate turnover
    accounts_receivable: float = 0.0
    accounts_payable: float = 0.0
    fixed_assets: float = 0.0  # Property, plant, equipment

    # Professional Services fields (optional - requires additional data)
    employee_count: Optional[int] = None  # For Revenue per Employee
    billable_hours: Optional[float] = None  # Total billable hours in period
    total_hours: Optional[float] = None  # Total available hours in period

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_assets": self.total_assets,
            "current_assets": self.current_assets,
            "inventory": self.inventory,
            "total_liabilities": self.total_liabilities,
            "current_liabilities": self.current_liabilities,
            "total_equity": self.total_equity,
            "total_revenue": self.total_revenue,
            "cost_of_goods_sold": self.cost_of_goods_sold,
            "total_expenses": self.total_expenses,
            "operating_expenses": self.operating_expenses,
            "average_inventory": self.average_inventory or self.inventory,
            "accounts_receivable": self.accounts_receivable,
            "accounts_payable": self.accounts_payable,
            "fixed_assets": self.fixed_assets,
            "employee_count": self.employee_count,
            "billable_hours": self.billable_hours,
            "total_hours": self.total_hours,
        }

    @classmethod
    def from_category_totals(cls, totals_dict: Dict[str, float]) -> "IndustryTotals":
        """Create IndustryTotals from a standard CategoryTotals dict."""
        return cls(
            total_assets=totals_dict.get("total_assets", 0.0),
            current_assets=totals_dict.get("current_assets", 0.0),
            inventory=totals_dict.get("inventory", 0.0),
            total_liabilities=totals_dict.get("total_liabilities", 0.0),
            current_liabilities=totals_dict.get("current_liabilities", 0.0),
            total_equity=totals_dict.get("total_equity", 0.0),
            total_revenue=totals_dict.get("total_revenue", 0.0),
            cost_of_goods_sold=totals_dict.get("cost_of_goods_sold", 0.0),
            total_expenses=totals_dict.get("total_expenses", 0.0),
            operating_expenses=totals_dict.get("operating_expenses", 0.0),
        )


class IndustryRatioCalculator(ABC):
    """
    Abstract base class for industry-specific ratio calculators.

    Each industry subclass implements ratios that are most relevant
    to that industry's operations and performance evaluation.
    """

    industry_name: str = "Unknown"
    industry_type: IndustryType = IndustryType.OTHER

    def __init__(self, totals: IndustryTotals):
        self.totals = totals
        log_secure_operation(
            "industry_ratio_init",
            f"Initializing {self.industry_name} ratio calculator"
        )

    @abstractmethod
    def calculate_all(self) -> Dict[str, IndustryRatioResult]:
        """Calculate all industry-specific ratios."""
        pass

    @abstractmethod
    def get_ratio_names(self) -> List[str]:
        """Return list of ratio names this calculator provides."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Return all ratios as a serializable dictionary."""
        ratios = self.calculate_all()
        return {
            "industry": self.industry_name,
            "industry_type": self.industry_type.value,
            "ratios": {key: ratio.to_dict() for key, ratio in ratios.items()},
        }


class ManufacturingRatioCalculator(IndustryRatioCalculator):
    """
    Manufacturing industry ratio calculator.

    Key ratios for manufacturing:
    - Inventory Turnover: How efficiently inventory is converted to sales
    - Days Inventory Outstanding: Average days to sell inventory
    - Asset Turnover: How efficiently assets generate revenue

    IFRS/GAAP Note:
    - LIFO inventory (US GAAP only) can significantly understate inventory,
      inflating turnover ratios. IFRS requires FIFO or weighted average.
    - Consider LIFO reserve adjustment when comparing companies.
    """

    industry_name = "Manufacturing"
    industry_type = IndustryType.MANUFACTURING

    def get_ratio_names(self) -> List[str]:
        return [
            "inventory_turnover",
            "days_inventory_outstanding",
            "asset_turnover",
        ]

    def calculate_inventory_turnover(self) -> IndustryRatioResult:
        """
        Inventory Turnover = COGS / Average Inventory

        Measures how many times inventory is sold and replaced over a period.
        Higher turnover generally indicates efficient inventory management.

        Benchmark: Manufacturing typically 4-6x annually
        """
        # Use average inventory if available, otherwise use current inventory
        inventory = self.totals.average_inventory or self.totals.inventory

        if inventory == 0:
            return IndustryRatioResult(
                name="Inventory Turnover",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No inventory identified",
                health_status="neutral",
                industry=self.industry_name,
                benchmark_note="Manufacturing benchmark: 4-6x annually",
            )

        if self.totals.cost_of_goods_sold == 0:
            return IndustryRatioResult(
                name="Inventory Turnover",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No COGS identified",
                health_status="neutral",
                industry=self.industry_name,
                benchmark_note="Manufacturing benchmark: 4-6x annually",
            )

        turnover = self.totals.cost_of_goods_sold / inventory

        # Interpretation based on manufacturing benchmarks
        if turnover >= 8:
            health = "healthy"
            interpretation = "Excellent inventory turnover - efficient management"
        elif turnover >= 6:
            health = "healthy"
            interpretation = "Strong inventory turnover"
        elif turnover >= 4:
            health = "healthy"
            interpretation = "Adequate inventory turnover for manufacturing"
        elif turnover >= 2:
            health = "warning"
            interpretation = "Below-average turnover - review inventory levels"
        else:
            health = "concern"
            interpretation = "Low turnover - potential excess or obsolete inventory"

        return IndustryRatioResult(
            name="Inventory Turnover",
            value=round(turnover, 2),
            display_value=f"{turnover:.2f}x",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
            industry=self.industry_name,
            benchmark_note="Manufacturing benchmark: 4-6x annually",
        )

    def calculate_days_inventory_outstanding(self) -> IndustryRatioResult:
        """
        Days Inventory Outstanding (DIO) = 365 / Inventory Turnover

        Also known as "Days Sales of Inventory" (DSI).
        Measures average number of days to sell inventory.
        Lower is generally better (faster inventory movement).

        Benchmark: Manufacturing typically 60-90 days
        """
        turnover_result = self.calculate_inventory_turnover()

        if not turnover_result.is_calculable or turnover_result.value is None:
            return IndustryRatioResult(
                name="Days Inventory Outstanding",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: Inventory turnover not available",
                health_status="neutral",
                industry=self.industry_name,
                benchmark_note="Manufacturing benchmark: 60-90 days",
            )

        if turnover_result.value == 0:
            return IndustryRatioResult(
                name="Days Inventory Outstanding",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: Zero inventory turnover",
                health_status="neutral",
                industry=self.industry_name,
                benchmark_note="Manufacturing benchmark: 60-90 days",
            )

        dio = 365 / turnover_result.value

        # Interpretation based on manufacturing benchmarks
        if dio <= 45:
            health = "healthy"
            interpretation = "Excellent - very fast inventory movement"
        elif dio <= 60:
            health = "healthy"
            interpretation = "Strong inventory velocity"
        elif dio <= 90:
            health = "healthy"
            interpretation = "Adequate for manufacturing operations"
        elif dio <= 120:
            health = "warning"
            interpretation = "Slow inventory movement - review demand planning"
        else:
            health = "concern"
            interpretation = "Very slow turnover - risk of obsolescence"

        return IndustryRatioResult(
            name="Days Inventory Outstanding",
            value=round(dio, 1),
            display_value=f"{dio:.0f} days",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
            industry=self.industry_name,
            benchmark_note="Manufacturing benchmark: 60-90 days",
        )

    def calculate_asset_turnover(self) -> IndustryRatioResult:
        """
        Asset Turnover = Revenue / Total Assets

        Measures how efficiently a company uses its assets to generate revenue.
        Important for capital-intensive manufacturing operations.

        Benchmark: Manufacturing typically 0.5-1.5x depending on sub-industry
        """
        if self.totals.total_assets == 0:
            return IndustryRatioResult(
                name="Asset Turnover",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No assets identified",
                health_status="neutral",
                industry=self.industry_name,
                benchmark_note="Manufacturing benchmark: 0.5-1.5x annually",
            )

        if self.totals.total_revenue == 0:
            return IndustryRatioResult(
                name="Asset Turnover",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No revenue identified",
                health_status="neutral",
                industry=self.industry_name,
                benchmark_note="Manufacturing benchmark: 0.5-1.5x annually",
            )

        turnover = self.totals.total_revenue / self.totals.total_assets

        # Interpretation based on manufacturing benchmarks
        if turnover >= 1.5:
            health = "healthy"
            interpretation = "Excellent asset utilization"
        elif turnover >= 1.0:
            health = "healthy"
            interpretation = "Strong asset efficiency"
        elif turnover >= 0.5:
            health = "healthy"
            interpretation = "Adequate for capital-intensive manufacturing"
        elif turnover >= 0.3:
            health = "warning"
            interpretation = "Below-average - review asset utilization"
        else:
            health = "concern"
            interpretation = "Low asset turnover - potential underutilization"

        return IndustryRatioResult(
            name="Asset Turnover",
            value=round(turnover, 2),
            display_value=f"{turnover:.2f}x",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
            industry=self.industry_name,
            benchmark_note="Manufacturing benchmark: 0.5-1.5x annually",
        )

    def calculate_all(self) -> Dict[str, IndustryRatioResult]:
        """Calculate all manufacturing ratios."""
        return {
            "inventory_turnover": self.calculate_inventory_turnover(),
            "days_inventory_outstanding": self.calculate_days_inventory_outstanding(),
            "asset_turnover": self.calculate_asset_turnover(),
        }


class RetailRatioCalculator(IndustryRatioCalculator):
    """
    Retail industry ratio calculator.

    Key ratios for retail:
    - Inventory Turnover: Critical for retail operations
    - Gross Margin Return on Inventory (GMROI): Profitability per inventory dollar
    - Sales per Square Foot: (placeholder - requires additional data)

    Note: Sprint 36 will expand retail ratios.
    """

    industry_name = "Retail"
    industry_type = IndustryType.RETAIL

    def get_ratio_names(self) -> List[str]:
        return [
            "inventory_turnover",
            "gmroi",
        ]

    def calculate_inventory_turnover(self) -> IndustryRatioResult:
        """
        Inventory Turnover for Retail = COGS / Average Inventory

        Retail typically has higher turnover expectations than manufacturing.

        Benchmark: Retail typically 8-12x annually (varies by sub-sector)
        """
        inventory = self.totals.average_inventory or self.totals.inventory

        if inventory == 0 or self.totals.cost_of_goods_sold == 0:
            return IndustryRatioResult(
                name="Inventory Turnover",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: Missing inventory or COGS data",
                health_status="neutral",
                industry=self.industry_name,
                benchmark_note="Retail benchmark: 8-12x annually",
            )

        turnover = self.totals.cost_of_goods_sold / inventory

        # Retail-specific thresholds (higher than manufacturing)
        if turnover >= 12:
            health = "healthy"
            interpretation = "Excellent retail inventory turnover"
        elif turnover >= 8:
            health = "healthy"
            interpretation = "Strong inventory management"
        elif turnover >= 5:
            health = "warning"
            interpretation = "Below retail average - review merchandise mix"
        else:
            health = "concern"
            interpretation = "Low turnover - risk of markdowns/obsolescence"

        return IndustryRatioResult(
            name="Inventory Turnover",
            value=round(turnover, 2),
            display_value=f"{turnover:.2f}x",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
            industry=self.industry_name,
            benchmark_note="Retail benchmark: 8-12x annually",
        )

    def calculate_gmroi(self) -> IndustryRatioResult:
        """
        Gross Margin Return on Inventory (GMROI)
        = Gross Margin / Average Inventory Cost
        = (Revenue - COGS) / Average Inventory

        Measures how much gross profit is earned for each dollar invested in inventory.

        Benchmark: Retail typically targets GMROI > 2.0
        """
        inventory = self.totals.average_inventory or self.totals.inventory

        if inventory == 0:
            return IndustryRatioResult(
                name="GMROI",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No inventory data",
                health_status="neutral",
                industry=self.industry_name,
                benchmark_note="Retail benchmark: GMROI > 2.0",
            )

        gross_margin = self.totals.total_revenue - self.totals.cost_of_goods_sold
        gmroi = gross_margin / inventory

        if gmroi >= 3.0:
            health = "healthy"
            interpretation = "Excellent return on inventory investment"
        elif gmroi >= 2.0:
            health = "healthy"
            interpretation = "Strong GMROI - profitable inventory"
        elif gmroi >= 1.0:
            health = "warning"
            interpretation = "Marginal return - review pricing/mix"
        else:
            health = "concern"
            interpretation = "Poor return - inventory not generating adequate profit"

        return IndustryRatioResult(
            name="GMROI",
            value=round(gmroi, 2),
            display_value=f"${gmroi:.2f}",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
            industry=self.industry_name,
            benchmark_note="Retail benchmark: GMROI > 2.0",
        )

    def calculate_all(self) -> Dict[str, IndustryRatioResult]:
        """Calculate all retail ratios."""
        return {
            "inventory_turnover": self.calculate_inventory_turnover(),
            "gmroi": self.calculate_gmroi(),
        }


class ProfessionalServicesRatioCalculator(IndustryRatioCalculator):
    """
    Professional Services industry ratio calculator.

    Key ratios for professional services (law firms, consulting, accounting):
    - Revenue per Employee: Productivity measure
    - Utilization Rate: Percentage of billable time
    - Realization Rate: (placeholder - requires billing data)

    Note: These ratios require additional data beyond standard financial statements.
    When data is unavailable, helpful placeholder messages guide users on what's needed.

    IFRS/GAAP Note:
    - Revenue recognition timing can affect per-period calculations
    - IFRS 15 / ASC 606 may impact when revenue is recognized for services
    """

    industry_name = "Professional Services"
    industry_type = IndustryType.PROFESSIONAL_SERVICES

    def get_ratio_names(self) -> List[str]:
        return [
            "revenue_per_employee",
            "utilization_rate",
            "revenue_per_billable_hour",
        ]

    def calculate_revenue_per_employee(self) -> IndustryRatioResult:
        """
        Revenue per Employee = Total Revenue / Employee Count

        Measures productivity and scalability of the professional services firm.
        Higher values indicate efficient use of human capital.

        Benchmark: Varies significantly by industry
        - Law firms: $200K-$500K+
        - Consulting: $150K-$400K
        - Accounting: $100K-$250K
        """
        if self.totals.employee_count is None:
            return IndustryRatioResult(
                name="Revenue per Employee",
                value=None,
                display_value="Data Required",
                is_calculable=False,
                interpretation="Requires employee_count data. Add employee headcount to calculate this metric.",
                health_status="neutral",
                industry=self.industry_name,
                benchmark_note="Typical range: $100K-$500K depending on service type",
            )

        if self.totals.employee_count == 0:
            return IndustryRatioResult(
                name="Revenue per Employee",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: Zero employees reported",
                health_status="neutral",
                industry=self.industry_name,
            )

        if self.totals.total_revenue == 0:
            return IndustryRatioResult(
                name="Revenue per Employee",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No revenue identified",
                health_status="neutral",
                industry=self.industry_name,
            )

        rpe = self.totals.total_revenue / self.totals.employee_count

        # Interpretation based on professional services benchmarks
        if rpe >= 300000:
            health = "healthy"
            interpretation = "Excellent productivity - high-value services"
        elif rpe >= 200000:
            health = "healthy"
            interpretation = "Strong revenue per employee"
        elif rpe >= 100000:
            health = "healthy"
            interpretation = "Adequate for professional services"
        elif rpe >= 50000:
            health = "warning"
            interpretation = "Below average - review pricing or efficiency"
        else:
            health = "concern"
            interpretation = "Low productivity - significant improvement needed"

        return IndustryRatioResult(
            name="Revenue per Employee",
            value=round(rpe, 0),
            display_value=f"${rpe:,.0f}",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
            industry=self.industry_name,
            benchmark_note="Typical range: $100K-$500K depending on service type",
        )

    def calculate_utilization_rate(self) -> IndustryRatioResult:
        """
        Utilization Rate = Billable Hours / Total Available Hours

        Measures the percentage of time spent on billable client work.
        Critical KPI for professional services profitability.

        Benchmark: Professional services typically target 65-85%
        """
        if self.totals.billable_hours is None or self.totals.total_hours is None:
            return IndustryRatioResult(
                name="Utilization Rate",
                value=None,
                display_value="Data Required",
                is_calculable=False,
                interpretation="Requires billable_hours and total_hours data. Track time to calculate this metric.",
                health_status="neutral",
                industry=self.industry_name,
                benchmark_note="Target: 65-85% utilization",
            )

        if self.totals.total_hours == 0:
            return IndustryRatioResult(
                name="Utilization Rate",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: Zero total hours reported",
                health_status="neutral",
                industry=self.industry_name,
            )

        utilization = (self.totals.billable_hours / self.totals.total_hours) * 100

        # Cap at 100% (data entry error protection)
        utilization = min(utilization, 100.0)

        # Interpretation based on professional services benchmarks
        if utilization >= 85:
            health = "healthy"
            interpretation = "Excellent utilization - near capacity"
        elif utilization >= 75:
            health = "healthy"
            interpretation = "Strong utilization rate"
        elif utilization >= 65:
            health = "healthy"
            interpretation = "Adequate utilization for sustainable growth"
        elif utilization >= 50:
            health = "warning"
            interpretation = "Below target - review staffing or business development"
        else:
            health = "concern"
            interpretation = "Low utilization - significant underutilization of staff"

        return IndustryRatioResult(
            name="Utilization Rate",
            value=round(utilization, 1),
            display_value=f"{utilization:.1f}%",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
            industry=self.industry_name,
            benchmark_note="Target: 65-85% utilization",
        )

    def calculate_revenue_per_billable_hour(self) -> IndustryRatioResult:
        """
        Revenue per Billable Hour = Total Revenue / Billable Hours

        Measures effective billing rate across all services.
        Indicates pricing power and service value.

        Benchmark: Varies by service type
        - Law: $200-$800+/hour
        - Consulting: $150-$500/hour
        - Accounting: $100-$400/hour
        """
        if self.totals.billable_hours is None:
            return IndustryRatioResult(
                name="Revenue per Billable Hour",
                value=None,
                display_value="Data Required",
                is_calculable=False,
                interpretation="Requires billable_hours data. Track time to calculate effective rate.",
                health_status="neutral",
                industry=self.industry_name,
                benchmark_note="Typical range: $100-$500/hour depending on service type",
            )

        if self.totals.billable_hours == 0:
            return IndustryRatioResult(
                name="Revenue per Billable Hour",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: Zero billable hours reported",
                health_status="neutral",
                industry=self.industry_name,
            )

        if self.totals.total_revenue == 0:
            return IndustryRatioResult(
                name="Revenue per Billable Hour",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No revenue identified",
                health_status="neutral",
                industry=self.industry_name,
            )

        rate = self.totals.total_revenue / self.totals.billable_hours

        # Interpretation based on professional services benchmarks
        if rate >= 300:
            health = "healthy"
            interpretation = "Premium billing rate - high-value services"
        elif rate >= 200:
            health = "healthy"
            interpretation = "Strong effective rate"
        elif rate >= 100:
            health = "healthy"
            interpretation = "Adequate rate for professional services"
        elif rate >= 50:
            health = "warning"
            interpretation = "Below market - review pricing strategy"
        else:
            health = "concern"
            interpretation = "Low rate - significant pricing improvement needed"

        return IndustryRatioResult(
            name="Revenue per Billable Hour",
            value=round(rate, 2),
            display_value=f"${rate:,.2f}/hr",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
            industry=self.industry_name,
            benchmark_note="Typical range: $100-$500/hour depending on service type",
        )

    def calculate_all(self) -> Dict[str, IndustryRatioResult]:
        """Calculate all professional services ratios."""
        return {
            "revenue_per_employee": self.calculate_revenue_per_employee(),
            "utilization_rate": self.calculate_utilization_rate(),
            "revenue_per_billable_hour": self.calculate_revenue_per_billable_hour(),
        }


class GenericIndustryCalculator(IndustryRatioCalculator):
    """
    Generic calculator for industries without specific implementations.

    Returns a subset of commonly applicable ratios with industry-neutral
    interpretations. Serves as a fallback for industries not yet implemented.
    """

    industry_name = "General"
    industry_type = IndustryType.OTHER

    def __init__(self, totals: IndustryTotals, industry_name: str = "General"):
        super().__init__(totals)
        self.industry_name = industry_name

    def get_ratio_names(self) -> List[str]:
        return ["asset_turnover"]

    def calculate_asset_turnover(self) -> IndustryRatioResult:
        """Generic asset turnover calculation."""
        if self.totals.total_assets == 0 or self.totals.total_revenue == 0:
            return IndustryRatioResult(
                name="Asset Turnover",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: Missing data",
                health_status="neutral",
                industry=self.industry_name,
            )

        turnover = self.totals.total_revenue / self.totals.total_assets

        return IndustryRatioResult(
            name="Asset Turnover",
            value=round(turnover, 2),
            display_value=f"{turnover:.2f}x",
            is_calculable=True,
            interpretation="Asset utilization efficiency",
            health_status="neutral",
            industry=self.industry_name,
        )

    def calculate_all(self) -> Dict[str, IndustryRatioResult]:
        return {"asset_turnover": self.calculate_asset_turnover()}


# =============================================================================
# Industry to Calculator Mapping
# =============================================================================

INDUSTRY_CALCULATOR_MAP: Dict[IndustryType, Type[IndustryRatioCalculator]] = {
    IndustryType.MANUFACTURING: ManufacturingRatioCalculator,
    IndustryType.RETAIL: RetailRatioCalculator,
    IndustryType.PROFESSIONAL_SERVICES: ProfessionalServicesRatioCalculator,
    # Future implementations:
    # IndustryType.TECHNOLOGY: TechnologyRatioCalculator,
    # IndustryType.HEALTHCARE: HealthcareRatioCalculator,
    # IndustryType.FINANCIAL_SERVICES: FinancialServicesRatioCalculator,
    # IndustryType.REAL_ESTATE: RealEstateRatioCalculator,
    # IndustryType.CONSTRUCTION: ConstructionRatioCalculator,
}


def get_industry_calculator(
    industry: str,
    totals: IndustryTotals
) -> IndustryRatioCalculator:
    """
    Factory function to get the appropriate calculator for an industry.

    Args:
        industry: Industry string (matches IndustryType enum values)
        totals: IndustryTotals with financial data

    Returns:
        Appropriate IndustryRatioCalculator subclass instance
    """
    try:
        industry_type = IndustryType(industry.lower())
    except ValueError:
        industry_type = IndustryType.OTHER

    calculator_class = INDUSTRY_CALCULATOR_MAP.get(industry_type)

    if calculator_class:
        return calculator_class(totals)
    else:
        return GenericIndustryCalculator(totals, industry_name=industry.replace("_", " ").title())


def calculate_industry_ratios(
    industry: str,
    totals_dict: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calculate industry-specific ratios from category totals.

    Args:
        industry: Industry classification string
        totals_dict: Dictionary of category totals (from CategoryTotals.to_dict())

    Returns:
        Dictionary with industry name and calculated ratios
    """
    totals = IndustryTotals.from_category_totals(totals_dict)
    calculator = get_industry_calculator(industry, totals)

    log_secure_operation(
        "industry_ratios_calculated",
        f"Calculated {calculator.industry_name} ratios"
    )

    return calculator.to_dict()


def get_available_industries() -> List[Dict[str, str]]:
    """
    Get list of industries with specific ratio implementations.

    Returns:
        List of dicts with industry value and display name
    """
    available = []
    for industry_type, calculator_class in INDUSTRY_CALCULATOR_MAP.items():
        available.append({
            "value": industry_type.value,
            "label": calculator_class.industry_name,
            "ratio_count": len(calculator_class(IndustryTotals()).get_ratio_names()),
        })
    return available
