"""
Export Sharing Routes — Phase LXIX: Pricing v3 (Phase 6).

Share export results via temporary public links (48h TTL).
Gated to Professional+ tiers.

Route group prefix: /export-sharing
"""

import hashlib
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from export_share_model import ExportShare
from models import User
from shared.entitlement_checks import check_export_sharing_access
from shared.rate_limits import RATE_LIMIT_EXPORT, RATE_LIMIT_WRITE, limiter

router = APIRouter(prefix="/export-sharing", tags=["export-sharing"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CreateShareRequest(BaseModel):
    tool_name: str = Field(..., max_length=100)
    export_format: str = Field(..., pattern="^(pdf|xlsx|csv)$")
    export_data_b64: str = Field(..., description="Base64-encoded export file bytes")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/create")
@limiter.limit(RATE_LIMIT_WRITE)
async def create_share(
    body: CreateShareRequest,
    request=None,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Create a shareable export link. Professional+ only."""
    check_export_sharing_access(user)

    import base64
    import binascii

    try:
        export_bytes = base64.b64decode(body.export_data_b64)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Invalid base64 export data.")

    # 50MB limit for shared exports
    if len(export_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Export data exceeds 50MB limit.")

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    share = ExportShare(
        user_id=user.id,
        organization_id=getattr(user, "organization_id", None),
        share_token_hash=token_hash,
        tool_name=body.tool_name,
        export_format=body.export_format,
        export_data=export_bytes,
        shared_by_name=user.name or user.email,
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    result = share.to_dict()
    result["share_token"] = raw_token
    return result


@router.get("/{token}")
@limiter.limit(RATE_LIMIT_EXPORT)
async def download_share(
    token: str,
    request=None,
    db: Session = Depends(get_db),
):
    """Download a shared export. Public endpoint (no auth required)."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    share = (
        db.query(ExportShare)
        .filter(
            ExportShare.share_token_hash == token_hash,
            ExportShare.revoked_at.is_(None),
        )
        .first()
    )
    if not share:
        raise HTTPException(status_code=404, detail="Share link not found or revoked.")

    # Check expiry
    now = datetime.now(UTC)
    expires = share.expires_at
    if expires.tzinfo is None:
        from datetime import timezone

        expires = expires.replace(tzinfo=timezone.utc)
    if now > expires:
        raise HTTPException(status_code=410, detail="This share link has expired.")

    # Update access counter
    share.access_count = (share.access_count or 0) + 1
    share.last_accessed_at = now
    db.commit()

    # Determine content type
    content_types = {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
    }
    content_type = content_types.get(share.export_format, "application/octet-stream")

    # Sanitize tool_name for Content-Disposition: strip control chars, quotes, path separators
    import re

    safe_name = re.sub(r"[^\w\-]", "_", share.tool_name or "export")[:80]
    filename = f"paciolus-{safe_name}.{share.export_format}"

    return Response(
        content=share.export_data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{token}")
@limiter.limit(RATE_LIMIT_WRITE)
async def revoke_share(
    token: str,
    request=None,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Revoke a share link. Creator only."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    share = (
        db.query(ExportShare)
        .filter(
            ExportShare.share_token_hash == token_hash,
            ExportShare.user_id == user.id,
        )
        .first()
    )
    if not share:
        raise HTTPException(status_code=404, detail="Share not found.")

    share.revoked_at = datetime.now(UTC)
    db.commit()
    return {"detail": "Share link revoked."}


@router.get("/")
async def list_shares(
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """List current user's active share links."""
    now = datetime.now(UTC)
    shares = (
        db.query(ExportShare)
        .filter(
            ExportShare.user_id == user.id,
            ExportShare.revoked_at.is_(None),
            ExportShare.expires_at > now,
        )
        .order_by(ExportShare.created_at.desc())
        .all()
    )
    return [s.to_dict() for s in shares]
