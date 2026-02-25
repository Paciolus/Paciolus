"""
Billing analytics tests — Phase LX post-launch control.

Tests:
- BillingEvent model creation and constraints
- record_billing_event() with Prometheus counter
- 5 decision metric queries (trial starts, conversion rate, paid by plan, avg seats, cancellations)
- Weekly review aggregation with deltas
- Webhook handler event recording integration
"""

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from subscription_model import (
    BillingEvent,
    BillingEventType,
    BillingInterval,
    Subscription,
    SubscriptionStatus,
)

# ---------------------------------------------------------------------------
# BillingEvent model
# ---------------------------------------------------------------------------


class TestBillingEventModel:
    """Test BillingEvent model creation and serialization."""

    def test_create_billing_event(self, db_session, make_user):
        user = make_user(email="event_test@example.com")
        event = BillingEvent(
            user_id=user.id,
            event_type=BillingEventType.TRIAL_STARTED,
            tier="solo",
            interval="monthly",
        )
        db_session.add(event)
        db_session.flush()
        assert event.id is not None
        assert event.event_type == BillingEventType.TRIAL_STARTED
        assert event.tier == "solo"

    def test_billing_event_nullable_user(self, db_session):
        """Events from webhooks may have no resolved user_id."""
        event = BillingEvent(
            user_id=None,
            event_type=BillingEventType.PAYMENT_FAILED,
            tier="team",
        )
        db_session.add(event)
        db_session.flush()
        assert event.id is not None
        assert event.user_id is None

    def test_billing_event_metadata_json(self, db_session, make_user):
        user = make_user(email="meta_test@example.com")
        meta = {"reason": "too_expensive", "feedback": "Need more features"}
        event = BillingEvent(
            user_id=user.id,
            event_type=BillingEventType.SUBSCRIPTION_CANCELED,
            tier="solo",
            metadata_json=json.dumps(meta),
        )
        db_session.add(event)
        db_session.flush()
        loaded = json.loads(event.metadata_json)
        assert loaded["reason"] == "too_expensive"

    def test_billing_event_repr(self, db_session):
        event = BillingEvent(
            event_type=BillingEventType.SUBSCRIPTION_CREATED,
            tier="team",
        )
        db_session.add(event)
        db_session.flush()
        assert "SUBSCRIPTION_CREATED" in repr(event)

    def test_all_event_types_valid(self):
        """All 10 event types are accessible."""
        assert len(BillingEventType) == 10
        expected = {
            "trial_started",
            "trial_converted",
            "trial_expired",
            "subscription_created",
            "subscription_upgraded",
            "subscription_downgraded",
            "subscription_canceled",
            "subscription_churned",
            "payment_failed",
            "payment_recovered",
        }
        actual = {e.value for e in BillingEventType}
        assert actual == expected

    def test_billing_event_seat_count(self, db_session, make_user):
        user = make_user(email="seats_test@example.com")
        event = BillingEvent(
            user_id=user.id,
            event_type=BillingEventType.SUBSCRIPTION_CREATED,
            tier="team",
            interval="annual",
            seat_count=5,
        )
        db_session.add(event)
        db_session.flush()
        assert event.seat_count == 5


# ---------------------------------------------------------------------------
# record_billing_event()
# ---------------------------------------------------------------------------


class TestRecordBillingEvent:
    """Test the record_billing_event helper."""

    def test_records_event_and_returns(self, db_session, make_user):
        from billing.analytics import record_billing_event

        user = make_user(email="record_test@example.com")
        event = record_billing_event(
            db_session,
            BillingEventType.TRIAL_STARTED,
            user_id=user.id,
            tier="solo",
            interval="monthly",
        )
        assert event.id is not None
        assert event.event_type == BillingEventType.TRIAL_STARTED

    def test_records_event_with_metadata(self, db_session, make_user):
        from billing.analytics import record_billing_event

        user = make_user(email="meta_record@example.com")
        event = record_billing_event(
            db_session,
            BillingEventType.SUBSCRIPTION_CANCELED,
            user_id=user.id,
            tier="team",
            metadata={"reason": "switched_competitor"},
        )
        loaded = json.loads(event.metadata_json)
        assert loaded["reason"] == "switched_competitor"

    def test_increments_prometheus_counter(self, db_session, make_user):
        from billing.analytics import record_billing_event

        user = make_user(email="prom_test@example.com")
        with patch("shared.parser_metrics.billing_events_total") as mock_counter:
            mock_labels = mock_counter.labels.return_value
            record_billing_event(
                db_session,
                BillingEventType.SUBSCRIPTION_CREATED,
                user_id=user.id,
                tier="solo",
            )
            mock_counter.labels.assert_called_once_with(
                event_type="subscription_created",
                tier="solo",
            )
            mock_labels.inc.assert_called_once()


