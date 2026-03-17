"""
Organization service layer — business logic for org CRUD, invites, and member management.

Extracted from routes/organization.py to enable independent unit testing and
enforce a clean separation between HTTP handling and domain workflows. All
database queries, seat-limit checks, and role-gating live here. Route handlers
delegate to these functions and translate results into HTTP responses.
"""

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import User
from organization_model import (
    INVITE_EXPIRY_HOURS,
    InviteStatus,
    Organization,
    OrganizationInvite,
    OrganizationMember,
    OrgRole,
)
from shared.entitlement_checks import check_seat_limit_for_org

# ---------------------------------------------------------------------------
# Data transfer objects (service → route)
# ---------------------------------------------------------------------------


@dataclass
class InviteResult:
    """Result of creating an invite, including the one-time plaintext token."""

    invite_dict: dict
    raw_token: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _slugify(name: str) -> str:
    """Create a URL-safe slug from an organization name."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:90]  # Leave room for uniqueness suffix


def _unique_slug(db: Session, base: str) -> str:
    """Ensure slug uniqueness by appending a short random suffix if needed."""
    slug = _slugify(base)
    if not db.query(Organization).filter(Organization.slug == slug).first():
        return slug
    for _ in range(10):
        candidate = f"{slug}-{secrets.token_hex(3)}"
        if not db.query(Organization).filter(Organization.slug == candidate).first():
            return candidate
    return f"{slug}-{secrets.token_hex(6)}"


def get_user_org(db: Session, user: User) -> Organization:
    """Get the user's organization or raise 404."""
    member = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="You are not part of an organization.")
    org = db.query(Organization).filter(Organization.id == member.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return org


def require_admin(db: Session, user: User, org: Organization) -> OrganizationMember:
    """Require user to be owner or admin of the org. Returns their membership."""
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )
    if not member or member.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        raise HTTPException(status_code=403, detail="Owner or admin role required.")
    return member


def require_owner(db: Session, user: User, org: Organization) -> OrganizationMember:
    """Require user to be the owner of the org."""
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )
    if not member or member.role != OrgRole.OWNER:
        raise HTTPException(status_code=403, detail="Owner role required.")
    return member


# ---------------------------------------------------------------------------
# Organization CRUD
# ---------------------------------------------------------------------------


def create_org(db: Session, user: User, name: str) -> dict:
    """Create an organization. The calling user becomes the owner.

    Returns the org dict. Raises 409 if user already belongs to an org.
    """
    existing = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already belong to an organization.")

    slug = _unique_slug(db, name)
    org = Organization(name=name, slug=slug, owner_user_id=user.id)
    db.add(org)
    db.flush()  # Get org.id

    # Create owner membership
    membership = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=OrgRole.OWNER,
    )
    db.add(membership)

    # Link user to org
    user.organization_id = org.id

    db.commit()
    db.refresh(org)
    return org.to_dict()


def get_org(db: Session, user: User) -> dict:
    """Get the current user's organization with member count."""
    org = get_user_org(db, user)
    member_count = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org.id).count()
    result = org.to_dict()
    result["member_count"] = member_count
    return result


def update_org(db: Session, user: User, name: str) -> dict:
    """Update organization name. Requires owner or admin role.

    Returns updated org dict.
    """
    org = get_user_org(db, user)
    require_admin(db, user, org)
    org.name = name
    db.commit()
    db.refresh(org)
    return org.to_dict()


# ---------------------------------------------------------------------------
# Invite management
# ---------------------------------------------------------------------------


def create_invite(db: Session, user: User, email: str, role: str) -> InviteResult:
    """Create an organization invite. Requires owner/admin. Checks seat limit.

    Returns an InviteResult with the invite dict and plaintext token (shown once).
    """
    org = get_user_org(db, user)
    require_admin(db, user, org)

    # Check seat limit against org subscription (not the inviter's personal subscription)
    check_seat_limit_for_org(db, org.id)

    # Check for duplicate pending invite
    existing_invite = (
        db.query(OrganizationInvite)
        .filter(
            OrganizationInvite.organization_id == org.id,
            func.lower(OrganizationInvite.invitee_email) == email.lower(),
            OrganizationInvite.status == InviteStatus.PENDING,
        )
        .first()
    )
    if existing_invite:
        raise HTTPException(status_code=409, detail="Unable to send invite. Please try again later.")

    # Check if user is already a member
    existing_user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if existing_user:
        existing_member = db.query(OrganizationMember).filter(OrganizationMember.user_id == existing_user.id).first()
        if existing_member and existing_member.organization_id == org.id:
            raise HTTPException(status_code=409, detail="User is already a member of this organization.")

    # Generate token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    invite = OrganizationInvite(
        organization_id=org.id,
        invite_token_hash=token_hash,
        invitee_email=email,
        role=OrgRole(role),
        invited_by_user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=INVITE_EXPIRY_HOURS),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return InviteResult(invite_dict=invite.to_dict(), raw_token=raw_token)


