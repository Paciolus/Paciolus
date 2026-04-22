"""
Paciolus — Going Concern Indicator Profile Engine
Sprint 360: Phase XLIX — ISA 570
Sprint 685: expanded indicator set + test consolidation.

Aggregates TB + optional cash-flow signals into ISA 570 going concern
indicators. Deterministic tests (Sprint 685 post-consolidation):

1. Net liability position — total liabilities exceed total assets
2. Working capital deficit — merged from the prior current-ratio and
   negative-working-capital tests, which were mathematically
   equivalent (current_ratio < 1.0 ⇔ working_capital < 0). Keeps the
   dollar-magnitude output — more informative for GC than the ratio.
3. Recurring losses — negative net margin (prior period if available)
4. Revenue decline — period-over-period revenue decrease
5. High leverage — debt-to-equity ratio above 3.0
6. Negative operating cash flow — optional; runs when
   ``operating_cash_flow`` is supplied. ISA 570.16 explicitly names
   this as a financial indicator distinct from accrual-basis losses.
7. Covenant breach — optional; runs when ``covenant_thresholds``
   is supplied (auditor-configurable floors/ceilings on current
   ratio, interest coverage, debt/equity).

Categories ISA 570.16 flags that this engine CANNOT detect from TB
alone are documented in ``DISCLAIMER`` and surfaced as narrative
prompts in ``_build_narrative``:
  * Loss of key customer / supplier
  * Loss of key management
  * Labor disputes
  * Pending litigation with material exposure
  * Non-compliance with capital requirements
  * Inability to obtain financing for essential investments

Guardrail: Descriptive metrics only — factual observations, no
conclusions. This analysis does NOT constitute an audit opinion on
going concern. All computation is ephemeral (zero-storage compliance).

ISA 570 (Going Concern) ¶16, IAS 1.25-26.
"""

from dataclasses import dataclass, field
from typing import Optional

NEAR_ZERO = 1e-10

# Thresholds
CURRENT_RATIO_THRESHOLD = 1.0  # Kept for backward compat; consumers using the
# consolidated working-capital-deficit test should not rely on it directly.
LEVERAGE_THRESHOLD = 3.0
REVENUE_DECLINE_THRESHOLD = 0.10  # 10% decline triggers indicator

DISCLAIMER = (
    "IMPORTANT: This analysis presents factual financial metrics only and does "
    "not constitute an audit conclusion regarding going concern. The indicators "
    "surfaced here are the TB-derivable subset of ISA 570 ¶16 — they cover "
    "liquidity, leverage, profitability, revenue trajectory, and (when "
    "supplied) operating cash flow and covenant compliance. ISA 570 ¶16 also "
    "names indicators this engine CANNOT derive from a trial balance alone: "
    "loss of key customers or management, labor disputes, material pending "
    "litigation, non-compliance with capital requirements, and inability to "
    "obtain essential financing. Auditors must evaluate those categories "
    "independently. No automated analysis replaces the auditor's professional "
    "judgment under ISA 570."
)


@dataclass(frozen=True)
class CovenantThresholds:
    """Sprint 685: auditor-configurable covenant thresholds.

    Only thresholds set to a non-None value are evaluated. A breach fires
    one indicator; the narrative names which specific floor/ceiling
    tripped. Defaults are typical mid-market private-credit covenants
    but should be overridden to match the entity's actual loan agreement.
    """

    # Current ratio MUST be at or above this value (floor).
    min_current_ratio: Optional[float] = None
    # Interest coverage (EBIT / interest expense) MUST be at or above this.
    min_interest_coverage: Optional[float] = None
    # Debt-to-equity MUST be at or below this (ceiling).
    max_debt_to_equity: Optional[float] = None


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


