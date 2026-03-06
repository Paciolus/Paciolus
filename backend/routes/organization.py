"""
Organization Routes — Phase LXIX: Pricing v3.

CRUD operations for organizations, member management, and invite flow.

Route group prefix: /organization
Auth: require_current_user (all endpoints)
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from models import User
from organization_model import (
    INVITE_EXPIRY_HOURS,
    InviteStatus,
    Organization,
    OrganizationInvite,
    OrganizationMember,
    OrgRole,
)
from shared.entitlement_checks import check_seat_limit
from shared.rate_limits import RATE_LIMIT_WRITE, limiter

router = APIRouter(prefix="/organization", tags=["organization"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class CreateOrgRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class UpdateOrgRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern="^(admin|member)$")


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(..., pattern="^(admin|member)$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slugify(name: str) -> str:
    """Create a URL-safe slug from an organization name."""
    import re

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


def _get_user_org(db: Session, user: User) -> Organization:
    """Get the user's organization or raise 404."""
    member = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="You are not part of an organization.")
    org = db.query(Organization).filter(Organization.id == member.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return org


def _require_admin(db: Session, user: User, org: Organization) -> OrganizationMember:
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


def _require_owner(db: Session, user: User, org: Organization) -> OrganizationMember:
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


@router.post("")
@limiter.limit(RATE_LIMIT_WRITE)
async def create_organization(
    body: CreateOrgRequest,
    request=None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Create an organization. User becomes the owner."""
    # Check if user already belongs to an org
    existing = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already belong to an organization.")

    slug = _unique_slug(db, body.name)
    org = Organization(name=body.name, slug=slug, owner_user_id=user.id)
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


@router.get("")
async def get_organization(
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's organization."""
    org = _get_user_org(db, user)
    member_count = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org.id).count()
    result = org.to_dict()
    result["member_count"] = member_count
    return result


@router.put("")
@limiter.limit(RATE_LIMIT_WRITE)
async def update_organization(
    body: UpdateOrgRequest,
    request=None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Update organization name. Owner or admin only."""
    org = _get_user_org(db, user)
    _require_admin(db, user, org)
    org.name = body.name
    db.commit()
    db.refresh(org)
    return org.to_dict()


# ---------------------------------------------------------------------------
# Invite management
# ---------------------------------------------------------------------------


@router.post("/invite")
@limiter.limit(RATE_LIMIT_WRITE)
async def create_invite(
    body: InviteRequest,
    request=None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Send an organization invite. Owner/admin only. Checks seat limit."""
    org = _get_user_org(db, user)
    _require_admin(db, user, org)

    # Check seat limit
    check_seat_limit(user, db)

    # Check for duplicate pending invite
    existing_invite = (
        db.query(OrganizationInvite)
        .filter(
            OrganizationInvite.organization_id == org.id,
            func.lower(OrganizationInvite.invitee_email) == body.email.lower(),
            OrganizationInvite.status == InviteStatus.PENDING,
        )
        .first()
    )
    if existing_invite:
        raise HTTPException(status_code=409, detail="Unable to send invite. Please try again later.")

    # Check if user is already a member
    existing_user = db.query(User).filter(func.lower(User.email) == body.email.lower()).first()
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
        invitee_email=body.email,
        role=OrgRole(body.role),
        invited_by_user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=INVITE_EXPIRY_HOURS),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    result = invite.to_dict()
    result["invite_token"] = raw_token  # Return plaintext token only at creation time
    return result


@router.get("/invites")
async def list_invites(
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """List pending invites. Owner/admin only."""
    org = _get_user_org(db, user)
    _require_admin(db, user, org)

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


@router.delete("/invites/{invite_id}")
@limiter.limit(RATE_LIMIT_WRITE)
async def revoke_invite(
    invite_id: int,
    request=None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Revoke a pending invite. Owner/admin only."""
    org = _get_user_org(db, user)
    _require_admin(db, user, org)

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


@router.post("/invite/accept/{token}")
@limiter.limit(RATE_LIMIT_WRITE)
async def accept_invite(
    token: str,
    request=None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Accept an organization invite. Links the current user to the org."""
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

    # Check seat limit for the org
    org = db.query(Organization).filter(Organization.id == invite.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    # Load org owner to check their seat entitlement
    org_owner = db.query(User).filter(User.id == org.owner_user_id).first()
    if org_owner:
        check_seat_limit(org_owner, db)

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

    sub = (
        db.query(Subscription)
        .filter(
            Subscription.id == org.subscription_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
        )
        .first()
    )
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


@router.get("/members")
async def list_members(
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """List organization members."""
    org = _get_user_org(db, user)

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


@router.put("/members/{member_id}/role")
@limiter.limit(RATE_LIMIT_WRITE)
async def update_member_role(
    member_id: int,
    body: UpdateMemberRoleRequest,
    request=None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Change a member's role. Owner only."""
    org = _get_user_org(db, user)
    _require_owner(db, user, org)

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

    member.role = OrgRole(body.role)
    db.commit()
    return member.to_dict()


@router.delete("/members/{member_id}")
@limiter.limit(RATE_LIMIT_WRITE)
async def remove_member(
    member_id: int,
    request=None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Remove a member from the organization. Reverts their tier to free."""
    org = _get_user_org(db, user)
    _require_admin(db, user, org)

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
