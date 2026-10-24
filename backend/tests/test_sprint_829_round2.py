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


# ── Shared date parser, AP-T14 ─────────────────────────────────────────


@pytest.mark.parametrize(
    "value, expected",
    [
        ("01-Jan-2025", "2025-01-01"),
        ("5 Jan 2025", "2025-01-05"),
        ("Jan 5, 2025", "2025-01-05"),
        ("January 5, 2025", "2025-01-05"),
        ("20250105", "2025-01-05"),
        ("2025-01-05 00:00:00.000", "2025-01-05"),
        ("01/08/25", "2025-01-08"),
        ("08.01.2025", "2025-01-08"),
        ("2025-01-08T23:15:00Z", "2025-01-08"),
        ("6/2/2025 11:15 PM", "2025-06-02"),
    ],
)
def test_exported_ledger_date_forms_are_parsed(value, expected):
    from shared.parsing_helpers import parse_date

    assert parse_date(value).isoformat() == expected


def test_excel_datetime_cells_parse_and_nat_does_not():
    """Payroll pay dates from an .xlsx register arrive as Timestamps; all were None."""
    import pandas as pd

    from shared.parsing_helpers import parse_date

    assert parse_date(pd.Timestamp("2025-03-15 00:00:00")).isoformat() == "2025-03-15"
    assert parse_date(pd.NaT) is None


def test_invoice_without_po_runs_when_a_po_column_is_present():
    from services.audit.ap_testing.analysis import APTestingEngine, detect_ap_columns

    cols = ["Vendor Name", "Amount", "Payment Date", "Invoice Number", "PO Number"]
    assert detect_ap_columns(cols).po_number_column == "PO Number"
    assert "po_number_column" in detect_ap_columns(cols).to_dict()

    overridden = APTestingEngine().apply_column_overrides(
        detect_ap_columns(["Vendor Name", "Amount", "Payment Date", "Req"]), {"po_number_column": "Req"}
    )
    assert overridden.po_number_column == "Req"


def test_an_unclosed_trial_balance_satisfies_the_accounting_equation():
    """T2: revenue/expense not yet closed to retained earnings are equity; the
    pre-closing TB was reported as a significant imbalance of its net income."""
    from audit.classification import validate_balance_sheet_equation
    from ratio_engine import CategoryTotals

    unclosed = CategoryTotals(
        total_assets=150000, total_liabilities=70000, total_equity=30000, total_revenue=200000, total_expenses=150000
    )
    result = validate_balance_sheet_equation(unclosed)
    assert result["is_balanced"] is True
    assert result["current_period_earnings"] == 50000

    # A genuinely broken one still fails.
    broken = CategoryTotals(total_assets=150000, total_liabilities=70000, total_equity=30000)
    assert validate_balance_sheet_equation(broken)["status"] == "significant_imbalance"


# ── Bank reconciliation ────────────────────────────────────────────────


def test_bank_split_never_mixes_signs_or_ignores_a_zero_date_tolerance():
    from bank_reconciliation import BankRecConfig, BankTransaction, LedgerTransaction, MatchType, match_transactions

    bank = [BankTransaction(date="2025-12-10", description="Deposit", amount=1000.0)]
    mixed = [
        LedgerTransaction(date="2025-12-10", description="Receipt", amount=1500.0),
        LedgerTransaction(date="2025-12-10", description="Cheque 101", amount=-500.0),
    ]
    matches = match_transactions(bank, mixed, BankRecConfig())
    assert not any(m.match_type == MatchType.SPLIT for m in matches)

    far_apart = [
        LedgerTransaction(date="2025-12-10", description="Receipt A", amount=600.0),
        LedgerTransaction(date="2025-12-28", description="Receipt B", amount=400.0),
    ]
    matches = match_transactions(bank, far_apart, BankRecConfig(date_tolerance_days=0))
    assert not any(m.match_type == MatchType.SPLIT for m in matches)

    same_day = [
        LedgerTransaction(date="2025-12-10", description="Receipt A", amount=600.0),
        LedgerTransaction(date="2025-12-10", description="Receipt B", amount=400.0),
    ]
    matches = match_transactions(bank, same_day, BankRecConfig(date_tolerance_days=0))
    assert [m.match_type for m in matches] == [MatchType.SPLIT]


