"""Sprint 880b: export_shares.upload_pending — a durable record before a share's bytes are stored.

Revision ID: b880e5a7d9f1
Revises: a879d4f6c8e3
Create Date: 2026-11-16

WHY
---
Share creation uploaded the file to R2 and then committed the row. When the
commit failed, the handler's clean-up delete could fail too, leaving a file no
row pointed at, which the purge could never find (review DH-09). The row is now
committed first with ``upload_pending`` true; it is cleared once the upload has
landed. A pending row is never served or listed, and the purge deletes its file
(if any) and then the row once it is older than a short grace period, so a crash
at any point leaves a record that leads to the file.

Existing rows were all stored before they were committed: the server default
(false) covers them.

Guarded with an inspector check, like ``d878a5c1e9b2``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b880e5a7d9f1"
down_revision: str | Sequence[str] | None = "a879d4f6c8e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "export_shares"
_COLUMN = "upload_pending"


def _has_column() -> bool:
    return _COLUMN in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(_TABLE)}


def upgrade() -> None:
    if _has_column():
        return
    with op.batch_alter_table(_TABLE) as batch:
        batch.add_column(sa.Column(_COLUMN, sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    if not _has_column():
        return
    with op.batch_alter_table(_TABLE) as batch:
        batch.drop_column(_COLUMN)
