"""
Account Mapping Trace section renderer for the Financial Statements PDF.

Renders the per-line-item account-to-statement mapping with tie-out badges
and an overall summary badge showing how many lines are tied.
"""

from typing import Any

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf.components import LedgerRule, create_leader_dots
from pdf.styles import ClassicalColors


def render_mapping_trace(story: list, styles: dict, statements: Any) -> None:
    """Append the Account Mapping Trace section to *story*.

    No-ops if ``statements.mapping_trace`` is empty or falsy.
    """
    if not statements.mapping_trace:
        return

    story.append(Spacer(1, 8))
    story.append(Paragraph("\u2767", styles["SectionOrnament"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Account Mapping Trace", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 8))

    # Group entries by statement
    current_statement = ""
    tied_count = 0
    total_count = len(statements.mapping_trace)

    for entry in statements.mapping_trace:
        if entry.statement != current_statement:
            current_statement = entry.statement
            story.append(Paragraph(current_statement, styles["SubsectionHeader"]))
            story.append(Spacer(1, 4))

        # Entry header line with leader dots
        line = create_leader_dots(
            f"      {entry.line_label} [{entry.lead_sheet_ref}]", f"${entry.statement_amount:,.2f}"
        )
        story.append(Paragraph(f"<b>{line}</b>", styles["LeaderLine"]))

        # Account detail table
        if entry.account_count > 0 and entry.accounts:
            acct_data = [["Account", "Debit", "Credit", "Net"]]
            for acct in entry.accounts:
                acct_data.append(
                    [
                        acct.account_name[:40],
                        f"${acct.debit:,.2f}",
                        f"${acct.credit:,.2f}",
                        f"${acct.net_balance:,.2f}",
                    ]
                )

            acct_table = Table(acct_data, colWidths=[3.0 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch])
            acct_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
                        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                        ("TEXTCOLOR", (0, 1), (-1, -1), ClassicalColors.OBSIDIAN_600),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.5, ClassicalColors.LEDGER_RULE),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (0, -1), 24),
                    ]
                )
            )
            story.append(acct_table)

        # Tie-out badge
        if entry.is_tied:
            tied_count += 1
            tie_text = "\u2713 Tied"
            tie_color = ClassicalColors.SAGE
        else:
            tie_text = f"\u26a0 Difference: ${entry.tie_difference:,.2f}"
            tie_color = ClassicalColors.CLAY

        story.append(Paragraph(f'<font color="{tie_color.hexval()}">{tie_text}</font>', styles["DocumentRef"]))
        story.append(Spacer(1, 6))

    # Summary badge
    story.append(LedgerRule(thickness=0.5, spaceBefore=4, spaceAfter=4))
    if tied_count == total_count:
        summary_text = f"\u2713   All {total_count} lines tied"
        summary_style = "BalancedStatus"
        summary_border = ClassicalColors.SAGE
    else:
        untied = total_count - tied_count
        summary_text = f"\u26a0   {untied} of {total_count} lines with tie-out differences"
        summary_style = "UnbalancedStatus"
        summary_border = ClassicalColors.CLAY

    summary_data = [[Paragraph(summary_text, styles[summary_style])]]
    summary_table = Table(summary_data, colWidths=[4 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 2, summary_border),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
            ]
        )
    )
    summary_table.hAlign = "CENTER"
    story.append(summary_table)
