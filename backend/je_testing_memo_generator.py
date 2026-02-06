"""
JE Testing Memo PDF Generator (Sprint 67)

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
from datetime import datetime, UTC
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable
)

from pdf_generator import (
    ClassicalColors, DoubleRule, LedgerRule,
    format_classical_date, generate_reference_number,
    create_leader_dots, _add_or_replace_style,
)
from security_utils import log_secure_operation


# =============================================================================
# Risk tier display mapping
# =============================================================================

RISK_TIER_DISPLAY = {
    "low": ("LOW RISK", ClassicalColors.SAGE),
    "elevated": ("ELEVATED", ClassicalColors.GOLD_INSTITUTIONAL),
    "moderate": ("MODERATE", ClassicalColors.GOLD_INSTITUTIONAL),
    "high": ("HIGH RISK", ClassicalColors.CLAY),
    "critical": ("CRITICAL", ClassicalColors.CLAY),
}

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


# =============================================================================
# Style creation
# =============================================================================

def _create_memo_styles() -> dict:
    """Create styles for the JE Testing Memo."""
    styles = getSampleStyleSheet()

    memo_styles = [
        ParagraphStyle(
            'MemoTitle', fontName='Times-Bold', fontSize=24,
            textColor=ClassicalColors.OBSIDIAN_DEEP, alignment=TA_CENTER,
            spaceAfter=6,
        ),
        ParagraphStyle(
            'MemoSubtitle', fontName='Times-Roman', fontSize=11,
            textColor=ClassicalColors.OBSIDIAN_500, alignment=TA_CENTER,
            spaceAfter=4,
        ),
        ParagraphStyle(
            'MemoRef', fontName='Times-Italic', fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_500, alignment=TA_CENTER,
            spaceAfter=12,
        ),
        ParagraphStyle(
            'MemoSection', fontName='Times-Bold', fontSize=11,
            textColor=ClassicalColors.OBSIDIAN_DEEP, spaceAfter=6,
            spaceBefore=16,
        ),
        ParagraphStyle(
            'MemoBody', fontName='Times-Roman', fontSize=10,
            textColor=ClassicalColors.OBSIDIAN_DEEP, spaceAfter=4,
            leading=14,
        ),
        ParagraphStyle(
            'MemoBodySmall', fontName='Times-Roman', fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_500, spaceAfter=3,
            leading=12,
        ),
        ParagraphStyle(
            'MemoLeader', fontName='Courier', fontSize=10,
            textColor=ClassicalColors.OBSIDIAN_DEEP, spaceAfter=2,
        ),
        ParagraphStyle(
            'MemoTableCell', fontName='Times-Roman', fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_DEEP, leading=11,
        ),
        ParagraphStyle(
            'MemoTableHeader', fontName='Times-Bold', fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_DEEP, leading=11,
        ),
        ParagraphStyle(
            'MemoFooter', fontName='Times-Roman', fontSize=8,
            textColor=ClassicalColors.OBSIDIAN_500, alignment=TA_CENTER,
        ),
        ParagraphStyle(
            'MemoDisclaimer', fontName='Times-Roman', fontSize=7,
            textColor=ClassicalColors.OBSIDIAN_500, alignment=TA_CENTER,
            leading=9, spaceAfter=4,
        ),
    ]

    style_dict = {}
    for s in memo_styles:
        _add_or_replace_style(styles, s)
        style_dict[s.name] = s

    return style_dict


# =============================================================================
# Generator
# =============================================================================

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

    styles = _create_memo_styles()
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

    # -------------------------------------------------------------------------
    # 1. HEADER
    # -------------------------------------------------------------------------
    story.append(Paragraph("Journal Entry Testing Memo", styles['MemoTitle']))
    if client_name:
        story.append(Paragraph(client_name, styles['MemoSubtitle']))
    story.append(Paragraph(
        f"{format_classical_date()} &nbsp;&bull;&nbsp; {reference}",
        styles['MemoRef'],
    ))
    story.append(DoubleRule(doc.width))
    story.append(Spacer(1, 12))

    # -------------------------------------------------------------------------
    # 2. SCOPE
    # -------------------------------------------------------------------------
    story.append(Paragraph("I. SCOPE", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    total_entries = composite.get("total_entries", 0)
    tests_run = composite.get("tests_run", 0)

    scope_lines = [
        create_leader_dots("Total Journal Entries Tested", f"{total_entries:,}"),
        create_leader_dots("Tests Applied", str(tests_run)),
        create_leader_dots("Data Quality Score", f"{data_quality.get('completeness_score', 0):.0f}%"),
    ]
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))

    for line in scope_lines:
        story.append(Paragraph(line, styles['MemoLeader']))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # 3. METHODOLOGY
    # -------------------------------------------------------------------------
    story.append(Paragraph("II. METHODOLOGY", styles['MemoSection']))
    story.append(LedgerRule(doc.width))
    story.append(Paragraph(
        "The following automated tests were applied to the General Ledger extract "
        "in accordance with professional auditing standards (PCAOB AS 1215, ISA 530):",
        styles['MemoBody'],
    ))

    method_data = [["Test", "Tier", "Description"]]
    for tr in test_results:
        desc = TEST_DESCRIPTIONS.get(tr["test_key"], tr.get("description", ""))
        # Wrap in Paragraph for text wrapping
        method_data.append([
            Paragraph(tr["test_name"], styles['MemoTableCell']),
            Paragraph(tr["test_tier"].title(), styles['MemoTableCell']),
            Paragraph(desc[:120], styles['MemoTableCell']),
        ])

    method_table = Table(method_data, colWidths=[1.5 * inch, 0.8 * inch, 4.3 * inch])
    method_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
    ]))
    story.append(method_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # 4. RESULTS SUMMARY
    # -------------------------------------------------------------------------
    story.append(Paragraph("III. RESULTS SUMMARY", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    risk_tier = composite.get("risk_tier", "low")
    tier_label, tier_color = RISK_TIER_DISPLAY.get(risk_tier, ("UNKNOWN", ClassicalColors.OBSIDIAN_500))

    story.append(Paragraph(
        create_leader_dots("Composite Risk Score", f"{composite.get('score', 0):.1f} / 100"),
        styles['MemoLeader'],
    ))
    story.append(Paragraph(
        create_leader_dots("Risk Tier", tier_label),
        styles['MemoLeader'],
    ))
    story.append(Paragraph(
        create_leader_dots("Total Entries Flagged", f"{composite.get('total_flagged', 0):,}"),
        styles['MemoLeader'],
    ))
    story.append(Paragraph(
        create_leader_dots("Overall Flag Rate", f"{composite.get('flag_rate', 0):.1%}"),
        styles['MemoLeader'],
    ))

    sev = composite.get("flags_by_severity", {})
    story.append(Paragraph(
        create_leader_dots("High Severity Flags", str(sev.get("high", 0))),
        styles['MemoLeader'],
    ))
    story.append(Paragraph(
        create_leader_dots("Medium Severity Flags", str(sev.get("medium", 0))),
        styles['MemoLeader'],
    ))
    story.append(Paragraph(
        create_leader_dots("Low Severity Flags", str(sev.get("low", 0))),
        styles['MemoLeader'],
    ))
    story.append(Spacer(1, 6))

    # Results by test table
    results_data = [["Test", "Flagged", "Rate", "Severity"]]
    for tr in sorted(test_results, key=lambda t: t.get("flag_rate", 0), reverse=True):
        results_data.append([
            tr["test_name"],
            str(tr["entries_flagged"]),
            f"{tr['flag_rate']:.1%}",
            tr["severity"].upper(),
        ])

    results_table = Table(results_data, colWidths=[2.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch])
    results_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
    ]))
    story.append(results_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # 5. TOP FINDINGS
    # -------------------------------------------------------------------------
    top_findings = composite.get("top_findings", [])
    if top_findings:
        story.append(Paragraph("IV. KEY FINDINGS", styles['MemoSection']))
        story.append(LedgerRule(doc.width))
        for i, finding in enumerate(top_findings[:5], 1):
            story.append(Paragraph(f"{i}. {finding}", styles['MemoBody']))
        story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # 6. BENFORD'S LAW ANALYSIS
    # -------------------------------------------------------------------------
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

        # Distribution table
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

    # -------------------------------------------------------------------------
    # 7. CONCLUSION
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # WORKPAPER SIGN-OFF
    # -------------------------------------------------------------------------
    if prepared_by or reviewed_by:
        story.append(LedgerRule(doc.width))
        signoff_data = [["", "Name", "Date"]]
        wp_date = workpaper_date or format_classical_date()
        if prepared_by:
            signoff_data.append(["Prepared By:", prepared_by, wp_date])
        if reviewed_by:
            signoff_data.append(["Reviewed By:", reviewed_by, ""])
        signoff_table = Table(signoff_data, colWidths=[1.2 * inch, 3.0 * inch, 2.0 * inch])
        signoff_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(signoff_table)
        story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # DISCLAIMER
    # -------------------------------------------------------------------------
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "This memo documents automated journal entry testing procedures. "
        "Results should be interpreted in the context of the specific engagement "
        "and are not a substitute for professional judgment. "
        "Generated by Paciolus — Zero-Storage Audit Intelligence.",
        styles['MemoDisclaimer'],
    ))

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("je_memo_complete", f"JE memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
