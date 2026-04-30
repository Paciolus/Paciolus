"""Sprint 735: ``require_client_owner`` direct-only authorization contract.

Sprint 735 introduced ``require_client_owner`` alongside the existing
``require_client``. The two helpers must have *different* authorization
scope: ``require_client`` grants org-scoped access, ``require_client_owner``
grants direct-ownership only.

This test pins both contracts so a future "let's just merge them" cleanup
attempt fails loudly. Path B in Sprint 735 was the conscious decision to
keep diagnostic / trends / prior-period routes direct-only — merging the
helpers later would silently broaden authorization on those routes.
"""

from __future__ import annotations

import re

import pytest
from fastapi import HTTPException

from models import Client
from organization_model import OrganizationMember, OrgRole
from shared.client_access import require_client, require_client_owner


def _make_org(db, owner, name: str = "Sprint 735 Org"):
    """Create an Organization with `owner` as OWNER member; mirrors
    ``test_refactor_2026_04_20._make_org``."""
    from organization_model import Organization

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")[:90]
    org = Organization(name=name, slug=slug, owner_user_id=owner.id)
    db.add(org)
    db.flush()
    membership = OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER)
    db.add(membership)
    owner.organization_id = org.id
    db.flush()
    return org


def _make_client(db, owner, name: str = "Sprint 735 Client"):
    client = Client(name=name, user_id=owner.id)
    db.add(client)
    db.flush()
    return client


class TestRequireClientOwnerDirectOnly:
    """Sprint 735's new helper must NOT grant org-scoped access — that's
    what ``require_client`` is for. This is the one assertion that prevents
    a future regression where the two helpers get accidentally unified."""

    def test_direct_owner_gets_client(self, db_session, make_user):
        """Owner of the client gets the client back."""
        owner = make_user(email="owner_735_direct@example.com")
        client = _make_client(db_session, owner)

        result = require_client_owner(client_id=client.id, current_user=owner, db=db_session)

        assert result.id == client.id
        assert result.user_id == owner.id

    def test_unrelated_user_raises_404(self, db_session, make_user):
        """A user with no relationship to the owner gets 404."""
        owner = make_user(email="owner_735_unrelated@example.com")
        stranger = make_user(email="stranger_735@example.com")
        client = _make_client(db_session, owner)

        with pytest.raises(HTTPException) as exc_info:
            require_client_owner(client_id=client.id, current_user=stranger, db=db_session)

        assert exc_info.value.status_code == 404
        assert "Client not found" in str(exc_info.value.detail)

    def test_org_teammate_also_raises_404(self, db_session, make_user):
        """**The key Sprint 735 contract:** an active org-member of the
        client's owner does NOT get access via ``require_client_owner``,
        even though they would via ``require_client``. This pins the
        direct-only semantics so merging the helpers later requires
        an explicit policy decision (and customer comms)."""
        owner = make_user(email="owner_735_team@example.com")
        org = _make_org(db_session, owner)
        teammate = make_user(email="teammate_735@example.com")

        # Add teammate to the same org (active membership)
        membership = OrganizationMember(organization_id=org.id, user_id=teammate.id, role=OrgRole.MEMBER)
        db_session.add(membership)
        teammate.organization_id = org.id
        db_session.flush()

        client = _make_client(db_session, owner)

        with pytest.raises(HTTPException) as exc_info:
            require_client_owner(client_id=client.id, current_user=teammate, db=db_session)

        assert exc_info.value.status_code == 404, (
            "Sprint 735 contract violation: org teammate should NOT get access via "
            "require_client_owner. Use require_client (org-scoped) for routes that "
            "should grant teammate access. If this assertion is failing because "
            "policy changed and teammates should now see diagnostic outputs, that "
            "is a NEW sprint with explicit customer comms — not a refactor."
        )


class TestRequireClientOrgScoped:
    """Companion contract: ``require_client`` MUST grant org-scoped access.
    If this regresses to direct-only, clients.py and settings.py silently
    lose org-teammate functionality."""

    def test_org_teammate_gets_client_via_require_client(self, db_session, make_user):
        """Active org-member of the client's owner gets the client back
        via ``require_client``. This is the behavior that Sprint 735's
        ``require_client_owner`` deliberately does NOT inherit."""
        owner = make_user(email="owner_req_client@example.com")
        org = _make_org(db_session, owner)
        teammate = make_user(email="teammate_req_client@example.com")

        membership = OrganizationMember(organization_id=org.id, user_id=teammate.id, role=OrgRole.MEMBER)
        db_session.add(membership)
        teammate.organization_id = org.id
        db_session.flush()

        client = _make_client(db_session, owner)

        # Sanity: direct owner still gets the client
        owner_result = require_client(client_id=client.id, current_user=owner, db=db_session)
        assert owner_result.id == client.id

        # Key assertion: teammate ALSO gets the client (org-scoped behavior)
        teammate_result = require_client(client_id=client.id, current_user=teammate, db=db_session)
        assert teammate_result.id == client.id, (
            "require_client must be org-scoped — teammate should access "
            "the owner's client. If this regresses, clients.py and settings.py "
            "lose teammate visibility for client metadata."
        )
