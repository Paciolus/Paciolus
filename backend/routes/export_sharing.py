"""
Export Sharing Routes — Phase LXIX: Pricing v3 (Phase 6).

Share export results via temporary public links (tier-configurable TTL).
Gated to Professional+ tiers.

Sprint 593: Passcode protection, single-use mode, security headers,
            anomaly logging, tier-configurable TTL (24h Pro / 48h Ent).

Route group prefix: /export-sharing
"""

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from export_share_model import ExportShare
from models import User
from shared.entitlement_checks import check_export_sharing_access, get_effective_entitlements
from shared.organization_schemas import DetailResponse, ExportShareCreateResponse, ExportShareResponse
from shared.rate_limits import RATE_LIMIT_EXPORT, RATE_LIMIT_WRITE, limiter

logger = logging.getLogger(__name__)

ANOMALY_ACCESS_THRESHOLD = 10

# Magic bytes for allowed export formats
_MAGIC_BYTES: dict[str, list[bytes]] = {
    "pdf": [b"%PDF"],
    "xlsx": [b"PK\x03\x04"],  # ZIP-based Office format
    "csv": [],  # CSV has no magic bytes — validated by content inspection
}

router = APIRouter(prefix="/export-sharing", tags=["export-sharing"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CreateShareRequest(BaseModel):
    tool_name: str = Field(..., max_length=100)
    export_format: str = Field(..., pattern="^(pdf|xlsx|csv)$")
    export_data_b64: str = Field(..., description="Base64-encoded export file bytes")
    passcode: str | None = Field(
        None, min_length=4, max_length=64, description="Optional passcode for download protection"
    )
    single_use: bool = Field(False, description="Auto-revoke after first download")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mask_ip(ip: str) -> str:
    """Mask last octet of IPv4 for Zero-Storage compliant logging."""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
    return "***"  # IPv6 or unexpected format


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _validate_export_magic_bytes(export_bytes: bytes, export_format: str) -> None:
    """Validate that export bytes match expected magic bytes for the format.

    Raises HTTPException 400 if the content does not match the declared format.
    CSV has no magic bytes, so only basic printability checks are applied.
    """
    magic_list = _MAGIC_BYTES.get(export_format)
    if magic_list is None:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {export_format}")

    if not magic_list:
        # CSV: verify content is predominantly printable text (not binary)
        if export_format == "csv":
            sample = export_bytes[:4096]
            try:
                sample.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Export content does not match declared CSV format (binary data detected).",
                )
        return

    # Check magic bytes
    if not any(export_bytes[: len(magic)] == magic for magic in magic_list):
        raise HTTPException(
            status_code=400,
            detail=f"Export content does not match declared {export_format.upper()} format.",
        )


@router.post("/create", response_model=ExportShareCreateResponse)
@limiter.limit(RATE_LIMIT_WRITE)
async def create_share(
    body: CreateShareRequest,
    request: Any = None,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create a shareable export link. Professional+ only."""
    # AUDIT-08: pass db so subscription status is checked (not sessionless fallback)
    check_export_sharing_access(user, db)

    # Resolve tier-configurable TTL
    entitlements = get_effective_entitlements(user, db)
    ttl_hours = entitlements.share_ttl_hours
    if ttl_hours <= 0:
        raise HTTPException(status_code=403, detail="Export sharing is not available on your current plan.")

    import base64
    import binascii

    try:
        export_bytes = base64.b64decode(body.export_data_b64)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Invalid base64 export data.")

    # 50MB limit for shared exports
    if len(export_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Export data exceeds 50MB limit.")

    # Validate content matches declared format (provenance check)
    _validate_export_magic_bytes(export_bytes, body.export_format)

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    # Hash optional passcode (SHA-256 — sufficient for ephemeral links)
    passcode_hash = None
    if body.passcode:
        passcode_hash = hashlib.sha256(body.passcode.encode()).hexdigest()

    share = ExportShare(
        user_id=user.id,
        organization_id=getattr(user, "organization_id", None),
        share_token_hash=token_hash,
        tool_name=body.tool_name,
        export_format=body.export_format,
        export_data=export_bytes,
        passcode_hash=passcode_hash,
        single_use=body.single_use,
        shared_by_name=user.name or user.email,
        expires_at=datetime.now(UTC) + timedelta(hours=ttl_hours),
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    # Log share creation for abuse monitoring
    logger.info(
        "Export share created: user_id=%s, tool=%s, format=%s, size=%d, share_id=%s, single_use=%s, has_passcode=%s",
        user.id,
        body.tool_name,
        body.export_format,
        len(export_bytes),
        share.id,
        body.single_use,
        passcode_hash is not None,
    )

    result = share.to_dict()
    result["share_token"] = raw_token
    return result


@router.get("/{token}")
@limiter.limit(RATE_LIMIT_EXPORT)
async def download_share(
    token: str,
    request: Any = None,
    db: Session = Depends(get_db),
    passcode: str | None = Query(None, description="Passcode if the share link is protected"),
) -> Response:
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

    # Passcode verification (Sprint 593)
    if share.passcode_hash:
        if not passcode:
            raise HTTPException(status_code=403, detail="This share link requires a passcode.")
        if hashlib.sha256(passcode.encode()).hexdigest() != share.passcode_hash:
            raise HTTPException(status_code=403, detail="Invalid passcode.")

    # Update access counter
    share.access_count = (share.access_count or 0) + 1
    share.last_accessed_at = now

    # Single-use auto-revoke (Sprint 593): revoke after serving
    if share.single_use:
        share.revoked_at = now

    db.commit()

    # Anomaly detection logging (Sprint 593)
    client_ip = getattr(request, "client", None)
    masked_ip = _mask_ip(client_ip.host) if client_ip else "unknown"
    ua_hash = (
        hashlib.sha256((request.headers.get("user-agent", "") or "").encode()).hexdigest()[:12]
        if request
        else "unknown"
    )

    logger.info(
        "Share download: share_id=%s, ip=%s, ua_hash=%s, access_count=%d",
        share.id,
        masked_ip,
        ua_hash,
        share.access_count,
    )

    if share.access_count > ANOMALY_ACCESS_THRESHOLD:
        logger.warning(
            "Share download anomaly: share_id=%s exceeded threshold (count=%d), ip=%s",
            share.id,
            share.access_count,
            masked_ip,
        )

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
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            # X-Content-Type-Options and Referrer-Policy set by SecurityHeadersMiddleware
        },
    )


@router.delete("/{token}", response_model=DetailResponse)
@limiter.limit(RATE_LIMIT_WRITE)
async def revoke_share(
    token: str,
    request: Any = None,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
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


@router.get("/", response_model=list[ExportShareResponse])
async def list_shares(
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
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
