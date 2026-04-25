"""Sprint 719 — Webhook event-ordering / off-by-one regression test.

The 2026-04-24 Guardian audit flagged
``backend/billing/webhook_handler.py:978`` where the stale-event guard
read ``if event_time < sub_updated``. Equal-second events bypassed the
guard. Sprint 719 fix: change `<` to `<=`.

This test:
1. Asserts equal-time events are now skipped (the off-by-one fix).
2. Asserts strictly-older events are still skipped (no regression).
3. Asserts strictly-newer events are still processed (no regression).

The Sprint 719 fix lives at ``billing/webhook_handler.py`` in
``process_webhook_event`` for the subscription-event ordering branch.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_subscription_updated_at():
    """Pinned datetime to use as Subscription.updated_at."""
    return datetime(2026, 4, 24, 12, 0, 0, tzinfo=UTC)


def _run_with_event_created(event_created: int, sub_updated_at: datetime) -> bool:
    """Invoke process_webhook_event with mocked dependencies, return its result."""
    from billing import webhook_handler

    mock_db = MagicMock()
    mock_sub = MagicMock()
    mock_sub.updated_at = sub_updated_at

    # Patch the WEBHOOK_HANDLERS lookup to use a sentinel that records its
    # invocation; if the stale-event guard works, the sentinel is NOT called.
    handler_called = {"called": False}

    def sentinel_handler(db, event_data):  # noqa: ARG001
        handler_called["called"] = True

    with (
        patch.object(
            webhook_handler,
            "WEBHOOK_HANDLERS",
            {"customer.subscription.updated": sentinel_handler},
        ),
        patch.object(webhook_handler, "get_subscription", return_value=mock_sub),
        patch.object(webhook_handler, "_resolve_user_id", return_value=42),
    ):
        result = webhook_handler.process_webhook_event(
            mock_db,
            "customer.subscription.updated",
            event_data={"id": "sub_test", "customer": "cus_test"},
            event_created=event_created,
        )

    return handler_called["called"]


def test_equal_time_event_is_skipped(mock_subscription_updated_at: datetime):
    """Sprint 719: equal-second events are now skipped as stale.

    Pre-Sprint-719 (`<`): equal-time events fell through to the handler
    and risked double-applying state changes. Post-Sprint-719 (`<=`):
    equal-time events are skipped — the safer default given Stripe's
    second-resolution `event.created` versus our millisecond-resolution
    `sub.updated_at`.
    """
    event_created = int(mock_subscription_updated_at.timestamp())
    handler_was_called = _run_with_event_created(event_created, mock_subscription_updated_at)
    assert not handler_was_called, (
        "Sprint 719: equal-time event should be skipped as stale. "
        "If this test fails, the off-by-one regression is back."
    )


def test_older_event_is_still_skipped(mock_subscription_updated_at: datetime):
    """Strictly-older events (event_time < sub_updated) are skipped.

    No-regression test for the original guard behavior.
    """
    older = mock_subscription_updated_at - timedelta(seconds=60)
    handler_was_called = _run_with_event_created(int(older.timestamp()), mock_subscription_updated_at)
    assert not handler_was_called


def test_newer_event_is_processed(mock_subscription_updated_at: datetime):
    """Strictly-newer events (event_time > sub_updated) are processed.

    No-regression test confirming the guard doesn't over-skip.
    """
    newer = mock_subscription_updated_at + timedelta(seconds=60)
    handler_was_called = _run_with_event_created(int(newer.timestamp()), mock_subscription_updated_at)
    assert handler_was_called
