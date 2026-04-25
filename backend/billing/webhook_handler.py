"""
Stripe webhook event handler — Sprint 366 + Phase LIX Sprint C + Self-Serve Checkout.
Phase LX: BillingEvent recording for post-launch analytics.

Processes Stripe webhook events to keep local subscription state in sync.
Signature verification ensures events come from Stripe.
Sprint C adds: customer.subscription.trial_will_end handler.
Self-Serve Checkout: multi-item subscription handling, seat add-on filtering.
Phase LX: Each handler records a BillingEvent for decision metrics.
"""

import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from billing.subscription_manager import get_subscription, sync_subscription_from_stripe
from models import User, UserTier
from subscription_model import BillingEventType, Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)


def _auto_create_organization(db: Session, user_id: int, tier: str) -> None:
    """Auto-create an organization for Professional/Enterprise checkout.

    No-op if the user already belongs to an organization.
    Phase LXIX — Pricing v3.
    """
    import re
    import secrets

    from organization_model import Organization, OrganizationMember, OrgRole
    from subscription_model import Subscription, SubscriptionStatus

    # Check if user already has an org membership — if so, just ensure linkage
    existing = db.query(OrganizationMember).filter(OrganizationMember.user_id == user_id).first()
    if existing:
        # Ensure the existing org has subscription linkage
        existing_org = db.query(Organization).filter(Organization.id == existing.organization_id).first()
        if existing_org and existing_org.subscription_id is None:
            sub = (
                db.query(Subscription)
                .filter(
                    Subscription.user_id == user_id,
                    Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
                )
                .first()
            )
            if sub:
                existing_org.subscription_id = sub.id
                db.flush()
                logger.info("Linked subscription %d to existing org %d for user %d", sub.id, existing_org.id, user_id)
        return

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return

    # Generate org name from user's name or email
    base_name = user.name or user.email.split("@")[0]
    org_name = f"{base_name}'s Organization"

    # Create slug
    slug = re.sub(r"[^a-z0-9]+", "-", base_name.lower().strip()).strip("-")[:90]
    if db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{slug}-{secrets.token_hex(3)}"

    # Find the subscription
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
        )
        .first()
    )

    org = Organization(
        name=org_name,
        slug=slug,
        owner_user_id=user_id,
        subscription_id=sub.id if sub else None,
    )
    db.add(org)
    db.flush()

    # Create owner membership
    membership = OrganizationMember(
        organization_id=org.id,
        user_id=user_id,
        role=OrgRole.OWNER,
    )
    db.add(membership)

    # Link user to org
    user.organization_id = org.id

    db.flush()
    logger.info(
        "Auto-created organization '%s' (id=%d) for user %d on %s checkout",
        org.name,
        org.id,
        user_id,
        tier,
    )


def _apply_dpa_from_metadata(db: Session, user_id: int, metadata: dict) -> None:
    """Stamp dpa_accepted_at + dpa_version on the subscription from Stripe session metadata.

    Called after sync_subscription_from_stripe() in handle_checkout_completed().
    Only stamps if the metadata carries DPA fields and the subscription doesn't already
    have a recorded acceptance (preserves any acceptance recorded before checkout).
    Sprint 459 — PI1.3 / C2.1.
    """
    from datetime import UTC, datetime

    from billing.subscription_manager import get_subscription

    dpa_accepted_at_str = metadata.get("dpa_accepted_at")
    dpa_version = metadata.get("dpa_version")

    if not dpa_accepted_at_str or not dpa_version:
        return

    sub = get_subscription(db, user_id)
    if sub is None:
        return

    # Don't overwrite a later acceptance (e.g., if the user re-checked during an upgrade)
    if sub.dpa_accepted_at is None:
        try:
            parsed = datetime.fromisoformat(dpa_accepted_at_str)
            # Correct normalization: convert offset-aware to UTC, assume naive is UTC
            if parsed.tzinfo is not None:
                sub.dpa_accepted_at = parsed.astimezone(UTC)
            else:
                sub.dpa_accepted_at = parsed.replace(tzinfo=UTC)
        except ValueError:
            sub.dpa_accepted_at = datetime.now(UTC)
        sub.dpa_version = dpa_version
        db.flush()
        logger.info("DPA v%s acceptance stamped on subscription for user %d via webhook", dpa_version, user_id)