# ---------------------------------------------------------------------------
# Decision metric queries
# ---------------------------------------------------------------------------


class TestTrialStarts:
    """Test get_trial_starts query."""

    def test_counts_trial_starts_in_period(self, db_session, make_user):
        from billing.analytics import get_trial_starts

        user = make_user(email="trial_count@example.com")
        now = datetime.now(UTC)
        week_ago = now - timedelta(days=7)

        for i in range(3):
            db_session.add(
                BillingEvent(
                    user_id=user.id,
                    event_type=BillingEventType.TRIAL_STARTED,
                    tier="solo",
                    created_at=now - timedelta(days=i),
                )
            )
        # One outside range
        db_session.add(
            BillingEvent(
                user_id=user.id,
                event_type=BillingEventType.TRIAL_STARTED,
                tier="solo",
                created_at=now - timedelta(days=10),
            )
        )
        db_session.flush()

        count = get_trial_starts(db_session, week_ago, now + timedelta(hours=1))
        assert count == 3

    def test_returns_zero_when_no_events(self, db_session):
        from billing.analytics import get_trial_starts

        count = get_trial_starts(db_session, datetime.now(UTC) - timedelta(days=7))
        assert count == 0


class TestTrialToPaidRate:
    """Test get_trial_to_paid_rate query."""

    def test_calculates_conversion_rate(self, db_session, make_user):
        from billing.analytics import get_trial_to_paid_rate

        user = make_user(email="conv_rate@example.com")
        now = datetime.now(UTC)
        since = now - timedelta(days=30)

        # 4 starts, 2 conversions
        for i in range(4):
            db_session.add(
                BillingEvent(
                    user_id=user.id,
                    event_type=BillingEventType.TRIAL_STARTED,
                    tier="solo",
                    created_at=now - timedelta(days=i),
                )
            )
        for i in range(2):
            db_session.add(
                BillingEvent(
                    user_id=user.id,
                    event_type=BillingEventType.TRIAL_CONVERTED,
                    tier="solo",
                    created_at=now - timedelta(days=i),
                )
            )
        db_session.flush()

        result = get_trial_to_paid_rate(db_session, since)
        assert result["starts"] == 4
        assert result["conversions"] == 2
        assert result["rate"] == 0.5

    def test_zero_starts_returns_zero_rate(self, db_session):
        from billing.analytics import get_trial_to_paid_rate

        result = get_trial_to_paid_rate(db_session, datetime.now(UTC) - timedelta(days=1))
        assert result["rate"] == 0.0


class TestPaidByPlan:
    """Test get_paid_by_plan query."""

    def test_groups_active_subscriptions(self, db_session, make_user):
        from billing.analytics import get_paid_by_plan

        u1 = make_user(email="plan_solo@example.com")
        u2 = make_user(email="plan_team@example.com")
        u3 = make_user(email="plan_team2@example.com")

        db_session.add(
            Subscription(
                user_id=u1.id,
                tier="solo",
                status=SubscriptionStatus.ACTIVE,
                billing_interval=BillingInterval.MONTHLY,
            )
        )
        db_session.add(
            Subscription(
                user_id=u2.id,
                tier="team",
                status=SubscriptionStatus.ACTIVE,
                billing_interval=BillingInterval.MONTHLY,
            )
        )
        db_session.add(
            Subscription(
                user_id=u3.id,
                tier="team",
                status=SubscriptionStatus.CANCELED,
                billing_interval=BillingInterval.MONTHLY,
            )
        )
        db_session.flush()

        since = datetime.now(UTC) - timedelta(days=7)
        result = get_paid_by_plan(db_session, since)
        assert result.get("solo", 0) == 1
        assert result.get("team", 0) == 1  # canceled one not counted


class TestAvgSeatsByTier:
    """Test get_avg_seats_by_tier query."""

    def test_calculates_average_seats(self, db_session, make_user):
        from billing.analytics import get_avg_seats_by_tier

        u1 = make_user(email="seat_a@example.com")
        u2 = make_user(email="seat_b@example.com")

        db_session.add(
            Subscription(
                user_id=u1.id,
                tier="team",
                status=SubscriptionStatus.ACTIVE,
                billing_interval=BillingInterval.MONTHLY,
                seat_count=3,
                additional_seats=2,
            )
        )
        db_session.add(
            Subscription(
                user_id=u2.id,
                tier="team",
                status=SubscriptionStatus.ACTIVE,
                billing_interval=BillingInterval.ANNUAL,
                seat_count=3,
                additional_seats=4,
            )
        )
        db_session.flush()

        result = get_avg_seats_by_tier(db_session)
        # (3+2 + 3+4) / 2 = 6.0
        assert result["team"] == 6.0

    def test_excludes_solo_plans(self, db_session, make_user):
        from billing.analytics import get_avg_seats_by_tier

        u = make_user(email="solo_seat@example.com")
        db_session.add(
            Subscription(
                user_id=u.id,
                tier="solo",
                status=SubscriptionStatus.ACTIVE,
                billing_interval=BillingInterval.MONTHLY,
                seat_count=1,
                additional_seats=0,
            )
        )
        db_session.flush()

        result = get_avg_seats_by_tier(db_session)
        assert "solo" not in result


