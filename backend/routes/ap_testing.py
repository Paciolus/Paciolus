"""
Paciolus API — AP Testing Routes
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request

from security_utils import log_secure_operation, clear_memory
from models import User
from auth import require_verified_user
from ap_testing_engine import run_ap_testing
from shared.helpers import validate_file_size, parse_uploaded_file, parse_json_mapping
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT

router = APIRouter(tags=["ap_testing"])


@router.post("/audit/ap-payments")
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_ap_payments(
    request: Request,
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(default=None),
    current_user: User = Depends(require_verified_user),
):
    """Run automated AP payment testing on an accounts payable extract."""
    column_mapping_dict = parse_json_mapping(column_mapping, "ap_testing")

    log_secure_operation(
        "ap_testing_upload",
        f"Processing AP file: {file.filename}"
    )

    try:
        file_bytes = await validate_file_size(file)
        column_names, rows = parse_uploaded_file(file_bytes, file.filename or "")
        del file_bytes

        result = run_ap_testing(
            rows=rows,
            column_names=column_names,
            config=None,
            column_mapping=column_mapping_dict,
        )

        del rows
        clear_memory()

        return result.to_dict()

    except Exception as e:
        log_secure_operation("ap_testing_error", str(e))
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process AP file: {str(e)}"
        )
