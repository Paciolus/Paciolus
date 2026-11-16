"""Sprint 872 (AZ-11): an invitation is accepted only by a verified account
whose verified address matches it.

Before: ``POST /organization/invite/accept/{token}`` depended on
``require_current_user``, and registration issues a session before the
address is verified — so anyone holding a leaked invitation could register
the invited address, skip verification and join the firm.

Real access tokens, real dependencies (no auth overrides).
"""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy.orm import Session

from auth import create_access_token
from database import get_db
from main import app
from models import User
from organization_model import (
    INVITE_EXPIRY_HOURS,
    InviteStatus,
    Organization,
    OrganizationInvite,
    OrganizationMember,
    OrgRole,
)
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

pytestmark = pytest.mark.usefixtures("bypass_csrf")

INVITED = "invited-872@example.com"


@pytest.fixture
def api(db_session: Session) -> Iterator[httpx.AsyncClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def firm_invite(db_session: Session, make_user) -> tuple[Organization, OrganizationInvite, str]:
    owner = make_user(email="owner-872@example.com")
    sub = Subscription(
        user_id=owner.id,
        tier="professional",
        status=SubscriptionStatus.ACTIVE,
        billing_interval=BillingInterval.MONTHLY,
        seat_count=7,
        additional_seats=0,
    )
    db_session.add(sub)
    db_session.flush()
    org = Organization(name="Firm 872", slug=f"firm-872-{secrets.token_hex(3)}", owner_user_id=owner.id)
    org.subscription_id = sub.id
    db_session.add(org)
    db_session.flush()
    db_session.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER))
    owner.organization_id = org.id
    raw = secrets.token_urlsafe(32)
    invite = OrganizationInvite(
        organization_id=org.id,
        invite_token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        invitee_email=INVITED,
        role=OrgRole.MEMBER,
        invited_by_user_id=owner.id,
        expires_at=datetime.now(UTC) + timedelta(hours=INVITE_EXPIRY_HOURS),
    )
    db_session.add(invite)
    db_session.flush()
    return org, invite, raw


def _auth(user: User) -> dict[str, str]:
    token, _ = create_access_token(user.id, user.email, user.password_changed_at)
    return {"Authorization": f"Bearer {token}"}


def _membership(db: Session, user: User) -> OrganizationMember | None:
    return db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()


def _status(db: Session, invite: OrganizationInvite) -> InviteStatus:
    db.refresh(invite)
    return invite.status


@pytest.mark.asyncio
async def test_unverified_account_with_matching_address_is_refused(api, db_session, make_user, firm_invite):
    _org, invite, raw = firm_invite
    squatter = make_user(email=INVITED, is_verified=False)
    r = await api.post(f"/organization/invite/accept/{raw}", headers=_auth(squatter))
    assert r.status_code == 403
    assert _status(db_session, invite) == InviteStatus.PENDING
    assert _membership(db_session, squatter) is None


@pytest.mark.asyncio
async def test_verified_account_with_matching_address_is_accepted(api, db_session, make_user, firm_invite):
    org, invite, raw = firm_invite
    invitee = make_user(email=INVITED, is_verified=True)
    r = await api.post(f"/organization/invite/accept/{raw}", headers=_auth(invitee))
    assert r.status_code == 200, r.text
    assert _status(db_session, invite) == InviteStatus.ACCEPTED
    member = _membership(db_session, invitee)
    assert member is not None and member.organization_id == org.id


@pytest.mark.asyncio
async def test_verified_account_with_a_different_address_is_refused(api, db_session, make_user, firm_invite):
    _org, invite, raw = firm_invite
    other = make_user(email="someone-else-872@example.com", is_verified=True)
    r = await api.post(f"/organization/invite/accept/{raw}", headers=_auth(other))
    assert r.status_code == 403
    assert _status(db_session, invite) == InviteStatus.PENDING
    assert _membership(db_session, other) is None


@pytest.mark.asyncio
async def test_unverified_pending_email_change_to_the_invited_address_is_refused(
    api, db_session, make_user, firm_invite
):
    """A verified account whose *pending* (unverified) new address is the
    invited one has not verified that address."""
    _org, invite, raw = firm_invite
    user = make_user(email="verified-old-872@example.com", is_verified=True)
    user.pending_email = INVITED
    db_session.flush()
    r = await api.post(f"/organization/invite/accept/{raw}", headers=_auth(user))
    assert r.status_code == 403
    assert _status(db_session, invite) == InviteStatus.PENDING
