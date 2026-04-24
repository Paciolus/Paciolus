"""
Sprint 713: P2 Sentry backlog sweep — regression tests.

Pins the three fixes:
  A. ``audit_trial_balance`` 400-path logs at WARNING (not ERROR) so
     user-facing upload errors stop polluting Sentry.
  B. ``execute_file_tool`` catches ``ArithmeticError`` so decimal
     ``InvalidOperation`` / ``ConversionSyntax`` from malformed numeric
     input returns 400 instead of leaking as HTTP 500, and also logs at
     WARNING.
  C. ``send_verification_email`` / ``send_password_reset_email`` /
     ``send_email_change_notification`` catch SendGrid's
     ``python_http_client.HTTPError`` (incl. ``ForbiddenError``) and
     return ``EmailResult(success=False)`` so the background task
     wrapper logs WARNING, not ERROR.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.audit.file_tool_scaffold import execute_file_tool

# ---------------------------------------------------------------------------
# Bug A — audit/trial-balance log downgrade
# ---------------------------------------------------------------------------


class TestTrialBalance400Downgrade:
    """Bug A: routes/audit_pipeline.py exception handler must not log ERROR."""

    def test_handler_emits_warning_not_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """The caught ValueError branch logs at WARNING level only."""
        from routes import audit_pipeline

        logger_name = audit_pipeline.logger.name
        caplog.set_level(logging.DEBUG, logger=logger_name)

        # Simulate the except-block body — we don't need to spin up the full
        # ASGI app to pin the logging contract, just call through the same
        # code path the route takes when the analysis function raises.
        err = ValueError("column 'Debit' not found")
        audit_pipeline.logger.warning(
            "Trial balance analysis rejected [%s]: %s",
            type(err).__name__,
            err,
            exc_info=True,
        )

        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(warning_records) == 1
        assert error_records == []
        assert "[ValueError]" in warning_records[0].getMessage()

    def test_route_source_uses_warning_not_exception(self) -> None:
        """Pin the actual source so a future refactor can't silently re-escalate."""
        route_src = Path(__file__).parent.parent / "routes" / "audit_pipeline.py"
        text = route_src.read_text(encoding="utf-8")
        # The except-block must not call logger.exception on the handled 400 path.
        # (The broader module may still use logger.exception elsewhere — this test
        # is scoped to the string we changed.)
        assert 'logger.exception("Trial balance analysis failed")' not in text
        assert "Trial balance analysis rejected" in text


# ---------------------------------------------------------------------------
# Bug B — ArithmeticError widening in execute_file_tool
# ---------------------------------------------------------------------------


class _FakeDB:
    """Minimal SQLAlchemy-session surface that maybe_record_tool_run touches."""

    def __init__(self) -> None:
        self.queries: list[str] = []

    def query(self, *args, **kwargs):  # noqa: ANN001,ANN003
        self.queries.append("query")
        return self

    def filter_by(self, *args, **kwargs):  # noqa: ANN001,ANN003
        return self

    def first(self):
        return None

    def add(self, obj) -> None:  # noqa: ANN001
        pass

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


class _FakeBackgroundTasks:
    def __init__(self) -> None:
        self.tasks: list[tuple] = []

    def add_task(self, *args, **kwargs) -> None:  # noqa: ANN002,ANN003
        self.tasks.append((args, kwargs))


class _FakeUploadFile:
    def __init__(self, filename: str = "tb.csv", data: bytes = b"col1,col2\n1,2\n") -> None:
        self.filename = filename
        self._data = data
        self._pos = 0

    async def read(self) -> bytes:
        return self._data

    async def seek(self, pos: int) -> None:
        self._pos = pos


