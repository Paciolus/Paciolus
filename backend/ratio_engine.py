"""Financial ratio calculations and analysis using standard accounting formulas."""

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
    """Aggregate totals by account category."""
    total_assets: float = 0.0
    current_assets: float = 0.0
    inventory: float = 0.0
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    total_equity: float = 0.0
    total_revenue: float = 0.0
    cost_of_goods_sold: float = 0.0
    total_expenses: float = 0.0
    operating_expenses: float = 0.0  # Sprint 26: For Operating Profit Margin

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
            "operating_expenses": round(self.operating_expenses, 2),
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
            operating_expenses=data.get("operating_expenses", 0.0),
        )


class RatioEngine:
    """Calculates standard financial ratios from category totals."""

    def __init__(self, category_totals: CategoryTotals):
        self.totals = category_totals
        log_secure_operation(
            "ratio_engine_init",
            f"Initializing ratio calculations with totals: {category_totals.to_dict()}"
        )

    def calculate_current_ratio(self) -> RatioResult:
        """Current Ratio = Current Assets / Current Liabilities."""
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
        """Quick Ratio = (Current Assets - Inventory) / Current Liabilities."""
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
        """Debt-to-Equity = Total Liabilities / Total Equity."""
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
        """Gross Margin = (Revenue - COGS) / Revenue, expressed as percentage."""
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

    def calculate_net_profit_margin(self) -> RatioResult:
        """Net Profit Margin = (Revenue - Total Expenses) / Revenue × 100%.

        Sprint 26: Measures overall profitability after all expenses.
        """
        if self.totals.total_revenue == 0:
            return RatioResult(
                name="Net Profit Margin",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No revenue identified",
                health_status="neutral",
            )

        net_income = self.totals.total_revenue - self.totals.total_expenses
        margin = (net_income / self.totals.total_revenue) * 100

        # Interpretation thresholds (industry-generic)
        if margin >= 20:
            health = "healthy"
            interpretation = "Excellent profitability"
        elif margin >= 10:
            health = "healthy"
            interpretation = "Healthy net profit margin"
        elif margin >= 5:
            health = "warning"
            interpretation = "Moderate profitability - monitor expenses"
        elif margin >= 0:
            health = "warning"
            interpretation = "Low profitability - cost control needed"
        else:
            health = "concern"
            interpretation = "Operating at a loss"

        return RatioResult(
            name="Net Profit Margin",
            value=round(margin, 1),
            display_value=f"{margin:.1f}%",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
        )

    def calculate_operating_margin(self) -> RatioResult:
        """Operating Margin = (Revenue - COGS - Operating Expenses) / Revenue × 100%.

        Sprint 26: Measures profitability from core operations before interest/taxes.
        Operating Expenses = Total Expenses - COGS (if operating_expenses not separately tracked)
        """
        if self.totals.total_revenue == 0:
            return RatioResult(
                name="Operating Margin",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No revenue identified",
                health_status="neutral",
            )

        # Use operating_expenses if available, otherwise derive from total_expenses - COGS
        if self.totals.operating_expenses > 0:
            operating_exp = self.totals.operating_expenses
        else:
            # Fallback: operating expenses = total expenses - COGS
            operating_exp = self.totals.total_expenses - self.totals.cost_of_goods_sold

        operating_income = self.totals.total_revenue - self.totals.cost_of_goods_sold - operating_exp
        margin = (operating_income / self.totals.total_revenue) * 100

        # Interpretation thresholds (industry-generic)
        if margin >= 25:
            health = "healthy"
            interpretation = "Excellent operating efficiency"
        elif margin >= 15:
            health = "healthy"
            interpretation = "Strong operating margin"
        elif margin >= 10:
            health = "healthy"
            interpretation = "Adequate operating margin"
        elif margin >= 5:
            health = "warning"
            interpretation = "Thin operating margin - review costs"
        elif margin >= 0:
            health = "warning"
            interpretation = "Minimal operating profit"
        else:
            health = "concern"
            interpretation = "Operating loss - immediate attention needed"

        return RatioResult(
            name="Operating Margin",
            value=round(margin, 1),
            display_value=f"{margin:.1f}%",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
        )

    def calculate_return_on_assets(self) -> RatioResult:
        """Return on Assets (ROA) = Net Income / Total Assets × 100%.

        Sprint 27: Measures how efficiently a company uses its assets to generate profit.
        """
        if self.totals.total_assets == 0:
            return RatioResult(
                name="Return on Assets",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No assets identified",
                health_status="neutral",
            )

        # Net Income = Revenue - Total Expenses
        net_income = self.totals.total_revenue - self.totals.total_expenses
        roa = (net_income / self.totals.total_assets) * 100

        # Interpretation thresholds (industry-generic)
        if roa >= 15:
            health = "healthy"
            interpretation = "Excellent asset utilization"
        elif roa >= 10:
            health = "healthy"
            interpretation = "Strong return on assets"
        elif roa >= 5:
            health = "healthy"
            interpretation = "Adequate asset efficiency"
        elif roa >= 0:
            health = "warning"
            interpretation = "Low asset efficiency - review asset utilization"
        else:
            health = "concern"
            interpretation = "Negative ROA - assets generating losses"

        return RatioResult(
            name="Return on Assets",
            value=round(roa, 1),
            display_value=f"{roa:.1f}%",
            is_calculable=True,
            interpretation=interpretation,
            health_status=health,
        )

    def calculate_return_on_equity(self) -> RatioResult:
        """Return on Equity (ROE) = Net Income / Total Equity × 100%.

        Sprint 27: Measures profitability relative to shareholders' equity.
        Key metric for investors evaluating management effectiveness.
        """
        if self.totals.total_equity == 0:
            return RatioResult(
                name="Return on Equity",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No equity identified",
                health_status="neutral",
            )

        # Net Income = Revenue - Total Expenses
        net_income = self.totals.total_revenue - self.totals.total_expenses
        roe = (net_income / self.totals.total_equity) * 100

        # Handle negative equity case (technical insolvency)
        if self.totals.total_equity < 0:
            # With negative equity, a positive ROE actually means losses
            if roe > 0:
                return RatioResult(
                    name="Return on Equity",
                    value=round(roe, 1),
                    display_value=f"{roe:.1f}%",
                    is_calculable=True,
                    interpretation="Warning: Negative equity with losses",
                    health_status="concern",
                )

        # Interpretation thresholds (industry-generic)
        if roe >= 20:
            health = "healthy"
            interpretation = "Excellent return for shareholders"
        elif roe >= 15:
            health = "healthy"
            interpretation = "Strong return on equity"
        elif roe >= 10:
            health = "healthy"
            interpretation = "Adequate shareholder returns"
        elif roe >= 0:
            health = "warning"
            interpretation = "Below-average returns - review profitability"
        else:
            health = "concern"
            interpretation = "Negative ROE - equity generating losses"

        return RatioResult(
            name="Return on Equity",
            value=round(roe, 1),
            display_value=f"{roe:.1f}%",
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
            "net_profit_margin": self.calculate_net_profit_margin(),
            "operating_margin": self.calculate_operating_margin(),
            "return_on_assets": self.calculate_return_on_assets(),
            "return_on_equity": self.calculate_return_on_equity(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Return all ratios as a serializable dictionary."""
        ratios = self.calculate_all_ratios()
        return {key: ratio.to_dict() for key, ratio in ratios.items()}


class CommonSizeAnalyzer:
    """Expresses items as percentages of a base (Total Assets or Revenue)."""

    def __init__(self, category_totals: CategoryTotals):
        self.totals = category_totals

    def balance_sheet_percentages(self) -> Dict[str, float]:
        """Express balance sheet items as percentage of Total Assets."""
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
        """Express income statement items as percentage of Revenue."""
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
    """Compare current vs previous diagnostic runs using aggregate totals."""

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
        """Calculate variance between current and previous values."""
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
        """Calculate variances for all category totals. Returns empty dict if no previous data."""
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

# Sprint 26: Keywords for Operating Expenses identification
OPERATING_EXPENSE_KEYWORDS = [
    'salary', 'salaries', 'wage', 'wages', 'payroll',
    'rent', 'lease', 'utilities', 'utility',
    'insurance', 'depreciation', 'amortization',
    'office', 'supplies', 'maintenance', 'repair',
    'advertising', 'marketing', 'promotion',
    'travel', 'entertainment', 'meals',
    'professional fee', 'legal', 'accounting', 'consulting',
    'telephone', 'internet', 'communication',
    'training', 'education', 'subscription',
    'bank fee', 'bank charge', 'service charge',
    'operating', 'administrative', 'general expense', 'g&a',
    'selling expense', 'distribution',
]

# Keywords that indicate NON-operating expenses (exclude from operating expenses)
NON_OPERATING_KEYWORDS = [
    'interest expense', 'interest payment',
    'tax', 'income tax', 'tax expense',
    'extraordinary', 'unusual', 'non-recurring',
    'loss on sale', 'loss on disposal', 'impairment',
    'discontinued', 'restructuring',
]


def extract_category_totals(
    account_balances: Dict[str, Dict[str, float]],
    classified_accounts: Dict[str, str]
) -> CategoryTotals:
    """Extract aggregate category totals from account balances."""
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
            # Sprint 26: Check if Operating Expense (not COGS, not non-operating)
            elif any(kw in account_lower for kw in OPERATING_EXPENSE_KEYWORDS):
                # Exclude non-operating items
                if not any(kw in account_lower for kw in NON_OPERATING_KEYWORDS):
                    totals.operating_expenses += amount

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
    """Calculate all analytics (ratios, common-size, variances)."""
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
