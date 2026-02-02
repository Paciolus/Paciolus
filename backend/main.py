"""
CloseSignify Backend
Trial Balance Auditor for Fractional CFOs
"""

import csv
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from security_utils import log_secure_operation, clear_memory
from audit_engine import audit_trial_balance_streaming, DEFAULT_CHUNK_SIZE

# Import config (will hard fail if .env is missing)
from config import API_HOST, API_PORT, CORS_ORIGINS, DEBUG, print_config_summary

app = FastAPI(
    title="CloseSignify API",
    description="Trial Balance Auditor for Fractional CFOs",
    version="0.1.0"
)

# CORS configuration from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Waitlist file path (only storage exception per security policy)
WAITLIST_FILE = Path(__file__).parent / "waitlist.csv"


class WaitlistEntry(BaseModel):
    email: EmailStr


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class WaitlistResponse(BaseModel):
    success: bool
    message: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns API status and version information.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="0.1.0"
    )


@app.post("/waitlist", response_model=WaitlistResponse)
async def join_waitlist(entry: WaitlistEntry):
    """
    Add an email to the waitlist.
    This is the ONLY storage exception per the Zero-Storage policy.
    Waitlist contains no accounting data.
    """
    try:
        # Check if file exists, create with header if not
        file_exists = WAITLIST_FILE.exists()

        with open(WAITLIST_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["email", "timestamp"])
            writer.writerow([entry.email, datetime.utcnow().isoformat()])

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


@app.post("/audit/trial-balance")
async def audit_trial_balance(
    file: UploadFile = File(...),
    materiality_threshold: float = Form(default=0.0, ge=0.0)
):
    """
    Analyze a trial balance file for balance validation using streaming processing.

    HIGH-PERFORMANCE: File is processed in chunks for memory efficiency.
    Handles files larger than available RAM.

    ZERO-STORAGE: All processing is in-memory. No data written to disk.

    Accepts CSV or Excel files with 'Debit' and 'Credit' columns.

    Args:
        file: The trial balance file (CSV or Excel)
        materiality_threshold: Dollar amount threshold for materiality classification.
            Balances below this threshold are marked as "immaterial" (Indistinct).
            Default: 0.0 (flag all abnormal balances as material)
    """
    log_secure_operation(
        "audit_upload_streaming",
        f"Processing file: {file.filename} (threshold: ${materiality_threshold:,.2f}, chunk_size: {DEFAULT_CHUNK_SIZE})"
    )

    try:
        # Read file bytes into memory - NO DISK STORAGE
        file_bytes = await file.read()

        # Use streaming audit for memory-efficient processing
        result = audit_trial_balance_streaming(
            file_bytes=file_bytes,
            filename=file.filename or "",
            materiality_threshold=materiality_threshold,
            chunk_size=DEFAULT_CHUNK_SIZE
        )

        # Clear file bytes after processing
        del file_bytes
        clear_memory()

        return result

    except Exception as e:
        log_secure_operation("audit_error", str(e))
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process file: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    print_config_summary()
    uvicorn.run(app, host=API_HOST, port=API_PORT)
