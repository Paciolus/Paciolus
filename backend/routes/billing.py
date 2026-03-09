"""
Billing routes — Sprints 365-366 + Phase LIX Sprint E-F + Self-Serve Checkout.

Stripe checkout, subscription management, billing portal, and webhook handler.
All checkout/management endpoints require authentication.
Webhook endpoint uses Stripe signature verification (no auth, CSRF-exempt).
Sprint E adds: seat management endpoints (add-seats, remove-seats), seat_count in checkout.
Sprint F adds: PRICING_V2_ENABLED feature flag gating seat/promo endpoints.
Self-Serve Checkout: Base Plan + Seat Add-On dual line items, seat validation.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from auth import require_current_user, require_verified_user
from database import get_db
from models import User
from shared.rate_limits import RATE_LIMIT_DEFAULT, RATE_LIMIT_WRITE, limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Shared Stripe endpoint guard (Sprint 519 Phase 1C)
# ---------------------------------------------------------------------------

from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def stripe_endpoint_guard(user_id: int, operation: str) -> Generator[None, None, None]:
    """Context manager that wraps the common Stripe endpoint pattern:

    1. Check is_stripe_enabled() → 503 if not
    2. Yield for the provider call
    3. Catch Exception → log + raise 502
    """
    from billing.stripe_client import is_stripe_enabled

    if not is_stripe_enabled():
        raise HTTPException(status_code=503, detail="Billing is not available.")

    try:
        yield
    except Exception as e:
        logger.error("Stripe %s failed for user %d: %s", operation, user_id, type(e).__name__)
        raise HTTPException(
            status_code=502,
            detail="Payment provider error. Please try again or contact support.",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/create-checkout-session",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(RATE_LIMIT_WRITE)
def create_checkout(
    request: Request,
    body: CheckoutRequest,
    user: Annotated[User, Depends(require_verified_user)],
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    """Create a Stripe Checkout Session for upgrading to a paid plan."""
    from billing.checkout_orchestrator import (
        CheckoutProviderError,
        CheckoutUnavailableError,
        CheckoutValidationError,
        orchestrate_checkout,
    )

    try:
        checkout_url = orchestrate_checkout(
            tier=body.tier,
            interval=body.interval,
            seat_count=body.seat_count,
            promo_code=body.promo_code,
            dpa_accepted=body.dpa_accepted,
            user_id=user.id,
            user_email=user.email,
            db=db,
        )
    except CheckoutUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except CheckoutValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CheckoutProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

    from shared.parser_metrics import pricing_v2_checkouts_total

    pricing_v2_checkouts_total.labels(tier=body.tier, interval=body.interval).inc()

    return CheckoutResponse(checkout_url=checkout_url)


@router.get("/subscription", response_model=SubscriptionResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def get_subscription_status(
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> SubscriptionResponse:
    """Get the current user's subscription details."""
    from billing.subscription_manager import get_subscription

    sub = get_subscription(db, user.id)
    if sub is None:
        return SubscriptionResponse(
            tier=user.tier.value if user.tier else "free",
            status="active",
        )

    return SubscriptionResponse(
        id=sub.id,
        tier=sub.tier,
        status=sub.status.value if sub.status else "active",
        billing_interval=sub.billing_interval.value if sub.billing_interval else None,
        current_period_start=sub.current_period_start.isoformat() if sub.current_period_start else None,
        current_period_end=sub.current_period_end.isoformat() if sub.current_period_end else None,
        cancel_at_period_end=sub.cancel_at_period_end,
        seat_count=sub.seat_count or 1,
        additional_seats=sub.additional_seats or 0,
        total_seats=sub.total_seats,
        dpa_accepted_at=sub.dpa_accepted_at.isoformat() if sub.dpa_accepted_at else None,
        dpa_version=sub.dpa_version,
    )


