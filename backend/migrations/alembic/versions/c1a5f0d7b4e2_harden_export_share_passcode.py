"""Harden export-share passcode: widen hash column, add brute-force columns.

Security hardening (2026-04-20):
  * Widen ``passcode_hash`` from VARCHAR(64) (SHA-256 hex) to VARCHAR(255)
    so it can hold bcrypt output (~60 chars).  Existing rows keep their
    legacy SHA-256 value; the application refuses to verify legacy hashes
    at runtime and returns a 403 telling owners to re-create the share.
  * Add ``passcode_failed_attempts`` (INTEGER NOT NULL DEFAULT 0) and
    ``passcode_locked_until`` (TIMESTAMP NULL) for per-token brute-force
    throttling.

Shares are ephemeral (24-48h TTL) so no data backfill is required —
legacy-hashed shares that are still alive at deploy time will simply
return 403 and their owners can re-issue.

Revision ID: c1a5f0d7b4e2
Revises: f7b3c91a04e2
Create Date: 2026-04-20

Chain note: the file originally set ``down_revision = "f8a3d1c09b72"`` —
but that revision is a branchpoint from 2026-Q1 whose downstream chain
was already consumed by the ``dd9b8bff6e0c`` mergepoint.  Descending
from it would have produced a second alembic head parallel to the
Sprint 594 email-normalize chain (head ``f7b3c91a04e2``).  Corrected on
2026-04-21 audit: re-parented to descend directly from the actual head
``f7b3c91a04e2``.  The migration body is independent of user.email
normalization, so the re-parenting is semantically safe.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c1a5f0d7b4e2"
down_revision = "f7b3c91a04e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # 1. Widen passcode_hash column.
    # SQLite ALTER COLUMN is only partially supported; use batch mode so
    # the column is recreated with the new type.  PostgreSQL supports the
    # direct ALTER path.
    if dialect == "sqlite":
        with op.batch_alter_table("export_shares") as batch_op:
            batch_op.alter_column(
                "passcode_hash",
                existing_type=sa.String(64),
                type_=sa.String(255),
                existing_nullable=True,
            )
    else:
        op.alter_column(
            "export_shares",
            "passcode_hash",
            existing_type=sa.String(64),
            type_=sa.String(255),
            existing_nullable=True,
        )

    # 2. Add brute-force throttle columns.
    op.add_column(
        "export_shares",
        sa.Column(
            "passcode_failed_attempts",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "export_shares",
        sa.Column("passcode_locked_until", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("export_shares", "passcode_locked_until")
    op.drop_column("export_shares", "passcode_failed_attempts")

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("export_shares") as batch_op:
            batch_op.alter_column(
                "passcode_hash",
                existing_type=sa.String(255),
                type_=sa.String(64),
                existing_nullable=True,
            )
    else:
        op.alter_column(
            "export_shares",
            "passcode_hash",
            existing_type=sa.String(255),
            type_=sa.String(64),
            existing_nullable=True,
        )
