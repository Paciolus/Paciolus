"""
Recurring Cleanup Scheduler — Sprint 307

In-process APScheduler BackgroundScheduler that runs cleanup jobs on fixed
intervals.  Supplements the cold-start cleanup in main.py lifespan so that
long-running servers don't accumulate stale tokens, sessions, or metadata.

Architecture:
- APScheduler 3.x BackgroundScheduler with a single ThreadPoolExecutor worker
- coalesce=True + max_instances=1: missed triggers coalesce, no overlap
- All cleanup functions are idempotent (DELETE WHERE ts < cutoff)
- Each job creates its own SessionLocal() — not request-scoped

Telemetry:
- Structured logging only (aggregate counts, durations) — Zero-Storage compliant
- No financial data, PII, or account details in any log entry

Watchdog:
- Runs every 5 minutes, warns if any job is overdue by >2x its interval
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from config import (
    CLEANUP_REFRESH_TOKEN_INTERVAL_MINUTES,
    CLEANUP_RETENTION_INTERVAL_HOURS,
    CLEANUP_SCHEDULER_ENABLED,
    CLEANUP_TOOL_SESSION_INTERVAL_MINUTES,
    CLEANUP_VERIFICATION_TOKEN_INTERVAL_MINUTES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_scheduler = None
_last_run_times: dict[str, datetime] = {}

# Expected intervals for watchdog checks (job_name → timedelta)
_EXPECTED_INTERVALS: dict[str, timedelta] = {
    "refresh_tokens": timedelta(minutes=CLEANUP_REFRESH_TOKEN_INTERVAL_MINUTES),
    "verification_tokens": timedelta(minutes=CLEANUP_VERIFICATION_TOKEN_INTERVAL_MINUTES),
    "tool_sessions": timedelta(minutes=CLEANUP_TOOL_SESSION_INTERVAL_MINUTES),
    "retention_cleanup": timedelta(hours=CLEANUP_RETENTION_INTERVAL_HOURS),
}

WATCHDOG_INTERVAL_MINUTES = 5


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

@dataclass
class CleanupTelemetry:
    """Structured telemetry for a single cleanup job run."""

    job_name: str
    started_at: str  # ISO 8601
    duration_ms: float
    records_processed: int
    error: str | None = field(default=None)

    def to_log_dict(self) -> dict:
        """Return a dict suitable for structured logging."""
        d: dict = {
            "event": "cleanup_job",
            "job_name": self.job_name,
            "started_at": self.started_at,
            "duration_ms": round(self.duration_ms, 2),
            "records_processed": self.records_processed,
        }
        if self.error is not None:
            d["error"] = self.error
        return d


# ---------------------------------------------------------------------------
# Generic job wrapper
# ---------------------------------------------------------------------------

def _run_cleanup_job(
    job_name: str,
    cleanup_func,
    *,
    is_retention: bool = False,
) -> None:
    """Execute a cleanup function with telemetry and its own DB session.

    Args:
        job_name: Human-readable name for logging.
        cleanup_func: Callable(db) -> int  OR  Callable(db) -> dict[str, int]
            (retention returns a dict of {table: count}).
        is_retention: If True, sum dict values for records_deleted.
    """
    from database import SessionLocal

    started_at = datetime.now(UTC)
    t0 = time.perf_counter()
    records_processed = 0
    error_msg: str | None = None
    db = SessionLocal()

    try:
        result = cleanup_func(db)
        if is_retention and isinstance(result, dict):
            records_processed = sum(result.values())
        else:
            records_processed = int(result)
    except Exception as exc:
        from shared.log_sanitizer import sanitize_exception
        error_msg = sanitize_exception(exc)
    finally:
        db.close()

    duration_ms = (time.perf_counter() - t0) * 1000
    _last_run_times[job_name] = started_at

    telemetry = CleanupTelemetry(
        job_name=job_name,
        started_at=started_at.isoformat(),
        duration_ms=duration_ms,
        records_processed=records_processed,
        error=error_msg,
    )

    if error_msg:
        logger.error("Cleanup job failed: %s", telemetry.to_log_dict())
    elif records_processed > 0:
        logger.info("Cleanup job completed: %s", telemetry.to_log_dict())
    else:
        logger.debug("Cleanup job no-op: %s", telemetry.to_log_dict())


# ---------------------------------------------------------------------------
# Thin job wrappers (lazy imports to avoid circular dependencies)
# ---------------------------------------------------------------------------

def _job_refresh_tokens() -> None:
    from auth import cleanup_expired_refresh_tokens
    _run_cleanup_job("refresh_tokens", cleanup_expired_refresh_tokens)


def _job_verification_tokens() -> None:
    from auth import cleanup_expired_verification_tokens
    _run_cleanup_job("verification_tokens", cleanup_expired_verification_tokens)


def _job_tool_sessions() -> None:
    from tool_session_model import cleanup_expired_tool_sessions
    _run_cleanup_job("tool_sessions", cleanup_expired_tool_sessions)


def _job_retention_cleanup() -> None:
    from retention_cleanup import run_retention_cleanup
    _run_cleanup_job("retention_cleanup", run_retention_cleanup, is_retention=True)


# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------

def _watchdog() -> None:
    """Check if any cleanup job is overdue by more than 2x its expected interval."""
    now = datetime.now(UTC)
    for job_name, expected_interval in _EXPECTED_INTERVALS.items():
        last_run = _last_run_times.get(job_name)
        if last_run is None:
            # Job hasn't run yet — skip (startup grace period)
            continue
        overdue_threshold = expected_interval * 2
        elapsed = now - last_run
        if elapsed > overdue_threshold:
            logger.warning(
                "Cleanup job '%s' is overdue: last ran %s ago (expected every %s)",
                job_name,
                elapsed,
                expected_interval,
            )


# ---------------------------------------------------------------------------
# Scheduler lifecycle
# ---------------------------------------------------------------------------

def init_scheduler() -> None:
    """Start the background cleanup scheduler.

    No-op if CLEANUP_SCHEDULER_ENABLED is False.
    Called from main.py lifespan after startup cleanup.
    """
    global _scheduler

    if not CLEANUP_SCHEDULER_ENABLED:
        logger.info("Cleanup scheduler disabled (CLEANUP_SCHEDULER_ENABLED=false)")
        return

    from apscheduler.executors.pool import ThreadPoolExecutor
    from apscheduler.schedulers.background import BackgroundScheduler

    _scheduler = BackgroundScheduler(
        executors={"default": ThreadPoolExecutor(max_workers=1)},
        job_defaults={"coalesce": True, "max_instances": 1},
    )

    _scheduler.add_job(
        _job_refresh_tokens,
        "interval",
        minutes=CLEANUP_REFRESH_TOKEN_INTERVAL_MINUTES,
        id="cleanup_refresh_tokens",
    )
    _scheduler.add_job(
        _job_verification_tokens,
        "interval",
        minutes=CLEANUP_VERIFICATION_TOKEN_INTERVAL_MINUTES,
        id="cleanup_verification_tokens",
    )
    _scheduler.add_job(
        _job_tool_sessions,
        "interval",
        minutes=CLEANUP_TOOL_SESSION_INTERVAL_MINUTES,
        id="cleanup_tool_sessions",
    )
    _scheduler.add_job(
        _job_retention_cleanup,
        "interval",
        hours=CLEANUP_RETENTION_INTERVAL_HOURS,
        id="cleanup_retention",
    )
    _scheduler.add_job(
        _watchdog,
        "interval",
        minutes=WATCHDOG_INTERVAL_MINUTES,
        id="cleanup_watchdog",
    )

    _scheduler.start()
    logger.info(
        "Cleanup scheduler started: refresh=%dmin, verification=%dmin, "
        "tool_sessions=%dmin, retention=%dh, watchdog=%dmin",
        CLEANUP_REFRESH_TOKEN_INTERVAL_MINUTES,
        CLEANUP_VERIFICATION_TOKEN_INTERVAL_MINUTES,
        CLEANUP_TOOL_SESSION_INTERVAL_MINUTES,
        CLEANUP_RETENTION_INTERVAL_HOURS,
        WATCHDOG_INTERVAL_MINUTES,
    )


def shutdown_scheduler() -> None:
    """Stop the background cleanup scheduler.

    Safe to call even if scheduler was never started or already shut down.
    Called from main.py lifespan shutdown.
    """
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Cleanup scheduler stopped")
