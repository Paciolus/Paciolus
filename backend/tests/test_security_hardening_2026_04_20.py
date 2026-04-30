"""
Security hardening regression suite — 2026-04-20.

Covers:
  * Objective 1 — Passcode KDF, salt, constant-time verify, strength policy,
    per-token brute-force throttle.
  * Objective 2 — Passcode moved out of query string onto POST body; legacy
    query-string pattern is rejected; GET on a passcode-protected share
    returns an instructional 403.
  * Objective 3 — CSRF hardening: refresh/logout rejects X-Requested-With
    fallback in production; Sec-Fetch-Site policy enforced; valid token
    still accepted.
  * Objective 4 — Security headers gated by ENV_MODE, not ``not DEBUG``.
  * Objective 5 — Rate-limit fail-closed in production.
  * Objective 6 — Dev-credential script refuses non-development ENV_MODE
    and has no hardcoded password.
"""

from __future__ import annotations

import base64
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# ---------------------------------------------------------------------------
# Objective 1 — passcode KDF + strength policy + brute-force throttle
# ---------------------------------------------------------------------------

from shared.passcode_security import (  # noqa: E402
    PasscodeThrottleState,
    WeakPasscodeError,
    compute_next_lockout,
    current_lockout_remaining_seconds,
    hash_passcode,
    validate_passcode_strength,
    verify_passcode,
)


class _FakeShareRow:
    """Minimal duck-typed row for PasscodeThrottleState unit tests."""

    def __init__(self) -> None:
        self.passcode_failed_attempts = 0
        self.passcode_locked_until: datetime | None = None


class TestPasscodeStrengthPolicy:
    def test_min_length_enforced(self):
        with pytest.raises(WeakPasscodeError):
            validate_passcode_strength("Abc1!")  # 5 chars

    def test_boundary_length_ok(self):
        # 10 chars, 3 classes (lower, upper, digit) → valid
        validate_passcode_strength("Abcdefg123")

    def test_three_class_requirement(self):
        with pytest.raises(WeakPasscodeError):
            # 10 chars but only lowercase + digit — 2 classes, below minimum
            validate_passcode_strength("abcdefg123")

    def test_symbol_counts_as_class(self):
        validate_passcode_strength("abcdefg!23")  # lower + digit + symbol

    def test_max_length_enforced(self):
        with pytest.raises(WeakPasscodeError):
            validate_passcode_strength("A1!" + "a" * 200)

    def test_empty_rejected(self):
        with pytest.raises(WeakPasscodeError):
            validate_passcode_strength("")


class TestPasscodeKDF:
    def test_hash_is_argon2id_format(self):
        """Sprint 697: new passcode hashes use Argon2id (not bcrypt).
        The argon2-cffi library writes the explicit ``$argon2id$`` prefix."""
        digest = hash_passcode("StrongP@ss1")
        assert digest.startswith("$argon2id$")

    def test_legacy_bcrypt_hash_still_verifies(self):
        """Sprint 697 transition window: existing shares hashed under
        Sprint 696's bcrypt branch must still verify so they don't
        break until their ≤48h TTL expires."""
        import bcrypt as _bcrypt

        # Produce a bcrypt hash the same way Sprint 696 did.
        salt = _bcrypt.gensalt(rounds=12)
        bcrypt_hash = _bcrypt.hashpw(b"StrongP@ss1", salt).decode("utf-8")
        assert bcrypt_hash.startswith("$2b$")
        assert verify_passcode("StrongP@ss1", bcrypt_hash) is True
        assert verify_passcode("WrongPass1!", bcrypt_hash) is False

    def test_same_input_yields_different_hashes(self):
        """Per-passcode salt — two hashes of the same input must differ."""
        assert hash_passcode("StrongP@ss1") != hash_passcode("StrongP@ss1")

    def test_verify_roundtrip_true(self):
        digest = hash_passcode("StrongP@ss1")
        assert verify_passcode("StrongP@ss1", digest) is True

    def test_verify_roundtrip_false(self):
        digest = hash_passcode("StrongP@ss1")
        assert verify_passcode("StrongP@ss2", digest) is False

    def test_verify_rejects_legacy_sha256_hash(self):
        """Pre-remediation rows are 64-char hex SHA-256.  These must not verify."""
        import hashlib as _h

        legacy = _h.sha256(b"whatever").hexdigest()
        assert verify_passcode("whatever", legacy) is False

    def test_verify_handles_empty_inputs(self):
        assert verify_passcode("", "") is False
        assert verify_passcode("x", "") is False
        assert verify_passcode("", "$2b$12$" + "a" * 53) is False


