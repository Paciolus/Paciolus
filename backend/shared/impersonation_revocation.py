"""Impersonation token revocation store (Sprint 661).

Stores revoked impersonation ``jti`` values with a bounded TTL so the
ImpersonationMiddleware can distinguish active impersonation sessions
from sessions an admin has explicitly ended.

Backend selection:
- If ``REDIS_URL`` is configured and reachable, use a Redis SET keyed by jti.
- Without ``REDIS_URL`` (development, tests), use an in-process dict with expiry.
- Production with ``REDIS_URL`` set but Redis unreachable or erroring: a check
  that cannot be confirmed answers "revoked" (Sprint 877), and the probe is
  retried every 30 s. The in-memory store is **not cluster-safe** — a
  revocation posted to worker A is invisible to worker B — so it must never be
  the answer where revocation is meant to be shared.
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
# Sprint 877: a failed probe is retried after this many seconds instead of
# pinning the worker to its private in-memory store for life.
_REDIS_RETRY_SECONDS = 30.0
_redis_retry_at = 0.0


def _redis_required() -> bool:
    """Production with REDIS_URL set: revocation must be shared, so an unconfirmable
    check is treated as revoked (fail closed). Only impersonation tokens — superadmin,
    read-only — ever reach is_revoked(), so no ordinary sign-in depends on this."""
    try:
        from config import ENV_MODE, REDIS_URL
    except Exception:  # noqa: BLE001
        return False
    return bool(REDIS_URL) and ENV_MODE == "production"


def _get_redis():
    """Lazily initialize a Redis client from REDIS_URL.

    Returns the client or ``None`` if Redis is not configured or unreachable.
    """
    global _redis_client, _redis_checked, _redis_retry_at
    if _redis_client is not None:
        return _redis_client
    if _redis_checked and time.time() < _redis_retry_at:
        return None
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
            "Impersonation revocation store: Redis unreachable (%s) — retrying in %.0fs",
            exc,
            _REDIS_RETRY_SECONDS,
        )
        _redis_client = None
        _redis_retry_at = time.time() + _REDIS_RETRY_SECONDS
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
            _logger.warning("Redis revocation EXISTS failed: %s", exc)
    # Sprint 877: a worker's private memory cannot see a revocation posted to
    # another worker. Where revocation is meant to be shared, "cannot confirm"
    # must mean "revoked", not "valid".
    if _redis_required():
        return True

    now = time.time()
    with _memory_lock:
        _prune_memory(now)
        exp = _memory_store.get(jti)
        return exp is not None and exp > now


def _reset_for_tests() -> None:
    """Clear both the memory store and cached Redis probe (test helper)."""
    global _redis_client, _redis_checked, _redis_retry_at
    with _memory_lock:
        _memory_store.clear()
    _redis_client = None
    _redis_checked = False
    _redis_retry_at = 0.0
