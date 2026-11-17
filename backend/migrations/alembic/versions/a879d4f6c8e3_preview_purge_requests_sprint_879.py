"""Sprint 879d: preview_purge_requests — purge a user's previews in every worker.

Revision ID: a879d4f6c8e3
Revises: f879c3e5b7d2
Create Date: 2026-11-16

WHY
---
The preview cache lives in each Gunicorn worker's memory (CEO decision: no
Redis, no disk). Logout or account deletion handled by one worker purges that
worker at once and records a row here; every worker's sweeper drops the user's
older previews on its next tick (review DH-07). Rows are deleted by the
sweeper once older than the cache lifetime.

User id and time only. No foreign key: a deleted account's request must
outlive its user row for up to 10 minutes.

Guarded with an inspector check, like ``d878a5c1e9b2``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a879d4f6c8e3"
down_revision: str | Sequence[str] | None = "f879c3e5b7d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "preview_purge_requests"
_INDEX = "ix_preview_purge_requests_requested_at"


def _has_table(table: str) -> bool:
    return table in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _has_table(_TABLE):
        return
    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("requested_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(_INDEX, _TABLE, ["requested_at"], unique=False)


def downgrade() -> None:
    if _has_table(_TABLE):
        op.drop_index(_INDEX, table_name=_TABLE)
        op.drop_table(_TABLE)
