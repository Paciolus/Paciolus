"""Add seat_version column to subscriptions table.

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-03-18

AUDIT-06 FIX 1: Seat Mutation Race Condition.
- seat_version: incremented on each seat mutation, used for Stripe idempotency keys
"""

import sqlalchemy as sa
from alembic import op

revision = "c7d8e9f0a1b2"
down_revision = "b6c7d8e9f0a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.add_column(sa.Column("seat_version", sa.Integer(), nullable=False, server_default=sa.text("0")))


def downgrade() -> None:
    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.drop_column("seat_version")
