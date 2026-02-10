"""
Paciolus API — Payroll Testing Routes
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from sqlalchemy.orm import Session

from security_utils import log_secure_operation, clear_memory
from database import get_db
from models import User
from auth import require_verified_user
from shared.error_messages import sanitize_error
from payroll_testing_engine import run_payroll_testing
from shared.helpers import validate_file_size, parse_uploaded_file, parse_json_mapping, maybe_record_tool_run
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT

router = APIRouter(tags=["payroll_testing"])


@router.post("/audit/payroll-testing")
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_payroll_testing(
    request: Request,
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Run automated payroll & employee testing on a payroll register."""
    column_mapping_dict = parse_json_mapping(column_mapping, "payroll_testing")

    log_secure_operation(
        "payroll_testing_upload",
        f"Processing payroll file: {file.filename}"
    )

    try:
        file_bytes = await validate_file_size(file)
        column_names, rows = parse_uploaded_file(file_bytes, file.filename or "")
        del file_bytes

        result = run_payroll_testing(
            headers=column_names,
            rows=rows,
            config=None,
            column_mapping=column_mapping_dict,
            filename=file.filename or "",
        )

        del rows
        clear_memory()

        score = result.composite_score.score if hasattr(result, 'composite_score') and result.composite_score else None
        maybe_record_tool_run(db, engagement_id, current_user.id, "payroll_testing", True, score)

        return result.to_dict()

    except Exception as e:
        maybe_record_tool_run(db, engagement_id, current_user.id, "payroll_testing", False)
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "analysis", "payroll_testing_error")
        )
