"""Sprint 885 / 10A (review OUT-01): the convergence CSV is written by the safe CSV writer.

The route built each line by string concatenation, so an uploaded account name
containing a comma split into extra cells — one of them a live formula — and a
quote or line break broke the record structure. Every record must parse as
exactly three cells, and formula text must be escaped.
"""

import csv
import io

import httpx
import pytest

from auth import require_current_user
from database import get_db
from engagement_manager import EngagementManager
from main import app
from models import Client, Industry, User, UserTier

HOSTILE_ACCOUNTS = [
    "Operating Expense,=1+1",
    'Cash "Main" Account',
    "Accrued\nLiabilities",
    "Prepaids\r\n=cmd|' /C calc'!A0",
    "Rent;@SUM(A1:A2)",
    '=HYPERLINK("http://x")',
    "Revenue,+1,-2",
]


@pytest.fixture
def owner(db_session):
    user = User(
        email="sprint885_conv@example.com",
        name="Conv Tester",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session
    yield user
    app.dependency_overrides.clear()


@pytest.fixture
def engagement(db_session, owner, make_engagement):
    client = Client(user_id=owner.id, name="Conv Client", industry=Industry.TECHNOLOGY, fiscal_year_end="12-31")
    db_session.add(client)
    db_session.flush()
    return make_engagement(client=client, user=owner)


@pytest.fixture
def hostile_index(monkeypatch):
    items = [
        {"account": name, "convergence_count": i + 1, "tools_flagging_it": ["je_testing", f"=tool{i},x"]}
        for i, name in enumerate(HOSTILE_ACCOUNTS)
    ]
    monkeypatch.setattr(EngagementManager, "get_convergence_index", lambda self, engagement_id: items)
    return items


async def _download(engagement_id: int) -> list[list[str]]:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/engagements/{engagement_id}/export/convergence-csv")
    assert response.status_code == 200
    return list(csv.reader(io.StringIO(response.content.decode("utf-8"))))


@pytest.mark.usefixtures("bypass_csrf")
class TestConvergenceCsvStructure:
    @pytest.mark.asyncio
    async def test_every_record_has_exactly_three_cells(self, engagement, hostile_index):
        rows = await _download(engagement.id)
        assert rows[0] == ["Account", "Convergence Count", "Tools Flagging It"]
        assert len(rows) == 1 + len(HOSTILE_ACCOUNTS)
        for row in rows:
            assert len(row) == 3, row

    @pytest.mark.asyncio
    async def test_account_text_round_trips_and_formulas_are_escaped(self, engagement, hostile_index):
        rows = await _download(engagement.id)
        for row, name in zip(rows[1:], HOSTILE_ACCOUNTS, strict=True):
            account, count, tools = row
            expected = "'" + name if name[0] in "=+-@\t\r\n|" else name
            assert account == expected
            # No cell may begin with a formula trigger unless escaped with a quote.
            for cell in (account, tools):
                assert not cell or cell[0] not in "=+-@\t\r\n|"
            assert count.isdigit()

    @pytest.mark.asyncio
    async def test_count_stays_a_number(self, engagement, hostile_index):
        rows = await _download(engagement.id)
        assert [r[1] for r in rows[1:]] == [str(i + 1) for i in range(len(HOSTILE_ACCOUNTS))]
