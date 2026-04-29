"""
Tests for shared.route_errors (Sprint 745).
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from shared.route_errors import raise_http_error


def test_raises_with_user_message_when_no_exception() -> None:
    with pytest.raises(HTTPException) as excinfo:
        raise_http_error(400, label="upload_format", user_message="Bad file format.")
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Bad file format."


def test_default_message_when_neither_supplied() -> None:
    with pytest.raises(HTTPException) as excinfo:
        raise_http_error(404, label="not_found")
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "An error occurred."


def test_user_message_wins_over_exception_message() -> None:
    with pytest.raises(HTTPException) as excinfo:
        raise_http_error(
            400,
            label="business",
            user_message="Try again with valid input.",
            exception=ValueError("internal SQL leak details"),
        )
    assert excinfo.value.detail == "Try again with valid input."


def test_exception_only_uses_sanitize_error() -> None:
    """Without user_message, the exception drives the sanitized detail."""
    err = ValueError("could not convert 'abc' to float")
    with pytest.raises(HTTPException) as excinfo:
        raise_http_error(400, label="business", exception=err)
    detail = excinfo.value.detail
    assert isinstance(detail, str)
    # error_messages.py maps ValueError-convert patterns to a friendly message
    assert "non-numeric values" in detail


def test_passthrough_returns_original_message_when_safe() -> None:
    err = ValueError("Engagement is locked: cannot post adjustment")
    with pytest.raises(HTTPException) as excinfo:
        raise_http_error(409, label="engagement_lock", exception=err, allow_passthrough=True)
    detail = excinfo.value.detail
    assert "Engagement is locked" in detail


def test_passthrough_blocks_messages_with_internal_details() -> None:
    err = ValueError('Traceback (most recent call last):\n  File "/app/route.py", line 12')
    with pytest.raises(HTTPException) as excinfo:
        raise_http_error(500, label="boom", exception=err, allow_passthrough=True)
    detail = excinfo.value.detail
    # Internal detail patterns short-circuit passthrough → fallback message
    assert isinstance(detail, str)
    assert "Traceback" not in detail
    assert "/app/" not in detail


def test_status_code_is_propagated() -> None:
    for code in (400, 401, 403, 404, 409, 422, 500, 502, 503):
        with pytest.raises(HTTPException) as excinfo:
            raise_http_error(code, label="x", user_message="msg")
        assert excinfo.value.status_code == code
