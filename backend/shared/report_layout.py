"""
Shared Report Layout Utilities — Sprint 4: Text Layout Hardening

Reusable helpers for wrapping long text in ReportLab table cells,
preventing truncation-by-slicing and ensuring dynamic row heights.

Design principles:
- Never hide user data to "make it fit" — wrap instead of truncate.
- Paragraph-wrapped cells expand rows automatically.
- repeatRows=1 on multi-row tables for page-break header repetition.
- Minimum leading ensures readable line spacing in wrapped cells.
"""

from reportlab.platypus import Paragraph

# =============================================================================
# Leading / padding constants
# =============================================================================

MINIMUM_LEADING = 11  # pt — matches MemoTableCell leading (fontSize 9 + 2pt)
TABLE_CELL_TOP_PAD = 3  # pt — standard compact padding
TABLE_CELL_BOTTOM_PAD = 3  # pt — standard compact padding


# =============================================================================
# Cell wrapping
# =============================================================================


def wrap_cell(text: str, style) -> Paragraph:
    """Wrap text in a Paragraph for safe table-cell rendering.

    Always use this instead of slicing strings (e.g., name[:30] + "...").
    ReportLab's Table will auto-expand row height for wrapped content.

    Args:
        text: The full, untruncated text to display.
        style: A ParagraphStyle (e.g., styles["MemoTableCell"]).

    Returns:
        A Paragraph flowable that wraps within its column width.
    """
    return Paragraph(str(text), style)
