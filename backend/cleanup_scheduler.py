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
- AUDIT-06 FIX 3: DB-backed execution lock prevents multi-worker duplication

Telemetry:
- Structured logging only (aggregate counts, durations) — Zero-Storage compliant
- No financial data, PII, or account details in any log entry

Watchdog:
- Runs every 5 minutes, warns if any job is overdue by >2x its interval
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

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
    "verify_database_tls": timedelta(hours=24),
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
# AUDIT-06 FIX 3: DB-backed execution lock
# ---------------------------------------------------------------------------

_WORKER_ID = f"worker-{os.getpid()}"


@contextmanager
def with_scheduler_lock(job_name: str, db: Any, ttl_seconds: int = 600) -> Generator[bool, None, None]:
    """Acquire a DB-backed lock for a scheduled job.

    Uses INSERT ... ON CONFLICT to atomically acquire the lock.
    If the lock is held and not expired, skips execution.
    On completion, deletes the lock row.

    Yields True if lock was acquired, False if skipped.
    """
    from sqlalchemy import text

    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=ttl_seconds)

    # Attempt upsert: acquire lock if not held or expired
    # Works on both PostgreSQL (ON CONFLICT) and SQLite (ON CONFLICT)
    result = db.execute(
        text(
            "INSERT INTO scheduler_locks (job_name, locked_at, locked_by, expires_at) "
            "VALUES (:job_name, :locked_at, :locked_by, :expires_at) "
            "ON CONFLICT (job_name) DO UPDATE "
            "SET locked_at = :locked_at, locked_by = :locked_by, expires_at = :expires_at "
            "WHERE scheduler_locks.expires_at < :now"
        ),
        {
            "job_name": job_name,
            "locked_at": now,
            "locked_by": _WORKER_ID,
            "expires_at": expires_at,
            "now": now,
        },
    )
    db.commit()

    if result.rowcount == 0:
        # Lock is held by another worker and not expired — skip
        logger.debug("Scheduler lock held for '%s', skipping", job_name)
        yield False
        return

    try:
        yield True
    finally:
        # Release lock on completion
        db.execute(
            text("DELETE FROM scheduler_locks WHERE job_name = :job_name AND locked_by = :locked_by"),
            {"job_name": job_name, "locked_by": _WORKER_ID},
        )
        db.commit()


# ---------------------------------------------------------------------------
# Generic job wrapper
# ---------------------------------------------------------------------------


