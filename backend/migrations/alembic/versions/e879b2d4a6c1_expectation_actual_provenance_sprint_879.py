"""Sprint 879b: where a captured expectation actual came from.

Revision ID: e879b2d4a6c1
Revises: d878a5c1e9b2
Create Date: 2026-11-16

WHY
---
Flux, multi-period and industry-ratio runs wrote each matching account's
balance into ``analytical_expectations.result_actual_value`` with no action
from the auditor (review DH-04). Runs now only propose actuals; the auditor
captures them. These columns record the capture: ``actual_source`` ("manual"
or the proposing tool), the proposing run, and who captured it when.

NO BACKFILL. Rows captured before this sprint keep their values with a NULL
source — the database cannot tell an auto-saved actual from a typed one.

Guarded with an inspector check, like ``d878a5c1e9b2``: a database built by
``create_all()`` may already have the columns.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e879b2d4a6c1"
down_revision: str | Sequence[str] | None = "d878a5c1e9b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "analytical_expectations"
_FK_RUN = "fk_analytical_expectations_actual_source_tool_run_id"
_FK_USER = "fk_analytical_expectations_actual_captured_by"


def _columns() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(_TABLE)}


def upgrade() -> None:
    existing = _columns()
    with op.batch_alter_table(_TABLE) as batch:
        if "actual_source" not in existing:
            batch.add_column(sa.Column("actual_source", sa.String(length=40), nullable=True))
        if "actual_source_tool_run_id" not in existing:
            batch.add_column(sa.Column("actual_source_tool_run_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(_FK_RUN, "tool_runs", ["actual_source_tool_run_id"], ["id"], ondelete="SET NULL")
        if "actual_captured_at" not in existing:
            batch.add_column(sa.Column("actual_captured_at", sa.DateTime(), nullable=True))
        if "actual_captured_by" not in existing:
            batch.add_column(sa.Column("actual_captured_by", sa.Integer(), nullable=True))
            batch.create_foreign_key(_FK_USER, "users", ["actual_captured_by"], ["id"])


def downgrade() -> None:
    existing = _columns()
    with op.batch_alter_table(_TABLE) as batch:
        if "actual_captured_by" in existing:
            batch.drop_constraint(_FK_USER, type_="foreignkey")
            batch.drop_column("actual_captured_by")
        if "actual_captured_at" in existing:
            batch.drop_column("actual_captured_at")
        if "actual_source_tool_run_id" in existing:
            batch.drop_constraint(_FK_RUN, type_="foreignkey")
            batch.drop_column("actual_source_tool_run_id")
        if "actual_source" in existing:
            batch.drop_column("actual_source")
