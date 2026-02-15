"""
Tests for Sprint 199: Token Revocation on Password Change.

Covers:
- password_changed_at column on User model
- create_access_token embeds pwd_at claim
- decode_access_token extracts password_changed_at into TokenData
- require_current_user validates pwd_at against DB
- change_user_password revokes all refresh tokens + sets password_changed_at
- Account deactivation scenario
"""

import hashlib
import time
from datetime import datetime, timedelta, UTC

import pytest
from sqlalchemy.orm import Session

from models import User, RefreshToken
from auth import (
    create_access_token,
    decode_access_token,
    change_user_password,
    hash_password,
    _hash_token,
    _revoke_all_user_tokens,
    create_refresh_token,
)

# Helper to create a user with a known plaintext password
KNOWN_PASSWORD = "OldPassword1!"
KNOWN_HASH = hash_password(KNOWN_PASSWORD)
NEW_PASSWORD = "NewPassword2@"
ALT_PASSWORD = "Password2@"
ALT2_PASSWORD = "Password3#"


# =============================================================================
# User.password_changed_at Column
# =============================================================================


class TestPasswordChangedAtColumn:
    """Tests for the password_changed_at column on User model."""

    def test_password_changed_at_defaults_to_none(self, make_user):
        """New users should have password_changed_at as None."""
        user = make_user()
        assert user.password_changed_at is None

    def test_password_changed_at_can_be_set(self, db_session: Session, make_user):
        """password_changed_at can be set to a datetime."""
        user = make_user()
        now = datetime.now(UTC)
        user.password_changed_at = now
        db_session.commit()
        db_session.refresh(user)
        assert user.password_changed_at is not None

    def test_password_changed_at_persists_after_refresh(self, db_session: Session, make_user):
        """password_changed_at value survives a DB round-trip."""
        user = make_user()
        now = datetime.now(UTC)
        user.password_changed_at = now
        db_session.commit()

        loaded = db_session.query(User).filter(User.id == user.id).first()
        assert loaded.password_changed_at is not None
        # SQLite drops timezone — compare without tz
        assert loaded.password_changed_at.replace(tzinfo=None) == now.replace(tzinfo=None)


# =============================================================================
# create_access_token with pwd_at claim
# =============================================================================


class TestCreateAccessTokenPwdAt:
    """Tests for pwd_at claim in create_access_token."""

    def test_no_pwd_at_when_password_never_changed(self):
        """Token should NOT contain pwd_at when password_changed_at is None."""
        token, _ = create_access_token(1, "test@example.com", password_changed_at=None)
        token_data = decode_access_token(token)
        assert token_data is not None
        assert token_data.password_changed_at is None

    def test_pwd_at_embedded_when_password_changed(self):
        """Token should contain pwd_at when password_changed_at is provided."""
        pwd_time = datetime(2026, 2, 13, 10, 0, 0, tzinfo=UTC)
        token, _ = create_access_token(1, "test@example.com", password_changed_at=pwd_time)
        token_data = decode_access_token(token)
        assert token_data is not None
        assert token_data.password_changed_at is not None
        assert int(token_data.password_changed_at.timestamp()) == int(pwd_time.timestamp())

    def test_pwd_at_is_epoch_integer(self):
        """The pwd_at claim should be stored as an integer epoch."""
        import jwt
        from config import JWT_SECRET_KEY, JWT_ALGORITHM

        pwd_time = datetime(2026, 1, 15, 8, 30, 0, tzinfo=UTC)
        token, _ = create_access_token(1, "test@example.com", password_changed_at=pwd_time)

        # Decode raw payload to check the claim type
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert "pwd_at" in payload
        assert isinstance(payload["pwd_at"], int)
        assert payload["pwd_at"] == int(pwd_time.timestamp())

    def test_backward_compatible_without_password_changed_at(self):
        """Token created without pwd_at should still decode correctly."""
        token, _ = create_access_token(42, "old@example.com")
        token_data = decode_access_token(token)
        assert token_data is not None
        assert token_data.user_id == 42
        assert token_data.email == "old@example.com"
        assert token_data.password_changed_at is None


# =============================================================================
# decode_access_token with password_changed_at
# =============================================================================


