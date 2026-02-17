"""
Tests for Sprint 197: Refresh Token Infrastructure.

Covers:
- RefreshToken model (columns, properties, timezone handling)
- _hash_token helper
- create_refresh_token
- rotate_refresh_token (happy path, reuse detection, expired, inactive)
- revoke_refresh_token / _revoke_all_user_tokens
- AuthResponse schema (includes refresh_token field)
- Route registration (/auth/refresh, /auth/logout)
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import pytest

from auth import (
    AuthResponse,
    LogoutRequest,
    RefreshRequest,
    _hash_token,
    _revoke_all_user_tokens,
    create_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)
from models import RefreshToken

# =============================================================================
# TestRefreshTokenModel
# =============================================================================

class TestRefreshTokenModel:
    """Tests for the RefreshToken SQLAlchemy model."""

    def test_columns_exist(self, make_refresh_token):
        """All expected columns are present on the model."""
        _, rt = make_refresh_token()
        assert rt.id is not None
        assert rt.user_id is not None
        assert rt.token_hash is not None
        assert rt.expires_at is not None
        assert rt.created_at is not None

    def test_revoked_at_nullable(self, make_refresh_token):
        """revoked_at is None by default."""
        _, rt = make_refresh_token()
        assert rt.revoked_at is None

    def test_replaced_by_hash_nullable(self, make_refresh_token):
        """replaced_by_hash is None by default."""
        _, rt = make_refresh_token()
        assert rt.replaced_by_hash is None

    def test_user_relationship(self, make_refresh_token, make_user):
        """RefreshToken.user backref works."""
        user = make_user(email="rel_test@example.com")
        _, rt = make_refresh_token(user=user)
        assert rt.user.id == user.id

    def test_is_expired_false_when_future(self, make_refresh_token):
        """is_expired returns False when expires_at is in the future."""
        _, rt = make_refresh_token(
            expires_at=datetime.now(UTC) + timedelta(days=7)
        )
        assert rt.is_expired is False

    def test_is_expired_true_when_past(self, make_refresh_token):
        """is_expired returns True when expires_at is in the past."""
        _, rt = make_refresh_token(
            expires_at=datetime.now(UTC) - timedelta(seconds=1)
        )
        assert rt.is_expired is True

    def test_is_expired_sqlite_naive_datetime(self, db_session, make_user):
        """is_expired handles timezone-naive datetimes from SQLite."""
        user = make_user(email="naive_tz@example.com")
        # Simulate SQLite stripping timezone info
        naive_past = datetime(2020, 1, 1)
        rt = RefreshToken(
            user_id=user.id,
            token_hash=hashlib.sha256(b"naive_test").hexdigest(),
            expires_at=naive_past,
        )
        db_session.add(rt)
        db_session.flush()
        assert rt.is_expired is True

    def test_is_revoked_false_by_default(self, make_refresh_token):
        """is_revoked returns False when revoked_at is None."""
        _, rt = make_refresh_token()
        assert rt.is_revoked is False

    def test_is_revoked_true_when_set(self, make_refresh_token):
        """is_revoked returns True when revoked_at is set."""
        _, rt = make_refresh_token(revoked_at=datetime.now(UTC))
        assert rt.is_revoked is True

    def test_is_active_true_when_valid(self, make_refresh_token):
        """is_active returns True when not expired and not revoked."""
        _, rt = make_refresh_token()
        assert rt.is_active is True

    def test_is_active_false_when_expired(self, make_refresh_token):
        """is_active returns False when expired."""
        _, rt = make_refresh_token(
            expires_at=datetime.now(UTC) - timedelta(seconds=1)
        )
        assert rt.is_active is False

    def test_is_active_false_when_revoked(self, make_refresh_token):
        """is_active returns False when revoked."""
        _, rt = make_refresh_token(revoked_at=datetime.now(UTC))
        assert rt.is_active is False

    def test_repr(self, make_refresh_token):
        """__repr__ includes id and user_id."""
        _, rt = make_refresh_token()
        rep = repr(rt)
        assert "RefreshToken" in rep
        assert str(rt.id) in rep

    def test_token_hash_unique(self, db_session, make_user):
        """token_hash has a unique constraint."""
        user = make_user(email="uniq_test@example.com")
        hash_val = hashlib.sha256(b"duplicate").hexdigest()
        rt1 = RefreshToken(
            user_id=user.id,
            token_hash=hash_val,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(rt1)
        db_session.flush()

        rt2 = RefreshToken(
            user_id=user.id,
            token_hash=hash_val,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db_session.add(rt2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.flush()
        db_session.rollback()

    def test_user_backref_multiple_tokens(self, make_user, make_refresh_token):
        """User.refresh_tokens backref returns all tokens for that user."""
        user = make_user(email="multi_token@example.com")
        make_refresh_token(user=user)
        make_refresh_token(user=user)
        assert len(user.refresh_tokens) == 2


# =============================================================================
# TestHashToken
# =============================================================================

class TestHashToken:
    """Tests for the _hash_token helper."""

    def test_deterministic(self):
        """Same input produces same hash."""
        raw = "test_token_value"
        assert _hash_token(raw) == _hash_token(raw)

    def test_64_char_hex(self):
        """Output is a 64-character hex string (SHA-256)."""
        result = _hash_token("any_token")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_different_inputs_different_hashes(self):
        """Different inputs produce different hashes."""
        assert _hash_token("token_a") != _hash_token("token_b")

    def test_matches_hashlib_directly(self):
        """Output matches direct hashlib SHA-256."""
        raw = "verify_against_hashlib"
        expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        assert _hash_token(raw) == expected


# =============================================================================
# TestCreateRefreshToken
# =============================================================================

class TestCreateRefreshToken:
    """Tests for create_refresh_token."""

    def test_returns_raw_and_db_record(self, db_session, make_user):
        """Returns a tuple of (raw_token_string, RefreshToken)."""
        user = make_user(email="create_rt@example.com")
        raw, db_token = create_refresh_token(db_session, user.id)
        assert isinstance(raw, str)
        assert isinstance(db_token, RefreshToken)

    def test_stores_hash_not_raw(self, db_session, make_user):
        """Database stores the hash, not the raw token."""
        user = make_user(email="hash_check@example.com")
        raw, db_token = create_refresh_token(db_session, user.id)
        assert db_token.token_hash != raw
        assert db_token.token_hash == _hash_token(raw)

    def test_correct_expiry(self, db_session, make_user):
        """Token expires in REFRESH_TOKEN_EXPIRATION_DAYS."""
        from config import REFRESH_TOKEN_EXPIRATION_DAYS
        user = make_user(email="expiry_check@example.com")
        before = datetime.now(UTC)
        raw, db_token = create_refresh_token(db_session, user.id)
        after = datetime.now(UTC)

        expected_min = before + timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS)
        expected_max = after + timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS)

        # Handle timezone-naive from SQLite
        exp = db_token.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)

        assert expected_min <= exp <= expected_max

    def test_token_is_active(self, db_session, make_user):
        """Newly created token is active."""
        user = make_user(email="active_check@example.com")
        _, db_token = create_refresh_token(db_session, user.id)
        assert db_token.is_active is True

    def test_user_id_set(self, db_session, make_user):
        """Token is linked to the correct user."""
        user = make_user(email="userid_check@example.com")
        _, db_token = create_refresh_token(db_session, user.id)
        assert db_token.user_id == user.id


# =============================================================================
# TestRotateRefreshToken
# =============================================================================

class TestRotateRefreshToken:
    """Tests for rotate_refresh_token."""

    def test_happy_path_returns_new_pair(self, db_session, make_user):
        """Rotation returns new access token, new refresh token, and user."""
        user = make_user(email="rotate_happy@example.com")
        raw, _ = create_refresh_token(db_session, user.id)

        access, new_refresh, returned_user = rotate_refresh_token(db_session, raw)
        assert isinstance(access, str)
        assert isinstance(new_refresh, str)
        assert returned_user.id == user.id

    def test_old_token_revoked(self, db_session, make_user):
        """Old token is revoked after rotation."""
        user = make_user(email="rotate_revoke@example.com")
        raw, old_token = create_refresh_token(db_session, user.id)

        rotate_refresh_token(db_session, raw)
        db_session.refresh(old_token)
        assert old_token.is_revoked is True

    def test_replaced_by_hash_set(self, db_session, make_user):
        """Old token's replaced_by_hash points to the new token's hash."""
        user = make_user(email="rotate_chain@example.com")
        raw, old_token = create_refresh_token(db_session, user.id)

        _, new_refresh, _ = rotate_refresh_token(db_session, raw)
        db_session.refresh(old_token)
        assert old_token.replaced_by_hash == _hash_token(new_refresh)

    def test_new_token_is_different(self, db_session, make_user):
        """New refresh token is different from the old one."""
        user = make_user(email="rotate_diff@example.com")
        raw, _ = create_refresh_token(db_session, user.id)

        _, new_refresh, _ = rotate_refresh_token(db_session, raw)
        assert new_refresh != raw

    def test_reuse_detection_revokes_all(self, db_session, make_user):
        """Presenting a revoked token revokes ALL user tokens."""
        from fastapi import HTTPException

        user = make_user(email="reuse_detect@example.com")
        raw1, _ = create_refresh_token(db_session, user.id)

        # Rotate once — raw1 is now revoked
        _, raw2, _ = rotate_refresh_token(db_session, raw1)

        # Present the revoked raw1 again → reuse detection
        with pytest.raises(HTTPException) as exc_info:
            rotate_refresh_token(db_session, raw1)
        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail.lower()

        # raw2 should also be revoked now
        hash2 = _hash_token(raw2)
        token2 = db_session.query(RefreshToken).filter(
            RefreshToken.token_hash == hash2
        ).first()
        assert token2.is_revoked is True

    def test_expired_token_raises_401(self, db_session, make_user):
        """Expired token raises 401."""
        from fastapi import HTTPException

        user = make_user(email="rotate_expired@example.com")
        raw_token = secrets.token_urlsafe(48)
        token_hash = _hash_token(raw_token)
        db_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
        db_session.add(db_token)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            rotate_refresh_token(db_session, raw_token)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_invalid_token_raises_401(self, db_session):
        """Completely unknown token raises 401."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            rotate_refresh_token(db_session, "nonexistent_token")
        assert exc_info.value.status_code == 401

    def test_inactive_user_raises_401(self, db_session, make_user):
        """Inactive user cannot refresh."""
        from fastapi import HTTPException

        user = make_user(email="inactive_refresh@example.com", is_active=False)
        raw, _ = create_refresh_token(db_session, user.id)

        with pytest.raises(HTTPException) as exc_info:
            rotate_refresh_token(db_session, raw)
        assert exc_info.value.status_code == 401
        assert "inactive" in exc_info.value.detail.lower()