@router.post("/cancel", response_model=BillingMessageResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def cancel_subscription_endpoint(
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
    body: CancelRequest | None = None,
) -> BillingMessageResponse:
    """Cancel the current subscription at the end of the billing period."""
    from billing.subscription_manager import cancel_subscription, get_subscription

    # Capture tier before cancel for event recording
    sub = get_subscription(db, user.id)
    tier_at_cancel = sub.tier if sub else None

    with stripe_endpoint_guard(user.id, "cancellation"):
        result = cancel_subscription(db, user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="No active subscription found.")

    # Phase LX: Record cancellation event with optional reason
    from billing.analytics import record_billing_event
    from subscription_model import BillingEventType

    reason = body.reason if body else None
    metadata = {"reason": reason} if reason else None
    record_billing_event(
        db,
        BillingEventType.SUBSCRIPTION_CANCELED,
        user_id=user.id,
        tier=tier_at_cancel,
        metadata=metadata,
    )

    return BillingMessageResponse(
        message="Your subscription will be canceled at the end of the current billing period."
    )


@router.post("/reactivate", response_model=BillingMessageResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def reactivate_subscription_endpoint(
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> BillingMessageResponse:
    """Reactivate a subscription that was scheduled for cancellation."""
    from billing.subscription_manager import reactivate_subscription

    with stripe_endpoint_guard(user.id, "reactivation"):
        result = reactivate_subscription(db, user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="No subscription found to reactivate.")

    return BillingMessageResponse(message="Your subscription has been reactivated.")


@router.post(
    "/add-seats",
    response_model=SeatChangeResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(RATE_LIMIT_WRITE)
def add_seats_endpoint(
    request: Request,
    body: SeatChangeRequest,
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> SeatChangeResponse:
    """Add seats to the current subscription. Stripe prorates automatically."""
    from billing.subscription_manager import add_seats

    with stripe_endpoint_guard(user.id, "add-seats"):
        result = add_seats(db, user.id, body.seats)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to add seats. Check your subscription status or contact sales for 26+ seats.",
        )

    return SeatChangeResponse(
        message=f"Successfully added {body.seats} seat(s).",
        seat_count=result.seat_count or 1,
        additional_seats=result.additional_seats or 0,
        total_seats=result.total_seats,
    )


@router.post(
    "/remove-seats",
    response_model=SeatChangeResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(RATE_LIMIT_WRITE)
def remove_seats_endpoint(
    request: Request,
    body: SeatChangeRequest,
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> SeatChangeResponse:
    """Remove seats from the current subscription. Cannot go below base seats."""
    from billing.subscription_manager import remove_seats

    with stripe_endpoint_guard(user.id, "remove-seats"):
        result = remove_seats(db, user.id, body.seats)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to remove seats. Cannot go below the included seats for your plan.",
        )

    return SeatChangeResponse(
        message=f"Successfully removed {body.seats} seat(s).",
        seat_count=result.seat_count or 1,
        additional_seats=result.additional_seats or 0,
        total_seats=result.total_seats,
    )


@router.get("/portal-session", response_model=PortalResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def get_portal_session(
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> PortalResponse:
    """Get a Stripe Billing Portal URL for self-service management."""
    from billing.subscription_manager import create_portal_session, get_subscription

    sub = get_subscription(db, user.id)
    if sub is None or not sub.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No billing account found.")

    from config import FRONTEND_URL

    with stripe_endpoint_guard(user.id, "portal session"):
        portal_url = create_portal_session(sub.stripe_customer_id, f"{FRONTEND_URL}/settings/billing")

    return PortalResponse(portal_url=portal_url)


@router.get("/usage", response_model=UsageResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def get_usage(
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> UsageResponse:
    """Get current usage stats for entitlement display."""
    from billing.usage_service import get_usage_stats

    stats = get_usage_stats(db, user.id, user.tier.value if user.tier else "free")

    return UsageResponse(
        uploads_used=stats.uploads_used,
        uploads_limit=stats.uploads_limit,
        diagnostics_used=stats.uploads_used,  # Backward compat alias
        diagnostics_limit=stats.uploads_limit,  # Backward compat alias
        clients_used=stats.clients_used,
        clients_limit=stats.clients_limit,
        tier=stats.tier,
    )


# ---------------------------------------------------------------------------
# Analytics (Phase LX — post-launch control)
# ---------------------------------------------------------------------------


class WeeklyReviewResponse(BaseModel):
    """Weekly pricing review metrics for founder dashboard."""

    period: dict
    metrics: dict
    previous_period: dict
    deltas: dict


@router.get("/analytics/weekly-review", response_model=WeeklyReviewResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_weekly_review_endpoint(
    request: Request,
    user: Annotated[User, Depends(require_verified_user)],
    db: Session = Depends(get_db),
) -> WeeklyReviewResponse:
    """Weekly pricing review — 5 decision metrics with period-over-period deltas.

    Metrics: trial starts, trial→paid rate, paid by plan, avg seats, cancellations by reason.
    Security Sprint: Restricted to org owner/admin to prevent sensitive billing data leakage.
    """
    from organization_model import OrganizationMember, OrgRole

    # Security: Only org owner/admin can access billing analytics
    if user.organization_id:
        member = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == user.id,
                OrganizationMember.organization_id == user.organization_id,
            )
            .first()
        )
        if not member or member.role not in (OrgRole.OWNER, OrgRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or owner role required to access billing analytics.",
            )
    else:
        # Solo user — only allow if they have an active subscription (they're viewing their own data)
        from billing.subscription_manager import get_subscription

        sub = get_subscription(db, user.id)
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Active subscription required to access billing analytics.",
            )

    from billing.analytics import get_weekly_review

    review = get_weekly_review(db, user_id=user.id, org_id=user.organization_id)
    return WeeklyReviewResponse(**review)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    """Stripe webhook endpoint. No auth — uses Stripe signature verification.

    CSRF-exempt (added to CSRF_EXEMPT_PATHS in security_middleware.py).
    """
    from billing.stripe_client import is_stripe_enabled

    if not is_stripe_enabled():
        return Response(status_code=200)

    from config import STRIPE_WEBHOOK_SECRET

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    from billing.stripe_client import get_stripe

    stripe = get_stripe()

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Deduplicate: skip already-processed events (Stripe retries on timeout)
    event_id = event.get("id")
    if event_id:
        from subscription_model import ProcessedWebhookEvent

        existing = db.query(ProcessedWebhookEvent).filter(ProcessedWebhookEvent.stripe_event_id == event_id).first()
        if existing:
            logger.info("Duplicate webhook event %s — skipping", event_id)
            return Response(status_code=200)

    from billing.webhook_handler import process_webhook_event

    event_type = event.get("type", "")
    event_data = event.get("data", {}).get("object", {})

    process_webhook_event(db, event_type, event_data)

    # Record processed event for deduplication
    if event_id:
        from subscription_model import ProcessedWebhookEvent

        db.add(ProcessedWebhookEvent(stripe_event_id=event_id))
        db.commit()

    return Response(status_code=200)
