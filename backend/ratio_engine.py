"""
Financial ratio calculations and analysis using standard accounting formulas.

IFRS/GAAP Compatibility Notes:
-----------------------------
These ratios are calculated using standard formulas applicable under both US GAAP
and IFRS. However, the underlying account classifications may differ between
frameworks, particularly for:

- Inventory valuation (LIFO permitted under US GAAP, prohibited under IFRS)
- Asset revaluations (permitted under IFRS, prohibited under US GAAP)
- Lease accounting (converged post-2019, but presentation differences remain)
- R&D capitalization (IFRS permits development cost capitalization)
- Provision recognition thresholds (IFRS has lower threshold)

See docs/STANDARDS.md for detailed framework comparison.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Optional

from security_utils import log_secure_operation
from shared.monetary import quantize_monetary

# =============================================================================
# Threshold Constants
# =============================================================================

DAYS_IN_YEAR = 365

# Current Ratio thresholds
CURRENT_RATIO_STRONG = 2.0
CURRENT_RATIO_ADEQUATE = 1.0
CURRENT_RATIO_WARNING = 0.5

# Quick Ratio thresholds
QUICK_RATIO_STRONG = 1.0
QUICK_RATIO_WARNING = 0.5

# Debt-to-Equity thresholds
DTE_CONSERVATIVE = 0.5
DTE_BALANCED = 1.0
DTE_MODERATE = 2.0

# Gross Margin thresholds (%)
GROSS_MARGIN_STRONG = 50
GROSS_MARGIN_MODERATE = 30
GROSS_MARGIN_LOW = 15

# Net Profit Margin thresholds (%)
NET_MARGIN_STRONG = 20
NET_MARGIN_MODERATE = 10
NET_MARGIN_LOW = 5

# Operating Margin thresholds (%)
OP_MARGIN_STRONG = 25
OP_MARGIN_MODERATE = 15
OP_MARGIN_ADEQUATE = 10
OP_MARGIN_LOW = 5

# ROA thresholds (%)
ROA_STRONG = 15
ROA_MODERATE = 10
ROA_ADEQUATE = 5

# ROE thresholds (%)
ROE_STRONG = 20
ROE_MODERATE = 15
ROE_ADEQUATE = 10

# DSO thresholds (days)
DSO_EXCELLENT = 30
DSO_GOOD = 45
DSO_MODERATE = 60
DSO_POOR = 90

# DPO thresholds (industry-generic)
DPO_EXCELLENT = 30
DPO_MODERATE = 60
DPO_EXTENDED = 90

# DIO thresholds (industry-generic)
DIO_EXCELLENT = 30
DIO_MODERATE = 60
DIO_EXTENDED = 90

# CCC threshold — negative CCC below this signals aggressive financing
CCC_NEGATIVE_THRESHOLD = -30

# Equity Ratio thresholds
EQUITY_RATIO_STRONG = 0.5
EQUITY_RATIO_MODERATE = 0.3

# Long-Term Debt Ratio thresholds (lower is better)
LT_DEBT_CONSERVATIVE = 0.2
LT_DEBT_MODERATE = 0.4

# Asset Turnover thresholds (higher is better)
ASSET_TURNOVER_STRONG = 2.0
ASSET_TURNOVER_ADEQUATE = 1.0

# Inventory Turnover thresholds (times/year, higher is better)
INV_TURNOVER_STRONG = 8.0
INV_TURNOVER_ADEQUATE = 4.0

# Receivables Turnover thresholds (times/year, higher is better)
REC_TURNOVER_STRONG = 12.0
REC_TURNOVER_ADEQUATE = 6.0

# Momentum classification thresholds (percentage points)
MOMENTUM_ACCELERATION = 2.0
MOMENTUM_CHANGE = 1.0

# Confidence scoring stddev thresholds
STDDEV_HIGH_CONFIDENCE = 5
STDDEV_MEDIUM_CONFIDENCE = 10
STDDEV_LOW_CONFIDENCE = 20


class TrendDirection(str, Enum):
    """Direction of change for variance calculations."""

    POSITIVE = "positive"  # Favorable change
    NEGATIVE = "negative"  # Unfavorable change
    NEUTRAL = "neutral"  # No significant change


@dataclass
class RatioResult:
    """Result of a ratio calculation with interpretation."""

    name: str
    value: Optional[float]
    display_value: str
    is_calculable: bool
    interpretation: str
    threshold_status: str  # "above_threshold", "at_threshold", "below_threshold", "neutral"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "display_value": self.display_value,
            "is_calculable": self.is_calculable,
            "interpretation": self.interpretation,
            "threshold_status": self.threshold_status,
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

    def to_dict(self) -> dict[str, Any]:
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
    accounts_receivable: float = 0.0  # Sprint 53: For DSO calculation
    accounts_payable: float = 0.0  # Sprint 293: For DPO calculation
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    total_equity: float = 0.0
    total_revenue: float = 0.0
    cost_of_goods_sold: float = 0.0
    total_expenses: float = 0.0
    operating_expenses: float = 0.0  # Sprint 26: For Operating Profit Margin

    def to_dict(self) -> dict[str, float]:
        return {
            "total_assets": float(quantize_monetary(self.total_assets)),
            "current_assets": float(quantize_monetary(self.current_assets)),
            "inventory": float(quantize_monetary(self.inventory)),
            "accounts_receivable": float(quantize_monetary(self.accounts_receivable)),
            "accounts_payable": float(quantize_monetary(self.accounts_payable)),
            "total_liabilities": float(quantize_monetary(self.total_liabilities)),
            "current_liabilities": float(quantize_monetary(self.current_liabilities)),
            "total_equity": float(quantize_monetary(self.total_equity)),
            "total_revenue": float(quantize_monetary(self.total_revenue)),
            "cost_of_goods_sold": float(quantize_monetary(self.cost_of_goods_sold)),
            "total_expenses": float(quantize_monetary(self.total_expenses)),
            "operating_expenses": float(quantize_monetary(self.operating_expenses)),
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "CategoryTotals":
        return cls(
            total_assets=data.get("total_assets", 0.0),
            current_assets=data.get("current_assets", 0.0),
            inventory=data.get("inventory", 0.0),
            accounts_receivable=data.get("accounts_receivable", 0.0),
            accounts_payable=data.get("accounts_payable", 0.0),
            total_liabilities=data.get("total_liabilities", 0.0),
            current_liabilities=data.get("current_liabilities", 0.0),
            total_equity=data.get("total_equity", 0.0),
            total_revenue=data.get("total_revenue", 0.0),
            cost_of_goods_sold=data.get("cost_of_goods_sold", 0.0),
            total_expenses=data.get("total_expenses", 0.0),
            operating_expenses=data.get("operating_expenses", 0.0),
        )


@dataclass
class DupontDecomposition:
    """Three-component DuPont decomposition of Return on Equity."""

    net_profit_margin: float
    asset_turnover: float
    equity_multiplier: float
    decomposed_roe: float
    verification_matches: bool
    prior_period_deltas: Optional[dict[str, float]] = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "net_profit_margin": round(self.net_profit_margin, 4),
            "asset_turnover": round(self.asset_turnover, 4),
            "equity_multiplier": round(self.equity_multiplier, 4),
            "decomposed_roe": round(self.decomposed_roe, 4),
            "verification_matches": self.verification_matches,
        }
        if self.prior_period_deltas is not None:
            result["prior_period_deltas"] = {k: round(v, 4) for k, v in self.prior_period_deltas.items()}
        return result


class RatioEngine:
    """Calculates standard financial ratios from category totals."""

    def __init__(self, category_totals: CategoryTotals):
        self.totals = category_totals
        log_secure_operation(
            "ratio_engine_init", f"Initializing ratio calculations with totals: {category_totals.to_dict()}"
        )

    def calculate_current_ratio(self) -> RatioResult:
        """
        Current Ratio = Current Assets / Current Liabilities.

        Measures short-term liquidity - ability to pay obligations due within one year.

        IFRS/GAAP Note:
        - Both frameworks require current/non-current classification
        - IFRS allows liquidity-based presentation as alternative
        - Operating cycle definition is consistent across standards
        - Threshold: Generally, ratio >= 1.0 indicates adequate liquidity
        """
        if self.totals.current_liabilities == 0:
            return RatioResult(
                name="Current Ratio",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No current liabilities identified",
                threshold_status="neutral",
            )

        ratio = self.totals.current_assets / self.totals.current_liabilities

        # Interpretation thresholds (standard financial analysis)
        if ratio >= CURRENT_RATIO_STRONG:
            health = "above_threshold"
            interpretation = "Strong liquidity position"
        elif ratio >= CURRENT_RATIO_ADEQUATE:
            health = "above_threshold"
            interpretation = "Adequate liquidity to cover short-term obligations"
        elif ratio >= CURRENT_RATIO_WARNING:
            health = "at_threshold"
            interpretation = "May have difficulty covering short-term obligations"
        else:
            health = "below_threshold"
            interpretation = "Potential liquidity risk"

        return RatioResult(
            name="Current Ratio",
            value=round(ratio, 2),
            display_value=f"{ratio:.2f}",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_quick_ratio(self) -> RatioResult:
        """
        Quick Ratio = (Current Assets - Inventory) / Current Liabilities.

        Also known as the "Acid Test" ratio. More conservative than current ratio
        as it excludes inventory which may not be quickly convertible to cash.

        IFRS/GAAP Note:
        - LIFO inventory (US GAAP only) may understate inventory, inflating this ratio
        - IFRS prohibits LIFO, requiring FIFO or weighted average
        - When comparing LIFO companies to IFRS, consider LIFO reserve adjustment
        - Threshold: Generally, ratio >= 1.0 indicates strong liquidity
        """
        if self.totals.current_liabilities == 0:
            return RatioResult(
                name="Quick Ratio",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No current liabilities identified",
                threshold_status="neutral",
            )

        quick_assets = self.totals.current_assets - self.totals.inventory
        ratio = quick_assets / self.totals.current_liabilities

        # Interpretation thresholds
        if ratio >= QUICK_RATIO_STRONG:
            health = "above_threshold"
            interpretation = "Strong quick liquidity position"
        elif ratio >= QUICK_RATIO_WARNING:
            health = "at_threshold"
            interpretation = "Moderate liquidity without inventory liquidation"
        else:
            health = "below_threshold"
            interpretation = "May need to liquidate inventory to cover obligations"

        return RatioResult(
            name="Quick Ratio",
            value=round(ratio, 2),
            display_value=f"{ratio:.2f}",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_debt_to_equity(self) -> RatioResult:
        """
        Debt-to-Equity = Total Liabilities / Total Equity.

        Measures financial leverage and long-term solvency. Higher ratios indicate
        greater reliance on debt financing.

        IFRS/GAAP Note:
        - Redeemable preferred stock may be liability (IFRS) vs equity (US GAAP)
        - Compound instruments split differently between frameworks
        - Asset revaluations (IFRS only) increase equity, reducing this ratio
        - Industry norms vary significantly (utilities vs tech)
        - Threshold: Generally, ratio <= 2.0 is considered manageable
        """
        if self.totals.total_equity == 0:
            return RatioResult(
                name="Debt-to-Equity",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No equity identified",
                threshold_status="neutral",
            )

        ratio = self.totals.total_liabilities / self.totals.total_equity

        # Interpretation (varies by industry, using general guidelines)
        if ratio <= DTE_CONSERVATIVE:
            health = "above_threshold"
            interpretation = "Conservative leverage position"
        elif ratio <= DTE_BALANCED:
            health = "above_threshold"
            interpretation = "Balanced debt and equity financing"
        elif ratio <= DTE_MODERATE:
            health = "at_threshold"
            interpretation = "Moderately leveraged"
        else:
            health = "below_threshold"
            interpretation = "High financial leverage"

        return RatioResult(
            name="Debt-to-Equity",
            value=round(ratio, 2),
            display_value=f"{ratio:.2f}",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_gross_margin(self) -> RatioResult:
        """
        Gross Margin = (Revenue - COGS) / Revenue × 100%.

        Measures profitability before operating expenses. Indicates pricing power
        and production efficiency.

        IFRS/GAAP Note:
        - Revenue recognition largely converged (ASC 606 / IFRS 15) since 2018
        - COGS composition generally consistent across frameworks
        - Freight-out costs may be in COGS (IFRS) or operating expenses (US GAAP)
        - LIFO vs FIFO inventory affects COGS differently
        - Threshold: Industry-dependent; generally >= 30% is healthy
        """
        if self.totals.total_revenue == 0:
            return RatioResult(
                name="Gross Margin",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No revenue identified",
                threshold_status="neutral",
            )

        gross_profit = self.totals.total_revenue - self.totals.cost_of_goods_sold
        margin = (gross_profit / self.totals.total_revenue) * 100

        # Interpretation (varies significantly by industry)
        if margin >= GROSS_MARGIN_STRONG:
            health = "above_threshold"
            interpretation = "Strong gross margin"
        elif margin >= GROSS_MARGIN_MODERATE:
            health = "above_threshold"
            interpretation = "Healthy gross margin"
        elif margin >= GROSS_MARGIN_LOW:
            health = "at_threshold"
            interpretation = "Moderate gross margin"
        else:
            health = "below_threshold"
            interpretation = "Low gross margin - review pricing/costs"

        return RatioResult(
            name="Gross Margin",
            value=round(margin, 1),
            display_value=f"{margin:.1f}%",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_net_profit_margin(self) -> RatioResult:
        """
        Net Profit Margin = (Revenue - Total Expenses) / Revenue × 100%.

        Measures bottom-line profitability after all expenses including interest
        and taxes. The ultimate measure of operational efficiency.

        IFRS/GAAP Note:
        - Extraordinary items prohibited under both frameworks (post-2015)
        - R&D capitalization (IFRS) can shift costs between periods
        - Interest classification may differ (operating vs financing)
        - Tax provisions may differ due to recognition thresholds
        - Threshold: Industry-dependent; generally >= 10% is healthy
        """
        if self.totals.total_revenue == 0:
            return RatioResult(
                name="Net Profit Margin",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No revenue identified",
                threshold_status="neutral",
            )

        net_income = self.totals.total_revenue - self.totals.total_expenses
        margin = (net_income / self.totals.total_revenue) * 100

        # Interpretation thresholds (industry-generic)
        if margin >= NET_MARGIN_STRONG:
            health = "above_threshold"
            interpretation = "Excellent profitability"
        elif margin >= NET_MARGIN_MODERATE:
            health = "above_threshold"
            interpretation = "Healthy net profit margin"
        elif margin >= NET_MARGIN_LOW:
            health = "at_threshold"
            interpretation = "Moderate profitability - monitor expenses"
        elif margin >= 0:
            health = "at_threshold"
            interpretation = "Low profitability - cost control needed"
        else:
            health = "below_threshold"
            interpretation = "Operating at a loss"

        return RatioResult(
            name="Net Profit Margin",
            value=round(margin, 1),
            display_value=f"{margin:.1f}%",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_operating_margin(self) -> RatioResult:
        """
        Operating Margin = (Revenue - COGS - Operating Expenses) / Revenue × 100%.

        Measures profitability from core operations before interest and taxes.
        Also known as EBIT margin when interest/taxes are excluded.

        IFRS/GAAP Note:
        - Neither framework requires a specific "operating profit" line item
        - R&D costs expensed (US GAAP) vs potentially capitalized (IFRS)
        - Lease expense presentation differs: single expense (US GAAP operating)
          vs depreciation + interest (IFRS 16 for most leases)
        - Foreign exchange treatment may differ in operating vs non-operating
        - Threshold: Industry-dependent; generally >= 15% indicates efficiency
        """
        if self.totals.total_revenue == 0:
            return RatioResult(
                name="Operating Margin",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No revenue identified",
                threshold_status="neutral",
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
        if margin >= OP_MARGIN_STRONG:
            health = "above_threshold"
            interpretation = "Excellent operating efficiency"
        elif margin >= OP_MARGIN_MODERATE:
            health = "above_threshold"
            interpretation = "Strong operating margin"
        elif margin >= OP_MARGIN_ADEQUATE:
            health = "above_threshold"
            interpretation = "Adequate operating margin"
        elif margin >= OP_MARGIN_LOW:
            health = "at_threshold"
            interpretation = "Thin operating margin - review costs"
        elif margin >= 0:
            health = "at_threshold"
            interpretation = "Minimal operating profit"
        else:
            health = "below_threshold"
            interpretation = "Operating loss - immediate attention needed"

        return RatioResult(
            name="Operating Margin",
            value=round(margin, 1),
            display_value=f"{margin:.1f}%",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_return_on_assets(self) -> RatioResult:
        """
        Return on Assets (ROA) = Net Income / Total Assets × 100%.

        Measures how efficiently a company uses its assets to generate profit.
        Key indicator of management effectiveness in deploying capital.

        IFRS/GAAP Note:
        - Asset revaluations (IFRS permitted) inflate asset base, reducing ROA
        - Impairment reversals (IFRS permitted) can increase asset values
        - R&D capitalization (IFRS) increases assets vs expensing (US GAAP)
        - Right-of-use assets (both frameworks post-2019) inflate total assets
        - Historical cost (US GAAP) provides more consistent trend analysis
        - Threshold: Industry-dependent; generally >= 5% is adequate
        """
        if self.totals.total_assets == 0:
            return RatioResult(
                name="Return on Assets",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No assets identified",
                threshold_status="neutral",
            )

        # Net Income = Revenue - Total Expenses
        net_income = self.totals.total_revenue - self.totals.total_expenses
        roa = (net_income / self.totals.total_assets) * 100

        # Interpretation thresholds (industry-generic)
        if roa >= ROA_STRONG:
            health = "above_threshold"
            interpretation = "Excellent asset utilization"
        elif roa >= ROA_MODERATE:
            health = "above_threshold"
            interpretation = "Strong return on assets"
        elif roa >= ROA_ADEQUATE:
            health = "above_threshold"
            interpretation = "Adequate asset efficiency"
        elif roa >= 0:
            health = "at_threshold"
            interpretation = "Low asset efficiency - review asset utilization"
        else:
            health = "below_threshold"
            interpretation = "Negative ROA - assets generating losses"

        return RatioResult(
            name="Return on Assets",
            value=round(roa, 1),
            display_value=f"{roa:.1f}%",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_return_on_equity(self) -> RatioResult:
        """
        Return on Equity (ROE) = Net Income / Total Equity × 100%.

        Measures profitability relative to shareholders' equity. Key metric for
        investors evaluating management effectiveness and shareholder value creation.

        IFRS/GAAP Note:
        - Revaluation surplus (IFRS) in equity may inflate denominator
        - OCI reclassification (recycling) rules differ between frameworks
        - Actuarial gains/losses: recycled (US GAAP) vs not recycled (IFRS)
        - Preferred stock classification affects equity composition
        - Treasury stock treatment is consistent (contra-equity)
        - Threshold: Generally >= 15% indicates strong shareholder returns
        """
        if self.totals.total_equity == 0:
            return RatioResult(
                name="Return on Equity",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No equity identified",
                threshold_status="neutral",
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
                    threshold_status="below_threshold",
                )

        # Interpretation thresholds (industry-generic)
        if roe >= ROE_STRONG:
            health = "above_threshold"
            interpretation = "Excellent return for shareholders"
        elif roe >= ROE_MODERATE:
            health = "above_threshold"
            interpretation = "Strong return on equity"
        elif roe >= ROE_ADEQUATE:
            health = "above_threshold"
            interpretation = "Adequate shareholder returns"
        elif roe >= 0:
            health = "at_threshold"
            interpretation = "Below-average returns - review profitability"
        else:
            health = "below_threshold"
            interpretation = "Negative ROE - equity generating losses"

        return RatioResult(
            name="Return on Equity",
            value=round(roe, 1),
            display_value=f"{roe:.1f}%",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_dso(self) -> RatioResult:
        """
        Days Sales Outstanding (DSO) = (Accounts Receivable / Revenue) × 365.

        Measures the average number of days to collect payment after a sale.
        Lower DSO indicates faster collection and better cash flow management.

        Sprint 53 - Phase IV: Activity/Efficiency Ratio

        IFRS/GAAP Note:
        - Revenue recognition timing affects calculation (IFRS 15 / ASC 606)
        - Use average receivables for more accuracy if multiple periods available
        - Allowance for doubtful accounts should use net receivables
        - Consider seasonality when interpreting results
        - Industry benchmarks vary significantly (30-90 days typical)
        """
        if self.totals.total_revenue == 0:
            return RatioResult(
                name="Days Sales Outstanding",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No revenue identified",
                threshold_status="neutral",
            )

        if self.totals.accounts_receivable == 0:
            return RatioResult(
                name="Days Sales Outstanding",
                value=0.0,
                display_value="0 days",
                is_calculable=True,
                interpretation="No accounts receivable - cash basis or fully collected",
                threshold_status="above_threshold",
            )

        dso = (self.totals.accounts_receivable / self.totals.total_revenue) * DAYS_IN_YEAR

        # Interpretation thresholds (industry-generic)
        if dso <= DSO_EXCELLENT:
            health = "above_threshold"
            interpretation = "Excellent collection efficiency"
        elif dso <= DSO_GOOD:
            health = "above_threshold"
            interpretation = "Good collection performance"
        elif dso <= DSO_MODERATE:
            health = "at_threshold"
            interpretation = "Average collection - monitor aging"
        elif dso <= DSO_POOR:
            health = "at_threshold"
            interpretation = "Slow collections - review credit policies"
        else:
            health = "below_threshold"
            interpretation = "Extended collection period - cash flow risk"

        return RatioResult(
            name="Days Sales Outstanding",
            value=round(dso, 1),
            display_value=f"{dso:.0f} days",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_dpo(self) -> RatioResult:
        """
        Days Payable Outstanding (DPO) = (Accounts Payable / COGS) × 365.

        Measures the average number of days to pay suppliers.
        Higher DPO indicates slower payment, preserving cash.

        Sprint 293 - Phase XL: Cash Conversion Cycle
        """
        if self.totals.cost_of_goods_sold == 0:
            return RatioResult(
                name="Days Payable Outstanding",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No cost of goods sold identified",
                threshold_status="neutral",
            )

        if self.totals.accounts_payable == 0:
            return RatioResult(
                name="Days Payable Outstanding",
                value=0.0,
                display_value="0 days",
                is_calculable=True,
                interpretation="No accounts payable identified",
                threshold_status="neutral",
            )

        dpo = (self.totals.accounts_payable / self.totals.cost_of_goods_sold) * DAYS_IN_YEAR

        if dpo <= DPO_EXCELLENT:
            health = "above_threshold"
            interpretation = "Rapid payment cycle"
        elif dpo <= DPO_MODERATE:
            health = "above_threshold"
            interpretation = "Standard payment cycle"
        elif dpo <= DPO_EXTENDED:
            health = "at_threshold"
            interpretation = "Extended payment cycle"
        else:
            health = "below_threshold"
            interpretation = "Significantly extended payment cycle"

        return RatioResult(
            name="Days Payable Outstanding",
            value=round(dpo, 1),
            display_value=f"{dpo:.0f} days",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_dio(self) -> RatioResult:
        """
        Days Inventory Outstanding (DIO) = (Inventory / COGS) × 365.

        Measures the average number of days inventory is held before sale.
        Lower DIO indicates faster inventory turnover.

        Sprint 293 - Phase XL: Cash Conversion Cycle
        """
        if self.totals.cost_of_goods_sold == 0:
            return RatioResult(
                name="Days Inventory Outstanding",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No cost of goods sold identified",
                threshold_status="neutral",
            )

        if self.totals.inventory == 0:
            return RatioResult(
                name="Days Inventory Outstanding",
                value=0.0,
                display_value="0 days",
                is_calculable=True,
                interpretation="No inventory identified",
                threshold_status="neutral",
            )

        dio = (self.totals.inventory / self.totals.cost_of_goods_sold) * DAYS_IN_YEAR

        if dio <= DIO_EXCELLENT:
            health = "above_threshold"
            interpretation = "Rapid inventory turnover"
        elif dio <= DIO_MODERATE:
            health = "above_threshold"
            interpretation = "Standard inventory turnover"
        elif dio <= DIO_EXTENDED:
            health = "at_threshold"
            interpretation = "Extended inventory holding period"
        else:
            health = "below_threshold"
            interpretation = "Significantly extended inventory holding period"

        return RatioResult(
            name="Days Inventory Outstanding",
            value=round(dio, 1),
            display_value=f"{dio:.0f} days",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_ccc(self) -> RatioResult:
        """
        Cash Conversion Cycle (CCC) = DIO + DSO - DPO.

        Measures the total days from cash outlay (inventory purchase) to
        cash receipt (customer payment). Lower CCC indicates faster cash
        recovery. Negative CCC means the company collects before paying.

        Sprint 293 - Phase XL: Cash Conversion Cycle
        """
        dso_result = self.calculate_dso()
        dpo_result = self.calculate_dpo()
        dio_result = self.calculate_dio()

        # Need at least DSO and one of DPO/DIO to be calculable
        if not dso_result.is_calculable:
            return RatioResult(
                name="Cash Conversion Cycle",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: DSO unavailable (no revenue)",
                threshold_status="neutral",
            )

        dso_val = dso_result.value or 0.0
        dpo_val = dpo_result.value or 0.0 if dpo_result.is_calculable else 0.0
        dio_val = dio_result.value or 0.0 if dio_result.is_calculable else 0.0

        ccc = dio_val + dso_val - dpo_val

        if ccc < CCC_NEGATIVE_THRESHOLD:
            health = "at_threshold"
            interpretation = "Significantly negative cycle — aggressive supplier financing"
        elif ccc < 0:
            health = "above_threshold"
            interpretation = "Negative cycle — cash collected before supplier payment due"
        elif ccc <= 30:
            health = "above_threshold"
            interpretation = "Short cash cycle"
        elif ccc <= 60:
            health = "above_threshold"
            interpretation = "Standard cash cycle"
        elif ccc <= 90:
            health = "at_threshold"
            interpretation = "Extended cash cycle"
        else:
            health = "below_threshold"
            interpretation = "Long cash cycle — significant working capital tied up"

        return RatioResult(
            name="Cash Conversion Cycle",
            value=round(ccc, 1),
            display_value=f"{ccc:.0f} days",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_equity_ratio(self) -> RatioResult:
        """
        Equity Ratio = Total Equity / Total Assets.

        Measures the proportion of total assets financed by shareholders' equity.
        Higher ratio indicates greater financial stability and lower reliance on debt.

        Thresholds: Strong >=0.5, Moderate >=0.3, Low <0.3
        """
        if self.totals.total_assets == 0:
            return RatioResult(
                name="Equity Ratio",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No assets identified",
                threshold_status="neutral",
            )

        ratio = self.totals.total_equity / self.totals.total_assets

        if ratio >= EQUITY_RATIO_STRONG:
            health = "above_threshold"
            interpretation = "Strong equity position relative to assets"
        elif ratio >= EQUITY_RATIO_MODERATE:
            health = "at_threshold"
            interpretation = "Moderate equity financing"
        else:
            health = "below_threshold"
            interpretation = "Low equity ratio - high reliance on debt financing"

        return RatioResult(
            name="Equity Ratio",
            value=round(ratio, 2),
            display_value=f"{ratio:.2f}",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_long_term_debt_ratio(self) -> RatioResult:
        """
        Long-Term Debt Ratio = (Total Liabilities - Current Liabilities) / Total Assets.

        Measures the proportion of assets financed by long-term debt.
        Lower is better, indicating less long-term leverage.

        Thresholds: Conservative <=0.2, Moderate <=0.4, High >0.4
        """
        if self.totals.total_assets == 0:
            return RatioResult(
                name="Long-Term Debt Ratio",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No assets identified",
                threshold_status="neutral",
            )

        long_term_debt = self.totals.total_liabilities - self.totals.current_liabilities
        ratio = long_term_debt / self.totals.total_assets

        if ratio <= LT_DEBT_CONSERVATIVE:
            health = "above_threshold"
            interpretation = "Conservative long-term debt position"
        elif ratio <= LT_DEBT_MODERATE:
            health = "at_threshold"
            interpretation = "Moderate long-term debt level"
        else:
            health = "below_threshold"
            interpretation = "High long-term debt relative to assets"

        return RatioResult(
            name="Long-Term Debt Ratio",
            value=round(ratio, 2),
            display_value=f"{ratio:.2f}",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_asset_turnover(self) -> RatioResult:
        """
        Asset Turnover = Total Revenue / Total Assets.

        Measures how efficiently assets are used to generate revenue.
        Higher is better, indicating more efficient asset utilization.

        Thresholds: Strong >=2.0, Adequate >=1.0, Low <1.0
        """
        if self.totals.total_assets == 0:
            return RatioResult(
                name="Asset Turnover",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No assets identified",
                threshold_status="neutral",
            )

        ratio = self.totals.total_revenue / self.totals.total_assets

        if ratio >= ASSET_TURNOVER_STRONG:
            health = "above_threshold"
            interpretation = "Strong asset utilization efficiency"
        elif ratio >= ASSET_TURNOVER_ADEQUATE:
            health = "at_threshold"
            interpretation = "Adequate asset turnover"
        else:
            health = "below_threshold"
            interpretation = "Low asset turnover - assets underutilized"

        return RatioResult(
            name="Asset Turnover",
            value=round(ratio, 2),
            display_value=f"{ratio:.2f}x",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_inventory_turnover(self) -> RatioResult:
        """
        Inventory Turnover = COGS / Inventory (times/year).

        Measures how many times inventory is sold and replaced in a period.
        Higher is better, indicating efficient inventory management.

        Thresholds: Strong >=8, Adequate >=4, Low <4
        """
        if self.totals.inventory == 0:
            return RatioResult(
                name="Inventory Turnover",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No inventory identified",
                threshold_status="neutral",
            )

        if self.totals.cost_of_goods_sold == 0:
            return RatioResult(
                name="Inventory Turnover",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No cost of goods sold identified",
                threshold_status="neutral",
            )

        ratio = self.totals.cost_of_goods_sold / self.totals.inventory

        if ratio >= INV_TURNOVER_STRONG:
            health = "above_threshold"
            interpretation = "Strong inventory turnover"
        elif ratio >= INV_TURNOVER_ADEQUATE:
            health = "at_threshold"
            interpretation = "Adequate inventory turnover"
        else:
            health = "below_threshold"
            interpretation = "Low inventory turnover - potential overstock or obsolescence"

        return RatioResult(
            name="Inventory Turnover",
            value=round(ratio, 2),
            display_value=f"{ratio:.2f}x",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_receivables_turnover(self) -> RatioResult:
        """
        Receivables Turnover = Revenue / Accounts Receivable (times/year).

        Measures how efficiently receivables are collected.
        Higher is better, indicating faster collection.

        Thresholds: Strong >=12, Adequate >=6, Low <6
        """
        if self.totals.accounts_receivable == 0:
            return RatioResult(
                name="Receivables Turnover",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No accounts receivable identified",
                threshold_status="neutral",
            )

        if self.totals.total_revenue == 0:
            return RatioResult(
                name="Receivables Turnover",
                value=None,
                display_value="N/A",
                is_calculable=False,
                interpretation="Cannot calculate: No revenue identified",
                threshold_status="neutral",
            )

        ratio = self.totals.total_revenue / self.totals.accounts_receivable

        if ratio >= REC_TURNOVER_STRONG:
            health = "above_threshold"
            interpretation = "Strong receivables collection efficiency"
        elif ratio >= REC_TURNOVER_ADEQUATE:
            health = "at_threshold"
            interpretation = "Adequate receivables turnover"
        else:
            health = "below_threshold"
            interpretation = "Low receivables turnover - review collection policies"

        return RatioResult(
            name="Receivables Turnover",
            value=round(ratio, 2),
            display_value=f"{ratio:.2f}x",
            is_calculable=True,
            interpretation=interpretation,
            threshold_status=health,
        )

    def calculate_dupont(
        self,
        previous_totals: Optional[CategoryTotals] = None,
    ) -> Optional[DupontDecomposition]:
        """
        Three-component DuPont decomposition of Return on Equity.

        ROE = Net Profit Margin × Asset Turnover × Equity Multiplier

        Components:
        - Net Profit Margin = Net Income / Revenue
        - Asset Turnover = Revenue / Total Assets
        - Equity Multiplier = Total Assets / Total Equity

        Returns None if any denominator is zero.
        """
        if self.totals.total_revenue == 0 or self.totals.total_assets == 0 or self.totals.total_equity == 0:
            return None

        net_income = self.totals.total_revenue - self.totals.total_expenses

        net_profit_margin = net_income / self.totals.total_revenue
        asset_turnover = self.totals.total_revenue / self.totals.total_assets
        equity_multiplier = self.totals.total_assets / self.totals.total_equity
        decomposed_roe = net_profit_margin * asset_turnover * equity_multiplier

        # Verify against direct ROE calculation
        roe_result = self.calculate_return_on_equity()
        direct_roe = roe_result.value / 100.0 if roe_result.is_calculable and roe_result.value is not None else None
        verification_matches = direct_roe is not None and abs(decomposed_roe - direct_roe) < 0.0001

        # Calculate prior period deltas if previous_totals provided
        prior_period_deltas: Optional[dict[str, float]] = None
        if previous_totals is not None and (
            previous_totals.total_revenue != 0
            and previous_totals.total_assets != 0
            and previous_totals.total_equity != 0
        ):
            prev_net_income = previous_totals.total_revenue - previous_totals.total_expenses
            prev_npm = prev_net_income / previous_totals.total_revenue
            prev_at = previous_totals.total_revenue / previous_totals.total_assets
            prev_em = previous_totals.total_assets / previous_totals.total_equity
            prev_roe = prev_npm * prev_at * prev_em

            prior_period_deltas = {
                "net_profit_margin_delta": round(net_profit_margin - prev_npm, 4),
                "asset_turnover_delta": round(asset_turnover - prev_at, 4),
                "equity_multiplier_delta": round(equity_multiplier - prev_em, 4),
                "decomposed_roe_delta": round(decomposed_roe - prev_roe, 4),
            }

        return DupontDecomposition(
            net_profit_margin=round(net_profit_margin, 4),
            asset_turnover=round(asset_turnover, 4),
            equity_multiplier=round(equity_multiplier, 4),
            decomposed_roe=round(decomposed_roe, 4),
            verification_matches=verification_matches,
            prior_period_deltas=prior_period_deltas,
        )

    def calculate_all_ratios(self) -> dict[str, RatioResult]:
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
            "dso": self.calculate_dso(),  # Sprint 53: Days Sales Outstanding
            "dpo": self.calculate_dpo(),  # Sprint 293: Days Payable Outstanding
            "dio": self.calculate_dio(),  # Sprint 293: Days Inventory Outstanding
            "ccc": self.calculate_ccc(),  # Sprint 293: Cash Conversion Cycle
            "equity_ratio": self.calculate_equity_ratio(),  # R4: Extended Solvency
            "long_term_debt_ratio": self.calculate_long_term_debt_ratio(),  # R4: Extended Solvency
            "asset_turnover": self.calculate_asset_turnover(),  # R4: Extended Solvency
            "inventory_turnover": self.calculate_inventory_turnover(),  # R5: Core Turnover
            "receivables_turnover": self.calculate_receivables_turnover(),  # R5: Core Turnover
        }

    def to_dict(self) -> dict[str, Any]:
        """Return all ratios as a serializable dictionary."""
        ratios = self.calculate_all_ratios()
        return {key: ratio.to_dict() for key, ratio in ratios.items()}


class CommonSizeAnalyzer:
    """Expresses items as percentages of a base (Total Assets or Revenue)."""

    def __init__(self, category_totals: CategoryTotals):
        self.totals = category_totals

    def balance_sheet_percentages(self) -> dict[str, float]:
        """Express balance sheet items as percentage of Total Assets."""
        base = self.totals.total_assets
        if base == 0:
            return {}

        non_current_assets = self.totals.total_assets - self.totals.current_assets

        return {
            "current_assets_pct": round((self.totals.current_assets / base) * 100, 1),
            "inventory_pct": round((self.totals.inventory / base) * 100, 1),
            "accounts_receivable_pct": round((self.totals.accounts_receivable / base) * 100, 1),
            "non_current_assets_pct": round((non_current_assets / base) * 100, 1),
            "total_liabilities_pct": round((self.totals.total_liabilities / base) * 100, 1),
            "current_liabilities_pct": round((self.totals.current_liabilities / base) * 100, 1),
            "accounts_payable_pct": round((self.totals.accounts_payable / base) * 100, 1),
            "total_equity_pct": round((self.totals.total_equity / base) * 100, 1),
        }

    def income_statement_percentages(self) -> dict[str, float]:
        """Express income statement items as percentage of Revenue."""
        base = self.totals.total_revenue
        if base == 0:
            return {}

        gross_profit = base - self.totals.cost_of_goods_sold
        net_income = base - self.totals.total_expenses
        operating_income = base - self.totals.cost_of_goods_sold - self.totals.operating_expenses

        return {
            "cogs_pct": round((self.totals.cost_of_goods_sold / base) * 100, 1),
            "gross_profit_pct": round((gross_profit / base) * 100, 1),
            "operating_expenses_pct": round((self.totals.operating_expenses / base) * 100, 1),
            "operating_income_pct": round((operating_income / base) * 100, 1),
            "total_expenses_pct": round((self.totals.total_expenses / base) * 100, 1),
            "net_income_pct": round((net_income / base) * 100, 1),
        }

    def to_dict(self) -> dict[str, dict[str, float]]:
        """Return all common-size percentages."""
        return {
            "balance_sheet": self.balance_sheet_percentages(),
            "income_statement": self.income_statement_percentages(),
        }


class VarianceAnalyzer:
    """Compare current vs previous diagnostic runs using aggregate totals."""

    def __init__(self, current_totals: CategoryTotals, previous_totals: Optional[CategoryTotals] = None):
        self.current = current_totals
        self.previous = previous_totals

    def _calculate_variance(
        self, metric_name: str, current_value: float, previous_value: float, higher_is_better: bool = True
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

    def calculate_variances(self) -> dict[str, VarianceResult]:
        """Calculate variances for all category totals. Returns empty dict if no previous data."""
        if self.previous is None:
            return {}

        return {
            "total_assets": self._calculate_variance(
                "Total Assets", self.current.total_assets, self.previous.total_assets, higher_is_better=True
            ),
            "total_liabilities": self._calculate_variance(
                "Total Liabilities",
                self.current.total_liabilities,
                self.previous.total_liabilities,
                higher_is_better=False,  # Lower liabilities generally better
            ),
            "total_equity": self._calculate_variance(
                "Total Equity", self.current.total_equity, self.previous.total_equity, higher_is_better=True
            ),
            "total_revenue": self._calculate_variance(
                "Total Revenue", self.current.total_revenue, self.previous.total_revenue, higher_is_better=True
            ),
            "current_assets": self._calculate_variance(
                "Current Assets", self.current.current_assets, self.previous.current_assets, higher_is_better=True
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        """Return all variances as serializable dictionary."""
        variances = self.calculate_variances()
        return {key: var.to_dict() for key, var in variances.items()}


# ============================================================================
# Sprint 33: Multi-Period Trend Analysis
# ============================================================================


@dataclass
class PeriodSnapshot:
    """A single period's data for trend analysis."""

    period_date: date
    period_type: str  # monthly, quarterly, annual
    category_totals: CategoryTotals
    ratios: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "period_date": self.period_date.isoformat(),
            "period_type": self.period_type,
            "category_totals": self.category_totals.to_dict(),
            "ratios": self.ratios,
        }