# =============================================================================
# TestRevokeRefreshToken
# =============================================================================

class TestRevokeRefreshToken:
    """Tests for revoke_refresh_token."""

    def test_revoke_existing(self, db_session, make_user):
        """Revoking an active token returns True."""
        user = make_user(email="revoke_exist@example.com")
        raw, _ = create_refresh_token(db_session, user.id)
        assert revoke_refresh_token(db_session, raw) is True

    def test_revoke_nonexistent(self, db_session):
        """Revoking a nonexistent token returns False."""
        assert revoke_refresh_token(db_session, "does_not_exist") is False

    def test_revoke_already_revoked(self, db_session, make_user):
        """Revoking an already-revoked token returns False."""
        user = make_user(email="revoke_twice@example.com")
        raw, _ = create_refresh_token(db_session, user.id)
        revoke_refresh_token(db_session, raw)
        assert revoke_refresh_token(db_session, raw) is False

    def test_revoke_does_not_affect_others(self, db_session, make_user):
        """Revoking one token does not affect other tokens for the same user."""
        user = make_user(email="revoke_others@example.com")
        raw1, _ = create_refresh_token(db_session, user.id)
        raw2, token2 = create_refresh_token(db_session, user.id)

        revoke_refresh_token(db_session, raw1)
        db_session.refresh(token2)
        assert token2.is_active is True

    def test_revoked_token_has_timestamp(self, db_session, make_user):
        """Revoked token has revoked_at set."""
        user = make_user(email="revoke_ts@example.com")
        raw, db_token = create_refresh_token(db_session, user.id)
        revoke_refresh_token(db_session, raw)
        db_session.refresh(db_token)
        assert db_token.revoked_at is not None


