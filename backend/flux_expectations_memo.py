"""
Paciolus — ISA 520 Flux Expectations Memo Generator
Sprint 297: Phase XL | Sprint 514: Report Enrichment

Renders a PDF documenting auditor-authored expectations alongside observed
flux variances. Pattern B (custom SimpleDocTemplate) following population_profile_memo.py.

CRITICAL GUARDRAIL: Expectation fields are user-authored text only.
Paciolus NEVER auto-populates these fields. The memo explicitly states
that expectations are practitioner-documented, not system-generated.

Sections: Header -> ISA 520 Disclaimer -> Scope -> Completion Tracker ->
          Expectation Items (with stubs) -> Methodology -> References ->
          Sign-Off -> Intelligence Stamp -> Disclaimer
"""

from typing import Optional

from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_generator import (
    ClassicalColors,
    DoubleRule,
    LedgerRule,
    create_leader_dots,
    format_classical_date,
    generate_reference_number,
)
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import build_disclaimer, build_intelligence_stamp, create_memo_styles
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

# Badge colors
_AMBER = HexColor("#B8860B")
_AMBER_BG = HexColor("#FFF8DC")


def _risk_sort_key(item: dict) -> tuple:
    """Sort key: High Risk first, then Medium, then Low; within tier by abs(variance) desc."""
    risk = item.get("risk_level", "low").lower()
    order = {"high": 0, "medium": 1, "low": 2, "none": 3}
    return (order.get(risk, 3), -abs(item.get("delta_amount", 0)))


def _render_badge(text: str, styles: dict) -> Table:
    """Render a small amber badge with text."""
    badge = Table(
        [[Paragraph(f"<font color='#B8860B'><b>{text}</b></font>", styles["MemoBody"])]],
        colWidths=[None],
    )
    badge.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _AMBER_BG),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    badge.hAlign = "LEFT"
    return badge


