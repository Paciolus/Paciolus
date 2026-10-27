"""Sprint 847 (security review M4, L3, L4, L14): ending sessions really ends them.

- M4: changing the email (the recovery address) needs the current password,
  and completing the swap ends every session and outstanding reset link.
- L3: "revoke all sessions" ends live access tokens, not only refresh tokens.
- L4: only the newest password-reset link works.
- L14: impersonation tokens carry ``pwd_at``, so they work for users who have
  changed their password.

(M3 — refresh-token reuse detection surviving cleanup — is in
``test_sprint201_cleanup.py``.)
"""

import time
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from auth import (
    UserProfileUpdate,
    create_access_token,
    create_impersonation_token,
    create_refresh_token,
    hash_password,
    hash_token,
    require_current_user,
    update_user_profile,
)
from models import EmailVerificationToken, PasswordResetToken, RefreshToken
from services.auth.recovery import complete_password_reset, initiate_password_reset
from services.auth.registration import complete_email_verification
from services.auth.sessions import revoke_all_user_sessions

_PASSWORD = "Correct-Horse-Battery-9"
_HASH = hash_password(_PASSWORD)


def _get() -> Request:
    return Request({"type": "http", "method": "GET", "headers": [], "path": "/", "query_string": b""})


def _access_token(user) -> str:
    token, _ = create_access_token(user.id, user.email, user.password_changed_at)
    return token


def _wait_for_next_second() -> None:
    # Revocation compares whole epoch seconds (as the pwd_at check does), so a
    # token minted in the same second as the revocation is still accepted.
    time.sleep(1.05 - (time.time() % 1))


@pytest.fixture
def user(make_user):
    return make_user(email="hardening@example.com", hashed_password=_HASH)


# ---------------------------------------------------------------------------
# M4: email change
# ---------------------------------------------------------------------------


class TestEmailChangeNeedsPassword:
    def test_missing_password_is_refused(self, db_session, user):
        with pytest.raises(ValueError, match="current password"):
            update_user_profile(db_session, user, UserProfileUpdate(email="attacker@example.com"))
        db_session.refresh(user)
        assert user.pending_email is None

    def test_wrong_password_is_refused(self, db_session, user):
        with pytest.raises(ValueError, match="incorrect"):
            update_user_profile(
                db_session, user, UserProfileUpdate(email="attacker@example.com", current_password="guess")
            )
        db_session.refresh(user)
        assert user.pending_email is None

    def test_name_change_needs_no_password(self, db_session, user):
        updated, token = update_user_profile(db_session, user, UserProfileUpdate(name="New Name"))
        assert updated.name == "New Name"
        assert token is None

    def test_unchanged_email_needs_no_password(self, db_session, user):
        updated, token = update_user_profile(db_session, user, UserProfileUpdate(email=user.email, name="Same"))
        assert token is None and updated.name == "Same"


class TestEmailSwapEndsEverySession:
    def test_swap_revokes_refresh_tokens_access_tokens_and_reset_links(self, db_session, user):
        old_access = _access_token(user)
        create_refresh_token(db_session, user.id)
        reset = initiate_password_reset(db_session, user.email)

        _, verification = update_user_profile(
            db_session, user, UserProfileUpdate(email="new-home@example.com", current_password=_PASSWORD)
        )
        assert require_current_user(_get(), old_access, db_session).id == user.id  # still valid until the swap

        _wait_for_next_second()
        complete_email_verification(db_session, verification)
        db_session.refresh(user)
        assert user.email == "new-home@example.com"

        active_refresh = (
            db_session.query(RefreshToken)
            .filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at == None)  # noqa: E711
            .count()
        )
        assert active_refresh == 0

        with pytest.raises(HTTPException) as exc:
            require_current_user(_get(), old_access, db_session)
        assert exc.value.status_code == 401

        reset_row = (
            db_session.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == hash_token(reset.token_result.token))
            .one()
        )
        assert reset_row.used_at is not None

        # A fresh login after the swap works.
        assert require_current_user(_get(), _access_token(user), db_session).id == user.id

    def test_plain_registration_verification_revokes_nothing(self, db_session, make_user):
        new_user = make_user(email="fresh@example.com", is_verified=False, hashed_password=_HASH)
        create_refresh_token(db_session, new_user.id)
        db_session.add(
            EmailVerificationToken(
                user_id=new_user.id,
                token_hash=hash_token("plain-verify-token"),
                expires_at=datetime(2099, 1, 1, tzinfo=UTC),
            )
        )
        db_session.commit()

        complete_email_verification(db_session, "plain-verify-token")
        db_session.refresh(new_user)
        assert new_user.sessions_revoked_at is None
        assert (
            db_session.query(RefreshToken)
            .filter(RefreshToken.user_id == new_user.id, RefreshToken.revoked_at == None)  # noqa: E711
            .count()
            == 1
        )


# ---------------------------------------------------------------------------
# L3: revoke all sessions
# ---------------------------------------------------------------------------


class TestRevokeAllEndsAccessTokens:
    def test_access_token_issued_before_revocation_is_rejected(self, db_session, user):
        old_access = _access_token(user)
        _wait_for_next_second()
        revoke_all_user_sessions(db_session, user)

        with pytest.raises(HTTPException) as exc:
            require_current_user(_get(), old_access, db_session)
        assert exc.value.status_code == 401

    def test_token_issued_after_revocation_works(self, db_session, user):
        revoke_all_user_sessions(db_session, user)
        _wait_for_next_second()
        assert require_current_user(_get(), _access_token(user), db_session).id == user.id


# ---------------------------------------------------------------------------
# L4: password-reset links
# ---------------------------------------------------------------------------


def _reset_row(db_session, raw: str) -> PasswordResetToken:
    return db_session.query(PasswordResetToken).filter(PasswordResetToken.token_hash == hash_token(raw)).one()


class TestOnlyNewestResetLinkWorks:
    def test_new_request_retires_older_link(self, db_session, user):
        first = initiate_password_reset(db_session, user.email).token_result.token
        second = initiate_password_reset(db_session, user.email).token_result.token

        assert _reset_row(db_session, first).used_at is not None
        assert _reset_row(db_session, second).used_at is None
        with pytest.raises(ValueError, match="already been used"):
            complete_password_reset(db_session, first, "Another-Strong-Pass-1")

    def test_completed_reset_retires_other_links(self, db_session, user):
        first = initiate_password_reset(db_session, user.email).token_result.token
        # A second outstanding row (e.g. issued before this sprint shipped).
        db_session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token("older-outstanding-link"),
                expires_at=datetime(2099, 1, 1, tzinfo=UTC),
            )
        )
        db_session.commit()

        complete_password_reset(db_session, first, "Another-Strong-Pass-1")
        assert _reset_row(db_session, "older-outstanding-link").used_at is not None


# ---------------------------------------------------------------------------
# L14: impersonation after a password change
# ---------------------------------------------------------------------------


class TestImpersonationAfterPasswordChange:
    def test_impersonating_a_user_who_changed_password_works(self, db_session, make_user):
        target = make_user(email="changed_pw@example.com")
        target.password_changed_at = datetime.now(UTC)
        db_session.commit()

        token, _ = create_impersonation_token(
            target.id, target.email, admin_user_id=999, password_changed_at=target.password_changed_at
        )
        assert require_current_user(_get(), token, db_session).id == target.id
