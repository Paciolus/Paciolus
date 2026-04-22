"""Sprint 700: tests for the legacy SHA-256 passcode cleanup.

Pins the format-detection invariants and the revoke-or-leave contract:
  * 64-char hex passcode_hash → revoked
  * bcrypt / Argon2id passcode_hash → untouched
  * Empty / NULL passcode_hash (no-passcode shares) → untouched
  * Already-revoked rows → not re-revoked
  * Dry-run mode returns the summary without writing
"""

from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime, timedelta

import bcrypt
import pytest

from export_share_model import ExportShare
from scripts.invalidate_legacy_passcode_shares import (
    _is_legacy_sha256,
    find_legacy_shares,
    invalidate_legacy_shares,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_PDF_BYTES = b"%PDF-1.4\n%\xff\xff\xff\xff\n1 0 obj\n<< >>\nendobj\n"


def _make_share(
    db_session,
    user,
    *,
    passcode_hash: str | None,
    revoked: bool = False,
    expires_in_hours: int = 24,
) -> ExportShare:
    now = datetime.now(UTC)
    share = ExportShare(
        share_token_hash=hashlib.sha256(f"tok_{user.id}_{passcode_hash}_{now.timestamp()}".encode()).hexdigest(),
        user_id=user.id,
        tool_name="trial_balance",
        export_format="pdf",
        export_data=VALID_PDF_BYTES,
        passcode_hash=passcode_hash,
        single_use=False,
        created_at=now,
        expires_at=now + timedelta(hours=expires_in_hours),
        access_count=0,
        revoked_at=now if revoked else None,
    )
    db_session.add(share)
    db_session.flush()
    return share


# ---------------------------------------------------------------------------
# Format detector
# ---------------------------------------------------------------------------


class TestLegacyFormatDetector:
    def test_sha256_hex_is_legacy(self):
        assert _is_legacy_sha256(hashlib.sha256(b"x").hexdigest()) is True

    def test_bcrypt_is_not_legacy(self):
        salt = bcrypt.gensalt(rounds=4)  # low cost = fast test
        h = bcrypt.hashpw(b"pw", salt).decode("utf-8")
        assert _is_legacy_sha256(h) is False

    def test_argon2id_is_not_legacy(self):
        # Realistic Argon2id format string; doesn't need to be a real hash.
        h = (
            "$argon2id$v=19$m=65536,t=3,p=4$"
            + base64.b64encode(b"0" * 16).decode()
            + "$"
            + base64.b64encode(b"0" * 32).decode()
        )
        assert _is_legacy_sha256(h) is False

    def test_empty_is_not_legacy(self):
        assert _is_legacy_sha256("") is False
        assert _is_legacy_sha256(None) is False

    def test_non_hex_64char_is_not_legacy(self):
        """A 64-char string with non-hex characters must not be classified as SHA-256."""
        assert _is_legacy_sha256("z" * 64) is False


# ---------------------------------------------------------------------------
# find_legacy_shares
# ---------------------------------------------------------------------------


class TestFindLegacyShares:
    def test_returns_only_legacy_hashed_live_shares(self, db_session, make_user):
        user = make_user(email="owner@example.com")
        legacy1 = _make_share(db_session, user, passcode_hash=hashlib.sha256(b"a").hexdigest())
        legacy2 = _make_share(db_session, user, passcode_hash=hashlib.sha256(b"b").hexdigest())

        bcrypt_share = _make_share(
            db_session,
            user,
            passcode_hash=bcrypt.hashpw(b"pw", bcrypt.gensalt(rounds=4)).decode("utf-8"),
        )
        no_passcode = _make_share(db_session, user, passcode_hash=None)
        already_revoked_legacy = _make_share(
            db_session,
            user,
            passcode_hash=hashlib.sha256(b"c").hexdigest(),
            revoked=True,
        )

        legacy = find_legacy_shares(db_session)
        legacy_ids = sorted(s.id for s in legacy)

        assert legacy_ids == sorted([legacy1.id, legacy2.id])
        assert bcrypt_share.id not in legacy_ids
        assert no_passcode.id not in legacy_ids
        assert already_revoked_legacy.id not in legacy_ids


# ---------------------------------------------------------------------------
# invalidate_legacy_shares
# ---------------------------------------------------------------------------


class TestInvalidateLegacyShares:
    def test_dry_run_reports_but_does_not_write(self, db_session, make_user):
        user = make_user(email="dry@example.com")
        legacy = _make_share(db_session, user, passcode_hash=hashlib.sha256(b"x").hexdigest())

        summary = invalidate_legacy_shares(db_session, apply=False)

        assert summary["applied"] is False
        assert summary["count"] == 1
        assert summary["share_ids"] == [legacy.id]
        # Important: the row is still live after dry-run.
        db_session.refresh(legacy)
        assert legacy.revoked_at is None

    def test_apply_revokes_only_legacy_rows(self, db_session, make_user):
        user = make_user(email="apply@example.com")
        legacy_share = _make_share(db_session, user, passcode_hash=hashlib.sha256(b"x").hexdigest())
        bcrypt_share = _make_share(
            db_session,
            user,
            passcode_hash=bcrypt.hashpw(b"pw", bcrypt.gensalt(rounds=4)).decode("utf-8"),
        )
        no_passcode = _make_share(db_session, user, passcode_hash=None)

        summary = invalidate_legacy_shares(db_session, apply=True)
        db_session.commit()

        assert summary["applied"] is True
        assert summary["count"] == 1
        assert summary["share_ids"] == [legacy_share.id]

        for share in (legacy_share, bcrypt_share, no_passcode):
            db_session.refresh(share)
        assert legacy_share.revoked_at is not None
        assert bcrypt_share.revoked_at is None
        assert no_passcode.revoked_at is None

    def test_apply_on_empty_population_is_noop(self, db_session, make_user):
        make_user(email="empty@example.com")
        # No shares created — the population is empty.

        summary = invalidate_legacy_shares(db_session, apply=True)
        assert summary["count"] == 0
        assert summary["share_ids"] == []
        assert summary["applied"] is False  # nothing to apply


# ---------------------------------------------------------------------------
# run_retention_cleanup integration
# ---------------------------------------------------------------------------


class TestRetentionCleanupIntegration:
    def test_run_retention_cleanup_includes_legacy_passcode_shares_key(self, db_session):
        """Nightly retention cleanup reports the new bucket even at zero."""
        from retention_cleanup import run_retention_cleanup

        results = run_retention_cleanup(db_session)
        assert "legacy_passcode_shares" in results
        assert isinstance(results["legacy_passcode_shares"], int)

    def test_run_retention_cleanup_revokes_legacy_shares(self, db_session, make_user):
        from retention_cleanup import run_retention_cleanup

        user = make_user(email="nightly@example.com")
        legacy = _make_share(
            db_session,
            user,
            passcode_hash=hashlib.sha256(b"x").hexdigest(),
        )

        results = run_retention_cleanup(db_session)

        assert results["legacy_passcode_shares"] == 1
        db_session.refresh(legacy)
        assert legacy.revoked_at is not None


# ---------------------------------------------------------------------------
# Entrypoint robustness
# ---------------------------------------------------------------------------


class TestScriptEntrypoint:
    def test_script_module_is_importable(self):
        import scripts.invalidate_legacy_passcode_shares as mod

        assert callable(mod.find_legacy_shares)
        assert callable(mod.invalidate_legacy_shares)
        assert callable(mod.main)

    @pytest.mark.parametrize(
        "args,expected_exit",
        [
            (["--help"], 0),
        ],
    )
    def test_cli_help_exits_clean(self, args, expected_exit, monkeypatch, capsys):
        import scripts.invalidate_legacy_passcode_shares as mod

        monkeypatch.setattr("sys.argv", ["prog", *args])
        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == expected_exit
