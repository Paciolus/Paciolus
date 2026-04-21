"""Organization policy helpers.

Extracted from ``routes/organization.py`` so the HTTP layer can stay focused
on request/response shaping while membership / role / slug / subscription
rules live in a testable service module.

None of these helpers are transactional boundaries — callers own the commit.
"""

from __future__ import annotations

import logging
import re
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import User
from organization_model import (
    Organization,
    OrganizationMember,
    OrgRole,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------


def slugify(name: str) -> str:
    """Create a URL-safe slug from an organization name (≤ 90 chars, leaves
    room for a disambiguating suffix)."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:90]


def unique_slug(db: Session, base: str) -> str:
    """Return a slug that does not yet exist in the ``organizations`` table.

    Tries the plain slug first; on collision appends a short random suffix
    up to 10 attempts, then a longer one as a last resort.
    """
    slug = slugify(base)
    if not db.query(Organization).filter(Organization.slug == slug).first():
        return slug
    for _ in range(10):
        candidate = f"{slug}-{secrets.token_hex(3)}"
        if not db.query(Organization).filter(Organization.slug == candidate).first():
            return candidate
    return f"{slug}-{secrets.token_hex(6)}"


# ---------------------------------------------------------------------------
# Membership / role checks
# ---------------------------------------------------------------------------


def get_user_org(db: Session, user: User) -> Organization:
    """Return the organization ``user`` belongs to, or raise 404."""
    member = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="You are not part of an organization.")
    org = db.query(Organization).filter(Organization.id == member.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return org


def require_admin(db: Session, user: User, org: Organization) -> OrganizationMember:
    """Require ``user`` to be owner or admin of ``org``; return their membership."""
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )
    if not member or member.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        logger.warning("403 access denied: user_id=%s, required_role=admin_or_owner", user.id)
        raise HTTPException(status_code=403, detail="Access denied.")
    return member


def require_owner(db: Session, user: User, org: Organization) -> OrganizationMember:
    """Require ``user`` to be the owner of ``org``; return their membership."""
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )
    if not member or member.role != OrgRole.OWNER:
        logger.warning("403 access denied: user_id=%s, required_role=owner", user.id)
        raise HTTPException(status_code=403, detail="Access denied.")
    return member


# ---------------------------------------------------------------------------
# Subscription / tier inheritance on invite acceptance
# ---------------------------------------------------------------------------


def apply_org_subscription_to_user(db: Session, user: User, org: Organization) -> None:
    """Propagate the organization's active subscription tier onto ``user``.

    Lookup order:
      1. Subscription linked directly from ``org.subscription_id``.
      2. Fallback: the org owner's personal ACTIVE/TRIALING subscription.
         When found via fallback, backfill ``org.subscription_id`` so
         subsequent joins resolve the fast path.

    If no subscription is found, ``user.tier`` is left untouched (caller's
    prior default applies).
    """
    from subscription_model import Subscription, SubscriptionStatus

    sub = None
    if org.subscription_id:
        sub = (
            db.query(Subscription)
            .filter(
                Subscription.id == org.subscription_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
            )
            .first()
        )

    if sub is None and org.owner_user_id:
        sub = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == org.owner_user_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
            )
            .first()
        )
        if sub is not None:
            org.subscription_id = sub.id

    if sub:
        user.tier = sub.tier  # type: ignore[assignment]


def revert_user_tier_after_removal(db: Session, user: User) -> None:
    """Restore ``user.tier`` after they leave an organization.

    If the user has their own ACTIVE/TRIALING personal subscription, inherit
    that tier. Otherwise downgrade to FREE. Always clears ``organization_id``.
    """
    from models import UserTier
    from subscription_model import Subscription, SubscriptionStatus

    user.organization_id = None

    personal_sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
        )
        .first()
    )
    if personal_sub and personal_sub.tier:
        user.tier = UserTier(personal_sub.tier)
    else:
        user.tier = UserTier.FREE
