"""Add soft-delete columns (archived_at, archived_by, archive_reason) — Sprint 345

Phase XLVI: Audit History Immutability.
Adds 3 nullable columns + index on archived_at to 5 audit-trail tables:
  - activity_logs
  - diagnostic_summaries
  - tool_runs
  - follow_up_items
  - follow_up_item_comments

All columns are nullable with no default — existing rows stay active (NULL = active).

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = [
    "activity_logs",
    "diagnostic_summaries",
    "tool_runs",
    "follow_up_items",
    "follow_up_item_comments",
]


def upgrade() -> None:
    for table_name in _TABLES:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(
                sa.Column("archived_at", sa.DateTime(), nullable=True)
            )
            batch_op.add_column(
                sa.Column("archived_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True)
            )
            batch_op.add_column(
                sa.Column("archive_reason", sa.String(255), nullable=True)
            )
            batch_op.create_index(
                f"ix_{table_name}_archived_at", ["archived_at"]
            )


def downgrade() -> None:
    for table_name in reversed(_TABLES):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_index(f"ix_{table_name}_archived_at")
            batch_op.drop_column("archive_reason")
            batch_op.drop_column("archived_by")
            batch_op.drop_column("archived_at")
