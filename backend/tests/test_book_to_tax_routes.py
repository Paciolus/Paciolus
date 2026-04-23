"""
Book-to-Tax route tier-gate tests — Sprint 689f.
"""

import sys

import httpx
import pytest

sys.path.insert(0, "..")

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import User, UserTier


def _valid_payload() -> dict:
    return {
        "tax_year": 2025,
        "book_pretax_income": "500000.00",
        "total_assets": "5000000.00",
        "federal_tax_rate": "0.21",
        "state_tax_rate": "0.05",
        "adjustments": [
            {"label": "Meals (50%)", "amount": "10000.00", "difference_type": "permanent", "direction": "add"},
        ],
        "rollforward": {"beginning_dta": "0", "beginning_dtl": "0"},
    }


@pytest.fixture
def free_user(db_session):
    user = User(
        email="free_btt@example.com",
        name="Free",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.FREE,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def professional_user(db_session):
    user = User(
        email="pro_btt@example.com",
        name="Pro",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _override(user, db_session):
    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session


@pytest.mark.usefixtures("bypass_csrf")
class TestBookToTaxTierGate:
    @pytest.mark.asyncio
    async def test_free_tier_blocked_on_analyze(self, free_user, db_session):
        _override(free_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/book-to-tax", json=_valid_payload())
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "TIER_LIMIT_EXCEEDED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_free_tier_blocked_on_csv_export(self, free_user, db_session):
        _override(free_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/book-to-tax/export.csv", json=_valid_payload())
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "TIER_LIMIT_EXCEEDED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_professional_tier_passes_analyze(self, professional_user, db_session):
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/book-to-tax", json=_valid_payload())
            assert response.status_code == 200
            body = response.json()
            assert body["tax_year"] == 2025
            assert "schedule_m1" in body
            assert "tax_provision" in body
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_professional_tier_passes_csv_export(self, professional_user, db_session):
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/book-to-tax/export.csv", json=_valid_payload())
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/csv")
        finally:
            app.dependency_overrides.clear()