class TestBruteForceThrottle:
    def test_first_attempts_no_lockout(self):
        # attempts 1-4 → no penalty
        for attempts in range(1, 5):
            assert compute_next_lockout(attempts) is None

    def test_fifth_attempt_triggers_short_lockout(self):
        td = compute_next_lockout(5)
        assert td is not None and td.total_seconds() == 60

    def test_escalating_lockout(self):
        t5 = compute_next_lockout(5).total_seconds()
        t9 = compute_next_lockout(9).total_seconds()
        assert t9 > t5

    def test_long_lockout_kicks_in_at_ten(self):
        t10 = compute_next_lockout(10).total_seconds()
        # first long-throttle step = 2 * 300 = 600 seconds
        assert t10 == 600

    def test_lockout_capped_at_one_hour(self):
        t_huge = compute_next_lockout(1_000).total_seconds()
        assert t_huge == 3600

    def test_throttle_state_flow(self):
        row = _FakeShareRow()
        state = PasscodeThrottleState(row)
        assert state.is_locked() is False

        # four failures → no lock
        for _ in range(4):
            state.register_failure()
        assert state.is_locked() is False
        assert row.passcode_locked_until is None

        # fifth failure → 60s lock
        state.register_failure()
        assert state.is_locked() is True
        remaining = current_lockout_remaining_seconds(row.passcode_locked_until)
        assert 55 <= remaining <= 60

        # reset clears both
        state.reset()
        assert state.is_locked() is False
        assert row.passcode_failed_attempts == 0
        assert row.passcode_locked_until is None


# ---------------------------------------------------------------------------
# Objective 2 — passcode out of query string; POST flow; brute-force
# enforcement via the route
# ---------------------------------------------------------------------------

from models import UserTier  # noqa: E402

VALID_PDF = b"%PDF-1.4 integration test"


@pytest.fixture(autouse=True)
def _enable_rate_limiter_off():
    """Override the autouse limiter-disabler — keep it disabled, matching
    the project default for API tests."""
    yield


async def _create_share(
    db_session,
    make_user,
    *,
    passcode: str | None = None,
    tier: UserTier = UserTier.PROFESSIONAL,
):
    """Helper: create a PDF share via the /create route, return (token, share_row)."""
    from auth import require_verified_user
    from database import get_db
    from main import app

    user = make_user(email=f"share_{os.urandom(4).hex()}@example.com", tier=tier)
    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session

    payload = {
        "tool_name": "trial_balance",
        "export_format": "pdf",
        "export_data_b64": base64.b64encode(VALID_PDF).decode(),
    }
    if passcode is not None:
        payload["passcode"] = passcode

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/export-sharing/create", json=payload)
    return user, resp


