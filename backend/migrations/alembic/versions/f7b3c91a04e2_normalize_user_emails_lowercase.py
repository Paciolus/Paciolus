"""Normalize user.email to lowercase + stripped form.

Fixes the production lockout where a mixed-case registration created a
user row whose email did not match the lowercased lookup performed by
/auth/forgot-password (and, after the accompanying code fix, by
/auth/login and /auth/register as well).

Strategy:
  1. Detect case-collision groups. If `SELECT LOWER(TRIM(email)) ... GROUP BY 1
     HAVING COUNT(*) > 1` returns any rows, abort with a clear error so the
     operator can resolve duplicates manually — we refuse to silently drop
     user data.
  2. Otherwise, UPDATE users SET email = LOWER(TRIM(email)) for any row that
     is not already normalized.
  3. Apply the same normalization to `pending_email` for consistency with
     the Sprint 203 email-change flow.

Downgrade is a no-op: lowercasing is not reversible, and restoring the
original casing would require information we no longer have.

Revision ID: f7b3c91a04e2
Revises: a848ac91d39a
Create Date: 2026-04-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f7b3c91a04e2"
down_revision = "a848ac91d39a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Detect case-collision groups — refuse to clobber real data.
    collisions = bind.execute(
        sa.text(
            """
            SELECT LOWER(TRIM(email)) AS normalized, COUNT(*) AS n
            FROM users
            WHERE email IS NOT NULL
            GROUP BY LOWER(TRIM(email))
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    if collisions:
        rows = ", ".join(f"{row.normalized!r}={row.n}" for row in collisions)
        raise RuntimeError(
            "Email normalization aborted: case-colliding user rows detected "
            f"({rows}). Resolve duplicates manually before re-running this "
            "migration."
        )

    # 2. Lowercase + strip existing emails. Only touch rows that need it to
    #    minimize UPDATE noise on quiet tables.
    bind.execute(
        sa.text(
            """
            UPDATE users
            SET email = LOWER(TRIM(email))
            WHERE email IS NOT NULL
              AND email <> LOWER(TRIM(email))
            """
        )
    )

    # 3. Same treatment for pending_email (Sprint 203 flow).
    bind.execute(
        sa.text(
            """
            UPDATE users
            SET pending_email = LOWER(TRIM(pending_email))
            WHERE pending_email IS NOT NULL
              AND pending_email <> LOWER(TRIM(pending_email))
            """
        )
    )


def downgrade() -> None:
    # No-op: case-folding is lossy.
    pass
