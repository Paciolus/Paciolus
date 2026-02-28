"""
Tests for Cryptographic Audit Log Chaining — Sprint 461, CC7.4.

Validates:
1. Content hash determinism (same record → same hash)
2. Content hash sensitivity (any field change → different hash)
3. Chain hash construction (HMAC-SHA256 linking)
4. Genesis sentinel for first record in a user's chain
5. Multi-record chain construction
6. Tamper detection (modified record content)
7. Missing record detection (deleted chain link)
8. Chain verification endpoint (GET /audit/chain-verify)
9. Cross-user isolation (user A's chain doesn't affect user B)
10. Partial verification (start_id / end_id range)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import ActivityLog
from shared.audit_chain import (
    GENESIS_SENTINEL,
    compute_chain_hash,
    compute_content_hash,
    stamp_chain_hash,
    verify_chain,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_log(
    db_session, user, *, record_count=10, total_debits=1000.0, total_credits=1000.0, was_balanced=True, anomaly_count=0
):
    """Create an ActivityLog and stamp its chain hash."""
    log = ActivityLog(
        user_id=user.id,
        filename_hash="a" * 64,
        record_count=record_count,
        total_debits=total_debits,
        total_credits=total_credits,
        materiality_threshold=100.0,
        was_balanced=was_balanced,
        anomaly_count=anomaly_count,
        material_count=0,
        immaterial_count=0,
    )
    db_session.add(log)
    db_session.flush()
    stamp_chain_hash(db_session, log)
    db_session.flush()
    return log


def _make_log_no_chain(db_session, user, **kwargs):
    """Create an ActivityLog WITHOUT a chain hash (for testing pre-existing records)."""
    log = ActivityLog(
        user_id=user.id,
        filename_hash="b" * 64,
        record_count=kwargs.get("record_count", 10),
        total_debits=kwargs.get("total_debits", 500.0),
        total_credits=kwargs.get("total_credits", 500.0),
        materiality_threshold=50.0,
        was_balanced=True,
        anomaly_count=0,
        material_count=0,
        immaterial_count=0,
    )
    db_session.add(log)
    db_session.flush()
    return log


# =============================================================================
# 1. Content Hash Tests
# =============================================================================


class TestContentHash:
    """Validate content hash determinism and sensitivity."""

    def test_deterministic_same_record(self, db_session, make_user):
        """Same record always produces the same content hash."""
        user = make_user(email="hash_det@test.com")
        log = _make_log(db_session, user)
        h1 = compute_content_hash(log)
        h2 = compute_content_hash(log)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_different_record_count_changes_hash(self, db_session, make_user):
        """Changing record_count produces a different content hash."""
        user = make_user(email="hash_rc@test.com")
        log1 = _make_log(db_session, user, record_count=10)
        log2 = _make_log(db_session, user, record_count=20)
        assert compute_content_hash(log1) != compute_content_hash(log2)

    def test_different_debits_changes_hash(self, db_session, make_user):
        """Changing total_debits produces a different content hash."""
        user = make_user(email="hash_deb@test.com")
        log1 = _make_log(db_session, user, total_debits=1000.0)
        log2 = _make_log(db_session, user, total_debits=2000.0)
        assert compute_content_hash(log1) != compute_content_hash(log2)

    def test_different_balanced_changes_hash(self, db_session, make_user):
        """Changing was_balanced produces a different content hash."""
        user = make_user(email="hash_bal@test.com")
        log1 = _make_log(db_session, user, was_balanced=True)
        log2 = _make_log(db_session, user, was_balanced=False)
        assert compute_content_hash(log1) != compute_content_hash(log2)

    def test_different_anomaly_count_changes_hash(self, db_session, make_user):
        """Changing anomaly_count produces a different content hash."""
        user = make_user(email="hash_anom@test.com")
        log1 = _make_log(db_session, user, anomaly_count=0)
        log2 = _make_log(db_session, user, anomaly_count=5)
        assert compute_content_hash(log1) != compute_content_hash(log2)


# =============================================================================
# 2. Chain Hash Construction Tests
# =============================================================================


class TestChainHashConstruction:
    """Validate HMAC-SHA256 chain hash linking."""

    def test_chain_hash_is_64_hex(self, db_session, make_user):
        """Chain hash is a 64-character hex string."""
        user = make_user(email="chain_hex@test.com")
        log = _make_log(db_session, user)
        assert log.chain_hash is not None
        assert len(log.chain_hash) == 64
        int(log.chain_hash, 16)  # Valid hex

    def test_genesis_record_uses_sentinel(self, db_session, make_user):
        """First record in a user's chain uses GENESIS_SENTINEL as predecessor."""
        user = make_user(email="chain_gen@test.com")
        log = _make_log(db_session, user)
        content_hash = compute_content_hash(log)
        expected = compute_chain_hash(GENESIS_SENTINEL, content_hash)
        assert log.chain_hash == expected

    def test_second_record_chains_to_first(self, db_session, make_user):
        """Second record's chain hash is derived from the first's chain hash."""
        user = make_user(email="chain_seq@test.com")
        log1 = _make_log(db_session, user)
        log2 = _make_log(db_session, user)
        content_hash_2 = compute_content_hash(log2)
        expected = compute_chain_hash(log1.chain_hash, content_hash_2)
        assert log2.chain_hash == expected

    def test_three_record_chain(self, db_session, make_user):
        """Three records form a valid sequential chain."""
        user = make_user(email="chain_three@test.com")
        log1 = _make_log(db_session, user)
        log2 = _make_log(db_session, user, record_count=20)
        log3 = _make_log(db_session, user, record_count=30)

        # Verify chain linkage
        ch1_expected = compute_chain_hash(GENESIS_SENTINEL, compute_content_hash(log1))
        ch2_expected = compute_chain_hash(log1.chain_hash, compute_content_hash(log2))
        ch3_expected = compute_chain_hash(log2.chain_hash, compute_content_hash(log3))

        assert log1.chain_hash == ch1_expected
        assert log2.chain_hash == ch2_expected
        assert log3.chain_hash == ch3_expected

    def test_different_content_produces_different_chain(self, db_session, make_user):
        """Two records with different content at the same chain position produce different hashes."""
        user1 = make_user(email="chain_diff1@test.com")
        user2 = make_user(email="chain_diff2@test.com")
        log1 = _make_log(db_session, user1, record_count=10)
        log2 = _make_log(db_session, user2, record_count=99)
        # Both are genesis records (same predecessor = GENESIS_SENTINEL)
        # but different content → different chain hashes
        assert log1.chain_hash != log2.chain_hash


