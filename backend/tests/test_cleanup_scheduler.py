"""
Tests for cleanup_scheduler.py — Sprint 307

Covers:
- CleanupTelemetry dataclass serialization
- _run_cleanup_job exception safety, session close, last_run tracking
- Watchdog on-schedule / overdue / never-run behavior
- Scheduler lifecycle (disabled, init+shutdown, double-shutdown)
- Config defaults for all 5 scheduler env vars
- Main.py integration (import presence, .env.example docs)
"""

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# TestCleanupTelemetry
# ---------------------------------------------------------------------------


class TestCleanupTelemetry:
    """CleanupTelemetry dataclass serialization."""

    def test_success_telemetry(self):
        from cleanup_scheduler import CleanupTelemetry

        t = CleanupTelemetry(
            job_name="refresh_tokens",
            started_at="2026-02-19T10:00:00+00:00",
            duration_ms=42.5,
            records_processed=7,
        )
        d = t.to_log_dict()
        assert d["event"] == "cleanup_job"
        assert d["job_name"] == "refresh_tokens"
        assert d["duration_ms"] == 42.5
        assert d["records_processed"] == 7
        assert "error" not in d

    def test_error_telemetry(self):
        from cleanup_scheduler import CleanupTelemetry

        t = CleanupTelemetry(
            job_name="tool_sessions",
            started_at="2026-02-19T10:00:00+00:00",
            duration_ms=1.2,
            records_processed=0,
            error="OperationalError: database is locked",
        )
        d = t.to_log_dict()
        assert d["error"] == "OperationalError: database is locked"
        assert d["records_processed"] == 0


# ---------------------------------------------------------------------------
# TestRunCleanupJob
# ---------------------------------------------------------------------------


