"""
Paciolus API — AP Testing Routes
"""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth import require_verified_user
from ap_testing_engine import run_ap_testing
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT
from shared.testing_route import run_single_file_testing

router = APIRouter(tags=["ap_testing"])


@router.post("/audit/ap-payments")
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_ap_payments(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Run automated AP payment testing on an accounts payable extract."""
    return await run_single_file_testing(
        file=file, column_mapping=column_mapping,
        engagement_id=engagement_id, current_user=current_user, db=db,
        background_tasks=background_tasks,
        tool_name="ap_testing", mapping_key="ap_testing",
        log_label="AP", error_key="ap_testing_error",
        run_engine=lambda rows, cols, mapping, fn: run_ap_testing(
            rows=rows, column_names=cols, config=None, column_mapping=mapping,
        ),
    )
