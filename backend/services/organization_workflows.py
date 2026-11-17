"""Organization workflows as synchronous services — Sprint 892 (CEO brief 17B, review ST-12).

The HTTP handlers in ``routes/organization.py`` held each workflow: authorization, the seat lock,
the state changes and the commit. Each workflow now lives here, whole, and the route parses input
and turns ``OrganizationError`` into a response. The reusable policy pieces stay in
``shared.organization_policy`` (they raise ``HTTPException`` themselves, which passes through).
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta

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
from shared.organization_policy import (
    apply_org_subscription_to_user,
    get_user_org,
    require_admin,
    require_owner,
    revert_user_tier_after_removal,
    revoke_member_firm_shares,
    unique_slug,
)

logger = logging.getLogger(__name__)


class OrganizationError(Exception):
    """A workflow refusal with the status and message the route returns."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def create_organization(db: Session, user: User, name: str) -> Organization:
    """Create an organization with ``user`` as its owner, and commit."""
    existing = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if existing:
        raise OrganizationError(409, "You already belong to an organization.")

    slug = unique_slug(db, name)
    org = Organization(name=name, slug=slug, owner_user_id=user.id)
    db.add(org)
    db.flush()  # Get org.id

    # Create owner membership
    db.add(OrganizationMember(organization_id=org.id, user_id=user.id, role=OrgRole.OWNER))

    # Link user to org
    user.organization_id = org.id

    db.commit()
    db.refresh(org)
    return org


def _lock_org_for_seat_check(db: Session, org_id: int) -> Organization | None:
    """Take a row lock on the organization before a seat-limit check.

    Without a lock two concurrent requests both see a free seat and both insert.
    ``SELECT ... FOR UPDATE`` holds the lock until the caller commits, so a second
    request blocks and then counts the first one's row (Postgres; a no-op on SQLite).
    """
    return db.query(Organization).filter(Organization.id == org_id).with_for_update().first()


def create_invite(db: Session, user: User, email: str, role: str) -> tuple[OrganizationInvite, str]:
    """Invite ``email`` to the user's organization; returns the invite and its plaintext token."""
    org = get_user_org(db, user)
    require_admin(db, user, org)

    # Seat limit against the org subscription (not the inviter's personal one). Lock the
    # organization row first so seat reservations serialize (Sprint 821).
    _lock_org_for_seat_check(db, org.id)
    check_seat_limit_for_org(db, org.id)

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
        raise OrganizationError(409, "Unable to send invite. Please try again later.")

    existing_user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if existing_user:
        existing_member = db.query(OrganizationMember).filter(OrganizationMember.user_id == existing_user.id).first()
        if existing_member and existing_member.organization_id == org.id:
            raise OrganizationError(409, "User is already a member of this organization.")

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
    return invite, raw_token


def accept_invite(db: Session, user: User, token: str) -> None:
    """Accept an invite: membership, inherited tier, invite marked accepted — one commit."""
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
        raise OrganizationError(404, "Invite not found or already used.")

    # A leaked or intercepted token must not work for an unintended account.
    # Sprint 872 (AZ-11): always compared — an invite with no address matches nobody.
    if user.email.strip().lower() != (invite.invitee_email or "").strip().lower():
        raise OrganizationError(403, "This invite was sent to a different email address.")

    if invite.is_expired:
        invite.status = InviteStatus.EXPIRED
        db.commit()
        raise OrganizationError(410, "This invite has expired.")

    org = _lock_org_for_seat_check(db, invite.organization_id)
    if not org:
        raise OrganizationError(404, "Organization not found.")

    check_seat_limit_for_org(db, org.id, exclude_invite_id=invite.id)

    existing = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if existing:
        raise OrganizationError(409, "You already belong to an organization.")

    db.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=invite.role,
            invited_by_user_id=invite.invited_by_user_id,
        )
    )

    # Update user + inherit org's subscription tier (backfills org.subscription_id when it
    # can be resolved only from the org owner's personal subscription).
    user.organization_id = org.id
    apply_org_subscription_to_user(db, user, org)

    invite.status = InviteStatus.ACCEPTED
    invite.accepted_at = datetime.now(UTC)
    invite.accepted_by_user_id = user.id

    db.commit()


def remove_member(db: Session, user: User, member_id: int) -> None:
    """Remove a member (not the owner); their tier reverts; one commit."""
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
        raise OrganizationError(404, "Member not found.")

    if member.role == OrgRole.OWNER:
        raise OrganizationError(400, "Cannot remove the organization owner.")

    # Sprint 853 (AZ-15): an admin may remove members, but only the owner may
    # remove an admin — otherwise one admin can remove the other.
    if member.role == OrgRole.ADMIN:
        require_owner(db, user, org)

    # Restore the tier from a personal subscription if there is one, otherwise FREE.
    removed_user = db.query(User).filter(User.id == member.user_id).first()
    if removed_user:
        revert_user_tier_after_removal(db, removed_user)

    # Sprint 853: the firm's clients stay with the firm (their
    # ``organization_id`` does not change), so deleting the membership is what
    # takes them out of the member's reach. Share links the member made for
    # firm records are revoked with it.
    revoked = revoke_member_firm_shares(db, member.user_id, org.id)

    db.delete(member)
    db.commit()

    # Sprint 880 (DH-08): the revoked links' files go now. A failed delete is
    # retried by the share purge (every 10 minutes), which keeps the row until
    # storage confirms.
    from shared import export_share_storage

    for key in revoked:
        if key:
            export_share_storage.delete(key)

    logger.info(
        "Member removed: org_id=%s user_id=%s by=%s shares_revoked=%d", org.id, member.user_id, user.id, len(revoked)
    )
