"""Client access policy helpers (Sprint 754 — relocated from `shared/helpers.py`).

Hosts the four client-access helpers that govern who can read/write a
`Client` record:

  - `is_authorized_for_client(user, client, db)` — predicate combining
    direct ownership + organization-scoped sharing.
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
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from models import Client, User


def is_authorized_for_client(user: User, client: Client, db: Session) -> bool:
    """Check whether ``user`` may access ``client``.

    Returns True if:
      (a) ``client.user_id == user.id`` (direct ownership), or
      (b) both ``user`` and the client's owner are active members of the
          same organization (organization-scoped sharing).
    """
    if client.user_id == user.id:
        return True

    if user.organization_id:
        from organization_model import OrganizationMember

        owner_membership = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == client.user_id,
                OrganizationMember.organization_id == user.organization_id,
            )
            .first()
        )
        if owner_membership:
            return True

    return False


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

    Org-scoped — grants access to the direct owner *and* to any active
    member of the same organization. Use this for routes where the client
    is shared across an org (metadata, settings).
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
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