def test_stale_items_use_the_right_population_and_the_statement_date():
    from datetime import date

    from bank_reconciliation import (
        BankTransaction,
        LedgerTransaction,
        MatchType,
        ReconciliationMatch,
        run_reconciliation_tests,
    )

    ref = date(2025, 12, 31)
    matches = [
        # Bank credit missing from the books — not a deposit in transit.
        ReconciliationMatch(
            bank_txn=BankTransaction(date="2025-11-01", description="Interest", amount=12.0),
            match_type=MatchType.BANK_ONLY,
        ),
        # Receipt in the books, not yet on the statement — a deposit in transit.
        ReconciliationMatch(
            ledger_txn=LedgerTransaction(date="2025-12-01", description="Deposit", amount=5000.0),
            match_type=MatchType.LEDGER_ONLY,
        ),
        # Old outstanding cheque.
        ReconciliationMatch(
            ledger_txn=LedgerTransaction(date="2025-08-01", description="Cheque 88", amount=-900.0),
            match_type=MatchType.LEDGER_ONLY,
        ),
    ]
    deposits, checks = run_reconciliation_tests(matches, reference_date=ref)[:2]
    assert [i.description for i in deposits.flagged_items] == ["Deposit outstanding 30 days: Deposit"]
    assert [i.amount for i in checks.flagged_items] == [-900.0]


# ── Three-way match ────────────────────────────────────────────────────


def test_multi_line_po_lines_pair_by_content_not_file_order():
    from three_way_match_engine import Invoice, PurchaseOrder, Receipt, run_three_way_match

    pos = [
        PurchaseOrder(
            po_number="PO-1",
            vendor="Acme",
            description="Widget A",
            quantity=10,
            unit_price=5,
            total_amount=50,
            row_number=1,
        ),
        PurchaseOrder(
            po_number="PO-1",
            vendor="Acme",
            description="Widget B",
            quantity=2,
            unit_price=200,
            total_amount=400,
            row_number=2,
        ),
    ]
    invoices = [  # billed correctly, listed in the other order
        Invoice(
            invoice_number="INV-9",
            po_reference="PO-1",
            vendor="Acme",
            description="Widget B",
            quantity=2,
            unit_price=200,
            total_amount=400,
            row_number=1,
        ),
        Invoice(
            invoice_number="INV-9",
            po_reference="PO-1",
            vendor="Acme",
            description="Widget A",
            quantity=10,
            unit_price=5,
            total_amount=50,
            row_number=2,
        ),
    ]
    receipts = [
        Receipt(po_reference="PO-1", vendor="Acme", description="Widget B", quantity_received=2, row_number=1),
        Receipt(po_reference="PO-1", vendor="Acme", description="Widget A", quantity_received=10, row_number=2),
    ]
    result = run_three_way_match(pos, invoices, receipts)
    assert len(result.full_matches) == 2
    assert result.variances == []


def test_invoice_quantity_is_compared_with_the_quantity_received():
    from three_way_match_engine import Invoice, PurchaseOrder, Receipt, run_three_way_match

    pos = [PurchaseOrder(po_number="PO-2", vendor="Acme", quantity=100, unit_price=10, total_amount=1000, row_number=1)]
    invoices = [
        Invoice(
            invoice_number="INV-2",
            po_reference="PO-2",
            vendor="Acme",
            quantity=100,
            unit_price=10,
            total_amount=1000,
            row_number=1,
        )
    ]
    receipts = [Receipt(po_reference="PO-2", vendor="Acme", quantity_received=60, row_number=1)]
    result = run_three_way_match(pos, invoices, receipts)
    billed = [v for v in result.variances if v.field == "billed_quantity"]
    assert len(billed) == 1
    assert (billed[0].invoice_value, billed[0].receipt_value, billed[0].severity) == (100, 60, "high")


