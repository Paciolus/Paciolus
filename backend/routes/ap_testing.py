"""
Paciolus API — AP Testing Routes
"""
import io
import json
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request

from security_utils import log_secure_operation, clear_memory
from models import User
from auth import require_verified_user
from ap_testing_engine import run_ap_testing
from shared.helpers import validate_file_size
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
    column_mapping_dict: Optional[dict[str, str]] = None
    if column_mapping:
        try:
            column_mapping_dict = json.loads(column_mapping)
            log_secure_operation(
                "ap_testing_column_mapping",
                f"Received AP column mapping: {list(column_mapping_dict.keys())}"
            )
        except json.JSONDecodeError:
            log_secure_operation("ap_testing_column_mapping_error", "Invalid JSON in column_mapping")

    log_secure_operation(
        "ap_testing_upload",
        f"Processing AP file: {file.filename}"
    )

    try:
        file_bytes = await validate_file_size(file)

        filename_lower = (file.filename or "").lower()
        if filename_lower.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))

        column_names = list(df.columns.astype(str))
        rows = df.to_dict('records')

        del file_bytes
        del df

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
