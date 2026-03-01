"""
Paciolus API — Core Audit Routes (Inspect, Trial Balance, Flux)
"""

import asyncio
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from audit_engine import (
    DEFAULT_CHUNK_SIZE,
    audit_trial_balance_multi_sheet,
    audit_trial_balance_streaming,
)
from auth import require_verified_user
from currency_engine import convert_trial_balance
from database import get_db
from flux_engine import FluxEngine
from lead_sheet_mapping import group_by_lead_sheet, lead_sheet_grouping_to_dict
from models import User
from recon_engine import ReconEngine
from routes.currency import get_user_rate_table
from security_utils import log_secure_operation
from shared.account_extractors import extract_flux_accounts, extract_tb_accounts
from shared.diagnostic_response_schemas import (
    AccrualCompletenessReportResponse,
    ExpenseCategoryReportResponse,
    FluxAnalysisResponse,
    PopulationProfileResponse,
    PreFlightReportResponse,
    TrialBalanceResponse,
)
from shared.entitlement_checks import check_diagnostic_limit
from shared.error_messages import sanitize_error
from shared.helpers import (
    maybe_record_tool_run,
    memory_cleanup,
    parse_json_list,
    parse_json_mapping,
    parse_uploaded_file,
    validate_file_size,
)
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from workbook_inspector import inspect_workbook, is_excel_file

router = APIRouter(tags=["audit"])


class SheetInfo(BaseModel):
    name: str
    row_count: int
    column_count: int
    columns: list
    has_data: bool


class WorkbookInspectResponse(BaseModel):
    filename: str
    sheet_count: int
    sheets: list[SheetInfo]
    total_rows: int
    is_multi_sheet: bool
    format: str
    requires_sheet_selection: bool


# FluxAnalysisResponse moved to shared.diagnostic_response_schemas


@router.post("/audit/inspect-workbook", response_model=WorkbookInspectResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def inspect_workbook_endpoint(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_verified_user),
) -> WorkbookInspectResponse:
    """Inspect an Excel workbook to retrieve sheet metadata."""
    log_secure_operation("inspect_workbook_upload", f"Inspecting workbook: {file.filename}")

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            if not is_excel_file(filename):
                return {
                    "filename": file.filename,
                    "sheet_count": 1,
                    "sheets": [
                        {"name": "Sheet1", "row_count": -1, "column_count": -1, "columns": [], "has_data": True}
                    ],
                    "total_rows": -1,
                    "is_multi_sheet": False,
                    "format": "csv",
                    "requires_sheet_selection": False,
                }

            def _inspect() -> dict[str, Any]:
                workbook_info = inspect_workbook(file_bytes, filename)
                result = workbook_info.to_dict()
                result["requires_sheet_selection"] = workbook_info.is_multi_sheet
                return result

            result = await asyncio.to_thread(_inspect)

            return result

        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(
                    e,
                    "upload",
                    "inspect_workbook_error",
                ),
            )
        except (KeyError, TypeError, OSError) as e:
            logger.exception("Workbook inspection failed")
            raise HTTPException(status_code=400, detail=sanitize_error(e, "upload", "inspect_workbook_error"))


class PdfPreviewResponse(BaseModel):
    filename: str
    page_count: int
    tables_found: int
    extraction_confidence: float
    header_confidence: float
    numeric_density: float
    row_consistency: float
    column_names: list[str]
    sample_rows: list[dict[str, str]]
    remediation_hints: list[str]
    passes_quality_gate: bool


