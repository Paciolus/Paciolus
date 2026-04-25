"""
Export Sharing Routes — Phase LXIX: Pricing v3 (Phase 6).

Share export results via temporary public links (tier-configurable TTL).
Gated to Professional+ tiers.

Sprint 593: Passcode protection, single-use mode, security headers,
            anomaly logging, tier-configurable TTL (24h Pro / 48h Ent).
2026-04-20 hardening: passcode upgraded to bcrypt KDF + per-token
            brute-force throttle; passcode moved out of query string
            onto a dedicated POST /download body.

Route group prefix: /export-sharing
"""

import hashlib
import logging
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from export_share_model import ExportShare
from models import User
from shared import export_share_storage
from shared.entitlement_checks import check_export_sharing_access, get_effective_entitlements
from shared.organization_schemas import DetailResponse, ExportShareCreateResponse, ExportShareResponse
from shared.passcode_security import (
    PASSCODE_MAX_LENGTH,
    PASSCODE_MIN_LENGTH,
    PasscodeThrottleState,
    WeakPasscodeError,
    current_lockout_remaining_seconds,
    hash_passcode,
    validate_passcode_strength,
    verify_passcode,
)
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
    # Passcode length range is echoed from shared.passcode_security so clients
    # see one authoritative policy boundary.  Strength rules (char classes)
    # are enforced at runtime — Pydantic cannot express "3 of 4 classes".
    passcode: str | None = Field(
        None,
        min_length=PASSCODE_MIN_LENGTH,
        max_length=PASSCODE_MAX_LENGTH,
        description=(
            f"Optional passcode for download protection. "
            f"Must be {PASSCODE_MIN_LENGTH}-{PASSCODE_MAX_LENGTH} characters "
            "and include at least 3 of: lowercase, uppercase, digit, symbol."
        ),
    )
    single_use: bool = Field(False, description="Auto-revoke after first download")


class DownloadRequest(BaseModel):
    """POST body for /export-sharing/{token}/download.

    Passcodes MUST be submitted via this body rather than a query string —
    query strings leak via access logs, browser history, and proxy layers.
    Non-passcode shares can still use the GET endpoint for convenience.
    """

    passcode: str | None = Field(
        None,
        min_length=1,  # weak/short input is rejected by the verifier, not the schema
        max_length=PASSCODE_MAX_LENGTH,
        description="Passcode if the share link is protected.",
    )


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


def _resolve_share_or_404(token: str, db: Session) -> ExportShare:
    """Look up a non-revoked share by raw token; raise 404 otherwise."""
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
    return share


def _enforce_not_expired(share: ExportShare) -> datetime:
    """Raise 410 if the share has expired; otherwise return ``now``."""
    now = datetime.now(UTC)
    expires = share.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if now > expires:
        raise HTTPException(status_code=410, detail="This share link has expired.")
    return now


_CONTENT_TYPES = {
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
}


def _resolve_export_bytes(share: ExportShare) -> bytes:
    """Return the export payload, preferring R2 when ``object_key`` is set.

    Raises 410 when the row points at R2 but the object is missing —
    rather than silently serving an empty body.  The inline-blob path
    is retained as a fallback for rows created before the Sprint 611
    flip and for dev/test environments without R2 configured.
    """
    if share.object_key:
        data = export_share_storage.download(share.object_key)
        if data is None:
            logger.warning(
                "Share object missing from R2: share_id=%s key=%s",
                share.id,
                share.object_key,
            )
            raise HTTPException(
                status_code=410,
                detail="Shared export is no longer available.",
            )
        return data
    if share.export_data is not None:
        return bytes(share.export_data)
    logger.error("Share row has neither object_key nor export_data: share_id=%s", share.id)
    raise HTTPException(status_code=410, detail="Shared export is no longer available.")


def _build_download_response(share: ExportShare) -> Response:
    """Serialize a share's bytes into a safe downloadable Response."""
    content_type = _CONTENT_TYPES.get(share.export_format, "application/octet-stream")
    safe_name = re.sub(r"[^\w\-]", "_", share.tool_name or "export")[:80]
    filename = f"paciolus-{safe_name}.{share.export_format}"
    return Response(
        content=_resolve_export_bytes(share),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            # X-Content-Type-Options and Referrer-Policy set by SecurityHeadersMiddleware
        },
    )


