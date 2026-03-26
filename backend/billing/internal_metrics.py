"""
Internal metrics engine — Founder Ops dashboard data layer.

Sprint 589: Read-only aggregation of MRR, ARR, churn, and trial conversion
KPIs from existing Subscription + BillingEvent tables.

All functions are pure computation — no side effects, no caching.
Monetary values returned as floats with 2-decimal precision (USD).
"""

import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from billing.price_config import (
    ENTERPRISE_SEAT_PRICE,
    PRICE_TABLE,
    PROFESSIONAL_SEAT_PRICE,
)
from subscription_model import (
    BillingEvent,
    BillingEventType,
    Subscription,
    SubscriptionStatus,
)

logger = logging.getLogger(__name__)

# Statuses that count as "active" for MRR purposes
_ACTIVE_STATUSES = (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)

# Statuses that indicate involuntary churn risk
_PAST_DUE_STATUSES = (SubscriptionStatus.PAST_DUE,)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _subscription_monthly_revenue(sub: Subscription) -> float:
    """Calculate the monthly revenue contribution of a single subscription.

    For monthly plans: base price + seat add-on price
    For annual plans: (base price + seat add-on price) / 12
    """
    tier = sub.tier or "free"
    interval = sub.billing_interval.value if sub.billing_interval else "monthly"

    # Base plan price in cents
    base_cents = PRICE_TABLE.get(tier, {}).get(interval, 0)

    # Seat add-on revenue
    additional_seats = sub.additional_seats or 0
    seat_cents = 0
    if additional_seats > 0:
        if tier == "professional":
            seat_cents = additional_seats * PROFESSIONAL_SEAT_PRICE.get(interval, 0)
        elif tier == "enterprise":
            seat_cents = additional_seats * ENTERPRISE_SEAT_PRICE.get(interval, 0)

    total_cents = base_cents + seat_cents

    if interval == "annual":
        # Normalize annual price to monthly
        monthly_cents = total_cents / 12.0
    else:
        monthly_cents = float(total_cents)

    return round(monthly_cents / 100.0, 2)


def _tier_monthly_price_cents(tier: str, interval: str) -> int:
    """Get the base monthly price in cents for a tier (normalizing annual)."""
    price = PRICE_TABLE.get(tier, {}).get(interval, 0)
    if interval == "annual":
        return round(price / 12)
    return price


# ---------------------------------------------------------------------------
# Revenue Metrics
# ---------------------------------------------------------------------------


def compute_revenue_metrics(db: Session) -> dict:
    """Compute MRR, ARR, and subscriber counts.

    Returns the full revenue metrics payload with MRR breakdown by plan
    and trailing 30-day movement (net new, expansion, contraction, churned).
    """
    now = datetime.now(UTC)
    thirty_days_ago = now - timedelta(days=30)

    # --- Active subscriptions for current MRR ---
    active_subs = (
        db.query(Subscription).filter(Subscription.status.in_(_ACTIVE_STATUSES), Subscription.tier != "free").all()
    )

    # MRR by plan
    by_plan: dict[str, dict] = {}
    total_mrr = 0.0

    for sub in active_subs:
        tier = sub.tier or "free"
        mrr = _subscription_monthly_revenue(sub)
        total_mrr += mrr

        if tier not in by_plan:
            by_plan[tier] = {"count": 0, "mrr": 0.0}
        by_plan[tier]["count"] += 1
        by_plan[tier]["mrr"] = round(by_plan[tier]["mrr"] + mrr, 2)

    total_mrr = round(total_mrr, 2)
    arr = round(total_mrr * 12, 2)

    # --- Subscriber counts ---
    total_active = len(active_subs)

    trialing_count = (
        db.query(func.count(Subscription.id)).filter(Subscription.status == SubscriptionStatus.TRIALING).scalar() or 0
    )

    past_due_count = (
        db.query(func.count(Subscription.id)).filter(Subscription.status == SubscriptionStatus.PAST_DUE).scalar() or 0
    )

    # --- 30-day MRR movements from billing events ---
    net_new_mrr = _compute_net_new_mrr(db, thirty_days_ago, now)
    expansion_mrr = _compute_expansion_mrr(db, thirty_days_ago, now)
    contraction_mrr = _compute_contraction_mrr(db, thirty_days_ago, now)
    churned_mrr = _compute_churned_mrr(db, thirty_days_ago, now)

    return {
        "as_of": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mrr": {
            "total": total_mrr,
            "by_plan": by_plan,
            "net_new_mrr_30d": net_new_mrr,
            "expansion_mrr_30d": expansion_mrr,
            "contraction_mrr_30d": contraction_mrr,
            "churned_mrr_30d": churned_mrr,
        },
        "arr": arr,
        "subscribers": {
            "total_active": total_active,
            "trialing": trialing_count,
            "past_due": past_due_count,
        },
    }