def _resolve_user_id(db: Session, event_data: dict) -> int | None:
    """Extract Paciolus user_id from webhook event metadata or customer lookup."""
    # Try metadata first
    metadata = event_data.get("metadata") or {}
    raw_user_id = metadata.get("paciolus_user_id")
    if raw_user_id is not None:
        try:
            return int(raw_user_id)
        except (ValueError, TypeError):
            logger.warning(
                "Invalid paciolus_user_id in webhook metadata: %r",
                raw_user_id,
            )
            # Fall through to customer ID lookup

    # Try customer ID lookup
    customer_id = event_data.get("customer")
    if customer_id:
        sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
        if sub:
            return sub.user_id

    return None


def _resolve_tier_from_price(price_id: str) -> str | None:
    """Map a Stripe Price ID to a Paciolus tier.

    Returns None if the price ID is unrecognized or is a seat add-on price.
    Callers must handle None (log + skip sync) — never silently default.
    """
    from billing.price_config import _load_stripe_price_ids, get_all_seat_price_ids

    # Skip seat add-on prices — they don't map to a tier
    if price_id in get_all_seat_price_ids():
        return None

    for tier, intervals in _load_stripe_price_ids().items():
        if price_id in intervals.values():
            return tier

    logger.warning("Unrecognized Stripe Price ID: %s — cannot resolve tier", price_id)
    return None


def _find_base_plan_item(items: list[dict]) -> dict | None:
    """Find the base plan line item (not a seat add-on) from subscription items.

    Returns the first item whose price ID is NOT a seat add-on.
    Falls back to the first item if all items are unrecognized (backward compat).
    """
    from billing.price_config import get_all_seat_price_ids

    seat_ids = get_all_seat_price_ids()
    for item in items:
        price_id = item.get("price", {}).get("id", "")
        if price_id not in seat_ids:
            return item
    return items[0] if items else None


def handle_checkout_completed(db: Session, event_data: dict) -> None:
    """Handle checkout.session.completed — new subscription created."""
    user_id = _resolve_user_id(db, event_data)
    if user_id is None:
        logger.warning("checkout.session.completed: could not resolve user_id")
        return

    subscription_id = event_data.get("subscription")
    customer_id = event_data.get("customer")

    if not subscription_id or not customer_id:
        logger.warning("checkout.session.completed: missing subscription or customer ID")
        return

    # Fetch the full subscription from Stripe
    from billing.stripe_client import get_stripe

    stripe = get_stripe()
    stripe_sub = stripe.Subscription.retrieve(subscription_id)

    # Resolve tier from the base plan item (skip seat add-ons)
    items = stripe_sub.get("items", {}).get("data", [])
    base_item = _find_base_plan_item(items)
    tier: str | None = None
    if base_item:
        price_id = base_item.get("price", {}).get("id", "")
        tier = _resolve_tier_from_price(price_id)

    if tier is None:
        logger.error(
            "checkout.session.completed: could not resolve tier for user %d (subscription %s)",
            user_id,
            subscription_id,
        )
        return

    sync_subscription_from_stripe(db, user_id, stripe_sub, customer_id, tier)
    logger.info("checkout.session.completed: synced user %d to tier %s", user_id, tier)

    # Backfill org subscription linkage: if user already has an org but it has no
    # subscription_id, link it now (handles "org-first, purchase-afterward" lifecycle).
    from organization_model import Organization, OrganizationMember

    existing_membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user_id).first()
    if existing_membership:
        existing_org = db.query(Organization).filter(Organization.id == existing_membership.organization_id).first()
        if existing_org and existing_org.subscription_id is None:
            local_sub = get_subscription(db, user_id)
            if local_sub:
                existing_org.subscription_id = local_sub.id
                db.flush()
                logger.info(
                    "Backfilled subscription_id=%d on org %d for user %d",
                    local_sub.id,
                    existing_org.id,
                    user_id,
                )

    # Phase LXIX: Auto-create organization for Professional/Enterprise tiers
    if tier in ("professional", "enterprise"):
        _auto_create_organization(db, user_id, tier)

    # Sprint 459: Stamp DPA acceptance if carried in session metadata
    _apply_dpa_from_metadata(db, user_id, event_data.get("metadata", {}))

    # Phase LX: Record billing event
    from billing.analytics import record_billing_event

    stripe_status = stripe_sub.get("status", "")
    interval = stripe_sub.get("items", {}).get("data", [{}])[0].get("plan", {}).get("interval", "")
    interval_mapped = "annual" if interval == "year" else "monthly"

    if stripe_status == "trialing":
        record_billing_event(
            db,
            BillingEventType.TRIAL_STARTED,
            user_id=user_id,
            tier=tier,
            interval=interval_mapped,
        )
    else:
        record_billing_event(
            db,
            BillingEventType.SUBSCRIPTION_CREATED,
            user_id=user_id,
            tier=tier,
            interval=interval_mapped,
        )


