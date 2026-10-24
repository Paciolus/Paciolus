"""Sprint 833 — bank-rec split-match search bound (CEO decision 2, Sprint 815 item 2).

The split pass combines 2-4 ledger items per open bank item. With every row on
one day (or undated) the old pool was unbounded: ~2s per bank item at 80
candidates, 64.7M combinations at 200. The pool is now capped (a Paciolus
convention). Conservative requirements pinned here:

- a capped search never clears anything — an unfound split stays an open
  bank-only / ledger-only reconciling item;
- the result always discloses the bounds, and counts the open bank items that
  were not searched exhaustively.
"""

from __future__ import annotations

import io
import random
import threading
import time
from decimal import Decimal

from pypdf import PdfReader

from bank_reconciliation import (
    DEFAULT_SPLIT_MATCH_MAX_CANDIDATES,
    BankRecConfig,
    BankTransaction,
    LedgerTransaction,
    MatchType,
    match_transactions,
    reconcile_bank_statement,
    split_search_disclosure,
)
from bank_reconciliation_memo_generator import generate_bank_rec_memo
from shared.export_schemas import BankRecMemoInput
from shared.testing_response_schemas import BankRecResponse


def _bank(row: int, amount: str, date: str = "2026-03-15") -> BankTransaction:
    return BankTransaction(row_number=row, date=date, description=f"Bank {row}", amount=Decimal(amount))


def _ledger(row: int, amount: str, date: str = "2026-03-15") -> LedgerTransaction:
    return LedgerTransaction(row_number=row, date=date, description=f"Ledger {row}", amount=Decimal(amount))


def _dense_same_day(n: int) -> tuple[list[BankTransaction], list[LedgerTransaction]]:
    """n bank and n ledger rows on one day, none matching one-to-one."""
    rng = random.Random(830)
    bank = [_bank(i, f"{rng.randint(5_000, 90_000)}.37") for i in range(n)]
    ledger = [_ledger(i, f"{rng.randint(100, 20_000)}.{rng.randint(0, 99):02d}") for i in range(n)]
    return bank, ledger


class TestPerformanceBound:
    def test_200_unmatched_same_day_rows_complete_quickly(self):
        bank, ledger = _dense_same_day(200)
        box: dict = {}

        def _run() -> None:
            start = time.perf_counter()
            box["matches"] = match_transactions(bank, ledger, BankRecConfig())
            box["elapsed"] = time.perf_counter() - start

        # Daemon thread so the pre-Sprint-830 engine (hours at this size)
        # fails the test instead of hanging the suite.
        worker = threading.Thread(target=_run, daemon=True)
        worker.start()
        worker.join(timeout=20)
        assert not worker.is_alive(), "split-match pass did not finish within 20s"
        assert box["elapsed"] < 5.0

        matches = box["matches"]
        # Nothing was cleared by the bound: all rows remain open items.
        assert sum(1 for m in matches if m.match_type == MatchType.BANK_ONLY) == 200
        assert sum(1 for m in matches if m.match_type == MatchType.LEDGER_ONLY) == 200
        disclosure = split_search_disclosure(matches, BankRecConfig())
        assert disclosure["limited_count"] > 0
        assert "not searched exhaustively" in disclosure["note"]


