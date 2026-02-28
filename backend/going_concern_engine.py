"""
Paciolus — Going Concern Indicator Profile Engine
Sprint 360: Phase XLIX — ISA 570

Aggregates existing TB financial ratios and balance patterns into ISA 570
going concern indicators. Six deterministic tests:

1. Net liability position — total liabilities exceed total assets
2. Current ratio below 1.0 — liquidity risk
3. Negative working capital — current liabilities exceed current assets
4. Recurring losses — negative net margin (prior period if available)
5. Revenue decline — period-over-period revenue decrease
6. High leverage — debt-to-equity ratio above 3.0

Guardrail: Descriptive metrics only — factual observations, no conclusions.
This analysis does NOT constitute an audit opinion on going concern.
All computation is ephemeral (zero-storage compliance).

ISA 570 (Going Concern), IAS 1.25-26.
"""

from dataclasses import dataclass, field
from typing import Optional

NEAR_ZERO = 1e-10

# Thresholds
CURRENT_RATIO_THRESHOLD = 1.0
LEVERAGE_THRESHOLD = 3.0
REVENUE_DECLINE_THRESHOLD = 0.10  # 10% decline triggers indicator

DISCLAIMER = (
    "IMPORTANT: This analysis presents factual financial metrics only and does "
    "not constitute an audit conclusion regarding going concern. ISA 570 requires "
    "that the auditor exercise independent professional judgment based on all "
    "available audit evidence. No automated analysis can replace that judgment."
)


# ═══════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════


@dataclass
class GoingConcernIndicator:
    """A single going concern indicator observation."""

    indicator_name: str
    triggered: bool
    threshold_proximity: str  # "far_above", "above", "near" — distance from threshold
    description: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None

    def to_dict(self) -> dict:
        result: dict = {
            "indicator_name": self.indicator_name,
            "triggered": self.triggered,
            "threshold_proximity": self.threshold_proximity,
            "description": self.description,
        }
        if self.metric_value is not None:
            result["metric_value"] = round(self.metric_value, 2)
        if self.threshold is not None:
            result["threshold"] = round(self.threshold, 2)
        return result


@dataclass
class GoingConcernReport:
    """Complete going concern indicator profile."""

    indicators: list[GoingConcernIndicator] = field(default_factory=list)
    indicators_triggered: int = 0
    indicators_checked: int = 0
    prior_period_available: bool = False
    narrative: str = ""
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict:
        return {
            "indicators": [i.to_dict() for i in self.indicators],
            "indicators_triggered": self.indicators_triggered,
            "indicators_checked": self.indicators_checked,
            "prior_period_available": self.prior_period_available,
            "narrative": self.narrative,
            "disclaimer": self.disclaimer,
        }


# ═══════════════════════════════════════════════════════════════
# Indicator tests
# ═══════════════════════════════════════════════════════════════


def _test_net_liability_position(
    total_assets: float,
    total_liabilities: float,
    total_equity: float,
) -> GoingConcernIndicator:
    """Test 1: Net liability position — liabilities exceed assets (negative equity)."""
    triggered = total_equity < -NEAR_ZERO and total_liabilities > total_assets
    excess = total_liabilities - total_assets if triggered else 0.0

    if triggered:
        severity = "high"
        description = (
            f"Total liabilities (${total_liabilities:,.2f}) exceed total assets "
            f"(${total_assets:,.2f}) by ${excess:,.2f}. "
            f"Total equity is ${total_equity:,.2f}."
        )
    else:
        severity = "low"
        description = (
            f"Total assets (${total_assets:,.2f}) exceed total liabilities "
            f"(${total_liabilities:,.2f}). Total equity is ${total_equity:,.2f}."
        )

    return GoingConcernIndicator(
        indicator_name="Net Liability Position",
        triggered=triggered,
        threshold_proximity=severity,
        description=description,
        metric_value=total_equity,
    )


def _test_current_ratio(
    current_assets: float,
    current_liabilities: float,
) -> GoingConcernIndicator:
    """Test 2: Current ratio below 1.0 — liquidity risk."""
    if abs(current_liabilities) < NEAR_ZERO:
        return GoingConcernIndicator(
            indicator_name="Current Ratio",
            triggered=False,
            threshold_proximity="low",
            description="Current liabilities are zero; current ratio is not calculable.",
        )

    ratio = current_assets / current_liabilities
    triggered = ratio < CURRENT_RATIO_THRESHOLD

    if triggered:
        severity = "high" if ratio < 0.5 else "medium"
        description = (
            f"Current ratio is {ratio:.2f} (current assets ${current_assets:,.2f} / "
            f"current liabilities ${current_liabilities:,.2f}). "
            f"A ratio below {CURRENT_RATIO_THRESHOLD:.1f} indicates current liabilities "
            f"exceed current assets."
        )
    else:
        severity = "low"
        description = (
            f"Current ratio is {ratio:.2f} (current assets ${current_assets:,.2f} / "
            f"current liabilities ${current_liabilities:,.2f})."
        )

    return GoingConcernIndicator(
        indicator_name="Current Ratio",
        triggered=triggered,
        threshold_proximity=severity,
        description=description,
        metric_value=ratio,
        threshold=CURRENT_RATIO_THRESHOLD,
    )


