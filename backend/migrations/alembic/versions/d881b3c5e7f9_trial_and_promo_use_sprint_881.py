"""Sprint 881 (AZ-16): users.trial_used_at + promo_redemptions.

Revision ID: d881b3c5e7f9
Revises: c881a2b4d6e8
Create Date: 2026-11-18

WHY
---
Checkout granted the introductory trial whenever the account had no
subscription or a cancelled one, so cancelling and buying again restarted the
trial; promo codes were checked only against the billing interval, never
against earlier use. CEO decision 2026-11-16: one trial per account, each promo
code once per account.

* ``users.trial_used_at`` — set when Stripe confirms a trialing subscription.
* ``promo_redemptions`` — one row per (account, code) Stripe confirmed with a
  discount; unique on (user_id, promo_code).

Both are recorded from the webhook, not when checkout opens (CEO 2026-11-18).
No customers yet, so nothing is backfilled. Guarded with inspector checks.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d881b3c5e7f9"
down_revision: str | Sequence[str] | None = "c881a2b4d6e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _user_columns() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}


def upgrade() -> None:
    if "trial_used_at" not in _user_columns():
        with op.batch_alter_table("users") as batch:
            batch.add_column(sa.Column("trial_used_at", sa.DateTime(), nullable=True))

    if "promo_redemptions" not in _tables():
        op.create_table(
            "promo_redemptions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("promo_code", sa.String(length=32), nullable=False),
            sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
            sa.Column("redeemed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "promo_code", name="uq_promo_redemptions_user_code"),
        )
        op.create_index(op.f("ix_promo_redemptions_id"), "promo_redemptions", ["id"], unique=False)
        op.create_index(op.f("ix_promo_redemptions_user_id"), "promo_redemptions", ["user_id"], unique=False)


def downgrade() -> None:
    if "promo_redemptions" in _tables():
        op.drop_index(op.f("ix_promo_redemptions_user_id"), table_name="promo_redemptions")
        op.drop_index(op.f("ix_promo_redemptions_id"), table_name="promo_redemptions")
        op.drop_table("promo_redemptions")
    if "trial_used_at" in _user_columns():
        with op.batch_alter_table("users") as batch:
            batch.drop_column("trial_used_at")
