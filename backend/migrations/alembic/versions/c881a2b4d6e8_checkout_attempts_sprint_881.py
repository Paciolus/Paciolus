"""Sprint 881 (AZ-09): checkout_attempts + subscription conflict flag.

Revision ID: c881a2b4d6e8
Revises: b880e5a7d9f1
Create Date: 2026-11-18

WHY
---
Checkout opened a new ``mode: subscription`` session whatever the account
already had, and sync overwrote the single local row's
``stripe_subscription_id`` with whichever subscription it saw last, so an
account could be billed for two subscriptions while the app tracked one.

* ``checkout_attempts`` — one durable row per Checkout Session opened for a new
  subscription: Stripe customer, session ID, plan, status. Purchase admission
  uses it to find and expire an earlier session before opening another.
* ``subscriptions.conflicting_stripe_subscription_id`` /
  ``conflict_detected_at`` — set by sync when a second live Stripe subscription
  appears for an account; the stored subscription is kept.

No customers yet (CEO 2026-11-16), so nothing is backfilled. Guarded with
inspector checks, like ``b880e5a7d9f1``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c881a2b4d6e8"
down_revision: str | Sequence[str] | None = "b880e5a7d9f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SUBS = "subscriptions"
_SUB_COLUMNS = ("conflicting_stripe_subscription_id", "conflict_detected_at")


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _sub_columns() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(_SUBS)}


def upgrade() -> None:
    if "checkout_attempts" not in _tables():
        op.create_table(
            "checkout_attempts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("tier", sa.String(length=20), nullable=False),
            sa.Column("billing_interval", sa.String(length=10), nullable=False),
            sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
            sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=True),
            sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
            sa.Column("trial_offered", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("promo_code", sa.String(length=32), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("stripe_checkout_session_id"),
        )
        op.create_index(op.f("ix_checkout_attempts_id"), "checkout_attempts", ["id"], unique=False)
        op.create_index(op.f("ix_checkout_attempts_user_id"), "checkout_attempts", ["user_id"], unique=False)

    present = _sub_columns()
    with op.batch_alter_table(_SUBS) as batch:
        if "conflicting_stripe_subscription_id" not in present:
            batch.add_column(sa.Column("conflicting_stripe_subscription_id", sa.String(length=255), nullable=True))
        if "conflict_detected_at" not in present:
            batch.add_column(sa.Column("conflict_detected_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    present = _sub_columns()
    with op.batch_alter_table(_SUBS) as batch:
        for column in _SUB_COLUMNS:
            if column in present:
                batch.drop_column(column)
    if "checkout_attempts" in _tables():
        op.drop_index(op.f("ix_checkout_attempts_user_id"), table_name="checkout_attempts")
        op.drop_index(op.f("ix_checkout_attempts_id"), table_name="checkout_attempts")
        op.drop_table("checkout_attempts")
