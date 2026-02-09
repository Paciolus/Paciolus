"""
Revenue Testing Memo PDF Generator (Sprint 105)

Auto-generated testing memo per ISA 240 / ISA 500 / PCAOB AS 2401.
Renaissance Ledger aesthetic consistent with existing PDF exports.

Revenue recognition carries a presumed fraud risk under ISA 240.
This memo documents automated revenue anomaly indicators — it does NOT
constitute fraud detection conclusions or sufficiency per ISA 500.

Sections:
1. Header (client, period, preparer)
2. Scope (entries tested, data quality)
3. Methodology (tests applied with descriptions)
4. Results Summary (composite score, flags by test)
5. Findings (top flagged revenue entries)
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


REVENUE_TEST_DESCRIPTIONS = {
    "large_manual_entries": "Flags manual revenue entries exceeding performance materiality threshold (ISA 240 fraud risk indicator).",
    "year_end_concentration": "Flags revenue concentrated in the last days of the period, a common revenue recognition anomaly indicator.",
    "round_revenue_amounts": "Flags revenue entries at round dollar amounts that may indicate estimates or adjustments.",
    "sign_anomalies": "Flags debit balances in revenue accounts (normally credit), indicating potential mispostings.",
    "unclassified_entries": "Flags revenue entries missing account classification (unmapped to chart of accounts).",
    "zscore_outliers": "Uses z-score analysis to identify statistically unusual revenue amounts.",
    "trend_variance": "Flags significant period-over-period revenue changes that may indicate revenue recognition anomalies.",
    "concentration_risk": "Flags single accounts representing a disproportionate share of total revenue.",
    "cutoff_risk": "Flags revenue entries near period boundaries that may indicate cut-off anomalies.",
    "benford_law": "Applies Benford's Law first-digit analysis to revenue transaction amounts.",
    "duplicate_entries": "Flags revenue entries with identical amount, date, and account — potential duplicate postings.",
    "contra_revenue_anomalies": "Flags elevated returns/allowances relative to gross revenue, a fraud risk indicator.",
}


def generate_revenue_testing_memo(
    revenue_result: dict[str, Any],
    filename: str = "revenue_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for revenue testing results.

    Args:
        revenue_result: RevenueTestingResult.to_dict() output
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description (e.g., "FY 2025")
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("revenue_memo_generate", f"Generating revenue testing memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "RVT-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story = []
    composite = revenue_result.get("composite_score", {})
    test_results = revenue_result.get("test_results", [])
    data_quality = revenue_result.get("data_quality", {})

    # 1. HEADER
    build_memo_header(
        story, styles, doc.width,
        "Revenue Recognition Testing Memo",
        reference, client_name,
    )

    # 2. SCOPE
    build_scope_section(
        story, styles, doc.width, composite, data_quality,
        entry_label="Total Revenue Entries Tested",
        period_tested=period_tested,
    )

    # 3. METHODOLOGY
    build_methodology_section(
        story, styles, doc.width, test_results, REVENUE_TEST_DESCRIPTIONS,
        "The following automated tests were applied to the revenue GL extract "
        "in accordance with professional auditing standards "
        "(ISA 240: Auditor's Responsibilities Relating to Fraud — "
        "presumed fraud risk in revenue recognition, "
        "ISA 500: Audit Evidence, PCAOB AS 2401: Consideration of Fraud). "
        "Results represent revenue anomaly indicators, not fraud detection conclusions:",
    )

    # 4. RESULTS SUMMARY
    build_results_summary_section(
        story, styles, doc.width, composite, test_results,
        flagged_label="Total Revenue Entries Flagged",
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
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract exhibits a LOW risk profile. "
            "No material revenue recognition anomalies requiring further investigation were identified."
        )
    elif score_val < 25:
        assessment = (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract exhibits an ELEVATED risk profile. "
            "Select flagged entries should be reviewed for proper revenue recognition treatment "
            "and supporting documentation."
        )
    elif score_val < 50:
        assessment = (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract exhibits a MODERATE risk profile. "
            "Flagged entries warrant focused review as revenue recognition anomaly indicators, "
            "particularly year-end concentration and cut-off items."
        )
    else:
        assessment = (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract exhibits a HIGH risk profile. "
            "Significant revenue recognition anomaly indicators were identified that require "
            "detailed investigation and may warrant expanded revenue audit procedures "
            "per ISA 240 and PCAOB AS 2401."
        )

    story.append(Paragraph(assessment, styles['MemoBody']))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(story, styles, doc.width, prepared_by, reviewed_by, workpaper_date)

    # DISCLAIMER
    build_disclaimer(
        story, styles,
        domain="revenue recognition testing",
        isa_reference="ISA 240 (presumed fraud risk in revenue recognition) and ISA 500",
    )

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("revenue_memo_complete", f"Revenue memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