def _test_negative_working_capital(
    current_assets: float,
    current_liabilities: float,
) -> GoingConcernIndicator:
    """Test 3: Negative working capital — current liabilities exceed current assets."""
    working_capital = current_assets - current_liabilities
    triggered = working_capital < -NEAR_ZERO

    if triggered:
        deficit = abs(working_capital)
        severity = "high" if deficit > current_assets * 0.5 else "medium"
        description = (
            f"Working capital is negative: ${working_capital:,.2f} "
            f"(current assets ${current_assets:,.2f} minus "
            f"current liabilities ${current_liabilities:,.2f})."
        )
    else:
        severity = "low"
        description = (
            f"Working capital is ${working_capital:,.2f} "
            f"(current assets ${current_assets:,.2f} minus "
            f"current liabilities ${current_liabilities:,.2f})."
        )

    return GoingConcernIndicator(
        indicator_name="Negative Working Capital",
        triggered=triggered,
        threshold_proximity=severity,
        description=description,
        metric_value=working_capital,
    )


def _test_recurring_losses(
    total_revenue: float,
    total_expenses: float,
    prior_revenue: Optional[float] = None,
    prior_expenses: Optional[float] = None,
) -> GoingConcernIndicator:
    """Test 4: Recurring losses — negative net margin in current period.

    If prior period available, also checks for consecutive losses.
    """
    net_income = total_revenue - total_expenses
    current_loss = net_income < -NEAR_ZERO

    prior_loss = False
    if prior_revenue is not None and prior_expenses is not None:
        prior_net = prior_revenue - prior_expenses
        prior_loss = prior_net < -NEAR_ZERO

    if current_loss and prior_loss:
        severity = "high"
        description = (
            f"Net loss of ${abs(net_income):,.2f} in the current period "
            f"(revenue ${total_revenue:,.2f} minus expenses ${total_expenses:,.2f}). "
            f"Prior period also recorded a net loss of ${abs(prior_revenue - prior_expenses):,.2f}."
        )
    elif current_loss:
        severity = "medium"
        description = (
            f"Net loss of ${abs(net_income):,.2f} in the current period "
            f"(revenue ${total_revenue:,.2f} minus expenses ${total_expenses:,.2f})."
        )
    else:
        severity = "low"
        description = (
            f"Net income of ${net_income:,.2f} in the current period "
            f"(revenue ${total_revenue:,.2f} minus expenses ${total_expenses:,.2f})."
        )

    return GoingConcernIndicator(
        indicator_name="Recurring Losses",
        triggered=current_loss,
        threshold_proximity=severity,
        description=description,
        metric_value=net_income,
    )


def _test_revenue_decline(
    total_revenue: float,
    prior_revenue: float,
) -> GoingConcernIndicator:
    """Test 5: Revenue decline — period-over-period revenue decrease > 10%."""
    if abs(prior_revenue) < NEAR_ZERO:
        return GoingConcernIndicator(
            indicator_name="Revenue Decline",
            triggered=False,
            threshold_proximity="low",
            description="Prior period revenue is zero; revenue decline is not calculable.",
        )

    change_pct = (total_revenue - prior_revenue) / abs(prior_revenue)
    triggered = change_pct < -REVENUE_DECLINE_THRESHOLD

    if triggered:
        severity = "high" if change_pct < -0.25 else "medium"
        description = (
            f"Revenue declined {abs(change_pct) * 100:.1f}% from ${prior_revenue:,.2f} to ${total_revenue:,.2f}."
        )
    else:
        severity = "low"
        direction = "increased" if change_pct > NEAR_ZERO else "remained stable"
        description = (
            f"Revenue {direction} ({change_pct * 100:+.1f}%) from ${prior_revenue:,.2f} to ${total_revenue:,.2f}."
        )

    return GoingConcernIndicator(
        indicator_name="Revenue Decline",
        triggered=triggered,
        threshold_proximity=severity,
        description=description,
        metric_value=change_pct * 100,
        threshold=-REVENUE_DECLINE_THRESHOLD * 100,
    )


