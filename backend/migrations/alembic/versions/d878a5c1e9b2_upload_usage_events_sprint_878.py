"""Sprint 878: upload_usage_events — the server-side upload allowance ledger.

Revision ID: d878a5c1e9b2
Revises: c853a1f0e2d4
Create Date: 2026-11-16

WHY
---
A user without an active metered subscription (Free, or a lapsed plan) was
metered by counting this month's unarchived ``activity_logs`` rows. The browser
writes those rows itself, in a request separate from the analysis, and "Clear
history" archives them - so skipping the call or clearing history reset the
allowance (review AZ-05). Each successful metered run now writes one row here,
from the server's success path, and no user-facing route touches the table.

NO BACKFILL. The ledger starts empty, so a Free user's count for the month of
the deploy restarts at zero once. The old count was not trustworthy enough to
carry over (it was whatever the browser had logged and not cleared).

Guarded with an inspector check, like ``c853a1f0e2d4``: a database built by
``create_all()`` may already have the table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d878a5c1e9b2"
down_revision: str | Sequence[str] | None = "c853a1f0e2d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "upload_usage_events"
_INDEX = "ix_upload_usage_events_user_consumed"


def _has_table(table: str) -> bool:
    return table in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _has_table(_TABLE):
        return
    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(length=50), nullable=True),
        sa.Column("consumed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(_INDEX, _TABLE, ["user_id", "consumed_at"], unique=False)


def downgrade() -> None:
    if _has_table(_TABLE):
        op.drop_index(_INDEX, table_name=_TABLE)
        op.drop_table(_TABLE)
