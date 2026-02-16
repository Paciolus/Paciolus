"""
Paciolus API — Multi-Period TB Comparison Routes
"""
import logging
from datetime import datetime, UTC
from typing import Optional, List

logger = logging.getLogger(__name__)

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
from models import User
from auth import require_verified_user
from shared.error_messages import sanitize_error
from multi_period_comparison import (
    compare_trial_balances,
    compare_three_periods,
    export_movements_csv,
)
from shared.helpers import maybe_record_tool_run
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT, RATE_LIMIT_EXPORT
from shared.diagnostic_response_schemas import (
    MovementSummaryResponse,
    ThreeWayMovementSummaryResponse,
)

router = APIRouter(tags=["multi_period"])


class AccountEntry(BaseModel):
    """Single account entry in a trial balance."""
    account: str = Field(..., min_length=1, max_length=500)
    debit: float = Field(0.0, ge=0)
    credit: float = Field(0.0, ge=0)
    type: str = "unknown"


class ComparePeriodAccountsRequest(BaseModel):
    """Request to compare two trial balance datasets at the account level."""
    prior_accounts: List[dict] = Field(..., description="Prior period account list")
    current_accounts: List[dict] = Field(..., description="Current period account list")
    prior_label: str = Field("Prior Period", min_length=1, max_length=100, description="Label for prior period")
    current_label: str = Field("Current Period", min_length=1, max_length=100, description="Label for current period")
    materiality_threshold: float = Field(0.0, ge=0, description="Materiality threshold in dollars")
    engagement_id: Optional[int] = Field(None, description="Optional engagement to link this run to")


class ThreeWayComparisonRequest(BaseModel):
    """Request to compare three trial balance datasets (prior + current + budget)."""
    prior_accounts: List[dict] = Field(..., description="Prior period account list")
    current_accounts: List[dict] = Field(..., description="Current period account list")
    budget_accounts: List[dict] = Field(..., description="Budget/forecast account list")
    prior_label: str = Field("Prior Year", min_length=1, max_length=100, description="Label for prior period")
    current_label: str = Field("Current Year", min_length=1, max_length=100, description="Label for current period")
    budget_label: str = Field("Budget", min_length=1, max_length=100, description="Label for budget/forecast")
    materiality_threshold: float = Field(0.0, ge=0, description="Materiality threshold in dollars")
    engagement_id: Optional[int] = Field(None, description="Optional engagement to link this run to")


class MovementExportRequest(BaseModel):
    """Request to export movement comparison as CSV."""
    prior_accounts: List[dict] = Field(..., description="Prior period account list")
    current_accounts: List[dict] = Field(..., description="Current period account list")
    budget_accounts: Optional[List[dict]] = Field(None, description="Optional budget account list")
    prior_label: str = Field("Prior Period", min_length=1, max_length=100, description="Label for prior period")
    current_label: str = Field("Current Period", min_length=1, max_length=100, description="Label for current period")
    budget_label: str = Field("Budget", min_length=1, max_length=100, description="Label for budget/forecast")
    materiality_threshold: float = Field(0.0, ge=0, description="Materiality threshold in dollars")


@router.post("/audit/compare-periods", response_model=MovementSummaryResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
def compare_period_trial_balances(
    request: Request,
    payload: ComparePeriodAccountsRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Compare two trial balance datasets at the account level."""
    log_secure_operation(
        "compare_period_trial_balances",
        f"User {current_user.id} comparing {len(payload.prior_accounts)} vs {len(payload.current_accounts)} accounts"
    )

    result = compare_trial_balances(
        prior_accounts=payload.prior_accounts,
        current_accounts=payload.current_accounts,
        prior_label=payload.prior_label,
        current_label=payload.current_label,
        materiality_threshold=payload.materiality_threshold,
    )

    background_tasks.add_task(maybe_record_tool_run, db, payload.engagement_id, current_user.id, "multi_period", True)

    return result.to_dict()


@router.post("/audit/compare-three-way", response_model=ThreeWayMovementSummaryResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
def compare_three_way_trial_balances(
    request: Request,
    payload: ThreeWayComparisonRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Compare three trial balance datasets: Prior vs Current vs Budget/Forecast."""
    log_secure_operation(
        "compare_three_way_trial_balances",
        f"User {current_user.id} three-way: {len(payload.prior_accounts)} vs "
        f"{len(payload.current_accounts)} vs {len(payload.budget_accounts)} accounts"
    )

    result = compare_three_periods(
        prior_accounts=payload.prior_accounts,
        current_accounts=payload.current_accounts,
        budget_accounts=payload.budget_accounts,
        prior_label=payload.prior_label,
        current_label=payload.current_label,
        budget_label=payload.budget_label,
        materiality_threshold=payload.materiality_threshold,
    )

    background_tasks.add_task(maybe_record_tool_run, db, payload.engagement_id, current_user.id, "multi_period", True)

    return result.to_dict()


@router.post("/export/csv/movements")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_movements(
    request: Request,
    payload: MovementExportRequest = ...,
    current_user: User = Depends(require_verified_user),
):
    """Export movement comparison data as CSV."""
    log_secure_operation(
        "csv_movements_export_start",
        f"User {current_user.id} exporting movements CSV"
    )

    try:
        has_budget = payload.budget_accounts is not None and len(payload.budget_accounts) > 0

        if has_budget:
            three_way = compare_three_periods(
                prior_accounts=payload.prior_accounts,
                current_accounts=payload.current_accounts,
                budget_accounts=payload.budget_accounts,
                prior_label=payload.prior_label,
                current_label=payload.current_label,
                budget_label=payload.budget_label,
                materiality_threshold=payload.materiality_threshold,
            )
            csv_content = export_movements_csv(
                three_way,
                include_budget=True,
                budget_data=True,
            )
        else:
            two_way = compare_trial_balances(
                prior_accounts=payload.prior_accounts,
                current_accounts=payload.current_accounts,
                prior_label=payload.prior_label,
                current_label=payload.current_label,
                materiality_threshold=payload.materiality_threshold,
            )
            csv_content = export_movements_csv(two_way)

        csv_bytes = csv_content.encode("utf-8-sig")

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        download_filename = f"Movement_Comparison_{timestamp}.csv"

        log_secure_operation(
            "csv_movements_export_complete",
            f"CSV movements generated: {len(csv_bytes)} bytes"
        )

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            },
        )

    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Multi-period CSV movements export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "csv_movements_export_error")
        )
