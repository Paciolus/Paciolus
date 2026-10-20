"""expand toolname enum with sprint 689 tools

Revision ID: d8b945d0b4e5
Revises: b5c6d7e8f9a0
Create Date: 2026-10-20 13:43:51.667032

Sprint 787. Sprint 689 expanded the tool catalog 12 -> 18 and Sprint 717 reconciled the
frontend ledger, but `ToolName` was never touched — so `tool_runs.tool_name` could not
hold a run of any of the six newer tools. On PostgreSQL that column is a native enum
type, so the type needs the values added before any insert can succeed; on SQLite the
column is VARCHAR with no type constraint, which is why every local and CI test passed
while production would have rejected the insert.

Mirrors the pattern established by f8a3d1c09b72 (flux_analysis, Sprint 308).

`ALTER TYPE ... ADD VALUE` cannot run inside a transaction block on PostgreSQL before
12. Production and CI are both on PostgreSQL 15, where it is transaction-safe, so no
autocommit juggling is needed here.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d8b945d0b4e5"
down_revision: str | None = "b5c6d7e8f9a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Values must match tools_registry.py slugs, which is what
# shared/tool_run_recorder.py passes to ToolName(...).
NEW_TOOL_NAMES: tuple[str, ...] = (
    "sod_checker",
    "intercompany_elimination",
    "w2_reconciliation",
    "form_1099",
    "book_to_tax",
    "cash_flow_projector",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for value in NEW_TOOL_NAMES:
        op.execute(f"ALTER TYPE toolname ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # PostgreSQL cannot drop an enum value without recreating the type and rewriting
    # every dependent column. These are non-destructive additions, so the downgrade is
    # deliberately a no-op — matching f8a3d1c09b72.
    pass
