"""Sprint 698: per-IP passcode-failure throttle for export-share download.

Sprint 696 added per-token passcode lockout (same share + many failures
from one attacker → lockout). Sprint 698 layers per-IP tracking so an
attacker cycling through MANY share tokens from one IP is bounded
before the brute-force accumulates enough signal across tokens.

Tests here exercise the interaction directly by calling
``_verify_passcode_or_raise`` — the HTTP layer is covered by the
existing ``test_export_sharing_routes.py`` suite.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException


@pytest.fixture(autouse=True)
def _reset_ip_tracker():
    """Each test starts with a clean IP-failure tracker state.

    Sprint 718: storage moved to ``shared/ip_failure_tracker.py``. In tests
    (no REDIS_URL) the underlying ``_memory_store`` dict still functions as
    the store; ``reset_all_for_admin_unlock()`` clears it.
    """
    from shared import ip_failure_tracker

    ip_failure_tracker.reset_all_for_admin_unlock()
    yield
    ip_failure_tracker.reset_all_for_admin_unlock()


def _make_share(db_session, passcode_hash: str | None = None):
    """Minimal valid ExportShare row for passcode-verification tests."""
    from export_share_model import ExportShare
    from models import User, UserTier

    # Need an owner user for the FK.
    user = User(
        email="share_owner@example.com",
        name="Share Owner",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    share = ExportShare(
        user_id=user.id,
        # share_token_hash is VARCHAR(64) — keep within the limit so
        # this test passes on Postgres (SQLite doesn't enforce length).
        share_token_hash="a" * 64,
        export_data=b"PK\x03\x04test",
        export_format="xlsx",
        tool_name="test",
        passcode_hash=passcode_hash or "$2b$12$notrealhash",
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        passcode_failed_attempts=0,
        passcode_locked_until=None,
    )
    db_session.add(share)
    db_session.flush()
    return share


class TestPerIpThrottle:
    def test_correct_passcode_does_not_record_ip_failure(self, db_session):
        """Successful verification must not pollute the IP tracker."""
        from routes.export_sharing import _verify_passcode_or_raise
        from shared import ip_failure_tracker
        from shared.passcode_security import hash_passcode

        share = _make_share(db_session, passcode_hash=hash_passcode("Correct1!Pass"))

        # Call with the correct passcode — no IP record should be made.
        _verify_passcode_or_raise(share, "Correct1!Pass", db_session, client_ip="203.0.113.5")
        assert "203.0.113.5" not in ip_failure_tracker._memory_store

    def test_wrong_passcode_records_ip_failure(self, db_session):
        """Every wrong passcode increments the per-IP counter."""
        from routes.export_sharing import _verify_passcode_or_raise
        from shared import ip_failure_tracker
        from shared.passcode_security import hash_passcode

        share = _make_share(db_session, passcode_hash=hash_passcode("Correct1!Pass"))

        with pytest.raises(HTTPException) as exc:
            _verify_passcode_or_raise(share, "WrongPassword1!", db_session, client_ip="198.51.100.7")
        assert exc.value.status_code == 403

        assert "198.51.100.7" in ip_failure_tracker._memory_store
        assert len(ip_failure_tracker._memory_store["198.51.100.7"]) == 1

    def test_blocked_ip_429_even_with_correct_passcode(self, db_session):
        """Sprint 698 key invariant: once the IP crosses the threshold,
        even a correct passcode gets 429 — prevents an attacker from
        probing to see which passcode works after they've hit the wall."""
        import time

        from routes.export_sharing import _verify_passcode_or_raise
        from security_middleware import IP_FAILURE_THRESHOLD
        from shared import ip_failure_tracker
        from shared.passcode_security import hash_passcode

        share = _make_share(db_session, passcode_hash=hash_passcode("Correct1!Pass"))

        # Pre-populate the IP tracker past the threshold (memory store is the
        # backing in tests; production uses Redis but the API is the same).
        now = time.time()
        ip_failure_tracker._memory_store["192.0.2.99"] = [now] * (IP_FAILURE_THRESHOLD + 1)

        with pytest.raises(HTTPException) as exc:
            _verify_passcode_or_raise(share, "Correct1!Pass", db_session, client_ip="192.0.2.99")
        assert exc.value.status_code == 429
        assert "network" in str(exc.value.detail).lower()
        # Retry-After header surfaced.
        assert exc.value.headers.get("Retry-After") == "900"

    def test_ip_block_takes_precedence_over_token_lockout(self, db_session):
        """Both per-IP AND per-token gates exist; per-IP check fires
        first so an attacker burning through many tokens sees the IP
        block rather than a per-token lockout message."""
        import time

        from routes.export_sharing import _verify_passcode_or_raise
        from security_middleware import IP_FAILURE_THRESHOLD
        from shared import ip_failure_tracker
        from shared.passcode_security import hash_passcode

        # Share is locked per-token AND IP is blocked.
        share = _make_share(db_session, passcode_hash=hash_passcode("Correct1!Pass"))
        share.passcode_locked_until = datetime.now(UTC) + timedelta(minutes=10)
        db_session.flush()

        now = time.time()
        ip_failure_tracker._memory_store["192.0.2.50"] = [now] * (IP_FAILURE_THRESHOLD + 1)

        with pytest.raises(HTTPException) as exc:
            _verify_passcode_or_raise(share, "Correct1!Pass", db_session, client_ip="192.0.2.50")
        # Per-IP message wins — not the per-token "X seconds" message.
        assert exc.value.status_code == 429
        assert "network" in str(exc.value.detail).lower()

    def test_no_client_ip_falls_back_to_per_token_only(self, db_session):
        """When the request has no ``client`` attribute (e.g., test stub,
        some proxy configurations), only the per-token gate applies.
        Backward-compat with callers that don't supply an IP."""
        from routes.export_sharing import _verify_passcode_or_raise
        from shared.passcode_security import hash_passcode

        share = _make_share(db_session, passcode_hash=hash_passcode("Correct1!Pass"))

        # No IP — should still work.
        with pytest.raises(HTTPException) as exc:
            _verify_passcode_or_raise(share, "WrongPassword1!", db_session, client_ip=None)
        assert exc.value.status_code == 403

        # Correct passcode still unlocks.
        _verify_passcode_or_raise(share, "Correct1!Pass", db_session, client_ip=None)

    def test_wrong_passcode_from_multiple_ips_tracks_each_separately(self, db_session):
        """Per-IP tracker is keyed by IP; one bad passcode from A.B.C.D
        doesn't count against E.F.G.H."""
        from routes.export_sharing import _verify_passcode_or_raise
        from shared import ip_failure_tracker
        from shared.passcode_security import hash_passcode

        share = _make_share(db_session, passcode_hash=hash_passcode("Correct1!Pass"))

        for ip in ("10.0.0.1", "10.0.0.2", "10.0.0.3"):
            with pytest.raises(HTTPException):
                _verify_passcode_or_raise(share, "WrongPassword1!", db_session, client_ip=ip)

        assert set(ip_failure_tracker._memory_store.keys()) == {"10.0.0.1", "10.0.0.2", "10.0.0.3"}
        for ip in ("10.0.0.1", "10.0.0.2", "10.0.0.3"):
            assert len(ip_failure_tracker._memory_store[ip]) == 1