class TestCancellationsByReason:
    """Test get_cancellations_by_reason query."""

    def test_groups_by_reason(self, db_session, make_user):
        from billing.analytics import get_cancellations_by_reason

        user = make_user(email="cancel_reason@example.com")
        now = datetime.now(UTC)
        since = now - timedelta(days=7)

        db_session.add(
            BillingEvent(
                user_id=user.id,
                event_type=BillingEventType.SUBSCRIPTION_CANCELED,
                tier="solo",
                metadata_json=json.dumps({"reason": "too_expensive"}),
                created_at=now,
            )
        )
        db_session.add(
            BillingEvent(
                user_id=user.id,
                event_type=BillingEventType.SUBSCRIPTION_CANCELED,
                tier="solo",
                metadata_json=json.dumps({"reason": "too_expensive"}),
                created_at=now,
            )
        )
        db_session.add(
            BillingEvent(
                user_id=user.id,
                event_type=BillingEventType.SUBSCRIPTION_CANCELED,
                tier="team",
                metadata_json=json.dumps({"reason": "missing_feature"}),
                created_at=now,
            )
        )
        db_session.flush()

        result = get_cancellations_by_reason(db_session, since)
        assert result["too_expensive"] == 2
        assert result["missing_feature"] == 1

    def test_unspecified_reason(self, db_session, make_user):
        from billing.analytics import get_cancellations_by_reason

        user = make_user(email="no_reason@example.com")
        now = datetime.now(UTC)
        db_session.add(
            BillingEvent(
                user_id=user.id,
                event_type=BillingEventType.SUBSCRIPTION_CANCELED,
                tier="solo",
                metadata_json=None,
                created_at=now,
            )
        )
        db_session.flush()

        result = get_cancellations_by_reason(db_session, now - timedelta(days=1))
        assert result["unspecified"] == 1


# ---------------------------------------------------------------------------
# Weekly review aggregation
# ---------------------------------------------------------------------------


class TestWeeklyReview:
    """Test get_weekly_review aggregation."""

    def test_returns_structure(self, db_session):
        from billing.analytics import get_weekly_review

        review = get_weekly_review(db_session)
        assert "period" in review
        assert "metrics" in review
        assert "previous_period" in review
        assert "deltas" in review

    def test_period_boundaries_are_monday(self, db_session):
        from billing.analytics import get_weekly_review

        # Use a known Wednesday
        wednesday = datetime(2026, 2, 25, 12, 0, 0, tzinfo=UTC)
        review = get_weekly_review(db_session, week_of=wednesday)
        assert review["period"]["start"] == "2026-02-23"  # Monday
        assert review["period"]["end"] == "2026-03-02"  # Next Monday

    def test_metrics_contain_all_5_keys(self, db_session):
        from billing.analytics import get_weekly_review

        review = get_weekly_review(db_session)
        metrics = review["metrics"]
        assert "trial_starts" in metrics
        assert "trial_conversion" in metrics
        assert "paid_by_plan" in metrics
        assert "avg_seats" in metrics
        assert "cancellations_by_reason" in metrics

    def test_deltas_calculated(self, db_session, make_user):
        from billing.analytics import get_weekly_review

        user = make_user(email="delta_test@example.com")
        now = datetime.now(UTC)

        # 2 trials this week
        for _ in range(2):
            db_session.add(
                BillingEvent(
                    user_id=user.id,
                    event_type=BillingEventType.TRIAL_STARTED,
                    tier="solo",
                    created_at=now,
                )
            )
        # 1 trial last week
        db_session.add(
            BillingEvent(
                user_id=user.id,
                event_type=BillingEventType.TRIAL_STARTED,
                tier="solo",
                created_at=now - timedelta(days=7),
            )
        )
        db_session.flush()

        review = get_weekly_review(db_session, week_of=now)
        # Delta should be positive (more this week than last)
        assert review["deltas"]["trial_starts"] >= 0


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