@router.post("/audit/preview-pdf", response_model=PdfPreviewResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def preview_pdf_endpoint(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_verified_user),
) -> PdfPreviewResponse:
    """Preview PDF table extraction with quality metrics before full parse."""
    from shared.pdf_parser import CONFIDENCE_THRESHOLD, PREVIEW_PAGE_LIMIT, extract_pdf_tables

    log_secure_operation(
        "preview_pdf_upload",
        f"Previewing PDF: {file.filename}",
    )

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _preview() -> Any:
                return extract_pdf_tables(file_bytes, filename, max_pages=PREVIEW_PAGE_LIMIT)

            result = await asyncio.to_thread(_preview)

            # Build sample rows (first 5) as list of dicts
            sample_rows: list[dict[str, str]] = []
            for row in result.rows[:5]:
                row_dict: dict[str, str] = {}
                for i, col in enumerate(result.column_names):
                    row_dict[col] = row[i] if i < len(row) else ""
                sample_rows.append(row_dict)

            return {
                "filename": filename,
                "page_count": result.metadata.page_count,
                "tables_found": result.metadata.tables_found,
                "extraction_confidence": result.metadata.extraction_confidence,
                "header_confidence": result.metadata.header_confidence,
                "numeric_density": result.metadata.numeric_density,
                "row_consistency": result.metadata.row_consistency,
                "column_names": result.column_names,
                "sample_rows": sample_rows,
                "remediation_hints": result.metadata.remediation_hints,
                "passes_quality_gate": result.metadata.extraction_confidence >= CONFIDENCE_THRESHOLD,
            }

        except (ValueError, OSError) as e:
            logger.exception("PDF preview failed")
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(e, "upload", "preview_pdf_error"),
            )


@router.post("/audit/preflight", response_model=PreFlightReportResponse, status_code=200)
@limiter.limit(RATE_LIMIT_AUDIT)
async def preflight_check(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> PreFlightReportResponse:
    """Run a lightweight data quality pre-flight assessment on a trial balance file."""
    log_secure_operation("preflight_upload", f"Pre-flight check for file: {file.filename}")

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _analyze() -> dict[str, Any]:
                from preflight_engine import run_preflight

                column_names, rows = parse_uploaded_file(file_bytes, filename)
                report = run_preflight(column_names, rows, filename)
                result = report.to_dict()
                del column_names, rows
                return result

            result = await asyncio.to_thread(_analyze)

            background_tasks.add_task(
                maybe_record_tool_run,
                db,
                engagement_id,
                current_user.id,
                "preflight",
                True,
                composite_score=result.get("readiness_score"),
            )

            return result

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Pre-flight check failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "preflight", False)
            raise HTTPException(status_code=400, detail=sanitize_error(e, "upload", "preflight_error"))


@router.post("/audit/population-profile", response_model=PopulationProfileResponse, status_code=200)
@limiter.limit(RATE_LIMIT_AUDIT)
async def population_profile_check(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> PopulationProfileResponse:
    """Compute population profile statistics for a trial balance file."""
    log_secure_operation("population_profile_upload", f"Population profile for file: {file.filename}")

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _analyze() -> dict[str, Any]:
                from population_profile_engine import run_population_profile

                column_names, rows = parse_uploaded_file(file_bytes, filename)
                report = run_population_profile(column_names, rows, filename)
                result = report.to_dict()
                del column_names, rows
                return result

            result = await asyncio.to_thread(_analyze)

            background_tasks.add_task(
                maybe_record_tool_run,
                db,
                engagement_id,
                current_user.id,
                "population_profile",
                True,
            )

            return result

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Population profile check failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "population_profile", False)
            raise HTTPException(status_code=400, detail=sanitize_error(e, "upload", "population_profile_error"))


# --- Expense Category Analytical Procedures (Sprint 289) ---