def test_ratios_state_how_many_unclassified_accounts_they_exclude():
    """T4: unknown-category accounts were dropped from every ratio without a word."""
    from ratio_engine import summarize_unclassified

    balances = {
        "Cash": {"debit": 1000, "credit": 0},
        "Zxq 1": {"debit": 250, "credit": 0},
        "Zxq 2": {"debit": 0, "credit": 400.5},
        "Zxq 3": {"debit": 10, "credit": 10},  # nets to zero — nothing excluded
    }
    classified = {"Cash": "asset", "Zxq 1": "unknown", "Zxq 3": "unknown"}
    assert summarize_unclassified(balances, classified) == {"count": 2, "total_abs_balance": 650.5}


def test_a_file_supplied_account_type_outranks_a_contradicting_keyword():
    """T5: the file's type column was only a fallback — "Revenue Share Payable"
    typed Liability went to the Revenue lead sheet, "Inventory Reserve Expense"
    typed Expense to Inventory."""
    from classification_rules import AccountCategory
    from lead_sheet_mapping import LeadSheet, assign_lead_sheet, group_by_lead_sheet

    assert assign_lead_sheet("Revenue Share Payable", AccountCategory.LIABILITY, trust_category=True).lead_sheet == (
        LeadSheet.G
    )
    assert assign_lead_sheet("Inventory Reserve Expense", AccountCategory.EXPENSE, trust_category=True).lead_sheet == (
        LeadSheet.N
    )
    # A compatible keyword still refines placement within the type.
    assert assign_lead_sheet("Prepaid Insurance", AccountCategory.ASSET, trust_category=True).lead_sheet == LeadSheet.D
    # Without a supplied type the keyword placement is unchanged.
    assert assign_lead_sheet("Revenue Share Payable", AccountCategory.LIABILITY).lead_sheet == LeadSheet.L

    grouping = group_by_lead_sheet(
        [{"account": "Revenue Share Payable", "debit": 0, "credit": 900, "type": "liability", "type_supplied": True}]
    )
    assert {s.lead_sheet for s in grouping.summaries if s.account_count} == {LeadSheet.G}


@pytest.mark.parametrize(
    "name, category, is_current",
    [
        ("Non-current Receivable", "asset", False),
        ("Long-term Notes Receivable", "asset", False),
        ("Deferred Tax Asset", "asset", False),
        ("Accounts Receivable", "asset", True),
        ("Long-term Notes Payable", "liability", False),
        ("Non-current Lease Liability", "liability", False),
        ("Current Portion of Long-term Debt", "liability", True),
        ("Accounts Payable", "liability", True),
        ("Mortgage Payable", "liability", False),
        ("Deferred Revenue", "liability", True),
        ("Customer Deposits", "liability", True),
        ("Line of Credit", "liability", True),
    ],
)
def test_current_classification_respects_non_current_names(name, category, is_current):
    """T3: substring keywords put long-term balances in the current ratio."""
    from ratio_engine import extract_category_totals

    totals = extract_category_totals(
        {name: {"debit": 100, "credit": 0} if category == "asset" else {"debit": 0, "credit": 100}},
        {name: category},
    )
    current = totals.current_assets if category == "asset" else totals.current_liabilities
    assert (current == 100) is is_current


def test_allowance_nets_into_receivables_for_dso_and_the_current_ratio():
    from ratio_engine import extract_category_totals

    totals = extract_category_totals(
        {
            "Accounts Receivable": {"debit": 10000, "credit": 0},
            "Allowance for Doubtful Accounts": {"debit": 0, "credit": 500},
        },
        {"Accounts Receivable": "asset", "Allowance for Doubtful Accounts": "asset"},
    )
    assert totals.accounts_receivable == 9500
    assert totals.current_assets == 9500


def test_je_after_hours_reads_iso_z_and_12_hour_timestamps():
    from services.audit.je_testing.analysis import _extract_hour

    assert _extract_hour("2025-06-02T23:15:00Z") == 23
    assert _extract_hour("6/2/2025 11:15 PM") == 23
    assert _extract_hour("2025-06-02 23:15:00.000") == 23


