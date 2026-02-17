"""
Paciolus API — Health & Waitlist Routes
"""
import csv
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import text

from security_utils import log_secure_operation
from shared.rate_limits import limiter
from version import __version__

router = APIRouter(tags=["health"])

WAITLIST_FILE = Path(__file__).parent.parent / "waitlist.csv"


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


@router.get("/health", response_model=HealthResponse)
async def health_check(deep: bool = Query(False, description="Include database connectivity check")):
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
    except Exception:
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

        log_secure_operation("waitlist_signup", f"New signup: {entry.email[:3]}***")

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