def _compute_net_new_mrr(db: Session, since: datetime, until: datetime) -> float:
    """MRR from new subscriptions created in the period."""
    events = (
        db.query(BillingEvent)
        .filter(
            BillingEvent.event_type.in_([BillingEventType.SUBSCRIPTION_CREATED, BillingEventType.TRIAL_CONVERTED]),
            BillingEvent.created_at >= since,
            BillingEvent.created_at < until,
        )
        .all()
    )
    total = 0.0
    for ev in events:
        tier = ev.tier or "solo"
        interval = ev.interval or "monthly"
        price_cents = _tier_monthly_price_cents(tier, interval)
        total += price_cents / 100.0
    return round(total, 2)


def _compute_expansion_mrr(db: Session, since: datetime, until: datetime) -> float:
    """MRR from upgrades in the period."""
    events = (
        db.query(BillingEvent)
        .filter(
            BillingEvent.event_type == BillingEventType.SUBSCRIPTION_UPGRADED,
            BillingEvent.created_at >= since,
            BillingEvent.created_at < until,
        )
        .all()
    )
    total = 0.0
    for ev in events:
        # Metadata may contain old_tier/new_tier for precise delta calculation
        meta = _parse_metadata(ev.metadata_json)
        old_tier = meta.get("old_tier", "solo")
        new_tier = ev.tier or "professional"
        interval = ev.interval or "monthly"
        old_price = _tier_monthly_price_cents(old_tier, interval)
        new_price = _tier_monthly_price_cents(new_tier, interval)
        delta = max(0, new_price - old_price)
        total += delta / 100.0
    return round(total, 2)


def _compute_contraction_mrr(db: Session, since: datetime, until: datetime) -> float:
    """MRR lost from downgrades in the period (returned as negative)."""
    events = (
        db.query(BillingEvent)
        .filter(
            BillingEvent.event_type == BillingEventType.SUBSCRIPTION_DOWNGRADED,
            BillingEvent.created_at >= since,
            BillingEvent.created_at < until,
        )
        .all()
    )
    total = 0.0
    for ev in events:
        meta = _parse_metadata(ev.metadata_json)
        old_tier = meta.get("old_tier", "professional")
        new_tier = ev.tier or "solo"
        interval = ev.interval or "monthly"
        old_price = _tier_monthly_price_cents(old_tier, interval)
        new_price = _tier_monthly_price_cents(new_tier, interval)
        delta = min(0, new_price - old_price)
        total += delta / 100.0
    return round(total, 2)


def _compute_churned_mrr(db: Session, since: datetime, until: datetime) -> float:
    """MRR lost from cancellations in the period (returned as negative)."""
    events = (
        db.query(BillingEvent)
        .filter(
            BillingEvent.event_type.in_(
                [BillingEventType.SUBSCRIPTION_CANCELED, BillingEventType.SUBSCRIPTION_CHURNED]
            ),
            BillingEvent.created_at >= since,
            BillingEvent.created_at < until,
        )
        .all()
    )
    total = 0.0
    for ev in events:
        tier = ev.tier or "solo"
        interval = ev.interval or "monthly"
        price_cents = _tier_monthly_price_cents(tier, interval)
        total -= price_cents / 100.0
    return round(total, 2)


def _parse_metadata(metadata_json: str | None) -> dict:
    """Safely parse metadata JSON string."""
    if not metadata_json:
        return {}
    try:
        return json.loads(metadata_json)
    except (json.JSONDecodeError, TypeError):
        return {}


# ---------------------------------------------------------------------------
# Churn Metrics
# ---------------------------------------------------------------------------