def test_reconciliation_summary_counts_split_matches():
    from bank_reconciliation import (
        BankRecConfig,
        BankTransaction,
        LedgerTransaction,
        calculate_summary,
        match_transactions,
    )

    bank = [BankTransaction(date="2025-12-10", description="Deposit", amount=3000.0)]
    ledger = [
        LedgerTransaction(date="2025-12-10", description="A", amount=1000.0),
        LedgerTransaction(date="2025-12-10", description="B", amount=2000.0),
    ]
    summary = calculate_summary(match_transactions(bank, ledger, BankRecConfig()))
    assert summary.matched_count == 1
    assert (summary.total_bank, summary.total_ledger, summary.reconciling_difference) == (3000, 3000, 0)


# ── Revenue P2s ────────────────────────────────────────────────────────


def test_revenue_trend_nets_returns_and_concentration_ignores_contra():
    from services.audit.revenue_testing.analysis import (
        RevenueEntry,
        RevenueTestingConfig,
        test_concentration_risk,
        test_revenue_trend_variance,
    )

    trend = [
        RevenueEntry(amount=-1_200_000, row_number=1, account_name="Sales"),
        RevenueEntry(amount=150_000, row_number=2, account_name="Customer returns"),
        RevenueEntry(amount=-1, row_number=3, account_name="Sales"),
    ]
    result = test_revenue_trend_variance(trend, RevenueTestingConfig(prior_period_total=1_000_000))
    assert result.entries_flagged == 0  # net 1,050,001 vs 1,000,000 is +5%

    mix = [
        RevenueEntry(amount=-600_000, row_number=1, account_name="Product"),
        RevenueEntry(amount=-400_000, row_number=2, account_name="Service"),
        RevenueEntry(amount=200_000, row_number=3, account_name="Sales Returns"),
    ]
    flagged = test_concentration_risk(mix, RevenueTestingConfig())
    assert flagged.entries_flagged == 1  # was 600/1,200 = 50.0%, under the threshold
    assert "'product' represents 60.0%" in flagged.flagged_entries[0].issue


# ── AR P2s ─────────────────────────────────────────────────────────────


def test_not_yet_due_invoices_are_current_not_errors():
    from services.audit.ar_aging.analysis import (
        ARAgingConfig,
        ARSubledgerEntry,
        compute_aging_schedule,
        test_negative_aging,
    )

    entries = [
        ARSubledgerEntry(customer_name="A", amount=600, aging_days=-10, due_date="2026-01-10", row_number=1),
        ARSubledgerEntry(customer_name="B", amount=400, aging_days=45, due_date="2025-11-16", row_number=2),
        ARSubledgerEntry(customer_name="C", amount=100, aging_days=-5, row_number=3),  # no due date: an error
    ]
    assert [f.entry.row_number for f in test_negative_aging(entries, ARAgingConfig()).flagged_entries] == [3]
    schedule = compute_aging_schedule(entries)
    assert sum(b["amount"] for b in schedule) == 1100
    assert schedule[0]["amount"] == 700


def test_customer_concentration_base_excludes_customers_in_credit():
    from services.audit.ar_aging.analysis import ARAgingConfig, ARSubledgerEntry, test_customer_concentration

    entries = [ARSubledgerEntry(customer_name=c, amount=2500, row_number=i) for i, c in enumerate("ABCD", 1)]
    entries.append(ARSubledgerEntry(customer_name="E", amount=-4000, row_number=5))
    result = test_customer_concentration(entries, ARAgingConfig())
    assert {f.details["customer_pct"] for f in result.flagged_entries} <= {0.25}
    assert all(f.severity.value != "high" for f in result.flagged_entries)


# ── Inventory P2s ──────────────────────────────────────────────────────


def test_value_mismatch_catches_zero_extended_and_large_absolute_differences():
    from services.audit.inventory_testing.analysis import (
        InventoryEntry,
        InventoryTestingConfig,
        test_extended_value_mismatch,
    )

    entries = [
        InventoryEntry(item_id="A", quantity=100, unit_cost=50, extended_value=0, row_number=1),
        InventoryEntry(item_id="B", quantity=100_000, unit_cost=100, extended_value=10_090_000, row_number=2),
        InventoryEntry(item_id="C", quantity=10, unit_cost=5, extended_value=50, row_number=3),
    ]
    flagged = test_extended_value_mismatch(entries, InventoryTestingConfig())
    assert sorted(f.entry.row_number for f in flagged.flagged_entries) == [1, 2]

    # No extended-value column at all: nothing to test, nothing flagged.
    bare = [InventoryEntry(item_id="A", quantity=100, unit_cost=50, row_number=1)]
    assert test_extended_value_mismatch(bare, InventoryTestingConfig()).entries_flagged == 0


