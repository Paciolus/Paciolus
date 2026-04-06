"""Add passcode_hash and single_use columns to export_shares.

Sprint 593: Share-Link Security Hardening.

Revision ID: b2c3d4e5f6a7
Revises: f0a1b2c3d4e5
Create Date: 2026-04-06
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "f0a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "export_shares",
        sa.Column("passcode_hash", sa.String(64), nullable=True),
    )
    op.add_column(
        "export_shares",
        sa.Column("single_use", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("export_shares", "single_use")
    op.drop_column("export_shares", "passcode_hash")
