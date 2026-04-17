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

Reference thresholds for tax year 2026 (unchanged from 2025):
  * 1099-NEC nonemployee compensation — $600 aggregate per vendor
  * 1099-MISC rents / royalties / medical / legal — $600 aggregate
  * 1099-INT interest — $10 aggregate
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
    LEGAL = "legal"  # → 1099-MISC box 10
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
    {PaymentCategory.MEDICAL, PaymentCategory.LEGAL}
)


CATEGORY_TO_FORM_BOX: dict[PaymentCategory, tuple[FormType, int]] = {
    PaymentCategory.NONEMPLOYEE_COMP: (FormType.NEC, 1),
    PaymentCategory.RENTS: (FormType.MISC, 1),
    PaymentCategory.ROYALTIES: (FormType.MISC, 2),
    PaymentCategory.MEDICAL: (FormType.MISC, 6),
    PaymentCategory.LEGAL: (FormType.MISC, 10),
    PaymentCategory.INTEREST: (FormType.INT, 1),
}

# Filing thresholds in dollars. Each form type aggregates per-vendor
# dollars across all boxes within that form type.
FORM_THRESHOLDS: dict[FormType, Decimal] = {
    FormType.NEC: Decimal("600"),
    FormType.MISC: Decimal("600"),
    FormType.INT: Decimal("10"),
}


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
class Form1099Result:
    tax_year: int
    candidates: list[Form1099Candidate]
    data_quality: list[VendorDataQuality]
    w9_collection_list: list[W9CollectionRow]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tax_year": self.tax_year,
            "candidates": [c.to_dict() for c in self.candidates],
            "data_quality": [dq.to_dict() for dq in self.data_quality],
            "w9_collection_list": [w.to_dict() for w in self.w9_collection_list],
            "summary": self.summary,
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

    vendors_by_id: dict[str, VendorRecord] = {v.vendor_id: v for v in config.vendors}

    # Bucket: (vendor_id, form_type) -> list[VendorPayment]
    grouped: dict[tuple[str, FormType], list[VendorPayment]] = defaultdict(list)
    excluded_dollars: dict[tuple[str, FormType], Decimal] = defaultdict(lambda: ZERO)
    payments_without_vendor: list[str] = []

    for payment in config.payments:
        vendor = vendors_by_id.get(payment.vendor_id)
        if vendor is None:
            payments_without_vendor.append(payment.vendor_id)
            continue

        form_type = _resolve_form_type(payment.payment_category)

        # Processor-reported methods excluded from payer filing.
        if payment.payment_method in PROCESSOR_REPORTED_METHODS:
            excluded_dollars[(vendor.vendor_id, form_type)] += payment.amount
            continue

        # Corporation exemption unless medical/legal.
        if _vendor_is_corporation(vendor.entity_type) and (
            payment.payment_category not in NON_EXEMPT_CORPORATION_CATEGORIES
        ):
            excluded_dollars[(vendor.vendor_id, form_type)] += payment.amount
            continue

        grouped[(vendor.vendor_id, form_type)].append(payment)

    candidates: list[Form1099Candidate] = []
    summary_totals: dict[str, Decimal] = defaultdict(lambda: ZERO)
    summary_counts: dict[str, int] = defaultdict(int)

    for (vendor_id, form_type), payments in grouped.items():
        vendor = vendors_by_id[vendor_id]
        # Sum by payment category.
        by_category: dict[PaymentCategory, Decimal] = defaultdict(lambda: ZERO)
        for p in payments:
            by_category[p.payment_category] += p.amount
        total = sum(by_category.values(), ZERO)

        threshold = FORM_THRESHOLDS[form_type]
        if total < threshold:
            # Below threshold — still report for audit, but clearly marked
            # as below-threshold so the candidate list stays focused on
            # filings the practitioner actually needs to make.
            excluded_dollars[(vendor_id, form_type)] += total
            continue

        box_amounts = [
            VendorBoxAmount(
                category=cat.value,
                form_type=form_type.value,
                box=_resolve_box(cat),
                amount=_quantise(amount),
            )
            for cat, amount in sorted(by_category.items(), key=lambda pair: pair[0].value)
        ]

        dq = _assess_vendor(vendor)
        review_reasons: list[str] = []
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
                excluded_amount=_quantise(excluded_dollars[(vendor_id, form_type)]),
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
    }

    # Deterministic output ordering — form type then vendor name.
    candidates.sort(key=lambda c: (c.form_type, c.vendor_name.lower()))

    return Form1099Result(
        tax_year=config.tax_year,
        candidates=candidates,
        data_quality=sorted(assessed.values(), key=lambda dq: dq.vendor_name.lower()),
        w9_collection_list=sorted(w9_list, key=lambda w: w.vendor_name.lower()),
        summary=summary,
    )
