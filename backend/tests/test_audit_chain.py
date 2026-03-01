"""
Tests for Cryptographic Audit Log Chaining — Sprint 461

Tests cover:
- HMAC-SHA512 chain hash computation (deterministic, unique)
- Record serialization (deterministic, field order)
- Chain construction (single + multi-record)
- Tamper detection (modified field, modified hash)
- Chain verification function (empty range, valid chain, broken chain)
- GET /audit/chain-verify endpoint (success, broken, auth required, validation)
- Chain hash integration (set on activity creation, links to previous)
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest

sys.path.insert(0, "..")

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import ActivityLog, User, UserTier
from shared.audit_chain import (
    GENESIS_HASH,
    _serialize_record,
    compute_chain_hash,
    verify_audit_chain,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user(db_session):
    """Create a real user in the test DB."""
    user = User(
        email="chain_test@example.com",
        name="Chain Test User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.TEAM,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_auth(mock_user, db_session):
    """Override auth and DB dependencies for route testing."""
    app.dependency_overrides[require_current_user] = lambda: mock_user
    app.dependency_overrides[require_verified_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def override_auth_unverified(db_session):
    """Override auth but with an unverified user."""
    app.dependency_overrides[get_db] = lambda: db_session
    # Don't override require_verified_user — it should reject
    yield
    app.dependency_overrides.clear()


def _make_activity_log(db_session, user, **overrides):
    """Helper to create an ActivityLog record with defaults."""
    defaults = {
        "user_id": user.id,
        "filename_hash": "a" * 64,
        "filename_display": "test.csv",
        "record_count": 100,
        "total_debits": Decimal("500000.00"),
        "total_credits": Decimal("500000.00"),
        "materiality_threshold": Decimal("1000.00"),
        "was_balanced": True,
        "anomaly_count": 3,
        "material_count": 1,
        "immaterial_count": 2,
        "is_consolidated": False,
        "sheet_count": None,
        "timestamp": datetime.now(UTC),
    }
    defaults.update(overrides)
    record = ActivityLog(**defaults)
    db_session.add(record)
    db_session.flush()
    return record


# =============================================================================
# Unit Tests: Hash Computation
# =============================================================================


class TestComputeChainHash:
    """Tests for compute_chain_hash function."""

    def test_deterministic(self, db_session, mock_user):
        """Same inputs produce identical hash."""
        record = _make_activity_log(db_session, mock_user)
        hash1 = compute_chain_hash(GENESIS_HASH, record)
        hash2 = compute_chain_hash(GENESIS_HASH, record)
        assert hash1 == hash2

    def test_different_records_different_hashes(self, db_session, mock_user):
        """Different records produce different hashes."""
        r1 = _make_activity_log(db_session, mock_user, record_count=100)
        r2 = _make_activity_log(db_session, mock_user, record_count=200)
        h1 = compute_chain_hash(GENESIS_HASH, r1)
        h2 = compute_chain_hash(GENESIS_HASH, r2)
        assert h1 != h2

    def test_different_previous_hash_different_result(self, db_session, mock_user):
        """Different previous hashes produce different chain hashes."""
        record = _make_activity_log(db_session, mock_user)
        h1 = compute_chain_hash(GENESIS_HASH, record)
        h2 = compute_chain_hash("f" * 128, record)
        assert h1 != h2

    def test_hash_length_128_hex(self, db_session, mock_user):
        """HMAC-SHA512 produces 128-character hex string."""
        record = _make_activity_log(db_session, mock_user)
        h = compute_chain_hash(GENESIS_HASH, record)
        assert len(h) == 128
        assert all(c in "0123456789abcdef" for c in h)

    def test_genesis_hash_is_128_zeros(self):
        """Genesis hash constant is 128 hex zeros."""
        assert GENESIS_HASH == "0" * 128
        assert len(GENESIS_HASH) == 128


class TestSerializeRecord:
    """Tests for _serialize_record function."""

    def test_deterministic(self, db_session, mock_user):
        """Same record produces identical serialization."""
        record = _make_activity_log(db_session, mock_user)
        s1 = _serialize_record(record)
        s2 = _serialize_record(record)
        assert s1 == s2

    def test_pipe_delimited(self, db_session, mock_user):
        """Serialization uses pipe delimiters."""
        record = _make_activity_log(db_session, mock_user)
        s = _serialize_record(record)
        assert "|" in s
        # 14 fields = 13 pipes
        assert s.count("|") == 13

    def test_includes_all_fields(self, db_session, mock_user):
        """Serialization includes all expected field values."""
        record = _make_activity_log(
            db_session,
            mock_user,
            record_count=42,
            anomaly_count=7,
        )
        s = _serialize_record(record)
        assert "42" in s
        assert "7" in s


# =============================================================================
# Unit Tests: Chain Construction
# =============================================================================


class TestChainConstruction:
    """Tests for building a chain of hashed records."""

    def test_single_record_chain(self, db_session, mock_user):
        """Single record chains from genesis hash."""
        record = _make_activity_log(db_session, mock_user)
        record.chain_hash = compute_chain_hash(GENESIS_HASH, record)
        db_session.flush()

        expected = compute_chain_hash(GENESIS_HASH, record)
        assert record.chain_hash == expected

    def test_multi_record_chain(self, db_session, mock_user):
        """Multiple records form a linked chain."""
        r1 = _make_activity_log(db_session, mock_user, record_count=10)
        r1.chain_hash = compute_chain_hash(GENESIS_HASH, r1)
        db_session.flush()

        r2 = _make_activity_log(db_session, mock_user, record_count=20)
        r2.chain_hash = compute_chain_hash(r1.chain_hash, r2)
        db_session.flush()

        r3 = _make_activity_log(db_session, mock_user, record_count=30)
        r3.chain_hash = compute_chain_hash(r2.chain_hash, r3)
        db_session.flush()

        # Verify chain links
        assert r1.chain_hash != r2.chain_hash != r3.chain_hash
        assert compute_chain_hash(GENESIS_HASH, r1) == r1.chain_hash
        assert compute_chain_hash(r1.chain_hash, r2) == r2.chain_hash
        assert compute_chain_hash(r2.chain_hash, r3) == r3.chain_hash


# =============================================================================
# Unit Tests: Tamper Detection
# =============================================================================


class TestTamperDetection:
    """Tests for detecting tampering in the hash chain."""

    def test_modified_field_detected(self, db_session, mock_user):
        """Modifying a record field breaks the chain hash."""
        record = _make_activity_log(db_session, mock_user, record_count=100)
        record.chain_hash = compute_chain_hash(GENESIS_HASH, record)
        db_session.flush()

        original_hash = record.chain_hash

        # Simulate tampering: modify a field
        record.record_count = 999
        db_session.flush()

        # Recompute hash with tampered data — it won't match stored hash
        recomputed = compute_chain_hash(GENESIS_HASH, record)
        assert recomputed != original_hash

    def test_modified_hash_detected_in_chain(self, db_session, mock_user):
        """Modifying a chain hash is detected during verification."""
        r1 = _make_activity_log(db_session, mock_user, record_count=10)
        r1.chain_hash = compute_chain_hash(GENESIS_HASH, r1)
        db_session.flush()

        r2 = _make_activity_log(db_session, mock_user, record_count=20)
        r2.chain_hash = compute_chain_hash(r1.chain_hash, r2)
        db_session.flush()

        # Tamper with r1's hash
        r1.chain_hash = "tampered" + "0" * 120
        db_session.flush()

        # Verification should fail at r1
        result = verify_audit_chain(db_session, r1.id, r2.id)
        assert result.is_valid is False
        assert result.first_broken_id == r1.id


# =============================================================================
# Unit Tests: verify_audit_chain
# =============================================================================


class TestVerifyAuditChain:
    """Tests for the verify_audit_chain function."""

    def test_empty_range(self, db_session):
        """Empty range returns valid with 0 records checked."""
        result = verify_audit_chain(db_session, 999999, 999999)
        assert result.is_valid is True
        assert result.records_checked == 0

    def test_valid_chain(self, db_session, mock_user):
        """Valid chain returns is_valid=True."""
        r1 = _make_activity_log(db_session, mock_user, record_count=10)
        r1.chain_hash = compute_chain_hash(GENESIS_HASH, r1)
        db_session.flush()

        r2 = _make_activity_log(db_session, mock_user, record_count=20)
        r2.chain_hash = compute_chain_hash(r1.chain_hash, r2)
        db_session.flush()

        result = verify_audit_chain(db_session, r1.id, r2.id)
        assert result.is_valid is True
        assert result.records_checked == 2
        assert result.first_broken_id is None

    def test_broken_chain(self, db_session, mock_user):
        """Broken chain returns is_valid=False with broken ID."""
        r1 = _make_activity_log(db_session, mock_user, record_count=10)
        r1.chain_hash = compute_chain_hash(GENESIS_HASH, r1)
        db_session.flush()

        r2 = _make_activity_log(db_session, mock_user, record_count=20)
        r2.chain_hash = "bad_hash_" + "0" * 119
        db_session.flush()

        result = verify_audit_chain(db_session, r1.id, r2.id)
        assert result.is_valid is False
        assert result.first_broken_id == r2.id
        assert "hash mismatch" in result.error_message


# =============================================================================
# Integration Tests: API Endpoints
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestChainVerifyEndpoint:
    """Tests for GET /audit/chain-verify."""

    @pytest.mark.asyncio
    async def test_verify_valid_chain(self, override_auth, db_session, mock_user):
        """Verification endpoint returns valid for correctly chained records."""
        r1 = _make_activity_log(db_session, mock_user)
        r1.chain_hash = compute_chain_hash(GENESIS_HASH, r1)
        db_session.flush()

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/audit/chain-verify",
                params={"start_id": r1.id, "end_id": r1.id},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["records_checked"] == 1

    @pytest.mark.asyncio
    async def test_verify_broken_chain(self, override_auth, db_session, mock_user):
        """Verification endpoint detects a broken chain."""
        r1 = _make_activity_log(db_session, mock_user)
        r1.chain_hash = "wrong_hash_" + "0" * 117
        db_session.flush()

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/audit/chain-verify",
                params={"start_id": r1.id, "end_id": r1.id},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["first_broken_id"] == r1.id

    @pytest.mark.asyncio
    async def test_verify_requires_auth(self, db_session):
        """Verification endpoint requires authentication."""
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/audit/chain-verify",
                    params={"start_id": 1, "end_id": 10},
                )
            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_verify_rejects_invalid_range(self, override_auth):
        """end_id < start_id returns 422."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/audit/chain-verify",
                params={"start_id": 10, "end_id": 5},
            )
        assert response.status_code == 422