def _run_cleanup_job(
    job_name: str,
    cleanup_func: Callable[..., object],
    *,
    is_retention: bool = False,
) -> None:
    """Execute a cleanup function with telemetry, DB-backed lock, and its own DB session.

    AUDIT-06 FIX 3: Acquires a DB lock before executing to prevent
    multi-worker duplication under Gunicorn WEB_CONCURRENCY > 1.

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
    caught_exc: BaseException | None = None
    db = SessionLocal()

    try:
        with with_scheduler_lock(job_name, db) as acquired:
            if not acquired:
                return  # Another worker holds the lock

            result = cleanup_func(db)
            if is_retention and isinstance(result, dict):
                records_processed = sum(result.values())
            else:
                records_processed = int(str(result))
    except Exception as exc:
        from shared.log_sanitizer import sanitize_exception

        error_msg = sanitize_exception(exc, context="scheduled cleanup")
        caught_exc = exc

        # Sprint 711 Bug 2: capture exception explicitly while still inside the
        # except block so the traceback survives. The deferred logger.error
        # below loses sys.exc_info() context; Sentry's logging integration was
        # only attaching the message, dropping the actual exception type +
        # frames (104 events accumulated as untriageable "InternalError").
        try:
            import sentry_sdk

            sentry_sdk.capture_exception(exc)
        except Exception:  # noqa: BLE001 — telemetry must never mask the original
            pass
    finally:
        # Defensive rollback: if cleanup_func or with_scheduler_lock raised
        # mid-transaction, the session can be in an aborted state. close()
        # alone does not always recover the connection cleanly under psycopg2
        # — explicit rollback first prevents subsequent jobs from inheriting
        # a poisoned connection out of the pool.
        try:
            db.rollback()
        except Exception:  # noqa: BLE001 — best-effort cleanup
            pass
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
        logger.error("Cleanup job failed: %s", telemetry.to_log_dict(), exc_info=caught_exc)
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


def _job_reset_upload_quotas() -> None:
    """Reset upload counters for subscriptions past their billing period end.

    AUDIT-06 FIX 3: Uses atomic UPDATE instead of read-then-write to prevent
    race conditions with concurrent upload increments.
    """

    def _reset(db: Any) -> int:
        from sqlalchemy import text

        now = datetime.now(UTC)
        # Atomic UPDATE — no read→write race with concurrent upload increments
        result = db.execute(
            text(
                "UPDATE subscriptions "
                "SET uploads_used_current_period = 0 "
                "WHERE status = 'active' "
                "AND current_period_end IS NOT NULL "
                "AND current_period_end <= :now "
                "AND uploads_used_current_period > 0"
            ),
            {"now": now},
        )
        count = int(result.rowcount)
        if count > 0:
            db.commit()
        return count

    _run_cleanup_job("reset_upload_quotas", _reset)


def purge_expired_export_shares(db: Any) -> int:
    """Delete expired or revoked export-share rows and their R2 objects.

    Sprint 611: rows whose bytes live in R2 also have the bucket object
    deleted.  R2 deletion is best-effort — a failure here logs and moves
    on rather than blocking the DB purge, since the next cleanup pass
    will retry and the object key is hash-deterministic (no orphan
    proliferation from retries).

    Module-level (not nested) so the behaviour is directly testable
    without running the full APScheduler wrapper.
    """
    from export_share_model import ExportShare
    from shared import export_share_storage

    now = datetime.now(UTC)
    expired = db.query(ExportShare).filter(ExportShare.expires_at <= now).all()
    revoked = db.query(ExportShare).filter(ExportShare.revoked_at.isnot(None)).all()
    doomed = {s.id: s for s in expired}
    doomed.update({s.id: s for s in revoked})
    if not doomed:
        return 0

    for share in doomed.values():
        key = share.object_key
        if key:
            export_share_storage.delete(key)  # best-effort; logs on failure

    db.query(ExportShare).filter(ExportShare.id.in_(doomed.keys())).delete(synchronize_session=False)
    db.commit()
    return len(doomed)


def _job_expired_export_shares() -> None:
    """Scheduler entry-point wrapping ``purge_expired_export_shares``."""
    _run_cleanup_job("expired_export_shares", purge_expired_export_shares)


def _job_bulk_upload_cleanup() -> None:
    """Evict stale in-memory bulk upload jobs (2h TTL + hard cap).

    AUDIT-06 FIX 3: DB-locked to prevent multi-worker duplication.
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        with with_scheduler_lock("bulk_upload_cleanup", db) as acquired:
            if not acquired:
                return

            from routes.bulk_upload import _evict_stale_jobs

            _evict_stale_jobs()
    except Exception as exc:
        from shared.log_sanitizer import sanitize_exception

        logger.error("Bulk upload cleanup failed: %s", sanitize_exception(exc, context="bulk upload cleanup"))
    finally:
        db.close()


def _job_team_activity_cleanup() -> None:
    """Purge team activity logs older than 90 days."""

    def _purge(db: Any) -> int:
        from team_activity_model import TeamActivityLog

        cutoff = datetime.now(UTC) - timedelta(days=90)
        count = int(
            db.query(TeamActivityLog).filter(TeamActivityLog.created_at < cutoff).delete(synchronize_session=False)
        )
        if count:
            db.commit()
        return count

    _run_cleanup_job("team_activity_cleanup", _purge)


def _job_expired_upload_dedup() -> None:
    """Purge expired upload dedup rows (5-minute TTL).

    AUDIT-06 FIX 4: Piggybacks on the scheduler to keep the dedup table lean.
    """

    def _purge(db: Any) -> int:
        from sqlalchemy import text

        now = datetime.now(UTC)
        result = db.execute(
            text("DELETE FROM upload_dedup WHERE expires_at <= :now"),
            {"now": now},
        )
        count = int(result.rowcount)
        if count > 0:
            db.commit()
        return count

    _run_cleanup_job("expired_upload_dedup", _purge)


# ---------------------------------------------------------------------------
# Dunning grace period expiration (Sprint 591)
# ---------------------------------------------------------------------------


