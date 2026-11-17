"""Sprint 879d (review DH-07): a previewed file is gone within 10 minutes.

``PreflightCache`` evicted expired entries only inside ``put()``; ``get()`` and
``take()`` expired just the token they read. An abandoned preview in an idle
worker stayed in memory indefinitely, and the cap was 100 entries, not bytes.

Now every process sweeps on a timer, the cache has a byte budget and a
per-user limit, and logout / account deletion remove a user's previews — in
the worker that handled the request at once, and in every other worker on its
next sweep (``preview_purge_requests``). Owner binding and single use stay.
"""

from __future__ import annotations

import time

import pytest

from shared.preflight_cache import PreflightCache
from tests.test_firm_owned_records import api  # noqa: F401 — `api` is a fixture

TTL = 600


class _Clock:
    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now


def _wait_until(pred, timeout: float = 3.0) -> bool:  # noqa: ANN001
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.01)
    return pred()


def _cache(clock: _Clock, **kw) -> PreflightCache:  # noqa: ANN003
    kw.setdefault("sweep_interval", 0.02)
    kw.setdefault("purge_source", None)
    return PreflightCache(ttl_seconds=TTL, clock=clock, **kw)


# --- the timer ---------------------------------------------------------------


def test_an_abandoned_preview_is_swept_with_no_other_cache_calls():
    clock = _Clock()
    cache = _cache(clock)
    try:
        cache.put(b"Cash,1000\n" * 1000, "tb.csv", owner_id=1)
        assert cache.total_bytes > 0
        clock.now += TTL - 1
        time.sleep(0.1)  # several sweeps — still inside the 10 minutes
        assert len(cache._store) == 1
        clock.now += 2  # past 10 minutes; nothing touches the cache from here on
        assert _wait_until(lambda: len(cache._store) == 0), "expired preview still held"
        assert cache.total_bytes == 0
    finally:
        cache.stop()


def test_the_sweeper_runs_in_a_forked_child(monkeypatch):
    """A worker forked from a preloaded master starts its own sweeper."""
    import os

    clock = _Clock()
    cache = _cache(clock)
    try:
        cache.put(b"x", "a.csv", owner_id=1)
        first = cache._sweeper
        monkeypatch.setattr(os, "getpid", lambda: -12345)
        cache.put(b"y", "b.csv", owner_id=2)
        assert cache._sweeper is not first and cache._sweeper.is_alive()
    finally:
        cache.stop()


# --- size budget and per-user limit ------------------------------------------


def test_the_byte_budget_holds_under_several_large_previews():
    clock = _Clock()
    cache = _cache(clock, max_total_bytes=10_000, max_entries_per_owner=10)
    try:
        tokens = []
        for owner in range(6):
            clock.now += 1
            tokens.append(cache.put(b"z" * 3_000, "big.xlsx", owner_id=owner))
            assert cache.total_bytes <= 10_000
        assert len(cache._store) == 3
        # Oldest went first; the newest three survive.
        assert all(cache.get(t) is None for t in tokens[:3])
        assert all(cache.get(t) is not None for t in tokens[3:])
    finally:
        cache.stop()


def test_a_preview_larger_than_the_whole_budget_is_not_cached():
    cache = _cache(_Clock(), max_total_bytes=1_000)
    try:
        assert cache.put(b"z" * 1_001, "huge.pdf", owner_id=1) is None
        assert cache.total_bytes == 0
    finally:
        cache.stop()


def test_per_user_limit_evicts_that_users_oldest_only():
    clock = _Clock()
    cache = _cache(clock, max_entries_per_owner=2)
    try:
        other = cache.put(b"o", "o.csv", owner_id=99)
        clock.now += 1
        a = cache.put(b"a", "a.csv", owner_id=1)
        clock.now += 1
        b = cache.put(b"b", "b.csv", owner_id=1)
        clock.now += 1
        c = cache.put(b"c", "c.csv", owner_id=1)
        assert cache.get(a) is None
        assert cache.get(b) is not None and cache.get(c) is not None
        assert cache.get(other) is not None
    finally:
        cache.stop()


# --- owner binding and single use (unchanged) --------------------------------


def test_wrong_owner_cannot_take_and_the_entry_survives():
    cache = _cache(_Clock())
    try:
        t = cache.put(b"data", "f.csv", owner_id=1)
        assert cache.take(t, owner_id=2) is None
        assert cache.take(t, owner_id=1) is not None
    finally:
        cache.stop()


