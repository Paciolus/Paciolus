"""Memory probe + soft budget enforcement for memo generation (Sprint 722).

ReportLab + openpyxl accumulate in RAM. On Render Standard 2 GB, generating
many memos back-to-back risks OOM-killing the worker before any Sentry signal
reaches us. This module gives every memo route a uniform RSS probe + GC sweep
+ Sentry warning when the post-generation footprint crosses ``MEMO_RSS_WARN_MB``.

The recurrence-prevention story for Sprint 722 is:

    1. Every memo PDF goes through ``track_memo_memory()`` (wired into
       ``routes.export_memos._memo_export_handler``). New memo endpoints inherit
       the probe automatically — there is no per-generator opt-in to forget.
    2. ``backend/tests/test_memo_memory_budget.py`` exercises the probe and
       asserts the gc sweep keeps RSS bounded across repeated invocations of a
       representative memo. Removing ``gc.collect()`` regresses the test.
    3. The companion runbook ``docs/runbooks/memory-pressure.md`` documents
       how to read the structured logs and what to do when the alert fires.

Threshold rationale (corrected Sprint 897, O-2): Render Standard is 2 GB for the
whole container, shared by every Gunicorn worker — not 2 GB per worker. With the
default two workers each has roughly 1 GB, and a large upload parse can take
several hundred MB of that, so the warning fires at 600 MB per process: early
enough to act before the container is OOM-killed. Override per environment via
``MEMO_RSS_WARN_MB``.
"""

from __future__ import annotations

import gc
import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter

import psutil

logger = logging.getLogger(__name__)

DEFAULT_WARN_MB = 600


def _resolve_warn_threshold_mb() -> int:
    """Read ``MEMO_RSS_WARN_MB`` from env. Falls back to ``DEFAULT_WARN_MB`` (600 MB per process; see the module docstring)."""
    raw = os.environ.get("MEMO_RSS_WARN_MB")
    if not raw:
        return DEFAULT_WARN_MB
    try:
        value = int(raw)
    except ValueError:
        logger.warning("memo.memory.invalid_threshold value=%r — using %d MB", raw, DEFAULT_WARN_MB)
        return DEFAULT_WARN_MB
    return value if value > 0 else DEFAULT_WARN_MB


def get_rss_mb() -> float:
    """Resident set size for the current process, in MB. Process-local; no cross-worker aggregation."""
    return psutil.Process().memory_info().rss / (1024 * 1024)


@contextmanager
def track_memo_memory(label: str) -> Iterator[None]:
    """Wrap a memo-generation call with RSS logging + gc sweep + Sentry warning on threshold breach.

    Emits two structured log lines per invocation:

        memo.memory.before label=<label> rss_mb=<float>
        memo.memory.after  label=<label> rss_mb=<float> delta_mb=<float> elapsed_ms=<float>

    On post-generation RSS > ``MEMO_RSS_WARN_MB``, also emits a Sentry warning
    breadcrumb + ``capture_message`` so the alert fires before OOM-kill clips the
    worker. The gc sweep runs unconditionally — it's the cheap part and the
    main reason this wrapper exists.
    """
    threshold_mb = _resolve_warn_threshold_mb()
    rss_before = get_rss_mb()
    started = perf_counter()
    logger.info("memo.memory.before label=%s rss_mb=%.1f", label, rss_before)
    try:
        yield
    finally:
        # Sweep first so the post-RSS reading reflects the steady state the next
        # request will inherit, not the temporary peak inside the generator.
        gc.collect()
        rss_after = get_rss_mb()
        elapsed_ms = (perf_counter() - started) * 1000
        logger.info(
            "memo.memory.after label=%s rss_mb=%.1f delta_mb=%+.1f elapsed_ms=%.0f",
            label,
            rss_after,
            rss_after - rss_before,
            elapsed_ms,
        )
        if rss_after > threshold_mb:
            logger.warning(
                "memo.memory.threshold_breach label=%s rss_mb=%.1f threshold_mb=%d",
                label,
                rss_after,
                threshold_mb,
            )
            _emit_sentry_warning(label, rss_after, threshold_mb)


def _emit_sentry_warning(label: str, rss_mb: float, threshold_mb: int) -> None:
    """Emit a Sentry warning + breadcrumb. Soft-imports sentry_sdk so unit tests don't require it."""
    try:
        import sentry_sdk
    except ImportError:
        return
    sentry_sdk.add_breadcrumb(
        category="memo.memory",
        level="warning",
        message=f"{label} post-generation RSS {rss_mb:.0f} MB exceeded threshold {threshold_mb} MB",
        data={"label": label, "rss_mb": rss_mb, "threshold_mb": threshold_mb},
    )
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("memo.label", label)
        scope.set_extra("rss_mb", rss_mb)
        scope.set_extra("threshold_mb", threshold_mb)
        sentry_sdk.capture_message(
            f"Memo memory threshold exceeded: {label} rss={rss_mb:.0f}MB",
            level="warning",
        )
