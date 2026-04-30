"""
Paciolus API — Health & Waitlist Routes

Endpoints:
  GET /health         — Legacy shallow/deep probe (backward compat)
  GET /health/live    — Liveness probe: static, zero I/O (restart decisions)
  GET /health/ready   — Readiness probe: DB + pool stats (traffic routing)
  GET /health/redis   — Redis availability probe (Sprint 730; only meaningful
                        when REDIS_URL is set — slowapi rate-limit storage)
  GET /health/r2      — R2 export-share-storage probe (Sprint 730; only
                        meaningful when R2 env vars are configured)
  POST /waitlist      — Email waitlist signup
"""

import logging
import time
from datetime import UTC, datetime
from typing import Literal, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from models import WaitlistSignup
from security_utils import log_secure_operation
from shared.log_sanitizer import mask_email
from shared.rate_limits import RATE_LIMIT_HEALTH, limiter
from version import __version__

router = APIRouter(tags=["health"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class WaitlistRequest(BaseModel):
    email: EmailStr


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: Optional[str] = None


class WaitlistResponse(BaseModel):
    success: bool
    message: str


class LivenessResponse(BaseModel):
    status: Literal["healthy"]
    timestamp: str
    # Exact version intentionally omitted from the public liveness response.
    # External fingerprinting via /health/live let scanners pin exploit
    # attempts to a known build; the orchestrator only needs status to
    # decide whether to restart. /health/ready (operationally scoped)
    # continues to expose version for internal readiness reporting.


class DependencyStatus(BaseModel):
    status: Literal["healthy", "unhealthy"]
    latency_ms: float
    details: dict | None = None


class ReadinessResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: str
    version: str
    dependencies: dict[str, DependencyStatus]


# ---------------------------------------------------------------------------
# GET /health — legacy (kept for backward compat)
# ---------------------------------------------------------------------------


@router.get("/health", response_model=HealthResponse)
@limiter.limit(RATE_LIMIT_HEALTH)
async def health_check(
    request: Request, response: Response, deep: bool = Query(False, description="Include database connectivity check")
) -> HealthResponse:
    """Legacy health probe. Prefer /health/live (liveness) and /health/ready (readiness)."""
    if not deep:
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(UTC).isoformat(),
        )

    # Signal deprecation — clients should migrate to /health/ready
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</health/ready>; rel="successor-version"'

    # Deep probe: verify DB connectivity with SELECT 1
    from database import SessionLocal

    db_status = "connected"
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except (SQLAlchemyError, OSError):
        logger.exception("Deep health check: database unreachable")
        raise HTTPException(
            status_code=503,
            detail=HealthResponse(
                status="unhealthy",
                timestamp=datetime.now(UTC).isoformat(),
                database="unreachable",
            ).model_dump(),
        )

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        database=db_status,
    )


# ---------------------------------------------------------------------------
# GET /health/live — liveness probe
# ---------------------------------------------------------------------------


@router.get("/health/live", response_model=LivenessResponse)
@limiter.limit(RATE_LIMIT_HEALTH)
async def liveness_probe(request: Request) -> LivenessResponse:
    """Liveness probe — orchestrator should use this for restart decisions.

    Pure static response with zero I/O. If the process can serve this,
    it is alive and should NOT be restarted.
    """
    return LivenessResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# GET /health/ready — readiness probe
# ---------------------------------------------------------------------------


