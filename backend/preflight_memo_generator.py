"""
Paciolus — Pre-Flight Report PDF Memo Generator
Sprint 283: Phase XXXVIII

Custom memo using memo_base.py primitives. Not TestingMemoConfig — preflight
is a diagnostic check, not a testing tool.

Sections: Header → Scope → Column Detection → Issues → Workpaper Sign-Off → Disclaimer
"""

from typing import Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_generator import ClassicalColors, DoubleRule, LedgerRule, create_leader_dots, format_classical_date
from shared.memo_base import build_disclaimer, build_intelligence_stamp, build_workpaper_signoff, create_memo_styles


def generate_preflight_memo(
    preflight_result: dict,
    filename: str = "preflight_report",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a Pre-Flight Report PDF memo.

    Args:
        preflight_result: Dict from PreFlightReport.to_dict()
        filename: Source filename
        client_name: Optional client name for header
        period_tested: Optional period label
        prepared_by: Preparer name for sign-off
        reviewed_by: Reviewer name for sign-off
        workpaper_date: Date for sign-off

    Returns:
        PDF bytes
    """
    import io

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(8.5 * inch, 11 * inch),
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    doc_width = doc.width
    styles = create_memo_styles()
    story: list = []

    # ── Header ──
    story.append(Paragraph("Data Quality Pre-Flight Report", styles['MemoTitle']))
    if client_name:
        story.append(Paragraph(client_name, styles['MemoSubtitle']))
    story.append(Paragraph(
        f"{format_classical_date()} &nbsp;&bull;&nbsp; WP-PF-001",
        styles['MemoRef'],
    ))
    story.append(DoubleRule(doc_width))
    story.append(Spacer(1, 12))

    # ── I. SCOPE ──
    story.append(Paragraph("I. SCOPE", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

    readiness = preflight_result.get("readiness_score", 0)
    label = preflight_result.get("readiness_label", "Unknown")

    scope_lines = [
        create_leader_dots("Source File", filename),
        create_leader_dots("Total Rows", f"{preflight_result.get('row_count', 0):,}"),
        create_leader_dots("Total Columns", str(preflight_result.get("column_count", 0))),
        create_leader_dots("Readiness Score", f"{readiness:.1f} / 100"),
        create_leader_dots("Assessment", label),
    ]
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))

    for line in scope_lines:
        story.append(Paragraph(line, styles['MemoLeader']))
    story.append(Spacer(1, 8))

    # ── II. COLUMN DETECTION ──
    columns = preflight_result.get("columns", [])
    if columns:
        story.append(Paragraph("II. COLUMN DETECTION", styles['MemoSection']))
        story.append(LedgerRule(doc_width))

        col_data = [["Role", "Detected Column", "Confidence", "Status"]]
        for col in columns:
            conf = col.get("confidence", 0)
            col_data.append([
                col.get("role", "").title(),
                col.get("detected_name") or "—",
                f"{conf:.0%}",
                col.get("status", "").replace("_", " ").title(),
            ])

        col_table = Table(col_data, colWidths=[1.2 * inch, 2.5 * inch, 1.2 * inch, 1.5 * inch])
        col_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
        ]))
        story.append(col_table)
        story.append(Spacer(1, 8))

    # ── III. DATA QUALITY ISSUES ──
    issues = preflight_result.get("issues", [])
    story.append(Paragraph("III. DATA QUALITY ISSUES", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

    if not issues:
        story.append(Paragraph("No data quality issues detected.", styles['MemoBody']))
    else:
        issue_data = [["Category", "Severity", "Description", "Affected", "Remediation"]]
        for issue in sorted(issues, key=lambda i: {"high": 0, "medium": 1, "low": 2}.get(i.get("severity", "low"), 3)):
            issue_data.append([
                Paragraph(issue.get("category", "").replace("_", " ").title(), styles['MemoTableCell']),
                Paragraph(issue.get("severity", "").upper(), styles['MemoTableCell']),
                Paragraph(issue.get("message", ""), styles['MemoTableCell']),
                str(issue.get("affected_count", 0)),
                Paragraph(issue.get("remediation", "")[:200], styles['MemoTableCell']),
            ])

        issue_table = Table(issue_data, colWidths=[1.0 * inch, 0.7 * inch, 2.0 * inch, 0.6 * inch, 2.3 * inch])
        issue_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
        ]))
        story.append(issue_table)

    story.append(Spacer(1, 12))

    # ── Workpaper Sign-Off ──
    build_workpaper_signoff(story, styles, doc_width, prepared_by, reviewed_by, workpaper_date)

    # ── Intelligence Stamp ──
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # ── Disclaimer ──
    build_disclaimer(
        story, styles,
        domain="data quality assessment",
        isa_reference="ISA 500 (Audit Evidence) and ISA 330 (Auditor's Responses)",
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
