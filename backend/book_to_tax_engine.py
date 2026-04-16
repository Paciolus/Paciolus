"""
Book-to-Tax Adjustment Engine (Sprint 635).

Reconciles book income (per GAAP) to taxable income by classifying
adjustments into permanent and temporary differences, produces an
IRS Schedule M-1 / M-3 layout, and rolls the timing differences into
a deferred tax asset / liability summary.

Zero-storage: form-input only. The engine is a calculator, not a tax
opinion — the practitioner remains responsible for whether a given
adjustment is permanent vs temporary for the entity's facts.

Entity-size heuristic for M-1 vs M-3 output: assets under $10M → M-1;
$10M and above → M-3 (IRS Schedule M-3 threshold for corporations). The
engine emits both schedules so the caller can render whichever is
appropriate for the engagement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

CENT = Decimal("0.01")
ZERO = Decimal("0")

M3_THRESHOLD_TOTAL_ASSETS = Decimal("10000000")  # IRS Schedule M-3 trigger


class DifferenceType(str, Enum):
    PERMANENT = "permanent"
    TEMPORARY = "temporary"


class AdjustmentDirection(str, Enum):
    # Direction describes how the adjustment moves book toward tax.
    ADD = "add"  # Add to book income to arrive at taxable income
    SUBTRACT = "subtract"


# Catalog of common permanent and temporary book-to-tax differences.
# The engine accepts either a free-form label or one of these standard
# codes. Permanent items never reverse — they create a permanent gap
# between the effective and statutory rates. Temporary items reverse
# over time and drive the deferred tax balance.
@dataclass(frozen=True)
class StandardAdjustment:
    code: str
    description: str
    difference_type: DifferenceType
    typical_direction: AdjustmentDirection


STANDARD_ADJUSTMENTS: tuple[StandardAdjustment, ...] = (
    # --- Permanent differences ---
    StandardAdjustment(
        code="meals_50pct",
        description="Meals — 50% disallowance",
        difference_type=DifferenceType.PERMANENT,
        typical_direction=AdjustmentDirection.ADD,
    ),
    StandardAdjustment(
        code="fines_penalties",
        description="Fines and penalties",
        difference_type=DifferenceType.PERMANENT,
        typical_direction=AdjustmentDirection.ADD,
    ),
    StandardAdjustment(
        code="officer_life_insurance",
        description="Officer life insurance premiums",
        difference_type=DifferenceType.PERMANENT,
        typical_direction=AdjustmentDirection.ADD,
    ),
    StandardAdjustment(
        code="tax_exempt_interest",
        description="Tax-exempt interest income",
        difference_type=DifferenceType.PERMANENT,
        typical_direction=AdjustmentDirection.SUBTRACT,
    ),
    StandardAdjustment(
        code="political_contributions",
        description="Political contributions / lobbying",
        difference_type=DifferenceType.PERMANENT,
        typical_direction=AdjustmentDirection.ADD,
    ),
    StandardAdjustment(
        code="dividends_received_deduction",
        description="Dividends received deduction (corporations)",
        difference_type=DifferenceType.PERMANENT,
        typical_direction=AdjustmentDirection.SUBTRACT,
    ),
    # --- Temporary differences ---
    StandardAdjustment(
        code="depreciation_timing",
        description="Depreciation timing (book vs MACRS)",
        difference_type=DifferenceType.TEMPORARY,
        typical_direction=AdjustmentDirection.SUBTRACT,
    ),
    StandardAdjustment(
        code="bad_debt_reserve",
        description="Bad debt reserve (book allowance vs tax write-off)",
        difference_type=DifferenceType.TEMPORARY,
        typical_direction=AdjustmentDirection.ADD,
    ),
    StandardAdjustment(
        code="prepaid_expenses",
        description="Prepaid expenses timing",
        difference_type=DifferenceType.TEMPORARY,
        typical_direction=AdjustmentDirection.ADD,
    ),
    StandardAdjustment(
        code="accrued_vacation",
        description="Accrued vacation (not paid within 2.5 months)",
        difference_type=DifferenceType.TEMPORARY,
        typical_direction=AdjustmentDirection.ADD,
    ),
    StandardAdjustment(
        code="unicap",
        description="UNICAP adjustment (Section 263A)",
        difference_type=DifferenceType.TEMPORARY,
        typical_direction=AdjustmentDirection.ADD,
    ),
    StandardAdjustment(
        code="stock_compensation",
        description="Stock-based compensation timing",
        difference_type=DifferenceType.TEMPORARY,
        typical_direction=AdjustmentDirection.ADD,
    ),
    StandardAdjustment(
        code="warranty_reserve",
        description="Warranty reserve accrual",
        difference_type=DifferenceType.TEMPORARY,
        typical_direction=AdjustmentDirection.ADD,
    ),
)

STANDARD_ADJUSTMENTS_BY_CODE: dict[str, StandardAdjustment] = {s.code: s for s in STANDARD_ADJUSTMENTS}


class BookToTaxInputError(ValueError):
    """Raised for invalid book-to-tax inputs."""


# =============================================================================
# Inputs
# =============================================================================


@dataclass
class AdjustmentEntry:
    """A single book-to-tax adjustment."""

    label: str
    amount: Decimal  # Always positive; direction drives the sign
    difference_type: DifferenceType
    direction: AdjustmentDirection
    code: str | None = None  # Optional reference to STANDARD_ADJUSTMENTS

    def __post_init__(self) -> None:
        if isinstance(self.amount, (int, float)):
            self.amount = Decimal(str(self.amount))
        if self.amount < ZERO:
            raise BookToTaxInputError(f"Adjustment amount must be non-negative ({self.label}: {self.amount})")


@dataclass
class DeferredTaxRollforwardInput:
    """Prior-period deferred balances that the new activity rolls onto."""

    beginning_dta: Decimal = ZERO
    beginning_dtl: Decimal = ZERO


@dataclass
class BookToTaxConfig:
    tax_year: int
    book_pretax_income: Decimal
    total_assets: Decimal
    federal_tax_rate: Decimal  # e.g. Decimal("0.21")
    adjustments: list[AdjustmentEntry]
    rollforward: DeferredTaxRollforwardInput = field(default_factory=DeferredTaxRollforwardInput)
    state_tax_rate: Decimal = ZERO


# =============================================================================
# Outputs
# =============================================================================


@dataclass
class AdjustmentLine:
    label: str
    code: str | None
    difference_type: str
    direction: str
    amount: Decimal
    signed_amount: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "code": self.code,
            "difference_type": self.difference_type,
            "direction": self.direction,
            "amount": str(self.amount),
            "signed_amount": str(self.signed_amount),
        }


@dataclass
class ScheduleM1:
    net_income_per_books: Decimal
    federal_income_tax_per_books: Decimal
    permanent_additions: list[AdjustmentLine]
    temporary_additions: list[AdjustmentLine]
    permanent_subtractions: list[AdjustmentLine]
    temporary_subtractions: list[AdjustmentLine]
    taxable_income: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "net_income_per_books": str(self.net_income_per_books),
            "federal_income_tax_per_books": str(self.federal_income_tax_per_books),
            "permanent_additions": [a.to_dict() for a in self.permanent_additions],
            "temporary_additions": [a.to_dict() for a in self.temporary_additions],
            "permanent_subtractions": [a.to_dict() for a in self.permanent_subtractions],
            "temporary_subtractions": [a.to_dict() for a in self.temporary_subtractions],
            "taxable_income": str(self.taxable_income),
        }


@dataclass
class ScheduleM3Section:
    """M-3 splits each adjustment into permanent vs temporary columns."""

    label: str
    code: str | None
    permanent: Decimal
    temporary: Decimal

    @property
    def total(self) -> Decimal:
        return self.permanent + self.temporary

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "code": self.code,
            "permanent": str(self.permanent),
            "temporary": str(self.temporary),
            "total": str(self.total),
        }


@dataclass
class ScheduleM3:
    income_per_books: Decimal
    income_items: list[ScheduleM3Section]
    expense_items: list[ScheduleM3Section]
    taxable_income: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "income_per_books": str(self.income_per_books),
            "income_items": [s.to_dict() for s in self.income_items],
            "expense_items": [s.to_dict() for s in self.expense_items],
            "taxable_income": str(self.taxable_income),
        }


@dataclass
class DeferredTaxRollforward:
    beginning_dta: Decimal
    beginning_dtl: Decimal
    current_year_temporary_adjustments: Decimal  # Signed — adds to taxable income
    tax_rate: Decimal
    current_year_movement: Decimal  # Signed dollars hitting DTA/DTL
    ending_dta: Decimal
    ending_dtl: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "beginning_dta": str(self.beginning_dta),
            "beginning_dtl": str(self.beginning_dtl),
            "current_year_temporary_adjustments": str(self.current_year_temporary_adjustments),
            "tax_rate": str(self.tax_rate),
            "current_year_movement": str(self.current_year_movement),
            "ending_dta": str(self.ending_dta),
            "ending_dtl": str(self.ending_dtl),
        }


@dataclass
class TaxProvision:
    taxable_income: Decimal
    current_federal_tax: Decimal
    current_state_tax: Decimal
    deferred_tax_expense: Decimal  # Change in DTL less change in DTA
    total_tax_expense: Decimal
    effective_rate: Decimal  # total_tax_expense / book_pretax_income

    def to_dict(self) -> dict[str, Any]:
        return {
            "taxable_income": str(self.taxable_income),
            "current_federal_tax": str(self.current_federal_tax),
            "current_state_tax": str(self.current_state_tax),
            "deferred_tax_expense": str(self.deferred_tax_expense),
            "total_tax_expense": str(self.total_tax_expense),
            "effective_rate": str(self.effective_rate),
        }


@dataclass
class BookToTaxResult:
    tax_year: int
    entity_size: str  # "small" (M-1) or "large" (M-3)
    schedule_m1: ScheduleM1
    schedule_m3: ScheduleM3
    deferred_tax: DeferredTaxRollforward
    tax_provision: TaxProvision

    def to_dict(self) -> dict[str, Any]:
        return {
            "tax_year": self.tax_year,
            "entity_size": self.entity_size,
            "schedule_m1": self.schedule_m1.to_dict(),
            "schedule_m3": self.schedule_m3.to_dict(),
            "deferred_tax": self.deferred_tax.to_dict(),
            "tax_provision": self.tax_provision.to_dict(),
        }


# =============================================================================
# Helpers
# =============================================================================


def _quantise(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _signed(entry: AdjustmentEntry) -> Decimal:
    """Signed contribution of the adjustment toward taxable income."""
    if entry.direction == AdjustmentDirection.ADD:
        return entry.amount
    return -entry.amount


def _to_line(entry: AdjustmentEntry) -> AdjustmentLine:
    return AdjustmentLine(
        label=entry.label,
        code=entry.code,
        difference_type=entry.difference_type.value,
        direction=entry.direction.value,
        amount=_quantise(entry.amount),
        signed_amount=_quantise(_signed(entry)),
    )


# =============================================================================
# Public entry point
# =============================================================================


def calculate_book_to_tax(config: BookToTaxConfig) -> BookToTaxResult:
    """Produce a full Schedule M-1 / M-3 reconciliation plus deferred tax."""
    if config.tax_year < 2000 or config.tax_year > 2099:
        raise BookToTaxInputError(f"Tax year must be 4-digit year between 2000 and 2099 ({config.tax_year})")
    if config.federal_tax_rate < ZERO or config.federal_tax_rate > Decimal("1"):
        raise BookToTaxInputError(f"Federal tax rate must be between 0 and 1 ({config.federal_tax_rate})")

    # ── Schedule M-1 composition ──
    permanent_adds: list[AdjustmentLine] = []
    permanent_subs: list[AdjustmentLine] = []
    temporary_adds: list[AdjustmentLine] = []
    temporary_subs: list[AdjustmentLine] = []
    temporary_net = ZERO
    signed_total = ZERO

    for entry in config.adjustments:
        line = _to_line(entry)
        signed = _signed(entry)
        signed_total += signed
        if entry.difference_type == DifferenceType.PERMANENT:
            if entry.direction == AdjustmentDirection.ADD:
                permanent_adds.append(line)
            else:
                permanent_subs.append(line)
        else:
            temporary_net += signed
            if entry.direction == AdjustmentDirection.ADD:
                temporary_adds.append(line)
            else:
                temporary_subs.append(line)

    # Book federal tax per books is a book-only amount — we don't compute
    # it here, we include a zero line for the caller to override in the
    # PDF. Book income already reflects book tax expense.
    book_fit = ZERO

    taxable_income = config.book_pretax_income + signed_total

    schedule_m1 = ScheduleM1(
        net_income_per_books=_quantise(config.book_pretax_income),
        federal_income_tax_per_books=_quantise(book_fit),
        permanent_additions=permanent_adds,
        temporary_additions=temporary_adds,
        permanent_subtractions=permanent_subs,
        temporary_subtractions=temporary_subs,
        taxable_income=_quantise(taxable_income),
    )

    # ── Schedule M-3 composition ──
    # M-3 groups each adjustment into income or expense items and splits
    # permanent vs temporary across the two columns.
    income_items: list[ScheduleM3Section] = []
    expense_items: list[ScheduleM3Section] = []

    # Classify by direction: SUBTRACT items reduce taxable income, which
    # typically corresponds to income-side differences (tax-exempt
    # interest, dividends received deduction, depreciation where tax >
    # book). ADD items are typically expense-side (meals disallowance,
    # bad debt reserve, etc.).
    for entry in config.adjustments:
        section = ScheduleM3Section(
            label=entry.label,
            code=entry.code,
            permanent=(_quantise(_signed(entry)) if entry.difference_type == DifferenceType.PERMANENT else ZERO),
            temporary=(_quantise(_signed(entry)) if entry.difference_type == DifferenceType.TEMPORARY else ZERO),
        )
        if entry.direction == AdjustmentDirection.SUBTRACT:
            income_items.append(section)
        else:
            expense_items.append(section)

    schedule_m3 = ScheduleM3(
        income_per_books=_quantise(config.book_pretax_income),
        income_items=income_items,
        expense_items=expense_items,
        taxable_income=_quantise(taxable_income),
    )

    # ── Deferred tax rollforward ──
    # Net temporary adjustment × rate = current-year deferred movement.
    # A positive temporary adjustment (ADD to taxable income) means the
    # entity paid more tax this year; the expected reversal in future
    # years creates a deferred tax asset.
    rate = config.federal_tax_rate
    movement = _quantise(temporary_net * rate)

    # Beginning balances roll forward; net the movement against the DTA
    # side (positive temporary) or the DTL side (negative temporary).
    ending_dta = config.rollforward.beginning_dta
    ending_dtl = config.rollforward.beginning_dtl
    if temporary_net >= ZERO:
        ending_dta = _quantise(ending_dta + movement)
    else:
        # Negative movement reduces DTA first; any residual builds DTL.
        residual = movement.copy_abs()
        if ending_dta >= residual:
            ending_dta = _quantise(ending_dta - residual)
        else:
            residual -= ending_dta
            ending_dta = ZERO
            ending_dtl = _quantise(ending_dtl + residual)

    deferred = DeferredTaxRollforward(
        beginning_dta=_quantise(config.rollforward.beginning_dta),
        beginning_dtl=_quantise(config.rollforward.beginning_dtl),
        current_year_temporary_adjustments=_quantise(temporary_net),
        tax_rate=rate,
        current_year_movement=movement,
        ending_dta=ending_dta,
        ending_dtl=ending_dtl,
    )

    # ── Tax provision ──
    current_fed = _quantise(max(taxable_income, ZERO) * rate)
    current_state = _quantise(max(taxable_income, ZERO) * config.state_tax_rate)
    # Deferred tax expense = change in DTL - change in DTA.
    change_dtl = ending_dtl - config.rollforward.beginning_dtl
    change_dta = ending_dta - config.rollforward.beginning_dta
    deferred_expense = _quantise(change_dtl - change_dta)
    total_tax = _quantise(current_fed + current_state + deferred_expense)

    if config.book_pretax_income != ZERO:
        effective = (total_tax / config.book_pretax_income).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    else:
        effective = ZERO

    provision = TaxProvision(
        taxable_income=_quantise(taxable_income),
        current_federal_tax=current_fed,
        current_state_tax=current_state,
        deferred_tax_expense=deferred_expense,
        total_tax_expense=total_tax,
        effective_rate=effective,
    )

    entity_size = "large" if config.total_assets >= M3_THRESHOLD_TOTAL_ASSETS else "small"

    return BookToTaxResult(
        tax_year=config.tax_year,
        entity_size=entity_size,
        schedule_m1=schedule_m1,
        schedule_m3=schedule_m3,
        deferred_tax=deferred,
        tax_provision=provision,
    )
