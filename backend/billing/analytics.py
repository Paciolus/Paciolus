"""
Billing analytics engine — Phase LX post-launch control.

Provides:
- record_billing_event(): Append-only event recording + Prometheus counter
- 5 decision metric queries for founder weekly review:
    1. trial_starts (count)
    2. trial_to_paid_rate (trial_converted / trial_started)
    3. paid_by_plan (subscriptions grouped by tier)
    4. avg_seats_by_tier (average seat count for Team)
    5. cancellations_by_reason (grouped by metadata.reason)
- Weekly review summary aggregation

Dashboard query templates are documented as SQL comments in each function
for direct use with Prometheus/Grafana or ad-hoc DB queries.
"""

import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from subscription_model import (
    BillingEvent,
    BillingEventType,
    Subscription,
    SubscriptionStatus,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event recording
# ---------------------------------------------------------------------------


def record_billing_event(
    db: Session,
    event_type: BillingEventType,
    *,
    user_id: int | None = None,
    tier: str | None = None,
    interval: str | None = None,
    seat_count: int | None = None,
    metadata: dict | None = None,
) -> BillingEvent:
    """Record a billing lifecycle event to the append-only log.

    Also increments the Prometheus counter for real-time dashboards.

    SQL equivalent (for ad-hoc verification):
        INSERT INTO billing_events (user_id, event_type, tier, interval, seat_count, metadata_json)
        VALUES (:user_id, :event_type, :tier, :interval, :seat_count, :metadata_json);
    """
    event = BillingEvent(
        user_id=user_id,
        event_type=event_type,
        tier=tier,
        interval=interval,
        seat_count=seat_count,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(event)
    db.commit()

    # Prometheus counter
    from shared.parser_metrics import billing_events_total

    billing_events_total.labels(
        event_type=event_type.value,
        tier=tier or "unknown",
    ).inc()

    logger.info(
        "billing_event: type=%s tier=%s user=%s",
        event_type.value,
        tier,
        user_id,
    )
    return event


# ---------------------------------------------------------------------------
# Decision metric queries
# ---------------------------------------------------------------------------


def get_trial_starts(db: Session, since: datetime, until: datetime | None = None) -> int:
    """Count trial starts in a period.

    Dashboard SQL:
        SELECT COUNT(*) FROM billing_events
        WHERE event_type = 'trial_started'
          AND created_at >= :since AND created_at < :until;
    """
    q = db.query(func.count(BillingEvent.id)).filter(
        BillingEvent.event_type == BillingEventType.TRIAL_STARTED,
        BillingEvent.created_at >= since,
    )
    if until:
        q = q.filter(BillingEvent.created_at < until)
    return q.scalar() or 0


def get_trial_to_paid_rate(db: Session, since: datetime, until: datetime | None = None) -> dict:
    """Trial-to-paid conversion rate.

    Returns {starts, conversions, rate} where rate is 0.0–1.0.

    Dashboard SQL:
        SELECT
            SUM(CASE WHEN event_type = 'trial_started' THEN 1 ELSE 0 END) AS starts,
            SUM(CASE WHEN event_type = 'trial_converted' THEN 1 ELSE 0 END) AS conversions
        FROM billing_events
        WHERE event_type IN ('trial_started', 'trial_converted')
          AND created_at >= :since AND created_at < :until;
    """
    base = db.query(
        func.sum(case((BillingEvent.event_type == BillingEventType.TRIAL_STARTED, 1), else_=0)).label("starts"),
        func.sum(case((BillingEvent.event_type == BillingEventType.TRIAL_CONVERTED, 1), else_=0)).label("conversions"),
    ).filter(
        BillingEvent.event_type.in_([BillingEventType.TRIAL_STARTED, BillingEventType.TRIAL_CONVERTED]),
        BillingEvent.created_at >= since,
    )
    if until:
        base = base.filter(BillingEvent.created_at < until)

    row = base.one()
    starts = row.starts or 0
    conversions = row.conversions or 0
    rate = conversions / starts if starts > 0 else 0.0
    return {"starts": starts, "conversions": conversions, "rate": round(rate, 4)}


def get_paid_by_plan(db: Session, since: datetime, until: datetime | None = None) -> dict[str, int]:
    """Active paid subscriptions by plan (point-in-time from Subscription table).

    Also includes new subscriptions created in the period from the event log.

    Dashboard SQL (point-in-time from subscriptions table):
        SELECT tier, COUNT(*) FROM subscriptions
        WHERE status IN ('active', 'trialing')
        GROUP BY tier;

    Dashboard SQL (new in period from events):
        SELECT tier, COUNT(*) FROM billing_events
        WHERE event_type IN ('subscription_created', 'trial_converted')
          AND created_at >= :since AND created_at < :until
        GROUP BY tier;
    """
    # Point-in-time active subscribers
    rows = (
        db.query(Subscription.tier, func.count(Subscription.id))
        .filter(Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]))
        .group_by(Subscription.tier)
        .all()
    )
    return {tier: count for tier, count in rows}


