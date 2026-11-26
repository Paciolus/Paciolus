"""Sprint 900: two upload responses that failed their own response model, so the route answered 500.

Found 2026-11-25 by the Sprint 889 end-to-end job, which runs the real backend:

1. ``/audit/trial-balance`` on any out-of-balance trial balance. Sprint 667 prepends a
   synthetic "Trial Balance — Overall" anomaly that lacked six fields
   ``AbnormalBalanceResponse`` requires (debit, credit, category, matched_keywords,
   requires_review, suggestions).
2. ``/audit/preflight`` on any file whose columns were inferred rather than matched by
   header. Sprint 668 added the "inferred" column status; the response schema did not.

Unit tests of the engines passed because they never went through the response model.
These go through the routes.
"""

import io

import httpx
import pytest

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import User, UserTier

# Debits 51,000, credits 50,000.
OUT_OF_BALANCE = b"""Account,Debit,Credit
Cash,50000,0
Revenue,0,50000
Expense,1000,0
"""

GENERIC_HEADERS = b"""Col A,Col B,Col C
Cash,50000,0
Revenue,0,50000
Expense,1000,0
"""


@pytest.fixture
def user(db_session):
    u = User(
        email="sprint900_responses@example.com",
        name="Sprint 900",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.SOLO,
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


async def _post(path: str, content: bytes, **data: str) -> httpx.Response:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, files={"file": ("tb.csv", io.BytesIO(content), "text/csv")}, data=data)


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "user")
async def test_out_of_balance_trial_balance_is_answered():
    response = await _post("/audit/trial-balance", OUT_OF_BALANCE, materiality_threshold="500")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["balanced"] is False
    first = body["abnormal_balances"][0]
    assert first["anomaly_type"] == "tb_out_of_balance"
    assert first["severity"] == "high"


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "user")
async def test_preflight_on_generic_headers_is_answered():
    response = await _post("/audit/preflight", GENERIC_HEADERS)
    assert response.status_code == 200, response.text
    assert any(c["status"] == "inferred" for c in response.json()["columns"])
