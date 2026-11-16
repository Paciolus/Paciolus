"""Client access policy helpers (Sprint 754 — relocated from `shared/helpers.py`).

Hosts the four client-access helpers that govern who can read/write a
`Client` record:

  - `client_scope(db, user_id)` — the SQL filter every manager uses
    (Sprint 853: firm clients belong to the firm, personal clients to
    their creator); `can_access_client` is its Python form.
  - `is_authorized_for_client(user, client, db)` — predicate form.
  - `get_accessible_client(user, client_id, db)` — `Client | None`.
  - `require_client(...)` — FastAPI dependency raising 404 if access is
    denied. Org-scoped (broader auth surface).
  - `require_client_owner(...)` — FastAPI dependency raising 404 unless
    the caller is the direct owner. Used by diagnostic / trends /
    prior-period routes that intentionally exclude org teammates (Sprint
    735 — see `require_client_owner` docstring for the audit-trail).

The deferred-items entry in `tasks/todo.md` (2026-04-20) said: "revisit
only if a fourth helper joins them." Sprint 735's `require_client_owner`
was the fourth, and Sprint 754 made the move. All 6 callers were
migrated to import from `shared.client_access` directly — no shim is
maintained on `shared.helpers` (matches the Sprint 724 discipline of
no re-export shims).
"""

from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi import Path as PathParam
from sqlalchemy import ColumnElement, and_, or_
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from models import Client, User


class RecordNotFound(ValueError):
    """A record is missing or out of the caller's reach (Sprint 853).

    A ``ValueError`` subclass so existing callers that catch ``ValueError``
    keep working; routes map it to 404 ahead of their 400 validation branch,
    so "not yours" and "does not exist" look the same from outside.
    """


def caller_organization_id(db: Session, user_id: int) -> int | None:
    """The firm ``user_id`` belongs to right now, from the membership row.

    ``OrganizationMember`` is the record of membership (``get_user_org`` reads
    it too); ``User.organization_id`` is a convenience copy kept beside it.
    """
    from organization_model import OrganizationMember

    row = db.query(OrganizationMember.organization_id).filter(OrganizationMember.user_id == user_id).first()
    return row[0] if row else None


def client_scope(db: Session, user_id: int) -> ColumnElement[bool]:
    """SQL filter on ``Client`` for every client ``user_id`` may reach.

    Sprint 853 (review AZ-01 / DH-02): a client belongs to the firm recorded
    on it (``Client.organization_id``), not to whoever created it.

      * a firm client is reachable by the firm's current members only;
      * a personal client (no firm) is reachable by its creator only.

    Joining or leaving a firm never moves a record, so a removed member loses
    the firm's clients and a new firm never gains them. Every manager and
    route that scopes clients or their child records (engagements, follow-up
    items and comments, expectations, misstatements, tool runs, saved
    summaries, exports, the workpaper index) goes through this filter.
    """
    personal = and_(Client.organization_id.is_(None), Client.user_id == user_id)
    org_id = caller_organization_id(db, user_id)
    if org_id is None:
        return personal
    return or_(personal, Client.organization_id == org_id)


def can_access_client(db: Session, user_id: int, client: Client) -> bool:
    """Python form of :func:`client_scope` for an already-loaded client."""
    if client.organization_id is None:
        return client.user_id == user_id
    return client.organization_id == caller_organization_id(db, user_id)


class FirmRoleRequired(HTTPException):
    """403: the record is in reach but the caller's firm role is too low."""

    def __init__(self) -> None:
        super().__init__(status_code=403, detail="Only the firm's owner or an admin can do this.")


def require_destructive_role(db: Session, user_id: int, client: Client) -> None:
    """Gate a destructive action on a client or one of its records (Sprint 853, AZ-15).

    CEO decision (2026-11-16): deleting a client, or archiving an engagement,
    expectation or misstatement, needs the firm's owner or an admin; members
    still create and edit. A personal client has only its creator in reach,
    so it needs nothing more.

    This sits *beside* the firm check, not instead of it: callers first load
    the record through :func:`client_scope` (404 if out of reach), then call
    this (403 if in reach but the role is too low).
    """
    if client.organization_id is None:
        return

    from organization_model import OrganizationMember, OrgRole

    role = (
        db.query(OrganizationMember.role)
        .filter(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == client.organization_id,
        )
        .scalar()
    )
    if role not in (OrgRole.OWNER, OrgRole.ADMIN):
        raise FirmRoleRequired()


def require_destructive_role_for_engagement(db: Session, user_id: int, engagement_client_id: int) -> None:
    """:func:`require_destructive_role` for a record reached through an engagement."""
    client = db.query(Client).filter(Client.id == engagement_client_id).one()
    require_destructive_role(db, user_id, client)


def is_authorized_for_client(user: User, client: Client, db: Session) -> bool:
    """Check whether ``user`` may access ``client`` (see :func:`client_scope`)."""
    return can_access_client(db, user.id, client)


def get_accessible_client(user: User, client_id: int, db: Session) -> Client | None:
    """Return ``Client`` if ``user`` may access it, else None."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return None
    if is_authorized_for_client(user, client, db):
        return client
    return None


def require_client(
    client_id: int = PathParam(..., description="The ID of the client"),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> Client:
    """FastAPI dependency: resolve a ``Client`` by id or raise 404.

    Firm-scoped — a firm client is open to the firm's current members, a
    personal client to its creator (see :func:`client_scope`).
    """
    client = get_accessible_client(current_user, client_id, db)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def require_client_owner(
    client_id: int = PathParam(..., description="The ID of the client"),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> Client:
    """FastAPI dependency: resolve a ``Client`` by id with **direct-ownership
    only** authorization (no organization-scoped sharing). Raises 404 if the
    caller is not the direct owner, even if they're an active member of the
    same organization as the owner.

    Sprint 735: introduced for diagnostic / trends / prior-period routes that
    historically used inline ``db.query(Client).filter(Client.id == ...,
    Client.user_id == current_user.id).first()`` to enforce direct-only
    access. Adopting the existing ``require_client`` helper there would have
    silently broadened authorization to org members (since ``require_client``
    calls ``get_accessible_client`` → ``is_authorized_for_client`` which
    OR-checks org membership) — a real behavior change, not a syntax cleanup.

    This helper preserves the existing direct-ownership semantics. If product
    later decides to open diagnostic outputs to org teammates, migrate routes
    from ``require_client_owner`` to ``require_client`` explicitly with
    customer comms — don't merge the two helpers silently.
    """
    client = db.query(Client).filter(Client.id == client_id, Client.user_id == current_user.id).first()
    # Sprint 853: being the creator is no longer enough on its own. A firm
    # client stays with the firm, so a creator who has left it gets a 404.
    if not client or not can_access_client(db, current_user.id, client):
        raise HTTPException(status_code=404, detail="Client not found")
    return client
