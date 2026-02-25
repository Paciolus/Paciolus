"""Rename starter tier to solo.

Aligns internal tier ID with public display name.

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-02-25
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d9e0f1a2b3c4"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL: add new enum value (cannot remove old in PG — safe no-op on SQLite)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE usertier ADD VALUE IF NOT EXISTS 'solo'")

    # Migrate data in both tables
    op.execute("UPDATE users SET tier = 'solo' WHERE tier = 'starter'")
    op.execute("UPDATE subscriptions SET tier = 'solo' WHERE tier = 'starter'")


def downgrade() -> None:
    op.execute("UPDATE users SET tier = 'starter' WHERE tier = 'solo'")
    op.execute("UPDATE subscriptions SET tier = 'starter' WHERE tier = 'solo'")
