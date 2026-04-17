"""
Form 1099 Preparation Routes (Sprint 634).

Form-input only — zero-storage. Accepts a vendor list and a payment
list, returns filing candidates. CSV export is shipped in this sprint;
PDF is deferred to the downstream section framework follow-up.
"""

from __future__ import annotations

import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError

from auth import User, require_verified_user
from form_1099_engine import (
    EntityType,
    Form1099Config,
    Form1099InputError,
    PaymentCategory,
    PaymentMethod,
    VendorPayment,
    VendorRecord,
    prepare_1099s,
)
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["form-1099"])


VendorEntity = Literal[
    "individual",
    "partnership",
    "llc",
    "corporation",
    "s_corporation",
    "government",
    "tax_exempt",
    "unknown",
]

PaymentMethodLiteral = Literal["check", "ach", "wire", "cash", "credit_card", "paypal", "unknown"]

PaymentCategoryLiteral = Literal["nonemployee_comp", "rents", "royalties", "medical", "legal", "interest", "other"]


class VendorRequest(BaseModel):
    vendor_id: str = Field(..., min_length=1, max_length=64)
    vendor_name: str = Field(..., min_length=1, max_length=200)
    tin: str | None = Field(default=None, max_length=24)
    entity_type: VendorEntity = "unknown"
    address_line_1: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=24)
    postal_code: str | None = Field(default=None, max_length=24)


class PaymentRequest(BaseModel):
    vendor_id: str = Field(..., min_length=1, max_length=64)
    amount: str = Field(..., min_length=1, max_length=24)
    payment_category: PaymentCategoryLiteral = "nonemployee_comp"
    payment_method: PaymentMethodLiteral = "check"
    payment_date: str | None = Field(default=None, max_length=20)
    invoice_number: str | None = Field(default=None, max_length=80)


class Form1099Request(BaseModel):
    tax_year: int = Field(..., ge=2000, le=2099)
    vendors: list[VendorRequest] = Field(default_factory=list, max_length=5000)
    payments: list[PaymentRequest] = Field(default_factory=list, max_length=50000)


def _to_decimal(field_name: str, raw: str) -> Decimal:
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")


def _build_config(payload: Form1099Request) -> Form1099Config:
    vendors = [
        VendorRecord(
            vendor_id=v.vendor_id,
            vendor_name=v.vendor_name,
            tin=v.tin,
            entity_type=EntityType(v.entity_type),
            address_line_1=v.address_line_1,
            city=v.city,
            state=v.state,
            postal_code=v.postal_code,
        )
        for v in payload.vendors
    ]
    payments = [
        VendorPayment(
            vendor_id=p.vendor_id,
            amount=_to_decimal("payment amount", p.amount),
            payment_category=PaymentCategory(p.payment_category),
            payment_method=PaymentMethod(p.payment_method),
            payment_date=p.payment_date,
            invoice_number=p.invoice_number,
        )
        for p in payload.payments
    ]
    return Form1099Config(
        tax_year=payload.tax_year,
        vendors=vendors,
        payments=payments,
    )


@router.post("/audit/form-1099")
@limiter.limit(RATE_LIMIT_AUDIT)
def prepare_1099_candidates(
    request: Request,
    payload: Form1099Request,
    current_user: User = Depends(require_verified_user),
) -> dict:
    try:
        result = prepare_1099s(_build_config(payload))
    except Form1099InputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, ValidationError) as e:
        logger.exception("1099 preparation failed")
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "audit", "form_1099_error"),
        )
    return result.to_dict()


@router.post("/audit/form-1099/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_1099_csv(
    request: Request,
    payload: Form1099Request,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    try:
        result = prepare_1099s(_build_config(payload))
    except Form1099InputError as e:
        raise HTTPException(status_code=400, detail=str(e))

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Tax Year",
            "Form Type",
            "Vendor ID",
            "Vendor Name",
            "Total Reportable",
            "Categories",
            "Payment Count",
            "Excluded Amount",
            "Review Required",
            "Review Reasons",
        ]
    )
    for candidate in result.candidates:
        categories = "; ".join(f"{b.category} (box {b.box})={b.amount}" for b in candidate.box_amounts)
        writer.writerow(
            [
                result.tax_year,
                candidate.form_type,
                candidate.vendor_id,
                candidate.vendor_name,
                str(candidate.total_reportable),
                categories,
                candidate.payment_count,
                str(candidate.excluded_amount),
                "Yes" if candidate.flagged_for_review else "No",
                "; ".join(candidate.review_reasons),
            ]
        )

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=form_1099_candidates_{result.tax_year}.csv"},
    )
