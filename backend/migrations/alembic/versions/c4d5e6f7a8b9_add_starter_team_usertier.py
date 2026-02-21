"""add starter and team to UserTier enum

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-02-21 12:00:00.000000

Sprint 362: Expand UserTier from 3 to 5 values (FREE, STARTER, PROFESSIONAL, TEAM, ENTERPRISE).
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: str | None = 'b2c3d4e5f6a7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # PostgreSQL: ALTER TYPE to add new enum values
    # SQLite: No-op (SQLite stores enums as VARCHAR, no type constraint)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE usertier ADD VALUE IF NOT EXISTS 'starter'")
        op.execute("ALTER TYPE usertier ADD VALUE IF NOT EXISTS 'team'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed without recreating the type.
    # This is a non-destructive addition, so downgrade is a no-op.
    pass