def _render_conclusion_block(styles: dict) -> list:
    """Render the structured multi-option conclusion block."""
    elements = []
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("<b>Conclusion:</b>", styles["MemoBody"]))

    options = [
        "[ ] Variance explained \u2014 no further procedures required",
        "[ ] Variance partially explained \u2014 additional procedures planned (describe below)",
        "[ ] Variance unexplained \u2014 escalate to engagement partner",
        "[ ] Inconclusive \u2014 awaiting management response",
    ]
    for opt in options:
        elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;{opt}", styles["MemoBody"]))

    elements.append(Spacer(1, 4))
    elements.append(
        Paragraph(
            "Notes: ________________________________________________________",
            styles["MemoBody"],
        )
    )
    elements.append(
        Paragraph(
            "Initials: _______ &nbsp;&nbsp; Date: ___/___/______",
            styles["MemoBody"],
        )
    )
    return elements


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
    fiscal_year_end: Optional[str] = None,
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

    # Generate reference number (WP-FE prefix)
    reference = generate_reference_number().replace("PAC-", "WP-FE-")

    # ── Pre-compute completion metrics ──
    summary = flux_result.get("summary", {})
    items = flux_result.get("items", [])

    # All flagged items (high + medium risk)
    flagged_items = [item for item in items if item.get("risk_level", "low").lower() in ("high", "medium")]
    flagged_items.sort(key=_risk_sort_key)

    total_flagged = len(flagged_items)
    documented_count = sum(
        1
        for item in flagged_items
        if item.get("account", "") in expectations
        and expectations[item["account"]].get("auditor_expectation", "").strip()
    )
    pending_count = total_flagged - documented_count

    # Highest risk variance (first item after sort = highest risk, largest variance)
    highest_risk_item = flagged_items[0] if flagged_items else None
    highest_risk_label = ""
    if highest_risk_item:
        pct = highest_risk_item.get("display_percent", "N/A")
        delta = highest_risk_item.get("delta_amount", 0)
        acct = highest_risk_item.get("account", "Unknown")
        highest_risk_label = f"{acct} ({pct} / ${abs(delta):,.0f})"

    # Total unexplained variance (sum of abs(delta) for pending items)
    total_unexplained = sum(
        abs(item.get("delta_amount", 0))
        for item in flagged_items
        if item.get("account", "") not in expectations
        or not expectations.get(item.get("account", ""), {}).get("auditor_expectation", "").strip()
    )

    # ── Cover Page (diagonal color bands) ──
    logo_path = find_logo()
    cover_metadata = ReportMetadata(
        title="ISA 520 Flux & Expectation Documentation",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference=reference,
        fiscal_year_end=fiscal_year_end or "",
    )
    build_cover_page(story, styles, cover_metadata, doc_width, logo_path)

    # ── Header ──
    story.append(Paragraph("ISA 520 Analytical Procedures \u2014 Expectation Documentation", styles["MemoTitle"]))
    if client_name:
        story.append(Paragraph(client_name, styles["MemoSubtitle"]))
    story.append(
        Paragraph(
            f"{format_classical_date()} &nbsp;&bull;&nbsp; {reference}",
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
        "before comparing to actual results. This memo documents that process. "
        "Items marked \u26a0 PENDING require practitioner input before this workpaper "
        "may be considered complete for engagement file purposes."
    )
    story.append(Paragraph(disclaimer_text, styles["MemoBody"]))
    story.append(Spacer(1, 12))

    # ── I. SCOPE ──
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Source document transparency
    if source_document_title and filename:
        source_line = create_leader_dots("Source", f"{source_document_title} ({filename})")
    elif source_document_title:
        source_line = create_leader_dots("Source", source_document_title)
    else:
        source_line = create_leader_dots("Source File", filename)

    # Documented/pending badges
    exp_badge = f"{documented_count:,}"
    if pending_count > 0:
        exp_badge += f"  \u26a0 ({pending_count} pending)"

    scope_lines = [
        source_line,
        create_leader_dots("Total Accounts Compared", f"{summary.get('total_items', len(items)):,}"),
        create_leader_dots("High Risk Items", f"{summary.get('high_risk_count', 0):,}"),
        create_leader_dots("Medium Risk Items", f"{summary.get('medium_risk_count', 0):,}"),
        create_leader_dots("Materiality Threshold", f"${summary.get('threshold', 0):,.0f}"),
        create_leader_dots("Expectations Documented", exp_badge),
        create_leader_dots("Conclusions Documented", "0  \u26a0 (all pending)"),
    ]
    if highest_risk_label:
        scope_lines.append(create_leader_dots("Highest Risk Variance", highest_risk_label))
    if total_unexplained > 0:
        scope_lines.append(create_leader_dots("Total Unexplained Variance", f"${total_unexplained:,.0f}"))

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
    story.append(Paragraph("II. Practitioner Expectations vs. Observed Variances", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # ── Completion Status Tracker ──
    if total_flagged > 0:
        doc_pct = (documented_count / total_flagged * 100) if total_flagged else 0
        pend_pct = 100 - doc_pct

        # Text-based progress bar
        filled = int(doc_pct / 10)
        bar_doc = "\u2588" * filled + "\u2591" * (10 - filled)
        bar_pend = "\u2591" * 10

        tracker_data = [
            ["Expectation Documentation Status", ""],
            ["Total Flagged Items:", f"{total_flagged}"],
            ["Documented (Complete):", f"{documented_count}   {bar_doc}  {doc_pct:.1f}%"],
            ["Pending Practitioner Input:", f"{pending_count}   {bar_pend}  {pend_pct:.1f}%"],
        ]
        tracker_table = Table(
            tracker_data,
            colWidths=[2.5 * inch, doc_width - 2.5 * inch],
        )
        tracker_style = [
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 1), (1, -1), "Courier"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), ClassicalColors.OBSIDIAN),
            ("SPAN", (0, 0), (1, 0)),
            ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ("LINEBELOW", (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_DEEP),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
        ]
        tracker_table.setStyle(TableStyle(tracker_style))
        story.append(tracker_table)
        story.append(Spacer(1, 4))

        if pending_count > 0:
            story.append(
                Paragraph(
                    "<font color='#B8860B'><b>\u26a0 This workpaper is INCOMPLETE.</b> "
                    "All flagged items require expectation documentation before "
                    "the workpaper may be signed off.</font>",
                    styles["MemoBody"],
                )
            )
        story.append(Spacer(1, 8))

    if not flagged_items:
        story.append(
            Paragraph(
                "No high or medium risk accounts were identified in this analysis.",
                styles["MemoBody"],
            )
        )
    else:
        for item in flagged_items:
            account = item.get("account", "Unknown")
            account_note = item.get("account_note", "")
            exp_data = expectations.get(account, {})
            has_expectation = account in expectations and exp_data.get("auditor_expectation", "").strip()
            expectation_text = exp_data.get("auditor_expectation", "").strip() if has_expectation else ""
            explanation_text = exp_data.get("auditor_explanation", "").strip() if has_expectation else ""

            delta = item.get("delta_amount", 0)
            pct = item.get("display_percent", "N/A")
            risk = item.get("risk_level", "low")
            indicators = item.get("variance_indicators", [])

            # Account header with optional note
            story.append(Spacer(1, 6))
            label = f"<b>{account}</b>"
            if account_note:
                label += f" &nbsp;<i>{account_note}</i>"
            label += f" &nbsp;({item.get('type', 'Unknown')})"
            story.append(Paragraph(label, styles["MemoBody"]))

            # Status badge
            if not has_expectation:
                story.append(_render_badge("\u26a0 PENDING \u2014 Practitioner documentation required", styles))

            # Observed variance table
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
            if has_expectation:
                story.append(Paragraph(expectation_text, styles["MemoBody"]))
            else:
                story.append(
                    Paragraph(
                        "<i>[PRACTITIONER TO COMPLETE: Document your expectation of the recorded amount "
                        "prior to comparing to actual results, per ISA 520.5(a).]</i>",
                        styles["MemoBody"],
                    )
                )

            # Practitioner explanation
            story.append(Paragraph("<b>Explanation of Variance:</b>", styles["MemoBody"]))
            if has_expectation and explanation_text:
                story.append(Paragraph(explanation_text, styles["MemoBody"]))
            else:
                story.append(
                    Paragraph(
                        "<i>[PRACTITIONER TO COMPLETE: Explain the variance and assess whether it is "
                        "consistent with your expectation or requires further investigation.]</i>",
                        styles["MemoBody"],
                    )
                )

            # Structured conclusion block
            story.extend(_render_conclusion_block(styles))

            # Conclusion pending badge (always, since conclusions are fill-in)
            story.append(Spacer(1, 2))
            story.append(_render_badge("\u26a0 CONCLUSION PENDING", styles))

            # Optional footnote
            footnote = item.get("footnote", "")
            if footnote:
                story.append(Spacer(1, 4))
                story.append(Paragraph(f"<i>{footnote}</i>", styles["MemoBody"]))

            story.append(LedgerRule(doc_width))

    story.append(Spacer(1, 12))

    # ── Methodology ──
    build_methodology_statement(
        story,
        styles,
        doc_width,
        tool_domain="flux_analysis",
        framework=resolved_framework,
        domain_label="flux analysis expectations documentation",
    )

    # ── Authoritative References (before sign-off) ──
    build_authoritative_reference_block(
        story,
        styles,
        doc_width,
        tool_domain="flux_analysis",
        framework=resolved_framework,
        domain_label="flux analysis expectations documentation",
    )

    # ── III. FORMAL SIGN-OFF ──
    story.append(Paragraph("III. Formal Sign-Off", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Completion gating: DRAFT watermark when items pending
    if pending_count > 0:
        story.append(
            Paragraph(
                "<font size='14' color='#B8860B'><b>DRAFT \u2014 INCOMPLETE WORKPAPER</b></font>",
                styles["MemoBody"],
            )
        )
        story.append(
            Paragraph(
                "<i>This workpaper cannot be finalized until all expectation and conclusion fields are completed.</i>",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

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

    # ── Intelligence Stamp ──
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # ── IV. DISCLAIMER ──
    story.append(Paragraph("IV. Disclaimer", styles["MemoSection"]))
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
