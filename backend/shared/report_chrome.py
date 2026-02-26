"""
Shared Report Chrome — Sprint 2: Report Standardization

Cover page, page header, and page footer shared by all PDF generators.
Replaces the per-generator header/footer implementations with a single
set of composable building blocks.

Diagonal Color Bands (cover page background):
  5 overlapping bands at 20° sweep using Oat & Obsidian brand palette
  (Obsidian, Gold Institutional, Sage) at varying opacities (5%–82%).
  Bands occupy the lower-left to upper-right region, leaving clear space
  for title and metadata in the upper portion.

Usage:
    from shared.report_chrome import (
        ReportMetadata, build_cover_page, draw_page_header, draw_page_footer, find_logo,
    )

    logo_path = find_logo()
    metadata = ReportMetadata(title="AP Payment Testing Memo", ...)
    build_cover_page(story, styles, metadata, doc.width, logo_path)
    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    Image,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from pdf_generator import (
    ClassicalColors,
    DoubleRule,
    format_classical_date,
)
from shared.report_styles import (
    FONT_BODY,
    FONT_ITALIC,
    FONT_TITLE,
    MARGIN_LEFT,
    SIZE_DISCLAIMER,
    SIZE_FOOTER,
    SPACE_COVER_AFTER_LOGO,
    SPACE_COVER_AFTER_RULE,
    SPACE_COVER_AFTER_TITLE,
    SPACE_FOOTER_Y,
)


def _safe_style(styles: dict, *names):
    """Retrieve the first matching style from *styles*.

    Handles both ``dict`` (from ``create_memo_styles()``) and reportlab
    ``StyleSheet1`` (from ``create_classical_styles()``), which raises
    ``KeyError`` on missing keys instead of returning ``None``.
    """
    for name in names:
        try:
            return styles[name]
        except (KeyError, TypeError):
            continue
    # Ultimate fallback — a minimal body style
    from reportlab.lib.styles import ParagraphStyle

    return ParagraphStyle("_Fallback", fontName=FONT_BODY, fontSize=10)


# =============================================================================
# Diagonal Color Bands — Cover Page Background
# =============================================================================

_BAND_ANGLE_DEG = 20
_BAND_BLEED = 60  # horizontal bleed beyond page edges (pt)
_BAND_TAN = math.tan(math.radians(_BAND_ANGLE_DEG))
_BAND_COS = math.cos(math.radians(_BAND_ANGLE_DEG))

# Band definitions: (y_base_pt, perp_width_pt, color, alpha)
# y_base: where the lower edge intersects x=0 (from page bottom)
# perp_width: perpendicular thickness of the band
# Ordered back-to-front for correct visual layering
_COVER_BANDS: list[tuple] = [
    (-60, 200, ClassicalColors.OBSIDIAN, 0.05),  # Wide subtle wash
    (10, 130, ClassicalColors.OBSIDIAN_DEEP, 0.82),  # Primary bold band
    (75, 35, ClassicalColors.SAGE, 0.30),  # Sage accent stripe
    (130, 80, ClassicalColors.GOLD_INSTITUTIONAL, 0.45),  # Gold accent band
    (210, 18, ClassicalColors.GOLD_INSTITUTIONAL, 0.15),  # Thin gold highlight
]


class CoverBands(Flowable):
    """Diagonal color bands — cover page background element.

    Zero-height flowable that renders 5 overlapping diagonal bands across the
    full page using the Oat & Obsidian brand palette.  Must be the FIRST
    element in the story so bands render behind subsequent cover page content
    (logo, title, metadata) in PDF's painter-model draw order.

    Design: 5 bands at 20° sweep (lower-left → upper-right), varying widths
    (18–200 pt) and opacities (5%–82%) for layered depth.  A faint oatmeal
    background tint (3%) provides warmth.
    """

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        return (availWidth, 0)

    def draw(self) -> None:
        c = self.canv
        page_w, page_h = c._pagesize

        # Determine canvas-to-page coordinate offset.
        # As the first 0-height flowable, the canvas origin is at
        # (frame._x1, frame._y2) in absolute page coordinates.
        frame = getattr(c, "_frame", None)
        if frame is not None:
            off_x = frame._x1
            off_y = frame._y2
        else:
            off_x = 0.75 * 72  # fallback: 0.75" left margin
            off_y = page_h - 1.0 * 72  # fallback: 1" top margin

        # Faint oatmeal background tint (3% opacity)
        c.saveState()
        c.setFillColor(ClassicalColors.OATMEAL)
        c.setFillAlpha(0.03)
        c.rect(-off_x, -off_y, page_w, page_h, fill=1, stroke=0)
        c.restoreState()

        # Draw diagonal bands (back-to-front)
        x_l = -_BAND_BLEED
        x_r = page_w + _BAND_BLEED

        for y_base, width, color, alpha in _COVER_BANDS:
            vert = width / _BAND_COS  # vertical offset for perpendicular width

            # Lower edge endpoints: y = y_base + x * tan(angle)
            y_bl = y_base + x_l * _BAND_TAN
            y_br = y_base + x_r * _BAND_TAN
            # Upper edge: offset by vert
            y_tl = y_bl + vert
            y_tr = y_br + vert

            c.saveState()
            c.setFillColor(color)
            c.setFillAlpha(alpha)

            p = c.beginPath()
            p.moveTo(x_l - off_x, y_bl - off_y)
            p.lineTo(x_r - off_x, y_br - off_y)
            p.lineTo(x_r - off_x, y_tr - off_y)
            p.lineTo(x_l - off_x, y_tl - off_y)
            p.close()
            c.drawPath(p, fill=1, stroke=0)
            c.restoreState()


# =============================================================================
# Data model
# =============================================================================


@dataclass(frozen=True)
class ReportMetadata:
    """Metadata for a report cover page.

    All fields except ``title`` are optional — the cover page adapts
    gracefully when fields are missing.

    Source document transparency (Sprint 6):
      - ``source_document``: uploaded filename (required fallback)
      - ``source_document_title``: parsed document title from metadata (optional)
      - ``source_context_note``: additional context, e.g. "derived from consolidated statement" (optional)

    Rendering rules:
      - If title present: show title as "Source Document", filename as "Source File"
      - If title absent: show filename as "Source Document" (backwards-compatible)
    """

    title: str
    subtitle: str = ""
    client_name: str = ""
    engagement_period: str = ""
    source_document: str = ""
    source_document_title: str = ""
    source_context_note: str = ""
    reference: str = ""


# =============================================================================
# Logo discovery
# =============================================================================

_LOGO_FILENAME = "PaciolusLogo_LightBG.png"


def find_logo() -> Optional[str]:
    """Search standard paths for the Paciolus logo.

    Returns the absolute path as a string if found, or ``None``.
    Never raises — a missing logo is non-fatal.
    """
    backend_dir = Path(__file__).resolve().parent.parent  # backend/
    search_paths = [
        backend_dir.parent / "frontend" / "public" / _LOGO_FILENAME,
        backend_dir.parent / _LOGO_FILENAME,
        backend_dir / "assets" / _LOGO_FILENAME,
    ]
    for path in search_paths:
        if path.exists():
            return str(path)
    return None


# =============================================================================
# Cover page builder
# =============================================================================


def build_cover_page(
    story: list,
    styles: dict,
    metadata: ReportMetadata,
    doc_width: float,
    logo_path: Optional[str] = None,
) -> None:
    """Append cover page flowables to *story*.

    Structure:
      0. Diagonal color bands (background — rendered behind all content)
      1. Logo (or text-only "PACIOLUS" lockup if missing)
      2. Report title
      3. Subtitle (if provided)
      4. Gold DoubleRule
      5. Metadata table (client, period, source, reference, timestamp)
      6. PageBreak — content starts on page 2

    The function modifies *story* in-place and returns None.
    """
    # 0. Diagonal color bands background
    story.append(CoverBands())

    # 1. Logo or text lockup
    if logo_path:
        try:
            logo = Image(logo_path, width=1.2 * inch, height=0.4 * inch, kind="proportional")
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, SPACE_COVER_AFTER_LOGO))
        except (OSError, ValueError):
            _append_text_lockup(story, styles)
    else:
        _append_text_lockup(story, styles)

    # 2. Title
    title_style = _safe_style(styles, "ClassicalTitle", "MemoTitle")
    story.append(Paragraph(metadata.title, title_style))
    story.append(Spacer(1, SPACE_COVER_AFTER_TITLE))

    # 3. Subtitle (optional)
    if metadata.subtitle:
        subtitle_style = _safe_style(styles, "ClassicalSubtitle", "MemoSubtitle")
        story.append(Paragraph(metadata.subtitle, subtitle_style))

    # 4. DoubleRule
    story.append(
        DoubleRule(width=doc_width, color=ClassicalColors.GOLD_INSTITUTIONAL, spaceAfter=SPACE_COVER_AFTER_RULE)
    )

    # 5. Metadata table
    _append_metadata_table(story, styles, metadata, doc_width)

    # 6. PageBreak
    story.append(PageBreak())


def _append_text_lockup(story: list, styles: dict) -> None:
    """Fallback text lockup when the logo image is unavailable."""
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle

    lockup_title = ParagraphStyle(
        "_CoverLockupTitle",
        fontName=FONT_TITLE,
        fontSize=18,
        textColor=ClassicalColors.GOLD_INSTITUTIONAL,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    lockup_subtitle = ParagraphStyle(
        "_CoverLockupSubtitle",
        fontName=FONT_ITALIC,
        fontSize=10,
        textColor=ClassicalColors.OBSIDIAN_500,
        alignment=TA_CENTER,
        spaceAfter=SPACE_COVER_AFTER_LOGO,
    )
    story.append(Paragraph("PACIOLUS", lockup_title))
    story.append(Paragraph("Audit Intelligence", lockup_subtitle))


def _append_metadata_table(
    story: list,
    styles: dict,
    metadata: ReportMetadata,
    doc_width: float,
) -> None:
    """Build the clean key-value metadata table on the cover page."""
    body_style = _safe_style(styles, "MemoBody", "BodyText")
    rows: list[list[str]] = []

    if metadata.client_name:
        rows.append(["Client", metadata.client_name])
    if metadata.engagement_period:
        rows.append(["Period", metadata.engagement_period])

    # Source document transparency (Sprint 6):
    # Title present → show title as "Source Document" + filename as "Source File"
    # Title absent  → show filename as "Source Document" (backwards-compatible)
    if metadata.source_document_title:
        rows.append(["Source Document", metadata.source_document_title])
        if metadata.source_document:
            rows.append(["Source File", metadata.source_document])
    elif metadata.source_document:
        rows.append(["Source Document", metadata.source_document])
    if metadata.source_context_note:
        rows.append(["Source Context", metadata.source_context_note])

    if metadata.reference:
        rows.append(["Reference", metadata.reference])

    # Always include prepared timestamp
    rows.append(["Prepared", format_classical_date()])

    if not rows:
        return

    # Wrap cells in Paragraphs for consistent styling
    table_data = []
    for label, value in rows:
        table_data.append(
            [
                Paragraph(f"<b>{label}</b>", body_style),
                Paragraph(value, body_style),
            ]
        )

    col_widths = [1.8 * inch, doc_width - 1.8 * inch]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), FONT_BODY),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (-1, -1), ClassicalColors.OBSIDIAN_600),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))


# =============================================================================
# Page header callback (pages 2+)
# =============================================================================


def draw_page_header(canvas, doc, title: str = "", reference: str = "") -> None:
    """Canvas callback for pages 2+.

    Draws a gold double rule at the top with the report title (left) and
    reference (right).  Call via ``onLaterPages``.
    """
    page_width, page_height = letter
    margin = MARGIN_LEFT * inch

    canvas.saveState()

    # Gold double rule at top
    canvas.setStrokeColor(ClassicalColors.GOLD_INSTITUTIONAL)
    y_thick = page_height - 0.5 * inch
    y_thin = y_thick - 0.05 * inch

    canvas.setLineWidth(2)
    canvas.line(margin, y_thick, page_width - margin, y_thick)
    canvas.setLineWidth(0.5)
    canvas.line(margin, y_thin, page_width - margin, y_thin)

    # Title (left) + reference (right) below rule
    y_text = y_thin - 12
    canvas.setFont(FONT_ITALIC, 8)
    canvas.setFillColor(ClassicalColors.OBSIDIAN_500)
    if title:
        canvas.drawString(margin, y_text, title)
    if reference:
        canvas.drawRightString(page_width - margin, y_text, reference)

    canvas.restoreState()


# =============================================================================
# Page footer callback (all pages)
# =============================================================================

_DISCLAIMER_LINE = (
    "This output supports professional judgment. It does not constitute an audit, review, or attestation engagement."
)


def draw_page_footer(canvas, doc) -> None:
    """Canvas callback for all pages.

    Draws a centered page number and one-line zero-storage disclaimer
    at the bottom of every page.
    """
    page_width = letter[0]

    canvas.saveState()

    # Page number — classical style: — N —
    page_num = doc.page
    canvas.setFont(FONT_BODY, SIZE_FOOTER + 1)
    canvas.setFillColor(ClassicalColors.OBSIDIAN_500)
    canvas.drawCentredString(page_width / 2, SPACE_FOOTER_Y, f"\u2014 {page_num} \u2014")

    # Disclaimer line
    canvas.setFont(FONT_BODY, SIZE_DISCLAIMER)
    canvas.setFillColor(ClassicalColors.OBSIDIAN_500)
    canvas.drawCentredString(page_width / 2, SPACE_FOOTER_Y - 12, _DISCLAIMER_LINE)

    canvas.restoreState()
