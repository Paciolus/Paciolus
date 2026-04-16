"""
Loan Amortization Routes (Sprint 625 / Sprint 672).

Form-input only — zero-storage compliant. Generates an amortization schedule
with CSV, XLSX, and PDF exports. Sprint 672 added the XLSX and PDF exports
so auditors can paste formatted schedules into engagement workpapers.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError

from auth import User, require_verified_user
from loan_amortization_engine import (
    AmortizationResult,
    ExtraPayment,
    LoanConfig,
    LoanInputError,
    LoanMethod,
    RateChange,
    generate_amortization_schedule,
)
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["loan-amortization"])


# =============================================================================
# Request / response schemas
# =============================================================================


class RateChangeRequest(BaseModel):
    period_number: int = Field(..., ge=1, le=600)
    new_annual_rate: str = Field(..., min_length=1, max_length=12)


class ExtraPaymentRequest(BaseModel):
    period_number: int = Field(..., ge=1, le=600)
    amount: str = Field(..., min_length=1, max_length=20)


class LoanAmortizationRequest(BaseModel):
    principal: str = Field(..., min_length=1, max_length=20)
    annual_rate: str = Field(..., min_length=1, max_length=12)  # e.g. "0.06"
    term_periods: int = Field(..., ge=1, le=600)
    frequency: Literal["monthly", "quarterly", "semi-annual", "annual"] = "monthly"
    method: Literal["standard", "interest_only", "balloon"] = "standard"
    start_date: Optional[date] = None
    balloon_amount: Optional[str] = Field(default=None, max_length=20)
    extra_payments: list[ExtraPaymentRequest] = Field(default_factory=list, max_length=200)
    rate_changes: list[RateChangeRequest] = Field(default_factory=list, max_length=50)


class AmortizationScheduleResponse(BaseModel):
    schedule: list[dict]
    annual_summary: list[dict]
    inputs: dict
    total_interest: str
    total_payments: str
    payoff_date: Optional[str]
    journal_entry_templates: list[dict]


# =============================================================================
# Helpers
# =============================================================================


def _to_decimal(field_name: str, raw: str) -> Decimal:
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")


def _build_config(payload: LoanAmortizationRequest) -> LoanConfig:
    return LoanConfig(
        principal=_to_decimal("principal", payload.principal),
        annual_rate=_to_decimal("annual_rate", payload.annual_rate),
        term_periods=payload.term_periods,
        frequency=payload.frequency,
        method=LoanMethod(payload.method),
        start_date=payload.start_date,
        balloon_amount=_to_decimal("balloon_amount", payload.balloon_amount) if payload.balloon_amount else None,
        extra_payments=[
            ExtraPayment(period_number=e.period_number, amount=_to_decimal("extra amount", e.amount))
            for e in payload.extra_payments
        ],
        rate_changes=[
            RateChange(period_number=r.period_number, new_annual_rate=_to_decimal("rate change", r.new_annual_rate))
            for r in payload.rate_changes
        ],
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/audit/loan-amortization",
    response_model=AmortizationScheduleResponse,
)
@limiter.limit(RATE_LIMIT_AUDIT)
def calculate_schedule(
    request: Request,
    payload: LoanAmortizationRequest,
    current_user: User = Depends(require_verified_user),
) -> AmortizationScheduleResponse:
    """Calculate a loan amortization schedule from form inputs.

    Zero-storage: nothing is persisted; the response is computed on demand.
    """
    try:
        config = _build_config(payload)
        result = generate_amortization_schedule(config)
    except LoanInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, ValidationError) as e:
        logger.exception("Loan amortization computation failed")
        raise HTTPException(status_code=400, detail=sanitize_error(e, "audit", "loan_amortization_error"))

    payload_dict = result.to_dict()
    return AmortizationScheduleResponse(**payload_dict)  # type: ignore[arg-type]


@router.post(
    "/audit/loan-amortization/export.csv",
)
@limiter.limit(RATE_LIMIT_AUDIT)
def export_schedule_csv(
    request: Request,
    payload: LoanAmortizationRequest,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """CSV export of the amortization schedule."""
    try:
        config = _build_config(payload)
        result = generate_amortization_schedule(config)
    except LoanInputError as e:
        raise HTTPException(status_code=400, detail=str(e))

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Period",
            "Payment Date",
            "Beginning Balance",
            "Scheduled Payment",
            "Interest",
            "Principal",
            "Extra Principal",
            "Ending Balance",
        ]
    )
    for entry in result.schedule:
        writer.writerow(
            [
                entry.period_number,
                entry.payment_date.isoformat() if entry.payment_date else "",
                f"{entry.beginning_balance}",
                f"{entry.scheduled_payment}",
                f"{entry.interest}",
                f"{entry.principal}",
                f"{entry.extra_principal}",
                f"{entry.ending_balance}",
            ]
        )
    writer.writerow([])
    writer.writerow(["Total Interest", "", "", "", f"{result.total_interest}", "", "", ""])
    writer.writerow(["Total Payments", "", "", "", "", "", "", f"{result.total_payments}"])

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=loan_amortization_schedule.csv"},
    )


def _compute_or_400(payload: LoanAmortizationRequest) -> AmortizationResult:
    try:
        return generate_amortization_schedule(_build_config(payload))
    except LoanInputError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/audit/loan-amortization/export.xlsx")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_schedule_xlsx(
    request: Request,
    payload: LoanAmortizationRequest,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """XLSX export with Schedule, Annual Summary, and Inputs sheets (Sprint 672)."""
    from loan_amortization_excel import build_amortization_workbook

    result = _compute_or_400(payload)
    xlsx_bytes = build_amortization_workbook(result)

    return StreamingResponse(
        iter([xlsx_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=loan_amortization_schedule.xlsx"},
    )


@router.post("/audit/loan-amortization/export.pdf")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_schedule_pdf(
    request: Request,
    payload: LoanAmortizationRequest,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """PDF export of the amortization schedule (Sprint 672)."""
    from pdf.sections.loan_amortization import build_amortization_pdf

    result = _compute_or_400(payload)
    pdf_bytes = build_amortization_pdf(result)

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=loan_amortization_schedule.pdf"},
    )
