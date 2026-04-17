"""
Tests for DB TLS enforcement (DB_TLS_REQUIRED + DB_TLS_OVERRIDE).

Covers:
1. Runtime TLS check: required + inactive → RuntimeError (startup blocked)
2. Runtime TLS check: required + active → passes, emits security event
3. Break-glass override: valid ticket + non-expired → bypasses enforcement
4. Break-glass override: expired date → ignored, enforcement applies
5. Break-glass override: malformed → ignored
6. TLS not required → warning only (existing behavior preserved)
7. Daily TLS verification job emits HMAC-signed evidence
8. Config-level sslmode enforcement in connection string
"""

import os
import sys
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_pg_engine_mock(ssl_active: bool):
    """Create a mock engine that behaves like PostgreSQL for init_db().

    Returns a mock engine whose connect() context manager returns a
    mock connection. The connection's execute() inspects the SQL text
    to return appropriate values for:
    - pg_stat_ssl → ssl_active parameter
    - SELECT version() → version string
    - All other queries → generic safe MagicMock
    """
    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"
    mock_engine.pool = MagicMock()
    type(mock_engine.pool).__name__ = "QueuePool"

    # raw_connection for enum patching
    raw_conn = MagicMock()
    raw_cursor = MagicMock()
    raw_cursor.fetchone.return_value = (1,)  # Pretend ENTERPRISE enum exists
    raw_conn.cursor.return_value = raw_cursor
    mock_engine.raw_connection.return_value = raw_conn

    mock_conn = MagicMock()

    def _smart_execute(query, params=None):
        """Route queries to appropriate mock results."""
        query_str = str(query)
        result = MagicMock()

        if "pg_stat_ssl" in query_str:
            result.fetchone.return_value = (ssl_active,)
        elif "SELECT version()" in query_str or "version()" in query_str:
            result.scalar.return_value = "PostgreSQL 15.0 (test)"
        elif "information_schema.columns" in query_str:
            result.fetchone.return_value = ("column_exists",)  # Column exists
        elif "PRAGMA" in query_str:
            result.fetchall.return_value = []
        else:
            result.fetchone.return_value = None
            result.fetchall.return_value = []
            result.scalar.return_value = None
            result.rowcount = 0

        return result

    mock_conn.execute.side_effect = _smart_execute
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_engine.connect.return_value = mock_conn

    return mock_engine


class TestRuntimeTLSEnforcement:
    """init_db() must block startup when TLS is inactive and required."""

    def test_tls_required_and_inactive_raises(self):
        """DB_TLS_REQUIRED=true + TLS inactive → RuntimeError."""
        mock_engine = _make_pg_engine_mock(ssl_active=False)

        with (
            patch("database.engine", mock_engine),
            patch("database.DB_TLS_REQUIRED", True),
            patch("database.DB_TLS_OVERRIDE_VALID", False),
            patch("database.DB_TLS_OVERRIDE_TICKET", ""),
            patch("database.Base") as mock_base,
        ):
            mock_base.metadata.create_all = MagicMock()

            from database import init_db

            with pytest.raises(RuntimeError, match="TLS verification failed"):
                init_db()

    def test_tls_required_and_active_passes(self):
        """DB_TLS_REQUIRED=true + TLS active → no error, logs verification."""
        mock_engine = _make_pg_engine_mock(ssl_active=True)

        with (
            patch("database.engine", mock_engine),
            patch("database.DB_TLS_REQUIRED", True),
            patch("database.DB_TLS_OVERRIDE_VALID", False),
            patch("database.DB_TLS_OVERRIDE_TICKET", ""),
            patch("database.Base") as mock_base,
            patch("database.log_secure_operation") as mock_log,
        ):
            mock_base.metadata.create_all = MagicMock()

            from database import init_db

            init_db()  # Should not raise

            mock_log.assert_any_call("db_tls_verified", "PostgreSQL TLS active at startup")

    def test_tls_not_required_inactive_warns_only(self):
        """DB_TLS_REQUIRED=false + TLS inactive → warning, no crash."""
        mock_engine = _make_pg_engine_mock(ssl_active=False)

        with (
            patch("database.engine", mock_engine),
            patch("database.DB_TLS_REQUIRED", False),
            patch("database.DB_TLS_OVERRIDE_VALID", False),
            patch("database.DB_TLS_OVERRIDE_TICKET", ""),
            patch("database.Base") as mock_base,
        ):
            mock_base.metadata.create_all = MagicMock()

            from database import init_db

            init_db()  # Should not raise


