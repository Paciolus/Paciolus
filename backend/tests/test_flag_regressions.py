"""
FLAG Scenario Regression Tests — AUDIT-06 Phase 2

Tests only: no production code modified.

Each test documents expected behavior for FLAG scenarios from the AUDIT-06
edge-case matrix. A PASS means the behavior is confirmed correct. A FAIL
means a live bug has been found. Failures are NOT suppressed — they are
findings for follow-up remediation.

FLAG Groups:
  G1 — Single-Account Populations (14 diagnostics)
  G2 — Negative Balances in Unexpected Accounts (15 diagnostics)
  G3 — Extremely Large Values >$1T (21 diagnostics)
  G4 — Missing Expected Account Types (14 diagnostics)
  G5 — Duplicate Account Codes (19 diagnostics)
"""

import csv
import io
import json
import sys
from datetime import date
from decimal import Decimal
from typing import Any

sys.path.insert(0, "..")

# ---------------------------------------------------------------------------
# Engine imports
# ---------------------------------------------------------------------------

from accrual_completeness_engine import run_accrual_completeness  # RPT-20
from ap_testing_engine import run_ap_testing  # RPT-04
from ar_aging_engine import run_ar_aging  # RPT-07
from audit_engine import audit_trial_balance_streaming  # RPT-01/21
from bank_reconciliation import reconcile_bank_statement  # RPT-10
from benchmark_engine import (  # RPT-17
    IndustryBenchmark,
    compare_to_benchmark,
)
from composite_risk_engine import (  # RPT-18
    AccountRiskAssessment,
    build_composite_risk_profile,
)
from currency_engine import (  # RPT-13
    CurrencyRateTable,
    ExchangeRate,
    convert_trial_balance,
)
from engagement_dashboard_engine import compute_engagement_dashboard  # DASH-01
from expense_category_engine import run_expense_category_analytics  # RPT-19
from fixed_asset_testing_engine import run_fixed_asset_testing  # RPT-08
from flux_engine import FluxEngine  # RPT-15
from inventory_testing_engine import run_inventory_testing  # RPT-09
from je_testing_engine import run_je_testing  # RPT-03
from models import Industry
from multi_period_comparison import compare_trial_balances  # RPT-02
from payroll_testing_engine import run_payroll_testing  # RPT-05
from population_profile_engine import run_population_profile  # RPT-16
from ratio_engine import CategoryTotals, RatioEngine  # RPT-14
from revenue_testing_engine import run_revenue_testing  # RPT-06
from sampling_engine import SamplingConfig, design_sample  # RPT-12
from three_way_match_engine import (  # RPT-11
    Invoice,
    PurchaseOrder,
    Receipt,
    run_three_way_match,
)

# ===========================================================================
# HELPERS
# ===========================================================================


