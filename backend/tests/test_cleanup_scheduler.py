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
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


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

    def test_session_always_closed_on_success(self):
        """Session is closed even when cleanup returns 0."""
        from cleanup_scheduler import _run_cleanup_job

        mock_session = MagicMock()
        mock_func = MagicMock(return_value=0)

        with patch("database.SessionLocal", return_value=mock_session):
            _run_cleanup_job("zero_job", mock_func)

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
        from cleanup_scheduler import _EXPECTED_INTERVALS, _last_run_times, _watchdog

        now = datetime.now(UTC)
        for job_name in _EXPECTED_INTERVALS:
            _last_run_times[job_name] = now - timedelta(minutes=1)

        with caplog.at_level(logging.WARNING, logger="cleanup_scheduler"):
            _watchdog()

        assert "overdue" not in caplog.text

    def test_overdue_warning(self, caplog):
        """Jobs that haven't run in >2x interval produce a warning."""
        from cleanup_scheduler import _last_run_times, _watchdog

        # Set refresh_tokens as very old
        _last_run_times["refresh_tokens"] = datetime.now(UTC) - timedelta(hours=3)
        # Keep others recent
        now = datetime.now(UTC)
        _last_run_times["verification_tokens"] = now
        _last_run_times["tool_sessions"] = now
        _last_run_times["retention_cleanup"] = now

        with caplog.at_level(logging.WARNING, logger="cleanup_scheduler"):
            _watchdog()

        assert "refresh_tokens" in caplog.text
        assert "overdue" in caplog.text

    def test_never_run_skip(self, caplog):
        """Jobs that have never run (no entry in _last_run_times) are skipped."""
        from cleanup_scheduler import _last_run_times, _watchdog

        _last_run_times.clear()

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
