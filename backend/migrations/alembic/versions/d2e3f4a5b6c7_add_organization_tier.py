"""Add organization tier to UserTier and subscription_tier enums.

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-03-01

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d2e3f4a5b6c7"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE usertier ADD VALUE IF NOT EXISTS 'organization'")
        op.execute("ALTER TYPE subscription_tier ADD VALUE IF NOT EXISTS 'organization'")


def downgrade() -> None:
    # Enum value additions are non-reversible in PostgreSQL
    pass
