"""
Shared Report Styles — Sprint 2: Report Standardization

Typography, spacing, and margin tokens shared across all PDF generators.
Centralizes constants that were previously hardcoded across pdf_generator.py,
memo_base.py, and individual memo generators.

This module does NOT create ParagraphStyle objects — those remain in
create_classical_styles() and create_memo_styles() until Sprint 6 unifies them.
"""

from reportlab.lib.units import inch

# Re-export ClassicalColors for convenience (single import path)
from pdf_generator import ClassicalColors

# =============================================================================
# Font families
# =============================================================================

FONT_TITLE = "Times-Bold"
FONT_BODY = "Times-Roman"
FONT_MONO = "Courier"
FONT_ITALIC = "Times-Italic"

# =============================================================================
# Font sizes (pt)
# =============================================================================

SIZE_DISPLAY = 28
SIZE_TITLE = 24
SIZE_SECTION = 11
SIZE_BODY = 10
SIZE_TABLE = 9
SIZE_FOOTER = 8
SIZE_DISCLAIMER = 7
SIZE_SMALL = 9

# =============================================================================
# Spacing (pt)
# =============================================================================

SPACE_COVER_AFTER_LOGO = 16
SPACE_COVER_AFTER_TITLE = 8
SPACE_COVER_AFTER_RULE = 24
SPACE_SECTION_BEFORE = 16
SPACE_SECTION_AFTER = 6
SPACE_BODY_AFTER = 4
SPACE_FOOTER_Y = 0.5 * inch  # page number Y position

# =============================================================================
# Margins (inches, as float — multiply by inch when needed)
# =============================================================================

MARGIN_LEFT = 0.75
MARGIN_RIGHT = 0.75
MARGIN_TOP = 1.0
MARGIN_BOTTOM = 0.8

# =============================================================================
# Shared table style helpers
# =============================================================================


def ledger_table_style() -> list[tuple]:
    """Return the standard ledger table styling commands.

    Usage:
        table.setStyle(TableStyle(ledger_table_style()))

    This is the repeating pattern used across ~20 tables in memo generators:
    bold header row, obsidian-deep text, 1px header underline, 0.25px row
    separators, top-aligned, compact padding, flush left first column.
    """
    return [
        ("FONTNAME", (0, 0), (-1, 0), FONT_TITLE),
        ("FONTNAME", (0, 1), (-1, -1), FONT_BODY),
        ("FONTSIZE", (0, 0), (-1, -1), SIZE_TABLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]
