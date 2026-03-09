"""
PDF report generator for diagnostic summaries.

Sprint 29: Classical PDF Enhancement — "Renaissance Ledger"
Honors Luca Pacioli (father of accounting) with institutional elegance.

Design Philosophy: "Renaissance Ledger Meets Modern Institution"
- Classical serif typography (Times-Roman family)
- Leader dots for financial summaries
- Double-rule gold borders
- Ledger-style tables with horizontal rules only
- Section ornaments (fleurons)
- Warm paper background
- Pacioli watermark
"""

import io
from datetime import UTC, datetime
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from security_utils import log_secure_operation


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

    # ═══════════════════════════════════════════════════════════════
    # TITLE STYLES
    # ═══════════════════════════════════════════════════════════════

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

    # ═══════════════════════════════════════════════════════════════
    # SECTION HEADERS
    # ═══════════════════════════════════════════════════════════════

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

    # ═══════════════════════════════════════════════════════════════
    # BODY TEXT
    # ═══════════════════════════════════════════════════════════════

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

    # ═══════════════════════════════════════════════════════════════
    # STATUS STYLES
    # ═══════════════════════════════════════════════════════════════

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

    # ═══════════════════════════════════════════════════════════════
    # TABLE STYLES
    # ═══════════════════════════════════════════════════════════════

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

    # ═══════════════════════════════════════════════════════════════
    # FOOTER STYLES
    # ═══════════════════════════════════════════════════════════════

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

    return styles


class DoubleRule(Flowable):
    """
    A double-rule flowable for classical document borders.

    Creates the signature "Goldman Sachs" style header rule:
    thick line + gap + thin line
    """

    def __init__(
        self,
        width: float,
        color: Any = ClassicalColors.GOLD_INSTITUTIONAL,
        thick: float = 2,
        thin: float = 0.5,
        gap: float = 2,
        spaceAfter: float = 12,
    ) -> None:
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thick = thick
        self.thin = thin
        self.gap = gap
        self._spaceAfter = spaceAfter

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)

        # Thick rule
        self.canv.setLineWidth(self.thick)
        self.canv.line(0, self.gap + self.thin, self.width, self.gap + self.thin)

        # Thin rule below
        self.canv.setLineWidth(self.thin)
        self.canv.line(0, 0, self.width, 0)

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self.width = min(self.width, availWidth) if self.width else availWidth
        return (self.width, self.thick + self.gap + self.thin + self._spaceAfter)


class LedgerRule(Flowable):
    """A simple horizontal ledger rule."""

    def __init__(
        self,
        width: Optional[float] = None,
        thickness: float = 0.5,
        color: Any = ClassicalColors.LEDGER_RULE,
        spaceBefore: float = 8,
        spaceAfter: float = 8,
    ) -> None:
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color
        self._spaceBefore = spaceBefore
        self._spaceAfter = spaceAfter

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self.width = min(self.width, availWidth) if self.width else availWidth
        return (self.width, self.thickness + self._spaceBefore + self._spaceAfter)


def format_classical_date(dt: datetime = None) -> str:
    """
    Format date in classical style: '4th February 2026'
    """
    if dt is None:
        dt = datetime.now(UTC)

    day = dt.day
    # Ordinal suffix
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    return dt.strftime(f"{day}{suffix} %B %Y")


def generate_reference_number() -> str:
    """Generate institutional reference number: PAC-YYYY-MMDD-NNN"""
    now = datetime.now(UTC)
    # Simple sequential based on time (in production, use a proper sequence)
    seq = (now.hour * 3600 + now.minute * 60 + now.second) % 1000
    return f"PAC-{now.year}-{now.month:02d}{now.day:02d}-{seq:03d}"


def create_leader_dots(label: str, value: str, total_chars: int = 55) -> str:
    """
    Create a leader-dot line for financial summaries.

    Example: "Total Debits .......................... $1,234,567.89"
    """
    # Calculate dots needed
    label_len = len(label)
    value_len = len(value)
    dots_needed = total_chars - label_len - value_len - 2  # -2 for spaces

    if dots_needed < 3:
        dots_needed = 3

    dots = "." * dots_needed
    return f"{label} {dots} {value}"