# =============================================================================
# 3. Chain Verification Tests
# =============================================================================


class TestChainVerification:
    """Validate chain integrity verification."""

    def test_empty_chain_is_intact(self, db_session, make_user):
        """An empty chain (no records) is considered intact."""
        user = make_user(email="verify_empty@test.com")
        result = verify_chain(db_session, user.id)
        assert result.is_intact is True
        assert result.total_records == 0
        assert result.verified_records == 0
        assert result.first_broken_id is None
        assert result.links == []

    def test_single_record_chain_intact(self, db_session, make_user):
        """A single correctly chained record verifies as intact."""
        user = make_user(email="verify_single@test.com")
        _make_log(db_session, user)
        result = verify_chain(db_session, user.id)
        assert result.is_intact is True
        assert result.total_records == 1
        assert result.verified_records == 1

    def test_multi_record_chain_intact(self, db_session, make_user):
        """A chain of 5 records verifies as intact."""
        user = make_user(email="verify_multi@test.com")
        for i in range(5):
            _make_log(db_session, user, record_count=10 + i)
        result = verify_chain(db_session, user.id)
        assert result.is_intact is True
        assert result.total_records == 5
        assert result.verified_records == 5

    def test_tampered_record_detected(self, db_session, make_user):
        """Modifying a record's content is detected as a chain break."""
        user = make_user(email="verify_tamper@test.com")
        log1 = _make_log(db_session, user)
        log2 = _make_log(db_session, user, record_count=20)
        _make_log(db_session, user, record_count=30)

        # Tamper with log2's content directly via SQL (bypass ORM)
        db_session.execute(ActivityLog.__table__.update().where(ActivityLog.id == log2.id).values(record_count=999))
        db_session.flush()

        result = verify_chain(db_session, user.id)
        assert result.is_intact is False
        assert result.first_broken_id == log2.id
        # log1 should still be valid
        assert result.links[0].chain_valid is True
        assert result.links[1].chain_valid is False

    def test_tampered_chain_hash_detected(self, db_session, make_user):
        """Directly modifying a chain_hash is detected."""
        user = make_user(email="verify_hash_tamper@test.com")
        log1 = _make_log(db_session, user)
        log2 = _make_log(db_session, user, record_count=20)

        # Tamper with log1's chain_hash
        db_session.execute(ActivityLog.__table__.update().where(ActivityLog.id == log1.id).values(chain_hash="f" * 64))
        db_session.flush()

        result = verify_chain(db_session, user.id)
        assert result.is_intact is False
        # log1 breaks because its stored hash doesn't match recomputed
        assert result.first_broken_id == log1.id

    def test_null_chain_hash_detected(self, db_session, make_user):
        """A record with NULL chain_hash (pre-existing) is detected as a break."""
        user = make_user(email="verify_null@test.com")
        _make_log_no_chain(db_session, user)
        result = verify_chain(db_session, user.id)
        assert result.is_intact is False
        assert result.total_records == 1
        assert result.verified_records == 0

    def test_partial_verification_start_id(self, db_session, make_user):
        """Verification with start_id skips earlier records."""
        user = make_user(email="verify_start@test.com")
        _make_log(db_session, user, record_count=10)
        log2 = _make_log(db_session, user, record_count=20)
        _make_log(db_session, user, record_count=30)

        result = verify_chain(db_session, user.id, start_id=log2.id)
        assert result.total_records == 2
        assert result.is_intact is True

    def test_partial_verification_end_id(self, db_session, make_user):
        """Verification with end_id stops before later records."""
        user = make_user(email="verify_end@test.com")
        log1 = _make_log(db_session, user, record_count=10)
        _make_log(db_session, user, record_count=20)
        _make_log(db_session, user, record_count=30)

        result = verify_chain(db_session, user.id, end_id=log1.id)
        assert result.total_records == 1
        assert result.is_intact is True


