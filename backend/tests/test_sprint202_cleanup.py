"""
Tests for Sprint 202: Verification Token Cleanup Job.

Covers cleanup_expired_verification_tokens() which deletes
used or expired EmailVerificationToken rows on startup.
"""

from datetime import UTC, datetime, timedelta

from auth import hash_token
from email_service import generate_verification_token
from models import EmailVerificationToken


class TestCleanupExpiredVerificationTokens:
    """Tests for cleanup_expired_verification_tokens."""

    def test_deletes_used_tokens(self, db_session, make_user):
        """Used tokens (used_at set) are deleted by cleanup."""
        from auth import cleanup_expired_verification_tokens

        user = make_user(email="vcleanup_used@example.com")
        token_result = generate_verification_token()
        vt = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(token_result.token),
            expires_at=token_result.expires_at,
            used_at=datetime.now(UTC),
        )
        db_session.add(vt)
        db_session.commit()

        count = cleanup_expired_verification_tokens(db_session)
        assert count == 1

        remaining = db_session.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).count()
        assert remaining == 0

    def test_deletes_expired_tokens(self, db_session, make_user):
        """Expired tokens (expires_at in the past) are deleted by cleanup."""
        from auth import cleanup_expired_verification_tokens

        user = make_user(email="vcleanup_expired@example.com")
        vt = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token("expired_token_abc123"),
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        db_session.add(vt)
        db_session.commit()

        count = cleanup_expired_verification_tokens(db_session)
        assert count == 1

        remaining = db_session.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).count()
        assert remaining == 0

    def test_preserves_unused_unexpired_tokens(self, db_session, make_user):
        """Active (unused, unexpired) tokens are NOT deleted."""
        from auth import cleanup_expired_verification_tokens

        user = make_user(email="vcleanup_active@example.com")
        token_result = generate_verification_token()
        vt = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(token_result.token),
            expires_at=token_result.expires_at,
        )
        db_session.add(vt)
        db_session.commit()

        count = cleanup_expired_verification_tokens(db_session)
        assert count == 0

        remaining = db_session.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).count()
        assert remaining == 1

    def test_mixed_tokens_only_stale_deleted(self, db_session, make_user):
        """Only stale tokens are deleted; active ones remain."""
        from auth import cleanup_expired_verification_tokens

        user = make_user(email="vcleanup_mixed@example.com")

        # Active token (unused, unexpired)
        active_result = generate_verification_token()
        active_vt = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(active_result.token),
            expires_at=active_result.expires_at,
        )
        db_session.add(active_vt)

        # Used token
        used_result = generate_verification_token()
        used_vt = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(used_result.token),
            expires_at=used_result.expires_at,
            used_at=datetime.now(UTC),
        )
        db_session.add(used_vt)

        # Expired token
        expired_vt = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token("mixed_expired_token"),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db_session.add(expired_vt)
        db_session.commit()

        count = cleanup_expired_verification_tokens(db_session)
        assert count == 2  # used + expired

        remaining = db_session.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).all()
        assert len(remaining) == 1
        assert remaining[0].id == active_vt.id

    def test_returns_zero_when_no_stale(self, db_session):
        """Returns 0 when there are no stale tokens."""
        from auth import cleanup_expired_verification_tokens

        count = cleanup_expired_verification_tokens(db_session)
        assert count == 0

    def test_cleanup_across_multiple_users(self, db_session, make_user):
        """Cleanup works across multiple users."""
        from auth import cleanup_expired_verification_tokens

        user_a = make_user(email="vcleanup_a@example.com")
        user_b = make_user(email="vcleanup_b@example.com")

        # Stale token for user A (used)
        token_a = generate_verification_token()
        vt_a = EmailVerificationToken(
            user_id=user_a.id,
            token_hash=hash_token(token_a.token),
            expires_at=token_a.expires_at,
            used_at=datetime.now(UTC),
        )
        db_session.add(vt_a)

        # Stale token for user B (expired)
        vt_b = EmailVerificationToken(
            user_id=user_b.id,
            token_hash=hash_token("multi_user_expired"),
            expires_at=datetime.now(UTC) - timedelta(hours=2),
        )
        db_session.add(vt_b)
        db_session.commit()

        count = cleanup_expired_verification_tokens(db_session)
        assert count == 2
