"""Add upload_dedup table.

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-03-18

AUDIT-06 FIX 4: Upload Endpoint Deduplication.
- upload_dedup: SHA-256-based dedup key to prevent duplicate trial-balance submissions
"""

import sqlalchemy as sa
from alembic import op

revision = "e9f0a1b2c3d4"
down_revision = "d8e9f0a1b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "upload_dedup",
        sa.Column("dedup_key", sa.String(255), primary_key=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("upload_dedup")
