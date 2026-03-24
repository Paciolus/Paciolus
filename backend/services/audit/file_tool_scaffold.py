"""
Shared file-tool execution scaffold (Sprint 519 Phase 1D).

Extracted from audit.py — provides a reusable scaffold for file-tool
endpoints that follow the validate → analyze → record pattern.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, Optional

from fastapi import BackgroundTasks, HTTPException, UploadFile
from sqlalchemy.orm import Session

from shared.error_messages import sanitize_error
from shared.helpers import maybe_record_tool_run, memory_cleanup, validate_file_size

logger = logging.getLogger(__name__)


async def execute_file_tool(
    file: UploadFile,
    tool_name: str,
    analyze_fn: Callable[[bytes, str], dict[str, Any]],
    background_tasks: BackgroundTasks,
    db: Session,
    engagement_id: Optional[int],
    user_id: int,
    error_context: str,
    composite_score_key: Optional[str] = None,
) -> dict[str, Any]:
    """Shared scaffold for file-tool endpoints.

    Handles: validate_file_size -> asyncio.to_thread(analyze_fn) ->
    maybe_record_tool_run -> error mapping.

    The caller provides the tool-specific analysis function which receives
    (file_bytes, filename) and returns a dict result.
    """
    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            result = await asyncio.to_thread(analyze_fn, file_bytes, filename)

            kwargs: dict[str, Any] = {}
            if composite_score_key and composite_score_key in result:
                kwargs["composite_score"] = result[composite_score_key]

            background_tasks.add_task(
                maybe_record_tool_run,
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

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("%s failed", tool_name)
            maybe_record_tool_run(db, engagement_id, user_id, tool_name, False)
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(e, "upload", error_context),
            )
