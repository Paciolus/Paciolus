"""Add uncorrected_misstatements table.

Revision ID: a3b4c5d6e7f8
Revises: f2a8e7d6c5b4
Create Date: 2026-04-26

Sprint 729a (ISA 450): persisted SUM schedule line items —
source classification, F/S impact (signed), CPA disposition,
notes. Aggregation is computed at read time.
"""

import sqlalchemy as sa
from alembic import op

revision = "a3b4c5d6e7f8"
down_revision = "f2a8e7d6c5b4"
branch_labels = None
depends_on = None


_SOURCE_TYPES = ("adjusting_entry_passed", "sample_projection", "known_error")
_CLASSIFICATIONS = ("factual", "judgmental", "projected")
_DISPOSITIONS = (
    "not_yet_reviewed",
    "auditor_proposes_correction",
    "auditor_accepts_as_immaterial",
)


def upgrade() -> None:
    op.create_table(
        "uncorrected_misstatements",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "engagement_id",
            sa.Integer(),
            sa.ForeignKey("engagements.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "source_type",
            sa.Enum(*_SOURCE_TYPES, name="misstatementsourcetype"),
            nullable=False,
            index=True,
        ),
        sa.Column("source_reference", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "accounts_affected_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "classification",
            sa.Enum(*_CLASSIFICATIONS, name="misstatementclassification"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "fs_impact_net_income",
            sa.Numeric(19, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "fs_impact_net_assets",
            sa.Numeric(19, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "cpa_disposition",
            sa.Enum(*_DISPOSITIONS, name="misstatementdisposition"),
            nullable=False,
            server_default="not_yet_reviewed",
            index=True,
        ),
        sa.Column("cpa_notes", sa.Text(), nullable=True),
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
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("archived_by", sa.Integer(), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
    )

    op.create_index(
        "ix_uncorrected_misstatements_eng_disposition",
        "uncorrected_misstatements",
        ["engagement_id", "cpa_disposition"],
    )
    op.create_index(
        "ix_uncorrected_misstatements_eng_classification",
        "uncorrected_misstatements",
        ["engagement_id", "classification"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_uncorrected_misstatements_eng_classification",
        table_name="uncorrected_misstatements",
    )
    op.drop_index(
        "ix_uncorrected_misstatements_eng_disposition",
        table_name="uncorrected_misstatements",
    )
    op.drop_table("uncorrected_misstatements")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="misstatementdisposition").drop(bind, checkfirst=True)
        sa.Enum(name="misstatementclassification").drop(bind, checkfirst=True)
        sa.Enum(name="misstatementsourcetype").drop(bind, checkfirst=True)
