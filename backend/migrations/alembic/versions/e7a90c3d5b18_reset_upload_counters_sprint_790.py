"""Sprint 790: reset every subscription's upload counter to zero.

Revision ID: e7a90c3d5b18
Revises: c9e4a1b73f20
Create Date: 2026-10-24

WHY
---
Until Sprint 790 ``subscriptions.uploads_used_current_period`` was read by the
quota gate (``check_upload_limit``) but advanced only by bulk upload, so on
every other path the paid-tier allowance was never enforced. Sprint 790 starts
advancing it once per successful analysis run. The values sitting in the
column today were produced under the old rules — bulk-upload member files,
never reset on renewals the hourly job missed — and do not mean "runs used this
period". Enforcing against them could lock an account out on a count nobody
can explain.

CEO decision (Sprint 790): reset all counters at deploy. There are no paying
subscribers yet, so this costs nothing now and would cost goodwill later.

The UPDATE touches only the counter. No financial data is read or written.
Idempotent: re-running it on an already-zeroed table changes nothing.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "e7a90c3d5b18"
down_revision: str | Sequence[str] | None = "c9e4a1b73f20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE subscriptions SET uploads_used_current_period = 0 WHERE uploads_used_current_period <> 0")


def downgrade() -> None:
    # Intentionally a no-op. The pre-reset values were not a meaningful count
    # (see the module docstring) and are not recoverable after the UPDATE;
    # restoring them would only re-create the lockout risk this revision removes.
    pass