def _test_working_capital_deficit(
    current_assets: float,
    current_liabilities: float,
) -> GoingConcernIndicator:
    """Sprint 685: merged test for liquidity risk.

    The prior implementation had two separate tests — "Current Ratio < 1.0"
    and "Negative Working Capital" — that were mathematically equivalent:
    current_ratio < 1.0 ⇔ current_assets < current_liabilities ⇔
    working_capital < 0. Running both double-counted the indicator in the
    "2-of-6 triggered" threshold logic.

    The consolidated test preserves both the ratio AND the dollar deficit
    in the description (ratio is comparable across entities, deficit is
    more actionable for a specific engagement). Keeps ``metric_value``
    as the working-capital dollar amount (more informative for GC memos).
    """
    # Edge case: zero current liabilities — ratio is undefined, but
    # working capital = current_assets and is always non-negative.
    if abs(current_liabilities) < NEAR_ZERO:
        working_capital = current_assets
        return GoingConcernIndicator(
            indicator_name="Working Capital Deficit",
            triggered=False,
            threshold_proximity="low",
            description=(
                f"Current liabilities are zero; working capital equals "
                f"current assets (${current_assets:,.2f}). Current ratio "
                "is not meaningful."
            ),
            metric_value=working_capital,
        )

    working_capital = current_assets - current_liabilities
    ratio = current_assets / current_liabilities
    triggered = working_capital < -NEAR_ZERO

    if triggered:
        deficit = abs(working_capital)
        # Severity escalates when the deficit is more than half of current
        # assets (i.e., current liabilities are more than 1.5× current
        # assets) — indicates severe liquidity stress.
        severity = "high" if deficit > max(current_assets / 2, NEAR_ZERO) else "medium"
        description = (
            f"Working capital deficit of ${deficit:,.2f} "
            f"(current assets ${current_assets:,.2f} vs. current "
            f"liabilities ${current_liabilities:,.2f}; current ratio "
            f"{ratio:.2f})."
        )
    else:
        severity = "low"
        description = f"Working capital is ${working_capital:,.2f} (current ratio {ratio:.2f})."

    return GoingConcernIndicator(
        indicator_name="Working Capital Deficit",
        triggered=triggered,
        threshold_proximity=severity,
        description=description,
        metric_value=working_capital,
        threshold=0.0,  # Deficit threshold is zero (working capital must be ≥ 0)
    )


def _test_negative_operating_cash_flow(
    operating_cash_flow: float,
    materiality_threshold: float,
) -> GoingConcernIndicator:
    """Sprint 685: ISA 570 ¶16(b) — negative operating cash flow.

    Distinct from "recurring losses" because accrual-basis losses can
    co-exist with positive cash flow (e.g., depreciation-heavy businesses),
    and cash losses can co-exist with accrual profit (e.g., working
    capital growth). ISA 570 explicitly names both as separate
    financial-event indicators.

    Fires when operating cash flow is negative and its magnitude exceeds
    the engagement's materiality threshold. Below-materiality negative
    OCF is noted but not flagged — small operational cash timing
    differences are normal and not a GC concern.
    """
    if operating_cash_flow >= -NEAR_ZERO:
        return GoingConcernIndicator(
            indicator_name="Negative Operating Cash Flow",
            triggered=False,
            threshold_proximity="low",
            description=(f"Operating cash flow is positive (${operating_cash_flow:,.2f})."),
            metric_value=operating_cash_flow,
        )

    abs_deficit = abs(operating_cash_flow)
    # Sub-materiality deficit is noted but not flagged.
    if materiality_threshold > 0 and abs_deficit < materiality_threshold:
        return GoingConcernIndicator(
            indicator_name="Negative Operating Cash Flow",
            triggered=False,
            threshold_proximity="low",
            description=(
                f"Operating cash flow is slightly negative "
                f"(${operating_cash_flow:,.2f}); below the materiality "
                f"threshold of ${materiality_threshold:,.2f}."
            ),
            metric_value=operating_cash_flow,
            threshold=-materiality_threshold,
        )

    # Materially negative OCF — severity scales with magnitude relative to
    # materiality (2× materiality = high, otherwise medium).
    severity = "high" if abs_deficit > 2 * materiality_threshold else "medium"
    return GoingConcernIndicator(
        indicator_name="Negative Operating Cash Flow",
        triggered=True,
        threshold_proximity=severity,
        description=(
            f"Operating cash flow is negative at ${operating_cash_flow:,.2f} "
            f"(exceeds materiality threshold of ${materiality_threshold:,.2f}). "
            "ISA 570 ¶16(b) names negative operating cash flow as a financial "
            "going-concern indicator distinct from accrual-basis losses."
        ),
        metric_value=operating_cash_flow,
        threshold=-materiality_threshold,
    )


