"""
Sprint 821 — the subscription row is read once per request, not three times.

A testing upload resolved it in tool access, then twice in the upload-limit
check. The loader remembers only the primary key and returns the row through
``Session.get``, so a deleted or re-pointed row is never served stale.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import event

sys.path.insert(0, str(Path(__file__).parent.parent))


def _count_subscription_selects(db_session):
    calls: list[str] = []

    def _listener(conn, cursor, statement, params, context, executemany):
        if statement.lstrip().upper().startswith("SELECT") and "FROM subscriptions" in statement:
            calls.append(statement)

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", _listener)
    return calls, lambda: event.remove(engine, "before_cursor_execute", _listener)


def _subscribed_user(make_user, db_session, uploads_used=0):
    from subscription_model import BillingInterval, Subscription, SubscriptionStatus

    user = make_user(email="sub-queries@example.com")
    db_session.add(
        Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            uploads_used_current_period=uploads_used,
            **_current_window(),
        )
    )
    db_session.flush()
    return user


def test_one_subscription_query_for_access_and_upload_limit(make_user, db_session):
    from shared.entitlement_checks import check_upload_limit, get_effective_entitlements

    user = _subscribed_user(make_user, db_session)
    calls, stop = _count_subscription_selects(db_session)
    try:
        get_effective_entitlements(user, db_session)
        check_upload_limit(user=user, db=db_session)
        check_upload_limit(user=user, db=db_session)
    finally:
        stop()
    assert len(calls) == 1


def test_a_deleted_subscription_is_not_served_from_the_cache(make_user, db_session):
    from shared.entitlement_checks import _user_subscription

    user = _subscribed_user(make_user, db_session)
    sub = _user_subscription(db_session, user.id)
    assert sub is not None
    db_session.delete(sub)
    db_session.flush()
    assert _user_subscription(db_session, user.id) is None


def test_increment_updates_the_same_row_the_limit_check_reads(make_user, db_session):
    from shared.entitlement_checks import _user_subscription, increment_upload_count

    user = _subscribed_user(make_user, db_session, uploads_used=3)
    increment_upload_count(db_session, user.id)
    assert _user_subscription(db_session, user.id).uploads_used_current_period == 4


def _current_window() -> dict:
    """Subscription kwargs placing a seeded counter in the current monthly window.

    Sprint 790 (PR #227 review): a count is only read while
    ``uploads_window_start`` is the current window; a NULL window reads as 0.
    """
    from datetime import UTC, datetime, timedelta

    start = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
    return {
        "current_period_start": start,
        "current_period_end": start + timedelta(days=30),
        "uploads_window_start": start,
    }
