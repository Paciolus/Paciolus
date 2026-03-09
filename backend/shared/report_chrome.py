"""
Shared Report Chrome — Sprint 2: Report Standardization

Cover page, page header, and page footer shared by all PDF generators.
Replaces the per-generator header/footer implementations with a single
set of composable building blocks.

Inverted Dark Field (cover page background):
  Solid dark (#1c1c1c) fill with 4 geometric triangles in muted
  brand-adjacent tones (sage, warm stone, light gold).  Gold gradient
  rules frame the title block.

Usage:
    from shared.report_chrome import (
        ReportMetadata, build_cover_page, draw_page_header, draw_page_footer, find_logo,
    )

    logo_path = find_logo()
    metadata = ReportMetadata(title="AP Payment Testing Memo", ...)
    build_cover_page(story, styles, metadata, doc.width, logo_path)
    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
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


def _safe_style(styles: dict, *names: str) -> Any:
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
# Inverted Dark Field — Cover Page Background
# =============================================================================

# Triangle definitions: ((x1,y1, x2,y2, x3,y3), hex_color, alpha)
# Coordinates in absolute page space (origin bottom-left, Letter 612×792 pt)
_COVER_TRIANGLES: list[tuple] = [
    ((306, 792, 612, 792, 612, 512), "#4a5c42", 0.35),  # Upper-right, sage
    ((428, 792, 612, 792, 612, 624), "#8a7a5a", 0.30),  # Upper-right, warm stone
    ((520, 792, 612, 792, 612, 708), "#c4b48a", 0.25),  # Upper-right, light gold
    ((0, 0, 306, 0, 0, 232), "#4a5c42", 0.20),  # Lower-left echo, sage
]


class CoverBands(Flowable):
    """Inverted Dark Field — cover page background element.

    Zero-height flowable that renders a solid dark (#1c1c1c) full-page fill
    overlaid with 4 geometric triangles in muted brand-adjacent tones.
    Must be the FIRST element in the story so the background renders behind
    subsequent cover page content in PDF's painter-model draw order.
    """

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        return (availWidth, 0)

    def draw(self) -> None:
        c = self.canv
        page_w, page_h = c._pagesize

        # Determine canvas-to-page coordinate offset.
        frame = getattr(c, "_frame", None)
        if frame is not None:
            off_x = frame._x1
            off_y = frame._y2
        else:
            off_x = 0.75 * 72  # fallback: 0.75" left margin
            off_y = page_h - 1.0 * 72  # fallback: 1" top margin

        # Solid dark background fill
        c.saveState()
        c.setFillColor(HexColor("#1c1c1c"))
        c.rect(-off_x, -off_y, page_w, page_h, stroke=0, fill=1)
        c.restoreState()

        # Geometric triangles
        for verts, hex_color, alpha in _COVER_TRIANGLES:
            x1, y1, x2, y2, x3, y3 = verts
            c.saveState()
            c.setFillColor(HexColor(hex_color))
            c.setFillAlpha(alpha)
            p = c.beginPath()
            p.moveTo(x1 - off_x, y1 - off_y)
            p.lineTo(x2 - off_x, y2 - off_y)
            p.lineTo(x3 - off_x, y3 - off_y)
            p.close()
            c.drawPath(p, stroke=0, fill=1)
            c.restoreState()


# =============================================================================
# Gold gradient rule — simulated fade for cover page
# =============================================================================

_GRADIENT_SEGMENTS = 30
_GOLD_RULE = HexColor("#c9a84c")


class GoldGradientRule(Flowable):
    """Horizontal 1 pt rule that fades transparent -> gold -> transparent.

    Simulates a gradient stroke by drawing short line segments with stepped
    opacity (0->0.8 over the left third, 0.8 across the middle, 0.8->0
    over the right third).
    """

    def __init__(self, width: float, spaceAfter: float = 0) -> None:
        super().__init__()
        self._rule_width = width
        self.spaceAfter = spaceAfter

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        return (self._rule_width, 1)

    def draw(self) -> None:
        c = self.canv
        w = self._rule_width
        seg_w = w / _GRADIENT_SEGMENTS

        for i in range(_GRADIENT_SEGMENTS):
            frac = i / _GRADIENT_SEGMENTS
            if frac < 1 / 3:
                alpha = 0.8 * (frac * 3)
            elif frac < 2 / 3:
                alpha = 0.8
            else:
                alpha = 0.8 * (1 - (frac - 2 / 3) * 3)

            c.saveState()
            c.setStrokeColor(_GOLD_RULE)
            c.setStrokeAlpha(alpha)
            c.setLineWidth(1)
            c.line(i * seg_w, 0, (i + 1) * seg_w, 0)
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
    # Fix 6: Engagement context fields
    fiscal_year_end: str = ""
    prepared_by: str = ""
    reviewed_by: str = ""
    report_status: str = "Draft"  # "Draft" or "Final"


# =============================================================================
# Logo discovery
# =============================================================================

_LOGO_FILENAME = "PaciolusLogo_LightBG.png"
_LOGO_FILENAME_DARK = "PaciolusLogo_DarkBG.png"


def _find_logo_file(filename: str) -> Optional[str]:
    """Search standard paths for a logo file by name.

    Returns the absolute path as a string if found, or ``None``.
    Never raises — a missing logo is non-fatal.
    """
    backend_dir = Path(__file__).resolve().parent.parent  # backend/
    search_paths = [
        backend_dir.parent / "frontend" / "public" / filename,
        backend_dir.parent / filename,
        backend_dir / "assets" / filename,
    ]
    for path in search_paths:
        if path.exists():
            return str(path)
    return None


def find_logo() -> Optional[str]:
    """Return the light-background logo path (for page headers)."""
    return _find_logo_file(_LOGO_FILENAME)


def find_logo_dark() -> Optional[str]:
    """Return the dark-background logo path (for the cover page)."""
    return _find_logo_file(_LOGO_FILENAME_DARK)


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
      0. Inverted Dark Field background (dark fill + triangles)
      1. Logo (or text-only "PACIOLUS" lockup if missing)
      2. Gold gradient rule above title
      3. Report title
      4. Subtitle (if provided)
      5. Gold gradient rule below title
      6. Metadata table (client, period, source, reference, timestamp)
      7. PageBreak — content starts on page 2

    The function modifies *story* in-place and returns None.
    """
    # 0. Inverted Dark Field background
    story.append(CoverBands())

    # 1. Logo or text lockup — prefer dark-BG variant for dark cover
    cover_logo = find_logo_dark() or logo_path
    if cover_logo:
        try:
            logo = Image(cover_logo, width=1.2 * inch, height=0.4 * inch, kind="proportional")
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, SPACE_COVER_AFTER_LOGO))
        except (OSError, ValueError):
            _append_text_lockup(story, styles)
    else:
        _append_text_lockup(story, styles)

    # 2. Gold gradient rule above title
    story.append(GoldGradientRule(width=doc_width, spaceAfter=8))

    # 3. Title
    title_style = _safe_style(styles, "ClassicalTitle", "MemoTitle")
    cover_title = ParagraphStyle(
        "_CoverTitle",
        parent=title_style,
        textColor=HexColor("#f5f0e8"),
    )
    story.append(Paragraph(metadata.title, cover_title))
    story.append(Spacer(1, SPACE_COVER_AFTER_TITLE))

    # 4. Subtitle (optional)
    if metadata.subtitle:
        subtitle_style = _safe_style(styles, "ClassicalSubtitle", "MemoSubtitle")
        cover_subtitle = ParagraphStyle(
            "_CoverSubtitle",
            parent=subtitle_style,
            textColor=HexColor("#888888"),
        )
        story.append(Paragraph(metadata.subtitle, cover_subtitle))

    # 5. Gold gradient rule below title
    story.append(GoldGradientRule(width=doc_width, spaceAfter=SPACE_COVER_AFTER_RULE))

    # 6. Metadata table
    _append_metadata_table(story, styles, metadata, doc_width)

    # 7. PageBreak
    story.append(PageBreak())


