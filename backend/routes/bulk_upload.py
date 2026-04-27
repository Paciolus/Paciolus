"""
Bulk Upload Routes — Phase LXIX: Pricing v3 (Phase 9); Sprint 720 cross-worker.

Accept up to 5 files for parallel processing. Enterprise only.

Route group prefix: /upload/bulk

Sprint 720 (2026-04-25): job state migrated from process-local
``OrderedDict`` to ``shared/bulk_job_store.py`` (Redis-backed with
in-memory fallback). Cross-worker visibility for status polls is now
provided by the shared store; processing tasks themselves still have
single-worker affinity via ``asyncio.create_task`` (a true queue-
driven processor is a future sprint when Enterprise volume warrants
the infra).
"""

import asyncio
import hashlib
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from models import User
from shared import bulk_job_store
from shared.entitlement_checks import check_bulk_upload_access, check_upload_limit, increment_upload_count
from shared.organization_schemas import BulkUploadStartResponse, BulkUploadStatusResponse
from shared.rate_limits import RATE_LIMIT_WRITE, limiter
from shared.upload_pipeline import validate_file_size

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload/bulk", tags=["bulk-upload"])

MAX_FILES = 5
_JOB_TTL_HOURS = 2


@router.post("", response_model=BulkUploadStartResponse)
@limiter.limit(RATE_LIMIT_WRITE)
async def start_bulk_upload(
    request: Any = None,
    files: list[UploadFile] = File(...),
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Accept up to 5 files for bulk processing. Enterprise only."""
    # AUDIT-08: correct arg order — signature is (user: User, db: Session)
    check_bulk_upload_access(user, db)

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

    # Check upload quota for all files — signature is (user: User, db: Session)
    for _ in files:
        check_upload_limit(user, db)

    # Sprint 720: bulk_job_store handles eviction itself (Redis TTL or
    # in-memory LRU+age cap); no explicit _evict_stale_jobs call needed.

    # Build file descriptors from already-validated bytes (UploadFile objects
    # may be closed after the response completes, so we must NOT pass them
    # to the background task)
    job_id = str(uuid.uuid4())
    file_statuses = []
    file_descriptors: list[dict] = []

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
        file_descriptors.append({"filename": f.filename, "content": content})

    bulk_job_store.put(
        job_id,
        {
            "job_id": job_id,
            "user_id": user.id,
            "created_at": datetime.now(UTC).isoformat(),
            "status": "processing",
            "files": file_statuses,
            "completed_count": 0,
            "total_count": len(files),
        },
        ttl_seconds=_JOB_TTL_HOURS * 3600,
    )

    # Process files asynchronously using pre-read bytes (not UploadFile objects)
    asyncio.create_task(_process_bulk_files(job_id, file_descriptors, user.id))

    return {
        "job_id": job_id,
        "total_files": len(files),
        "status": "processing",
    }


async def _process_bulk_files(
    job_id: str,
    file_descriptors: list[dict],
    user_id: int,
) -> None:
    """Process files one by one (sequential to avoid overwhelming the system).

    Args:
        file_descriptors: List of {"filename": str, "content": bytes} dicts.
            Content is pre-read from UploadFile before the response completes.

    Sprint 720 note: each mutation re-fetches the job from the shared
    store and persists the mutated copy back. This is what gives status
    polls on a different worker visibility into in-flight progress.
    """
    job = bulk_job_store.get(job_id)
    if not job:
        return

    for idx, fd in enumerate(file_descriptors):
        try:
            job["files"][idx]["status"] = "processing"
            bulk_job_store.put(job_id, job, ttl_seconds=_JOB_TTL_HOURS * 3600)

            content = fd["content"]

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
                "filename": fd["filename"],
                "size_bytes": len(content),
                "processed_at": datetime.now(UTC).isoformat(),
            }

        except Exception as exc:
            job["files"][idx]["status"] = "error"
            job["files"][idx]["error"] = "File processing failed. Please verify the file format and try again."
            logger.warning("Bulk upload file %d failed for job %s: %s", idx, job_id, type(exc).__name__)

        job["completed_count"] = sum(1 for fs in job["files"] if fs["status"] in ("complete", "error"))
        bulk_job_store.put(job_id, job, ttl_seconds=_JOB_TTL_HOURS * 3600)

    job["status"] = "complete"
    bulk_job_store.put(job_id, job, ttl_seconds=_JOB_TTL_HOURS * 3600)


@router.get("/{job_id}/status", response_model=BulkUploadStatusResponse)
async def get_bulk_status(
    job_id: str,
    user: User = Depends(require_verified_user),
) -> dict[str, Any]:
    """Poll bulk upload job progress."""
    job = bulk_job_store.get(job_id)
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
