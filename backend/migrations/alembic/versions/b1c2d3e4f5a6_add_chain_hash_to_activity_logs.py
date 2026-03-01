"""add chain_hash to activity_logs

Revision ID: b1c2d3e4f5a6
Revises: f8a3d1c09b72
Create Date: 2026-03-01 00:00:00.000000

Sprint 461 — Cryptographic Audit Log Chaining (SOC 2 CC7.4).
Adds an HMAC-SHA512 chain hash column to activity_logs for tamper-resistant
evidence. Existing rows will have NULL (chain starts from the first new record).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "f8a3d1c09b72"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "activity_logs",
        sa.Column("chain_hash", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_activity_logs_chain_hash",
        "activity_logs",
        ["chain_hash"],
    )


def downgrade() -> None:
    op.drop_index("ix_activity_logs_chain_hash", table_name="activity_logs")
    op.drop_column("activity_logs", "chain_hash")
