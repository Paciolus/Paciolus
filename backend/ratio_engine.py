"""
Paciolus Ratio Intelligence Engine
Sprint 19: Comparative Analytics & Ratio Engine

Mathematical Diagnostic Logic for financial ratio calculations and analysis.
All formulas are standard accounting ratios used in financial analysis.

ZERO-STORAGE COMPLIANCE:
- Ratios are calculated from in-memory data during diagnostic runs
- Only aggregate category totals are persisted (never raw transaction data)
- Variance comparison uses stored metadata totals, not raw data

IP DOCUMENTATION: See logs/dev-log.md
These calculations use standard financial ratio formulas taught in accounting
and finance curricula worldwide. No proprietary algorithms.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

from security_utils import log_secure_operation
from classification_rules import AccountCategory


class TrendDirection(str, Enum):
    """Direction of change for variance calculations."""
    POSITIVE = "positive"  # Favorable change
    NEGATIVE = "negative"  # Unfavorable change
    NEUTRAL = "neutral"    # No significant change


@dataclass
class RatioResult:
    """Result of a ratio calculation with interpretation."""
    name: str
    value: Optional[float]
    display_value: str
    is_calculable: bool
    interpretation: str
    health_status: str  # "healthy", "warning", "concern"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "display_value": self.display_value,
            "is_calculable": self.is_calculable,
            "interpretation": self.interpretation,
            "health_status": self.health_status,
        }


@dataclass
class VarianceResult:
    """Result of a variance calculation between two diagnostic runs."""
    metric_name: str
    current_value: float
    previous_value: float
    change_amount: float
    change_percent: float
    direction: TrendDirection
    display_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "change_amount": self.change_amount,
            "change_percent": self.change_percent,
            "direction": self.direction.value,
            "display_text": self.display_text,
        }


@dataclass
class CategoryTotals:
    """
    Aggregate totals by account category.

    ZERO-STORAGE: These totals can be persisted as metadata
    without storing individual account details.
    """
    total_assets: float = 0.0
    current_assets: float = 0.0
    inventory: float = 0.0
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    total_equity: float = 0.0
    total_revenue: float = 0.0
    cost_of_goods_sold: float = 0.0
    total_expenses: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "total_assets": round(self.total_assets, 2),
            "current_assets": round(self.current_assets, 2),
            "inventory": round(self.inventory, 2),
            "total_liabilities": round(self.total_liabilities, 2),
            "current_liabilities": round(self.current_liabilities, 2),
            "total_equity": round(self.total_equity, 2),
            "total_revenue": round(self.total_revenue, 2),
            "cost_of_goods_sold": round(self.cost_of_goods_sold, 2),
            "total_expenses": round(self.total_expenses, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "CategoryTotals":
        return cls(
            total_assets=data.get("total_assets", 0.0),
            current_assets=data.get("current_assets", 0.0),
            inventory=data.get("inventory", 0.0),
            total_liabilities=data.get("total_liabilities", 0.0),
            current_liabilities=data.get("current_liabilities", 0.0),
            total_equity=data.get("total_equity", 0.0),
            total_revenue=data.get("total_revenue", 0.0),
            cost_of_goods_sold=data.get("cost_of_goods_sold", 0.0),
            total_expenses=data.get("total_expenses", 0.0),
        )


class RatioEngine:
    """
    Financial Ratio Calculator - Mathematical Diagnostic Logic

    Calculates standard financial ratios from category totals.
    All formulas are industry-standard accounting ratios.
    """

    def __init__(self, category_totals: CategoryTotals):
        """
        Initialize with category totals from a diagnostic run.

        Args:
            category_totals: Aggregate totals by account category
        """
        self.totals = category_totals
        log_secure_operation(
            "ratio_engine_init",
            f"Initializing ratio calculations with totals: {category_totals.to_dict()}"
        )

    def calculate_current_ratio(self) -> RatioResult:
        """
        Current Ratio = Current Assets / Current Liabilities

        Measures short-term liquidity. Generally, > 1.0 indicates ability
        to cover short-term obligations.

        Standard formula: FASB/GAAP liquidity analysis
        """
        if self.totals.current_liabilities == 0:
            return RatioResult(
                name="Current Ratio",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No current liabilities identified",
                health_status="neutral",
            )

        ratio = self.totals.current_assets / self.totals.current_liabilities

        # Interpretation thresholds (standard financial analysis)
        if ratio >= 2.0:
            health = "healthy"
            interpretation = "Strong liquidity position"
        elif ratio >= 1.0:
            health = "healthy"
            interpretation = "Adequate liquidity to cover short-term obligations"
        elif ratio >= 0.5:
            health = "warning"
            interpretation = "May have difficulty covering short-term obligations"
        else:
            health = "concern"
            interpretation = "Potential liquidity risk"

        return RatioResult(
            name="Current Ratio",
            value=round(ratio, 2),
            display_value=f"{ratio:.2f}",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
        )

    def calculate_quick_ratio(self) -> RatioResult:
        """
        Quick Ratio = (Current Assets - Inventory) / Current Liabilities

        Also called "Acid Test Ratio". More conservative liquidity measure
        that excludes inventory (which may not be quickly liquidated).

        Standard formula: FASB/GAAP liquidity analysis
        """
        if self.totals.current_liabilities == 0:
            return RatioResult(
                name="Quick Ratio",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No current liabilities identified",
                health_status="neutral",
            )

        quick_assets = self.totals.current_assets - self.totals.inventory
        ratio = quick_assets / self.totals.current_liabilities

        # Interpretation thresholds
        if ratio >= 1.0:
            health = "healthy"
            interpretation = "Strong quick liquidity position"
        elif ratio >= 0.5:
            health = "warning"
            interpretation = "Moderate liquidity without inventory liquidation"
        else:
            health = "concern"
            interpretation = "May need to liquidate inventory to cover obligations"

        return RatioResult(
            name="Quick Ratio",
            value=round(ratio, 2),
            display_value=f"{ratio:.2f}",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
        )

    def calculate_debt_to_equity(self) -> RatioResult:
        """
        Debt-to-Equity Ratio = Total Liabilities / Total Equity

        Measures financial leverage. Higher ratio indicates more debt
        financing relative to equity.

        Standard formula: FASB/GAAP leverage analysis
        """
        if self.totals.total_equity == 0:
            return RatioResult(
                name="Debt-to-Equity",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No equity identified",
                health_status="neutral",
            )

        ratio = self.totals.total_liabilities / self.totals.total_equity

        # Interpretation (varies by industry, using general guidelines)
        if ratio <= 0.5:
            health = "healthy"
            interpretation = "Conservative leverage position"
        elif ratio <= 1.0:
            health = "healthy"
            interpretation = "Balanced debt and equity financing"
        elif ratio <= 2.0:
            health = "warning"
            interpretation = "Moderately leveraged"
        else:
            health = "concern"
            interpretation = "High financial leverage"

        return RatioResult(
            name="Debt-to-Equity",
            value=round(ratio, 2),
            display_value=f"{ratio:.2f}",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
        )

    def calculate_gross_margin(self) -> RatioResult:
        """
        Gross Margin = (Revenue - COGS) / Revenue

        Measures profitability before operating expenses.
        Expressed as a percentage.

        Standard formula: FASB/GAAP profitability analysis
        """
        if self.totals.total_revenue == 0:
            return RatioResult(
                name="Gross Margin",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No revenue identified",
                health_status="neutral",
            )

        gross_profit = self.totals.total_revenue - self.totals.cost_of_goods_sold
        margin = (gross_profit / self.totals.total_revenue) * 100

        # Interpretation (varies significantly by industry)
        if margin >= 50:
            health = "healthy"
            interpretation = "Strong gross margin"
        elif margin >= 30:
            health = "healthy"
            interpretation = "Healthy gross margin"
        elif margin >= 15:
            health = "warning"
            interpretation = "Moderate gross margin"
        else:
            health = "concern"
            interpretation = "Low gross margin - review pricing/costs"

        return RatioResult(
            name="Gross Margin",
            value=round(margin, 1),
            display_value=f"{margin:.1f}%",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
        )

    def calculate_all_ratios(self) -> Dict[str, RatioResult]:
        """Calculate all available ratios and return as dictionary."""
        return {
            "current_ratio": self.calculate_current_ratio(),
            "quick_ratio": self.calculate_quick_ratio(),
            "debt_to_equity": self.calculate_debt_to_equity(),
            "gross_margin": self.calculate_gross_margin(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Return all ratios as a serializable dictionary."""
        ratios = self.calculate_all_ratios()
        return {key: ratio.to_dict() for key, ratio in ratios.items()}