class TestCapNeverClearsAnException:
    def test_split_beyond_the_cap_stays_open_and_is_disclosed(self):
        # The real split (600 + 400) is 3 days from the bank date; 25 same-day
        # decoys that cannot sum to 1,000 fill the nearest-dated cap first.
        cfg = BankRecConfig(date_tolerance_days=5)
        bank = [_bank(1, "1000.00", date="2026-03-15")]
        decoys = [_ledger(100 + i, "1.13", date="2026-03-15") for i in range(25)]
        real = [_ledger(1, "600.00", date="2026-03-18"), _ledger(2, "400.00", date="2026-03-18")]

        matches = match_transactions(bank, decoys + real, cfg)

        assert not any(m.match_type == MatchType.SPLIT for m in matches)
        bank_only = [m for m in matches if m.match_type == MatchType.BANK_ONLY]
        assert len(bank_only) == 1 and bank_only[0].split_search_limited is True
        assert bank_only[0].to_dict()["split_search_limited"] is True
        open_ledger_rows = {m.ledger_txn.row_number for m in matches if m.match_type == MatchType.LEDGER_ONLY}
        assert {1, 2} <= open_ledger_rows

        disclosure = split_search_disclosure(matches, cfg)
        assert disclosure["limited_count"] == 1
        assert disclosure["date_window_days"] == 5
        assert disclosure["max_candidates"] == DEFAULT_SPLIT_MATCH_MAX_CANDIDATES
        assert "±5 days" in disclosure["note"]
        assert "1 bank item was not searched exhaustively" in disclosure["note"]
        assert "Paciolus convention" in disclosure["note"]

    def test_split_outside_the_date_window_stays_open(self):
        bank = [_bank(1, "1000.00", date="2026-03-15")]
        ledger = [_ledger(1, "600.00", date="2026-03-15"), _ledger(2, "400.00", date="2026-03-16")]
        matches = match_transactions(bank, ledger, BankRecConfig())  # window 0 = same day

        assert [m.match_type for m in matches].count(MatchType.BANK_ONLY) == 1
        assert [m.match_type for m in matches].count(MatchType.LEDGER_ONLY) == 2
        disclosure = split_search_disclosure(matches, BankRecConfig())
        assert disclosure["date_window_days"] == 0
        assert "same day" in disclosure["note"]
        # Window exclusion is not a cap: the search within the window was exhaustive.
        assert disclosure["limited_count"] == 0

    def test_lossless_prune_keeps_search_exhaustive(self):
        # 30 same-day items larger than the bank amount can never be a piece of
        # its split, so they do not count against the cap.
        bank = [_bank(1, "1000.00")]
        too_big = [_ledger(100 + i, f"{2000 + i}.00") for i in range(30)]
        real = [_ledger(1, "600.00"), _ledger(2, "400.00")]
        matches = match_transactions(bank, too_big + real, BankRecConfig())

        split = [m for m in matches if m.match_type == MatchType.SPLIT]
        assert len(split) == 1
        assert {t.row_number for t in split[0].ledger_txns} == {1, 2}
        assert split_search_disclosure(matches, BankRecConfig())["limited_count"] == 0

    def test_cap_is_configurable(self):
        bank = [_bank(1, "1000.00")]
        decoys = [_ledger(100 + i, "1.13") for i in range(25)]
        real = [_ledger(1, "600.00"), _ledger(2, "400.00")]
        # With a cap above the pool size the search is exhaustive and finds it.
        matches = match_transactions(bank, decoys + real, BankRecConfig(split_match_max_candidates=30))
        assert any(m.match_type == MatchType.SPLIT for m in matches)


class TestEndToEndDisclosure:
    def test_pipeline_emits_disclosure_and_split_passes_response_schema(self):
        bank_rows = [{"Date": "2026-03-15", "Description": "Deposit", "Amount": "1000.00"}]
        ledger_rows = [
            {"Date": "2026-03-15", "Description": "Receipt A", "Amount": "600.00"},
            {"Date": "2026-03-15", "Description": "Receipt B", "Amount": "400.00"},
        ]
        result = reconcile_bank_statement(
            bank_rows, ledger_rows, ["Date", "Description", "Amount"], ["Date", "Description", "Amount"]
        )
        payload = result.to_dict()
        assert payload["split_search"]["limited_count"] == 0
        assert payload["split_search"]["max_candidates"] == DEFAULT_SPLIT_MATCH_MAX_CANDIDATES
        assert payload["active_thresholds"]["split_match_max_candidates"] == DEFAULT_SPLIT_MATCH_MAX_CANDIDATES
        assert [m["match_type"] for m in payload["summary"]["matches"]] == ["split"]

        # Before Sprint 833 the response model rejected "split", so the
        # endpoint 500'd on any reconciliation containing a split match.
        validated = BankRecResponse.model_validate(payload)
        assert validated.split_search is not None
        assert validated.summary.matches[0].match_type == "split"
        assert len(validated.summary.matches[0].ledger_txns or []) == 2


class TestMemoDisclosure:
    def test_memo_prints_split_search_note(self):
        bank_rows = [{"Date": "2026-03-15", "Description": "Deposit", "Amount": "1000.00"}]
        cols = ["Date", "Description", "Amount"]
        payload = reconcile_bank_statement(bank_rows, [], cols, cols).to_dict()
        payload["split_search"]["note"] = "2 bank items were not searched exhaustively."
        # The memo export input keeps the field rather than dropping it.
        memo_input = BankRecMemoInput(
            summary=payload["summary"],
            bank_column_detection=payload["bank_column_detection"],
            ledger_column_detection=payload["ledger_column_detection"],
            split_search=payload["split_search"],
        )
        pdf = generate_bank_rec_memo(memo_input.model_dump())
        text = " ".join(" ".join((p.extract_text() or "").split()) for p in PdfReader(io.BytesIO(pdf)).pages)
        assert "Split matching:" in text
        assert "not searched exhaustively" in text
