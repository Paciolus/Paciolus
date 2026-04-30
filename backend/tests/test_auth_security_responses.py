"""
Tests for services.auth.security_responses (Sprint 747).

Pins the AUDIT-07 F4 enumeration-safety contract: the same 401 body /
headers must come back regardless of why the credential check failed.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from services.auth.security_responses import raise_invalid_credentials


def test_raises_401_with_stable_body() -> None:
    with pytest.raises(HTTPException) as excinfo:
        raise_invalid_credentials()
    exc = excinfo.value
    assert exc.status_code == 401
    assert exc.detail == {"message": "Invalid email or password"}


def test_includes_www_authenticate_header() -> None:
    with pytest.raises(HTTPException) as excinfo:
        raise_invalid_credentials()
    assert excinfo.value.headers == {"WWW-Authenticate": "Bearer"}


def test_repeated_calls_return_identical_response_shape() -> None:
    """Stability: AUDIT-07 F4 requires the body to never reveal which
    branch of the login pipeline failed (wrong-password vs unknown-email
    vs locked vs IP-blocked). The helper enforces that by being the only
    way to produce the response."""
    detail_a = None
    headers_a = None
    for _ in range(3):
        with pytest.raises(HTTPException) as excinfo:
            raise_invalid_credentials()
        if detail_a is None:
            detail_a = excinfo.value.detail
            headers_a = excinfo.value.headers
        else:
            assert excinfo.value.detail == detail_a
            assert excinfo.value.headers == headers_a
