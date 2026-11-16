"""Sprint 873: the coverage-analysis flag must survive the API response model.

Concentration rows (`audit/rules/concentration.py`) carry `coverage_analysis:
True` so the app and the PDF can treat them as materiality-coverage context
rather than anomalies (Sprint 668). `AbnormalBalanceResponse` did not declare
the field and ignores extras, so every response stripped it.
"""

import io

import httpx
import pytest

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import User, UserTier

# One revenue account is 100% of revenue: the concentration rule reports it.
CSV = b"""Account Name,Debit,Credit
Cash,52173.45,
Accounts Receivable,18891.33,
Product Sales Revenue,,61234.56
Rent Expense,9234.55,
Retained Earnings,,19064.77
"""


@pytest.fixture
def user(db_session):
    u = User(
        email="sprint873_coverage@example.com",
        name="Coverage",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(u)
    db_session.flush()
    app.dependency_overrides[require_current_user] = lambda: u
    app.dependency_overrides[require_verified_user] = lambda: u
    app.dependency_overrides[get_db] = lambda: db_session
    yield u
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "user")
async def test_concentration_rows_keep_their_coverage_flag():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/audit/trial-balance",
            files={"file": ("tb.csv", io.BytesIO(CSV), "text/csv")},
            data={"materiality_threshold": "0"},
        )
    assert response.status_code == 200, response.text
    rows = response.json()["abnormal_balances"]
    coverage = [r for r in rows if "coverage observation, not an anomaly" in r["issue"]]
    assert coverage, "fixture must produce at least one concentration row"
    assert all(r.get("coverage_analysis") is True for r in coverage)
    assert all(not r.get("coverage_analysis") for r in rows if r not in coverage)
