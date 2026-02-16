"""
Retention cleanup for persisted aggregate metadata — Packet 8

Deterministic, idempotent cleanup of time-bounded metadata tables.
Runs at app startup via lifespan. Deletes rows older than the
configured retention window.

ZERO-STORAGE NOTE: These tables store only aggregate metadata
(counts, totals, hashes) — never raw financial data. Retention
cleanup is a privacy/hygiene measure, not a data-loss risk.
"""

import logging
from datetime import datetime, UTC, timedelta

from sqlalchemy.orm import Session

from config import _load_optional

logger = logging.getLogger(__name__)

# Configurable retention window (days). Applies to:
#   - activity_logs.timestamp
#   - diagnostic_summaries.timestamp
# Default: 365 days (1 year).  Override via RETENTION_DAYS env var.
RETENTION_DAYS = int(_load_optional("RETENTION_DAYS", "365"))


def cleanup_expired_activity_logs(db: Session, *, cutoff: datetime | None = None) -> int:
    """Delete activity_logs older than the retention cutoff.

    Returns the number of rows deleted.  Idempotent: repeated calls
    with the same cutoff delete nothing on second run.
    """
    from models import ActivityLog

    if cutoff is None:
        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)

    deleted = db.query(ActivityLog).filter(
        ActivityLog.timestamp < cutoff,
    ).delete(synchronize_session=False)

    if deleted > 0:
        db.commit()
    return deleted


def cleanup_expired_diagnostic_summaries(db: Session, *, cutoff: datetime | None = None) -> int:
    """Delete diagnostic_summaries older than the retention cutoff.

    Returns the number of rows deleted.  Idempotent: repeated calls
    with the same cutoff delete nothing on second run.
    """
    from models import DiagnosticSummary

    if cutoff is None:
        cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)

    deleted = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.timestamp < cutoff,
    ).delete(synchronize_session=False)

    if deleted > 0:
        db.commit()
    return deleted


def run_retention_cleanup(db: Session) -> dict[str, int]:
    """Run all retention cleanup tasks.  Called from app lifespan.

    Returns a dict of {table_name: deleted_count} for logging.
    Only logs aggregate counts — no sensitive data.
    """
    results: dict[str, int] = {}

    results["activity_logs"] = cleanup_expired_activity_logs(db)
    results["diagnostic_summaries"] = cleanup_expired_diagnostic_summaries(db)

    total = sum(results.values())
    if total > 0:
        logger.info(
            "Retention cleanup: deleted %d activity_logs, %d diagnostic_summaries "
            "(retention=%d days)",
            results["activity_logs"],
            results["diagnostic_summaries"],
            RETENTION_DAYS,
        )
    return results
