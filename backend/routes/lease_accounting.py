"""
Lease Accounting Routes (Sprint 629).

Form-input only — zero-storage compliant. Runs the ASC 842 lessee workflow:
classification, initial measurement, amortization schedules, and disclosure
tables. CSV export endpoint provided.
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
from pydantic import BaseModel, Field

from auth import User, require_verified_user
from lease_accounting_engine import (
    LeaseConfig,
    LeaseInputError,
    compute_lease_accounting,
)
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["lease-accounting"])


# =============================================================================
# Schemas
# =============================================================================


class LeaseAccountingRequest(BaseModel):
    lease_name: str = Field(..., min_length=1, max_length=200)
    payment_amount: str = Field(..., min_length=1, max_length=20)
    term_periods: int = Field(..., ge=1, le=600)
    annual_discount_rate: str = Field(..., min_length=1, max_length=12)
    frequency: Literal["monthly", "quarterly", "semi-annual", "annual"] = "monthly"
    payments_in_advance: bool = True
    annual_escalation_rate: str = Field(default="0", max_length=12)
    initial_direct_costs: str = Field(default="0", max_length=20)
    prepaid_lease_payments: str = Field(default="0", max_length=20)
    lease_incentives: str = Field(default="0", max_length=20)
    asset_useful_life_years: Optional[int] = Field(default=None, ge=1, le=100)
    asset_fair_value: Optional[str] = Field(default=None, max_length=20)
    transfers_ownership: bool = False
    bargain_purchase_option: bool = False
    specialized_nature: bool = False
    start_date: Optional[date] = None


class LeaseAccountingResponse(BaseModel):
    inputs: dict
    classification: dict
    initial_lease_liability: str
    initial_rou_asset: str
    liability_schedule: list[dict]
    rou_schedule: list[dict]
    disclosure_tables: dict
    total_lease_cost: str
    total_interest_expense: str


# =============================================================================
# Helpers
# =============================================================================


def _to_decimal(field_name: str, raw: str) -> Decimal:
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")


def _build_config(payload: LeaseAccountingRequest) -> LeaseConfig:
    return LeaseConfig(
        lease_name=payload.lease_name,
        payment_amount=_to_decimal("payment_amount", payload.payment_amount),
        term_periods=payload.term_periods,
        annual_discount_rate=_to_decimal("annual_discount_rate", payload.annual_discount_rate),
        frequency=payload.frequency,
        payments_in_advance=payload.payments_in_advance,
        annual_escalation_rate=_to_decimal("annual_escalation_rate", payload.annual_escalation_rate),
        initial_direct_costs=_to_decimal("initial_direct_costs", payload.initial_direct_costs),
        prepaid_lease_payments=_to_decimal("prepaid_lease_payments", payload.prepaid_lease_payments),
        lease_incentives=_to_decimal("lease_incentives", payload.lease_incentives),
        asset_useful_life_years=payload.asset_useful_life_years,
        asset_fair_value=_to_decimal("asset_fair_value", payload.asset_fair_value)
        if payload.asset_fair_value
        else None,
        transfers_ownership=payload.transfers_ownership,
        bargain_purchase_option=payload.bargain_purchase_option,
        specialized_nature=payload.specialized_nature,
        start_date=payload.start_date,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/audit/lease-accounting", response_model=LeaseAccountingResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
def calculate_lease(
    request: Request,
    payload: LeaseAccountingRequest,
    current_user: User = Depends(require_verified_user),
) -> LeaseAccountingResponse:
    """Run ASC 842 lessee workflow: classification + initial measurement +
    amortization + disclosures.

    Zero-storage: nothing persisted. Single-lease only — multi-lease bundling
    is a future-sprint enhancement.
    """
    try:
        config = _build_config(payload)
        result = compute_lease_accounting(config)
    except LeaseInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError,) as e:
        logger.exception("Lease accounting computation failed")
        raise HTTPException(status_code=400, detail=sanitize_error(e, "audit", "lease_accounting_error"))
    return LeaseAccountingResponse(**result.to_dict())  # type: ignore[arg-type]


@router.post("/audit/lease-accounting/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_lease_csv(
    request: Request,
    payload: LeaseAccountingRequest,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """CSV export of liability schedule, ROU schedule, and disclosures."""
    try:
        config = _build_config(payload)
        result = compute_lease_accounting(config)
    except LeaseInputError as e:
        raise HTTPException(status_code=400, detail=str(e))

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow([f"Lease: {config.lease_name}"])
    writer.writerow(
        [
            "Classification",
            result.classification_result.classification.value,
        ]
    )
    writer.writerow(["Initial Lease Liability", str(result.initial_lease_liability)])
    writer.writerow(["Initial ROU Asset", str(result.initial_rou_asset)])
    writer.writerow([])

    writer.writerow(["LIABILITY SCHEDULE"])
    writer.writerow(["Period", "Payment Date", "Payment", "Interest", "Principal", "Ending Liability"])
    for entry in result.liability_schedule:
        writer.writerow(
            [
                entry.period_number,
                entry.payment_date.isoformat() if entry.payment_date else "",
                f"{entry.payment}",
                f"{entry.interest}",
                f"{entry.principal}",
                f"{entry.ending_liability}",
            ]
        )
    writer.writerow([])

    writer.writerow(["RIGHT-OF-USE ASSET SCHEDULE"])
    writer.writerow(["Period", "Payment Date", "ROU Amortization", "Period Lease Cost", "Ending ROU Balance"])
    for entry in result.rou_schedule:
        writer.writerow(
            [
                entry.period_number,
                entry.payment_date.isoformat() if entry.payment_date else "",
                f"{entry.rou_amortization}",
                f"{entry.period_lease_cost}",
                f"{entry.ending_rou_balance}",
            ]
        )
    writer.writerow([])

    writer.writerow(["MATURITY ANALYSIS (UNDISCOUNTED)"])
    for bucket in result.disclosure_tables.maturity_analysis:
        writer.writerow([bucket.label, str(bucket.undiscounted_payments)])
    d = result.disclosure_tables
    writer.writerow(["Total undiscounted payments", str(d.total_undiscounted_payments)])
    writer.writerow(["Less: imputed interest", str(d.less_imputed_interest)])
    writer.writerow(["Present value of lease liability", str(d.present_value_of_lease_liability)])
    writer.writerow(["Weighted-avg remaining term (years)", str(d.weighted_average_remaining_term_years)])
    writer.writerow(["Weighted-avg discount rate", str(d.weighted_average_discount_rate)])

    safe_name = "".join(c if c.isalnum() else "_" for c in config.lease_name)[:60]
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=lease_{safe_name}.csv"},
    )
