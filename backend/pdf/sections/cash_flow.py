"""
Cash Flow Statement section renderer for the Financial Statements PDF.

Renders the indirect-method cash flow statement with operating, investing,
and financing sub-sections, net change in cash, reconciliation badge, and
any associated notes.
"""

from typing import Any

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf.components import DoubleRule, LedgerRule, create_leader_dots
from pdf.styles import ClassicalColors


def render_cash_flow(story: list, styles: dict, statements: Any) -> None:
    """Append the Cash Flow Statement section to *story*.

    No-ops gracefully if ``statements.cash_flow_statement`` is ``None``.
    """
    if statements.cash_flow_statement is None:
        return

    cf = statements.cash_flow_statement
    story.append(Spacer(1, 8))
    story.append(Paragraph("\u2767", styles["SectionOrnament"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Cash Flow Statement", styles["SectionHeader"]))
    story.append(Paragraph("(Indirect Method)", styles["DocumentRef"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 8))

    for section in [cf.operating, cf.investing, cf.financing]:
        story.append(Paragraph(section.label, styles["SubsectionHeader"]))
        story.append(Spacer(1, 4))
        for item in section.items:
            line = create_leader_dots(f"      {item.label}", f"${item.amount:,.2f}")
            story.append(Paragraph(line, styles["LeaderLine"]))
        # Subtotal
        line = create_leader_dots(f"    Net {section.label}", f"${section.subtotal:,.2f}")
        story.append(Paragraph(f"<b>{line}</b>", styles["LeaderLine"]))
        story.append(LedgerRule(thickness=0.25, spaceBefore=2, spaceAfter=8))

    # Net Change in Cash
    story.append(LedgerRule(thickness=0.5, spaceBefore=4, spaceAfter=2))
    line = create_leader_dots("  NET CHANGE IN CASH", f"${cf.net_change:,.2f}")
    story.append(Paragraph(f"<b>{line}</b>", styles["LeaderLine"]))
    story.append(
        DoubleRule(width=6.5 * inch, color=ClassicalColors.OBSIDIAN_600, thick=1, thin=0.5, gap=1, spaceAfter=8)
    )

    # Reconciliation
    if cf.has_prior_period:
        _render_reconciliation(story, styles, cf)

    # Notes
    if cf.notes:
        story.append(Spacer(1, 8))
        for note in cf.notes:
            story.append(Paragraph(f"<i>Note: {note}</i>", styles["DocumentRef"]))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _render_reconciliation(story: list, styles: dict, cf: Any) -> None:
    story.append(Spacer(1, 4))
    line = create_leader_dots("  Beginning Cash", f"${cf.beginning_cash:,.2f}")
    story.append(Paragraph(line, styles["LeaderLine"]))
    line = create_leader_dots("  Net Change in Cash", f"${cf.net_change:,.2f}")
    story.append(Paragraph(line, styles["LeaderLine"]))
    story.append(LedgerRule(thickness=0.5, spaceBefore=2, spaceAfter=2))
    line = create_leader_dots("  ENDING CASH", f"${cf.ending_cash:,.2f}")
    story.append(Paragraph(f"<b>{line}</b>", styles["LeaderLine"]))
    story.append(
        DoubleRule(width=6.5 * inch, color=ClassicalColors.OBSIDIAN_600, thick=1, thin=0.5, gap=1, spaceAfter=8)
    )

    # Reconciliation badge
    if cf.is_reconciled:
        recon_text = "\u2713  Reconciled"
        recon_style = "BalancedStatus"
        recon_border = ClassicalColors.SAGE
    else:
        recon_text = f"\u26a0   UNRECONCILED (${cf.reconciliation_difference:,.2f})"
        recon_style = "UnbalancedStatus"
        recon_border = ClassicalColors.CLAY

    recon_data = [[Paragraph(recon_text, styles[recon_style])]]
    recon_table = Table(recon_data, colWidths=[4 * inch])
    recon_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 2, recon_border),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
            ]
        )
    )
    recon_table.hAlign = "CENTER"
    story.append(recon_table)