def test_duplicate_items_ignore_one_sku_across_locations_and_cost_only_groups():
    from services.audit.inventory_testing.analysis import (
        InventoryEntry,
        InventoryTestingConfig,
        test_duplicate_items,
    )

    two_warehouses = [
        InventoryEntry(item_id="SKU-1", description="Widget", unit_cost=25, quantity=5, location="East", row_number=1),
        InventoryEntry(item_id="SKU-1", description="Widget", unit_cost=25, quantity=7, location="West", row_number=2),
    ]
    assert test_duplicate_items(two_warehouses, InventoryTestingConfig()).entries_flagged == 0

    no_description = [InventoryEntry(item_id=f"S{i}", unit_cost=25, quantity=1, row_number=i) for i in range(1, 6)]
    assert test_duplicate_items(no_description, InventoryTestingConfig()).entries_flagged == 0

    same_id_same_place = [
        InventoryEntry(item_id="SKU-9", unit_cost=10, quantity=1, location="East", row_number=1),
        InventoryEntry(item_id="SKU-9", unit_cost=10, quantity=1, location="East", row_number=2),
    ]
    assert test_duplicate_items(same_id_same_place, InventoryTestingConfig()).entries_flagged == 2


def test_fixed_monthly_payments_are_not_fuzzy_duplicates():
    from services.audit.ap_testing.analysis import APPayment, APTestingConfig, test_fuzzy_duplicate_payments

    lease = [
        APPayment(vendor_name="Landlord LLC", amount=18432.17, payment_date=f"2025-{m:02d}-01", row_number=m)
        for m in range(1, 7)
    ]
    assert test_fuzzy_duplicate_payments(lease, APTestingConfig()).entries_flagged == 0

    # A re-keyed duplicate inside the window is still caught.
    dup = [
        APPayment(vendor_name="Acme", amount=900, payment_date="2025-02-10", invoice_number="INV-5", row_number=1),
        APPayment(vendor_name="Acme", amount=900, payment_date="2025-02-14", invoice_number="INV-6", row_number=2),
    ]
    assert test_fuzzy_duplicate_payments(dup, APTestingConfig()).entries_flagged == 2


def test_round_amount_cap_keeps_the_largest_and_counts_all():
    from services.audit.je_testing.analysis import JETestingConfig, test_round_amounts

    entries = [_je(i, f"JE-{i}", "2025-03-05", "Expense", debit=10000) for i in range(1, 61)]
    entries.append(_je(61, "JE-61", "2025-03-05", "Revenue", credit=500000))
    result = test_round_amounts(entries, JETestingConfig())
    assert result.entries_flagged == 61
    assert len(result.flagged_entries) == 50
    assert result.flagged_entries[0].entry.row_number == 61


def test_small_group_outliers_can_be_flagged():
    """Nine $101–$109 payments and one $1M payment: z inclusive of the outlier
    can never exceed (n−1)/√n ≈ 2.85, so it was never flagged."""
    from services.audit.ap_testing.analysis import APPayment, APTestingConfig, test_unusual_payment_amounts
    from services.audit.je_testing.analysis import JETestingConfig, test_unusual_amounts

    amounts = [101, 102, 103, 104, 105, 106, 107, 108, 109, 1_000_000]
    payments = [
        APPayment(vendor_name="V", amount=a, payment_date="2025-01-02", row_number=i) for i, a in enumerate(amounts)
    ]
    ap = test_unusual_payment_amounts(payments, APTestingConfig())
    assert [f.entry.row_number for f in ap.flagged_entries] == [9]

    entries = [_je(i, f"JE-{i}", "2025-03-05", "Supplies", debit=a) for i, a in enumerate(amounts)]
    je = test_unusual_amounts(entries, JETestingConfig())
    assert [f.entry.row_number for f in je.flagged_entries] == [9]