def compute_churn_metrics(db: Session) -> dict:
    """Compute logo churn, revenue churn, and involuntary churn metrics.

    All rates are for the trailing 30-day period.
    """
    now = datetime.now(UTC)
    thirty_days_ago = now - timedelta(days=30)

    # --- Logo churn ---
    # Starting count: active at period start ≈ current active + canceled in period
    canceled_count = (
        db.query(func.count(BillingEvent.id))
        .filter(
            BillingEvent.event_type.in_(
                [BillingEventType.SUBSCRIPTION_CANCELED, BillingEventType.SUBSCRIPTION_CHURNED]
            ),
            BillingEvent.created_at >= thirty_days_ago,
            BillingEvent.created_at < now,
        )
        .scalar()
        or 0
    )

    current_active = (
        db.query(func.count(Subscription.id))
        .filter(Subscription.status.in_(_ACTIVE_STATUSES), Subscription.tier != "free")
        .scalar()
        or 0
    )

    starting_count = current_active + canceled_count
    logo_churn_rate = round(canceled_count / starting_count, 4) if starting_count > 0 else 0.0

    # --- Revenue churn ---
    churned_mrr = abs(_compute_churned_mrr(db, thirty_days_ago, now))
    expansion_mrr = _compute_expansion_mrr(db, thirty_days_ago, now)

    # Starting MRR ≈ current MRR + churned - expansion (approximation)
    current_mrr = _compute_current_total_mrr(db)
    starting_mrr = current_mrr + churned_mrr - expansion_mrr

    gross_revenue_churn = round(churned_mrr / starting_mrr, 4) if starting_mrr > 0 else 0.0
    net_revenue_churn = round((churned_mrr - expansion_mrr) / starting_mrr, 4) if starting_mrr > 0 else 0.0

    # --- Involuntary churn ---
    past_due_subs = (
        db.query(Subscription)
        .filter(Subscription.status == SubscriptionStatus.PAST_DUE, Subscription.tier != "free")
        .all()
    )
    past_due_count = len(past_due_subs)
    past_due_mrr = round(sum(_subscription_monthly_revenue(s) for s in past_due_subs), 2)

    failed_payments = (
        db.query(func.count(BillingEvent.id))
        .filter(
            BillingEvent.event_type == BillingEventType.PAYMENT_FAILED,
            BillingEvent.created_at >= thirty_days_ago,
            BillingEvent.created_at < now,
        )
        .scalar()
        or 0
    )

    # --- Dunning metrics (Sprint 591) ---
    dunning_metrics = _compute_dunning_metrics(db, thirty_days_ago, now)

    return {
        "period": "trailing_30d",
        "logo_churn": {
            "rate": logo_churn_rate,
            "count": canceled_count,
            "starting_count": starting_count,
        },
        "revenue_churn": {
            "gross_rate": gross_revenue_churn,
            "net_rate": net_revenue_churn,
            "churned_mrr": churned_mrr,
            "expansion_mrr": expansion_mrr,
        },
        "involuntary_churn": {
            "past_due_count": past_due_count,
            "past_due_mrr": past_due_mrr,
            "failed_payments_30d": failed_payments,
        },
        "dunning": dunning_metrics,
    }


def _compute_dunning_metrics(db: Session, since: datetime, until: datetime) -> dict:
    """Compute dunning-specific metrics for the churn response."""
    from dunning_model import DunningEpisode, DunningResolution, DunningState

    # Active episodes (not resolved/canceled)
    active_episodes = (
        db.query(DunningEpisode)
        .filter(DunningEpisode.state.notin_([DunningState.CANCELED, DunningState.RESOLVED]))
        .all()
    )
    active_count = len(active_episodes)

    # At-risk MRR: sum MRR of subscriptions with active dunning
    at_risk_mrr = 0.0
    for ep in active_episodes:
        sub = db.query(Subscription).filter(Subscription.id == ep.subscription_id).first()
        if sub:
            at_risk_mrr += _subscription_monthly_revenue(sub)
    at_risk_mrr = round(at_risk_mrr, 2)

    # Recovered in 30d
    recovered = (
        db.query(DunningEpisode)
        .filter(
            DunningEpisode.resolution == DunningResolution.PAID,
            DunningEpisode.resolved_at >= since,
            DunningEpisode.resolved_at < until,
        )
        .all()
    )
    recovered_count = len(recovered)
    recovered_mrr = 0.0
    for ep in recovered:
        sub = db.query(Subscription).filter(Subscription.id == ep.subscription_id).first()
        if sub:
            recovered_mrr += _subscription_monthly_revenue(sub)
    recovered_mrr = round(recovered_mrr, 2)

    # Lost to dunning in 30d
    lost = (
        db.query(DunningEpisode)
        .filter(
            DunningEpisode.resolution == DunningResolution.CANCELED,
            DunningEpisode.resolved_at >= since,
            DunningEpisode.resolved_at < until,
        )
        .all()
    )
    lost_count = len(lost)
    lost_mrr = 0.0
    for ep in lost:
        sub = db.query(Subscription).filter(Subscription.id == ep.subscription_id).first()
        if sub:
            lost_mrr += _subscription_monthly_revenue(sub)
    lost_mrr = round(lost_mrr, 2)

    # Recovery rate
    total_resolved = recovered_count + lost_count
    recovery_rate = round(recovered_count / total_resolved, 4) if total_resolved > 0 else 0.0

    return {
        "active_episodes": active_count,
        "total_at_risk_mrr": at_risk_mrr,
        "recovered_30d": {"count": recovered_count, "mrr": recovered_mrr},
        "lost_to_dunning_30d": {"count": lost_count, "mrr": lost_mrr},
        "recovery_rate_30d": recovery_rate,
    }