def _test_covenant_breach(
    current_assets: float,
    current_liabilities: float,
    total_liabilities: float,
    total_equity: float,
    operating_income: Optional[float],
    interest_expense: Optional[float],
    thresholds: CovenantThresholds,
) -> GoingConcernIndicator:
    """Sprint 685: ISA 570 ¶16(d) — debt-covenant breach indicator.

    Takes auditor-supplied covenant floors/ceilings and flags the FIRST
    breach found (breaches compound; the auditor memo lists them all
    through the description). Skipped entirely when no thresholds are
    provided.

    Covenants evaluated:
      * min_current_ratio: current_assets / current_liabilities
      * min_interest_coverage: operating_income / interest_expense
      * max_debt_to_equity: total_liabilities / total_equity
    """
    breaches: list[str] = []

    if thresholds.min_current_ratio is not None and abs(current_liabilities) >= NEAR_ZERO:
        cr = current_assets / current_liabilities
        if cr < thresholds.min_current_ratio:
            breaches.append(f"current ratio {cr:.2f} below covenant floor {thresholds.min_current_ratio:.2f}")

    if (
        thresholds.min_interest_coverage is not None
        and operating_income is not None
        and interest_expense is not None
        and abs(interest_expense) >= NEAR_ZERO
    ):
        icr = operating_income / abs(interest_expense)
        if icr < thresholds.min_interest_coverage:
            breaches.append(f"interest coverage {icr:.2f} below covenant floor {thresholds.min_interest_coverage:.2f}")

    if thresholds.max_debt_to_equity is not None and abs(total_equity) >= NEAR_ZERO:
        dte = total_liabilities / total_equity
        if dte > thresholds.max_debt_to_equity:
            breaches.append(f"debt-to-equity {dte:.2f} above covenant ceiling {thresholds.max_debt_to_equity:.2f}")

    if breaches:
        # Multiple concurrent breaches = high severity; single breach = medium.
        severity = "high" if len(breaches) >= 2 else "medium"
        description = (
            f"{len(breaches)} debt-covenant breach"
            + ("es" if len(breaches) > 1 else "")
            + f": {'; '.join(breaches)}. ISA 570 ¶16(d) identifies covenant "
            "non-compliance as a financial going-concern indicator."
        )
        return GoingConcernIndicator(
            indicator_name="Debt Covenant Breach",
            triggered=True,
            threshold_proximity=severity,
            description=description,
            metric_value=float(len(breaches)),
        )

    return GoingConcernIndicator(
        indicator_name="Debt Covenant Breach",
        triggered=False,
        threshold_proximity="low",
        description="No auditor-configured covenant thresholds were breached.",
        metric_value=0.0,
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
        assert prior_revenue is not None and prior_expenses is not None
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
    operating_cash_flow: Optional[float] = None,
    materiality_threshold: float = 0.0,
    covenant_thresholds: Optional[CovenantThresholds] = None,
    operating_income: Optional[float] = None,
    interest_expense: Optional[float] = None,
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
        prior_revenue: Optional prior-period revenue for recurring-losses
            and revenue-decline tests.
        prior_expenses: Optional prior-period expenses for recurring-losses.
        operating_cash_flow: Sprint 685 — optional. When supplied and the
            entity has negative OCF exceeding materiality, ISA 570 ¶16(b)
            indicator fires.
        materiality_threshold: Used only for the cash-flow test's sub-
            materiality filter. Pass 0 to flag any negative OCF.
        covenant_thresholds: Sprint 685 — optional. Auditor-configurable
            loan-covenant floors/ceilings. When supplied, ISA 570 ¶16(d)
            breach indicator evaluates.
        operating_income: Needed only if
            ``covenant_thresholds.min_interest_coverage`` is set.
        interest_expense: Needed only if
            ``covenant_thresholds.min_interest_coverage`` is set.

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

    # Test 2 (Sprint 685 — consolidated): Working Capital Deficit.
    # Prior implementation ran Current Ratio AND Negative Working Capital
    # as two tests; they were mathematically equivalent and double-counted.
    indicators.append(_test_working_capital_deficit(current_assets, current_liabilities))

    # Test 3: Recurring losses (always runs; uses prior if available)
    indicators.append(
        _test_recurring_losses(
            total_revenue,
            total_expenses,
            prior_revenue=prior_revenue if prior_available else None,
            prior_expenses=prior_expenses if prior_available else None,
        )
    )

    # Test 4: Revenue decline (requires prior period)
    if prior_available:
        indicators.append(_test_revenue_decline(total_revenue, prior_revenue or 0.0))

    # Test 5: High leverage
    indicators.append(_test_high_leverage(total_liabilities, total_equity))

    # Sprint 685 Test 6: negative operating cash flow (optional). Only
    # runs when OCF is supplied — otherwise we can't derive it from a
    # trial balance alone.
    if operating_cash_flow is not None:
        indicators.append(
            _test_negative_operating_cash_flow(
                operating_cash_flow,
                materiality_threshold=materiality_threshold,
            )
        )

    # Sprint 685 Test 7: covenant breach (optional). Only runs when
    # the auditor has supplied covenant thresholds for this engagement.
    if covenant_thresholds is not None:
        indicators.append(
            _test_covenant_breach(
                current_assets,
                current_liabilities,
                total_liabilities,
                total_equity,
                operating_income=operating_income,
                interest_expense=interest_expense,
                thresholds=covenant_thresholds,
            )
        )

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
