"""
Income Statement section renderer for the Financial Statements PDF.

Renders income-statement line items in either leader-dot format (single
period) or a comparative table with percentage-change columns, followed
by a cross-reference index.
"""

from typing import Any

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf.components import DoubleRule, LedgerRule, create_leader_dots
from pdf.styles import ClassicalColors

# Cross-reference legend for income-statement lead-sheet refs
_IS_LEGEND_MAP = {
    "L": ("Revenue", "Revenue Recognition Testing Memo"),
    "M": ("Cost of Goods Sold", "Trial Balance Diagnostic"),
    "N": ("Operating Expenses", "Expense Category Analysis"),
    "O": ("Other Income / (Expense), Net", "Trial Balance Diagnostic"),
}


def render_income_statement(story: list, styles: dict, statements: Any) -> None:
    """Append the Income Statement section (with cross-ref index) to *story*."""

    story.append(Paragraph("Income Statement", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 8))

    _is_has_prior = any(item.prior_amount is not None for item in statements.income_statement)

    if _is_has_prior:
        _render_comparative_table(story, styles, statements)
    else:
        _render_leader_dot(story, styles, statements)

    # Cross-reference index
    _render_cross_reference(story, styles, statements)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _render_comparative_table(story: list, styles: dict, statements: Any) -> None:
    is_table_data = [["Account", "Current", "Prior", "Change", "% Change"]]
    is_table_styles = [
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ("FONTNAME", (1, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    is_row = 1
    for item in statements.income_statement:
        prior_str = f"${item.prior_amount:,.2f}" if item.prior_amount is not None else "\u2014"
        change_str = ""
        pct_str = ""
        if item.prior_amount is not None:
            change = item.amount - item.prior_amount
            change_str = f"${change:,.2f}"
            # Suppress % Change on subtotals/totals per prompt
            if not item.is_subtotal and not item.is_total and item.prior_amount != 0:
                pct_change = (change / abs(item.prior_amount)) * 100
                pct_str = f"{pct_change:+.1f}%"

        ref = f" ({item.lead_sheet_ref})" if item.lead_sheet_ref else ""
        if item.is_total:
            is_table_data.append([f"  {item.label}{ref}", f"${item.amount:,.2f}", prior_str, change_str, pct_str])
            is_table_styles.append(("FONTNAME", (0, is_row), (-1, is_row), "Times-Bold"))
            is_table_styles.append(("LINEABOVE", (0, is_row), (-1, is_row), 0.5, ClassicalColors.OBSIDIAN_600))
            is_table_styles.append(("LINEBELOW", (0, is_row), (-1, is_row), 1, ClassicalColors.OBSIDIAN_600))
        elif item.is_subtotal:
            is_table_data.append([f"  {item.label}", f"${item.amount:,.2f}", prior_str, change_str, ""])
            is_table_styles.append(("FONTNAME", (0, is_row), (-1, is_row), "Times-Bold"))
            is_table_styles.append(("LINEBELOW", (0, is_row), (-1, is_row), 0.25, ClassicalColors.LEDGER_RULE))
        else:
            is_table_data.append([f"  {item.label}{ref}", f"${item.amount:,.2f}", prior_str, change_str, pct_str])
        is_row += 1

    is_table = Table(is_table_data, colWidths=[2.2 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 1.0 * inch])
    is_table.setStyle(TableStyle(is_table_styles))
    story.append(is_table)


def _render_leader_dot(story: list, styles: dict, statements: Any) -> None:
    for item in statements.income_statement:
        if item.is_total:
            story.append(LedgerRule(thickness=0.5, spaceBefore=4, spaceAfter=2))
            line = create_leader_dots(f"  {item.label}", f"${item.amount:,.2f}")
            story.append(Paragraph(f"<b>{line}</b>", styles["LeaderLine"]))
            story.append(
                DoubleRule(
                    width=6.5 * inch, color=ClassicalColors.OBSIDIAN_600, thick=1, thin=0.5, gap=1, spaceAfter=12
                )
            )
        elif item.is_subtotal:
            line = create_leader_dots(f"    {item.label}", f"${item.amount:,.2f}")
            story.append(Paragraph(f"<b>{line}</b>", styles["LeaderLine"]))
            story.append(LedgerRule(thickness=0.25, spaceBefore=2, spaceAfter=4))
        else:
            ref = f" ({item.lead_sheet_ref})" if item.lead_sheet_ref else ""
            line = create_leader_dots(f"  {item.label}{ref}", f"${item.amount:,.2f}")
            story.append(Paragraph(line, styles["LeaderLine"]))


def _render_cross_reference(story: list, styles: dict, statements: Any) -> None:
    _is_refs_used = {
        item.lead_sheet_ref for item in statements.income_statement if item.lead_sheet_ref and item.amount != 0
    }
    _is_legend_items = [(ref, *_IS_LEGEND_MAP[ref]) for ref in sorted(_is_refs_used) if ref in _IS_LEGEND_MAP]

    if _is_legend_items:
        story.append(Spacer(1, 8))
        story.append(LedgerRule(thickness=0.5, spaceBefore=2, spaceAfter=4))
        story.append(Paragraph("Cross-Reference Index", styles["SubsectionHeader"]))
        story.append(Spacer(1, 2))
        for ref, acct_name, report_name in _is_legend_items:
            legend_text = f"({ref}) {acct_name} \u2014 See {report_name}"
            story.append(Paragraph(legend_text, styles["DocumentRef"]))
        story.append(Spacer(1, 4))
