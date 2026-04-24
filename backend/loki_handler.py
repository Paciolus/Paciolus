"""
Loki HTTPS push handler (Sprint 716).

Attaches to the Python logging root as an additive destination alongside stdout.
Designed for Grafana Cloud Loki (Free tier) at ``/loki/api/v1/push``; also works
with self-hosted Loki behind Basic Auth.

Design constraints
------------------
- Zero new dependencies — uses stdlib ``urllib.request``. The request runs on a
  background daemon thread so emit() is non-blocking.
- Fail-open: if Loki is unreachable or returns non-2xx, the batch is dropped and
  a rate-limited warning is written to stderr. Logging never recurses back into
  the application logger (which would loop).
- Backpressure: emits land in a bounded in-memory queue. When the queue is full
  (e.g., Loki is down and traffic is heavy) further emits are silently dropped
  rather than blocking request handlers.
"""

from __future__ import annotations

import json
import logging
import queue
import sys
import threading
import time
import urllib.error
import urllib.request
from base64 import b64encode
from typing import Any

_STDERR_WARN_COOLDOWN_SECONDS = 300.0  # Print push errors at most once per 5 min


class LokiHandler(logging.Handler):
    """Background-threaded Loki HTTP push handler.

    Buffers log records in memory and flushes in batches to a Loki push endpoint
    on a daemon thread. emit() is non-blocking; flush failures are logged to
    stderr at most once per ``_STDERR_WARN_COOLDOWN_SECONDS`` to avoid log spam.
    """

    def __init__(
        self,
        url: str,
        user: str,
        token: str,
        labels: dict[str, str],
        batch_size: int = 100,
        flush_interval: float = 2.0,
        queue_maxsize: int = 10_000,
        timeout: float = 5.0,
    ) -> None:
        super().__init__()
        self._url = url
        self._auth = "Basic " + b64encode(f"{user}:{token}".encode()).decode()
        self._static_labels = dict(labels)
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._timeout = timeout
        self._queue: queue.Queue[logging.LogRecord] = queue.Queue(maxsize=queue_maxsize)
        self._stop = threading.Event()
        self._last_warn = 0.0
        self._thread = threading.Thread(
            target=self._run,
            name="LokiHandlerFlush",
            daemon=True,
        )
        self._thread.start()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            pass

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=self._flush_interval + self._timeout + 1.0)
        super().close()

    def _run(self) -> None:
        while not self._stop.is_set():
            batch = self._collect_batch()
            if batch:
                self._flush(batch)

        drain: list[logging.LogRecord] = []
        while True:
            try:
                drain.append(self._queue.get_nowait())
            except queue.Empty:
                break
        if drain:
            self._flush(drain)

    def _collect_batch(self) -> list[logging.LogRecord]:
        batch: list[logging.LogRecord] = []
        deadline = time.monotonic() + self._flush_interval
        while len(batch) < self._batch_size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                batch.append(self._queue.get(timeout=remaining))
            except queue.Empty:
                break
        return batch

    def _flush(self, records: list[logging.LogRecord]) -> None:
        payload = self._build_payload(records)
        self._post(payload)

    def _build_payload(self, records: list[logging.LogRecord]) -> dict[str, Any]:
        # Group by (level, logger) so each stream has coherent labels. Loki
        # requires values to be sorted ascending by timestamp within a stream.
        streams: dict[tuple[str, str], list[tuple[str, str]]] = {}
        for r in records:
            key = (r.levelname, r.name)
            ts_ns = str(int(r.created * 1_000_000_000))
            line = self.format(r)
            streams.setdefault(key, []).append((ts_ns, line))

        return {
            "streams": [
                {
                    "stream": {
                        **self._static_labels,
                        "level": level,
                        "logger": logger_name,
                    },
                    "values": sorted(values, key=lambda v: v[0]),
                }
                for (level, logger_name), values in streams.items()
            ]
        }

    def _post(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": self._auth,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # nosec B310 — fixed https URL from config
                if resp.status >= 300:
                    self._warn_stderr(f"Loki push returned HTTP {resp.status}")
        except (urllib.error.URLError, OSError) as exc:
            self._warn_stderr(f"Loki push failed: {exc}")

    def _warn_stderr(self, msg: str) -> None:
        now = time.monotonic()
        if now - self._last_warn > _STDERR_WARN_COOLDOWN_SECONDS:
            self._last_warn = now
            print(f"[LokiHandler] {msg}", file=sys.stderr)
