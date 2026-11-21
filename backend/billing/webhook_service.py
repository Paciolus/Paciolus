"""Stripe webhook processing as one synchronous unit — Sprint 890 (CEO brief 15E step 1, review ST-03).

The route used to await the body and then, on the event loop, verify the signature, claim the event
in the database, run the handler (which may call ``stripe.Subscription.retrieve``) and commit. All
of that is blocking. The route now reads the body and calls ``handle_stripe_webhook`` through the
thread pool; this function owns its session and its transaction from start to finish.

Kept exactly as before: signature checks (400), the atomic de-duplication marker inserted before
processing (a duplicate returns 200 without side effects), one commit for the marker and the
business changes together, and the status mapping — bad data 400, operational errors 500 so Stripe
retries. (This also covers the webhook half of brief 17B.)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.exc import IntegrityError

from database import SessionScope

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebhookOutcome:
    status_code: int
    detail: Optional[str] = None  # set for the 4xx answers that carry a message


def handle_stripe_webhook(payload: bytes, sig_header: Optional[str], session_scope: SessionScope) -> WebhookOutcome:
    from billing.stripe_client import get_stripe, to_plain_dict
    from config import STRIPE_WEBHOOK_SECRET

    if not sig_header:
        logger.warning("Webhook rejected: missing stripe-signature header")
        return WebhookOutcome(400, "Missing stripe-signature header")

    stripe = get_stripe()
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        logger.warning("Webhook rejected: invalid JSON payload")
        return WebhookOutcome(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.warning("Webhook signature verification failed (sig prefix: %s)", sig_header[:20])
        return WebhookOutcome(400, "Invalid signature")

    # stripe-python >= 15: an Event is not a dict, and the handlers read it with .get() (Sprint 786b).
    event = to_plain_dict(event)
    event_id = event.get("id")
    event_type = event.get("type", "")
    event_data = event.get("data", {}).get("object", {})
    event_created = event.get("created")  # Stripe's Unix timestamp, for the ordering guard

    from billing.webhook_handler import process_webhook_event
    from subscription_model import ProcessedWebhookEvent

    with session_scope() as db:
        if event_id:
            # Atomic de-duplication: claim the event before processing; only the winner proceeds.
            try:
                db.add(ProcessedWebhookEvent(stripe_event_id=event_id))
                db.flush()
            except IntegrityError:
                db.rollback()
                logger.debug("Duplicate webhook event %s — skipping", event_id)
                return WebhookOutcome(200)
            except Exception:
                db.rollback()
                logger.error("DB error during webhook dedup for event %s", event_id, exc_info=True)
                return WebhookOutcome(500)

        # Handlers only flush: one commit makes the marker and the business changes atomic.
        try:
            process_webhook_event(db, event_type, event_data, event_created=event_created)
            db.commit()
        except (ValueError, KeyError) as exc:
            db.rollback()
            logger.warning(
                "Webhook data error for event %s (%s): %s: %s", event_id, event_type, type(exc).__name__, str(exc)
            )
            return WebhookOutcome(400)
        except Exception:
            db.rollback()
            logger.error("Webhook processing failed for event %s (%s)", event_id, event_type, exc_info=True)
            return WebhookOutcome(500)
    return WebhookOutcome(200)
