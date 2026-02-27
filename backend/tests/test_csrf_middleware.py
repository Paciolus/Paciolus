"""
Tests for CSRF middleware and token management.
Sprint 200: CSRF & CORS Hardening
Sprint 261: Updated for stateless HMAC CSRF (no in-memory dict)
Packet 6: Secret separation (CSRF_SECRET_KEY ≠ JWT_SECRET_KEY)

Tests cover:
- CSRF token generation and validation (stateless HMAC)
- Token expiration (via timestamp)
- CSRFMiddleware exempt path handling
- CSRFMiddleware blocks mutations without valid token
- CSRFMiddleware allows GET/OPTIONS (safe methods)
- Updated exempt paths include all auth/public endpoints
- CORS configuration uses explicit methods/headers
- Secret separation: JWT key changes do not affect CSRF validation
- Exempt path policy guardrails (refresh/logout assumptions)
"""

import ast
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import security_middleware as _sm
from security_middleware import (
    CSRF_EXEMPT_PATHS,
    CSRF_REQUIRED_METHODS,
    CSRF_TOKEN_EXPIRY_MINUTES,
    CSRFMiddleware,
    generate_csrf_token,
    validate_csrf_token,
)

# =============================================================================
# CSRF Token Generation & Validation (Sprint 261: Stateless HMAC)
# =============================================================================


class TestCsrfTokenGeneration:
    """Tests for CSRF token generation (stateless HMAC, user-bound)."""

    def test_generates_unique_tokens(self):
        """Each call should produce a unique token."""
        t1 = generate_csrf_token("test-user-id")
        t2 = generate_csrf_token("test-user-id")
        assert t1 != t2

    def test_generated_token_format(self):
        """Token should be nonce:timestamp:user_id:signature format (4 parts)."""
        token = generate_csrf_token("test-user-id")
        parts = token.split(":")
        assert len(parts) == 4
        nonce, timestamp, user_id, signature = parts
        assert isinstance(nonce, str)
        assert len(nonce) == 32  # 16 bytes hex
        int(timestamp)  # Should not raise
        assert user_id == "test-user-id"
        assert len(signature) == 64  # SHA-256 hex

    def test_generated_token_validates(self):
        """A freshly generated token should validate."""
        token = generate_csrf_token("test-user-id")
        assert validate_csrf_token(token) is True

    def test_token_has_recent_timestamp(self):
        """Token timestamp should be close to current time."""
        token = generate_csrf_token("test-user-id")
        ts = int(token.split(":")[1])
        assert abs(time.time() - ts) < 2


