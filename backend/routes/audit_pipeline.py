"""
Paciolus API — Audit Pipeline Routes (Trial Balance Analysis)
"""

import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from audit_engine import (
    DEFAULT_CHUNK_SIZE,
    audit_trial_balance_multi_sheet,
    audit_trial_balance_streaming,
)
from auth import require_verified_user
from database import get_db
from models import User
from security_utils import log_secure_operation
from shared.account_extractors import extract_tb_accounts
from shared.diagnostic_response_schemas import TrialBalanceResponse
from shared.entitlement_checks import check_diagnostic_limit
from shared.error_messages import sanitize_error
from shared.helpers import (
    maybe_record_tool_run,
    memory_cleanup,
    parse_json_list,
    parse_json_mapping,
    validate_file_size,
)
from shared.materiality_resolver import resolve_materiality
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.tb_post_processor import apply_currency_conversion, apply_lead_sheet_grouping

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audit"])


@router.post("/audit/trial-balance", response_model=TrialBalanceResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_trial_balance(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    materiality_threshold: float = Form(default=0.0, ge=0.0),
    account_type_overrides: Optional[str] = Form(default=None),
    column_mapping: Optional[str] = Form(default=None),
    selected_sheets: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(check_diagnostic_limit),
    _verified: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> TrialBalanceResponse:
    """Analyze a trial balance file for balance validation using streaming processing."""

    overrides_dict: Optional[dict[str, str]] = None
    if account_type_overrides:
        try:
            overrides_dict = json.loads(account_type_overrides)
            log_secure_operation("audit_overrides", f"Received {len(overrides_dict)} account type overrides")
        except json.JSONDecodeError:
            log_secure_operation("audit_overrides_error", "Invalid JSON in overrides, ignoring")

    column_mapping_dict = parse_json_mapping(column_mapping, "audit_column")
    selected_sheets_list = parse_json_list(selected_sheets, "audit_selected_sheets")

    # Sprint 310: Resolve materiality from engagement cascade if not explicitly set
    materiality_threshold, materiality_source = resolve_materiality(
        materiality_threshold,
        engagement_id,
        current_user.id,
        db,
    )

    log_secure_operation(
        "audit_upload_streaming",
        f"Processing file: {file.filename} (threshold: ${materiality_threshold:,.2f}, source: {materiality_source}, chunk_size: {DEFAULT_CHUNK_SIZE})",
    )

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _analyze() -> dict[str, Any]:
                if selected_sheets_list and len(selected_sheets_list) > 0:
                    result = audit_trial_balance_multi_sheet(
                        file_bytes=file_bytes,
                        filename=filename,
                        selected_sheets=selected_sheets_list,
                        materiality_threshold=materiality_threshold,
                        chunk_size=DEFAULT_CHUNK_SIZE,
                        account_type_overrides=overrides_dict,
                        column_mapping=column_mapping_dict,
                    )
                else:
                    result = audit_trial_balance_streaming(
                        file_bytes=file_bytes,
                        filename=filename,
                        materiality_threshold=materiality_threshold,
                        chunk_size=DEFAULT_CHUNK_SIZE,
                        account_type_overrides=overrides_dict,
                        column_mapping=column_mapping_dict,
                    )

                apply_lead_sheet_grouping(result, materiality_threshold)

                return result

            result = await asyncio.to_thread(_analyze)

            # Sprint 258: Auto-convert if user has rate table in session
            apply_currency_conversion(result, current_user.id, db)

            # Sprint 310: Include materiality source in response
            result["materiality_source"] = materiality_source

            flagged = extract_tb_accounts(result)
            background_tasks.add_task(
                maybe_record_tool_run, db, engagement_id, current_user.id, "trial_balance", True, None, flagged
            )

            return result

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Trial balance analysis failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "trial_balance", False)
            raise HTTPException(status_code=400, detail=sanitize_error(e, "upload", "audit_error"))