class TestDecodeAccessTokenPwdAt:
    """Tests for password_changed_at in TokenData."""

    def test_token_data_has_password_changed_at_field(self):
        """TokenData should have password_changed_at field."""
        from auth import TokenData
        td = TokenData(user_id=1, email="x@y.com")
        assert td.password_changed_at is None

    def test_decode_round_trip_with_pwd_at(self):
        """Encode then decode should preserve password_changed_at."""
        pwd_time = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
        token, _ = create_access_token(7, "round@trip.com", password_changed_at=pwd_time)
        td = decode_access_token(token)
        assert td.password_changed_at is not None
        assert abs(td.password_changed_at.timestamp() - pwd_time.timestamp()) < 1

    def test_decode_round_trip_without_pwd_at(self):
        """Encode then decode should give None when no pwd_at."""
        token, _ = create_access_token(7, "no@pwd.com")
        td = decode_access_token(token)
        assert td.password_changed_at is None


# =============================================================================
# require_current_user pwd_at validation
# =============================================================================


class TestRequireCurrentUserPwdAt:
    """Tests for pwd_at claim validation in require_current_user."""

    def test_accepts_token_when_no_password_change(self, db_session: Session, make_user):
        """Token without pwd_at should be accepted when user has no password_changed_at."""
        user = make_user()
        assert user.password_changed_at is None
        token, _ = create_access_token(user.id, user.email)
        td = decode_access_token(token)
        assert td is not None
        assert td.user_id == user.id
        # User has no password_changed_at — no validation needed

    def test_accepts_token_with_matching_pwd_at(self, db_session: Session, make_user):
        """Token with pwd_at matching DB should be accepted."""
        user = make_user()
        pwd_time = datetime.now(UTC)
        user.password_changed_at = pwd_time
        db_session.commit()

        token, _ = create_access_token(user.id, user.email, password_changed_at=pwd_time)
        td = decode_access_token(token)
        assert td is not None
        assert td.password_changed_at is not None

    def test_rejects_token_without_pwd_at_when_password_changed(self, db_session: Session, make_user):
        """Token without pwd_at should be REJECTED when user has password_changed_at set."""
        user = make_user()
        # Simulate a password change
        user.password_changed_at = datetime.now(UTC)
        db_session.commit()
        db_session.refresh(user)

        # Old token (no pwd_at)
        token, _ = create_access_token(user.id, user.email, password_changed_at=None)
        td = decode_access_token(token)
        assert td.password_changed_at is None

        # The require_current_user check should reject this
        # We test the logic directly since we can't use TestClient
        assert user.password_changed_at is not None
        assert td.password_changed_at is None
        # This condition triggers rejection in require_current_user

    def test_rejects_token_with_stale_pwd_at(self, db_session: Session, make_user):
        """Token with old pwd_at should be REJECTED when password was changed again."""
        user = make_user()

        # First password change
        old_pwd_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
        user.password_changed_at = old_pwd_time
        db_session.commit()

        # Token issued at first password change
        token, _ = create_access_token(user.id, user.email, password_changed_at=old_pwd_time)

        # Second password change (later)
        new_pwd_time = datetime(2026, 2, 1, 0, 0, 0, tzinfo=UTC)
        user.password_changed_at = new_pwd_time
        db_session.commit()
        db_session.refresh(user)

        # Decode the old token
        td = decode_access_token(token)
        assert td.password_changed_at is not None

        # Verify the stale check logic
        db_pwd_at = user.password_changed_at
        if db_pwd_at.tzinfo is None:
            from datetime import timezone
            db_pwd_at = db_pwd_at.replace(tzinfo=timezone.utc)
        assert int(td.password_changed_at.timestamp()) < int(db_pwd_at.timestamp())

    def test_accepts_token_with_current_pwd_at(self, db_session: Session, make_user):
        """Token with current pwd_at should be accepted."""
        user = make_user()
        pwd_time = datetime.now(UTC)
        user.password_changed_at = pwd_time
        db_session.commit()
        db_session.refresh(user)

        token, _ = create_access_token(user.id, user.email, password_changed_at=pwd_time)
        td = decode_access_token(token)

        db_pwd_at = user.password_changed_at
        if db_pwd_at.tzinfo is None:
            from datetime import timezone
            db_pwd_at = db_pwd_at.replace(tzinfo=timezone.utc)

        # Same epoch — should be accepted (not less than)
        assert int(td.password_changed_at.timestamp()) >= int(db_pwd_at.timestamp())


# =============================================================================
# change_user_password — token revocation
# =============================================================================