def handle_subscription_updated(db: Session, event_data: dict) -> None:
    """Handle customer.subscription.updated — plan change, renewal, etc.

    Guards against re-activating a cancelled subscription from stale events.
    """
    user_id = _resolve_user_id(db, event_data)
    if user_id is None:
        logger.warning("customer.subscription.updated: could not resolve user_id")
        return

    # Guard: if local subscription is already CANCELED, reject re-activation
    existing_sub = get_subscription(db, user_id)
    new_status = event_data.get("status", "")
    if existing_sub and existing_sub.status == SubscriptionStatus.CANCELED and new_status == "active":
        logger.warning(
            "customer.subscription.updated: ignoring active status for user %d — subscription already canceled",
            user_id,
        )
        return

    customer_id = event_data.get("customer")

    # Resolve tier from the base plan item (skip seat add-ons)
    items = event_data.get("items", {}).get("data", [])
    base_item = _find_base_plan_item(items)
    tier: str | None = None
    if base_item:
        price_id = base_item.get("price", {}).get("id", "")
        tier = _resolve_tier_from_price(price_id)

    if tier is None:
        logger.error(
            "customer.subscription.updated: could not resolve tier for user %d",
            user_id,
        )
        return

    # Phase LX: Detect trial→paid conversion or tier change before sync
    from billing.analytics import record_billing_event

    old_status = existing_sub.status if existing_sub else None
    old_tier = existing_sub.tier if existing_sub else None

    sync_subscription_from_stripe(db, user_id, event_data, customer_id or "", tier)
    logger.info("customer.subscription.updated: synced user %d to tier %s", user_id, tier)

    # If subscription transitions to any non-entitled state, downgrade (AUDIT-08-F2)
    if new_status in ("canceled", "unpaid", "past_due", "incomplete", "incomplete_expired", "paused"):
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.tier = UserTier.FREE
        _downgrade_org_members_to_free(db, user_id)
        db.flush()
        logger.info(
            "customer.subscription.updated: user %d and org members downgraded (status=%s)", user_id, new_status
        )

    # Trial → paid conversion
    if old_status == SubscriptionStatus.TRIALING and new_status == "active":
        record_billing_event(
            db,
            BillingEventType.TRIAL_CONVERTED,
            user_id=user_id,
            tier=tier,
        )
    # Tier upgrade/downgrade (only if both old and new tier are known)
    elif old_tier and old_tier != tier:
        _TIER_RANK = {"free": 0, "solo": 1, "professional": 2, "enterprise": 3}
        old_rank = _TIER_RANK.get(old_tier, 0)
        new_rank = _TIER_RANK.get(tier, 0)
        if new_rank > old_rank:
            record_billing_event(
                db,
                BillingEventType.SUBSCRIPTION_UPGRADED,
                user_id=user_id,
                tier=tier,
                metadata={"from_tier": old_tier},
            )
        elif new_rank < old_rank:
            record_billing_event(
                db,
                BillingEventType.SUBSCRIPTION_DOWNGRADED,
                user_id=user_id,
                tier=tier,
                metadata={"from_tier": old_tier},
            )


