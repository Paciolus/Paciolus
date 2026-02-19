"""
Paciolus API — Health & Waitlist Routes

Endpoints:
  GET /health       — Legacy shallow/deep probe (backward compat)
  GET /health/live  — Liveness probe: static, zero I/O (restart decisions)
  GET /health/ready — Readiness probe: DB + pool stats (traffic routing)
  POST /waitlist    — Email waitlist signup
"""
import csv
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from security_utils import log_secure_operation
from shared.log_sanitizer import mask_email
from shared.rate_limits import limiter
from version import __version__

router = APIRouter(tags=["health"])

WAITLIST_FILE = Path(__file__).parent.parent / "waitlist.csv"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class WaitlistEntry(BaseModel):
    email: EmailStr


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    database: Optional[str] = None


class WaitlistResponse(BaseModel):
    success: bool
    message: str


class LivenessResponse(BaseModel):
    status: Literal["healthy"]
    timestamp: str
    version: str


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
async def health_check(deep: bool = Query(False, description="Include database connectivity check")):
    """Legacy health probe. Prefer /health/live (liveness) and /health/ready (readiness)."""
    if not deep:
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(UTC).isoformat(),
            version=__version__,
        )

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
                version=__version__,
                database="unreachable",
            ).model_dump(),
        )

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        version=__version__,
        database=db_status,
    )


# ---------------------------------------------------------------------------
# GET /health/live — liveness probe
# ---------------------------------------------------------------------------

@router.get("/health/live", response_model=LivenessResponse)
async def liveness_probe():
    """Liveness probe — orchestrator should use this for restart decisions.

    Pure static response with zero I/O. If the process can serve this,
    it is alive and should NOT be restarted.
    """
    return LivenessResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        version=__version__,
    )


# ---------------------------------------------------------------------------
# GET /health/ready — readiness probe
# ---------------------------------------------------------------------------

@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_probe():
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

        # Pool statistics (QueuePool for PostgreSQL, StaticPool/NullPool for SQLite)
        pool = engine.pool
        pool_details: dict = {"pool_class": type(pool).__name__}
        if hasattr(pool, "size"):
            pool_details.update({
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            })
        else:
            pool_details["note"] = "Pool statistics not available for this dialect"

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


@router.post("/waitlist", response_model=WaitlistResponse, status_code=201)
@limiter.limit("3/minute")
async def join_waitlist(request: Request, entry: WaitlistEntry):
    """Add email to waitlist (only non-ephemeral storage in the system)."""
    try:
        file_exists = WAITLIST_FILE.exists()

        with open(WAITLIST_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["email", "timestamp"])
            writer.writerow([entry.email, datetime.now(UTC).isoformat()])

        log_secure_operation("waitlist_signup", f"New signup: {mask_email(entry.email)}")

        return WaitlistResponse(
            success=True,
            message="You're on the list! We'll be in touch soon."
        )

    except OSError as e:
        logger.exception("Waitlist CSV write failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to join waitlist. Please try again."
        )
