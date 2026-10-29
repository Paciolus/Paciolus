"""
W-2 / W-3 Reconciliation Routes (Sprint 636).

Form-input only — zero-storage. Accepts payroll YTD + optional draft
W-2 list + optional quarterly 941s; returns employee discrepancies and
Form 941 mismatches. CSV export ships now; PDF deferred.
"""

from __future__ import annotations

import io
import logging
from decimal import Decimal
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import User, require_verified_user
from database import get_db
from shared.export_helpers import MEDIA_CSV, attachment_response
from shared.filenames import safe_csv_writer, sanitize_csv_value
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.request_decimal import parse_request_decimal as _to_decimal
from shared.testing_route import enforce_tool_access, run_json_tool
from w2_reconciliation_engine import (
    STATUTORY_LIMITS_BY_YEAR,
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
    # Sprint 855 (W4): an omitted figure is "not supplied" and is not compared.
    # It used to default to "0", so a 941 file without a Medicare column drew a
    # HIGH mismatch for a figure the return never stated.
    quarter: int = Field(..., ge=1, le=4)
    total_federal_wages: Optional[str] = Field(default=None, max_length=24)
    total_federal_withholding: Optional[str] = Field(default=None, max_length=24)
    total_ss_wages: Optional[str] = Field(default=None, max_length=24)
    total_medicare_wages: Optional[str] = Field(default=None, max_length=24)


class StatutoryLimitOverrides(BaseModel):
    """Per-request overrides for the statutory limits (Sprint 793a).

    The engine has carried a field for each of these since Sprint 636, and that
    sprint's record states the thresholds are "caller-overridable via
    `W2ReconciliationConfig`" — true in the engine and, until now, unreachable
    through the API. A practitioner who knew the correct figure for their filing
    year had no way to supply it.

    Since Sprint 811 the engine selects limits from a year-keyed table and
    refuses a year it has no table for (only 2025 today). For a tabulated year
    an omitted field keeps that year's figure; for any other year all eleven
    required fields must be supplied or the run is refused. The three catch-up
    fields (Sprint 826) are optional -- a check whose figure is missing is
    reported in ``checks_not_run`` rather than skipped silently. (Sprint 838:
    this docstring previously described the pre-811 single fixed set.)

    Decimal strings rather than floats, matching every other monetary field on
    this route.
    """

    ss_wage_base: Optional[str] = Field(default=None, max_length=24)
    ss_rate: Optional[str] = Field(default=None, max_length=12)
    medicare_rate: Optional[str] = Field(default=None, max_length=12)
    additional_medicare_rate: Optional[str] = Field(default=None, max_length=12)
    additional_medicare_threshold: Optional[str] = Field(default=None, max_length=24)
    hsa_self_only_limit: Optional[str] = Field(default=None, max_length=24)
    hsa_family_limit: Optional[str] = Field(default=None, max_length=24)
    limit_401k_elective: Optional[str] = Field(default=None, max_length=24)
    limit_401k_catchup_50: Optional[str] = Field(default=None, max_length=24)
    limit_401k_catchup_60_63: Optional[str] = Field(default=None, max_length=24)
    limit_simple_ira: Optional[str] = Field(default=None, max_length=24)
    # Sprint 826 (W1/W2, option C): optional catch-up limits. Unlike the eleven
    # above, these never cause a refusal: a run without them still works, and the
    # check that needs one is reported in `checks_not_run` instead. Supplying the
    # eleven above without these is still a full override (non-breaking).
    hsa_catchup_55: Optional[str] = Field(
        default=None, max_length=24, description="HSA age-55 catch-up, IRC §223(b)(3)(B) ($1,000, not indexed)."
    )
    limit_simple_catchup_50: Optional[str] = Field(
        default=None, max_length=24, description="SIMPLE IRA age 50+ catch-up, IRC §414(v)(2)(B)(ii)."
    )
    limit_simple_catchup_60_63: Optional[str] = Field(
        default=None,
        max_length=24,
        description="SIMPLE IRA age 60-63 catch-up, IRC §414(v)(2)(E)(ii) (tax years 2025 onward).",
    )


class W2ReconciliationRequest(BaseModel):
    tax_year: int = Field(..., ge=2000, le=2099)
    employees: list[EmployeePayrollRequest] = Field(default_factory=list, max_length=10000)
    w2_drafts: list[EmployeeW2DraftRequest] = Field(default_factory=list, max_length=10000)
    form_941_quarters: list[Form941QuarterRequest] = Field(default_factory=list, max_length=4)
    tolerance: str = Field(default="1.00", max_length=12)
    # Sprint 793a: optional per-request statutory limits. Omit for engine defaults.
    statutory_limits: Optional[StatutoryLimitOverrides] = Field(
        default=None,
        description=(
            "Override the statutory limits for this run. Limits are selected by tax year; a "
            "year with no table is refused unless all eleven required limits are supplied. For "
            "a tabulated year, omitted fields keep that year's figure. Catch-up limits are "
            "optional; a check whose limit is missing is reported in checks_not_run."
        ),
    )
    # Sprint 787b: optional engagement link so a run lands in the workpaper trail.
    engagement_id: Optional[int] = Field(None, description="Optional engagement to link this run to")


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

    def _optional_decimal(label: str, raw: Optional[str]) -> Optional[Decimal]:
        return None if raw is None or not raw.strip() else _to_decimal(label, raw)

    form_941 = [
        Form941Quarter(
            quarter=q.quarter,
            total_federal_wages=_optional_decimal("941 fed wages", q.total_federal_wages),
            total_federal_withholding=_optional_decimal("941 fed withholding", q.total_federal_withholding),
            total_ss_wages=_optional_decimal("941 ss wages", q.total_ss_wages),
            total_medicare_wages=_optional_decimal("941 medicare wages", q.total_medicare_wages),
        )
        for q in payload.form_941_quarters
    ]
    # Sprint 793a: forward only the limits the caller actually supplied, so an
    # omitted field keeps the engine's dataclass default rather than being
    # overwritten with None.
    overrides: dict[str, Decimal] = {}
    if payload.statutory_limits is not None:
        for field_name, raw in payload.statutory_limits.model_dump().items():
            if raw is not None:
                overrides[field_name] = _to_decimal(field_name, raw)

    return W2ReconciliationConfig(
        tax_year=payload.tax_year,
        employees=employees,
        w2_drafts=w2_drafts,
        form_941_quarters=form_941,
        tolerance=_to_decimal("tolerance", payload.tolerance),
        **overrides,
    )


class W2SupportedYearsResponse(BaseModel):
    """Tax years the app can reconcile without a statutory-limits override."""

    tax_years: list[int]
    note: str


@router.get("/audit/w2-reconciliation/supported-years", response_model=W2SupportedYearsResponse)
def get_supported_tax_years() -> W2SupportedYearsResponse:
    """Tax years with a built-in statutory limit table (Sprint 839).

    Read-only reference data, so public like the benchmark lists. The web form
    cannot send ``statutory_limits``, so these are the only years it can run;
    the page reads them here instead of hard-coding them.
    """
    return W2SupportedYearsResponse(
        tax_years=sorted(STATUTORY_LIMITS_BY_YEAR),
        note=(
            "Each year's wage base and contribution limits are built in only after the figures are "
            "confirmed. Other years are refused rather than reconciled with another year's limits."
        ),
    )


@router.post("/audit/w2-reconciliation")
@limiter.limit(RATE_LIMIT_AUDIT)
def run_reconciliation(
    request: Request,
    payload: W2ReconciliationRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict:
    # Sprint 689d: gate promoted tool at tier + upload-limit level;
    # Sprint 787b: run recorded on the engagement workpaper trail (success
    # synchronously, before the response). Sprint 819: the sequence lives in
    # shared/testing_route.py::run_json_tool.
    result = run_json_tool(
        db=db,
        current_user=current_user,
        tool_name="w2_reconciliation",
        engagement_id=payload.engagement_id,
        compute=lambda: reconcile_w2(_build_config(payload)),
        input_errors=(W2ReconciliationInputError,),
        error_key="w2_reconciliation_error",
        route_logger=logger,
        failure_log="W-2 reconciliation failed",
    )
    return result.to_dict()


@router.post("/audit/w2-reconciliation/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_reconciliation_csv(
    request: Request,
    payload: W2ReconciliationRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> Response:
    # Sprint 689d: gate promoted tool (export mirrors analyze-route gating).
    enforce_tool_access(current_user, "w2_reconciliation", db)

    try:
        result = reconcile_w2(_build_config(payload))
    except W2ReconciliationInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ArithmeticError:
        # Sprint 827: a huge-but-finite amount ("1e400") passes parsing, then
        # quantize() raises InvalidOperation — an input problem, not a 500.
        raise HTTPException(status_code=400, detail="An amount is too large to process.")

    buffer = io.StringIO()
    writer = safe_csv_writer(buffer)

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
    # Sprint 838: employee IDs and names are caller-supplied, and messages
    # interpolate them -- every text cell is neutralised against formula
    # injection (CWE-1236), not just the "Checks Not Run" IDs. Amounts are
    # engine-computed Decimals and stay numeric (a leading "-" is a sign).
    for d in result.employee_discrepancies:
        writer.writerow(
            [
                sanitize_csv_value(d.employee_id),
                sanitize_csv_value(d.employee_name),
                d.kind.value,
                d.severity.value,
                str(d.expected),
                str(d.actual),
                str(d.difference),
                sanitize_csv_value(d.message),
            ]
        )

    writer.writerow([])
    writer.writerow(["Form 941 Mismatches"])
    writer.writerow(["Quarter", "Compared With", "Kind", "Severity", "Expected", "Actual", "Difference", "Message"])
    for m in result.form_941_mismatches:
        writer.writerow(
            [
                m.quarter if m.quarter is not None else "ALL",
                "W-3" if m.compared_with == "w3" else "Payroll YTD",
                m.kind.value,
                m.severity.value,
                str(m.expected),
                str(m.actual),
                str(m.difference),
                sanitize_csv_value(m.message),
            ]
        )

    writer.writerow([])
    writer.writerow(["W-3 Totals"])
    w3 = result.w3_totals
    if w3 is None:
        # Sprint 855 (W8): no drafts, no W-3 — not a row of zeros.
        writer.writerow([result.summary["w3_status"]])
    else:
        writer.writerow(["Employee Count", w3.employee_count])
        writer.writerow(["Total Federal Wages", str(w3.total_federal_wages)])
        writer.writerow(["Total Federal Withholding", str(w3.total_federal_withholding)])
        writer.writerow(["Total SS Wages", str(w3.total_ss_wages)])
        writer.writerow(["Total SS Tax Withheld", str(w3.total_ss_tax_withheld)])
        writer.writerow(["Total Medicare Wages", str(w3.total_medicare_wages)])
        writer.writerow(["Total Medicare Tax Withheld", str(w3.total_medicare_tax_withheld)])

    # Sprint 826 (W1/W2): the export must carry the same "not run" disclosure as
    # the screen, or a workpaper built from it would read as fully checked.
    if result.checks_not_run:
        writer.writerow([])
        writer.writerow(["Checks Not Run"])
        writer.writerow(["Check", "Reason", "Employee IDs", "Message"])
        for notice in result.checks_not_run:
            # Employee IDs are caller-supplied: neutralise a leading formula
            # trigger (CWE-1236) before they reach a spreadsheet.
            employee_ids = " ".join(sanitize_csv_value(i) for i in notice["employee_ids"])
            writer.writerow([notice["check"], notice["reason"], employee_ids, sanitize_csv_value(notice["message"])])

    buffer.seek(0)
    return attachment_response(
        buffer.getvalue(), f"w2_reconciliation_{result.tax_year}.csv", MEDIA_CSV, quote_filename=False
    )
