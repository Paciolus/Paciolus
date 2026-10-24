"""Record a tool run to the engagement layer and the unified ToolActivity feed.

A tool run has two observability surfaces:

1. ``ToolActivity`` — cross-engagement feed consumed by the multi-tool
   dashboard (Sprint 579). Always written, regardless of engagement link.
2. ``Engagement.tool_runs`` — per-engagement workpaper trail. Only written
   when the caller supplies ``engagement_id`` and the engagement resolves
   for the current user.

**Transaction ownership (corrected in Sprint 787b).** This module previously
declared that it "is deliberately never the transactional boundary: it calls
``db.add`` but does not commit, letting the route handler own the commit."

That contract was never honoured by a single one of the thirteen call sites.
``get_db`` ends with ``finally: db.close()`` and nothing else, so for any run
**without** an ``engagement_id`` the pending ``ToolActivity`` insert was
discarded when the session closed — measured, not inferred: zero rows survive.
Every engagement-less tool run across all thirteen routes was therefore missing
from the multi-tool dashboard feed. Runs *with* a resolving engagement happened
to persist only because ``EngagementManager.record_tool_run`` commits, which
flushed the activity row along with it.

Rather than add a commit to thirteen route handlers for a row none of them knows
about, the recorder now owns the commit for the activity row — consistent with
``record_tool_run``, which already commits on the same session.
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
    *,
    consumes_upload: bool = False,
) -> None:
    """Write a ToolActivity row, and (if engagement_id resolves) a ToolRun row.

    **Upload metering (Sprint 790).** When ``success`` is true and the caller
    passes ``consumes_upload=True``, the user's monthly upload counter advances
    by one (``shared.entitlement_checks.increment_upload_count``). The unit is
    one successful analysis run, however many files it took; a failed run
    (``success=False``) never consumes allowance. Only routes that gate on
    ``check_upload_limit`` pass the flag, so an ungated side-analysis (the TB
    diagnostics behind ``file_tool_scaffold``, multi-period comparisons of
    already-uploaded balances, sampling evaluation) does not draw down a quota
    it was never checked against. ``tests/test_sprint_790_upload_metering.py``
    holds both directions of that pairing.

    Resolution happens **before** the activity row is written (Sprint 787b). The
    previous order wrote ``ToolActivity`` carrying the caller-supplied
    ``engagement_id`` first, then queried for the engagement — and that query's
    autoflush pushed the pending insert, so a nonexistent or stale id violated
    the ``tool_activity.engagement_id`` foreign key and surfaced as an unhandled
    ``IntegrityError``. A client posting a stale engagement id got a 500 from
    every one of the thirteen wired routes, on both the success and the failure
    path, including the failure path where the intended answer was a 400.

    An id that does not resolve now degrades to an **unlinked** activity row,
    which is the same "skip the workpaper trail" semantics the function already
    applied to an engagement belonging to another user.
    """
    from engagement_manager import EngagementManager

    engagement = None
    manager = None
    if engagement_id is not None:
        manager = EngagementManager(db)
        engagement = manager.get_engagement(user_id, engagement_id)
        if not engagement:
            log_secure_operation(
                "tool_run_skip",
                f"Engagement {engagement_id} not found for user {user_id}; skipping tool run",
            )

    _log_tool_activity(
        db,
        user_id=user_id,
        tool_name=tool_name,
        # Only a resolved engagement is attached; an unresolved id would be an
        # invalid foreign key, and the activity row is still worth keeping.
        engagement_id=engagement_id if engagement else None,
        filename=filename,
        record_count=record_count,
        summary=summary,
    )

    if success and consumes_upload:
        _consume_upload(db, user_id, tool_name)

    if engagement is None or manager is None:
        return

    from engagement_model import ToolName, ToolRunStatus

    manager.record_tool_run(
        engagement_id=engagement_id,
        tool_name=ToolName(tool_name),
        status=ToolRunStatus.COMPLETED if success else ToolRunStatus.FAILED,
        composite_score=composite_score if success else None,
        flagged_accounts=flagged_accounts if success else None,
    )


def _consume_upload(db: Session, user_id: int, tool_name: str) -> None:
    """Advance the upload counter for one successful run.

    A failure here must not turn a finished analysis into a 500: the user has
    their result, and an under-count can only ever let a run through, never
    lock anyone out. So it is logged and rolled back, not raised.
    """
    from shared.entitlement_checks import increment_upload_count

    try:
        increment_upload_count(db, user_id)
    except Exception:
        logger.exception("Failed to advance upload counter for user %d, tool %s", user_id, tool_name)
        db.rollback()


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
        # Sprint 787b: commit here. The comment this replaces said "No commit
        # here — the route handler owns the transaction boundary", but none of
        # the thirteen callers commits, and get_db's teardown is a bare
        # db.close(), so every engagement-less run silently lost its row. The
        # session carries nothing else pending at this point: the entitlement
        # and tier checks that run before the recorder are read-only.
        db.commit()
    except Exception:
        logger.exception("Failed to log tool activity for user %d, tool %s", user_id, tool_name)
        db.rollback()
