"""Sprint 897 (O-4): the bulk-job store and the IP failure tracker retry Redis.

Before this sprint, one failed Redis probe pinned a worker to its private
in-memory store for the life of the process: bulk-job status polls 404'd on
other workers and IP failure counts split per worker, with no recovery short
of a restart. Both now retry the probe after ``_REDIS_RETRY_SECONDS``, as
Sprint 877 did for impersonation revocation.
"""

from __future__ import annotations

import pytest

import config
from shared import bulk_job_store, ip_failure_tracker


class _FakeClient:
    def ping(self) -> bool:
        return True


@pytest.fixture(params=[bulk_job_store, ip_failure_tracker], ids=["bulk_job_store", "ip_failure_tracker"])
def store(request, monkeypatch):
    module = request.param
    module._reset_redis_probe_for_tests()
    yield module
    module._reset_redis_probe_for_tests()


def _patch_redis(monkeypatch, outcomes: list[object]) -> list[int]:
    import redis

    calls: list[int] = []

    def from_url(*_args, **_kwargs):
        calls.append(1)
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(redis.Redis, "from_url", staticmethod(from_url))
    return calls


def test_failed_probe_is_retried_after_the_window(store, monkeypatch):
    monkeypatch.setattr(config, "REDIS_URL", "redis://example.invalid:6379/0")
    client = _FakeClient()
    calls = _patch_redis(monkeypatch, [ConnectionError("down"), client])
    now = [1_000.0]
    monkeypatch.setattr(store.time, "time", lambda: now[0])

    assert store._get_redis() is None
    assert len(calls) == 1

    # Inside the window: memory fallback, no new probe.
    now[0] += store._REDIS_RETRY_SECONDS - 1
    assert store._get_redis() is None
    assert len(calls) == 1

    # After the window: probe again and recover.
    now[0] += 2
    assert store._get_redis() is client
    assert len(calls) == 2

    # Once connected the client is reused without probing.
    assert store._get_redis() is client
    assert len(calls) == 2


def test_no_redis_url_is_settled_once(store, monkeypatch):
    monkeypatch.setattr(config, "REDIS_URL", None)
    calls = _patch_redis(monkeypatch, [])
    now = [1_000.0]
    monkeypatch.setattr(store.time, "time", lambda: now[0])

    assert store._get_redis() is None
    now[0] += 10_000
    assert store._get_redis() is None
    assert calls == []


class _FakeSortedSetRedis:
    """Just enough of redis for the IP failure tracker."""

    def __init__(self) -> None:
        self.sets: dict[str, dict[str, float]] = {}

    def ping(self) -> bool:
        return True

    def zremrangebyscore(self, key, _lo, hi):
        members = self.sets.get(key, {})
        for m in [m for m, s in members.items() if s <= hi]:
            del members[m]

    def zcard(self, key) -> int:
        return len(self.sets.get(key, {}))


class _FakeKeyValueRedis:
    """Just enough of redis for the bulk-job store."""

    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def ping(self) -> bool:
        return True

    def set(self, key, value, ex=None):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        self.data.pop(key, None)


def test_reconnect_does_not_lift_an_active_ip_block(monkeypatch):
    """PR #341 review: failures counted in memory during an outage still count after Redis returns."""
    tracker = ip_failure_tracker
    tracker._reset_redis_probe_for_tests()
    tracker._memory_store.clear()
    monkeypatch.setattr(config, "REDIS_URL", "redis://example.invalid:6379/0")
    client = _FakeSortedSetRedis()
    _patch_redis(monkeypatch, [ConnectionError("down"), client])
    now = [10_000.0]
    monkeypatch.setattr(tracker.time, "time", lambda: now[0])
    try:
        for _ in range(20):
            tracker.record_failure("203.0.113.9", window_seconds=900)
        assert tracker.is_blocked("203.0.113.9", window_seconds=900, threshold=20)

        now[0] += tracker._REDIS_RETRY_SECONDS + 1
        assert tracker._get_redis() is client
        assert tracker.is_blocked("203.0.113.9", window_seconds=900, threshold=20)

        # Once the window passes the memory failures expire as usual.
        now[0] += 900
        assert not tracker.is_blocked("203.0.113.9", window_seconds=900, threshold=20)
    finally:
        tracker._memory_store.clear()
        tracker._reset_redis_probe_for_tests()


def test_job_written_during_outage_is_found_after_reconnect(monkeypatch):
    """PR #341 review (same class): a job stored in memory is not lost when Redis returns."""
    from datetime import UTC, datetime

    jobs = bulk_job_store
    jobs._reset_redis_probe_for_tests()
    jobs._memory_store.clear()
    monkeypatch.setattr(config, "REDIS_URL", "redis://example.invalid:6379/0")
    client = _FakeKeyValueRedis()
    _patch_redis(monkeypatch, [ConnectionError("down"), client])
    now = [10_000.0]
    monkeypatch.setattr(jobs.time, "time", lambda: now[0])
    job = {"status": "running", "created_at": datetime.now(UTC).isoformat()}
    try:
        jobs.put("job-1", job)
        now[0] += jobs._REDIS_RETRY_SECONDS + 1
        assert jobs._get_redis() is client
        assert jobs.get("job-1") == job

        # The next write goes to Redis and supersedes the memory copy.
        updated = {**job, "status": "done"}
        jobs.put("job-1", updated)
        assert "job-1" not in jobs._memory_store
        assert jobs.get("job-1") == updated
    finally:
        jobs._memory_store.clear()
        jobs._reset_redis_probe_for_tests()
