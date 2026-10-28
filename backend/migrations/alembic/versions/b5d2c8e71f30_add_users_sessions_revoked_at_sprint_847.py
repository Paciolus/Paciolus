"""Sprint 847: add users.sessions_revoked_at (access-token revocation).

Revision ID: b5d2c8e71f30
Revises: a8c4e2f19d07
Create Date: 2026-10-27

WHY
---
Logging out of every session ("revoke all sessions") and changing the account
email revoked refresh tokens only; an already-issued access JWT stayed valid
until it expired (security review L3, M4). ``require_current_user`` now
rejects any token whose ``iat`` is earlier than this timestamp, mirroring the
Sprint 199 ``password_changed_at`` / ``pwd_at`` check. NULL means "never
revoked", so no backfill is needed.

Guarded with an inspector check, following ``f3b81d6e2a47``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b5d2c8e71f30"
down_revision: str | Sequence[str] | None = "a8c4e2f19d07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if not _has_column("users", "sessions_revoked_at"):
        with op.batch_alter_table("users", schema=None) as batch_op:
            batch_op.add_column(sa.Column("sessions_revoked_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    if _has_column("users", "sessions_revoked_at"):
        with op.batch_alter_table("users", schema=None) as batch_op:
            batch_op.drop_column("sessions_revoked_at")