def _log_access(share: ExportShare, request: Any) -> tuple[str, str]:
    """Record the access attempt (masked IP, hashed UA) and return them."""
    client_ip = getattr(request, "client", None)
    masked_ip = _mask_ip(client_ip.host) if client_ip else "unknown"
    ua_hash = (
        hashlib.sha256((request.headers.get("user-agent", "") or "").encode()).hexdigest()[:12]
        if request
        else "unknown"
    )
    return masked_ip, ua_hash


def _verify_passcode_or_raise(
    share: ExportShare,
    passcode: str | None,
    db: Session,
    client_ip: str | None = None,
) -> None:
    """Enforce passcode, brute-force throttle (per-token + per-IP), and
    update counters.

    Sprint 698: per-IP throttle layered on top of the per-token lockout.
    Sprint 696 hardened single-token brute-force; an attacker cycling
    through multiple share tokens from one IP was only bounded by the
    slowapi 60/min generic limit. Per-IP failure tracking (same pattern
    as auth failures — see ``record_ip_failure`` / ``check_ip_blocked``)
    catches credential-stuffing across many share links before it
    accumulates enough signal.

    Raises:
        403 if passcode missing or invalid.
        429 if the share is locked (per-token) OR the IP is blocked (per-IP).
    """
    # Per-IP block takes precedence — if the attacker's IP is already
    # over threshold we refuse before even consulting the token state.
    if client_ip:
        from security_middleware import check_ip_blocked

        if check_ip_blocked(client_ip):
            raise HTTPException(
                status_code=429,
                detail=("Too many failed passcode attempts from this network. Try again later."),
                headers={"Retry-After": "900"},  # 15-min default window
            )

    throttle = PasscodeThrottleState(share)
    if throttle.is_locked():
        remaining = current_lockout_remaining_seconds(share.passcode_locked_until)
        raise HTTPException(
            status_code=429,
            detail=(f"Too many failed passcode attempts. Try again in {remaining} seconds."),
            headers={"Retry-After": str(max(1, remaining))},
        )

    if not passcode:
        raise HTTPException(
            status_code=403,
            detail="This share link requires a passcode. POST it to /export-sharing/{token}/download.",
        )

    if not verify_passcode(passcode, share.passcode_hash or ""):
        throttle.register_failure()
        db.commit()
        # Sprint 698: also record the failure against the IP tracker so
        # cross-token credential-stuffing is bounded.
        if client_ip:
            from security_middleware import record_ip_failure

            record_ip_failure(client_ip)
        logger.info(
            "Share passcode mismatch: share_id=%s, attempts=%s, ip=%s",
            share.id,
            share.passcode_failed_attempts,
            client_ip or "unknown",
        )
        raise HTTPException(status_code=403, detail="Invalid passcode.")

    throttle.reset()


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

    # Passcode strength + KDF (2026-04-20 hardening).
    passcode_hash: str | None = None
    if body.passcode:
        try:
            validate_passcode_strength(body.passcode)
        except WeakPasscodeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        passcode_hash = hash_passcode(body.passcode)

    # Sprint 611: store the bytes in R2 when configured; fall back to the
    # inline DB column otherwise (dev / test).  Exactly one of
    # ``object_key`` / ``export_data`` is set on each row.
    object_key: str | None = None
    inline_bytes: bytes | None = export_bytes
    if export_share_storage.is_configured():
        content_type = _CONTENT_TYPES.get(body.export_format, "application/octet-stream")
        try:
            object_key = export_share_storage.upload(token_hash, export_bytes, content_type)
        except Exception as exc:
            logger.error("R2 upload failed: %s", type(exc).__name__, exc_info=exc)
            raise HTTPException(
                status_code=503,
                detail="Export storage is temporarily unavailable. Please try again.",
            ) from exc
        if object_key is None:
            # is_configured() said yes but upload returned None — treat as
            # transient and 503 rather than silently falling back to the
            # DB blob (which would re-introduce the capacity risk).
            raise HTTPException(
                status_code=503,
                detail="Export storage is temporarily unavailable. Please try again.",
            )
        inline_bytes = None

    share = ExportShare(
        user_id=user.id,
        organization_id=getattr(user, "organization_id", None),
        share_token_hash=token_hash,
        tool_name=body.tool_name,
        export_format=body.export_format,
        export_data=inline_bytes,
        object_key=object_key,
        passcode_hash=passcode_hash,
        single_use=body.single_use,
        shared_by_name=user.name or user.email,
        expires_at=datetime.now(UTC) + timedelta(hours=ttl_hours),
    )
    db.add(share)
    try:
        db.commit()
    except Exception:
        # DB write failed after R2 upload succeeded — best-effort delete
        # the orphan object so we don't leak bytes into the bucket.
        if object_key:
            export_share_storage.delete(object_key)
        raise
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


