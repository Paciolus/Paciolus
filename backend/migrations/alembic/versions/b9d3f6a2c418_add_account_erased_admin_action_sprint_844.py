"""Sprint 844: add ACCOUNT_ERASED to the adminactiontype enum.

Revision ID: b9d3f6a2c418
Revises: b5d2c8e71f30 (re-parented 2026-10-28: main gained Sprint 847's b5d2c8e71f30 on the same parent)
Create Date: 2026-10-24

The superadmin erase route (``POST /internal/admin/users/{id}/erase``) records
an ``AdminActionType.ACCOUNT_ERASED`` audit entry. ``admin_audit_logs.action_type``
is ``Enum(AdminActionType)`` with no ``values_callable``, so SQLAlchemy binds the
member NAME ('ACCOUNT_ERASED'); that is the label added here (see d8b945d0b4e5
for the lowercase-slug mistake this avoids). SQLite stores the column as
VARCHAR, so this is a no-op there. ``IF NOT EXISTS`` keeps it safe on a schema
built by ``create_all()`` from the updated ORM.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "b9d3f6a2c418"
down_revision: str | Sequence[str] | None = "b5d2c8e71f30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE adminactiontype ADD VALUE IF NOT EXISTS 'ACCOUNT_ERASED'")


def downgrade() -> None:
    # PostgreSQL cannot drop an enum label without recreating the type; the
    # addition is harmless to leave in place.
    pass