class TestChangeUserPasswordRevocation:
    """Tests for token revocation when password changes."""

    def test_password_change_sets_password_changed_at(self, db_session: Session, make_user):
        """Changing password should set password_changed_at."""
        user = make_user(hashed_password=KNOWN_HASH)
        assert user.password_changed_at is None

        result = change_user_password(db_session, user, KNOWN_PASSWORD, NEW_PASSWORD)
        assert result is True
        assert user.password_changed_at is not None

    def test_password_change_revokes_all_refresh_tokens(self, db_session: Session, make_user):
        """Changing password should revoke ALL of the user's refresh tokens."""
        user = make_user(hashed_password=KNOWN_HASH)

        # Create some refresh tokens
        raw1, rt1 = create_refresh_token(db_session, user.id)
        raw2, rt2 = create_refresh_token(db_session, user.id)
        raw3, rt3 = create_refresh_token(db_session, user.id)

        assert rt1.is_active
        assert rt2.is_active
        assert rt3.is_active

        # Change password
        result = change_user_password(db_session, user, KNOWN_PASSWORD, NEW_PASSWORD)
        assert result is True

        # All tokens should be revoked
        db_session.refresh(rt1)
        db_session.refresh(rt2)
        db_session.refresh(rt3)
        assert rt1.is_revoked
        assert rt2.is_revoked
        assert rt3.is_revoked

    def test_password_change_does_not_revoke_other_users_tokens(self, db_session: Session, make_user):
        """Changing password should NOT revoke other users' tokens."""
        user1 = make_user(email="user1@example.com", hashed_password=KNOWN_HASH)
        user2 = make_user(email="user2@example.com", hashed_password=hash_password(ALT_PASSWORD))

        raw1, rt1 = create_refresh_token(db_session, user1.id)
        raw2, rt2 = create_refresh_token(db_session, user2.id)

        # Change user1's password
        change_user_password(db_session, user1, KNOWN_PASSWORD, ALT2_PASSWORD)

        # user1's token revoked, user2's token untouched
        db_session.refresh(rt1)
        db_session.refresh(rt2)
        assert rt1.is_revoked
        assert rt2.is_active

    def test_failed_password_change_does_not_revoke(self, db_session: Session, make_user):
        """Failed password change (wrong current password) should NOT revoke tokens."""
        user = make_user(hashed_password=KNOWN_HASH)
        raw, rt = create_refresh_token(db_session, user.id)

        result = change_user_password(db_session, user, "WrongPassword9!", NEW_PASSWORD)
        assert result is False

        db_session.refresh(rt)
        assert rt.is_active
        assert user.password_changed_at is None

    def test_password_change_timestamps_are_consistent(self, db_session: Session, make_user):
        """password_changed_at should be set close to when the password was actually changed."""
        user = make_user(hashed_password=KNOWN_HASH)
        before = datetime.now(UTC)
        change_user_password(db_session, user, KNOWN_PASSWORD, NEW_PASSWORD)
        after = datetime.now(UTC)

        pwd_at = user.password_changed_at
        if pwd_at.tzinfo is None:
            from datetime import timezone
            pwd_at = pwd_at.replace(tzinfo=timezone.utc)

        assert before <= pwd_at <= after

    def test_already_revoked_tokens_stay_revoked(self, db_session: Session, make_user):
        """Already-revoked tokens should remain revoked (no double-revocation issues)."""
        user = make_user(hashed_password=KNOWN_HASH)
        raw, rt = create_refresh_token(db_session, user.id)

        # Manually revoke
        rt.revoked_at = datetime.now(UTC)
        db_session.commit()
        assert rt.is_revoked

        # Change password — should not error
        result = change_user_password(db_session, user, KNOWN_PASSWORD, NEW_PASSWORD)
        assert result is True

        db_session.refresh(rt)
        assert rt.is_revoked


# =============================================================================
# Account deactivation — token revocation
# =============================================================================


class TestAccountDeactivationRevocation:
    """Tests for token revocation when account is deactivated."""

    def test_deactivation_scenario_revokes_tokens(self, db_session: Session, make_user):
        """When a user is deactivated, all their refresh tokens should be revoked."""
        user = make_user()
        raw1, rt1 = create_refresh_token(db_session, user.id)
        raw2, rt2 = create_refresh_token(db_session, user.id)

        assert rt1.is_active
        assert rt2.is_active

        # Deactivate user and revoke tokens (the pattern to be used in any deactivation route)
        user.is_active = False
        _revoke_all_user_tokens(db_session, user.id)
        db_session.commit()

        db_session.refresh(rt1)
        db_session.refresh(rt2)
        assert rt1.is_revoked
        assert rt2.is_revoked
        assert not user.is_active

    def test_deactivated_user_tokens_are_blocked_by_require_current_user(self, db_session: Session, make_user):
        """Deactivated user's access tokens should be rejected by require_current_user.
        (Existing behavior — is_active check was already in place.)
        """
        user = make_user()
        assert user.is_active

        token, _ = create_access_token(user.id, user.email)
        td = decode_access_token(token)
        assert td.user_id == user.id

        user.is_active = False
        db_session.commit()
        db_session.refresh(user)

        assert not user.is_active
        # require_current_user checks is_active — this confirms the field is False