class TestAnalyticsRouteRegistration:
    """Verify analytics endpoint is registered."""

    def test_weekly_review_route_exists(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/billing/analytics/weekly-review" in paths


# ---------------------------------------------------------------------------
# Webhook instrumentation (integration check)
# ---------------------------------------------------------------------------


class TestWebhookEventRecording:
    """Test that webhook handlers record BillingEvents."""

    def test_checkout_completed_records_trial_started(self, db_session, make_user):
        from billing.webhook_handler import handle_checkout_completed

        user = make_user(email="webhook_trial@example.com")

        mock_stripe_sub = {
            "id": "sub_test",
            "status": "trialing",
            "customer": "cus_test",
            "items": {"data": [{"price": {"id": "price_solo_monthly"}, "plan": {"interval": "month"}}]},
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
        }

        event_data = {
            "metadata": {"paciolus_user_id": str(user.id)},
            "subscription": "sub_test",
            "customer": "cus_test",
        }

        with patch("billing.stripe_client.get_stripe") as mock_stripe:
            mock_stripe.return_value.Subscription.retrieve.return_value = mock_stripe_sub
            with patch("billing.webhook_handler._resolve_tier_from_price", return_value="solo"):
                with patch("billing.webhook_handler.sync_subscription_from_stripe"):
                    handle_checkout_completed(db_session, event_data)

        events = (
            db_session.query(BillingEvent)
            .filter(
                BillingEvent.user_id == user.id,
                BillingEvent.event_type == BillingEventType.TRIAL_STARTED,
            )
            .all()
        )
        assert len(events) == 1
        assert events[0].tier == "solo"

    def test_checkout_completed_records_subscription_created(self, db_session, make_user):
        from billing.webhook_handler import handle_checkout_completed

        user = make_user(email="webhook_sub@example.com")

        mock_stripe_sub = {
            "id": "sub_test2",
            "status": "active",
            "customer": "cus_test2",
            "items": {"data": [{"price": {"id": "price_team_annual"}, "plan": {"interval": "year"}}]},
            "current_period_start": 1700000000,
            "current_period_end": 1731536000,
        }

        event_data = {
            "metadata": {"paciolus_user_id": str(user.id)},
            "subscription": "sub_test2",
            "customer": "cus_test2",
        }

        with patch("billing.stripe_client.get_stripe") as mock_stripe:
            mock_stripe.return_value.Subscription.retrieve.return_value = mock_stripe_sub
            with patch("billing.webhook_handler._resolve_tier_from_price", return_value="team"):
                with patch("billing.webhook_handler.sync_subscription_from_stripe"):
                    handle_checkout_completed(db_session, event_data)

        events = (
            db_session.query(BillingEvent)
            .filter(
                BillingEvent.user_id == user.id,
                BillingEvent.event_type == BillingEventType.SUBSCRIPTION_CREATED,
            )
            .all()
        )
        assert len(events) == 1
        assert events[0].tier == "team"
        assert events[0].interval == "annual"

    def test_subscription_deleted_records_churn(self, db_session, make_user):
        from billing.webhook_handler import handle_subscription_deleted

        user = make_user(email="webhook_churn@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_churn",
        )
        db_session.add(sub)
        db_session.flush()

        event_data = {"customer": "cus_churn"}
        handle_subscription_deleted(db_session, event_data)

        events = (
            db_session.query(BillingEvent)
            .filter(
                BillingEvent.user_id == user.id,
                BillingEvent.event_type == BillingEventType.SUBSCRIPTION_CHURNED,
            )
            .all()
        )
        assert len(events) == 1

    def test_payment_failed_records_event(self, db_session, make_user):
        from billing.webhook_handler import handle_invoice_payment_failed

        user = make_user(email="webhook_fail@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="team",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_fail",
        )
        db_session.add(sub)
        db_session.flush()

        handle_invoice_payment_failed(db_session, {"customer": "cus_fail"})

        events = (
            db_session.query(BillingEvent)
            .filter(
                BillingEvent.user_id == user.id,
                BillingEvent.event_type == BillingEventType.PAYMENT_FAILED,
            )
            .all()
        )
        assert len(events) == 1

    def test_payment_recovered_records_event(self, db_session, make_user):
        from billing.webhook_handler import handle_invoice_paid

        user = make_user(email="webhook_recover@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="team",
            status=SubscriptionStatus.PAST_DUE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_recover",
        )
        db_session.add(sub)
        db_session.flush()

        handle_invoice_paid(db_session, {"customer": "cus_recover"})

        events = (
            db_session.query(BillingEvent)
            .filter(
                BillingEvent.user_id == user.id,
                BillingEvent.event_type == BillingEventType.PAYMENT_RECOVERED,
            )
            .all()
        )
        assert len(events) == 1
