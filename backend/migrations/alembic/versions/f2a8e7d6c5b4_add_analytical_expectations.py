"""Add analytical_expectations table.

Revision ID: f2a8e7d6c5b4
Revises: e1a2b3c4d5f6
Create Date: 2026-04-26

Sprint 728a (ISA 520): persisted workpaper for analytical-procedure
expectations — target, expected value/range, precision threshold,
corroboration basis + tags, CPA notes, and (once captured) the actual
result + variance + within/exceeds status.

Schema mirrors follow_up_items.py (engagement-scoped, soft-deletable).
"""

import sqlalchemy as sa
from alembic import op

revision = "f2a8e7d6c5b4"
down_revision = "e1a2b3c4d5f6"
branch_labels = None
depends_on = None


_TARGET_TYPES = ("account", "balance", "ratio", "flux_line")
_RESULT_STATUSES = ("not_evaluated", "within_threshold", "exceeds_threshold")


def upgrade() -> None:
    op.create_table(
        "analytical_expectations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "engagement_id",
            sa.Integer(),
            sa.ForeignKey("engagements.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "procedure_target_type",
            sa.Enum(*_TARGET_TYPES, name="expectationtargettype"),
            nullable=False,
            index=True,
        ),
        sa.Column("procedure_target_label", sa.String(length=200), nullable=False),
        sa.Column("expected_value", sa.Numeric(19, 2), nullable=True),
        sa.Column("expected_range_low", sa.Numeric(19, 2), nullable=True),
        sa.Column("expected_range_high", sa.Numeric(19, 2), nullable=True),
        sa.Column("precision_threshold_amount", sa.Numeric(19, 2), nullable=True),
        sa.Column("precision_threshold_percent", sa.Float(), nullable=True),
        sa.Column("corroboration_basis_text", sa.Text(), nullable=False),
        sa.Column(
            "corroboration_tags_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("cpa_notes", sa.Text(), nullable=True),
        sa.Column("result_actual_value", sa.Numeric(19, 2), nullable=True),
        sa.Column("result_variance_amount", sa.Numeric(19, 2), nullable=True),
        sa.Column(
            "result_status",
            sa.Enum(*_RESULT_STATUSES, name="expectationresultstatus"),
            nullable=False,
            server_default="not_evaluated",
            index=True,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_by",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # SoftDeleteMixin columns
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("archived_by", sa.Integer(), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
    )

    op.create_index(
        "ix_analytical_expectations_eng_status",
        "analytical_expectations",
        ["engagement_id", "result_status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analytical_expectations_eng_status",
        table_name="analytical_expectations",
    )
    op.drop_table("analytical_expectations")

    # Drop the enums (PostgreSQL only — SQLite is permissive)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="expectationresultstatus").drop(bind, checkfirst=True)
        sa.Enum(name="expectationtargettype").drop(bind, checkfirst=True)