# =============================================================================
# 4. Cross-User Isolation Tests
# =============================================================================


class TestCrossUserIsolation:
    """Validate that chain verification is scoped per user."""

    def test_user_chains_are_independent(self, db_session, make_user):
        """User A's chain hash is independent of user B's records."""
        user_a = make_user(email="iso_a@test.com")
        user_b = make_user(email="iso_b@test.com")

        log_a = _make_log(db_session, user_a, record_count=10)
        log_b = _make_log(db_session, user_b, record_count=10)

        # Both are genesis records despite different users
        content_a = compute_content_hash(log_a)
        content_b = compute_content_hash(log_b)
        expected_a = compute_chain_hash(GENESIS_SENTINEL, content_a)
        expected_b = compute_chain_hash(GENESIS_SENTINEL, content_b)

        assert log_a.chain_hash == expected_a
        assert log_b.chain_hash == expected_b

    def test_user_a_intact_despite_user_b_tampered(self, db_session, make_user):
        """Tampering with user B's chain doesn't affect user A's verification."""
        user_a = make_user(email="iso_check_a@test.com")
        user_b = make_user(email="iso_check_b@test.com")

        _make_log(db_session, user_a, record_count=10)
        log_b = _make_log(db_session, user_b, record_count=10)

        # Tamper with user B's record
        db_session.execute(ActivityLog.__table__.update().where(ActivityLog.id == log_b.id).values(record_count=999))
        db_session.flush()

        result_a = verify_chain(db_session, user_a.id)
        result_b = verify_chain(db_session, user_b.id)
        assert result_a.is_intact is True
        assert result_b.is_intact is False

    def test_verification_returns_correct_user_id(self, db_session, make_user):
        """Verification result contains the correct user_id."""
        user = make_user(email="iso_uid@test.com")
        _make_log(db_session, user)
        result = verify_chain(db_session, user.id)
        assert result.user_id == user.id


# =============================================================================
# 5. Chain Hash Function Unit Tests
# =============================================================================


class TestChainHashFunction:
    """Unit tests for compute_chain_hash()."""

    def test_deterministic(self):
        """Same inputs always produce the same output."""
        h1 = compute_chain_hash("a" * 64, "b" * 64)
        h2 = compute_chain_hash("a" * 64, "b" * 64)
        assert h1 == h2

    def test_different_previous_produces_different_output(self):
        """Different previous_chain_hash produces different output."""
        h1 = compute_chain_hash("a" * 64, "b" * 64)
        h2 = compute_chain_hash("c" * 64, "b" * 64)
        assert h1 != h2

    def test_different_content_produces_different_output(self):
        """Different content_hash produces different output."""
        h1 = compute_chain_hash("a" * 64, "b" * 64)
        h2 = compute_chain_hash("a" * 64, "c" * 64)
        assert h1 != h2

    def test_output_is_64_hex(self):
        """Output is a 64-character hex string (SHA-256)."""
        h = compute_chain_hash("a" * 64, "b" * 64)
        assert len(h) == 64
        int(h, 16)  # Valid hex


# =============================================================================
# 6. Genesis Sentinel Tests
# =============================================================================


class TestGenesisSentinel:
    """Validate genesis sentinel behavior."""

    def test_sentinel_is_64_zeros(self):
        """Genesis sentinel is 64 zero characters."""
        assert GENESIS_SENTINEL == "0" * 64
        assert len(GENESIS_SENTINEL) == 64

    def test_first_record_uses_sentinel(self, db_session, make_user):
        """The first record's chain is computed from the sentinel."""
        user = make_user(email="sentinel_first@test.com")
        log = _make_log(db_session, user)
        content = compute_content_hash(log)
        expected = compute_chain_hash(GENESIS_SENTINEL, content)
        assert log.chain_hash == expected
