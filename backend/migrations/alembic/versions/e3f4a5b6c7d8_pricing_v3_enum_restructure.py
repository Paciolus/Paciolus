"""Pricing v3 enum restructure — replace team/organization with enterprise.

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-03-02

Phase LXIX: Pricing Restructure v3.
Current enum:  free, solo, professional, team, organization
Target enum:   free, solo, professional, enterprise

Pre-launch (zero customers) so team/organization rows are empty.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3f4a5b6c7d8"
down_revision: str = "d2e3f4a5b6c7"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # SQLite: enums are just strings, no type reconstruction needed
        op.execute("UPDATE users SET tier = 'solo' WHERE tier IN ('team', 'organization')")
        op.execute("UPDATE subscriptions SET tier = 'solo' WHERE tier IN ('team', 'organization')")
        return

    # Step 1: Migrate any existing team/organization rows to solo (zero rows expected)
    op.execute("UPDATE users SET tier = 'solo' WHERE tier IN ('team', 'organization')")
    op.execute("UPDATE subscriptions SET tier = 'solo' WHERE tier IN ('team', 'organization')")

    # Step 2: Reconstruct usertier enum (remove team/organization, add enterprise)
    op.execute("ALTER TYPE usertier RENAME TO usertier_old")
    op.execute("CREATE TYPE usertier AS ENUM ('free', 'solo', 'professional', 'enterprise')")
    op.execute("ALTER TABLE users ALTER COLUMN tier TYPE usertier USING tier::text::usertier")
    op.execute("DROP TYPE usertier_old")

    # Step 3: Reconstruct subscription_tier enum
    op.execute("ALTER TYPE subscription_tier RENAME TO subscription_tier_old")
    op.execute("CREATE TYPE subscription_tier AS ENUM ('free', 'solo', 'professional', 'enterprise')")
    op.execute("ALTER TABLE subscriptions ALTER COLUMN tier TYPE subscription_tier USING tier::text::subscription_tier")
    op.execute("DROP TYPE subscription_tier_old")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Reverse: reconstruct enums with team/organization, remove enterprise
    op.execute("UPDATE users SET tier = 'solo' WHERE tier = 'enterprise'")
    op.execute("UPDATE subscriptions SET tier = 'solo' WHERE tier = 'enterprise'")

    op.execute("ALTER TYPE usertier RENAME TO usertier_old")
    op.execute("CREATE TYPE usertier AS ENUM ('free', 'solo', 'professional', 'team', 'organization')")
    op.execute("ALTER TABLE users ALTER COLUMN tier TYPE usertier USING tier::text::usertier")
    op.execute("DROP TYPE usertier_old")

    op.execute("ALTER TYPE subscription_tier RENAME TO subscription_tier_old")
    op.execute("CREATE TYPE subscription_tier AS ENUM ('free', 'solo', 'professional', 'team', 'organization')")
    op.execute("ALTER TABLE subscriptions ALTER COLUMN tier TYPE subscription_tier USING tier::text::subscription_tier")
    op.execute("DROP TYPE subscription_tier_old")
