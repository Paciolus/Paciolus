"""expand toolname enum with sprint 689 tools

Revision ID: d8b945d0b4e5
Revises: b5c6d7e8f9a0
Create Date: 2026-10-20 13:43:51.667032

Sprint 787. Adds the six Sprint-689 tool labels, plus two older members whose labels were
never added at all: STATISTICAL_SAMPLING (missed by the Sprint 278-era tool) and
FLUX_ANALYSIS (added as the lowercase slug by Sprint 308's f8a3d1c09b72 rather than the
member name SQLAlchemy binds).

Sprint 689 expanded the tool catalog 12 -> 18 and Sprint 717 reconciled the
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


# Labels must be the enum MEMBER NAMES, not the slugs.
#
# `ToolRun.tool_name` is `Enum(ToolName)` with no `values_callable`, so SQLAlchemy binds
# `.name` — it sends 'SOD_CHECKER', never 'sod_checker'. The baseline migration got this
# right (`sa.Enum('TRIAL_BALANCE', 'MULTI_PERIOD', ...)`), and the first draft of this
# migration got it wrong by copying the slug list from tools_registry.
#
# Sprint 308's f8a3d1c09b72 made the same mistake and it is still live: it added
# 'flux_analysis' lowercase, so on any PostgreSQL database with that label a flux_analysis
# tool run cannot be inserted — the ORM sends 'FLUX_ANALYSIS', which is not a label. That
# is filed separately as Sprint 741c; this migration does not repair it, because repairing
# an enum label requires knowing which labels the target database actually has.
NEW_TOOL_NAMES: tuple[str, ...] = (
    # Sprint 689's six tools — the reason this migration exists.
    "SOD_CHECKER",
    "INTERCOMPANY_ELIMINATION",
    "W2_RECONCILIATION",
    "FORM_1099",
    "BOOK_TO_TAX",
    "CASH_FLOW_PROJECTOR",
    # Two older members whose labels were never added, found by
    # tests/test_toolname_catalog_parity.py. Both are reachable today —
    # routes/sampling.py and routes/audit_flux.py each call maybe_record_tool_run — so on
    # a PostgreSQL database built from this chain, recording either run fails with 22P02.
    #
    # STATISTICAL_SAMPLING: the baseline created `toolname` with eleven labels and the
    #   Sprint 278-era sampling tool never added its own.
    # FLUX_ANALYSIS: Sprint 308's f8a3d1c09b72 added the *slug* 'flux_analysis' instead of
    #   the member name. The stale lowercase label stays behind unused; dropping it means
    #   recreating the type, which is Sprint 741c and needs a read of the live schema.
    "STATISTICAL_SAMPLING",
    "FLUX_ANALYSIS",
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
