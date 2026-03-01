"""
Prior Period Comparison Engine - Sprint 51

Compares current audit results to prior period data for variance analysis.
Supports side-by-side comparison of trial balance totals and ratios.

ZERO-STORAGE COMPLIANCE:
- Prior periods stored as aggregate totals only (DiagnosticSummary)
- No raw transaction data is stored
- Comparison results are ephemeral (computed on demand)

GAAP/IFRS Notes:
- Comparative financial statements are required for public companies
- ASC 205-10: Comparative statements preferred for two periods
- IAS 1: Requires comparative information for prior period
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# =============================================================================
# CONSTANTS
# =============================================================================

NEAR_ZERO = 0.005  # Below any meaningful financial balance; guards division-by-near-zero

# Significance thresholds for variance highlighting
SIGNIFICANT_VARIANCE_PERCENT = 10.0  # Flag variances > 10%
SIGNIFICANT_VARIANCE_AMOUNT = 10000.0  # Flag variances > $10,000

# Categories for comparison
BALANCE_SHEET_CATEGORIES = [
    ("total_assets", "Total Assets"),
    ("current_assets", "Current Assets"),
    ("inventory", "Inventory"),
    ("total_liabilities", "Total Liabilities"),
    ("current_liabilities", "Current Liabilities"),
    ("total_equity", "Total Equity"),
]

INCOME_STATEMENT_CATEGORIES = [
    ("total_revenue", "Total Revenue"),
    ("cost_of_goods_sold", "Cost of Goods Sold"),
    ("total_expenses", "Total Expenses"),
    ("operating_expenses", "Operating Expenses"),
]

RATIO_CATEGORIES = [
    ("current_ratio", "Current Ratio", False),  # Not a percentage
    ("quick_ratio", "Quick Ratio", False),
    ("debt_to_equity", "Debt to Equity", False),
    ("gross_margin", "Gross Margin", True),  # Is a percentage
    ("net_profit_margin", "Net Profit Margin", True),
    ("operating_margin", "Operating Margin", True),
    ("return_on_assets", "Return on Assets", True),
    ("return_on_equity", "Return on Equity", True),
]


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class CategoryVariance:
    """Variance analysis for a single category."""

    category_key: str
    category_name: str
    current_value: float
    prior_value: float
    dollar_variance: float
    percent_variance: Optional[float]  # None if prior is zero
    is_significant: bool
    direction: str  # "increase", "decrease", "unchanged"

    def to_dict(self) -> dict:
        return {
            "category_key": self.category_key,
            "category_name": self.category_name,
            "current_value": self.current_value,
            "prior_value": self.prior_value,
            "dollar_variance": self.dollar_variance,
            "percent_variance": self.percent_variance,
            "is_significant": self.is_significant,
            "direction": self.direction,
        }


@dataclass
class RatioVariance:
    """Variance analysis for a single ratio."""

    ratio_key: str
    ratio_name: str
    current_value: Optional[float]
    prior_value: Optional[float]
    point_change: Optional[float]  # For ratios, we use point change not percent
    is_significant: bool
    direction: str
    is_percentage: bool  # Whether to display as percentage

    def to_dict(self) -> dict:
        return {
            "ratio_key": self.ratio_key,
            "ratio_name": self.ratio_name,
            "current_value": self.current_value,
            "prior_value": self.prior_value,
            "point_change": self.point_change,
            "is_significant": self.is_significant,
            "direction": self.direction,
            "is_percentage": self.is_percentage,
        }


@dataclass
class DiagnosticVariance:
    """Variance for diagnostic metadata."""

    metric_key: str
    metric_name: str
    current_value: float
    prior_value: float
    variance: float
    direction: str

    def to_dict(self) -> dict:
        return {
            "metric_key": self.metric_key,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "prior_value": self.prior_value,
            "variance": self.variance,
            "direction": self.direction,
        }


@dataclass
class PeriodComparison:
    """Complete comparison between current and prior period."""

    # Period identification
    current_period_label: str
    prior_period_label: str
    prior_period_id: int
    comparison_timestamp: datetime

    # Category variances
    balance_sheet_variances: list[CategoryVariance] = field(default_factory=list)
    income_statement_variances: list[CategoryVariance] = field(default_factory=list)
    ratio_variances: list[RatioVariance] = field(default_factory=list)
    diagnostic_variances: list[DiagnosticVariance] = field(default_factory=list)

    # Summary statistics
    significant_variance_count: int = 0
    total_categories_compared: int = 0

    # Framework comparability metadata (Sprint 378)
    framework_note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "current_period_label": self.current_period_label,
            "prior_period_label": self.prior_period_label,
            "prior_period_id": self.prior_period_id,
            "comparison_timestamp": self.comparison_timestamp.isoformat(),
            "balance_sheet_variances": [v.to_dict() for v in self.balance_sheet_variances],
            "income_statement_variances": [v.to_dict() for v in self.income_statement_variances],
            "ratio_variances": [v.to_dict() for v in self.ratio_variances],
            "diagnostic_variances": [v.to_dict() for v in self.diagnostic_variances],
            "significant_variance_count": self.significant_variance_count,
            "total_categories_compared": self.total_categories_compared,
            "framework_note": self.framework_note,
        }


# =============================================================================
# COMPARISON FUNCTIONS
# =============================================================================


def calculate_variance(
    current: float,
    prior: float,
    percent_threshold: float = SIGNIFICANT_VARIANCE_PERCENT,
    amount_threshold: float = SIGNIFICANT_VARIANCE_AMOUNT,
) -> tuple[float, Optional[float], bool, str]:
    """
    Calculate variance between current and prior values.

    Returns:
        tuple of (dollar_variance, percent_variance, is_significant, direction)
    """
    dollar_variance = current - prior

    # Calculate percent variance (None if prior is near-zero)
    if abs(prior) > NEAR_ZERO:
        percent_variance = (dollar_variance / abs(prior)) * 100
    else:
        percent_variance = None

    # Determine direction
    if dollar_variance > 0:
        direction = "increase"
    elif dollar_variance < 0:
        direction = "decrease"
    else:
        direction = "unchanged"

    # Check significance
    is_significant = False
    if abs(dollar_variance) >= amount_threshold:
        is_significant = True
    elif percent_variance is not None and abs(percent_variance) >= percent_threshold:
        is_significant = True

    return dollar_variance, percent_variance, is_significant, direction


def calculate_ratio_variance(
    current: Optional[float],
    prior: Optional[float],
    is_percentage: bool = False,
) -> tuple[Optional[float], bool, str]:
    """
    Calculate variance between ratio values.

    For ratios, we use point change (e.g., 2.5 to 2.8 = +0.3 points).
    For percentage ratios, multiply by 100 for display.

    Returns:
        tuple of (point_change, is_significant, direction)
    """
    if current is None or prior is None:
        return None, False, "unchanged"

    point_change = current - prior

    # Determine direction
    if point_change > 0.01:
        direction = "increase"
    elif point_change < -0.01:
        direction = "decrease"
    else:
        direction = "unchanged"

    # Significance threshold for ratios (0.1 point change or 10% relative change)
    is_significant = False
    if abs(point_change) >= 0.1:
        is_significant = True
    elif abs(prior) > NEAR_ZERO and abs(point_change / prior) >= 0.1:
        is_significant = True

    return point_change, is_significant, direction


def compare_periods(
    current_data: dict,
    prior_data: dict,
    current_label: str = "Current Period",
    prior_label: Optional[str] = None,
    prior_id: int = 0,
) -> PeriodComparison:
    """
    Compare current audit data to prior period data.

    Args:
        current_data: Dictionary of current period totals and ratios
        prior_data: Dictionary of prior period totals and ratios (from DiagnosticSummary)
        current_label: Label for current period
        prior_label: Label for prior period (defaults to prior_data's period_label)
        prior_id: ID of the prior period DiagnosticSummary

    Returns:
        PeriodComparison with all variance analysis
    """
    # Get prior label from data if not provided
    if prior_label is None:
        prior_label = prior_data.get("period_label") or f"Period {prior_id}"

    comparison = PeriodComparison(
        current_period_label=current_label,
        prior_period_label=prior_label,
        prior_period_id=prior_id,
        comparison_timestamp=datetime.now(timezone.utc),
    )

    significant_count = 0
    total_count = 0

    # Compare balance sheet categories
    for key, name in BALANCE_SHEET_CATEGORIES:
        current_val = current_data.get(key, 0.0) or 0.0
        prior_val = prior_data.get(key, 0.0) or 0.0

        dollar_var, percent_var, is_sig, direction = calculate_variance(current_val, prior_val)

        variance = CategoryVariance(
            category_key=key,
            category_name=name,
            current_value=current_val,
            prior_value=prior_val,
            dollar_variance=dollar_var,
            percent_variance=percent_var,
            is_significant=is_sig,
            direction=direction,
        )
        comparison.balance_sheet_variances.append(variance)

        if is_sig:
            significant_count += 1
        total_count += 1

    # Compare income statement categories
    for key, name in INCOME_STATEMENT_CATEGORIES:
        current_val = current_data.get(key, 0.0) or 0.0
        prior_val = prior_data.get(key, 0.0) or 0.0

        dollar_var, percent_var, is_sig, direction = calculate_variance(current_val, prior_val)

        variance = CategoryVariance(
            category_key=key,
            category_name=name,
            current_value=current_val,
            prior_value=prior_val,
            dollar_variance=dollar_var,
            percent_variance=percent_var,
            is_significant=is_sig,
            direction=direction,
        )
        comparison.income_statement_variances.append(variance)

        if is_sig:
            significant_count += 1
        total_count += 1

    # Compare ratios
    for key, name, is_pct in RATIO_CATEGORIES:
        current_val = current_data.get(key)
        prior_val = prior_data.get(key)

        point_change, is_sig, direction = calculate_ratio_variance(current_val, prior_val, is_pct)

        ratio_var = RatioVariance(
            ratio_key=key,
            ratio_name=name,
            current_value=current_val,
            prior_value=prior_val,
            point_change=point_change,
            is_significant=is_sig,
            direction=direction,
            is_percentage=is_pct,
        )
        comparison.ratio_variances.append(ratio_var)

        if is_sig:
            significant_count += 1
        total_count += 1

    # Compare diagnostic metrics
    diagnostic_metrics = [
        ("total_debits", "Total Debits"),
        ("total_credits", "Total Credits"),
        ("anomaly_count", "Anomaly Count"),
        ("row_count", "Row Count"),
    ]

    for key, name in diagnostic_metrics:
        current_val = current_data.get(key, 0) or 0
        prior_val = prior_data.get(key, 0) or 0

        variance_val = current_val - prior_val
        if variance_val > 0:
            direction = "increase"
        elif variance_val < 0:
            direction = "decrease"
        else:
            direction = "unchanged"

        diagnostic_var = DiagnosticVariance(
            metric_key=key,
            metric_name=name,
            current_value=current_val,
            prior_value=prior_val,
            variance=variance_val,
            direction=direction,
        )
        comparison.diagnostic_variances.append(diagnostic_var)

    comparison.significant_variance_count = significant_count
    comparison.total_categories_compared = total_count

    return comparison


def generate_period_label(period_date, period_type: Optional[str] = None) -> str:
    """
    Generate a human-readable period label from date and type.

    Examples:
        - annual: "FY2025"
        - quarterly: "Q3 2025"
        - monthly: "Dec 2025"
    """
    if period_date is None:
        return "Unknown Period"

    year = period_date.year
    month = period_date.month

    if period_type == "annual":
        return f"FY{year}"
    elif period_type == "quarterly":
        quarter = (month - 1) // 3 + 1
        return f"Q{quarter} {year}"
    elif period_type == "monthly":
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return f"{month_names[month - 1]} {year}"
    else:
        # Default format
        return period_date.strftime("%Y-%m-%d")
