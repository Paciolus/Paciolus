"""
Lease Accounting Engine (Sprint 629).

Implements the ASC 842 lease classification and initial-measurement workflow
for a single lease. Form-input only — zero-storage compliant.

What this engine does:
- Runs the 5-criteria classification test (ASC 842-10-25-2) and reports the
  result as 'finance' or 'operating'.
- Computes initial measurement: lease liability (PV of remaining payments)
  and ROU asset (liability + prepayments + initial direct costs - lease
  incentives).
- Generates the lease-liability amortization schedule using the effective-
  interest method.
- Generates the ROU-asset amortization schedule:
    * Operating: total lease cost is straight-line; ROU amortization plugs the
      difference between SL lease cost and period interest expense.
    * Finance: ROU is amortized straight-line independently from the
      liability's interest accretion.
- Builds disclosure tables: 5-year maturity analysis with thereafter, plus
  weighted-average remaining lease term and discount rate.

What this engine does NOT do (intentionally deferred):
- Modifications and remeasurements (rate change, scope change, term change).
- Sublease accounting and lessor accounting.
- Variable lease payments tied to an index (only fixed-step escalation).
- Short-term lease practical expedient (caller decides).

References:
- ASC 842-10-25-2 (classification criteria)
- ASC 842-20-30 / 842-20-35 (lessee initial and subsequent measurement)
- ASC 842-20-50 (disclosure)
- IFRS 16 (analogous; finance lease model only)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Literal, Optional

from dateutil.relativedelta import relativedelta

CENT = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")

# ASC 842 thresholds
PV_FV_THRESHOLD = Decimal("0.90")  # ASC 842-10-25-2(d): PV of payments ≥ 90% of FV
LIFE_PERCENT_THRESHOLD = Decimal("0.75")  # ASC 842-10-25-2(c): term ≥ 75% of useful life

PaymentFrequency = Literal["monthly", "quarterly", "semi-annual", "annual"]
PERIODS_PER_YEAR: dict[str, int] = {"monthly": 12, "quarterly": 4, "semi-annual": 2, "annual": 1}
MONTHS_PER_PERIOD: dict[str, int] = {"monthly": 1, "quarterly": 3, "semi-annual": 6, "annual": 12}


class LeaseClassification(str, Enum):
    OPERATING = "operating"
    FINANCE = "finance"


class LeaseInputError(ValueError):
    """Raised for invalid lease parameters."""


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class LeaseConfig:
    """Inputs for a single lease."""

    lease_name: str
    payment_amount: Decimal  # base periodic payment (in advance is the default)
    term_periods: int  # number of payment periods over the lease term
    annual_discount_rate: Decimal  # incremental borrowing rate or implicit rate
    frequency: PaymentFrequency = "monthly"
    payments_in_advance: bool = True  # standard real-estate / equipment convention
    annual_escalation_rate: Decimal = ZERO  # CPI/fixed step-up applied annually
    initial_direct_costs: Decimal = ZERO
    prepaid_lease_payments: Decimal = ZERO
    lease_incentives: Decimal = ZERO
    asset_useful_life_years: Optional[int] = None  # for life-percent test
    asset_fair_value: Optional[Decimal] = None  # for PV/FV test
    transfers_ownership: bool = False  # ASC 842-10-25-2(a)
    bargain_purchase_option: bool = False  # ASC 842-10-25-2(b)
    specialized_nature: bool = False  # ASC 842-10-25-2(e)
    start_date: Optional[date] = None

    def validate(self) -> None:
        if self.payment_amount <= 0:
            raise LeaseInputError("Payment amount must be positive.")
        if self.term_periods <= 0:
            raise LeaseInputError("Term must be at least one period.")
        if self.term_periods > 600:
            raise LeaseInputError("Term exceeds the 600-period cap.")
        if self.annual_discount_rate < 0:
            raise LeaseInputError("Discount rate cannot be negative.")
        if self.annual_escalation_rate < 0:
            raise LeaseInputError("Escalation rate cannot be negative.")
        if self.frequency not in PERIODS_PER_YEAR:
            raise LeaseInputError(f"Unsupported frequency: {self.frequency}")
        if self.asset_useful_life_years is not None and self.asset_useful_life_years <= 0:
            raise LeaseInputError("Asset useful life must be positive.")
        if self.asset_fair_value is not None and self.asset_fair_value <= 0:
            raise LeaseInputError("Asset fair value must be positive.")


# =============================================================================
# Result dataclasses
# =============================================================================


@dataclass
class ClassificationCriterion:
    """One leg of the ASC 842-10-25-2 classification test."""

    code: str  # "a" .. "e"
    label: str
    triggered: bool
    detail: str = ""

    def to_dict(self) -> dict:
        return {"code": self.code, "label": self.label, "triggered": self.triggered, "detail": self.detail}


@dataclass
class ClassificationResult:
    classification: LeaseClassification
    criteria: list[ClassificationCriterion]

    def to_dict(self) -> dict:
        return {
            "classification": self.classification.value,
            "criteria": [c.to_dict() for c in self.criteria],
        }


@dataclass
class LiabilityScheduleEntry:
    period_number: int
    payment_date: Optional[date]
    payment: Decimal
    interest: Decimal
    principal: Decimal
    ending_liability: Decimal

    def to_dict(self) -> dict:
        return {
            "period_number": self.period_number,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "payment": str(self.payment),
            "interest": str(self.interest),
            "principal": str(self.principal),
            "ending_liability": str(self.ending_liability),
        }


@dataclass
class RouScheduleEntry:
    period_number: int
    payment_date: Optional[date]
    rou_amortization: Decimal
    period_lease_cost: Decimal  # Total expense recognized this period
    ending_rou_balance: Decimal

    def to_dict(self) -> dict:
        return {
            "period_number": self.period_number,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "rou_amortization": str(self.rou_amortization),
            "period_lease_cost": str(self.period_lease_cost),
            "ending_rou_balance": str(self.ending_rou_balance),
        }


@dataclass
class MaturityBucket:
    label: str  # "Year 1", "Year 2", ..., "Thereafter"
    undiscounted_payments: Decimal

    def to_dict(self) -> dict:
        return {"label": self.label, "undiscounted_payments": str(self.undiscounted_payments)}


@dataclass
class DisclosureTables:
    maturity_analysis: list[MaturityBucket]
    total_undiscounted_payments: Decimal
    less_imputed_interest: Decimal
    present_value_of_lease_liability: Decimal
    weighted_average_remaining_term_years: Decimal
    weighted_average_discount_rate: Decimal

    def to_dict(self) -> dict:
        return {
            "maturity_analysis": [b.to_dict() for b in self.maturity_analysis],
            "total_undiscounted_payments": str(self.total_undiscounted_payments),
            "less_imputed_interest": str(self.less_imputed_interest),
            "present_value_of_lease_liability": str(self.present_value_of_lease_liability),
            "weighted_average_remaining_term_years": str(self.weighted_average_remaining_term_years),
            "weighted_average_discount_rate": str(self.weighted_average_discount_rate),
        }


@dataclass
class LeaseAccountingResult:
    config: LeaseConfig
    classification_result: ClassificationResult
    initial_lease_liability: Decimal
    initial_rou_asset: Decimal
    liability_schedule: list[LiabilityScheduleEntry]
    rou_schedule: list[RouScheduleEntry]
    disclosure_tables: DisclosureTables
    total_lease_cost: Decimal
    total_interest_expense: Decimal

    def to_dict(self) -> dict:
        return {
            "inputs": {
                "lease_name": self.config.lease_name,
                "payment_amount": str(self.config.payment_amount),
                "term_periods": self.config.term_periods,
                "annual_discount_rate": str(self.config.annual_discount_rate),
                "frequency": self.config.frequency,
                "payments_in_advance": self.config.payments_in_advance,
                "annual_escalation_rate": str(self.config.annual_escalation_rate),
                "initial_direct_costs": str(self.config.initial_direct_costs),
                "prepaid_lease_payments": str(self.config.prepaid_lease_payments),
                "lease_incentives": str(self.config.lease_incentives),
                "asset_useful_life_years": self.config.asset_useful_life_years,
                "asset_fair_value": (str(self.config.asset_fair_value) if self.config.asset_fair_value else None),
                "transfers_ownership": self.config.transfers_ownership,
                "bargain_purchase_option": self.config.bargain_purchase_option,
                "specialized_nature": self.config.specialized_nature,
                "start_date": self.config.start_date.isoformat() if self.config.start_date else None,
            },
            "classification": self.classification_result.to_dict(),
            "initial_lease_liability": str(self.initial_lease_liability),
            "initial_rou_asset": str(self.initial_rou_asset),
            "liability_schedule": [e.to_dict() for e in self.liability_schedule],
            "rou_schedule": [e.to_dict() for e in self.rou_schedule],
            "disclosure_tables": self.disclosure_tables.to_dict(),
            "total_lease_cost": str(self.total_lease_cost),
            "total_interest_expense": str(self.total_interest_expense),
        }


# =============================================================================
# Helpers
# =============================================================================


def _q(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _period_rate(annual_rate: Decimal, frequency: PaymentFrequency) -> Decimal:
    return annual_rate / Decimal(PERIODS_PER_YEAR[frequency])


def _build_payment_stream(config: LeaseConfig) -> list[Decimal]:
    """Generate per-period payment amounts, applying the annual escalation."""
    base = config.payment_amount
    periods_per_year = PERIODS_PER_YEAR[config.frequency]
    payments: list[Decimal] = []
    for period_idx in range(1, config.term_periods + 1):
        years_elapsed = (period_idx - 1) // periods_per_year
        if years_elapsed == 0 or config.annual_escalation_rate == 0:
            payments.append(base)
        else:
            multiplier = (Decimal("1") + config.annual_escalation_rate) ** years_elapsed
            payments.append(base * multiplier)
    return payments


def _present_value(payments: list[Decimal], period_rate: Decimal, in_advance: bool) -> Decimal:
    """PV of the payment stream at the given period rate."""
    if period_rate == 0:
        return sum(payments, ZERO)
    pv = ZERO
    for idx, payment in enumerate(payments, start=1):
        # Payments in advance: payment 1 at t=0, payment 2 at t=1, ...
        # Payments in arrears: payment 1 at t=1, payment 2 at t=2, ...
        period_offset = idx - 1 if in_advance else idx
        pv += payment / ((Decimal("1") + period_rate) ** period_offset)
    return pv


# =============================================================================
# Classification (ASC 842-10-25-2)
# =============================================================================


def classify_lease(config: LeaseConfig, present_value: Decimal) -> ClassificationResult:
    """Run the 5-criteria classification test. ANY triggered criterion drives
    classification to finance; otherwise operating.
    """
    criteria: list[ClassificationCriterion] = []

    # (a) Transfers ownership
    criteria.append(
        ClassificationCriterion(
            code="a",
            label="Transfers ownership of the underlying asset to the lessee",
            triggered=config.transfers_ownership,
            detail="Auditor input — transfer at end of term means automatic finance lease.",
        )
    )

    # (b) Bargain / reasonably-certain purchase option
    criteria.append(
        ClassificationCriterion(
            code="b",
            label="Lessee is reasonably certain to exercise a purchase option",
            triggered=config.bargain_purchase_option,
            detail="Auditor input — bargain purchase option means automatic finance lease.",
        )
    )

    # (c) Lease term ≥ 75% of asset useful life
    if config.asset_useful_life_years and config.asset_useful_life_years > 0:
        lease_term_years = Decimal(config.term_periods) / Decimal(PERIODS_PER_YEAR[config.frequency])
        useful_life = Decimal(config.asset_useful_life_years)
        ratio = lease_term_years / useful_life
        triggered_c = ratio >= LIFE_PERCENT_THRESHOLD
        detail_c = f"Lease term {lease_term_years:.2f} yrs / useful life {useful_life} yrs = {ratio:.2%}."
    else:
        triggered_c = False
        detail_c = "Asset useful life not provided — criterion not evaluable."
    criteria.append(
        ClassificationCriterion(
            code="c",
            label="Lease term covers the major part (≥75%) of the asset's remaining useful life",
            triggered=triggered_c,
            detail=detail_c,
        )
    )

    # (d) PV of lease payments ≥ 90% of fair value
    if config.asset_fair_value and config.asset_fair_value > 0:
        ratio_d = present_value / config.asset_fair_value
        triggered_d = ratio_d >= PV_FV_THRESHOLD
        detail_d = f"PV ${present_value:.2f} / FV ${config.asset_fair_value:.2f} = {ratio_d:.2%}."
    else:
        triggered_d = False
        detail_d = "Asset fair value not provided — criterion not evaluable."
    criteria.append(
        ClassificationCriterion(
            code="d",
            label="PV of lease payments substantially exceeds (≥90%) the fair value of the underlying asset",
            triggered=triggered_d,
            detail=detail_d,
        )
    )

    # (e) Specialized nature
    criteria.append(
        ClassificationCriterion(
            code="e",
            label="Underlying asset is so specialized it has no alternative use to the lessor at end of term",
            triggered=config.specialized_nature,
            detail="Auditor input.",
        )
    )

    classification = (
        LeaseClassification.FINANCE if any(c.triggered for c in criteria) else LeaseClassification.OPERATING
    )
    return ClassificationResult(classification=classification, criteria=criteria)


# =============================================================================
# Schedules
# =============================================================================


def _build_liability_schedule(
    config: LeaseConfig,
    payments: list[Decimal],
    period_rate: Decimal,
    initial_liability: Decimal,
) -> list[LiabilityScheduleEntry]:
    """Effective-interest amortization. With payments in advance, payment is
    applied at the start of the period; interest then accrues on the remaining
    balance over the period.
    """
    schedule: list[LiabilityScheduleEntry] = []
    months_per_period = MONTHS_PER_PERIOD[config.frequency]
    balance = initial_liability
    for idx, payment in enumerate(payments, start=1):
        is_final = idx == len(payments)
        if config.payments_in_advance:
            # Payment applied at start of period; interest accrues after the
            # payment over the remaining balance. No interest accrues after
            # the final in-advance payment because the lease has ended.
            balance_after_payment = balance - payment
            if is_final:
                interest = ZERO
            else:
                interest = balance_after_payment * period_rate
            balance_end = balance_after_payment + interest
            # Principal reduction is the net change in liability
            principal_part = balance - balance_end
        else:
            interest = balance * period_rate
            balance_after_interest = balance + interest
            principal_part = payment - interest
            balance_end = balance_after_interest - payment
        if is_final:
            # Absorb any rounding drift: force EOP to zero
            principal_part = principal_part + balance_end
            balance_end = ZERO
        if balance_end < 0:
            balance_end = ZERO
        payment_date: Optional[date] = None
        if config.start_date is not None:
            payment_date = config.start_date + relativedelta(months=months_per_period * (idx - 1))
        schedule.append(
            LiabilityScheduleEntry(
                period_number=idx,
                payment_date=payment_date,
                payment=_q(payment),
                interest=_q(interest),
                principal=_q(principal_part),
                ending_liability=_q(balance_end),
            )
        )
        balance = balance_end
    return schedule


def _build_operating_rou_schedule(
    config: LeaseConfig,
    payments: list[Decimal],
    liability_schedule: list[LiabilityScheduleEntry],
    initial_rou: Decimal,
) -> list[RouScheduleEntry]:
    """Operating lease: total lease cost is straight-line over the term;
    ROU amortization plugs the difference between SL cost and period interest.
    """
    total_payments = sum(payments, ZERO)
    sl_period_cost = total_payments / Decimal(config.term_periods)
    months_per_period = MONTHS_PER_PERIOD[config.frequency]
    schedule: list[RouScheduleEntry] = []
    rou_balance = initial_rou
    for idx, liability_entry in enumerate(liability_schedule, start=1):
        is_final = idx == len(liability_schedule)
        rou_amortization = sl_period_cost - liability_entry.interest
        if is_final:
            # Force ending ROU to exactly zero
            rou_amortization = rou_balance
        if rou_amortization > rou_balance:
            rou_amortization = rou_balance
        if rou_amortization < 0:
            rou_amortization = ZERO
        rou_balance = rou_balance - rou_amortization
        payment_date: Optional[date] = None
        if config.start_date is not None:
            payment_date = config.start_date + relativedelta(months=months_per_period * (idx - 1))
        schedule.append(
            RouScheduleEntry(
                period_number=idx,
                payment_date=payment_date,
                rou_amortization=_q(rou_amortization),
                period_lease_cost=_q(sl_period_cost),
                ending_rou_balance=_q(rou_balance),
            )
        )
    return schedule


def _build_finance_rou_schedule(
    config: LeaseConfig,
    liability_schedule: list[LiabilityScheduleEntry],
    initial_rou: Decimal,
) -> list[RouScheduleEntry]:
    """Finance lease: ROU amortized straight-line, separate from interest."""
    months_per_period = MONTHS_PER_PERIOD[config.frequency]
    sl_amortization = initial_rou / Decimal(config.term_periods)
    schedule: list[RouScheduleEntry] = []
    rou_balance = initial_rou
    for idx, liability_entry in enumerate(liability_schedule, start=1):
        is_final = idx == len(liability_schedule)
        rou_amort = sl_amortization
        if is_final:
            rou_amort = rou_balance
        if rou_amort > rou_balance:
            rou_amort = rou_balance
        rou_balance = rou_balance - rou_amort
        # Period lease cost = ROU amortization + interest (not blended)
        period_cost = rou_amort + liability_entry.interest
        payment_date: Optional[date] = None
        if config.start_date is not None:
            payment_date = config.start_date + relativedelta(months=months_per_period * (idx - 1))
        schedule.append(
            RouScheduleEntry(
                period_number=idx,
                payment_date=payment_date,
                rou_amortization=_q(rou_amort),
                period_lease_cost=_q(period_cost),
                ending_rou_balance=_q(rou_balance),
            )
        )
    return schedule


# =============================================================================
# Disclosures
# =============================================================================


def _build_disclosure_tables(
    config: LeaseConfig,
    payments: list[Decimal],
    liability_schedule: list[LiabilityScheduleEntry],
    initial_liability: Decimal,
) -> DisclosureTables:
    """Maturity analysis: payments by year for years 1-5, then 'Thereafter'."""
    periods_per_year = PERIODS_PER_YEAR[config.frequency]
    by_year: dict[int, Decimal] = {}
    for idx, payment in enumerate(payments, start=1):
        year_idx = (idx - 1) // periods_per_year + 1
        by_year[year_idx] = by_year.get(year_idx, ZERO) + payment

    buckets: list[MaturityBucket] = []
    for year in range(1, 6):
        buckets.append(MaturityBucket(label=f"Year {year}", undiscounted_payments=_q(by_year.get(year, ZERO))))
    thereafter = sum((amt for yr, amt in by_year.items() if yr >= 6), ZERO)
    buckets.append(MaturityBucket(label="Thereafter", undiscounted_payments=_q(thereafter)))

    total_undiscounted = sum(payments, ZERO)
    less_interest = total_undiscounted - initial_liability

    # Weighted-average remaining term: sum(remaining_periods * payment) / sum(payments)
    # in years
    if total_undiscounted == 0:
        weighted_term = ZERO
    else:
        weighted_period_sum = sum(
            (Decimal(idx) * pay for idx, pay in enumerate(payments, start=1)),
            ZERO,
        )
        weighted_term = (weighted_period_sum / total_undiscounted) / Decimal(periods_per_year)

    return DisclosureTables(
        maturity_analysis=buckets,
        total_undiscounted_payments=_q(total_undiscounted),
        less_imputed_interest=_q(less_interest),
        present_value_of_lease_liability=_q(initial_liability),
        weighted_average_remaining_term_years=weighted_term.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        weighted_average_discount_rate=config.annual_discount_rate.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
    )


# =============================================================================
# Public engine
# =============================================================================


def compute_lease_accounting(config: LeaseConfig) -> LeaseAccountingResult:
    """Run the full ASC 842 lessee workflow for a single lease."""
    config.validate()
    payments = _build_payment_stream(config)
    period_rate = _period_rate(config.annual_discount_rate, config.frequency)
    initial_liability = _present_value(payments, period_rate, config.payments_in_advance)

    classification_result = classify_lease(config, initial_liability)

    initial_rou = (
        initial_liability + config.prepaid_lease_payments + config.initial_direct_costs - config.lease_incentives
    )
    if initial_rou < 0:
        initial_rou = ZERO

    liability_schedule = _build_liability_schedule(config, payments, period_rate, initial_liability)

    if classification_result.classification == LeaseClassification.OPERATING:
        rou_schedule = _build_operating_rou_schedule(config, payments, liability_schedule, initial_rou)
    else:
        rou_schedule = _build_finance_rou_schedule(config, liability_schedule, initial_rou)

    disclosures = _build_disclosure_tables(config, payments, liability_schedule, initial_liability)

    total_interest = sum((e.interest for e in liability_schedule), ZERO)
    total_cost = sum((e.period_lease_cost for e in rou_schedule), ZERO)

    return LeaseAccountingResult(
        config=config,
        classification_result=classification_result,
        initial_lease_liability=_q(initial_liability),
        initial_rou_asset=_q(initial_rou),
        liability_schedule=liability_schedule,
        rou_schedule=rou_schedule,
        disclosure_tables=disclosures,
        total_lease_cost=_q(total_cost),
        total_interest_expense=_q(total_interest),
    )
