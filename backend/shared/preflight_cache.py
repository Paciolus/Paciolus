"""
Preflight cache — short-lived in-memory store for file bytes parsed during preview/inspection.

Eliminates a second parse for the PDF preview → audit and workbook inspect → audit
flows. Keyed by single-use, owner-bound UUID tokens.

**What the data statement promises (Sprint 879d, review DH-07):** an uploaded file
may sit in memory for up to 10 minutes. This cache is how it can:

- **Timer, in every process.** A daemon sweeper thread removes expired entries
  every ``sweep_interval`` seconds, so an abandoned preview in an idle worker is
  gone within ``ttl + sweep_interval`` — expiry no longer waits for the next
  ``put()``. The thread starts with the first ``put()`` in each process (and again
  after a fork), so every Gunicorn worker has its own.
- **Byte budget + per-user limit.** ``max_total_bytes`` caps the whole cache
  (oldest evicted first); ``max_entries_per_owner`` caps one user (their oldest
  evicted). A single file larger than the budget is not cached (``put`` → None).
- **Logout / account deletion.** :meth:`purge_owner` drops a user's entries in
  this process; ``shared.preflight_purge.request_purge`` also records a purge
  request that every other worker's sweeper applies on its next tick.

**Per process, by decision (CEO 2026-11-16):** the cache stays in memory in each
worker — no Redis, no disk. A token presented to a worker that does not hold it
is a miss; the browser always sends the file with the token
(``buildTrialBalanceFormData``), so the miss is analysed from the re-sent bytes.
"""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

MAX_ENTRIES = 100
TTL_SECONDS = 600  # 10 minutes — the published limit
MAX_TOTAL_BYTES = 256 * 1024 * 1024  # per process; two 100 MB uploads fit
MAX_ENTRIES_PER_OWNER = 2  # a PDF preview and a workbook inspection
SWEEP_INTERVAL_SECONDS = 15.0

PurgeSource = Callable[[], Iterable[tuple[int, float]]]


@dataclass
class PreflightEntry:
    file_bytes: bytes
    filename: str
    owner_id: int | None = None
    created_at: float = field(default_factory=time.monotonic)
    created_wall: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


def _default_purge_source() -> Iterable[tuple[int, float]]:
    from shared.preflight_purge import pending_purges

    return pending_purges(TTL_SECONDS)


