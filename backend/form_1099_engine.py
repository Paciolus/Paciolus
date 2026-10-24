"""
Form 1099 Preparation Engine (Sprint 634).

Aggregates AP payments by vendor across a tax year, applies the common
1099 reporting thresholds (1099-NEC, 1099-MISC, 1099-INT), and produces
a candidate listing ready for IRS filing. Also emits a data-quality
report flagging vendors that are missing TINs, addresses, or have
inconsistent records.

Zero-storage: form-input only. The engine is deliberately conservative —
it flags candidates for practitioner review rather than asserting a
filing obligation. 1099 rules are IRS-defined and outside platform
judgment.

Reporting thresholds are keyed by tax year (Sprint 837); see
``THRESHOLDS_BY_TABLE_YEAR`` and ``thresholds_for_year()``:
  * Tax years through 2025: 1099-NEC $600; 1099-MISC boxes 1/3/6/10 $600,
    box 2 (royalties) $10; 1099-INT $10.
  * Tax year 2026: 1099-NEC and 1099-MISC boxes 1/3/6 $2,000 (One Big
    Beautiful Bill Act, 2025, for payments made after December 31, 2025);
    royalties and 1099-INT stay $10; box 10 attorney gross proceeds stays
    $600 pending confirmation.
  * Tax years 2027+: the inflation-indexed figure is not tabulated; the 2026
    figures are applied with a notice (an indexed threshold can only be
    at least $2,000, so applying $2,000 cannot miss a required filing).
  * The result carries the thresholds applied and their basis, and lists
    payees at or above $600 but below the year's threshold separately.
  * Corporations are generally exempt, except for medical/legal payments
  * Credit-card / third-party network payments are reportable by the
    payment processor on 1099-K, not by the payer — we exclude those.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

from shared.parsing_helpers import parse_date

CENT = Decimal("0.01")
ZERO = Decimal("0")


class FormType(str, Enum):
    NEC = "1099-NEC"
    MISC = "1099-MISC"
    INT = "1099-INT"


class PaymentCategory(str, Enum):
    NONEMPLOYEE_COMP = "nonemployee_comp"  # → 1099-NEC box 1
    RENTS = "rents"  # → 1099-MISC box 1
    ROYALTIES = "royalties"  # → 1099-MISC box 2
    MEDICAL = "medical"  # → 1099-MISC box 6
    LEGAL = "legal"  # Gross proceeds paid to an attorney → 1099-MISC box 10
    # Sprint 826 (F4): fees paid to an attorney for legal services are
    # nonemployee compensation (1099-NEC box 1), reportable even when the firm
    # is a corporation. With only "legal" available they landed on MISC box 10,
    # which is for gross proceeds, and "nonemployee_comp" excluded corporate
    # law firms entirely.
    ATTORNEY_FEES = "attorney_fees"  # → 1099-NEC box 1
    INTEREST = "interest"  # → 1099-INT box 1
    OTHER = "other"


class EntityType(str, Enum):
    INDIVIDUAL = "individual"
    PARTNERSHIP = "partnership"
    LLC = "llc"
    CORPORATION = "corporation"
    S_CORPORATION = "s_corporation"
    GOVERNMENT = "government"
    TAX_EXEMPT = "tax_exempt"
    UNKNOWN = "unknown"


class PaymentMethod(str, Enum):
    CHECK = "check"
    ACH = "ach"
    WIRE = "wire"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    UNKNOWN = "unknown"


# Payment methods excluded from payer reporting (reported by processor on 1099-K).
PROCESSOR_REPORTED_METHODS: frozenset[PaymentMethod] = frozenset({PaymentMethod.CREDIT_CARD, PaymentMethod.PAYPAL})

# Corporation-exempt categories — payments to corporations generally do
# not require 1099 filing except in these two categories.
NON_EXEMPT_CORPORATION_CATEGORIES: frozenset[PaymentCategory] = frozenset(
    {PaymentCategory.MEDICAL, PaymentCategory.LEGAL, PaymentCategory.ATTORNEY_FEES}
)


CATEGORY_TO_FORM_BOX: dict[PaymentCategory, tuple[FormType, int]] = {
    PaymentCategory.NONEMPLOYEE_COMP: (FormType.NEC, 1),
    PaymentCategory.ATTORNEY_FEES: (FormType.NEC, 1),
    PaymentCategory.RENTS: (FormType.MISC, 1),
    PaymentCategory.ROYALTIES: (FormType.MISC, 2),
    PaymentCategory.MEDICAL: (FormType.MISC, 6),
    PaymentCategory.LEGAL: (FormType.MISC, 10),
    PaymentCategory.INTEREST: (FormType.INT, 1),
    # Sprint 826 (F7): "other income" is 1099-MISC box 3. Unmapped, it was
    # reported in a box 0 that does not exist.
    PaymentCategory.OTHER: (FormType.MISC, 3),
}

# Filing thresholds in dollars for tax years through 2025. Each form type
# aggregates per-vendor dollars across all boxes within that form type.
# Sprint 837: kept as the pre-2026 figures; the engine resolves the run's
# thresholds through ``thresholds_for_year()``.
FORM_THRESHOLDS: dict[FormType, Decimal] = {
    FormType.NEC: Decimal("600"),
    FormType.MISC: Decimal("600"),
    FormType.INT: Decimal("10"),
}

# Sprint 826 (F1, F6): 1099-MISC thresholds apply per box, not to the form's
# combined total — rents $400 plus medical $300 is not a $700 filing, and a
# $450 royalty *is* one, because royalties (box 2) report at $10. A MISC is
# due when any box reaches its own threshold. Figures pending the Sprint 793b
# practitioner confirmation along with the rest of the statutory tables.
MISC_BOX_THRESHOLDS: dict[int, Decimal] = {
    1: Decimal("600"),  # rents
    2: Decimal("10"),  # royalties
    3: Decimal("600"),  # other income
    6: Decimal("600"),  # medical and health care payments
    10: Decimal("600"),  # gross proceeds paid to an attorney
}

# The pre-2026 general threshold. A payee at or above it but below the run
# year's threshold is listed for review rather than silently dropped.
LEGACY_GENERAL_THRESHOLD = Decimal("600")


# =============================================================================
# Thresholds keyed by tax year (Sprint 837)
# =============================================================================
#
# This engine applied $600 to every tax year and its docstring said 2026 was
# unchanged. Multiple secondary sources (CPA Practice Advisor, Avalara, Patriot
# Software, TaxBandits) report that the One Big Beautiful Bill Act (2025) raised
# the 1099-NEC and 1099-MISC reporting threshold from $600 to $2,000 for
# payments made after December 31, 2025, indexed for inflation from 2027.
# Royalties ($10, IRC §6050N) and interest ($10, IRC §6049) are not affected.
# Attorney gross proceeds (1099-MISC box 10) are reported under IRC §6045(f);
# whether that threshold changed is uncertain, so $600 is kept: the
# conservative choice, because a lower threshold flags more candidates.
#
# ---------------------------------------------------------------------------
# Sprint 793b practitioner confirmation list: every threshold below.
# Paciolus is not an authority; these restate the authorities' figures, and each
# needs a practitioner's sign-off against the IRS Instructions for Forms
# 1099-MISC, 1099-NEC and 1099-INT for the year before 793b closes.
#
#   Tax years through 2025 (table year 2025)
#   - 1099-NEC box 1 $600 ................ IRC §6041A(a)
#   - 1099-MISC box 1 rents $600 ......... IRC §6041(a)
#   - 1099-MISC box 2 royalties $10 ...... IRC §6050N
#   - 1099-MISC box 3 other income $600 .. IRC §6041(a)
#   - 1099-MISC box 6 medical $600 ....... IRC §6041(a)
#   - 1099-MISC box 10 attorney gross
#     proceeds $600 ...................... IRC §6045(f)
#   - 1099-INT box 1 $10 ................. IRC §6049
#
#   Tax year 2026 (table year 2026; also applied to 2027+ with a notice)
#   - 1099-NEC box 1 $2,000 .............. IRC §6041A as amended by the One Big
#                                          Beautiful Bill Act (2025). Secondary
#                                          sources only; not yet checked against
#                                          the statute text or IRS instructions
#   - 1099-MISC boxes 1, 3, 6 $2,000 ..... IRC §6041 as amended by the One Big
#                                          Beautiful Bill Act (2025), as above
#   - 1099-MISC box 2 royalties $10 ...... IRC §6050N (reported unchanged)
#   - 1099-MISC box 10 $600 [CONFIRM] .... IRC §6045(f). Whether OBBBA changed
#                                          it is uncertain; $600 kept as the
#                                          conservative figure
#   - 1099-INT box 1 $10 ................. IRC §6049 (reported unchanged)
#
#   Tax years 2027+: inflation-indexed figure not tabulated. Add a row when the
#   IRS publishes it; until then the 2026 row is applied with a notice.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ThresholdItem:
    """One reporting threshold with the authority it restates."""

    form_type: FormType
    box: int
    description: str
    amount: Decimal
    basis: str
    needs_confirmation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "form_type": self.form_type.value,
            "box": self.box,
            "description": self.description,
            "amount": str(self.amount.quantize(CENT)),
            "basis": self.basis,
            "needs_confirmation": self.needs_confirmation,
        }


_PRE_2026_ITEMS: tuple[ThresholdItem, ...] = (
    ThresholdItem(FormType.NEC, 1, "Nonemployee compensation", Decimal("600"), "IRC §6041A(a)"),
    ThresholdItem(FormType.MISC, 1, "Rents", Decimal("600"), "IRC §6041(a)"),
    ThresholdItem(FormType.MISC, 2, "Royalties", Decimal("10"), "IRC §6050N"),
    ThresholdItem(FormType.MISC, 3, "Other income", Decimal("600"), "IRC §6041(a)"),
    ThresholdItem(FormType.MISC, 6, "Medical and health care payments", Decimal("600"), "IRC §6041(a)"),
    ThresholdItem(FormType.MISC, 10, "Gross proceeds paid to an attorney", Decimal("600"), "IRC §6045(f)"),
    ThresholdItem(FormType.INT, 1, "Interest income", Decimal("10"), "IRC §6049"),
)

_OBBBA_BASIS = (
    "One Big Beautiful Bill Act (2025): $2,000 for payments made after December 31, 2025, "
    "as reported by secondary sources"
)

_2026_ITEMS: tuple[ThresholdItem, ...] = (
    ThresholdItem(FormType.NEC, 1, "Nonemployee compensation", Decimal("2000"), f"IRC §6041A; {_OBBBA_BASIS}"),
    ThresholdItem(FormType.MISC, 1, "Rents", Decimal("2000"), f"IRC §6041; {_OBBBA_BASIS}"),
    ThresholdItem(FormType.MISC, 2, "Royalties", Decimal("10"), "IRC §6050N (reported unchanged)"),
    ThresholdItem(FormType.MISC, 3, "Other income", Decimal("2000"), f"IRC §6041; {_OBBBA_BASIS}"),
    ThresholdItem(FormType.MISC, 6, "Medical and health care payments", Decimal("2000"), f"IRC §6041; {_OBBBA_BASIS}"),
    ThresholdItem(
        FormType.MISC,
        10,
        "Gross proceeds paid to an attorney",
        Decimal("600"),
        "IRC §6045(f). Whether the 2025 change applies to this box is not confirmed; "
        "$600 is applied as the conservative figure (a lower threshold flags more candidates)",
        needs_confirmation=True,
    ),
    ThresholdItem(FormType.INT, 1, "Interest income", Decimal("10"), "IRC §6049 (reported unchanged)"),
)

# Keyed by table year. A tax year uses the latest table year not after it.
THRESHOLDS_BY_TABLE_YEAR: dict[int, tuple[ThresholdItem, ...]] = {
    2025: _PRE_2026_ITEMS,
    2026: _2026_ITEMS,
}
LATEST_TABULATED_YEAR = max(THRESHOLDS_BY_TABLE_YEAR)


@dataclass(frozen=True)
class ThresholdSchedule:
    """The thresholds applied to one run, with their provenance."""

    tax_year: int
    table_year: int
    items: tuple[ThresholdItem, ...]
    notices: tuple[str, ...]

    def box_threshold(self, form_type: FormType, box: int) -> Decimal:
        for item in self.items:
            if item.form_type == form_type and item.box == box:
                return item.amount
        # Unmapped MISC box: the general (other income) figure.
        return self.form_threshold(FormType.MISC)

    def form_threshold(self, form_type: FormType) -> Decimal:
        """Threshold for NEC / INT, or the general 1099-MISC figure (box 3)."""
        box = 3 if form_type == FormType.MISC else 1
        for item in self.items:
            if item.form_type == form_type and item.box == box:
                return item.amount
        raise KeyError(f"no threshold tabulated for {form_type.value} box {box}")

    def confirm_against(self) -> str:
        return f"Confirm against the IRS Instructions for Forms 1099-MISC, 1099-NEC and 1099-INT for {self.tax_year}."

    def to_dict(self) -> dict[str, Any]:
        return {
            "tax_year": self.tax_year,
            "figures_from_tax_year": self.table_year,
            "items": [i.to_dict() for i in self.items],
            "confirm_against": self.confirm_against(),
        }


def thresholds_for_year(tax_year: int) -> ThresholdSchedule:
    """Resolve the reporting thresholds for ``tax_year``.

    Years up to 2025 use the 2025 table (the $600 rules applied for decades).
    Years after the latest table use the latest table with a notice: for 2027+
    that is the 2026 $2,000 figure, which an inflation-indexed threshold can
    only equal or exceed, so applying it cannot miss a required filing.
    """
    eligible = [y for y in THRESHOLDS_BY_TABLE_YEAR if y <= tax_year]
    table_year = max(eligible) if eligible else min(THRESHOLDS_BY_TABLE_YEAR)
    notices: list[str] = []
    if tax_year == 2026:
        notices.append(
            "For payments made after December 31, 2025, the 1099-NEC and 1099-MISC (rents, other income, "
            "medical) reporting threshold is $2,000 under the One Big Beautiful Bill Act (2025), as reported "
            "by secondary sources. Royalties and 1099-INT remain $10. Attorney gross proceeds (1099-MISC "
            "box 10) are tested at $600 pending confirmation. Confirm against the IRS Instructions for "
            "Forms 1099-MISC and 1099-NEC for 2026."
        )
    if tax_year > LATEST_TABULATED_YEAR:
        notices.append(
            f"The inflation-adjusted 1099-NEC / 1099-MISC threshold for {tax_year} is not in Paciolus. "
            f"The {LATEST_TABULATED_YEAR} figures are applied ($2,000 for 1099-NEC and 1099-MISC boxes 1, 3 "
            "and 6). An indexed threshold can only be equal or higher, so no required filing is missed, but "
            f"some candidates may fall below the actual {tax_year} threshold. Confirm the {tax_year} figure "
            f"against the IRS Instructions for Forms 1099-MISC and 1099-NEC for {tax_year}."
        )
    return ThresholdSchedule(
        tax_year=tax_year,
        table_year=table_year,
        items=THRESHOLDS_BY_TABLE_YEAR[table_year],
        notices=tuple(notices),
    )


class Form1099InputError(ValueError):
    """Raised for invalid 1099 preparation inputs."""


# =============================================================================
# Input dataclasses
# =============================================================================


@dataclass
class VendorRecord:
    vendor_id: str
    vendor_name: str
    tin: str | None = None  # EIN or SSN, unformatted or formatted
    entity_type: EntityType = EntityType.UNKNOWN
    address_line_1: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None


@dataclass
class VendorPayment:
    vendor_id: str
    amount: Decimal
    payment_category: PaymentCategory = PaymentCategory.NONEMPLOYEE_COMP
    payment_method: PaymentMethod = PaymentMethod.CHECK
    payment_date: str | None = None
    invoice_number: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.amount, (int, float)):
            self.amount = Decimal(str(self.amount))


@dataclass
class Form1099Config:
    tax_year: int
    vendors: list[VendorRecord]
    payments: list[VendorPayment]


# =============================================================================
# Output dataclasses
# =============================================================================


@dataclass
class VendorBoxAmount:
    category: str
    form_type: str
    box: int
    amount: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "form_type": self.form_type,
            "box": self.box,
            "amount": str(self.amount),
        }


@dataclass
class VendorDataQuality:
    vendor_id: str
    vendor_name: str
    missing_tin: bool
    invalid_tin_format: bool
    missing_address: bool
    unknown_entity_type: bool
    notes: list[str] = field(default_factory=list)

    @property
    def has_issue(self) -> bool:
        return self.missing_tin or self.invalid_tin_format or self.missing_address or self.unknown_entity_type

    def to_dict(self) -> dict[str, Any]:
        return {
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "missing_tin": self.missing_tin,
            "invalid_tin_format": self.invalid_tin_format,
            "missing_address": self.missing_address,
            "unknown_entity_type": self.unknown_entity_type,
            "has_issue": self.has_issue,
            "notes": list(self.notes),
        }


@dataclass
class Form1099Candidate:
    vendor_id: str
    vendor_name: str
    form_type: str
    total_reportable: Decimal
    box_amounts: list[VendorBoxAmount]
    payment_count: int
    excluded_amount: Decimal  # Processor-reported or below-threshold dollars
    flagged_for_review: bool
    review_reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "form_type": self.form_type,
            "total_reportable": str(self.total_reportable),
            "box_amounts": [b.to_dict() for b in self.box_amounts],
            "payment_count": self.payment_count,
            "excluded_amount": str(self.excluded_amount),
            "flagged_for_review": self.flagged_for_review,
            "review_reasons": list(self.review_reasons),
        }


@dataclass
class W9CollectionRow:
    """A vendor that needs a W-9 on file before filing."""

    vendor_id: str
    vendor_name: str
    reason: str  # e.g. "missing TIN", "invalid TIN format"

    def to_dict(self) -> dict[str, Any]:
        return {
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "reason": self.reason,
        }


@dataclass
class BelowThresholdPayee:
    """Sprint 837: a payee at or above $600 but below the year's threshold.

    Not a filing candidate. Listed so that a change in the threshold (2026:
    $600 to $2,000) never removes a payee from view silently.
    """

    vendor_id: str
    vendor_name: str
    form_type: str
    total: Decimal
    box_amounts: list[VendorBoxAmount]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "form_type": self.form_type,
            "total": str(self.total),
            "box_amounts": [b.to_dict() for b in self.box_amounts],
            "reason": self.reason,
        }


@dataclass
class Form1099Result:
    tax_year: int
    candidates: list[Form1099Candidate]
    data_quality: list[VendorDataQuality]
    w9_collection_list: list[W9CollectionRow]
    summary: dict[str, Any]
    # Sprint 837: transparency about the thresholds applied.
    thresholds: ThresholdSchedule | None = None
    below_threshold_payees: list[BelowThresholdPayee] = field(default_factory=list)

    @property
    def notices(self) -> list[str]:
        return list(self.thresholds.notices) if self.thresholds else []

    def to_dict(self) -> dict[str, Any]:
        return {
            "tax_year": self.tax_year,
            "candidates": [c.to_dict() for c in self.candidates],
            "data_quality": [dq.to_dict() for dq in self.data_quality],
            "w9_collection_list": [w.to_dict() for w in self.w9_collection_list],
            "summary": self.summary,
            "thresholds": self.thresholds.to_dict() if self.thresholds else None,
            "notices": self.notices,
            "below_threshold_payees": [b.to_dict() for b in self.below_threshold_payees],
        }


# =============================================================================
# Helpers
# =============================================================================


def _quantise(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _digits(value: str | None) -> str:
    if not value:
        return ""
    return "".join(ch for ch in value if ch.isdigit())


def _is_valid_tin_format(tin: str | None) -> bool:
    """EIN (9 digits, XX-XXXXXXX) or SSN (9 digits, XXX-XX-XXXX)."""
    digits = _digits(tin)
    return len(digits) == 9


def _resolve_form_type(category: PaymentCategory) -> FormType:
    mapping = CATEGORY_TO_FORM_BOX.get(category)
    if mapping is None:
        return FormType.MISC
    return mapping[0]


def _resolve_box(category: PaymentCategory) -> int:
    mapping = CATEGORY_TO_FORM_BOX.get(category)
    if mapping is None:
        return 0
    return mapping[1]


def _vendor_is_corporation(entity: EntityType) -> bool:
    return entity in (EntityType.CORPORATION, EntityType.S_CORPORATION)


# Sprint 826 (F8): payments to tax-exempt organisations and to governments are
# listed exceptions to 1099-NEC/MISC reporting — without the medical and legal
# carve-back that applies to corporations. They were reported as NEC.
EXEMPT_PAYEE_ENTITIES: frozenset[EntityType] = frozenset({EntityType.GOVERNMENT, EntityType.TAX_EXEMPT})


# =============================================================================
# Core engine
# =============================================================================


def _assess_vendor(vendor: VendorRecord) -> VendorDataQuality:
    notes: list[str] = []
    missing_tin = not (vendor.tin and vendor.tin.strip())
    invalid_format = False
    if not missing_tin:
        invalid_format = not _is_valid_tin_format(vendor.tin)
        if invalid_format:
            notes.append("TIN not in 9-digit EIN/SSN format")
    else:
        notes.append("TIN missing — request W-9")

    missing_address = not (vendor.address_line_1 and vendor.state and vendor.postal_code)
    if missing_address:
        notes.append("Mailing address incomplete — required for 1099 copy B")

    unknown_entity = vendor.entity_type == EntityType.UNKNOWN
    if unknown_entity:
        notes.append("Entity type unknown — cannot apply corporation exemption")

    return VendorDataQuality(
        vendor_id=vendor.vendor_id,
        vendor_name=vendor.vendor_name,
        missing_tin=missing_tin,
        invalid_tin_format=invalid_format,
        missing_address=missing_address,
        unknown_entity_type=unknown_entity,
        notes=notes,
    )


def prepare_1099s(config: Form1099Config) -> Form1099Result:
    """Build 1099 filing candidates from vendor + payment inputs."""
    if config.tax_year < 2000 or config.tax_year > 2099:
        raise Form1099InputError(f"Tax year must be a reasonable 4-digit year (got {config.tax_year})")

    schedule = thresholds_for_year(config.tax_year)
    vendors_by_id: dict[str, VendorRecord] = {v.vendor_id: v for v in config.vendors}

    # Sprint 826 (F3): the filing threshold applies per payee, and a payee is
    # a TIN. Two vendor records sharing a TIN with $400 each are one $800
    # payee; keyed by vendor ID they were two sub-threshold vendors and no form.
    def _payee_key(vendor: VendorRecord) -> str:
        digits = _digits(vendor.tin)
        return f"tin:{digits}" if len(digits) == 9 else f"vendor:{vendor.vendor_id}"

    payee_vendor_ids: dict[str, list[str]] = defaultdict(list)
    for vendor in config.vendors:
        ids = payee_vendor_ids[_payee_key(vendor)]
        if vendor.vendor_id not in ids:
            ids.append(vendor.vendor_id)

    # Bucket: (payee_key, form_type) -> list[VendorPayment]
    grouped: dict[tuple[str, FormType], list[VendorPayment]] = defaultdict(list)
    excluded_dollars: dict[tuple[str, FormType], Decimal] = defaultdict(lambda: ZERO)
    payments_without_vendor: list[str] = []
    payments_outside_tax_year = 0

    for payment in config.payments:
        vendor = vendors_by_id.get(payment.vendor_id)
        if vendor is None:
            payments_without_vendor.append(payment.vendor_id)
            continue

        # Sprint 826 (F2): a dated payment counts toward the year it was paid.
        # payment_date was accepted and never read, so December and January
        # payments either side of the year all landed in it. Undated payments
        # are kept, as before — the practitioner supplied them for this year.
        paid_on = parse_date(payment.payment_date) if payment.payment_date else None
        if paid_on is not None and paid_on.year != config.tax_year:
            payments_outside_tax_year += 1
            continue

        payee = _payee_key(vendor)

        form_type = _resolve_form_type(payment.payment_category)

        # Processor-reported methods excluded from payer filing.
        if payment.payment_method in PROCESSOR_REPORTED_METHODS:
            excluded_dollars[(payee, form_type)] += payment.amount
            continue

        # Exempt payees: governments and tax-exempt organisations.
        if vendor.entity_type in EXEMPT_PAYEE_ENTITIES:
            excluded_dollars[(payee, form_type)] += payment.amount
            continue

        # Corporation exemption unless medical/legal.
        if _vendor_is_corporation(vendor.entity_type) and (
            payment.payment_category not in NON_EXEMPT_CORPORATION_CATEGORIES
        ):
            excluded_dollars[(payee, form_type)] += payment.amount
            continue

        grouped[(payee, form_type)].append(payment)

    candidates: list[Form1099Candidate] = []
    below_threshold: list[BelowThresholdPayee] = []
    summary_totals: dict[str, Decimal] = defaultdict(lambda: ZERO)
    summary_counts: dict[str, int] = defaultdict(int)

    for (payee, form_type), payments in grouped.items():
        payee_ids = [vid for vid in payee_vendor_ids[payee] if any(p.vendor_id == vid for p in payments)]
        vendor = vendors_by_id[payee_ids[0]]
        vendor_id = vendor.vendor_id
        # Sum by payment category.
        by_category: dict[PaymentCategory, Decimal] = defaultdict(lambda: ZERO)
        for p in payments:
            by_category[p.payment_category] += p.amount
        total = sum(by_category.values(), ZERO)

        box_amounts = [
            VendorBoxAmount(
                category=cat.value,
                form_type=form_type.value,
                box=_resolve_box(cat),
                amount=_quantise(amount),
            )
            for cat, amount in sorted(by_category.items(), key=lambda pair: pair[0].value)
        ]

        # Sprint 837: thresholds come from the run's tax year, not a fixed table.
        if form_type == FormType.MISC:
            by_box: dict[int, Decimal] = defaultdict(lambda: ZERO)
            for category, amount in by_category.items():
                by_box[_resolve_box(category)] += amount
            meets_threshold = any(
                amount >= schedule.box_threshold(FormType.MISC, box) for box, amount in by_box.items()
            )
            # Would have met the pre-2026 $600 figure in some box whose threshold is now higher.
            near_boxes = [
                (box, amount)
                for box, amount in sorted(by_box.items())
                if LEGACY_GENERAL_THRESHOLD <= amount < schedule.box_threshold(FormType.MISC, box)
            ]
            below_reason = "; ".join(
                f"box {box} ${amount:,.2f} is below the {config.tax_year} threshold of "
                f"${schedule.box_threshold(FormType.MISC, box):,.2f}"
                for box, amount in near_boxes
            )
        else:
            threshold = schedule.form_threshold(form_type)
            meets_threshold = total >= threshold
            near_boxes = [(1, total)] if LEGACY_GENERAL_THRESHOLD <= total < threshold else []
            below_reason = (
                f"${total:,.2f} is below the {config.tax_year} {form_type.value} threshold of ${threshold:,.2f}"
            )
        if not meets_threshold:
            # Below threshold: not a candidate, so the candidate list stays
            # focused on filings the practitioner needs to make. A payee that
            # reaches $600 is listed separately for review (Sprint 837).
            excluded_dollars[(payee, form_type)] += total
            if near_boxes:
                below_threshold.append(
                    BelowThresholdPayee(
                        vendor_id=vendor.vendor_id,
                        vendor_name=vendor.vendor_name,
                        form_type=form_type.value,
                        total=_quantise(total),
                        box_amounts=box_amounts,
                        reason=(
                            f"Below the {config.tax_year} reporting threshold — not required, shown for review "
                            f"({below_reason})."
                        ),
                    )
                )
            continue

        dq = _assess_vendor(vendor)
        review_reasons: list[str] = []
        if len(payee_ids) > 1:
            review_reasons.append("Aggregated by TIN across vendor records " + ", ".join(payee_ids))
        if dq.missing_tin:
            review_reasons.append("TIN missing — W-9 required")
        if dq.invalid_tin_format:
            review_reasons.append("TIN format invalid")
        if dq.missing_address:
            review_reasons.append("Address incomplete")
        if dq.unknown_entity_type:
            review_reasons.append("Entity type unknown")

        candidates.append(
            Form1099Candidate(
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                form_type=form_type.value,
                total_reportable=_quantise(total),
                box_amounts=box_amounts,
                payment_count=len(payments),
                excluded_amount=_quantise(excluded_dollars[(payee, form_type)]),
                flagged_for_review=bool(review_reasons),
                review_reasons=review_reasons,
            )
        )
        summary_totals[form_type.value] += total
        summary_counts[form_type.value] += 1

    # Deduplicate data-quality assessments across vendors (one per vendor).
    assessed: dict[str, VendorDataQuality] = {}
    for vendor in config.vendors:
        assessed[vendor.vendor_id] = _assess_vendor(vendor)

    # W-9 collection list — vendors with candidates AND missing/invalid TIN.
    vendors_with_candidates: set[str] = {c.vendor_id for c in candidates}
    w9_list: list[W9CollectionRow] = []
    for vendor_id in vendors_with_candidates:
        dq = assessed.get(vendor_id)
        if dq is None:
            continue
        if dq.missing_tin:
            w9_list.append(
                W9CollectionRow(
                    vendor_id=dq.vendor_id,
                    vendor_name=dq.vendor_name,
                    reason="TIN missing",
                )
            )
        elif dq.invalid_tin_format:
            w9_list.append(
                W9CollectionRow(
                    vendor_id=dq.vendor_id,
                    vendor_name=dq.vendor_name,
                    reason="TIN format invalid",
                )
            )

    summary = {
        "total_candidates": len(candidates),
        "totals_by_form": {k: str(_quantise(v)) for k, v in summary_totals.items()},
        "counts_by_form": dict(summary_counts),
        "w9_collection_count": len(w9_list),
        "data_quality_issue_count": sum(1 for dq in assessed.values() if dq.has_issue),
        "payments_without_vendor": len(payments_without_vendor),
        "payments_outside_tax_year": payments_outside_tax_year,
        "below_threshold_count": len(below_threshold),
    }

    # Deterministic output ordering — form type then vendor name.
    candidates.sort(key=lambda c: (c.form_type, c.vendor_name.lower()))

    return Form1099Result(
        tax_year=config.tax_year,
        candidates=candidates,
        data_quality=sorted(assessed.values(), key=lambda dq: dq.vendor_name.lower()),
        w9_collection_list=sorted(w9_list, key=lambda w: w.vendor_name.lower()),
        summary=summary,
        thresholds=schedule,
        below_threshold_payees=sorted(below_threshold, key=lambda b: (b.form_type, b.vendor_name.lower())),
    )
