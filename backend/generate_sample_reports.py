"""
Generate Sample PDF Reports for All Paciolus Tools
===================================================
Creates realistic fictional data and produces PDFs for every memo generator.

Usage: python generate_sample_reports.py
Output: ../sample-reports/*.pdf
"""

import os
import sys

# Ensure backend is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample-reports")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Shared fictional company metadata
CLIENT = "Meridian Capital Group, LLC"
PERIOD = "FY 2025 (January 1 – December 31, 2025)"
PREPARED = "Sarah M. Chen, CPA"
REVIEWED = "James R. Whitfield, CPA, CIA"
WP_DATE = "2026-02-15"
ERP_NOTE = "Exported from Meridian ERP (QuickBooks Enterprise) on Jan 15, 2026"


def save_pdf(name: str, pdf_bytes: bytes) -> None:
    path = os.path.join(OUTPUT_DIR, name)
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    print(f"  [OK] {name} ({len(pdf_bytes):,} bytes)")


# ─────────────────────────────────────────────────────────────────────
# 1. TRIAL BALANCE DIAGNOSTIC REPORT
# ─────────────────────────────────────────────────────────────────────
def gen_tb_diagnostic():
    from pdf_generator import generate_audit_report

    audit_result = {
        "status": "success",
        "balanced": True,
        "total_debits": 12_847_392.50,
        "total_credits": 12_847_392.50,
        "difference": 0.00,
        "row_count": 247,
        "materiality_threshold": 50_000.00,
        "material_count": 3,
        "immaterial_count": 5,
        "risk_summary": {
            "total_anomalies": 8,
            "high_severity": 3,
            "low_severity": 5,
            "anomaly_types": {
                "abnormal_balance": 2,
                "suspense_account": 1,
                "concentration_risk": 3,
                "rounding_anomaly": 2,
            },
        },
        "abnormal_balances": [
            {
                "account": "Accounts Receivable — Trade",
                "type": "Asset",
                "issue": "Credit balance of $23,400 — expected debit for trade receivable",
                "amount": -23_400.00,
                "debit": 0.00,
                "credit": 23_400.00,
                "materiality": "immaterial",
                "category": "Current Assets",
                "confidence": 0.92,
                "anomaly_type": "abnormal_balance",
                "severity": "medium",
            },
            {
                "account": "Suspense — Clearing Account",
                "type": "Other",
                "issue": "Suspense account with uncleared balance at period end",
                "amount": 67_850.00,
                "debit": 67_850.00,
                "credit": 0.00,
                "materiality": "material",
                "category": "Other",
                "confidence": 0.98,
                "anomaly_type": "suspense_account",
                "severity": "high",
            },
            {
                "account": "Revenue — Consulting Services",
                "type": "Revenue",
                "issue": "Single account represents 62% of total revenue — concentration risk",
                "amount": 4_250_000.00,
                "debit": 0.00,
                "credit": 4_250_000.00,
                "materiality": "material",
                "category": "Revenue",
                "confidence": 0.88,
                "anomaly_type": "concentration_risk",
                "severity": "high",
            },
            {
                "account": "Office Supplies",
                "type": "Expense",
                "issue": "Multiple round-number transactions ($5,000.00 exactly) — 8 occurrences",
                "amount": 40_000.00,
                "debit": 40_000.00,
                "credit": 0.00,
                "materiality": "immaterial",
                "category": "Operating Expenses",
                "confidence": 0.75,
                "anomaly_type": "rounding_anomaly",
                "severity": "low",
            },
            {
                "account": "Prepaid Insurance",
                "type": "Asset",
                "issue": "Credit balance of $1,200 — expected debit for prepaid",
                "amount": -1_200.00,
                "debit": 0.00,
                "credit": 1_200.00,
                "materiality": "immaterial",
                "category": "Current Assets",
                "confidence": 0.90,
                "anomaly_type": "abnormal_balance",
                "severity": "low",
            },
            {
                "account": "Cost of Goods Sold",
                "type": "Expense",
                "issue": "Account represents 45% of total expenses — concentration risk",
                "amount": 2_890_000.00,
                "debit": 2_890_000.00,
                "credit": 0.00,
                "materiality": "material",
                "category": "Cost of Goods Sold",
                "confidence": 0.82,
                "anomaly_type": "concentration_risk",
                "severity": "high",
            },
            {
                "account": "Advertising Expense",
                "type": "Expense",
                "issue": "Round-dollar amount ($100,000.00) — estimate or manipulation indicator",
                "amount": 100_000.00,
                "debit": 100_000.00,
                "credit": 0.00,
                "materiality": "immaterial",
                "category": "Operating Expenses",
                "confidence": 0.70,
                "anomaly_type": "rounding_anomaly",
                "severity": "low",
            },
            {
                "account": "Intercompany Receivable",
                "type": "Asset",
                "issue": "Single counterparty concentration — 100% of intercompany balance",
                "amount": 325_000.00,
                "debit": 325_000.00,
                "credit": 0.00,
                "materiality": "immaterial",
                "category": "Current Assets",
                "confidence": 0.85,
                "anomaly_type": "concentration_risk",
                "severity": "low",
                # Change 6: Cross-reference to currency memo
                "cross_reference_note": (
                    "Note: Unconverted intercompany balances were also identified in the "
                    "Multi-Currency Conversion memo (Ref: PAC-2026-0215-042). These findings "
                    "may relate to the same counterparty. Cross-reference recommended."
                ),
            },
        ],
        # Change 5: Category totals for Population Composition table
        "category_totals": {
            "total_assets": 4_892_000.00,
            "current_assets": 3_217_000.00,
            "inventory": 456_000.00,
            "total_liabilities": 3_180_392.50,
            "current_liabilities": 1_890_000.00,
            "total_equity": 2_524_000.00,
            "total_revenue": 6_850_000.00,
            "cost_of_goods_sold": 2_890_000.00,
            "total_expenses": 5_401_000.00,
        },
        "population_profile": {
            "account_count": 247,
            "section_density": [
                {"section_label": "Current Assets", "account_count": 42, "section_balance": 3_217_000.00},
                {"section_label": "Non-Current Assets", "account_count": 18, "section_balance": 1_675_000.00},
                {"section_label": "Current Liabilities", "account_count": 35, "section_balance": 1_890_000.00},
                {"section_label": "Non-Current Liabilities", "account_count": 12, "section_balance": 1_290_392.50},
                {"section_label": "Equity", "account_count": 8, "section_balance": 2_524_000.00},
                {"section_label": "Revenue", "account_count": 22, "section_balance": 6_850_000.00},
                {"section_label": "Cost of Sales", "account_count": 15, "section_balance": 2_890_000.00},
                {"section_label": "Operating Expenses", "account_count": 85, "section_balance": 2_511_000.00},
                {"section_label": "Other Income/Expense", "account_count": 10, "section_balance": 289_000.00},
            ],
        },
    }

    pdf = generate_audit_report(
        audit_result,
        "meridian_tb_fy2025.csv",
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
    )
    save_pdf("01_trial_balance_diagnostic.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 2. FINANCIAL STATEMENTS
# ─────────────────────────────────────────────────────────────────────
def gen_financial_statements():
    from financial_statement_builder import (
        CashFlowLineItem,
        CashFlowSection,
        CashFlowStatement,
        FinancialStatements,
        StatementLineItem,
    )
    from pdf_generator import generate_financial_statements_pdf

    bs = [
        StatementLineItem("ASSETS", 0, indent_level=0),
        StatementLineItem("Current Assets", 0, indent_level=0),
        StatementLineItem("Cash and Cash Equivalents", 1_245_000.00, indent_level=1, lead_sheet_ref="A"),
        StatementLineItem("Accounts Receivable", 892_000.00, indent_level=1, lead_sheet_ref="B"),
        StatementLineItem("Inventory", 456_000.00, indent_level=1, lead_sheet_ref="C"),
        StatementLineItem("Prepaid Expenses", 78_000.00, indent_level=1, lead_sheet_ref="D"),
        StatementLineItem("Total Current Assets", 2_671_000.00, is_subtotal=True),
        StatementLineItem("Non-Current Assets", 0, indent_level=0),
        StatementLineItem("Property, Plant & Equipment", 3_420_000.00, indent_level=1, lead_sheet_ref="E"),
        StatementLineItem("Accumulated Depreciation", -1_180_000.00, indent_level=1, lead_sheet_ref="E"),
        StatementLineItem("Intangible Assets", 250_000.00, indent_level=1, lead_sheet_ref="F"),
        StatementLineItem("Total Non-Current Assets", 2_490_000.00, is_subtotal=True),
        StatementLineItem("TOTAL ASSETS", 5_161_000.00, is_total=True),
        StatementLineItem("LIABILITIES AND EQUITY", 0, indent_level=0),
        StatementLineItem("Current Liabilities", 0, indent_level=0),
        StatementLineItem("Accounts Payable", 634_000.00, indent_level=1, lead_sheet_ref="G"),
        StatementLineItem("Accrued Expenses", 289_000.00, indent_level=1, lead_sheet_ref="H"),
        StatementLineItem("Current Portion of Long-Term Debt", 120_000.00, indent_level=1, lead_sheet_ref="I"),
        StatementLineItem("Total Current Liabilities", 1_043_000.00, is_subtotal=True),
        StatementLineItem("Non-Current Liabilities", 0, indent_level=0),
        StatementLineItem("Long-Term Debt", 1_500_000.00, indent_level=1, lead_sheet_ref="J"),
        StatementLineItem("Deferred Tax Liability", 98_000.00, indent_level=1, lead_sheet_ref="K"),
        StatementLineItem("Total Non-Current Liabilities", 1_598_000.00, is_subtotal=True),
        StatementLineItem("TOTAL LIABILITIES", 2_641_000.00, is_total=True),
        StatementLineItem("Equity", 0, indent_level=0),
        StatementLineItem("Common Stock", 500_000.00, indent_level=1, lead_sheet_ref="L"),
        StatementLineItem("Retained Earnings", 2_020_000.00, indent_level=1, lead_sheet_ref="M"),
        StatementLineItem("TOTAL EQUITY", 2_520_000.00, is_total=True),
        StatementLineItem("TOTAL LIABILITIES AND EQUITY", 5_161_000.00, is_total=True),
    ]

    inc = [
        StatementLineItem("Revenue", 6_850_000.00, indent_level=1, lead_sheet_ref="N"),
        StatementLineItem("Cost of Goods Sold", 2_890_000.00, indent_level=1, lead_sheet_ref="O"),
        StatementLineItem("GROSS PROFIT", 3_960_000.00, is_subtotal=True),
        StatementLineItem("Salaries & Wages", 1_420_000.00, indent_level=1),
        StatementLineItem("Rent Expense", 360_000.00, indent_level=1),
        StatementLineItem("Depreciation Expense", 285_000.00, indent_level=1),
        StatementLineItem("Marketing & Advertising", 195_000.00, indent_level=1),
        StatementLineItem("Insurance Expense", 72_000.00, indent_level=1),
        StatementLineItem("Office & Supplies", 48_000.00, indent_level=1),
        StatementLineItem("Utilities", 36_000.00, indent_level=1),
        StatementLineItem("Professional Fees", 84_000.00, indent_level=1),
        StatementLineItem("TOTAL OPERATING EXPENSES", 2_500_000.00, is_subtotal=True),
        StatementLineItem("OPERATING INCOME", 1_460_000.00, is_subtotal=True),
        StatementLineItem("Interest Expense", 92_000.00, indent_level=1),
        StatementLineItem("Other Income", 15_000.00, indent_level=1),
        StatementLineItem("INCOME BEFORE TAX", 1_383_000.00, is_subtotal=True),
        StatementLineItem("Income Tax Expense", 345_750.00, indent_level=1),
        StatementLineItem("NET INCOME", 1_037_250.00, is_total=True),
    ]

    cf = CashFlowStatement(
        operating=CashFlowSection(
            label="Cash Flows from Operating Activities",
            items=[
                CashFlowLineItem("Net Income", 1_037_250.00),
                CashFlowLineItem("Depreciation & Amortization", 285_000.00),
                CashFlowLineItem("Increase in Accounts Receivable", -142_000.00),
                CashFlowLineItem("Decrease in Inventory", 38_000.00),
                CashFlowLineItem("Increase in Accounts Payable", 67_000.00),
                CashFlowLineItem("Increase in Accrued Expenses", 23_000.00),
            ],
            subtotal=1_308_250.00,
        ),
        investing=CashFlowSection(
            label="Cash Flows from Investing Activities",
            items=[
                CashFlowLineItem("Purchase of Equipment", -420_000.00),
                CashFlowLineItem("Purchase of Intangible Assets", -50_000.00),
            ],
            subtotal=-470_000.00,
        ),
        financing=CashFlowSection(
            label="Cash Flows from Financing Activities",
            items=[
                CashFlowLineItem("Repayment of Long-Term Debt", -120_000.00),
                CashFlowLineItem("Dividends Paid", -250_000.00),
            ],
            subtotal=-370_000.00,
        ),
        net_change=468_250.00,
        beginning_cash=776_750.00,
        ending_cash=1_245_000.00,
        is_reconciled=True,
        has_prior_period=True,
    )

    statements = FinancialStatements(
        balance_sheet=bs,
        income_statement=inc,
        total_assets=5_161_000.00,
        total_liabilities=2_641_000.00,
        total_equity=2_520_000.00,
        is_balanced=True,
        balance_difference=0.00,
        total_revenue=6_850_000.00,
        gross_profit=3_960_000.00,
        operating_income=1_460_000.00,
        net_income=1_037_250.00,
        depreciation_amount=285_000.00,
        interest_expense=92_000.00,
        cash_flow_statement=cf,
        entity_name=CLIENT,
        period_end="December 31, 2025",
    )

    pdf = generate_financial_statements_pdf(
        statements,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
    )
    save_pdf("02_financial_statements.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# Helper: Standard testing result dict
# ─────────────────────────────────────────────────────────────────────
def _make_testing_result(
    total_entries: int,
    tests: list[dict],
    score: float,
    risk_tier: str,
    top_findings: list = None,
    benford_result: dict = None,
    column_detection: dict = None,
):
    total_flagged = sum(t["entries_flagged"] for t in tests)
    high = sum(1 for t in tests if t["severity"] == "high" and t["entries_flagged"] > 0)
    medium = sum(1 for t in tests if t["severity"] == "medium" and t["entries_flagged"] > 0)
    low = sum(1 for t in tests if t["severity"] == "low" and t["entries_flagged"] > 0)

    result = {
        "composite_score": {
            "score": score,
            "risk_tier": risk_tier,
            "total_entries": total_entries,
            "tests_run": len(tests),
            "total_flagged": total_flagged,
            "flag_rate": total_flagged / total_entries if total_entries else 0,
            "flags_by_severity": {
                "high": sum(t["entries_flagged"] for t in tests if t["severity"] == "high"),
                "medium": sum(t["entries_flagged"] for t in tests if t["severity"] == "medium"),
                "low": sum(t["entries_flagged"] for t in tests if t["severity"] == "low"),
            },
            "top_findings": top_findings or [],
        },
        "data_quality": {
            "completeness_score": 94.2,
            "null_fields": 12,
            "date_parse_errors": 0,
            "amount_parse_errors": 3,
        },
        "test_results": tests,
        "column_detection": column_detection or {"overall_confidence": 0.92},
    }
    if benford_result:
        result["benford_result"] = benford_result
    return result


def _test(name, key, tier, flagged, rate, severity, status="warning", flagged_entries=None):
    result = {
        "test_name": name,
        "test_key": key,
        "test_tier": tier,
        "status": "passed" if flagged == 0 else status,
        "entries_flagged": flagged,
        "flag_rate": rate,
        "severity": severity,
        "description": "",
    }
    if flagged_entries is not None:
        result["flagged_entries"] = flagged_entries
    return result


# ─────────────────────────────────────────────────────────────────────
# 3. JOURNAL ENTRY TESTING MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_je_testing():
    from je_testing_memo_generator import generate_je_testing_memo

    # Sample flagged entries for high-severity tests (BUG-02 fix)
    unbalanced_flagged = [
        {
            "entry": {
                "entry_id": "JE-2025-0847",
                "entry_date": "2025-03-15",
                "account": "4100 — Revenue",
                "debit": 125000.00,
                "credit": 124999.50,
                "description": "Q1 revenue accrual adjustment",
            },
            "details": {"difference": 0.50},
        },
        {
            "entry": {
                "entry_id": "JE-2025-1203",
                "entry_date": "2025-06-30",
                "account": "5200 — COGS",
                "debit": 87432.00,
                "credit": 87430.00,
                "description": "Inventory write-down reclassification",
            },
            "details": {"difference": 2.00},
        },
        {
            "entry": {
                "entry_id": "JE-2025-1891",
                "entry_date": "2025-11-28",
                "account": "6300 — Consulting",
                "debit": 45000.00,
                "credit": 44850.00,
                "description": "Year-end consulting accrual",
            },
            "details": {"difference": 150.00},
        },
    ]
    holiday_flagged = [
        {
            "entry": {
                "entry_id": "JE-2025-1756",
                "entry_date": "2025-11-27",
                "account": "5100 — Salaries",
                "debit": 34200.00,
                "credit": 0,
                "description": "Payroll correction",
                "posted_by": "M. Chen",
            },
            "details": {"holiday": "Thanksgiving Day"},
        },
        {
            "entry": {
                "entry_id": "JE-2025-1757",
                "entry_date": "2025-11-27",
                "account": "2100 — AP",
                "debit": 0,
                "credit": 12500.00,
                "description": "Vendor payment reversal",
                "posted_by": "M. Chen",
            },
            "details": {"holiday": "Thanksgiving Day"},
        },
        {
            "entry": {
                "entry_id": "JE-2025-1923",
                "entry_date": "2025-12-25",
                "account": "4100 — Revenue",
                "debit": 0,
                "credit": 78900.00,
                "description": "Revenue recognition adjustment",
                "posted_by": "S. Patel",
            },
            "details": {"holiday": "Christmas Day"},
        },
        {
            "entry": {
                "entry_id": "JE-2025-1924",
                "entry_date": "2025-12-25",
                "account": "1200 — AR",
                "debit": 78900.00,
                "credit": 0,
                "description": "AR reclassification",
                "posted_by": "S. Patel",
            },
            "details": {"holiday": "Christmas Day"},
        },
    ]

    tests = [
        _test(
            "Unbalanced Entries",
            "unbalanced_entries",
            "structural",
            3,
            0.002,
            "high",
            flagged_entries=unbalanced_flagged,
        ),
        _test("Missing Fields", "missing_fields", "structural", 12, 0.008, "medium"),
        _test("Duplicate Entries", "duplicate_entries", "structural", 7, 0.005, "medium"),
        _test("Round Dollar Amounts", "round_dollar_amounts", "statistical", 45, 0.030, "low"),
        _test("Unusual Amounts", "unusual_amounts", "statistical", 8, 0.005, "medium"),
        _test("Benford's Law", "benford_law", "statistical", 0, 0.000, "low"),
        _test("Weekend Postings", "weekend_postings", "structural", 23, 0.015, "low"),
        _test("Month-End Clustering", "month_end_clustering", "statistical", 156, 0.104, "medium"),
        _test("Holiday Postings", "holiday_postings", "advanced", 4, 0.003, "high", flagged_entries=holiday_flagged),
    ]

    benford = {
        "passed_prechecks": True,
        "eligible_count": 1_420,
        "mad": 0.00412,
        "conformity_level": "close_conformity",
        "expected_distribution": {
            "1": 0.30103,
            "2": 0.17609,
            "3": 0.12494,
            "4": 0.09691,
            "5": 0.07918,
            "6": 0.06695,
            "7": 0.05799,
            "8": 0.05115,
            "9": 0.04576,
        },
        "actual_distribution": {
            "1": 0.2985,
            "2": 0.1792,
            "3": 0.1248,
            "4": 0.0978,
            "5": 0.0801,
            "6": 0.0672,
            "7": 0.0589,
            "8": 0.0518,
            "9": 0.0417,
        },
        "deviation_by_digit": {
            "1": -0.0025,
            "2": 0.0022,
            "3": -0.0003,
            "4": 0.0009,
            "5": 0.0011,
            "6": -0.0003,
            "7": 0.0006,
            "8": -0.0013,
            "9": -0.0004,
        },
    }

    result = _make_testing_result(
        total_entries=1_500,
        tests=tests,
        score=18.4,
        risk_tier="moderate",
        top_findings=[
            "3 unbalanced journal entries detected — debits do not equal credits",
            "4 journal entries posted on US federal holidays (Thanksgiving, Christmas)",
            "156 entries clustered in last 3 days of month (10.4% flag rate)",
            "12 entries with missing critical fields (account or date)",
        ],
        benford_result=benford,
    )

    pdf = generate_je_testing_memo(
        result,
        "meridian_gl_fy2025.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="General Ledger Detail — FY2025 Export",
        source_context_note=ERP_NOTE,
    )
    save_pdf("03_journal_entry_testing.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 4. AP PAYMENT TESTING MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_ap_testing():
    from ap_testing_memo_generator import generate_ap_testing_memo

    # Flagged entries for high-severity tests
    dup_flagged = [
        {
            "entry": {
                "vendor_name": "Apex Office Solutions",
                "invoice_number": "INV-8834",
                "payment_date": "2025-03-15",
                "amount": 7100,
                "check_number": "10234",
            },
            "details": {"payment_1_date": "2025-03-15", "payment_2_date": "2025-03-22"},
        },
        {
            "entry": {
                "vendor_name": "Apex Office Solutions",
                "invoice_number": "INV-8834",
                "payment_date": "2025-03-22",
                "amount": 7100,
                "check_number": "10291",
            },
            "details": {"payment_1_date": "2025-03-15", "payment_2_date": "2025-03-22"},
        },
    ]

    prepay_flagged = [
        {
            "entry": {
                "vendor_name": "Lakeside Catering",
                "invoice_number": "LC-2201",
                "invoice_date": "2025-06-10",
                "payment_date": "2025-05-28",
                "amount": 4500,
            },
            "details": {"days_early": 13},
        },
        {
            "entry": {
                "vendor_name": "QuickShip Logistics",
                "invoice_number": "QS-0477",
                "invoice_date": "2025-08-01",
                "payment_date": "2025-07-15",
                "amount": 12800,
            },
            "details": {"days_early": 17},
        },
        {
            "entry": {
                "vendor_name": "DataCore Systems",
                "invoice_number": "DC-9910",
                "invoice_date": "2025-11-05",
                "payment_date": "2025-10-22",
                "amount": 3200,
            },
            "details": {"days_early": 14},
        },
    ]

    reuse_flagged = [
        {
            "entry": {"invoice_number": "INV-5500"},
            "details": {
                "vendor_1_name": "Metro Supplies",
                "vendor_1_amount": 2340,
                "vendor_1_date": "2025-04-12",
                "vendor_2_name": "Metro Supply Co.",
                "vendor_2_amount": 2340,
                "vendor_2_date": "2025-07-19",
            },
        },
    ]

    threshold_flagged = [
        {
            "entry": {"vendor_name": "Apex Office Solutions", "payment_date": "2025-09-30", "amount": 9950},
            "details": {"threshold_amount": 10000, "amount_below_threshold": 50},
        },
        {
            "entry": {"vendor_name": "Apex Office Solutions", "payment_date": "2025-09-30", "amount": 9875},
            "details": {"threshold_amount": 10000, "amount_below_threshold": 125},
        },
        {
            "entry": {"vendor_name": "DataCore Systems", "payment_date": "2025-06-15", "amount": 9990},
            "details": {"threshold_amount": 10000, "amount_below_threshold": 10},
        },
        {
            "entry": {"vendor_name": "Lakeside Catering", "payment_date": "2025-12-20", "amount": 9800},
            "details": {"threshold_amount": 10000, "amount_below_threshold": 200},
        },
        {
            "entry": {"vendor_name": "QuickShip Logistics", "payment_date": "2025-12-20", "amount": 9925},
            "details": {"threshold_amount": 10000, "amount_below_threshold": 75},
        },
    ]

    vendor_var_flagged = [
        {
            "entry": {},
            "details": {
                "name_a": "Metro Supplies",
                "name_b": "Metro Supply Co.",
                "similarity": 0.91,
                "total_paid_a": 48200,
                "total_paid_b": 22100,
            },
        },
        {
            "entry": {},
            "details": {
                "name_a": "Metro Supply Co.",
                "name_b": "Metro Supplies",
                "similarity": 0.91,
                "total_paid_a": 22100,
                "total_paid_b": 48200,
            },
        },
        {
            "entry": {},
            "details": {
                "name_a": "Apex Office Solutions",
                "name_b": "Apex Office Soln.",
                "similarity": 0.87,
                "total_paid_a": 61500,
                "total_paid_b": 5400,
            },
        },
        {
            "entry": {},
            "details": {
                "name_a": "Apex Office Soln.",
                "name_b": "Apex Office Solutions",
                "similarity": 0.87,
                "total_paid_a": 5400,
                "total_paid_b": 61500,
            },
        },
        {
            "entry": {},
            "details": {
                "name_a": "DataCore Systems",
                "name_b": "Data Core Sys",
                "similarity": 0.82,
                "total_paid_a": 34600,
                "total_paid_b": 8900,
            },
        },
        {
            "entry": {},
            "details": {
                "name_a": "Data Core Sys",
                "name_b": "DataCore Systems",
                "similarity": 0.82,
                "total_paid_a": 8900,
                "total_paid_b": 34600,
            },
        },
        {
            "entry": {},
            "details": {
                "name_a": "QuickShip Logistics",
                "name_b": "Quick Ship Log.",
                "similarity": 0.79,
                "total_paid_a": 29300,
                "total_paid_b": 3100,
            },
        },
    ]

    tests = [
        _test(
            "Exact Duplicate Payments",
            "exact_duplicate_payments",
            "structural",
            2,
            0.003,
            "high",
            flagged_entries=dup_flagged,
        ),
        _test("Missing Critical Fields", "missing_critical_fields", "structural", 5, 0.007, "medium"),
        _test("Check Number Gaps", "check_number_gaps", "structural", 8, 0.011, "low"),
        _test("Round Dollar Amounts", "round_dollar_amounts", "statistical", 34, 0.048, "low"),
        _test(
            "Payment Before Invoice",
            "payment_before_invoice",
            "structural",
            3,
            0.004,
            "high",
            flagged_entries=prepay_flagged,
        ),
        _test("Fuzzy Duplicate Payments", "fuzzy_duplicate_payments", "statistical", 6, 0.008, "medium"),
        _test(
            "Invoice Number Reuse",
            "invoice_number_reuse",
            "structural",
            1,
            0.001,
            "high",
            flagged_entries=reuse_flagged,
        ),
        _test("Unusual Payment Amounts", "unusual_payment_amounts", "statistical", 4, 0.006, "medium"),
        _test("Weekend Payments", "weekend_payments", "structural", 11, 0.015, "low"),
        _test("High-Frequency Vendors", "high_frequency_vendors", "statistical", 2, 0.003, "medium"),
        _test(
            "Vendor Name Variations",
            "vendor_name_variations",
            "statistical",
            7,
            0.010,
            "medium",
            flagged_entries=vendor_var_flagged,
        ),
        _test(
            "Just-Below-Threshold",
            "just_below_threshold",
            "advanced",
            5,
            0.007,
            "high",
            flagged_entries=threshold_flagged,
        ),
        _test("Suspicious Descriptions", "suspicious_descriptions", "advanced", 3, 0.004, "medium"),
    ]

    result = _make_testing_result(
        total_entries=710,
        tests=tests,
        score=24.7,
        risk_tier="moderate",
        top_findings=[
            "2 exact duplicate payments totaling $14,200 to vendor 'Apex Office Solutions'",
            "3 payments processed before invoice date — potential prepayment fraud",
            "1 invoice number reused across vendors 'Metro Supplies' and 'Metro Supply Co.'",
            "5 payments just below $10,000 approval threshold on same dates",
        ],
    )
    result["dpo_data"] = {
        "dpo": 80.1,
        "ap_balance": 634000,
        "cogs": 2890000,
    }

    pdf = generate_ap_testing_memo(
        result,
        "meridian_ap_fy2025.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="AP Payment Register — FY2025 Export",
        source_context_note=ERP_NOTE,
    )
    save_pdf("04_ap_payment_testing.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 5. PAYROLL TESTING MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_payroll_testing():
    from payroll_testing_memo_generator import generate_payroll_testing_memo

    # Flagged entries for HIGH severity tests (BUG-02: detail tables)
    pr_t1_flagged = [
        {
            "entry": {
                "employee_id": "EMP-1102",
                "employee_name": "Sarah Blake",
                "department": "Marketing",
                "pay_date": "2025-10-15",
                "gross_pay": 4850.00,
                "term_date": None,
                "bank_account": "",
            },
            "severity": "high",
            "issue": "Employee ID 'EMP-1102' has 2 different names",
            "details": {"names": ["michael torres", "sarah blake"], "entry_count": 24},
        },
    ]
    pr_t4_flagged = [
        {
            "entry": {
                "employee_id": "EMP-4421",
                "employee_name": "Robert Nguyen",
                "department": "Operations",
                "pay_date": "2025-12-15",
                "gross_pay": 4200.00,
                "term_date": "2025-11-22",
                "bank_account": "",
            },
            "severity": "high",
            "issue": "Payment 23 days after termination (2025-11-22)",
            "details": {"days_after": 23, "term_date": "2025-11-22"},
        },
        {
            "entry": {
                "employee_id": "EMP-4421",
                "employee_name": "Robert Nguyen",
                "department": "Operations",
                "pay_date": "2025-12-31",
                "gross_pay": 4200.00,
                "term_date": "2025-11-22",
                "bank_account": "",
            },
            "severity": "high",
            "issue": "Payment 39 days after termination (2025-11-22)",
            "details": {"days_after": 39, "term_date": "2025-11-22"},
        },
    ]
    pr_t9_flagged = [
        {
            "entry": {
                "employee_id": "EMP-3187",
                "employee_name": "Vacant",
                "department": "",
                "pay_date": "2025-01-15",
                "gross_pay": 3750.00,
                "term_date": None,
                "bank_account": "",
            },
            "severity": "high",
            "issue": "Ghost indicators: No department assignment; Single pay entry in period; Pay entries only in first/last month of period",
            "details": {
                "indicators": [
                    "No department assignment",
                    "Single pay entry in period",
                    "Pay entries only in first/last month of period",
                ],
                "indicator_count": 3,
                "employee_key": "emp-3187",
                "entry_count": 1,
            },
        },
    ]
    pr_t10_flagged = [
        {
            "entry": {
                "employee_id": "EMP-2901",
                "employee_name": "Lisa Chen",
                "department": "Finance",
                "pay_date": "2025-06-15",
                "gross_pay": 5100.00,
                "term_date": None,
                "bank_account": "****7743",
            },
            "severity": "high",
            "issue": "Bank account shared by 2 employees",
            "details": {
                "match_type": "bank_account",
                "shared_employees": ["lisa chen", "david chen"],
                "account_masked": "****7743",
            },
        },
        {
            "entry": {
                "employee_id": "EMP-5512",
                "employee_name": "David Chen",
                "department": "Engineering",
                "pay_date": "2025-06-15",
                "gross_pay": 6300.00,
                "term_date": None,
                "bank_account": "****7743",
            },
            "severity": "high",
            "issue": "Bank account shared by 2 employees",
            "details": {
                "match_type": "bank_account",
                "shared_employees": ["lisa chen", "david chen"],
                "account_masked": "****7743",
            },
        },
    ]

    tests = [
        _test("Duplicate Employee IDs", "PR-T1", "structural", 1, 0.002, "high", flagged_entries=pr_t1_flagged),
        _test("Missing Critical Fields", "PR-T2", "structural", 8, 0.015, "medium"),
        _test("Round Salary Amounts", "PR-T3", "statistical", 22, 0.042, "low"),
        _test("Pay After Termination", "PR-T4", "structural", 2, 0.004, "high", flagged_entries=pr_t4_flagged),
        _test("Check Number Gaps", "PR-T5", "structural", 5, 0.010, "low"),
        _test("Unusual Pay Amounts", "PR-T6", "statistical", 6, 0.012, "medium"),
        _test("Pay Frequency Anomalies", "PR-T7", "statistical", 3, 0.006, "medium"),
        _test("Benford's Law — Gross Pay", "PR-T8", "statistical", 0, 0.000, "low"),
        _test("Ghost Employee Indicators", "PR-T9", "advanced", 1, 0.002, "high", flagged_entries=pr_t9_flagged),
        _test("Duplicate Bank Accounts", "PR-T10", "advanced", 2, 0.004, "high", flagged_entries=pr_t10_flagged),
        _test("Duplicate Tax IDs", "PR-T11", "advanced", 0, 0.000, "low"),
    ]

    # Override Benford description to include MAD score (IMPROVEMENT-03)
    for t in tests:
        if t["test_key"] == "PR-T8":
            t["description"] = "First-digit distribution analysis (MAD=0.0042, close_conformity, \u03c7\u00b2=4.81)"

    result = _make_testing_result(
        total_entries=520,
        tests=tests,
        score=28.3,
        risk_tier="elevated",
        top_findings=[
            {
                "employee": "EMP-4421 (Robert Nguyen)",
                "issue": "2 payments totaling $8,400.00 after termination date (2025-11-22)",
            },
            {
                "employee": "EMP-3187 (Vacant \u2014 No Department)",
                "issue": "Ghost employee indicators: no department, single entry, boundary month",
            },
            {"employee": "EMP-2901 / EMP-5512", "issue": "Shared bank account ending in 7743"},
            {
                "employee": "EMP-1102 (Sarah Blake)",
                "issue": "Duplicate employee ID mapped to different name in Q3 vs Q4",
            },
        ],
    )

    # Enrichment data (IMPROVEMENT-01, 02, 04)
    result["payroll_register_total"] = 1_387_450.00
    result["gl_salaries_wages"] = 1_420_000.00
    result["department_summary"] = [
        {"department": "Engineering", "employee_count": 42, "total_gross_pay": 498_200.00, "pct_of_total": 35.9},
        {"department": "Operations", "employee_count": 35, "total_gross_pay": 374_400.00, "pct_of_total": 27.0},
        {"department": "Finance", "employee_count": 18, "total_gross_pay": 221_100.00, "pct_of_total": 15.9},
        {"department": "Marketing", "employee_count": 15, "total_gross_pay": 180_250.00, "pct_of_total": 13.0},
        {"department": "HR", "employee_count": 8, "total_gross_pay": 96_000.00, "pct_of_total": 6.9},
        {
            "department": "No Department / Unassigned",
            "employee_count": 2,
            "total_gross_pay": 17_500.00,
            "pct_of_total": 1.3,
        },
    ]
    result["headcount_rollforward"] = {
        "period_start": "2025-01-01",
        "period_end": "2025-12-31",
        "beginning_headcount": 112,
        "new_hires": 14,
        "terminations": 8,
        "computed_ending": 118,
        "final_period_headcount": 117,
        "variance": 1,
    }
    result["column_detection"]["has_hire_dates"] = True
    result["column_detection"]["has_term_dates"] = True

    pdf = generate_payroll_testing_memo(
        result,
        "meridian_payroll_fy2025.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Payroll Register \u2014 FY2025 Export",
        source_context_note=ERP_NOTE,
    )
    save_pdf("05_payroll_testing.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 6. REVENUE TESTING MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_revenue_testing():
    from revenue_testing_memo_generator import generate_revenue_testing_memo

    # Flagged entries for HIGH severity tests (IMPROVEMENT-01: detail tables)
    cutoff_flagged = [
        {
            "entry": {
                "date": "2025-12-31",
                "amount": -185000.00,
                "account_name": "Product Revenue",
                "account_number": "4000",
                "description": "Meridian Enterprise Q4 license",
                "reference": "RV-2025-0812",
                "posted_by": "admin",
                "row_number": 801,
            },
            "severity": "high",
            "issue": "Revenue $185,000.00 near period end (2025-12-31)",
            "details": {
                "boundary_type": "period end",
                "entry_date": "2025-12-31",
                "period_end": "2025-12-31",
                "days_from_boundary": 0,
            },
        },
        {
            "entry": {
                "date": "2025-12-30",
                "amount": -142500.00,
                "account_name": "Product Revenue",
                "account_number": "4000",
                "description": "Apex Corp annual renewal",
                "reference": "RV-2025-0808",
                "posted_by": "admin",
                "row_number": 798,
            },
            "severity": "high",
            "issue": "Revenue $142,500.00 near period end (2025-12-30)",
            "details": {
                "boundary_type": "period end",
                "entry_date": "2025-12-30",
                "period_end": "2025-12-31",
                "days_from_boundary": 1,
            },
        },
        {
            "entry": {
                "date": "2025-12-30",
                "amount": -98000.00,
                "account_name": "Service Revenue",
                "account_number": "4100",
                "description": "Year-end consulting engagement",
                "reference": "RV-2025-0809",
                "posted_by": "jsmith",
                "row_number": 799,
            },
            "severity": "high",
            "issue": "Revenue $98,000.00 near period end (2025-12-30)",
            "details": {
                "boundary_type": "period end",
                "entry_date": "2025-12-30",
                "period_end": "2025-12-31",
                "days_from_boundary": 1,
            },
        },
        {
            "entry": {
                "date": "2025-12-29",
                "amount": -76500.00,
                "account_name": "Product Revenue",
                "account_number": "4000",
                "description": "Summit Industries implementation",
                "reference": "RV-2025-0805",
                "posted_by": "admin",
                "row_number": 795,
            },
            "severity": "high",
            "issue": "Revenue $76,500.00 near period end (2025-12-29)",
            "details": {
                "boundary_type": "period end",
                "entry_date": "2025-12-29",
                "period_end": "2025-12-31",
                "days_from_boundary": 2,
            },
        },
        {
            "entry": {
                "date": "2025-12-29",
                "amount": -62000.00,
                "account_name": "Service Revenue",
                "account_number": "4100",
                "description": "Northwind Q4 support",
                "reference": "RV-2025-0806",
                "posted_by": "jsmith",
                "row_number": 796,
            },
            "severity": "medium",
            "issue": "Revenue $62,000.00 near period end (2025-12-29)",
            "details": {
                "boundary_type": "period end",
                "entry_date": "2025-12-29",
                "period_end": "2025-12-31",
                "days_from_boundary": 2,
            },
        },
        {
            "entry": {
                "date": "2025-12-29",
                "amount": -45000.00,
                "account_name": "Product Revenue",
                "account_number": "4000",
                "description": "BlueStar license upgrade",
                "reference": "RV-2025-0807",
                "posted_by": "admin",
                "row_number": 797,
            },
            "severity": "medium",
            "issue": "Revenue $45,000.00 near period end (2025-12-29)",
            "details": {
                "boundary_type": "period end",
                "entry_date": "2025-12-29",
                "period_end": "2025-12-31",
                "days_from_boundary": 2,
            },
        },
        {
            "entry": {
                "date": "2025-12-29",
                "amount": -38500.00,
                "account_name": "Product Revenue",
                "account_number": "4000",
                "description": "Cascade Partners onboarding",
                "reference": "RV-2025-0804",
                "posted_by": "admin",
                "row_number": 794,
            },
            "severity": "medium",
            "issue": "Revenue $38,500.00 near period end (2025-12-29)",
            "details": {
                "boundary_type": "period end",
                "entry_date": "2025-12-29",
                "period_end": "2025-12-31",
                "days_from_boundary": 2,
            },
        },
    ]
    recognition_flagged = [
        {
            "entry": {
                "date": "2025-11-15",
                "amount": -225000.00,
                "account_name": "Product Revenue",
                "account_number": "4000",
                "description": "Platform deployment — implementation in progress",
                "reference": "RV-2025-0714",
                "posted_by": "admin",
                "row_number": 714,
            },
            "severity": "high",
            "issue": "Revenue recognized 45 days before obligation satisfaction date (2025-12-30) — risk indicator for premature recognition (ASC 606-10-25-30)",
            "details": {"delta_days": 45, "entry_date": "2025-11-15", "satisfaction_date": "2025-12-30"},
        },
        {
            "entry": {
                "date": "2025-10-01",
                "amount": -180000.00,
                "account_name": "Service Revenue",
                "account_number": "4100",
                "description": "Annual support contract — Q4 deliverables pending",
                "reference": "RV-2025-0648",
                "posted_by": "jsmith",
                "row_number": 648,
            },
            "severity": "high",
            "issue": "Revenue recognized 90 days before obligation satisfaction date (2025-12-31) — risk indicator for premature recognition (ASC 606-10-25-30)",
            "details": {"delta_days": 90, "entry_date": "2025-10-01", "satisfaction_date": "2025-12-31"},
        },
        {
            "entry": {
                "date": "2025-09-15",
                "amount": -95000.00,
                "account_name": "Product Revenue",
                "account_number": "4000",
                "description": "Custom module — delivery Dec 2025",
                "reference": "RV-2025-0589",
                "posted_by": "admin",
                "row_number": 589,
            },
            "severity": "high",
            "issue": "Revenue recognized 107 days before obligation satisfaction date (2025-12-31) — risk indicator for premature recognition (ASC 606-10-25-30)",
            "details": {"delta_days": 107, "entry_date": "2025-09-15", "satisfaction_date": "2025-12-31"},
        },
        {
            "entry": {
                "date": "2025-12-01",
                "amount": -67000.00,
                "account_name": "Service Revenue",
                "account_number": "4100",
                "description": "Training program — sessions scheduled Jan 2026",
                "reference": "RV-2025-0762",
                "posted_by": "jsmith",
                "row_number": 762,
            },
            "severity": "high",
            "issue": "Revenue recognized 31 days before obligation satisfaction date (2026-01-01) — risk indicator for premature recognition (ASC 606-10-25-30)",
            "details": {"delta_days": 31, "entry_date": "2025-12-01", "satisfaction_date": "2026-01-01"},
        },
    ]
    sign_anomalies_flagged = [
        {
            "entry": {
                "date": "2025-06-30",
                "amount": 87500.00,
                "account_name": "Product Revenue",
                "account_number": "4000",
                "description": "Revenue adjustment — reclass",
                "reference": "RV-2025-0392",
                "posted_by": "admin",
                "row_number": 392,
            },
            "severity": "high",
            "issue": "Debit balance in revenue: $87,500.00 — Product Revenue",
            "details": {"amount": 87500.00, "account": "Product Revenue"},
        },
        {
            "entry": {
                "date": "2025-09-15",
                "amount": 23000.00,
                "account_name": "Service Revenue",
                "account_number": "4100",
                "description": "Reversal — client credit",
                "reference": "RV-2025-0594",
                "posted_by": "jsmith",
                "row_number": 594,
            },
            "severity": "medium",
            "issue": "Debit balance in revenue: $23,000.00 — Service Revenue",
            "details": {"amount": 23000.00, "account": "Service Revenue"},
        },
    ]
    concentration_flagged = [
        {
            "entry": {
                "date": "2025-12-15",
                "amount": -2603000.00,
                "account_name": "Product Revenue",
                "account_number": "4000",
                "description": "Meridian Enterprise — master agreement",
                "reference": "RV-2025-0788",
                "posted_by": "admin",
                "row_number": 788,
            },
            "severity": "high",
            "issue": "Account 'meridian enterprise' represents 38.0% of total revenue ($2,603,000.00/$6,850,000.00)",
            "details": {
                "account": "meridian enterprise",
                "account_total": 2_603_000.00,
                "total_revenue": 6_850_000.00,
                "concentration_pct": 0.38,
            },
        },
    ]

    tests = [
        _test("Large Manual Entries", "large_manual_entries", "structural", 4, 0.005, "medium"),
        _test(
            "Year-End Concentration",
            "year_end_concentration",
            "structural",
            18,
            0.022,
            "medium",
            flagged_entries=[
                {
                    "entry": {
                        "date": f"2025-12-{25 + i}",
                        "amount": -(120000.0 + i * 15000),
                        "account_name": "Product Revenue",
                        "reference": f"RV-2025-08{i:02d}",
                        "posted_by": "admin",
                        "row_number": 780 + i,
                    },
                    "severity": "medium",
                    "issue": f"Revenue entry in last 7 days: ${120000 + i * 15000:,.2f}",
                    "details": {
                        "concentration_pct": 0.32,
                        "last_week_revenue": 2_192_000.00,
                        "total_revenue": 6_850_000.00,
                    },
                }
                for i in range(18)
            ],
        ),
        _test("Round Amounts", "round_revenue_amounts", "structural", 28, 0.034, "low"),
        _test(
            "Sign Anomalies", "sign_anomalies", "structural", 2, 0.002, "high", flagged_entries=sign_anomalies_flagged
        ),
        _test("Unclassified Entries", "unclassified_entries", "structural", 6, 0.007, "medium"),
        _test("Z-Score Outliers", "zscore_outliers", "statistical", 5, 0.006, "medium"),
        _test("Revenue Trend Variance", "trend_variance", "statistical", 3, 0.004, "medium"),
        _test(
            "Concentration Risk",
            "concentration_risk",
            "statistical",
            1,
            0.001,
            "high",
            flagged_entries=concentration_flagged,
        ),
        _test("Cut-Off Risk", "cutoff_risk", "statistical", 7, 0.009, "high", flagged_entries=cutoff_flagged),
        _test("Benford's Law", "benford_law", "statistical", 0, 0.000, "low"),
        _test("Duplicate Entries", "duplicate_entries", "advanced", 3, 0.004, "medium"),
        _test(
            "Contra-Revenue Anomalies",
            "contra_revenue_anomalies",
            "advanced",
            2,
            0.002,
            "medium",
            flagged_entries=[
                {
                    "entry": {
                        "date": "2025-04-15",
                        "amount": 42000.00,
                        "account_name": "Sales Returns",
                        "reference": "RV-2025-0221",
                        "posted_by": "admin",
                        "row_number": 221,
                    },
                    "severity": "medium",
                    "issue": "Contra-revenue: $42,000.00",
                    "details": {"contra_pct": 0.013, "contra_total": 89_050.00, "gross_revenue": 6_850_000.00},
                },
                {
                    "entry": {
                        "date": "2025-08-22",
                        "amount": 47050.00,
                        "account_name": "Allowances",
                        "reference": "RV-2025-0498",
                        "posted_by": "jsmith",
                        "row_number": 498,
                    },
                    "severity": "medium",
                    "issue": "Contra-revenue: $47,050.00",
                    "details": {"contra_pct": 0.013, "contra_total": 89_050.00, "gross_revenue": 6_850_000.00},
                },
            ],
        ),
        _test(
            "Recognition Timing",
            "recognition_before_satisfaction",
            "contract",
            4,
            0.005,
            "high",
            flagged_entries=recognition_flagged,
        ),
        _test("Contract Obligation Linkage", "missing_obligation_linkage", "contract", 2, 0.002, "medium"),
        _test("Modification Treatment", "modification_treatment_mismatch", "contract", 1, 0.001, "medium"),
        _test("SSP Allocation", "allocation_inconsistency", "contract", 0, 0.000, "low"),
    ]

    # Override Benford description to include MAD score (IMPROVEMENT-02)
    for t in tests:
        if t["test_key"] == "benford_law":
            t["description"] = "First-digit distribution analysis (MAD=0.0038, close_conformity, \u03c7\u00b2=5.12)"

    result = _make_testing_result(
        total_entries=820,
        tests=tests,
        score=22.1,
        risk_tier="moderate",
        top_findings=[
            "Cut-Off Risk: 7 entries flagged (0.9%) \u2014 revenue recorded within 3 days of period end (aggregate value: $647,500)",
            "Recognition Before Satisfaction: 4 entries flagged (0.5%) \u2014 ASC 606 performance obligation not satisfied (aggregate value: $567,000)",
            "Year-End Concentration: 18 entries flagged (2.2%) \u2014 December revenue clustering (aggregate value: $2,192,000)",
            "Concentration Risk: 1 entry flagged (0.1%) \u2014 single customer represents 38% of total revenue (estimated revenue: $2,603,000 based on $6,850,000 total)",
        ],
    )

    # Revenue enrichment data (IMPROVEMENT-03, IMPROVEMENT-04)
    result["total_revenue"] = 6_850_000.00
    result["contra_revenue_total"] = 89_050.00

    pdf = generate_revenue_testing_memo(
        result,
        "meridian_revenue_fy2025.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Revenue Transaction Detail \u2014 FY2025 Export",
        source_context_note=ERP_NOTE,
    )
    save_pdf("06_revenue_testing.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 7. AR AGING MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_ar_aging():
    from ar_aging_memo_generator import generate_ar_aging_memo

    tests = [
        _test("Sign Anomalies", "sign_anomalies", "structural", 3, 0.008, "medium"),
        _test("Missing Allowance", "missing_allowance", "structural", 0, 0.000, "low"),
        _test("Negative Aging Buckets", "negative_aging_buckets", "structural", 2, 0.005, "medium"),
        _test("Unreconciled Detail", "unreconciled_detail", "structural", 1, 0.003, "high"),
        _test("Aging Bucket Concentration", "aging_bucket_concentration", "statistical", 0, 0.000, "low"),
        _test("Past-Due Concentration", "past_due_concentration", "statistical", 4, 0.011, "medium"),
        _test("Allowance Adequacy Ratio", "allowance_adequacy_ratio", "statistical", 1, 0.003, "high"),
        _test("Customer Concentration", "customer_concentration", "statistical", 2, 0.005, "medium"),
        _test("DSO Trend Variance", "dso_trend_variance", "statistical", 1, 0.003, "medium"),
        _test("Roll-Forward Reconciliation", "roll_forward_reconciliation", "advanced", 0, 0.000, "low"),
        _test("Credit Limit Breaches", "credit_limit_breaches", "advanced", 3, 0.008, "high"),
    ]

    result = _make_testing_result(
        total_entries=375,
        tests=tests,
        score=19.8,
        risk_tier="moderate",
        top_findings=[
            "Allowance-to-receivable ratio of 2.1% — below industry benchmark of 3-5%",
            "3 customers exceeding credit limits (totaling $142,000 over-limit)",
            "TB-to-sub-ledger reconciling difference of $8,450",
            "4 past-due accounts representing 28% of receivables balance",
        ],
    )

    pdf = generate_ar_aging_memo(
        result,
        "meridian_ar_fy2025.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Accounts Receivable Aging Schedule — FY2025",
        source_context_note=ERP_NOTE,
    )
    save_pdf("07_ar_aging_analysis.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 8. FIXED ASSET TESTING MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_fixed_asset_testing():
    from fixed_asset_testing_memo_generator import generate_fixed_asset_testing_memo

    # Flagged entries for high-severity tests (BUG-03: detail tables)
    over_depr_flagged = [
        {
            "entry": {
                "asset_id": "FA-0142",
                "description": "HVAC System — Building A",
                "cost": 185000.00,
                "accumulated_depreciation": 212750.00,
                "acquisition_date": "2015-03-22",
                "useful_life": 15.0,
                "category": "Building Improvements",
                "net_book_value": -27750.00,
                "row_number": 42,
            },
            "test_name": "Over-Depreciation",
            "test_key": "over_depreciation",
            "test_tier": "structural",
            "severity": "high",
            "issue": "Depreciation exceeds cost by 15.0%",
            "confidence": 0.90,
            "details": {
                "cost": 185000.00,
                "accumulated_depreciation": 212750.00,
                "excess": 27750.00,
                "excess_pct": 0.15,
            },
        },
        {
            "entry": {
                "asset_id": "FA-0218",
                "description": "Warehouse Shelving Units",
                "cost": 42000.00,
                "accumulated_depreciation": 46620.00,
                "acquisition_date": "2017-08-10",
                "useful_life": 7.0,
                "category": "Equipment",
                "net_book_value": -4620.00,
                "row_number": 118,
            },
            "test_name": "Over-Depreciation",
            "test_key": "over_depreciation",
            "test_tier": "structural",
            "severity": "high",
            "issue": "Depreciation exceeds cost by 11.0%",
            "confidence": 0.90,
            "details": {"cost": 42000.00, "accumulated_depreciation": 46620.00, "excess": 4620.00, "excess_pct": 0.11},
        },
    ]

    duplicate_flagged = [
        {
            "entry": {
                "asset_id": "FA-0087",
                "description": "Dell Latitude 5540",
                "cost": 1250.00,
                "accumulated_depreciation": 625.00,
                "acquisition_date": "2023-06-15",
                "useful_life": 3.0,
                "category": "IT Equipment",
                "net_book_value": 625.00,
                "row_number": 87,
            },
            "test_name": "Duplicate Assets",
            "test_key": "duplicate_assets",
            "test_tier": "advanced",
            "severity": "high",
            "issue": "Potential duplicate: $1,250.00, 'dell latitude 5540', acquired 2023-06-15 (2 occurrences)",
            "confidence": 0.85,
            "details": {
                "duplicate_count": 2,
                "cost": 1250.00,
                "description": "dell latitude 5540",
                "acquisition_date": "2023-06-15",
            },
        },
        {
            "entry": {
                "asset_id": "FA-0088",
                "description": "Dell Latitude 5540",
                "cost": 1250.00,
                "accumulated_depreciation": 625.00,
                "acquisition_date": "2023-06-15",
                "useful_life": 3.0,
                "category": "IT Equipment",
                "net_book_value": 625.00,
                "row_number": 88,
            },
            "test_name": "Duplicate Assets",
            "test_key": "duplicate_assets",
            "test_tier": "advanced",
            "severity": "high",
            "issue": "Potential duplicate: $1,250.00, 'dell latitude 5540', acquired 2023-06-15 (2 occurrences)",
            "confidence": 0.85,
            "details": {
                "duplicate_count": 2,
                "cost": 1250.00,
                "description": "dell latitude 5540",
                "acquisition_date": "2023-06-15",
            },
        },
    ]

    negative_flagged = [
        {
            "entry": {
                "asset_id": "FA-0193",
                "description": "Server Rack — Data Center",
                "cost": -15400.00,
                "accumulated_depreciation": 0.00,
                "acquisition_date": "2024-01-18",
                "useful_life": 5.0,
                "category": "IT Equipment",
                "net_book_value": -15400.00,
                "row_number": 193,
            },
            "test_name": "Negative Values",
            "test_key": "negative_values",
            "test_tier": "structural",
            "severity": "high",
            "issue": "Negative cost: $-15,400.00",
            "confidence": 0.95,
            "details": {"cost": -15400.00, "accumulated_depreciation": 0.00},
        },
    ]

    tests = [
        _test("Fully Depreciated Still in Use", "fully_depreciated", "structural", 12, 0.048, "medium"),
        _test("Missing Required Fields", "missing_fields", "structural", 3, 0.012, "medium"),
        _test(
            "Negative Cost/Accum. Depr.",
            "negative_values",
            "structural",
            1,
            0.004,
            "high",
            flagged_entries=negative_flagged,
        ),
        _test(
            "Depreciation Exceeds Cost",
            "over_depreciation",
            "structural",
            2,
            0.008,
            "high",
            flagged_entries=over_depr_flagged,
        ),
        _test("Useful Life Outliers", "useful_life_outliers", "statistical", 5, 0.020, "medium"),
        _test("Cost Z-Score Outliers", "cost_zscore_outliers", "statistical", 3, 0.012, "medium"),
        _test("Asset Age Concentration", "age_concentration", "statistical", 0, 0.000, "low"),
        _test("Duplicate Assets", "duplicate_assets", "advanced", 2, 0.008, "high", flagged_entries=duplicate_flagged),
        _test("Residual Value Anomalies", "residual_value_anomalies", "advanced", 4, 0.016, "medium"),
        _test("Lease Asset Indicators", "lease_indicators", "advanced", 0, 0.000, "low"),
    ]

    # IMP-03: Aggregate cost of fully depreciated assets
    fully_depr_aggregate_cost = 187_500.00  # Sum of 12 fully depreciated assets' original costs

    result = _make_testing_result(
        total_entries=250,
        tests=tests,
        score=21.5,
        risk_tier="moderate",
        top_findings=[
            "2 assets with accumulated depreciation exceeding original cost",
            f"12 fully depreciated assets still in use — aggregate original cost ${fully_depr_aggregate_cost:,.2f} "
            "(net book value: $0) — potential impairment indicator",
            "2 potential duplicate assets ('Dell Latitude 5540' — same cost, same date)",
            "1 asset with negative cost value (data entry error suspected)",
        ],
    )

    # IMP-01: Roll-forward data
    result["register_total_cost"] = 3_420_000.00
    result["register_total_accum_depr"] = 1_180_000.00
    result["tb_ppe_gross"] = 3_420_000.00
    result["tb_accum_depr"] = 1_180_000.00
    result["additions"] = 420_000.00
    result["disposals"] = 0
    result["depreciation_expense"] = 285_000.00
    result["period_label"] = "FY2025"

    # IMP-04: Category summary
    result["category_summary"] = [
        {
            "category": "Building Improvements",
            "count": 28,
            "gross_cost": 1_240_000.00,
            "accum_depr": 412_000.00,
            "avg_age_years": 8.2,
        },
        {
            "category": "Equipment",
            "count": 95,
            "gross_cost": 980_000.00,
            "accum_depr": 385_000.00,
            "avg_age_years": 5.7,
        },
        {
            "category": "IT Equipment",
            "count": 72,
            "gross_cost": 540_000.00,
            "accum_depr": 298_000.00,
            "avg_age_years": 3.1,
        },
        {"category": "Furniture", "count": 38, "gross_cost": 420_000.00, "accum_depr": 62_000.00, "avg_age_years": 2.4},
        {"category": "Vehicles", "count": 17, "gross_cost": 240_000.00, "accum_depr": 23_000.00, "avg_age_years": 1.8},
    ]

    # Column detection with category
    result["column_detection"] = {
        "asset_id_column": "Asset ID",
        "cost_column": "Cost",
        "accumulated_depreciation_column": "Accum Depr",
        "category_column": "Asset Category",
        "overall_confidence": 0.95,
    }

    pdf = generate_fixed_asset_testing_memo(
        result,
        "meridian_fixed_assets_fy2025.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Fixed Asset Register — FY2025 Export",
        source_context_note=ERP_NOTE,
    )
    save_pdf("08_fixed_asset_testing.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 9. INVENTORY TESTING MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_inventory_testing():
    from inventory_testing_memo_generator import generate_inventory_testing_memo

    tests = [
        _test("Missing Required Fields", "missing_fields", "structural", 7, 0.009, "medium"),
        _test("Negative Quantities/Costs", "negative_values", "structural", 2, 0.003, "high"),
        _test("Extended Value Mismatch", "value_mismatch", "structural", 4, 0.005, "medium"),
        _test("Unit Cost Z-Score Outliers", "cost_outliers", "statistical", 6, 0.008, "medium"),
        _test("Quantity Z-Score Outliers", "qty_outliers", "statistical", 3, 0.004, "medium"),
        _test("Slow-Moving Inventory", "slow_moving", "statistical", 89, 0.116, "medium"),
        _test("Category Concentration", "category_concentration", "statistical", 1, 0.001, "low"),
        _test("Duplicate Items", "duplicate_items", "advanced", 5, 0.007, "high"),
        _test("Zero-Value Items", "zero_value", "advanced", 14, 0.018, "low"),
    ]

    result = _make_testing_result(
        total_entries=768,
        tests=tests,
        score=15.2,
        risk_tier="moderate",
        top_findings=[
            "89 items with no movement in 180+ days — potential obsolescence ($234,500 value)",
            "5 potential duplicate items (identical description + unit cost)",
            "4 items where extended value ≠ quantity × unit cost",
            "14 items with zero recorded value but positive quantity on hand",
        ],
    )

    pdf = generate_inventory_testing_memo(
        result,
        "meridian_inventory_fy2025.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Inventory Listing — FY2025 Export",
        source_context_note=ERP_NOTE,
    )
    save_pdf("09_inventory_testing.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 10. BANK RECONCILIATION MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_bank_rec():
    from bank_reconciliation_memo_generator import generate_bank_rec_memo

    # Outstanding deposit items (bank-only) with dates for aging
    outstanding_deposits = [
        {"date": "2025-12-31", "days_outstanding": 0, "description": "Wire transfer - Atlas Corp", "amount": 12500.00},
        {
            "date": "2025-12-30",
            "days_outstanding": 1,
            "description": "ACH deposit - Quarterly rebate",
            "amount": 3200.00,
        },
        {"date": "2025-12-29", "days_outstanding": 2, "description": "Check deposit #4521", "amount": 1850.00},
        {"date": "2025-12-28", "days_outstanding": 3, "description": "Wire - Pinnacle Partners", "amount": 4100.00},
        {
            "date": "2025-12-27",
            "days_outstanding": 4,
            "description": "ACH deposit - Insurance refund",
            "amount": 750.00,
        },
        {"date": "2025-12-24", "days_outstanding": 7, "description": "Check deposit #4519", "amount": 2300.00},
        {"date": "2025-12-22", "days_outstanding": 9, "description": "Wire - Meridian Sub LLC", "amount": 1450.00},
        {"date": "2025-12-20", "days_outstanding": 11, "description": "ACH deposit - Tenant rent", "amount": 3800.00},
        {"date": "2025-12-18", "days_outstanding": 13, "description": "Check deposit #4515", "amount": 920.00},
        {"date": "2025-12-15", "days_outstanding": 16, "description": "Wire - Consulting fee", "amount": 2700.00},
        {"date": "2025-12-12", "days_outstanding": 19, "description": "ACH deposit - Royalty pmt", "amount": 1600.00},
        {"date": "2025-12-10", "days_outstanding": 21, "description": "Check deposit #4510", "amount": 850.00},
        {
            "date": "2025-12-05",
            "days_outstanding": 26,
            "description": "Wire - Year-end bonus refund",
            "amount": 3100.00,
        },
        {"date": "2025-12-01", "days_outstanding": 30, "description": "ACH deposit - Service fee", "amount": 1950.00},
        {
            "date": "2025-11-25",
            "days_outstanding": 36,
            "description": "Check deposit #4501 - Overdue",
            "amount": 1200.00,
        },
        {"date": "2025-11-18", "days_outstanding": 43, "description": "Wire - Settlement proceeds", "amount": 2100.00},
        {"date": "2025-11-01", "days_outstanding": 60, "description": "ACH - Disputed refund", "amount": 800.00},
        {"date": "2025-10-15", "days_outstanding": 77, "description": "Check #4488 - Old deposit", "amount": 500.00},
    ]

    # Outstanding check items (ledger-only) with dates for aging
    outstanding_checks = [
        {
            "date": "2025-12-30",
            "days_outstanding": 1,
            "description": "Check #8901 - Office supplies",
            "amount": -1250.00,
        },
        {
            "date": "2025-12-28",
            "days_outstanding": 3,
            "description": "Check #8899 - Contractor pmt",
            "amount": -4500.00,
        },
        {"date": "2025-12-24", "days_outstanding": 7, "description": "Check #8895 - Utilities", "amount": -2100.00},
        {"date": "2025-12-20", "days_outstanding": 11, "description": "ACH pmt - Vendor A", "amount": -3400.00},
        {"date": "2025-12-15", "days_outstanding": 16, "description": "Check #8888 - Insurance", "amount": -5600.00},
        {"date": "2025-12-10", "days_outstanding": 21, "description": "ACH pmt - Payroll tax", "amount": -8200.00},
        {"date": "2025-12-01", "days_outstanding": 30, "description": "Check #8875 - Lease pmt", "amount": -3800.00},
        {"date": "2025-11-15", "days_outstanding": 46, "description": "Check #8860 - Legal fees", "amount": -2400.00},
        {"date": "2025-11-01", "days_outstanding": 60, "description": "Check #8845 - Equipment", "amount": -1900.00},
        {"date": "2025-09-15", "days_outstanding": 107, "description": "Check #8790 - Old vendor", "amount": -3200.00},
        {"date": "2025-08-20", "days_outstanding": 133, "description": "Check #8755 - Stale pmt", "amount": -1570.00},
        {"date": "2025-07-01", "days_outstanding": 183, "description": "Check #8700 - Uncashed", "amount": -1000.00},
    ]

    # 8 test results for methodology table
    test_results = [
        {
            "test_name": "Exact Match Reconciliation",
            "test_key": "exact_match",
            "test_tier": "structural",
            "entries_flagged": 0,
            "flag_rate": 0.0,
            "severity": "low",
        },
        {
            "test_name": "Bank-Only Items",
            "test_key": "bank_only_items",
            "test_tier": "structural",
            "entries_flagged": 18,
            "flag_rate": 0.048,
            "severity": "medium",
        },
        {
            "test_name": "Ledger-Only Items",
            "test_key": "ledger_only_items",
            "test_tier": "structural",
            "entries_flagged": 12,
            "flag_rate": 0.032,
            "severity": "medium",
        },
        {
            "test_name": "Stale Deposits (>10 days)",
            "test_key": "stale_deposits",
            "test_tier": "structural",
            "entries_flagged": 11,
            "flag_rate": 0.030,
            "severity": "high",
        },
        {
            "test_name": "Stale Checks (>90 days)",
            "test_key": "stale_checks",
            "test_tier": "structural",
            "entries_flagged": 3,
            "flag_rate": 0.008,
            "severity": "medium",
        },
        {
            "test_name": "NSF / Returned Items",
            "test_key": "nsf_items",
            "test_tier": "advanced",
            "entries_flagged": 0,
            "flag_rate": 0.0,
            "severity": "low",
        },
        {
            "test_name": "Interbank Transfers",
            "test_key": "interbank_transfers",
            "test_tier": "advanced",
            "entries_flagged": 0,
            "flag_rate": 0.0,
            "severity": "low",
        },
        {
            "test_name": "High Value (>Materiality)",
            "test_key": "high_value_transactions",
            "test_tier": "statistical",
            "entries_flagged": 0,
            "flag_rate": 0.0,
            "severity": "low",
        },
    ]

    # rec_tests (engine output format) — mirrors test_results for the 5 engine tests
    rec_tests = [
        {
            "test_name": "Stale Deposits (>10 days)",
            "flagged_count": 11,
            "severity": "high",
            "flagged_items": [
                {
                    "test_name": "Stale Deposits",
                    "description": "Deposit outstanding 11 days",
                    "amount": 3800.00,
                    "date": "2025-12-20",
                    "severity": "medium",
                    "details": {"age_days": 11},
                },
                {
                    "test_name": "Stale Deposits",
                    "description": "Deposit outstanding 77 days",
                    "amount": 500.00,
                    "date": "2025-10-15",
                    "severity": "high",
                    "details": {"age_days": 77},
                },
            ],
        },
        {
            "test_name": "Stale Checks (>90 days)",
            "flagged_count": 3,
            "severity": "medium",
            "flagged_items": [
                {
                    "test_name": "Stale Checks",
                    "description": "Check outstanding 107 days",
                    "amount": -3200.00,
                    "date": "2025-09-15",
                    "severity": "medium",
                    "details": {"age_days": 107},
                },
                {
                    "test_name": "Stale Checks",
                    "description": "Check outstanding 133 days",
                    "amount": -1570.00,
                    "date": "2025-08-20",
                    "severity": "medium",
                    "details": {"age_days": 133},
                },
                {
                    "test_name": "Stale Checks",
                    "description": "Check outstanding 183 days",
                    "amount": -1000.00,
                    "date": "2025-07-01",
                    "severity": "medium",
                    "details": {"age_days": 183},
                },
            ],
        },
        {"test_name": "NSF / Returned Items", "flagged_count": 0, "severity": "low", "flagged_items": []},
        {"test_name": "Interbank Transfers", "flagged_count": 0, "severity": "low", "flagged_items": []},
        {"test_name": "High Value (>Materiality)", "flagged_count": 0, "severity": "low", "flagged_items": []},
    ]

    # Composite risk score
    # Reconciling difference present (+15), outstanding > 20 (+8), stale deposits (+6),
    # stale checks (+4) = 33 => ELEVATED
    composite_score = {
        "score": 33.0,
        "risk_tier": "elevated",
        "total_flagged": 44,
        "flag_rate": 0.118,
        "flags_by_severity": {"high": 4, "medium": 37, "low": 3},
        "tests_run": 8,
        "total_entries": 372,
        "top_findings": [
            "Stale Deposits (>10 days): 11 items flagged",
            "Stale Checks (>90 days): 3 items flagged",
        ],
    }

    # Aging summary
    aging_summary = {
        "deposits_over_10_days": {"count": 11, "amount": 19520.00, "pct": 42.7},
        "deposits_over_30_days": {"count": 4, "amount": 4600.00, "pct": 10.1},
        "checks_over_30_days": {"count": 5, "amount": 10070.00, "pct": 25.9},
        "checks_over_90_days": {"count": 3, "amount": 5770.00, "pct": 14.8},
    }

    rec_result = {
        "summary": {
            "matched_count": 342,
            "bank_only_count": 18,
            "ledger_only_count": 12,
            "matched_amount": 4_782_340.00,
            "bank_only_amount": 45_670.00,
            "ledger_only_amount": 38_920.00,
            "reconciling_difference": 6_750.00,
            "total_bank": 4_828_010.00,
            "total_ledger": 4_821_260.00,
        },
        "bank_column_detection": {"overall_confidence": 0.95},
        "ledger_column_detection": {"overall_confidence": 0.91},
        "test_results": test_results,
        "composite_score": composite_score,
        "rec_tests": rec_tests,
        "outstanding_deposits": outstanding_deposits,
        "outstanding_checks": outstanding_checks,
        "aging_summary": aging_summary,
        "ending_balance_reconciliation": {
            "bank_ending_balance": 1_251_750.00,
            "gl_ending_balance": 1_245_000.00,
        },
        "ar_cross_reference": {
            "ar_reconciling_difference": 8_450.00,
            "ar_reference": "ARA-2026-0306-494",
        },
    }

    pdf = generate_bank_rec_memo(
        rec_result,
        "meridian_bank_rec_dec2025.csv",
        client_name=CLIENT,
        period_tested="December 2025",
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Bank Statement — December 2025",
        source_context_note="Statement from First National Bank, Acct #****7842",
    )
    save_pdf("10_bank_reconciliation.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 11. THREE-WAY MATCH MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_three_way_match():
    from three_way_match_memo_generator import generate_three_way_match_memo

    twm_result = {
        "summary": {
            "total_pos": 156,
            "total_invoices": 148,
            "total_receipts": 139,
            "full_match_count": 118,
            "partial_match_count": 21,
            "full_match_rate": 0.756,
            "partial_match_rate": 0.135,
            "material_variances_count": 7,
            "net_variance": 23_450.00,
            "risk_assessment": "medium",
            "total_po_amount": 1_842_000.00,
            "total_invoice_amount": 1_865_450.00,
            "total_receipt_amount": 1_831_200.00,
        },
        "variances": [
            {
                "field": "amount",
                "po_value": 45000.00,
                "invoice_value": 47500.00,
                "variance_amount": 2500.00,
                "severity": "high",
                "vendor": "Meridian Supply Co.",
                "po_number": "PO-2025-0812",
                "invoice_number": "INV-47832",
            },
            {
                "field": "amount",
                "po_value": 12000.00,
                "invoice_value": 13200.00,
                "variance_amount": 1200.00,
                "severity": "medium",
                "vendor": "Atlas Industrial",
                "po_number": "PO-2025-0834",
                "invoice_number": "INV-48201",
            },
            {
                "field": "amount",
                "po_value": 8500.00,
                "invoice_value": 9100.00,
                "variance_amount": 600.00,
                "severity": "medium",
                "vendor": "Pacific Materials Group",
                "po_number": "PO-2025-0819",
                "invoice_number": "INV-47956",
            },
            {
                "field": "amount",
                "po_value": 67000.00,
                "invoice_value": 72000.00,
                "variance_amount": 5000.00,
                "severity": "high",
                "vendor": "Consolidated Equipment Ltd.",
                "po_number": "PO-2025-0847",
                "invoice_number": "INV-48445",
            },
            {
                "field": "date",
                "po_value": "2025-10-15",
                "invoice_value": "2025-12-20",
                "variance_amount": 66,
                "severity": "high",
                "vendor": "Consolidated Equipment Ltd.",
                "po_number": "PO-2025-0847",
                "invoice_number": "INV-48445",
            },
            {
                "field": "amount",
                "po_value": 23000.00,
                "invoice_value": 24150.00,
                "variance_amount": 1150.00,
                "severity": "medium",
                "vendor": "Northern Components Inc.",
                "po_number": "PO-2025-0856",
                "invoice_number": "INV-48612",
            },
            {
                "field": "amount",
                "po_value": 5400.00,
                "invoice_value": 5800.00,
                "variance_amount": 400.00,
                "severity": "medium",
                "vendor": "Western Fabrication",
                "po_number": "PO-2025-0861",
                "invoice_number": "INV-48720",
            },
        ],
        "test_results": [
            {
                "test_key": "three_way_full_match",
                "test_name": "Three-Way Full Match",
                "test_tier": "structural",
                "entries_flagged": 38,
                "flag_rate": 0.244,
                "severity": "medium",
                "description": "",
            },
            {
                "test_key": "amount_variance",
                "test_name": "Amount Variance",
                "test_tier": "statistical",
                "entries_flagged": 6,
                "flag_rate": 0.038,
                "severity": "high",
                "description": "",
            },
            {
                "test_key": "date_variance",
                "test_name": "Date Variance",
                "test_tier": "structural",
                "entries_flagged": 1,
                "flag_rate": 0.006,
                "severity": "high",
                "description": "",
            },
            {
                "test_key": "unmatched_documents",
                "test_name": "Unmatched Documents",
                "test_tier": "structural",
                "entries_flagged": 17,
                "flag_rate": 0.109,
                "severity": "high",
                "description": "",
            },
            {
                "test_key": "duplicate_invoice_numbers",
                "test_name": "Duplicate Invoice Numbers",
                "test_tier": "advanced",
                "entries_flagged": 0,
                "flag_rate": 0.0,
                "severity": "low",
                "description": "",
            },
            {
                "test_key": "quantity_variance",
                "test_name": "Quantity Variance",
                "test_tier": "statistical",
                "entries_flagged": 0,
                "flag_rate": 0.0,
                "severity": "low",
                "description": "",
            },
        ],
        "composite_score": {
            "score": 66.0,
            "risk_tier": "high",
            "total_flagged": 62,
            "flag_rate": 0.397,
            "tests_run": 6,
            "flags_by_severity": {"high": 18, "medium": 38, "low": 6},
            "top_findings": [
                "7 Material Variances — Net Overbilling $23,450.00 (invoice amounts exceed PO-authorized amounts)",
                "75.6% Full Match Rate — Below 80% best practice threshold; systemic review of procure-to-pay controls recommended",
                "5 Unmatched Invoices — Unauthorized payment risk; do not release payment until PO authorization is confirmed",
                "66-Day Date Gap — Potential backdating on PO-2025-0847 (PO date 2025-10-15, invoice 2025-12-20)",
            ],
        },
        "config": {
            "amount_tolerance": 0.01,
            "price_variance_threshold": 0.05,
            "date_window_days": 30,
            "enable_fuzzy_matching": True,
        },
        "data_quality": {"overall_quality_score": 91.5},
        "column_detection": {
            "po": {"overall_confidence": 0.93},
            "invoice": {"overall_confidence": 0.90},
            "receipt": {"overall_confidence": 0.88},
        },
        "partial_matches": [{"id": i} for i in range(21)],
        "unmatched_pos": [
            {"po_number": "PO-2025-0901", "vendor": "Delta Logistics", "po_date": "2025-11-15", "po_amount": 12500.00},
            {"po_number": "PO-2025-0903", "vendor": "Summit Hardware", "po_date": "2025-11-18", "po_amount": 7800.00},
            {
                "po_number": "PO-2025-0907",
                "vendor": "Apex Electrical Supply",
                "po_date": "2025-11-22",
                "po_amount": 19200.00,
            },
            {
                "po_number": "PO-2025-0912",
                "vendor": "Greenfield Chemical Co.",
                "po_date": "2025-11-28",
                "po_amount": 4350.00,
            },
            {
                "po_number": "PO-2025-0918",
                "vendor": "Ironclad Fasteners",
                "po_date": "2025-12-02",
                "po_amount": 2100.00,
            },
            {
                "po_number": "PO-2025-0921",
                "vendor": "Coastal Freight Services",
                "po_date": "2025-12-05",
                "po_amount": 15600.00,
            },
            {
                "po_number": "PO-2025-0925",
                "vendor": "Pinnacle Safety Products",
                "po_date": "2025-12-08",
                "po_amount": 6900.00,
            },
            {
                "po_number": "PO-2025-0930",
                "vendor": "Redwood Timber Inc.",
                "po_date": "2025-12-12",
                "po_amount": 31400.00,
            },
            {
                "po_number": "PO-2025-0934",
                "vendor": "BlueLine Plumbing Supply",
                "po_date": "2025-12-15",
                "po_amount": 5250.00,
            },
        ],
        "unmatched_invoices": [
            {
                "invoice_number": "INV-49001",
                "vendor": "Unknown Vendor A",
                "invoice_date": "2025-12-15",
                "amount": 8750.00,
            },
            {
                "invoice_number": "INV-49015",
                "vendor": "Atlas Industrial",
                "invoice_date": "2025-12-18",
                "amount": 3200.00,
            },
            {
                "invoice_number": "INV-49023",
                "vendor": "Unknown Vendor B",
                "invoice_date": "2025-12-20",
                "amount": 14500.00,
            },
            {
                "invoice_number": "INV-49038",
                "vendor": "Meridian Supply Co.",
                "invoice_date": "2025-12-22",
                "amount": 1850.00,
            },
            {
                "invoice_number": "INV-49044",
                "vendor": "Unknown Vendor C",
                "invoice_date": "2025-12-28",
                "amount": 6100.00,
            },
        ],
        "unmatched_receipts": [
            {
                "receipt_number": "GRN-8801",
                "vendor": "Pacific Materials Group",
                "receipt_date": "2025-12-20",
                "amount": 3200.00,
            },
            {
                "receipt_number": "GRN-8815",
                "vendor": "Northern Components Inc.",
                "receipt_date": "2025-12-23",
                "amount": 9400.00,
            },
            {
                "receipt_number": "GRN-8822",
                "vendor": "Summit Hardware",
                "receipt_date": "2025-12-27",
                "amount": 2750.00,
            },
        ],
    }

    pdf = generate_three_way_match_memo(
        twm_result,
        "meridian_procurement_fy2025.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Procurement Documents — FY2025 Export",
        source_context_note="PO register, invoice log, and receiving log from Meridian ERP",
    )
    save_pdf("11_three_way_match.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 12. MULTI-PERIOD COMPARISON MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_multi_period():
    from multi_period_memo_generator import generate_multi_period_memo

    comparison_result = {
        "prior_label": "FY 2024",
        "current_label": "FY 2025",
        "budget_label": None,
        "total_accounts": 247,
        "dormant_account_count": 3,
        "movements_by_type": {
            "new_account": 4,
            "closed_account": 2,
            "sign_change": 1,
            "increase": 142,
            "decrease": 95,
            "unchanged": 3,
        },
        "movements_by_significance": {
            "material": 8,
            "significant": 22,
            "minor": 217,
        },
        "significant_movements": [
            {
                "account_name": "Revenue — Consulting Services",
                "prior_balance": 3_600_000,
                "current_balance": 4_250_000,
                "change_amount": 650_000,
                "change_percent": 18.1,
                "movement_type": "increase",
            },
            {
                "account_name": "Cost of Goods Sold",
                "prior_balance": 2_400_000,
                "current_balance": 2_890_000,
                "change_amount": 490_000,
                "change_percent": 20.4,
                "movement_type": "increase",
            },
            {
                "account_name": "Accounts Receivable — Trade",
                "prior_balance": 750_000,
                "current_balance": 892_000,
                "change_amount": 142_000,
                "change_percent": 18.9,
                "movement_type": "increase",
            },
            {
                "account_name": "Long-Term Debt",
                "prior_balance": 1_620_000,
                "current_balance": 1_500_000,
                "change_amount": -120_000,
                "change_percent": -7.4,
                "movement_type": "decrease",
            },
            {
                "account_name": "Marketing & Advertising",
                "prior_balance": 120_000,
                "current_balance": 195_000,
                "change_amount": 75_000,
                "change_percent": 62.5,
                "movement_type": "increase",
            },
            {
                "account_name": "Salaries & Wages",
                "prior_balance": 1_180_000,
                "current_balance": 1_420_000,
                "change_amount": 240_000,
                "change_percent": 20.3,
                "movement_type": "increase",
            },
            {
                "account_name": "Cash and Cash Equivalents",
                "prior_balance": 776_750,
                "current_balance": 1_245_000,
                "change_amount": 468_250,
                "change_percent": 60.3,
                "movement_type": "increase",
            },
            {
                "account_name": "Inventory",
                "prior_balance": 494_000,
                "current_balance": 456_000,
                "change_amount": -38_000,
                "change_percent": -7.7,
                "movement_type": "decrease",
            },
        ],
        "lead_sheet_summaries": [
            {
                "lead_sheet": "A",
                "lead_sheet_name": "Cash & Equivalents",
                "account_count": 3,
                "prior_total": 776_750,
                "current_total": 1_245_000,
                "net_change": 468_250,
            },
            {
                "lead_sheet": "B",
                "lead_sheet_name": "Receivables",
                "account_count": 5,
                "prior_total": 750_000,
                "current_total": 892_000,
                "net_change": 142_000,
            },
            {
                "lead_sheet": "E",
                "lead_sheet_name": "Fixed Assets",
                "account_count": 18,
                "prior_total": 2_100_000,
                "current_total": 2_240_000,
                "net_change": 140_000,
            },
            {
                "lead_sheet": "G",
                "lead_sheet_name": "Payables",
                "account_count": 8,
                "prior_total": 567_000,
                "current_total": 634_000,
                "net_change": 67_000,
            },
            {
                "lead_sheet": "N",
                "lead_sheet_name": "Revenue",
                "account_count": 6,
                "prior_total": 5_800_000,
                "current_total": 6_850_000,
                "net_change": 1_050_000,
            },
        ],
    }

    pdf = generate_multi_period_memo(
        comparison_result,
        "meridian_multi_period.csv",
        client_name=CLIENT,
        period_tested="FY 2024 vs. FY 2025",
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Trial Balance Comparison — FY2024 vs FY2025",
        source_context_note=ERP_NOTE,
    )
    save_pdf("12_multi_period_comparison.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 13. SAMPLING DESIGN MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_sampling_design():
    from sampling_memo_generator import generate_sampling_design_memo

    design_result = {
        "method": "mus",
        "confidence_level": 0.95,
        "confidence_factor": 3.0,
        "tolerable_misstatement": 75_000.00,
        "expected_misstatement": 15_000.00,
        "population_size": 1_240,
        "population_value": 4_850_000.00,
        "sampling_interval": 25_000.00,
        "calculated_sample_size": 194,
        "actual_sample_size": 207,
        "strata_summary": [
            {
                "stratum": "High Value (100%)",
                "threshold": ">$25,000",
                "count": 42,
                "total_value": 2_100_000.00,
                "sample_size": 42,
            },
            {
                "stratum": "Remainder (MUS)",
                "threshold": "≤$25,000",
                "count": 1_198,
                "total_value": 2_750_000.00,
                "sample_size": 165,
            },
        ],
    }

    pdf = generate_sampling_design_memo(
        design_result,
        "meridian_ar_subledger.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="AR Sub-Ledger — FY2025",
        source_context_note=ERP_NOTE,
    )
    save_pdf("13_sampling_design.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 14. SAMPLING EVALUATION MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_sampling_evaluation():
    from sampling_memo_generator import generate_sampling_evaluation_memo

    design_result = {
        "method": "mus",
        "confidence_level": 0.95,
        "confidence_factor": 3.0,
        "tolerable_misstatement": 75_000.00,
        "expected_misstatement": 15_000.00,
        "population_size": 1_240,
        "population_value": 4_850_000.00,
        "sampling_interval": 25_000.00,
        "calculated_sample_size": 194,
        "actual_sample_size": 207,
        "strata_summary": [
            {
                "stratum": "High Value (100%)",
                "threshold": ">$25,000",
                "count": 42,
                "total_value": 2_100_000.00,
                "sample_size": 42,
            },
            {
                "stratum": "Remainder (MUS)",
                "threshold": "≤$25,000",
                "count": 1_198,
                "total_value": 2_750_000.00,
                "sample_size": 165,
            },
        ],
    }

    evaluation_result = {
        "method": "mus",
        "confidence_level": 0.95,
        "sample_size": 207,
        "errors_found": 3,
        "total_misstatement": 4_230.00,
        "projected_misstatement": 12_480.00,
        "basic_precision": 25_000.00,
        "incremental_allowance": 8_750.00,
        "upper_error_limit": 46_230.00,
        "tolerable_misstatement": 75_000.00,
        "conclusion": "pass",
        "conclusion_detail": (
            "The upper error limit ($46,230) does not exceed the tolerable misstatement ($75,000). "
            "Based on this sample, the population is accepted at the 95% confidence level. "
            "The 3 errors identified are individually immaterial and represent pricing differences "
            "that have been corrected in the subsequent period."
        ),
        "errors": [
            {
                "item_id": "INV-2847",
                "recorded_amount": 3_450.00,
                "audited_amount": 3_200.00,
                "misstatement": 250.00,
                "tainting": 0.0725,
            },
            {
                "item_id": "INV-4102",
                "recorded_amount": 12_800.00,
                "audited_amount": 9_220.00,
                "misstatement": 3_580.00,
                "tainting": 0.2797,
            },
            {
                "item_id": "INV-5391",
                "recorded_amount": 1_600.00,
                "audited_amount": 1_200.00,
                "misstatement": 400.00,
                "tainting": 0.2500,
            },
        ],
    }

    pdf = generate_sampling_evaluation_memo(
        evaluation_result,
        design_result,
        "meridian_ar_subledger.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="AR Sub-Ledger — FY2025",
        source_context_note=ERP_NOTE,
    )
    save_pdf("14_sampling_evaluation.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 15. CURRENCY CONVERSION MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_currency_conversion():
    from currency_memo_generator import generate_currency_conversion_memo

    conversion_result = {
        "presentation_currency": "USD",
        "total_accounts": 247,
        "converted_count": 235,
        "unconverted_count": 12,
        "currencies_found": ["USD", "EUR", "GBP", "CAD", "JPY"],
        "rates_applied": {
            "EUR/USD": "1.0842",
            "GBP/USD": "1.2715",
            "CAD/USD": "0.7423",
            "JPY/USD": "0.006689",
        },
        "unconverted_items": [
            {
                "account_number": "5100",
                "account_name": "Intercompany — Singapore",
                "original_currency": "SGD",
                "issue": "missing_rate",
                "severity": "high",
            },
            {
                "account_number": "5110",
                "account_name": "Intercompany — Brazil",
                "original_currency": "BRL",
                "issue": "missing_rate",
                "severity": "high",
            },
            {
                "account_number": "5120",
                "account_name": "Foreign Subsidiary — Korea",
                "original_currency": "KRW",
                "issue": "missing_rate",
                "severity": "medium",
            },
            {
                "account_number": "1400",
                "account_name": "Vendor Deposit — India",
                "original_currency": "INR",
                "issue": "missing_rate",
                "severity": "medium",
            },
        ],
    }

    pdf = generate_currency_conversion_memo(
        conversion_result,
        "meridian_tb_multicurrency.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Multi-Currency Trial Balance — FY2025",
        source_context_note="Closing rates sourced from Reuters as of Dec 31, 2025",
    )
    save_pdf("15_currency_conversion.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 16. PRE-FLIGHT MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_preflight():
    from preflight_memo_generator import generate_preflight_memo

    preflight_result = {
        "readiness_score": 82.5,
        "readiness_label": "Ready with minor issues",
        "row_count": 247,
        "column_count": 7,
        "columns": [
            {"role": "account_name", "detected_name": "Account Description", "confidence": 0.98, "status": "confirmed"},
            {"role": "debit", "detected_name": "Debit Balance", "confidence": 0.95, "status": "confirmed"},
            {"role": "credit", "detected_name": "Credit Balance", "confidence": 0.95, "status": "confirmed"},
            {"role": "account_number", "detected_name": "Acct #", "confidence": 0.88, "status": "confirmed"},
            {"role": "account_type", "detected_name": "Category", "confidence": 0.72, "status": "low_confidence"},
            {"role": "currency", "detected_name": None, "confidence": 0.0, "status": "not_found"},
        ],
        "issues": [
            {
                "category": "missing_data",
                "severity": "medium",
                "message": "15 rows have blank account descriptions",
                "affected_count": 15,
                "remediation": "Fill in missing account names to improve classification accuracy",
            },
            {
                "category": "data_type",
                "severity": "low",
                "message": "3 amount columns contain text values mixed with numbers",
                "affected_count": 3,
                "remediation": "Remove non-numeric characters from amount columns",
            },
            {
                "category": "column_detection",
                "severity": "low",
                "message": "Currency column not detected — defaulting to USD",
                "affected_count": 247,
                "remediation": "Add a 'Currency' column if multi-currency TB",
            },
            {
                "category": "formatting",
                "severity": "low",
                "message": "12 account names contain leading/trailing whitespace",
                "affected_count": 12,
                "remediation": "Trim whitespace from account names for consistent matching",
            },
        ],
    }

    pdf = generate_preflight_memo(
        preflight_result,
        "meridian_tb_fy2025.xlsx",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Trial Balance Upload — FY2025",
        source_context_note=ERP_NOTE,
    )
    save_pdf("16_preflight_report.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 17. POPULATION PROFILE MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_population_profile():
    from population_profile_memo import generate_population_profile_memo

    profile_result = {
        "account_count": 247,
        "total_abs_balance": 12_847_392.50,
        "gini_coefficient": 0.7823,
        "gini_interpretation": "High",
        "mean_abs_balance": 52_012.52,
        "median_abs_balance": 18_450.00,
        "std_dev_abs_balance": 198_750.00,
        "min_abs_balance": 125.00,
        "max_abs_balance": 4_250_000.00,
        "p25": 4_200.00,
        "p75": 67_500.00,
        "buckets": [
            {"label": "$0 — $1,000", "count": 32, "percent_count": 13.0, "sum_abs": 18_750.00},
            {"label": "$1,001 — $10,000", "count": 78, "percent_count": 31.6, "sum_abs": 412_000.00},
            {"label": "$10,001 — $100,000", "count": 95, "percent_count": 38.5, "sum_abs": 3_245_000.00},
            {"label": "$100,001 — $1,000,000", "count": 35, "percent_count": 14.2, "sum_abs": 4_921_642.50},
            {"label": "> $1,000,000", "count": 7, "percent_count": 2.8, "sum_abs": 4_250_000.00},
        ],
        "top_accounts": [
            {
                "rank": 1,
                "account": "Revenue — Consulting Services",
                "category": "Revenue",
                "net_balance": 4_250_000.00,
                "percent_of_total": 33.1,
            },
            {
                "rank": 2,
                "account": "Cost of Goods Sold",
                "category": "Expense",
                "net_balance": 2_890_000.00,
                "percent_of_total": 22.5,
            },
            {
                "rank": 3,
                "account": "Property, Plant & Equipment",
                "category": "Asset",
                "net_balance": 3_420_000.00,
                "percent_of_total": 26.6,
            },
            {
                "rank": 4,
                "account": "Long-Term Debt",
                "category": "Liability",
                "net_balance": 1_500_000.00,
                "percent_of_total": 11.7,
            },
            {
                "rank": 5,
                "account": "Salaries & Wages",
                "category": "Expense",
                "net_balance": 1_420_000.00,
                "percent_of_total": 11.1,
            },
        ],
    }

    pdf = generate_population_profile_memo(
        profile_result,
        "meridian_tb_fy2025.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Trial Balance — FY2025",
        source_context_note=ERP_NOTE,
    )
    save_pdf("17_population_profile.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 18. EXPENSE CATEGORY MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_expense_category():
    from expense_category_memo import generate_expense_category_memo

    report_result = {
        "categories": [
            {
                "label": "Cost of Goods Sold",
                "amount": 2_890_000.00,
                "pct_of_revenue": 42.19,
                "prior_amount": 2_400_000.00,
                "dollar_change": 490_000.00,
                "exceeds_threshold": True,
            },
            {
                "label": "Payroll & Benefits",
                "amount": 1_420_000.00,
                "pct_of_revenue": 20.73,
                "prior_amount": 1_180_000.00,
                "dollar_change": 240_000.00,
                "exceeds_threshold": True,
            },
            {
                "label": "Depreciation & Amortization",
                "amount": 285_000.00,
                "pct_of_revenue": 4.16,
                "prior_amount": 260_000.00,
                "dollar_change": 25_000.00,
                "exceeds_threshold": False,
            },
            {
                "label": "Interest & Tax",
                "amount": 437_750.00,
                "pct_of_revenue": 6.39,
                "prior_amount": 398_000.00,
                "dollar_change": 39_750.00,
                "exceeds_threshold": False,
            },
            {
                "label": "Other Operating Expenses",
                "amount": 795_000.00,
                "pct_of_revenue": 11.61,
                "prior_amount": 642_000.00,
                "dollar_change": 153_000.00,
                "exceeds_threshold": True,
            },
        ],
        "total_expenses": 5_827_750.00,
        "total_revenue": 6_850_000.00,
        "revenue_available": True,
        "prior_available": True,
        "materiality_threshold": 50_000.00,
        "category_count": 5,
    }

    pdf = generate_expense_category_memo(
        report_result,
        "meridian_tb_fy2025.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Trial Balance — FY2025",
        source_context_note=ERP_NOTE,
    )
    save_pdf("18_expense_category.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 19. ACCRUAL COMPLETENESS MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_accrual_completeness():
    from accrual_completeness_memo import generate_accrual_completeness_memo

    report_result = {
        "accrual_accounts": [
            {"account_name": "Accrued Payroll", "balance": 142_000.00, "matched_keyword": "accrued"},
            {"account_name": "Accrued Interest Payable", "balance": 24_500.00, "matched_keyword": "accrued"},
            {"account_name": "Accrued Utilities", "balance": 8_200.00, "matched_keyword": "accrued"},
            {"account_name": "Accrued Legal Fees", "balance": 35_000.00, "matched_keyword": "accrued"},
            {"account_name": "Warranty Reserve", "balance": 18_750.00, "matched_keyword": "reserve"},
            {"account_name": "Deferred Revenue", "balance": 60_550.00, "matched_keyword": "deferred"},
        ],
        "total_accrued_balance": 289_000.00,
        "accrual_account_count": 6,
        "monthly_run_rate": 485_646.00,
        "accrual_to_run_rate_pct": 59.5,
        "threshold_pct": 50.0,
        "below_threshold": False,
        "prior_available": True,
        "prior_operating_expenses": 5_827_750.00,
        "narrative": (
            "The accrual-to-run-rate ratio of 59.5% exceeds the 50% threshold, suggesting "
            "accrual balances are within a reasonable range relative to operating activity levels. "
            "However, the practitioner should verify the completeness of the warranty reserve "
            "and deferred revenue balances against supporting documentation."
        ),
    }

    pdf = generate_accrual_completeness_memo(
        report_result,
        "meridian_tb_fy2025.csv",
        client_name=CLIENT,
        period_tested=PERIOD,
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Trial Balance — FY2025",
        source_context_note=ERP_NOTE,
    )
    save_pdf("19_accrual_completeness.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 20. FLUX EXPECTATIONS MEMO
# ─────────────────────────────────────────────────────────────────────
def gen_flux_expectations():
    from flux_expectations_memo import generate_flux_expectations_memo

    flux_result = {
        "items": [
            {
                "account": "Revenue — Consulting Services",
                "type": "Revenue",
                "prior": 3_600_000.00,
                "current": 4_250_000.00,
                "delta_amount": 650_000.00,
                "display_percent": "+18.1%",
                "risk_level": "high",
                "variance_indicators": ["material_change", "exceeds_threshold"],
            },
            {
                "account": "Marketing & Advertising",
                "type": "Expense",
                "prior": 120_000.00,
                "current": 195_000.00,
                "delta_amount": 75_000.00,
                "display_percent": "+62.5%",
                "risk_level": "high",
                "variance_indicators": ["material_change", "percentage_outlier"],
            },
            {
                "account": "Cash and Cash Equivalents",
                "type": "Asset",
                "prior": 776_750.00,
                "current": 1_245_000.00,
                "delta_amount": 468_250.00,
                "display_percent": "+60.3%",
                "risk_level": "medium",
                "variance_indicators": ["material_change"],
            },
        ],
        "summary": {
            "total_items": 247,
            "high_risk_count": 2,
            "medium_risk_count": 6,
            "threshold": 50_000,
        },
    }

    expectations = {
        "Revenue — Consulting Services": {
            "auditor_expectation": (
                "Revenue was expected to increase approximately 10-15% based on the "
                "new enterprise client contracts signed in Q2 2025 and the expanded "
                "scope of the Apex Industries engagement."
            ),
            "auditor_explanation": (
                "The 18.1% increase exceeds initial expectations. Per discussion with "
                "management, the additional growth is attributable to two unplanned "
                "project extensions with Northwind Corp ($180K) and early recognition "
                "of the Phase 2 deliverables on the Titan project. Management has "
                "provided supporting contracts and milestone documentation."
            ),
        },
        "Marketing & Advertising": {
            "auditor_expectation": (
                "Marketing spend was expected to remain flat or increase modestly "
                "(5-10%) based on the approved FY2025 budget."
            ),
            "auditor_explanation": (
                "The 62.5% increase is primarily driven by the Q3 brand repositioning "
                "campaign ($45K) and the October industry conference sponsorship ($22K). "
                "Both items were approved by the Board in July 2025 as an amendment to "
                "the original marketing budget. Supporting approvals have been obtained."
            ),
        },
        "Cash and Cash Equivalents": {
            "auditor_expectation": (
                "Cash was expected to increase moderately due to improved operating "
                "cash flow from revenue growth, partially offset by debt repayments."
            ),
            "auditor_explanation": (
                "The 60.3% increase is consistent with strong operating cash flows "
                "($1.3M) less capital expenditures ($470K) and debt service ($370K). "
                "The increase reconciles to the cash flow statement within $0 variance."
            ),
        },
    }

    pdf = generate_flux_expectations_memo(
        flux_result,
        expectations,
        "meridian_flux_analysis.csv",
        client_name=CLIENT,
        period_tested="FY 2024 vs. FY 2025",
        prepared_by=PREPARED,
        reviewed_by=REVIEWED,
        workpaper_date=WP_DATE,
        source_document_title="Flux Analysis — FY2024 vs FY2025",
        source_context_note=ERP_NOTE,
    )
    save_pdf("20_flux_expectations.pdf", pdf)


# ─────────────────────────────────────────────────────────────────────
# 21. ANOMALY SUMMARY REPORT
# ─────────────────────────────────────────────────────────────────────
def gen_anomaly_summary():
    """Build anomaly summary PDF from scratch using shared report primitives.

    The real AnomalySummaryGenerator requires a DB session + ORM objects,
    so we replicate the same PDF structure with fictional data here.
    """
    from io import BytesIO

    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    from pdf_generator import ClassicalColors, LedgerRule
    from shared.memo_base import create_memo_styles
    from shared.report_chrome import (
        ReportMetadata,
        build_cover_page,
        draw_page_footer,
        find_logo,
    )

    DISCLAIMER_TEXT = (
        "DATA ANALYTICS REPORT \u2014 NOT AN AUDIT COMMUNICATION. "
        "This report lists data anomalies detected through automated testing. It does not "
        "constitute an audit opinion, internal control assessment, or management letter per "
        "ISA 265/PCAOB AS 1305. The auditor must perform additional procedures and provide "
        "all deficiency classifications in the blank section below."
    )

    AUDITOR_INSTRUCTIONS = (
        "The auditor should document their assessment of the data anomalies above, "
        "including any implications for the audit approach, control testing, or "
        "substantive procedures."
    )

    styles = create_memo_styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    doc_width = letter[0] - 1.5 * inch
    story = []

    # --- Disclaimer banner ---
    disclaimer_style = ParagraphStyle(
        "DisclaimerBanner",
        fontName="Times-Bold",
        fontSize=10,
        textColor=ClassicalColors.CLAY,
        alignment=TA_CENTER,
        leading=13,
        spaceAfter=12,
        spaceBefore=4,
        backColor=ClassicalColors.OATMEAL_PAPER,
        borderPadding=8,
    )
    story.append(Paragraph(DISCLAIMER_TEXT, disclaimer_style))
    story.append(Spacer(1, 8))

    # --- Cover Page ---
    logo_path = find_logo()
    metadata = ReportMetadata(
        title="Anomaly Summary Report",
        client_name=CLIENT,
        engagement_period=PERIOD,
    )
    build_cover_page(story, styles, metadata, doc_width, logo_path)

    # --- Section I: Scope ---
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    story.append(Paragraph("<b>Tools Executed:</b> 8 of 12 available tools", styles["MemoBody"]))
    story.append(Paragraph("<b>Total Tool Runs:</b> 14", styles["MemoBody"]))

    scope_data = [
        ["Tool", "Runs", "Last Run"],
        ["Trial Balance Diagnostics", "2", "Feb 10, 2026 14:32"],
        ["Journal Entry Testing", "2", "Feb 11, 2026 09:15"],
        ["AP Payment Testing", "1", "Feb 11, 2026 10:48"],
        ["Payroll & Employee Testing", "1", "Feb 11, 2026 11:22"],
        ["Revenue Testing", "2", "Feb 12, 2026 08:45"],
        ["AR Aging Analysis", "1", "Feb 12, 2026 10:30"],
        ["Fixed Asset Testing", "3", "Feb 13, 2026 14:05"],
        ["Bank Reconciliation", "2", "Feb 14, 2026 09:00"],
    ]
    scope_table = Table(scope_data, colWidths=[3.0 * inch, 0.8 * inch, 2.5 * inch])
    scope_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(Spacer(1, 6))
    story.append(scope_table)
    story.append(Spacer(1, 12))

    # --- Section II: Data Anomalies by Tool ---
    story.append(Paragraph("II. Data Anomalies by Tool", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    story.append(
        Paragraph(
            "<b>Total Anomalies:</b> 12 &nbsp;&nbsp;|&nbsp;&nbsp; "
            "High: 4 &nbsp;&nbsp;|&nbsp;&nbsp; Medium: 5 &nbsp;&nbsp;|&nbsp;&nbsp; Low: 3",
            styles["MemoBody"],
        )
    )
    story.append(Spacer(1, 8))

    # Per-tool anomaly sections
    anomaly_groups = [
        (
            "Journal Entry Testing",
            [
                ("HIGH", "3 unbalanced journal entries where debits do not equal credits"),
                ("HIGH", "4 journal entries posted on US federal holidays (Thanksgiving, Christmas)"),
                ("MEDIUM", "156 entries clustered in last 3 days of each month (10.4% flag rate)"),
            ],
        ),
        (
            "AP Payment Testing",
            [
                ("HIGH", "2 exact duplicate payments totaling $14,200 to vendor 'Apex Office Solutions'"),
                ("HIGH", "3 payments processed before invoice date \u2014 potential prepayment anomaly"),
                ("MEDIUM", "5 payments just below $10,000 approval threshold on consecutive dates"),
            ],
        ),
        (
            "Revenue Testing",
            [
                ("MEDIUM", "7 entries with potential cut-off risk \u2014 revenue recorded within 3 days of period end"),
                ("MEDIUM", "Single customer represents 38% of total revenue \u2014 concentration risk"),
            ],
        ),
        (
            "Fixed Asset Testing",
            [
                ("MEDIUM", "2 assets with accumulated depreciation exceeding original cost"),
                ("LOW", "12 fully depreciated assets still in use \u2014 potential impairment indicator"),
            ],
        ),
        (
            "AR Aging Analysis",
            [
                ("LOW", "Allowance-to-receivable ratio of 2.1% \u2014 below industry benchmark of 3\u20135%"),
                ("LOW", "3 customers exceeding credit limits totaling $142,000 over-limit"),
            ],
        ),
    ]

    for tool_label, items in anomaly_groups:
        story.append(Paragraph(f"<b>{tool_label}</b> ({len(items)} items)", styles["MemoBody"]))
        table_data = [["#", "Severity", "Description"]]
        for idx, (sev, desc) in enumerate(items, 1):
            table_data.append([str(idx), sev, Paragraph(desc, styles["MemoTableCell"])])
        anomaly_table = Table(table_data, colWidths=[0.4 * inch, 0.8 * inch, 5.2 * inch])
        anomaly_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                ]
            )
        )
        story.append(anomaly_table)
        story.append(Spacer(1, 10))

    # --- Section III: For Practitioner Assessment (blank page) ---
    story.append(PageBreak())
    story.append(Paragraph("III. For Practitioner Assessment", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))
    story.append(Paragraph("<i>" + AUDITOR_INSTRUCTIONS + "</i>", styles["MemoBody"]))
    story.append(Spacer(1, 24))

    for _ in range(20):
        story.append(LedgerRule(doc_width))
        story.append(Spacer(1, 18))

    # --- Disclaimer footer (repeated) ---
    story.append(Spacer(1, 16))
    story.append(Paragraph(DISCLAIMER_TEXT, styles["MemoDisclaimer"]))

    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    save_pdf("21_anomaly_summary.pdf", pdf_bytes)


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────
GENERATORS = [
    ("Trial Balance Diagnostic", gen_tb_diagnostic),
    ("Financial Statements", gen_financial_statements),
    ("Journal Entry Testing", gen_je_testing),
    ("AP Payment Testing", gen_ap_testing),
    ("Payroll & Employee Testing", gen_payroll_testing),
    ("Revenue Testing", gen_revenue_testing),
    ("AR Aging Analysis", gen_ar_aging),
    ("Fixed Asset Testing", gen_fixed_asset_testing),
    ("Inventory Testing", gen_inventory_testing),
    ("Bank Reconciliation", gen_bank_rec),
    ("Three-Way Match", gen_three_way_match),
    ("Multi-Period Comparison", gen_multi_period),
    ("Sampling — Design Phase", gen_sampling_design),
    ("Sampling — Evaluation Phase", gen_sampling_evaluation),
    ("Currency Conversion", gen_currency_conversion),
    ("Pre-Flight Report", gen_preflight),
    ("Population Profile", gen_population_profile),
    ("Expense Category Analytics", gen_expense_category),
    ("Accrual Completeness", gen_accrual_completeness),
    ("Flux Expectations", gen_flux_expectations),
    ("Anomaly Summary", gen_anomaly_summary),
]


if __name__ == "__main__":
    print("\nPaciolus Sample Report Generator")
    print(f"{'=' * 50}")
    print(f"Client: {CLIENT}")
    print(f"Output: {OUTPUT_DIR}\n")

    success = 0
    failed = 0

    for name, fn in GENERATORS:
        try:
            print(f"Generating: {name}...")
            fn()
            success += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Complete: {success} succeeded, {failed} failed")
    print(f"PDFs saved to: {OUTPUT_DIR}")