@dataclass
class TrendPoint:
    """A data point in a trend line."""

    period_date: date
    value: float
    change_from_previous: Optional[float] = None
    change_percent: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "period_date": self.period_date.isoformat(),
            "value": round(self.value, 2) if self.value is not None else None,
            "change_from_previous": round(self.change_from_previous, 2)
            if self.change_from_previous is not None
            else None,
            "change_percent": round(self.change_percent, 1) if self.change_percent is not None else None,
        }


@dataclass
class TrendSummary:
    """Summary of a trend across multiple periods."""

    metric_name: str
    data_points: list[TrendPoint]
    overall_direction: TrendDirection
    total_change: float
    total_change_percent: float
    periods_analyzed: int
    average_value: float
    min_value: float
    max_value: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "overall_direction": self.overall_direction.value,
            "total_change": round(self.total_change, 2),
            "total_change_percent": round(self.total_change_percent, 1),
            "periods_analyzed": self.periods_analyzed,
            "average_value": round(self.average_value, 2),
            "min_value": round(self.min_value, 2),
            "max_value": round(self.max_value, 2),
        }


class TrendAnalyzer:
    """
    Analyze trends across multiple historical periods.

    Zero-Storage Compliance:
    - Only aggregate totals and ratios are stored
    - No raw transaction data is retained
    - Trend metadata is calculated on-demand
    """

    def __init__(self, snapshots: list[PeriodSnapshot]):
        """
        Initialize with a list of period snapshots sorted by date.

        Args:
            snapshots: List of PeriodSnapshot objects, oldest first
        """
        # Sort snapshots by period_date (oldest first)
        self.snapshots = sorted(snapshots, key=lambda s: s.period_date)
        log_secure_operation("trend_analyzer_init", f"Initializing trend analysis with {len(snapshots)} periods")

    def _calculate_trend_points(self, values: list[tuple[date, float]]) -> list[TrendPoint]:
        """Calculate trend points with period-over-period changes."""
        if not values:
            return []

        points = []
        previous_value = None

        for period_date, value in values:
            change_from_previous = None
            change_percent = None

            if previous_value is not None:
                change_from_previous = value - previous_value
                if previous_value != 0:
                    change_percent = (change_from_previous / abs(previous_value)) * 100

            points.append(
                TrendPoint(
                    period_date=period_date,
                    value=value,
                    change_from_previous=change_from_previous,
                    change_percent=change_percent,
                )
            )
            previous_value = value

        return points

    def _determine_overall_direction(self, points: list[TrendPoint], higher_is_better: bool = True) -> TrendDirection:
        """Determine the overall trend direction based on majority of changes."""
        if len(points) < 2:
            return TrendDirection.NEUTRAL

        positive_changes = 0
        negative_changes = 0

        for point in points[1:]:  # Skip first point (no previous)
            if point.change_from_previous is not None:
                if point.change_from_previous > 0:
                    positive_changes += 1
                elif point.change_from_previous < 0:
                    negative_changes += 1

        total_changes = positive_changes + negative_changes
        if total_changes == 0:
            return TrendDirection.NEUTRAL

        # Majority wins
        if positive_changes > negative_changes:
            return TrendDirection.POSITIVE if higher_is_better else TrendDirection.NEGATIVE
        elif negative_changes > positive_changes:
            return TrendDirection.NEGATIVE if higher_is_better else TrendDirection.POSITIVE
        else:
            return TrendDirection.NEUTRAL

    def analyze_metric_trend(
        self, metric_name: str, extractor: callable, higher_is_better: bool = True
    ) -> Optional[TrendSummary]:
        """
        Analyze trend for a specific metric.

        Args:
            metric_name: Name of the metric being analyzed
            extractor: Function that takes a PeriodSnapshot and returns the value
            higher_is_better: Whether an increase is favorable

        Returns:
            TrendSummary or None if insufficient data
        """
        if len(self.snapshots) < 2:
            return None

        # Extract values for each period
        values = []
        for snapshot in self.snapshots:
            try:
                value = extractor(snapshot)
                if value is not None:
                    values.append((snapshot.period_date, value))
            except (KeyError, AttributeError):
                continue

        if len(values) < 2:
            return None

        # Calculate trend points
        points = self._calculate_trend_points(values)

        # Calculate summary statistics
        all_values = [v for _, v in values]
        first_value = all_values[0]
        last_value = all_values[-1]
        total_change = last_value - first_value
        total_change_percent = (total_change / abs(first_value) * 100) if first_value != 0 else 0

        return TrendSummary(
            metric_name=metric_name,
            data_points=points,
            overall_direction=self._determine_overall_direction(points, higher_is_better),
            total_change=total_change,
            total_change_percent=total_change_percent,
            periods_analyzed=len(values),
            average_value=sum(all_values) / len(all_values),
            min_value=min(all_values),
            max_value=max(all_values),
        )

    def analyze_category_totals(self) -> dict[str, TrendSummary]:
        """Analyze trends for all category totals."""
        trends = {}

        # Define metrics with their extractors and interpretation
        metrics = [
            ("total_assets", lambda s: s.category_totals.total_assets, True),
            ("total_liabilities", lambda s: s.category_totals.total_liabilities, False),
            ("total_equity", lambda s: s.category_totals.total_equity, True),
            ("total_revenue", lambda s: s.category_totals.total_revenue, True),
            ("total_expenses", lambda s: s.category_totals.total_expenses, False),
            ("current_assets", lambda s: s.category_totals.current_assets, True),
            ("current_liabilities", lambda s: s.category_totals.current_liabilities, False),
        ]

        for metric_name, extractor, higher_is_better in metrics:
            trend = self.analyze_metric_trend(metric_name, extractor, higher_is_better)
            if trend:
                trends[metric_name] = trend

        return trends

    def analyze_ratio_trends(self) -> dict[str, TrendSummary]:
        """Analyze trends for all calculated ratios."""
        trends = {}

        # Define ratio metrics with their extractors and interpretation
        ratio_metrics = [
            ("current_ratio", lambda s: s.ratios.get("current_ratio"), True),
            ("quick_ratio", lambda s: s.ratios.get("quick_ratio"), True),
            ("debt_to_equity", lambda s: s.ratios.get("debt_to_equity"), False),
            ("gross_margin", lambda s: s.ratios.get("gross_margin"), True),
            ("net_profit_margin", lambda s: s.ratios.get("net_profit_margin"), True),
            ("operating_margin", lambda s: s.ratios.get("operating_margin"), True),
            ("return_on_assets", lambda s: s.ratios.get("return_on_assets"), True),
            ("return_on_equity", lambda s: s.ratios.get("return_on_equity"), True),
        ]

        for metric_name, extractor, higher_is_better in ratio_metrics:
            trend = self.analyze_metric_trend(metric_name, extractor, higher_is_better)
            if trend:
                trends[metric_name] = trend

        return trends

    def get_full_analysis(self) -> dict[str, Any]:
        """Get complete trend analysis for all metrics."""
        category_trends = self.analyze_category_totals()
        ratio_trends = self.analyze_ratio_trends()

        return {
            "periods_analyzed": len(self.snapshots),
            "date_range": {
                "start": self.snapshots[0].period_date.isoformat() if self.snapshots else None,
                "end": self.snapshots[-1].period_date.isoformat() if self.snapshots else None,
            },
            "category_trends": {k: v.to_dict() for k, v in category_trends.items()},
            "ratio_trends": {k: v.to_dict() for k, v in ratio_trends.items()},
        }

    def to_dict(self) -> dict[str, Any]:
        """Return full analysis as serializable dictionary."""
        return self.get_full_analysis()


