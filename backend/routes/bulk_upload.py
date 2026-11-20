"""
Bulk Upload Routes — Phase LXIX: Pricing v3 (Phase 9); Sprint 720 cross-worker.

Route group prefix: /upload/bulk

Sprint 888 (CEO decision, brief 13B): bulk upload is a feature to build, not one
that exists. The first version accepted up to five files and marked each one
"complete" with only its name and size — no engine ran. Until it performs real
analysis, ``POST /upload/bulk`` answers 501 and reads nothing. The status route
stays so the response shape is ready for the real feature; no job can be created,
so it answers 404. Build plan: ``tasks/todo.md`` (Sprint 888, "Bulk upload").
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import require_verified_user
from models import User
from shared import bulk_job_store
from shared.organization_schemas import BulkUploadStatusResponse
from shared.rate_limits import RATE_LIMIT_WRITE, limiter

router = APIRouter(prefix="/upload/bulk", tags=["bulk-upload"])

BULK_UPLOAD_NOT_AVAILABLE = "Bulk upload is not available yet."


@router.post(
    "",
    status_code=501,
    responses={501: {"description": BULK_UPLOAD_NOT_AVAILABLE}},
)
@limiter.limit(RATE_LIMIT_WRITE)
def start_bulk_upload(
    request: Request,
    user: User = Depends(require_verified_user),
) -> None:
    """Not available yet: bulk upload runs no analysis, so it accepts no files."""
    raise HTTPException(status_code=501, detail=BULK_UPLOAD_NOT_AVAILABLE)


@router.get("/{job_id}/status", response_model=BulkUploadStatusResponse)
def get_bulk_status(
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
