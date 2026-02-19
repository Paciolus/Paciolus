"""add flux_analysis to ToolName enum

Revision ID: f8a3d1c09b72
Revises: ea6c8f7cc976
Create Date: 2026-02-19 12:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f8a3d1c09b72'
down_revision: str | None = 'ea6c8f7cc976'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Sprint 308: Add FLUX_ANALYSIS to ToolName enum
    # PostgreSQL: ALTER TYPE to add new enum value
    # SQLite: No-op (SQLite stores enums as VARCHAR, no type constraint)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE toolname ADD VALUE IF NOT EXISTS 'flux_analysis'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed without recreating the type.
    # This is a non-destructive addition, so downgrade is a no-op.
    pass