def _finalize_download(share: ExportShare, request: Any, db: Session) -> Response:
    """Shared tail logic for both GET and POST download paths."""
    now = _enforce_not_expired(share)

    # Update access counter
    share.access_count = (share.access_count or 0) + 1
    share.last_accessed_at = now

    # Single-use auto-revoke (Sprint 593): revoke after serving
    if share.single_use:
        share.revoked_at = now

    db.commit()

    masked_ip, ua_hash = _log_access(share, request)

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

    return _build_download_response(share)


@router.get("/{token}")
@limiter.limit(RATE_LIMIT_EXPORT)
async def download_share(
    token: str,
    request: Any = None,
    db: Session = Depends(get_db),
) -> Response:
    """Download a non-passcode-protected shared export.

    Public endpoint (no auth required).  Passcode-protected shares MUST
    use the POST /{token}/download endpoint.

    Sprint 718 hardening: passcode-protected shares now return 404 (not
    a 403 with "passcode required") so the GET endpoint cannot be used
    to enumerate which random tokens are real and worth concentrated
    brute-force. The intended POST flow signals the passcode requirement
    via its own response shape; clients exclusively using the GET
    endpoint never need to discriminate "exists+passcode" from "doesn't
    exist."

    2026-04-20 hardening: the ``?passcode=`` query-string pattern has been
    REMOVED.  Query-string secrets leak via access logs, browser history,
    and transparent proxies.  Callers must migrate to the POST variant.
    """
    share = _resolve_share_or_404(token, db)
    _enforce_not_expired(share)

    if share.passcode_hash:
        # Sprint 718: collapse to 404 so this endpoint can't be used to
        # enumerate which tokens are real — eliminates the existence-leak
        # surface flagged by the 2026-04-24 security review (M-02).
        raise HTTPException(status_code=404, detail="Share not found")

    return _finalize_download(share, request, db)


@router.post("/{token}/download")
@limiter.limit(RATE_LIMIT_EXPORT)
async def download_share_with_passcode(
    token: str,
    body: DownloadRequest,
    request: Any = None,
    db: Session = Depends(get_db),
) -> Response:
    """POST-body download: accepts the passcode in JSON instead of query string.

    Public endpoint (no auth required).  For passcode-protected shares, the
    request body must include ``{"passcode": "..."}``.  Non-passcode shares
    may also POST here (body.passcode is ignored) for clients that prefer
    a single call pattern.
    """
    share = _resolve_share_or_404(token, db)
    _enforce_not_expired(share)

    if share.passcode_hash:
        # Sprint 698: thread the client IP so per-IP throttle can fire.
        client_ip = None
        if request is not None and getattr(request, "client", None) is not None:
            client_ip = request.client.host
        _verify_passcode_or_raise(share, body.passcode, db, client_ip=client_ip)

    return _finalize_download(share, request, db)


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
    # Best-effort immediate R2 cleanup so revoked bytes disappear before
    # the hourly sweep runs.  Failure is non-fatal — the scheduler will
    # retry the delete on the next expired-shares pass.
    if share.object_key:
        export_share_storage.delete(share.object_key)
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
