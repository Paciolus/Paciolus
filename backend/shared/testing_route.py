"""
Shared single-file testing route factory.

Encapsulates the boilerplate shared by 6 single-file testing endpoints:
  validate_file_size → parse_uploaded_file → run_engine → cleanup →
  score extraction → maybe_record_tool_run → to_dict

Used by: AP, Payroll, JE (main), Revenue, Fixed Asset, Inventory routes.
NOT used by: Three-Way Match (3-file), AR Aging (dual-file + config).

Also ``run_json_tool`` (Sprint 819 item 6): the enforce -> quota -> run ->
record sequence the six promoted JSON-body tools (SoD, intercompany, W-2,
Form 1099, book-to-tax, cash-flow projector) each repeated.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, Optional, TypeVar

logger = logging.getLogger(__name__)

from fastapi import BackgroundTasks, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from models import User, UserTier
from security_utils import log_secure_operation
from shared.entitlement_checks import check_upload_limit, get_effective_entitlements
from shared.error_messages import sanitize_error
from shared.helpers import parse_json_mapping
from shared.tool_run_recorder import maybe_record_tool_run
from shared.upload_pipeline import (
    memory_cleanup,
    parse_uploaded_file,
    validate_file_size,
)


def enforce_tool_access(current_user: User, tool_name: str, db: object = None) -> None:
    """Check entitlement for tool access. Raises HTTPException(403) in hard mode.

    Shared by the factory function and individual non-factory routes.
    AUDIT-06 FIX 2: subscription-status-aware when db is provided.
    """
    if db is not None:
        entitlements = get_effective_entitlements(current_user, db)
    else:
        from shared.entitlements import get_entitlements

        entitlements = get_entitlements(UserTier(current_user.tier.value))
    if entitlements.tools_allowed and tool_name not in entitlements.tools_allowed:
        from config import ENTITLEMENT_ENFORCEMENT

        if ENTITLEMENT_ENFORCEMENT == "hard":
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "TIER_LIMIT_EXCEEDED",
                    "message": f"Tool '{tool_name}' is not available on your current plan.",
                    "resource": "tool_access",
                    "current_tier": current_user.tier.value,
                    "upgrade_url": "/pricing",
                },
            )
        else:
            logger.warning(
                "SOFT entitlement block: tool=%s, user=%d, tier=%s", tool_name, current_user.id, current_user.tier.value
            )


_R = TypeVar("_R")

# What a promoted tool maps to a sanitized 400 when its engine fails unexpectedly.
_JSON_TOOL_UNEXPECTED_ERRORS: tuple[type[Exception], ...] = (ValueError, ValidationError, ArithmeticError)


def run_json_tool(
    *,
    db: Session,
    current_user: User,
    tool_name: str,
    engagement_id: Optional[int],
    compute: Callable[[], _R],
    input_errors: tuple[type[Exception], ...] = (),
    unexpected_errors: tuple[type[Exception], ...] = _JSON_TOOL_UNEXPECTED_ERRORS,
    error_key: str = "",
    route_logger: Optional[logging.Logger] = None,
    failure_log: str = "",
    reraise_errors: tuple[type[Exception], ...] = (),
) -> _R:
    """Gate, run and record one JSON-body tool run (Sprint 819 item 6).

    1. ``enforce_tool_access`` then ``check_upload_limit`` (tier + quota).
    2. ``compute()`` — builds the engine config from the request and runs it.
    3. On failure, a FAILED ToolRun is recorded against ``engagement_id`` and:
       - ``input_errors`` (the engine's own input-error type) -> 400, ``str(e)``;
       - ``unexpected_errors`` -> logged with ``failure_log`` on ``route_logger``,
         then 400 with ``sanitize_error(e, "audit", error_key)``;
       - ``reraise_errors`` -> re-raised unchanged (SoD: its 400 comes from
         request validation, and KeyError/TypeError propagate as before).
       Anything else — including the ``HTTPException`` a request-decimal parse
       raises — propagates without recording, as it always has.
    4. On success, a COMPLETED ToolRun is recorded **synchronously**, before the
       response is sent (PR #183 review: a background task runs after the body
       is sent, so the Sprint 791 hooks' immediate refresh missed the row).
       ``composite_score`` and ``flagged_accounts`` are None by design: none of
       these engines produces a composite score, and their findings are not
       GL-account-level, so ``shared/account_extractors.py`` has no extractor.

    Each ``except`` is checked in the order above, so an engine input error that
    subclasses ``ValueError`` still gets its own message.
    """
    enforce_tool_access(current_user, tool_name, db)
    check_upload_limit(current_user, db)

    try:
        result = compute()
    except input_errors as e:
        maybe_record_tool_run(db, engagement_id, current_user.id, tool_name, False)
        raise HTTPException(status_code=400, detail=str(e))
    except unexpected_errors as e:
        (route_logger or logger).exception(failure_log)
        maybe_record_tool_run(db, engagement_id, current_user.id, tool_name, False)
        raise HTTPException(status_code=400, detail=sanitize_error(e, "audit", error_key))
    except reraise_errors:
        maybe_record_tool_run(db, engagement_id, current_user.id, tool_name, False)
        raise

    maybe_record_tool_run(db, engagement_id, current_user.id, tool_name, True, None, None, consumes_upload=True)
    return result


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
    result_extras: Optional[dict[str, Any]] = None,
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
        result_extras: Optional fields merged into the returned result (Sprint 836:
            ``settings_applied`` / ``settings_ignored``).
    """
    # Sprint 367: Entitlement check — verify tool access before processing
    enforce_tool_access(current_user, tool_name, db)
    # Sprint 678: every testing-tool upload counts against the monthly quota.
    check_upload_limit(current_user, db)

    column_mapping_dict = parse_json_mapping(column_mapping, mapping_key)

    log_secure_operation(f"{mapping_key}_upload", f"Processing {log_label} file: {file.filename}")

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _process() -> Any:
                column_names, rows = parse_uploaded_file(file_bytes, filename)
                result = run_engine(rows, column_names, column_mapping_dict, filename)
                return result

            result = await asyncio.to_thread(_process)

            result_dict = result.to_dict()
            score = (
                result.composite_score.score if hasattr(result, "composite_score") and result.composite_score else None
            )
            flagged = extract_accounts(result_dict) if extract_accounts else None
            maybe_record_tool_run(
                db,
                engagement_id,
                current_user.id,
                tool_name,
                True,
                score,
                flagged,
                filename,
                result_dict.get("record_count"),
                consumes_upload=True,
            )

            response = dict(result_dict)
            if result_extras:
                response.update(result_extras)
            return response

        except (ValueError, KeyError, TypeError, ArithmeticError) as e:
            # Sprint 814: the Sprint 713 treatment, which only ever reached
            # file_tool_scaffold. ArithmeticError covers decimal.InvalidOperation
            # from a malformed amount cell — a user-facing 400, so WARNING, not
            # a Sentry-paging ERROR.
            logger.warning("%s rejected [%s]", tool_name, type(e).__name__)  # Sprint 840 (S6): type only
            maybe_record_tool_run(db, engagement_id, current_user.id, tool_name, False)
            raise HTTPException(status_code=400, detail=sanitize_error(e, "analysis", error_key))
