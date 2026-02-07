"""
JE Testing Memo PDF Generator (Sprint 67, refactored Sprint 90)

Auto-generated testing memo per PCAOB AS 1215 / ISA 530.
Renaissance Ledger aesthetic consistent with existing PDF export.

Sections:
1. Header (client, period, preparer)
2. Scope (entries tested, GL source)
3. Methodology (tests applied with descriptions)
4. Results Summary (composite score, flags by test)
5. Findings (top flagged entries)
6. Benford's Law Analysis (distribution table)
7. Conclusion (professional assessment)
"""

import io
from typing import Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from pdf_generator import (
    ClassicalColors, LedgerRule,
    generate_reference_number, create_leader_dots,
)
from shared.memo_base import (
    create_memo_styles, build_memo_header, build_scope_section,
    build_methodology_section, build_results_summary_section,
    build_workpaper_signoff, build_disclaimer,
)
from security_utils import log_secure_operation


TEST_DESCRIPTIONS = {
    "unbalanced_entries": "Identifies journal entries where total debits do not equal total credits.",
    "missing_fields": "Flags entries missing critical fields (account, date, or amount).",
    "duplicate_entries": "Detects entries with identical account, date, and amount combinations.",
    "round_dollar_amounts": "Flags entries with suspiciously round dollar amounts ($10K+).",
    "unusual_amounts": "Uses z-score analysis to identify statistically unusual amounts per account.",
    "benford_law": "Tests first-digit distribution against Benford's Law expected frequencies.",
    "weekend_postings": "Flags entries posted on Saturdays or Sundays, weighted by amount.",
    "month_end_clustering": "Detects unusual concentration of entries in last 3 days of month.",
}


def generate_je_testing_memo(
    je_result: dict[str, Any],
    filename: str = "je_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for JE testing results.

    Args:
        je_result: JETestingResult.to_dict() output
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description (e.g., "FY 2025")
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("je_memo_generate", f"Generating JE testing memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "JET-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story = []
    composite = je_result.get("composite_score", {})
    test_results = je_result.get("test_results", [])
    data_quality = je_result.get("data_quality", {})
    benford = je_result.get("benford_result")

    # 1. HEADER
    build_memo_header(story, styles, doc.width, "Journal Entry Testing Memo", reference, client_name)

    # 2. SCOPE
    build_scope_section(story, styles, doc.width, composite, data_quality,
                        entry_label="Total Journal Entries Tested", period_tested=period_tested)

    # 3. METHODOLOGY
    build_methodology_section(
        story, styles, doc.width, test_results, TEST_DESCRIPTIONS,
        "The following automated tests were applied to the General Ledger extract "
        "in accordance with professional auditing standards (PCAOB AS 1215, ISA 530):",
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
            story.append(Paragraph(f"{i}. {finding}", styles['MemoBody']))
        story.append(Spacer(1, 8))

    # 6. BENFORD'S LAW ANALYSIS (JE-specific)
    if benford and benford.get("passed_prechecks"):
        section_num = "V" if top_findings else "IV"
        story.append(Paragraph(f"{section_num}. BENFORD'S LAW ANALYSIS", styles['MemoSection']))
        story.append(LedgerRule(doc.width))

        story.append(Paragraph(
            create_leader_dots("Eligible Entries", f"{benford.get('eligible_count', 0):,}"),
            styles['MemoLeader'],
        ))
        story.append(Paragraph(
            create_leader_dots("MAD Score", f"{benford.get('mad', 0):.5f}"),
            styles['MemoLeader'],
        ))
        conformity = benford.get("conformity_level", "").replace("_", " ").title()
        story.append(Paragraph(
            create_leader_dots("Conformity Level", conformity),
            styles['MemoLeader'],
        ))
        story.append(Spacer(1, 6))

        expected = benford.get("expected_distribution", {})
        actual = benford.get("actual_distribution", {})
        deviation = benford.get("deviation_by_digit", {})

        if expected and actual:
            benford_data = [["Digit", "Expected", "Actual", "Deviation"]]
            for d in range(1, 10):
                key = str(d)
                exp_val = expected.get(key, 0)
                act_val = actual.get(key, 0)
                dev_val = deviation.get(key, 0)
                benford_data.append([
                    str(d),
                    f"{exp_val:.2%}",
                    f"{act_val:.2%}",
                    f"{dev_val:+.2%}",
                ])

            benford_table = Table(benford_data, colWidths=[0.8 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
            benford_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(benford_table)
        story.append(Spacer(1, 8))

    # 7. CONCLUSION
    conclusion_num = "VI" if (benford and benford.get("passed_prechecks")) else ("V" if top_findings else "IV")
    story.append(Paragraph(f"{conclusion_num}. CONCLUSION", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    score_val = composite.get("score", 0)
    if score_val < 10:
        assessment = (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract exhibits a LOW risk profile. "
            "No material anomalies requiring further investigation were identified."
        )
    elif score_val < 25:
        assessment = (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract exhibits an ELEVATED risk profile. "
            "Select flagged entries should be reviewed for proper authorization and documentation."
        )
    elif score_val < 50:
        assessment = (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract exhibits a MODERATE risk profile. "
            "Flagged entries warrant focused review, particularly high-severity findings."
        )
    else:
        assessment = (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract exhibits a HIGH risk profile. "
            "Significant anomalies were identified that require detailed investigation "
            "and may warrant expanded audit procedures."
        )

    story.append(Paragraph(assessment, styles['MemoBody']))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(story, styles, doc.width, prepared_by, reviewed_by, workpaper_date)

    # DISCLAIMER
    build_disclaimer(story, styles, domain="journal entry testing")

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("je_memo_complete", f"JE memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
