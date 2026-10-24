"""Sprint 838 — bank rec CSV carries split matches and the split-search flag;
the API response carries the suggested journal entries the engine produces."""

import csv
import io
import json
from decimal import Decimal

import httpx
import pytest

from auth import require_current_user, require_verified_user
from bank_reconciliation import (
    SPLIT_SEARCH_LIMITED_CSV_NOTE,
    BankTransaction,
    LedgerTransaction,
    MatchType,
    ReconciliationMatch,
    calculate_summary,
    export_reconciliation_csv,
    reconcile_bank_statement,
)
from database import get_db
from main import app
from models import User, UserTier
from shared.testing_response_schemas import BankRecResponse


def _matches() -> list[ReconciliationMatch]:
    split_ledger = [
        LedgerTransaction(
            date="2026-03-15", description="=Receipt A", amount=Decimal("600.00"), reference="JE1", row_number=1
        ),
        LedgerTransaction(
            date="2026-03-15", description="Receipt B", amount=Decimal("400.00"), reference="@JE2", row_number=2
        ),
    ]
    return [
        ReconciliationMatch(
            bank_txn=BankTransaction(
                date="2026-03-15",
                description="+Lockbox deposit",
                amount=Decimal("1000.00"),
                reference="DEP9",
                row_number=1,
            ),
            ledger_txn=split_ledger[0],
            ledger_txns=split_ledger,
            match_type=MatchType.SPLIT,
            match_confidence=0.9,
        ),
        ReconciliationMatch(
            bank_txn=BankTransaction(
                date="2026-03-20", description="Unexplained", amount=Decimal("777.00"), row_number=2
            ),
            match_type=MatchType.BANK_ONLY,
            split_search_limited=True,
        ),
        ReconciliationMatch(
            bank_txn=BankTransaction(
                date="2026-03-21", description="Searched fully", amount=Decimal("55.00"), row_number=3
            ),
            match_type=MatchType.BANK_ONLY,
        ),
    ]


def _section(rows: list[list[str]], title: str) -> list[list[str]]:
    """Rows of a section after its title + header row, up to the blank line."""
    start = rows.index([title]) + 2
    out = []
    for row in rows[start:]:
        if not row:
            break
        out.append(row)
    return out


def _summary_value(rows: list[list[str]], label: str) -> str:
    for row in rows:
        if row and row[0] == label:
            return row[1]
    raise AssertionError(f"summary row {label!r} missing")


def _assert_csv(csv_str: str) -> None:
    rows = list(csv.reader(io.StringIO(csv_str)))
    split_rows = _section(rows, "SPLIT MATCHES (ONE BANK ITEM TO MULTIPLE LEDGER ITEMS)")
    assert len(split_rows) == 2  # one row per ledger piece
    first, second = split_rows
    assert first[0] == second[0] == "1"
    assert first[1:5] == ["2026-03-15", "'+Lockbox deposit", "1000.00", "DEP9"]
    assert second[1:5] == ["", "", "", ""]  # bank amount appears once per group
    assert first[6] == "'=Receipt A" and first[7] == "600.00"
    assert second[6] == "Receipt B" and second[8] == "'@JE2" and second[7] == "400.00"

    bank_only = _section(rows, "OUTSTANDING DEPOSITS (BANK ONLY)")
    by_desc = {r[1]: r for r in bank_only}
    assert by_desc["Unexplained"][4] == SPLIT_SEARCH_LIMITED_CSV_NOTE
    assert by_desc["Searched fully"][4] == ""

    assert _summary_value(rows, "Split Matches (included in Matched Items)") == "1"
    assert _summary_value(rows, "Bank Only Items Not Searched Exhaustively for Splits") == "1"
    assert _summary_value(rows, "Matched Items") == "1"


class TestCsvSplitsAndLimitedFlag:
    def test_engine_csv_lists_split_pieces_and_limited_flag(self):
        _assert_csv(export_reconciliation_csv(calculate_summary(_matches())))

    def test_csv_dates_are_formula_safe(self):
        m = ReconciliationMatch(
            bank_txn=BankTransaction(date="=1+1", description="x", amount=Decimal("1"), row_number=1),
            match_type=MatchType.BANK_ONLY,
        )
        rows = list(csv.reader(io.StringIO(export_reconciliation_csv(calculate_summary([m])))))
        assert _section(rows, "OUTSTANDING DEPOSITS (BANK ONLY)")[0][0] == "'=1+1"


@pytest.fixture
def verified_user(db_session):
    user = User(
        email="bankrec_838@example.com",
        name="Pro",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.mark.usefixtures("bypass_csrf")
class TestCsvExportRoute:
    @pytest.mark.asyncio
    async def test_route_rebuild_keeps_split_pieces_and_limited_flag(self, verified_user, db_session):
        """The route rebuilds the summary from the client's JSON; it dropped
        ``ledger_txns`` and ``split_search_limited`` before Sprint 838."""
        summary = calculate_summary(_matches())
        # Wire shape: the frontend posts back the numbers it received.
        body = json.loads(json.dumps(summary.to_dict(), default=float))
        app.dependency_overrides[require_current_user] = lambda: verified_user
        app.dependency_overrides[require_verified_user] = lambda: verified_user
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/export/csv/bank-rec",
                    json={"summary": body, "matches": body["matches"], "filename": "rec"},
                )
            assert response.status_code == 200, response.text
            _assert_csv(response.content.decode("utf-8-sig"))
        finally:
            app.dependency_overrides.clear()


class TestSuggestedJournalEntriesInResponse:
    def test_response_model_keeps_suggested_journal_entries(self):
        bank_rows = [
            {"Date": "2026-03-15", "Description": "Deposit", "Amount": "1000.00"},
            {"Date": "2026-03-31", "Description": "MONTHLY SERVICE FEE", "Amount": "-25.00"},
        ]
        ledger_rows = [{"Date": "2026-03-15", "Description": "Deposit", "Amount": "1000.00"}]
        result = reconcile_bank_statement(
            bank_rows, ledger_rows, ["Date", "Description", "Amount"], ["Date", "Description", "Amount"]
        )
        raw = result.to_dict()
        assert raw.get("suggested_journal_entries"), "fixture must produce a suggested JE"

        dumped = BankRecResponse.model_validate(raw).model_dump()
        jes = dumped["suggested_journal_entries"]
        assert jes and len(jes) == len(raw["suggested_journal_entries"])
        je = jes[0]
        assert je["bank_txn"]["description"] == "MONTHLY SERVICE FEE"
        assert je["amount"] == 25.0 or je["amount"] == -25.0
        assert je["kind"] in {"service_charge", "bank_fee"}
        assert je["debit_account"] and je["credit_account"]
