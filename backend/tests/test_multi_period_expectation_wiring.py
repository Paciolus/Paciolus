"""
Sprint 728c — Multi-period TB route auto-evaluates ISA 520 expectations
when engagement_id is supplied.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from analytical_expectations_manager import AnalyticalExpectationsManager
from analytical_expectations_model import ExpectationResultStatus, ExpectationTargetType
from engagement_manager import EngagementManager

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


_PRIOR = [
    {"account": "Revenue", "debit": 0, "credit": 1000, "type": "revenue"},
    {"account": "Cash", "debit": 5000, "credit": 0, "type": "asset"},
]
_CURRENT = [
    {"account": "Revenue", "debit": 0, "credit": 1020, "type": "revenue"},
    {"account": "Cash", "debit": 5500, "credit": 0, "type": "asset"},
]


@pytest.mark.usefixtures("bypass_csrf")
class TestMultiPeriodWiring:
    async def test_evaluates_when_engagement_id_present(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        eng = _setup(db_session, user, make_client)

        ae_mgr = AnalyticalExpectationsManager(db_session)
        # ACCOUNT-typed expectation on Revenue with threshold $50
        exp = ae_mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior-period",
            corroboration_tags=["prior_period"],
        )

        async with await _client() as ac:
            r = await ac.post(
                "/audit/compare-periods",
                json={
                    "prior_accounts": _PRIOR,
                    "current_accounts": _CURRENT,
                    "engagement_id": eng.id,
                    "materiality_threshold": 0,
                },
            )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "expectations_evaluated" in body
        # Multi-period emits signed balances (revenue is credit-normal so current
        # comes through as negative). Either WITHIN or EXCEEDS is acceptable proof
        # of wiring; assert the expectation was evaluated, not the specific status.
        evaluated = body["expectations_evaluated"]
        assert any(
            e["expectation_id"] == exp.id and e["status"] in ("within_threshold", "exceeds_threshold")
            for e in evaluated
        ), evaluated

        db_session.refresh(exp)
        assert exp.result_status != ExpectationResultStatus.NOT_EVALUATED

    async def test_no_engagement_id_skips_evaluation(self, db_session, override_auth_verified, make_client):
        user = override_auth_verified
        # No engagement created; just call the route
        async with await _client() as ac:
            r = await ac.post(
                "/audit/compare-periods",
                json={
                    "prior_accounts": _PRIOR,
                    "current_accounts": _CURRENT,
                    "materiality_threshold": 0,
                },
            )
        assert r.status_code == 200
        body = r.json()
        assert body.get("expectations_evaluated", []) == []
