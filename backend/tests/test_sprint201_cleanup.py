"""
Tests for Sprint 201: Cleanup & Explicit Configuration.

Covers:
- Explicit bcrypt rounds (bcrypt__rounds=12)
- jti (JWT ID) claim in access tokens
- cleanup_expired_refresh_tokens startup job
"""

import secrets
from datetime import UTC, datetime, timedelta

from models import RefreshToken

# =============================================================================
# TestBcryptRounds
# =============================================================================

class TestBcryptRounds:
    """Tests for explicit bcrypt rounds configuration (raw bcrypt, Sprint 279)."""

    def test_bcrypt_rounds_constant_is_12(self):
        """BCRYPT_ROUNDS constant is explicitly set to 12."""
        from auth import BCRYPT_ROUNDS
        assert BCRYPT_ROUNDS == 12

    def test_hash_password_produces_valid_hash(self):
        """hash_password produces verifiable hashes."""
        from auth import hash_password, verify_password
        hashed = hash_password("TestPassword123!")
        assert verify_password("TestPassword123!", hashed) is True
        assert verify_password("WrongPassword!", hashed) is False

    def test_hash_contains_rounds_marker(self):
        """bcrypt hash string contains the $12$ rounds marker."""
        from auth import hash_password
        hashed = hash_password("TestPassword123!")
        # bcrypt format: $2b$12$...
        assert "$12$" in hashed

    def test_hash_starts_with_bcrypt_prefix(self):
        """bcrypt hash starts with $2b$ prefix."""
        from auth import hash_password
        hashed = hash_password("TestPassword123!")
        assert hashed.startswith("$2b$")


# =============================================================================
# TestJtiClaim
# =============================================================================

class TestJtiClaim:
    """Tests for jti (JWT ID) claim in access tokens."""

    def test_access_token_contains_jti(self):
        """Access token payload includes a jti claim."""
        import jwt

        from auth import create_access_token
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        token, _ = create_access_token(user_id=1, email="test@example.com")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert "jti" in payload

    def test_jti_is_32_char_hex(self):
        """jti claim is a 32-character hex string (token_hex(16))."""
        import jwt

        from auth import create_access_token
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        token, _ = create_access_token(user_id=1, email="test@example.com")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        jti = payload["jti"]
        assert len(jti) == 32
        assert all(c in "0123456789abcdef" for c in jti)

    def test_jti_is_unique_per_token(self):
        """Each token gets a unique jti."""
        import jwt

        from auth import create_access_token
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        token1, _ = create_access_token(user_id=1, email="test@example.com")
        token2, _ = create_access_token(user_id=1, email="test@example.com")

        payload1 = jwt.decode(token1, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        payload2 = jwt.decode(token2, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert payload1["jti"] != payload2["jti"]

    def test_decode_still_works_with_jti(self):
        """decode_access_token still returns valid TokenData with jti present."""
        from auth import create_access_token, decode_access_token

        token, _ = create_access_token(user_id=42, email="jti@example.com")
        token_data = decode_access_token(token)
        assert token_data is not None
        assert token_data.user_id == 42
        assert token_data.email == "jti@example.com"


# =============================================================================
# TestCleanupExpiredRefreshTokens
# =============================================================================

class TestCleanupExpiredRefreshTokens:
    """Tests for cleanup_expired_refresh_tokens."""

    def test_deletes_revoked_tokens(self, db_session, make_user):
        """Revoked tokens are deleted by cleanup."""
        from auth import cleanup_expired_refresh_tokens, create_refresh_token, revoke_refresh_token

        user = make_user(email="cleanup_revoked@example.com")
        raw, _ = create_refresh_token(db_session, user.id)
        revoke_refresh_token(db_session, raw)

        count = cleanup_expired_refresh_tokens(db_session)
        assert count == 1

        # Verify token is gone from DB
        remaining = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).count()
        assert remaining == 0

    def test_deletes_expired_tokens(self, db_session, make_user):
        """Expired tokens are deleted by cleanup."""
        from auth import _hash_token, cleanup_expired_refresh_tokens

        user = make_user(email="cleanup_expired@example.com")
        raw_token = secrets.token_urlsafe(48)
        expired_token = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        db_session.add(expired_token)
        db_session.commit()

        count = cleanup_expired_refresh_tokens(db_session)
        assert count == 1

        remaining = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).count()
        assert remaining == 0

    def test_preserves_active_tokens(self, db_session, make_user):
        """Active (non-revoked, non-expired) tokens are NOT deleted."""
        from auth import cleanup_expired_refresh_tokens, create_refresh_token

        user = make_user(email="cleanup_active@example.com")
        _, db_token = create_refresh_token(db_session, user.id)

        count = cleanup_expired_refresh_tokens(db_session)
        assert count == 0

        # Token should still exist
        remaining = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).count()
        assert remaining == 1

    def test_mixed_tokens_only_stale_deleted(self, db_session, make_user):
        """Only stale tokens are deleted; active ones remain."""
        from auth import _hash_token, cleanup_expired_refresh_tokens, create_refresh_token, revoke_refresh_token

        user = make_user(email="cleanup_mixed@example.com")

        # Active token
        _, active_token = create_refresh_token(db_session, user.id)

        # Revoked token
        raw_revoked, _ = create_refresh_token(db_session, user.id)
        revoke_refresh_token(db_session, raw_revoked)

        # Expired token
        raw_expired = secrets.token_urlsafe(48)
        expired_token = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(raw_expired),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db_session.add(expired_token)
        db_session.commit()

        count = cleanup_expired_refresh_tokens(db_session)
        assert count == 2  # revoked + expired

        remaining = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).all()
        assert len(remaining) == 1
        assert remaining[0].id == active_token.id

    def test_returns_zero_when_no_stale(self, db_session, make_user):
        """Returns 0 when there are no stale tokens."""
        from auth import cleanup_expired_refresh_tokens

        count = cleanup_expired_refresh_tokens(db_session)
        assert count == 0

    def test_cleanup_across_multiple_users(self, db_session, make_user):
        """Cleanup works across multiple users."""
        from auth import cleanup_expired_refresh_tokens, create_refresh_token, revoke_refresh_token

        user_a = make_user(email="cleanup_a@example.com")
        user_b = make_user(email="cleanup_b@example.com")

        raw_a, _ = create_refresh_token(db_session, user_a.id)
        revoke_refresh_token(db_session, raw_a)

        raw_b, _ = create_refresh_token(db_session, user_b.id)
        revoke_refresh_token(db_session, raw_b)

        count = cleanup_expired_refresh_tokens(db_session)
        assert count == 2
