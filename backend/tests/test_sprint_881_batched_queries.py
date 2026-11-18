"""Sprint 881 (ST-16) — two billing loops no longer query once per row.

* ``internal_metrics._compute_median_conversion_time`` ran one query per conversion to
  find the trial that preceded it.
* ``dunning_engine.process_grace_period_expirations`` loaded the subscription and the
  user inside its loop, and the suspension email loaded the user a second time.

Both now load what they need in batches. Each test runs the work over a small and a
larger set of records and asserts the look-up count does not grow with the row count,
and that results (and, for dunning, the transaction and email order) are unchanged.

Known limit, kept on purpose: ``record_billing_event`` commits once per churn event
(the existing transaction behaviour), which expires the loaded rows, so the next
episode re-reads its rows by primary key. Those refresh reads still scale with the
episodes; removing them means changing the commit boundaries.
"""

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import event

from models import User, UserTier
from subscription_model import BillingEvent, BillingEventType, BillingInterval, Subscription, SubscriptionStatus


@contextmanager
def count_selects(db_session):
    selects: list[str] = []

    def _listener(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            selects.append(statement)

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", _listener)
    try:
        yield selects
    finally:
        event.remove(engine, "before_cursor_execute", _listener)


def _user(db_session, email, tier=UserTier.SOLO):
    user = User(email=email, hashed_password="x", tier=tier, is_active=True, is_verified=True)
    db_session.add(user)
    db_session.flush()
    return user


def _event(db_session, event_type, user_id, at):
    db_session.add(BillingEvent(event_type=event_type, user_id=user_id, tier="solo", created_at=at))


# ---------------------------------------------------------------------------
# Median time to conversion
# ---------------------------------------------------------------------------


class TestMedianConversionTimeIsBatched:
    def _seed(self, db_session, prefix, conversions, now):
        """Each user: trial (2 + i) days before converting. User 0 also has an older trial,
        and a trial *after* converting, to pin "the latest trial before the conversion"."""
        for i in range(conversions):
            user = _user(db_session, f"{prefix}{i}@example.com")
            converted = now - timedelta(days=1, hours=i)
            _event(db_session, BillingEventType.TRIAL_STARTED, user.id, converted - timedelta(days=2 + i))
            _event(db_session, BillingEventType.TRIAL_CONVERTED, user.id, converted)
            if i == 0:
                _event(db_session, BillingEventType.TRIAL_STARTED, user.id, converted - timedelta(days=40))
                _event(db_session, BillingEventType.TRIAL_STARTED, user.id, converted + timedelta(hours=1))
        db_session.flush()

    def _run(self, db_session, now):
        from billing.internal_metrics import _compute_median_conversion_time

        with count_selects(db_session) as selects:
            median = _compute_median_conversion_time(db_session, now - timedelta(days=30), now)
        return median, len(selects)

    def test_query_count_does_not_grow_with_conversions(self, db_session):
        now = datetime.now(UTC)
        self._seed(db_session, "st16_med_a_", 2, now)
        median_small, selects_small = self._run(db_session, now)

        self._seed(db_session, "st16_med_b_", 7, now)
        median_large, selects_large = self._run(db_session, now)

        assert selects_small == selects_large
        assert selects_large <= 2
        # 2 users: days 2, 3 → 2.5. 9 users: [2, 2, 3, 3, 4, 5, 6, 7, 8] → 4.
        assert median_small == pytest.approx(2.5, abs=0.05)
        assert median_large == pytest.approx(4.0, abs=0.05)

    def test_conversion_without_a_preceding_trial_is_skipped(self, db_session):
        now = datetime.now(UTC)
        user = _user(db_session, "st16_med_none@example.com")
        _event(db_session, BillingEventType.TRIAL_CONVERTED, user.id, now - timedelta(days=1))
        _event(db_session, BillingEventType.TRIAL_STARTED, user.id, now - timedelta(hours=1))  # after: ignored
        db_session.flush()
        median, _ = self._run(db_session, now)
        assert median is None


# ---------------------------------------------------------------------------
# Grace-period expiry
# ---------------------------------------------------------------------------


@contextmanager
def _quiet_dunning_emails():
    with (
        patch("email_service.send_dunning_first_failure"),
        patch("email_service.send_dunning_second_failure"),
        patch("email_service.send_dunning_final_notice"),
        patch("email_service.send_dunning_suspended") as suspended,
    ):
        yield suspended


class TestGracePeriodExpiryIsBatched:
    def _expired_episodes(self, db_session, prefix, count):
        from billing.dunning_engine import handle_payment_failed

        episodes = []
        for i in range(count):
            user = _user(db_session, f"{prefix}{i}@example.com")
            sub = Subscription(
                user_id=user.id,
                tier="solo",
                status=SubscriptionStatus.ACTIVE,
                billing_interval=BillingInterval.MONTHLY,
                seat_count=1,
                additional_seats=0,
            )
            db_session.add(sub)
            db_session.flush()
            for _ in range(3):
                episode = handle_payment_failed(db_session, sub)
            episode.last_failed_at = datetime.now(UTC) - timedelta(days=8)
            episodes.append(episode)
        db_session.flush()
        return episodes

    def _run(self, db_session):
        from billing.dunning_engine import process_grace_period_expirations

        with _quiet_dunning_emails() as suspended, count_selects(db_session) as selects:
            canceled = process_grace_period_expirations(db_session)
        touching = [s for s in selects if "FROM subscriptions" in s or "FROM users" in s]
        # Explicit per-row look-ups (``.first()`` → ``LIMIT``) — what ST-16 removed. Primary-key
        # refreshes after each per-event commit carry no LIMIT (see the module docstring).
        lookups = [s for s in touching if "LIMIT" in s.upper()]
        batches = [s for s in touching if " IN (" in s.upper() or "IN (__[" in s.upper()]
        return canceled, (lookups, batches), [c.args[0] for c in suspended.call_args_list]

    def test_query_count_does_not_grow_with_episodes(self, db_session):
        with _quiet_dunning_emails():
            self._expired_episodes(db_session, "st16_grace_a_", 2)
        canceled_small, lookups_small, emails_small = self._run(db_session)

        with _quiet_dunning_emails():
            episodes = self._expired_episodes(db_session, "st16_grace_b_", 5)
        canceled_large, lookups_large, emails_large = self._run(db_session)

        assert (canceled_small, canceled_large) == (2, 5)
        (per_row_small, batch_small), (per_row_large, batch_large) = lookups_small, lookups_large
        assert per_row_small == per_row_large == []
        assert len(batch_small) == len(batch_large) == 2  # one for subscriptions, one for users
        # Email order follows the episodes, as before.
        assert emails_large == [f"st16_grace_b_{i}@example.com" for i in range(5)]
        for episode in episodes:
            db_session.refresh(episode)
            sub = db_session.get(Subscription, episode.subscription_id)
            assert sub.status == SubscriptionStatus.CANCELED
            assert db_session.get(User, sub.user_id).tier == UserTier.FREE

    def test_churn_events_recorded_per_episode(self, db_session):
        with _quiet_dunning_emails():
            episodes = self._expired_episodes(db_session, "st16_grace_ev_", 3)
        self._run(db_session)
        user_ids = [db_session.get(Subscription, e.subscription_id).user_id for e in episodes]
        churned = (
            db_session.query(BillingEvent.user_id)
            .filter(
                BillingEvent.event_type == BillingEventType.SUBSCRIPTION_CHURNED, BillingEvent.user_id.in_(user_ids)
            )
            .order_by(BillingEvent.id)
            .all()
        )
        assert [u for (u,) in churned] == user_ids
