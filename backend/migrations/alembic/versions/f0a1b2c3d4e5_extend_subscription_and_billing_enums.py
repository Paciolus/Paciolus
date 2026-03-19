"""Extend SubscriptionStatus and BillingEventType enums.

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-03-18

AUDIT-08-F1: Add incomplete, incomplete_expired, unpaid, paused to subscriptionstatus.
AUDIT-08-F4/F5/F6: Add payment_succeeded, invoice_created, dispute_* to billingeventtype.
Also adds trial_ending which was in the model but missing from the DB enum.
"""

from alembic import op

revision = "f0a1b2c3d4e5"
down_revision = "e9f0a1b2c3d4"
branch_labels = None
depends_on = None

# New SubscriptionStatus values
_NEW_SUB_STATUSES = ["incomplete", "incomplete_expired", "unpaid", "paused"]

# New BillingEventType values (includes trial_ending which was never migrated)
_NEW_EVENT_TYPES = [
    "trial_ending",
    "payment_succeeded",
    "invoice_created",
    "dispute_created",
    "dispute_resolved_won",
    "dispute_resolved_lost",
    "dispute_closed_other",
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # SQLite: enums are stored as VARCHAR strings, no type changes needed
        return

    # Extend subscriptionstatus enum
    for value in _NEW_SUB_STATUSES:
        op.execute(f"ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS '{value}'")

    # Extend billingeventtype enum
    for value in _NEW_EVENT_TYPES:
        op.execute(f"ALTER TYPE billingeventtype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # PostgreSQL does not support removing values from an enum without
    # full type reconstruction. Since these statuses may already be in use,
    # downgrade is a no-op to avoid data loss. Manual cleanup required.
    pass
