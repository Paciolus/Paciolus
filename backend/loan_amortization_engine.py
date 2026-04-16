"""
Loan Amortization Engine (Sprint 625).

Generates period-by-period amortization schedules for fixed and variable-rate
loans. Supports standard level-payment amortization, interest-only loans,
balloon loans (level payment plus a final lump sum), and ad-hoc extra
principal payments. Form-input only — zero-storage compliant.

All monetary math uses Decimal with HALF_UP rounding at the final
quantization step. Per-period interest is computed at full precision and
only rounded for the schedule output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Literal, Optional

from dateutil.relativedelta import relativedelta

# =============================================================================
# Constants
# =============================================================================

CENT = Decimal("0.01")
ZERO = Decimal("0")

# Periods per year by payment frequency
PERIODS_PER_YEAR: dict[str, int] = {
    "monthly": 12,
    "quarterly": 4,
    "semi-annual": 2,
    "annual": 1,
}

MONTHS_PER_PERIOD: dict[str, int] = {
    "monthly": 1,
    "quarterly": 3,
    "semi-annual": 6,
    "annual": 12,
}

MAX_TERM_PERIODS = 600  # Hard cap to prevent runaway schedules (50 yrs monthly)


# =============================================================================
# Configuration & errors
# =============================================================================


class LoanMethod(str, Enum):
    STANDARD = "standard"  # Level-payment fully amortizing
    INTEREST_ONLY = "interest_only"  # Interest only until final balloon
    BALLOON = "balloon"  # Level payment, lump-sum at maturity


PaymentFrequency = Literal["monthly", "quarterly", "semi-annual", "annual"]


class LoanInputError(ValueError):
    """Raised for invalid loan parameters."""


@dataclass
class RateChange:
    """Variable-rate trigger — at `period_number` (1-indexed) the rate becomes
    `new_annual_rate` (decimal, e.g. 0.06 for 6%).

    The new rate is applied for that period and subsequent periods until the
    next change. Standard loans recompute the level payment from the new rate
    over the remaining periods.
    """

    period_number: int
    new_annual_rate: Decimal


@dataclass
class ExtraPayment:
    """Additional principal payment applied at the end of `period_number`,
    after the regular payment but before the next period's interest accrues.
    """

    period_number: int
    amount: Decimal


@dataclass
class LoanConfig:
    """Inputs to the amortization engine."""

    principal: Decimal
    annual_rate: Decimal  # Decimal form (0.06 for 6%)
    term_periods: int  # Number of payment periods
    frequency: PaymentFrequency = "monthly"
    method: LoanMethod = LoanMethod.STANDARD
    start_date: Optional[date] = None
    balloon_amount: Optional[Decimal] = None  # Required for BALLOON
    extra_payments: list[ExtraPayment] = field(default_factory=list)
    rate_changes: list[RateChange] = field(default_factory=list)

    def validate(self) -> None:
        if self.principal <= 0:
            raise LoanInputError("Principal must be positive.")
        if self.annual_rate < 0:
            raise LoanInputError("Annual rate cannot be negative.")
        if self.term_periods <= 0:
            raise LoanInputError("Term must be at least one period.")
        if self.term_periods > MAX_TERM_PERIODS:
            raise LoanInputError(f"Term exceeds maximum of {MAX_TERM_PERIODS} periods.")
        if self.frequency not in PERIODS_PER_YEAR:
            raise LoanInputError(f"Unsupported frequency: {self.frequency}")
        if self.method == LoanMethod.BALLOON:
            if self.balloon_amount is None or self.balloon_amount <= 0:
                raise LoanInputError("Balloon loans require a positive balloon_amount.")
            if self.balloon_amount > self.principal:
                raise LoanInputError("Balloon amount cannot exceed principal.")
        for chg in self.rate_changes:
            if chg.period_number < 1 or chg.period_number > self.term_periods:
                raise LoanInputError(f"Rate change period {chg.period_number} is outside the loan term.")
            if chg.new_annual_rate < 0:
                raise LoanInputError("Rate change cannot be negative.")
        for extra in self.extra_payments:
            if extra.period_number < 1 or extra.period_number > self.term_periods:
                raise LoanInputError(f"Extra payment period {extra.period_number} is outside the loan term.")
            if extra.amount <= 0:
                raise LoanInputError("Extra payments must be positive.")


# =============================================================================
# Result dataclasses
# =============================================================================


@dataclass
class PeriodEntry:
    period_number: int
    payment_date: Optional[date]
    beginning_balance: Decimal
    scheduled_payment: Decimal
    interest: Decimal
    principal: Decimal
    extra_principal: Decimal
    ending_balance: Decimal

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "period_number": self.period_number,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "beginning_balance": str(self.beginning_balance),
            "scheduled_payment": str(self.scheduled_payment),
            "interest": str(self.interest),
            "principal": str(self.principal),
            "extra_principal": str(self.extra_principal),
            "ending_balance": str(self.ending_balance),
        }


@dataclass
class AnnualSummary:
    year_index: int  # 1-indexed year of the loan
    calendar_year: Optional[int]  # If start_date provided
    total_payments: Decimal
    total_interest: Decimal
    total_principal: Decimal
    ending_balance: Decimal

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "year_index": self.year_index,
            "calendar_year": self.calendar_year,
            "total_payments": str(self.total_payments),
            "total_interest": str(self.total_interest),
            "total_principal": str(self.total_principal),
            "ending_balance": str(self.ending_balance),
        }


@dataclass
class JournalEntryTemplate:
    """Suggested book journal entry templates for the loan."""

    description: str
    debits: list[tuple[str, Decimal]]
    credits: list[tuple[str, Decimal]]

    def to_dict(self) -> dict[str, object]:
        return {
            "description": self.description,
            "debits": [{"account": a, "amount": str(amt)} for a, amt in self.debits],
            "credits": [{"account": a, "amount": str(amt)} for a, amt in self.credits],
        }


@dataclass
class AmortizationResult:
    config: LoanConfig
    schedule: list[PeriodEntry]
    annual_summary: list[AnnualSummary]
    total_interest: Decimal
    total_payments: Decimal
    payoff_date: Optional[date]
    journal_entry_templates: list[JournalEntryTemplate]

    def to_dict(self) -> dict[str, object]:
        return {
            "inputs": {
                "principal": str(self.config.principal),
                "annual_rate": str(self.config.annual_rate),
                "term_periods": self.config.term_periods,
                "frequency": self.config.frequency,
                "method": self.config.method.value,
                "start_date": self.config.start_date.isoformat() if self.config.start_date else None,
                "balloon_amount": str(self.config.balloon_amount) if self.config.balloon_amount else None,
                "extra_payments": [
                    {"period_number": e.period_number, "amount": str(e.amount)} for e in self.config.extra_payments
                ],
                "rate_changes": [
                    {"period_number": r.period_number, "new_annual_rate": str(r.new_annual_rate)}
                    for r in self.config.rate_changes
                ],
            },
            "schedule": [p.to_dict() for p in self.schedule],
            "annual_summary": [s.to_dict() for s in self.annual_summary],
            "total_interest": str(self.total_interest),
            "total_payments": str(self.total_payments),
            "payoff_date": self.payoff_date.isoformat() if self.payoff_date else None,
            "journal_entry_templates": [t.to_dict() for t in self.journal_entry_templates],
        }


# =============================================================================
# Math helpers
# =============================================================================


def _q(value: Decimal) -> Decimal:
    """Quantize to cents using HALF_UP."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _period_rate(annual_rate: Decimal, frequency: PaymentFrequency) -> Decimal:
    return annual_rate / Decimal(PERIODS_PER_YEAR[frequency])


