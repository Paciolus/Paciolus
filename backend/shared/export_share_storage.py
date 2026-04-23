"""
Cloudflare R2 storage backend for ExportShare blobs — Sprint 611.

Moves the up-to-50 MB cached-export bytes out of Neon Postgres and into the
``paciolus-exports`` R2 bucket so that shared exports stop bloating the
primary DB + backups (Neon Launch tier cap = 10 GB).

Client is S3-compatible (boto3) pointed at the R2 endpoint.  Returns
``is_configured() == False`` when the four ``R2_EXPORTS_*`` env vars are
absent, in which case callers fall back to the in-row ``export_data``
blob column (dev / test mode).  Production has all four set as of
2026-04-23 per the R2 provisioning recorded in ``ceo-actions.md``.

ZERO-STORAGE NOTE: the objects stored here are rendered export artifacts
(PDF / XLSX / CSV cached outputs), not source financial data.  TTL is
enforced by both the share expiry cleanup job (24-48h) and the R2-side
delete on revoke/expire.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_s3_client: Any = None
_bucket_name: str | None = None
_configured: bool | None = None


def _get_client() -> Any:
    """Lazy-load the R2 S3 client.

    Returns ``None`` when R2 is not configured so callers can fall back
    to the legacy inline blob path without raising.
    """
    global _s3_client, _bucket_name, _configured

    if _configured is False:
        return None
    if _s3_client is not None:
        return _s3_client

    from config import _load_optional

    bucket = _load_optional("R2_EXPORTS_BUCKET", "")
    endpoint = _load_optional("R2_EXPORTS_ENDPOINT", "")
    access_key = _load_optional("R2_EXPORTS_ACCESS_KEY_ID", "")
    secret_key = _load_optional("R2_EXPORTS_SECRET_ACCESS_KEY", "")

    if not (bucket and endpoint and access_key and secret_key):
        _configured = False
        logger.info(
            "R2 export-share storage not configured — falling back to inline blob column",
        )
        return None

    try:
        import boto3
        from botocore.config import Config as BotoConfig
    except ImportError:
        _configured = False
        logger.warning("boto3 not installed — R2 export-share storage unavailable")
        return None

    try:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            # R2 ignores region but boto3 requires one; 'auto' is R2-canonical.
            region_name="auto",
            config=BotoConfig(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )
        _bucket_name = bucket
        _configured = True
        logger.info("R2 export-share storage initialized: bucket=%s", bucket)
        return _s3_client
    except Exception as exc:
        _configured = False
        logger.warning(
            "Failed to initialize R2 export-share client: %s",
            type(exc).__name__,
        )
        return None


def is_configured() -> bool:
    """True when the R2 client can be used for reads/writes."""
    return _get_client() is not None


def _object_key(share_token_hash: str) -> str:
    """Build the bucket object key from the SHA-256 share-token hash.

    The hash is already a high-entropy 64-char hex string, so no extra
    salt/prefix is needed.  A ``shares/`` prefix keeps the bucket
    human-scannable if an operator ever needs to list objects.
    """
    return f"shares/{share_token_hash}"


def upload(share_token_hash: str, data: bytes, content_type: str) -> str | None:
    """Upload export bytes to R2 and return the object key.

    Returns ``None`` when R2 is not configured; the caller is expected
    to fall back to the inline blob path.  Raises on transport errors
    so the caller can 503 out instead of silently losing data.
    """
    client = _get_client()
    if client is None or _bucket_name is None:
        return None

    key = _object_key(share_token_hash)
    client.put_object(
        Bucket=_bucket_name,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return key


def download(object_key: str) -> bytes | None:
    """Fetch export bytes from R2 by object key.

    Returns ``None`` when R2 is not configured OR the object is missing.
    The route path distinguishes the two by short-circuiting on
    ``is_configured()`` before calling.
    """
    client = _get_client()
    if client is None or _bucket_name is None:
        return None

    try:
        response = client.get_object(Bucket=_bucket_name, Key=object_key)
        return bytes(response["Body"].read())
    except Exception as exc:
        logger.warning(
            "R2 export-share download failed: key=%s err=%s",
            object_key,
            type(exc).__name__,
        )
        return None


def delete(object_key: str) -> bool:
    """Best-effort delete of an R2 object.

    Returns False when R2 is not configured or the DELETE errored.
    Cleanup scheduler logs and moves on — the object will be overwritten
    on next upload (keys are hash-deterministic) or age out via a bucket
    lifecycle rule if one is configured.
    """
    client = _get_client()
    if client is None or _bucket_name is None:
        return False

    try:
        client.delete_object(Bucket=_bucket_name, Key=object_key)
        return True
    except Exception as exc:
        logger.warning(
            "R2 export-share delete failed: key=%s err=%s",
            object_key,
            type(exc).__name__,
        )
        return False


def _reset_for_tests() -> None:
    """Reset lazy-init cache; intended for tests that patch env vars."""
    global _s3_client, _bucket_name, _configured
    _s3_client = None
    _bucket_name = None
    _configured = None
