"""Sprint 887: add tool_runs.flag_count.

Revision ID: c3e7a1f9d524
Revises: b9d3f6a2c418
Create Date: 2026-11-20

The anomaly summary described a tool as "clean" when it had a run and no
follow-up item, failed runs included (review OUT-20). Each run now records how
many items it flagged, so the summary can say "no exceptions flagged" only for a
successful run that flagged nothing. Nullable: runs recorded before this column,
and tools without a flag count, show "results unavailable". A count is metadata,
not financial data (Zero-Storage).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3e7a1f9d524"
down_revision: str | Sequence[str] | None = "b9d3f6a2c418"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("tool_runs") as batch_op:
        batch_op.add_column(sa.Column("flag_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tool_runs") as batch_op:
        batch_op.drop_column("flag_count")
