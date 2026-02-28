"""add dpa_accepted_at and dpa_version to subscriptions

Revision ID: a4b5c6d7e8f9
Revises: ecda5f408617
Create Date: 2026-02-27 00:00:00.000000

Sprint 459 — PI1.3 / C2.1: DPA Acceptance Workflow.
Records when a Team/Organization customer accepted the Data Processing Addendum
and which version they accepted.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a4b5c6d7e8f9"
down_revision = "ecda5f408617"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("dpa_accepted_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("dpa_version", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "dpa_version")
    op.drop_column("subscriptions", "dpa_accepted_at")
