"""Add object_key column + relax export_data to nullable on export_shares.

Sprint 611: ExportShare Object Store Migration (R2).

The ``export_data`` LargeBinary column held up to 50 MB per shared export
in primary Neon Postgres — 20 concurrent shares ≈ 1 GB, against a 10 GB
Neon Launch tier cap, and the bytes shipped in every DB backup.
Sprint 611 moves the blobs to the ``paciolus-exports`` R2 bucket and
keeps only an object key on the DB row.

Schema invariant after this migration:
  * ``object_key IS NOT NULL XOR export_data IS NOT NULL``
  * New rows written by the route will set exactly one.
  * The ``export_data`` column is retained (nullable) so that in-flight
    shares created before the deploy keep resolving until they age out.
    A follow-up migration can drop the column once the longest TTL
    (48h Enterprise) has elapsed since the route flip.

Revision ID: e1a2b3c4d5f6
Revises: c1a5f0d7b4e2
Create Date: 2026-04-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e1a2b3c4d5f6"
down_revision = "c1a5f0d7b4e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "export_shares",
        sa.Column("object_key", sa.String(128), nullable=True),
    )

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("export_shares") as batch_op:
            batch_op.alter_column(
                "export_data",
                existing_type=sa.LargeBinary(),
                nullable=True,
            )
    else:
        op.alter_column(
            "export_shares",
            "export_data",
            existing_type=sa.LargeBinary(),
            nullable=True,
        )


def downgrade() -> None:
    # Backfill any R2-only rows into export_data is not possible from the
    # migration context (no R2 creds in Alembic); the column is only
    # re-tightened to NOT NULL if no R2-only rows exist.  Callers that
    # genuinely need to roll back should purge R2-only rows first.
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("export_shares") as batch_op:
            batch_op.alter_column(
                "export_data",
                existing_type=sa.LargeBinary(),
                nullable=False,
            )
    else:
        op.alter_column(
            "export_shares",
            "export_data",
            existing_type=sa.LargeBinary(),
            nullable=False,
        )

    op.drop_column("export_shares", "object_key")