def _level_payment(principal: Decimal, period_rate: Decimal, periods: int) -> Decimal:
    """Standard level-payment amortization formula.

    P = L * r / (1 - (1+r)^-n) for r > 0, or L / n for r == 0.
    """
    if periods <= 0:
        raise LoanInputError("Periods must be positive for payment calculation.")
    if period_rate == 0:
        return principal / Decimal(periods)
    one_plus_r = Decimal(1) + period_rate
    factor = one_plus_r**-periods
    return principal * period_rate / (Decimal(1) - factor)


def _balloon_payment(principal: Decimal, balloon: Decimal, period_rate: Decimal, periods: int) -> Decimal:
    """Level payment that amortizes (principal - PV(balloon)) over `periods`.

    The balloon is paid at maturity in addition to the final scheduled payment,
    so per-period payment amortizes only the non-balloon portion.
    """
    if periods <= 0:
        raise LoanInputError("Periods must be positive for payment calculation.")
    if period_rate == 0:
        return (principal - balloon) / Decimal(periods)
    one_plus_r = Decimal(1) + period_rate
    pv_balloon = balloon / (one_plus_r**periods)
    amortizable = principal - pv_balloon
    return _level_payment(amortizable, period_rate, periods)


# =============================================================================
# Public engine
# =============================================================================


