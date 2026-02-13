"""
Tests for CSRF middleware and token management.
Sprint 200: CSRF & CORS Hardening

Tests cover:
- CSRF token generation and validation
- Token expiration and cleanup
- CSRFMiddleware exempt path handling
- CSRFMiddleware blocks mutations without valid token
- CSRFMiddleware allows GET/OPTIONS (safe methods)
- Updated exempt paths include all auth/public endpoints
- CORS configuration uses explicit methods/headers
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import security_middleware as _sm
from security_middleware import (
    generate_csrf_token,
    validate_csrf_token,
    _csrf_tokens,
    _cleanup_expired_tokens,
    CSRF_TOKEN_EXPIRY_MINUTES,
    CSRF_EXEMPT_PATHS,
    CSRF_REQUIRED_METHODS,
    CSRFMiddleware,
)


# =============================================================================
# CSRF Token Generation & Validation
# =============================================================================


class TestCsrfTokenGeneration:
    """Tests for CSRF token generation."""

    def setup_method(self):
        """Clear token store before each test."""
        _csrf_tokens.clear()

    def test_generates_unique_tokens(self):
        """Each call should produce a unique token."""
        t1 = generate_csrf_token()
        t2 = generate_csrf_token()
        assert t1 != t2

    def test_generated_token_is_hex_string(self):
        """Token should be a hex string of expected length."""
        token = generate_csrf_token()
        assert isinstance(token, str)
        # 32 bytes = 64 hex chars
        assert len(token) == 64
        int(token, 16)  # Should not raise

    def test_generated_token_stored_in_memory(self):
        """Token should be stored in the in-memory dict."""
        token = generate_csrf_token()
        assert token in _csrf_tokens

    def test_generated_token_has_timestamp(self):
        """Stored token should have a datetime timestamp."""
        token = generate_csrf_token()
        assert isinstance(_csrf_tokens[token], datetime)


class TestCsrfTokenValidation:
    """Tests for CSRF token validation."""

    def setup_method(self):
        _csrf_tokens.clear()

    def test_valid_token_returns_true(self):
        """A freshly generated token should validate."""
        token = generate_csrf_token()
        assert validate_csrf_token(token) is True

    def test_empty_token_returns_false(self):
        """Empty string should fail validation."""
        assert validate_csrf_token("") is False

    def test_none_token_returns_false(self):
        """None should fail validation."""
        assert validate_csrf_token(None) is False

    def test_unknown_token_returns_false(self):
        """A random token not in the store should fail."""
        assert validate_csrf_token("not-a-real-token") is False

    def test_expired_token_returns_false(self):
        """A token past its expiry should fail validation."""
        token = generate_csrf_token()
        # Backdate the token to make it expired
        _csrf_tokens[token] = datetime.now(UTC) - timedelta(
            minutes=CSRF_TOKEN_EXPIRY_MINUTES + 1
        )
        assert validate_csrf_token(token) is False

    def test_expired_token_is_removed_from_store(self):
        """Validating an expired token should remove it."""
        token = generate_csrf_token()
        _csrf_tokens[token] = datetime.now(UTC) - timedelta(
            minutes=CSRF_TOKEN_EXPIRY_MINUTES + 1
        )
        validate_csrf_token(token)
        assert token not in _csrf_tokens


class TestCsrfTokenCleanup:
    """Tests for expired token cleanup."""

    def setup_method(self):
        _csrf_tokens.clear()

    def test_cleanup_removes_expired_tokens(self):
        """Expired tokens should be removed by cleanup."""
        t1 = generate_csrf_token()
        t2 = generate_csrf_token()
        # Expire t1
        _csrf_tokens[t1] = datetime.now(UTC) - timedelta(
            minutes=CSRF_TOKEN_EXPIRY_MINUTES + 1
        )
        _cleanup_expired_tokens()
        assert t1 not in _csrf_tokens
        assert t2 in _csrf_tokens

    def test_cleanup_preserves_fresh_tokens(self):
        """Fresh tokens should survive cleanup."""
        t1 = generate_csrf_token()
        _cleanup_expired_tokens()
        assert t1 in _csrf_tokens


# =============================================================================
# CSRF Exempt Paths
# =============================================================================


class TestCsrfExemptPaths:
    """Verify the exempt path set includes all required paths."""

    def test_auth_login_exempt(self):
        assert "/auth/login" in CSRF_EXEMPT_PATHS

    def test_auth_register_exempt(self):
        assert "/auth/register" in CSRF_EXEMPT_PATHS

    def test_auth_refresh_exempt(self):
        """Sprint 200: refresh must be exempt (called by 401 interceptor)."""
        assert "/auth/refresh" in CSRF_EXEMPT_PATHS

    def test_auth_logout_exempt(self):
        """Sprint 200: logout must be exempt (called during logout flow)."""
        assert "/auth/logout" in CSRF_EXEMPT_PATHS

    def test_auth_verify_email_exempt(self):
        """Sprint 200: verify-email called from email link without session."""
        assert "/auth/verify-email" in CSRF_EXEMPT_PATHS

    def test_auth_csrf_exempt(self):
        assert "/auth/csrf" in CSRF_EXEMPT_PATHS

    def test_contact_submit_exempt(self):
        """Sprint 200: public form with honeypot + rate limit."""
        assert "/contact/submit" in CSRF_EXEMPT_PATHS

    def test_waitlist_exempt(self):
        """Sprint 200: public form."""
        assert "/waitlist" in CSRF_EXEMPT_PATHS

    def test_docs_exempt(self):
        assert "/docs" in CSRF_EXEMPT_PATHS

    def test_openapi_exempt(self):
        assert "/openapi.json" in CSRF_EXEMPT_PATHS


# =============================================================================
# CSRF Required Methods
# =============================================================================


class TestCsrfRequiredMethods:
    """Verify the required methods set is correct."""

    def test_post_requires_csrf(self):
        assert "POST" in CSRF_REQUIRED_METHODS

    def test_put_requires_csrf(self):
        assert "PUT" in CSRF_REQUIRED_METHODS

    def test_delete_requires_csrf(self):
        assert "DELETE" in CSRF_REQUIRED_METHODS

    def test_patch_requires_csrf(self):
        assert "PATCH" in CSRF_REQUIRED_METHODS

    def test_get_does_not_require_csrf(self):
        assert "GET" not in CSRF_REQUIRED_METHODS

    def test_options_does_not_require_csrf(self):
        assert "OPTIONS" not in CSRF_REQUIRED_METHODS


# =============================================================================
# CSRFMiddleware Integration
# =============================================================================


class TestCsrfMiddleware:
    """Tests for the CSRFMiddleware dispatch logic."""

    def setup_method(self):
        """Clear token store and restore original validate_csrf_token.

        The conftest.py autouse fixture patches validate_csrf_token to always
        return True for API tests. We need the real function here to test
        that the middleware actually blocks invalid/missing tokens.
        """
        _csrf_tokens.clear()
        _sm.validate_csrf_token = validate_csrf_token

    def teardown_method(self):
        """Re-apply the conftest bypass for other API tests."""
        _sm.validate_csrf_token = lambda token: True

    def _make_request(self, method: str, path: str, csrf_token: str = None):
        """Create a mock Starlette Request."""
        request = MagicMock()
        request.method = method
        request.url.path = path
        headers = {}
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: headers.get(key, default)
        return request

    @pytest.mark.asyncio
    async def test_get_request_passes_through(self):
        """GET requests should not require CSRF token."""
        middleware = CSRFMiddleware(app=MagicMock())
        request = self._make_request("GET", "/clients")
        call_next = AsyncMock(return_value=MagicMock())

        response = await middleware.dispatch(request, call_next)
        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_options_request_passes_through(self):
        """OPTIONS (preflight) requests should not require CSRF token."""
        middleware = CSRFMiddleware(app=MagicMock())
        request = self._make_request("OPTIONS", "/clients")
        call_next = AsyncMock(return_value=MagicMock())

        response = await middleware.dispatch(request, call_next)
        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_exempt_path_passes_through(self):
        """POST to an exempt path should not require CSRF token."""
        middleware = CSRFMiddleware(app=MagicMock())
        request = self._make_request("POST", "/auth/login")
        call_next = AsyncMock(return_value=MagicMock())

        response = await middleware.dispatch(request, call_next)
        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_post_without_csrf_blocked(self):
        """POST to a protected path without CSRF should raise 403."""
        middleware = CSRFMiddleware(app=MagicMock())
        request = self._make_request("POST", "/clients")
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403
        assert b"CSRF" in response.body
        call_next.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_post_with_invalid_csrf_blocked(self):
        """POST with an invalid CSRF token should raise 403."""
        middleware = CSRFMiddleware(app=MagicMock())
        request = self._make_request("POST", "/clients", csrf_token="bogus-token")
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_post_with_valid_csrf_passes(self):
        """POST with a valid CSRF token should pass through."""
        middleware = CSRFMiddleware(app=MagicMock())
        token = generate_csrf_token()
        request = self._make_request("POST", "/clients", csrf_token=token)
        call_next = AsyncMock(return_value=MagicMock())

        response = await middleware.dispatch(request, call_next)
        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_put_with_valid_csrf_passes(self):
        """PUT with a valid CSRF token should pass through."""
        middleware = CSRFMiddleware(app=MagicMock())
        token = generate_csrf_token()
        request = self._make_request("PUT", "/clients/1", csrf_token=token)
        call_next = AsyncMock(return_value=MagicMock())

        response = await middleware.dispatch(request, call_next)
        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_delete_without_csrf_blocked(self):
        """DELETE without CSRF should raise 403."""
        middleware = CSRFMiddleware(app=MagicMock())
        request = self._make_request("DELETE", "/clients/1")
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_patch_without_csrf_blocked(self):
        """PATCH without CSRF should raise 403."""
        middleware = CSRFMiddleware(app=MagicMock())
        request = self._make_request("PATCH", "/clients/1")
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_all_new_exempt_paths_pass(self):
        """All Sprint 200 exempt paths should pass without CSRF."""
        middleware = CSRFMiddleware(app=MagicMock())
        new_exemptions = [
            "/auth/refresh",
            "/auth/logout",
            "/auth/verify-email",
            "/contact/submit",
            "/waitlist",
        ]
        for path in new_exemptions:
            call_next = AsyncMock(return_value=MagicMock())
            request = self._make_request("POST", path)
            response = await middleware.dispatch(request, call_next)
            call_next.assert_awaited_once_with(request), f"Failed for {path}"

    @pytest.mark.asyncio
    async def test_expired_csrf_token_blocked(self):
        """POST with an expired CSRF token should raise 403."""
        middleware = CSRFMiddleware(app=MagicMock())
        token = generate_csrf_token()
        # Expire the token
        _csrf_tokens[token] = datetime.now(UTC) - timedelta(
            minutes=CSRF_TOKEN_EXPIRY_MINUTES + 1
        )
        request = self._make_request("POST", "/audit/adjustments", csrf_token=token)
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403


# =============================================================================
# CORS Configuration
# =============================================================================


class TestCorsConfiguration:
    """Verify CORS middleware is configured with explicit methods/headers."""

    def test_cors_middleware_registered_with_explicit_methods(self):
        """CORS should use explicit method list, not wildcard."""
        from main import app

        # Find CORSMiddleware in the middleware stack
        cors_found = False
        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "CORSMiddleware":
                cors_found = True
                kwargs = middleware.kwargs
                methods = kwargs.get("allow_methods", [])
                assert "*" not in methods, "CORS should not use wildcard methods"
                assert "GET" in methods
                assert "POST" in methods
                assert "PUT" in methods
                assert "PATCH" in methods
                assert "DELETE" in methods
                assert "OPTIONS" in methods
                break
        assert cors_found, "CORSMiddleware not found in app middleware"

    def test_cors_middleware_has_explicit_headers(self):
        """CORS should list explicit allowed headers."""
        from main import app

        for middleware in app.user_middleware:
            if middleware.cls.__name__ == "CORSMiddleware":
                kwargs = middleware.kwargs
                headers = kwargs.get("allow_headers", [])
                assert "*" not in headers, "CORS should not use wildcard headers"
                assert "Authorization" in headers
                assert "Content-Type" in headers
                assert "X-CSRF-Token" in headers
                assert "Accept" in headers
                break

    def test_csrf_middleware_registered(self):
        """CSRFMiddleware should be registered in app middleware."""
        from main import app

        csrf_found = any(
            m.cls.__name__ == "CSRFMiddleware"
            for m in app.user_middleware
        )
        assert csrf_found, "CSRFMiddleware not found in app middleware"
