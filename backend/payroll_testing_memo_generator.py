"""
Payroll Testing Memo PDF Generator (Sprint 88, refactored Sprint 90)

Auto-generated testing memo per ISA 240 / ISA 500 / PCAOB AS 2401.
Renaissance Ledger aesthetic consistent with existing PDF exports.

Sections:
1. Header (client, period, preparer)
2. Scope (employees tested, pay entries)
3. Methodology (tests applied with descriptions)
4. Results Summary (composite score, flags by test)
5. Findings (top flagged employees)
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


PAYROLL_TEST_DESCRIPTIONS = {
    "PR-T1": "Identifies employee IDs associated with multiple different names, indicating possible data integrity issues.",
    "PR-T2": "Flags payroll entries with blank employee names, zero gross pay, or missing pay dates.",
    "PR-T3": "Flags round-dollar pay amounts ($100K, $50K, $25K, $10K multiples) that may indicate estimates.",
    "PR-T4": "Flags payments made after the employee's recorded termination date.",
    "PR-T5": "Detects gaps in sequential payroll check numbering that may indicate voided or missing checks.",
    "PR-T6": "Uses z-score analysis to identify statistically unusual pay amounts per department.",
    "PR-T7": "Flags employees with irregular pay spacing compared to the population cadence.",
    "PR-T8": "Applies Benford's Law first-digit analysis to gross pay amounts.",
    "PR-T9": "Flags employees with ghost employee indicators: no department, single entry, boundary-month-only payments.",
    "PR-T10": "Flags employees sharing the same bank account or similar addresses.",
    "PR-T11": "Flags employees sharing the same tax identification number.",
}


def generate_payroll_testing_memo(
    payroll_result: dict[str, Any],
    filename: str = "payroll_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for payroll testing results.

    Args:
        payroll_result: PayrollTestingResult.to_dict() output
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description (e.g., "FY 2025")
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("payroll_memo_generate", f"Generating payroll testing memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "PRT-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story = []
    composite = payroll_result.get("composite_score", {})
    test_results = payroll_result.get("test_results", [])
    data_quality = payroll_result.get("data_quality", {})

    # 1. HEADER
    build_memo_header(story, styles, doc.width, "Payroll &amp; Employee Testing Memo", reference, client_name)

    # 2. SCOPE
    build_scope_section(story, styles, doc.width, composite, data_quality,
                        entry_label="Total Payroll Entries Tested", period_tested=period_tested)

    # 3. METHODOLOGY
    build_methodology_section(
        story, styles, doc.width, test_results, PAYROLL_TEST_DESCRIPTIONS,
        "The following automated tests were applied to the payroll register "
        "in accordance with professional auditing standards "
        "(ISA 240: Auditor's Responsibilities Relating to Fraud, "
        "ISA 500: Audit Evidence, PCAOB AS 2401: Consideration of Fraud):",
    )

    # 4. RESULTS SUMMARY
    build_results_summary_section(story, styles, doc.width, composite, test_results,
                                  flagged_label="Total Entries Flagged")

    # 5. TOP FINDINGS
    top_findings = composite.get("top_findings", [])
    if top_findings:
        story.append(Paragraph("IV. KEY FINDINGS", styles['MemoSection']))
        story.append(LedgerRule(doc.width))
        for i, finding in enumerate(top_findings[:5], 1):
            if isinstance(finding, dict):
                text = f"{finding.get('employee', 'Unknown')} \u2014 {finding.get('issue', '')}"
            else:
                text = str(finding)
            story.append(Paragraph(f"{i}. {text}", styles['MemoBody']))
        story.append(Spacer(1, 8))

    # 6. CONCLUSION
    conclusion_num = "V" if top_findings else "IV"
    story.append(Paragraph(f"{conclusion_num}. CONCLUSION", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    score_val = composite.get("score", 0)
    if score_val < 10:
        assessment = (
            "Based on the automated payroll testing procedures applied, "
            "the payroll register exhibits a LOW risk profile. "
            "No material anomalies requiring further investigation were identified."
        )
    elif score_val < 25:
        assessment = (
            "Based on the automated payroll testing procedures applied, "
            "the payroll register exhibits an ELEVATED risk profile. "
            "Select flagged entries should be reviewed for proper authorization and documentation."
        )
    elif score_val < 50:
        assessment = (
            "Based on the automated payroll testing procedures applied, "
            "the payroll register exhibits a MODERATE risk profile. "
            "Flagged entries warrant focused review, particularly ghost employee indicators."
        )
    else:
        assessment = (
            "Based on the automated payroll testing procedures applied, "
            "the payroll register exhibits a HIGH risk profile. "
            "Significant anomalies were identified that require detailed investigation "
            "and may warrant expanded payroll audit procedures."
        )

    story.append(Paragraph(assessment, styles['MemoBody']))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(story, styles, doc.width, prepared_by, reviewed_by, workpaper_date)

    # DISCLAIMER
    build_disclaimer(story, styles, domain="payroll testing")

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("payroll_memo_complete", f"Payroll memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
