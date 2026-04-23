"""
Book-to-Tax Adjustment Routes (Sprint 635).

Form-input only — zero-storage. M-1 / M-3 reconciliation, deferred tax
rollforward, and a provision summary. CSV export is shipped in this
sprint; PDF section rendering is deferred to the downstream section
framework follow-up.
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
from sqlalchemy.orm import Session

from auth import User, require_verified_user
from book_to_tax_engine import (
    STANDARD_ADJUSTMENTS,
    AdjustmentDirection,
    AdjustmentEntry,
    BookToTaxConfig,
    BookToTaxInputError,
    DeferredTaxRollforwardInput,
    DifferenceType,
    calculate_book_to_tax,
)
from database import get_db
from shared.entitlement_checks import check_upload_limit
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_route import enforce_tool_access

logger = logging.getLogger(__name__)

router = APIRouter(tags=["book-to-tax"])


DirectionLiteral = Literal["add", "subtract"]
DifferenceLiteral = Literal["permanent", "temporary"]


class AdjustmentRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=200)
    amount: str = Field(..., min_length=1, max_length=24)
    difference_type: DifferenceLiteral
    direction: DirectionLiteral
    code: str | None = Field(default=None, max_length=64)


class RollforwardRequest(BaseModel):
    beginning_dta: str = Field(default="0", max_length=24)
    beginning_dtl: str = Field(default="0", max_length=24)


class BookToTaxRequest(BaseModel):
    tax_year: int = Field(..., ge=2000, le=2099)
    book_pretax_income: str = Field(..., min_length=1, max_length=24)
    total_assets: str = Field(..., min_length=1, max_length=24)
    federal_tax_rate: str = Field(..., min_length=1, max_length=12)
    state_tax_rate: str = Field(default="0", max_length=12)
    adjustments: list[AdjustmentRequest] = Field(default_factory=list, max_length=500)
    rollforward: RollforwardRequest = Field(default_factory=RollforwardRequest)


def _to_decimal(field_name: str, raw: str) -> Decimal:
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")


def _build_config(payload: BookToTaxRequest) -> BookToTaxConfig:
    adjustments = [
        AdjustmentEntry(
            label=a.label,
            amount=_to_decimal("adjustment", a.amount),
            difference_type=DifferenceType(a.difference_type),
            direction=AdjustmentDirection(a.direction),
            code=a.code,
        )
        for a in payload.adjustments
    ]
    return BookToTaxConfig(
        tax_year=payload.tax_year,
        book_pretax_income=_to_decimal("book_pretax_income", payload.book_pretax_income),
        total_assets=_to_decimal("total_assets", payload.total_assets),
        federal_tax_rate=_to_decimal("federal_tax_rate", payload.federal_tax_rate),
        state_tax_rate=_to_decimal("state_tax_rate", payload.state_tax_rate),
        adjustments=adjustments,
        rollforward=DeferredTaxRollforwardInput(
            beginning_dta=_to_decimal("beginning_dta", payload.rollforward.beginning_dta),
            beginning_dtl=_to_decimal("beginning_dtl", payload.rollforward.beginning_dtl),
        ),
    )


@router.get("/audit/book-to-tax/standard-adjustments")
@limiter.limit(RATE_LIMIT_AUDIT)
def list_standard_adjustments(
    request: Request,
    current_user: User = Depends(require_verified_user),
) -> dict:
    """Return the catalog of common permanent / temporary adjustments.

    Used by the frontend to pre-populate the adjustment picker so the
    practitioner can select from the common list rather than typing
    adjustment codes from memory.
    """
    return {
        "standard_adjustments": [
            {
                "code": s.code,
                "description": s.description,
                "difference_type": s.difference_type.value,
                "typical_direction": s.typical_direction.value,
            }
            for s in STANDARD_ADJUSTMENTS
        ]
    }


@router.post("/audit/book-to-tax")
@limiter.limit(RATE_LIMIT_AUDIT)
def calculate(
    request: Request,
    payload: BookToTaxRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict:
    # Sprint 689f: gate promoted tool at tier + upload-limit level.
    enforce_tool_access(current_user, "book_to_tax", db)
    check_upload_limit(current_user, db)

    try:
        result = calculate_book_to_tax(_build_config(payload))
    except BookToTaxInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, ValidationError) as e:
        logger.exception("Book-to-tax calculation failed")
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "audit", "book_to_tax_error"),
        )
    return result.to_dict()


@router.post("/audit/book-to-tax/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_book_to_tax_csv(
    request: Request,
    payload: BookToTaxRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    # Sprint 689f: gate promoted tool (export mirrors analyze-route gating).
    enforce_tool_access(current_user, "book_to_tax", db)

    try:
        result = calculate_book_to_tax(_build_config(payload))
    except BookToTaxInputError as e:
        raise HTTPException(status_code=400, detail=str(e))

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["Schedule M-1"])
    writer.writerow(["Line", "Description", "Amount"])
    writer.writerow(["1", "Net Income per Books", str(result.schedule_m1.net_income_per_books)])
    writer.writerow(["2", "Federal Income Tax per Books", str(result.schedule_m1.federal_income_tax_per_books)])
    writer.writerow([])
    writer.writerow(["Permanent Additions"])
    for a in result.schedule_m1.permanent_additions:
        writer.writerow(["", a.label, str(a.amount)])
    writer.writerow(["Temporary Additions"])
    for a in result.schedule_m1.temporary_additions:
        writer.writerow(["", a.label, str(a.amount)])
    writer.writerow(["Permanent Subtractions"])
    for a in result.schedule_m1.permanent_subtractions:
        writer.writerow(["", a.label, str(a.amount)])
    writer.writerow(["Temporary Subtractions"])
    for a in result.schedule_m1.temporary_subtractions:
        writer.writerow(["", a.label, str(a.amount)])
    writer.writerow([])
    writer.writerow(["", "Taxable Income", str(result.schedule_m1.taxable_income)])

    writer.writerow([])
    writer.writerow(["Deferred Tax Rollforward"])
    dt = result.deferred_tax
    writer.writerow(["", "Beginning DTA", str(dt.beginning_dta)])
    writer.writerow(["", "Beginning DTL", str(dt.beginning_dtl)])
    writer.writerow(["", "Current-Year Temporary Net", str(dt.current_year_temporary_adjustments)])
    writer.writerow(["", "Tax Rate", str(dt.tax_rate)])
    writer.writerow(["", "Movement", str(dt.current_year_movement)])
    writer.writerow(["", "Ending DTA", str(dt.ending_dta)])
    writer.writerow(["", "Ending DTL", str(dt.ending_dtl)])

    writer.writerow([])
    writer.writerow(["Tax Provision"])
    p = result.tax_provision
    writer.writerow(["", "Taxable Income", str(p.taxable_income)])
    writer.writerow(["", "Current Federal Tax", str(p.current_federal_tax)])
    writer.writerow(["", "Current State Tax", str(p.current_state_tax)])
    writer.writerow(["", "Deferred Tax Expense", str(p.deferred_tax_expense)])
    writer.writerow(["", "Total Tax Expense", str(p.total_tax_expense)])
    writer.writerow(["", "Effective Rate", str(p.effective_rate)])

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=book_to_tax_{result.tax_year}.csv"},
    )
