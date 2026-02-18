"""
Shared single-file testing route factory.

Encapsulates the boilerplate shared by 6 single-file testing endpoints:
  validate_file_size → parse_uploaded_file → run_engine → cleanup →
  score extraction → maybe_record_tool_run → to_dict

Used by: AP, Payroll, JE (main), Revenue, Fixed Asset, Inventory routes.
NOT used by: Three-Way Match (3-file), AR Aging (dual-file + config).
"""
import asyncio
import logging
from collections.abc import Callable
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import BackgroundTasks, HTTPException, UploadFile
from sqlalchemy.orm import Session

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


async def run_single_file_testing(
    *,
    file: UploadFile,
    column_mapping: Optional[str],
    engagement_id: Optional[int],
    current_user: User,
    db: Session,
    background_tasks: BackgroundTasks,
    tool_name: str,
    mapping_key: str,
    log_label: str,
    error_key: str,
    run_engine: Callable,
    extract_accounts: Optional[Callable[[dict], list[str]]] = None,
) -> dict:
    """Run a single-file testing endpoint with standard boilerplate.

    Args:
        file: Uploaded CSV/Excel file.
        column_mapping: Optional JSON string of column overrides.
        engagement_id: Optional engagement to record tool run against.
        current_user: Authenticated user.
        db: Database session.
        background_tasks: FastAPI BackgroundTasks for deferred work.
        tool_name: Tool identifier for tool run recording.
        mapping_key: Key for parse_json_mapping context.
        log_label: Label for secure operation log (e.g. "AP", "Payroll").
        error_key: Key for error sanitization context.
        run_engine: Callback(rows, column_names, column_mapping_dict, filename) -> result.
        extract_accounts: Optional callback to extract flagged account names from result dict.
    """
    column_mapping_dict = parse_json_mapping(column_mapping, mapping_key)

    log_secure_operation(
        f"{mapping_key}_upload",
        f"Processing {log_label} file: {file.filename}"
    )

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _process():
                column_names, rows = parse_uploaded_file(file_bytes, filename)
                result = run_engine(rows, column_names, column_mapping_dict, filename)
                return result

            result = await asyncio.to_thread(_process)

            result_dict = result.to_dict()
            score = result.composite_score.score if hasattr(result, 'composite_score') and result.composite_score else None
            flagged = extract_accounts(result_dict) if extract_accounts else None
            background_tasks.add_task(maybe_record_tool_run, db, engagement_id, current_user.id, tool_name, True, score, flagged)

            return result_dict

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("%s analysis failed", tool_name)
            maybe_record_tool_run(db, engagement_id, current_user.id, tool_name, False)
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(e, "analysis", error_key)
            )