def test_a_token_is_single_use():
    cache = _cache(_Clock())
    try:
        t = cache.put(b"data", "f.csv", owner_id=1)
        assert cache.take(t, owner_id=1) is not None
        assert cache.take(t, owner_id=1) is None
    finally:
        cache.stop()


# --- purge on logout / deletion -----------------------------------------------


def test_purge_owner_removes_only_that_users_entries():
    cache = _cache(_Clock())
    try:
        mine = [cache.put(b"m", "m.csv", owner_id=1) for _ in range(2)]
        theirs = cache.put(b"t", "t.csv", owner_id=2)
        assert cache.purge_owner(1) == 2
        assert all(cache.get(t) is None for t in mine)
        assert cache.get(theirs) is not None
    finally:
        cache.stop()


def test_another_workers_purge_request_is_applied_on_the_next_sweep():
    """Logout handled by worker A; this cache is worker B's."""
    requests: list[tuple[int, float]] = []
    clock = _Clock()
    cache = _cache(clock, purge_source=lambda: list(requests))
    try:
        before = cache.put(b"old", "old.csv", owner_id=7)
        keep = cache.put(b"k", "k.csv", owner_id=8)
        requests.append((7, time.time() + 0.001))  # worker A records the logout
        time.sleep(0.01)
        after = cache.put(b"new", "new.csv", owner_id=7)  # signed in again afterwards
        assert _wait_until(lambda: before not in cache._store)
        assert after in cache._store and keep in cache._store
    finally:
        cache.stop()


# --- through the app ------------------------------------------------------------


@pytest.mark.asyncio
async def test_logout_removes_the_users_previews(db_session, make_user, make_refresh_token):
    import httpx

    from config import REFRESH_COOKIE_NAME
    from database import get_db
    from main import app
    from security_middleware import generate_csrf_token
    from shared.preflight_cache import preflight_cache
    from shared.preflight_purge import PreviewPurgeRequest

    user = make_user(email="preview-logout@example.com")
    other = make_user(email="preview-logout-other@example.com")
    raw, _row = make_refresh_token(user=user)
    mine = preflight_cache.put(b"Cash,1000\n", "tb.csv", owner_id=user.id)
    theirs = preflight_cache.put(b"Cash,2000\n", "tb.csv", owner_id=other.id)
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", cookies={REFRESH_COOKIE_NAME: raw}
        ) as client:
            r = await client.post(
                "/auth/logout",
                headers={"X-CSRF-Token": generate_csrf_token(str(user.id)), "X-Requested-With": "XMLHttpRequest"},
            )
        assert r.status_code == 200, r.text
        assert mine not in preflight_cache._store
        assert theirs in preflight_cache._store
        # Other workers learn of it from the shared purge request.
        assert db_session.query(PreviewPurgeRequest).filter(PreviewPurgeRequest.user_id == user.id).count() == 1
    finally:
        app.dependency_overrides.pop(get_db, None)
        preflight_cache.remove(theirs)


def test_account_deletion_removes_the_users_previews(db_session, make_user):
    from services.account_erasure import erase_account
    from shared.preflight_cache import preflight_cache
    from shared.preflight_purge import PreviewPurgeRequest

    user = make_user(email="preview-erase@example.com")
    uid = user.id
    token = preflight_cache.put(b"Cash,1000\n", "tb.csv", owner_id=uid)
    erase_account(db_session, user)
    assert token not in preflight_cache._store
    assert db_session.query(PreviewPurgeRequest).filter(PreviewPurgeRequest.user_id == uid).count() == 1


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_a_miss_at_analysis_time_completes_from_the_resent_file(api, make_user):  # noqa: ANN001
    """The browser always sends the file with the token (buildTrialBalanceFormData),
    so a miss — another worker, expired, purged — analyses the re-sent bytes."""
    from models import UserTier
    from tests.test_firm_owned_records import _auth

    user = make_user(email="preview-miss@example.com", tier=UserTier.SOLO)
    tb = b"Account,Debit,Credit\nCash,1000,0\nRevenue,0,1000\n"
    r = await api.post(
        "/audit/trial-balance",
        files={"file": ("tb.csv", tb, "text/csv")},
        data={"preflight_token": "0" * 32},  # not in this worker's cache
        headers=_auth(user),
    )
    assert r.status_code == 200, r.text
    assert r.json()["balanced"] is True or r.json().get("was_balanced") is True