class CommonSizeAnalyzer:
    """
    Common-Size Analysis - Mathematical Diagnostic Logic

    Expresses each line item as a percentage of a base amount
    (Total Assets for balance sheet, Revenue for income statement).

    Standard analytical technique used in financial statement analysis.
    """

    def __init__(self, category_totals: CategoryTotals):
        self.totals = category_totals

    def balance_sheet_percentages(self) -> Dict[str, float]:
        """
        Express balance sheet items as percentage of Total Assets.

        Standard format for common-size balance sheet analysis.
        """
        base = self.totals.total_assets
        if base == 0:
            return {}

        return {
            "current_assets_pct": round((self.totals.current_assets / base) * 100, 1),
            "inventory_pct": round((self.totals.inventory / base) * 100, 1),
            "total_liabilities_pct": round((self.totals.total_liabilities / base) * 100, 1),
            "current_liabilities_pct": round((self.totals.current_liabilities / base) * 100, 1),
            "total_equity_pct": round((self.totals.total_equity / base) * 100, 1),
        }

    def income_statement_percentages(self) -> Dict[str, float]:
        """
        Express income statement items as percentage of Revenue.

        Standard format for common-size income statement analysis.
        """
        base = self.totals.total_revenue
        if base == 0:
            return {}

        gross_profit = base - self.totals.cost_of_goods_sold
        net_income = base - self.totals.total_expenses

        return {
            "cogs_pct": round((self.totals.cost_of_goods_sold / base) * 100, 1),
            "gross_profit_pct": round((gross_profit / base) * 100, 1),
            "total_expenses_pct": round((self.totals.total_expenses / base) * 100, 1),
            "net_income_pct": round((net_income / base) * 100, 1),
        }

    def to_dict(self) -> Dict[str, Dict[str, float]]:
        """Return all common-size percentages."""
        return {
            "balance_sheet": self.balance_sheet_percentages(),
            "income_statement": self.income_statement_percentages(),
        }


