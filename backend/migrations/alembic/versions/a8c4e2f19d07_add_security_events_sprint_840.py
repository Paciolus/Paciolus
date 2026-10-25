"""Sprint 840: add security_events (failed logins, lockouts, token reuse).

Revision ID: a8c4e2f19d07
Revises: f3b81d6e2a47
Create Date: 2026-10-24

WHY
---
Security events went to an in-memory list per worker that nothing read, so
they were lost on every restart (claims review S5). ``security_utils.
log_secure_operation`` now writes the events in ``PERSISTED_EVENTS`` here.
No customer financial data: event type, user ID, hashed IP, short detail.

Guarded with an inspector check, following ``f3b81d6e2a47``: a database whose
schema came from ``create_all()`` may already have the table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a8c4e2f19d07"
down_revision: str | Sequence[str] | None = "f3b81d6e2a47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(table: str) -> bool:
    return table in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _has_table("security_events"):
        return
    op.create_table(
        "security_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("details", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_security_events_created_at"), "security_events", ["created_at"], unique=False)
    op.create_index(op.f("ix_security_events_event_type"), "security_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_security_events_user_id"), "security_events", ["user_id"], unique=False)


def downgrade() -> None:
    if not _has_table("security_events"):
        return
    op.drop_index(op.f("ix_security_events_user_id"), table_name="security_events")
    op.drop_index(op.f("ix_security_events_event_type"), table_name="security_events")
    op.drop_index(op.f("ix_security_events_created_at"), table_name="security_events")
    op.drop_table("security_events")