# ============================================================================
# Sprint 37: Rolling Window Analysis
# ============================================================================


class MomentumType(str, Enum):
    """Momentum classification for trend acceleration."""

    ACCELERATING = "accelerating"
    DECELERATING = "decelerating"
    STEADY = "steady"
    REVERSING = "reversing"


@dataclass
class RollingAverage:
    """A rolling average value with period context."""

    window_months: int
    value: float
    data_points: int
    start_date: date
    end_date: date

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_months": self.window_months,
            "value": round(self.value, 2),
            "data_points": self.data_points,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
        }


@dataclass
class MomentumIndicator:
    """Trend momentum analysis result."""

    momentum_type: MomentumType
    rate_of_change: float  # Average change between periods
    acceleration: float  # Change in rate of change
    confidence: float  # 0.0 to 1.0 based on data consistency

    def to_dict(self) -> dict[str, Any]:
        return {
            "momentum_type": self.momentum_type.value,
            "rate_of_change": round(self.rate_of_change, 2),
            "acceleration": round(self.acceleration, 4),
            "confidence": round(self.confidence, 2),
        }


@dataclass
class RollingWindowResult:
    """Complete rolling window analysis for a metric."""

    metric_name: str
    rolling_averages: dict[int, RollingAverage]  # window_months -> RollingAverage
    momentum: MomentumIndicator
    current_value: float
    trend_direction: TrendDirection

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "rolling_averages": {str(k): v.to_dict() for k, v in self.rolling_averages.items()},
            "momentum": self.momentum.to_dict(),
            "current_value": round(self.current_value, 2),
            "trend_direction": self.trend_direction.value,
        }