def _test_high_leverage(
    total_liabilities: float,
    total_equity: float,
) -> GoingConcernIndicator:
    """Test 6: High leverage — debt-to-equity ratio above 3.0."""
    if abs(total_equity) < NEAR_ZERO:
        triggered = total_liabilities > NEAR_ZERO
        return GoingConcernIndicator(
            indicator_name="High Leverage",
            triggered=triggered,
            threshold_proximity="far_above" if triggered else "near",
            description=(
                f"Total equity is approximately zero (${total_equity:,.2f}). "
                f"Debt-to-equity ratio is not calculable."
                + (f" Total liabilities are ${total_liabilities:,.2f}." if triggered else "")
            ),
        )

    if total_equity < -NEAR_ZERO:
        return GoingConcernIndicator(
            indicator_name="High Leverage",
            triggered=True,
            threshold_proximity="far_above",
            description=(
                f"Total equity is negative (${total_equity:,.2f}). "
                f"Debt-to-equity ratio is not meaningful when equity is negative. "
                f"Total liabilities are ${total_liabilities:,.2f}."
            ),
        )

    dte = total_liabilities / total_equity
    triggered = dte > LEVERAGE_THRESHOLD

    if triggered:
        severity = "high" if dte > 5.0 else "medium"
        description = (
            f"Debt-to-equity ratio is {dte:.2f} "
            f"(total liabilities ${total_liabilities:,.2f} / "
            f"total equity ${total_equity:,.2f}). "
            f"Ratio exceeds {LEVERAGE_THRESHOLD:.1f}."
        )
    else:
        severity = "low"
        description = (
            f"Debt-to-equity ratio is {dte:.2f} "
            f"(total liabilities ${total_liabilities:,.2f} / "
            f"total equity ${total_equity:,.2f})."
        )

    return GoingConcernIndicator(
        indicator_name="High Leverage",
        triggered=triggered,
        threshold_proximity=severity,
        description=description,
        metric_value=dte,
        threshold=LEVERAGE_THRESHOLD,
    )


# ═══════════════════════════════════════════════════════════════
# Main computation
# ═══════════════════════════════════════════════════════════════


def compute_going_concern_profile(
    total_assets: float,
    total_liabilities: float,
    total_equity: float,
    current_assets: float,
    current_liabilities: float,
    total_revenue: float,
    total_expenses: float,
    prior_revenue: Optional[float] = None,
    prior_expenses: Optional[float] = None,
) -> GoingConcernReport:
    """Compute ISA 570 going concern indicator profile from pre-aggregated totals.

    Args:
        total_assets: Sum of all asset balances
        total_liabilities: Sum of all liability balances
        total_equity: Sum of all equity balances
        current_assets: Sum of current asset balances
        current_liabilities: Sum of current liability balances
        total_revenue: Sum of revenue balances
        total_expenses: Sum of expense balances
        prior_revenue: Optional prior-period revenue for tests 4 & 5
        prior_expenses: Optional prior-period expenses for test 4

    Returns:
        GoingConcernReport with indicator observations and narrative.
    """
    # Check if we have any meaningful data
    all_zero = (
        abs(total_assets) < NEAR_ZERO
        and abs(total_liabilities) < NEAR_ZERO
        and abs(total_equity) < NEAR_ZERO
        and abs(total_revenue) < NEAR_ZERO
        and abs(total_expenses) < NEAR_ZERO
    )

    if all_zero:
        return GoingConcernReport(
            narrative="No financial data available for going concern analysis.",
        )

    prior_available = prior_revenue is not None and prior_expenses is not None

    indicators: list[GoingConcernIndicator] = []

    # Test 1: Net liability position
    indicators.append(
        _test_net_liability_position(
            total_assets,
            total_liabilities,
            total_equity,
        )
    )

    # Test 2: Current ratio
    indicators.append(_test_current_ratio(current_assets, current_liabilities))

    # Test 3: Negative working capital
    indicators.append(_test_negative_working_capital(current_assets, current_liabilities))

    # Test 4: Recurring losses (always runs; uses prior if available)
    indicators.append(
        _test_recurring_losses(
            total_revenue,
            total_expenses,
            prior_revenue=prior_revenue if prior_available else None,
            prior_expenses=prior_expenses if prior_available else None,
        )
    )

    # Test 5: Revenue decline (requires prior period)
    if prior_available:
        indicators.append(_test_revenue_decline(total_revenue, prior_revenue))

    # Test 6: High leverage
    indicators.append(_test_high_leverage(total_liabilities, total_equity))

    # Aggregate
    triggered_count = sum(1 for i in indicators if i.triggered)
    checked_count = len(indicators)

    # Build narrative
    narrative = _build_narrative(indicators, triggered_count, checked_count, prior_available)

    return GoingConcernReport(
        indicators=indicators,
        indicators_triggered=triggered_count,
        indicators_checked=checked_count,
        prior_period_available=prior_available,
        narrative=narrative,
    )


def _build_narrative(
    indicators: list[GoingConcernIndicator],
    triggered_count: int,
    checked_count: int,
    prior_available: bool,
) -> str:
    """Build a descriptive narrative for the going concern profile.

    Guardrail: uses ONLY descriptive language. Never states that the entity
    has going concern issues or that professional judgment is needed in an
    evaluative manner.
    """
    parts: list[str] = []

    parts.append(f"{checked_count} going concern indicator(s) evaluated.")

    if triggered_count > 0:
        triggered_names = [i.indicator_name for i in indicators if i.triggered]
        parts.append(f"{triggered_count} indicator(s) triggered: {', '.join(triggered_names)}.")
    else:
        parts.append("No going concern indicators triggered.")

    if not prior_available:
        parts.append("Prior period data not available — revenue decline test was skipped.")

    return " ".join(parts)