@router.get("/health/ready", response_model=ReadinessResponse)
@limiter.limit(RATE_LIMIT_HEALTH)
async def readiness_probe(request: Request) -> ReadinessResponse:
    """Readiness probe — load balancer should use this for traffic routing.

    Checks database connectivity with SELECT 1, measures latency, and
    reports connection pool statistics when available (PostgreSQL).

    Note: No Redis, Celery, or cache dependencies exist — database is
    the only dependency.
    """
    from database import SessionLocal, engine

    # --- Database check ---
    start = time.perf_counter()
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
        latency_ms = (time.perf_counter() - start) * 1000

        # Pool statistics — expose only in non-production to prevent
        # operational data leakage (pool size, connection counts)
        from config import ENV_MODE

        pool_details: dict | None = None
        if ENV_MODE != "production":
            pool = engine.pool
            pool_details = {"pool_class": type(pool).__name__}
            if hasattr(pool, "size"):
                pool_details.update(
                    {
                        "pool_size": pool.size(),
                        "checked_in": pool.checkedin(),  # type: ignore[attr-defined]
                        "checked_out": pool.checkedout(),  # type: ignore[attr-defined]
                        "overflow": pool.overflow(),  # type: ignore[attr-defined]
                    }
                )

        db_dep = DependencyStatus(
            status="healthy",
            latency_ms=round(latency_ms, 2),
            details=pool_details,
        )
        return ReadinessResponse(
            status="healthy",
            timestamp=datetime.now(UTC).isoformat(),
            version=__version__,
            dependencies={"database": db_dep},
        )

    except (SQLAlchemyError, OSError):
        latency_ms = (time.perf_counter() - start) * 1000
        logger.exception("Readiness probe: database unreachable")
        db_dep = DependencyStatus(
            status="unhealthy",
            latency_ms=round(latency_ms, 2),
        )
        raise HTTPException(
            status_code=503,
            detail=ReadinessResponse(
                status="unhealthy",
                timestamp=datetime.now(UTC).isoformat(),
                version=__version__,
                dependencies={"database": db_dep},
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# GET /health/redis — Sprint 730 Redis availability probe
# ---------------------------------------------------------------------------


@router.get("/health/redis", response_model=DependencyStatus)
@limiter.limit(RATE_LIMIT_HEALTH)
async def redis_probe(request: Request) -> DependencyStatus:
    """Redis availability probe (Sprint 730).

    When REDIS_URL is set, slowapi uses Redis as its rate-limit storage and a
    Redis outage degrades the rate limiter to fail-open. This probe makes the
    Redis health an explicit signal so an oncall alert can fire on probe
    failures rather than waiting for a credential-stuffing burst to surface
    the silent fail-open.

    When REDIS_URL is NOT set (single-worker deployments, dev), returns
    ``healthy`` with ``details.redis="not_configured"`` — the rate limiter is
    using its in-memory fallback and there's nothing to probe.
    """
    import os

    start = time.perf_counter()
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if not redis_url:
        latency_ms = (time.perf_counter() - start) * 1000
        return DependencyStatus(
            status="healthy",
            latency_ms=round(latency_ms, 2),
            details={"redis": "not_configured"},
        )

    try:
        import redis as redis_lib  # noqa: WPS433  — soft import; redis is optional
    except ImportError:
        latency_ms = (time.perf_counter() - start) * 1000
        return DependencyStatus(
            status="unhealthy",
            latency_ms=round(latency_ms, 2),
            details={"redis": "library_missing"},
        )

    try:
        client = redis_lib.from_url(redis_url, socket_timeout=2, socket_connect_timeout=2)
        pong = client.ping()
        latency_ms = (time.perf_counter() - start) * 1000
        if pong:
            return DependencyStatus(
                status="healthy",
                latency_ms=round(latency_ms, 2),
                details={"redis": "connected"},
            )
        return DependencyStatus(
            status="unhealthy",
            latency_ms=round(latency_ms, 2),
            details={"redis": "ping_returned_false"},
        )
    except Exception as exc:  # noqa: BLE001 — broad on purpose; Redis client raises many subclasses
        latency_ms = (time.perf_counter() - start) * 1000
        logger.warning("Redis health probe failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail=DependencyStatus(
                status="unhealthy",
                latency_ms=round(latency_ms, 2),
                details={"redis": type(exc).__name__},
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# GET /health/r2 — Sprint 730 R2 export-share-storage probe
# ---------------------------------------------------------------------------


@router.get("/health/r2", response_model=DependencyStatus)
@limiter.limit(RATE_LIMIT_HEALTH)
async def r2_probe(request: Request) -> DependencyStatus:
    """R2 export-share-storage availability probe (Sprint 730).

    When R2 is configured (R2_EXPORTS_* env vars set), this lists the bucket
    head to verify auth + connectivity. When R2 is not configured, returns
    ``healthy`` with ``details.r2="not_configured"``.

    The probe does NOT touch user data — it only verifies that the bucket is
    reachable with the configured credentials. The mass-410-vs-503 distinction
    in ``export_share_storage.download()`` is what handles per-object errors;
    this endpoint is about whether R2 is reachable at all.
    """
    from shared import export_share_storage

    start = time.perf_counter()
    if not export_share_storage.is_configured():
        latency_ms = (time.perf_counter() - start) * 1000
        return DependencyStatus(
            status="healthy",
            latency_ms=round(latency_ms, 2),
            details={"r2": "not_configured"},
        )

    try:
        # head_bucket is the canonical "is the bucket reachable + are my creds
        # valid" probe in S3-compatible APIs. Doesn't list any objects.
        client = export_share_storage._get_client()  # noqa: SLF001 — module-internal probe
        bucket = export_share_storage._bucket_name  # noqa: SLF001
        if client is None or bucket is None:
            latency_ms = (time.perf_counter() - start) * 1000
            return DependencyStatus(
                status="unhealthy",
                latency_ms=round(latency_ms, 2),
                details={"r2": "client_not_initialized"},
            )
        client.head_bucket(Bucket=bucket)
        latency_ms = (time.perf_counter() - start) * 1000
        return DependencyStatus(
            status="healthy",
            latency_ms=round(latency_ms, 2),
            details={"r2": "reachable", "bucket": bucket},
        )
    except Exception as exc:  # noqa: BLE001 — botocore raises many subclasses
        latency_ms = (time.perf_counter() - start) * 1000
        logger.warning("R2 health probe failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail=DependencyStatus(
                status="unhealthy",
                latency_ms=round(latency_ms, 2),
                details={"r2": type(exc).__name__},
            ).model_dump(),
        )


@router.post("/waitlist", response_model=WaitlistResponse, status_code=201)
@limiter.limit("3/minute")
async def join_waitlist(request: Request, entry: WaitlistRequest, db: Session = Depends(get_db)) -> WaitlistResponse:
    """Add email to waitlist (database-backed with dedup)."""
    try:
        signup = WaitlistSignup(email=entry.email)
        db.add(signup)
        db.commit()
        log_secure_operation("waitlist_signup", f"New signup: {mask_email(entry.email)}")
    except IntegrityError:
        db.rollback()
        # Duplicate email — return success silently (no information leakage)

    return WaitlistResponse(success=True, message="You're on the list! We'll be in touch soon.")
