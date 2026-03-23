"""Clean stale ORGANIZATION tier values to FREE.

Revision ID: b1c2d3e4f5a6
Revises: 418d00cd85ae
Create Date: 2026-03-23

Sprint 570 / DEC F-002: Prior pricing structure used ORGANIZATION as a tier.
Current tiers are FREE, SOLO, PROFESSIONAL, ENTERPRISE. Any leftover
ORGANIZATION rows are migrated to FREE.
"""

from alembic import op

revision = "b1c2d3e4f5a6"
down_revision = "418d00cd85ae"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE users SET tier = 'free' WHERE tier = 'organization'")


def downgrade() -> None:
    # No reverse — ORGANIZATION is no longer a valid tier.
    # Users who were ORGANIZATION have no way to be distinguished after migration.
    pass
