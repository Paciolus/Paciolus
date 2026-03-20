"""
Billing webhook routes — Stripe webhook endpoint for processing subscription
lifecycle events. Uses Stripe signature verification instead of auth; CSRF-exempt
(registered in CSRF_EXEMPT_PATHS). Extracted from the monolithic billing.py
during Refactor 4 (bounded-domain split).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from database import get_db
from shared.rate_limits import RATE_LIMIT_WEBHOOK, limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/webhook", status_code=status.HTTP_200_OK)
@limiter.limit(RATE_LIMIT_WEBHOOK)
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
        logger.warning(
            "Webhook signature verification failed (sig prefix: %s)", sig_header[:20] if sig_header else "none"
        )
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Atomic deduplication: insert the event marker BEFORE processing.
    # Uses INSERT ... ON CONFLICT DO NOTHING (upsert) — only the winner proceeds.
    # This prevents duplicate side effects under concurrent delivery (Stripe retries).
    from sqlalchemy.exc import IntegrityError

    event_id = event.get("id")
    if event_id:
        from subscription_model import ProcessedWebhookEvent

        # Attempt to claim this event atomically
        try:
            db.add(ProcessedWebhookEvent(stripe_event_id=event_id))
            db.flush()  # Will raise IntegrityError if already exists
        except IntegrityError:
            db.rollback()
            logger.debug("Duplicate webhook event %s — skipping", event_id)
            return Response(status_code=200)
        except Exception:
            # Operational DB error (connection failure, schema error, etc.)
            # Must NOT return 200 — Stripe needs to retry.
            db.rollback()
            logger.error("DB error during webhook dedup for event %s", event_id, exc_info=True)
            return Response(status_code=500)

    from billing.webhook_handler import process_webhook_event

    event_type = event.get("type", "")
    event_data = event.get("data", {}).get("object", {})

    # Store the Stripe event created timestamp for ordering guard
    event_created = event.get("created")  # Unix timestamp from Stripe

    # All handler logic uses db.flush() internally — single commit at the end
    # ensures atomicity between the dedup marker and business logic changes.
    try:
        process_webhook_event(db, event_type, event_data, event_created=event_created)
        # Commit the dedup marker + any business logic changes together
        db.commit()
    except (ValueError, KeyError) as exc:
        # Data errors: malformed event payload or unknown enum value.
        # Return 400 so Stripe does NOT retry (retrying won't fix bad data).
        db.rollback()
        logger.warning("Webhook data error for event %s (%s): %s", event_id, event_type, str(exc))
        return Response(status_code=400)
    except Exception:
        # Operational errors: DB failure, network issue, etc.
        # Return 500 so Stripe retries with exponential backoff.
        db.rollback()
        logger.error("Webhook processing failed for event %s (%s)", event_id, event_type, exc_info=True)
        return Response(status_code=500)

    return Response(status_code=200)
