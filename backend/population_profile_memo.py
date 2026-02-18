"""
Paciolus — Population Profile PDF Memo Generator
Sprint 287: Phase XXXIX

Custom memo using memo_base.py primitives. Pattern B (custom sections).
Sections: Header → Scope → Descriptive Statistics → Magnitude Distribution →
          Concentration Analysis → Workpaper Sign-Off → Disclaimer
"""

from typing import Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_generator import ClassicalColors, DoubleRule, LedgerRule, create_leader_dots, format_classical_date
from shared.memo_base import build_disclaimer, build_workpaper_signoff, create_memo_styles


def generate_population_profile_memo(
    profile_result: dict,
    filename: str = "population_profile",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a Population Profile Report PDF memo.

    Args:
        profile_result: Dict from PopulationProfileReport.to_dict()
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
    story.append(Paragraph("TB Population Profile Report", styles['MemoTitle']))
    if client_name:
        story.append(Paragraph(client_name, styles['MemoSubtitle']))
    story.append(Paragraph(
        f"{format_classical_date()} &nbsp;&bull;&nbsp; WP-PP-001",
        styles['MemoRef'],
    ))
    story.append(DoubleRule(doc_width))
    story.append(Spacer(1, 12))

    # ── I. SCOPE ──
    story.append(Paragraph("I. SCOPE", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

    account_count = profile_result.get("account_count", 0)
    total_abs = profile_result.get("total_abs_balance", 0)
    gini = profile_result.get("gini_coefficient", 0)
    gini_interp = profile_result.get("gini_interpretation", "Low")

    scope_lines = [
        create_leader_dots("Source File", filename),
        create_leader_dots("Unique Accounts", f"{account_count:,}"),
        create_leader_dots("Total Population Value", f"${total_abs:,.2f}"),
        create_leader_dots("Gini Coefficient", f"{gini:.4f} ({gini_interp})"),
    ]
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))

    for line in scope_lines:
        story.append(Paragraph(line, styles['MemoLeader']))
    story.append(Spacer(1, 8))

    # ── II. DESCRIPTIVE STATISTICS ──
    story.append(Paragraph("II. DESCRIPTIVE STATISTICS", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

    stats_data = [["Statistic", "Value"]]
    stats_data.append(["Mean (Absolute Balance)", f"${profile_result.get('mean_abs_balance', 0):,.2f}"])
    stats_data.append(["Median (Absolute Balance)", f"${profile_result.get('median_abs_balance', 0):,.2f}"])
    stats_data.append(["Standard Deviation", f"${profile_result.get('std_dev_abs_balance', 0):,.2f}"])
    stats_data.append(["Minimum", f"${profile_result.get('min_abs_balance', 0):,.2f}"])
    stats_data.append(["Maximum", f"${profile_result.get('max_abs_balance', 0):,.2f}"])
    stats_data.append(["25th Percentile (P25)", f"${profile_result.get('p25', 0):,.2f}"])
    stats_data.append(["75th Percentile (P75)", f"${profile_result.get('p75', 0):,.2f}"])

    stats_table = Table(stats_data, colWidths=[3.5 * inch, 3.0 * inch])
    stats_table.setStyle(TableStyle([
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
    story.append(stats_table)
    story.append(Spacer(1, 8))

    # ── III. MAGNITUDE DISTRIBUTION ──
    buckets = profile_result.get("buckets", [])
    if buckets:
        story.append(Paragraph("III. MAGNITUDE DISTRIBUTION", styles['MemoSection']))
        story.append(LedgerRule(doc_width))

        bucket_data = [["Bucket", "Count", "% of Accounts", "Sum of Balances"]]
        for b in buckets:
            if isinstance(b, dict):
                bucket_data.append([
                    b.get("label", ""),
                    str(b.get("count", 0)),
                    f"{b.get('percent_count', 0):.1f}%",
                    f"${b.get('sum_abs', 0):,.2f}",
                ])

        bucket_table = Table(bucket_data, colWidths=[1.8 * inch, 1.0 * inch, 1.5 * inch, 2.2 * inch])
        bucket_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (1, 1), (1, -1), 'Courier'),
            ('FONTNAME', (3, 1), (3, -1), 'Courier'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
        ]))
        story.append(bucket_table)
        story.append(Spacer(1, 8))

    # ── IV. CONCENTRATION ANALYSIS ──
    top_accounts = profile_result.get("top_accounts", [])
    story.append(Paragraph("IV. CONCENTRATION ANALYSIS", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

    # Gini callout
    story.append(Paragraph(
        f"The Gini coefficient of <b>{gini:.4f}</b> indicates <b>{gini_interp}</b> concentration. "
        "A Gini of 0 means all accounts have equal balances; 1.0 means one account holds all value. "
        "Higher concentration warrants targeted substantive procedures on dominant accounts.",
        styles['MemoBody'],
    ))
    story.append(Spacer(1, 6))

    if top_accounts:
        top_data = [["Rank", "Account", "Category", "Net Balance", "% of Total"]]
        for t in top_accounts:
            if isinstance(t, dict):
                top_data.append([
                    str(t.get("rank", "")),
                    Paragraph(str(t.get("account", ""))[:40], styles['MemoTableCell']),
                    t.get("category", "Unknown"),
                    f"${t.get('net_balance', 0):,.2f}",
                    f"{t.get('percent_of_total', 0):.1f}%",
                ])

        top_table = Table(top_data, colWidths=[0.5 * inch, 2.5 * inch, 1.2 * inch, 1.5 * inch, 0.8 * inch])
        top_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (3, 0), (4, -1), 'RIGHT'),
            ('FONTNAME', (3, 1), (3, -1), 'Courier'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
        ]))
        story.append(top_table)

    story.append(Spacer(1, 12))

    # ── Workpaper Sign-Off ──
    build_workpaper_signoff(story, styles, doc_width, prepared_by, reviewed_by, workpaper_date)

    # ── Disclaimer ──
    build_disclaimer(
        story, styles,
        domain="population profile analysis",
        isa_reference="ISA 520 (Analytical Procedures) and ISA 530 (Audit Sampling)",
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