class VarianceAnalyzer:
    """
    Variance Intelligence - Compare current vs previous diagnostic runs.

    ZERO-STORAGE COMPLIANCE:
    Compares aggregate category totals from stored metadata,
    never raw transaction data.
    """

    def __init__(
        self,
        current_totals: CategoryTotals,
        previous_totals: Optional[CategoryTotals] = None
    ):
        self.current = current_totals
        self.previous = previous_totals

    def _calculate_variance(
        self,
        metric_name: str,
        current_value: float,
        previous_value: float,
        higher_is_better: bool = True
    ) -> VarianceResult:
        """
        Calculate variance between current and previous values.

        Args:
            metric_name: Display name for the metric
            current_value: Current period value
            previous_value: Previous period value
            higher_is_better: Whether increase is favorable
        """
        change_amount = current_value - previous_value

        if previous_value != 0:
            change_percent = (change_amount / abs(previous_value)) * 100
        else:
            change_percent = 100.0 if current_value != 0 else 0.0

        # Determine direction (favorable vs unfavorable)
        if abs(change_percent) < 1.0:
            direction = TrendDirection.NEUTRAL
        elif higher_is_better:
            direction = TrendDirection.POSITIVE if change_amount > 0 else TrendDirection.NEGATIVE
        else:
            direction = TrendDirection.NEGATIVE if change_amount > 0 else TrendDirection.POSITIVE

        # Generate display text
        if direction == TrendDirection.NEUTRAL:
            display_text = "Unchanged"
        elif change_percent >= 0:
            display_text = f"Up {abs(change_percent):.1f}%"
        else:
            display_text = f"Down {abs(change_percent):.1f}%"

        return VarianceResult(
            metric_name=metric_name,
            current_value=round(current_value, 2),
            previous_value=round(previous_value, 2),
            change_amount=round(change_amount, 2),
            change_percent=round(change_percent, 1),
            direction=direction,
            display_text=display_text,
        )

    def calculate_variances(self) -> Dict[str, VarianceResult]:
        """
        Calculate variances for all category totals.

        Returns empty dict if no previous run available.
        """
        if self.previous is None:
            return {}

        return {
            "total_assets": self._calculate_variance(
                "Total Assets",
                self.current.total_assets,
                self.previous.total_assets,
                higher_is_better=True
            ),
            "total_liabilities": self._calculate_variance(
                "Total Liabilities",
                self.current.total_liabilities,
                self.previous.total_liabilities,
                higher_is_better=False  # Lower liabilities generally better
            ),
            "total_equity": self._calculate_variance(
                "Total Equity",
                self.current.total_equity,
                self.previous.total_equity,
                higher_is_better=True
            ),
            "total_revenue": self._calculate_variance(
                "Total Revenue",
                self.current.total_revenue,
                self.previous.total_revenue,
                higher_is_better=True
            ),
            "current_assets": self._calculate_variance(
                "Current Assets",
                self.current.current_assets,
                self.previous.current_assets,
                higher_is_better=True
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Return all variances as serializable dictionary."""
        variances = self.calculate_variances()
        return {key: var.to_dict() for key, var in variances.items()}


# =============================================================================
# CATEGORY TOTALS EXTRACTION
# =============================================================================

# Keywords for identifying current vs non-current assets
CURRENT_ASSET_KEYWORDS = [
    'cash', 'bank', 'receivable', 'inventory', 'prepaid', 'supplies',
    'short-term', 'short term', 'current', 'marketable securities'
]

# Keywords for COGS identification
COGS_KEYWORDS = [
    'cost of goods', 'cogs', 'cost of sales', 'cost of revenue',
    'direct cost', 'direct material', 'direct labor', 'manufacturing cost'
]


def extract_category_totals(
    account_balances: Dict[str, Dict[str, float]],
    classified_accounts: Dict[str, str]
) -> CategoryTotals:
    """
    Extract category totals from account balances.

    ZERO-STORAGE: This function produces aggregate totals that can be
    safely persisted without storing individual account details.

    Args:
        account_balances: Dict of account_name -> {"debit": float, "credit": float}
        classified_accounts: Dict of account_name -> category (from classifier)

    Returns:
        CategoryTotals with aggregate amounts by category
    """
    totals = CategoryTotals()

    for account_name, balances in account_balances.items():
        debit = balances.get("debit", 0.0)
        credit = balances.get("credit", 0.0)
        net_balance = debit - credit

        # Get classification for this account
        category = classified_accounts.get(account_name, "unknown")
        account_lower = account_name.lower()

        if category == "asset":
            # Assets have natural debit balance
            amount = abs(net_balance) if net_balance > 0 else -abs(net_balance)
            totals.total_assets += amount

            # Check if current asset
            if any(kw in account_lower for kw in CURRENT_ASSET_KEYWORDS):
                totals.current_assets += amount
                if 'inventory' in account_lower:
                    totals.inventory += amount

        elif category == "liability":
            # Liabilities have natural credit balance
            amount = abs(net_balance) if net_balance < 0 else -abs(net_balance)
            totals.total_liabilities += amount

            # Check if current liability
            if any(kw in account_lower for kw in ['payable', 'current', 'short-term', 'accrued']):
                totals.current_liabilities += amount

        elif category == "equity":
            # Equity has natural credit balance
            amount = abs(net_balance) if net_balance < 0 else -abs(net_balance)
            totals.total_equity += amount

        elif category == "revenue":
            # Revenue has natural credit balance
            amount = abs(net_balance) if net_balance < 0 else -abs(net_balance)
            totals.total_revenue += amount

        elif category == "expense":
            # Expenses have natural debit balance
            amount = abs(net_balance) if net_balance > 0 else -abs(net_balance)
            totals.total_expenses += amount

            # Check if COGS
            if any(kw in account_lower for kw in COGS_KEYWORDS):
                totals.cost_of_goods_sold += amount

    log_secure_operation(
        "category_totals_extracted",
        f"Extracted totals - Assets: ${totals.total_assets:,.2f}, "
        f"Liabilities: ${totals.total_liabilities:,.2f}, "
        f"Revenue: ${totals.total_revenue:,.2f}"
    )

    return totals


def calculate_analytics(
    category_totals: CategoryTotals,
    previous_totals: Optional[CategoryTotals] = None
) -> Dict[str, Any]:
    """
    Calculate all analytics (ratios, common-size, variances).

    Main entry point for the Ratio Intelligence module.

    Args:
        category_totals: Current period category totals
        previous_totals: Optional previous period for variance calculation

    Returns:
        Complete analytics dictionary ready for API response
    """
    # Calculate ratios
    ratio_engine = RatioEngine(category_totals)
    ratios = ratio_engine.to_dict()

    # Calculate common-size percentages
    common_size = CommonSizeAnalyzer(category_totals)
    common_size_analysis = common_size.to_dict()

    # Calculate variances if previous data available
    variance_analyzer = VarianceAnalyzer(category_totals, previous_totals)
    variances = variance_analyzer.to_dict()

    return {
        "category_totals": category_totals.to_dict(),
        "ratios": ratios,
        "common_size": common_size_analysis,
        "variances": variances,
        "has_previous_data": previous_totals is not None,
    }
