"""
Paciolus — Expense Category Analytical Procedures PDF Memo Generator
Sprint 289: Phase XXXIX

Custom memo using memo_base.py primitives. Pattern B (custom sections).
Sections: Header → Scope → Category Breakdown → Period-over-Period (conditional) →
          Workpaper Sign-Off → Disclaimer

ISA 520 documentation structure. Guardrail: descriptive metrics only.
"""

from typing import Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_generator import ClassicalColors, DoubleRule, LedgerRule, create_leader_dots, format_classical_date
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import build_disclaimer, build_intelligence_stamp, build_workpaper_signoff, create_memo_styles
from shared.scope_methodology import (
    build_authoritative_reference_block,
    build_methodology_statement,
    build_scope_statement,
)


def generate_expense_category_memo(
    report_result: dict,
    filename: str = "expense_category",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
) -> bytes:
    """Generate an Expense Category Analytical Procedures PDF memo.

    Args:
        report_result: Dict from ExpenseCategoryReport.to_dict()
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
    story.append(Paragraph("Expense Category Analytical Procedures", styles["MemoTitle"]))
    if client_name:
        story.append(Paragraph(client_name, styles["MemoSubtitle"]))
    story.append(
        Paragraph(
            f"{format_classical_date()} &nbsp;&bull;&nbsp; WP-ECA-001",
            styles["MemoRef"],
        )
    )
    story.append(DoubleRule(doc_width))
    story.append(Spacer(1, 12))

    # ── I. SCOPE ──
    story.append(Paragraph("I. SCOPE", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    categories = report_result.get("categories", [])
    total_expenses = report_result.get("total_expenses", 0)
    total_revenue = report_result.get("total_revenue", 0)
    revenue_available = report_result.get("revenue_available", False)
    prior_available = report_result.get("prior_available", False)
    materiality = report_result.get("materiality_threshold", 0)
    category_count = report_result.get("category_count", 0)

    scope_lines = [
        create_leader_dots("Source File", filename),
        create_leader_dots("Expense Categories", f"{category_count} active"),
        create_leader_dots("Total Expenses", f"${total_expenses:,.2f}"),
        create_leader_dots("Total Revenue", f"${total_revenue:,.2f}" if revenue_available else "Not available"),
        create_leader_dots("Materiality Threshold", f"${materiality:,.2f}"),
        create_leader_dots("Prior Period Data", "Included" if prior_available else "Not provided"),
    ]
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 8))

    build_scope_statement(
        story,
        styles,
        doc_width,
        tool_domain="expense_category",
        framework=resolved_framework,
        domain_label="expense category analytical procedures",
    )

    # ── II. CATEGORY BREAKDOWN ──
    story.append(Paragraph("II. CATEGORY BREAKDOWN", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    if categories:
        if prior_available and any(c.get("prior_amount") is not None for c in categories):
            # Full table with prior columns
            cat_headers = ["Category", "Amount", "% of Rev", "Prior Amount", "$ Change", "Exceeds Mat."]
            col_widths = [2.0 * inch, 1.2 * inch, 0.9 * inch, 1.2 * inch, 1.0 * inch, 0.7 * inch]
        else:
            # Compact table without prior
            cat_headers = ["Category", "Amount", "% of Revenue"]
            col_widths = [3.0 * inch, 2.0 * inch, 1.5 * inch]

        cat_data = [cat_headers]
        for c in categories:
            if isinstance(c, dict):
                amount = c.get("amount", 0)
                pct = c.get("pct_of_revenue")
                pct_str = f"{pct:.2f}%" if pct is not None else "N/A"

                if len(cat_headers) > 3:
                    prior_amt = c.get("prior_amount")
                    dollar_change = c.get("dollar_change")
                    exceeds = c.get("exceeds_materiality", False)
                    cat_data.append(
                        [
                            c.get("label", ""),
                            f"${amount:,.2f}",
                            pct_str,
                            f"${prior_amt:,.2f}" if prior_amt is not None else "N/A",
                            f"${dollar_change:,.2f}" if dollar_change is not None else "N/A",
                            "Yes" if exceeds else "No",
                        ]
                    )
                else:
                    cat_data.append(
                        [
                            c.get("label", ""),
                            f"${amount:,.2f}",
                            pct_str,
                        ]
                    )

        # Total row
        total_pct = (total_expenses / total_revenue * 100) if revenue_available and abs(total_revenue) > 1e-10 else None
        total_pct_str = f"{total_pct:.2f}%" if total_pct is not None else "N/A"
        if len(cat_headers) > 3:
            cat_data.append(["TOTAL", f"${total_expenses:,.2f}", total_pct_str, "", "", ""])
        else:
            cat_data.append(["TOTAL", f"${total_expenses:,.2f}", total_pct_str])

        cat_table = Table(cat_data, colWidths=col_widths)
        cat_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTNAME", (0, 1), (-1, -2), "Times-Roman"),
                    ("FONTNAME", (0, -1), (-1, -1), "Times-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, -2), (-1, -2), 0.5, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -2), 0.25, ClassicalColors.LEDGER_RULE),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (1, 1), (1, -1), "Courier"),
                    ("FONTNAME", (3, 1), (3, -1), "Courier"),
                    ("FONTNAME", (4, 1), (4, -1), "Courier"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                ]
            )
        )
        story.append(cat_table)
        story.append(Spacer(1, 8))

    # ── III. PERIOD-OVER-PERIOD COMPARISON (conditional) ──
    if prior_available and any(isinstance(c, dict) and c.get("prior_amount") is not None for c in categories):
        story.append(Paragraph("III. PERIOD-OVER-PERIOD COMPARISON", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        story.append(
            Paragraph(
                "The following table presents the dollar change between current and prior period "
                "for categories where aggregate prior-period data was available. "
                "The materiality flag indicates whether the absolute change exceeds the "
                f"specified threshold of ${materiality:,.2f}.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

        # Count categories exceeding materiality
        exceeds_count = sum(1 for c in categories if isinstance(c, dict) and c.get("exceeds_materiality", False))
        story.append(
            Paragraph(
                f"Categories with changes exceeding materiality threshold: {exceeds_count}",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 12))

    # ── Methodology & Authoritative References ──
    build_methodology_statement(
        story,
        styles,
        doc_width,
        tool_domain="expense_category",
        framework=resolved_framework,
        domain_label="expense category analytical procedures",
    )
    build_authoritative_reference_block(
        story,
        styles,
        doc_width,
        tool_domain="expense_category",
        framework=resolved_framework,
        domain_label="expense category analytical procedures",
    )

    # ── Workpaper Sign-Off ──
    build_workpaper_signoff(story, styles, doc_width, prepared_by, reviewed_by, workpaper_date)

    # ── Intelligence Stamp ──
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # ── Disclaimer ──
    build_disclaimer(
        story,
        styles,
        domain="expense category analytical procedures",
        isa_reference="ISA 520 (Analytical Procedures)",
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
