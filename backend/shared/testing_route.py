"""
Shared single-file testing route factory.

Encapsulates the boilerplate shared by 6 single-file testing endpoints:
  validate_file_size → parse_uploaded_file → run_engine → cleanup →
  score extraction → maybe_record_tool_run → to_dict

Used by: AP, Payroll, JE (main), Revenue, Fixed Asset, Inventory routes.
NOT used by: Three-Way Match (3-file), AR Aging (dual-file + config).
"""
from typing import Callable, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from security_utils import log_secure_operation, clear_memory
from models import User
from shared.error_messages import sanitize_error
from shared.helpers import validate_file_size, parse_uploaded_file, parse_json_mapping, maybe_record_tool_run


async def run_single_file_testing(
    *,
    file: UploadFile,
    column_mapping: Optional[str],
    engagement_id: Optional[int],
    current_user: User,
    db: Session,
    tool_name: str,
    mapping_key: str,
    log_label: str,
    error_key: str,
    run_engine: Callable,
) -> dict:
    """Run a single-file testing endpoint with standard boilerplate.

    Args:
        file: Uploaded CSV/Excel file.
        column_mapping: Optional JSON string of column overrides.
        engagement_id: Optional engagement to record tool run against.
        current_user: Authenticated user.
        db: Database session.
        tool_name: Tool identifier for tool run recording.
        mapping_key: Key for parse_json_mapping context.
        log_label: Label for secure operation log (e.g. "AP", "Payroll").
        error_key: Key for error sanitization context.
        run_engine: Callback(rows, column_names, column_mapping_dict, filename) -> result.
    """
    column_mapping_dict = parse_json_mapping(column_mapping, mapping_key)

    log_secure_operation(
        f"{mapping_key}_upload",
        f"Processing {log_label} file: {file.filename}"
    )

    try:
        file_bytes = await validate_file_size(file)
        column_names, rows = parse_uploaded_file(file_bytes, file.filename or "")
        del file_bytes

        result = run_engine(rows, column_names, column_mapping_dict, file.filename or "")

        del rows
        clear_memory()

        score = result.composite_score.score if hasattr(result, 'composite_score') and result.composite_score else None
        maybe_record_tool_run(db, engagement_id, current_user.id, tool_name, True, score)

        return result.to_dict()

    except Exception as e:
        maybe_record_tool_run(db, engagement_id, current_user.id, tool_name, False)
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "analysis", error_key)
        )
