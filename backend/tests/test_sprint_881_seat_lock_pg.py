"""Sprint 881 (TQ-11) — the seat lock is tested as behaviour, on PostgreSQL.

``test_organization_routes.TestBug04`` sends its "concurrent" invites one after the
other and asserts only ``200 in statuses``; ``test_sprint_821_concurrency_guards``
checks that compiled SQL contains ``FOR UPDATE``. Neither fails if the lock stops
working.

Here a firm has two seats, one taken by the owner, under hard enforcement. Two
invitations are sent at once through the real ``POST /organization/invite`` route,
each request on its own committed session (as in production). The seat check is
followed by a 0.5 s pause, so without the row lock both requests count one free seat
and both insert. With the lock the second waits for the first to commit and then
counts its invitation. Expected: exactly one 200, one 403, one pending invitation.

Checked by hand: with ``services.organization_workflows._lock_org_for_seat_check`` patched to a
no-op this test fails (two 200s, two pending invitations) — see Sprint 881 in
tasks/todo.md.

SQLite has no row locks, so this module is skipped there; CI's
``backend-tests-postgres`` job runs it.
"""

import time
import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from models import User, UserTier
from organization_model import InviteStatus, Organization, OrganizationInvite, OrganizationMember, OrgRole
from subscription_model import BillingInterval, Subscription, SubscriptionStatus
from tests.conftest import _is_test_sqlite

pytestmark = pytest.mark.skipif(_is_test_sqlite, reason="row locks need PostgreSQL")


@pytest.fixture
def two_seat_firm(db_engine):
    """Owner + Professional subscription with 2 seats in total, committed for real."""
    factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    tag = uuid.uuid4().hex[:8]
    with factory() as s:
        owner = User(
            email=f"tq11_owner_{tag}@example.com",
            hashed_password="x",
            tier=UserTier.PROFESSIONAL,
            is_active=True,
            is_verified=True,
        )
        s.add(owner)
        s.flush()
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=2,  # two seats in total for this test, one taken by the owner
            additional_seats=0,
        )
        s.add(sub)
        s.flush()
        org = Organization(name=f"TQ11 {tag}", slug=f"tq11-{tag}", owner_user_id=owner.id, subscription_id=sub.id)
        s.add(org)
        s.flush()
        s.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER))
        owner.organization_id = org.id
        s.commit()
        ids = {"owner": owner.id, "org": org.id, "sub": sub.id}

    yield factory, owner, ids, tag

    with factory() as s:
        s.query(User).filter(User.id == ids["owner"]).update({User.organization_id: None})
        s.query(OrganizationInvite).filter(OrganizationInvite.organization_id == ids["org"]).delete()
        s.query(OrganizationMember).filter(OrganizationMember.organization_id == ids["org"]).delete()
        s.query(Organization).filter(Organization.id == ids["org"]).delete()
        s.query(Subscription).filter(Subscription.id == ids["sub"]).delete()
        s.query(User).filter(User.id == ids["owner"]).delete()
        s.commit()


@pytest.mark.usefixtures("bypass_csrf")
@pytest.mark.anyio
async def test_two_simultaneous_invites_for_the_last_seat(two_seat_firm):
    import asyncio

    import services.organization_workflows as org_routes  # Sprint 892 moved the workflow here
    from auth import require_current_user
    from database import get_db
    from main import app

    factory, owner, ids, tag = two_seat_firm

    def per_request_session():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    real_check = org_routes.check_seat_limit_for_org

    def check_then_pause(db, org_id, exclude_invite_id=None):
        real_check(db, org_id, exclude_invite_id=exclude_invite_id)
        time.sleep(0.5)  # hold the window between the count and the insert open

    app.dependency_overrides[require_current_user] = lambda: owner
    app.dependency_overrides[get_db] = per_request_session
    try:
        with (
            patch("shared.entitlement_checks._get_seat_enforcement_mode", return_value="hard"),
            patch.object(org_routes, "check_seat_limit_for_org", check_then_pause),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                responses = await asyncio.gather(
                    client.post("/organization/invite", json={"email": f"tq11_a_{tag}@example.com"}),
                    client.post("/organization/invite", json={"email": f"tq11_b_{tag}@example.com"}),
                )
    finally:
        app.dependency_overrides.clear()

    assert sorted(r.status_code for r in responses) == [200, 403], [r.text for r in responses]
    with factory() as s:
        pending = (
            s.query(OrganizationInvite)
            .filter(
                OrganizationInvite.organization_id == ids["org"],
                OrganizationInvite.status == InviteStatus.PENDING,
                OrganizationInvite.expires_at > datetime.now(UTC),
            )
            .count()
        )
    assert pending == 1
