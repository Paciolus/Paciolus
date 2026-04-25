"""Sprint 718 — Cookie / Bearer auth parity tests.

Production browser clients send the access token via HttpOnly cookie;
non-browser API clients use the ``Authorization: Bearer …`` header.
Every auth-extracting helper must work for *both* sources, otherwise we
silently degrade security guarantees on one path.

The 2026-04-24 security review (H-01) found that
``CSRFMiddleware._extract_user_id_from_auth`` only read Bearer headers,
so the CSRF user-binding check short-circuited to ``expected_user_id=None``
on every browser POST/PUT/DELETE/PATCH. This test prevents that class
of regression.

Coverage:
    - ``security_middleware.CSRFMiddleware._extract_user_id_from_auth``:
      yields the same user_id from Bearer header AND from
      ACCESS_COOKIE_NAME cookie.
    - ``auth.resolve_access_token``: yields the same token whether the
      caller passed a Bearer header or set the ACCESS_COOKIE_NAME cookie.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _make_request_stub(headers: dict[str, str] | None = None, cookies: dict[str, str] | None = None):
    """Minimal Request-like stub for middleware introspection."""
    request = MagicMock()
    request.headers = headers or {}
    request.cookies = cookies or {}
    return request


@pytest.fixture
def access_token_for_user_42() -> str:
    """Create a real (non-expired) JWT for user_id=42."""
    from auth import create_access_token

    token, _ = create_access_token(
        user_id=42,
        email="parity@example.com",
        password_changed_at=None,
        tier="solo",
    )
    return token


# ───────────────────────── CSRFMiddleware._extract_user_id_from_auth ─────


def test_csrf_extract_user_id_via_bearer_header(access_token_for_user_42: str):
    from config import ACCESS_COOKIE_NAME
    from security_middleware import CSRFMiddleware

    middleware = CSRFMiddleware(app=MagicMock())
    request = _make_request_stub(
        headers={"Authorization": f"Bearer {access_token_for_user_42}"},
    )
    extracted = middleware._extract_user_id_from_auth(request)
    assert extracted == "42"
    # Cookie path must independently work — verified next.
    assert ACCESS_COOKIE_NAME  # smoke


def test_csrf_extract_user_id_via_cookie(access_token_for_user_42: str):
    """Sprint 718: production browser path uses HttpOnly cookies. The
    middleware must read the cookie when the Authorization header is
    absent. Pre-Sprint-718 this returned None for every browser POST,
    silently disabling CSRF user-binding."""
    from config import ACCESS_COOKIE_NAME
    from security_middleware import CSRFMiddleware

    middleware = CSRFMiddleware(app=MagicMock())
    request = _make_request_stub(
        cookies={ACCESS_COOKIE_NAME: access_token_for_user_42},
    )
    extracted = middleware._extract_user_id_from_auth(request)
    assert extracted == "42", "CSRF user-binding disabled for browser cookie auth — Sprint 718 H-01 regression."


def test_csrf_extract_user_id_bearer_wins_over_cookie(access_token_for_user_42: str):
    """When both are present, Bearer takes precedence. Matches
    `auth.resolve_access_token` semantics."""
    from auth import create_access_token
    from config import ACCESS_COOKIE_NAME
    from security_middleware import CSRFMiddleware

    other_token, _ = create_access_token(
        user_id=99,
        email="other@example.com",
        password_changed_at=None,
        tier="solo",
    )

    middleware = CSRFMiddleware(app=MagicMock())
    request = _make_request_stub(
        headers={"Authorization": f"Bearer {access_token_for_user_42}"},
        cookies={ACCESS_COOKIE_NAME: other_token},
    )
    extracted = middleware._extract_user_id_from_auth(request)
    assert extracted == "42"


def test_csrf_extract_user_id_returns_none_when_no_token():
    from security_middleware import CSRFMiddleware

    middleware = CSRFMiddleware(app=MagicMock())
    request = _make_request_stub()
    assert middleware._extract_user_id_from_auth(request) is None


def test_csrf_extract_user_id_returns_none_for_invalid_token():
    from config import ACCESS_COOKIE_NAME
    from security_middleware import CSRFMiddleware

    middleware = CSRFMiddleware(app=MagicMock())

    bad_header = _make_request_stub(headers={"Authorization": "Bearer not.a.jwt"})
    assert middleware._extract_user_id_from_auth(bad_header) is None

    bad_cookie = _make_request_stub(cookies={ACCESS_COOKIE_NAME: "not.a.jwt"})
    assert middleware._extract_user_id_from_auth(bad_cookie) is None


# ───────────────────────── auth.resolve_access_token ─────────────────────


def test_resolve_access_token_bearer_path(access_token_for_user_42: str):
    from auth import resolve_access_token

    request = _make_request_stub()
    resolved = resolve_access_token(request=request, header_token=access_token_for_user_42)
    assert resolved == access_token_for_user_42


def test_resolve_access_token_cookie_path(access_token_for_user_42: str):
    """When no Bearer header is supplied, the cookie wins. Production
    browser path."""
    from auth import resolve_access_token
    from config import ACCESS_COOKIE_NAME

    request = _make_request_stub(cookies={ACCESS_COOKIE_NAME: access_token_for_user_42})
    resolved = resolve_access_token(request=request, header_token=None)
    assert resolved == access_token_for_user_42


def test_resolve_access_token_no_token_returns_none():
    from auth import resolve_access_token

    request = _make_request_stub()
    assert resolve_access_token(request=request, header_token=None) is None
