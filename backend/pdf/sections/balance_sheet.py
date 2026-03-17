"""
Balance Sheet section renderer for the Financial Statements PDF.

Renders the balance sheet line items in either leader-dot format (single
period) or a comparative table (when prior-period data is available),
followed by the balance verification badge and cross-reference index.
"""

from typing import Any

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf.components import DoubleRule, LedgerRule, create_leader_dots
from pdf.styles import ClassicalColors

# Cross-reference legend for balance-sheet lead-sheet refs
_BS_LEGEND_MAP = {
    "A": ("Cash and Cash Equivalents", "Bank Reconciliation Memo"),
    "B": ("Receivables", "AR Aging Analysis Memo"),
    "C": ("Inventory", "Inventory Register Analysis Memo"),
    "D": ("Prepaid Expenses", "Trial Balance Diagnostic"),
    "E": ("Property, Plant & Equipment", "Fixed Asset Testing Memo"),
    "F": ("Other Assets & Intangibles", "Trial Balance Diagnostic"),
    "G": ("AP & Accrued Liabilities", "AP Payment Testing Memo"),
    "H": ("Other Current Liabilities", "Accrual Completeness Estimator"),
    "I": ("Long-term Debt", "Trial Balance Diagnostic"),
    "J": ("Other Long-term Liabilities", "Trial Balance Diagnostic"),
    "K": ("Stockholders' Equity", "Trial Balance Diagnostic"),
}


def render_balance_sheet(story: list, styles: dict, statements: Any) -> None:
    """Append the Balance Sheet section (with badge and cross-ref index) to *story*."""

    story.append(Paragraph("Balance Sheet", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 8))

    # Check if prior period data is available for comparative columns
    _bs_has_prior = any(item.prior_amount is not None for item in statements.balance_sheet)

    if _bs_has_prior:
        _render_comparative_table(story, styles, statements)
    else:
        _render_leader_dot(story, styles, statements)

    # Balance verification badge
    _render_balance_badge(story, styles, statements)

    # Cross-reference index
    _render_cross_reference(story, styles, statements)

    # Section ornament
    story.append(Spacer(1, 8))
    story.append(Paragraph("\u2767", styles["SectionOrnament"]))
    story.append(Spacer(1, 8))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _render_comparative_table(story: list, styles: dict, statements: Any) -> None:
    period_label = statements.period_end or "Current"
    bs_table_data = [["Account", period_label, "Prior Period", "Change"]]
    bs_table_styles = [
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
    row_idx = 1
    for item in statements.balance_sheet:
        prior_str = f"${item.prior_amount:,.2f}" if item.prior_amount is not None else "\u2014"
        change_str = ""
        if item.prior_amount is not None:
            change = item.amount - item.prior_amount
            change_str = f"${change:,.2f}"

        if item.is_total:
            ref = f" ({item.lead_sheet_ref})" if item.lead_sheet_ref else ""
            bs_table_data.append([f"  {item.label}{ref}", f"${item.amount:,.2f}", prior_str, change_str])
            bs_table_styles.append(("FONTNAME", (0, row_idx), (-1, row_idx), "Times-Bold"))
            bs_table_styles.append(("LINEABOVE", (0, row_idx), (-1, row_idx), 0.5, ClassicalColors.OBSIDIAN_600))
            bs_table_styles.append(("LINEBELOW", (0, row_idx), (-1, row_idx), 1, ClassicalColors.OBSIDIAN_600))
        elif item.is_subtotal:
            bs_table_data.append([f"    {item.label}", f"${item.amount:,.2f}", prior_str, change_str])
            bs_table_styles.append(("FONTNAME", (0, row_idx), (-1, row_idx), "Times-Bold"))
            bs_table_styles.append(("LINEBELOW", (0, row_idx), (-1, row_idx), 0.25, ClassicalColors.LEDGER_RULE))
        elif item.indent_level == 0 and not item.lead_sheet_ref:
            bs_table_data.append([item.label, "", "", ""])
            bs_table_styles.append(("FONTNAME", (0, row_idx), (0, row_idx), "Times-Bold"))
            bs_table_styles.append(("FONTSIZE", (0, row_idx), (0, row_idx), 9))
            bs_table_styles.append(("TEXTCOLOR", (0, row_idx), (0, row_idx), ClassicalColors.OBSIDIAN_DEEP))
        else:
            ref = f" ({item.lead_sheet_ref})" if item.lead_sheet_ref else ""
            bs_table_data.append([f"      {item.label}{ref}", f"${item.amount:,.2f}", prior_str, change_str])
        row_idx += 1

    bs_table = Table(bs_table_data, colWidths=[2.7 * inch, 1.3 * inch, 1.3 * inch, 1.2 * inch])
    bs_table.setStyle(TableStyle(bs_table_styles))
    story.append(bs_table)


def _render_leader_dot(story: list, styles: dict, statements: Any) -> None:
    if statements.has_prior_period is False:
        pass  # No note needed if prior data was never provided
    for item in statements.balance_sheet:
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
        elif item.indent_level == 0 and not item.lead_sheet_ref:
            story.append(Spacer(1, 6))
            story.append(Paragraph(item.label, styles["SubsectionHeader"]))
        else:
            ref = f" ({item.lead_sheet_ref})" if item.lead_sheet_ref else ""
            line = create_leader_dots(f"      {item.label}{ref}", f"${item.amount:,.2f}")
            story.append(Paragraph(line, styles["LeaderLine"]))


def _render_balance_badge(story: list, styles: dict, statements: Any) -> None:
    story.append(Spacer(1, 12))
    if statements.is_balanced:
        badge_text = "\u2713  Balanced"
        badge_style = "BalancedStatus"
        badge_border = ClassicalColors.SAGE
    else:
        badge_text = f"\u26a0   OUT OF BALANCE (${statements.balance_difference:,.2f})"
        badge_style = "UnbalancedStatus"
        badge_border = ClassicalColors.CLAY

    badge_data = [[Paragraph(badge_text, styles[badge_style])]]
    badge_table = Table(badge_data, colWidths=[4 * inch])
    badge_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 2, badge_border),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
            ]
        )
    )
    badge_table.hAlign = "CENTER"
    story.append(badge_table)


def _render_cross_reference(story: list, styles: dict, statements: Any) -> None:
    _bs_refs_used = {
        item.lead_sheet_ref for item in statements.balance_sheet if item.lead_sheet_ref and item.amount != 0
    }
    _bs_legend_items = [(ref, *_BS_LEGEND_MAP[ref]) for ref in sorted(_bs_refs_used) if ref in _BS_LEGEND_MAP]

    if _bs_legend_items:
        story.append(Spacer(1, 8))
        story.append(LedgerRule(thickness=0.5, spaceBefore=2, spaceAfter=4))
        story.append(Paragraph("Cross-Reference Index", styles["SubsectionHeader"]))
        story.append(Spacer(1, 2))
        for ref, acct_name, report_name in _bs_legend_items:
            legend_text = f"({ref}) {acct_name} \u2014 See {report_name}"
            story.append(Paragraph(legend_text, styles["DocumentRef"]))
        story.append(Spacer(1, 4))
