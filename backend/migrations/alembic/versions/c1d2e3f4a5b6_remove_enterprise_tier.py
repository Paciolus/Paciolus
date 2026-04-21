"""Remove enterprise tier — migrate enterprise users to team.

Revision ID: c1d2e3f4a5b6
Revises: a4b5c6d7e8f9, b1c2d3e4f5a6
Create Date: 2026-03-01

Enterprise tier removed. Existing enterprise users/subscriptions migrated to team.
PostgreSQL enum values updated for both usertier and subscription_tier.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: tuple[str, str] = ("a4b5c6d7e8f9", "b1c2d3e4f5a6")
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Step 1: Migrate all enterprise users → team
    op.execute("UPDATE users SET tier = 'team' WHERE tier = 'enterprise'")

    # Step 2: Migrate all enterprise subscriptions → team
    op.execute("UPDATE subscriptions SET tier = 'team' WHERE tier = 'enterprise'")

    # Steps 3/4: enum recreation is PostgreSQL-only.  SQLite stores enum
    # columns as plain TEXT and has no type-altering DDL, so the data
    # UPDATEs above are the complete migration there.  (Added 2026-04-21
    # audit so `alembic upgrade head` works from scratch on SQLite.)
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Step 3: Remove 'enterprise' from the usertier enum
    op.execute("ALTER TYPE usertier RENAME TO usertier_old")
    op.execute("CREATE TYPE usertier AS ENUM ('free', 'solo', 'professional', 'team')")
    op.execute("ALTER TABLE users ALTER COLUMN tier TYPE usertier USING tier::text::usertier")
    op.execute("DROP TYPE usertier_old")

    # Step 4: Remove 'enterprise' from the subscription_tier enum
    op.execute("ALTER TYPE subscription_tier RENAME TO subscription_tier_old")
    op.execute("CREATE TYPE subscription_tier AS ENUM ('free', 'solo', 'professional', 'team')")
    op.execute("ALTER TABLE subscriptions ALTER COLUMN tier TYPE subscription_tier USING tier::text::subscription_tier")
    op.execute("DROP TYPE subscription_tier_old")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Re-add 'enterprise' to usertier enum
    op.execute("ALTER TYPE usertier RENAME TO usertier_old")
    op.execute("CREATE TYPE usertier AS ENUM ('free', 'solo', 'professional', 'team', 'enterprise')")
    op.execute("ALTER TABLE users ALTER COLUMN tier TYPE usertier USING tier::text::usertier")
    op.execute("DROP TYPE usertier_old")

    # Re-add 'enterprise' to subscription_tier enum
    op.execute("ALTER TYPE subscription_tier RENAME TO subscription_tier_old")
    op.execute("CREATE TYPE subscription_tier AS ENUM ('free', 'solo', 'professional', 'team', 'enterprise')")
    op.execute("ALTER TABLE subscriptions ALTER COLUMN tier TYPE subscription_tier USING tier::text::subscription_tier")
    op.execute("DROP TYPE subscription_tier_old")
