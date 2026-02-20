"""Float to Numeric(19,2) for monetary columns — Sprint 341

Converts 17 monetary Float columns to Numeric(19,2) across 3 tables:
- ActivityLog: total_debits, total_credits, materiality_threshold
- DiagnosticSummary: 10 category totals + total_debits, total_credits, materiality_threshold
- Engagement: materiality_amount

Non-monetary columns (ratios, factors, scores, percentages, booleans, counts)
intentionally remain as Float.

Revision ID: a1b2c3d4e5f6
Revises: dd9b8bff6e0c
Create Date: 2026-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'dd9b8bff6e0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- ActivityLog: 3 monetary columns ---
    with op.batch_alter_table("activity_logs") as batch_op:
        batch_op.alter_column("total_debits",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2),
                              existing_nullable=False)
        batch_op.alter_column("total_credits",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2),
                              existing_nullable=False)
        batch_op.alter_column("materiality_threshold",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2),
                              existing_nullable=False)

    # --- DiagnosticSummary: 13 monetary columns ---
    with op.batch_alter_table("diagnostic_summaries") as batch_op:
        # Balance Sheet totals
        batch_op.alter_column("total_assets",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        batch_op.alter_column("current_assets",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        batch_op.alter_column("inventory",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        batch_op.alter_column("total_liabilities",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        batch_op.alter_column("current_liabilities",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        batch_op.alter_column("total_equity",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        # Income Statement totals
        batch_op.alter_column("total_revenue",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        batch_op.alter_column("cost_of_goods_sold",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        batch_op.alter_column("total_expenses",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        batch_op.alter_column("operating_expenses",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        # Diagnostic metadata
        batch_op.alter_column("total_debits",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        batch_op.alter_column("total_credits",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))
        batch_op.alter_column("materiality_threshold",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2))

    # --- Engagement: 1 monetary column ---
    with op.batch_alter_table("engagements") as batch_op:
        batch_op.alter_column("materiality_amount",
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=19, scale=2),
                              existing_nullable=True)


def downgrade() -> None:
    # --- Engagement ---
    with op.batch_alter_table("engagements") as batch_op:
        batch_op.alter_column("materiality_amount",
                              existing_type=sa.Numeric(precision=19, scale=2),
                              type_=sa.Float(),
                              existing_nullable=True)

    # --- DiagnosticSummary ---
    with op.batch_alter_table("diagnostic_summaries") as batch_op:
        for col in ["total_assets", "current_assets", "inventory",
                     "total_liabilities", "current_liabilities", "total_equity",
                     "total_revenue", "cost_of_goods_sold", "total_expenses",
                     "operating_expenses", "total_debits", "total_credits",
                     "materiality_threshold"]:
            batch_op.alter_column(col,
                                  existing_type=sa.Numeric(precision=19, scale=2),
                                  type_=sa.Float())

    # --- ActivityLog ---
    with op.batch_alter_table("activity_logs") as batch_op:
        for col in ["total_debits", "total_credits", "materiality_threshold"]:
            batch_op.alter_column(col,
                                  existing_type=sa.Numeric(precision=19, scale=2),
                                  type_=sa.Float(),
                                  existing_nullable=False)
