"""
Billing Schemas — extracted from routes/billing.py (Sprint 544).
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CheckoutRequest(BaseModel):
    """Request to create a Stripe Checkout Session.

    Redirect URLs (success_url, cancel_url) are intentionally excluded — they are
    derived server-side from FRONTEND_URL to prevent open-redirect injection.
    Extra fields are silently ignored; a Prometheus counter fires if URL fields
    are detected in the request body.
    """

    model_config = ConfigDict(extra="ignore")

    tier: str = Field(..., pattern="^(solo|professional|enterprise)$")
    interval: str = Field(..., pattern="^(monthly|annual)$")
    promo_code: str | None = Field(None, max_length=50)
    seat_count: int = Field(0, ge=0, le=60)
    dpa_accepted: bool = Field(False)

    @model_validator(mode="before")
    @classmethod
    def detect_redirect_injection(cls, data: Any) -> Any:
        """Increment Prometheus counter if client supplies redirect URL fields."""
        if isinstance(data, dict):
            from shared.parser_metrics import billing_redirect_injection_attempt_total

            for field in ("success_url", "cancel_url"):
                if field in data:
                    billing_redirect_injection_attempt_total.labels(field=field).inc()
        return data


class CheckoutResponse(BaseModel):
    """Response with Stripe Checkout Session URL."""

    checkout_url: str


class SubscriptionResponse(BaseModel):
    """Current subscription details."""

    id: int | None = None
    tier: str
    status: str
    billing_interval: str | None = None
    current_period_start: str | None = None
    current_period_end: str | None = None
    cancel_at_period_end: bool = False
    seat_count: int = 1
    additional_seats: int = 0
    total_seats: int = 1
    dpa_accepted_at: str | None = None
    dpa_version: str | None = None


class PortalResponse(BaseModel):
    """Stripe Billing Portal URL."""

    portal_url: str


class UsageResponse(BaseModel):
    """Current usage stats for the billing period."""

    uploads_used: int
    uploads_limit: int  # 0 = unlimited
    diagnostics_used: int  # Backward compat alias
    diagnostics_limit: int  # Backward compat alias
    clients_used: int
    clients_limit: int  # 0 = unlimited
    tier: str


class SeatChangeRequest(BaseModel):
    """Request to add or remove seats."""

    seats: int = Field(..., ge=1, le=22)


class SeatChangeResponse(BaseModel):
    """Response after seat change with updated counts."""

    message: str
    seat_count: int
    additional_seats: int
    total_seats: int


class CancelRequest(BaseModel):
    """Optional cancellation reason for analytics (Phase LX)."""

    reason: str | None = Field(None, max_length=200)


class BillingMessageResponse(BaseModel):
    """Simple message response."""

    message: str


class WeeklyReviewResponse(BaseModel):
    """Weekly pricing review metrics for founder dashboard."""

    period: dict
    metrics: dict
    previous_period: dict
    deltas: dict