def _downgrade_org_members_to_free(db: Session, user_id: int) -> int:
    """Downgrade all org members (including the owner) to FREE tier.

    Returns the number of members downgraded.
    """
    from organization_model import Organization, OrganizationMember

    # Find the org owned by this user (subscription owner)
    org = db.query(Organization).filter(Organization.owner_user_id == user_id).first()
    if not org:
        return 0

    members = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org.id).all()

    member_user_ids = [m.user_id for m in members]
    if not member_user_ids:
        return 0

    member_users = db.query(User).filter(User.id.in_(member_user_ids)).all()
    users_by_id = {u.id: u for u in member_users}

    count = 0
    for member in members:
        member_user = users_by_id.get(member.user_id)
        if member_user and member_user.tier != UserTier.FREE:
            member_user.tier = UserTier.FREE
            count += 1

    if count:
        logger.info(
            "Downgraded %d org member(s) to FREE for org %d (owner user %d)",
            count,
            org.id,
            user_id,
        )

    return count


def handle_subscription_deleted(db: Session, event_data: dict) -> None:
    """Handle customer.subscription.deleted — subscription canceled.

    Downgrades the owner AND all org members to FREE tier in a single transaction.
    """
    user_id = _resolve_user_id(db, event_data)
    if user_id is None:
        logger.warning("customer.subscription.deleted: could not resolve user_id")
        return

    sub = get_subscription(db, user_id)
    if sub:
        sub.status = SubscriptionStatus.CANCELED
        sub.cancel_at_period_end = False

    # Downgrade owner to free tier
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.tier = UserTier.FREE

    # Downgrade ALL org members to free tier (not just the owner)
    _downgrade_org_members_to_free(db, user_id)

    db.flush()

    logger.info("customer.subscription.deleted: user %d and org members downgraded to free", user_id)

    # Phase LX: Record churn event (subscription actually ended)
    from billing.analytics import record_billing_event

    old_tier = sub.tier if sub else None
    record_billing_event(
        db,
        BillingEventType.SUBSCRIPTION_CHURNED,
        user_id=user_id,
        tier=old_tier,
    )


def handle_invoice_payment_failed(db: Session, event_data: dict) -> None:
    """Handle invoice.payment_failed — payment issue.

    AUDIT-08-F2: Now also revokes paid access (user.tier → FREE) and
    downgrades org members, not just sub.status.
    """
    customer_id = event_data.get("customer")
    if not customer_id:
        return

    sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
    if sub:
        sub.status = SubscriptionStatus.PAST_DUE

        # AUDIT-08-F2: Revoke paid access on payment failure
        user = db.query(User).filter(User.id == sub.user_id).first()
        if user and user.tier != UserTier.FREE:
            user.tier = UserTier.FREE
            _downgrade_org_members_to_free(db, sub.user_id)

        db.flush()
        logger.warning("invoice.payment_failed: user %d is now past_due, tier downgraded", sub.user_id)

        # Phase LX: Record payment failure event
        from billing.analytics import record_billing_event

        record_billing_event(
            db,
            BillingEventType.PAYMENT_FAILED,
            user_id=sub.user_id,
            tier=sub.tier,
        )

        # Sprint 591: Advance dunning state machine
        from billing.dunning_engine import handle_payment_failed

        stripe_invoice_id = event_data.get("id")
        handle_payment_failed(db, sub, stripe_invoice_id=stripe_invoice_id)


