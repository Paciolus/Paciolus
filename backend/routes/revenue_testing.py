"""
Paciolus API — Revenue Testing Routes (Sprint 104)
"""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth import require_verified_user
from revenue_testing_engine import run_revenue_testing, RevenueTestingConfig
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT
from shared.testing_route import run_single_file_testing
from shared.testing_response_schemas import RevenueTestingResponse

router = APIRouter(tags=["revenue_testing"])


@router.post("/audit/revenue-testing", response_model=RevenueTestingResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_revenue(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    prior_period_total: Optional[float] = Form(default=None),
    period_start: Optional[str] = Form(default=None),
    period_end: Optional[str] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Run automated revenue recognition testing on a revenue GL extract.

    ISA 240: Presumed fraud risk in revenue recognition.
    """
    config = RevenueTestingConfig(
        prior_period_total=prior_period_total,
        period_start=period_start,
        period_end=period_end,
    )

    return await run_single_file_testing(
        file=file, column_mapping=column_mapping,
        engagement_id=engagement_id, current_user=current_user, db=db,
        background_tasks=background_tasks,
        tool_name="revenue_testing", mapping_key="revenue_testing",
        log_label="revenue", error_key="revenue_testing_error",
        run_engine=lambda rows, cols, mapping, fn: run_revenue_testing(
            rows=rows, column_names=cols, config=config, column_mapping=mapping,
        ),
    )
