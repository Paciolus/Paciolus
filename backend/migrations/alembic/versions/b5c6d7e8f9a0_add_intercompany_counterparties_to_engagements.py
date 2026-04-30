"""add intercompany_counterparties to engagements

Revision ID: b5c6d7e8f9a0
Revises: a3b4c5d6e7f8
Create Date: 2026-04-30 00:00:00.000000

Sprint 764 — Intercompany Layered Detection.
Adds engagement-scoped counterparty mapping for ISA 550 related-party
identification.  JSON-encoded ``{"<account_name>": "<counterparty>"}``
stored as Text (same pattern as ``ToolRun.flagged_accounts`` for
cross-DB portability).  Nullable: auditor populates explicitly; the
detection layer falls back to the heuristic separator parser when
absent.  Per-run request mappings override this engagement-level
default — see ``shared.intercompany_resolver``.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b5c6d7e8f9a0"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "engagements",
        sa.Column("intercompany_counterparties", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("engagements", "intercompany_counterparties")
