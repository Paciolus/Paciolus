"""
Sprint 264: Verify server_default=func.now() on timestamp columns.

Tests:
1. Each model gets a non-NULL timestamp from the DB when Python-side default is bypassed.
2. SQLite CURRENT_TIMESTAMP produces UTC (not local time).
3. All 15 server_default columns are present in model DDL.
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).parent.parent))



# ---------------------------------------------------------------------------
# DDL inspection: confirm server_default is declared
# ---------------------------------------------------------------------------

# (table_name, column_name) pairs that MUST have a server_default
_EXPECTED_SERVER_DEFAULTS = [
    ("users", "created_at"),
    ("users", "updated_at"),
    ("activity_logs", "timestamp"),
    ("clients", "created_at"),
    ("clients", "updated_at"),
    ("diagnostic_summaries", "timestamp"),
    ("email_verification_tokens", "created_at"),
    ("refresh_tokens", "created_at"),
    ("engagements", "created_at"),
    ("engagements", "updated_at"),
    ("tool_runs", "run_at"),
    ("follow_up_items", "created_at"),
    ("follow_up_items", "updated_at"),
    ("follow_up_item_comments", "created_at"),
    ("follow_up_item_comments", "updated_at"),
    # Sprint 262 — already done
    ("tool_sessions", "created_at"),
    ("tool_sessions", "updated_at"),
]


class TestTimestampServerDefaults:
    """Verify server_default=func.now() is declared on all timestamp columns."""

    @pytest.mark.parametrize("table_name,column_name", _EXPECTED_SERVER_DEFAULTS)
    def test_server_default_declared(self, db_engine, table_name, column_name):
        """DDL inspection: column has a non-NULL server_default."""
        inspector = inspect(db_engine)
        columns = {c["name"]: c for c in inspector.get_columns(table_name)}
        col = columns[column_name]
        assert col["default"] is not None, (
            f"{table_name}.{column_name} is missing server_default in DDL"
        )


# ---------------------------------------------------------------------------
# Functional: DB-generated timestamps when Python default is bypassed
# ---------------------------------------------------------------------------

class TestDBGeneratedTimestamps:
    """Insert rows via raw SQL (bypassing Python defaults) and verify timestamps are populated."""

    def test_user_timestamps(self, db_session):
        """User.created_at and updated_at get DB defaults."""
        db_session.execute(text(
            "INSERT INTO users (email, hashed_password, is_active, is_verified, tier, failed_login_attempts, settings) "
            "VALUES ('dbtest@example.com', 'hash123', 1, 0, 'free', 0, '{}')"
        ))
        db_session.flush()
        row = db_session.execute(text(
            "SELECT created_at, updated_at FROM users WHERE email = 'dbtest@example.com'"
        )).fetchone()
        assert row[0] is not None, "created_at should be populated by server_default"
        assert row[1] is not None, "updated_at should be populated by server_default"

    def test_activity_log_timestamp(self, db_session):
        """ActivityLog.timestamp gets DB default."""
        # Create user first
        db_session.execute(text(
            "INSERT INTO users (email, hashed_password, is_active, is_verified, tier, failed_login_attempts, settings) "
            "VALUES ('log@example.com', 'hash', 1, 0, 'free', 0, '{}')"
        ))
        db_session.flush()
        user_id = db_session.execute(text("SELECT id FROM users WHERE email = 'log@example.com'")).scalar()
        db_session.execute(text(
            "INSERT INTO activity_logs (user_id, filename_hash, record_count, total_debits, total_credits, "
            "materiality_threshold, was_balanced) "
            f"VALUES ({user_id}, 'abc123', 100, 1000.0, 1000.0, 50.0, 1)"
        ))
        db_session.flush()
        ts = db_session.execute(text("SELECT timestamp FROM activity_logs LIMIT 1")).scalar()
        assert ts is not None, "timestamp should be populated by server_default"

    def test_client_timestamps(self, db_session):
        """Client.created_at and updated_at get DB defaults."""
        db_session.execute(text(
            "INSERT INTO users (email, hashed_password, is_active, is_verified, tier, failed_login_attempts, settings) "
            "VALUES ('client@example.com', 'hash', 1, 0, 'free', 0, '{}')"
        ))
        db_session.flush()
        user_id = db_session.execute(text("SELECT id FROM users WHERE email = 'client@example.com'")).scalar()
        db_session.execute(text(
            f"INSERT INTO clients (user_id, name, industry, fiscal_year_end, settings) "
            f"VALUES ({user_id}, 'Test Corp', 'other', '12-31', '{{}}')"
        ))
        db_session.flush()
        row = db_session.execute(text("SELECT created_at, updated_at FROM clients LIMIT 1")).fetchone()
        assert row[0] is not None
        assert row[1] is not None

    def test_engagement_timestamps(self, db_session):
        """Engagement.created_at and updated_at get DB defaults."""
        # Setup: user + client
        db_session.execute(text(
            "INSERT INTO users (email, hashed_password, is_active, is_verified, tier, failed_login_attempts, settings) "
            "VALUES ('eng@example.com', 'hash', 1, 0, 'free', 0, '{}')"
        ))
        db_session.flush()
        user_id = db_session.execute(text("SELECT id FROM users WHERE email = 'eng@example.com'")).scalar()
        db_session.execute(text(
            f"INSERT INTO clients (user_id, name, industry, fiscal_year_end, settings) "
            f"VALUES ({user_id}, 'EngCorp', 'other', '12-31', '{{}}')"
        ))
        db_session.flush()
        client_id = db_session.execute(text("SELECT id FROM clients LIMIT 1")).scalar()
        db_session.execute(text(
            f"INSERT INTO engagements (client_id, period_start, period_end, status, "
            f"performance_materiality_factor, trivial_threshold_factor, created_by) "
            f"VALUES ({client_id}, '2025-01-01', '2025-12-31', 'active', 0.75, 0.05, {user_id})"
        ))
        db_session.flush()
        row = db_session.execute(text("SELECT created_at, updated_at FROM engagements LIMIT 1")).fetchone()
        assert row[0] is not None
        assert row[1] is not None

    def test_tool_run_timestamp(self, db_session):
        """ToolRun.run_at gets DB default."""
        # Setup chain: user → client → engagement
        db_session.execute(text(
            "INSERT INTO users (email, hashed_password, is_active, is_verified, tier, failed_login_attempts, settings) "
            "VALUES ('tr@example.com', 'hash', 1, 0, 'free', 0, '{}')"
        ))
        db_session.flush()
        user_id = db_session.execute(text("SELECT id FROM users WHERE email = 'tr@example.com'")).scalar()
        db_session.execute(text(
            f"INSERT INTO clients (user_id, name, industry, fiscal_year_end, settings) "
            f"VALUES ({user_id}, 'TRCorp', 'other', '12-31', '{{}}')"
        ))
        db_session.flush()
        client_id = db_session.execute(text(
            f"SELECT id FROM clients WHERE user_id = {user_id}"
        )).scalar()
        db_session.execute(text(
            f"INSERT INTO engagements (client_id, period_start, period_end, status, "
            f"performance_materiality_factor, trivial_threshold_factor, created_by) "
            f"VALUES ({client_id}, '2025-01-01', '2025-12-31', 'active', 0.75, 0.05, {user_id})"
        ))
        db_session.flush()
        eng_id = db_session.execute(text(
            f"SELECT id FROM engagements WHERE client_id = {client_id}"
        )).scalar()
        db_session.execute(text(
            f"INSERT INTO tool_runs (engagement_id, tool_name, run_number, status) "
            f"VALUES ({eng_id}, 'trial_balance', 1, 'completed')"
        ))
        db_session.flush()
        ts = db_session.execute(text("SELECT run_at FROM tool_runs LIMIT 1")).scalar()
        assert ts is not None, "run_at should be populated by server_default"


# ---------------------------------------------------------------------------
# UTC verification: SQLite CURRENT_TIMESTAMP is UTC
# ---------------------------------------------------------------------------

class TestSQLiteCurrentTimestampIsUTC:
    """Confirm that SQLite's CURRENT_TIMESTAMP produces UTC, not local time."""

    def test_current_timestamp_matches_utc(self, db_session):
        """
        SQLite CURRENT_TIMESTAMP should be within 2 seconds of Python's UTC now.
        If the system timezone offset were applied, the difference would be hours.
        """
        utc_before = datetime.now(UTC).replace(tzinfo=None)
        row = db_session.execute(text("SELECT CURRENT_TIMESTAMP")).fetchone()
        utc_after = datetime.now(UTC).replace(tzinfo=None)

        # SQLite returns 'YYYY-MM-DD HH:MM:SS' format
        db_ts = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")

        assert utc_before - timedelta(seconds=2) <= db_ts <= utc_after + timedelta(seconds=2), (
            f"CURRENT_TIMESTAMP ({db_ts}) is not within 2s of UTC ({utc_before} – {utc_after}). "
            "SQLite may be returning local time."
        )

    def test_server_default_timestamp_is_utc(self, db_session):
        """
        Insert a row using server_default and verify the generated timestamp is UTC.
        """
        utc_before = datetime.now(UTC).replace(tzinfo=None)
        db_session.execute(text(
            "INSERT INTO users (email, hashed_password, is_active, is_verified, tier, failed_login_attempts, settings) "
            "VALUES ('utctest@example.com', 'hash', 1, 0, 'free', 0, '{}')"
        ))
        db_session.flush()
        utc_after = datetime.now(UTC).replace(tzinfo=None)

        ts_str = db_session.execute(text(
            "SELECT created_at FROM users WHERE email = 'utctest@example.com'"
        )).scalar()

        db_ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        assert utc_before - timedelta(seconds=2) <= db_ts <= utc_after + timedelta(seconds=2), (
            f"server_default timestamp ({db_ts}) drifts from UTC ({utc_before} – {utc_after})"
        )
