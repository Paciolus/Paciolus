"""
Shared Log Sanitizer — Sprint 300

Reusable utilities for PII/token sanitization in log output.
Prevents leakage of raw tokens, email addresses, and exception
details into logs or API responses.
"""

import hashlib


def token_fingerprint(token: str) -> str:
    """Return a safe fingerprint of a token for logging.

    Format: first 8 chars + SHA-256 hash prefix (8 hex chars).
    Never exposes the full token value.

    Args:
        token: The raw token string.

    Returns:
        A safe fingerprint like ``"abc12345...[a1b2c3d4]"``
    """
    if len(token) <= 8:
        return "***"
    sha_prefix = hashlib.sha256(token.encode("utf-8")).hexdigest()[:8]
    return f"{token[:8]}...[{sha_prefix}]"


def mask_email(email: str) -> str:
    """Mask an email address for safe logging.

    Format: first 3 chars of local part + ``***@domain``.
    Falls back to ``***@***`` for very short or malformed addresses.

    Args:
        email: The raw email address.

    Returns:
        A masked email like ``"abc***@domain.com"``
    """
    parts = email.split("@")
    if len(parts) == 2 and len(parts[0]) > 3:
        return f"{parts[0][:3]}***@{parts[1]}"
    return "***@***"


def sanitize_exception(e: Exception) -> str:
    """Return a safe representation of an exception for logging/API responses.

    Returns the exception class name with a generic message.
    Never exposes the raw ``str(e)`` which may contain emails,
    API keys, URLs, or other PII from third-party libraries.

    Args:
        e: The caught exception.

    Returns:
        A safe string like ``"OSError: email delivery failed"``
    """
    return f"{type(e).__name__}: email delivery failed"
