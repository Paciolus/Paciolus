"""add chain_hash to activity_logs

Revision ID: b7c8d9e0f1a2
Revises: a4b5c6d7e8f9
Create Date: 2026-02-28 00:00:00.000000

Sprint 461 — CC7.4 / Audit Logging §5.4: Cryptographic audit log chaining.
HMAC-SHA256 hash chain for tamper-evident audit trail.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7c8d9e0f1a2"
down_revision = "a4b5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "activity_logs",
        sa.Column("chain_hash", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_activity_logs_chain_hash",
        "activity_logs",
        ["chain_hash"],
    )


def downgrade() -> None:
    op.drop_index("ix_activity_logs_chain_hash", table_name="activity_logs")
    op.drop_column("activity_logs", "chain_hash")
