"""
Paciolus API — Health & Waitlist Routes
"""
import csv
from datetime import datetime, UTC
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

from security_utils import log_secure_operation
from version import __version__
from shared.rate_limits import limiter

router = APIRouter(tags=["health"])

WAITLIST_FILE = Path(__file__).parent.parent / "waitlist.csv"


class WaitlistEntry(BaseModel):
    email: EmailStr


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class WaitlistResponse(BaseModel):
    success: bool
    message: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        version=__version__
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

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to join waitlist. Please try again."
        )
