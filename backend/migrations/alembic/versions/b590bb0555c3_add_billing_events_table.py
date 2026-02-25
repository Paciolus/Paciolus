"""Add billing_events table for post-launch analytics.

Sprint 439: Creates append-only billing lifecycle event log.
Phase LX model (BillingEvent) was defined but never migrated.

Revision ID: b590bb0555c3
Revises: d9e0f1a2b3c4
Create Date: 2026-02-25
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b590bb0555c3"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None

# BillingEventType enum values (must match subscription_model.py)
_EVENT_TYPES = (
    "trial_started",
    "trial_converted",
    "trial_expired",
    "subscription_created",
    "subscription_upgraded",
    "subscription_downgraded",
    "subscription_canceled",
    "subscription_churned",
    "payment_failed",
    "payment_recovered",
)


def upgrade() -> None:
    # Create the enum type explicitly for PostgreSQL
    billing_event_type = sa.Enum(*_EVENT_TYPES, name="billingeventtype")

    op.create_table(
        "billing_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("event_type", billing_event_type, nullable=False, index=True),
        sa.Column("tier", sa.String(20), nullable=True, index=True),
        sa.Column("interval", sa.String(10), nullable=True),
        sa.Column("seat_count", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("billing_events")

    # Drop the enum type on PostgreSQL (no-op on SQLite)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS billingeventtype")