class TestRunCleanupJob:
    """_run_cleanup_job wrapper behavior."""

    def test_successful_cleanup(self):
        """Job wrapper invokes cleanup func and updates last_run."""
        from cleanup_scheduler import _last_run_times, _run_cleanup_job

        mock_func = MagicMock(return_value=3)
        mock_session = MagicMock()

        with patch("database.SessionLocal", return_value=mock_session):
            _run_cleanup_job("test_job", mock_func)

        mock_func.assert_called_once_with(mock_session)
        mock_session.close.assert_called_once()
        assert "test_job" in _last_run_times

    def test_exception_safety(self, caplog):
        """Job wrapper catches exceptions and still closes session."""
        from cleanup_scheduler import _run_cleanup_job

        def failing_func(db):
            raise RuntimeError("boom")

        mock_session = MagicMock()

        with (
            patch("database.SessionLocal", return_value=mock_session),
            caplog.at_level(logging.ERROR, logger="cleanup_scheduler"),
        ):
            _run_cleanup_job("failing_job", failing_func)

        mock_session.close.assert_called_once()
        assert "Cleanup job failed" in caplog.text

    def test_failure_log_includes_traceback_exc_info(self, caplog):
        """Sanitized telemetry goes to user-visible logs, but the full
        exception (with traceback) is attached via exc_info so Sentry and
        other structured-log sinks can capture the stack trace.

        Regression guard — without this, scheduled-job failures surface in
        Sentry as just "InternalError: scheduled cleanup failed" with no
        traceback, defeating triage.
        """
        from cleanup_scheduler import _run_cleanup_job

        def failing_func(db):
            raise RuntimeError("boom-with-traceback")

        mock_session = MagicMock()

        with (
            patch("database.SessionLocal", return_value=mock_session),
            caplog.at_level(logging.ERROR, logger="cleanup_scheduler"),
        ):
            _run_cleanup_job("failing_job", failing_func)

        error_records = [r for r in caplog.records if "Cleanup job failed" in r.getMessage()]
        assert error_records, "expected a 'Cleanup job failed' error record"
        record = error_records[0]
        assert record.exc_info is not None, "exc_info must be attached for Sentry traceback"
        exc_type, exc_value, _tb = record.exc_info
        assert exc_type is RuntimeError
        assert "boom-with-traceback" in str(exc_value)
        # Sanitized message preserved in the telemetry payload
        assert "RuntimeError: scheduled cleanup failed" in caplog.text
        # Sprint 732: error_type_fqn disambiguates bare class names —
        # SQLAlchemy / psycopg2 / Python all expose `InternalError`. The FQN
        # is module-path metadata, no PII risk.
        assert "error_type_fqn" in caplog.text
        assert "builtins.RuntimeError" in caplog.text

    def test_failure_log_captures_wrapped_cause_and_orig(self, caplog):
        """Sprint 732 follow-up: ``error_type_fqn`` resolved the bare-class
        ambiguity to ``sqlalchemy.exc.InternalError`` for the recurring Neon
        cleanup failures, but that's the SQLAlchemy wrapper. The actual leaf
        class lives in ``__cause__`` (explicit raise-from chain) and ``.orig``
        (SQLAlchemy DBAPIError attribute holding the wrapped psycopg2 exc),
        with ``orig.pgcode`` carrying the Postgres SQLSTATE for psycopg2 errors.

        Without this extension every cleanup failure in Render logs reads
        ``error_type_fqn: sqlalchemy.exc.InternalError`` and triage stalls;
        with it, the same line carries the concrete wrapped class + SQLSTATE.
        """
        from cleanup_scheduler import _run_cleanup_job

        # Synthesize a SQLAlchemy DBAPIError-shaped exception: has both a
        # `__cause__` chain and an `.orig` attribute with a `pgcode`.
        class FakePsycopg2OperationalError(Exception):
            pgcode = "08006"  # connection_failure

        class FakeSQLAlchemyInternalError(Exception):
            pass

        def failing_func(db):
            orig_exc = FakePsycopg2OperationalError("connection lost")
            wrapper = FakeSQLAlchemyInternalError("scheduled cleanup failed")
            wrapper.orig = orig_exc  # type: ignore[attr-defined]
            try:
                raise orig_exc
            except FakePsycopg2OperationalError as e:
                raise wrapper from e

        mock_session = MagicMock()

        with (
            patch("database.SessionLocal", return_value=mock_session),
            caplog.at_level(logging.ERROR, logger="cleanup_scheduler"),
        ):
            _run_cleanup_job("failing_with_chain", failing_func)

        # Wrapper class is in error_type_fqn (existing field).
        assert "FakeSQLAlchemyInternalError" in caplog.text
        # Cause chain (raise X from Y) surfaces in error_cause_fqn.
        assert "error_cause_fqn" in caplog.text
        assert "FakePsycopg2OperationalError" in caplog.text
        # SQLAlchemy `.orig` attribute surfaces in error_orig_fqn.
        assert "error_orig_fqn" in caplog.text
        # psycopg2 pgcode (Postgres SQLSTATE) surfaces in error_orig_pgcode.
        assert "error_orig_pgcode" in caplog.text
        assert "08006" in caplog.text

    def test_session_always_closed_on_success(self):
        """Session is closed even when cleanup returns 0."""
        from cleanup_scheduler import _run_cleanup_job

        mock_session = MagicMock()
        mock_func = MagicMock(return_value=0)

        with patch("database.SessionLocal", return_value=mock_session):
            _run_cleanup_job("zero_job", mock_func)

        mock_session.close.assert_called_once()

    def test_sentry_capture_exception_called_on_failure(self):
        """Sprint 711 Bug 2: failures must explicitly call
        sentry_sdk.capture_exception while still inside the except block.

        Without this, the deferred logger.error(..., exc_info=caught_exc) call
        runs outside the except block — and although Python's LogRecord does
        carry exc_info, Sentry's logging integration was observed dropping it
        in production (104 dunning_grace_period failures landed as
        traceback-less '[InternalError]' events). The explicit
        capture_exception is belt-and-suspenders so the traceback never
        gets lost again.
        """
        from cleanup_scheduler import _run_cleanup_job

        def failing_func(db):
            raise RuntimeError("explicit-capture-test")

        mock_session = MagicMock()
        mock_sentry = MagicMock()

        with (
            patch("database.SessionLocal", return_value=mock_session),
            patch.dict("sys.modules", {"sentry_sdk": mock_sentry}),
        ):
            _run_cleanup_job("failing_job", failing_func)

        mock_sentry.capture_exception.assert_called_once()
        captured = mock_sentry.capture_exception.call_args[0][0]
        assert isinstance(captured, RuntimeError)
        assert "explicit-capture-test" in str(captured)

    def test_session_rollback_before_close_on_failure(self):
        """Sprint 711 Bug 2: defensive rollback before close() prevents a
        poisoned-transaction connection from being returned to the pool and
        inherited by a subsequent job. Pure cleanup hygiene; on success-path
        cleanup_func should have already committed."""
        from cleanup_scheduler import _run_cleanup_job

        def failing_func(db):
            raise RuntimeError("rollback-test")

        mock_session = MagicMock()

        with patch("database.SessionLocal", return_value=mock_session):
            _run_cleanup_job("failing_job", failing_func)

        # Both rollback and close must run, with rollback first.
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        rollback_call_index = mock_session.method_calls.index(
            next(c for c in mock_session.method_calls if c[0] == "rollback")
        )
        close_call_index = mock_session.method_calls.index(
            next(c for c in mock_session.method_calls if c[0] == "close")
        )
        assert rollback_call_index < close_call_index, "rollback must precede close"

    def test_rollback_failure_does_not_mask_close(self):
        """Sprint 711 Bug 2: if defensive rollback itself raises, the session
        must still be closed. The rollback is best-effort."""
        from cleanup_scheduler import _run_cleanup_job

        def failing_func(db):
            raise RuntimeError("compound-failure-test")

        mock_session = MagicMock()
        mock_session.rollback.side_effect = RuntimeError("rollback exploded")

        with patch("database.SessionLocal", return_value=mock_session):
            _run_cleanup_job("failing_job", failing_func)

        mock_session.close.assert_called_once()

    def test_retention_dict_summing(self):
        """is_retention=True sums dict values for records_deleted."""
        from cleanup_scheduler import _run_cleanup_job

        mock_func = MagicMock(return_value={"activity_logs": 5, "diagnostic_summaries": 3})
        mock_session = MagicMock()

        with (
            patch("database.SessionLocal", return_value=mock_session),
            patch("cleanup_scheduler.logger") as mock_logger,
        ):
            _run_cleanup_job("retention_test", mock_func, is_retention=True)

        # Should have logged with records_processed=8
        call_args = mock_logger.info.call_args
        telemetry_dict = call_args[0][1]
        assert telemetry_dict["records_processed"] == 8


