"""
S3 Storage Client — Phase LXIX: Pricing v3 (Phase 8).

Lazy-loaded boto3 S3 client for firm branding logo storage.
No-ops gracefully when S3 is not configured (development mode).
"""

import logging

logger = logging.getLogger(__name__)

_s3_client = None
_bucket_name: str | None = None


def _get_client():
    """Lazy-load the S3 client."""
    global _s3_client, _bucket_name

    if _s3_client is not None:
        return _s3_client

    from config import _load_optional

    _bucket_name = _load_optional("S3_BUCKET_NAME", "")
    region = _load_optional("S3_REGION", "us-east-1")

    if not _bucket_name:
        logger.info("S3_BUCKET_NAME not configured — storage operations will be no-ops")
        return None

    try:
        import boto3

        _s3_client = boto3.client("s3", region_name=region)
        logger.info("S3 client initialized: bucket=%s, region=%s", _bucket_name, region)
        return _s3_client
    except ImportError:
        logger.warning("boto3 not installed — S3 storage unavailable")
        return None
    except Exception as exc:
        logger.warning("Failed to initialize S3 client: %s", type(exc).__name__)
        return None


def upload_bytes(key: str, data: bytes, content_type: str) -> bool:
    """Upload bytes to S3. Returns True on success."""
    client = _get_client()
    if client is None or _bucket_name is None:
        logger.debug("S3 upload skipped (not configured): %s", key)
        return False

    client.put_object(
        Bucket=_bucket_name,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return True


def download_bytes(key: str) -> bytes | None:
    """Download bytes from S3. Returns None if not found or not configured."""
    client = _get_client()
    if client is None or _bucket_name is None:
        return None

    try:
        response = client.get_object(Bucket=_bucket_name, Key=key)
        return response["Body"].read()
    except Exception:
        return None


def delete_key(key: str) -> bool:
    """Delete an object from S3. Returns True on success."""
    client = _get_client()
    if client is None or _bucket_name is None:
        return False

    client.delete_object(Bucket=_bucket_name, Key=key)
    return True
