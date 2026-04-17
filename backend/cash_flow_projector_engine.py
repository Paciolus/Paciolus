"""
Cash Flow Projector Engine (Sprint 633).

Forward-looking 30/60/90-day cash position forecast driven by AR aging,
AP aging, opening cash balance, and recurring cash flows. Three
scenarios — base, stress, best — apply collection-rate and AP-deferral
adjustments to a deterministic weekly grid.

Zero-storage compliant: form-input only, nothing persisted.

The existing historical `financial_statement_builder.py` produces an
indirect-method cash flow statement from the trial balance. This engine
is its forward-looking counterpart, intended for operational finance
teams rather than financial reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any, Literal

CENT = Decimal("0.01")
ZERO = Decimal("0")

FORECAST_DAYS = 90  # Fixed horizon — sprint spec: 30 / 60 / 90 day windows
HORIZON_BUCKETS: tuple[int, ...] = (30, 60, 90)


class ScenarioName(str, Enum):
    BASE = "base"
    STRESS = "stress"
    BEST = "best"


Frequency = Literal["weekly", "biweekly", "monthly", "quarterly"]


class CashFlowInputError(ValueError):
    """Raised for invalid cash flow projection inputs."""


# =============================================================================
# Aging buckets (day ranges) — matches AR / AP aging conventions
# =============================================================================


@dataclass
class AgingBuckets:
    """AR or AP aging, in days-past-due buckets.

    Values are totals (Decimal dollars) in each bucket. Either set of
    buckets can be omitted when the caller only has one side of the
    aging — the engine degrades gracefully.
    """

    current: Decimal = ZERO  # not yet due
    days_1_30: Decimal = ZERO
    days_31_60: Decimal = ZERO
    days_61_90: Decimal = ZERO
    days_over_90: Decimal = ZERO

    def total(self) -> Decimal:
        return self.current + self.days_1_30 + self.days_31_60 + self.days_61_90 + self.days_over_90


@dataclass
class RecurringFlow:
    """A repeating cash inflow or outflow (payroll, rent, loan service)."""

    label: str
    amount: Decimal  # Positive = inflow, negative = outflow
    frequency: Frequency
    first_date: date


@dataclass
class ScenarioAssumptions:
    """Per-scenario adjustments applied to the base collection and deferral rates."""

    # Collection rate on AR. 1.0 = assume all current AR collects on time.
    ar_current_collection: Decimal
    ar_1_30_collection: Decimal
    ar_31_60_collection: Decimal
    ar_61_90_collection: Decimal
    ar_over_90_collection: Decimal
    # AP pay-down rate. 1.0 = pay all AP on schedule. <1.0 = defer some.
    ap_current_payment: Decimal
    ap_1_30_payment: Decimal
    ap_31_60_payment: Decimal
    ap_61_90_payment: Decimal
    ap_over_90_payment: Decimal


SCENARIOS: dict[ScenarioName, ScenarioAssumptions] = {
    ScenarioName.BASE: ScenarioAssumptions(
        ar_current_collection=Decimal("0.95"),
        ar_1_30_collection=Decimal("0.85"),
        ar_31_60_collection=Decimal("0.70"),
        ar_61_90_collection=Decimal("0.50"),
        ar_over_90_collection=Decimal("0.20"),
        ap_current_payment=Decimal("1.00"),
        ap_1_30_payment=Decimal("1.00"),
        ap_31_60_payment=Decimal("0.95"),
        ap_61_90_payment=Decimal("0.90"),
        ap_over_90_payment=Decimal("0.80"),
    ),
    ScenarioName.STRESS: ScenarioAssumptions(
        ar_current_collection=Decimal("0.80"),
        ar_1_30_collection=Decimal("0.65"),
        ar_31_60_collection=Decimal("0.50"),
        ar_61_90_collection=Decimal("0.30"),
        ar_over_90_collection=Decimal("0.10"),
        ap_current_payment=Decimal("1.00"),
        ap_1_30_payment=Decimal("1.00"),
        ap_31_60_payment=Decimal("1.00"),
        ap_61_90_payment=Decimal("1.00"),
        ap_over_90_payment=Decimal("1.00"),
    ),
    ScenarioName.BEST: ScenarioAssumptions(
        ar_current_collection=Decimal("1.00"),
        ar_1_30_collection=Decimal("0.95"),
        ar_31_60_collection=Decimal("0.85"),
        ar_61_90_collection=Decimal("0.70"),
        ar_over_90_collection=Decimal("0.40"),
        ap_current_payment=Decimal("0.90"),
        ap_1_30_payment=Decimal("0.85"),
        ap_31_60_payment=Decimal("0.80"),
        ap_61_90_payment=Decimal("0.75"),
        ap_over_90_payment=Decimal("0.70"),
    ),
}


# =============================================================================
# Engine config / result
# =============================================================================


@dataclass
class CashFlowConfig:
    opening_balance: Decimal
    start_date: date
    ar_aging: AgingBuckets = field(default_factory=AgingBuckets)
    ap_aging: AgingBuckets = field(default_factory=AgingBuckets)
    recurring_flows: list[RecurringFlow] = field(default_factory=list)
    # Materiality threshold for "low-cash week" flag — if the ending
    # balance drops below this at any point, the scenario surfaces a
    # warning. Default None disables the check.
    min_safe_cash: Decimal | None = None


@dataclass
class DailyPoint:
    day_index: int  # 0..89
    day_date: date
    ar_inflow: Decimal
    ap_outflow: Decimal
    recurring_net: Decimal
    net_change: Decimal
    ending_balance: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "day_index": self.day_index,
            "day_date": self.day_date.isoformat(),
            "ar_inflow": str(self.ar_inflow),
            "ap_outflow": str(self.ap_outflow),
            "recurring_net": str(self.recurring_net),
            "net_change": str(self.net_change),
            "ending_balance": str(self.ending_balance),
        }


@dataclass
class HorizonSummary:
    day: int  # 30 / 60 / 90
    cumulative_inflow: Decimal
    cumulative_outflow: Decimal
    ending_balance: Decimal
    lowest_balance: Decimal
    lowest_balance_day: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "day": self.day,
            "cumulative_inflow": str(self.cumulative_inflow),
            "cumulative_outflow": str(self.cumulative_outflow),
            "ending_balance": str(self.ending_balance),
            "lowest_balance": str(self.lowest_balance),
            "lowest_balance_day": self.lowest_balance_day,
        }


@dataclass
class CollectionPriority:
    """AR bucket prioritised for follow-up (highest expected-value at risk)."""

    bucket: str
    amount_outstanding: Decimal
    expected_collection: Decimal
    collection_probability: Decimal  # base-scenario

    def to_dict(self) -> dict[str, Any]:
        return {
            "bucket": self.bucket,
            "amount_outstanding": str(self.amount_outstanding),
            "expected_collection": str(self.expected_collection),
            "collection_probability": str(self.collection_probability),
        }


@dataclass
class ScenarioResult:
    scenario: str
    daily: list[DailyPoint]
    horizon: dict[int, HorizonSummary]
    goes_negative: bool
    first_negative_day: int | None
    breach_min_safe_cash: bool
    collection_priorities: list[CollectionPriority]
    ap_deferral_candidates: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "daily": [d.to_dict() for d in self.daily],
            "horizon": {str(k): v.to_dict() for k, v in self.horizon.items()},
            "goes_negative": self.goes_negative,
            "first_negative_day": self.first_negative_day,
            "breach_min_safe_cash": self.breach_min_safe_cash,
            "collection_priorities": [p.to_dict() for p in self.collection_priorities],
            "ap_deferral_candidates": self.ap_deferral_candidates,
        }


@dataclass
class CashFlowForecast:
    """Top-level engine output."""

    inputs: dict[str, Any]
    scenarios: dict[str, ScenarioResult]
    horizon_days: tuple[int, ...] = HORIZON_BUCKETS

    def to_dict(self) -> dict[str, Any]:
        return {
            "inputs": self.inputs,
            "scenarios": {k: v.to_dict() for k, v in self.scenarios.items()},
            "horizon_days": list(self.horizon_days),
        }


# =============================================================================
# Core projection logic
# =============================================================================


def _quantise(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _ar_inflow_schedule(ar: AgingBuckets, assumptions: ScenarioAssumptions) -> dict[int, Decimal]:
    """Spread expected AR collections across the 90-day horizon.

    Heuristic:
      * ``current`` AR collects linearly across days 0–30 at the
        assumed rate.
      * ``1–30`` AR collects linearly across days 0–20.
      * ``31–60`` AR collects linearly across days 0–15.
      * ``61–90`` AR collects linearly across days 0–10.
      * ``over 90`` AR collects linearly across days 0–45.
    Remaining (uncollected) AR never enters the inflow schedule.
    """
    schedule: dict[int, Decimal] = {d: ZERO for d in range(FORECAST_DAYS)}

    def _spread(total: Decimal, rate: Decimal, days: int) -> None:
        if total <= ZERO or rate <= ZERO or days <= 0:
            return
        expected = total * rate
        per_day = expected / Decimal(days)
        for d in range(min(days, FORECAST_DAYS)):
            schedule[d] += per_day

    _spread(ar.current, assumptions.ar_current_collection, 30)
    _spread(ar.days_1_30, assumptions.ar_1_30_collection, 20)
    _spread(ar.days_31_60, assumptions.ar_31_60_collection, 15)
    _spread(ar.days_61_90, assumptions.ar_61_90_collection, 10)
    _spread(ar.days_over_90, assumptions.ar_over_90_collection, 45)

    return schedule


def _ap_outflow_schedule(ap: AgingBuckets, assumptions: ScenarioAssumptions) -> dict[int, Decimal]:
    """Spread AP payments across the 90-day horizon.

    Heuristic:
      * ``current`` AP pays linearly across days 10–40 (the 30-day
        term window after the balance date).
      * ``1–30`` AP pays linearly across days 0–15.
      * ``31–60`` AP pays linearly across days 0–10.
      * ``61–90`` AP pays linearly across days 0–7 (more urgent).
      * ``over 90`` AP pays linearly across days 0–5.
    """
    schedule: dict[int, Decimal] = {d: ZERO for d in range(FORECAST_DAYS)}

    def _spread(total: Decimal, rate: Decimal, start: int, days: int) -> None:
        if total <= ZERO or rate <= ZERO or days <= 0:
            return
        expected = total * rate
        per_day = expected / Decimal(days)
        end = min(start + days, FORECAST_DAYS)
        actual_days = end - start
        if actual_days <= 0:
            return
        # Re-scale per_day if the horizon cuts off the tail.
        adjusted = expected / Decimal(actual_days) if days > actual_days else per_day
        for d in range(start, end):
            schedule[d] += adjusted

    _spread(ap.current, assumptions.ap_current_payment, 10, 30)
    _spread(ap.days_1_30, assumptions.ap_1_30_payment, 0, 15)
    _spread(ap.days_31_60, assumptions.ap_31_60_payment, 0, 10)
    _spread(ap.days_61_90, assumptions.ap_61_90_payment, 0, 7)
    _spread(ap.days_over_90, assumptions.ap_over_90_payment, 0, 5)

    return schedule


def _recurring_schedule(flows: list[RecurringFlow], start: date) -> dict[int, Decimal]:
    """Flatten recurring flows into per-day amounts over the 90-day horizon."""
    schedule: dict[int, Decimal] = {d: ZERO for d in range(FORECAST_DAYS)}

    step_days = {
        "weekly": 7,
        "biweekly": 14,
        "monthly": 30,  # Approximation for the 90-day forecast
        "quarterly": 90,
    }

    for flow in flows:
        step = step_days[flow.frequency]
        # First hit day relative to the forecast start.
        delta = (flow.first_date - start).days
        day = delta
        while day < 0:
            day += step
        while day < FORECAST_DAYS:
            schedule[day] += flow.amount
            day += step

    return schedule


def _run_scenario(
    config: CashFlowConfig,
    scenario: ScenarioName,
) -> ScenarioResult:
    assumptions = SCENARIOS[scenario]
    ar_schedule = _ar_inflow_schedule(config.ar_aging, assumptions)
    ap_schedule = _ap_outflow_schedule(config.ap_aging, assumptions)
    rec_schedule = _recurring_schedule(config.recurring_flows, config.start_date)

    daily: list[DailyPoint] = []
    balance = config.opening_balance
    goes_negative = False
    first_negative_day: int | None = None
    lowest_balance = config.opening_balance
    lowest_balance_day = 0
    breach_min_safe_cash = False

    cumulative_in = ZERO
    cumulative_out = ZERO
    horizon: dict[int, HorizonSummary] = {}

    for d in range(FORECAST_DAYS):
        ar_in = ar_schedule.get(d, ZERO)
        ap_out = ap_schedule.get(d, ZERO)
        rec_net = rec_schedule.get(d, ZERO)

        net_change = ar_in - ap_out + rec_net
        balance += net_change

        if balance < lowest_balance:
            lowest_balance = balance
            lowest_balance_day = d

        if balance < ZERO and not goes_negative:
            goes_negative = True
            first_negative_day = d

        if config.min_safe_cash is not None and balance < config.min_safe_cash:
            breach_min_safe_cash = True

        cumulative_in += ar_in
        if rec_net > ZERO:
            cumulative_in += rec_net
        cumulative_out += ap_out
        if rec_net < ZERO:
            cumulative_out += -rec_net

        point = DailyPoint(
            day_index=d,
            day_date=config.start_date + timedelta(days=d),
            ar_inflow=_quantise(ar_in),
            ap_outflow=_quantise(ap_out),
            recurring_net=_quantise(rec_net),
            net_change=_quantise(net_change),
            ending_balance=_quantise(balance),
        )
        daily.append(point)

        if (d + 1) in HORIZON_BUCKETS:
            horizon[d + 1] = HorizonSummary(
                day=d + 1,
                cumulative_inflow=_quantise(cumulative_in),
                cumulative_outflow=_quantise(cumulative_out),
                ending_balance=_quantise(balance),
                lowest_balance=_quantise(lowest_balance),
                lowest_balance_day=lowest_balance_day,
            )

    collection_priorities = _collection_priorities(config.ar_aging)
    ap_deferral_candidates = _ap_deferral_candidates(config.ap_aging, scenario)

    return ScenarioResult(
        scenario=scenario.value,
        daily=daily,
        horizon=horizon,
        goes_negative=goes_negative,
        first_negative_day=first_negative_day,
        breach_min_safe_cash=breach_min_safe_cash,
        collection_priorities=collection_priorities,
        ap_deferral_candidates=ap_deferral_candidates,
    )


def _collection_priorities(ar: AgingBuckets) -> list[CollectionPriority]:
    """Rank AR buckets by expected-collection contribution under the base scenario.

    Highest expected cash at reasonable probability wins priority. Older
    buckets typically have the widest expected / outstanding gap — that
    delta is where chasing pays off most.
    """
    base = SCENARIOS[ScenarioName.BASE]
    rows = [
        ("current", ar.current, base.ar_current_collection),
        ("1-30", ar.days_1_30, base.ar_1_30_collection),
        ("31-60", ar.days_31_60, base.ar_31_60_collection),
        ("61-90", ar.days_61_90, base.ar_61_90_collection),
        ("over-90", ar.days_over_90, base.ar_over_90_collection),
    ]
    results = [
        CollectionPriority(
            bucket=name,
            amount_outstanding=_quantise(total),
            expected_collection=_quantise(total * rate),
            collection_probability=rate,
        )
        for name, total, rate in rows
        if total > ZERO
    ]
    # Priority = amount at risk = outstanding - expected.
    results.sort(key=lambda p: p.amount_outstanding - p.expected_collection, reverse=True)
    return results


def _ap_deferral_candidates(ap: AgingBuckets, scenario: ScenarioName) -> list[dict[str, Any]]:
    """Identify AP buckets where deferring payment produces the most liquidity.

    Under the ``best`` scenario assumptions the engine defers more
    aggressively; under ``stress`` no deferral is recommended because
    late fees compound the liquidity problem.
    """
    if scenario == ScenarioName.STRESS:
        return []
    assumptions = SCENARIOS[scenario]
    rows = [
        ("current", ap.current, assumptions.ap_current_payment),
        ("1-30", ap.days_1_30, assumptions.ap_1_30_payment),
        ("31-60", ap.days_31_60, assumptions.ap_31_60_payment),
        ("61-90", ap.days_61_90, assumptions.ap_61_90_payment),
        ("over-90", ap.days_over_90, assumptions.ap_over_90_payment),
    ]
    candidates: list[dict[str, Any]] = []
    for name, total, rate in rows:
        if total > ZERO and rate < Decimal("1.0"):
            deferred = total * (Decimal("1.0") - rate)
            candidates.append(
                {
                    "bucket": name,
                    "outstanding": str(_quantise(total)),
                    "defer_amount": str(_quantise(deferred)),
                    "defer_rate": str(Decimal("1.0") - rate),
                }
            )
    candidates.sort(key=lambda r: Decimal(r["defer_amount"]), reverse=True)
    return candidates


# =============================================================================
# Public entry point
# =============================================================================


def project_cash_flow(config: CashFlowConfig) -> CashFlowForecast:
    """Run the 30 / 60 / 90-day forecast across all three scenarios."""
    if config.opening_balance < ZERO:
        raise CashFlowInputError("Opening balance cannot be negative.")

    scenarios: dict[str, ScenarioResult] = {}
    for name in (ScenarioName.BASE, ScenarioName.STRESS, ScenarioName.BEST):
        scenarios[name.value] = _run_scenario(config, name)

    inputs = {
        "opening_balance": str(_quantise(config.opening_balance)),
        "start_date": config.start_date.isoformat(),
        "ar_total": str(_quantise(config.ar_aging.total())),
        "ap_total": str(_quantise(config.ap_aging.total())),
        "recurring_flow_count": len(config.recurring_flows),
        "min_safe_cash": str(_quantise(config.min_safe_cash)) if config.min_safe_cash is not None else None,
    }

    return CashFlowForecast(inputs=inputs, scenarios=scenarios)
