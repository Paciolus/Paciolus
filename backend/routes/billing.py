"""
Billing routes — Sprints 365-366.

Stripe checkout, subscription management, billing portal, and webhook handler.
All checkout/management endpoints require authentication.
Webhook endpoint uses Stripe signature verification (no auth, CSRF-exempt).
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
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
    """Request to create a Stripe Checkout Session."""
    tier: str = Field(..., pattern="^(starter|professional|team)$")
    interval: str = Field(..., pattern="^(monthly|annual)$")
    success_url: str = Field(..., min_length=1, max_length=500)
    cancel_url: str = Field(..., min_length=1, max_length=500)


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


class PortalResponse(BaseModel):
    """Stripe Billing Portal URL."""
    portal_url: str


class UsageResponse(BaseModel):
    """Current usage stats for the billing period."""
    diagnostics_used: int
    diagnostics_limit: int  # 0 = unlimited
    clients_used: int
    clients_limit: int  # 0 = unlimited
    tier: str


class BillingMessageResponse(BaseModel):
    """Simple message response."""
    message: str


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
    from billing.price_config import get_stripe_price_id
    from billing.stripe_client import is_stripe_enabled

    if not is_stripe_enabled():
        raise HTTPException(
            status_code=503,
            detail="Billing is not currently available. Please contact sales.",
        )

    price_id = get_stripe_price_id(body.tier, body.interval)
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail=f"No price configured for {body.tier}/{body.interval}. Please contact support.",
        )

    from billing.checkout import create_checkout_session, create_or_get_stripe_customer
    from billing.subscription_manager import get_subscription

    # Get or create Stripe customer
    existing_sub = get_subscription(db, user.id)
    stripe_customer_id = existing_sub.stripe_customer_id if existing_sub else None
    customer_id = create_or_get_stripe_customer(user.id, user.email, stripe_customer_id)

    # Save the customer ID if it's new
    if existing_sub and not existing_sub.stripe_customer_id:
        existing_sub.stripe_customer_id = customer_id
        db.commit()

    checkout_url = create_checkout_session(
        customer_id=customer_id,
        price_id=price_id,
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        user_id=user.id,
    )

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
    )


@router.post("/cancel", response_model=BillingMessageResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def cancel_subscription_endpoint(
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> BillingMessageResponse:
    """Cancel the current subscription at the end of the billing period."""
    from billing.stripe_client import is_stripe_enabled
    from billing.subscription_manager import cancel_subscription

    if not is_stripe_enabled():
        raise HTTPException(status_code=503, detail="Billing is not available.")

    result = cancel_subscription(db, user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="No active subscription found.")

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
    from billing.stripe_client import is_stripe_enabled
    from billing.subscription_manager import reactivate_subscription

    if not is_stripe_enabled():
        raise HTTPException(status_code=503, detail="Billing is not available.")

    result = reactivate_subscription(db, user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="No subscription found to reactivate.")

    return BillingMessageResponse(message="Your subscription has been reactivated.")


@router.get("/portal-session", response_model=PortalResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def get_portal_session(
    request: Request,
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> PortalResponse:
    """Get a Stripe Billing Portal URL for self-service management."""
    from billing.stripe_client import is_stripe_enabled
    from billing.subscription_manager import create_portal_session, get_subscription

    if not is_stripe_enabled():
        raise HTTPException(status_code=503, detail="Billing is not available.")

    sub = get_subscription(db, user.id)
    if sub is None or not sub.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No billing account found.")

    from config import FRONTEND_URL
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
    from datetime import UTC, datetime

    from sqlalchemy import func

    from models import ActivityLog, Client, UserTier
    from shared.entitlements import get_entitlements

    entitlements = get_entitlements(UserTier(user.tier.value))

    # Count diagnostics this month
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    diagnostics_used = (
        db.query(func.count(ActivityLog.id))
        .filter(
            ActivityLog.user_id == user.id,
            ActivityLog.timestamp >= month_start,
            ActivityLog.archived_at.is_(None),
        )
        .scalar()
    ) or 0

    # Count clients
    clients_used = (
        db.query(func.count(Client.id))
        .filter(Client.user_id == user.id)
        .scalar()
    ) or 0

    return UsageResponse(
        diagnostics_used=diagnostics_used,
        diagnostics_limit=entitlements.diagnostics_per_month,
        clients_used=clients_used,
        clients_limit=entitlements.max_clients,
        tier=user.tier.value if user.tier else "free",
    )


@router.post("/webhook", status_code=status.HTTP_200_OK)
@limiter.limit(RATE_LIMIT_DEFAULT)
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
            payload, sig_header, STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    from billing.webhook_handler import process_webhook_event

    event_type = event.get("type", "")
    event_data = event.get("data", {}).get("object", {})

    process_webhook_event(db, event_type, event_data)

    return Response(status_code=200)
