"""Sprint 893: an unused preview is released after its TTL without waiting for another preview."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.preflight_cache import SWEEP_SECONDS, TTL_SECONDS, PreflightCache


def _wait_until(predicate, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


def test_unused_entry_is_released_with_no_further_puts():
    cache = PreflightCache(ttl_seconds=0.2, sweep_seconds=0.05)
    try:
        cache.put(b"secret tb bytes", "tb.pdf", owner_id=1)
        assert len(cache) == 1
        # No put, get or take after this point: only the sweeper can release it.
        assert _wait_until(lambda: len(cache) == 0, timeout=3.0)
    finally:
        cache.stop_sweeper()


def test_entry_is_kept_until_its_ttl():
    cache = PreflightCache(ttl_seconds=5, sweep_seconds=0.05)
    try:
        token = cache.put(b"bytes", "tb.pdf", owner_id=1)
        time.sleep(0.3)
        assert len(cache) == 1
        assert cache.take(token, owner_id=1) is not None
    finally:
        cache.stop_sweeper()


def test_published_bound_is_ten_minutes_plus_one_sweep():
    # The copy says previews are held for up to 10 minutes; the sweep keeps release close to that.
    assert TTL_SECONDS == 600
    assert SWEEP_SECONDS <= 30
