"""
Classical color palette and paragraph style definitions for Renaissance Ledger PDFs.

All PDF generators share this single source of truth for colors, fonts, and
ParagraphStyle objects.  The ClassicalColors class extends Oat & Obsidian with
institutional warmth; create_classical_styles() returns a fully-populated
ReportLab stylesheet ready for any Paciolus report.
"""

from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------


class ClassicalColors:
    """
    Classical color palette for Renaissance Ledger aesthetic.

    Extends Oat & Obsidian with institutional warmth.
    """

    # Core Obsidian (deep blacks for authority)
    OBSIDIAN_DEEP = colors.HexColor("#1A1A1A")  # Primary text
    OBSIDIAN = colors.HexColor("#212121")
    OBSIDIAN_700 = colors.HexColor("#303030")
    OBSIDIAN_600 = colors.HexColor("#424242")
    OBSIDIAN_500 = colors.HexColor("#616161")

    # Warm Oatmeal (paper and accents)
    OATMEAL_PAPER = colors.HexColor("#F7F5F0")  # Warm paper background
    OATMEAL = colors.HexColor("#EBE9E4")
    OATMEAL_300 = colors.HexColor("#DDD9D1")
    OATMEAL_400 = colors.HexColor("#C9C3B8")
    OATMEAL_500 = colors.HexColor("#B5AD9F")

    # Ledger elements
    LEDGER_RULE = colors.HexColor("#D4CFC5")  # Subtle horizontal rules
    LEDGER_DOT = colors.HexColor("#C9C3B8")  # Leader dots

    # Semantic colors
    CLAY = colors.HexColor("#BC4749")  # Errors, material risks
    CLAY_400 = colors.HexColor("#D16C6E")
    SAGE = colors.HexColor("#4A7C59")  # Success, balanced
    SAGE_400 = colors.HexColor("#6FA882")

    # Institutional accent
    GOLD_INSTITUTIONAL = colors.HexColor("#B8934C")  # Premium borders
    GOLD_LIGHT = colors.HexColor("#D4B87A")

    # Utilities
    WHITE = colors.white


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------


def _add_or_replace_style(styles: Any, style: ParagraphStyle) -> None:
    """Add a style to the stylesheet, replacing if it already exists."""
    if style.name in [s.name for s in styles.byName.values()]:
        existing = styles[style.name]
        for attr in [
            "fontName",
            "fontSize",
            "textColor",
            "alignment",
            "spaceBefore",
            "spaceAfter",
            "leading",
            "leftIndent",
            "rightIndent",
            "firstLineIndent",
            "bulletIndent",
        ]:
            if hasattr(style, attr) and getattr(style, attr) is not None:
                setattr(existing, attr, getattr(style, attr))
    else:
        styles.add(style)


def create_classical_styles() -> dict:
    """
    Create Renaissance Ledger styled paragraph styles.

    Typography hierarchy:
    - Display: Times-Bold 28pt (titles)
    - Section: Times-Bold 12pt, title case
    - Body: Times-Roman 10pt
    - Financial: Courier for tabular figures
    """
    styles = getSampleStyleSheet()

    # ===================================================================
    # TITLE STYLES
    # ===================================================================

    # Main document title - Classical serif, commanding presence
    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="ClassicalTitle",
            fontName="Times-Bold",
            fontSize=28,
            textColor=ClassicalColors.OBSIDIAN_DEEP,
            alignment=TA_CENTER,
            spaceAfter=6,
            leading=32,
        ),
    )

    # Subtitle - Lighter weight, institutional
    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="ClassicalSubtitle",
            fontName="Times-Roman",
            fontSize=12,
            textColor=ClassicalColors.OBSIDIAN_500,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
    )

    # Document reference line (date, ref number)
    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="DocumentRef",
            fontName="Times-Italic",
            fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_500,
            alignment=TA_CENTER,
            spaceAfter=20,
        ),
    )

    # ===================================================================
    # SECTION HEADERS
    # ===================================================================

    # Section header - Title case, bold serif, gold accent (Fix 7)
    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="SectionHeader",
            fontName="Times-Bold",
            fontSize=13,
            textColor=ClassicalColors.OBSIDIAN_DEEP,
            spaceBefore=28,
            spaceAfter=10,
            leading=16,
        ),
    )

    # Subsection header
    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="SubsectionHeader",
            fontName="Times-Bold",
            fontSize=10,
            textColor=ClassicalColors.OBSIDIAN_600,
            spaceBefore=16,
            spaceAfter=6,
        ),
    )

    # ===================================================================
    # BODY TEXT
    # ===================================================================

    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="BodyText",
            fontName="Times-Roman",
            fontSize=10,
            textColor=ClassicalColors.OBSIDIAN_600,
            leading=14,
            spaceAfter=8,
        ),
    )

    # Leader dot line style (for financial summaries)
    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="LeaderLine",
            fontName="Courier",
            fontSize=10,
            textColor=ClassicalColors.OBSIDIAN_DEEP,
            leading=16,
            spaceAfter=2,
        ),
    )

    # ===================================================================
    # STATUS STYLES
    # ===================================================================

    # Balanced status - Classical seal effect
    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="BalancedStatus",
            fontName="Times-Bold",
            fontSize=14,
            textColor=ClassicalColors.SAGE,
            alignment=TA_CENTER,
        ),
    )

    # Unbalanced status
    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="UnbalancedStatus",
            fontName="Times-Bold",
            fontSize=14,
            textColor=ClassicalColors.CLAY,
            alignment=TA_CENTER,
        ),
    )

    # ===================================================================
    # TABLE STYLES
    # ===================================================================

    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="TableCell",
            fontName="Times-Roman",
            fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_600,
            leading=11,
        ),
    )

    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="TableHeader",
            fontName="Times-Bold",
            fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_DEEP,
        ),
    )

    # ===================================================================
    # FOOTER STYLES
    # ===================================================================

    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="Footer",
            fontName="Times-Roman",
            fontSize=8,
            textColor=ClassicalColors.OBSIDIAN_500,
            alignment=TA_CENTER,
        ),
    )

    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="FooterMotto",
            fontName="Times-Italic",
            fontSize=8,
            textColor=ClassicalColors.GOLD_INSTITUTIONAL,
            alignment=TA_CENTER,
        ),
    )

    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="LegalDisclaimer",
            fontName="Times-Roman",
            fontSize=7,
            textColor=ClassicalColors.OBSIDIAN_500,
            alignment=TA_CENTER,
            leading=9,
        ),
    )

    # Section ornament (centered)
    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="SectionOrnament",
            fontName="Times-Roman",
            fontSize=12,
            textColor=ClassicalColors.SAGE,
            alignment=TA_CENTER,
            spaceBefore=12,
            spaceAfter=12,
        ),
    )

    return {name: styles[name] for name in styles.byName}