def generate_amortization_schedule(config: LoanConfig) -> AmortizationResult:
    """Compute full amortization schedule for the supplied configuration."""
    config.validate()

    frequency = config.frequency
    months_per_period = MONTHS_PER_PERIOD[frequency]
    rate_change_map = {chg.period_number: chg.new_annual_rate for chg in config.rate_changes}
    extra_map: dict[int, Decimal] = {}
    for extra in config.extra_payments:
        extra_map[extra.period_number] = extra_map.get(extra.period_number, ZERO) + extra.amount

    current_annual_rate = config.annual_rate
    period_rate = _period_rate(current_annual_rate, frequency)

    if config.method == LoanMethod.STANDARD:
        scheduled_payment = _level_payment(config.principal, period_rate, config.term_periods)
    elif config.method == LoanMethod.BALLOON:
        assert config.balloon_amount is not None  # validated above
        scheduled_payment = _balloon_payment(config.principal, config.balloon_amount, period_rate, config.term_periods)
    else:  # INTEREST_ONLY
        scheduled_payment = config.principal * period_rate

    balance = config.principal
    schedule: list[PeriodEntry] = []
    total_interest = ZERO
    total_payments = ZERO

    for period_idx in range(1, config.term_periods + 1):
        # Apply variable-rate change if scheduled at this period
        if period_idx in rate_change_map:
            current_annual_rate = rate_change_map[period_idx]
            period_rate = _period_rate(current_annual_rate, frequency)
            remaining = config.term_periods - period_idx + 1
            if config.method == LoanMethod.STANDARD:
                scheduled_payment = _level_payment(balance, period_rate, remaining)
            elif config.method == LoanMethod.BALLOON and config.balloon_amount is not None:
                if balance > config.balloon_amount:
                    scheduled_payment = _balloon_payment(balance, config.balloon_amount, period_rate, remaining)
                else:
                    scheduled_payment = balance * period_rate
            else:
                scheduled_payment = balance * period_rate

        interest = balance * period_rate
        is_final = period_idx == config.term_periods

        if config.method == LoanMethod.INTEREST_ONLY:
            principal_portion = balance if is_final else ZERO
            payment_amount = interest + principal_portion
        elif config.method == LoanMethod.BALLOON:
            assert config.balloon_amount is not None
            if is_final:
                # Final scheduled payment + balloon lump sum on top
                principal_portion = balance - ZERO  # whatever is left
                payment_amount = interest + principal_portion
            else:
                principal_portion = scheduled_payment - interest
                if principal_portion < 0:
                    principal_portion = ZERO
                payment_amount = scheduled_payment
        else:  # STANDARD
            if is_final:
                # Last payment fully retires the balance regardless of rounding drift
                principal_portion = balance
                payment_amount = interest + principal_portion
            else:
                principal_portion = scheduled_payment - interest
                if principal_portion > balance:
                    principal_portion = balance
                payment_amount = scheduled_payment

        # Apply scheduled principal first
        beginning_balance = balance
        balance = balance - principal_portion
        if balance < 0:
            # Numerical drift on final period — clamp
            balance = ZERO

        # Apply extra principal (capped at remaining balance)
        extra_amount = extra_map.get(period_idx, ZERO)
        if extra_amount > balance:
            extra_amount = balance
        balance = balance - extra_amount

        # Quantize for the schedule
        q_interest = _q(interest)
        q_payment = _q(payment_amount)
        q_principal = _q(principal_portion)
        q_extra = _q(extra_amount)
        q_begin = _q(beginning_balance)
        q_end = _q(balance)

        payment_date: Optional[date] = None
        if config.start_date is not None:
            payment_date = config.start_date + relativedelta(months=months_per_period * period_idx)

        schedule.append(
            PeriodEntry(
                period_number=period_idx,
                payment_date=payment_date,
                beginning_balance=q_begin,
                scheduled_payment=q_payment,
                interest=q_interest,
                principal=q_principal,
                extra_principal=q_extra,
                ending_balance=q_end,
            )
        )

        total_interest += q_interest
        total_payments += q_payment + q_extra

        if balance == 0 and period_idx < config.term_periods:
            # Loan paid off early via extra payments — stop schedule
            break

    payoff_date = schedule[-1].payment_date if schedule else None
    annual_summary = _build_annual_summary(schedule, frequency, config.start_date)
    je_templates = _build_journal_entry_templates(config, schedule)

    return AmortizationResult(
        config=config,
        schedule=schedule,
        annual_summary=annual_summary,
        total_interest=_q(total_interest),
        total_payments=_q(total_payments),
        payoff_date=payoff_date,
        journal_entry_templates=je_templates,
    )


