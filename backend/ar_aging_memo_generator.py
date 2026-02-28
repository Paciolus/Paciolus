"""
AR Aging Analysis Memo PDF Generator (Sprint 108, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: ISA 500 / ISA 540 / PCAOB AS 2501.

Uses custom scope builder for dual-input mode (TB + optional sub-ledger).
"""

from typing import Any, Optional

from reportlab.platypus import Paragraph, Spacer

from pdf_generator import LedgerRule, create_leader_dots
from shared.memo_template import TestingMemoConfig, generate_testing_memo

AR_AGING_TEST_DESCRIPTIONS = {
    "ar_sign_anomalies": "Flags AR accounts with credit balances, indicating potential overpayments, misclassifications, or contra-AR entries.",
    "missing_allowance": "Checks for the existence of an Allowance for Doubtful Accounts (contra-AR), required under IFRS 9 / ASC 326.",
    "negative_aging": "Flags sub-ledger entries with negative aging days, indicating date logic errors or future-dated invoices.",
    "unreconciled_detail": "Compares the AR sub-ledger total to the TB AR balance to identify unreconciled differences.",
    "bucket_concentration": "Flags disproportionate concentration in a single aging bucket (e.g., >60% in current or over-120).",
    "past_due_concentration": "Flags elevated past-due receivables as a proportion of total AR, an indicator of collection risk.",
    "allowance_adequacy": "Compares the allowance-to-AR ratio against expected ranges — an anomaly indicator, not a sufficiency determination.",
    "customer_concentration": "Flags single customers representing a disproportionate share of total receivables (credit concentration risk).",
    "dso_trend": "Compares current-period DSO to prior-period DSO to identify significant trend changes in collection efficiency.",
    "rollforward_reconciliation": "Tests the AR roll-forward: beginning balance + revenue - collections should approximate ending AR balance.",
    "credit_limit_breaches": "Flags customers whose outstanding balance exceeds their approved credit limit.",
}

AR_AGING_TEST_PARAMETERS = {
    "ar_sign_anomalies": "Credit balance in debit-normal account",
    "missing_allowance": "Contra-AR account check",
    "negative_aging": "Aging days < 0",
    "unreconciled_detail": "Sub-ledger vs. TB difference",
    "bucket_concentration": "> 60% in single bucket",
    "past_due_concentration": "Past-due % of total AR",
    "allowance_adequacy": "Allowance-to-AR ratio range",
    "customer_concentration": "Top-10 customers %",
    "dso_trend": "Period-over-period DSO change",
    "rollforward_reconciliation": "Beg + Rev - Collections \u2248 End",
    "credit_limit_breaches": "Balance > approved limit",
}

AR_AGING_TEST_ASSERTIONS = {
    "ar_sign_anomalies": ["presentation"],
    "missing_allowance": ["valuation"],
    "negative_aging": ["accuracy"],
    "unreconciled_detail": ["completeness"],
    "bucket_concentration": ["valuation"],
    "past_due_concentration": ["valuation"],
    "allowance_adequacy": ["valuation"],
    "customer_concentration": ["existence"],
    "dso_trend": ["valuation"],
    "rollforward_reconciliation": ["completeness", "accuracy"],
    "credit_limit_breaches": ["rights_obligations"],
}

_AR_CONFIG = TestingMemoConfig(
    title="Accounts Receivable Aging Analysis Memo",
    ref_prefix="ARA",
    entry_label="Total AR Items Tested",  # not used — custom scope replaces
    flagged_label="Total AR Items Flagged",
    log_prefix="ar_aging_memo",
    domain="accounts receivable aging analysis",
    test_descriptions=AR_AGING_TEST_DESCRIPTIONS,
    test_parameters=AR_AGING_TEST_PARAMETERS,
    test_assertions=AR_AGING_TEST_ASSERTIONS,
    methodology_intro=(
        "The following automated tests were applied to the accounts receivable "
        "trial balance and sub-ledger data in accordance with professional auditing standards "
        "(ISA 500: Audit Evidence, ISA 540: Auditing Accounting Estimates \u2014 "
        "receivables valuation and expected credit loss estimation, "
        "PCAOB AS 2501: Auditing Accounting Estimates). "
        "Results represent receivables anomaly indicators, not allowance sufficiency conclusions:"
    ),
    isa_reference="ISA 500 (Audit Evidence) and ISA 540 (Auditing Accounting Estimates)",
    tool_domain="ar_aging_testing",
    risk_assessments={
        "low": (
            "Based on the automated AR aging analysis procedures applied, "
            "the accounts receivable data exhibits a LOW risk profile. "
            "No material receivables anomaly indicators requiring further investigation were identified."
        ),
        "elevated": (
            "Based on the automated AR aging analysis procedures applied, "
            "the accounts receivable data exhibits an ELEVATED risk profile. "
            "Select flagged items should be reviewed for proper receivables valuation treatment "
            "and supporting documentation."
        ),
        "moderate": (
            "Based on the automated AR aging analysis procedures applied, "
            "the accounts receivable data exhibits a MODERATE risk profile. "
            "Flagged items warrant focused review as receivables anomaly indicators, "
            "particularly aging concentration and allowance adequacy metrics."
        ),
        "high": (
            "Based on the automated AR aging analysis procedures applied, "
            "the accounts receivable data exhibits a HIGH risk profile. "
            "Significant receivables anomaly indicators were identified that may warrant "
            "detailed investigation and expanded receivables audit procedures "
            "at the engagement team's discretion per ISA 540 and PCAOB AS 2501."
        ),
    },
)


def _build_ar_scope_section(
    story: list,
    styles: dict,
    doc_width: float,
    composite: dict[str, Any],
    data_quality: dict[str, Any],
    period_tested: Optional[str] = None,
) -> None:
    """Build an AR-specific scope section with dual-input details."""
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    tests_run = composite.get("tests_run", 0)
    tests_skipped = composite.get("tests_skipped", 0)
    has_subledger = composite.get("has_subledger", False)
    total_tb = data_quality.get("total_tb_accounts", 0)
    total_sl = data_quality.get("total_subledger_entries", 0)

    scope_lines = []
    if period_tested:
        scope_lines.append(create_leader_dots("Period Tested", period_tested))

    scope_lines.append(create_leader_dots("TB Accounts Analyzed", f"{total_tb:,}"))

    if has_subledger:
        scope_lines.append(create_leader_dots("Sub-Ledger Entries", f"{total_sl:,}"))
        scope_lines.append(create_leader_dots("Analysis Mode", "Full (TB + Sub-Ledger)"))
    else:
        scope_lines.append(create_leader_dots("Analysis Mode", "TB-Only (Structural)"))

    scope_lines.append(create_leader_dots("Tests Applied", str(tests_run)))
    if tests_skipped > 0:
        scope_lines.append(create_leader_dots("Tests Skipped", f"{tests_skipped} (require sub-ledger)"))

    scope_lines.append(
        create_leader_dots(
            "Data Quality Score",
            f"{data_quality.get('completeness_score', 0):.0f}%",
        )
    )

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 8))


def generate_ar_aging_memo(
    ar_result: dict[str, Any],
    filename: str = "ar_aging",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    include_signoff: bool = False,
) -> bytes:
    """Generate a PDF testing memo for AR aging analysis results."""
    return generate_testing_memo(
        ar_result,
        _AR_CONFIG,
        filename=filename,
        client_name=client_name,
        period_tested=period_tested,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        source_document_title=source_document_title,
        source_context_note=source_context_note,
        build_scope=_build_ar_scope_section,
        include_signoff=include_signoff,
    )