# ---------------------------------------------------------------------------
# TestWatchdog
# ---------------------------------------------------------------------------


class TestWatchdog:
    """Watchdog missed-run detection."""

    def test_on_schedule_no_warning(self, caplog):
        """Jobs that ran recently produce no warnings."""
        from unittest.mock import patch

        from cleanup_scheduler import _EXPECTED_INTERVALS, _last_run_times, _watchdog

        now = datetime.now(UTC)
        for job_name in _EXPECTED_INTERVALS:
            _last_run_times[job_name] = now - timedelta(minutes=1)

        with patch("cleanup_scheduler.with_scheduler_lock") as mock_lock:
            mock_lock.return_value.__enter__ = lambda s: True
            mock_lock.return_value.__exit__ = lambda s, *a: None
            with caplog.at_level(logging.WARNING, logger="cleanup_scheduler"):
                _watchdog()

        assert "overdue" not in caplog.text

    def test_overdue_warning(self, caplog):
        """Jobs that haven't run in >2x interval produce a warning."""
        from unittest.mock import patch

        from cleanup_scheduler import _last_run_times, _watchdog

        # Set refresh_tokens as very old
        _last_run_times["refresh_tokens"] = datetime.now(UTC) - timedelta(hours=3)
        # Keep others recent
        now = datetime.now(UTC)
        _last_run_times["verification_tokens"] = now
        _last_run_times["tool_sessions"] = now
        _last_run_times["retention_cleanup"] = now

        with patch("cleanup_scheduler.with_scheduler_lock") as mock_lock:
            mock_lock.return_value.__enter__ = lambda s: True
            mock_lock.return_value.__exit__ = lambda s, *a: None
            with caplog.at_level(logging.WARNING, logger="cleanup_scheduler"):
                _watchdog()

        assert "refresh_tokens" in caplog.text
        assert "overdue" in caplog.text

    def test_never_run_skip(self, caplog):
        """Jobs that have never run (no entry in _last_run_times) are skipped."""
        from unittest.mock import patch

        from cleanup_scheduler import _last_run_times, _watchdog

        _last_run_times.clear()

        with patch("cleanup_scheduler.with_scheduler_lock") as mock_lock:
            mock_lock.return_value.__enter__ = lambda s: True
            mock_lock.return_value.__exit__ = lambda s, *a: None
            with caplog.at_level(logging.WARNING, logger="cleanup_scheduler"):
                _watchdog()

        assert "overdue" not in caplog.text


# ---------------------------------------------------------------------------
# TestSchedulerLifecycle
# ---------------------------------------------------------------------------


class TestSchedulerLifecycle:
    """init_scheduler / shutdown_scheduler lifecycle."""

    def test_disabled_noop(self, caplog):
        """When CLEANUP_SCHEDULER_ENABLED=False, init_scheduler is a no-op."""
        import cleanup_scheduler as cs

        cs.CLEANUP_SCHEDULER_ENABLED = False
        try:
            with caplog.at_level(logging.INFO, logger="cleanup_scheduler"):
                cs.init_scheduler()

            assert cs._scheduler is None
            assert "disabled" in caplog.text
        finally:
            cs.CLEANUP_SCHEDULER_ENABLED = True

    def test_init_and_shutdown(self):
        """Scheduler starts and stops without error."""
        import cleanup_scheduler as cs

        cs.CLEANUP_SCHEDULER_ENABLED = True
        try:
            cs.init_scheduler()
            assert cs._scheduler is not None
            assert cs._scheduler.running

            cs.shutdown_scheduler()
            assert cs._scheduler is None
        finally:
            # Safety cleanup
            if cs._scheduler is not None:
                cs._scheduler.shutdown(wait=False)
                cs._scheduler = None

    def test_double_shutdown_safe(self):
        """Calling shutdown_scheduler twice doesn't raise."""
        import cleanup_scheduler as cs

        cs.CLEANUP_SCHEDULER_ENABLED = True
        try:
            cs.init_scheduler()
            cs.shutdown_scheduler()
            cs.shutdown_scheduler()  # Should not raise
            assert cs._scheduler is None
        finally:
            if cs._scheduler is not None:
                cs._scheduler.shutdown(wait=False)
                cs._scheduler = None


