"""Record a tool run to the engagement layer and the unified ToolActivity feed.

A tool run has two observability surfaces:

1. ``ToolActivity`` — cross-engagement feed consumed by the multi-tool
   dashboard (Sprint 579). Always written, regardless of engagement link.
2. ``Engagement.tool_runs`` — per-engagement workpaper trail. Only written
   when the caller supplies ``engagement_id`` and the engagement resolves
   for the current user.

``maybe_record_tool_run`` is deliberately never the transactional boundary:
it calls ``db.add`` but does not commit, letting the route handler own the
commit (and any rollback semantics).
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from shared.filenames import get_filename_display

logger = logging.getLogger(__name__)


def maybe_record_tool_run(
    db: Session,
    engagement_id: Optional[int],
    user_id: int,
    tool_name: str,
    success: bool,
    composite_score: Optional[float] = None,
    flagged_accounts: Optional[list[str]] = None,
    filename: Optional[str] = None,
    record_count: Optional[int] = None,
    summary: Optional[dict] = None,
) -> None:
    """Write a ToolActivity row, and (if engagement_id resolves) a ToolRun row."""
    _log_tool_activity(
        db,
        user_id=user_id,
        tool_name=tool_name,
        engagement_id=engagement_id,
        filename=filename,
        record_count=record_count,
        summary=summary,
    )

    if engagement_id is None:
        return

    from engagement_manager import EngagementManager
    from engagement_model import ToolName, ToolRunStatus

    manager = EngagementManager(db)

    engagement = manager.get_engagement(user_id, engagement_id)
    if not engagement:
        log_secure_operation(
            "tool_run_skip",
            f"Engagement {engagement_id} not found for user {user_id}; skipping tool run",
        )
        return

    manager.record_tool_run(
        engagement_id=engagement_id,
        tool_name=ToolName(tool_name),
        status=ToolRunStatus.COMPLETED if success else ToolRunStatus.FAILED,
        composite_score=composite_score if success else None,
        flagged_accounts=flagged_accounts if success else None,
    )


def _log_tool_activity(
    db: Session,
    user_id: int,
    tool_name: str,
    engagement_id: Optional[int] = None,
    filename: Optional[str] = None,
    record_count: Optional[int] = None,
    summary: Optional[dict] = None,
) -> None:
    """Append a ToolActivity row for the unified dashboard feed (Sprint 579)."""
    from models import ToolActivity

    display_name = get_filename_display(filename) if filename else None
    summary_json = json.dumps(summary) if summary else None

    try:
        activity = ToolActivity(
            user_id=user_id,
            tool_name=tool_name,
            filename_display=display_name,
            record_count=record_count,
            summary_json=summary_json,
            engagement_id=engagement_id,
        )
        db.add(activity)
        # No commit here — the route handler owns the transaction boundary.
    except Exception:
        logger.exception("Failed to log tool activity for user %d, tool %s", user_id, tool_name)
