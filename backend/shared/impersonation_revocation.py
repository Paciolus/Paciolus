"""Impersonation token revocation store (Sprint 661).

Stores revoked impersonation ``jti`` values with a bounded TTL so the
ImpersonationMiddleware can distinguish active impersonation sessions
from sessions an admin has explicitly ended.

Backend selection:
- If ``REDIS_URL`` is configured and reachable, use a Redis SET keyed by jti.
- Otherwise fall back to an in-process dict with expiry metadata.

The in-memory fallback is **not cluster-safe**. Production deployments
running multiple workers must set ``REDIS_URL``; otherwise a revocation
posted to worker A will not be visible to worker B.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

_logger = logging.getLogger(__name__)

_KEY_PREFIX = "impersonation:revoked:"
_MAX_TTL_SECONDS = 24 * 60 * 60  # Never keep entries longer than 24h.

_memory_store: dict[str, float] = {}
_memory_lock = threading.Lock()
_redis_client: object | None = None
_redis_checked = False


def _get_redis():
    """Lazily initialize a Redis client from REDIS_URL.

    Returns the client or ``None`` if Redis is not configured or unreachable.
    """
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client
    _redis_checked = True

    try:
        from config import REDIS_URL
    except Exception:
        return None
    if not REDIS_URL:
        return None

    try:
        import redis  # type: ignore[import-not-found]

        client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1.0)
        client.ping()
        _redis_client = client
        _logger.info("Impersonation revocation store: Redis")
    except Exception as exc:  # noqa: BLE001
        _logger.warning(
            "Impersonation revocation store: Redis unreachable (%s) — using in-memory fallback",
            exc,
        )
        _redis_client = None
    return _redis_client


def _prune_memory(now: float) -> None:
    expired = [k for k, exp in _memory_store.items() if exp <= now]
    for k in expired:
        _memory_store.pop(k, None)


def revoke(jti: str, ttl_seconds: int) -> None:
    """Record that ``jti`` has been revoked for up to ``ttl_seconds``.

    The TTL should match the remaining token lifetime plus a small buffer.
    Values are clamped to ``[1, 24h]``.
    """
    if not jti:
        return
    ttl = max(1, min(int(ttl_seconds), _MAX_TTL_SECONDS))
    client = _get_redis()
    if client is not None:
        try:
            client.set(_KEY_PREFIX + jti, "1", ex=ttl)
            return
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Redis revocation SET failed, falling back to memory: %s", exc)

    with _memory_lock:
        _memory_store[jti] = time.time() + ttl


def is_revoked(jti: Optional[str]) -> bool:
    """Return True when ``jti`` has been recorded as revoked and has not yet expired."""
    if not jti:
        return False
    client = _get_redis()
    if client is not None:
        try:
            return bool(client.exists(_KEY_PREFIX + jti))
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Redis revocation EXISTS failed, falling back to memory: %s", exc)

    now = time.time()
    with _memory_lock:
        _prune_memory(now)
        exp = _memory_store.get(jti)
        return exp is not None and exp > now


def _reset_for_tests() -> None:
    """Clear both the memory store and cached Redis probe (test helper)."""
    global _redis_client, _redis_checked
    with _memory_lock:
        _memory_store.clear()
    _redis_client = None
    _redis_checked = False