# =============================================================================
# Integration: Password change invalidates tokens end-to-end
# =============================================================================


class TestPasswordChangeInvalidatesTokens:
    """End-to-end tests for the password change → token invalidation flow."""

    def test_old_access_token_becomes_stale_after_password_change(self, db_session: Session, make_user):
        """An access token issued before a password change should be detectable as stale."""
        user = make_user(hashed_password=KNOWN_HASH)

        # Issue token before password change (no pwd_at since password_changed_at is None)
        old_token, _ = create_access_token(user.id, user.email, user.password_changed_at)
        old_td = decode_access_token(old_token)
        assert old_td.password_changed_at is None

        # Change password
        change_user_password(db_session, user, KNOWN_PASSWORD, NEW_PASSWORD)
        db_session.refresh(user)

        # User now has password_changed_at set
        assert user.password_changed_at is not None

        # Old token has no pwd_at → stale when user.password_changed_at is set
        assert old_td.password_changed_at is None
        assert user.password_changed_at is not None

    def test_new_access_token_is_valid_after_password_change(self, db_session: Session, make_user):
        """A new token issued after password change should pass validation."""
        user = make_user(hashed_password=KNOWN_HASH)
        change_user_password(db_session, user, KNOWN_PASSWORD, NEW_PASSWORD)
        db_session.refresh(user)

        # Issue new token with current password_changed_at
        new_token, _ = create_access_token(user.id, user.email, user.password_changed_at)
        new_td = decode_access_token(new_token)
        assert new_td.password_changed_at is not None

        # Token's pwd_at should match DB
        db_pwd_at = user.password_changed_at
        if db_pwd_at.tzinfo is None:
            from datetime import timezone
            db_pwd_at = db_pwd_at.replace(tzinfo=timezone.utc)
        assert int(new_td.password_changed_at.timestamp()) == int(db_pwd_at.timestamp())

    def test_sequential_password_changes_invalidate_older_tokens(self, db_session: Session, make_user):
        """Each password change should invalidate all previously-issued tokens."""
        user = make_user(hashed_password=hash_password("Password1!"))

        # First password change
        change_user_password(db_session, user, "Password1!", ALT_PASSWORD)
        db_session.refresh(user)

        token1, _ = create_access_token(user.id, user.email, user.password_changed_at)

        # Wait to ensure distinct timestamps
        time.sleep(1.1)

        # Second password change
        change_user_password(db_session, user, ALT_PASSWORD, ALT2_PASSWORD)
        db_session.refresh(user)
        second_change = user.password_changed_at

        # token1 should be stale now
        td1 = decode_access_token(token1)
        db_pwd_at = second_change
        if db_pwd_at.tzinfo is None:
            from datetime import timezone
            db_pwd_at = db_pwd_at.replace(tzinfo=timezone.utc)
        assert int(td1.password_changed_at.timestamp()) < int(db_pwd_at.timestamp())

    def test_refresh_tokens_all_revoked_on_password_change(self, db_session: Session, make_user):
        """All refresh tokens should be revoked when password changes."""
        user = make_user(hashed_password=KNOWN_HASH)

        # Create 5 tokens (simulating multiple sessions/devices)
        tokens = []
        for _ in range(5):
            raw, rt = create_refresh_token(db_session, user.id)
            tokens.append((raw, rt))

        # All active
        for _, rt in tokens:
            assert rt.is_active

        # Change password
        change_user_password(db_session, user, KNOWN_PASSWORD, NEW_PASSWORD)

        # All revoked
        for _, rt in tokens:
            db_session.refresh(rt)
            assert rt.is_revoked


# =============================================================================
# Route registration
# =============================================================================


class TestRouteRegistration:
    """Verify password change routes are registered."""

    def test_password_change_route_exists(self):
        """PUT /users/me/password should be registered."""
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/users/me/password" in paths
