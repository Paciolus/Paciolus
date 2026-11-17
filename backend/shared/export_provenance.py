"""Export provenance tokens: only files Paciolus generated can be shared (Sprint 880, OUT-03).

A share link serves the bytes the client uploads to ``/export-sharing/create``.
Before this, those bytes were checked only for a leading ``%PDF`` / ZIP
signature, so a paid user could share *any* PDF or workbook (JavaScript,
external links, live formulas) through a Paciolus link.

Now every file download the server builds (``shared.export_helpers``) carries an
**export token**: an HMAC-signed statement of (user, format, SHA-256 of the
exact bytes, expiry), issued only to the signed-in user who requested the
export. Share creation accepts bytes only with a token that verifies for this
user, this format and these bytes, so the stored file is byte-for-byte the
export the server produced. The token holds nothing secret: the digest of a
file the user already has.

How the token reaches the response: ``attachment_response`` (which has the
bytes) adds an internal digest header; ``SecurityHeadersMiddleware`` (which has
the request, and so the user ``require_current_user`` recorded) removes it and,
for a signed-in user, replaces it with the signed token. Anonymous responses
get no token and the digest header never leaves the server.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Optional

# Long enough to export and then share; short enough that a token is not a
# standing permission to share a file.
EXPORT_TOKEN_TTL_SECONDS = 15 * 60
_CONTEXT = b"paciolus:export-provenance:v1"

TOKEN_HEADER = "X-Paciolus-Export-Token"
DIGEST_HEADER = "X-Paciolus-Export-Digest"  # internal: added by export_helpers, removed by middleware

SHAREABLE_FORMATS = frozenset({"pdf", "xlsx", "csv"})
_MEDIA_FORMATS = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "text/csv": "csv",
}


class ExportProvenanceError(ValueError):
    """The token is malformed, forged, expired, or not for this user, format or file."""


@dataclass(frozen=True)
class ExportClaim:
    user_id: int
    export_format: str
    sha256: str
    expires_at: int


def format_for_media_type(media_type: str) -> Optional[str]:
    """``pdf`` / ``xlsx`` / ``csv`` for a shareable media type (parameters ignored), else None."""
    return _MEDIA_FORMATS.get(media_type.split(";", 1)[0].strip().lower())


def digest_header_value(export_format: str, data: bytes) -> str:
    """Value of the internal digest header: ``<format>:<sha256 hex>``."""
    return f"{export_format}:{hashlib.sha256(data).hexdigest()}"


def _key() -> bytes:
    from config import JWT_SECRET_KEY

    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is required to sign export tokens")
    return hmac.new(JWT_SECRET_KEY.encode("utf-8"), _CONTEXT, hashlib.sha256).digest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign_digest(*, user_id: int, export_format: str, sha256: str, now: Optional[float] = None) -> str:
    if export_format not in SHAREABLE_FORMATS:
        raise ValueError("unshareable export format")
    payload = {
        "u": user_id,
        "f": export_format,
        "d": sha256,
        "x": int((now if now is not None else time.time()) + EXPORT_TOKEN_TTL_SECONDS),
    }
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    sig = _b64(hmac.new(_key(), body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{sig}"


def sign_export(*, user_id: int, export_format: str, data: bytes, now: Optional[float] = None) -> str:
    """Sign the exact ``data`` the server produced for ``user_id``."""
    return sign_digest(user_id=user_id, export_format=export_format, sha256=hashlib.sha256(data).hexdigest(), now=now)


def sign_from_digest_header(user_id: int, header_value: str) -> Optional[str]:
    """Turn an internal digest header into a token; None if the header is malformed."""
    export_format, _, sha256 = header_value.partition(":")
    if export_format not in SHAREABLE_FORMATS or len(sha256) != 64:
        return None
    return sign_digest(user_id=user_id, export_format=export_format, sha256=sha256)


def verify_export(
    token: str, *, user_id: int, export_format: str, data: bytes, now: Optional[float] = None
) -> ExportClaim:
    """Return the claim if ``token`` was issued to ``user_id`` for exactly these bytes in this format."""
    try:
        body, sig = token.split(".")
        expected = _b64(hmac.new(_key(), body.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            raise ExportProvenanceError("invalid export token")
        p = json.loads(_unb64(body))
        claim = ExportClaim(
            user_id=int(p["u"]),
            export_format=str(p["f"]),
            sha256=str(p["d"]),
            expires_at=int(p["x"]),
        )
    except ExportProvenanceError:
        raise
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise ExportProvenanceError("invalid export token") from None
    if claim.expires_at < (now if now is not None else time.time()):
        raise ExportProvenanceError("export token expired")
    if claim.user_id != user_id or claim.export_format != export_format:
        raise ExportProvenanceError("export token is not for this user or format")
    if not hmac.compare_digest(claim.sha256, hashlib.sha256(data).hexdigest()):
        raise ExportProvenanceError("file does not match the export token")
    return claim