# ---------------------------------------------------------------------------
# TestCleanupConfig
# ---------------------------------------------------------------------------


class TestCleanupConfig:
    """Config defaults for scheduler env vars."""

    def test_scheduler_enabled_default(self):
        from config import CLEANUP_SCHEDULER_ENABLED

        assert CLEANUP_SCHEDULER_ENABLED is True

    def test_refresh_token_interval_default(self):
        from config import CLEANUP_REFRESH_TOKEN_INTERVAL_MINUTES

        assert CLEANUP_REFRESH_TOKEN_INTERVAL_MINUTES == 60

    def test_verification_token_interval_default(self):
        from config import CLEANUP_VERIFICATION_TOKEN_INTERVAL_MINUTES

        assert CLEANUP_VERIFICATION_TOKEN_INTERVAL_MINUTES == 60

    def test_tool_session_interval_default(self):
        from config import CLEANUP_TOOL_SESSION_INTERVAL_MINUTES

        assert CLEANUP_TOOL_SESSION_INTERVAL_MINUTES == 30

    def test_retention_interval_default(self):
        from config import CLEANUP_RETENTION_INTERVAL_HOURS

        assert CLEANUP_RETENTION_INTERVAL_HOURS == 24


# ---------------------------------------------------------------------------
# TestMainIntegration
# ---------------------------------------------------------------------------


class TestMainIntegration:
    """Verify scheduler is wired into main.py and documented."""

    def test_main_imports_scheduler(self):
        """main.py imports init_scheduler and shutdown_scheduler."""
        main_path = Path(__file__).parent.parent / "main.py"
        source = main_path.read_text()
        assert "init_scheduler" in source
        assert "shutdown_scheduler" in source

    def test_env_example_documents_scheduler(self):
        """`.env.example` documents all 5 scheduler config vars."""
        env_path = Path(__file__).parent.parent / ".env.example"
        source = env_path.read_text()
        assert "CLEANUP_SCHEDULER_ENABLED" in source
        assert "CLEANUP_REFRESH_TOKEN_INTERVAL_MINUTES" in source
        assert "CLEANUP_VERIFICATION_TOKEN_INTERVAL_MINUTES" in source
        assert "CLEANUP_TOOL_SESSION_INTERVAL_MINUTES" in source
        assert "CLEANUP_RETENTION_INTERVAL_HOURS" in source


# ---------------------------------------------------------------------------
# TestJobWrappers
# ---------------------------------------------------------------------------


class TestJobWrappers:
    """Verify the thin job wrappers call _run_cleanup_job correctly."""

    def test_job_refresh_tokens(self):
        from cleanup_scheduler import _job_refresh_tokens

        with patch("cleanup_scheduler._run_cleanup_job") as mock_run:
            _job_refresh_tokens()
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == "refresh_tokens"

    def test_job_verification_tokens(self):
        from cleanup_scheduler import _job_verification_tokens

        with patch("cleanup_scheduler._run_cleanup_job") as mock_run:
            _job_verification_tokens()
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == "verification_tokens"

    def test_job_tool_sessions(self):
        from cleanup_scheduler import _job_tool_sessions

        with patch("cleanup_scheduler._run_cleanup_job") as mock_run:
            _job_tool_sessions()
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == "tool_sessions"

    def test_job_retention_cleanup(self):
        from cleanup_scheduler import _job_retention_cleanup

        with patch("cleanup_scheduler._run_cleanup_job") as mock_run:
            _job_retention_cleanup()
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == "retention_cleanup"
            assert mock_run.call_args[1]["is_retention"] is True


# ---------------------------------------------------------------------------
# TestConftest
# ---------------------------------------------------------------------------


class TestConftest:
    """Verify the autouse fixture disables the scheduler."""

    def test_scheduler_disabled_in_tests(self):
        """The conftest autouse fixture sets CLEANUP_SCHEDULER_ENABLED=False."""
        import cleanup_scheduler as cs

        assert cs.CLEANUP_SCHEDULER_ENABLED is False
