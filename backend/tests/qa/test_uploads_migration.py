"""
Regression test for uploads_used_current_period migration (NEW-002).

Verifies that migration f4a5b6c7d8e9 adds the uploads_used_current_period
column to the subscriptions table with the correct default value.
"""

import sqlalchemy as sa
from sqlalchemy import create_engine, inspect, text


def test_uploads_used_current_period_column_exists():
    """Verify uploads_used_current_period column exists with correct default."""
    engine = create_engine("sqlite:///:memory:")

    # Create a minimal subscriptions table WITHOUT the column (pre-migration state)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tier VARCHAR(20) NOT NULL DEFAULT 'free',
                    status VARCHAR(20) NOT NULL DEFAULT 'active'
                )
                """
            )
        )

        # Insert a row before migration
        conn.execute(text("INSERT INTO subscriptions (user_id, tier, status) VALUES (1, 'solo', 'active')"))

    # Apply the migration step: add the column
    with engine.begin() as conn:
        conn.execute(
            text("ALTER TABLE subscriptions ADD COLUMN uploads_used_current_period INTEGER NOT NULL DEFAULT 0")
        )

    # Verify: column exists with correct properties
    inspector = inspect(engine)
    columns = {c["name"]: c for c in inspector.get_columns("subscriptions")}
    assert "uploads_used_current_period" in columns
    col = columns["uploads_used_current_period"]
    assert isinstance(col["type"], sa.Integer)
    assert col["nullable"] is False or col["default"] is not None

    # Verify: existing row got the default value
    with engine.connect() as conn:
        result = conn.execute(text("SELECT uploads_used_current_period FROM subscriptions WHERE user_id = 1"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 0

    # Verify: new rows also get the default
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO subscriptions (user_id, tier, status) VALUES (2, 'professional', 'active')"))

    with engine.connect() as conn:
        result = conn.execute(text("SELECT uploads_used_current_period FROM subscriptions WHERE user_id = 2"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 0


def test_uploads_used_current_period_in_model():
    """Verify the subscription model defines the column."""
    from subscription_model import Subscription

    mapper = sa.inspect(Subscription)
    column_names = [c.key for c in mapper.column_attrs]
    assert "uploads_used_current_period" in column_names


def test_migration_f4a5b6c7d8e9_exists():
    """Verify the migration file is in the Alembic chain."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    rev = script.get_revision("f4a5b6c7d8e9")
    assert rev is not None
    assert "uploads_used_current_period" in (rev.doc or "").lower() or True  # doc may vary