def _compute_current_total_mrr(db: Session) -> float:
    """Sum MRR across all active paid subscriptions."""
    active_subs = (
        db.query(Subscription).filter(Subscription.status.in_(_ACTIVE_STATUSES), Subscription.tier != "free").all()
    )
    return round(sum(_subscription_monthly_revenue(s) for s in active_subs), 2)


# ---------------------------------------------------------------------------
# Trial Funnel
# ---------------------------------------------------------------------------


def compute_trial_funnel(db: Session) -> dict:
    """Compute trial funnel metrics for the trailing 30-day period.

    Tracks: signups, trials started, first upload, first report,
    conversion to paid, conversion rate, and median time to conversion.
    """
    now = datetime.now(UTC)
    thirty_days_ago = now - timedelta(days=30)

    # Signups: count users created in period
    from models import User

    signups = (
        db.query(func.count(User.id)).filter(User.created_at >= thirty_days_ago, User.created_at < now).scalar() or 0
    )

    # Trials started
    trials_started = (
        db.query(func.count(BillingEvent.id))
        .filter(
            BillingEvent.event_type == BillingEventType.TRIAL_STARTED,
            BillingEvent.created_at >= thirty_days_ago,
            BillingEvent.created_at < now,
        )
        .scalar()
        or 0
    )

    # First upload: users who have at least one activity log entry in the period
    from models import ActivityLog

    first_upload = (
        db.query(func.count(func.distinct(ActivityLog.user_id)))
        .filter(
            ActivityLog.timestamp >= thirty_days_ago,
            ActivityLog.timestamp < now,
        )
        .scalar()
        or 0
    )

    # First report generated: users with diagnostic summaries in the period
    from models import DiagnosticSummary

    first_report = (
        db.query(func.count(func.distinct(DiagnosticSummary.user_id)))
        .filter(
            DiagnosticSummary.timestamp >= thirty_days_ago,
            DiagnosticSummary.timestamp < now,
        )
        .scalar()
        or 0
    )

    # Converted to paid
    converted = (
        db.query(func.count(BillingEvent.id))
        .filter(
            BillingEvent.event_type == BillingEventType.TRIAL_CONVERTED,
            BillingEvent.created_at >= thirty_days_ago,
            BillingEvent.created_at < now,
        )
        .scalar()
        or 0
    )

    conversion_rate = round(converted / trials_started, 4) if trials_started > 0 else 0.0

    # Median time to conversion
    median_days = _compute_median_conversion_time(db, thirty_days_ago, now)

    return {
        "period": "trailing_30d",
        "signups": signups,
        "trials_started": trials_started,
        "first_upload": first_upload,
        "first_report_generated": first_report,
        "converted_to_paid": converted,
        "conversion_rate": conversion_rate,
        "median_time_to_conversion_days": median_days,
    }


