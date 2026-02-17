"""Add server_default=func.now() to all timestamp columns

Revision ID: 0f1346198438
Revises: 679561a74cc1
Create Date: 2026-02-15 17:51:40.289051

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0f1346198438'
down_revision: str | None = '679561a74cc1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Tables and their timestamp columns that need server_default=func.now().
# ToolSession (tool_sessions) is excluded — already has server_default from Sprint 262.
_TARGETS: list[tuple[str, list[str]]] = [
    ("users", ["created_at", "updated_at"]),
    ("activity_logs", ["timestamp"]),
    ("clients", ["created_at", "updated_at"]),
    ("diagnostic_summaries", ["timestamp"]),
    ("email_verification_tokens", ["created_at"]),
    ("refresh_tokens", ["created_at"]),
    ("engagements", ["created_at", "updated_at"]),
    ("tool_runs", ["run_at"]),
    ("follow_up_items", ["created_at", "updated_at"]),
    ("follow_up_item_comments", ["created_at", "updated_at"]),
]


def upgrade() -> None:
    for table_name, columns in _TARGETS:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            for col in columns:
                batch_op.alter_column(
                    col,
                    existing_type=sa.DateTime(),
                    server_default=sa.func.now(),
                )


def downgrade() -> None:
    for table_name, columns in _TARGETS:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            for col in columns:
                batch_op.alter_column(
                    col,
                    existing_type=sa.DateTime(),
                    server_default=None,
                )
