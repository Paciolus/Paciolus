"""Sprint 853: clients.organization_id — firm records belong to the firm.

Revision ID: c853a1f0e2d4
Revises: c3e7a1f9d524
Create Date: 2026-11-16

WHY
---
A client was owned by the person who created it (``clients.user_id``), and
firm sharing was worked out from that person's *current* membership. Removing
a member took the firm's clients with them; admitting them to another firm
opened those clients to the new firm (review AZ-01 / DH-02).

``clients.organization_id`` records the owning firm once, when the client is
created, and access is decided from it (``shared.client_access.client_scope``).

BACKFILL (CEO decision, 2026-11-16)
-----------------------------------
A client whose creator belongs to a firm today becomes that firm's client
(from ``organization_members``, the membership record). A client whose creator
has no firm stays personal (NULL). Joining or leaving a firm afterwards never
moves a record. The counts are logged so the deploy log records the split.

``ondelete=RESTRICT``: a firm that still owns clients cannot be deleted out
from under them. Guarded with an inspector check like ``f3b81d6e2a47``, since a
database built by ``create_all()`` may already have the column.
"""

import logging
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c853a1f0e2d4"
down_revision: str | Sequence[str] | None = "c3e7a1f9d524"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

logger = logging.getLogger("alembic.runtime.migration")

_FK_NAME = "fk_clients_organization_id"
_INDEX_NAME = "ix_clients_organization_id"


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if not _has_column("clients", "organization_id"):
        with op.batch_alter_table("clients", schema=None) as batch_op:
            batch_op.add_column(sa.Column("organization_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(_FK_NAME, "organizations", ["organization_id"], ["id"], ondelete="RESTRICT")
            batch_op.create_index(_INDEX_NAME, ["organization_id"], unique=False)

    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE clients SET organization_id = ("
            "  SELECT m.organization_id FROM organization_members m WHERE m.user_id = clients.user_id"
            ") WHERE organization_id IS NULL"
            " AND EXISTS (SELECT 1 FROM organization_members m WHERE m.user_id = clients.user_id)"
        )
    )
    firm = bind.execute(sa.text("SELECT COUNT(*) FROM clients WHERE organization_id IS NOT NULL")).scalar() or 0
    personal = bind.execute(sa.text("SELECT COUNT(*) FROM clients WHERE organization_id IS NULL")).scalar() or 0
    logger.info("Sprint 853 backfill: %d clients assigned to a firm, %d stayed personal", firm, personal)


def downgrade() -> None:
    if _has_column("clients", "organization_id"):
        with op.batch_alter_table("clients", schema=None) as batch_op:
            batch_op.drop_index(_INDEX_NAME)
            batch_op.drop_constraint(_FK_NAME, type_="foreignkey")
            batch_op.drop_column("organization_id")
