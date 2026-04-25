"""Sprint 720 — Bulk-upload job state with Redis backend + in-memory fallback.

Pre-Sprint-720 the bulk-upload route stored job state in a module-level
``_bulk_jobs: OrderedDict[str, dict]`` in ``routes/bulk_upload.py``.
Per-worker, per-process. POST hits Worker A; status poll hits Worker B
→ 404 ("Job not found"). Every deploy reset the store. The 2026-04-24
Guardian audit (#1.4) flagged the gap.

This module is the cross-worker store for bulk-upload jobs:
    - REDIS_URL set + reachable → Redis hash per job (HSET / HGETALL),
      with TTL via EXPIRE matching ``_JOB_TTL_HOURS``.
    - Else → in-memory dict fallback for local dev / single-worker.

Design choices:
    - Job state is small JSON (job metadata + per-file status list);
      we serialize via ``json.dumps`` for Redis storage.
    - Eviction is handled by Redis TTL (set on first write); the
      in-memory fallback uses LRU + age-cap as before for parity.
    - The fire-and-forget ``asyncio.create_task`` worker still has
      single-worker affinity for *processing*; the cross-worker
      benefit is on the *status-poll* side, which is where the bug
      manifested. Full queue-driven processing (Celery / RQ) is a
      future sprint when Enterprise volume warrants the infra.

Mirrors the ``shared/impersonation_revocation.py`` and
``shared/ip_failure_tracker.py`` Redis-with-fallback pattern.
"""

from __future__ import annotations

import json
import logging
import threading
from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any, Final

_logger = logging.getLogger(__name__)

_KEY_PREFIX: Final[str] = "bulkjob:"
_DEFAULT_TTL_SECONDS: Final[int] = 2 * 60 * 60  # 2h, matches _JOB_TTL_HOURS
_MAX_JOBS_IN_MEMORY: Final[int] = 100  # Matches pre-720 MAX_BULK_JOBS

# Lazy-init Redis client + memory fallback.
_redis_client: object | None = None
_redis_checked = False
_redis_lock = threading.Lock()

_memory_store: OrderedDict[str, dict[str, Any]] = OrderedDict()
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

            client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1.0, decode_responses=True)
            client.ping()
            _redis_client = client
            _logger.info("Bulk-job store: Redis backend")
        except Exception as exc:  # noqa: BLE001
            _logger.warning(
                "Bulk-job store: Redis unreachable (%s) — using in-memory fallback",
                exc,
            )
            _redis_client = None
        return _redis_client


def _evict_stale_in_memory() -> None:
    """Remove jobs older than the TTL from the in-memory store."""
    now = datetime.now(UTC)
    stale_keys: list[str] = []
    for key, job in _memory_store.items():
        try:
            created = datetime.fromisoformat(job["created_at"])
            if (now - created).total_seconds() > _DEFAULT_TTL_SECONDS:
                stale_keys.append(key)
        except (ValueError, KeyError, TypeError):
            stale_keys.append(key)
    for key in stale_keys:
        _memory_store.pop(key, None)
    while len(_memory_store) > _MAX_JOBS_IN_MEMORY:
        _memory_store.popitem(last=False)


def put(job_id: str, job: dict[str, Any], *, ttl_seconds: int = _DEFAULT_TTL_SECONDS) -> None:
    """Persist a job under ``job_id`` for at most ``ttl_seconds``."""
    if not job_id:
        return
    client = _get_redis()
    if client is not None:
        try:
            client.set(f"{_KEY_PREFIX}{job_id}", json.dumps(job), ex=ttl_seconds)
            return
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Bulk-job store: Redis put failed (%s)", exc)
            # fall through to memory

    with _memory_lock:
        _evict_stale_in_memory()
        _memory_store[job_id] = job


def get(job_id: str) -> dict[str, Any] | None:
    """Return the job under ``job_id`` or None if missing/expired."""
    if not job_id:
        return None
    client = _get_redis()
    if client is not None:
        try:
            raw = client.get(f"{_KEY_PREFIX}{job_id}")
            if raw is None:
                return None
            return json.loads(raw)  # type: ignore[no-any-return]
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Bulk-job store: Redis get failed (%s)", exc)
            # fall through to memory

    with _memory_lock:
        return _memory_store.get(job_id)


def delete(job_id: str) -> None:
    """Remove ``job_id`` from the store."""
    if not job_id:
        return
    client = _get_redis()
    if client is not None:
        try:
            client.delete(f"{_KEY_PREFIX}{job_id}")
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Bulk-job store: Redis delete failed (%s)", exc)
    with _memory_lock:
        _memory_store.pop(job_id, None)


def reset_all_for_tests() -> None:
    """Clear the entire store. Test-only helper."""
    client = _get_redis()
    if client is not None:
        try:
            cursor = 0
            while True:
                cursor, keys = client.scan(cursor=cursor, match=f"{_KEY_PREFIX}*", count=500)
                if keys:
                    client.delete(*keys)
                if cursor == 0:
                    break
        except Exception:  # noqa: BLE001
            pass
    with _memory_lock:
        _memory_store.clear()
