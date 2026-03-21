"""
Paciolus API — Audit Diagnostic Routes (Preflight, Population, Expense, Accrual)
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from models import User
from security_utils import log_secure_operation
from services.audit.file_tool_scaffold import execute_file_tool
from shared.diagnostic_response_schemas import (
    AccrualCompletenessReportResponse,
    ExpenseCategoryReportResponse,
    PopulationProfileResponse,
    PreFlightReportResponse,
)
from shared.helpers import parse_uploaded_file
from shared.materiality_resolver import resolve_materiality
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audit"])


@router.post("/audit/preflight", response_model=PreFlightReportResponse)
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

    def _analyze(file_bytes: bytes, filename: str) -> dict[str, Any]:
        from preflight_engine import run_preflight

        column_names, rows = parse_uploaded_file(file_bytes, filename)
        report = run_preflight(column_names, rows, filename)
        result = report.to_dict()
        del column_names, rows
        return result

    return await execute_file_tool(  # type: ignore[return-value]
        file,
        "preflight",
        _analyze,
        background_tasks,
        db,
        engagement_id,
        current_user.id,
        "preflight_error",
        composite_score_key="readiness_score",
    )


@router.post("/audit/population-profile", response_model=PopulationProfileResponse)
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

    def _analyze(file_bytes: bytes, filename: str) -> dict[str, Any]:
        from population_profile_engine import run_population_profile

        column_names, rows = parse_uploaded_file(file_bytes, filename)
        report = run_population_profile(column_names, rows, filename)
        result = report.to_dict()
        del column_names, rows
        return result

    return await execute_file_tool(  # type: ignore[return-value]
        file,
        "population_profile",
        _analyze,
        background_tasks,
        db,
        engagement_id,
        current_user.id,
        "population_profile_error",
    )


# --- Expense Category Analytical Procedures (Sprint 289) ---


@router.post("/audit/expense-category-analytics", response_model=ExpenseCategoryReportResponse)
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
    materiality_threshold, _exp_mat_source = resolve_materiality(
        materiality_threshold,
        engagement_id,
        current_user.id,
        db,
    )
    log_secure_operation("expense_category_upload", f"Expense category analytics for file: {file.filename}")

    def _analyze(file_bytes: bytes, filename: str) -> dict[str, Any]:
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

    return await execute_file_tool(  # type: ignore[return-value]
        file,
        "expense_category",
        _analyze,
        background_tasks,
        db,
        engagement_id,
        current_user.id,
        "expense_category_error",
    )


# --- Accrual Completeness Estimator (Sprint 290) ---


@router.post("/audit/accrual-completeness", response_model=AccrualCompletenessReportResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def accrual_completeness_check(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prior_operating_expenses: Optional[float] = Form(default=None),
    threshold_pct: float = Form(default=50.0),
    total_revenue: Optional[float] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> AccrualCompletenessReportResponse:
    """Compute accrual completeness estimator for a trial balance file."""
    log_secure_operation("accrual_completeness_upload", f"Accrual completeness check for file: {file.filename}")

    def _analyze(file_bytes: bytes, filename: str) -> dict[str, Any]:
        from accrual_completeness_engine import run_accrual_completeness

        column_names, rows = parse_uploaded_file(file_bytes, filename)
        report = run_accrual_completeness(
            column_names,
            rows,
            filename,
            prior_operating_expenses=prior_operating_expenses,
            threshold_pct=threshold_pct,
            total_revenue=total_revenue,
        )
        result = report.to_dict()
        del column_names, rows
        return result

    return await execute_file_tool(  # type: ignore[return-value]
        file,
        "accrual_completeness",
        _analyze,
        background_tasks,
        db,
        engagement_id,
        current_user.id,
        "accrual_completeness_error",
    )