class RollingWindowAnalyzer:
    """
    Calculate rolling window averages and trend momentum.

    Sprint 37: Rolling Window Analysis

    Supports 3, 6, and 12 month rolling windows for smoothing
    short-term fluctuations and identifying underlying trends.

    Momentum calculation measures whether trends are accelerating,
    decelerating, holding steady, or reversing.

    Zero-Storage Compliance:
    - Only aggregate totals and ratios are used
    - No raw transaction data is retained
    - Rolling calculations are computed on-demand
    """

    SUPPORTED_WINDOWS = [3, 6, 12]  # months

    def __init__(self, snapshots: list[PeriodSnapshot]):
        """
        Initialize with a list of period snapshots sorted by date.

        Args:
            snapshots: List of PeriodSnapshot objects, oldest first
        """
        # Sort snapshots by period_date (oldest first)
        self.snapshots = sorted(snapshots, key=lambda s: s.period_date)
        log_secure_operation(
            "rolling_window_init", f"Initializing rolling window analysis with {len(snapshots)} periods"
        )

    def _get_values_for_metric(self, extractor: callable) -> list[tuple[date, float]]:
        """Extract (date, value) pairs for a metric."""
        values = []
        for snapshot in self.snapshots:
            try:
                value = extractor(snapshot)
                if value is not None:
                    values.append((snapshot.period_date, value))
            except (KeyError, AttributeError):
                continue
        return values

    def _calculate_rolling_average(
        self, values: list[tuple[date, float]], window_months: int
    ) -> Optional[RollingAverage]:
        """
        Calculate rolling average for a specific window size.

        Uses all data points within the window period from the most recent date.
        """
        if not values or len(values) < 2:
            return None

        # Get the most recent date
        end_date = values[-1][0]

        # Calculate start date based on window
        # Approximate months as 30 days
        from datetime import timedelta

        window_days = window_months * 30
        start_date = end_date - timedelta(days=window_days)

        # Filter values within the window
        window_values = [(d, v) for d, v in values if d >= start_date]

        if len(window_values) < 2:
            return None

        # Calculate average
        avg_value = sum(v for _, v in window_values) / len(window_values)

        return RollingAverage(
            window_months=window_months,
            value=avg_value,
            data_points=len(window_values),
            start_date=window_values[0][0],
            end_date=window_values[-1][0],
        )

    def _calculate_momentum(self, values: list[tuple[date, float]], higher_is_better: bool = True) -> MomentumIndicator:
        """
        Calculate trend momentum (acceleration/deceleration).

        Momentum is determined by analyzing the rate of change
        over time and whether that rate is increasing or decreasing.
        """
        if len(values) < 3:
            return MomentumIndicator(
                momentum_type=MomentumType.STEADY,
                rate_of_change=0.0,
                acceleration=0.0,
                confidence=0.0,
            )

        # Calculate period-over-period changes
        changes = []
        for i in range(1, len(values)):
            prev_val = values[i - 1][1]
            curr_val = values[i][1]
            if prev_val != 0:
                change_pct = (curr_val - prev_val) / abs(prev_val) * 100
                changes.append(change_pct)

        if len(changes) < 2:
            avg_change = changes[0] if changes else 0.0
            return MomentumIndicator(
                momentum_type=MomentumType.STEADY,
                rate_of_change=avg_change,
                acceleration=0.0,
                confidence=0.3,
            )

        # Calculate average rate of change
        avg_change = sum(changes) / len(changes)

        # Calculate acceleration (change in rate of change)
        accelerations = []
        for i in range(1, len(changes)):
            accelerations.append(changes[i] - changes[i - 1])

        avg_acceleration = sum(accelerations) / len(accelerations) if accelerations else 0.0

        # Determine momentum type
        # Use module-level momentum thresholds

        if abs(avg_acceleration) < MOMENTUM_ACCELERATION:
            if abs(avg_change) < MOMENTUM_CHANGE:
                momentum_type = MomentumType.STEADY
            else:
                # Consistent direction without acceleration
                momentum_type = MomentumType.STEADY
        elif avg_change > 0 and avg_acceleration > 0:
            # Positive trend, accelerating
            momentum_type = MomentumType.ACCELERATING
        elif avg_change < 0 and avg_acceleration < 0:
            # Negative trend, accelerating (getting worse faster)
            momentum_type = MomentumType.ACCELERATING
        elif avg_change > 0 and avg_acceleration < 0:
            # Positive trend, decelerating (slowing down)
            momentum_type = MomentumType.DECELERATING
        elif avg_change < 0 and avg_acceleration > 0:
            # Negative trend, decelerating (getting better)
            momentum_type = MomentumType.DECELERATING
        else:
            # Check for trend reversal
            recent_changes = changes[-3:] if len(changes) >= 3 else changes
            if len(recent_changes) >= 2:
                first_half = sum(changes[: len(changes) // 2]) / (len(changes) // 2) if len(changes) >= 2 else 0
                second_half = (
                    sum(changes[len(changes) // 2 :]) / (len(changes) - len(changes) // 2) if len(changes) >= 2 else 0
                )
                if (first_half > 0 and second_half < 0) or (first_half < 0 and second_half > 0):
                    momentum_type = MomentumType.REVERSING
                else:
                    momentum_type = MomentumType.STEADY
            else:
                momentum_type = MomentumType.STEADY

        # Calculate confidence based on consistency
        if len(changes) >= 3:
            # Standard deviation as measure of consistency
            mean_change = avg_change
            variance = sum((c - mean_change) ** 2 for c in changes) / len(changes)
            std_dev = variance**0.5

            # Lower std_dev = higher confidence (more consistent)
            if std_dev < STDDEV_HIGH_CONFIDENCE:
                confidence = 0.9
            elif std_dev < STDDEV_MEDIUM_CONFIDENCE:
                confidence = 0.7
            elif std_dev < STDDEV_LOW_CONFIDENCE:
                confidence = 0.5
            else:
                confidence = 0.3
        else:
            confidence = 0.3

        return MomentumIndicator(
            momentum_type=momentum_type,
            rate_of_change=avg_change,
            acceleration=avg_acceleration,
            confidence=confidence,
        )

    def _determine_trend_direction(
        self, values: list[tuple[date, float]], higher_is_better: bool = True
    ) -> TrendDirection:
        """Determine overall trend direction from values."""
        if len(values) < 2:
            return TrendDirection.NEUTRAL

        first_value = values[0][1]
        last_value = values[-1][1]
        change = last_value - first_value

        if abs(change) < abs(first_value) * 0.01:  # Less than 1% change
            return TrendDirection.NEUTRAL

        if change > 0:
            return TrendDirection.POSITIVE if higher_is_better else TrendDirection.NEGATIVE
        else:
            return TrendDirection.NEGATIVE if higher_is_better else TrendDirection.POSITIVE

    def analyze_metric(
        self, metric_name: str, extractor: callable, higher_is_better: bool = True
    ) -> Optional[RollingWindowResult]:
        """
        Analyze rolling windows for a specific metric.

        Args:
            metric_name: Name of the metric being analyzed
            extractor: Function that takes a PeriodSnapshot and returns the value
            higher_is_better: Whether an increase is favorable

        Returns:
            RollingWindowResult or None if insufficient data
        """
        values = self._get_values_for_metric(extractor)

        if len(values) < 2:
            return None

        # Calculate rolling averages for each window
        rolling_averages = {}
        for window in self.SUPPORTED_WINDOWS:
            avg = self._calculate_rolling_average(values, window)
            if avg:
                rolling_averages[window] = avg

        if not rolling_averages:
            return None

        # Calculate momentum
        momentum = self._calculate_momentum(values, higher_is_better)

        # Get current value and trend direction
        current_value = values[-1][1]
        trend_direction = self._determine_trend_direction(values, higher_is_better)

        return RollingWindowResult(
            metric_name=metric_name,
            rolling_averages=rolling_averages,
            momentum=momentum,
            current_value=current_value,
            trend_direction=trend_direction,
        )

    def analyze_category_totals(self) -> dict[str, RollingWindowResult]:
        """Analyze rolling windows for all category totals."""
        results = {}

        metrics = [
            ("total_assets", lambda s: s.category_totals.total_assets, True),
            ("total_liabilities", lambda s: s.category_totals.total_liabilities, False),
            ("total_equity", lambda s: s.category_totals.total_equity, True),
            ("total_revenue", lambda s: s.category_totals.total_revenue, True),
            ("total_expenses", lambda s: s.category_totals.total_expenses, False),
        ]

        for metric_name, extractor, higher_is_better in metrics:
            result = self.analyze_metric(metric_name, extractor, higher_is_better)
            if result:
                results[metric_name] = result

        return results

    def analyze_ratios(self) -> dict[str, RollingWindowResult]:
        """Analyze rolling windows for all calculated ratios."""
        results = {}

        ratio_metrics = [
            ("current_ratio", lambda s: s.ratios.get("current_ratio"), True),
            ("quick_ratio", lambda s: s.ratios.get("quick_ratio"), True),
            ("debt_to_equity", lambda s: s.ratios.get("debt_to_equity"), False),
            ("gross_margin", lambda s: s.ratios.get("gross_margin"), True),
            ("net_profit_margin", lambda s: s.ratios.get("net_profit_margin"), True),
            ("operating_margin", lambda s: s.ratios.get("operating_margin"), True),
            ("return_on_assets", lambda s: s.ratios.get("return_on_assets"), True),
            ("return_on_equity", lambda s: s.ratios.get("return_on_equity"), True),
        ]

        for metric_name, extractor, higher_is_better in ratio_metrics:
            result = self.analyze_metric(metric_name, extractor, higher_is_better)
            if result:
                results[metric_name] = result

        return results

    def get_full_analysis(self) -> dict[str, Any]:
        """Get complete rolling window analysis for all metrics."""
        category_results = self.analyze_category_totals()
        ratio_results = self.analyze_ratios()

        return {
            "periods_analyzed": len(self.snapshots),
            "supported_windows": self.SUPPORTED_WINDOWS,
            "date_range": {
                "start": self.snapshots[0].period_date.isoformat() if self.snapshots else None,
                "end": self.snapshots[-1].period_date.isoformat() if self.snapshots else None,
            },
            "category_rolling": {k: v.to_dict() for k, v in category_results.items()},
            "ratio_rolling": {k: v.to_dict() for k, v in ratio_results.items()},
        }

    def to_dict(self) -> dict[str, Any]:
        """Return full analysis as serializable dictionary."""
        return self.get_full_analysis()


def create_period_snapshot(
    period_date: date, period_type: str, category_totals: CategoryTotals, ratios: Optional[dict[str, float]] = None
) -> PeriodSnapshot:
    """
    Factory function to create a PeriodSnapshot.

    Args:
        period_date: End date of the period
        period_type: "monthly", "quarterly", or "annual"
        category_totals: CategoryTotals object with aggregate amounts
        ratios: Optional dict of pre-calculated ratio values

    Returns:
        PeriodSnapshot object
    """
    if ratios is None:
        # Calculate ratios from category totals
        engine = RatioEngine(category_totals)
        all_ratios = engine.calculate_all_ratios()
        ratios = {name: result.value for name, result in all_ratios.items() if result.value is not None}

    return PeriodSnapshot(
        period_date=period_date,
        period_type=period_type,
        category_totals=category_totals,
        ratios=ratios,
    )


def calculate_dupont_decomposition(
    current: CategoryTotals,
    previous: Optional[CategoryTotals] = None,
) -> Optional[DupontDecomposition]:
    """
    Standalone DuPont decomposition function.

    Convenience wrapper around RatioEngine.calculate_dupont().

    Args:
        current: Current period CategoryTotals
        previous: Optional previous period CategoryTotals for delta calculation

    Returns:
        DupontDecomposition or None if required data is missing
    """
    engine = RatioEngine(current)
    return engine.calculate_dupont(previous_totals=previous)


# Keywords for identifying current vs non-current assets
CURRENT_ASSET_KEYWORDS = [
    "cash",
    "bank",
    "receivable",
    "inventory",
    "prepaid",
    "supplies",
    "short-term",
    "short term",
    "current",
    "marketable securities",
]

# Sprint 293: Keywords for identifying accounts payable (trade payables)
# Excludes notes payable, interest payable, taxes payable, etc.
ACCOUNTS_PAYABLE_KEYWORDS = [
    "accounts payable",
    "trade payable",
    "trade payables",
    "a/p",
    "vendor payable",
]

# Keywords for COGS identification
COGS_KEYWORDS = [
    "cost of goods",
    "cogs",
    "cost of sales",
    "cost of revenue",
    "direct cost",
    "direct material",
    "direct labor",
    "manufacturing cost",
]

# Sprint 26: Keywords for Operating Expenses identification
OPERATING_EXPENSE_KEYWORDS = [
    "salary",
    "salaries",
    "wage",
    "wages",
    "payroll",
    "rent",
    "lease",
    "utilities",
    "utility",
    "insurance",
    "depreciation",
    "amortization",
    "office",
    "supplies",
    "maintenance",
    "repair",
    "advertising",
    "marketing",
    "promotion",
    "travel",
    "entertainment",
    "meals",
    "professional fee",
    "legal",
    "accounting",
    "consulting",
    "telephone",
    "internet",
    "communication",
    "training",
    "education",
    "subscription",
    "bank fee",
    "bank charge",
    "service charge",
    "operating",
    "administrative",
    "general expense",
    "g&a",
    "selling expense",
    "distribution",
]

# Keywords that indicate NON-operating expenses (exclude from operating expenses)
NON_OPERATING_KEYWORDS = [
    "interest expense",
    "interest payment",
    "tax",
    "income tax",
    "tax expense",
    "extraordinary",
    "unusual",
    "non-recurring",
    "loss on sale",
    "loss on disposal",
    "impairment",
    "discontinued",
    "restructuring",
]


def extract_category_totals(
    account_balances: dict[str, dict[str, float]], classified_accounts: dict[str, str]
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
                if "inventory" in account_lower:
                    totals.inventory += amount
                # Sprint 53: Track accounts receivable for DSO calculation
                if "receivable" in account_lower:
                    totals.accounts_receivable += amount

        elif category == "liability":
            # Liabilities have natural credit balance
            amount = abs(net_balance) if net_balance < 0 else -abs(net_balance)
            totals.total_liabilities += amount

            # Check if current liability
            if any(kw in account_lower for kw in ["payable", "current", "short-term", "accrued"]):
                totals.current_liabilities += amount
                # Sprint 293: Track accounts payable for DPO calculation
                if any(kw in account_lower for kw in ACCOUNTS_PAYABLE_KEYWORDS):
                    totals.accounts_payable += amount

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
        f"Revenue: ${totals.total_revenue:,.2f}",
    )

    return totals


def calculate_analytics(
    category_totals: CategoryTotals, previous_totals: Optional[CategoryTotals] = None
) -> dict[str, Any]:
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