def _build_annual_summary(
    schedule: list[PeriodEntry],
    frequency: PaymentFrequency,
    start_date: Optional[date],
) -> list[AnnualSummary]:
    if not schedule:
        return []
    periods_per_year = PERIODS_PER_YEAR[frequency]
    years: dict[int, dict[str, Decimal]] = {}
    last_balance_by_year: dict[int, Decimal] = {}

    for entry in schedule:
        year_idx = (entry.period_number - 1) // periods_per_year + 1
        bucket = years.setdefault(
            year_idx,
            {"payments": ZERO, "interest": ZERO, "principal": ZERO},
        )
        bucket["payments"] += entry.scheduled_payment + entry.extra_principal
        bucket["interest"] += entry.interest
        bucket["principal"] += entry.principal + entry.extra_principal
        last_balance_by_year[year_idx] = entry.ending_balance

    summaries: list[AnnualSummary] = []
    for year_idx in sorted(years.keys()):
        bucket = years[year_idx]
        cal_year: Optional[int] = None
        if start_date is not None:
            cal_year = (start_date + relativedelta(years=year_idx - 1)).year
        summaries.append(
            AnnualSummary(
                year_index=year_idx,
                calendar_year=cal_year,
                total_payments=_q(bucket["payments"]),
                total_interest=_q(bucket["interest"]),
                total_principal=_q(bucket["principal"]),
                ending_balance=last_balance_by_year[year_idx],
            )
        )
    return summaries


def _build_journal_entry_templates(config: LoanConfig, schedule: list[PeriodEntry]) -> list[JournalEntryTemplate]:
    if not schedule:
        return []
    first = schedule[0]
    return [
        JournalEntryTemplate(
            description="Loan inception — record loan proceeds",
            debits=[("Cash", config.principal)],
            credits=[("Notes Payable", config.principal)],
        ),
        JournalEntryTemplate(
            description=f"Period {first.period_number} payment — split interest and principal",
            debits=[
                ("Interest Expense", first.interest),
                ("Notes Payable", first.principal + first.extra_principal),
            ],
            credits=[("Cash", first.scheduled_payment + first.extra_principal)],
        ),
    ]
