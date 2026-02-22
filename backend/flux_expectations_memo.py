"""
Paciolus — ISA 520 Flux Expectations Memo Generator
Sprint 297: Phase XL

Renders a PDF documenting auditor-authored expectations alongside observed
flux variances. Pattern B (custom SimpleDocTemplate) following population_profile_memo.py.

CRITICAL GUARDRAIL: Expectation fields are user-authored text only.
Paciolus NEVER auto-populates these fields. The memo explicitly states
that expectations are practitioner-documented, not system-generated.

Sections: Header → ISA 520 Disclaimer → Scope → Expectation Table →
          Workpaper Sign-Off
"""

from typing import Optional

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_generator import ClassicalColors, DoubleRule, LedgerRule, create_leader_dots, format_classical_date
from shared.memo_base import build_disclaimer, build_intelligence_stamp, build_workpaper_signoff, create_memo_styles


def generate_flux_expectations_memo(
    flux_result: dict,
    expectations: dict[str, dict],
    filename: str = "flux_analysis",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate ISA 520 Flux Expectations Memo PDF.

    Args:
        flux_result: Dict with 'items' and 'summary' from FluxResultInput.
        expectations: {account_name: {"auditor_expectation": str, "auditor_explanation": str}}.
        filename: Source filename.
        client_name: Optional client name for header.
        period_tested: Optional period label.
        prepared_by: Preparer name for sign-off.
        reviewed_by: Reviewer name for sign-off.
        workpaper_date: Date for sign-off.

    Returns:
        PDF bytes.
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
    story.append(Paragraph("ISA 520 Analytical Procedures — Expectation Documentation", styles['MemoTitle']))
    if client_name:
        story.append(Paragraph(client_name, styles['MemoSubtitle']))
    story.append(Paragraph(
        f"{format_classical_date()} &nbsp;&bull;&nbsp; WP-FE-001",
        styles['MemoRef'],
    ))
    story.append(DoubleRule(doc_width))
    story.append(Spacer(1, 12))

    # ── ISA 520 Disclaimer (MANDATORY, non-removable) ──
    story.append(Paragraph("PRACTITIONER NOTICE", styles['MemoSection']))
    story.append(LedgerRule(doc_width))
    disclaimer_text = (
        "The expectation narratives in this workpaper are authored entirely by the practitioner. "
        "Paciolus does not generate, suggest, or pre-populate expectation text. "
        "The observed variances are computed from uploaded trial balance data. "
        "ISA 520 requires the auditor to develop an expectation of recorded amounts "
        "before comparing to actual results. This memo documents that process."
    )
    story.append(Paragraph(disclaimer_text, styles['MemoBody']))
    story.append(Spacer(1, 12))

    # ── I. SCOPE ──
    story.append(Paragraph("I. SCOPE", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

    summary = flux_result.get("summary", {})
    items = flux_result.get("items", [])

    scope_lines = [
        create_leader_dots("Source File", filename),
        create_leader_dots("Total Accounts Compared", f"{summary.get('total_items', len(items)):,}"),
        create_leader_dots("High Risk Items", f"{summary.get('high_risk_count', 0):,}"),
        create_leader_dots("Medium Risk Items", f"{summary.get('medium_risk_count', 0):,}"),
        create_leader_dots("Materiality Threshold", f"${summary.get('threshold', 0):,.0f}"),
        create_leader_dots("Expectations Documented", f"{len(expectations):,}"),
    ]
    if period_tested:
        scope_lines.insert(1, create_leader_dots("Period Tested", period_tested))

    for line in scope_lines:
        story.append(Paragraph(line, styles['MemoBody']))
    story.append(Spacer(1, 12))

    # ── II. PRACTITIONER EXPECTATIONS VS. OBSERVED VARIANCES ──
    story.append(Paragraph("II. PRACTITIONER EXPECTATIONS VS. OBSERVED VARIANCES", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

    # Filter to items that have expectations documented
    items_with_expectations = [
        item for item in items
        if item.get("account", "") in expectations
    ]

    if not items_with_expectations:
        story.append(Paragraph(
            "No expectations have been documented for this analysis.",
            styles['MemoBody'],
        ))
    else:
        for item in items_with_expectations:
            account = item.get("account", "Unknown")
            exp_data = expectations.get(account, {})
            expectation_text = exp_data.get("auditor_expectation", "").strip()
            explanation_text = exp_data.get("auditor_explanation", "").strip()

            # Account header
            story.append(Spacer(1, 6))
            story.append(Paragraph(
                f"<b>{account}</b> &nbsp;({item.get('type', 'Unknown')})",
                styles['MemoBody'],
            ))

            # Observed variance table
            delta = item.get("delta_amount", 0)
            pct = item.get("display_percent", "N/A")
            risk = item.get("risk_level", "low")
            indicators = item.get("variance_indicators", [])

            obs_data = [
                ["Prior", f"${item.get('prior', 0):,.2f}"],
                ["Current", f"${item.get('current', 0):,.2f}"],
                ["Variance", f"${delta:,.2f} ({pct})"],
                ["Risk Level", risk.upper()],
                ["Indicators", ", ".join(indicators) if indicators else "None"],
            ]
            obs_table = Table(obs_data, colWidths=[1.5 * inch, doc_width - 1.5 * inch])
            obs_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Courier'),
                ('TEXTCOLOR', (0, 0), (-1, -1), ClassicalColors.OBSIDIAN),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(obs_table)

            # Practitioner expectation
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>Practitioner Expectation:</b>", styles['MemoBody']))
            story.append(Paragraph(
                expectation_text if expectation_text else "<i>[Not documented]</i>",
                styles['MemoBody'],
            ))

            # Practitioner explanation
            story.append(Paragraph("<b>Explanation of Variance:</b>", styles['MemoBody']))
            story.append(Paragraph(
                explanation_text if explanation_text else "<i>[Not documented]</i>",
                styles['MemoBody'],
            ))

            story.append(LedgerRule(doc_width))

    story.append(Spacer(1, 12))

    # ── III. WORKPAPER SIGN-OFF ──
    story.append(Paragraph("III. WORKPAPER SIGN-OFF", styles['MemoSection']))
    story.append(LedgerRule(doc_width))
    build_workpaper_signoff(
        story,
        styles,
        doc_width,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
    )
    story.append(Spacer(1, 12))

    # ── Intelligence Stamp ──
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # ── IV. DISCLAIMER ──
    story.append(Paragraph("IV. DISCLAIMER", styles['MemoSection']))
    story.append(LedgerRule(doc_width))
    build_disclaimer(
        story,
        styles,
        domain="Flux & Variance Intelligence",
        isa_reference="ISA 520 (Analytical Procedures) and ISA 330 (Auditor's Responses to Assessed Risks)",
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