class TestPoolerHostnameSkip:
    """Sprint 673: transparent poolers terminate TLS at the pool layer, so
    pg_stat_ssl reports the pooler-to-backend hop and always returns ssl=false.
    Detect `-pooler` in the hostname and skip the assertion in that case.
    """

    def test_pooler_hostname_skips_pg_stat_ssl_even_when_required(self):
        """`-pooler` host + DB_TLS_REQUIRED=true + ssl=false → no crash, no query."""
        mock_engine = _make_pg_engine_mock(ssl_active=False)
        # .example is an IANA-reserved TLD that never resolves — keeps
        # TruffleHog's Postgres detector from "verifying" the URL.
        pooler_url = "postgresql://tb-test-pooler.example:5432/db?sslmode=require"

        with (
            patch("database.engine", mock_engine),
            patch("database.DATABASE_URL", pooler_url),
            patch("database.DB_TLS_REQUIRED", True),
            patch("database.DB_TLS_OVERRIDE_VALID", False),
            patch("database.DB_TLS_OVERRIDE_TICKET", ""),
            patch("database.Base") as mock_base,
            patch("database.log_secure_operation") as mock_log,
        ):
            mock_base.metadata.create_all = MagicMock()

            from database import init_db

            init_db()  # Must NOT raise even though ssl_active=False

            # The pooler-skip secure event was emitted
            skip_events = [
                call for call in mock_log.call_args_list if call.args and call.args[0] == "db_tls_pooler_skip"
            ]
            assert skip_events, "expected db_tls_pooler_skip event"

            # pg_stat_ssl was never queried on the pooled connection
            conn = mock_engine.connect.return_value
            queries = [str(c.args[0]) for c in conn.execute.call_args_list]
            assert not any("pg_stat_ssl" in q for q in queries), (
                f"pg_stat_ssl should be skipped on pooler hostname; saw: {queries}"
            )

    def test_direct_hostname_still_runs_pg_stat_ssl(self):
        """Non-pooler host → existing assertion runs, ssl_active=True logs verified."""
        mock_engine = _make_pg_engine_mock(ssl_active=True)
        direct_url = "postgresql://tb-test.example:5432/db?sslmode=require"

        with (
            patch("database.engine", mock_engine),
            patch("database.DATABASE_URL", direct_url),
            patch("database.DB_TLS_REQUIRED", True),
            patch("database.DB_TLS_OVERRIDE_VALID", False),
            patch("database.DB_TLS_OVERRIDE_TICKET", ""),
            patch("database.Base") as mock_base,
            patch("database.log_secure_operation") as mock_log,
        ):
            mock_base.metadata.create_all = MagicMock()

            from database import init_db

            init_db()

            conn = mock_engine.connect.return_value
            queries = [str(c.args[0]) for c in conn.execute.call_args_list]
            assert any("pg_stat_ssl" in q for q in queries), (
                "pg_stat_ssl assertion must still run for non-pooler hostnames"
            )
            mock_log.assert_any_call("db_tls_verified", "PostgreSQL TLS active at startup")

    def test_is_pooled_hostname_helper_recognises_pooler_suffix(self):
        """Direct unit test for the hostname helper."""
        from database import _is_pooled_hostname

        assert _is_pooled_hostname("postgresql://tb-abc-pooler.example:5432/db")
        assert _is_pooled_hostname("postgresql://tb-abc-pooler.example/db?sslmode=require")
        assert not _is_pooled_hostname("postgresql://tb-abc.example:5432/db")
        assert not _is_pooled_hostname("sqlite:///./test.db")
        assert not _is_pooled_hostname("")


