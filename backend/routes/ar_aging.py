"""
Paciolus API — AR Aging Routes (Sprint 107)

Dual-file upload: TB (required) + optional AR sub-ledger.
TB-only: 4 tests. TB + sub-ledger: all 11 tests.
"""
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from ar_aging_engine import ARAgingConfig, run_ar_aging
from auth import require_verified_user
from database import get_db
from models import User
from security_utils import log_secure_operation
from shared.error_messages import sanitize_error
from shared.helpers import (
    maybe_record_tool_run,
    memory_cleanup,
    parse_json_mapping,
    parse_uploaded_file,
    validate_file_size,
)
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_response_schemas import ARAgingResponse

router = APIRouter(tags=["ar_aging"])


@router.post("/audit/ar-aging", response_model=ARAgingResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_ar_aging(
    request: Request,
    background_tasks: BackgroundTasks,
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

    with memory_cleanup():
        try:
            # Read file bytes (async I/O)
            tb_bytes = await validate_file_size(tb_file)
            tb_filename = tb_file.filename or ""

            sl_bytes: Optional[bytes] = None
            sl_filename: Optional[str] = None
            if subledger_file and subledger_file.filename:
                sl_bytes = await validate_file_size(subledger_file)
                sl_filename = subledger_file.filename or ""

            # Build config from form params
            config = ARAgingConfig(
                prior_period_dso=prior_period_dso,
                days_in_period=days_in_period or 365,
                beginning_ar_balance=beginning_ar_balance,
                collections_total=collections_total,
            )

            def _analyze():
                tb_columns, tb_rows = parse_uploaded_file(tb_bytes, tb_filename)

                sl_columns_local: Optional[list[str]] = None
                sl_rows_local: Optional[list[dict]] = None
                if sl_bytes is not None:
                    sl_columns_local, sl_rows_local = parse_uploaded_file(sl_bytes, sl_filename or "")

                return run_ar_aging(
                    tb_rows=tb_rows,
                    tb_columns=tb_columns,
                    sl_rows=sl_rows_local,
                    sl_columns=sl_columns_local,
                    config=config,
                    tb_column_mapping=tb_mapping_dict,
                    sl_column_mapping=sl_mapping_dict,
                )

            result = await asyncio.to_thread(_analyze)

            score = result.composite_score.score if hasattr(result, 'composite_score') and result.composite_score else None
            background_tasks.add_task(maybe_record_tool_run, db, engagement_id, current_user.id, "ar_aging", True, score)

            return result.to_dict()

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("AR aging analysis failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "ar_aging", False)
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(e, "analysis", "ar_aging_error")
            )