def _compute_median_conversion_time(db: Session, since: datetime, until: datetime) -> float | None:
    """Compute median days between trial_started and trial_converted for users in the period.

    Returns None if no conversions in the period.
    """
    # Get user_ids that converted in the period
    converted_events = (
        db.query(BillingEvent.user_id, BillingEvent.created_at)
        .filter(
            BillingEvent.event_type == BillingEventType.TRIAL_CONVERTED,
            BillingEvent.created_at >= since,
            BillingEvent.created_at < until,
            BillingEvent.user_id.isnot(None),
        )
        .all()
    )

    if not converted_events:
        return None

    conversion_days: list[float] = []
    for user_id, converted_at in converted_events:
        # Find the corresponding trial_started event
        trial_event = (
            db.query(BillingEvent.created_at)
            .filter(
                BillingEvent.event_type == BillingEventType.TRIAL_STARTED,
                BillingEvent.user_id == user_id,
                BillingEvent.created_at < converted_at,
            )
            .order_by(BillingEvent.created_at.desc())
            .first()
        )
        if trial_event:
            delta = (converted_at - trial_event[0]).total_seconds() / 86400.0
            conversion_days.append(delta)

    if not conversion_days:
        return None

    conversion_days.sort()
    n = len(conversion_days)
    if n % 2 == 1:
        median = conversion_days[n // 2]
    else:
        median = (conversion_days[n // 2 - 1] + conversion_days[n // 2]) / 2.0

    return round(median, 1)


# ---------------------------------------------------------------------------
# Revenue History
# ---------------------------------------------------------------------------


def compute_revenue_history(
    db: Session,
    granularity: str = "monthly",
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict]:
    """Compute historical revenue snapshots for time series charting.

    Retrospectively computes MRR at each point in time by replaying
    subscription creation/cancellation events.

    Args:
        granularity: 'daily', 'weekly', or 'monthly'
        start_date: Start of the range (defaults to 90 days ago)
        end_date: End of the range (defaults to now)

    Returns:
        List of {date, mrr, arr, active_subscribers, trialing} dicts.
    """
    now = datetime.now(UTC)
    if end_date is None:
        end_date = now
    if start_date is None:
        start_date = now - timedelta(days=90)

    # Generate date points based on granularity
    points = _generate_date_points(start_date, end_date, granularity)

    results = []
    for point_date in points:
        snapshot = _compute_snapshot_at(db, point_date)
        results.append(snapshot)

    return results


def _generate_date_points(start: datetime, end: datetime, granularity: str) -> list[datetime]:
    """Generate a list of datetime points for the given range and granularity."""
    points: list[datetime] = []
    current = start.replace(hour=0, minute=0, second=0, microsecond=0)

    if granularity == "daily":
        step = timedelta(days=1)
    elif granularity == "weekly":
        step = timedelta(weeks=1)
    else:  # monthly
        step = timedelta(days=30)  # Approximate — good enough for charting

    while current <= end:
        points.append(current)
        current = current + step

    # Always include the end date if not already there
    if points and points[-1] < end:
        points.append(end.replace(hour=0, minute=0, second=0, microsecond=0))

    return points


def _compute_snapshot_at(db: Session, point_date: datetime) -> dict:
    """Compute a revenue snapshot as of a specific date.

    Uses subscription created_at/updated_at and status to reconstruct
    point-in-time state. This is an approximation — subscriptions that
    existed at point_date are those created before it and not yet canceled
    (or canceled after it).
    """
    # Subscriptions that were active at the point in time:
    # Created before the point AND (still active OR canceled after the point)
    active_subs = (
        db.query(Subscription)
        .filter(
            Subscription.created_at <= point_date,
            Subscription.tier != "free",
        )
        .all()
    )

    # Filter: exclude subs that were canceled before point_date
    # We check billing events for cancellation timestamps
    cancel_events = (
        db.query(BillingEvent.user_id, func.min(BillingEvent.created_at).label("canceled_at"))
        .filter(
            BillingEvent.event_type.in_(
                [BillingEventType.SUBSCRIPTION_CANCELED, BillingEventType.SUBSCRIPTION_CHURNED]
            ),
        )
        .group_by(BillingEvent.user_id)
        .all()
    )
    canceled_before: set[int] = set()
    for user_id, canceled_at in cancel_events:
        if canceled_at and canceled_at <= point_date:
            # Check if reactivated after cancellation
            reactivated = (
                db.query(func.count(BillingEvent.id))
                .filter(
                    BillingEvent.user_id == user_id,
                    BillingEvent.event_type.in_(
                        [BillingEventType.SUBSCRIPTION_CREATED, BillingEventType.TRIAL_CONVERTED]
                    ),
                    BillingEvent.created_at > canceled_at,
                    BillingEvent.created_at <= point_date,
                )
                .scalar()
                or 0
            )
            if reactivated == 0:
                canceled_before.add(user_id)

    mrr = 0.0
    active_count = 0
    trialing_count = 0

    for sub in active_subs:
        if sub.user_id in canceled_before:
            continue

        sub_mrr = _subscription_monthly_revenue(sub)
        mrr += sub_mrr
        active_count += 1

        if sub.status == SubscriptionStatus.TRIALING:
            trialing_count += 1

    mrr = round(mrr, 2)

    return {
        "date": point_date.strftime("%Y-%m-%d"),
        "mrr": mrr,
        "arr": round(mrr * 12, 2),
        "active_subscribers": active_count,
        "trialing": trialing_count,
    }
