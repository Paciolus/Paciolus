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
    created_at: float = field(default_factory=time.monotonic)
    metadata: dict[str, Any] = field(default_factory=dict)


class PreflightCache:
    def __init__(self, max_entries: int = MAX_ENTRIES, ttl_seconds: int = TTL_SECONDS):
        self._store: dict[str, PreflightEntry] = {}
        self._lock = threading.Lock()
        self._max_entries = max_entries
        self._ttl = ttl_seconds

    def put(self, file_bytes: bytes, filename: str, metadata: dict[str, Any] | None = None) -> str:
        """Cache file data and return a preflight token (UUID hex)."""
        token = uuid.uuid4().hex
        entry = PreflightEntry(
            file_bytes=file_bytes,
            filename=filename,
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
