"""
Sprint 729a — SUM-schedule export-route test.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engagement_manager import EngagementManager
from uncorrected_misstatements_manager import UncorrectedMisstatementsManager
from uncorrected_misstatements_model import (
    MisstatementClassification,
    MisstatementSourceType,
)

pytestmark = pytest.mark.asyncio


async def _client():
    from main import app

    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def _setup(db_session, user, make_client):
    client = make_client(user=user)
    return EngagementManager(db_session).create_engagement(
        user.id,
        client.id,
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 12, 31, tzinfo=UTC),
        materiality_amount=100000.0,
    )


@pytest.mark.usefixtures("bypass_csrf")
class TestExport:
    async def test_pdf_for_empty(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _setup(db_session, user, make_client)
        async with await _client() as ac:
            r = await ac.post(f"/engagements/{eng.id}/export/sum-schedule")
        assert r.status_code == 200
        assert r.content.startswith(b"%PDF")
        assert "sum_schedule.pdf" in r.headers.get("content-disposition", "")

    async def test_pdf_with_items(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _setup(db_session, user, make_client)
        UncorrectedMisstatementsManager(db_session).create_misstatement(
            user_id=user.id,
            engagement_id=eng.id,
            source_type=MisstatementSourceType.KNOWN_ERROR,
            source_reference="Cutoff",
            description="Dec/Jan cutoff",
            accounts_affected=[{"account": "Revenue", "debit_credit": "CR", "amount": 10000}],
            classification=MisstatementClassification.FACTUAL,
            fs_impact_net_income=Decimal("-10000.00"),
            fs_impact_net_assets=Decimal("-10000.00"),
        )
        async with await _client() as ac:
            r = await ac.post(f"/engagements/{eng.id}/export/sum-schedule")
        assert r.status_code == 200
        assert r.content.startswith(b"%PDF")
        assert len(r.content) > 1500

    async def test_404_for_unknown(self, db_session, override_auth_verified):
        async with await _client() as ac:
            r = await ac.post("/engagements/9999999/export/sum-schedule")
        assert r.status_code == 404
