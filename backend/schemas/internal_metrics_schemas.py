"""
Pydantic response schemas for internal metrics endpoints.

Sprint 589: Founder Ops dashboard — MRR, ARR, churn, trial funnel.
All monetary values in USD as floats with 2-decimal precision.
"""

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Revenue Metrics
# ---------------------------------------------------------------------------


class PlanMRR(BaseModel):
    count: int = Field(description="Number of active subscriptions on this plan")
    mrr: float = Field(description="Monthly recurring revenue from this plan (USD)")


class MRRBreakdown(BaseModel):
    total: float = Field(description="Total MRR across all plans (USD)")
    by_plan: dict[str, PlanMRR] = Field(default_factory=dict, description="MRR breakdown by plan tier")
    net_new_mrr_30d: float = Field(description="MRR from new subscriptions in trailing 30 days")
    expansion_mrr_30d: float = Field(description="MRR gained from upgrades in trailing 30 days")
    contraction_mrr_30d: float = Field(description="MRR lost from downgrades in trailing 30 days (negative)")
    churned_mrr_30d: float = Field(description="MRR lost from cancellations in trailing 30 days (negative)")


class SubscriberCounts(BaseModel):
    total_active: int = Field(description="Total active (incl. trialing) paid subscribers")
    trialing: int = Field(description="Subscribers currently in trial period")
    past_due: int = Field(description="Subscribers with past-due payments")


class RevenueMetricsResponse(BaseModel):
    as_of: str = Field(description="Snapshot timestamp (ISO 8601 UTC)")
    mrr: MRRBreakdown
    arr: float = Field(description="Annual recurring revenue (MRR x 12)")
    subscribers: SubscriberCounts


# ---------------------------------------------------------------------------
# Churn Metrics
# ---------------------------------------------------------------------------


class LogoChurn(BaseModel):
    rate: float = Field(description="Logo churn rate (canceled / starting count)")
    count: int = Field(description="Number of canceled subscriptions in period")
    starting_count: int = Field(description="Active subscribers at start of period")


class RevenueChurn(BaseModel):
    gross_rate: float = Field(description="Gross revenue churn rate")
    net_rate: float = Field(description="Net revenue churn rate (gross - expansion)")
    churned_mrr: float = Field(description="MRR lost from cancellations (USD)")
    expansion_mrr: float = Field(description="MRR gained from upgrades (USD)")


class InvoluntaryChurn(BaseModel):
    past_due_count: int = Field(description="Subscriptions currently past due")
    past_due_mrr: float = Field(description="MRR at risk from past-due subscriptions")
    failed_payments_30d: int = Field(description="Failed payment events in trailing 30 days")


class DunningRecovery(BaseModel):
    count: int = Field(description="Number of episodes recovered/lost")
    mrr: float = Field(description="MRR recovered/lost (USD)")


class DunningMetrics(BaseModel):
    active_episodes: int = Field(description="Currently active dunning episodes")
    total_at_risk_mrr: float = Field(description="MRR at risk from active dunning")
    recovered_30d: DunningRecovery = Field(description="Recovered in trailing 30 days")
    lost_to_dunning_30d: DunningRecovery = Field(description="Lost to dunning in trailing 30 days")
    recovery_rate_30d: float = Field(description="Recovery rate (0.0-1.0)")


class ChurnMetricsResponse(BaseModel):
    period: str = Field(default="trailing_30d", description="Measurement period")
    logo_churn: LogoChurn
    revenue_churn: RevenueChurn
    involuntary_churn: InvoluntaryChurn
    dunning: DunningMetrics | None = Field(default=None, description="Dunning episode metrics")


# ---------------------------------------------------------------------------
# Trial Funnel
# ---------------------------------------------------------------------------


class TrialFunnelResponse(BaseModel):
    period: str = Field(default="trailing_30d", description="Measurement period")
    signups: int = Field(description="New user registrations in period")
    trials_started: int = Field(description="Trial subscriptions started in period")
    first_upload: int = Field(description="Unique users with first file upload in period")
    first_report_generated: int = Field(description="Unique users with first report in period")
    converted_to_paid: int = Field(description="Trials converted to paid in period")
    conversion_rate: float = Field(description="Trial-to-paid conversion rate (0.0-1.0)")
    median_time_to_conversion_days: float | None = Field(
        default=None, description="Median days from trial start to paid conversion"
    )


# ---------------------------------------------------------------------------
# Revenue History
# ---------------------------------------------------------------------------


class RevenueHistoryPoint(BaseModel):
    date: str = Field(description="Date of the snapshot (YYYY-MM-DD)")
    mrr: float = Field(description="MRR at this date (USD)")
    arr: float = Field(description="ARR at this date (USD)")
    active_subscribers: int = Field(description="Active paid subscribers at this date")
    trialing: int = Field(description="Trialing subscribers at this date")
