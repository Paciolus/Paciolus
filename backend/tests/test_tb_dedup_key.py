"""Sprint 872: re-running a trial balance with different settings is not a duplicate.

The 5-minute duplicate-submission guard on POST /audit/trial-balance keyed on
user + engagement + file bytes only. The TB page re-posts the same file when
the auditor changes the materiality threshold, confirms a column mapping or
re-runs after account-type overrides (useTrialBalanceUpload.ts recalcs,
useTrialBalancePreflight.ts) — so each of those answered 409 with raw text
telling the user to "re-submit with force_resubmit=true". Only an identical
request is a duplicate.
"""

import io
import json

import httpx
import pytest

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import User, UserTier

CSV = b"""Account Name,Debit,Credit
Cash,3217.45,
Accounts Receivable,2891.33,
Revenue,,4321.11
Rent Expense,1234.55,
Retained Earnings,,3022.22
"""


@pytest.fixture
def user(db_session):
    u = User(
        email="sprint872_dedup@example.com",
        name="Dedup",
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


async def _post(client: httpx.AsyncClient, **data: str) -> httpx.Response:
    return await client.post(
        "/audit/trial-balance",
        files={"file": ("tb.csv", io.BytesIO(CSV), "text/csv")},
        data={"materiality_threshold": "0", **data},
    )


@pytest.mark.usefixtures("bypass_csrf", "user")
class TestTrialBalanceDedupKey:
    @pytest.mark.asyncio
    async def test_identical_request_is_still_a_duplicate(self):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            assert (await _post(client)).status_code == 200
            second = await _post(client)
        assert second.status_code == 409
        assert second.json()["detail"]["error"] == "duplicate_submission"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "changed",
        [
            {"materiality_threshold": "500"},
            {"account_type_overrides": json.dumps({"Rent Expense": "liability"})},
            {
                "column_mapping": json.dumps(
                    {"account_column": "Account Name", "debit_column": "Debit", "credit_column": "Credit"}
                )
            },
        ],
        ids=["threshold", "overrides", "column_mapping"],
    )
    async def test_same_file_with_different_settings_is_not_a_duplicate(self, changed):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            assert (await _post(client)).status_code == 200
            rerun = await _post(client, **changed)
        assert rerun.status_code == 200, rerun.text

    @pytest.mark.asyncio
    async def test_force_resubmit_runs_an_identical_request(self):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            assert (await _post(client)).status_code == 200
            forced = await _post(client, force_resubmit="true")
        assert forced.status_code == 200
