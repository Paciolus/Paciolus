"""
W-2 / W-3 Reconciliation Routes (Sprint 636).

Form-input only — zero-storage. Accepts payroll YTD + optional draft
W-2 list + optional quarterly 941s; returns employee discrepancies and
Form 941 mismatches. CSV export ships now; PDF deferred.
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
from database import get_db
from shared.entitlement_checks import check_upload_limit
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_route import enforce_tool_access
from w2_reconciliation_engine import (
    EmployeePayroll,
    EmployeeW2Draft,
    Form941Quarter,
    HsaCoverage,
    W2ReconciliationConfig,
    W2ReconciliationInputError,
    reconcile_w2,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["w2-reconciliation"])


HsaCoverageLiteral = Literal["none", "self_only", "family"]
RetirementPlanLiteral = Literal["401k", "simple_ira"]


class EmployeePayrollRequest(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=64)
    employee_name: str = Field(..., min_length=1, max_length=200)
    age: int | None = Field(default=None, ge=14, le=120)
    federal_wages: str = Field(default="0", max_length=24)
    federal_withholding: str = Field(default="0", max_length=24)
    ss_wages: str = Field(default="0", max_length=24)
    ss_tax_withheld: str = Field(default="0", max_length=24)
    medicare_wages: str = Field(default="0", max_length=24)
    medicare_tax_withheld: str = Field(default="0", max_length=24)
    hsa_contributions: str = Field(default="0", max_length=24)
    hsa_coverage: HsaCoverageLiteral = "none"
    retirement_401k: str = Field(default="0", max_length=24)
    retirement_simple_ira: str = Field(default="0", max_length=24)
    retirement_plan_type: RetirementPlanLiteral | None = None


class EmployeeW2DraftRequest(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=64)
    box_1_federal_wages: str = Field(default="0", max_length=24)
    box_2_federal_withholding: str = Field(default="0", max_length=24)
    box_3_ss_wages: str = Field(default="0", max_length=24)
    box_4_ss_tax_withheld: str = Field(default="0", max_length=24)
    box_5_medicare_wages: str = Field(default="0", max_length=24)
    box_6_medicare_tax_withheld: str = Field(default="0", max_length=24)
    box_12_code_w_hsa: str = Field(default="0", max_length=24)
    box_12_code_d_401k: str = Field(default="0", max_length=24)
    box_12_code_s_simple: str = Field(default="0", max_length=24)


class Form941QuarterRequest(BaseModel):
    quarter: int = Field(..., ge=1, le=4)
    total_federal_wages: str = Field(default="0", max_length=24)
    total_federal_withholding: str = Field(default="0", max_length=24)
    total_ss_wages: str = Field(default="0", max_length=24)
    total_medicare_wages: str = Field(default="0", max_length=24)


class W2ReconciliationRequest(BaseModel):
    tax_year: int = Field(..., ge=2000, le=2099)
    employees: list[EmployeePayrollRequest] = Field(default_factory=list, max_length=10000)
    w2_drafts: list[EmployeeW2DraftRequest] = Field(default_factory=list, max_length=10000)
    form_941_quarters: list[Form941QuarterRequest] = Field(default_factory=list, max_length=4)
    tolerance: str = Field(default="1.00", max_length=12)


def _to_decimal(field_name: str, raw: str) -> Decimal:
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")


def _build_config(payload: W2ReconciliationRequest) -> W2ReconciliationConfig:
    employees = [
        EmployeePayroll(
            employee_id=e.employee_id,
            employee_name=e.employee_name,
            age=e.age,
            federal_wages=_to_decimal("federal_wages", e.federal_wages),
            federal_withholding=_to_decimal("federal_withholding", e.federal_withholding),
            ss_wages=_to_decimal("ss_wages", e.ss_wages),
            ss_tax_withheld=_to_decimal("ss_tax_withheld", e.ss_tax_withheld),
            medicare_wages=_to_decimal("medicare_wages", e.medicare_wages),
            medicare_tax_withheld=_to_decimal("medicare_tax_withheld", e.medicare_tax_withheld),
            hsa_contributions=_to_decimal("hsa_contributions", e.hsa_contributions),
            hsa_coverage=HsaCoverage(e.hsa_coverage),
            retirement_401k=_to_decimal("retirement_401k", e.retirement_401k),
            retirement_simple_ira=_to_decimal("retirement_simple_ira", e.retirement_simple_ira),
            retirement_plan_type=e.retirement_plan_type,
        )
        for e in payload.employees
    ]
    w2_drafts = [
        EmployeeW2Draft(
            employee_id=w.employee_id,
            box_1_federal_wages=_to_decimal("box_1", w.box_1_federal_wages),
            box_2_federal_withholding=_to_decimal("box_2", w.box_2_federal_withholding),
            box_3_ss_wages=_to_decimal("box_3", w.box_3_ss_wages),
            box_4_ss_tax_withheld=_to_decimal("box_4", w.box_4_ss_tax_withheld),
            box_5_medicare_wages=_to_decimal("box_5", w.box_5_medicare_wages),
            box_6_medicare_tax_withheld=_to_decimal("box_6", w.box_6_medicare_tax_withheld),
            box_12_code_w_hsa=_to_decimal("box_12_w", w.box_12_code_w_hsa),
            box_12_code_d_401k=_to_decimal("box_12_d", w.box_12_code_d_401k),
            box_12_code_s_simple=_to_decimal("box_12_s", w.box_12_code_s_simple),
        )
        for w in payload.w2_drafts
    ]
    form_941 = [
        Form941Quarter(
            quarter=q.quarter,
            total_federal_wages=_to_decimal("941 fed wages", q.total_federal_wages),
            total_federal_withholding=_to_decimal("941 fed withholding", q.total_federal_withholding),
            total_ss_wages=_to_decimal("941 ss wages", q.total_ss_wages),
            total_medicare_wages=_to_decimal("941 medicare wages", q.total_medicare_wages),
        )
        for q in payload.form_941_quarters
    ]
    return W2ReconciliationConfig(
        tax_year=payload.tax_year,
        employees=employees,
        w2_drafts=w2_drafts,
        form_941_quarters=form_941,
        tolerance=_to_decimal("tolerance", payload.tolerance),
    )


@router.post("/audit/w2-reconciliation")
@limiter.limit(RATE_LIMIT_AUDIT)
def run_reconciliation(
    request: Request,
    payload: W2ReconciliationRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict:
    # Sprint 689d: gate promoted tool at tier + upload-limit level.
    enforce_tool_access(current_user, "w2_reconciliation", db)
    check_upload_limit(current_user, db)

    try:
        result = reconcile_w2(_build_config(payload))
    except W2ReconciliationInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, ValidationError) as e:
        logger.exception("W-2 reconciliation failed")
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "audit", "w2_reconciliation_error"),
        )
    return result.to_dict()


@router.post("/audit/w2-reconciliation/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_reconciliation_csv(
    request: Request,
    payload: W2ReconciliationRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    # Sprint 689d: gate promoted tool (export mirrors analyze-route gating).
    enforce_tool_access(current_user, "w2_reconciliation", db)

    try:
        result = reconcile_w2(_build_config(payload))
    except W2ReconciliationInputError as e:
        raise HTTPException(status_code=400, detail=str(e))

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["Employee Discrepancies"])
    writer.writerow(
        [
            "Employee ID",
            "Employee Name",
            "Kind",
            "Severity",
            "Expected",
            "Actual",
            "Difference",
            "Message",
        ]
    )
    for d in result.employee_discrepancies:
        writer.writerow(
            [
                d.employee_id,
                d.employee_name,
                d.kind.value,
                d.severity.value,
                str(d.expected),
                str(d.actual),
                str(d.difference),
                d.message,
            ]
        )

    writer.writerow([])
    writer.writerow(["Form 941 Mismatches"])
    writer.writerow(["Quarter", "Kind", "Severity", "Expected", "Actual", "Difference", "Message"])
    for m in result.form_941_mismatches:
        writer.writerow(
            [
                m.quarter if m.quarter is not None else "ALL",
                m.kind.value,
                m.severity.value,
                str(m.expected),
                str(m.actual),
                str(m.difference),
                m.message,
            ]
        )

    writer.writerow([])
    writer.writerow(["W-3 Totals"])
    w3 = result.w3_totals
    writer.writerow(["Employee Count", w3.employee_count])
    writer.writerow(["Total Federal Wages", str(w3.total_federal_wages)])
    writer.writerow(["Total Federal Withholding", str(w3.total_federal_withholding)])
    writer.writerow(["Total SS Wages", str(w3.total_ss_wages)])
    writer.writerow(["Total SS Tax Withheld", str(w3.total_ss_tax_withheld)])
    writer.writerow(["Total Medicare Wages", str(w3.total_medicare_wages)])
    writer.writerow(["Total Medicare Tax Withheld", str(w3.total_medicare_tax_withheld)])

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=w2_reconciliation_{result.tax_year}.csv"},
    )
