"""
Retention cleanup for persisted aggregate metadata — Packet 8
Phase XLVI: converted from hard-delete to soft-delete (Sprint 346).

Deterministic, idempotent cleanup of time-bounded metadata tables.
Runs at app startup via lifespan. Archives rows older than the
configured retention window by setting ``archived_at``.

ZERO-STORAGE NOTE: These tables store only aggregate metadata
(counts, totals, hashes) — never raw financial data. Retention
cleanup is a privacy/hygiene measure, not a data-loss risk.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from config import _load_optional

logger = logging.getLogger(__name__)

# Configurable retention window (days). Applies to:
#   - activity_logs.timestamp
#   - diagnostic_summaries.timestamp
# Default: 365 days (1 year).  Override via RETENTION_DAYS env var.
RETENTION_DAYS = int(_load_optional("RETENTION_DAYS", "365"))


def cleanup_expired_activity_logs(db: Session, *, cutoff: datetime | None = None) -> int:
    """Archive activity_logs older than the retention cutoff (soft-delete).

    Returns the number of rows archived.  Idempotent: repeated calls
    with the same cutoff archive nothing on second run (already-archived
    rows are skipped).
    """
    from models import ActivityLog

    if cutoff is None:
        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)

    archived = db.query(ActivityLog).filter(
        ActivityLog.timestamp < cutoff,
        ActivityLog.archived_at.is_(None),
    ).update(
        {
            "archived_at": cutoff,
            "archive_reason": "retention_policy",
        },
        synchronize_session=False,
    )

    if archived > 0:
        db.commit()
    return archived


def cleanup_expired_diagnostic_summaries(db: Session, *, cutoff: datetime | None = None) -> int:
    """Archive diagnostic_summaries older than the retention cutoff (soft-delete).

    Returns the number of rows archived.  Idempotent: repeated calls
    with the same cutoff archive nothing on second run.
    """
    from models import DiagnosticSummary

    if cutoff is None:
        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)

    archived = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.timestamp < cutoff,
        DiagnosticSummary.archived_at.is_(None),
    ).update(
        {
            "archived_at": cutoff,
            "archive_reason": "retention_policy",
        },
        synchronize_session=False,
    )

    if archived > 0:
        db.commit()
    return archived


def run_retention_cleanup(db: Session) -> dict[str, int]:
    """Run all retention cleanup tasks.  Called from app lifespan.

    Returns a dict of {table_name: archived_count} for logging.
    Only logs aggregate counts — no sensitive data.
    """
    results: dict[str, int] = {}

    results["activity_logs"] = cleanup_expired_activity_logs(db)
    results["diagnostic_summaries"] = cleanup_expired_diagnostic_summaries(db)

    total = sum(results.values())
    if total > 0:
        logger.info(
            "Retention cleanup: archived %d activity_logs, %d diagnostic_summaries "
            "(retention=%d days)",
            results["activity_logs"],
            results["diagnostic_summaries"],
            RETENTION_DAYS,
        )
    return results
