"""
AP Testing Memo PDF Generator (Sprint 76, refactored Sprint 90)

Auto-generated testing memo per ISA 240 / ISA 500 / PCAOB AS 2401.
Renaissance Ledger aesthetic consistent with existing PDF exports.

Sections:
1. Header (client, period, preparer)
2. Scope (payments tested, vendor count)
3. Methodology (tests applied with descriptions)
4. Results Summary (composite score, flags by test)
5. Findings (top flagged payments)
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


AP_TEST_DESCRIPTIONS = {
    "exact_duplicate_payments": "Identifies payments with identical vendor, invoice number, amount, and payment date.",
    "missing_critical_fields": "Flags payments missing vendor name, amount, or payment date.",
    "check_number_gaps": "Flags gaps in sequential check numbering that may indicate voided or missing payments.",
    "round_dollar_amounts": "Flags payments at round dollar amounts that may indicate estimates or manipulation.",
    "payment_before_invoice": "Flags payments made before the invoice date, indicating prepayment errors or fraud.",
    "fuzzy_duplicate_payments": "Flags payments to the same vendor with matching amounts on different dates within a window.",
    "invoice_number_reuse": "Flags invoice numbers that appear across multiple vendors, indicating possible fraud.",
    "unusual_payment_amounts": "Uses z-score analysis to identify statistically unusual amounts per vendor.",
    "weekend_payments": "Flags payments processed on weekends, indicating unauthorized or unusual activity.",
    "high_frequency_vendors": "Flags vendors receiving an unusually high number of payments in a single day.",
    "vendor_name_variations": "Flags similar vendor names that may indicate ghost vendors or deliberate misspellings.",
    "just_below_threshold": "Flags payments just below approval thresholds and same-vendor same-day splits.",
    "suspicious_descriptions": "Flags payments with descriptions containing fraud indicator keywords.",
}


def generate_ap_testing_memo(
    ap_result: dict[str, Any],
    filename: str = "ap_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for AP testing results.

    Args:
        ap_result: APTestingResult.to_dict() output
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description (e.g., "FY 2025")
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("ap_memo_generate", f"Generating AP testing memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "APT-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story = []
    composite = ap_result.get("composite_score", {})
    test_results = ap_result.get("test_results", [])
    data_quality = ap_result.get("data_quality", {})

    # 1. HEADER
    build_memo_header(story, styles, doc.width, "AP Payment Testing Memo", reference, client_name)

    # 2. SCOPE
    build_scope_section(story, styles, doc.width, composite, data_quality,
                        entry_label="Total Payments Tested", period_tested=period_tested)

    # 3. METHODOLOGY
    build_methodology_section(
        story, styles, doc.width, test_results, AP_TEST_DESCRIPTIONS,
        "The following automated tests were applied to the AP payment register "
        "in accordance with professional auditing standards (ISA 240, ISA 500, PCAOB AS 2401):",
    )

    # 4. RESULTS SUMMARY
    build_results_summary_section(story, styles, doc.width, composite, test_results,
                                  flagged_label="Total Payments Flagged")

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
            "Based on the automated AP payment testing procedures applied, "
            "the AP payment register exhibits a LOW risk profile. "
            "No material anomalies requiring further investigation were identified."
        )
    elif score_val < 25:
        assessment = (
            "Based on the automated AP payment testing procedures applied, "
            "the AP payment register exhibits an ELEVATED risk profile. "
            "Select flagged payments should be reviewed for proper authorization and documentation."
        )
    elif score_val < 50:
        assessment = (
            "Based on the automated AP payment testing procedures applied, "
            "the AP payment register exhibits a MODERATE risk profile. "
            "Flagged payments warrant focused review, particularly high-severity findings."
        )
    else:
        assessment = (
            "Based on the automated AP payment testing procedures applied, "
            "the AP payment register exhibits a HIGH risk profile. "
            "Significant anomalies were identified that require detailed investigation "
            "and may warrant expanded audit procedures."
        )

    story.append(Paragraph(assessment, styles['MemoBody']))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(story, styles, doc.width, prepared_by, reviewed_by, workpaper_date)

    # DISCLAIMER
    build_disclaimer(story, styles, domain="AP payment testing")

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("ap_memo_complete", f"AP memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