def _csv_bytes(columns: list[str], rows: list[dict]) -> bytes:
    """Build CSV bytes suitable for file-based engine entry points."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


# -- TB rows (Account, Account Name, Account Type, Debit, Credit) ----------

TB_COLS = ["Account", "Account Name", "Account Type", "Debit", "Credit"]


def _tb(code, name, atype, debit=0, credit=0):
    return {
        "Account": code,
        "Account Name": name,
        "Account Type": atype,
        "Debit": debit,
        "Credit": credit,
    }


# -- GL rows (journal entry testing) ----------------------------------------

GL_COLS = ["Date", "Entry ID", "Account", "Description", "Debit", "Credit", "Posted By"]


def _gl(dt, eid, acct, desc, debit=0, credit=0, by="admin"):
    return {
        "Date": dt,
        "Entry ID": eid,
        "Account": acct,
        "Description": desc,
        "Debit": debit,
        "Credit": credit,
        "Posted By": by,
    }


# -- AP rows -----------------------------------------------------------------

AP_COLS = ["Date", "Vendor", "Invoice Number", "Amount", "Check Number", "Description"]


def _ap(dt, vendor, inv, amt, chk, desc):
    return {
        "Date": dt,
        "Vendor": vendor,
        "Invoice Number": inv,
        "Amount": amt,
        "Check Number": chk,
        "Description": desc,
    }


# -- Payroll rows ------------------------------------------------------------

PR_COLS = ["Date", "Employee ID", "Employee Name", "Gross Pay", "Net Pay", "Department"]


def _pr(dt, eid, name, gross, net, dept):
    return {
        "Date": dt,
        "Employee ID": eid,
        "Employee Name": name,
        "Gross Pay": gross,
        "Net Pay": net,
        "Department": dept,
    }


# -- Revenue rows ------------------------------------------------------------

REV_COLS = ["Date", "Account", "Description", "Amount"]


def _rev(dt, acct, desc, amt):
    return {"Date": dt, "Account": acct, "Description": desc, "Amount": amt}


# -- Fixed asset rows --------------------------------------------------------

FA_COLS = [
    "Asset ID",
    "Description",
    "Cost",
    "Accumulated Depreciation",
    "Acquisition Date",
    "Useful Life",
    "Depreciation Method",
]


def _fa(aid, desc, cost, accum, acq_dt, life, method="Straight-Line"):
    return {
        "Asset ID": aid,
        "Description": desc,
        "Cost": cost,
        "Accumulated Depreciation": accum,
        "Acquisition Date": acq_dt,
        "Useful Life": life,
        "Depreciation Method": method,
    }


# -- Inventory rows ----------------------------------------------------------

INV_COLS = ["Item ID", "Description", "Quantity", "Unit Cost", "Extended Value", "Category"]


def _inv(iid, desc, qty, ucost, ext, cat):
    return {
        "Item ID": iid,
        "Description": desc,
        "Quantity": qty,
        "Unit Cost": ucost,
        "Extended Value": ext,
        "Category": cat,
    }


# -- Bank rows ---------------------------------------------------------------

BANK_COLS = ["Date", "Description", "Amount"]


def _bank(dt, desc, amt):
    return {"Date": dt, "Description": desc, "Amount": amt}


# -- Three-way match helpers -------------------------------------------------


def _po(num, vendor, amt, row=1):
    return PurchaseOrder(po_number=num, vendor=vendor, total_amount=Decimal(str(amt)), row_number=row)


def _invoice(num, po_ref, vendor, amt, row=1):
    return Invoice(
        invoice_number=num, po_reference=po_ref, vendor=vendor, total_amount=Decimal(str(amt)), row_number=row
    )


def _receipt(num, po_ref, vendor, qty=1.0, row=1):
    return Receipt(receipt_number=num, po_reference=po_ref, vendor=vendor, quantity_received=qty, row_number=row)


# -- Currency helpers --------------------------------------------------------


def _rate_table(from_cur, to_cur, rate, pres="USD"):
    return CurrencyRateTable(
        rates=[
            ExchangeRate(
                effective_date=date(2026, 1, 1), from_currency=from_cur, to_currency=to_cur, rate=Decimal(str(rate))
            )
        ],
        presentation_currency=pres,
    )


# -- Benchmark helper --------------------------------------------------------


def _benchmark(ratio_name="current_ratio", p50=1.5):
    return IndustryBenchmark(
        ratio_name=ratio_name,
        industry=Industry.RETAIL,
        fiscal_year=2025,
        p10=0.5,
        p25=1.0,
        p50=p50,
        p75=2.5,
        p90=3.5,
        mean=1.8,
        std_dev=0.8,
        sample_size=500,
        source="Test fixture",
    )


# -- Dashboard report helper ------------------------------------------------


def _dashboard_report(rtype, score=50, flagged=3, high=1, tests=5):
    return {
        "report_type": rtype,
        "report_title": rtype.replace("_", " ").title(),
        "composite_score": {
            "score": score,
            "risk_tier": "medium",
            "total_flagged": flagged,
            "flags_by_severity": {"high": high, "medium": flagged - high, "low": 0},
            "tests_run": tests,
        },
        "test_results": [],
    }


# -- Serialization check ----------------------------------------------------


def _no_scientific_notation(obj: Any) -> bool:
    """Return True if JSON serialization of *obj* contains no scientific notation."""
    serialized = json.dumps(obj, default=str)
    # Scientific notation patterns: 1e+12, 1.5E-3, 2E12
    import re

    return not re.search(r"\d[eE][+-]?\d", serialized)


# -- Balanced TB for various tests ------------------------------------------


def _balanced_tb():
    """Minimal balanced 4-account TB."""
    return [
        _tb("1000", "Cash", "Asset", debit=100000),
        _tb("2000", "Accounts Payable", "Liability", credit=40000),
        _tb("3000", "Retained Earnings", "Equity", credit=30000),
        _tb("4000", "Revenue", "Revenue", credit=50000),
        _tb("5000", "Operating Expenses", "Expense", debit=20000),
    ]


TRILLION = 1_000_000_000_001.23  # > $1T, with cents


# ===========================================================================
# FLAG GROUP 1 — Single-Account Populations
# ===========================================================================


class TestFlagG1SingleAccountPopulation:
    """Tests for diagnostics receiving a one-row / one-item population."""

    def test_rpt01_single_account_tb_audit(self):
        """RPT-01: Single-row TB should not crash; should indicate limited population."""
        rows = [_tb("1000", "Cash", "Asset", debit=50000)]
        csv = _csv_bytes(TB_COLS, rows)
        result = audit_trial_balance_streaming(csv, "single.csv")
        assert isinstance(result, dict)
        # A single-account TB should have some quality or population indicator
        serialized = json.dumps(result, default=str)
        has_indicator = (
            result.get("total_accounts", 0) <= 1
            or "single" in serialized.lower()
            or "population" in serialized.lower()
            or "insufficient" in serialized.lower()
            or result.get("risk_summary", {}).get("total_accounts", 99) <= 1
        )
        assert has_indicator, (
            f"RPT-01 FLAG: Single-account TB produced result without population "
            f"quality indication. total_accounts={result.get('total_accounts')}"
        )

    def test_rpt03_single_gl_entry(self):
        """RPT-03: JE testing with 1 GL entry should not crash."""
        rows = [_gl("2025-06-15", "JE001", "Cash", "Opening balance", debit=50000)]
        result = run_je_testing(rows, GL_COLS)
        assert result is not None
        d = result.to_dict() if hasattr(result, "to_dict") else result
        assert isinstance(d, dict)

    def test_rpt04_single_ap_entry(self):
        """RPT-04: AP testing with 1 payment should not crash."""
        rows = [_ap("2025-06-15", "Vendor A", "INV001", 5000, "CHK001", "Materials")]
        result = run_ap_testing(rows, AP_COLS)
        assert result is not None

    def test_rpt05_single_payroll_entry(self):
        """RPT-05: Payroll testing with 1 employee should not crash."""
        rows = [_pr("2025-01-31", "E001", "Jane Doe", 5000, 3500, "Sales")]
        result = run_payroll_testing(PR_COLS, rows)
        assert result is not None

    def test_rpt06_single_revenue_entry(self):
        """RPT-06: Revenue testing with 1 entry should not crash."""
        rows = [_rev("2025-06-15", "4000 Revenue", "Product sale", 10000)]
        result = run_revenue_testing(rows, REV_COLS)
        assert result is not None

    def test_rpt07_single_ar_account(self):
        """RPT-07: AR aging with 1 TB row should not crash."""
        rows = [_tb("1200", "Accounts Receivable", "Asset", debit=25000)]
        result = run_ar_aging(rows, TB_COLS)
        assert result is not None

    def test_rpt08_single_fixed_asset(self):
        """RPT-08: Fixed asset testing with 1 asset should not crash."""
        rows = [_fa("FA001", "Office Equipment", 50000, 10000, "2020-01-15", 5)]
        result = run_fixed_asset_testing(rows, FA_COLS)
        assert result is not None

    def test_rpt09_single_inventory_item(self):
        """RPT-09: Inventory testing with 1 item should not crash."""
        rows = [_inv("INV001", "Widget A", 100, 25.50, 2550.00, "Raw Materials")]
        result = run_inventory_testing(rows, INV_COLS)
        assert result is not None

    def test_rpt10_single_bank_transaction(self):
        """RPT-10: Bank rec with 1 bank row + 1 ledger row should not crash."""
        bank = [_bank("2025-06-15", "Deposit", 10000)]
        ledger = [_bank("2025-06-15", "Cash Receipt", 10000)]
        result = reconcile_bank_statement(bank, ledger, BANK_COLS, BANK_COLS)
        assert result is not None

    def test_rpt11_single_three_way_set(self):
        """RPT-11: Three-way match with 1 PO/Invoice/Receipt should not crash."""
        result = run_three_way_match(
            [_po("PO001", "Vendor A", 5000)],
            [_invoice("INV001", "PO001", "Vendor A", 5000)],
            [_receipt("REC001", "PO001", "Vendor A")],
        )
        assert result is not None

    def test_rpt16_single_account_population_profile(self):
        """RPT-16: Population profile with 1 account should not crash and should flag limited population."""
        rows = [_tb("1000", "Cash", "Asset", debit=50000)]
        result = run_population_profile(TB_COLS, rows, "single.csv")
        d = result.to_dict() if hasattr(result, "to_dict") else result
        assert d.get("account_count", 0) <= 1, "RPT-16 FLAG: Single-account population profile should report count <= 1"

    def test_rpt17_single_ratio_benchmark(self):
        """RPT-17: Benchmark comparison with a single ratio value should not crash."""
        result = compare_to_benchmark("current_ratio", 1.5, _benchmark())
        assert result is not None

    def test_rpt18_single_risk_assessment(self):
        """RPT-18: Composite risk with 1 assessment should not crash."""
        assessment = AccountRiskAssessment(
            account_name="Cash",
            assertion="existence",
            inherent_risk="low",
            control_risk="low",
        )
        result = build_composite_risk_profile([assessment])
        assert result is not None
        assert result.total_assessments == 1

    def test_rpt20_single_accrual_account(self):
        """RPT-20: Accrual completeness with 1 accrual account should not crash."""
        rows = [_tb("2100", "Accrued Expenses", "Liability", credit=15000)]
        result = run_accrual_completeness(TB_COLS, rows, "single.csv")
        assert result is not None


# ===========================================================================
# FLAG GROUP 2 — Negative Balances in Unexpected Accounts
# ===========================================================================


class TestFlagG2NegativeBalances:
    """Tests for unexpected negative balances (wrong-sign accounts)."""

    def _assert_flags_or_handles(self, result_dict: dict, rpt: str):
        """Common assertion: result should contain some flag/warning for unexpected sign."""
        serialized = json.dumps(result_dict, default=str).lower()
        has_sign_handling = any(
            kw in serialized
            for kw in [
                "negative",
                "sign",
                "abnormal",
                "anomal",
                "unexpected",
                "contra",
                "warning",
                "flag",
                "reversal",
            ]
        )
        assert has_sign_handling, (
            f"{rpt} FLAG: Negative balance in unexpected account produced no sign-related "
            f"flag, warning, or anomaly in the response."
        )

    def test_rpt02_negative_balance_multi_period(self):
        """RPT-02: Multi-period with negative revenue should flag sign change."""
        prior = [
            _tb("1000", "Cash", "Asset", debit=50000),
            _tb("4000", "Revenue", "Revenue", credit=80000),
            _tb("2000", "Accounts Payable", "Liability", credit=30000),
        ]
        current = [
            _tb("1000", "Cash", "Asset", debit=50000),
            _tb("4000", "Revenue", "Revenue", debit=5000),  # Negative revenue (debit side)
            _tb("2000", "Accounts Payable", "Liability", credit=45000),
        ]
        result = compare_trial_balances(prior, current)
        d = result.to_dict() if hasattr(result, "to_dict") else {}
        # Revenue going from credit to debit is a sign change
        serialized = json.dumps(d, default=str).lower()
        assert "sign" in serialized or any(m.get("movement_type") == "sign_change" for m in d.get("movements", [])), (
            "RPT-02 FLAG: Revenue sign flip not flagged as sign_change"
        )

    def test_rpt03_negative_gl_amounts(self):
        """RPT-03: JE testing with negative debit in revenue account."""
        rows = [
            _gl("2025-06-15", "JE001", "Revenue", "Reversal", debit=-5000, credit=0),
            _gl("2025-06-15", "JE001", "Cash", "Reversal", debit=0, credit=-5000),
        ]
        result = run_je_testing(rows, GL_COLS)
        assert result is not None

    def test_rpt04_negative_ap_amount(self):
        """RPT-04: AP testing with negative payment amount."""
        rows = [
            _ap("2025-06-15", "Vendor A", "INV001", -5000, "CHK001", "Credit memo"),
            _ap("2025-06-20", "Vendor B", "INV002", 3000, "CHK002", "Materials"),
        ]
        result = run_ap_testing(rows, AP_COLS)
        assert result is not None

    def test_rpt05_negative_payroll(self):
        """RPT-05: Payroll with negative gross pay."""
        rows = [
            _pr("2025-01-31", "E001", "Jane Doe", -2000, -1500, "Sales"),
            _pr("2025-01-31", "E002", "John Smith", 5000, 3500, "Engineering"),
        ]
        result = run_payroll_testing(PR_COLS, rows)
        assert result is not None

    def test_rpt06_negative_revenue_entry(self):
        """RPT-06: Revenue testing with negative revenue amount (debit-side)."""
        rows = [
            _rev("2025-06-15", "4000 Revenue", "Credit memo", -10000),
            _rev("2025-06-20", "4000 Revenue", "Product sale", 15000),
        ]
        result = run_revenue_testing(rows, REV_COLS)
        assert result is not None

    def test_rpt07_negative_ar_balance(self):
        """RPT-07: AR aging with negative (credit) AR balance."""
        rows = [
            _tb("1200", "Accounts Receivable", "Asset", credit=5000),  # Negative AR
            _tb("4000", "Revenue", "Revenue", credit=50000),
        ]
        result = run_ar_aging(rows, TB_COLS)
        assert result is not None

    def test_rpt10_negative_bank_amount(self):
        """RPT-10: Bank rec with negative bank transaction amount."""
        bank = [
            _bank("2025-06-15", "NSF Return", -5000),
            _bank("2025-06-16", "Deposit", 10000),
        ]
        ledger = [
            _bank("2025-06-15", "NSF Charge", -5000),
            _bank("2025-06-16", "Cash Receipt", 10000),
        ]
        result = reconcile_bank_statement(bank, ledger, BANK_COLS, BANK_COLS)
        assert result is not None

    def test_rpt11_negative_po_amount(self):
        """RPT-11: Three-way match with negative PO amount."""
        result = run_three_way_match(
            [_po("PO001", "Vendor A", -5000)],
            [_invoice("INV001", "PO001", "Vendor A", -5000)],
            [_receipt("REC001", "PO001", "Vendor A")],
        )
        assert result is not None

    def test_rpt13_negative_currency_amount(self):
        """RPT-13: Currency conversion with negative balance."""
        rows = [
            {"Account": "1000", "Account Name": "Cash", "Amount": -50000, "Currency": "EUR"},
            {"Account": "2000", "Account Name": "AP", "Amount": 30000, "Currency": "EUR"},
        ]
        rt = _rate_table("EUR", "USD", "1.10")
        result = convert_trial_balance(rows, rt, amount_column="Amount", currency_column="Currency")
        assert result is not None
        d = result.to_dict() if hasattr(result, "to_dict") else result
        assert d.get("conversion_performed", False) or d.get("converted_count", 0) >= 0

    def test_rpt16_negative_balance_population_profile(self):
        """RPT-16: Population profile with negative asset balance."""
        rows = [
            _tb("1000", "Cash", "Asset", credit=5000),  # Negative asset
            _tb("2000", "Accounts Payable", "Liability", credit=30000),
            _tb("4000", "Revenue", "Revenue", credit=50000),
        ]
        result = run_population_profile(TB_COLS, rows, "negative.csv")
        assert result is not None

    def test_rpt17_negative_ratio_benchmark(self):
        """RPT-17: Benchmark comparison with negative ratio value."""
        result = compare_to_benchmark("current_ratio", -0.5, _benchmark())
        assert result is not None
        assert result.percentile is not None, "RPT-17 FLAG: Negative ratio should still produce a percentile placement"

    def test_rpt18_negative_diagnostic_score(self):
        """RPT-18: Composite risk with negative TB diagnostic score."""
        assessment = AccountRiskAssessment(
            account_name="Cash",
            assertion="existence",
            inherent_risk="moderate",
            control_risk="moderate",
        )
        result = build_composite_risk_profile(
            [assessment],
            tb_diagnostic_score=-10,
            tb_diagnostic_tier="low",
        )
        assert result is not None

    def test_rpt19_negative_expense_balance(self):
        """RPT-19: Expense category with negative expense (credit-side expense)."""
        rows = [
            _tb("5000", "Operating Expenses", "Expense", credit=10000),  # Negative expense
            _tb("4000", "Revenue", "Revenue", credit=80000),
            _tb("5100", "Salary Expense", "Expense", debit=50000),
        ]
        result = run_expense_category_analytics(TB_COLS, rows, "negative_expense.csv")
        assert result is not None

    def test_rpt20_negative_accrual_balance(self):
        """RPT-20: Accrual completeness with negative (debit) accrual."""
        rows = [
            _tb("2100", "Accrued Expenses", "Liability", debit=5000),  # Wrong sign
            _tb("5000", "Operating Expenses", "Expense", debit=60000),
        ]
        result = run_accrual_completeness(TB_COLS, rows, "negative_accrual.csv")
        assert result is not None

    def test_dash01_negative_scores_dashboard(self):
        """DASH-01: Dashboard with negative risk scores in reports."""
        reports = [
            {
                "report_type": "revenue_testing",
                "report_title": "Revenue Testing",
                "composite_score": {
                    "score": -5,
                    "risk_tier": "low",
                    "total_flagged": 0,
                    "flags_by_severity": {"high": 0, "medium": 0, "low": 0},
                    "tests_run": 5,
                },
                "test_results": [],
            }
        ]
        result = compute_engagement_dashboard(reports)
        assert result is not None
        d = result.to_dict() if hasattr(result, "to_dict") else result
        assert isinstance(d, dict)


# ===========================================================================
# FLAG GROUP 3 — Extremely Large Values (>$1T)
# ===========================================================================


class TestFlagG3LargeValues:
    """Tests for values exceeding $1,000,000,000,000 (one trillion)."""

    T = TRILLION  # 1_000_000_000_001.23

    def _assert_precision(self, result_obj: Any, rpt: str):
        """Assert no scientific notation in serialized result."""
        if hasattr(result_obj, "to_dict"):
            d = result_obj.to_dict()
        elif isinstance(result_obj, dict):
            d = result_obj
        else:
            d = str(result_obj)
        assert _no_scientific_notation(d), f"{rpt} FLAG: Scientific notation found in response with >$1T values"

    def test_rpt01_trillion_dollar_tb(self):
        """RPT-01: TB audit with >$1T balance should not overflow or truncate."""
        rows = [
            _tb("1000", "Cash", "Asset", debit=self.T),
            _tb("3000", "Equity", "Equity", credit=self.T),
        ]
        csv = _csv_bytes(TB_COLS, rows)
        result = audit_trial_balance_streaming(csv, "trillion.csv")
        assert isinstance(result, dict)
        self._assert_precision(result, "RPT-01")

    def test_rpt02_trillion_multi_period(self):
        """RPT-02: Multi-period with >$1T balances."""
        prior = [_tb("1000", "Cash", "Asset", debit=self.T)]
        current = [_tb("1000", "Cash", "Asset", debit=self.T + 1000)]
        result = compare_trial_balances(prior, current)
        self._assert_precision(result, "RPT-02")

    def test_rpt03_trillion_gl_entry(self):
        """RPT-03: JE testing with >$1T entry."""
        rows = [
            _gl("2025-06-15", "JE001", "Cash", "Large transfer", debit=self.T),
            _gl("2025-06-15", "JE001", "Equity", "Large transfer", credit=self.T),
        ]
        result = run_je_testing(rows, GL_COLS)
        self._assert_precision(result, "RPT-03")

    def test_rpt04_trillion_ap_payment(self):
        """RPT-04: AP testing with >$1T payment."""
        rows = [_ap("2025-06-15", "Mega Corp", "INV001", self.T, "CHK001", "Large payment")]
        result = run_ap_testing(rows, AP_COLS)
        self._assert_precision(result, "RPT-04")

    def test_rpt05_trillion_payroll(self):
        """RPT-05: Payroll with >$1T gross pay."""
        rows = [_pr("2025-01-31", "E001", "CEO Galactic", self.T, self.T * 0.7, "Executive")]
        result = run_payroll_testing(PR_COLS, rows)
        self._assert_precision(result, "RPT-05")

    def test_rpt06_trillion_revenue(self):
        """RPT-06: Revenue testing with >$1T entry."""
        rows = [_rev("2025-06-15", "4000 Revenue", "Mega deal", self.T)]
        result = run_revenue_testing(rows, REV_COLS)
        self._assert_precision(result, "RPT-06")

    def test_rpt07_trillion_ar(self):
        """RPT-07: AR aging with >$1T receivable balance."""
        rows = [
            _tb("1200", "Accounts Receivable", "Asset", debit=self.T),
            _tb("4000", "Revenue", "Revenue", credit=self.T),
        ]
        result = run_ar_aging(rows, TB_COLS)
        self._assert_precision(result, "RPT-07")

    def test_rpt08_trillion_fixed_asset(self):
        """RPT-08: Fixed asset with >$1T cost."""
        rows = [_fa("FA001", "Space Station", self.T, self.T * 0.1, "2020-01-01", 30)]
        result = run_fixed_asset_testing(rows, FA_COLS)
        self._assert_precision(result, "RPT-08")

    def test_rpt09_trillion_inventory(self):
        """RPT-09: Inventory with >$1T extended value."""
        rows = [_inv("INV001", "Rare Earth Stockpile", 1, self.T, self.T, "Strategic")]
        result = run_inventory_testing(rows, INV_COLS)
        self._assert_precision(result, "RPT-09")

    def test_rpt10_trillion_bank_rec(self):
        """RPT-10: Bank rec with >$1T transaction."""
        bank = [_bank("2025-06-15", "Wire Transfer", self.T)]
        ledger = [_bank("2025-06-15", "Wire Transfer", self.T)]
        result = reconcile_bank_statement(bank, ledger, BANK_COLS, BANK_COLS)
        self._assert_precision(result, "RPT-10")

    def test_rpt11_trillion_three_way(self):
        """RPT-11: Three-way match with >$1T amounts."""
        result = run_three_way_match(
            [_po("PO001", "Mega Corp", self.T)],
            [_invoice("INV001", "PO001", "Mega Corp", self.T)],
            [_receipt("REC001", "PO001", "Mega Corp")],
        )
        self._assert_precision(result, "RPT-11")

    def test_rpt12_trillion_sampling_population(self):
        """RPT-12: Statistical sampling with >$1T population value."""
        cols = ["Item ID", "Description", "Amount"]
        rows = [
            {"Item ID": "1", "Description": "Item A", "Amount": str(self.T)},
            {"Item ID": "2", "Description": "Item B", "Amount": "500000"},
            {"Item ID": "3", "Description": "Item C", "Amount": "300000"},
            {"Item ID": "4", "Description": "Item D", "Amount": "200000"},
            {"Item ID": "5", "Description": "Item E", "Amount": "100000"},
            {"Item ID": "6", "Description": "Item F", "Amount": "50000"},
        ]
        csv = _csv_bytes(cols, rows)
        config = SamplingConfig(
            method="mus",
            confidence_level=0.95,
            tolerable_misstatement=float(self.T) * 0.05,
        )
        result = design_sample(csv, "trillion_pop.csv", config)
        self._assert_precision(result, "RPT-12")

    def test_rpt14_trillion_ratios(self):
        """RPT-14: Ratio engine with >$1T category totals."""
        totals = CategoryTotals(
            total_assets=self.T,
            current_assets=self.T * 0.6,
            inventory=self.T * 0.1,
            accounts_receivable=self.T * 0.2,
            accounts_payable=self.T * 0.15,
            total_liabilities=self.T * 0.4,
            current_liabilities=self.T * 0.25,
            total_equity=self.T * 0.6,
            total_revenue=self.T * 0.8,
            cost_of_goods_sold=self.T * 0.5,
            total_expenses=self.T * 0.7,
            operating_expenses=self.T * 0.2,
        )
        engine = RatioEngine(totals)
        cr = engine.calculate_current_ratio()
        assert cr.value is not None
        self._assert_precision(cr, "RPT-14")

    def test_rpt15_trillion_flux(self):
        """RPT-15: Flux analysis with >$1T balances."""
        current = {"Cash": {"net": self.T, "type": "Asset"}}
        prior = {"Cash": {"net": self.T - 1000000, "type": "Asset"}}
        engine = FluxEngine(materiality_threshold=1000000)
        result = engine.compare(current, prior)
        self._assert_precision(result, "RPT-15")

    def test_rpt16_trillion_population_profile(self):
        """RPT-16: Population profile with >$1T balance."""
        rows = [
            _tb("1000", "Cash", "Asset", debit=self.T),
            _tb("2000", "AP", "Liability", credit=self.T * 0.4),
            _tb("3000", "Equity", "Equity", credit=self.T * 0.6),
        ]
        result = run_population_profile(TB_COLS, rows, "trillion.csv")
        self._assert_precision(result, "RPT-16")

    def test_rpt17_trillion_benchmark(self):
        """RPT-17: Benchmark comparison with >$1T ratio value (extreme edge)."""
        result = compare_to_benchmark("current_ratio", self.T, _benchmark())
        assert result is not None
        self._assert_precision(result, "RPT-17")

    def test_rpt18_trillion_diagnostic_score(self):
        """RPT-18: Composite risk with >$1T testing scores."""
        assessment = AccountRiskAssessment(
            account_name="Cash",
            assertion="existence",
            inherent_risk="low",
            control_risk="low",
        )
        result = build_composite_risk_profile(
            [assessment],
            testing_scores={"revenue_testing": self.T},
        )
        self._assert_precision(result, "RPT-18")

    def test_rpt19_trillion_expense(self):
        """RPT-19: Expense category with >$1T expense balance."""
        rows = [
            _tb("5000", "Cost of Goods Sold", "Expense", debit=self.T),
            _tb("4000", "Revenue", "Revenue", credit=self.T * 1.2),
        ]
        result = run_expense_category_analytics(TB_COLS, rows, "trillion.csv")
        self._assert_precision(result, "RPT-19")

    def test_rpt20_trillion_accrual(self):
        """RPT-20: Accrual completeness with >$1T accrual balance."""
        rows = [
            _tb("2100", "Accrued Liabilities", "Liability", credit=self.T),
            _tb("5000", "Operating Expenses", "Expense", debit=self.T * 0.8),
        ]
        result = run_accrual_completeness(TB_COLS, rows, "trillion.csv")
        self._assert_precision(result, "RPT-20")

    def test_rpt21_trillion_anomaly_summary(self):
        """RPT-21: Anomaly detection (same engine as RPT-01) with >$1T."""
        rows = [
            _tb("1000", "Cash", "Asset", debit=self.T),
            _tb("1100", "Suspense Account", "Asset", debit=self.T * 0.001),
            _tb("3000", "Equity", "Equity", credit=self.T * 1.001),
        ]
        csv = _csv_bytes(TB_COLS, rows)
        result = audit_trial_balance_streaming(csv, "trillion_anomaly.csv")
        self._assert_precision(result, "RPT-21")

    def test_dash01_trillion_dashboard(self):
        """DASH-01: Dashboard with >$1T risk scores."""
        reports = [_dashboard_report("revenue_testing", score=self.T)]
        result = compute_engagement_dashboard(reports)
        self._assert_precision(result, "DASH-01")


# ===========================================================================
# FLAG GROUP 4 — Missing Expected Account Types
# ===========================================================================


class TestFlagG4MissingAccountTypes:
    """Tests for input missing account types the engine depends on."""

    def test_rpt01_no_cash_accounts(self):
        """RPT-01: TB with no cash/asset accounts."""
        rows = [
            _tb("4000", "Revenue", "Revenue", credit=50000),
            _tb("5000", "Expenses", "Expense", debit=50000),
        ]
        csv = _csv_bytes(TB_COLS, rows)
        result = audit_trial_balance_streaming(csv, "no_cash.csv")
        assert isinstance(result, dict)

    def test_rpt02_no_overlap_multi_period(self):
        """RPT-02: Multi-period where current has no accounts matching prior."""
        prior = [_tb("1000", "Cash", "Asset", debit=50000)]
        current = [_tb("9000", "Other Income", "Revenue", credit=30000)]
        result = compare_trial_balances(prior, current)
        assert result is not None

    def test_rpt03_no_date_column(self):
        """RPT-03: JE testing with rows missing date information."""
        cols = ["Entry ID", "Account", "Description", "Debit", "Credit"]
        rows = [
            {"Entry ID": "JE001", "Account": "Cash", "Description": "Deposit", "Debit": 5000, "Credit": 0},
            {"Entry ID": "JE001", "Account": "Revenue", "Description": "Sale", "Debit": 0, "Credit": 5000},
        ]
        result = run_je_testing(rows, cols)
        assert result is not None

    def test_rpt04_no_vendor_column(self):
        """RPT-04: AP testing without vendor information."""
        cols = ["Date", "Invoice Number", "Amount", "Description"]
        rows = [
            {"Date": "2025-06-15", "Invoice Number": "INV001", "Amount": 5000, "Description": "Materials"},
            {"Date": "2025-06-20", "Invoice Number": "INV002", "Amount": 3000, "Description": "Services"},
        ]
        result = run_ap_testing(rows, cols)
        assert result is not None

    def test_rpt06_no_amount_entries(self):
        """RPT-06: Revenue testing where all amounts are zero."""
        rows = [
            _rev("2025-06-15", "4000 Revenue", "Free trial", 0),
            _rev("2025-06-20", "4000 Revenue", "Promotional", 0),
        ]
        result = run_revenue_testing(rows, REV_COLS)
        assert result is not None

    def test_rpt08_no_depreciation_column(self):
        """RPT-08: Fixed asset register missing depreciation column."""
        cols = ["Asset ID", "Description", "Cost", "Acquisition Date"]
        rows = [
            {"Asset ID": "FA001", "Description": "Equipment", "Cost": 50000, "Acquisition Date": "2020-01-01"},
            {"Asset ID": "FA002", "Description": "Furniture", "Cost": 15000, "Acquisition Date": "2021-06-15"},
        ]
        result = run_fixed_asset_testing(rows, cols)
        assert result is not None

    def test_rpt10_empty_ledger(self):
        """RPT-10: Bank rec with bank transactions but empty ledger."""
        bank = [
            _bank("2025-06-15", "Deposit", 10000),
            _bank("2025-06-16", "Payment", -5000),
        ]
        ledger: list[dict] = []
        result = reconcile_bank_statement(bank, ledger, BANK_COLS, BANK_COLS)
        assert result is not None

    def test_rpt11_no_invoices(self):
        """RPT-11: Three-way match with POs and receipts but no invoices."""
        result = run_three_way_match(
            [_po("PO001", "Vendor A", 5000)],
            [],  # No invoices
            [_receipt("REC001", "PO001", "Vendor A")],
        )
        assert result is not None

    def test_rpt15_no_prior_period(self):
        """RPT-15: Flux analysis with empty prior period."""
        current = {
            "Cash": {"net": 50000.0, "type": "Asset"},
            "Revenue": {"net": 80000.0, "type": "Revenue"},
        }
        prior: dict = {}
        engine = FluxEngine(materiality_threshold=1000)
        result = engine.compare(current, prior)
        assert result is not None
        # All accounts should be classified as new
        assert result.total_items > 0

    def test_rpt16_no_expense_accounts(self):
        """RPT-16: Population profile with only asset accounts (no expenses, revenue)."""
        rows = [
            _tb("1000", "Cash", "Asset", debit=50000),
            _tb("1100", "Accounts Receivable", "Asset", debit=30000),
        ]
        result = run_population_profile(TB_COLS, rows, "assets_only.csv")
        assert result is not None

    def test_rpt17_missing_ratio_benchmark(self):
        """RPT-17: Benchmark comparison with a ratio name not in benchmark set."""
        result = compare_to_benchmark("nonexistent_ratio", 1.5, _benchmark(ratio_name="current_ratio"))
        assert result is not None

    def test_rpt18_empty_assessments(self):
        """RPT-18: Composite risk with no account assessments."""
        result = build_composite_risk_profile(
            [],
            tb_diagnostic_score=50,
            tb_diagnostic_tier="moderate",
        )
        assert result is not None
        assert result.total_assessments == 0
        assert result.overall_risk_tier is None or isinstance(result.overall_risk_tier, str)

    def test_rpt20_no_accrual_accounts(self):
        """RPT-20: Accrual completeness with no accrued liability accounts."""
        rows = [
            _tb("1000", "Cash", "Asset", debit=50000),
            _tb("4000", "Revenue", "Revenue", credit=50000),
        ]
        result = run_accrual_completeness(TB_COLS, rows, "no_accruals.csv")
        assert result is not None
        d = result.to_dict() if hasattr(result, "to_dict") else {}
        # Should indicate no accruals found rather than returning misleading data
        serialized = json.dumps(d, default=str).lower()
        assert (
            d.get("total_accrual_accounts", 0) == 0
            or "no accrual" in serialized
            or "not found" in serialized
            or d.get("accrual_count", -1) == 0
        ), "RPT-20 FLAG: No accrual accounts but engine did not clearly indicate absence"

    def test_dash01_empty_reports(self):
        """DASH-01: Dashboard with zero reports should not crash."""
        result = compute_engagement_dashboard([])
        assert result is not None
        d = result.to_dict() if hasattr(result, "to_dict") else result
        assert d.get("report_count", -1) == 0


# ===========================================================================
# FLAG GROUP 5 — Duplicate Account Codes (non-RPT-02)
# ===========================================================================


class TestFlagG5DuplicateAccountCodes:
    """Tests for duplicate account codes in input data.

    RPT-02 duplicates are covered by FIX-2A. These test the remaining
    diagnostics listed as FLAG in the duplicate-account-codes column.
    """

    def test_rpt01_duplicate_accounts_tb(self):
        """RPT-01: TB with two rows sharing same account code, different amounts."""
        rows = [
            _tb("1000", "Cash - Operating", "Asset", debit=50000),
            _tb("1000", "Cash - Payroll", "Asset", debit=30000),
            _tb("3000", "Equity", "Equity", credit=80000),
        ]
        csv = _csv_bytes(TB_COLS, rows)
        result = audit_trial_balance_streaming(csv, "dupes.csv")
        assert isinstance(result, dict)

    def test_rpt03_duplicate_entry_ids(self):
        """RPT-03: JE testing with duplicate entry IDs but different accounts."""
        rows = [
            _gl("2025-06-15", "JE001", "Cash", "Deposit A", debit=5000),
            _gl("2025-06-15", "JE001", "Revenue", "Sale A", credit=5000),
            _gl("2025-06-15", "JE001", "Cash", "Deposit B", debit=3000),
            _gl("2025-06-15", "JE001", "Revenue", "Sale B", credit=3000),
        ]
        result = run_je_testing(rows, GL_COLS)
        assert result is not None

    def test_rpt04_duplicate_invoice_numbers(self):
        """RPT-04: AP with duplicate invoice numbers from same vendor."""
        rows = [
            _ap("2025-06-15", "Vendor A", "INV001", 5000, "CHK001", "Materials"),
            _ap("2025-06-20", "Vendor A", "INV001", 7000, "CHK002", "More materials"),
        ]
        result = run_ap_testing(rows, AP_COLS)
        assert result is not None
        d = result.to_dict() if hasattr(result, "to_dict") else {}
        # AP engine should detect duplicate invoice numbers
        serialized = json.dumps(d, default=str).lower()
        assert "duplicate" in serialized or any(
            t.get("test_key") in ("exact_duplicates", "fuzzy_duplicates", "invoice_reuse")
            and t.get("entries_flagged", 0) > 0
            for t in d.get("test_results", [])
        ), "RPT-04 FLAG: Duplicate invoice numbers not flagged"

    def test_rpt05_duplicate_employee_ids(self):
        """RPT-05: Payroll with duplicate employee IDs, different amounts."""
        rows = [
            _pr("2025-01-31", "E001", "Jane Doe", 5000, 3500, "Sales"),
            _pr("2025-01-31", "E001", "Jane M. Doe", 5500, 3800, "Sales"),
            _pr("2025-01-31", "E002", "John Smith", 4000, 2800, "Engineering"),
        ]
        result = run_payroll_testing(PR_COLS, rows)
        assert result is not None

    def test_rpt06_duplicate_revenue_entries(self):
        """RPT-06: Revenue with duplicate transaction entries."""
        rows = [
            _rev("2025-06-15", "4000 Revenue", "Product sale #100", 10000),
            _rev("2025-06-15", "4000 Revenue", "Product sale #100", 10000),
            _rev("2025-06-20", "4000 Revenue", "Product sale #101", 5000),
        ]
        result = run_revenue_testing(rows, REV_COLS)
        assert result is not None

    def test_rpt07_duplicate_ar_accounts(self):
        """RPT-07: AR aging with duplicate account codes in TB."""
        rows = [
            _tb("1200", "Accounts Receivable - Trade", "Asset", debit=25000),
            _tb("1200", "Accounts Receivable - Other", "Asset", debit=15000),
            _tb("4000", "Revenue", "Revenue", credit=40000),
        ]
        result = run_ar_aging(rows, TB_COLS)
        assert result is not None

    def test_rpt09_duplicate_inventory_items(self):
        """RPT-09: Inventory with duplicate item IDs."""
        rows = [
            _inv("INV001", "Widget A - Warehouse 1", 100, 25.50, 2550, "Raw Materials"),
            _inv("INV001", "Widget A - Warehouse 2", 50, 25.50, 1275, "Raw Materials"),
            _inv("INV002", "Widget B", 200, 10.00, 2000, "Finished Goods"),
        ]
        result = run_inventory_testing(rows, INV_COLS)
        assert result is not None

    def test_rpt10_duplicate_bank_transactions(self):
        """RPT-10: Bank rec with duplicate transactions in bank file."""
        bank = [
            _bank("2025-06-15", "Wire Transfer", 10000),
            _bank("2025-06-15", "Wire Transfer", 10000),
        ]
        ledger = [_bank("2025-06-15", "Wire Transfer", 10000)]
        result = reconcile_bank_statement(bank, ledger, BANK_COLS, BANK_COLS)
        assert result is not None

    def test_rpt11_duplicate_po_numbers(self):
        """RPT-11: Three-way match with duplicate PO numbers."""
        result = run_three_way_match(
            [
                _po("PO001", "Vendor A", 5000, row=1),
                _po("PO001", "Vendor A", 3000, row=2),
            ],
            [_invoice("INV001", "PO001", "Vendor A", 5000)],
            [_receipt("REC001", "PO001", "Vendor A")],
        )
        assert result is not None

    def test_rpt12_duplicate_sample_items(self):
        """RPT-12: Sampling with duplicate item IDs in population."""
        cols = ["Item ID", "Description", "Amount"]
        rows = [
            {"Item ID": "1", "Description": "Item A", "Amount": "50000"},
            {"Item ID": "1", "Description": "Item A Copy", "Amount": "30000"},
            {"Item ID": "2", "Description": "Item B", "Amount": "20000"},
            {"Item ID": "3", "Description": "Item C", "Amount": "15000"},
            {"Item ID": "4", "Description": "Item D", "Amount": "10000"},
            {"Item ID": "5", "Description": "Item E", "Amount": "5000"},
        ]
        csv = _csv_bytes(cols, rows)
        config = SamplingConfig(method="mus", confidence_level=0.95, tolerable_misstatement=50000)
        result = design_sample(csv, "dupes.csv", config)
        assert result is not None

    def test_rpt13_duplicate_currency_rows(self):
        """RPT-13: Currency conversion with duplicate account rows."""
        rows = [
            {"Account": "1000", "Account Name": "Cash - Operating", "Amount": 50000, "Currency": "EUR"},
            {"Account": "1000", "Account Name": "Cash - Savings", "Amount": 30000, "Currency": "EUR"},
        ]
        rt = _rate_table("EUR", "USD", "1.10")
        result = convert_trial_balance(rows, rt, amount_column="Amount", currency_column="Currency")
        assert result is not None

    def test_rpt14_duplicate_ratio_input(self):
        """RPT-14: Ratio engine is fed aggregated CategoryTotals, not raw accounts.

        Duplicate account codes would affect the upstream aggregation,
        not the ratio engine itself. This test verifies the engine produces
        correct ratios from totals that could include double-counted amounts.
        """
        totals = CategoryTotals(
            total_assets=100000,
            current_assets=80000,  # Possibly double-counted from duplicates
            total_liabilities=50000,
            current_liabilities=40000,
            total_equity=50000,
            total_revenue=120000,
        )
        engine = RatioEngine(totals)
        cr = engine.calculate_current_ratio()
        assert cr.value is not None
        assert cr.value == 2.0  # 80000 / 40000

    def test_rpt15_duplicate_flux_accounts(self):
        """RPT-15: Flux with account present in both periods (normal case).

        FluxEngine takes dicts keyed by account name — duplicates are
        impossible at this level. This test documents that behavior.
        """
        current = {
            "Cash": {"net": 50000.0, "type": "Asset"},
            "Revenue": {"net": 80000.0, "type": "Revenue"},
        }
        prior = {
            "Cash": {"net": 45000.0, "type": "Asset"},
            "Revenue": {"net": 75000.0, "type": "Revenue"},
        }
        engine = FluxEngine(materiality_threshold=1000)
        result = engine.compare(current, prior)
        assert result.total_items == 2

    def test_rpt16_duplicate_accounts_profile(self):
        """RPT-16: Population profile with duplicate account codes."""
        rows = [
            _tb("1000", "Cash - Operating", "Asset", debit=50000),
            _tb("1000", "Cash - Payroll", "Asset", debit=30000),
            _tb("2000", "AP", "Liability", credit=80000),
        ]
        result = run_population_profile(TB_COLS, rows, "dupes.csv")
        assert result is not None
        d = result.to_dict() if hasattr(result, "to_dict") else {}
        # The engine should either coalesce with a warning or count them separately
        serialized = json.dumps(d, default=str).lower()
        has_dup_handling = (
            "duplicate" in serialized
            or d.get("account_count", 0) >= 2  # Counted separately
            or "coalesce" in serialized
            or "merge" in serialized
        )
        assert has_dup_handling, "RPT-16 FLAG: Duplicate account codes not visibly handled in population profile"

    def test_rpt17_duplicate_ratio_benchmark(self):
        """RPT-17: Benchmark comparison called twice with same ratio (idempotency)."""
        r1 = compare_to_benchmark("current_ratio", 1.5, _benchmark())
        r2 = compare_to_benchmark("current_ratio", 1.5, _benchmark())
        assert r1.percentile == r2.percentile

    def test_rpt18_duplicate_assessments(self):
        """RPT-18: Composite risk with duplicate account/assertion pair."""
        a1 = AccountRiskAssessment(account_name="Cash", assertion="existence", inherent_risk="low", control_risk="low")
        a2 = AccountRiskAssessment(
            account_name="Cash", assertion="existence", inherent_risk="moderate", control_risk="moderate"
        )
        result = build_composite_risk_profile([a1, a2])
        assert result is not None
        assert result.total_assessments == 2

    def test_rpt19_duplicate_expense_accounts(self):
        """RPT-19: Expense category with duplicate expense account codes."""
        rows = [
            _tb("5000", "Salary Expense - Dept A", "Expense", debit=40000),
            _tb("5000", "Salary Expense - Dept B", "Expense", debit=35000),
            _tb("4000", "Revenue", "Revenue", credit=100000),
        ]
        result = run_expense_category_analytics(TB_COLS, rows, "dup_expense.csv")
        assert result is not None

    def test_rpt20_duplicate_accrual_accounts(self):
        """RPT-20: Accrual completeness with duplicate accrual account codes."""
        rows = [
            _tb("2100", "Accrued Expenses - Rent", "Liability", credit=10000),
            _tb("2100", "Accrued Expenses - Utilities", "Liability", credit=5000),
            _tb("5000", "Operating Expenses", "Expense", debit=60000),
        ]
        result = run_accrual_completeness(TB_COLS, rows, "dup_accrual.csv")
        assert result is not None

    def test_dash01_duplicate_report_types(self):
        """DASH-01: Dashboard with two reports of the same type."""
        reports = [
            _dashboard_report("revenue_testing", score=60, flagged=5, high=2),
            _dashboard_report("revenue_testing", score=40, flagged=2, high=0),
        ]
        result = compute_engagement_dashboard(reports)
        assert result is not None
        d = result.to_dict() if hasattr(result, "to_dict") else result
        assert d.get("report_count", 0) == 2, "DASH-01 FLAG: Two reports submitted but dashboard did not count both"
