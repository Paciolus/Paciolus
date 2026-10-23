"""
Sprint 815 — run-scoped parse memo.

The JE engine parsed every entry's dates ~11 times, each trying up to nine
strptime formats. A 100k-row GL with timestamps took 65.6s, almost all of it
in ``strptime``; with a memo held for the duration of one engine run it takes
9.6s, with identical scores and identical per-test flag counts.

The memo must never outlive the run — a process-wide cache would retain values
from uploaded files across requests, which Zero-Storage forbids.
"""

from __future__ import annotations

import ast
import random
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared import parsing_helpers
from shared.parsing_helpers import parse_date, parse_memo

BACKEND = Path(__file__).parent.parent

SAMPLES = [
    "2025-03-14",
    "03/14/2025",
    "14/03/2025",
    "2025/03/14",
    "03-14-2025",
    "14-03-2025",
    "2025-03-14 09:30:00",
    "03/14/2025 09:30:00",
    "2025-03-14T09:30:00",
    "  2025-03-14  ",
    "02/30/2025",
    "not a date",
    "",
    None,
]


def test_memoised_parsing_returns_exactly_what_unmemoised_parsing_returns():
    expected = [parse_date(s) for s in SAMPLES]
    with parse_memo():
        first = [parse_date(s) for s in SAMPLES]
        second = [parse_date(s) for s in SAMPLES]  # served from the memo
    assert first == expected
    assert second == expected


def test_the_memo_does_not_outlive_the_run():
    from je_testing_engine import run_je_testing

    rows = [
        {"Date": "01/15/2025", "Account": "Cash", "Debit": 100, "Credit": 0},
        {"Date": "01/15/2025", "Account": "Revenue", "Debit": 0, "Credit": 100},
    ]
    run_je_testing(rows, ["Date", "Account", "Debit", "Credit"])

    assert parsing_helpers._PARSE_MEMO.get() is None


def test_the_memo_is_dropped_even_when_the_run_raises():
    with pytest.raises(RuntimeError):
        with parse_memo():
            parse_date("2025-01-01")
            raise RuntimeError("engine failure")
    assert parsing_helpers._PARSE_MEMO.get() is None


def test_nested_runs_share_one_memo():
    with parse_memo():
        outer = parsing_helpers._PARSE_MEMO.get()
        with parse_memo():
            assert parsing_helpers._PARSE_MEMO.get() is outer
        assert parsing_helpers._PARSE_MEMO.get() is outer


ENTRY_POINTS = {
    "services/audit/ap_testing/analysis.py": ["run_ap_test_battery", "run_ap_testing"],
    "services/audit/ar_aging/analysis.py": ["run_ar_test_battery", "run_ar_aging"],
    "services/audit/fixed_asset_testing/analysis.py": ["run_fa_test_battery", "run_fixed_asset_testing"],
    "services/audit/inventory_testing/analysis.py": ["run_inv_test_battery", "run_inventory_testing"],
    "services/audit/je_testing/analysis.py": ["run_test_battery", "run_je_testing"],
    "services/audit/payroll_testing/analysis.py": ["run_payroll_test_battery", "run_payroll_testing"],
    "services/audit/revenue_testing/analysis.py": ["run_revenue_test_battery", "run_revenue_testing"],
    "bank_reconciliation.py": ["run_reconciliation_tests", "reconcile_bank_statement"],
    "three_way_match_engine.py": ["run_three_way_match"],
}


@pytest.mark.parametrize("path, functions", ENTRY_POINTS.items())
def test_every_engine_entry_point_runs_inside_a_memo(path, functions):
    tree = ast.parse((BACKEND / path).read_text(encoding="utf-8"))
    decorated = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and any(isinstance(d, ast.Name) and d.id == "with_parse_memo" for d in node.decorator_list)
    }
    assert set(functions) <= decorated, f"{path}: missing @with_parse_memo on {set(functions) - decorated}"


@pytest.mark.slow
def test_100k_row_general_ledger_with_timestamps_stays_fast():
    """Measured 65.6s before the memo, 9.6s after, on a developer machine.
    The ceiling leaves room for slower CI hardware while still failing loudly
    if the repetition comes back."""
    from je_testing_engine import run_je_testing

    rng = random.Random(7)
    accounts = ["1000", "1100", "2000", "3000", "4000", "5000", "6000", "7000"]
    rows = []
    for i in range(50_000):
        stamp = f"{rng.randint(1, 12):02d}/{rng.randint(1, 28):02d}/2025 {rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:00"
        amount = round(rng.uniform(10, 50_000), 2)
        debit_account, credit_account = rng.sample(accounts, 2)
        common = {"Entry ID": f"JE{i}", "Posting Date": stamp, "Entry Date": stamp, "Description": f"d{i % 500}"}
        rows.append({**common, "Account": debit_account, "Debit": amount, "Credit": 0.0})
        rows.append({**common, "Account": credit_account, "Debit": 0.0, "Credit": amount})

    started = time.perf_counter()
    run_je_testing(rows, ["Entry ID", "Posting Date", "Entry Date", "Description", "Account", "Debit", "Credit"])
    elapsed = time.perf_counter() - started

    assert elapsed < 30, f"100k-row JE run took {elapsed:.1f}s (was 9.6s after Sprint 815, 65.6s before)"


def test_threshold_gated_similarity_matches_plain_ratio_exactly():
    """The upper-bound shortcuts may only skip work, never change an answer."""
    from difflib import SequenceMatcher

    from shared.fuzzy_match import similarity_at_least

    rng = random.Random(11)
    alphabet = "abcde fgh"
    for _ in range(3000):
        a = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 14)))
        b = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 14)))
        threshold = rng.choice([0.0, 0.5, 0.8, 0.85, 0.9, 1.0])
        ratio = SequenceMatcher(None, a, b).ratio()
        assert similarity_at_least(a, b, threshold) == (ratio if ratio >= threshold else None), (a, b, threshold)
