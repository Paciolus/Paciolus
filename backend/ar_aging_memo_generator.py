"""
AR Aging Analysis Memo PDF Generator (Sprint 108)

Auto-generated testing memo per ISA 500 / ISA 540 / PCAOB AS 2501.
Renaissance Ledger aesthetic consistent with existing PDF exports.

AR aging analysis covers receivables valuation and estimation of
expected credit losses. This memo documents automated receivables
anomaly indicators — it does NOT constitute an allowance sufficiency
opinion or a determination of net realizable value.

Sections:
1. Header (client, period, preparer)
2. Scope (accounts tested, data quality, dual-input mode)
3. Methodology (tests applied with descriptions)
4. Results Summary (composite score, flags by test)
5. Findings (top flagged AR items)
6. Conclusion (professional assessment)
"""

import io
from typing import Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
)

from pdf_generator import (
    LedgerRule, generate_reference_number,
)
from shared.memo_base import (
    create_memo_styles, build_memo_header, build_scope_section,
    build_methodology_section, build_results_summary_section,
    build_workpaper_signoff, build_disclaimer,
)
from security_utils import log_secure_operation


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


def generate_ar_aging_memo(
    ar_result: dict[str, Any],
    filename: str = "ar_aging",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for AR aging analysis results.

    Args:
        ar_result: ARAgingResult.to_dict() output
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description (e.g., "FY 2025")
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("ar_aging_memo_generate", f"Generating AR aging memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "ARA-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story = []
    composite = ar_result.get("composite_score", {})
    test_results = ar_result.get("test_results", [])
    data_quality = ar_result.get("data_quality", {})

    # 1. HEADER
    build_memo_header(
        story, styles, doc.width,
        "Accounts Receivable Aging Analysis Memo",
        reference, client_name,
    )

    # 2. SCOPE — enhanced for dual-input
    _build_ar_scope_section(story, styles, doc.width, composite, data_quality, period_tested)

    # 3. METHODOLOGY
    build_methodology_section(
        story, styles, doc.width, test_results, AR_AGING_TEST_DESCRIPTIONS,
        "The following automated tests were applied to the accounts receivable "
        "trial balance and sub-ledger data in accordance with professional auditing standards "
        "(ISA 500: Audit Evidence, ISA 540: Auditing Accounting Estimates — "
        "receivables valuation and expected credit loss estimation, "
        "PCAOB AS 2501: Auditing Accounting Estimates). "
        "Results represent receivables anomaly indicators, not allowance sufficiency conclusions:",
    )

    # 4. RESULTS SUMMARY
    build_results_summary_section(
        story, styles, doc.width, composite, test_results,
        flagged_label="Total AR Items Flagged",
    )

    # 5. TOP FINDINGS
    top_findings = composite.get("top_findings", [])
    if top_findings:
        story.append(Paragraph("IV. KEY FINDINGS", styles['MemoSection']))
        story.append(LedgerRule(doc.width))
        for i, finding in enumerate(top_findings[:5], 1):
            story.append(Paragraph(f"{i}. {finding}", styles['MemoBody']))
        story.append(Spacer(1, 8))

    # 6. CONCLUSION
    conclusion_num = "V" if top_findings else "IV"
    story.append(Paragraph(f"{conclusion_num}. CONCLUSION", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    score_val = composite.get("score", 0)
    if score_val < 10:
        assessment = (
            "Based on the automated AR aging analysis procedures applied, "
            "the accounts receivable data exhibits a LOW risk profile. "
            "No material receivables anomaly indicators requiring further investigation were identified."
        )
    elif score_val < 25:
        assessment = (
            "Based on the automated AR aging analysis procedures applied, "
            "the accounts receivable data exhibits an ELEVATED risk profile. "
            "Select flagged items should be reviewed for proper receivables valuation treatment "
            "and supporting documentation."
        )
    elif score_val < 50:
        assessment = (
            "Based on the automated AR aging analysis procedures applied, "
            "the accounts receivable data exhibits a MODERATE risk profile. "
            "Flagged items warrant focused review as receivables anomaly indicators, "
            "particularly aging concentration and allowance adequacy metrics."
        )
    else:
        assessment = (
            "Based on the automated AR aging analysis procedures applied, "
            "the accounts receivable data exhibits a HIGH risk profile. "
            "Significant receivables anomaly indicators were identified that require "
            "detailed investigation and may warrant expanded receivables audit procedures "
            "per ISA 540 and PCAOB AS 2501."
        )

    story.append(Paragraph(assessment, styles['MemoBody']))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(story, styles, doc.width, prepared_by, reviewed_by, workpaper_date)

    # DISCLAIMER
    build_disclaimer(
        story, styles,
        domain="accounts receivable aging analysis",
        isa_reference="ISA 500 (Audit Evidence) and ISA 540 (Auditing Accounting Estimates)",
    )

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("ar_aging_memo_complete", f"AR aging memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes


def _build_ar_scope_section(
    story: list,
    styles: dict,
    doc_width: float,
    composite: dict[str, Any],
    data_quality: dict[str, Any],
    period_tested: Optional[str] = None,
) -> None:
    """Build an AR-specific scope section with dual-input details."""
    from pdf_generator import LedgerRule, create_leader_dots

    story.append(Paragraph("I. SCOPE", styles['MemoSection']))
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

    scope_lines.append(create_leader_dots(
        "Data Quality Score",
        f"{data_quality.get('completeness_score', 0):.0f}%",
    ))

    for line in scope_lines:
        story.append(Paragraph(line, styles['MemoLeader']))
    story.append(Spacer(1, 8))