@pytest.mark.usefixtures("bypass_csrf")
class TestChainHashOnCreation:
    """Tests that chain_hash is set when creating activity logs via API."""

    @pytest.mark.asyncio
    async def test_chain_hash_set_on_creation(self, override_auth, db_session, mock_user):
        """POST /activity/log sets chain_hash on the created record."""
        payload = {
            "filename": "chain_test.csv",
            "record_count": 50,
            "total_debits": 10000.0,
            "total_credits": 10000.0,
            "materiality_threshold": 500.0,
            "was_balanced": True,
            "anomaly_count": 1,
            "material_count": 0,
            "immaterial_count": 1,
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/activity/log", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["chain_hash"] is not None
        assert len(data["chain_hash"]) == 128

    @pytest.mark.asyncio
    async def test_chain_hash_links_to_previous(self, override_auth, db_session, mock_user):
        """Second record's chain_hash depends on first record's chain_hash."""
        payload = {
            "filename": "first.csv",
            "record_count": 10,
            "total_debits": 1000.0,
            "total_credits": 1000.0,
            "materiality_threshold": 100.0,
            "was_balanced": True,
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            r1 = await client.post("/activity/log", json=payload)
            assert r1.status_code == 201
            hash1 = r1.json()["chain_hash"]

            payload["filename"] = "second.csv"
            r2 = await client.post("/activity/log", json=payload)
            assert r2.status_code == 201
            hash2 = r2.json()["chain_hash"]

        # Hashes should be different (different record content + chain link)
        assert hash1 != hash2
        # Both should be valid 128-char hex strings
        assert len(hash1) == 128
        assert len(hash2) == 128
