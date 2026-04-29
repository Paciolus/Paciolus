"""
Paciolus API — Diagnostic Export Routes (PDF, Excel, CSV TB, CSV Anomalies, Lead Sheets, Financial Statements).
Sprint 155: Extracted from routes/export.py.
Sprint 725: 6 CSV endpoints collapsed onto shared.csv_export.diagnostic_csv_export.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from security_utils import log_secure_operation

logger = logging.getLogger(__name__)
from fastapi.responses import StreamingResponse

from auth import require_verified_user
from database import get_db
from excel_generator import generate_financial_statements_excel, generate_workpaper
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
from financial_statement_builder import FinancialStatementBuilder
from flux_engine import FluxItem, FluxResult
from leadsheet_generator import generate_leadsheets
from models import User
from pdf_generator import generate_audit_report, generate_financial_statements_pdf
from recon_engine import ReconResult, ReconScore
from shared.entitlement_checks import check_export_access
from shared.error_messages import sanitize_error
from shared.export_helpers import streaming_excel_response, streaming_pdf_response
from shared.export_schemas import (
    AccrualCompletenessCSVInput,
    ExpenseCategoryCSVInput,
    FinancialStatementsInput,
    LeadSheetInput,
    PopulationProfileCSVInput,
    PreFlightCSVInput,
)
from shared.filenames import safe_download_filename
from shared.helpers import (
    try_parse_risk,
    try_parse_risk_band,
)
from shared.pdf_branding import apply_pdf_branding, load_pdf_branding_context
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

    Sprint 679 (completion): Enterprise branding layered on via ContextVar.
    """
    log_secure_operation("pdf_export_start", f"Generating PDF report for: {audit_result.filename}")

    try:
        result_dict = audit_result.model_dump()

        branding = load_pdf_branding_context(current_user, db)
        with apply_pdf_branding(branding):
            pdf_bytes = generate_audit_report(
                result_dict,
                audit_result.filename,
                prepared_by=audit_result.prepared_by,
                reviewed_by=audit_result.reviewed_by,
                workpaper_date=audit_result.workpaper_date,
                include_signoff=audit_result.include_signoff,
            )

        download_filename = safe_download_filename(audit_result.filename or "TrialBalance", "Diagnostic", "pdf")

        log_secure_operation(
            "pdf_export_complete", f"PDF generated: {len(pdf_bytes)} bytes, filename: {download_filename}"
        )

        return streaming_pdf_response(pdf_bytes, download_filename)

    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("PDF export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "pdf_export_error"))


# --- Excel Export ---


@router.post("/export/excel", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_excel_workpaper(
    request: Request, audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)
) -> StreamingResponse:
    """Generate and stream an Excel workpaper."""
    log_secure_operation("excel_export_start", f"Generating Excel workpaper for: {audit_result.filename}")

    try:
        result_dict = audit_result.model_dump()

        excel_bytes = generate_workpaper(
            result_dict,
            audit_result.filename,
            prepared_by=audit_result.prepared_by,
            reviewed_by=audit_result.reviewed_by,
            workpaper_date=audit_result.workpaper_date,
            include_signoff=audit_result.include_signoff,
        )

        download_filename = safe_download_filename(audit_result.filename or "TrialBalance", "Workpaper", "xlsx")

        log_secure_operation(
            "excel_export_complete", f"Excel generated: {len(excel_bytes)} bytes, filename: {download_filename}"
        )

        return streaming_excel_response(excel_bytes, download_filename)

    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Excel export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "excel_export_error"))


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
    """Generate Excel Lead Sheets from analysis result."""
    log_secure_operation("leadsheet_export", f"Exporting lead sheets for {len(payload.flux.items)} items")

    try:
        flux_items = []
        for i in payload.flux.items:
            flux_items.append(
                FluxItem(
                    account_name=i.account,
                    account_type=i.type,
                    current_balance=i.current,
                    prior_balance=i.prior,
                    delta_amount=i.delta_amount,
                    delta_percent=i.delta_percent if i.delta_percent is not None else 0.0,
                    is_new_account=i.is_new,
                    is_removed_account=i.is_removed,
                    has_sign_flip=i.sign_flip,
                    risk_level=try_parse_risk(i.risk_level),
                    variance_indicators=i.variance_indicators,
                )
            )

        flux_result = FluxResult(
            items=flux_items,
            total_items=payload.flux.summary.total_items,
            high_risk_count=payload.flux.summary.high_risk_count,
            medium_risk_count=payload.flux.summary.medium_risk_count,
            new_accounts_count=payload.flux.summary.new_accounts,
            removed_accounts_count=payload.flux.summary.removed_accounts,
            materiality_threshold=payload.flux.summary.threshold,
        )

        recon_scores = []
        for s in payload.recon.scores:
            recon_scores.append(
                ReconScore(
                    account_name=s.account,
                    risk_score=s.score,
                    risk_band=try_parse_risk_band(s.band),
                    factors=s.factors,
                    suggested_action=s.action,
                )
            )

        recon_result = ReconResult(
            scores=recon_scores,
            high_risk_count=payload.recon.stats.high,
            medium_risk_count=payload.recon.stats.medium,
            low_risk_count=payload.recon.stats.low,
        )

        excel_bytes = generate_leadsheets(flux_result, recon_result, payload.filename)

        download_filename = safe_download_filename(payload.filename, "LeadSheets", "xlsx")

        log_secure_operation("leadsheet_generated", f"Generated {len(excel_bytes)} bytes")

        return streaming_excel_response(excel_bytes, download_filename)

    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Lead sheet export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "leadsheet_error"))


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

    Sprint 679 (completion): PDF path applies Enterprise branding via
    ContextVar. Excel path is unaffected — branding lives in PDF chrome.
    """
    log_secure_operation(
        "financial_statements_export_start", f"Generating {format} financial statements for: {payload.filename}"
    )

    # Validate input
    summaries = payload.lead_sheet_grouping.get("summaries", [])
    if not summaries:
        raise HTTPException(status_code=400, detail="lead_sheet_grouping must contain non-empty 'summaries' list")

    try:
        builder = FinancialStatementBuilder(
            payload.lead_sheet_grouping,
            entity_name=payload.entity_name or "",
            period_end=payload.period_end or "",
            prior_lead_sheet_grouping=payload.prior_lead_sheet_grouping,
        )
        statements = builder.build()

        if format == "excel":
            file_bytes = generate_financial_statements_excel(
                statements,
                prepared_by=payload.prepared_by,
                reviewed_by=payload.reviewed_by,
                workpaper_date=payload.workpaper_date,
                include_signoff=payload.include_signoff,
            )
            download_filename = safe_download_filename(payload.filename or "FinancialStatements", "FinStmts", "xlsx")
            return streaming_excel_response(file_bytes, download_filename)
        else:
            branding = load_pdf_branding_context(current_user, db)
            with apply_pdf_branding(branding):
                file_bytes = generate_financial_statements_pdf(
                    statements,
                    prepared_by=payload.prepared_by,
                    reviewed_by=payload.reviewed_by,
                    workpaper_date=payload.workpaper_date,
                    include_signoff=payload.include_signoff,
                )
            download_filename = safe_download_filename(payload.filename or "FinancialStatements", "FinStmts", "pdf")

        log_secure_operation(
            "financial_statements_export_complete", f"Financial statements {format} generated: {len(file_bytes)} bytes"
        )

        return streaming_pdf_response(file_bytes, download_filename)

    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Financial statements export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "financial_statements_export_error"))


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