class PaciolusReportGenerator:
    """
    Generates diagnostic reports in PDF format.

    Sprint 29: Renaissance Ledger aesthetic honoring Luca Pacioli.
    """

    def __init__(
        self,
        audit_result: dict[str, Any],
        filename: str = "diagnostic",
        prepared_by: Optional[str] = None,
        reviewed_by: Optional[str] = None,
        workpaper_date: Optional[str] = None,
        include_signoff: bool = False,
    ):
        self.audit_result = audit_result
        self.filename = filename
        self.styles = create_classical_styles()
        self.buffer = io.BytesIO()
        # Lazy import to avoid circular dependency (report_chrome imports from pdf_generator)
        from shared.report_chrome import find_logo

        self.logo_path = find_logo()
        self.reference_number = generate_reference_number()
        self.page_count = 0
        # Sprint 53: Workpaper fields (deprecated Sprint 7 — gated by include_signoff)
        self.prepared_by = prepared_by
        self.reviewed_by = reviewed_by
        self.workpaper_date = workpaper_date or datetime.now().strftime("%Y-%m-%d")
        self.include_signoff = include_signoff

        log_secure_operation("pdf_generator_init", f"Initializing Classical PDF generator for: {filename}")

    def generate(self) -> bytes:
        """Generate the PDF report with Renaissance Ledger aesthetic."""
        log_secure_operation("pdf_generate_start", "Starting Classical PDF generation")

        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1.0 * inch,  # Extra space for header decorations
            bottomMargin=1.0 * inch,
        )

        story = []

        # Build cover page (shared chrome)
        # Lazy import to avoid circular dependency (report_chrome imports from pdf_generator)
        from shared.report_chrome import ReportMetadata, build_cover_page, draw_page_footer

        metadata = ReportMetadata(
            title="DIAGNOSTIC INTELLIGENCE SUMMARY",
            subtitle=f"Analysis Report for {self.filename}",
            source_document=self.filename,
            reference=self.reference_number,
            prepared_by=self.prepared_by or "",
            reviewed_by=self.reviewed_by or "",
        )
        build_cover_page(story, self.styles, metadata, doc.width, self.logo_path)

        # Fix 5: Table of Contents
        story.extend(self._build_table_of_contents())

        # Fix 12: Data Intake Summary
        story.extend(self._build_data_intake_summary())

        # Build document sections
        story.extend(self._build_executive_summary())
        # Fix 7: Section dividers between major sections
        story.append(LedgerRule(color=ClassicalColors.GOLD_INSTITUTIONAL, thickness=0.5, spaceBefore=12, spaceAfter=12))
        story.extend(self._build_population_composition())
        story.append(LedgerRule(color=ClassicalColors.GOLD_INSTITUTIONAL, thickness=0.5, spaceBefore=12, spaceAfter=12))
        story.extend(self._build_risk_summary())
        story.append(LedgerRule(color=ClassicalColors.GOLD_INSTITUTIONAL, thickness=0.5, spaceBefore=12, spaceAfter=12))
        story.extend(self._build_anomaly_details())
        story.extend(self._build_workpaper_signoff())  # Sprint 53
        # Fix 10: Limitations section before footer
        story.extend(self._build_limitations_section())
        story.extend(self._build_classical_footer())

        # Build with page decorations
        # Cover page (page 1) gets footer only; later pages get full decorations
        def _on_first_page(canvas: Any, doc: Any) -> None:
            self._draw_diagnostic_watermark(canvas)
            draw_page_footer(canvas, doc)

        def _on_later_pages(canvas: Any, doc: Any) -> None:
            self._draw_diagnostic_watermark(canvas)
            draw_page_footer(canvas, doc)

        doc.build(
            story,
            onFirstPage=_on_first_page,
            onLaterPages=_on_later_pages,
        )

        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()

        log_secure_operation("pdf_generate_complete", f"Classical PDF generated: {len(pdf_bytes)} bytes")

        return pdf_bytes

    def _draw_diagnostic_watermark(self, canvas: Any) -> None:
        """Draw the Pacioli watermark — diagnostic PDF only.

        The shared draw_page_footer() handles page numbers and disclaimer;
        this method adds the distinctive diagonal Latin watermark that is
        unique to the diagnostic intelligence summary.
        """
        page_width, page_height = letter

        canvas.saveState()
        canvas.setFillColor(ClassicalColors.OATMEAL_400)
        canvas.setFillAlpha(0.04)  # Very subtle
        canvas.setFont("Times-Italic", 48)
        canvas.translate(page_width / 2, page_height / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "Particularis de Computis")
        canvas.restoreState()

    def _build_section_ornament(self) -> list:
        """Build a section break ornament (fleuron)."""
        return [
            Spacer(1, 4),
            Paragraph("❧", self.styles["SectionOrnament"]),
            Spacer(1, 4),
        ]

    def _build_table_of_contents(self) -> list:
        """Fix 5: Build a compact Table of Contents on page 2."""
        elements = []

        elements.append(Paragraph("Table of Contents", self.styles["SectionHeader"]))
        elements.append(LedgerRule(color=ClassicalColors.GOLD_INSTITUTIONAL, thickness=1))
        elements.append(Spacer(1, 8))

        # TOC entries — these are the major sections in order
        toc_entries = [
            "Data Intake Summary",
            "Executive Summary",
            "Population Composition",
            "Risk Assessment",
            "Exception Details",
            "Limitations",
        ]

        for i, entry in enumerate(toc_entries, 1):
            elements.append(
                Paragraph(
                    f"{i}. &nbsp;&nbsp;{entry}",
                    self.styles["BodyText"],
                )
            )

        elements.append(Spacer(1, 4))
        elements.append(
            Paragraph(
                "<i>Page numbers are sequential from the cover page. "
                "Section ordering reflects the standard diagnostic report structure.</i>",
                self.styles["BodyText"],
            )
        )
        elements.append(Spacer(1, 12))

        return elements

    def _build_data_intake_summary(self) -> list:
        """Fix 12: Build the Data Intake Summary section.

        Shows data quality characteristics of the input file so reviewers
        know how much to trust the output.
        """
        elements = []

        elements.append(Paragraph("Data Intake Summary", self.styles["SectionHeader"]))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        elements.append(Spacer(1, 4))

        row_count = self.audit_result.get("row_count", 0)
        col_detection = self.audit_result.get("column_detection", {})
        data_quality = self.audit_result.get("data_quality", {})

        # Extract data quality metrics
        rows_accepted = row_count
        rows_rejected = data_quality.get("rows_rejected", 0)
        null_accounts = data_quality.get("null_account_codes", 0)
        duplicates_detected = data_quality.get("duplicate_accounts", False)
        unrecognized_types = data_quality.get("unrecognized_types", 0)
        completeness = data_quality.get("completeness_score", 100)

        cell_style = self.styles["TableCell"]
        header_style = self.styles["TableHeader"]

        intake_data = [
            [Paragraph("Field", header_style), Paragraph("Value", header_style)],
            [Paragraph("File Received", cell_style), Paragraph(self.filename or "—", cell_style)],
            [Paragraph("Rows Submitted", cell_style), Paragraph(f"{row_count + rows_rejected:,}", cell_style)],
            [Paragraph("Rows Accepted", cell_style), Paragraph(f"{rows_accepted:,}", cell_style)],
            [Paragraph("Rows Rejected / Skipped", cell_style), Paragraph(str(rows_rejected), cell_style)],
            [Paragraph("Null / Blank Account Codes", cell_style), Paragraph(str(null_accounts), cell_style)],
            [
                Paragraph("Duplicate Account Codes", cell_style),
                Paragraph("Yes" if duplicates_detected else "No", cell_style),
            ],
            [Paragraph("Unrecognized Account Types", cell_style), Paragraph(str(unrecognized_types), cell_style)],
            [Paragraph("Data Completeness", cell_style), Paragraph(f"{completeness:.0f}%", cell_style)],
        ]

        # Column detection info
        if col_detection:
            confidence = col_detection.get("overall_confidence", 0)
            if isinstance(confidence, (int, float)):
                intake_data.append(
                    [
                        Paragraph("Column Detection Confidence", cell_style),
                        Paragraph(f"{confidence:.0%}", cell_style),
                    ]
                )

        intake_table = Table(intake_data, colWidths=[3.0 * inch, 3.5 * inch], repeatRows=1)
        intake_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    # Fix 7: Row banding
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ClassicalColors.WHITE, ClassicalColors.OATMEAL_PAPER]),
                ]
            )
        )
        elements.append(intake_table)

        # Summary note
        if rows_rejected == 0 and null_accounts == 0 and not duplicates_detected:
            elements.append(Spacer(1, 4))
            elements.append(
                Paragraph(
                    "<i>No data quality issues were identified during intake processing.</i>",
                    self.styles["BodyText"],
                )
            )

        elements.append(Spacer(1, 12))
        return elements

    def _build_limitations_section(self) -> list:
        """Fix 10: Build the formal Limitations section on the final page."""
        elements = []

        elements.append(Spacer(1, 16))
        elements.append(Paragraph("Limitations", self.styles["SectionHeader"]))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        elements.append(Spacer(1, 4))

        limitation_text = (
            "This report was prepared using Paciolus Diagnostic Intelligence and is intended to "
            "support the professional judgment of the engagement practitioner. The procedures "
            "reflected herein are analytical and diagnostic in nature and do not constitute an "
            "audit, review, compilation, or attestation engagement as defined under AICPA "
            "professional standards or PCAOB auditing standards. Findings and observations "
            "require independent corroboration before conclusions may be drawn."
        )
        elements.append(Paragraph(limitation_text, self.styles["BodyText"]))
        elements.append(Spacer(1, 6))

        # Part 3: Practitioner liability boundary
        practitioner_text = (
            "Practitioner information appearing on the cover of this report is provided by the "
            "user and reflects the engagement team responsible for applying professional judgment "
            "to this output. Paciolus does not review, endorse, certify, or assume responsibility "
            "for conclusions drawn by the engagement practitioner. The presence of practitioner "
            "credentials in this report does not constitute a representation by Paciolus regarding "
            "the quality or completeness of any professional engagement."
        )
        elements.append(Paragraph(practitioner_text, self.styles["BodyText"]))
        elements.append(Spacer(1, 6))

        zero_storage = (
            "Zero-Storage Architecture: All financial data was processed in-memory during this "
            "analysis session and was not persisted to any storage medium. No client financial "
            "data is retained by Paciolus after the analysis session concludes."
        )
        elements.append(Paragraph(f"<i>{zero_storage}</i>", self.styles["BodyText"]))
        elements.append(Spacer(1, 8))

        return elements

    def _build_executive_summary(self) -> list:
        """Build the executive summary with leader dots and status badge."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles["SectionHeader"]))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))

        # Fix 8: Formal Trial Balance Status indicator
        is_balanced = self.audit_result.get("balanced", False)
        difference = self.audit_result.get("difference", 0)

        if is_balanced:
            status_label = "BALANCED"
            status_detail = f"Debits equal Credits (${abs(difference):,.2f} variance)"
            badge_border = ClassicalColors.SAGE
            status_style = "BalancedStatus"
        else:
            status_label = "OUT OF BALANCE"
            status_detail = f"Variance of ${abs(difference):,.2f} identified"
            badge_border = ClassicalColors.CLAY
            status_style = "UnbalancedStatus"

        # Formal status badge with label + detail
        badge_data = [
            [Paragraph(f"✓  {status_label}", self.styles[status_style])],
            [Paragraph(status_detail, self.styles["BodyText"])],
        ]
        badge_table = Table(badge_data, colWidths=[5 * inch])
        badge_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1.5, badge_border),
                    ("TOPPADDING", (0, 0), (0, 0), 8),
                    ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
                    ("TOPPADDING", (0, 1), (0, 1), 2),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("BACKGROUND", (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
                ]
            )
        )
        badge_table.hAlign = "CENTER"

        elements.append(Spacer(1, 8))
        elements.append(badge_table)
        elements.append(Spacer(1, 10))

        # Financial summary with leader dots
        total_debits = self.audit_result.get("total_debits", 0)
        total_credits = self.audit_result.get("total_credits", 0)
        difference = self.audit_result.get("difference", 0)
        row_count = self.audit_result.get("row_count", 0)
        threshold = self.audit_result.get("materiality_threshold", 0)

        leader_lines = [
            create_leader_dots("Total Debits", f"${total_debits:,.2f}"),
            create_leader_dots("Total Credits", f"${total_credits:,.2f}"),
            create_leader_dots("Variance", f"${difference:,.2f}"),
            create_leader_dots("Rows Analyzed", f"{row_count:,}"),
            create_leader_dots("Materiality Threshold", f"${threshold:,.2f}"),
        ]

        # Add consolidated info if applicable
        if self.audit_result.get("is_consolidated"):
            sheet_count = self.audit_result.get("sheet_count", 0)
            leader_lines.append(create_leader_dots("Sheets Consolidated", str(sheet_count)))

        for line in leader_lines:
            elements.append(Paragraph(line, self.styles["LeaderLine"]))

        elements.append(Spacer(1, 12))

        # Change 2: Risk-Weighted Coverage metric
        if total_debits > 0:
            abnormal_balances = self.audit_result.get("abnormal_balances", [])
            material_items = [ab for ab in abnormal_balances if ab.get("materiality") == "material"]
            flagged_value = sum(abs(ab.get("amount", 0)) for ab in material_items)
            coverage_pct = flagged_value / total_debits * 100 if total_debits else 0
            # Sprint 526 Fix 5: Cap coverage at 100%
            coverage_pct = min(coverage_pct, 100.0)

            coverage_lines = [
                create_leader_dots("Flagged Value (Material)", f"${flagged_value:,.2f}"),
                create_leader_dots("Total TB Population", f"${total_debits:,.2f}"),
                create_leader_dots("Risk-Weighted Coverage", f"{coverage_pct:.1f}%"),
            ]
            for line in coverage_lines:
                elements.append(Paragraph(line, self.styles["LeaderLine"]))

            if flagged_value > 0:
                note = (
                    f"Material exceptions affect {coverage_pct:.1f}% of total trial balance value "
                    f"by amount. Accounts above materiality threshold warrant corroborating "
                    f"procedures before conclusions can be drawn."
                )
            else:
                note = "Risk-Weighted Coverage: 0.0% — No material exceptions identified."
            elements.append(Spacer(1, 2))
            elements.append(Paragraph(note, self.styles["BodyText"]))
            elements.append(Spacer(1, 6))

        return elements

    def _build_population_composition(self) -> list:
        """Build the Population Composition section (Change 5).

        Uses category_totals from audit_result if available, or falls back
        to population_profile section_density data. Percentages are based
        on total_debits to match the TB population value.
        """
        elements = []

        category_totals = self.audit_result.get("category_totals", {})
        if not category_totals:
            return elements

        row_count = self.audit_result.get("row_count", 0)

        # Map category_totals keys to display names
        type_mapping = [
            ("Asset", category_totals.get("total_assets", 0)),
            ("Liability", category_totals.get("total_liabilities", 0)),
            ("Equity", category_totals.get("total_equity", 0)),
            ("Revenue", category_totals.get("total_revenue", 0)),
            ("Expense", category_totals.get("total_expenses", 0)),
        ]

        grand_balance = sum(abs(v) for _, v in type_mapping)
        if grand_balance <= 0:
            return elements

        # Use population_profile section_density for account counts
        pop_profile = self.audit_result.get("population_profile", {})
        section_density = pop_profile.get("section_density", [])

        density_counts: dict[str, int] = {}
        for sd in section_density:
            label = sd.get("section_label", "")
            count = sd.get("account_count", 0)
            if "Asset" in label:
                density_counts["Asset"] = density_counts.get("Asset", 0) + count
            elif "Liabilit" in label:
                density_counts["Liability"] = density_counts.get("Liability", 0) + count
            elif "Equity" in label:
                density_counts["Equity"] = density_counts.get("Equity", 0) + count
            elif "Revenue" in label:
                density_counts["Revenue"] = density_counts.get("Revenue", 0) + count
            elif "Cost" in label or "Expense" in label or "Other" in label:
                density_counts["Expense"] = density_counts.get("Expense", 0) + count

        # Build rows: percentages relative to sum of absolute category balances
        type_rows: list[tuple[str, int, float, float]] = []
        classified_count = sum(density_counts.values())
        unclassified_count = max(0, row_count - classified_count) if density_counts else 0

        for type_name, balance in type_mapping:
            count = density_counts.get(type_name, 0)
            abs_balance = abs(balance)
            pct = abs_balance / grand_balance * 100
            type_rows.append((type_name, count, abs_balance, pct))

        if unclassified_count > 0:
            type_rows.append(("Other / Unclassified", unclassified_count, 0.0, 0.0))

        # Suppress if no real data
        if not any(r[2] > 0 for r in type_rows):
            return elements

        elements.append(Paragraph("Population Composition", self.styles["SectionHeader"]))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        elements.append(Spacer(1, 4))

        cell_style = self.styles["TableCell"]
        header_style = self.styles["TableHeader"]

        # Fix 2: Renamed column and added footnote for clarity
        table_data = [
            [
                Paragraph("Account Type", header_style),
                Paragraph("Count", header_style),
                Paragraph("Gross Balance", header_style),
                Paragraph("% of Gross Total", header_style),
            ]
        ]

        total_count = 0
        for type_name, count, balance, pct in type_rows:
            total_count += count
            table_data.append(
                [
                    Paragraph(type_name, cell_style),
                    Paragraph(str(count) if count > 0 else "\u2014", cell_style),
                    Paragraph(f"${balance:,.2f}", cell_style),
                    Paragraph(f"{pct:.1f}%", cell_style),
                ]
            )

        table_data.append(
            [
                Paragraph("Total", self.styles["TableHeader"]),
                Paragraph(str(total_count) if total_count > 0 else str(row_count), self.styles["TableHeader"]),
                Paragraph(f"${grand_balance:,.2f}", self.styles["TableHeader"]),
                Paragraph("100.0%", self.styles["TableHeader"]),
            ]
        )

        comp_table = Table(
            table_data,
            colWidths=[1.8 * inch, 0.8 * inch, 2.2 * inch, 1.2 * inch],
            repeatRows=1,
        )
        comp_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -2), 0.25, ClassicalColors.LEDGER_RULE),
                    ("LINEABOVE", (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_600),
                    ("FONTNAME", (0, -1), (-1, -1), "Times-Bold"),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [ClassicalColors.WHITE, ClassicalColors.OATMEAL_PAPER]),
                ]
            )
        )

        elements.append(comp_table)

        # Fix 2: Gross balance footnote — clarify non-additive nature
        gross_footnote = (
            "Gross Balance represents the sum of absolute account-level balances within each type. "
            "This column is not additive to a net trial balance total, as it includes both "
            "debit and credit balances without netting."
        )
        elements.append(Spacer(1, 2))
        elements.append(Paragraph(f"<i>{gross_footnote}</i>", self.styles["BodyText"]))

        # Classification confidence footnote
        col_detection = self.audit_result.get("column_detection", {})
        if col_detection:
            acct_confidence = col_detection.get("account_confidence", 1.0)
            if acct_confidence < 0.9:
                footnote = (
                    f"Account type classification based on {acct_confidence:.0%} column confidence. "
                    f"Unclassified accounts are excluded from type-specific tests."
                )
                elements.append(Spacer(1, 2))
                elements.append(Paragraph(f"<i>{footnote}</i>", self.styles["BodyText"]))

        elements.append(Spacer(1, 6))

        return elements

    def _build_risk_summary(self) -> list:
        """Build the risk summary section with composite risk score."""
        from shared.memo_base import RISK_SCALE_LEGEND, RISK_TIER_DISPLAY
        from shared.tb_diagnostic_constants import compute_tb_risk_score, get_risk_tier

        elements = []

        elements.append(Paragraph("Risk Assessment", self.styles["SectionHeader"]))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        elements.append(Spacer(1, 6))

        risk_summary = self.audit_result.get("risk_summary", {})
        material_count = self.audit_result.get("material_count", 0)
        immaterial_count = self.audit_result.get("immaterial_count", 0)
        total_anomalies = risk_summary.get("total_anomalies", material_count + immaterial_count)
        high_severity = risk_summary.get("high_severity", material_count)
        low_severity = risk_summary.get("low_severity", immaterial_count)

        # Change 3: Composite Risk Score
        abnormal_balances = self.audit_result.get("abnormal_balances", [])
        anomaly_types = risk_summary.get("anomaly_types", {})
        has_suspense = anomaly_types.get("suspense_account", 0) > 0
        has_credit_balance = any(
            ab.get("anomaly_type") in ("abnormal_balance", "natural_balance_violation")
            and ab.get("type", "").lower() == "asset"
            for ab in abnormal_balances
        )

        total_debits = self.audit_result.get("total_debits", 0)
        material_items = [ab for ab in abnormal_balances if ab.get("materiality") == "material"]
        flagged_value = sum(abs(ab.get("amount", 0)) for ab in material_items)
        coverage_pct = flagged_value / total_debits * 100 if total_debits > 0 else 0

        # Sprint 526 Fix 5: Use pre-computed score from API response when available
        # This ensures dashboard and PDF display identical scores
        pre_computed_score = risk_summary.get("risk_score")
        pre_computed_factors = risk_summary.get("risk_factors")
        if pre_computed_score is not None and pre_computed_factors is not None:
            risk_score = pre_computed_score
            risk_factors = [(name, pts) for name, pts in pre_computed_factors]
        else:
            risk_score, risk_factors = compute_tb_risk_score(
                material_count,
                immaterial_count,
                coverage_pct,
                has_suspense,
                has_credit_balance,
                abnormal_balances=abnormal_balances,
            )
        risk_tier = get_risk_tier(risk_score)
        tier_label, _ = RISK_TIER_DISPLAY.get(risk_tier, ("UNKNOWN", ClassicalColors.OBSIDIAN_500))

        # Render risk score block
        score_lines = [
            create_leader_dots("Composite Risk Score", f"{risk_score} / 100"),
            create_leader_dots("Risk Tier", tier_label),
        ]
        for line in score_lines:
            elements.append(Paragraph(line, self.styles["LeaderLine"]))
        elements.append(Paragraph(RISK_SCALE_LEGEND, self.styles["BodyText"]))

        # Risk score decomposition
        if risk_factors:
            elements.append(Spacer(1, 4))
            elements.append(Paragraph("<b>Score Decomposition</b>", self.styles["BodyText"]))
            for factor_name, contribution in risk_factors:
                elements.append(
                    Paragraph(
                        create_leader_dots(f"  {factor_name}", f"+{contribution}"),
                        self.styles["LeaderLine"],
                    )
                )
            # Total line
            elements.append(LedgerRule(color=ClassicalColors.LEDGER_RULE, thickness=0.5))
            elements.append(
                Paragraph(
                    create_leader_dots("  <b>Total (capped at 100)</b>", f"<b>{risk_score}</b>"),
                    self.styles["LeaderLine"],
                )
            )

        elements.append(Spacer(1, 6))

        # Risk metrics table with classical styling
        risk_data = [
            ["Total Findings", "Material Exceptions", "Minor Observations"],
            [str(total_anomalies), str(high_severity), str(low_severity)],
        ]

        risk_table = Table(risk_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
        risk_table.setStyle(
            TableStyle(
                [
                    # Header labels
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Roman"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_500),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    # Values
                    ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
                    ("FONTSIZE", (0, 1), (-1, 1), 24),
                    ("TEXTCOLOR", (0, 1), (0, 1), ClassicalColors.OBSIDIAN_DEEP),
                    ("TEXTCOLOR", (1, 1), (1, 1), ClassicalColors.CLAY),
                    ("TEXTCOLOR", (2, 1), (2, 1), ClassicalColors.OBSIDIAN_500),
                    ("ALIGN", (0, 1), (-1, 1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elements.append(risk_table)
        elements.append(Spacer(1, 6))

        return elements

    def _build_anomaly_details(self) -> list:
        """Build the anomaly details with ledger-style tables."""
        elements = []

        abnormal_balances = self.audit_result.get("abnormal_balances", [])

        if not abnormal_balances:
            elements.append(
                Paragraph("No exceptions identified. The trial balance appears sound.", self.styles["BodyText"])
            )
            return elements

        elements.append(Paragraph("Exception Details", self.styles["SectionHeader"]))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        elements.append(Spacer(1, 4))

        # Separate by materiality
        material = [ab for ab in abnormal_balances if ab.get("materiality") == "material"]
        immaterial = [ab for ab in abnormal_balances if ab.get("materiality") == "immaterial"]

        # Fix 3: Sort findings by absolute amount descending within each tier
        material.sort(key=lambda ab: abs(ab.get("amount", 0)), reverse=True)
        immaterial.sort(key=lambda ab: abs(ab.get("amount", 0)), reverse=True)

        if material:
            elements.append(Paragraph(f"Material Exceptions ({len(material)})", self.styles["SubsectionHeader"]))
            elements.append(self._create_ledger_table(material, is_material=True))
            elements.append(Spacer(1, 10))

        if immaterial:
            elements.append(Paragraph(f"Minor Observations ({len(immaterial)})", self.styles["SubsectionHeader"]))
            elements.append(self._create_ledger_table(immaterial, is_material=False))

        return elements

    def _create_ledger_table(self, anomalies: list, is_material: bool) -> KeepTogether:
        """
        Create a ledger-style table with horizontal rules only.

        Classic accounting ledger aesthetic:
        - No vertical borders (except left margin rule)
        - Horizontal hairlines between rows
        - Right-aligned amounts
        - Sprint 53: Added reference numbers for workpaper cross-referencing
        - Changes 1/4/6: Suggested procedures, benchmarks, cross-references
        - Fix 1: Signed total, Fix 3: Priority ranking, Fix 11: Amount annotations
        """
        from shared.tb_diagnostic_constants import get_concentration_benchmark, get_tb_suggested_procedure

        cell_style = self.styles["TableCell"]
        header_style = self.styles["TableHeader"]

        # Fix 3: Header row with Rank column
        data = [
            [
                Paragraph("Rank", header_style),
                Paragraph("Ref", header_style),
                Paragraph("Account", header_style),
                Paragraph("Nature of Exception", header_style),
                Paragraph("Amount", header_style),
            ]
        ]

        # Determine reference prefix based on materiality
        ref_prefix = "TB-M" if is_material else "TB-I"

        # Data rows (anomalies already sorted by abs(amount) descending in caller)
        total_amount = 0
        has_pattern_based = False
        for idx, ab in enumerate(anomalies, start=1):
            # Sprint 53: Generate reference number (stable identifier, not sort key)
            ref_num = f"{ref_prefix}{idx:03d}"

            account = ab.get("account", "Unknown")
            if ab.get("sheet_name"):
                account = f"{account} ({ab['sheet_name']})"

            acc_type = ab.get("type", "Unknown")

            # Build enriched Nature of Exception cell:
            issue_text = ab.get("issue", "")
            issue_parts = [f"<b>{issue_text}</b>"]
            issue_parts.append(f'<br/><font size="7" color="#616161"><i>{acc_type}</i></font>')

            # Concentration benchmark
            benchmark = get_concentration_benchmark(ab)
            if benchmark:
                issue_parts.append(f'<br/><font size="7" color="#616161"><i>{benchmark}</i></font>')

            # Cross-reference for intercompany findings
            cross_ref = ab.get("cross_reference_note")
            if cross_ref:
                issue_parts.append(f'<br/><font size="7" color="#4A7C59"><i>{cross_ref}</i></font>')

            # Suggested procedure (Fix 9: escalated for material findings)
            procedure = get_tb_suggested_procedure(ab, is_material=is_material)
            issue_parts.append(f'<br/><font size="7"><i>Suggested Procedure: {procedure}</i></font>')

            issue_cell = Paragraph("".join(issue_parts), cell_style)

            amount = ab.get("amount", 0)
            # Fix 1: Sum signed values (not absolute) so total matches manual sum of displayed amounts
            total_amount += amount

            # Fix 11: Annotate pattern-based amounts with per-transaction breakdown
            anomaly_type = ab.get("anomaly_type", "")
            amount_display = f"${amount:,.2f}"
            if anomaly_type == "rounding_anomaly":
                txn_count = ab.get("transaction_count")
                if txn_count and txn_count > 1:
                    per_txn = ab.get("per_transaction_amount")
                    if per_txn is None and amount != 0:
                        per_txn = abs(amount) / txn_count
                    if per_txn is not None:
                        amount_display += (
                            f'<br/><font size="6"><i>({txn_count} transactions \u00d7 ${per_txn:,.2f})</i></font>'
                        )
                    else:
                        amount_display += f'<br/><font size="6"><i>(sum of {txn_count} flagged transactions)</i></font>'
                    has_pattern_based = True

            # Fix 3: Priority rank badge
            rank_label = f"P{idx}"

            data.append(
                [
                    Paragraph(f"<b>{rank_label}</b>", cell_style),
                    Paragraph(ref_num, cell_style),
                    Paragraph(account, cell_style),
                    issue_cell,
                    Paragraph(amount_display, cell_style),
                ]
            )

        # Fix 1: Total row uses signed sum
        data.append(
            [
                Paragraph("", cell_style),
                Paragraph("", cell_style),
                Paragraph("", cell_style),
                Paragraph("TOTAL", self.styles["TableHeader"]),
                Paragraph(f"${total_amount:,.2f}", self.styles["TableHeader"]),
            ]
        )

        # Adjusted column widths: Rank + Ref + Account + Nature + Amount
        table = Table(data, colWidths=[0.5 * inch, 0.6 * inch, 1.3 * inch, 2.6 * inch, 1.0 * inch], repeatRows=1)

        # Build elements list to wrap table + footnotes together
        table_elements = []

        # Ledger styling
        accent_color = ClassicalColors.CLAY if is_material else ClassicalColors.OBSIDIAN_500

        style_commands = [
            # Header row
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            # Data rows - horizontal rules only (ledger style)
            ("LINEBELOW", (0, 1), (-1, -2), 0.25, ClassicalColors.LEDGER_RULE),
            # Total row
            ("LINEABOVE", (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_600),
            ("FONTNAME", (-2, -1), (-1, -1), "Times-Bold"),
            # Left margin accent (double line effect)
            ("LINEBEFORE", (0, 1), (0, -1), 2, accent_color),
            # Right-align amounts
            ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
            # Padding
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (0, -1), 8),
            # Vertical alignment
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            # Alternating row backgrounds (subtle)
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [ClassicalColors.WHITE, ClassicalColors.OATMEAL_PAPER]),
        ]

        table.setStyle(TableStyle(style_commands))
        table_elements.append(table)

        # Fix 1: Signed-balance footnote
        table_elements.append(Spacer(1, 2))
        table_elements.append(
            Paragraph(
                '<i><font size="7">Amounts shown reflect signed balances. '
                "Negative values indicate credit-balance findings. "
                "Amount represents account balance unless otherwise noted.</font></i>",
                self.styles["BodyText"],
            )
        )

        # Fix 11: Pattern-based amount footnote (if any present)
        if has_pattern_based:
            table_elements.append(
                Paragraph(
                    '<i><font size="7">For pattern-based findings (e.g., round-number anomalies), '
                    "the amount shown may represent the sum of flagged transactions rather than "
                    "the account balance.</font></i>",
                    self.styles["BodyText"],
                )
            )

        return KeepTogether(table_elements)

    def _build_workpaper_signoff(self) -> list:
        """
        Build workpaper signoff section with prepared/reviewed fields.

        Sprint 53: Professional workpaper fields for audit documentation.
        Deprecated Sprint 7: gated by self.include_signoff (default False).
        """
        elements = []

        if not self.include_signoff:
            return elements

        # Only include if workpaper fields are provided
        if not self.prepared_by and not self.reviewed_by:
            return elements

        elements.append(Spacer(1, 16))
        elements.append(Paragraph("Workpaper Sign-Off", self.styles["SectionHeader"]))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        elements.append(Spacer(1, 8))

        # Build signoff table
        signoff_data = [["Field", "Name", "Date"]]

        if self.prepared_by:
            signoff_data.append(
                [
                    "Prepared By:",
                    self.prepared_by,
                    self.workpaper_date,
                ]
            )

        if self.reviewed_by:
            signoff_data.append(
                [
                    "Reviewed By:",
                    self.reviewed_by,
                    self.workpaper_date,
                ]
            )

        # Create table
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
        elements.append(table)

        return elements

    def _build_classical_footer(self) -> list:
        """Build the classical document footer, kept together to avoid page split."""
        inner = []

        inner.append(Spacer(1, 12))
        inner.append(
            DoubleRule(width=6.5 * inch, color=ClassicalColors.LEDGER_RULE, thick=0.5, thin=0.25, spaceAfter=8)
        )

        # Pacioli motto (Italian)
        inner.append(Paragraph('"Particularis de Computis et Scripturis"', self.styles["FooterMotto"]))

        inner.append(Spacer(1, 8))

        # Generator info
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        inner.append(
            Paragraph(f"Generated by Paciolus® Diagnostic Intelligence  ·  {timestamp}", self.styles["Footer"])
        )

        # Zero-Storage promise
        inner.append(
            Paragraph(
                "Zero-Storage Architecture: Your financial data was processed in-memory and never stored.",
                self.styles["Footer"],
            )
        )

        return [KeepTogether(inner)]


def generate_financial_statements_pdf(
    statements: Any,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    include_signoff: bool = False,
) -> bytes:
    """
    Generate a PDF with Balance Sheet and Income Statement.

    Sprint 71: Financial Statements PDF using Renaissance Ledger aesthetic.

    Args:
        statements: FinancialStatements dataclass from FinancialStatementBuilder
        prepared_by: Name of preparer (deprecated — ignored unless include_signoff=True)
        reviewed_by: Name of reviewer (deprecated — ignored unless include_signoff=True)
        workpaper_date: Date for workpaper signoff (deprecated — ignored unless include_signoff=True)
        include_signoff: If True, render signoff section (default False since Sprint 7)
    """
    buffer = io.BytesIO()
    styles = create_classical_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=1.0 * inch,
    )

    story = []
    page_counter = [0]

    def draw_fs_decorations(canvas: Any, doc: Any) -> None:
        """Page decorations for financial statements PDF."""
        canvas.saveState()
        page_counter[0] += 1
        page_width, page_height = letter

        # Watermark
        canvas.saveState()
        canvas.setFillColor(ClassicalColors.OATMEAL_400)
        canvas.setFillAlpha(0.04)
        canvas.setFont("Times-Italic", 48)
        canvas.translate(page_width / 2, page_height / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "Particularis de Computis")
        canvas.restoreState()

        # Top gold double rule
        canvas.setStrokeColor(ClassicalColors.GOLD_INSTITUTIONAL)
        canvas.setLineWidth(2)
        canvas.line(0.75 * inch, page_height - 0.5 * inch, page_width - 0.75 * inch, page_height - 0.5 * inch)
        canvas.setLineWidth(0.5)
        canvas.line(0.75 * inch, page_height - 0.55 * inch, page_width - 0.75 * inch, page_height - 0.55 * inch)

        # Bottom rule
        canvas.setStrokeColor(ClassicalColors.LEDGER_RULE)
        canvas.setLineWidth(0.5)
        canvas.line(0.75 * inch, 0.75 * inch, page_width - 0.75 * inch, 0.75 * inch)

        # Page number
        canvas.setFont("Times-Roman", 9)
        canvas.setFillColor(ClassicalColors.OBSIDIAN_500)
        canvas.drawCentredString(page_width / 2, 0.5 * inch, f"— {page_counter[0]} —")

        # Disclaimer
        canvas.setFont("Times-Roman", 7)
        disclaimer = (
            "This output supports professional judgment and internal evaluation. "
            "It does not constitute an audit, review, or attestation engagement."
        )
        canvas.drawCentredString(page_width / 2, 0.35 * inch, disclaimer)
        canvas.restoreState()

    # ── COVER PAGE (diagonal color bands) ──
    # Lazy import to avoid circular dependency (report_chrome imports from pdf_generator)
    from shared.report_chrome import ReportMetadata as FSReportMetadata
    from shared.report_chrome import build_cover_page as fs_build_cover_page
    from shared.report_chrome import find_logo as fs_find_logo

    entity_name = statements.entity_name or "Financial Statements"
    fs_logo_path = fs_find_logo()
    fs_metadata = FSReportMetadata(
        title="FINANCIAL STATEMENTS",
        subtitle=entity_name,
        engagement_period=statements.period_end or "",
    )
    fs_build_cover_page(story, styles, fs_metadata, doc.width, fs_logo_path)

    # ── HEADER ──
    story.append(Paragraph("FINANCIAL STATEMENTS", styles["ClassicalTitle"]))
    story.append(Paragraph("─── ◆ ───", styles["SectionOrnament"]))
    story.append(Paragraph(entity_name, styles["ClassicalSubtitle"]))

    if statements.period_end:
        story.append(Paragraph(f"Period Ending {statements.period_end}", styles["DocumentRef"]))

    ref_number = generate_reference_number()
    classical_date = format_classical_date()
    story.append(Paragraph(f"Prepared {classical_date}  ·  Ref: {ref_number}", styles["DocumentRef"]))
    story.append(DoubleRule(width=6.5 * inch, color=ClassicalColors.GOLD_INSTITUTIONAL, spaceAfter=16))

    # ── BALANCE SHEET ──
    story.append(Paragraph("Balance Sheet", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 8))

    # Check if prior period data is available for comparative columns
    _bs_has_prior = any(item.prior_amount is not None for item in statements.balance_sheet)

    if _bs_has_prior:
        # Build comparative table
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
            prior_str = f"${item.prior_amount:,.2f}" if item.prior_amount is not None else "—"
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
    else:
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

    # ── BALANCE VERIFICATION ──
    story.append(Spacer(1, 12))
    if statements.is_balanced:
        badge_text = "✓  Balanced"
        badge_style = "BalancedStatus"
        badge_border = ClassicalColors.SAGE
    else:
        badge_text = f"⚠   OUT OF BALANCE (${statements.balance_difference:,.2f})"
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

    # ── CROSS-REFERENCE INDEX: Balance Sheet (Sprint 488) ──
    _bs_legend_map = {
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
    # Only show legend entries for lead sheets that have non-zero amounts
    _bs_refs_used = {
        item.lead_sheet_ref for item in statements.balance_sheet if item.lead_sheet_ref and item.amount != 0
    }
    _bs_legend_items = [(ref, *_bs_legend_map[ref]) for ref in sorted(_bs_refs_used) if ref in _bs_legend_map]

    if _bs_legend_items:
        story.append(Spacer(1, 8))
        story.append(LedgerRule(thickness=0.5, spaceBefore=2, spaceAfter=4))
        story.append(Paragraph("Cross-Reference Index", styles["SubsectionHeader"]))
        story.append(Spacer(1, 2))
        for ref, acct_name, report_name in _bs_legend_items:
            legend_text = f"({ref}) {acct_name} — See {report_name}"
            story.append(Paragraph(legend_text, styles["DocumentRef"]))
        story.append(Spacer(1, 4))

    # Section ornament
    story.append(Spacer(1, 8))
    story.append(Paragraph("❧", styles["SectionOrnament"]))
    story.append(Spacer(1, 8))

    # ── INCOME STATEMENT ──
    story.append(Paragraph("Income Statement", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 8))

    _is_has_prior = any(item.prior_amount is not None for item in statements.income_statement)

    if _is_has_prior:
        is_table_data = [["Account", "Current", "Prior", "Change", "% Change"]]
        is_table_styles = [
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
        is_row = 1
        for item in statements.income_statement:
            prior_str = f"${item.prior_amount:,.2f}" if item.prior_amount is not None else "—"
            change_str = ""
            pct_str = ""
            if item.prior_amount is not None:
                change = item.amount - item.prior_amount
                change_str = f"${change:,.2f}"
                # Suppress % Change on subtotals/totals per prompt
                if not item.is_subtotal and not item.is_total and item.prior_amount != 0:
                    pct_change = (change / abs(item.prior_amount)) * 100
                    pct_str = f"{pct_change:+.1f}%"

            ref = f" ({item.lead_sheet_ref})" if item.lead_sheet_ref else ""
            if item.is_total:
                is_table_data.append([f"  {item.label}{ref}", f"${item.amount:,.2f}", prior_str, change_str, pct_str])
                is_table_styles.append(("FONTNAME", (0, is_row), (-1, is_row), "Times-Bold"))
                is_table_styles.append(("LINEABOVE", (0, is_row), (-1, is_row), 0.5, ClassicalColors.OBSIDIAN_600))
                is_table_styles.append(("LINEBELOW", (0, is_row), (-1, is_row), 1, ClassicalColors.OBSIDIAN_600))
            elif item.is_subtotal:
                is_table_data.append([f"  {item.label}", f"${item.amount:,.2f}", prior_str, change_str, ""])
                is_table_styles.append(("FONTNAME", (0, is_row), (-1, is_row), "Times-Bold"))
                is_table_styles.append(("LINEBELOW", (0, is_row), (-1, is_row), 0.25, ClassicalColors.LEDGER_RULE))
            else:
                is_table_data.append([f"  {item.label}{ref}", f"${item.amount:,.2f}", prior_str, change_str, pct_str])
            is_row += 1

        is_table = Table(is_table_data, colWidths=[2.2 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 1.0 * inch])
        is_table.setStyle(TableStyle(is_table_styles))
        story.append(is_table)
    else:
        for item in statements.income_statement:
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
            else:
                ref = f" ({item.lead_sheet_ref})" if item.lead_sheet_ref else ""
                line = create_leader_dots(f"  {item.label}{ref}", f"${item.amount:,.2f}")
                story.append(Paragraph(line, styles["LeaderLine"]))

    # ── CROSS-REFERENCE INDEX: Income Statement (Sprint 488) ──
    _is_legend_map = {
        "L": ("Revenue", "Revenue Recognition Testing Memo"),
        "M": ("Cost of Goods Sold", "Trial Balance Diagnostic"),
        "N": ("Operating Expenses", "Expense Category Analysis"),
        "O": ("Other Income / (Expense), Net", "Trial Balance Diagnostic"),
    }
    _is_refs_used = {
        item.lead_sheet_ref for item in statements.income_statement if item.lead_sheet_ref and item.amount != 0
    }
    _is_legend_items = [(ref, *_is_legend_map[ref]) for ref in sorted(_is_refs_used) if ref in _is_legend_map]

    if _is_legend_items:
        story.append(Spacer(1, 8))
        story.append(LedgerRule(thickness=0.5, spaceBefore=2, spaceAfter=4))
        story.append(Paragraph("Cross-Reference Index", styles["SubsectionHeader"]))
        story.append(Spacer(1, 2))
        for ref, acct_name, report_name in _is_legend_items:
            legend_text = f"({ref}) {acct_name} — See {report_name}"
            story.append(Paragraph(legend_text, styles["DocumentRef"]))
        story.append(Spacer(1, 4))

    # ── CASH FLOW STATEMENT (Sprint 84) ──
    if statements.cash_flow_statement is not None:
        cf = statements.cash_flow_statement
        story.append(Spacer(1, 8))
        story.append(Paragraph("❧", styles["SectionOrnament"]))
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
                recon_text = "✓  Reconciled"
                recon_style = "BalancedStatus"
                recon_border = ClassicalColors.SAGE
            else:
                recon_text = f"⚠   UNRECONCILED (${cf.reconciliation_difference:,.2f})"
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

        # Notes
        if cf.notes:
            story.append(Spacer(1, 8))
            for note in cf.notes:
                story.append(Paragraph(f"<i>Note: {note}</i>", styles["DocumentRef"]))

    # ── KEY FINANCIAL RATIOS (CONTENT-04) ──
    _has_ratios = False
    if statements.total_revenue and statements.total_revenue != 0:
        _has_ratios = True
        story.append(Spacer(1, 8))
        story.append(Paragraph("❧", styles["SectionOrnament"]))
        story.append(Spacer(1, 8))

        story.append(Paragraph("Key Financial Ratios", styles["SectionHeader"]))
        story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        story.append(Spacer(1, 8))

        # Extract balance sheet components for ratio computation
        _current_assets = 0.0
        _current_liabilities = 0.0
        _total_cash = 0.0
        _total_ar = 0.0
        _found_ca = False
        _found_cl = False
        for item in statements.balance_sheet:
            if item.label == "Total Current Assets" and item.is_subtotal:
                _current_assets = item.amount
                _found_ca = True
            elif item.label == "Total Current Liabilities" and item.is_subtotal:
                _current_liabilities = item.amount
                _found_cl = True
            elif item.lead_sheet_ref == "A" and item.indent_level == 1:
                _total_cash = item.amount
            elif item.lead_sheet_ref == "B" and item.indent_level == 1:
                _total_ar = item.amount

        # Build ratio list in specified order (12 ratios)
        # Each entry: (label, current_value_str, prior_value_str_or_None)
        ratio_lines: list[tuple[str, str, Optional[str]]] = []
        _has_prior = statements.has_prior_period

        # 1. Gross Profit Margin
        if statements.gross_profit is not None:
            gp_margin = statements.gross_profit / statements.total_revenue
            prior_gp_margin_str = None
            if _has_prior and statements.prior_total_revenue and statements.prior_total_revenue != 0:
                prior_gp_margin_str = f"{statements.prior_gross_profit / statements.prior_total_revenue:.1%}"
            ratio_lines.append(("Gross Profit Margin", f"{gp_margin:.1%}", prior_gp_margin_str))

        # 2. Operating Margin
        if statements.operating_income is not None:
            op_margin = statements.operating_income / statements.total_revenue
            prior_op_str = None
            if _has_prior and statements.prior_total_revenue and statements.prior_total_revenue != 0:
                prior_op_str = f"{statements.prior_operating_income / statements.prior_total_revenue:.1%}"
            ratio_lines.append(("Operating Margin", f"{op_margin:.1%}", prior_op_str))

        # 3. Net Margin
        if statements.net_income is not None:
            net_margin = statements.net_income / statements.total_revenue
            prior_nm_str = None
            if _has_prior and statements.prior_total_revenue and statements.prior_total_revenue != 0:
                prior_nm_str = f"{statements.prior_net_income / statements.prior_total_revenue:.1%}"
            ratio_lines.append(("Net Margin", f"{net_margin:.1%}", prior_nm_str))

        # 4. EBITDA
        _depreciation = statements.depreciation_amount
        if statements.operating_income is not None:
            ebitda = statements.operating_income + _depreciation
            ratio_lines.append(("EBITDA", f"${ebitda:,.2f}", None))

            # 5. EBITDA Margin
            ebitda_margin = ebitda / statements.total_revenue
            ratio_lines.append(("EBITDA Margin", f"{ebitda_margin:.1%}", None))

        # 6. Debt-to-Equity Ratio
        if statements.total_equity and statements.total_equity != 0:
            de_ratio = statements.total_liabilities / statements.total_equity
            prior_de_str = None
            if _has_prior and statements.prior_total_equity and statements.prior_total_equity != 0:
                prior_de_str = f"{statements.prior_total_liabilities / statements.prior_total_equity:.2f}x"
            ratio_lines.append(("Debt-to-Equity Ratio", f"{de_ratio:.2f}x", prior_de_str))

        # 7. Interest Coverage
        _interest_exp = statements.interest_expense
        if statements.operating_income is not None and _interest_exp and _interest_exp != 0:
            interest_coverage = statements.operating_income / _interest_exp
            ratio_lines.append(("Interest Coverage", f"{interest_coverage:.1f}x", None))

        # 8. Asset Turnover
        if statements.total_assets and statements.total_assets != 0:
            asset_turnover = statements.total_revenue / statements.total_assets
            prior_at_str = None
            if _has_prior and statements.prior_total_assets and statements.prior_total_assets != 0:
                prior_at_str = f"{statements.prior_total_revenue / statements.prior_total_assets:.2f}x"
            ratio_lines.append(("Asset Turnover", f"{asset_turnover:.2f}x", prior_at_str))

        # 9. Current Ratio
        if _found_ca and _found_cl:
            if _current_liabilities != 0:
                current_ratio = _current_assets / _current_liabilities
                ratio_lines.append(("Current Ratio", f"{current_ratio:.2f}x", None))

            # 10. Quick Ratio
            if _current_liabilities != 0:
                quick_ratio = (_total_cash + _total_ar) / _current_liabilities
                ratio_lines.append(("Quick Ratio", f"{quick_ratio:.2f}x", None))

            # 11. Working Capital
            working_capital = _current_assets - _current_liabilities
            ratio_lines.append(("Working Capital", f"${working_capital:,.2f}", None))
        else:
            ratio_lines.append(("Current Ratio", "Requires current/non-current classification", None))

        # 12. DSO
        if _total_ar and statements.total_revenue != 0:
            dso = (_total_ar / statements.total_revenue) * 365
            ratio_lines.append(("Days Sales Outstanding (DSO)", f"{dso:.0f} days", None))

        # Render ratio table — with prior year column if available
        if _has_prior and any(r[2] is not None for r in ratio_lines):
            # Table format with prior year and change indicator
            ratio_data = [["Metric", "Current", "Prior", ""]]
            for label, current_val, prior_val in ratio_lines:
                change_indicator = ""
                if prior_val is not None:
                    # Parse numeric values to compute change direction
                    try:
                        c_num = float(
                            current_val.replace("%", "").replace("x", "").replace("$", "").replace(",", "").strip()
                        )
                        p_num = float(
                            prior_val.replace("%", "").replace("x", "").replace("$", "").replace(",", "").strip()
                        )
                        if p_num != 0:
                            pct_change = abs((c_num - p_num) / p_num) * 100
                            if pct_change > 10:
                                change_indicator = "\u25b2" if c_num > p_num else "\u25bc"
                    except (ValueError, ZeroDivisionError):
                        pass
                ratio_data.append([label, current_val, prior_val or "—", change_indicator])

            ratio_table = Table(ratio_data, colWidths=[2.8 * inch, 1.4 * inch, 1.4 * inch, 0.4 * inch])
            ratio_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                        ("FONTNAME", (0, 1), (0, -1), "Times-Roman"),
                        ("FONTNAME", (1, 1), (-1, -1), "Courier"),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                        ("TEXTCOLOR", (0, 1), (-1, -1), ClassicalColors.OBSIDIAN_600),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LINEBELOW", (0, -1), (-1, -1), 0.5, ClassicalColors.LEDGER_RULE),
                    ]
                )
            )
            story.append(ratio_table)
        else:
            for label, value, _ in ratio_lines:
                line = create_leader_dots(f"      {label}", value)
                story.append(Paragraph(line, styles["LeaderLine"]))

        story.append(Spacer(1, 4))

    # ── QUALITY OF EARNINGS (CONTENT-05) ──
    if statements.cash_flow_statement is not None and statements.net_income is not None and statements.net_income != 0:
        operating_cf = statements.cash_flow_statement.operating.subtotal

        if not _has_ratios:
            story.append(Spacer(1, 8))
            story.append(Paragraph("❧", styles["SectionOrnament"]))
            story.append(Spacer(1, 8))

        story.append(Paragraph("Quality of Earnings", styles["SubsectionHeader"]))
        story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=0.5))
        story.append(Spacer(1, 4))

        ocf_ni_ratio = operating_cf / statements.net_income

        # Interpretation
        if ocf_ni_ratio > 1.0:
            interpretation = (
                f"The OCF/NI ratio of {ocf_ni_ratio:.2f}x indicates that cash earnings exceed reported "
                f"net income — strong earnings quality. Operating cash flow "
                f"(${operating_cf:,.2f}) exceeds net income (${statements.net_income:,.2f}), "
                f"suggesting conservative accrual practices and reliable cash conversion."
            )
        elif ocf_ni_ratio >= 0.8:
            interpretation = (
                f"The OCF/NI ratio of {ocf_ni_ratio:.2f}x indicates acceptable earnings quality. "
                f"Operating cash flow (${operating_cf:,.2f}) is reasonably aligned with "
                f"net income (${statements.net_income:,.2f})."
            )
        else:
            interpretation = (
                f"The OCF/NI ratio of {ocf_ni_ratio:.2f}x indicates that net income "
                f"(${statements.net_income:,.2f}) may not be fully supported by operating cash flows "
                f"(${operating_cf:,.2f}). This warrants investigation of accrual quality, "
                f"non-cash revenue recognition, or working capital management practices."
            )

        ocf_line = create_leader_dots("      Cash Conversion Ratio (OCF / Net Income)", f"{ocf_ni_ratio:.2f}x")
        story.append(Paragraph(ocf_line, styles["LeaderLine"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(interpretation, styles["DocumentRef"]))
        story.append(Spacer(1, 4))

        # Benchmark context (Sprint 488)
        benchmark_text = (
            "A Cash Conversion Ratio consistently above 1.0x over multiple periods is generally considered "
            "a positive indicator of earnings quality. Ratios below 0.8x may indicate aggressive accrual "
            "accounting and warrant further analytical procedures."
        )
        story.append(Paragraph(f"<i>{benchmark_text}</i>", styles["DocumentRef"]))

        # Prior period Cash Conversion Ratio if available
        if statements.has_prior_period and statements.prior_net_income and statements.prior_net_income != 0:
            if statements.cash_flow_statement.has_prior_period:
                # Compute prior OCF from prior period data if available
                # Prior OCF isn't directly available, so note that
                pass
        story.append(Spacer(1, 8))

    # ── NOTES TO FINANCIAL STATEMENTS (Sprint 488) ──
    story.append(Spacer(1, 8))
    story.append(Paragraph("❧", styles["SectionOrnament"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Notes to Financial Statements", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 4))

    # Disclaimer
    notes_disclaimer = (
        "<i>The following notes are structural placeholders generated by Paciolus. "
        "Note content must be completed by management or the engagement team. "
        "Paciolus does not populate note disclosures.</i>"
    )
    story.append(Paragraph(notes_disclaimer, styles["DocumentRef"]))
    story.append(Spacer(1, 8))

    _footnote_stubs = [
        (
            "Note 1 — Basis of Presentation",
            "To be completed by management. Describe the basis of accounting, reporting period, "
            "and any significant departures from the applicable financial reporting framework.",
        ),
        (
            "Note 2 — Significant Accounting Policies",
            "Revenue Recognition: [Describe policy per ASC 606]\n"
            "Inventory Valuation: [Describe method — FIFO, LIFO, weighted average]\n"
            "Depreciation Method: [Describe method and useful life ranges]\n"
            "Income Taxes: [Describe tax status — LLC pass-through or corporate]",
        ),
        (
            "Note 3 — Long-Term Debt",
            "Describe terms, interest rate, maturity date, and collateral for outstanding "
            "long-term debt balances and current portions.",
        ),
        (
            "Note 4 — Related Party Transactions",
            "Disclose any transactions with related parties during the period, including "
            "intercompany receivable/payable balances identified in the trial balance.",
        ),
        (
            "Note 5 — Subsequent Events",
            "Disclose any material events occurring after the period end through the "
            "date these statements were prepared.",
        ),
    ]

    for note_title, note_body in _footnote_stubs:
        story.append(Paragraph(f"<b>{note_title}</b>", styles["DocumentRef"]))
        story.append(Spacer(1, 2))
        # Render placeholder text in italics
        for line in note_body.split("\n"):
            story.append(Paragraph(f"<i>{line.strip()}</i>", styles["DocumentRef"]))
        story.append(Spacer(1, 8))

    # ── ACCOUNT MAPPING TRACE (Sprint 284) ──
    if statements.mapping_trace:
        story.append(Spacer(1, 8))
        story.append(Paragraph("❧", styles["SectionOrnament"]))
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
                tie_text = "✓ Tied"
                tie_color = ClassicalColors.SAGE
            else:
                tie_text = f"⚠ Difference: ${entry.tie_difference:,.2f}"
                tie_color = ClassicalColors.CLAY

            story.append(Paragraph(f'<font color="{tie_color.hexval()}">{tie_text}</font>', styles["DocumentRef"]))
            story.append(Spacer(1, 6))

        # Summary badge
        story.append(LedgerRule(thickness=0.5, spaceBefore=4, spaceAfter=4))
        if tied_count == total_count:
            summary_text = f"✓   All {total_count} lines tied"
            summary_style = "BalancedStatus"
            summary_border = ClassicalColors.SAGE
        else:
            untied = total_count - tied_count
            summary_text = f"⚠   {untied} of {total_count} lines with tie-out differences"
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

    # ── WORKPAPER SIGNOFF ──
    if include_signoff and (prepared_by or reviewed_by):
        story.append(Spacer(1, 8))
        story.append(Paragraph("❧", styles["SectionOrnament"]))
        story.append(Spacer(1, 8))

        story.append(Paragraph("Workpaper Sign-Off", styles["SectionHeader"]))
        story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        story.append(Spacer(1, 8))

        wp_date = workpaper_date or datetime.now().strftime("%Y-%m-%d")
        signoff_data = [["Field", "Name", "Date"]]
        if prepared_by:
            signoff_data.append(["Prepared By:", prepared_by, wp_date])
        if reviewed_by:
            signoff_data.append(["Reviewed By:", reviewed_by, wp_date])

        signoff_table = Table(signoff_data, colWidths=[1.5 * inch, 3.5 * inch, 1.5 * inch])
        signoff_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 1), (-1, -1), ClassicalColors.OBSIDIAN_600),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, -1), (-1, -1), 0.5, ClassicalColors.LEDGER_RULE),
                ]
            )
        )
        story.append(signoff_table)

    # ── FOOTER ──
    story.append(Spacer(1, 24))
    story.append(DoubleRule(width=6.5 * inch, color=ClassicalColors.LEDGER_RULE, thick=0.5, thin=0.25, spaceAfter=8))
    story.append(Paragraph('"Particularis de Computis et Scripturis"', styles["FooterMotto"]))
    story.append(Spacer(1, 8))
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"Generated by Paciolus® Financial Statement Builder  ·  {timestamp}", styles["Footer"]))
    story.append(
        Paragraph(
            "Zero-Storage Architecture: Your financial data was processed in-memory and never stored.", styles["Footer"]
        )
    )

    doc.build(story, onFirstPage=draw_fs_decorations, onLaterPages=draw_fs_decorations)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation(
        "financial_statements_pdf_complete", f"Financial statements PDF generated: {len(pdf_bytes)} bytes"
    )

    return pdf_bytes


def generate_audit_report(
    audit_result: dict[str, Any],
    filename: str = "diagnostic",
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    include_signoff: bool = False,
) -> bytes:
    """
    Generate a PDF diagnostic report from audit results.

    Sprint 53: Added workpaper fields for professional documentation.
    Sprint 7: Signoff deprecated — gated by include_signoff (default False).

    Args:
        audit_result: The audit result dictionary
        filename: Base filename for the report
        prepared_by: Name of preparer (deprecated — ignored unless include_signoff=True)
        reviewed_by: Name of reviewer (deprecated — ignored unless include_signoff=True)
        workpaper_date: Date for workpaper signoff (deprecated — ignored unless include_signoff=True)
        include_signoff: If True, render signoff section (default False since Sprint 7)
    """
    generator = PaciolusReportGenerator(
        audit_result,
        filename,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        include_signoff=include_signoff,
    )
    return generator.generate()
