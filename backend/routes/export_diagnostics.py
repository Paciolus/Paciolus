"""
Paciolus API — Diagnostic Export Routes (PDF, Excel, CSV TB, CSV Anomalies, Lead Sheets, Financial Statements).
Sprint 155: Extracted from routes/export.py.
Sprint 725: 6 CSV endpoints collapsed onto shared.csv_export.diagnostic_csv_export.
Sprint 748a: 6 CSV routes migrated to delegate to export.pipeline.
Sprint 748b: PDF/Excel/Leadsheets/FinancialStatements routes migrated.
"""

import logging

from fastapi import APIRouter, Depends, Query, Request

logger = logging.getLogger(__name__)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from export.pipeline import (
    export_csv_accrual_completeness as pipeline_export_csv_accrual_completeness,
)
from export.pipeline import (
    export_csv_anomalies as pipeline_export_csv_anomalies,
)
from export.pipeline import (
    export_csv_expense_category as pipeline_export_csv_expense_category,
)
from export.pipeline import (
    export_csv_population_profile as pipeline_export_csv_population_profile,
)
from export.pipeline import (
    export_csv_preflight_issues as pipeline_export_csv_preflight_issues,
)
from export.pipeline import (
    export_csv_trial_balance as pipeline_export_csv_trial_balance,
)
from export.pipeline import (
    export_diagnostic_excel as pipeline_export_diagnostic_excel,
)
from export.pipeline import (
    export_diagnostic_pdf as pipeline_export_diagnostic_pdf,
)
from export.pipeline import (
    export_financial_statements as pipeline_export_financial_statements,
)
from export.pipeline import (
    export_leadsheets as pipeline_export_leadsheets,
)
from models import User
from shared.entitlement_checks import check_export_access
from shared.export_schemas import (
    AccrualCompletenessCSVInput,
    ExpenseCategoryCSVInput,
    FinancialStatementsInput,
    LeadSheetInput,
    PopulationProfileCSVInput,
    PreFlightCSVInput,
)
from shared.pdf_branding import load_pdf_branding_context
from shared.rate_limits import RATE_LIMIT_EXPORT, limiter
from shared.schemas import AuditResultInput

router = APIRouter(tags=["export"])


# --- PDF Export ---


@router.post("/export/pdf", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_pdf_report(
    request: Request,
    audit_result: AuditResultInput,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Generate and stream a PDF audit report.

    Sprint 679: Enterprise branding via ContextVar.
    Sprint 748b: delegates to ``export.pipeline`` with branding plumbed through.
    """
    branding = load_pdf_branding_context(current_user, db)
    return pipeline_export_diagnostic_pdf(audit_result, branding=branding)


# --- Excel Export ---


@router.post("/export/excel", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_excel_workpaper(
    request: Request, audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)
) -> StreamingResponse:
    """Generate and stream an Excel workpaper.

    Sprint 748b: delegates to ``export.pipeline``. No branding —
    Excel exports don't apply Enterprise PDF branding.
    """
    return pipeline_export_diagnostic_excel(audit_result)


# --- CSV Trial Balance ---


@router.post("/export/csv/trial-balance", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_trial_balance(
    request: Request, audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)
) -> StreamingResponse:
    """Export trial balance data as CSV."""
    return pipeline_export_csv_trial_balance(audit_result)


# --- CSV Anomalies ---


@router.post("/export/csv/anomalies", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_anomalies(
    request: Request, audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)
) -> StreamingResponse:
    """Export anomaly list as CSV."""
    return pipeline_export_csv_anomalies(audit_result)


# --- Lead Sheet Export ---


@router.post("/export/leadsheets", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_leadsheets(
    request: Request, payload: LeadSheetInput, current_user: User = Depends(require_verified_user)
) -> StreamingResponse:
    """Generate Excel Lead Sheets from analysis result.

    Sprint 748b: delegates to ``export.pipeline``. The flux/recon
    domain-object assembly previously inline here lives in
    ``export.serializers.excel.serialize_leadsheets_excel``.
    """
    return pipeline_export_leadsheets(payload)


# --- Financial Statements Export ---


@router.post("/export/financial-statements", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_financial_statements(
    request: Request,
    payload: FinancialStatementsInput,
    format: str = Query(default="pdf", pattern="^(pdf|excel)$"),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Generate and download financial statements as PDF or Excel.

    Sprint 679: PDF path applies Enterprise branding via ContextVar.
    Sprint 748b: delegates to ``export.pipeline``. PDF path passes the
    branding context through; Excel path ignores it.
    """
    branding = load_pdf_branding_context(current_user, db) if format == "pdf" else None
    return pipeline_export_financial_statements(payload, fmt=format, branding=branding)


# --- Pre-Flight Issues CSV (Sprint 283) ---


@router.post("/export/csv/preflight-issues", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_preflight_issues(
    request: Request,
    pf_input: PreFlightCSVInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export pre-flight quality issues as CSV."""
    return pipeline_export_csv_preflight_issues(pf_input)


# --- Population Profile CSV (Sprint 287) ---


@router.post("/export/csv/population-profile", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_population_profile(
    request: Request,
    pp_input: PopulationProfileCSVInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export population profile data as CSV."""
    return pipeline_export_csv_population_profile(pp_input)


# --- Expense Category CSV (Sprint 289) ---


@router.post("/export/csv/expense-category-analytics", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_expense_category(
    request: Request,
    ec_input: ExpenseCategoryCSVInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export expense category analytics data as CSV."""
    return pipeline_export_csv_expense_category(ec_input)


# --- Accrual Completeness CSV (Sprint 290) ---


@router.post("/export/csv/accrual-completeness", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_accrual_completeness(
    request: Request,
    ac_input: AccrualCompletenessCSVInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export accrual completeness data as CSV."""
    return pipeline_export_csv_accrual_completeness(ac_input)
