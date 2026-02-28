"""
Tests for Audit Chain Verification Route — Sprint 461, CC7.4.

Integration tests for:
- GET /audit/chain-verify — full chain, partial range, empty chain
- POST /activity/log — chain_hash field in response
- Chain integrity after normal insert flow
"""

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import ActivityLog, User, UserTier

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def chain_user(db_session):
    """Create a verified user for chain tests."""
    user = User(
        email="chain_route@example.com",
        name="Chain Route User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.TEAM,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_chain_auth(chain_user, db_session):
    """Override auth and DB dependencies for chain tests."""
    app.dependency_overrides[require_current_user] = lambda: chain_user
    app.dependency_overrides[require_verified_user] = lambda: chain_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


def _activity_payload(**overrides):
    """Generate a valid activity log payload."""
    base = {
        "filename": "test_file.csv",
        "record_count": 100,
        "total_debits": 50000.0,
        "total_credits": 50000.0,
        "materiality_threshold": 500.0,
        "was_balanced": True,
        "anomaly_count": 2,
        "material_count": 1,
        "immaterial_count": 1,
    }
    base.update(overrides)
    return base


# =============================================================================
# POST /activity/log — chain_hash in response
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestActivityLogChainResponse:
    """Verify POST /activity/log returns chain_hash."""

    @pytest.mark.asyncio
    async def test_log_response_includes_chain_hash(self, override_chain_auth):
        """POST /activity/log response includes a non-null chain_hash."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/activity/log", json=_activity_payload())
            assert resp.status_code == 201
            data = resp.json()
            assert "chain_hash" in data
            assert data["chain_hash"] is not None
            assert len(data["chain_hash"]) == 64

    @pytest.mark.asyncio
    async def test_sequential_logs_have_different_chain_hashes(self, override_chain_auth):
        """Two sequential activity logs have different chain hashes."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp1 = await client.post("/activity/log", json=_activity_payload(record_count=10))
            resp2 = await client.post("/activity/log", json=_activity_payload(record_count=20))
            assert resp1.status_code == 201
            assert resp2.status_code == 201
            hash1 = resp1.json()["chain_hash"]
            hash2 = resp2.json()["chain_hash"]
            assert hash1 != hash2


# =============================================================================
# GET /audit/chain-verify
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestChainVerifyEndpoint:
    """Integration tests for GET /audit/chain-verify."""

    @pytest.mark.asyncio
    async def test_empty_chain_intact(self, override_chain_auth):
        """Empty chain verifies as intact."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/audit/chain-verify")
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_intact"] is True
            assert data["total_records"] == 0
            assert data["verified_records"] == 0
            assert data["first_broken_id"] is None
            assert data["links"] == []

    @pytest.mark.asyncio
    async def test_single_record_chain_intact(self, override_chain_auth):
        """A single properly chained record verifies as intact."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/activity/log", json=_activity_payload())
            resp = await client.get("/audit/chain-verify")
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_intact"] is True
            assert data["total_records"] == 1
            assert data["verified_records"] == 1

    @pytest.mark.asyncio
    async def test_multi_record_chain_intact(self, override_chain_auth):
        """Multiple properly chained records verify as intact."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for i in range(3):
                await client.post(
                    "/activity/log",
                    json=_activity_payload(record_count=10 + i),
                )
            resp = await client.get("/audit/chain-verify")
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_intact"] is True
            assert data["total_records"] == 3
            assert data["verified_records"] == 3

    @pytest.mark.asyncio
    async def test_tampered_record_detected_via_endpoint(self, override_chain_auth, db_session):
        """Endpoint detects tampered record content."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp1 = await client.post("/activity/log", json=_activity_payload())
            log_id = resp1.json()["id"]
            await client.post(
                "/activity/log",
                json=_activity_payload(record_count=20),
            )

            # Tamper with the first record's content
            db_session.execute(ActivityLog.__table__.update().where(ActivityLog.id == log_id).values(record_count=999))
            db_session.flush()

            resp = await client.get("/audit/chain-verify")
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_intact"] is False
            assert data["first_broken_id"] == log_id

    @pytest.mark.asyncio
    async def test_partial_range_start_id(self, override_chain_auth):
        """Partial verification with start_id works."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp1 = await client.post("/activity/log", json=_activity_payload(record_count=10))
            resp2 = await client.post("/activity/log", json=_activity_payload(record_count=20))
            await client.post("/activity/log", json=_activity_payload(record_count=30))

            second_id = resp2.json()["id"]
            resp = await client.get(f"/audit/chain-verify?start_id={second_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_records"] == 2
            assert data["is_intact"] is True

    @pytest.mark.asyncio
    async def test_partial_range_end_id(self, override_chain_auth):
        """Partial verification with end_id works."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp1 = await client.post("/activity/log", json=_activity_payload(record_count=10))
            await client.post("/activity/log", json=_activity_payload(record_count=20))

            first_id = resp1.json()["id"]
            resp = await client.get(f"/audit/chain-verify?end_id={first_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_records"] == 1
            assert data["is_intact"] is True

    @pytest.mark.asyncio
    async def test_links_detail_in_response(self, override_chain_auth):
        """Response includes per-record link details."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp1 = await client.post("/activity/log", json=_activity_payload())
            await client.get("/audit/chain-verify")
            resp = await client.get("/audit/chain-verify")
            data = resp.json()
            assert len(data["links"]) == 1
            link = data["links"][0]
            assert link["record_id"] == resp1.json()["id"]
            assert link["chain_valid"] is True
            assert link["content_hash_matches"] is True
            assert len(link["expected_chain_hash"]) == 64
            assert len(link["actual_chain_hash"]) == 64
