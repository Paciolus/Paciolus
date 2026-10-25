"""Sprint 840: preflight tokens are single-use and bound to the uploading user."""

import threading

from shared.preflight_cache import PreflightCache


def test_owner_takes_the_entry_once():
    cache = PreflightCache()
    token = cache.put(b"bytes", "tb.csv", owner_id=7)
    entry = cache.take(token, 7)
    assert entry is not None and entry.file_bytes == b"bytes"
    assert cache.take(token, 7) is None


def test_another_user_cannot_take_it_and_does_not_burn_it():
    cache = PreflightCache()
    token = cache.put(b"bytes", "tb.csv", owner_id=7)
    assert cache.take(token, 8) is None
    assert cache.take(token, 7) is not None


def test_expired_entry_is_not_returned():
    cache = PreflightCache(ttl_seconds=-1)
    token = cache.put(b"bytes", "tb.csv", owner_id=7)
    assert cache.take(token, 7) is None


def test_concurrent_takes_consume_once():
    cache = PreflightCache()
    token = cache.put(b"bytes", "tb.csv", owner_id=7)
    results = []
    threads = [threading.Thread(target=lambda: results.append(cache.take(token, 7))) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sum(r is not None for r in results) == 1
