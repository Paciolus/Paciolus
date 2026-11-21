"""
Shared file-tool execution scaffold (Sprint 519 Phase 1D).

Extracted from audit.py — provides a reusable scaffold for file-tool
endpoints that follow the validate → analyze → record pattern.

Sprint 890 (15E step 4): the analysis and the run recording are one synchronous unit run through
the thread pool, with a session of its own; only reading the upload awaits on the event loop.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, Optional

from fastapi import BackgroundTasks, HTTPException, UploadFile

from database import SessionScope
from shared.error_messages import sanitize_error
from shared.tool_run_recorder import maybe_record_tool_run
from shared.upload_pipeline import (
    memory_cleanup,
    validate_file_size,
)

logger = logging.getLogger(__name__)


def _record_failure(session_scope: SessionScope, engagement_id: Optional[int], user_id: int, tool_name: str) -> None:
    with session_scope() as db:
        maybe_record_tool_run(db, engagement_id, user_id, tool_name, False)


async def execute_file_tool(
    file: UploadFile,
    tool_name: str,
    analyze_fn: Callable[[bytes, str], dict[str, Any]],
    background_tasks: BackgroundTasks,
    session_scope: SessionScope,
    engagement_id: Optional[int],
    user_id: int,
    error_context: str,
    composite_score_key: Optional[str] = None,
) -> dict[str, Any]:
    """Shared scaffold for file-tool endpoints.

    Handles: validate_file_size -> asyncio.to_thread(analyze + maybe_record_tool_run) ->
    error mapping.

    The caller provides the tool-specific analysis function which receives
    (file_bytes, filename) and returns a dict result.
    """
    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _analyze_and_record() -> dict[str, Any]:
                result = analyze_fn(file_bytes, filename)
                kwargs: dict[str, Any] = {}
                if composite_score_key and composite_score_key in result:
                    kwargs["composite_score"] = result[composite_score_key]
                with session_scope() as db:
                    maybe_record_tool_run(
                        db,
                        engagement_id,
                        user_id,
                        tool_name,
                        True,
                        filename=filename,
                        record_count=result.get("record_count") if isinstance(result, dict) else None,
                        **kwargs,
                    )
                return result

            return await asyncio.to_thread(_analyze_and_record)

        except (ValueError, KeyError, TypeError, ArithmeticError) as e:
            # Sprint 713: ArithmeticError catches decimal.InvalidOperation
            # (incl. ConversionSyntax) raised by unguarded Decimal() calls
            # on malformed numeric input. Log level is WARNING — these are
            # user-facing 400s, not Sentry-worthy ERROR events.
            logger.warning(
                "%s rejected [%s]: %s",
                tool_name,
                type(e).__name__,
                e,
                exc_info=True,
            )
            await asyncio.to_thread(_record_failure, session_scope, engagement_id, user_id, tool_name)
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(e, "upload", error_context),
            )
