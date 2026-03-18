"""Add scheduler_locks table.

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-03-18

AUDIT-06 FIX 3: APScheduler Multi-Worker Duplication.
- scheduler_locks: DB-backed execution lock to prevent multi-worker job duplication
"""

import sqlalchemy as sa
from alembic import op

revision = "d8e9f0a1b2c3"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduler_locks",
        sa.Column("job_name", sa.String(100), primary_key=True),
        sa.Column("locked_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("locked_by", sa.String(100), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("scheduler_locks")
