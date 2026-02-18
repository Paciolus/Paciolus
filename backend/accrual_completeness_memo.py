"""
Paciolus — Accrual Completeness Estimator PDF Memo Generator
Sprint 290: Phase XXXIX

Custom memo using memo_base.py primitives. Pattern B (custom sections).
Sections: Header → Scope → Accrual Accounts → Run-Rate Analysis (conditional) →
          Workpaper Sign-Off → Disclaimer

ISA 520 documentation structure. Guardrail: descriptive metrics only.
"""

from typing import Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_generator import ClassicalColors, DoubleRule, LedgerRule, create_leader_dots, format_classical_date
from shared.memo_base import build_disclaimer, build_workpaper_signoff, create_memo_styles


def generate_accrual_completeness_memo(
    report_result: dict,
    filename: str = "accrual_completeness",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate an Accrual Completeness Estimator PDF memo.

    Args:
        report_result: Dict from AccrualCompletenessReport.to_dict()
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
    story.append(Paragraph("Accrual Completeness Estimator", styles['MemoTitle']))
    if client_name:
        story.append(Paragraph(client_name, styles['MemoSubtitle']))
    story.append(Paragraph(
        f"{format_classical_date()} &nbsp;&bull;&nbsp; WP-ACE-001",
        styles['MemoRef'],
    ))
    story.append(DoubleRule(doc_width))
    story.append(Spacer(1, 12))

    # ── I. SCOPE ──
    story.append(Paragraph("I. SCOPE", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

    accrual_accounts = report_result.get("accrual_accounts", [])
    total_accrued = report_result.get("total_accrued_balance", 0)
    accrual_count = report_result.get("accrual_account_count", 0)
    monthly_run_rate = report_result.get("monthly_run_rate")
    ratio = report_result.get("accrual_to_run_rate_pct")
    threshold = report_result.get("threshold_pct", 50)
    below_threshold = report_result.get("below_threshold", False)
    prior_available = report_result.get("prior_available", False)
    prior_opex = report_result.get("prior_operating_expenses")

    scope_lines = [
        create_leader_dots("Source File", filename),
        create_leader_dots("Accrual Accounts Identified", str(accrual_count)),
        create_leader_dots("Total Accrued Balance", f"${total_accrued:,.2f}"),
        create_leader_dots("Prior Period Data", "Included" if prior_available else "Not provided"),
        create_leader_dots("Threshold", f"{threshold:.0f}%"),
    ]
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))
    if prior_available and monthly_run_rate is not None:
        scope_lines.append(create_leader_dots("Monthly Run-Rate", f"${monthly_run_rate:,.2f}"))
    if ratio is not None:
        scope_lines.append(create_leader_dots("Accrual-to-Run-Rate", f"{ratio:.1f}%"))

    for line in scope_lines:
        story.append(Paragraph(line, styles['MemoLeader']))
    story.append(Spacer(1, 8))

    # ── II. ACCRUAL ACCOUNTS ──
    if accrual_accounts:
        story.append(Paragraph("II. ACCRUAL ACCOUNTS", styles['MemoSection']))
        story.append(LedgerRule(doc_width))

        acct_data = [["Account", "Balance", "Matched Keyword"]]
        for a in accrual_accounts:
            if isinstance(a, dict):
                acct_data.append([
                    Paragraph(str(a.get("account_name", ""))[:50], styles['MemoTableCell']),
                    f"${a.get('balance', 0):,.2f}",
                    a.get("matched_keyword", ""),
                ])

        # Total row
        acct_data.append(["TOTAL", f"${total_accrued:,.2f}", ""])

        acct_table = Table(acct_data, colWidths=[3.0 * inch, 2.0 * inch, 1.5 * inch])
        acct_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -2), 'Times-Roman'),
            ('FONTNAME', (0, -1), (-1, -1), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, -2), (-1, -2), 0.5, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 1), (-1, -2), 0.25, ClassicalColors.LEDGER_RULE),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (1, 1), (1, -1), 'Courier'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
        ]))
        story.append(acct_table)
        story.append(Spacer(1, 8))

    # ── III. RUN-RATE ANALYSIS (conditional) ──
    if prior_available and monthly_run_rate is not None:
        story.append(Paragraph("III. RUN-RATE ANALYSIS", styles['MemoSection']))
        story.append(LedgerRule(doc_width))

        analysis_data = [["Metric", "Value"]]
        analysis_data.append(["Prior Operating Expenses (Annual)", f"${prior_opex:,.2f}" if prior_opex else "N/A"])
        analysis_data.append(["Monthly Run-Rate", f"${monthly_run_rate:,.2f}"])
        analysis_data.append(["Total Accrued Balance", f"${total_accrued:,.2f}"])
        analysis_data.append(["Accrual-to-Run-Rate Ratio", f"{ratio:.1f}%" if ratio is not None else "N/A"])
        analysis_data.append(["Threshold", f"{threshold:.0f}%"])
        analysis_data.append(["Below Threshold", "Yes" if below_threshold else "No"])

        analysis_table = Table(analysis_data, colWidths=[3.5 * inch, 3.0 * inch])
        analysis_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (1, 1), (1, -1), 'Courier'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
        ]))
        story.append(analysis_table)
        story.append(Spacer(1, 8))

    # ── Narrative ──
    narrative = report_result.get("narrative", "")
    if narrative:
        story.append(Paragraph("NARRATIVE", styles['MemoSection']))
        story.append(LedgerRule(doc_width))
        story.append(Paragraph(narrative, styles['MemoBody']))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 12))

    # ── Workpaper Sign-Off ──
    build_workpaper_signoff(story, styles, doc_width, prepared_by, reviewed_by, workpaper_date)

    # ── Disclaimer ──
    build_disclaimer(
        story, styles,
        domain="accrual completeness estimation",
        isa_reference="ISA 520 (Analytical Procedures)",
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