class TestPasscodeRoutePolicy:
    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_create_rejects_weak_passcode(self, db_session, make_user):
        # 8 chars — short of the 10-char minimum.  Pydantic min_length rejects
        # with HTTP 422 before the route handler runs.
        _, resp = await _create_share(db_session, make_user, passcode="Weak1234")
        assert resp.status_code == 422

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_create_rejects_two_class_passcode(self, db_session, make_user):
        # 10 chars but only 2 classes — triggers runtime WeakPasscodeError → 400.
        _, resp = await _create_share(db_session, make_user, passcode="abcdefg123")
        try:
            assert resp.status_code == 400
            assert "at least 3" in resp.text or "lower" in resp.text.lower()
        finally:
            from main import app

            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_get_on_passcode_share_returns_404(self, db_session, make_user):
        """Sprint 718 collapsed the share-enumeration response: passcode-protected and unknown
        shares both return 404 with no body that leaks share existence. The original 403-with-
        instructional-text behaviour was the enumeration vector."""
        _, resp = await _create_share(db_session, make_user, passcode="StrongP@ss1")
        assert resp.status_code == 200
        token = resp.json()["share_token"]

        from main import app

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.get(f"/export-sharing/{token}")
            assert r.status_code == 404
            # Body must not reveal that the share exists or that a passcode is required —
            # that was the leak Sprint 718 closed.
            assert "passcode" not in r.text.lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_query_string_passcode_ignored(self, db_session, make_user):
        """Old ``?passcode=...`` pattern must not authenticate — routing only.
        Sprint 718: response collapsed from 403 to 404 to remove the enumeration signal."""
        _, resp = await _create_share(db_session, make_user, passcode="StrongP@ss1")
        assert resp.status_code == 200
        token = resp.json()["share_token"]

        from main import app

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.get(f"/export-sharing/{token}?passcode=StrongP@ss1")
            # Must NOT serve the file. 404 (post-Sprint-718 enumeration collapse), not 403.
            assert r.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_post_download_with_correct_passcode(self, db_session, make_user):
        _, resp = await _create_share(db_session, make_user, passcode="StrongP@ss1")
        assert resp.status_code == 200
        token = resp.json()["share_token"]

        from main import app

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.post(
                    f"/export-sharing/{token}/download",
                    json={"passcode": "StrongP@ss1"},
                )
            assert r.status_code == 200
            assert r.content.startswith(b"%PDF")
            assert r.headers.get("content-type", "").startswith("application/pdf")
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_post_download_wrong_passcode_rejected(self, db_session, make_user):
        _, resp = await _create_share(db_session, make_user, passcode="StrongP@ss1")
        assert resp.status_code == 200
        token = resp.json()["share_token"]

        from main import app

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.post(
                    f"/export-sharing/{token}/download",
                    json={"passcode": "WRONGpass1!"},
                )
            assert r.status_code == 403
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_brute_force_lockout_after_five_failures(self, db_session, make_user):
        """Five wrong passcodes → 429 with Retry-After on the sixth attempt."""
        _, resp = await _create_share(db_session, make_user, passcode="StrongP@ss1")
        assert resp.status_code == 200
        token = resp.json()["share_token"]

        from main import app

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                # five consecutive wrong guesses
                for _ in range(5):
                    r = await client.post(
                        f"/export-sharing/{token}/download",
                        json={"passcode": "WRONGpass1!"},
                    )
                    assert r.status_code == 403

                # sixth attempt — locked out even if the passcode is correct
                r = await client.post(
                    f"/export-sharing/{token}/download",
                    json={"passcode": "StrongP@ss1"},
                )
                assert r.status_code == 429, r.text
                assert "Retry-After" in r.headers
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_non_passcode_share_still_uses_get(self, db_session, make_user):
        _, resp = await _create_share(db_session, make_user, passcode=None)
        assert resp.status_code == 200
        token = resp.json()["share_token"]

        from main import app

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.get(f"/export-sharing/{token}")
            assert r.status_code == 200
            assert r.content.startswith(b"%PDF")
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Objective 3 — CSRF hardening
# ---------------------------------------------------------------------------

from security_middleware import CSRF_CUSTOM_HEADER_PATHS, CSRFMiddleware  # noqa: E402


class _FakeHeaders(dict):
    """Case-insensitive dict mirroring starlette.Headers' .get() behaviour."""

    def get(self, key, default=None):
        for k, v in self.items():
            if k.lower() == key.lower():
                return v
        return default


class _FakeRequest:
    def __init__(self, method: str, path: str, headers: dict, cookies: dict | None = None):
        self.method = method
        self.headers = _FakeHeaders(headers)
        from types import SimpleNamespace

        self.url = SimpleNamespace(path=path)
        # Sprint 718 added cookie-aware CSRF — the middleware reads
        # request.cookies on the cookie-auth dispatch path. Default to an
        # empty dict so existing call sites exercise the
        # no-Authorization, no-cookie branch (no user_id binding required).
        self.cookies = cookies or {}


class TestCSRFOriginPolicy:
    def _mw(self):
        return CSRFMiddleware(app=None)

    def test_origin_missing_with_cross_site_fetch_rejected(self):
        mw = self._mw()
        req = _FakeRequest(
            "POST",
            "/some-endpoint",
            headers={"Sec-Fetch-Site": "cross-site"},
        )
        assert mw._validate_request_origin(req) is False

    def test_origin_missing_with_same_origin_fetch_allowed(self):
        mw = self._mw()
        req = _FakeRequest(
            "POST",
            "/some-endpoint",
            headers={"Sec-Fetch-Site": "same-origin"},
        )
        assert mw._validate_request_origin(req) is True

    def test_origin_missing_no_fetch_metadata_allowed(self):
        """Non-browser clients (no Origin, no Sec-Fetch-Site) still allowed."""
        mw = self._mw()
        req = _FakeRequest("POST", "/some-endpoint", headers={})
        assert mw._validate_request_origin(req) is True

    def test_origin_present_must_match_cors(self):
        mw = self._mw()
        req_bad = _FakeRequest(
            "POST",
            "/some-endpoint",
            headers={"Origin": "https://evil.example.com"},
        )
        assert mw._validate_request_origin(req_bad) is False


