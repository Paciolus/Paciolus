"""
Sprint 829 — second-round discovery findings (revenue, AR, inventory).
Each case reproduces the discovery pass's input.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_excel_datetime_due_dates_are_aged():
    """#1: an .xlsx sub-ledger's due dates arrive as "2025-06-01 00:00:00" and
    were never parsed, so the whole ledger landed in Current."""
    from services.audit.ar_aging.analysis import _compute_aging_days

    assert _compute_aging_days("2025-06-01 00:00:00", "2025-12-31") == 213
    assert _compute_aging_days("2025-06-01", "2025-12-31") == 213


def test_invoice_date_only_sub_ledger_is_aged_and_says_so():
    """#2: with no due date column nothing was aged and nothing warned."""
    from services.audit.ar_aging.analysis import SLColumnDetection, parse_sl_entries

    detection = SLColumnDetection(
        customer_name_column="Customer", amount_column="Amount", invoice_date_column="Invoice Date"
    )
    rows = [
        {"Customer": "A", "Amount": 5000, "Invoice Date": "2025-06-01"},
        {"Customer": "B", "Amount": 5000, "Invoice Date": "2025-12-15"},
    ]
    entries = parse_sl_entries(rows, detection, "2025-12-31")
    assert [e.aging_days for e in entries] == [213, 16]
    assert any("aged from the invoice date" in note for note in detection.detection_notes)


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Accounts Receivable", "ar"),
        ("Accounts Receivable - Trade", "ar"),
        ("Notes Receivable - Officer", "other"),
        ("Interest Receivable", "other"),
        ("Sales Revenue", "revenue"),
        ("Deferred Revenue", "other"),
        ("Sales Tax Payable", "other"),
    ],
)
def test_non_trade_receivables_and_unearned_revenue_are_not_classified_as_ar_or_revenue(name, expected):
    """#3: they read a 5% allowance as 0.91% and a 36.5-day DSO as 118, both HIGH."""
    from services.audit.ar_aging.analysis import _classify_account

    assert _classify_account(name)[0] == expected


def test_lcm_nrv_runs_when_a_selling_price_column_is_present():
    """#5: "Selling Price" was detected and then dropped, so IN-T10 never ran."""
    from inventory_testing_engine import InventoryTestingConfig, run_inventory_testing

    columns = ["Item ID", "Description", "Quantity", "Unit Cost", "Extended Value", "Selling Price"]
    rows = [
        {
            "Item ID": "A",
            "Description": "Underwater",
            "Quantity": 10,
            "Unit Cost": 100,
            "Extended Value": 1000,
            "Selling Price": 90,
        },
        {
            "Item ID": "B",
            "Description": "Thin margin",
            "Quantity": 10,
            "Unit Cost": 100,
            "Extended Value": 1000,
            "Selling Price": 105,
        },
        {
            "Item ID": "C",
            "Description": "Healthy",
            "Quantity": 10,
            "Unit Cost": 100,
            "Extended Value": 1000,
            "Selling Price": 200,
        },
    ]
    result = run_inventory_testing(
        rows=rows, column_names=columns, config=InventoryTestingConfig(), column_mapping=None
    )
    lcm = next(t for t in result.to_dict()["test_results"] if t["test_key"] == "lcm_nrv_indicator")
    assert lcm["entries_flagged"] == 2


@pytest.mark.parametrize(
    "csv_text",
    [
        'Account,Debit,Credit\nCash,"1,234.56",\nSales Revenue,,"1,234.56"\n',
        'Account,Debit,Credit\nCash,"$1,234.56",\nSales Revenue,,1234.56\n',
    ],
    ids=["thousands-separators", "mixed-formatting"],
)
def test_formatted_csv_amounts_are_read_not_zeroed(csv_text):
    """Round 2, T1 (core TB): formatted amounts in a CSV coerced to NaN -> 0, so
    a TB written as "1,234.56" reported balanced with totals of 0.00 — and a
    partly formatted one reported a false out-of-balance. Sprint 671 fixed this
    for PDF/ODS/TXT only; CSV and Excel take a different read path."""
    from audit.pipeline import audit_trial_balance_streaming

    result = audit_trial_balance_streaming(csv_text.encode(), "tb.csv")
    assert float(result["total_debits"]) == pytest.approx(1234.56)
    assert float(result["total_credits"]) == pytest.approx(1234.56)
    assert result["balanced"] is True


def test_dupont_and_common_size_reach_the_client_as_numbers():
    """Round 2, T6: through TrialBalanceResponse (analytics: dict[str, Any]) these
    serialised as JSON strings, and the frontend's formatDupont called
    "1.0000".toFixed(4) — a TypeError on every TB with a DuPont breakdown."""
    import json

    from audit.pipeline import audit_trial_balance_streaming
    from shared.diagnostic_response_schemas import TrialBalanceResponse

    csv = (
        "Account,Account Type,Debit,Credit\nCash,Asset,500000,\nAccounts Receivable,Asset,300000,\n"
        "Inventory,Asset,200000,\nAccounts Payable,Liability,,250000\nCommon Stock,Equity,,400000\n"
        "Retained Earnings,Equity,,200000\nSales Revenue,Revenue,,1000000\nCost of Goods Sold,Expense,600000,\n"
        "Rent Expense,Expense,250000,\n"
    )
    body = json.loads(TrialBalanceResponse(**audit_trial_balance_streaming(csv.encode(), "tb.csv")).model_dump_json())
    analytics = body["analytics"]
    dupont = {k: v for k, v in analytics["dupont"].items() if k not in ("verification_matches", "prior_period_deltas")}
    assert dupont and all(isinstance(v, float) for v in dupont.values()), dupont
    for section in analytics["common_size"].values():
        assert all(isinstance(v, (int, float)) for v in section.values()), section


