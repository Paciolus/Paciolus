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

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_generator import ClassicalColors, DoubleRule, LedgerRule, create_leader_dots, format_classical_date
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import build_disclaimer, build_intelligence_stamp, build_workpaper_signoff, create_memo_styles
from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    draw_page_footer,
    find_logo,
)
from shared.scope_methodology import (
    build_authoritative_reference_block,
    build_methodology_statement,
    build_scope_statement,
)


def generate_flux_expectations_memo(
    flux_result: dict,
    expectations: dict[str, dict],
    filename: str = "flux_analysis",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
    include_signoff: bool = False,
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

    # ── Cover Page (diagonal color bands) ──
    logo_path = find_logo()
    cover_metadata = ReportMetadata(
        title="ISA 520 Analytical Procedures — Expectation Documentation",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
    )
    build_cover_page(story, styles, cover_metadata, doc_width, logo_path)

    # ── Header ──
    story.append(Paragraph("ISA 520 Analytical Procedures — Expectation Documentation", styles["MemoTitle"]))
    if client_name:
        story.append(Paragraph(client_name, styles["MemoSubtitle"]))
    story.append(
        Paragraph(
            f"{format_classical_date()} &nbsp;&bull;&nbsp; WP-FE-001",
            styles["MemoRef"],
        )
    )
    story.append(DoubleRule(doc_width))
    story.append(Spacer(1, 12))

    # ── ISA 520 Disclaimer (MANDATORY, non-removable) ──
    story.append(Paragraph("Practitioner Notice", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))
    disclaimer_text = (
        "The expectation narratives in this workpaper are authored entirely by the practitioner. "
        "Paciolus does not generate, suggest, or pre-populate expectation text. "
        "The observed variances are computed from uploaded trial balance data. "
        "ISA 520 requires the auditor to develop an expectation of recorded amounts "
        "before comparing to actual results. This memo documents that process."
    )
    story.append(Paragraph(disclaimer_text, styles["MemoBody"]))
    story.append(Spacer(1, 12))

    # ── I. SCOPE ──
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    summary = flux_result.get("summary", {})
    items = flux_result.get("items", [])

    # Source document transparency (Sprint 6)
    if source_document_title and filename:
        source_line = create_leader_dots("Source", f"{source_document_title} ({filename})")
    elif source_document_title:
        source_line = create_leader_dots("Source", source_document_title)
    else:
        source_line = create_leader_dots("Source File", filename)

    scope_lines = [
        source_line,
        create_leader_dots("Total Accounts Compared", f"{summary.get('total_items', len(items)):,}"),
        create_leader_dots("High Risk Items", f"{summary.get('high_risk_count', 0):,}"),
        create_leader_dots("Medium Risk Items", f"{summary.get('medium_risk_count', 0):,}"),
        create_leader_dots("Materiality Threshold", f"${summary.get('threshold', 0):,.0f}"),
        create_leader_dots("Expectations Documented", f"{len(expectations):,}"),
    ]
    if period_tested:
        scope_lines.insert(1, create_leader_dots("Period Tested", period_tested))

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoBody"]))
    story.append(Spacer(1, 12))

    build_scope_statement(
        story,
        styles,
        doc_width,
        tool_domain="flux_analysis",
        framework=resolved_framework,
        domain_label="flux analysis expectations documentation",
    )

    # ── II. PRACTITIONER EXPECTATIONS VS. OBSERVED VARIANCES ──
    # CONTENT-11: Show ALL high/medium risk accounts, not just those with documented expectations
    story.append(Paragraph("II. Practitioner Expectations vs. Observed Variances", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Filter to all high/medium risk items
    high_medium_items = [item for item in items if item.get("risk_level", "low").lower() in ("high", "medium")]

    if not high_medium_items:
        story.append(
            Paragraph(
                "No high or medium risk accounts were identified in this analysis.",
                styles["MemoBody"],
            )
        )
    else:
        for item in high_medium_items:
            account = item.get("account", "Unknown")
            exp_data = expectations.get(account, {})
            has_expectation = account in expectations
            expectation_text = exp_data.get("auditor_expectation", "").strip() if has_expectation else ""
            explanation_text = exp_data.get("auditor_explanation", "").strip() if has_expectation else ""

            # Account header
            story.append(Spacer(1, 6))
            story.append(
                Paragraph(
                    f"<b>{account}</b> &nbsp;({item.get('type', 'Unknown')})",
                    styles["MemoBody"],
                )
            )

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
            obs_table.setStyle(
                TableStyle(
                    [
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (1, 0), (1, -1), "Courier"),
                        ("TEXTCOLOR", (0, 0), (-1, -1), ClassicalColors.OBSIDIAN),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            story.append(obs_table)

            # Practitioner expectation
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>Practitioner Expectation:</b>", styles["MemoBody"]))
            story.append(
                Paragraph(
                    expectation_text if expectation_text else "\u2014",
                    styles["MemoBody"],
                )
            )

            # Practitioner explanation
            story.append(Paragraph("<b>Explanation of Variance:</b>", styles["MemoBody"]))
            story.append(
                Paragraph(
                    explanation_text if explanation_text else "\u2014",
                    styles["MemoBody"],
                )
            )

            # Per-account conclusion placeholder (CONTENT-11)
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(
                    "[ ] Conclusion: _______________________________________________",
                    styles["MemoBody"],
                )
            )

            story.append(LedgerRule(doc_width))

    story.append(Spacer(1, 12))

    # ── Methodology & Authoritative References ──
    build_methodology_statement(
        story,
        styles,
        doc_width,
        tool_domain="flux_analysis",
        framework=resolved_framework,
        domain_label="flux analysis expectations documentation",
    )
    build_authoritative_reference_block(
        story,
        styles,
        doc_width,
        tool_domain="flux_analysis",
        framework=resolved_framework,
        domain_label="flux analysis expectations documentation",
    )

    # ── III. WORKPAPER SIGN-OFF ──
    story.append(Paragraph("III. Workpaper Sign-Off", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))
    build_workpaper_signoff(
        story,
        styles,
        doc_width,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        include_signoff=include_signoff,
    )
    story.append(Spacer(1, 12))

    # ── Intelligence Stamp ──
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # ── IV. FORMAL SIGN-OFF (CONTENT-11) ──
    story.append(Paragraph("IV. Formal Sign-Off", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    signoff_data = [
        ["Role", "Name", "Signature", "Date"],
        ["Prepared by", prepared_by or "_______________", "", "____/____/________"],
        ["Reviewed by", reviewed_by or "_______________", "", "____/____/________"],
        ["Partner", "_______________", "", "____/____/________"],
    ]
    signoff_table = Table(
        signoff_data,
        colWidths=[1.2 * inch, 2.0 * inch, 2.0 * inch, 1.5 * inch],
    )
    signoff_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(signoff_table)
    story.append(Spacer(1, 12))

    # ── V. DISCLAIMER ──
    story.append(Paragraph("V. Disclaimer", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))
    build_disclaimer(
        story,
        styles,
        domain="Flux & Variance Intelligence",
        isa_reference="ISA 520 (Analytical Procedures) and ISA 330 (Auditor's Responses to Assessed Risks)",
    )

    doc.build(story, onFirstPage=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
