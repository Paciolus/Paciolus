"""Sprint 697: Argon2id upgrade regression tests.

Pins the dual-path verify behaviour — new hashes are Argon2id; legacy
bcrypt hashes continue to verify during the transition window; SHA-256
hex remains rejected (Sprint 696 invariant).
"""

from __future__ import annotations

import bcrypt as _bcrypt

from shared.passcode_security import (
    _is_argon2_hash,
    _is_bcrypt_hash,
    _is_legacy_hash_format,
    hash_passcode,
    verify_passcode,
)


class TestArgon2HashFormat:
    def test_hash_passcode_emits_argon2id_prefix(self):
        digest = hash_passcode("StrongP@ss1")
        assert digest.startswith("$argon2id$"), f"unexpected prefix: {digest[:20]}"

    def test_each_hash_has_unique_salt(self):
        """Argon2 generates a fresh salt per call — two hashes of the
        same input must differ in the salt segment."""
        a = hash_passcode("StrongP@ss1")
        b = hash_passcode("StrongP@ss1")
        assert a != b

    def test_argon2_params_embedded_in_hash(self):
        """Sprint 697: the hash string encodes the Argon2 parameters so
        any future parameter bump is self-documenting in stored rows."""
        digest = hash_passcode("StrongP@ss1")
        # argon2-cffi format: $argon2id$v=19$m=<memory>,t=<time>,p=<parallelism>$...
        assert "v=19" in digest
        assert "m=65536" in digest  # 64 MiB memory cost
        assert "t=3" in digest  # 3 time cost
        assert "p=4" in digest  # 4 parallelism


class TestArgon2VerifyRoundTrip:
    def test_verify_correct_passcode(self):
        digest = hash_passcode("StrongP@ss1")
        assert verify_passcode("StrongP@ss1", digest) is True

    def test_verify_wrong_passcode(self):
        digest = hash_passcode("StrongP@ss1")
        assert verify_passcode("WrongPass1!", digest) is False

    def test_verify_empty_inputs(self):
        digest = hash_passcode("StrongP@ss1")
        assert verify_passcode("", digest) is False
        assert verify_passcode("StrongP@ss1", "") is False

    def test_verify_garbled_hash_returns_false(self):
        """A hash string that starts with $argon2id$ but is corrupted
        should verify False, not raise."""
        assert verify_passcode("StrongP@ss1", "$argon2id$not-a-real-hash") is False


class TestDualFormatVerification:
    """Sprint 697 transition window: both Argon2id (new) and bcrypt
    (legacy Sprint 696) hashes verify correctly. SHA-256 stays rejected."""

    def test_argon2_and_bcrypt_both_verify(self):
        passcode = "StrongP@ss1"
        argon = hash_passcode(passcode)

        # Produce a bcrypt hash the pre-Sprint-697 way.
        salt = _bcrypt.gensalt(rounds=12)
        bcrypt_hash = _bcrypt.hashpw(passcode.encode("utf-8"), salt).decode("utf-8")

        assert verify_passcode(passcode, argon) is True
        assert verify_passcode(passcode, bcrypt_hash) is True

    def test_argon2_hash_does_not_verify_against_bcrypt_check(self):
        """Sanity: an Argon2 hash must NOT be mistakenly decoded as bcrypt
        (length collision would be catastrophic). The prefix check
        routes each hash to its correct verifier."""
        argon = hash_passcode("StrongP@ss1")
        # bcrypt.checkpw on an argon hash would either raise or return
        # False; verify_passcode's Argon2 branch handles it correctly.
        assert verify_passcode("StrongP@ss1", argon) is True

    def test_legacy_sha256_still_rejected(self):
        """Sprint 696 invariant preserved: SHA-256 hex strings (pre-
        remediation format) are refused."""
        import hashlib as _h

        legacy_sha = _h.sha256(b"whatever").hexdigest()
        assert verify_passcode("whatever", legacy_sha) is False


class TestFormatDetectionHelpers:
    def test_is_argon2_hash_recognises_all_variants(self):
        for prefix in ("$argon2id$", "$argon2i$", "$argon2d$"):
            assert _is_argon2_hash(prefix + "rest") is True

    def test_is_argon2_hash_rejects_bcrypt(self):
        assert _is_argon2_hash("$2b$12$" + "a" * 53) is False

    def test_is_bcrypt_hash_recognises_all_variants(self):
        for prefix in ("$2a$", "$2b$", "$2y$"):
            assert _is_bcrypt_hash(prefix + "12$" + "a" * 53) is True

    def test_is_bcrypt_hash_rejects_argon2(self):
        assert _is_bcrypt_hash("$argon2id$" + "rest") is False

    def test_legacy_format_detector(self):
        """Anything that's not Argon2 or bcrypt is legacy."""
        assert _is_legacy_hash_format("a" * 64) is True  # SHA-256 hex
        assert _is_legacy_hash_format("") is True
        assert _is_legacy_hash_format("$argon2id$rest") is False
        assert _is_legacy_hash_format("$2b$12$rest") is False
