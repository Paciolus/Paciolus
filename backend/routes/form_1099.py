"""
Form 1099 Preparation Routes (Sprint 634).

Form-input only — zero-storage. Accepts a vendor list and a payment
list, returns filing candidates. CSV export is shipped in this sprint;
PDF is deferred to the downstream section framework follow-up.
"""

from __future__ import annotations

import io
import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from auth import User, require_verified_user
from database import get_db
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
from shared.entitlement_checks import check_upload_limit
from shared.error_messages import sanitize_error
from shared.export_helpers import MEDIA_CSV, attachment_response
from shared.filenames import safe_csv_writer
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.request_decimal import parse_request_decimal as _to_decimal
from shared.testing_route import enforce_tool_access
from shared.tool_run_recorder import maybe_record_tool_run

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

PaymentCategoryLiteral = Literal[
    "nonemployee_comp", "attorney_fees", "rents", "royalties", "medical", "legal", "interest", "other"
]


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
    # Sprint 787b: optional engagement link so a run lands in the workpaper trail.
    engagement_id: Optional[int] = Field(None, description="Optional engagement to link this run to")


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
    db: Session = Depends(get_db),
) -> dict:
    # Sprint 689e: gate promoted tool at tier + upload-limit level.
    enforce_tool_access(current_user, "form_1099", db)
    check_upload_limit(current_user, db)

    try:
        result = prepare_1099s(_build_config(payload))
    except Form1099InputError as e:
        maybe_record_tool_run(db, payload.engagement_id, current_user.id, "form_1099", False)
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, ValidationError, ArithmeticError) as e:
        logger.exception("1099 preparation failed")
        maybe_record_tool_run(db, payload.engagement_id, current_user.id, "form_1099", False)
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "audit", "form_1099_error"),
        )

    # Sprint 787b: record the run on the engagement workpaper trail. Both
    # composite_score and flagged_accounts are None by design, not omission:
    # this engine produces no composite score, and shared/account_extractors.py
    # has no extractor for it because its output is not GL-account-level.
    # PR #183 review: recorded synchronously, not via background_tasks.
    # Starlette sends the response body (responses.py:167) *before* awaiting the
    # background task (:170), so the client already has the result while the
    # insert is still pending. Sprint 791's hooks call refreshToolRuns() as soon
    # as the POST resolves, which would GET the workpaper list before the row
    # existed, replace the context state with the stale list, and never refresh
    # again — the new entry invisible until a manual reload. The write is one
    # INSERT plus a commit after an analysis that already ran in-process, so the
    # latency it buys back is not worth the race.
    maybe_record_tool_run(
        db, payload.engagement_id, current_user.id, "form_1099", True, None, None, consumes_upload=True
    )
    return result.to_dict()


@router.post("/audit/form-1099/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_1099_csv(
    request: Request,
    payload: Form1099Request,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> Response:
    # Sprint 689e: gate promoted tool (export mirrors analyze-route gating).
    enforce_tool_access(current_user, "form_1099", db)

    try:
        result = prepare_1099s(_build_config(payload))
    except Form1099InputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ArithmeticError:
        # Sprint 827: a huge-but-finite amount ("1e400") passes parsing, then
        # quantize() raises InvalidOperation — an input problem, not a 500.
        raise HTTPException(status_code=400, detail="An amount is too large to process.")

    buffer = io.StringIO()
    writer = safe_csv_writer(buffer)
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

    # Sprint 837: the CSV carries the same transparency as the API response —
    # payees below the year's threshold, any notice, and the thresholds applied.
    if result.below_threshold_payees:
        writer.writerow([])
        writer.writerow([f"Below the {result.tax_year} reporting threshold — not required, shown for review"])
        writer.writerow(["Tax Year", "Form Type", "Vendor ID", "Vendor Name", "Total", "Categories", "Reason"])
        for payee in result.below_threshold_payees:
            categories = "; ".join(f"{b.category} (box {b.box})={b.amount}" for b in payee.box_amounts)
            writer.writerow(
                [
                    result.tax_year,
                    payee.form_type,
                    payee.vendor_id,
                    payee.vendor_name,
                    str(payee.total),
                    categories,
                    payee.reason,
                ]
            )

    if result.notices:
        writer.writerow([])
        writer.writerow(["Notices"])
        for notice in result.notices:
            writer.writerow([notice])

    if result.thresholds is not None:
        writer.writerow([])
        writer.writerow([f"Thresholds applied for tax year {result.tax_year}"])
        writer.writerow(["Form Type", "Box", "Description", "Threshold", "Basis", "Needs Confirmation"])
        for item in result.thresholds.items:
            row = item.to_dict()
            writer.writerow(
                [
                    row["form_type"],
                    row["box"],
                    row["description"],
                    row["amount"],
                    row["basis"],
                    "Yes" if row["needs_confirmation"] else "No",
                ]
            )
        writer.writerow([result.thresholds.confirm_against()])

    buffer.seek(0)
    return attachment_response(
        buffer.getvalue(), f"form_1099_candidates_{result.tax_year}.csv", MEDIA_CSV, quote_filename=False
    )
