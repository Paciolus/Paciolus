"""
Cash Flow Projector Routes (Sprint 633).

Form-input only — zero-storage compliant. 30/60/90-day forward cash
position forecast with base / stress / best scenarios. CSV export is
shipped in this sprint; PDF and Excel exports are deferred to a
follow-up alongside the downstream section framework work.
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
from sqlalchemy.orm import Session

from auth import User, require_verified_user
from cash_flow_projector_engine import (
    AgingBuckets,
    CashFlowConfig,
    CashFlowInputError,
    RecurringFlow,
    project_cash_flow,
)
from database import get_db
from shared.entitlement_checks import check_upload_limit
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_route import enforce_tool_access

logger = logging.getLogger(__name__)

router = APIRouter(tags=["cash-flow-projector"])


class AgingBucketsRequest(BaseModel):
    current: str = Field(default="0", max_length=24)
    days_1_30: str = Field(default="0", max_length=24)
    days_31_60: str = Field(default="0", max_length=24)
    days_61_90: str = Field(default="0", max_length=24)
    days_over_90: str = Field(default="0", max_length=24)


class RecurringFlowRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=80)
    amount: str = Field(..., min_length=1, max_length=24)
    frequency: Literal["weekly", "biweekly", "monthly", "quarterly"]
    first_date: date


class CashFlowProjectionRequest(BaseModel):
    opening_balance: str = Field(..., min_length=1, max_length=24)
    start_date: date
    ar_aging: AgingBucketsRequest = Field(default_factory=AgingBucketsRequest)
    ap_aging: AgingBucketsRequest = Field(default_factory=AgingBucketsRequest)
    recurring_flows: list[RecurringFlowRequest] = Field(default_factory=list, max_length=100)
    min_safe_cash: Optional[str] = Field(default=None, max_length=24)


def _to_decimal(field_name: str, raw: str) -> Decimal:
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")


def _to_aging(payload: AgingBucketsRequest) -> AgingBuckets:
    return AgingBuckets(
        current=_to_decimal("ar/ap current", payload.current),
        days_1_30=_to_decimal("1-30", payload.days_1_30),
        days_31_60=_to_decimal("31-60", payload.days_31_60),
        days_61_90=_to_decimal("61-90", payload.days_61_90),
        days_over_90=_to_decimal("over-90", payload.days_over_90),
    )


def _build_config(payload: CashFlowProjectionRequest) -> CashFlowConfig:
    return CashFlowConfig(
        opening_balance=_to_decimal("opening_balance", payload.opening_balance),
        start_date=payload.start_date,
        ar_aging=_to_aging(payload.ar_aging),
        ap_aging=_to_aging(payload.ap_aging),
        recurring_flows=[
            RecurringFlow(
                label=f.label,
                amount=_to_decimal("recurring amount", f.amount),
                frequency=f.frequency,
                first_date=f.first_date,
            )
            for f in payload.recurring_flows
        ],
        min_safe_cash=_to_decimal("min_safe_cash", payload.min_safe_cash) if payload.min_safe_cash else None,
    )


@router.post("/audit/cash-flow-projector")
@limiter.limit(RATE_LIMIT_AUDIT)
def run_projection(
    request: Request,
    payload: CashFlowProjectionRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict:
    # Sprint 689g: gate promoted tool at tier + upload-limit level.
    enforce_tool_access(current_user, "cash_flow_projector", db)
    check_upload_limit(current_user, db)

    try:
        config = _build_config(payload)
        result = project_cash_flow(config)
    except CashFlowInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, ValidationError) as e:
        logger.exception("Cash flow projection computation failed")
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "audit", "cash_flow_projector_error"),
        )
    return result.to_dict()


@router.post("/audit/cash-flow-projector/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_projection_csv(
    request: Request,
    payload: CashFlowProjectionRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    # Sprint 689g: gate promoted tool (export mirrors analyze-route gating).
    enforce_tool_access(current_user, "cash_flow_projector", db)

    try:
        config = _build_config(payload)
        result = project_cash_flow(config)
    except CashFlowInputError as e:
        raise HTTPException(status_code=400, detail=str(e))

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Scenario",
            "Day Index",
            "Date",
            "AR Inflow",
            "AP Outflow",
            "Recurring Net",
            "Net Change",
            "Ending Balance",
        ]
    )
    for scenario_name, scenario in result.scenarios.items():
        for point in scenario.daily:
            writer.writerow(
                [
                    scenario_name,
                    point.day_index,
                    point.day_date.isoformat(),
                    str(point.ar_inflow),
                    str(point.ap_outflow),
                    str(point.recurring_net),
                    str(point.net_change),
                    str(point.ending_balance),
                ]
            )

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cash_flow_projection.csv"},
    )
