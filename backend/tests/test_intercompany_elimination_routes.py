"""
Intercompany Elimination route tier-gate tests — Sprint 689c.

The engine has its own exhaustive tests in
`test_intercompany_elimination_engine.py`; this file covers the
route-layer gating added when the tool was promoted to a standalone
frontend page: Free tier returns 403 TIER_LIMIT_EXCEEDED, paid tiers
pass through to the engine.
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
    """Minimum-viable reciprocal intercompany payload the engine accepts."""
    return {
        "entities": [
            {
                "entity_id": "A",
                "entity_name": "Parent",
                "accounts": [
                    {
                        "account": "Due From B",
                        "debit": "1000.00",
                        "credit": "0",
                        "counterparty_entity": "B",
                    }
                ],
            },
            {
                "entity_id": "B",
                "entity_name": "Sub",
                "accounts": [
                    {
                        "account": "Due To A",
                        "debit": "0",
                        "credit": "1000.00",
                        "counterparty_entity": "A",
                    }
                ],
            },
        ],
        "tolerance": "1.00",
    }


@pytest.fixture
def free_user(db_session):
    user = User(
        email="free_ic@example.com",
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
        email="pro_ic@example.com",
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
class TestIntercompanyEliminationTierGate:
    @pytest.mark.asyncio
    async def test_free_tier_blocked_on_analyze(self, free_user, db_session):
        _override(free_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/intercompany-elimination",
                    json=_valid_payload(),
                )
            assert response.status_code == 403
            detail = response.json()["detail"]
            assert detail["code"] == "TIER_LIMIT_EXCEEDED"
            assert detail["resource"] == "tool_access"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_free_tier_blocked_on_csv_export(self, free_user, db_session):
        _override(free_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/intercompany-elimination/export.csv",
                    json=_valid_payload(),
                )
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "TIER_LIMIT_EXCEEDED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_professional_tier_passes_analyze(self, professional_user, db_session):
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/intercompany-elimination",
                    json=_valid_payload(),
                )
            assert response.status_code == 200
            body = response.json()
            # Engine happy-path — reciprocal pair reconciles.
            assert body["summary"]["matched_pair_count"] == 1
            assert body["summary"]["reconciling_pair_count"] == 1
            assert body["summary"]["mismatch_count"] == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_professional_tier_passes_csv_export(self, professional_user, db_session):
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/intercompany-elimination/export.csv",
                    json=_valid_payload(),
                )
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/csv")
            assert "intercompany_consolidation.csv" in response.headers.get("content-disposition", "")
        finally:
            app.dependency_overrides.clear()
