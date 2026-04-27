"""
Sprint 729a — Uncorrected-misstatements CRUD + SUM-schedule route tests.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engagement_manager import EngagementManager

pytestmark = pytest.mark.asyncio


def _make_engagement(db_session, user, make_client, materiality=100000.0):
    client = make_client(user=user)
    return EngagementManager(db_session).create_engagement(
        user.id,
        client.id,
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 12, 31, tzinfo=UTC),
        materiality_amount=materiality,
    )


async def _client():
    from main import app

    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


_PAYLOAD = {
    "source_type": "known_error",
    "source_reference": "Revenue cutoff",
    "description": "Dec 31 revenue posted to January",
    "accounts_affected": [{"account": "Revenue", "debit_credit": "CR", "amount": 10000}],
    "classification": "factual",
    "fs_impact_net_income": -10000.0,
    "fs_impact_net_assets": -10000.0,
}


@pytest.mark.usefixtures("bypass_csrf")
class TestCreate:
    async def test_create_minimal(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement(db_session, user, make_client)
        async with await _client() as ac:
            r = await ac.post(f"/engagements/{eng.id}/uncorrected-misstatements", json=_PAYLOAD)
        assert r.status_code == 201, r.text
        d = r.json()
        assert d["classification"] == "factual"
        assert d["fs_impact_net_income"] == -10000.0
        assert d["cpa_disposition"] == "not_yet_reviewed"


@pytest.mark.usefixtures("bypass_csrf")
class TestSumSchedule:
    async def test_empty_schedule(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement(db_session, user, make_client)
        async with await _client() as ac:
            r = await ac.get(f"/engagements/{eng.id}/sum-schedule")
        assert r.status_code == 200
        d = r.json()
        assert d["aggregate"]["net_income"] == 0.0
        assert d["bucket"] == "clearly_trivial"
        assert d["unreviewed_count"] == 0

    async def test_schedule_with_items(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement(db_session, user, make_client)
        async with await _client() as ac:
            await ac.post(f"/engagements/{eng.id}/uncorrected-misstatements", json=_PAYLOAD)
            await ac.post(
                f"/engagements/{eng.id}/uncorrected-misstatements",
                json={
                    **_PAYLOAD,
                    "classification": "projected",
                    "source_type": "sample_projection",
                    "source_reference": "Inventory sample",
                    "fs_impact_net_income": -5000.0,
                    "fs_impact_net_assets": 5000.0,
                },
            )
            r = await ac.get(f"/engagements/{eng.id}/sum-schedule")
        d = r.json()
        assert len(d["items"]) == 2
        assert d["subtotals"]["projected_net_income"] == -5000.0
        assert d["aggregate"]["net_income"] == -15000.0
        assert d["unreviewed_count"] == 2


@pytest.mark.usefixtures("bypass_csrf")
class TestUpdateAndDelete:
    async def test_patch_disposition(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement(db_session, user, make_client)
        async with await _client() as ac:
            r1 = await ac.post(f"/engagements/{eng.id}/uncorrected-misstatements", json=_PAYLOAD)
            mid = r1.json()["id"]
            r2 = await ac.patch(
                f"/uncorrected-misstatements/{mid}",
                json={
                    "cpa_disposition": "auditor_accepts_as_immaterial",
                    "cpa_notes": "Below performance materiality.",
                },
            )
        assert r2.status_code == 200
        assert r2.json()["cpa_disposition"] == "auditor_accepts_as_immaterial"

    async def test_delete_returns_204(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement(db_session, user, make_client)
        async with await _client() as ac:
            r1 = await ac.post(f"/engagements/{eng.id}/uncorrected-misstatements", json=_PAYLOAD)
            mid = r1.json()["id"]
            r2 = await ac.delete(f"/uncorrected-misstatements/{mid}")
        assert r2.status_code == 204

    async def test_get_404(self, db_session, override_auth_verified):
        async with await _client() as ac:
            r = await ac.get("/uncorrected-misstatements/9999999")
        assert r.status_code == 404