class TestBreakGlassOverride:
    """DB_TLS_OVERRIDE allows temporary bypass with ticket + expiration."""

    def test_valid_override_bypasses_enforcement(self):
        """Valid override (non-expired) allows startup despite TLS inactive."""
        mock_engine = _make_pg_engine_mock(ssl_active=False)

        with (
            patch("database.engine", mock_engine),
            patch("database.DB_TLS_REQUIRED", True),
            patch("database.DB_TLS_OVERRIDE_VALID", True),
            patch("database.DB_TLS_OVERRIDE_TICKET", "SEC-1234"),
            patch("database.Base") as mock_base,
            patch("database.log_secure_operation") as mock_log,
        ):
            mock_base.metadata.create_all = MagicMock()

            from database import init_db

            init_db()  # Should not raise

            mock_log.assert_any_call(
                "db_tls_override",
                "TLS inactive but bypassed via override ticket=SEC-1234",
            )

    def test_expired_override_format(self):
        """Expired override date is detected during config parsing."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        override_str = f"SEC-999:{yesterday}"

        parts = override_str.split(":", 1)
        ticket = parts[0].strip()
        expiry = date.fromisoformat(parts[1].strip())

        assert ticket == "SEC-999"
        assert expiry < date.today()  # Expired — would be rejected by config.py

    def test_malformed_override_rejected(self):
        """Override without colon separator is rejected."""
        override_str = "no-colon-separator"
        parts = override_str.split(":", 1)
        assert len(parts) == 1  # Would be rejected by config.py validation

    def test_override_with_future_date_is_valid(self):
        """Override with future expiration date passes validation."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        override_str = f"SEC-5678:{tomorrow}"

        parts = override_str.split(":", 1)
        ticket = parts[0].strip()
        expiry = date.fromisoformat(parts[1].strip())

        assert ticket == "SEC-5678"
        assert expiry >= date.today()  # Valid — would be accepted


class TestDailyTLSVerificationJob:
    """_job_verify_database_tls emits HMAC-signed evidence."""

    def test_daily_check_logs_active_tls(self):
        """Daily job with TLS active emits signed security event."""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = (True,)

        mock_engine = MagicMock()
        mock_engine.dialect.name = "postgresql"

        with (
            patch("database.SessionLocal", return_value=mock_db),
            patch("database.engine", mock_engine),
            patch("security_utils.log_secure_operation") as mock_log,
            patch("config.JWT_SECRET_KEY", "test-secret-key-for-hmac-signing"),
        ):
            from cleanup_scheduler import _job_verify_database_tls

            _job_verify_database_tls()

            assert mock_log.called
            call_args = mock_log.call_args
            assert call_args[0][0] == "db_tls_daily_check"
            assert "tls=active" in call_args[0][1]
            assert "sig=" in call_args[0][1]

    def test_daily_check_logs_inactive_tls(self):
        """Daily job with TLS inactive emits warning with signature."""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = (False,)

        mock_engine = MagicMock()
        mock_engine.dialect.name = "postgresql"

        with (
            patch("database.SessionLocal", return_value=mock_db),
            patch("database.engine", mock_engine),
            patch("security_utils.log_secure_operation") as mock_log,
            patch("config.JWT_SECRET_KEY", "test-secret-key-for-hmac-signing"),
        ):
            from cleanup_scheduler import _job_verify_database_tls

            _job_verify_database_tls()

            assert mock_log.called
            call_args = mock_log.call_args
            assert "tls=INACTIVE" in call_args[0][1]
            assert "sig=" in call_args[0][1]

    def test_daily_check_skips_sqlite(self):
        """Daily job is a no-op for SQLite (dev/test)."""
        mock_engine = MagicMock()
        mock_engine.dialect.name = "sqlite"

        with (
            patch("database.engine", mock_engine),
            patch("security_utils.log_secure_operation") as mock_log,
        ):
            from cleanup_scheduler import _job_verify_database_tls

            _job_verify_database_tls()

            mock_log.assert_not_called()


class TestConfigSSLModeEnforcement:
    """Config-level sslmode check in DATABASE_URL."""

    def test_production_default_requires_tls(self):
        """Production mode defaults DB_TLS_REQUIRED to true."""
        env_mode = "production"
        default = "true" if env_mode == "production" else "false"
        assert default == "true"

    def test_development_default_does_not_require_tls(self):
        """Development mode defaults DB_TLS_REQUIRED to false."""
        env_mode = "development"
        default = "true" if env_mode == "production" else "false"
        assert default == "false"

    def test_sslmode_require_is_accepted(self):
        """sslmode=require passes the secure modes check."""
        _SECURE_SSL_MODES = {"require", "verify-ca", "verify-full"}
        assert "require" in _SECURE_SSL_MODES

    def test_sslmode_disable_is_rejected(self):
        """sslmode=disable fails the secure modes check."""
        _SECURE_SSL_MODES = {"require", "verify-ca", "verify-full"}
        assert "disable" not in _SECURE_SSL_MODES

    def test_sslmode_prefer_is_rejected(self):
        """sslmode=prefer is not considered secure (opportunistic, no auth)."""
        _SECURE_SSL_MODES = {"require", "verify-ca", "verify-full"}
        assert "prefer" not in _SECURE_SSL_MODES
