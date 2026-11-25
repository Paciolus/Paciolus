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