# =============================================================================
# TestRevokeAllUserTokens
# =============================================================================

class TestRevokeAllUserTokens:
    """Tests for _revoke_all_user_tokens."""

    def test_revokes_all_active(self, db_session, make_user):
        """All active tokens for a user are revoked."""
        user = make_user(email="revoke_all@example.com")
        _, t1 = create_refresh_token(db_session, user.id)
        _, t2 = create_refresh_token(db_session, user.id)
        _, t3 = create_refresh_token(db_session, user.id)

        count = _revoke_all_user_tokens(db_session, user.id)
        assert count == 3

        for t in [t1, t2, t3]:
            db_session.refresh(t)
            assert t.is_revoked is True

    def test_returns_count(self, db_session, make_user):
        """Returns the number of tokens revoked."""
        user = make_user(email="revoke_count@example.com")
        create_refresh_token(db_session, user.id)
        create_refresh_token(db_session, user.id)

        count = _revoke_all_user_tokens(db_session, user.id)
        assert count == 2

    def test_leaves_already_revoked_unchanged(self, db_session, make_user):
        """Already-revoked tokens are not double-revoked."""
        user = make_user(email="already_rev@example.com")
        raw1, _ = create_refresh_token(db_session, user.id)
        revoke_refresh_token(db_session, raw1)  # Revoke one manually
        create_refresh_token(db_session, user.id)  # One still active

        count = _revoke_all_user_tokens(db_session, user.id)
        assert count == 1  # Only the active one

    def test_no_active_tokens(self, db_session, make_user):
        """Returns 0 when no active tokens exist."""
        user = make_user(email="no_active@example.com")
        count = _revoke_all_user_tokens(db_session, user.id)
        assert count == 0

    def test_does_not_affect_other_users(self, db_session, make_user):
        """Revoking user A's tokens does not affect user B."""
        user_a = make_user(email="user_a@example.com")
        user_b = make_user(email="user_b@example.com")
        create_refresh_token(db_session, user_a.id)
        _, token_b = create_refresh_token(db_session, user_b.id)

        _revoke_all_user_tokens(db_session, user_a.id)
        db_session.refresh(token_b)
        assert token_b.is_active is True


