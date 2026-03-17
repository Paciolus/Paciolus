"""
Workpaper Sign-Off section renderer shared by both the diagnostic and
financial-statements PDFs.

Renders a table with Prepared By / Reviewed By fields when the signoff
gate is enabled and practitioner information is provided.
"""

from datetime import datetime
from typing import Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf.components import LedgerRule
from pdf.styles import ClassicalColors


def render_workpaper_signoff(
    story: list,
    styles: dict,
    prepared_by: Optional[str],
    reviewed_by: Optional[str],
    workpaper_date: Optional[str] = None,
    include_signoff: bool = False,
    *,
    section_ornament: bool = False,
) -> None:
    """Append the Workpaper Sign-Off section to *story*.

    No-ops if *include_signoff* is ``False`` or both *prepared_by* and
    *reviewed_by* are empty.

    If *section_ornament* is ``True``, a fleuron divider is prepended (used
    by the financial-statements orchestrator).
    """
    if not include_signoff:
        return
    if not prepared_by and not reviewed_by:
        return

    if section_ornament:
        story.append(Spacer(1, 8))
        story.append(Paragraph("\u2767", styles["SectionOrnament"]))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Workpaper Sign-Off", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 8))

    wp_date = workpaper_date or datetime.now().strftime("%Y-%m-%d")
    signoff_data = [["Field", "Name", "Date"]]
    if prepared_by:
        signoff_data.append(["Prepared By:", prepared_by, wp_date])
    if reviewed_by:
        signoff_data.append(["Reviewed By:", reviewed_by, wp_date])

    col_widths = [1.5 * inch, 3.5 * inch, 1.5 * inch]
    table = Table(signoff_data, colWidths=col_widths)

    style_commands = [
        # Header styling
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Body styling
        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("TEXTCOLOR", (0, 1), (-1, -1), ClassicalColors.OBSIDIAN_600),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        # Grid
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, ClassicalColors.LEDGER_RULE),
        # Background alternation
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ClassicalColors.WHITE, ClassicalColors.OATMEAL_PAPER]),
    ]

    table.setStyle(TableStyle(style_commands))
    story.append(table)
