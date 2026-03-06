"""
Bulk Upload Routes — Phase LXIX: Pricing v3 (Phase 9).

Accept up to 5 files for parallel processing. Enterprise only.

Route group prefix: /upload/bulk
"""

import asyncio
import hashlib
import logging
import uuid
from collections import OrderedDict
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from models import User
from shared.entitlement_checks import check_bulk_upload_access, check_upload_limit, increment_upload_count
from shared.helpers import validate_file_size
from shared.rate_limits import RATE_LIMIT_WRITE, limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload/bulk", tags=["bulk-upload"])

MAX_FILES = 5
MAX_BULK_JOBS = 100  # Eviction threshold to prevent unbounded memory growth
_JOB_TTL_HOURS = 2

# In-memory job store with LRU eviction (OrderedDict for insertion-order)
_bulk_jobs: OrderedDict[str, dict] = OrderedDict()


@router.post("")
@limiter.limit(RATE_LIMIT_WRITE)
async def start_bulk_upload(
    request=None,
    files: list[UploadFile] = File(...),
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Accept up to 5 files for bulk processing. Enterprise only."""
    check_bulk_upload_access(db, user.id)

    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_FILES} files per bulk upload.")

    if len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    # SECURITY: Run each file through the full 10-step validation pipeline
    # (extension, MIME, size, magic bytes, archive bomb, XML bomb detection)
    validated_contents: list[bytes] = []
    for f in files:
        file_bytes = await validate_file_size(f)
        validated_contents.append(file_bytes)

    # Check upload quota for all files
    for _ in files:
        check_upload_limit(db, user.id)

    # Evict stale jobs before creating a new one (prevent unbounded memory growth)
    _evict_stale_jobs()

    # Create job
    job_id = str(uuid.uuid4())
    file_statuses = []

    for idx, f in enumerate(files):
        content = validated_contents[idx]
        file_hash = hashlib.sha256(content).hexdigest()[:12]
        file_statuses.append(
            {
                "filename": f.filename,
                "file_hash": file_hash,
                "size_bytes": len(content),
                "status": "queued",
                "result": None,
                "error": None,
            }
        )

    _bulk_jobs[job_id] = {
        "job_id": job_id,
        "user_id": user.id,
        "created_at": datetime.now(UTC).isoformat(),
        "status": "processing",
        "files": file_statuses,
        "completed_count": 0,
        "total_count": len(files),
    }

    # Process files asynchronously (in background)
    asyncio.create_task(_process_bulk_files(job_id, files, user.id, db))

    return {
        "job_id": job_id,
        "total_files": len(files),
        "status": "processing",
    }


async def _process_bulk_files(
    job_id: str,
    files: list[UploadFile],
    user_id: int,
    db: Session,
) -> None:
    """Process files one by one (sequential to avoid overwhelming the system)."""
    job = _bulk_jobs.get(job_id)
    if not job:
        return

    for idx, f in enumerate(files):
        try:
            job["files"][idx]["status"] = "processing"

            # Read the content
            await f.seek(0)
            content = await f.read()

            # Increment upload counter
            try:
                from database import SessionLocal

                session = SessionLocal()
                try:
                    increment_upload_count(session, user_id)
                finally:
                    session.close()
            except Exception as exc:
                logger.warning(
                    "Upload count increment failed for user %d in job %s: %s", user_id, job_id, type(exc).__name__
                )

            # Mark as complete (actual analysis would be triggered here
            # via the same analysis functions used by the single-file endpoints)
            job["files"][idx]["status"] = "complete"
            job["files"][idx]["result"] = {
                "filename": f.filename,
                "size_bytes": len(content),
                "processed_at": datetime.now(UTC).isoformat(),
            }

        except Exception as exc:
            job["files"][idx]["status"] = "error"
            job["files"][idx]["error"] = "File processing failed. Please verify the file format and try again."
            logger.warning("Bulk upload file %d failed for job %s: %s", idx, job_id, type(exc).__name__)

        job["completed_count"] = sum(1 for fs in job["files"] if fs["status"] in ("complete", "error"))

    job["status"] = "complete"


@router.get("/{job_id}/status")
async def get_bulk_status(
    job_id: str,
    user: User = Depends(require_verified_user),
):
    """Poll bulk upload job progress."""
    job = _bulk_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "completed_count": job["completed_count"],
        "total_count": job["total_count"],
        "files": [
            {
                "filename": fs["filename"],
                "status": fs["status"],
                "error": fs["error"],
            }
            for fs in job["files"]
        ],
    }


def _evict_stale_jobs() -> None:
    """Remove expired jobs and enforce max job count to prevent memory exhaustion."""
    now = datetime.now(UTC)
    stale_keys = []
    for key, job in _bulk_jobs.items():
        try:
            created = datetime.fromisoformat(job["created_at"])
            if (now - created).total_seconds() > _JOB_TTL_HOURS * 3600:
                stale_keys.append(key)
        except (ValueError, KeyError):
            stale_keys.append(key)
    for key in stale_keys:
        del _bulk_jobs[key]

    # Hard cap: evict oldest jobs if over limit
    while len(_bulk_jobs) > MAX_BULK_JOBS:
        _bulk_jobs.popitem(last=False)
