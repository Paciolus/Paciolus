"""
Tests for GET /activity/recent endpoint (NEW-005).

Covers:
- Unauthenticated → 401
- Authenticated, no activity → empty array
- Authenticated with activity → reverse chronological, respects limit
- User isolation (user A cannot see user B's activity)
"""

import sys

import httpx
import pytest

sys.path.insert(0, "..")

from auth import require_current_user
from database import get_db
from main import app
from models import ActivityLog, User, UserTier


@pytest.fixture
def user_a(db_session):
    user = User(
        email="recent_a@example.com",
        name="User A",
        hashed_password="$2b$12$fakehash",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def user_b(db_session):
    user = User(
        email="recent_b@example.com",
        name="User B",
        hashed_password="$2b$12$fakehash",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_activity(db_session, user, filename_display, *, anomaly_count=0):
    """Helper to create an activity log entry."""
    from shared.filenames import hash_filename

    activity = ActivityLog(
        user_id=user.id,
        filename_hash=hash_filename(filename_display),
        filename_display=filename_display,
        record_count=10,
        total_debits=1000.0,
        total_credits=1000.0,
        materiality_threshold=100.0,
        was_balanced=True,
        anomaly_count=anomaly_count,
        material_count=0,
        immaterial_count=0,
    )
    db_session.add(activity)
    db_session.flush()
    return activity


@pytest.fixture
def override_auth_a(user_a, db_session):
    app.dependency_overrides[require_current_user] = lambda: user_a
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def override_auth_b(user_b, db_session):
    app.dependency_overrides[require_current_user] = lambda: user_b
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


class TestGetRecentActivity:
    """Tests for GET /activity/recent."""

    @pytest.mark.asyncio
    async def test_401_without_auth(self):
        """Unauthenticated request should return 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/activity/recent")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_when_no_activity(self, override_auth_a):
        """Returns empty array when user has no activity."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/activity/recent")
            assert response.status_code == 200
            assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_recent_entries(self, override_auth_a, user_a, db_session):
        """Returns entries in reverse chronological order."""
        _create_activity(db_session, user_a, "first.csv", anomaly_count=1)
        _create_activity(db_session, user_a, "second.csv", anomaly_count=2)
        _create_activity(db_session, user_a, "third.csv", anomaly_count=3)
        db_session.commit()

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/activity/recent?limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            # Most recent first
            assert data[0]["filename"] == "third.csv"
            assert data[1]["filename"] == "second.csv"
            # Verify shape
            assert "id" in data[0]
            assert "created_at" in data[0]
            assert "was_balanced" in data[0]
            assert "record_count" in data[0]
            assert "anomaly_count" in data[0]

    @pytest.mark.asyncio
    async def test_respects_limit(self, override_auth_a, user_a, db_session):
        """Limit parameter controls result count."""
        for i in range(10):
            _create_activity(db_session, user_a, f"file_{i}.csv")
        db_session.commit()

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/activity/recent?limit=3")
            assert response.status_code == 200
            assert len(response.json()) == 3

    @pytest.mark.asyncio
    async def test_user_isolation(self, user_a, user_b, db_session):
        """User A cannot see User B's activity."""
        _create_activity(db_session, user_a, "a_file.csv")
        _create_activity(db_session, user_b, "b_file.csv")
        db_session.commit()

        # Authenticate as user A
        app.dependency_overrides[require_current_user] = lambda: user_a
        app.dependency_overrides[get_db] = lambda: db_session

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/activity/recent?limit=50")
            assert response.status_code == 200
            data = response.json()
            filenames = [d["filename"] for d in data]
            assert "a_file.csv" in filenames
            assert "b_file.csv" not in filenames

        app.dependency_overrides.clear()
