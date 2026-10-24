"""Sprint 790: add subscriptions.uploads_window_start (monthly allowance window).

Revision ID: f3b81d6e2a47
Revises: e7a90c3d5b18
Create Date: 2026-10-24

WHY
---
The upload allowance is monthly on every billing interval (Solo 100/mo,
Professional 500/mo), but the counter only reset when the *billing period* did:
on renewal (``sync_subscription_from_stripe``) or at ``current_period_end``
(``reset_upload_quotas``). For an annual plan that is once a year, so an annual
subscriber who reached the cap in month 1 would have been locked out for the
other eleven (PR #227 review).

This column records which monthly window the stored count belongs to. A NULL or
older window reads as a count of 0 and is rolled over atomically by the next
increment (``shared.entitlement_checks.increment_upload_count``). No backfill:
every row starts NULL, which reads as an untouched allowance - the conservative
direction, and consistent with ``e7a90c3d5b18`` having just zeroed every counter.

Guarded with an inspector check, following ``c9e4a1b73f20``: a database whose
schema came from ``create_all()`` may already have the column, and an unguarded
add would fail the deploy at startup.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3b81d6e2a47"
down_revision: str | Sequence[str] | None = "e7a90c3d5b18"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if not _has_column("subscriptions", "uploads_window_start"):
        with op.batch_alter_table("subscriptions", schema=None) as batch_op:
            batch_op.add_column(sa.Column("uploads_window_start", sa.DateTime(), nullable=True))


def downgrade() -> None:
    if _has_column("subscriptions", "uploads_window_start"):
        with op.batch_alter_table("subscriptions", schema=None) as batch_op:
            batch_op.drop_column("uploads_window_start")