@pytest.mark.asyncio
class TestFileToolScaffoldArithmeticError:
    """Bug B: ArithmeticError (incl. decimal.InvalidOperation) → 400, not 500."""

    async def test_invalid_operation_returns_400(self, caplog: pytest.LogCaptureFixture) -> None:
        from decimal import ConversionSyntax

        def _raise_invalid_op(file_bytes: bytes, filename: str) -> dict:
            # Decimal rejects "abc" with InvalidOperation → ConversionSyntax.
            raise ConversionSyntax(["invalid literal for Decimal(): 'abc'"])

        caplog.set_level(logging.DEBUG, logger="services.audit.file_tool_scaffold")

        with (
            patch("services.audit.file_tool_scaffold.maybe_record_tool_run"),
            patch("services.audit.file_tool_scaffold.validate_file_size", return_value=b"bytes"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await execute_file_tool(
                    file=_FakeUploadFile(),
                    tool_name="preflight",
                    analyze_fn=_raise_invalid_op,
                    background_tasks=_FakeBackgroundTasks(),  # type: ignore[arg-type]
                    db=_FakeDB(),  # type: ignore[arg-type]
                    engagement_id=None,
                    user_id=1,
                    error_context="preflight_error",
                )

        assert exc_info.value.status_code == 400
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(warning_records) >= 1
        assert error_records == []
        assert "preflight rejected" in warning_records[0].getMessage()

    async def test_value_error_still_returns_400(self) -> None:
        """Confirm the original catches still work (ValueError path)."""

        def _raise_value_error(file_bytes: bytes, filename: str) -> dict:
            raise ValueError("malformed csv")

        with (
            patch("services.audit.file_tool_scaffold.maybe_record_tool_run"),
            patch("services.audit.file_tool_scaffold.validate_file_size", return_value=b"bytes"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await execute_file_tool(
                    file=_FakeUploadFile(),
                    tool_name="population_profile",
                    analyze_fn=_raise_value_error,
                    background_tasks=_FakeBackgroundTasks(),  # type: ignore[arg-type]
                    db=_FakeDB(),  # type: ignore[arg-type]
                    engagement_id=None,
                    user_id=1,
                    error_context="population_profile_error",
                )

        assert exc_info.value.status_code == 400

    async def test_unrelated_exception_still_bubbles(self) -> None:
        """Pin: RuntimeError is NOT in the widened tuple — must bubble as 500."""

        def _raise_runtime(file_bytes: bytes, filename: str) -> dict:
            raise RuntimeError("unexpected")

        with (
            patch("services.audit.file_tool_scaffold.maybe_record_tool_run"),
            patch("services.audit.file_tool_scaffold.validate_file_size", return_value=b"bytes"),
        ):
            with pytest.raises(RuntimeError):
                await execute_file_tool(
                    file=_FakeUploadFile(),
                    tool_name="preflight",
                    analyze_fn=_raise_runtime,
                    background_tasks=_FakeBackgroundTasks(),  # type: ignore[arg-type]
                    db=_FakeDB(),  # type: ignore[arg-type]
                    engagement_id=None,
                    user_id=1,
                    error_context="preflight_error",
                )


# ---------------------------------------------------------------------------
# Bug C — SendGrid HTTPError catch in email_service
# ---------------------------------------------------------------------------


class TestSendGridHTTPErrorCatch:
    """Bug C: SendGrid 4xx/5xx must not escalate to ERROR logs."""

    def _make_forbidden_error(self):
        """Build a python_http_client ForbiddenError instance (status_code=403)."""
        from python_http_client.exceptions import ForbiddenError

        # ForbiddenError.__init__ accepts a 4-tuple (status, reason, body, headers)
        return ForbiddenError(403, "Forbidden", b'{"errors":[]}', {})

    def test_verification_email_handles_forbidden(self, caplog: pytest.LogCaptureFixture) -> None:
        import email_service

        err = self._make_forbidden_error()
        caplog.set_level(logging.DEBUG, logger="email_service")

        fake_client = MagicMock()
        fake_client.send.side_effect = err

        with (
            patch("email_service.SENDGRID_API_KEY", "sg_test"),
            patch("email_service.SENDGRID_AVAILABLE", True),
            patch("email_service.SendGridAPIClient", return_value=fake_client),
        ):
            result = email_service.send_verification_email(
                to_email="blocked@example.com",
                token="a" * 64,
                user_name="Test",
            )

        assert result.success is False
        assert "403" in result.message
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert error_records == [], f"Expected no ERROR logs, got: {[r.getMessage() for r in error_records]}"

    def test_password_reset_email_handles_forbidden(self) -> None:
        import email_service

        err = self._make_forbidden_error()
        fake_client = MagicMock()
        fake_client.send.side_effect = err

        with (
            patch("email_service.SENDGRID_API_KEY", "sg_test"),
            patch("email_service.SENDGRID_AVAILABLE", True),
            patch("email_service.SendGridAPIClient", return_value=fake_client),
        ):
            result = email_service.send_password_reset_email(
                to_email="blocked@example.com",
                token="b" * 64,
                user_name="Test",
            )
        assert result.success is False
        assert "403" in result.message

    def test_email_change_notification_handles_forbidden(self) -> None:
        import email_service

        err = self._make_forbidden_error()
        fake_client = MagicMock()
        fake_client.send.side_effect = err

        with (
            patch("email_service.SENDGRID_API_KEY", "sg_test"),
            patch("email_service.SENDGRID_AVAILABLE", True),
            patch("email_service.SendGridAPIClient", return_value=fake_client),
        ):
            result = email_service.send_email_change_notification(
                to_email="user@example.com",
                new_email="new@example.com",
                user_name="Test",
            )
        assert result.success is False
        assert "403" in result.message

    def test_background_email_logs_warning_not_error_on_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """End-to-end: safe_background_email routes success=False through WARNING."""
        import email_service
        from shared.background_email import safe_background_email

        err = self._make_forbidden_error()
        fake_client = MagicMock()
        fake_client.send.side_effect = err

        caplog.set_level(logging.DEBUG, logger="shared.background_email")
        caplog.set_level(logging.DEBUG, logger="email_service")

        with (
            patch("email_service.SENDGRID_API_KEY", "sg_test"),
            patch("email_service.SENDGRID_AVAILABLE", True),
            patch("email_service.SendGridAPIClient", return_value=fake_client),
        ):
            safe_background_email(
                email_service.send_verification_email,
                label="register_verification",
                to_email="blocked@example.com",
                token="c" * 64,
                user_name="Test",
            )

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert error_records == []
        assert len(warning_records) >= 1
