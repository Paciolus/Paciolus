"""Organization workflows as synchronous services — Sprint 892 (CEO brief 17B, review ST-12).

The HTTP handlers in ``routes/organization.py`` held each workflow: authorization, the seat lock,
the state changes and the commit. Each workflow now lives here, whole, and the route parses input
and turns ``OrganizationError`` into a response. The reusable policy pieces stay in
``shared.organization_policy`` (they raise ``HTTPException`` themselves, which passes through).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from models import User
from organization_model import Organization, OrganizationMember, OrgRole
from shared.organization_policy import unique_slug


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