def handle_invoice_paid(db: Session, event_data: dict) -> None:
    """Handle invoice.paid — successful payment (renewal or recovery)."""
    customer_id = event_data.get("customer")
    if not customer_id:
        return

    sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
    if sub and sub.status == SubscriptionStatus.PAST_DUE:
        sub.status = SubscriptionStatus.ACTIVE
        db.flush()
        logger.info("invoice.paid: user %d recovered to active", sub.user_id)

        # Phase LX: Record payment recovery event
        from billing.analytics import record_billing_event

        record_billing_event(
            db,
            BillingEventType.PAYMENT_RECOVERED,
            user_id=sub.user_id,
            tier=sub.tier,
        )

        # Sprint 591: Resolve dunning episode on payment recovery
        from billing.dunning_engine import handle_payment_recovered

        handle_payment_recovered(db, sub)


def handle_subscription_trial_will_end(db: Session, event_data: dict) -> None:
    """Handle customer.subscription.trial_will_end — 3 days before trial expires.

    Phase LIX Sprint C. Logs the event for monitoring.

    Sprint 690: sends the trial-ending email via ``send_trial_ending_email``.
    Previously this handler was logging-only — users didn't get the standard
    3-day warning that Stripe's hook is designed to trigger.
    """
    user_id = _resolve_user_id(db, event_data)
    trial_end = event_data.get("trial_end")

    if user_id is None:
        logger.warning("customer.subscription.trial_will_end: could not resolve user_id")
        return

    logger.info(
        "customer.subscription.trial_will_end: user %d trial ends at %s",
        user_id,
        trial_end,
    )

    # Phase LX: Record trial ending warning (3-day notice — NOT actual expiration)
    from billing.analytics import record_billing_event

    sub = get_subscription(db, user_id)
    record_billing_event(
        db,
        BillingEventType.TRIAL_ENDING,
        user_id=user_id,
        tier=sub.tier if sub else None,
    )

    # Sprint 690: fire the trial-ending email.
    # Wrapped in try/except so a SendGrid outage or bad template cannot break
    # webhook processing — the billing event is the source of truth; email
    # is best-effort. Failures are surfaced via secure_operation logs.
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.email:
            return

        tier_label = sub.tier.title() if sub and sub.tier else "paid"
        days_remaining = _days_until(trial_end)

        portal_url = _portal_url_for_user(db, user_id)

        from email_service import send_trial_ending_email

        result = send_trial_ending_email(
            to_email=user.email,
            days_remaining=days_remaining,
            plan_name=f"Paciolus {tier_label}",
            portal_url=portal_url,
        )
        if not result.success:
            logger.warning(
                "trial_will_end email dispatch failed for user %d: %s",
                user_id,
                result.message,
            )
    except Exception as exc:  # pragma: no cover — defensive
        logger.exception("trial_will_end email dispatch raised: %s", type(exc).__name__)


