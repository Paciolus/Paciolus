"""
Paciolus API — AR Aging Routes (Sprint 107)

Dual-file upload: TB (required) + optional AR sub-ledger.
TB-only: 4 tests. TB + sub-ledger: all 11 tests.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from sqlalchemy.orm import Session

from security_utils import log_secure_operation, clear_memory
from database import get_db
from models import User
from auth import require_verified_user
from shared.error_messages import sanitize_error
from ar_aging_engine import run_ar_aging, ARAgingConfig
from shared.helpers import validate_file_size, parse_uploaded_file, parse_json_mapping, maybe_record_tool_run
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT

router = APIRouter(tags=["ar_aging"])


@router.post("/audit/ar-aging")
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_ar_aging(
    request: Request,
    tb_file: UploadFile = File(...),
    subledger_file: Optional[UploadFile] = File(default=None),
    tb_column_mapping: Optional[str] = Form(default=None),
    sl_column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    prior_period_dso: Optional[float] = Form(default=None),
    days_in_period: Optional[int] = Form(default=None),
    beginning_ar_balance: Optional[float] = Form(default=None),
    collections_total: Optional[float] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Run AR aging analysis on trial balance + optional sub-ledger.

    ISA 540: Auditing Accounting Estimates (allowance for doubtful accounts).
    ISA 500: Audit Evidence.
    """
    tb_mapping_dict = parse_json_mapping(tb_column_mapping, "ar_aging_tb")
    sl_mapping_dict = parse_json_mapping(sl_column_mapping, "ar_aging_sl")

    log_secure_operation(
        "ar_aging_upload",
        f"Processing AR aging: tb={tb_file.filename}, subledger={'yes' if subledger_file else 'no'}"
    )

    try:
        # Parse TB file (required)
        tb_bytes = await validate_file_size(tb_file)
        tb_columns, tb_rows = parse_uploaded_file(tb_bytes, tb_file.filename or "")
        del tb_bytes

        # Parse sub-ledger file (optional)
        sl_columns: Optional[list[str]] = None
        sl_rows: Optional[list[dict]] = None

        if subledger_file and subledger_file.filename:
            sl_bytes = await validate_file_size(subledger_file)
            sl_columns, sl_rows = parse_uploaded_file(sl_bytes, subledger_file.filename or "")
            del sl_bytes

        # Build config from form params
        config = ARAgingConfig(
            prior_period_dso=prior_period_dso,
            days_in_period=days_in_period or 365,
            beginning_ar_balance=beginning_ar_balance,
            collections_total=collections_total,
        )

        result = run_ar_aging(
            tb_rows=tb_rows,
            tb_columns=tb_columns,
            sl_rows=sl_rows,
            sl_columns=sl_columns,
            config=config,
            tb_column_mapping=tb_mapping_dict,
            sl_column_mapping=sl_mapping_dict,
        )

        del tb_rows
        if sl_rows:
            del sl_rows
        clear_memory()

        score = result.composite_score.score if hasattr(result, 'composite_score') and result.composite_score else None
        maybe_record_tool_run(db, engagement_id, current_user.id, "ar_aging", True, score)

        return result.to_dict()

    except Exception as e:
        maybe_record_tool_run(db, engagement_id, current_user.id, "ar_aging", False)
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "analysis", "ar_aging_error")
        )