def list_invites(db: Session, user: User) -> list[dict]:
    """List pending invites for the user's org. Requires owner/admin."""
    org = get_user_org(db, user)
    require_admin(db, user, org)

    invites = (
        db.query(OrganizationInvite)
        .filter(
            OrganizationInvite.organization_id == org.id,
            OrganizationInvite.status == InviteStatus.PENDING,
        )
        .order_by(OrganizationInvite.created_at.desc())
        .all()
    )
    return [inv.to_dict() for inv in invites]


def revoke_invite(db: Session, user: User, invite_id: int) -> dict:
    """Revoke a pending invite. Requires owner/admin.

    Returns confirmation dict.
    """
    org = get_user_org(db, user)
    require_admin(db, user, org)

    invite = (
        db.query(OrganizationInvite)
        .filter(
            OrganizationInvite.id == invite_id,
            OrganizationInvite.organization_id == org.id,
            OrganizationInvite.status == InviteStatus.PENDING,
        )
        .first()
    )
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found or already resolved.")

    invite.status = InviteStatus.REVOKED
    db.commit()
    return {"detail": "Invite revoked."}


def accept_invite(db: Session, user: User, token: str) -> dict:
    """Accept an organization invite. Links the current user to the org.

    Verifies email match, expiry, seat limits, and existing membership.
    Returns confirmation dict.
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    invite = (
        db.query(OrganizationInvite)
        .filter(
            OrganizationInvite.invite_token_hash == token_hash,
            OrganizationInvite.status == InviteStatus.PENDING,
        )
        .first()
    )
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found or already used.")

    # Security: Verify the accepting user's email matches the invite recipient.
    # Prevents a leaked/intercepted token from being used by an unintended account.
    if invite.invitee_email and user.email.lower() != invite.invitee_email.lower():
        raise HTTPException(
            status_code=403,
            detail="This invite was sent to a different email address.",
        )

    if invite.is_expired:
        invite.status = InviteStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=410, detail="This invite has expired.")

    # Check seat limit for the org (uses org subscription, not inviter's).
    # Exclude the invite being accepted from the pending count — accepting it
    # converts pending→accepted, not adding a new seat beyond what was reserved.
    org = db.query(Organization).filter(Organization.id == invite.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    check_seat_limit_for_org(db, org.id, exclude_invite_id=invite.id)

    # Check user isn't already in an org
    existing = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already belong to an organization.")

    # Create membership
    membership = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=invite.role,
        invited_by_user_id=invite.invited_by_user_id,
    )
    db.add(membership)

    # Update user
    user.organization_id = org.id
    # Inherit org's tier from subscription
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

    # Fallback: resolve subscription from org owner if org.subscription_id is null
    if sub is None and org.owner_user_id:
        sub = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == org.owner_user_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
            )
            .first()
        )
        # Backfill linkage
        if sub is not None:
            org.subscription_id = sub.id

    if sub:
        user.tier = sub.tier

    # Mark invite accepted
    invite.status = InviteStatus.ACCEPTED
    invite.accepted_at = datetime.now(UTC)
    invite.accepted_by_user_id = user.id

    db.commit()
    return {"detail": "Invite accepted. You are now a member of the organization."}


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------


def list_members(db: Session, user: User) -> list[dict]:
    """List organization members with user name/email."""
    org = get_user_org(db, user)

    members = (
        db.query(OrganizationMember, User)
        .join(User, User.id == OrganizationMember.user_id)
        .filter(OrganizationMember.organization_id == org.id)
        .order_by(OrganizationMember.joined_at)
        .all()
    )

    results = []
    for member, member_user in members:
        d = member.to_dict()
        d["user_name"] = member_user.name or member_user.email
        d["user_email"] = member_user.email
        results.append(d)

    return results


def update_member_role(db: Session, user: User, member_id: int, role: str) -> dict:
    """Change a member's role. Owner only.

    Returns the updated member dict.
    """
    org = get_user_org(db, user)
    require_owner(db, user, org)

    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org.id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")

    if member.role == OrgRole.OWNER:
        raise HTTPException(status_code=400, detail="Cannot change the owner's role.")

    member.role = OrgRole(role)
    db.commit()
    return member.to_dict()


def remove_member(db: Session, user: User, member_id: int) -> dict:
    """Remove a member from the organization. Requires admin. Reverts their tier to free.

    Returns confirmation dict.
    """
    org = get_user_org(db, user)
    require_admin(db, user, org)

    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org.id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")

    if member.role == OrgRole.OWNER:
        raise HTTPException(status_code=400, detail="Cannot remove the organization owner.")

    # Revert user to free tier
    removed_user = db.query(User).filter(User.id == member.user_id).first()
    if removed_user:
        from models import UserTier

        removed_user.tier = UserTier.FREE
        removed_user.organization_id = None

    db.delete(member)
    db.commit()

    return {"detail": "Member removed and reverted to free tier."}
