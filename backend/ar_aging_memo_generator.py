"""
AR Aging Analysis Memo PDF Generator (Sprint 108, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: ISA 500 / ISA 540 / PCAOB AS 2501.

Uses custom scope builder for dual-input mode (TB + optional sub-ledger).
"""

from typing import Any, Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer

from pdf_generator import LedgerRule, create_leader_dots
from shared.drill_down import (
    build_drill_down_table,
    format_currency,
    safe_str_value,
)
from shared.memo_template import TestingMemoConfig, _roman, generate_testing_memo

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

_AR_CONFIG = TestingMemoConfig(
    title="Accounts Receivable Aging Analysis Memo",
    ref_prefix="ARA",
    entry_label="Total AR Items Tested",  # not used — custom scope replaces
    flagged_label="Total AR Items Flagged",
    log_prefix="ar_aging_memo",
    domain="accounts receivable aging analysis",
    test_descriptions=AR_AGING_TEST_DESCRIPTIONS,
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
            "the accounts receivable data returned LOW flag density across the automated tests. "
            "No receivables anomalies exceeding the configured thresholds were detected by the automated tests applied."
        ),
        "elevated": (
            "Based on the automated AR aging analysis procedures applied, "
            "the accounts receivable data returned ELEVATED flag density across the automated tests. "
            "Select flagged items should be reviewed for proper receivables valuation treatment "
            "and supporting documentation."
        ),
        "moderate": (
            "Based on the automated AR aging analysis procedures applied, "
            "the accounts receivable data returned MODERATE flag density across the automated tests. "
            "Flagged items warrant focused review as receivables anomaly indicators, "
            "particularly aging concentration and allowance adequacy metrics."
        ),
        "high": (
            "Based on the automated AR aging analysis procedures applied, "
            "the accounts receivable data returned HIGH flag density across the automated tests. "
            "Significant receivables anomaly indicators were detected that require "
            "detailed investigation. The engagement team should evaluate whether additional "
            "receivables procedures are appropriate per ISA 540 and PCAOB AS 2501."
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


def _build_ar_extra_sections(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    section_counter: int,
) -> int:
    """Build AR-specific drill-down sections.

    CONTENT-01: Aging schedule table with narrative.
    CONTENT-02: Allowance gap quantification.
    DRILL-05: Credit limit breach customer detail, deduplicated by customer.
    """
    # ── CONTENT-01: Aging Schedule Table ──
    aging_schedule = result.get("aging_schedule")
    if aging_schedule:
        section_label = _roman(section_counter)
        story.append(Paragraph(f"{section_label}. Aging Schedule", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        # Compute past-due percentage (everything beyond Current bucket)
        total_amount = sum(b.get("amount", 0) for b in aging_schedule)
        past_due_amount = sum(b.get("amount", 0) for b in aging_schedule if b.get("bucket", "") != "Current (0-30)")
        past_due_pct = (past_due_amount / total_amount * 100) if total_amount != 0 else 0.0

        narrative = (
            f"The following table summarizes the distribution of accounts receivable "
            f"across standard aging buckets. "
            f"Past-due receivables (beyond 30 days) represent "
            f"{past_due_pct:.1f}% of total outstanding balances "
            f"({format_currency(past_due_amount)} of {format_currency(total_amount)})."
        )
        story.append(Paragraph(narrative, styles["MemoBody"]))
        story.append(Spacer(1, 4))

        schedule_rows = []
        for bucket in aging_schedule:
            schedule_rows.append(
                [
                    bucket.get("bucket", ""),
                    str(bucket.get("count", 0)),
                    format_currency(bucket.get("amount", 0)),
                    f"{bucket.get('percentage', 0):.1f}%",
                ]
            )

        build_drill_down_table(
            story,
            styles,
            doc_width,
            title="",
            headers=["Aging Bucket", "Count", "Amount", "% of Total"],
            rows=schedule_rows,
            total_flagged=len(schedule_rows),
            col_widths=[2.0 * inch, 1.0 * inch, 1.8 * inch, 1.2 * inch],
            right_align_cols=[1, 2, 3],
        )
        section_counter += 1

    # ── CONTENT-02: Allowance Gap Quantification ──
    ar_summary = result.get("ar_summary") or {}
    total_ar_balance = ar_summary.get("total_ar_balance")
    recorded_allowance = ar_summary.get("total_allowance")

    if total_ar_balance is not None and recorded_allowance is not None and total_ar_balance > 0:
        section_label = _roman(section_counter)
        story.append(Paragraph(f"{section_label}. Allowance Gap Analysis", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        allowance_3pct = total_ar_balance * 0.03
        allowance_4pct = total_ar_balance * 0.04
        gap_at_3pct = allowance_3pct - recorded_allowance
        gap_at_4pct = allowance_4pct - recorded_allowance

        story.append(
            Paragraph(
                "The following analysis compares the recorded allowance for doubtful accounts "
                "against common benchmark rates applied to the total AR balance. "
                "This is an anomaly indicator, not a sufficiency determination — "
                "allowance adequacy requires management judgment per ISA 540 / PCAOB AS 2501.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 4))

        gap_rows = [
            ["Total AR Balance", format_currency(total_ar_balance)],
            ["Allowance at 3%", format_currency(allowance_3pct)],
            ["Allowance at 4%", format_currency(allowance_4pct)],
            ["Recorded Allowance", format_currency(recorded_allowance)],
            ["Gap at 3%", format_currency(gap_at_3pct)],
            ["Gap at 4%", format_currency(gap_at_4pct)],
        ]

        build_drill_down_table(
            story,
            styles,
            doc_width,
            title="",
            headers=["Metric", "Amount"],
            rows=gap_rows,
            total_flagged=len(gap_rows),
            col_widths=[3.0 * inch, 2.5 * inch],
            right_align_cols=[1],
        )
        section_counter += 1

    # ── DRILL-05: Credit limit breach customer detail ──
    test_results = result.get("test_results", [])

    credit_tests = [
        tr for tr in test_results if tr.get("test_key") == "credit_limit_breaches" and tr.get("entries_flagged", 0) > 0
    ]
    if not credit_tests:
        return section_counter

    flagged = credit_tests[0].get("flagged_entries", [])

    # Deduplicate by customer
    seen_customers: set[str] = set()
    rows = []
    for fe in flagged:
        details = fe.get("details") or {}
        entry = fe.get("entry") or {}
        customer = details.get("customer", "")
        if customer in seen_customers:
            continue
        seen_customers.add(customer)
        credit_limit = details.get("credit_limit", 0)
        total_ar = details.get("total_ar", 0)
        over_limit = (
            total_ar - credit_limit
            if isinstance(total_ar, (int, float)) and isinstance(credit_limit, (int, float))
            else 0
        )
        aging_days = entry.get("aging_days", details.get("aging_days", ""))
        rows.append(
            [
                safe_str_value(customer)[:25],
                format_currency(credit_limit),
                format_currency(total_ar),
                format_currency(max(over_limit, 0)),
                str(aging_days) if aging_days else "—",
            ]
        )

    if rows:
        section_label = _roman(section_counter)
        story.append(Paragraph(f"{section_label}. Credit Limit Breach Detail", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))
        story.append(
            Paragraph(
                f"{len(rows)} customer(s) exceed their approved credit limit:",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 4))

        build_drill_down_table(
            story,
            styles,
            doc_width,
            title="",
            headers=["Customer", "Credit Limit", "Outstanding", "Over Limit", "Aging Days"],
            rows=rows,
            total_flagged=len(rows),
            col_widths=[2.0 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.0 * inch],
            right_align_cols=[1, 2, 3, 4],
        )
        section_counter += 1

    return section_counter


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
        build_extra_sections=_build_ar_extra_sections,
        include_signoff=include_signoff,
    )
