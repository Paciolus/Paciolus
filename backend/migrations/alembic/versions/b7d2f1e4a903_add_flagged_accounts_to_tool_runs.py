"""add flagged_accounts to tool_runs

Revision ID: b7d2f1e4a903
Revises: a3c5e9f28d01
Create Date: 2026-02-17
"""
import sqlalchemy as sa
from alembic import op

revision = "b7d2f1e4a903"
down_revision = "a3c5e9f28d01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tool_runs") as batch_op:
        batch_op.add_column(
            sa.Column("flagged_accounts", sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("tool_runs") as batch_op:
        batch_op.drop_column("flagged_accounts")
