"""Sprint 876: industry-ratio evaluation only runs against an engagement of the same client.

GET /clients/{A}/industry-ratios?engagement_id={E} checked client A's ownership,
then evaluated A's ratios against engagement E's ISA 520 expectations without
checking that E belongs to A. An engagement of client B (reachable through the
org-wide access fallback) had its expectations resolved with the wrong client's
numbers — enough to satisfy B's completion gate.
"""

from datetime import date
from unittest.mock import patch

import httpx
import pytest

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import DiagnosticSummary, PeriodType


@pytest.fixture
def setup(db_session, make_user, make_client, make_engagement):
    user = make_user(email="sprint876@example.com")
    client_a = make_client(user=user, name="Client A")
    client_b = make_client(user=user, name="Client B")
    eng_a = make_engagement(client=client_a)
    eng_b = make_engagement(client=client_b)
    db_session.add(
        DiagnosticSummary(
            client_id=client_a.id,
            user_id=user.id,
            period_date=date(2025, 6, 30),
            period_type=PeriodType.QUARTERLY,
            total_assets=1000000.0,
            current_assets=400000.0,
            total_liabilities=300000.0,
            current_liabilities=150000.0,
            total_equity=700000.0,
            total_revenue=500000.0,
            cost_of_goods_sold=200000.0,
            total_expenses=350000.0,
            current_ratio=2.67,
            total_debits=500000.0,
            total_credits=500000.0,
            was_balanced=True,
            anomaly_count=0,
            materiality_threshold=500.0,
            row_count=40,
        )
    )
    db_session.flush()
    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session
    yield client_a, eng_a, eng_b
    app.dependency_overrides.clear()


async def _get(path: str) -> httpx.Response:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path)


@pytest.mark.asyncio
async def test_another_clients_engagement_is_refused_and_not_evaluated(setup):
    client_a, _eng_a, eng_b = setup
    with patch("shared.expectation_evaluation.evaluate_expectations_against_measurements") as evaluate:
        response = await _get(f"/clients/{client_a.id}/industry-ratios?engagement_id={eng_b.id}")
    assert response.status_code == 404
    evaluate.assert_not_called()


@pytest.mark.asyncio
async def test_unknown_engagement_is_refused(setup):
    client_a, _eng_a, _eng_b = setup
    with patch("shared.expectation_evaluation.evaluate_expectations_against_measurements") as evaluate:
        response = await _get(f"/clients/{client_a.id}/industry-ratios?engagement_id=999999")
    assert response.status_code == 404
    evaluate.assert_not_called()


@pytest.mark.asyncio
async def test_own_engagement_is_evaluated(setup):
    client_a, eng_a, _eng_b = setup
    with patch("shared.expectation_evaluation.evaluate_expectations_against_measurements", return_value=[]) as evaluate:
        response = await _get(f"/clients/{client_a.id}/industry-ratios?engagement_id={eng_a.id}")
    assert response.status_code == 200, response.text
    evaluate.assert_called_once()
    assert evaluate.call_args.kwargs["engagement_id"] == eng_a.id


@pytest.mark.asyncio
async def test_without_engagement_nothing_changes(setup):
    client_a, _eng_a, _eng_b = setup
    with patch("shared.expectation_evaluation.evaluate_expectations_against_measurements") as evaluate:
        response = await _get(f"/clients/{client_a.id}/industry-ratios")
    assert response.status_code == 200
    evaluate.assert_not_called()
