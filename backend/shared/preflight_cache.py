"""
Preflight cache — short-lived in-memory store for file bytes parsed during preview/inspection.

Eliminates double upload+parse for the PDF preview → audit and workbook inspect → audit flows.
Keyed by UUID tokens with a 10-minute TTL and 100-entry LRU cap.

NOTE: In-memory only — suitable for single-process deployments. Should migrate to Redis
or a shared cache if the backend scales to multiple workers/processes.
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

MAX_ENTRIES = 100
TTL_SECONDS = 600  # 10 minutes


@dataclass
class PreflightEntry:
    file_bytes: bytes
    filename: str
    owner_id: int | None = None
    created_at: float = field(default_factory=time.monotonic)
    metadata: dict[str, Any] = field(default_factory=dict)


class PreflightCache:
    def __init__(self, max_entries: int = MAX_ENTRIES, ttl_seconds: int = TTL_SECONDS):
        self._store: dict[str, PreflightEntry] = {}
        self._lock = threading.Lock()
        self._max_entries = max_entries
        self._ttl = ttl_seconds

    def put(
        self,
        file_bytes: bytes,
        filename: str,
        metadata: dict[str, Any] | None = None,
        *,
        owner_id: int | None = None,
    ) -> str:
        """Cache file data and return a preflight token (UUID hex).

        Sprint 840: pass ``owner_id`` so only the uploading user can consume
        the token (see :meth:`take`).
        """
        token = uuid.uuid4().hex
        entry = PreflightEntry(
            file_bytes=file_bytes,
            filename=filename,
            owner_id=owner_id,
            metadata=metadata or {},
        )

        with self._lock:
            self._evict_expired()
            # LRU eviction if at capacity
            while len(self._store) >= self._max_entries:
                oldest_key = min(self._store, key=lambda k: self._store[k].created_at)
                del self._store[oldest_key]
            self._store[token] = entry

        return token

    def get(self, token: str) -> PreflightEntry | None:
        """Retrieve cached entry. Returns None if token is unknown or expired."""
        with self._lock:
            entry = self._store.get(token)
            if entry is None:
                return None
            if time.monotonic() - entry.created_at > self._ttl:
                del self._store[token]
                return None
            return entry

    def take(self, token: str, owner_id: int) -> PreflightEntry | None:
        """Atomically remove and return the entry, if ``owner_id`` uploaded it.

        Sprint 840: the audit route used ``get`` then ``remove`` — two lock
        acquisitions, so two concurrent requests could both consume one token
        — and never checked who the bytes belonged to. A token presented by
        anyone other than its owner returns None and leaves the entry alone.
        """
        with self._lock:
            entry = self._store.get(token)
            if entry is None:
                return None
            if time.monotonic() - entry.created_at > self._ttl:
                del self._store[token]
                return None
            if entry.owner_id != owner_id:
                return None
            del self._store[token]
            return entry

    def remove(self, token: str) -> None:
        """Explicitly remove an entry (e.g., after successful consumption)."""
        with self._lock:
            self._store.pop(token, None)

    def _evict_expired(self) -> None:
        """Remove all expired entries. Must be called under lock."""
        now = time.monotonic()
        expired = [k for k, v in self._store.items() if now - v.created_at > self._ttl]
        for k in expired:
            del self._store[k]


# Module-level singleton
preflight_cache = PreflightCache()
