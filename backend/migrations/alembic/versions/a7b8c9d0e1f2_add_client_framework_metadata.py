"""Add reporting framework metadata to clients table.

Sprint 1: Metadata Foundation — reporting_framework, entity_type,
jurisdiction_country, jurisdiction_state columns for deterministic
FASB/GASB framework resolution.

Revision ID: a7b8c9d0e1f2
Revises: d5e6f7a8b9c0
Create Date: 2026-02-24
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "a7b8c9d0e1f2"
down_revision: str = "d5e6f7a8b9c0"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    with op.batch_alter_table("clients") as batch_op:
        batch_op.add_column(
            sa.Column(
                "reporting_framework",
                sa.Enum("auto", "fasb", "gasb", name="reportingframework"),
                nullable=False,
                server_default="auto",
            )
        )
        batch_op.add_column(
            sa.Column(
                "entity_type",
                sa.Enum("for_profit", "nonprofit", "governmental", "other", name="entitytype"),
                nullable=False,
                server_default="other",
            )
        )
        batch_op.add_column(
            sa.Column(
                "jurisdiction_country",
                sa.String(2),
                nullable=False,
                server_default="US",
            )
        )
        batch_op.add_column(
            sa.Column(
                "jurisdiction_state",
                sa.String(50),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("clients") as batch_op:
        batch_op.drop_column("jurisdiction_state")
        batch_op.drop_column("jurisdiction_country")
        batch_op.drop_column("entity_type")
        batch_op.drop_column("reporting_framework")
