"""Purchase admission — at most one subscription per account (Sprint 881, AZ-09).

Checkout used to open a new ``mode: subscription`` session whatever the account
already had, so an active subscriber who checked out again was billed twice
while the app tracked one subscription. Admission now runs before any session is
opened:

1. **Serialize.** The user's row is locked (``SELECT ... FOR UPDATE``) for the
   whole decision, so two checkouts for one account run one after the other.
2. **Refuse a second subscription.** A non-terminal local subscription, or a
   non-terminal subscription in Stripe for any of the account's customers (the
   webhook may not have arrived yet), refuses the checkout. Plan and interval
   changes go through ``checkout_orchestrator.change_plan`` instead.
3. **Close earlier checkouts.** Every session still payable for the account's
   customers is expired before a new one opens. If Stripe says one has already
   completed, the purchase is in flight and the new checkout is refused.
4. **Record the attempt.** A ``checkout_attempts`` row is committed *before*
   Stripe is called (so a crash still leaves the customer to search next time),
   then updated with the session ID. The attempt ID is the session's
   ``client_reference_id`` and idempotency key.

ZERO-STORAGE: Stripe references and plan names only.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from billing import stripe_client
from billing.stripe_client import to_plain_dict
from models import User
from subscription_model import (
    TERMINAL_SUBSCRIPTION_STATUSES,
    CheckoutAttempt,
    CheckoutAttemptStatus,
    PromoRedemption,
    Subscription,
)

logger = logging.getLogger(__name__)

# Stripe's minimum Checkout Session lifetime. An abandoned session stops being
# payable after this, which bounds how long an untracked one could matter.
CHECKOUT_SESSION_LIFETIME = timedelta(minutes=30)

# An ``opening`` attempt younger than this may still be creating its Stripe
# session, which a second checkout could neither see nor expire. Older than this,
# its request is gone (Stripe calls time out well inside it) and the attempt is
# closed, any session it created being found through its customer.
OPENING_GRACE = timedelta(minutes=3)

_LIVE_ATTEMPT_STATUSES = (CheckoutAttemptStatus.OPENING.value, CheckoutAttemptStatus.OPEN.value)
_TERMINAL_STRIPE_STATUSES = frozenset(s.value for s in TERMINAL_SUBSCRIPTION_STATUSES)


class AlreadySubscribedError(Exception):
    """The account already has a subscription Stripe may still bill (→ 409)."""


class PurchaseInProgressError(Exception):
    """An earlier checkout for the account has already been paid (→ 409)."""


class CheckoutBeingOpenedError(Exception):
    """Another checkout for the account is still creating its Stripe session (→ 409)."""


def _naive_utc(dt: datetime) -> datetime:
    return dt.astimezone(UTC).replace(tzinfo=None) if dt.tzinfo else dt


def refuse_if_checkout_being_opened(db: Session, user_id: int) -> None:
    """Raise ``CheckoutBeingOpenedError`` while a recent ``opening`` attempt exists."""
    cutoff = _naive_utc(datetime.now(UTC) - OPENING_GRACE)
    opening = (
        db.query(CheckoutAttempt.id, CheckoutAttempt.created_at)
        .filter(CheckoutAttempt.user_id == user_id, CheckoutAttempt.status == CheckoutAttemptStatus.OPENING.value)
        .all()
    )
    for attempt_id, created_at in opening:
        if created_at is not None and _naive_utc(created_at) > cutoff:
            raise CheckoutBeingOpenedError(attempt_id)


def lock_purchaser(db: Session, user_id: int) -> User:
    """Lock the purchaser's user row for the rest of the transaction.

    A no-op on SQLite (tests); on PostgreSQL concurrent admissions for one
    account queue here until the first commits.
    """
    return db.query(User).filter(User.id == user_id).with_for_update().populate_existing().one()


def is_live(sub: Subscription | None) -> bool:
    """True when ``sub`` exists and Stripe may still bill it."""
    return sub is not None and sub.status not in TERMINAL_SUBSCRIPTION_STATUSES


def known_customer_ids(db: Session, user_id: int, sub: Subscription | None) -> list[str]:
    """Every Stripe customer this account has used, newest first, without duplicates."""
    ids: list[str] = []
    if sub is not None and sub.stripe_customer_id:
        ids.append(sub.stripe_customer_id)
    rows = (
        db.query(CheckoutAttempt.stripe_customer_id)
        .filter(CheckoutAttempt.user_id == user_id, CheckoutAttempt.stripe_customer_id.isnot(None))
        .order_by(CheckoutAttempt.id.desc())
        .all()
    )
    for (cid,) in rows:
        if cid and cid not in ids:
            ids.append(cid)
    return ids


def refuse_if_subscribed(sub: Subscription | None, customer_ids: list[str]) -> None:
    """Raise ``AlreadySubscribedError`` if a subscription exists locally or in Stripe."""
    if is_live(sub):
        raise AlreadySubscribedError("live local subscription")
    if not customer_ids:
        return
    stripe = stripe_client.get_stripe()
    for cid in customer_ids:
        listing = to_plain_dict(stripe.Subscription.list(customer=cid, status="all", limit=100))
        for stripe_sub in listing.get("data", []):
            if stripe_sub.get("status") not in _TERMINAL_STRIPE_STATUSES:
                raise AlreadySubscribedError(f"live Stripe subscription {stripe_sub.get('id')} on {cid}")


def close_open_checkouts(db: Session, user_id: int, customer_ids: list[str]) -> None:
    """Expire every session still payable for the account; refuse if one already completed."""
    stripe = stripe_client.get_stripe()
    expired: set[str] = set()
    for cid in customer_ids:
        listing = to_plain_dict(stripe.checkout.Session.list(customer=cid, status="open", limit=100))
        for session in listing.get("data", []):
            session_id = session.get("id")
            if not session_id:
                continue
            try:
                stripe.checkout.Session.expire(session_id)
            except Exception:
                # Paid between the list and the expire, or already expired.
                current = to_plain_dict(stripe.checkout.Session.retrieve(session_id))
                if current.get("status") == "complete":
                    raise PurchaseInProgressError(session_id)
                if current.get("status") != "expired":
                    raise
            expired.add(session_id)

    now = datetime.now(UTC)
    for attempt in (
        db.query(CheckoutAttempt)
        .filter(CheckoutAttempt.user_id == user_id, CheckoutAttempt.status.in_(_LIVE_ATTEMPT_STATUSES))
        .all()
    ):
        attempt.status = (
            CheckoutAttemptStatus.EXPIRED.value
            if attempt.stripe_checkout_session_id
            else CheckoutAttemptStatus.FAILED.value
        )
        attempt.updated_at = now
    if expired:
        logger.info("Expired %d earlier checkout session(s) for user %d", len(expired), user_id)


def begin_attempt(
    db: Session, user_id: int, tier: str, interval: str, customer_id: str, trial_offered: bool, promo_code: str | None
) -> CheckoutAttempt:
    """Commit an ``opening`` attempt row (this releases the purchaser lock)."""
    attempt = CheckoutAttempt(
        user_id=user_id,
        status=CheckoutAttemptStatus.OPENING.value,
        tier=tier,
        billing_interval=interval,
        stripe_customer_id=customer_id,
        trial_offered=trial_offered,
        promo_code=promo_code,
        expires_at=datetime.now(UTC) + CHECKOUT_SESSION_LIFETIME,
    )
    db.add(attempt)
    db.commit()
    return attempt


def session_expiry_epoch(attempt: CheckoutAttempt) -> int:
    expires = attempt.expires_at or (datetime.now(UTC) + CHECKOUT_SESSION_LIFETIME)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    return int(expires.timestamp())


def mark_attempt_completed(db: Session, event_data: dict) -> CheckoutAttempt | None:
    """On ``checkout.session.completed``, mark the session's attempt completed."""
    session_id = event_data.get("id")
    attempt = None
    if session_id:
        attempt = db.query(CheckoutAttempt).filter(CheckoutAttempt.stripe_checkout_session_id == session_id).first()
    if attempt is None:
        ref = event_data.get("client_reference_id") or (event_data.get("metadata") or {}).get(
            "paciolus_checkout_attempt_id"
        )
        if ref and str(ref).isdigit():
            attempt = db.query(CheckoutAttempt).filter(CheckoutAttempt.id == int(ref)).first()
    if attempt is None:
        return None
    attempt.status = CheckoutAttemptStatus.COMPLETED.value
    if session_id and not attempt.stripe_checkout_session_id:
        attempt.stripe_checkout_session_id = session_id
    attempt.stripe_subscription_id = event_data.get("subscription")
    return attempt


def promo_already_redeemed(db: Session, user_id: int, promo_code: str) -> bool:
    """True when Stripe has confirmed ``promo_code`` on one of this account's subscriptions (AZ-16)."""
    return (
        db.query(PromoRedemption.id)
        .filter(PromoRedemption.user_id == user_id, PromoRedemption.promo_code == promo_code.upper())
        .first()
        is not None
    )