# ── Journal entry testing ──────────────────────────────────────────────


def _je(row, entry_id, date, account, debit=0, credit=0, **kw):
    from services.audit.je_testing.analysis import JournalEntry

    return JournalEntry(
        row_number=row, entry_id=entry_id, posting_date=date, account=account, debit=debit, credit=credit, **kw
    )


def test_reciprocal_does_not_pair_an_entrys_own_debit_and_credit():
    """A balanced two-line entry is not a round trip; this flagged 61% of a clean GL HIGH."""
    from services.audit.je_testing.analysis import JETestingConfig, test_reciprocal_entries

    entries = [
        _je(1, "JE-1", "2025-03-05", "Rent Expense", debit=5000),
        _je(2, "JE-1", "2025-03-05", "Cash", credit=5000),
        _je(3, "JE-2", "2025-03-09", "Supplies", debit=2500),
        _je(4, "JE-2", "2025-03-09", "Accounts Payable", credit=2500),
    ]
    assert test_reciprocal_entries(entries, JETestingConfig()).entries_flagged == 0

    # A reversal by a separate entry is still caught.
    entries += [
        _je(5, "JE-3", "2025-03-10", "Cash", debit=5000),
        _je(6, "JE-3", "2025-03-10", "Rent Expense", credit=5000),
    ]
    assert test_reciprocal_entries(entries, JETestingConfig()).entries_flagged == 4


def test_just_below_threshold_counts_rows_and_keeps_debits_and_credits_apart():
    from services.audit.je_testing.analysis import JETestingConfig, test_just_below_threshold

    # A $6K debit and its $6K credit reversal on one day are not a $12K split.
    reversal = [
        _je(1, "JE-1", "2025-03-05", "Suspense", debit=6000),
        _je(2, "JE-2", "2025-03-05", "Suspense", credit=6000),
    ]
    assert test_just_below_threshold(reversal, JETestingConfig()).entries_flagged == 0

    # Two $4,900 debits: each just below $5K and together a split over $5K —
    # two flags per row, but two rows.
    split = [
        _je(1, "JE-1", "2025-03-05", "Consulting", debit=4900),
        _je(2, "JE-2", "2025-03-05", "Consulting", debit=4900),
    ]
    result = test_just_below_threshold(split, JETestingConfig())
    assert result.entries_flagged == 2
    assert result.flag_rate == 1.0


def test_after_hours_ignores_excel_midnight_date_cells():
    from services.audit.je_testing.analysis import JETestingConfig, test_after_hours_postings

    date_only = [_je(i, f"JE-{i}", "2025-03-05 00:00:00", "Cash", debit=100) for i in range(1, 6)]
    assert test_after_hours_postings(date_only, JETestingConfig()).entries_flagged == 0

    # Real timestamps: a 23:15 posting is flagged, and a genuine midnight
    # posting among them is still tested.
    timed = [
        _je(1, "JE-1", "2025-03-05 10:00:00", "Cash", debit=100),
        _je(2, "JE-2", "2025-03-05 23:15:00", "Cash", debit=100),
        _je(3, "JE-3", "2025-03-06 00:00:00", "Cash", debit=100),
    ]
    assert test_after_hours_postings(timed, JETestingConfig()).entries_flagged == 2


def test_numbering_gaps_read_the_trailing_sequence_per_series():
    from services.audit.je_testing.analysis import JETestingConfig, test_numbering_gaps

    ids = ["JE-2025-0001", "JE-2025-0002", "JE-2025-0006", "JE-2026-0001", "JE-2026-0002"]
    entries = [_je(i, eid, "2025-03-05", "Cash", debit=100) for i, eid in enumerate(ids, 1)]
    result = test_numbering_gaps(entries, JETestingConfig())
    assert result.entries_flagged == 1
    assert result.flagged_entries[0].entry.entry_id == "JE-2025-0006"
    assert result.flagged_entries[0].details["gap_size"] == 3


def test_an_unbalanced_ledger_is_never_rated_low():
    from services.audit.je_testing.analysis import calculate_composite_score, run_test_battery
    from shared.testing_enums import RiskTier

    entries = []
    for i in range(1, 101):
        entries += [
            _je(2 * i - 1, f"JE-{i}", "2025-03-05", "Expense", debit=100 + i, description="ok", posted_by="a"),
            _je(2 * i, f"JE-{i}", "2025-03-05", "Cash", credit=100 + i, description="ok", posted_by="a"),
        ]
    entries.append(_je(999, "JE-999", "2025-03-06", "Revenue", credit=250000, description="x", posted_by="a"))
    results, _ = run_test_battery(entries)
    composite = calculate_composite_score(results, len(entries))
    assert composite.risk_tier in (RiskTier.ELEVATED, RiskTier.HIGH)