class TestCsrfTokenValidation:
    """Tests for CSRF token validation (stateless HMAC, user-bound)."""

    def test_valid_token_returns_true(self):
        """A freshly generated token should validate."""
        token = generate_csrf_token("test-uid")
        assert validate_csrf_token(token) is True

    def test_empty_token_returns_false(self):
        """Empty string should fail validation."""
        assert validate_csrf_token("") is False

    def test_none_token_returns_false(self):
        """None should fail validation."""
        assert validate_csrf_token(None) is False

    def test_unknown_token_returns_false(self):
        """A random token not matching HMAC should fail."""
        assert validate_csrf_token("not-a-real-token") is False

    def test_expired_token_returns_false(self):
        """A token past its expiry should fail validation."""
        import hashlib
        import hmac as _hmac

        from config import CSRF_SECRET_KEY

        nonce = "a" * 32
        old_ts = str(int(time.time()) - (CSRF_TOKEN_EXPIRY_MINUTES + 1) * 60)
        payload = f"{nonce}:{old_ts}:test-uid"
        sig = _hmac.new(CSRF_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        expired_token = f"{nonce}:{old_ts}:test-uid:{sig}"
        assert validate_csrf_token(expired_token) is False

    def test_tampered_signature_returns_false(self):
        """Token with altered signature should fail."""
        token = generate_csrf_token("test-uid")
        parts = token.split(":")
        nonce, ts, uid, _sig = parts
        tampered = f"{nonce}:{ts}:{uid}:{'f' * 64}"
        assert validate_csrf_token(tampered) is False

    def test_stateless_no_server_storage(self):
        """Validation should work purely from token content (no state lookup)."""
        token = generate_csrf_token("test-uid")
        # HMAC tokens are stateless — no dict to clear
        assert validate_csrf_token(token) is True

    def test_user_id_mismatch_rejected(self):
        """Token generated for user-a must fail when expected_user_id is user-b."""
        token = generate_csrf_token("user-a")
        assert validate_csrf_token(token, expected_user_id="user-b") is False

    def test_user_id_match_passes(self):
        """Token generated for user-a must pass when expected_user_id is user-a."""
        token = generate_csrf_token("user-a")
        assert validate_csrf_token(token, expected_user_id="user-a") is True

    def test_no_expected_user_id_skips_binding_check(self):
        """When expected_user_id is not supplied, user binding check is skipped."""
        token = generate_csrf_token("any-user-id")
        assert validate_csrf_token(token) is True


class TestCsrfTokenEdgeCases:
    """Edge case tests for CSRF token validation."""

    def test_wrong_part_count(self):
        """Token with wrong number of parts should fail."""
        assert validate_csrf_token("onlyone") is False
        assert validate_csrf_token("two:parts") is False
        assert validate_csrf_token("three:part:token") is False
        assert validate_csrf_token("too:many:parts:here:now") is False  # 5 parts — too many

    def test_non_integer_timestamp(self):
        """Token with non-integer timestamp should fail."""
        # 4-part token with non-integer timestamp position
        assert validate_csrf_token("abc:notanumber:uid:def") is False

    def test_future_timestamp_rejected(self):
        """Token with future timestamp should fail."""
        import hashlib
        import hmac as _hmac

        from config import CSRF_SECRET_KEY

        nonce = "b" * 32
        future_ts = str(int(time.time()) + 7200)
        payload = f"{nonce}:{future_ts}:test-uid"
        sig = _hmac.new(CSRF_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        assert validate_csrf_token(f"{nonce}:{future_ts}:test-uid:{sig}") is False


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

    def test_auth_logout_not_exempt(self):
        """HttpOnly cookie hardening: logout is cookie-authenticated and CSRF IS enforced."""
        assert "/auth/logout" not in CSRF_EXEMPT_PATHS

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
        """Restore original validate_csrf_token.

        The conftest.py fixture patches validate_csrf_token to always
        return True for API tests. We need the real function here to test
        that the middleware actually blocks invalid/missing tokens.
        """
        _sm.validate_csrf_token = validate_csrf_token

    def teardown_method(self):
        """Re-apply the conftest bypass for other API tests."""
        _sm.validate_csrf_token = lambda token, expected_user_id=None: True

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
        token = generate_csrf_token("test-uid")
        request = self._make_request("POST", "/clients", csrf_token=token)
        call_next = AsyncMock(return_value=MagicMock())

        response = await middleware.dispatch(request, call_next)
        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_put_with_valid_csrf_passes(self):
        """PUT with a valid CSRF token should pass through."""
        middleware = CSRFMiddleware(app=MagicMock())
        token = generate_csrf_token("test-uid")
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
        """Sprint 200 exempt paths (excluding /auth/logout which now requires CSRF) pass without CSRF token."""
        middleware = CSRFMiddleware(app=MagicMock())
        # /auth/logout removed from this list — it is cookie-authenticated and CSRF IS enforced
        new_exemptions = [
            "/auth/refresh",
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
        import hashlib
        import hmac as _hmac

        from config import CSRF_SECRET_KEY

        middleware = CSRFMiddleware(app=MagicMock())
        # Create an expired 4-part token with valid HMAC
        nonce = "c" * 32
        old_ts = str(int(time.time()) - (CSRF_TOKEN_EXPIRY_MINUTES + 1) * 60)
        payload = f"{nonce}:{old_ts}:test-uid"
        sig = _hmac.new(CSRF_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        expired_token = f"{nonce}:{old_ts}:test-uid:{sig}"

        request = self._make_request("POST", "/audit/adjustments", csrf_token=expired_token)
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

        csrf_found = any(m.cls.__name__ == "CSRFMiddleware" for m in app.user_middleware)
        assert csrf_found, "CSRFMiddleware not found in app middleware"


# =============================================================================
# Secret Separation (Packet 6)
# =============================================================================


class TestCsrfSecretSeparation:
    """Verify CSRF tokens use CSRF_SECRET_KEY, not JWT_SECRET_KEY."""

    def test_csrf_config_key_exists(self):
        """CSRF_SECRET_KEY must be defined in config."""
        from config import CSRF_SECRET_KEY

        assert CSRF_SECRET_KEY is not None
        assert len(CSRF_SECRET_KEY) >= 32

    def test_csrf_uses_dedicated_secret(self):
        """_get_csrf_secret() must return CSRF_SECRET_KEY, not JWT_SECRET_KEY."""
        from config import CSRF_SECRET_KEY
        from security_middleware import _get_csrf_secret

        assert _get_csrf_secret() == CSRF_SECRET_KEY

    def test_token_signed_with_csrf_secret(self):
        """A hand-crafted 4-part token signed with CSRF_SECRET_KEY must validate."""
        import hashlib
        import hmac as _hmac

        from config import CSRF_SECRET_KEY

        nonce = "d" * 32
        ts = str(int(time.time()))
        payload = f"{nonce}:{ts}:test-uid"
        sig = _hmac.new(CSRF_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        token = f"{nonce}:{ts}:test-uid:{sig}"
        assert validate_csrf_token(token) is True

    def test_token_signed_with_wrong_secret_rejected(self):
        """A 4-part token signed with a different secret must fail validation."""
        import hashlib
        import hmac as _hmac

        wrong_secret = "wrong_secret_that_is_definitely_not_the_csrf_key_x"
        nonce = "e" * 32
        ts = str(int(time.time()))
        payload = f"{nonce}:{ts}:test-uid"
        sig = _hmac.new(wrong_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        token = f"{nonce}:{ts}:test-uid:{sig}"
        assert validate_csrf_token(token) is False

    def test_jwt_secret_change_does_not_affect_csrf(self):
        """Changing JWT_SECRET_KEY must not invalidate CSRF tokens."""
        # Generate a token with the current CSRF secret
        token = generate_csrf_token("test-uid")
        assert validate_csrf_token(token) is True

        # Temporarily change JWT_SECRET_KEY — CSRF should still validate
        import config

        original_jwt = config.JWT_SECRET_KEY
        config.JWT_SECRET_KEY = "completely_different_jwt_key_that_should_not_matter"
        try:
            assert validate_csrf_token(token) is True, "CSRF validation should not depend on JWT_SECRET_KEY"
        finally:
            config.JWT_SECRET_KEY = original_jwt

    def test_csrf_secret_separation_in_source(self):
        """_get_csrf_secret must reference CSRF_SECRET_KEY, not JWT_SECRET_KEY."""
        source_path = Path(__file__).parent.parent / "security_middleware.py"
        source = source_path.read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_get_csrf_secret":
                body_source = ast.get_source_segment(source, node)
                assert "CSRF_SECRET_KEY" in body_source, "_get_csrf_secret must import CSRF_SECRET_KEY"
                assert "JWT_SECRET_KEY" not in body_source, "_get_csrf_secret must NOT reference JWT_SECRET_KEY"
                return
        pytest.fail("_get_csrf_secret function not found in security_middleware.py")


# =============================================================================
# Exempt Path Policy Guardrails (Packet 6)
# =============================================================================


class TestCsrfExemptionPolicy:
    """Verify CSRF exemption assumptions are documented and correct."""

    def test_refresh_exempt_documented(self):
        """Source must contain a comment explaining /auth/refresh exemption."""
        source_path = Path(__file__).parent.parent / "security_middleware.py"
        source = source_path.read_text()
        assert "/auth/refresh" in source
        assert "cookie" in source.lower() or "Cookie" in source

    def test_logout_enforcement_documented(self):
        """Source must document that /auth/logout requires CSRF (cookie-authenticated)."""
        source_path = Path(__file__).parent.parent / "security_middleware.py"
        source = source_path.read_text()
        # /auth/logout is mentioned in the policy comment explaining it is NOT exempt
        assert "/auth/logout" in source
        # The rationale (cookie-authenticated) must be documented
        assert "cookie" in source.lower()

    def test_exempt_set_is_frozen(self):
        """The exempt set must contain exactly the expected paths.
        NOTE: /auth/logout removed from exempt set — it is cookie-authenticated,
        so CSRF IS enforced (HttpOnly cookie hardening sprint).
        """
        expected = {
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/auth/verify-email",
            "/auth/csrf",
            "/billing/webhook",
            "/contact/submit",
            "/waitlist",
            "/docs",
            "/openapi.json",
            "/redoc",
        }
        assert CSRF_EXEMPT_PATHS == expected, (
            f"Unexpected CSRF exemptions: added={CSRF_EXEMPT_PATHS - expected}, removed={expected - CSRF_EXEMPT_PATHS}"
        )

    def test_config_guardrail_csrf_required_in_production(self):
        """config.py must hard-fail if CSRF_SECRET_KEY is missing in production."""
        config_path = Path(__file__).parent.parent / "config.py"
        source = config_path.read_text()
        tree = ast.parse(source)

        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                segment = ast.get_source_segment(source, node)
                if segment and "production" in segment and "CSRF_SECRET_KEY" in segment:
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                            if child.func.id == "_hard_fail":
                                found = True
                                break
        assert found, "Production CSRF_SECRET_KEY guardrail not found in config.py"

    def test_config_guardrail_csrf_must_differ_from_jwt(self):
        """config.py must enforce CSRF ≠ JWT in production."""
        config_path = Path(__file__).parent.parent / "config.py"
        source = config_path.read_text()
        assert "CSRF_SECRET_KEY == JWT_SECRET_KEY" in source, (
            "config.py must check CSRF_SECRET_KEY != JWT_SECRET_KEY in production"
        )


# =============================================================================
# Origin/Referer Enforcement (Security Sprint)
# =============================================================================


class TestCsrfOriginRefererEnforcement:
    """Verify CSRFMiddleware._validate_request_origin() correctly enforces Origin/Referer."""

    def _make_middleware(self):
        return CSRFMiddleware(app=MagicMock())

    def _make_request_with_headers(self, headers: dict):
        """Create a mock Request with the given headers dict."""
        request = MagicMock()
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: headers.get(key, default)
        return request

    def test_matching_origin_allowed(self):
        """Origin matching CORS_ORIGINS returns True."""
        from config import CORS_ORIGINS

        middleware = self._make_middleware()
        allowed_origin = CORS_ORIGINS[0]
        request = self._make_request_with_headers({"Origin": allowed_origin})
        assert middleware._validate_request_origin(request) is True

    def test_mismatched_origin_blocked(self):
        """Origin not in CORS_ORIGINS returns False."""
        middleware = self._make_middleware()
        request = self._make_request_with_headers({"Origin": "https://evil.example.com"})
        assert middleware._validate_request_origin(request) is False

    def test_matching_referer_allowed(self):
        """When no Origin header, a matching Referer returns True."""
        from config import CORS_ORIGINS

        middleware = self._make_middleware()
        allowed_origin = CORS_ORIGINS[0]
        request = self._make_request_with_headers({"Referer": f"{allowed_origin}/some/path"})
        assert middleware._validate_request_origin(request) is True

    def test_absent_both_allowed(self):
        """No Origin and no Referer returns True (non-browser clients)."""
        middleware = self._make_middleware()
        request = self._make_request_with_headers({})
        assert middleware._validate_request_origin(request) is True

    def test_origin_takes_precedence_over_referer(self):
        """When both Origin and Referer present, Origin is checked (and matches)."""
        from config import CORS_ORIGINS

        middleware = self._make_middleware()
        allowed_origin = CORS_ORIGINS[0]
        request = self._make_request_with_headers(
            {
                "Origin": allowed_origin,
                "Referer": "https://evil.example.com/path",
            }
        )
        # Origin matches, so result is True despite bad Referer
        assert middleware._validate_request_origin(request) is True


# =============================================================================
# User Binding via Middleware (Security Sprint)
# =============================================================================


class TestCsrfUserBindingMiddleware:
    """Verify CSRFMiddleware enforces user binding when Bearer token is present."""

    def setup_method(self):
        """Restore original validate_csrf_token."""
        _sm.validate_csrf_token = validate_csrf_token

    def teardown_method(self):
        """Re-apply the conftest bypass for other API tests."""
        _sm.validate_csrf_token = lambda token, expected_user_id=None: True

    def _make_request(self, method: str, path: str, csrf_token: str = None, auth_header: str = None):
        """Create a mock Starlette Request with optional auth header."""
        request = MagicMock()
        request.method = method
        request.url.path = path
        headers = {}
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token
        if auth_header:
            headers["Authorization"] = auth_header
        request.headers = MagicMock()
        request.headers.get = lambda key, default=None: headers.get(key, default)
        return request

    @pytest.mark.asyncio
    async def test_authenticated_request_user_id_mismatch_blocked(self):
        """Bearer sub=42 + CSRF token for user 99 → 403."""

        import jwt

        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        # Build a JWT with sub=42
        jwt_token = jwt.encode({"sub": "42"}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        # Build a valid CSRF token for user 99 (different user)
        csrf_tok = generate_csrf_token("99")

        middleware = CSRFMiddleware(app=MagicMock())
        request = self._make_request(
            "POST",
            "/clients",
            csrf_token=csrf_tok,
            auth_header=f"Bearer {jwt_token}",
        )
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403
        call_next.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unauthenticated_request_valid_token_passes(self):
        """No Authorization header + valid CSRF token (any user_id) → passes."""
        middleware = CSRFMiddleware(app=MagicMock())
        token = generate_csrf_token("any-user")
        request = self._make_request("POST", "/clients", csrf_token=token)
        call_next = AsyncMock(return_value=MagicMock())

        response = await middleware.dispatch(request, call_next)
        call_next.assert_awaited_once_with(request)
