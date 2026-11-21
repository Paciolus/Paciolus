"""
Organization Routes — Phase LXIX: Pricing v3.

CRUD operations for organizations, member management, and invite flow.

Route group prefix: /organization
Auth: require_current_user (all endpoints)
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from models import User
from organization_model import (
    InviteStatus,
    Organization,
    OrganizationInvite,
    OrganizationMember,
    OrgRole,
)
from services import organization_workflows
from shared.organization_policy import (
    get_user_org,
    require_admin,
    require_owner,
    revert_user_tier_after_removal,
)
from shared.organization_schemas import (
    DetailResponse,
    OrganizationInviteCreateResponse,
    OrganizationInviteResponse,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationWithMemberCountResponse,
)
from shared.rate_limits import RATE_LIMIT_WRITE, limiter

logger = logging.getLogger(__name__)
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
# Organization CRUD
# ---------------------------------------------------------------------------


@router.post("", response_model=OrganizationResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def create_organization(
    body: CreateOrgRequest,
    request: Request,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create an organization. User becomes the owner."""
    try:
        return organization_workflows.create_organization(db, user, body.name).to_dict()
    except organization_workflows.OrganizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("", response_model=OrganizationWithMemberCountResponse)
def get_organization(
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get the current user's organization."""
    org = get_user_org(db, user)
    member_count = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org.id).count()
    result = org.to_dict()
    result["member_count"] = member_count
    return result


@router.put("", response_model=OrganizationResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def update_organization(
    body: UpdateOrgRequest,
    request: Request,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Update organization name. Owner or admin only."""
    org = get_user_org(db, user)
    require_admin(db, user, org)
    org.name = body.name
    db.commit()
    db.refresh(org)
    return org.to_dict()


# ---------------------------------------------------------------------------
# Invite management
# ---------------------------------------------------------------------------


def _lock_org_for_seat_check(db: Session, org_id: int) -> Organization | None:
    """Take a row lock on the organization before a seat-limit check.

    The seat check counts members + pending invites, then the caller inserts.
    Without a lock two concurrent requests both see a free seat and both
    insert. ``SELECT ... FOR UPDATE`` holds the lock until the caller commits,
    so a second request blocks and then counts the first one's row.
    """
    return db.query(Organization).filter(Organization.id == org_id).with_for_update().first()


@router.post("/invite", response_model=OrganizationInviteCreateResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def create_invite(
    body: InviteRequest,
    request: Request,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Send an organization invite. Owner/admin only. Checks seat limit."""
    try:
        invite, raw_token = organization_workflows.create_invite(db, user, body.email, body.role)
    except organization_workflows.OrganizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    result = invite.to_dict()
    result["invite_token"] = raw_token  # Return plaintext token only at creation time
    return result


@router.get("/invites", response_model=list[OrganizationInviteResponse])
def list_invites(
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List pending invites. Owner/admin only."""
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


@router.delete("/invites/{invite_id}", response_model=DetailResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def revoke_invite(
    invite_id: int,
    request: Request,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Revoke a pending invite. Owner/admin only."""
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


@router.post("/invite/accept/{token}", response_model=DetailResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def accept_invite(
    token: str,
    request: Request,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Accept an organization invite. Links the current user to the org."""
    try:
        organization_workflows.accept_invite(db, user, token)
    except organization_workflows.OrganizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return {"detail": "Invite accepted. You are now a member of the organization."}


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------


@router.get("/members", response_model=list[OrganizationMemberResponse])
def list_members(
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List organization members."""
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


@router.put("/members/{member_id}/role", response_model=OrganizationMemberResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def update_member_role(
    member_id: int,
    body: UpdateMemberRoleRequest,
    request: Request,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Change a member's role. Owner only."""
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

    member.role = OrgRole(body.role)
    db.commit()
    return member.to_dict()


@router.delete("/members/{member_id}", response_model=DetailResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def remove_member(
    member_id: int,
    request: Request,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Remove a member from the organization. Reverts their tier to free."""
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

    # Revert user tier: restore from personal subscription if one exists,
    # otherwise default to FREE.
    removed_user = db.query(User).filter(User.id == member.user_id).first()
    if removed_user:
        revert_user_tier_after_removal(db, removed_user)

    db.delete(member)
    db.commit()

    return {"detail": "Member removed from organization."}