class TestCSRFRefreshLogout:
    def _mw(self):
        return CSRFMiddleware(app=None)

    def test_refresh_and_logout_are_custom_header_paths(self):
        assert "/auth/refresh" in CSRF_CUSTOM_HEADER_PATHS
        assert "/auth/logout" in CSRF_CUSTOM_HEADER_PATHS

    @pytest.mark.anyio
    async def test_production_rejects_x_requested_with_only(self):
        """In production, X-Requested-With alone no longer passes CSRF for
        cookie-auth mutation endpoints."""
        mw = self._mw()

        async def _call_next(_req):
            from starlette.responses import Response as _R

            return _R(status_code=200, content="ok")

        req = _FakeRequest(
            "POST",
            "/auth/refresh",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        with patch("config.ENV_MODE", "production"):
            resp = await mw.dispatch(req, _call_next)
        assert resp.status_code == 403
        assert b"CSRF" in resp.body

    @pytest.mark.anyio
    async def test_dev_still_accepts_x_requested_with(self):
        mw = self._mw()

        async def _call_next(_req):
            from starlette.responses import Response as _R

            return _R(status_code=200, content="ok")

        req = _FakeRequest(
            "POST",
            "/auth/refresh",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        with patch("config.ENV_MODE", "development"):
            resp = await mw.dispatch(req, _call_next)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Objective 4 — security headers gated by ENV_MODE
# ---------------------------------------------------------------------------


class TestSecurityHeadersMiddleware:
    @pytest.mark.anyio
    async def test_hsts_emitted_when_production_mode_true(self):
        from starlette.responses import Response as _R

        from security_middleware import SecurityHeadersMiddleware

        async def _call_next(_req):
            return _R(status_code=200, content="ok")

        mw = SecurityHeadersMiddleware(app=None, production_mode=True)
        req = _FakeRequest("GET", "/", headers={})
        resp = await mw.dispatch(req, _call_next)

        assert "Strict-Transport-Security" in resp.headers
        assert "Content-Security-Policy" in resp.headers

    @pytest.mark.anyio
    async def test_hsts_not_emitted_in_dev_mode(self):
        from starlette.responses import Response as _R

        from security_middleware import SecurityHeadersMiddleware

        async def _call_next(_req):
            return _R(status_code=200, content="ok")

        mw = SecurityHeadersMiddleware(app=None, production_mode=False)
        req = _FakeRequest("GET", "/", headers={})
        resp = await mw.dispatch(req, _call_next)

        assert "Strict-Transport-Security" not in resp.headers
        assert "Content-Security-Policy" not in resp.headers

    def test_main_uses_env_mode_not_debug_inversion(self):
        """main.py must gate production_mode on ENV_MODE, not on ``not DEBUG``.

        This is a source-level assertion: we read main.py and ensure the
        correct sentinel appears and the legacy bug pattern is gone.
        """
        content = Path(__file__).parent.parent.joinpath("main.py").read_text(encoding="utf-8")
        # New gate must be present
        assert 'ENV_MODE == "production"' in content
        # Old inverted-DEBUG pattern must NOT be the sole gate; ensure it's
        # either gone or only appears inside a comment / warning context.
        # The precise bug was `production_mode=not DEBUG` — that exact token
        # sequence must not survive.
        assert "production_mode=not DEBUG" not in content


# ---------------------------------------------------------------------------
# Objective 5 — rate-limit fail-closed in production
# ---------------------------------------------------------------------------


def _prod_env(**extra: str) -> dict:
    """Minimal env dict for spawning a subprocess that imports backend/config.py.

    The subprocess approach is mandatory because the SecretsManager singleton
    caches reads — monkeypatching env vars in-process does not invalidate
    the cache, so config-reload tests would read stale values.
    """
    base = {
        "ENV_MODE": "production",
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000",
        "CORS_ORIGINS": "https://paciolus.com",
        "JWT_SECRET_KEY": "x" * 64,
        "CSRF_SECRET_KEY": "y" * 64,
        "AUDIT_CHAIN_SECRET_KEY": "z" * 64,
        "REDIS_URL": "redis://localhost:6379/0",
        # DB URL includes ?sslmode=require to satisfy the DB_TLS_REQUIRED
        # production guardrail.  The subprocess never actually connects — we
        # only exercise config-import-time logic.
        "DATABASE_URL": "postgresql://u:p@localhost:5432/x?sslmode=require",
        # Disable the pooler-skip path so the config loads cleanly.
        "DB_TLS_REQUIRED": "true",
        # Re-export Stripe as if configured (prod guardrail will otherwise fail).
        # STRIPE_SECRET_KEY only needs to be non-empty for the config-
        # import guard; no outbound call is made from this subprocess
        # boot. Use a non-Stripe-prefix placeholder so the pre-commit
        # secrets scanner (which flags any Stripe-prefix string) doesn't
        # false-positive on this test fixture. The publishable / webhook
        # placeholders must also be set explicitly: when the subprocess
        # env is missing them, python-dotenv backfills from backend/.env
        # (which holds developer test-mode Stripe keys), tripping the
        # Sprint 719 production format guard in config.py.
        "STRIPE_SECRET_KEY": "placeholder-non-stripe-format",
        "STRIPE_PUBLISHABLE_KEY": "placeholder-non-stripe-format",
        "STRIPE_WEBHOOK_SECRET": "placeholder-non-whsec-format",
        "SENDGRID_API_KEY": "SG.test",
        "SEAT_ENFORCEMENT_MODE": "hard",
        "ENTITLEMENT_ENFORCEMENT": "hard",
        # Propagate the process runtime essentials (Windows Python needs
        # SYSTEMROOT / PATH; Linux needs PATH for the interpreter resolve).
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    }
    base.update(extra)
    return base


class TestRateLimitFailClosed:
    """Validates config.py import-time guardrails by spawning a fresh
    Python process — bypasses the SecretsManager singleton's process-wide
    cache that makes in-process monkeypatching of env vars ineffective."""

    def _run_config_import(self, env: dict) -> "tuple[int, str]":
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.path.insert(0, '.'); "
                "import config; "
                "print('STRICT=', config.RATE_LIMIT_STRICT_MODE); "
                "print('OVERRIDE=', config.RATE_LIMIT_STRICT_OVERRIDE)",
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(Path(__file__).parent.parent),
        )
        return result.returncode, result.stdout + result.stderr

    def test_strict_mode_defaults_true_in_production(self):
        rc, out = self._run_config_import(_prod_env())
        assert rc == 0, out
        assert "STRICT= True" in out

    def test_production_without_strict_without_override_hard_fails(self):
        rc, out = self._run_config_import(_prod_env(RATE_LIMIT_STRICT_MODE="false"))
        assert rc != 0, out
        assert "RATE_LIMIT_STRICT_MODE" in out

    def test_expired_override_rejected(self):
        rc, out = self._run_config_import(
            _prod_env(
                RATE_LIMIT_STRICT_MODE="false",
                RATE_LIMIT_STRICT_OVERRIDE="TICKET-1:2020-01-01",
            )
        )
        assert rc != 0, out
        assert "expired" in out.lower() or "RATE_LIMIT_STRICT_OVERRIDE" in out

    def test_valid_override_allowed(self):
        future = (datetime.now(UTC) + timedelta(days=7)).strftime("%Y-%m-%d")
        rc, out = self._run_config_import(
            _prod_env(
                RATE_LIMIT_STRICT_MODE="false",
                RATE_LIMIT_STRICT_OVERRIDE=f"SEC-1234:{future}",
            )
        )
        assert rc == 0, out
        assert "SEC-1234:" in out

    def test_malformed_override_rejected(self):
        rc, out = self._run_config_import(
            _prod_env(
                RATE_LIMIT_STRICT_MODE="false",
                RATE_LIMIT_STRICT_OVERRIDE="not-a-valid-format",
            )
        )
        assert rc != 0, out


# ---------------------------------------------------------------------------
# Cryptographic key separation — AUDIT_CHAIN_SECRET_KEY (security remediation)
# ---------------------------------------------------------------------------


class TestAuditChainKeySeparation:
    """Production must hard-fail when AUDIT_CHAIN_SECRET_KEY is missing or
    equal to JWT_SECRET_KEY. Sharing the JWT key collapses the cryptographic
    domain boundary and silently breaks audit-chain verification on JWT
    rotation (SOC 2 CC7.4)."""

    def _run_config_import(self, env: dict) -> "tuple[int, str]":
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.path.insert(0, '.'); "
                "import config; "
                "print('AUDIT_KEY_SET=', bool(config.AUDIT_CHAIN_SECRET_KEY)); "
                "print('AUDIT_EQ_JWT=', config.AUDIT_CHAIN_SECRET_KEY == config.JWT_SECRET_KEY)",
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(Path(__file__).parent.parent),
        )
        return result.returncode, result.stdout + result.stderr

    def test_production_distinct_key_allowed(self):
        rc, out = self._run_config_import(_prod_env())
        assert rc == 0, out
        assert "AUDIT_KEY_SET= True" in out
        assert "AUDIT_EQ_JWT= False" in out

    def test_production_missing_audit_chain_key_hard_fails(self):
        env = _prod_env()
        env.pop("AUDIT_CHAIN_SECRET_KEY", None)
        rc, out = self._run_config_import(env)
        assert rc != 0, out
        assert "AUDIT_CHAIN_SECRET_KEY" in out

    def test_production_blank_audit_chain_key_hard_fails(self):
        rc, out = self._run_config_import(_prod_env(AUDIT_CHAIN_SECRET_KEY=""))
        assert rc != 0, out
        assert "AUDIT_CHAIN_SECRET_KEY" in out

    def test_production_audit_key_equal_to_jwt_hard_fails(self):
        # Both keys identical — a recently-discovered foot-gun.
        shared = "a" * 64
        rc, out = self._run_config_import(_prod_env(JWT_SECRET_KEY=shared, AUDIT_CHAIN_SECRET_KEY=shared))
        assert rc != 0, out
        assert "AUDIT_CHAIN_SECRET_KEY" in out
        assert "JWT_SECRET_KEY" in out


