"""
Billing checkout routes — Stripe Checkout session creation, subscription
management (get/cancel/reactivate), seat changes (add/remove), billing portal
session, and usage stats. All endpoints require authentication. Extracted from
the monolithic billing.py during Refactor 4 (bounded-domain split).
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth import require_current_user, require_verified_user
from billing.guards import stripe_endpoint_guard
from database import get_db
from models import User
from schemas.billing_schemas import (  # noqa: F401 — backward compat re-exports
    BillingMessageResponse,
    CancelRequest,
    CheckoutRequest,
    CheckoutResponse,
    PortalResponse,
    SeatChangeRequest,
    SeatChangeResponse,
    SubscriptionResponse,
    UsageResponse,
    WeeklyReviewResponse,
)
from shared.rate_limits import RATE_LIMIT_WRITE, limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


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
