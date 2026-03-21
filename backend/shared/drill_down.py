"""
Shared Drill-Down Detail Table Builder

Utility for rendering high-severity flagged entry detail tables in PDF memos.
Used by JET, APT, RVT, ARA, and other testing memo generators to surface
rich detail data that already exists in engine result dataclasses.
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from pdf_generator import ClassicalColors

# Maximum rows to render per drill-down table
MAX_DRILL_ROWS = 20


_EMPTY_STATE_TEXT = "No entry-level detail available for: {title}"


def build_drill_down_table(
    story: list,
    styles: dict,
    doc_width: float,
    title: str,
    headers: list[str],
    rows: list[list[Any]],
    *,
    max_rows: int = MAX_DRILL_ROWS,
    total_flagged: Optional[int] = None,
    col_widths: Optional[list[float]] = None,
    right_align_cols: Optional[list[int]] = None,
    suppress_empty: bool = True,
) -> None:
    """Build a drill-down detail table in the PDF story.

    Args:
        story: ReportLab story list to append to
        styles: Memo styles dict
        doc_width: Available document width
        title: Subsection title (e.g., "Unbalanced Entries — High Severity Detail")
        headers: Column header strings
        rows: Data rows (list of lists)
        max_rows: Maximum rows to display before truncation
        total_flagged: Total flagged count (for truncation message)
        col_widths: Optional explicit column widths; auto-computed if None
        right_align_cols: Column indices (0-based) to right-align (typically monetary)
        suppress_empty: If True (default), render nothing when rows is empty.
            If False, render a labeled placeholder indicating no detail is available.
    """
    if not rows:
        if suppress_empty:
            return
        # Render labeled empty state so absence is distinguishable from silent failure
        story.append(Paragraph(title, styles["MemoBody"]))
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                f"<i>{_EMPTY_STATE_TEXT.format(title=title)}</i>",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 6))
        return

    story.append(Paragraph(title, styles["MemoBody"]))
    story.append(Spacer(1, 4))

    display_rows = rows[:max_rows]

    # Auto-compute column widths if not provided
    if col_widths is None:
        n_cols = len(headers)
        col_width = doc_width / n_cols
        col_widths = [col_width] * n_cols

    # Wrap cell content in Paragraph for word wrapping
    wrapped_rows = []
    for row in display_rows:
        wrapped_row = []
        for cell in row:
            if isinstance(cell, str):
                wrapped_row.append(Paragraph(cell, styles["MemoTableCell"]))
            else:
                wrapped_row.append(cell)
        wrapped_rows.append(wrapped_row)

    table_data = [headers] + wrapped_rows
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Build style commands
    style_cmds = [
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]

    # Right-align specified columns
    if right_align_cols:
        for col_idx in right_align_cols:
            style_cmds.append(("ALIGN", (col_idx, 0), (col_idx, -1), "RIGHT"))

    table.setStyle(TableStyle(style_cmds))
    story.append(table)

    # Truncation message
    actual_total = total_flagged if total_flagged is not None else len(rows)
    if actual_total > max_rows:
        story.append(
            Paragraph(
                f"Showing {max_rows} of {actual_total} flagged entries. See CSV export for complete listing.",
                styles["MemoBodySmall"],
            )
        )

    story.append(Spacer(1, 6))


def format_currency(value: Any) -> str:
    """Format a numeric value as currency string.

    Accepts Decimal, int, float, or string representations.
    Uses Decimal internally to avoid float precision loss.
    """
    try:
        if isinstance(value, Decimal):
            d = value
        elif isinstance(value, (int, float)):
            d = Decimal(str(value))
        elif isinstance(value, str):
            # Strip currency formatting before parsing
            cleaned = value.replace("$", "").replace(",", "").strip()
            if cleaned.startswith("(") and cleaned.endswith(")"):
                cleaned = "-" + cleaned[1:-1]
            d = Decimal(cleaned)
        else:
            d = Decimal(str(value))
        if d < 0:
            return f"-${abs(d):,.2f}"
        return f"${d:,.2f}"
    except (TypeError, ValueError, InvalidOperation):
        return str(value) if value is not None else "—"


def safe_str_value(value: Any, default: str = "—") -> str:
    """Safely convert a value to string for table display."""
    if value is None:
        return default
    return str(value)
