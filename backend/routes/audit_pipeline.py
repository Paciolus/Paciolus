"""
Paciolus API — Audit Pipeline Routes (Trial Balance Analysis)
"""

import asyncio
import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
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
    preflight_token: Optional[str] = Form(default=None),
    force_resubmit: bool = Form(default=False),
    current_user: User = Depends(check_diagnostic_limit),
    _verified: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> TrialBalanceResponse:
    """Analyze a trial balance file for balance validation using streaming processing."""

    # Check preflight cache — reuse file bytes from a prior preview/inspect call
    from shared.preflight_cache import preflight_cache

    cached_entry = preflight_cache.get(preflight_token) if preflight_token else None
    if cached_entry:
        preflight_cache.remove(preflight_token)  # type: ignore[arg-type]  # one-time consumption

    # AUDIT-06 FIX 4: Dedup check — prevent rapid double-submissions
    from sqlalchemy import text

    # Read file bytes early for both dedup hash and analysis
    if cached_entry:
        raw_bytes = cached_entry.file_bytes
    else:
        raw_bytes = await file.read()
        await file.seek(0)  # Reset for downstream validate_file_size

    file_hash = hashlib.sha256(raw_bytes).hexdigest()[:16]
    dedup_key = f"{current_user.id}:{engagement_id or 0}:{file_hash}:trial_balance"
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=5)
    submitted_filename = file.filename or (cached_entry.filename if cached_entry else "(unknown)")

    # Sprint 671 Issue 15: When the client passes ``force_resubmit=true``
    # the dedup gate is bypassed entirely — the matched key is removed
    # before the insert so the gate cannot fire. The user-facing error
    # below also explicitly tells the client how to re-submit.
    if force_resubmit:
        db.execute(text("DELETE FROM upload_dedup WHERE dedup_key = :key"), {"key": dedup_key})
        db.commit()
        log_secure_operation(
            "audit_dedup_force_resubmit",
            f"User {current_user.id} bypassed dedup for {submitted_filename}",
        )

    # Attempt insert; on conflict check expiry
    result = db.execute(
        text(
            "INSERT INTO upload_dedup (dedup_key, created_at, expires_at) "
            "VALUES (:key, :now, :expires_at) "
            "ON CONFLICT (dedup_key) DO UPDATE "
            "SET created_at = :now, expires_at = :expires_at "
            "WHERE upload_dedup.expires_at < :now"
        ),
        {"key": dedup_key, "now": now, "expires_at": expires_at},
    )
    db.commit()

    if result.rowcount == 0:  # type: ignore[attr-defined]
        # Sprint 671 Issue 15: Name the matched filename and explicitly
        # tell the client how to override. The historic message ("please
        # wait for the current analysis to complete") was misleading —
        # it implied something was still in progress, which it usually
        # wasn't. The 5-minute expiry simply blocks rapid re-submission
        # of identical bytes. The override path is documented in the
        # error detail so a user inspecting the network response can act
        # on it without reading our docs.
        raise HTTPException(
            status_code=409,
            detail={
                "error": "duplicate_submission",
                "message": (
                    f"This file ('{submitted_filename}') matches a previous submission "
                    "within the last 5 minutes. The earlier upload is either still "
                    "processing or completed recently. To re-run the diagnostic on the "
                    "same file before the 5-minute window expires, re-submit with "
                    "force_resubmit=true."
                ),
                "filename": submitted_filename,
                "match_window_seconds": 300,
                "override": "force_resubmit=true",
            },
        )

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
            if cached_entry:
                # File bytes already validated during preview/inspect
                file_bytes = cached_entry.file_bytes
                filename = cached_entry.filename
            else:
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

            analysis_result: dict[str, Any] = await asyncio.to_thread(_analyze)

            # Sprint 258: Auto-convert if user has rate table in session
            apply_currency_conversion(analysis_result, current_user.id, db)

            # Sprint 310: Include materiality source in response
            analysis_result["materiality_source"] = materiality_source

            flagged = extract_tb_accounts(analysis_result)
            tb_filename = file.filename or ""
            tb_record_count = analysis_result.get("record_count")
            tb_summary = {
                "was_balanced": analysis_result.get("was_balanced"),
                "anomaly_count": analysis_result.get("anomaly_count", 0),
            }
            background_tasks.add_task(
                maybe_record_tool_run,
                db,
                engagement_id,
                current_user.id,
                "trial_balance",
                True,
                None,
                flagged,
                tb_filename,
                tb_record_count,
                tb_summary,
            )

            return analysis_result  # type: ignore[return-value]

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Trial balance analysis failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "trial_balance", False)
            raise HTTPException(status_code=400, detail=sanitize_error(e, "upload", "audit_error"))