@router.post("/audit/expense-category-analytics", response_model=ExpenseCategoryReportResponse, status_code=200)
@limiter.limit(RATE_LIMIT_AUDIT)
async def expense_category_analytics(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    materiality_threshold: float = Form(default=0.0),
    prior_cogs: Optional[float] = Form(default=None),
    prior_opex: Optional[float] = Form(default=None),
    prior_total_expenses: Optional[float] = Form(default=None),
    prior_revenue: Optional[float] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> ExpenseCategoryReportResponse:
    """Compute expense category analytical procedures for a trial balance file."""
    # Sprint 310: Resolve materiality from engagement cascade if not explicitly set
    materiality_threshold, _exp_mat_source = _resolve_materiality(
        materiality_threshold,
        engagement_id,
        current_user.id,
        db,
    )
    log_secure_operation("expense_category_upload", f"Expense category analytics for file: {file.filename}")

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _analyze() -> dict[str, Any]:
                from expense_category_engine import run_expense_category_analytics

                column_names, rows = parse_uploaded_file(file_bytes, filename)
                report = run_expense_category_analytics(
                    column_names,
                    rows,
                    filename,
                    materiality_threshold=materiality_threshold,
                    prior_cogs=prior_cogs,
                    prior_opex=prior_opex,
                    prior_total_expenses=prior_total_expenses,
                    prior_revenue=prior_revenue,
                )
                result = report.to_dict()
                del column_names, rows
                return result

            result = await asyncio.to_thread(_analyze)

            background_tasks.add_task(
                maybe_record_tool_run,
                db,
                engagement_id,
                current_user.id,
                "expense_category",
                True,
            )

            return result

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Expense category analytics failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "expense_category", False)
            raise HTTPException(status_code=400, detail=sanitize_error(e, "upload", "expense_category_error"))


# --- Accrual Completeness Estimator (Sprint 290) ---


@router.post("/audit/accrual-completeness", response_model=AccrualCompletenessReportResponse, status_code=200)
@limiter.limit(RATE_LIMIT_AUDIT)
async def accrual_completeness_check(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prior_operating_expenses: Optional[float] = Form(default=None),
    threshold_pct: float = Form(default=50.0),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> AccrualCompletenessReportResponse:
    """Compute accrual completeness estimator for a trial balance file."""
    log_secure_operation("accrual_completeness_upload", f"Accrual completeness check for file: {file.filename}")

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _analyze() -> dict[str, Any]:
                from accrual_completeness_engine import run_accrual_completeness

                column_names, rows = parse_uploaded_file(file_bytes, filename)
                report = run_accrual_completeness(
                    column_names,
                    rows,
                    filename,
                    prior_operating_expenses=prior_operating_expenses,
                    threshold_pct=threshold_pct,
                )
                result = report.to_dict()
                del column_names, rows
                return result

            result = await asyncio.to_thread(_analyze)

            background_tasks.add_task(
                maybe_record_tool_run,
                db,
                engagement_id,
                current_user.id,
                "accrual_completeness",
                True,
            )

            return result

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Accrual completeness check failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "accrual_completeness", False)
            raise HTTPException(status_code=400, detail=sanitize_error(e, "upload", "accrual_completeness_error"))


# ---------------------------------------------------------------------------
# Sprint 310: Materiality cascade resolution
# ---------------------------------------------------------------------------


def _resolve_materiality(
    materiality_threshold: float,
    engagement_id: Optional[int],
    user_id: int,
    db: Session,
) -> tuple[float, str]:
    """Resolve effective materiality. Priority: explicit > engagement > default.

    Returns (threshold, source) where source is 'manual', 'engagement', or 'none'.
    """
    if materiality_threshold > 0.0:
        return materiality_threshold, "manual"
    if engagement_id is not None:
        from engagement_manager import EngagementManager

        mgr = EngagementManager(db)
        eng = mgr.get_engagement(user_id, engagement_id)
        if eng and eng.materiality_amount:
            cascade = mgr.compute_materiality(eng)
            pm = cascade.get("performance_materiality", 0.0)
            if pm > 0:
                return pm, "engagement"
    return 0.0, "none"


