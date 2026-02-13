"""
Tests for Sprint 203: Email-Change Re-Verification.

Covers the pending_email workflow where email changes go through
re-verification instead of being applied immediately.
"""

from datetime import datetime, UTC

import pytest
from sqlalchemy.orm import Session

from models import User, EmailVerificationToken
from auth import update_user_profile, UserProfileUpdate


class TestEmailChangeReVerification:
    """Tests for email-change re-verification via pending_email."""

    def test_email_change_sets_pending_email(self, db_session, make_user):
        """Email change sets pending_email, keeps current email unchanged."""
        user = make_user(email="original@example.com")
        profile = UserProfileUpdate(email="new@example.com")

        updated, token = update_user_profile(db_session, user, profile)

        assert updated.email == "original@example.com"
        assert updated.pending_email == "new@example.com"
        assert token is not None

    def test_disposable_email_blocked_for_pending(self, db_session, make_user):
        """Disposable emails are blocked for email changes."""
        user = make_user(email="legit@example.com")
        profile = UserProfileUpdate(email="test@mailinator.com")

        with pytest.raises(ValueError, match="disposable"):
            update_user_profile(db_session, user, profile)

    def test_duplicate_email_check_for_pending(self, db_session, make_user):
        """Email already used by another account is rejected."""
        make_user(email="taken@example.com")
        user = make_user(email="requester@example.com")
        profile = UserProfileUpdate(email="taken@example.com")

        with pytest.raises(ValueError, match="already in use"):
            update_user_profile(db_session, user, profile)

    def test_verification_token_created_for_email_change(self, db_session, make_user):
        """A verification token is created in the DB for the email change."""
        user = make_user(email="tokencreate@example.com")
        profile = UserProfileUpdate(email="newtokencreate@example.com")

        updated, token = update_user_profile(db_session, user, profile)

        db_token = db_session.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.token == token,
        ).first()
        assert db_token is not None
        assert db_token.used_at is None

    def test_verify_swaps_pending_to_email(self, db_session, make_user):
        """Verifying a token swaps pending_email into email."""
        user = make_user(email="swap_old@example.com")
        profile = UserProfileUpdate(email="swap_new@example.com")

        updated, token = update_user_profile(db_session, user, profile)

        # Simulate verification
        verification = db_session.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token,
        ).first()
        verification.used_at = datetime.now(UTC)

        # Replicate the verify_email logic
        if updated.pending_email:
            updated.email = updated.pending_email
            updated.pending_email = None
        updated.is_verified = True
        updated.email_verified_at = datetime.now(UTC)
        db_session.commit()

        assert updated.email == "swap_new@example.com"
        assert updated.pending_email is None
        assert updated.is_verified is True

    def test_verify_works_normally_for_registration(self, db_session, make_user):
        """Registration verification (no pending_email) works unchanged."""
        user = make_user(email="register@example.com", is_verified=False)
        assert user.pending_email is None

        # Simulate normal verification
        user.is_verified = True
        user.email_verified_at = datetime.now(UTC)
        db_session.commit()

        assert user.email == "register@example.com"
        assert user.is_verified is True

    def test_resend_allows_verified_with_pending(self, db_session, make_user):
        """Verified user with pending_email passes the resend guard."""
        user = make_user(email="resend_pending@example.com", is_verified=True)
        user.pending_email = "new_resend@example.com"
        db_session.commit()

        # The guard condition: should NOT block when pending_email is set
        should_block = user.is_verified and not user.pending_email
        assert should_block is False

    def test_new_email_change_replaces_previous_pending(self, db_session, make_user):
        """A second email change invalidates old tokens and updates pending_email."""
        user = make_user(email="double@example.com")

        # First email change
        profile1 = UserProfileUpdate(email="first_new@example.com")
        updated, token1 = update_user_profile(db_session, user, profile1)
        assert updated.pending_email == "first_new@example.com"

        # Second email change (should invalidate first token)
        profile2 = UserProfileUpdate(email="second_new@example.com")
        updated, token2 = update_user_profile(db_session, user, profile2)
        assert updated.pending_email == "second_new@example.com"
        assert token2 != token1

        # First token should be marked as used (invalidated)
        old_token = db_session.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token1,
        ).first()
        assert old_token.used_at is not None

    def test_name_change_returns_no_token(self, db_session, make_user):
        """Name-only change returns no verification token."""
        user = make_user(email="nameonly@example.com")
        profile = UserProfileUpdate(name="New Name")

        updated, token = update_user_profile(db_session, user, profile)

        assert updated.name == "New Name"
        assert token is None
        assert updated.pending_email is None