def _job_dunning_grace_period() -> None:
    """Cancel subscriptions whose dunning grace period has expired."""

    def _process(db: Any) -> int:
        from billing.dunning_engine import process_grace_period_expirations

        return process_grace_period_expirations(db)

    _run_cleanup_job("dunning_grace_period", _process)


# ---------------------------------------------------------------------------
# Daily DB TLS verification (continuous evidence)
# ---------------------------------------------------------------------------


def _job_verify_database_tls() -> None:
    """Daily TLS verification — writes HMAC-signed evidence artifact.

    Queries pg_stat_ssl to confirm the database connection is encrypted,
    then emits a signed structured security event as continuous audit evidence.
    """
    import hashlib
    import hmac

    from sqlalchemy import text

    from database import SessionLocal, engine
    from security_utils import log_secure_operation

    if engine.dialect.name != "postgresql":
        return  # SQLite in dev — nothing to verify

    db = SessionLocal()
    try:
        ssl_row = db.execute(text("SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")).fetchone()
        ssl_active = bool(ssl_row and ssl_row[0])

        timestamp = datetime.now(UTC).isoformat()
        status = "active" if ssl_active else "INACTIVE"

        # HMAC-sign the evidence using audit chain secret for tamper evidence
        from config import AUDIT_CHAIN_SECRET_KEY

        evidence_payload = f"db_tls_check|{status}|{timestamp}"
        signature = hmac.new(AUDIT_CHAIN_SECRET_KEY.encode(), evidence_payload.encode(), hashlib.sha256).hexdigest()[
            :16
        ]

        log_secure_operation(
            "db_tls_daily_check",
            f"tls={status}, timestamp={timestamp}, sig={signature}",
        )

        if ssl_active:
            logger.info("Daily DB TLS check: tls=active, sig=%s", signature)
        else:
            logger.warning(
                "Daily DB TLS check: tls=INACTIVE — database connection is unencrypted. sig=%s",
                signature,
            )
    except Exception:
        logger.warning("Daily DB TLS verification check failed", exc_info=True)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------


def _watchdog() -> None:
    """Check if any cleanup job is overdue by more than 2x its expected interval.

    AUDIT-06 FIX 3: DB-locked to prevent multi-worker duplication.
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        with with_scheduler_lock("cleanup_watchdog", db, ttl_seconds=60) as acquired:
            if not acquired:
                return

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
    finally:
        db.close()


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
        jitter=30,
    )
    _scheduler.add_job(
        _job_verification_tokens,
        "interval",
        minutes=CLEANUP_VERIFICATION_TOKEN_INTERVAL_MINUTES,
        id="cleanup_verification_tokens",
        jitter=30,
    )
    _scheduler.add_job(
        _job_tool_sessions,
        "interval",
        minutes=CLEANUP_TOOL_SESSION_INTERVAL_MINUTES,
        id="cleanup_tool_sessions",
        jitter=30,
    )
    _scheduler.add_job(
        _job_retention_cleanup,
        "interval",
        hours=CLEANUP_RETENTION_INTERVAL_HOURS,
        id="cleanup_retention",
        jitter=60,
    )
    _scheduler.add_job(
        _job_reset_upload_quotas,
        "interval",
        hours=1,
        id="reset_upload_quotas",
        jitter=30,
    )
    _scheduler.add_job(
        _job_expired_export_shares,
        "interval",
        hours=1,
        id="expired_export_shares",
        jitter=30,
    )
    _scheduler.add_job(
        _job_team_activity_cleanup,
        "interval",
        hours=24,
        id="team_activity_cleanup",
        jitter=120,
    )
    _scheduler.add_job(
        _job_bulk_upload_cleanup,
        "interval",
        minutes=30,
        id="bulk_upload_cleanup",
        jitter=30,
    )
    _scheduler.add_job(
        _job_expired_upload_dedup,
        "interval",
        hours=1,
        id="expired_upload_dedup",
        jitter=30,
    )
    # Sprint 591: Dunning grace period expiration — runs hourly
    _scheduler.add_job(
        _job_dunning_grace_period,
        "interval",
        hours=1,
        id="dunning_grace_period",
        jitter=60,
    )
    # Daily DB TLS verification — continuous evidence for audit
    _scheduler.add_job(
        _job_verify_database_tls,
        "interval",
        hours=24,
        id="verify_database_tls",
        jitter=120,
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
