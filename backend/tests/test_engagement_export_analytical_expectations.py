"""
Sprint 728a — Export-route test for the ISA 520 analytical-expectations PDF.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from analytical_expectations_manager import AnalyticalExpectationsManager
from analytical_expectations_model import ExpectationTargetType
from engagement_manager import EngagementManager

pytestmark = pytest.mark.asyncio


async def _client():
    from main import app

    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def _setup_engagement(db_session, user, make_client):
    client = make_client(user=user)
    return EngagementManager(db_session).create_engagement(
        user.id,
        client.id,
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 12, 31, tzinfo=UTC),
        materiality_amount=100000.0,
    )


@pytest.mark.usefixtures("bypass_csrf")
class TestExportRoute:
    async def test_export_returns_pdf_for_empty_engagement(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _setup_engagement(db_session, user, make_client)

        async with await _client() as ac:
            r = await ac.post(f"/engagements/{eng.id}/export/analytical-expectations")
        assert r.status_code == 200, r.text
        assert r.headers["content-type"].startswith("application/pdf")
        assert r.content.startswith(b"%PDF")
        assert "analytical_expectations.pdf" in r.headers.get("content-disposition", "")

    async def test_export_returns_pdf_with_expectations(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _setup_engagement(db_session, user, make_client)

        AnalyticalExpectationsManager(db_session).create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior",
            corroboration_tags=["prior_period"],
        )

        async with await _client() as ac:
            r = await ac.post(f"/engagements/{eng.id}/export/analytical-expectations")
        assert r.status_code == 200
        assert r.content.startswith(b"%PDF")
        assert len(r.content) > 1500

    async def test_export_404_for_unknown_engagement(self, db_session, override_auth_verified):
        async with await _client() as ac:
            r = await ac.post("/engagements/9999999/export/analytical-expectations")
        assert r.status_code == 404