def _days_until(epoch_seconds: int | None) -> int:
    """Sprint 690: convert a Stripe epoch-seconds timestamp into an integer
    "days from now" count, clamped to [0, 365]. Returns 3 when the timestamp
    is missing (Stripe's trial_will_end hook fires 3 days before conversion
    by default, so 3 is the best guess when the field is absent)."""
    if not epoch_seconds:
        return 3

    from datetime import UTC, datetime

    try:
        end = datetime.fromtimestamp(int(epoch_seconds), tz=UTC)
    except (OSError, OverflowError, TypeError, ValueError):
        return 3

    delta = (end - datetime.now(UTC)).total_seconds()
    days = int(delta // 86400)
    return max(0, min(365, days))


def _portal_url_for_user(db: Session, user_id: int) -> str:
    """Sprint 690: resolve a Stripe Customer Portal URL for the trial-ending
    email CTA. Falls back to the in-app billing-settings page if the portal
    session cannot be created — the webhook handler must never crash on a
    URL lookup and the in-app settings page always works for authenticated
    users.

    Prefers the pre-generated portal URL if the subscription row has a
    cached one; otherwise builds a fresh session via Stripe."""
    from config import FRONTEND_URL

    default_url = f"{FRONTEND_URL}/settings/billing"
    try:
        sub = get_subscription(db, user_id)
        if sub is None or not sub.stripe_customer_id:
            return default_url

        from billing.subscription_manager import create_portal_session

        return create_portal_session(sub.stripe_customer_id, return_url=default_url) or default_url
    except Exception:
        return default_url


def handle_subscription_created(db: Session, event_data: dict) -> None:
    """Handle customer.subscription.created — subscription created outside Checkout.

    AUDIT-08-F3: Catches subscriptions created via API, Stripe dashboard, or future
    integrations that bypass checkout.session.completed. Calls sync_subscription_from_stripe
    to ensure local state is consistent. If checkout.session.completed already handled
    this subscription, this is a no-op reconciliation.
    """
    user_id = _resolve_user_id(db, event_data)
    if user_id is None:
        logger.warning("customer.subscription.created: could not resolve user_id")
        return

    customer_id = event_data.get("customer")
    stripe_subscription_id = event_data.get("id")
    if not customer_id or not stripe_subscription_id:
        logger.warning("customer.subscription.created: missing customer or subscription ID")
        return

    # Check if a local subscription already exists (checkout.session.completed arrived first)
    existing_sub = get_subscription(db, user_id)
    is_new = existing_sub is None or existing_sub.stripe_subscription_id != stripe_subscription_id

    # Resolve tier from the base plan item
    items = event_data.get("items", {}).get("data", [])
    base_item = _find_base_plan_item(items)
    tier: str | None = None
    if base_item:
        price_id = base_item.get("price", {}).get("id", "")
        tier = _resolve_tier_from_price(price_id)

    if tier is None:
        logger.error(
            "customer.subscription.created: could not resolve tier for user %d (subscription %s)",
            user_id,
            stripe_subscription_id,
        )
        return

    sync_subscription_from_stripe(db, user_id, event_data, customer_id, tier)
    logger.info("customer.subscription.created: synced user %d to tier %s", user_id, tier)

    # Record analytics only if this handler is the first to create the local row
    if is_new:
        from billing.analytics import record_billing_event

        stripe_status = event_data.get("status", "")
        if stripe_status == "trialing":
            record_billing_event(
                db,
                BillingEventType.TRIAL_STARTED,
                user_id=user_id,
                tier=tier,
            )
        else:
            record_billing_event(
                db,
                BillingEventType.SUBSCRIPTION_CREATED,
                user_id=user_id,
                tier=tier,
            )


def handle_invoice_payment_succeeded(db: Session, event_data: dict) -> None:
    """Handle invoice.payment_succeeded — successful payment confirmation.

    AUDIT-08-F4: Complements invoice.paid. Restores access from non-entitled states
    (PAST_DUE, INCOMPLETE, UNPAID) back to ACTIVE with the plan-appropriate tier.
    No-op if subscription is already ACTIVE (idempotent).
    """
    customer_id = event_data.get("customer")
    if not customer_id:
        return

    sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
    if not sub:
        return

    # Idempotent: if already active, nothing to do
    if sub.status == SubscriptionStatus.ACTIVE:
        return

    # Restore from non-entitled states
    if sub.status in (SubscriptionStatus.PAST_DUE, SubscriptionStatus.INCOMPLETE, SubscriptionStatus.UNPAID):
        sub.status = SubscriptionStatus.ACTIVE

        # Restore user tier to plan-appropriate tier
        user = db.query(User).filter(User.id == sub.user_id).first()
        if user and sub.tier:
            try:
                user.tier = UserTier(sub.tier)
            except ValueError:
                logger.warning(
                    "invoice.payment_succeeded: unknown tier '%s' for user %d",
                    sub.tier,
                    sub.user_id,
                )

        db.flush()
        logger.info("invoice.payment_succeeded: user %d restored to active (tier=%s)", sub.user_id, sub.tier)

        from billing.analytics import record_billing_event

        record_billing_event(
            db,
            BillingEventType.PAYMENT_SUCCEEDED,
            user_id=sub.user_id,
            tier=sub.tier,
        )


def handle_dispute_created(db: Session, event_data: dict) -> None:
    """Handle charge.dispute.created — payment dispute opened.

    AUDIT-08-F5 dispute access policy: On dispute, immediately suspend access
    (status → PAUSED, tier → FREE) pending resolution. This protects against
    fraud and forced payment reversals on a financial SaaS platform.
    """
    customer_id = event_data.get("customer")
    if not customer_id:
        # Try to derive from charge if customer not directly on dispute
        charge = event_data.get("charge")
        if isinstance(charge, dict):
            customer_id = charge.get("customer")
        if not customer_id:
            logger.warning("charge.dispute.created: could not resolve customer_id")
            return

    sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
    if not sub:
        logger.warning("charge.dispute.created: no subscription for customer %s", customer_id)
        return

    # Suspend access
    sub.status = SubscriptionStatus.PAUSED

    user = db.query(User).filter(User.id == sub.user_id).first()
    if user:
        user.tier = UserTier.FREE

    _downgrade_org_members_to_free(db, sub.user_id)
    db.flush()

    dispute_id = event_data.get("id", "unknown")
    dispute_reason = event_data.get("reason", "unknown")
    logger.warning(
        "charge.dispute.created: user %d suspended — dispute %s reason=%s",
        sub.user_id,
        dispute_id,
        dispute_reason,
    )

    from billing.analytics import record_billing_event

    record_billing_event(
        db,
        BillingEventType.DISPUTE_CREATED,
        user_id=sub.user_id,
        tier=sub.tier,
        metadata={"dispute_id": dispute_id, "reason": dispute_reason},
    )


def handle_dispute_closed(db: Session, event_data: dict) -> None:
    """Handle charge.dispute.closed — dispute resolved.

    AUDIT-08-F5 dispute resolution policy:
    - Won (merchant prevails): restore access to plan tier.
    - Lost (customer prevails): cancel subscription, downgrade permanently.
    - Other statuses: leave suspended, log for operator review.
    """
    customer_id = event_data.get("customer")
    if not customer_id:
        charge = event_data.get("charge")
        if isinstance(charge, dict):
            customer_id = charge.get("customer")
        if not customer_id:
            logger.warning("charge.dispute.closed: could not resolve customer_id")
            return

    sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
    if not sub:
        logger.warning("charge.dispute.closed: no subscription for customer %s", customer_id)
        return

    dispute_status = event_data.get("status", "")
    dispute_id = event_data.get("id", "unknown")
    user = db.query(User).filter(User.id == sub.user_id).first()

    from billing.analytics import record_billing_event

    if dispute_status == "won":
        # Merchant won — restore access
        sub.status = SubscriptionStatus.ACTIVE
        if user and sub.tier:
            try:
                user.tier = UserTier(sub.tier)
            except ValueError:
                pass
        db.flush()
        logger.info("charge.dispute.closed: user %d restored — dispute %s won", sub.user_id, dispute_id)
        record_billing_event(
            db,
            BillingEventType.DISPUTE_RESOLVED_WON,
            user_id=sub.user_id,
            tier=sub.tier,
            metadata={"dispute_id": dispute_id},
        )
    elif dispute_status == "lost":
        # Customer won — cancel subscription
        sub.status = SubscriptionStatus.CANCELED
        if user:
            user.tier = UserTier.FREE
        _downgrade_org_members_to_free(db, sub.user_id)
        db.flush()
        logger.warning("charge.dispute.closed: user %d canceled — dispute %s lost", sub.user_id, dispute_id)
        record_billing_event(
            db,
            BillingEventType.DISPUTE_RESOLVED_LOST,
            user_id=sub.user_id,
            tier=sub.tier,
            metadata={"dispute_id": dispute_id},
        )
    else:
        # Other status — leave suspended, log for review
        db.flush()
        logger.info(
            "charge.dispute.closed: user %d dispute %s status=%s — leaving suspended",
            sub.user_id,
            dispute_id,
            dispute_status,
        )
        record_billing_event(
            db,
            BillingEventType.DISPUTE_CLOSED_OTHER,
            user_id=sub.user_id,
            tier=sub.tier,
            metadata={"dispute_id": dispute_id, "status": dispute_status},
        )


def handle_invoice_created(db: Session, event_data: dict) -> None:
    """Handle invoice.created — invoice lifecycle visibility.

    AUDIT-08-F6: Observability only — records analytics event for invoice creation
    (including proration invoices). No status/tier changes.
    """
    customer_id = event_data.get("customer")
    if not customer_id:
        return

    sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
    user_id = sub.user_id if sub else None

    invoice_id = event_data.get("id", "unknown")
    amount_due = event_data.get("amount_due")
    billing_reason = event_data.get("billing_reason")

    logger.info(
        "invoice.created: invoice=%s amount_due=%s reason=%s user=%s",
        invoice_id,
        amount_due,
        billing_reason,
        user_id,
    )

    from billing.analytics import record_billing_event

    record_billing_event(
        db,
        BillingEventType.INVOICE_CREATED,
        user_id=user_id,
        tier=sub.tier if sub else None,
        metadata={
            "invoice_id": invoice_id,
            "amount_due": amount_due,
            "billing_reason": billing_reason,
        },
    )


# Event type → handler mapping
WEBHOOK_HANDLERS: dict[str, Callable] = {
    # Existing
    "checkout.session.completed": handle_checkout_completed,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
    "customer.subscription.trial_will_end": handle_subscription_trial_will_end,
    "invoice.payment_failed": handle_invoice_payment_failed,
    "invoice.paid": handle_invoice_paid,
    # AUDIT-08: New handlers
    "customer.subscription.created": handle_subscription_created,
    "invoice.payment_succeeded": handle_invoice_payment_succeeded,
    "charge.dispute.created": handle_dispute_created,
    "charge.dispute.closed": handle_dispute_closed,
    "invoice.created": handle_invoice_created,
}


def process_webhook_event(
    db: Session,
    event_type: str,
    event_data: dict,
    event_created: int | None = None,
) -> bool:
    """Process a Stripe webhook event.

    Args:
        event_created: Unix timestamp from the Stripe event envelope (event.created).
            Used for out-of-order event detection on subscription state changes.

    Returns True if the event was handled, False if ignored.
    """
    handler = WEBHOOK_HANDLERS.get(event_type)
    if handler is None:
        logger.debug("Ignoring unhandled webhook event: %s", event_type)
        return False

    # For subscription events, check event ordering before processing
    if (
        event_type
        in (
            "customer.subscription.updated",
            "customer.subscription.deleted",
        )
        and event_created is not None
    ):
        user_id = _resolve_user_id(db, event_data)
        if user_id is not None:
            sub = get_subscription(db, user_id)
            if sub and sub.updated_at:
                from datetime import UTC, datetime

                event_time = datetime.fromtimestamp(event_created, tz=UTC)
                sub_updated = sub.updated_at
                if sub_updated.tzinfo is None:
                    sub_updated = sub_updated.replace(tzinfo=UTC)
                # Sprint 719 fix: changed `<` → `<=` so equal-second events
                # are also treated as stale. event_created is second-resolution
                # from Stripe; sub.updated_at is millisecond-precision from our
                # write. event_time == sub_updated overwhelmingly means
                # "Stripe redelivered the same event we already processed,"
                # not "a brand-new event landed in the same second" — handlers
                # are idempotent regardless, but skipping is the safer default
                # and matches what every other audit-time check in this file
                # already does.
                if event_time <= sub_updated:
                    logger.warning(
                        "Stale %s event (created=%s) arrived at-or-before local update (%s) for user %d — skipping",
                        event_type,
                        event_time.isoformat(),
                        sub_updated.isoformat(),
                        user_id,
                    )
                    return True  # Return 200 to Stripe but skip processing

    handler(db, event_data)
    return True
