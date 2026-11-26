"""Per-process limit on concurrent upload parses (Sprint 897, O-2).

Render Standard gives the whole container 2 GB and one CPU, shared by every
Gunicorn worker. A 100 MB workbook can take several hundred MB while pandas
and openpyxl materialise it, and parses run in worker threads with no limit,
so a handful of large uploads arriving together could OOM-kill the service
for everyone. This module caps how many heavy parses one process runs at
once; the rest wait for a slot and, if none frees up in time, get a 503 with
``Retry-After`` instead of taking the container down.

Settings (read once at import):
    UPLOAD_PARSE_CONCURRENCY   slots per process, default 2 (minimum 1)
    UPLOAD_PARSE_WAIT_SECONDS  how long a parse waits for a slot, default 60

The slot is re-entrant per thread: a parse that already holds a slot and
calls another guarded function (for example a TB analysis that parses its
file through the shared pipeline) does not take a second slot, so it can
never deadlock against itself.
"""

from __future__ import annotations

import functools
import logging
import os
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import ParamSpec, TypeVar

from fastapi import HTTPException

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

DEFAULT_PARSE_CONCURRENCY = 2
DEFAULT_PARSE_WAIT_SECONDS = 60.0


def _read_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("%s=%r is not an integer — using %d", name, raw, default)
        return default
    return value if value >= 1 else default


def _read_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        logger.warning("%s=%r is not a number — using %s", name, raw, default)
        return default
    return value if value > 0 else default


PARSE_CONCURRENCY = _read_int("UPLOAD_PARSE_CONCURRENCY", DEFAULT_PARSE_CONCURRENCY)
PARSE_WAIT_SECONDS = _read_float("UPLOAD_PARSE_WAIT_SECONDS", DEFAULT_PARSE_WAIT_SECONDS)

_semaphore = threading.BoundedSemaphore(PARSE_CONCURRENCY)
_held = threading.local()


class ParseCapacityExceeded(HTTPException):
    """Raised when no parse slot frees up within the wait limit."""

    def __init__(self) -> None:
        super().__init__(
            status_code=503,
            detail="The service is busy processing other large files. Please try again in a minute.",
            headers={"Retry-After": "30"},
        )


def configure(concurrency: int, wait_seconds: float | None = None) -> None:
    """Replace the limit. For tests only — production reads the environment at import."""
    global _semaphore, PARSE_CONCURRENCY, PARSE_WAIT_SECONDS
    PARSE_CONCURRENCY = max(1, concurrency)
    _semaphore = threading.BoundedSemaphore(PARSE_CONCURRENCY)
    if wait_seconds is not None:
        PARSE_WAIT_SECONDS = wait_seconds


@contextmanager
def parse_slot() -> Iterator[None]:
    """Hold one parse slot for the duration of the block (re-entrant per thread)."""
    depth = getattr(_held, "depth", 0)
    if depth:
        _held.depth = depth + 1
        try:
            yield
        finally:
            _held.depth -= 1
        return

    sem = _semaphore
    if not sem.acquire(timeout=PARSE_WAIT_SECONDS):
        logger.warning(
            "upload.parse.capacity_exceeded concurrency=%d wait_seconds=%s", PARSE_CONCURRENCY, PARSE_WAIT_SECONDS
        )
        raise ParseCapacityExceeded()
    _held.depth = 1
    try:
        yield
    finally:
        _held.depth = 0
        sem.release()


def limit_parse_concurrency(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator form of :func:`parse_slot`."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with parse_slot():
            return func(*args, **kwargs)

    return wrapper
