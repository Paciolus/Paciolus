"""
Sprint 728a — Analytical-expectations CRUD route integration tests.

Mirrors the shape of test_follow_up_items_api.py — exercises the full
HTTP surface against the FastAPI app via httpx.AsyncClient.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engagement_manager import EngagementManager

pytestmark = pytest.mark.asyncio


def _make_engagement_for_user(db_session, user, make_client):
    client = make_client(user=user)
    eng = EngagementManager(db_session).create_engagement(
        user.id,
        client.id,
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 12, 31, tzinfo=UTC),
        materiality_amount=100000.0,
    )
    return eng


async def _client():
    from main import app

    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.mark.usefixtures("bypass_csrf")
class TestCreateExpectation:
    async def test_create_minimal_value(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement_for_user(db_session, user, make_client)

        async with await _client() as ac:
            r = await ac.post(
                f"/engagements/{eng.id}/analytical-expectations",
                json={
                    "procedure_target_type": "account",
                    "procedure_target_label": "Revenue",
                    "expected_value": 1000.0,
                    "precision_threshold_amount": 50.0,
                    "corroboration_basis_text": "Prior-period growth",
                    "corroboration_tags": ["prior_period"],
                },
            )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["procedure_target_type"] == "account"
        assert data["expected_value"] == 1000.0
        assert data["result_status"] == "not_evaluated"
        assert data["corroboration_tags"] == ["prior_period"]

    async def test_create_with_range_and_percent(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement_for_user(db_session, user, make_client)

        async with await _client() as ac:
            r = await ac.post(
                f"/engagements/{eng.id}/analytical-expectations",
                json={
                    "procedure_target_type": "ratio",
                    "procedure_target_label": "Current ratio",
                    "expected_range_low": 1.5,
                    "expected_range_high": 2.5,
                    "precision_threshold_percent": 10.0,
                    "corroboration_basis_text": "Industry median",
                    "corroboration_tags": ["industry_data"],
                },
            )
        assert r.status_code == 201
        data = r.json()
        assert data["expected_range_low"] == 1.5
        assert data["expected_range_high"] == 2.5
        assert data["precision_threshold_percent"] == 10.0

    async def test_create_rejects_xor_violation(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement_for_user(db_session, user, make_client)

        async with await _client() as ac:
            r = await ac.post(
                f"/engagements/{eng.id}/analytical-expectations",
                json={
                    "procedure_target_type": "account",
                    "procedure_target_label": "Revenue",
                    "expected_value": 1000.0,
                    "precision_threshold_amount": 50.0,
                    "precision_threshold_percent": 5.0,  # both — invalid
                    "corroboration_basis_text": "Prior",
                    "corroboration_tags": ["prior_period"],
                },
            )
        assert r.status_code == 400


@pytest.mark.usefixtures("bypass_csrf")
class TestListAndGet:
    async def test_list_returns_paginated(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement_for_user(db_session, user, make_client)

        async with await _client() as ac:
            for i in range(3):
                await ac.post(
                    f"/engagements/{eng.id}/analytical-expectations",
                    json={
                        "procedure_target_type": "account",
                        "procedure_target_label": f"Acc{i}",
                        "expected_value": 100.0 + i,
                        "precision_threshold_amount": 5.0,
                        "corroboration_basis_text": "Prior",
                        "corroboration_tags": ["prior_period"],
                    },
                )
            r = await ac.get(f"/engagements/{eng.id}/analytical-expectations")
        assert r.status_code == 200
        data = r.json()
        assert data["total_count"] == 3
        assert len(data["items"]) == 3

    async def test_list_filters_by_status(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement_for_user(db_session, user, make_client)

        async with await _client() as ac:
            r1 = await ac.post(
                f"/engagements/{eng.id}/analytical-expectations",
                json={
                    "procedure_target_type": "account",
                    "procedure_target_label": "A",
                    "expected_value": 100.0,
                    "precision_threshold_amount": 5.0,
                    "corroboration_basis_text": "P",
                    "corroboration_tags": ["prior_period"],
                },
            )
            await ac.post(
                f"/engagements/{eng.id}/analytical-expectations",
                json={
                    "procedure_target_type": "ratio",
                    "procedure_target_label": "B",
                    "expected_value": 1.5,
                    "precision_threshold_percent": 5.0,
                    "corroboration_basis_text": "I",
                    "corroboration_tags": ["industry_data"],
                },
            )
            # Capture actual on first → within
            await ac.patch(
                f"/analytical-expectations/{r1.json()['id']}",
                json={"result_actual_value": 102.0},
            )
            r = await ac.get(
                f"/engagements/{eng.id}/analytical-expectations",
                params={"result_status": "not_evaluated"},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["total_count"] == 1
        assert data["items"][0]["procedure_target_label"] == "B"


@pytest.mark.usefixtures("bypass_csrf")
class TestUpdateExpectation:
    async def test_capture_actual_recomputes_status(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement_for_user(db_session, user, make_client)

        async with await _client() as ac:
            r1 = await ac.post(
                f"/engagements/{eng.id}/analytical-expectations",
                json={
                    "procedure_target_type": "account",
                    "procedure_target_label": "Revenue",
                    "expected_value": 1000.0,
                    "precision_threshold_amount": 50.0,
                    "corroboration_basis_text": "Prior",
                    "corroboration_tags": ["prior_period"],
                },
            )
            exp_id = r1.json()["id"]

            r2 = await ac.patch(
                f"/analytical-expectations/{exp_id}",
                json={"result_actual_value": 1100.0},
            )
        assert r2.status_code == 200
        data = r2.json()
        assert data["result_status"] == "exceeds_threshold"
        assert data["result_actual_value"] == 1100.0
        assert data["result_variance_amount"] == 100.0

    async def test_clear_result_endpoint(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement_for_user(db_session, user, make_client)

        async with await _client() as ac:
            r1 = await ac.post(
                f"/engagements/{eng.id}/analytical-expectations",
                json={
                    "procedure_target_type": "account",
                    "procedure_target_label": "Revenue",
                    "expected_value": 1000.0,
                    "precision_threshold_amount": 50.0,
                    "corroboration_basis_text": "Prior",
                    "corroboration_tags": ["prior_period"],
                },
            )
            exp_id = r1.json()["id"]
            await ac.patch(
                f"/analytical-expectations/{exp_id}",
                json={"result_actual_value": 1100.0},
            )
            r3 = await ac.patch(
                f"/analytical-expectations/{exp_id}",
                json={"clear_result": True},
            )
        data = r3.json()
        assert data["result_status"] == "not_evaluated"
        assert data["result_actual_value"] is None


@pytest.mark.usefixtures("bypass_csrf")
class TestDeleteAndOwnership:
    async def test_archive_returns_204(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _make_engagement_for_user(db_session, user, make_client)

        async with await _client() as ac:
            r1 = await ac.post(
                f"/engagements/{eng.id}/analytical-expectations",
                json={
                    "procedure_target_type": "account",
                    "procedure_target_label": "Revenue",
                    "expected_value": 1000.0,
                    "precision_threshold_amount": 50.0,
                    "corroboration_basis_text": "Prior",
                    "corroboration_tags": ["prior_period"],
                },
            )
            exp_id = r1.json()["id"]
            r2 = await ac.delete(f"/analytical-expectations/{exp_id}")
        assert r2.status_code == 204

    async def test_get_nonexistent_returns_404(self, db_session, override_auth_verified, make_client):
        async with await _client() as ac:
            r = await ac.get("/analytical-expectations/9999999")
        assert r.status_code == 404
