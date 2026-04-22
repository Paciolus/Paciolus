"""
Export-share passcode hardening — 2026-04-20, upgraded 2026-04-21.

Replaces the original SHA-256-only passcode handling in export_sharing with:

* **Argon2id** hashing for new passcodes (Sprint 697, OWASP 2024 recommendation).
  Memory-hard KDF resistant to GPU/ASIC brute-force in ways bcrypt isn't.
  Parameters: time_cost=3, memory_cost=65536 KiB (64 MiB), parallelism=4
  — AWS-SECS benchmarks around 250ms on Render Standard.
* **bcrypt** hashing retained as a legacy verify path. Sprint 696 shares
  hashed with bcrypt will still verify until their TTL expires (≤48h —
  one share-TTL cycle). After the transition window the bcrypt branch
  can be removed in a follow-up sprint.
* Legacy SHA-256 hashes continue to be rejected outright (Sprint 696).
* Per-passcode salt (both KDFs generate salts per-call internally).
* Constant-time verification via the KDF-specific verify routines.
* Strength policy: min length 10, at least 3 character classes (unchanged).
* Per-share brute-force throttle: exponential lockout that grows after
  every 5 consecutive failures and is token-scoped (unchanged).
* Sprint 698: per-IP failure tracking layered on top of per-token throttle
  (see ``routes/export_sharing._verify_passcode_or_raise``).

This module is imported exclusively by ``routes/export_sharing.py``; it
does not affect user-account password handling in ``auth.py``.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import bcrypt as _bcrypt

# Sprint 697: Argon2id is the preferred KDF. ``argon2-cffi`` is now in
# requirements.txt; the import is eager so a missing/broken install
# surfaces at app-startup rather than at first passcode hash.
from argon2 import PasswordHasher as _Argon2Hasher
from argon2.exceptions import InvalidHashError as _Argon2InvalidHashError
from argon2.exceptions import VerificationError as _Argon2VerificationError
from argon2.exceptions import VerifyMismatchError as _Argon2VerifyMismatchError

logger = logging.getLogger(__name__)


# Argon2id parameters — calibrated per OWASP 2024 password-storage cheat
# sheet for a time_cost ≈ 250ms on Render Standard (2 vCPU / 4GB RAM).
# Memory cost is the dominant parameter for GPU resistance; 64 MiB is
# the OWASP minimum. Parallelism = 4 × physical cores typical.
_ARGON2_TIME_COST = 3
_ARGON2_MEMORY_COST = 64 * 1024  # 64 MiB
_ARGON2_PARALLELISM = 4
_ARGON2_HASH_LEN = 32
_ARGON2_SALT_LEN = 16

_argon2_hasher = _Argon2Hasher(
    time_cost=_ARGON2_TIME_COST,
    memory_cost=_ARGON2_MEMORY_COST,
    parallelism=_ARGON2_PARALLELISM,
    hash_len=_ARGON2_HASH_LEN,
    salt_len=_ARGON2_SALT_LEN,
)


# Strength policy ------------------------------------------------------------
#
# The hardening brief requires "minimum length at least 10 (or stronger policy
# with mixed classes)" with "clear 400 validation errors on weak passcodes".
# Per-tool passcodes are low-entropy by nature (users pick them to share);
# we enforce length AND a light character-class rule so a literal "1111111111"
# is rejected without demanding randomness-style policies that would push
# users toward unsafe side-channels (e.g. e-mailing the passcode in plain
# text).
PASSCODE_MIN_LENGTH = 10
PASSCODE_MAX_LENGTH = 128
PASSCODE_MIN_CLASSES = 3  # of {lower, upper, digit, symbol}

_LOWER_RE = re.compile(r"[a-z]")
_UPPER_RE = re.compile(r"[A-Z]")
_DIGIT_RE = re.compile(r"[0-9]")
_SYMBOL_RE = re.compile(r"[^A-Za-z0-9]")


class WeakPasscodeError(ValueError):
    """Raised when a supplied passcode fails the strength policy.

    Route handlers catch this and surface as HTTP 400 with a user-visible
    message describing the policy — no information leakage because the
    policy is documented, not secret.
    """


def validate_passcode_strength(passcode: str) -> None:
    """Validate a passcode against the share-link strength policy.

    Raises ``WeakPasscodeError`` with a human-readable explanation when
    the passcode is too short / long or fails the character-class rule.
    """
    if not isinstance(passcode, str) or not passcode:
        raise WeakPasscodeError("Passcode is required.")
    if len(passcode) < PASSCODE_MIN_LENGTH:
        raise WeakPasscodeError(f"Passcode must be at least {PASSCODE_MIN_LENGTH} characters long.")
    if len(passcode) > PASSCODE_MAX_LENGTH:
        raise WeakPasscodeError(f"Passcode must not exceed {PASSCODE_MAX_LENGTH} characters.")
    classes = (
        bool(_LOWER_RE.search(passcode))
        + bool(_UPPER_RE.search(passcode))
        + bool(_DIGIT_RE.search(passcode))
        + bool(_SYMBOL_RE.search(passcode))
    )
    if classes < PASSCODE_MIN_CLASSES:
        raise WeakPasscodeError("Passcode must include at least 3 of: lowercase, uppercase, digit, symbol.")


# Hashing --------------------------------------------------------------------
#
# bcrypt cost 12 matches the main auth password hash (backend/auth.py
# BCRYPT_ROUNDS=12) — chosen for ~250ms of CPU time on typical Render
# Standard hardware, a reasonable per-request cost for a low-frequency
# gated endpoint.
_BCRYPT_ROUNDS = 12

# bcrypt silently truncates passwords at 72 bytes.  The strength check
# already caps at 128 chars (ASCII fits), and we reject anything longer
# to avoid footguns for non-ASCII users whose UTF-8 encoding pushes them
# over 72 bytes.
_BCRYPT_MAX_BYTES = 72


def hash_passcode(passcode: str) -> str:
    """Hash a passcode with **Argon2id** (per-passcode salt, memory-hard).

    Sprint 697: switched from bcrypt to Argon2id. Returns an argon2-
    formatted hash string (prefix ``$argon2id$``). Legacy bcrypt hashes
    are still accepted by ``verify_passcode`` during the transition
    window so existing shares don't need to be re-created.

    Precondition: the caller has already run ``validate_passcode_strength``.

    Note: argon2-cffi internally UTF-8 encodes the password; we don't
    have the bcrypt-style 72-byte cliff here, but we keep the
    ``PASSCODE_MAX_LENGTH`` strength-policy check in ``validate_passcode_
    strength`` as a defense-in-depth bound.
    """
    if not isinstance(passcode, str) or not passcode:
        raise WeakPasscodeError("Passcode is required.")
    return _argon2_hasher.hash(passcode)


def _is_argon2_hash(hash_str: str) -> bool:
    """Argon2id hashes start with ``$argon2id$`` (argon2-cffi always
    writes the explicit variant tag)."""
    return hash_str.startswith("$argon2id$") or hash_str.startswith("$argon2i$") or hash_str.startswith("$argon2d$")


def _is_bcrypt_hash(hash_str: str) -> bool:
    """bcrypt hashes always start with one of ``$2a$``, ``$2b$``, or ``$2y$``."""
    return hash_str.startswith(("$2a$", "$2b$", "$2y$"))


def _is_legacy_hash_format(hash_str: str) -> bool:
    """Sprint 697: rename-for-clarity wrapper. Returns True when the
    supplied hash is neither Argon2 nor bcrypt — i.e., the pre-Sprint-696
    SHA-256 hex format (or garbage) that must be rejected.
    """
    return not (_is_argon2_hash(hash_str) or _is_bcrypt_hash(hash_str))


# Backward-compat alias — a few older code paths may have imported the
# pre-rename symbol. Kept as an alias so we don't have to ripple the
# rename through unrelated modules right now.
_looks_like_bcrypt = _is_bcrypt_hash


def verify_passcode(passcode: str, stored_hash: str) -> bool:
    """Constant-time verify ``passcode`` against ``stored_hash``.

    Sprint 697: dual-format support. Preferred path is Argon2id; bcrypt
    is retained during the ≤48h transition window so existing shares
    hashed under Sprint 696's bcrypt branch don't break on verify.
    Legacy SHA-256 format is rejected outright (Sprint 696 invariant).

    After all bcrypt-hashed shares have aged out (≤48h post-Sprint 697
    deploy), a follow-up can delete the bcrypt branch. Until then, both
    formats round-trip cleanly.
    """
    if not stored_hash or not passcode:
        return False

    if _is_argon2_hash(stored_hash):
        # Preferred path — Argon2id.
        try:
            _argon2_hasher.verify(stored_hash, passcode)
            return True
        except _Argon2VerifyMismatchError:
            return False
        except (_Argon2VerificationError, _Argon2InvalidHashError, ValueError, TypeError):
            # Corrupted hash / wrong format → treat as verification failure.
            return False

    if _is_bcrypt_hash(stored_hash):
        # Legacy bcrypt path — retained for the transition window.
        try:
            return _bcrypt.checkpw(passcode.encode("utf-8"), stored_hash.encode("utf-8"))
        except (ValueError, TypeError):
            return False

    # Anything else is legacy SHA-256 or garbage — refuse to verify.
    logger.info("Rejecting legacy passcode hash format (rehash required)")
    return False


# Brute-force throttle -------------------------------------------------------
#
# Per-share (not per-IP) lockout: attackers cannot lock out a share's owner
# by attacking a different share, and legitimate owners who fat-finger the
# passcode on their own share aren't affected by attacks on others.  The
# back-off schedule:
#
#   attempts 1-4 → no penalty (user might fat-finger)
#   attempts 5-9 → +60 seconds lockout per failure (1m, 2m, 3m, 4m, 5m)
#   attempts 10+ → +300 seconds lockout per failure (capped at 1 hour)
#
# On successful verification the counter resets.  Shares auto-expire at
# 24-48h so unbounded lockouts are not a concern.
_THROTTLE_START = 5
_THROTTLE_STEP_SECONDS = 60
_LONG_THROTTLE_START = 10
_LONG_THROTTLE_STEP_SECONDS = 300
_MAX_LOCKOUT_SECONDS = 3600  # 1 hour cap


def current_lockout_remaining_seconds(locked_until: Optional[datetime], *, now: Optional[datetime] = None) -> int:
    """Return seconds remaining on an active lockout, or 0 if not locked."""
    if locked_until is None:
        return 0
    _now = now or datetime.now(UTC)
    # Handle naive datetimes from SQLite.
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=UTC)
    delta = (locked_until - _now).total_seconds()
    return int(max(0, delta))


def compute_next_lockout(failed_attempts: int) -> Optional[timedelta]:
    """Return the lockout ``timedelta`` after ``failed_attempts`` failures.

    Returns ``None`` for the first few attempts (no penalty).  Caller is
    responsible for persisting the resulting ``locked_until`` timestamp.
    """
    if failed_attempts < _THROTTLE_START:
        return None
    if failed_attempts < _LONG_THROTTLE_START:
        # 5 → 60s, 6 → 120s, …, 9 → 300s
        seconds = (failed_attempts - _THROTTLE_START + 1) * _THROTTLE_STEP_SECONDS
    else:
        # 10 → 600s, 11 → 900s, …, capped at 1 hour
        seconds = (failed_attempts - _LONG_THROTTLE_START + 2) * _LONG_THROTTLE_STEP_SECONDS
    seconds = min(seconds, _MAX_LOCKOUT_SECONDS)
    return timedelta(seconds=seconds)


class PasscodeThrottleState:
    """Mutable view over the ExportShare brute-force columns.

    Intentionally duck-typed against the SQLAlchemy row so we can reuse
    the same logic in route handlers and in unit tests without pulling
    the full ORM session into tests.
    """

    def __init__(self, row: Any):
        self.row = row

    @property
    def failed_attempts(self) -> int:
        return self.row.passcode_failed_attempts or 0

    @property
    def locked_until(self) -> Optional[datetime]:
        return self.row.passcode_locked_until

    def is_locked(self, *, now: Optional[datetime] = None) -> bool:
        return current_lockout_remaining_seconds(self.locked_until, now=now) > 0

    def register_failure(self, *, now: Optional[datetime] = None) -> Optional[timedelta]:
        """Increment the counter and return the applied lockout (if any)."""
        _now = now or datetime.now(UTC)
        new_attempts = self.failed_attempts + 1
        self.row.passcode_failed_attempts = new_attempts
        lockout = compute_next_lockout(new_attempts)
        if lockout is not None:
            self.row.passcode_locked_until = _now + lockout
        return lockout

    def reset(self) -> None:
        """Clear the counter after a successful verification."""
        if self.row.passcode_failed_attempts or self.row.passcode_locked_until:
            self.row.passcode_failed_attempts = 0
            self.row.passcode_locked_until = None