@router.post("/audit/trial-balance", response_model=TrialBalanceResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_trial_balance(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    materiality_threshold: float = Form(default=0.0, ge=0.0),
    account_type_overrides: Optional[str] = Form(default=None),
    column_mapping: Optional[str] = Form(default=None),
    selected_sheets: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(check_diagnostic_limit),
    _verified: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> TrialBalanceResponse:
    """Analyze a trial balance file for balance validation using streaming processing."""

    overrides_dict: Optional[dict[str, str]] = None
    if account_type_overrides:
        try:
            overrides_dict = json.loads(account_type_overrides)
            log_secure_operation("audit_overrides", f"Received {len(overrides_dict)} account type overrides")
        except json.JSONDecodeError:
            log_secure_operation("audit_overrides_error", "Invalid JSON in overrides, ignoring")

    column_mapping_dict = parse_json_mapping(column_mapping, "audit_column")
    selected_sheets_list = parse_json_list(selected_sheets, "audit_selected_sheets")

    # Sprint 310: Resolve materiality from engagement cascade if not explicitly set
    materiality_threshold, materiality_source = _resolve_materiality(
        materiality_threshold,
        engagement_id,
        current_user.id,
        db,
    )

    log_secure_operation(
        "audit_upload_streaming",
        f"Processing file: {file.filename} (threshold: ${materiality_threshold:,.2f}, source: {materiality_source}, chunk_size: {DEFAULT_CHUNK_SIZE})",
    )

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _analyze() -> dict[str, Any]:
                if selected_sheets_list and len(selected_sheets_list) > 0:
                    result = audit_trial_balance_multi_sheet(
                        file_bytes=file_bytes,
                        filename=filename,
                        selected_sheets=selected_sheets_list,
                        materiality_threshold=materiality_threshold,
                        chunk_size=DEFAULT_CHUNK_SIZE,
                        account_type_overrides=overrides_dict,
                        column_mapping=column_mapping_dict,
                    )
                else:
                    result = audit_trial_balance_streaming(
                        file_bytes=file_bytes,
                        filename=filename,
                        materiality_threshold=materiality_threshold,
                        chunk_size=DEFAULT_CHUNK_SIZE,
                        account_type_overrides=overrides_dict,
                        column_mapping=column_mapping_dict,
                    )

                if "abnormal_balances" in result:
                    accounts_for_grouping = []
                    for ab in result.get("abnormal_balances", []):
                        accounts_for_grouping.append(
                            {
                                "account": ab.get("account", ""),
                                "debit": ab.get("amount", 0) if ab.get("amount", 0) > 0 else 0,
                                "credit": abs(ab.get("amount", 0)) if ab.get("amount", 0) < 0 else 0,
                                "type": ab.get("type", "unknown"),
                                "issue": ab.get("issue", ""),
                                "materiality": ab.get("materiality", ""),
                                "severity": ab.get("severity", "low"),
                                "anomaly_type": ab.get("anomaly_type", "unknown"),
                            }
                        )

                    lead_sheet_grouping = group_by_lead_sheet(accounts_for_grouping)
                    grouping_dict = lead_sheet_grouping_to_dict(lead_sheet_grouping)
                    result["lead_sheet_grouping"] = grouping_dict

                    # Sprint 296: Section density profile
                    if result.get("population_profile") is not None:
                        from population_profile_engine import compute_section_density

                        density = compute_section_density(grouping_dict, materiality_threshold)
                        result["population_profile"]["section_density"] = [s.to_dict() for s in density]

                return result

            result = await asyncio.to_thread(_analyze)

            # Sprint 258: Auto-convert if user has rate table in session
            rate_table = get_user_rate_table(db, current_user.id)
            if rate_table is not None and result.get("accounts"):
                try:
                    conversion = convert_trial_balance(
                        tb_rows=result["accounts"],
                        rate_table=rate_table,
                        amount_column="net_balance"
                        if "net_balance" in (result["accounts"][0] if result["accounts"] else {})
                        else "amount",
                    )
                    result["currency_conversion"] = conversion.to_dict()
                except (ValueError, KeyError, TypeError, AttributeError):
                    logger.warning("Currency conversion failed — returning unconverted results", exc_info=True)

            # Sprint 310: Include materiality source in response
            result["materiality_source"] = materiality_source

            flagged = extract_tb_accounts(result)
            background_tasks.add_task(
                maybe_record_tool_run, db, engagement_id, current_user.id, "trial_balance", True, None, flagged
            )

            return result

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Trial balance analysis failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "trial_balance", False)
            raise HTTPException(status_code=400, detail=sanitize_error(e, "upload", "audit_error"))


@router.post("/audit/flux", response_model=FluxAnalysisResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def flux_analysis(
    request: Request,
    background_tasks: BackgroundTasks,
    current_file: UploadFile = File(...),
    prior_file: UploadFile = File(...),
    materiality: float = Form(0.0),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Perform a Flux (Period-over-Period) Analysis."""
    # Sprint 310: Resolve materiality from engagement cascade if not explicitly set
    materiality, _flux_mat_source = _resolve_materiality(
        materiality,
        engagement_id,
        current_user.id,
        db,
    )
    log_secure_operation("flux_start", f"Starting Flux Analysis for user {current_user.id}")

    with memory_cleanup():
        try:
            content_curr = await validate_file_size(current_file)
            content_prior = await validate_file_size(prior_file)
            curr_filename = current_file.filename
            prior_filename = prior_file.filename

            def _analyze():
                from audit_engine import StreamingAuditor, process_tb_chunked

                current_balances = {}
                auditor_curr = StreamingAuditor(materiality_threshold=materiality)
                for chunk, rows in process_tb_chunked(content_curr, curr_filename, DEFAULT_CHUNK_SIZE):
                    auditor_curr.process_chunk(chunk, rows)
                    del chunk

                classified_curr = auditor_curr.get_classified_accounts()
                for acct, bals in auditor_curr.account_balances.items():
                    net = bals["debit"] - bals["credit"]
                    acct_type = classified_curr.get(acct, "Unknown")
                    current_balances[acct] = {
                        "net": net,
                        "type": acct_type,
                        "debit": bals["debit"],
                        "credit": bals["credit"],
                    }

                auditor_curr.clear()
                del auditor_curr

                prior_balances = {}
                auditor_prior = StreamingAuditor(materiality_threshold=materiality)
                for chunk, rows in process_tb_chunked(content_prior, prior_filename, DEFAULT_CHUNK_SIZE):
                    auditor_prior.process_chunk(chunk, rows)
                    del chunk

                classified_prior = auditor_prior.get_classified_accounts()
                for acct, bals in auditor_prior.account_balances.items():
                    net = bals["debit"] - bals["credit"]
                    acct_type = classified_prior.get(acct, "Unknown")
                    prior_balances[acct] = {
                        "net": net,
                        "type": acct_type,
                        "debit": bals["debit"],
                        "credit": bals["credit"],
                    }

                auditor_prior.clear()
                del auditor_prior

                flux_engine = FluxEngine(materiality_threshold=materiality)
                flux_result = flux_engine.compare(current_balances, prior_balances)

                recon_engine = ReconEngine(materiality_threshold=materiality)
                recon_result = recon_engine.calculate_scores(flux_result)

                return flux_result, recon_result

            flux_result, recon_result = await asyncio.to_thread(_analyze)

            log_secure_operation("flux_complete", f"Flux analysis complete: {len(flux_result.items)} items")

            flux_dict = flux_result.to_dict()
            flagged = extract_flux_accounts({"items": flux_dict.get("items", [])})
            background_tasks.add_task(
                maybe_record_tool_run,
                db,
                engagement_id,
                current_user.id,
                "flux_analysis",
                True,
                None,
                flagged,
            )

            return {"flux": flux_dict, "recon": recon_result.to_dict()}

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Flux analysis failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "flux_analysis", False)
            raise HTTPException(status_code=500, detail=sanitize_error(e, "analysis", "flux_error"))