class PreflightCache:
    def __init__(
        self,
        max_entries: int = MAX_ENTRIES,
        ttl_seconds: int = TTL_SECONDS,
        *,
        max_total_bytes: int = MAX_TOTAL_BYTES,
        max_entries_per_owner: int = MAX_ENTRIES_PER_OWNER,
        sweep_interval: float = SWEEP_INTERVAL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        purge_source: Optional[PurgeSource] = _default_purge_source,
    ):
        self._store: dict[str, PreflightEntry] = {}
        self._lock = threading.Lock()
        self._max_entries = max_entries
        self._ttl = ttl_seconds
        self._max_total_bytes = max_total_bytes
        self._max_per_owner = max_entries_per_owner
        self._sweep_interval = sweep_interval
        self._clock = clock
        self._purge_source = purge_source
        self._total_bytes = 0
        self._stop = threading.Event()
        self._sweeper: Optional[threading.Thread] = None
        self._sweeper_pid: Optional[int] = None

    # -- public API ---------------------------------------------------------

    @property
    def total_bytes(self) -> int:
        return self._total_bytes

    def put(
        self,
        file_bytes: bytes,
        filename: str,
        metadata: dict[str, Any] | None = None,
        *,
        owner_id: int | None = None,
    ) -> str | None:
        """Cache file data and return a preflight token, or None if it cannot fit.

        Sprint 840: pass ``owner_id`` so only the uploading user can consume
        the token (see :meth:`take`).
        """
        size = len(file_bytes)
        if size > self._max_total_bytes:
            return None
        token = uuid.uuid4().hex
        entry = PreflightEntry(
            file_bytes=file_bytes,
            filename=filename,
            owner_id=owner_id,
            created_at=self._clock(),
            metadata=metadata or {},
        )
        with self._lock:
            self._evict_expired()
            if owner_id is not None:
                mine = sorted((k for k, v in self._store.items() if v.owner_id == owner_id), key=self._age_key)
                while len(mine) >= self._max_per_owner:
                    self._drop(mine.pop(0))
            while self._store and (
                len(self._store) >= self._max_entries or self._total_bytes + size > self._max_total_bytes
            ):
                self._drop(min(self._store, key=self._age_key))
            self._store[token] = entry
            self._total_bytes += size
        self._ensure_sweeper()
        return token

    def get(self, token: str) -> PreflightEntry | None:
        """Retrieve cached entry. Returns None if token is unknown or expired."""
        with self._lock:
            entry = self._store.get(token)
            if entry is None:
                return None
            if self._expired(entry):
                self._drop(token)
                return None
            return entry

    def take(self, token: str, owner_id: int) -> PreflightEntry | None:
        """Atomically remove and return the entry, if ``owner_id`` uploaded it.

        Sprint 840: one lock acquisition, so two concurrent requests cannot both
        consume one token; a token presented by anyone other than its owner
        returns None and leaves the entry alone.
        """
        with self._lock:
            entry = self._store.get(token)
            if entry is None:
                return None
            if self._expired(entry):
                self._drop(token)
                return None
            if entry.owner_id != owner_id:
                return None
            self._drop(token)
            return entry

    def remove(self, token: str) -> None:
        """Explicitly remove an entry (e.g., after successful consumption)."""
        with self._lock:
            if token in self._store:
                self._drop(token)

    def purge_owner(self, owner_id: int, *, created_before_wall: Optional[float] = None) -> int:
        """Drop every entry ``owner_id`` uploaded (optionally only older ones)."""
        with self._lock:
            doomed = [
                k
                for k, v in self._store.items()
                if v.owner_id == owner_id and (created_before_wall is None or v.created_wall < created_before_wall)
            ]
            for k in doomed:
                self._drop(k)
            return len(doomed)

    def sweep(self) -> None:
        """Remove expired entries and apply other workers' purge requests."""
        with self._lock:
            self._evict_expired()
            empty = not self._store
        if empty or self._purge_source is None:
            return
        try:
            requests = list(self._purge_source())
        except Exception:  # noqa: BLE001 — a DB hiccup must not kill the sweeper
            logger.warning("Preview purge requests could not be read")
            return
        for owner_id, requested_at in requests:
            self.purge_owner(owner_id, created_before_wall=requested_at)

    def stop(self) -> None:
        """Stop the sweeper (tests)."""
        self._stop.set()
        if self._sweeper is not None:
            self._sweeper.join(timeout=2)

    # -- internals ----------------------------------------------------------

    def _age_key(self, token: str) -> float:
        return self._store[token].created_at

    def _expired(self, entry: PreflightEntry) -> bool:
        return self._clock() - entry.created_at >= self._ttl

    def _drop(self, token: str) -> None:
        """Remove one entry. Must be called under lock."""
        entry = self._store.pop(token)
        self._total_bytes -= len(entry.file_bytes)

    def _evict_expired(self) -> None:
        """Remove all expired entries. Must be called under lock."""
        for k in [k for k, v in self._store.items() if self._expired(v)]:
            self._drop(k)

    def _ensure_sweeper(self) -> None:
        pid = os.getpid()
        if self._sweeper is not None and self._sweeper_pid == pid and self._sweeper.is_alive():
            return
        with self._lock:
            if self._sweeper is not None and self._sweeper_pid == pid and self._sweeper.is_alive():
                return
            self._stop.set()  # an inherited (forked) or dead sweeper's loop ends
            self._stop = threading.Event()
            self._sweeper_pid = pid
            self._sweeper = threading.Thread(target=self._run, name="PreflightCacheSweeper", daemon=True)
            self._sweeper.start()

    def _run(self) -> None:
        stop = self._stop
        while not stop.wait(self._sweep_interval):
            try:
                self.sweep()
            except Exception:  # noqa: BLE001 — keep sweeping
                logger.warning("Preview cache sweep failed")


# Module-level singleton
preflight_cache = PreflightCache()
