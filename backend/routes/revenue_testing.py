"""
Paciolus API — Revenue Testing Routes (Sprint 104)
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from sqlalchemy.orm import Session

from security_utils import log_secure_operation, clear_memory
from database import get_db
from models import User
from auth import require_verified_user
from shared.error_messages import sanitize_error
from revenue_testing_engine import run_revenue_testing, RevenueTestingConfig
from shared.helpers import validate_file_size, parse_uploaded_file, parse_json_mapping, maybe_record_tool_run
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT

router = APIRouter(tags=["revenue_testing"])


@router.post("/audit/revenue-testing")
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_revenue(
    request: Request,
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
    column_mapping_dict = parse_json_mapping(column_mapping, "revenue_testing")

    log_secure_operation(
        "revenue_testing_upload",
        f"Processing revenue file: {file.filename}"
    )

    try:
        file_bytes = await validate_file_size(file)
        column_names, rows = parse_uploaded_file(file_bytes, file.filename or "")
        del file_bytes

        config = RevenueTestingConfig(
            prior_period_total=prior_period_total,
            period_start=period_start,
            period_end=period_end,
        )

        result = run_revenue_testing(
            rows=rows,
            column_names=column_names,
            config=config,
            column_mapping=column_mapping_dict,
        )

        del rows
        clear_memory()

        score = result.composite_score.score if hasattr(result, 'composite_score') and result.composite_score else None
        maybe_record_tool_run(db, engagement_id, current_user.id, "revenue_testing", True, score)

        return result.to_dict()

    except Exception as e:
        maybe_record_tool_run(db, engagement_id, current_user.id, "revenue_testing", False)
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "analysis", "revenue_testing_error")
        )