# =============================================================================
# TestSchemas
# =============================================================================

class TestAuthResponseSchema:
    """Tests for the updated AuthResponse schema."""

    def test_includes_refresh_token_field(self):
        """AuthResponse has a refresh_token field."""
        fields = AuthResponse.model_fields
        assert "refresh_token" in fields

    def test_construction_with_refresh_token(self):
        """AuthResponse can be constructed with refresh_token."""
        from auth import UserResponse
        user_data = UserResponse(
            id=1, email="test@test.com", is_active=True,
            is_verified=True, tier="free",
            created_at=datetime.now(UTC),
        )
        resp = AuthResponse(
            access_token="at",
            refresh_token="rt",
            expires_in=3600,
            user=user_data,
        )
        assert resp.refresh_token == "rt"
        assert resp.access_token == "at"

    def test_refresh_token_required(self):
        """AuthResponse fails without refresh_token."""
        from pydantic import ValidationError

        from auth import UserResponse
        user_data = UserResponse(
            id=1, email="test@test.com", is_active=True,
            is_verified=True, tier="free",
            created_at=datetime.now(UTC),
        )
        with pytest.raises(ValidationError):
            AuthResponse(
                access_token="at",
                expires_in=3600,
                user=user_data,
            )


class TestRefreshRequestSchema:
    """Tests for RefreshRequest schema."""

    def test_valid(self):
        req = RefreshRequest(refresh_token="some_token")
        assert req.refresh_token == "some_token"

    def test_empty_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RefreshRequest(refresh_token="")


class TestLogoutRequestSchema:
    """Tests for LogoutRequest schema."""

    def test_valid(self):
        req = LogoutRequest(refresh_token="some_token")
        assert req.refresh_token == "some_token"

    def test_empty_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            LogoutRequest(refresh_token="")


# =============================================================================
# TestRouteRegistration
# =============================================================================

class TestRouteRegistration:
    """Tests that refresh/logout routes are registered on the app."""

    def test_refresh_route_registered(self):
        """POST /auth/refresh is registered."""
        from main import app
        paths = [route.path for route in app.routes]
        assert "/auth/refresh" in paths

    def test_logout_route_registered(self):
        """POST /auth/logout is registered."""
        from main import app
        paths = [route.path for route in app.routes]
        assert "/auth/logout" in paths

    def test_refresh_route_method(self):
        """POST /auth/refresh accepts POST."""
        from main import app
        for route in app.routes:
            if getattr(route, "path", None) == "/auth/refresh":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("/auth/refresh route not found")

    def test_logout_route_method(self):
        """POST /auth/logout accepts POST."""
        from main import app
        for route in app.routes:
            if getattr(route, "path", None) == "/auth/logout":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("/auth/logout route not found")