# ---------------------------------------------------------------------------
# Objective 6 — dev-credential script safety
# ---------------------------------------------------------------------------


class TestCreateDevUserScript:
    SCRIPT = Path(__file__).parent.parent / "scripts" / "create_dev_user.py"

    def test_no_hardcoded_password_literal(self):
        content = self.SCRIPT.read_text(encoding="utf-8")
        # Specifically ensure the old default is gone.
        assert "DevPass1!" not in content
        # No other plaintext password assignments that would be mistaken
        # for a credential.  The brief forbids hardcoded defaults.
        assert "DEV_PASSWORD = " not in content

    def test_script_refuses_non_development_env_mode(self, monkeypatch, tmp_path):
        """Exits non-zero when ENV_MODE is not 'development' and the danger
        flag is not set.  Uses ENV_MODE=staging to exercise the script's own
        refusal path without triggering the unrelated production-mode config
        guardrails (which would fail earlier at config-import time — a
        different, equally safe failure mode but not what this test targets).
        """
        # Use ENV_MODE=staging: not 'development', but not 'production'
        # either so config.py's prod guards don't short-circuit the test.
        sqlite_path = tmp_path / "dev_user_test.db"
        env = {
            **os.environ,
            "ENV_MODE": "staging",
            "DEV_USER_PASSWORD": "DoesNotMatter1!",
            "DATABASE_URL": f"sqlite:///{sqlite_path}",
        }

        import subprocess

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode != 0, (
            f"Script must refuse non-development ENV_MODE; "
            f"got rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        combined = (result.stderr + result.stdout).lower()
        assert "development" in combined or "refusing" in combined, combined

    def test_script_accepts_danger_flag_in_non_dev(self, monkeypatch, tmp_path):
        """With --i-know-this-is-dangerous the script runs in staging mode
        and creates the user.  Smoke-tests the danger-flag code path."""
        sqlite_path = tmp_path / "dev_user_danger.db"
        env = {
            **os.environ,
            "ENV_MODE": "staging",
            "DEV_USER_PASSWORD": "DangerousRun1!",
            "DATABASE_URL": f"sqlite:///{sqlite_path}",
        }
        import subprocess

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "--i-know-this-is-dangerous"],
            capture_output=True,
            text=True,
            env=env,
        )
        # Script may still fail for unrelated reasons (e.g. SQLite schema) but
        # the danger-flag banner must have been reached, which is proof the
        # ENV_MODE gate accepted the override.
        combined = result.stderr + result.stdout
        assert "DANGER" in combined or "[OK]" in combined or "already exists" in combined, (
            f"rc={result.returncode} out={combined!r}"
        )

    def test_script_has_danger_flag(self):
        content = self.SCRIPT.read_text(encoding="utf-8")
        assert "--i-know-this-is-dangerous" in content
