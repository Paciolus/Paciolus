"""Sprint 718 — Per-IP failure tracker with Redis backend + in-memory fallback.

Records failed authentication attempts per source IP and exposes a
sliding-window block check. Supersedes the process-local
``_ip_failure_tracker`` dict that previously lived in
``security_middleware.py``.

Why this module exists:
    The in-memory dict was per-worker and per-process. Under multi-worker
    Render, an attacker could distribute attempts across workers to evade
    the threshold. Every deploy reset the counters. The 2026-04-24
    security review (M-03) flagged the gap; this module closes it.

Storage strategy:
    - REDIS_URL set + reachable → Redis sorted-set per IP, score = epoch
      seconds, ZREMRANGEBYSCORE prunes per call. Cross-worker, survives
      deploys.
    - Else → in-memory dict fallback (same shape as pre-718 behavior).
      Acceptable for local dev / single-worker.

The pattern mirrors ``shared/impersonation_revocation.py`` for consistency.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Final

_logger = logging.getLogger(__name__)

_KEY_PREFIX: Final[str] = "ipfail:"
_MAX_IPS_IN_MEMORY: Final[int] = 10_000

# Lazy-init Redis client + memory fallback.
_redis_client: object | None = None
_redis_checked = False
_redis_lock = threading.Lock()

_memory_store: dict[str, list[float]] = {}
_memory_lock = threading.Lock()


def _get_redis():
    """Lazily initialize a Redis client. Returns the client or None."""
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client
    with _redis_lock:
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
            _logger.info("IP failure tracker: Redis backend")
        except Exception as exc:  # noqa: BLE001
            _logger.warning(
                "IP failure tracker: Redis unreachable (%s) — using in-memory fallback",
                exc,
            )
            _redis_client = None
        return _redis_client


def _evict_stale_in_memory(cutoff: float) -> None:
    """Remove IPs whose recorded failures are all older than ``cutoff``."""
    stale = [ip for ip, ts in _memory_store.items() if not any(t > cutoff for t in ts)]
    for ip in stale:
        _memory_store.pop(ip, None)


def record_failure(ip: str, *, window_seconds: int) -> None:
    """Record one failed attempt from ``ip``.

    Window is enforced by the storage layer (Redis ZREMRANGEBYSCORE or
    in-memory list pruning). Caller passes window so the module stays
    config-free.
    """
    if not ip:
        return
    now = time.time()
    cutoff = now - window_seconds

    client = _get_redis()
    if client is not None:
        try:
            key = f"{_KEY_PREFIX}{ip}"
            pipe = client.pipeline()
            pipe.zremrangebyscore(key, "-inf", cutoff)
            pipe.zadd(key, {f"{now}:{id(now)}": now})
            pipe.expire(key, window_seconds + 60)  # small grace
            pipe.execute()
            return
        except Exception as exc:  # noqa: BLE001
            _logger.warning("IP failure tracker: Redis record_failure failed (%s)", exc)
            # fall through to memory

    with _memory_lock:
        if ip not in _memory_store:
            if len(_memory_store) >= _MAX_IPS_IN_MEMORY:
                _evict_stale_in_memory(cutoff)
            _memory_store[ip] = []
        entries = [t for t in _memory_store[ip] if t > cutoff]
        entries.append(now)
        _memory_store[ip] = entries


def is_blocked(ip: str, *, window_seconds: int, threshold: int) -> bool:
    """Return True if ``ip`` has at least ``threshold`` failures in the last ``window_seconds``."""
    if not ip:
        return False
    now = time.time()
    cutoff = now - window_seconds

    client = _get_redis()
    if client is not None:
        try:
            key = f"{_KEY_PREFIX}{ip}"
            client.zremrangebyscore(key, "-inf", cutoff)
            count = int(client.zcard(key))
            return count >= threshold
        except Exception as exc:  # noqa: BLE001
            _logger.warning("IP failure tracker: Redis is_blocked failed (%s)", exc)
            # fall through to memory

    with _memory_lock:
        entries = _memory_store.get(ip)
        if not entries:
            return False
        recent = [t for t in entries if t > cutoff]
        _memory_store[ip] = recent
        return len(recent) >= threshold


def reset(ip: str) -> None:
    """Clear all recorded failures for ``ip`` (e.g. after a successful login or admin unlock)."""
    if not ip:
        return
    client = _get_redis()
    if client is not None:
        try:
            client.delete(f"{_KEY_PREFIX}{ip}")
        except Exception as exc:  # noqa: BLE001
            _logger.warning("IP failure tracker: Redis reset failed (%s)", exc)
    with _memory_lock:
        _memory_store.pop(ip, None)


def reset_all_for_admin_unlock() -> int:
    """Clear every IP's failure history.

    Used by the admin lockout-recovery endpoint (Sprint 718). Returns the
    number of IP entries cleared (Redis returns the count of deleted keys;
    memory returns the number of dict entries removed).
    """
    cleared = 0
    client = _get_redis()
    if client is not None:
        try:
            cursor = 0
            while True:
                cursor, keys = client.scan(cursor=cursor, match=f"{_KEY_PREFIX}*", count=500)
                if keys:
                    client.delete(*keys)
                    cleared += len(keys)
                if cursor == 0:
                    break
        except Exception as exc:  # noqa: BLE001
            _logger.warning("IP failure tracker: Redis reset_all failed (%s)", exc)
    with _memory_lock:
        cleared += len(_memory_store)
        _memory_store.clear()
    return cleared
