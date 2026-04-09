"""Sprint 591: Add dunning_episodes table for failed payment workflow.

Revision ID: 591a_dunning
Revises: 590a_superadmin
Create Date: 2026-03-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "591a_dunning"
down_revision: str | None = "590a_superadmin"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dunning_episodes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=False, index=True),
        sa.Column("org_id", sa.Integer(), nullable=True, index=True),
        sa.Column("stripe_invoice_id", sa.String(255), nullable=True),
        sa.Column(
            "state",
            sa.Enum(
                "first_attempt_failed",
                "second_attempt_failed",
                "third_attempt_failed",
                "grace_period",
                "canceled",
                "resolved",
                name="dunningstate",
            ),
            nullable=False,
        ),
        sa.Column("failure_count", sa.Integer(), nullable=False, default=1),
        sa.Column("first_failed_at", sa.DateTime(), nullable=False),
        sa.Column("last_failed_at", sa.DateTime(), nullable=False),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column(
            "resolution",
            sa.Enum("paid", "canceled", "manual_override", name="dunningresolution"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_index("ix_dunning_sub_state", "dunning_episodes", ["subscription_id", "state"])
    op.create_index("ix_dunning_state_last_failed", "dunning_episodes", ["state", "last_failed_at"])


def downgrade() -> None:
    op.drop_index("ix_dunning_state_last_failed", table_name="dunning_episodes")
    op.drop_index("ix_dunning_sub_state", table_name="dunning_episodes")
    op.drop_table("dunning_episodes")
