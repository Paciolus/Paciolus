"""Add session metadata columns to refresh_tokens table.

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-03-18

AUDIT-02 FIX 2: Session Inventory & Revocation.
- last_used_at: stamped on each successful token rotation
- user_agent: captured at token creation, carried forward on rotation
- ip_address: captured at token creation, carried forward on rotation
"""

import sqlalchemy as sa
from alembic import op

revision = "b6c7d8e9f0a1"
down_revision = "a5b6c7d8e9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.add_column(sa.Column("last_used_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("user_agent", sa.String(512), nullable=True))
        batch_op.add_column(sa.Column("ip_address", sa.String(45), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.drop_column("ip_address")
        batch_op.drop_column("user_agent")
        batch_op.drop_column("last_used_at")
