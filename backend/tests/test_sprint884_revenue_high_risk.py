"""Sprint 884 / 9F (review OUT-23): a transaction flagged by two HIGH tests counts once.

The revenue memo's "High-Risk Entries (HIGH severity)" figure added every
HIGH test's flagged amounts, so a transaction flagged by two tests was counted
twice — and the "% of total" beside it overstated revenue at risk.
"""

from __future__ import annotations

from io import BytesIO

from revenue_testing_memo_generator import generate_revenue_testing_memo
from tests.test_revenue_testing_memo import _make_revenue_result


def _entry(row: int, amount: float) -> dict:
    return {
        "entry": {"date": "2025-12-31", "amount": amount, "account_name": "Product Revenue", "row_number": row},
        "severity": "high",
        "issue": "flagged",
        "details": {},
    }


def _test(key: str, entries: list[dict], severity: str = "high") -> dict:
    return {
        "test_name": key.replace("_", " ").title(),
        "test_key": key,
        "test_tier": "statistical",
        "entries_flagged": len(entries),
        "total_entries": 200,
        "flag_rate": len(entries) / 200,
        "severity": severity,
        "description": key,
        "flagged_entries": entries,
    }


def _pdf_text(pdf_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


def _memo(test_results: list[dict]) -> str:
    result = _make_revenue_result()
    result["test_results"] = test_results
    result["total_revenue"] = 10_000.0
    return _pdf_text(generate_revenue_testing_memo(result))


def test_a_transaction_flagged_by_two_high_tests_counts_once():
    text = _memo(
        [
            _test("cutoff_risk", [_entry(7, -1000.0), _entry(8, -500.0)]),
            _test("large_manual_entries", [_entry(7, -1000.0)]),
        ]
    )
    assert "High-Risk Entries (HIGH severity)" in text
    assert "$1,500.00 (15.0% of total)" in text
    assert "$2,500.00" not in text


def test_distinct_transactions_across_tests_all_count():
    text = _memo(
        [
            _test("cutoff_risk", [_entry(7, -1000.0)]),
            _test("large_manual_entries", [_entry(9, -250.0)]),
        ]
    )
    assert "$1,250.00 (12.5% of total)" in text


def test_medium_severity_tests_are_not_counted():
    text = _memo(
        [
            _test("cutoff_risk", [_entry(7, -1000.0)]),
            _test("round_revenue_amounts", [_entry(9, -250.0)], severity="medium"),
        ]
    )
    assert "$1,000.00 (10.0% of total)" in text