def _append_text_lockup(story: list, styles: dict) -> None:
    """Fallback text lockup when the logo image is unavailable."""
    lockup_title = ParagraphStyle(
        "_CoverLockupTitle",
        fontName=FONT_TITLE,
        fontSize=18,
        textColor=HexColor("#c9a84c"),
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    lockup_subtitle = ParagraphStyle(
        "_CoverLockupSubtitle",
        fontName=FONT_ITALIC,
        fontSize=10,
        textColor=HexColor("#8a7a5a"),
        alignment=TA_CENTER,
        spaceAfter=SPACE_COVER_AFTER_LOGO,
    )
    story.append(Paragraph("PACIOLUS", lockup_title))
    story.append(Paragraph("Particularis de Computis", lockup_subtitle))


def _append_metadata_table(
    story: list,
    styles: dict,
    metadata: ReportMetadata,
    doc_width: float,
) -> None:
    """Build the clean key-value metadata table on the cover page."""
    rows: list[list[str]] = []

    if metadata.client_name:
        rows.append(["Client", metadata.client_name])
    if metadata.fiscal_year_end:
        rows.append(["Fiscal Year End", metadata.fiscal_year_end])
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
    rows.append(["Generated", format_classical_date()])
    # Part 1: Engagement practitioner fields (not Paciolus personnel)
    if metadata.prepared_by:
        rows.append(["Engagement Practitioner", metadata.prepared_by])
    if metadata.reviewed_by:
        rows.append(["Engagement Reviewer", metadata.reviewed_by])
    rows.append(["Report Status", metadata.report_status or "Draft"])

    if not rows:
        return

    # Cover-specific styles for dark background
    label_style = ParagraphStyle(
        "_CoverMetaLabel",
        fontName=FONT_BODY,
        fontSize=10,
        textColor=HexColor("#f5f0e8"),
    )
    value_style = ParagraphStyle(
        "_CoverMetaValue",
        fontName=FONT_BODY,
        fontSize=10,
        textColor=Color(1, 1, 1, alpha=0.6),
    )

    table_data = []
    for label, value in rows:
        table_data.append(
            [
                Paragraph(f"<b>{label}</b>", label_style),
                Paragraph(value, value_style),
            ]
        )

    col_widths = [1.8 * inch, doc_width - 1.8 * inch]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), FONT_BODY),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LINEABOVE", (0, 0), (-1, 0), 1, HexColor("#c9a84c")),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, Color(1, 1, 1, alpha=0.15)),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)

    # Part 2: "Generated By" separator — clarifies Paciolus is the tool, not a co-preparer
    story.append(Spacer(1, 8))
    gen_note_style = ParagraphStyle(
        "_CoverGenNote",
        fontName=FONT_ITALIC,
        fontSize=8,
        textColor=Color(1, 1, 1, alpha=0.45),
        alignment=TA_CENTER,
    )
    story.append(
        Paragraph(
            "Report generated by Paciolus\u00ae Diagnostic Intelligence. Engagement information entered by user.",
            gen_note_style,
        )
    )
    story.append(Spacer(1, 8))


