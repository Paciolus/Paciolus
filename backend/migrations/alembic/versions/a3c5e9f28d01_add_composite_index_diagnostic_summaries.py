"""Add composite index ix_diagnostic_summaries_client_user_period

Sprint 280: Optimize diagnostic_summaries lookups by (client_id, user_id, period_date).

Revision ID: a3c5e9f28d01
Revises: 0f1346198438
Create Date: 2026-02-17 12:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a3c5e9f28d01'
down_revision: str | None = '0f1346198438'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_diagnostic_summaries_client_user_period",
        "diagnostic_summaries",
        ["client_id", "user_id", "period_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_diagnostic_summaries_client_user_period",
        table_name="diagnostic_summaries",
    )