def get_avg_seats_by_tier(db: Session) -> dict[str, float]:
    """Average total seats for Team plans.

    Dashboard SQL:
        SELECT tier, AVG(seat_count + additional_seats) AS avg_seats
        FROM subscriptions
        WHERE status IN ('active', 'trialing')
          AND tier IN ('team')
        GROUP BY tier;
    """
    rows = (
        db.query(
            Subscription.tier,
            func.avg(Subscription.seat_count + Subscription.additional_seats).label("avg_seats"),
        )
        .filter(
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
            Subscription.tier.in_(["team"]),
        )
        .group_by(Subscription.tier)
        .all()
    )
    return {tier: round(float(avg or 0), 1) for tier, avg in rows}


def get_cancellations_by_reason(db: Session, since: datetime, until: datetime | None = None) -> dict[str, int]:
    """Cancellations grouped by reason from metadata_json.

    Dashboard SQL:
        SELECT
            JSON_EXTRACT(metadata_json, '$.reason') AS reason,
            COUNT(*) AS count
        FROM billing_events
        WHERE event_type = 'subscription_canceled'
          AND created_at >= :since AND created_at < :until
        GROUP BY reason
        ORDER BY count DESC;
    """
    q = db.query(BillingEvent).filter(
        BillingEvent.event_type == BillingEventType.SUBSCRIPTION_CANCELED,
        BillingEvent.created_at >= since,
    )
    if until:
        q = q.filter(BillingEvent.created_at < until)

    reasons: dict[str, int] = {}
    for event in q.all():
        reason = "unspecified"
        if event.metadata_json:
            try:
                meta = json.loads(event.metadata_json)
                reason = meta.get("reason", "unspecified")
            except (json.JSONDecodeError, TypeError):
                pass
        reasons[reason] = reasons.get(reason, 0) + 1
    return reasons


# ---------------------------------------------------------------------------
# Weekly review aggregation
# ---------------------------------------------------------------------------


def get_weekly_review(db: Session, week_of: datetime | None = None) -> dict:
    """Aggregate all 5 decision metrics for a given week.

    Returns current week metrics + previous week metrics + deltas.

    Args:
        week_of: Any datetime in the target week. Defaults to now (current week).

    Response format:
        {
            "period": {"start": "2026-02-23", "end": "2026-03-01"},
            "metrics": {
                "trial_starts": 12,
                "trial_conversion": {"starts": 12, "conversions": 8, "rate": 0.6667},
                "paid_by_plan": {"solo": 5, "team": 3},
                "avg_seats": {"team": 3.5},
                "cancellations_by_reason": {"too_expensive": 2, "missing_feature": 1}
            },
            "previous_period": { ... same shape ... },
            "deltas": {
                "trial_starts": +3,
                "trial_conversion_rate": +0.05,
                "total_paid": +2,
                "total_cancellations": -1
            }
        }
    """
    if week_of is None:
        week_of = datetime.now(UTC)

    # Week boundaries (Monday 00:00 → next Monday 00:00)
    week_start = (week_of - timedelta(days=week_of.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    prev_start = week_start - timedelta(days=7)

    current = _build_period_metrics(db, week_start, week_end)
    previous = _build_period_metrics(db, prev_start, week_start)

    # Deltas
    deltas = {
        "trial_starts": current["trial_starts"] - previous["trial_starts"],
        "trial_conversion_rate": round(current["trial_conversion"]["rate"] - previous["trial_conversion"]["rate"], 4),
        "total_paid": sum(current["paid_by_plan"].values()) - sum(previous["paid_by_plan"].values()),
        "total_cancellations": (
            sum(current["cancellations_by_reason"].values()) - sum(previous["cancellations_by_reason"].values())
        ),
    }

    return {
        "period": {
            "start": week_start.strftime("%Y-%m-%d"),
            "end": week_end.strftime("%Y-%m-%d"),
        },
        "metrics": current,
        "previous_period": {
            "start": prev_start.strftime("%Y-%m-%d"),
            "end": week_start.strftime("%Y-%m-%d"),
            "metrics": previous,
        },
        "deltas": deltas,
    }


def _build_period_metrics(db: Session, since: datetime, until: datetime) -> dict:
    """Build all 5 decision metrics for a time period."""
    return {
        "trial_starts": get_trial_starts(db, since, until),
        "trial_conversion": get_trial_to_paid_rate(db, since, until),
        "paid_by_plan": get_paid_by_plan(db, since, until),
        "avg_seats": get_avg_seats_by_tier(db),
        "cancellations_by_reason": get_cancellations_by_reason(db, since, until),
    }