# =============================================================================
# Page header callback (pages 2+)
# =============================================================================


def draw_page_header(canvas: Any, doc: Any, title: str = "", reference: str = "") -> None:
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
    "Prepared using Paciolus Diagnostic Intelligence. Does not constitute an audit, review, or attestation engagement."
)


def draw_page_footer(canvas: Any, doc: Any) -> None:
    """Canvas callback for all pages.

    Cover page (page 1): subtle disclaimer only, no page number.
    Later pages: centered page number and disclaimer.
    """
    page_width = letter[0]

    canvas.saveState()

    if doc.page == 1:
        # Cover page — no page number; subtle disclaimer for dark background
        canvas.setFont(FONT_BODY, 7)
        canvas.setFillColor(Color(1, 1, 1, alpha=0.25))
        canvas.drawCentredString(page_width / 2, SPACE_FOOTER_Y - 12, _DISCLAIMER_LINE)
    else:
        # Page number — classical style: — N —
        canvas.setFont(FONT_BODY, SIZE_FOOTER + 1)
        canvas.setFillColor(ClassicalColors.OBSIDIAN_500)
        canvas.drawCentredString(page_width / 2, SPACE_FOOTER_Y, f"\u2014 {doc.page} \u2014")

        # Disclaimer line
        canvas.setFont(FONT_BODY, SIZE_DISCLAIMER)
        canvas.setFillColor(ClassicalColors.OBSIDIAN_500)
        canvas.drawCentredString(page_width / 2, SPACE_FOOTER_Y - 12, _DISCLAIMER_LINE)

    canvas.restoreState()
