"""
Multi-Period Comparison Memo PDF Generator (Sprint 128)

Auto-generated analytical procedures memo per ISA 520 (Analytical Procedures) /
PCAOB AS 2305 (Substantive Analytical Procedures).
Renaissance Ledger aesthetic consistent with existing PDF exports.

Sections:
1. Header (client, periods, preparer)
2. Scope (periods compared, total accounts, materiality, significance breakdown)
3. Movement Summary (counts by movement type)
4. Significant Account Movements (material/significant items table)
5. Lead Sheet Summary (net changes by lead sheet category)
6. Conclusion (professional assessment)
"""

import io
from typing import Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from pdf_generator import (
    ClassicalColors,
    LedgerRule,
    create_leader_dots,
    generate_reference_number,
)
from security_utils import log_secure_operation
from shared.memo_base import (
    build_disclaimer,
    build_intelligence_stamp,
    build_workpaper_signoff,
    create_memo_styles,
)
from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    draw_page_footer,
    find_logo,
)


def _format_currency(value: float) -> str:
    """Format a currency value for display."""
    if value >= 0:
        return f"${value:,.2f}"
    return f"-${abs(value):,.2f}"


def _build_significant_movements_table(
    story: list,
    styles: dict,
    movements: list[dict],
) -> None:
    """Build a table of significant account movements."""
    if not movements:
        story.append(Paragraph("No significant movements identified.", styles["MemoBodySmall"]))
        return

    headers = ["Account", "Prior", "Current", "Change", "% Change", "Type"]
    col_widths = [2.2 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 0.7 * inch, 0.8 * inch]

    data = [headers]
    # Show top 25 significant movements sorted by absolute change
    sorted_movements = sorted(movements, key=lambda m: abs(m.get("change_amount", 0)), reverse=True)[:25]

    for m in sorted_movements:
        name = m.get("account_name", "")
        if len(name) > 35:
            name = name[:32] + "..."
        prior = _format_currency(m.get("prior_balance", 0))
        current = _format_currency(m.get("current_balance", 0))
        change = _format_currency(m.get("change_amount", 0))
        pct = m.get("change_percent")
        pct_str = f"{pct:+.1f}%" if pct is not None else "N/A"
        movement = m.get("movement_type", "").replace("_", " ").title()
        data.append([name, prior, current, change, pct_str, movement])

    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("ALIGN", (1, 0), (4, -1), "RIGHT"),
                ("ALIGN", (5, 0), (5, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(table)

    total_sig = len(movements)
    if total_sig > 25:
        story.append(
            Paragraph(
                f"+ {total_sig - 25} additional significant movements (see CSV export for full list)",
                styles["MemoBodySmall"],
            )
        )


def _build_lead_sheet_table(
    story: list,
    styles: dict,
    summaries: list[dict],
) -> None:
    """Build a table of lead sheet net changes."""
    if not summaries:
        story.append(Paragraph("No lead sheet data available.", styles["MemoBodySmall"]))
        return

    headers = ["Lead Sheet", "Name", "Accounts", "Prior Total", "Current Total", "Net Change"]
    col_widths = [0.6 * inch, 2.0 * inch, 0.7 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch]

    data = [headers]
    for ls in summaries:
        code = ls.get("lead_sheet", "")
        name = ls.get("lead_sheet_name", "")
        if len(name) > 30:
            name = name[:27] + "..."
        count = str(ls.get("account_count", 0))
        prior = _format_currency(ls.get("prior_total", 0))
        current = _format_currency(ls.get("current_total", 0))
        net = _format_currency(ls.get("net_change", 0))
        data.append([code, name, count, prior, current, net])

    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(table)


def generate_multi_period_memo(
    comparison_result: dict[str, Any],
    filename: str = "multi_period_comparison",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF analytical procedures memo for multi-period comparison.

    Args:
        comparison_result: MovementSummaryResponse-shaped dict
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description override
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("multi_period_memo_generate", f"Generating multi-period memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "APC-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story = []
    prior_label = comparison_result.get("prior_label", "Prior")
    current_label = comparison_result.get("current_label", "Current")
    budget_label = comparison_result.get("budget_label")
    total_accounts = comparison_result.get("total_accounts", 0)
    movements_by_type = comparison_result.get("movements_by_type", {})
    movements_by_significance = comparison_result.get("movements_by_significance", {})
    significant_movements = comparison_result.get("significant_movements", [])
    lead_sheet_summaries = comparison_result.get("lead_sheet_summaries", [])
    dormant_count = comparison_result.get("dormant_account_count", 0)

    material_count = movements_by_significance.get("material", 0)
    significant_count = movements_by_significance.get("significant", 0)
    minor_count = movements_by_significance.get("minor", 0)

    # 1. COVER PAGE
    logo_path = find_logo()
    metadata = ReportMetadata(
        title="Analytical Procedures Memo",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        reference=reference,
    )
    build_cover_page(story, styles, metadata, doc.width, logo_path)

    # 2. SCOPE
    story.append(Paragraph("I. SCOPE", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    period_desc = period_tested or f"{prior_label} vs. {current_label}"
    if budget_label:
        period_desc += f" vs. {budget_label}"

    scope_lines = [
        create_leader_dots("Periods Compared", period_desc),
        create_leader_dots("Total Accounts Analyzed", f"{total_accounts:,}"),
        create_leader_dots("Material Movements", str(material_count)),
        create_leader_dots("Significant Movements", str(significant_count)),
        create_leader_dots("Minor Movements", str(minor_count)),
    ]
    if dormant_count > 0:
        scope_lines.append(create_leader_dots("Dormant Accounts", str(dormant_count)))

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 8))

    # 3. MOVEMENT SUMMARY
    story.append(Paragraph("II. MOVEMENT SUMMARY", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    type_labels = {
        "new_account": "New Accounts",
        "closed_account": "Closed Accounts",
        "sign_change": "Sign Changes",
        "increase": "Increases",
        "decrease": "Decreases",
        "unchanged": "Unchanged",
    }
    for type_key, type_label in type_labels.items():
        count = movements_by_type.get(type_key, 0)
        if count > 0:
            story.append(
                Paragraph(
                    create_leader_dots(type_label, str(count)),
                    styles["MemoLeader"],
                )
            )
    story.append(Spacer(1, 8))

    # 4. SIGNIFICANT ACCOUNT MOVEMENTS
    story.append(Paragraph("III. SIGNIFICANT ACCOUNT MOVEMENTS", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))
    _build_significant_movements_table(story, styles, significant_movements)
    story.append(Spacer(1, 8))

    # 5. LEAD SHEET SUMMARY
    section_num = "IV"
    if lead_sheet_summaries:
        # Strip movements from lead sheet data for the table (just summaries)
        stripped_summaries = []
        for ls in lead_sheet_summaries:
            stripped_summaries.append(
                {
                    "lead_sheet": ls.get("lead_sheet", ""),
                    "lead_sheet_name": ls.get("lead_sheet_name", ""),
                    "account_count": ls.get("account_count", 0),
                    "prior_total": ls.get("prior_total", 0),
                    "current_total": ls.get("current_total", 0),
                    "net_change": ls.get("net_change", 0),
                }
            )

        story.append(Paragraph(f"{section_num}. LEAD SHEET SUMMARY", styles["MemoSection"]))
        story.append(LedgerRule(doc.width))
        _build_lead_sheet_table(story, styles, stripped_summaries)
        story.append(Spacer(1, 8))
        section_num = "V"

    # 6. CONCLUSION
    story.append(Paragraph(f"{section_num}. CONCLUSION", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    total_sig = material_count + significant_count
    sig_rate = total_sig / total_accounts if total_accounts > 0 else 0

    if total_sig == 0:
        assessment = (
            "Based on the analytical procedures applied comparing "
            f"{prior_label} to {current_label}, "
            "no material or significant account movements were identified. "
            "Account balances are consistent with prior period expectations. "
            "No additional substantive procedures are indicated based on these results."
        )
    elif sig_rate <= 0.15:
        assessment = (
            "Based on the analytical procedures applied comparing "
            f"{prior_label} to {current_label}, "
            f"{total_sig} material/significant movement(s) were identified out of "
            f"{total_accounts} accounts analyzed. "
            "The auditor should investigate these movements to determine whether they are "
            "explained by known business changes or require further substantive testing."
        )
    elif sig_rate <= 0.30:
        assessment = (
            "Based on the analytical procedures applied comparing "
            f"{prior_label} to {current_label}, "
            f"{total_sig} material/significant movements were identified, representing a MODERATE "
            "rate of variance. Several accounts exhibit material period-over-period "
            "changes that should be corroborated with management explanations and additional "
            "substantive procedures per ISA 520."
        )
    else:
        assessment = (
            "Based on the analytical procedures applied comparing "
            f"{prior_label} to {current_label}, "
            f"{total_sig} material/significant movements were identified, representing an ELEVATED "
            "rate of variance across accounts. "
            "The volume and magnitude of movements may indicate significant changes in "
            "business operations, accounting policies, or potential misstatement risk. "
            "Expanded substantive procedures are recommended per ISA 520 and PCAOB AS 2305."
        )

    story.append(Paragraph(assessment, styles["MemoBody"]))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(story, styles, doc.width, prepared_by, reviewed_by, workpaper_date)

    # INTELLIGENCE STAMP
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # DISCLAIMER
    build_disclaimer(
        story,
        styles,
        domain="analytical procedures and trend analysis",
        isa_reference="ISA 520 (Analytical Procedures) and PCAOB AS 2305 (Substantive Analytical Procedures)",
    )

    # Build PDF (page footer on all pages)
    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("multi_period_memo_complete", f"Multi-period memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
