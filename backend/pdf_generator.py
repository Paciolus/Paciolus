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
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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

    # Section header - Title case, bold serif
    _add_or_replace_style(
        styles,
        ParagraphStyle(
            name="SectionHeader",
            fontName="Times-Bold",
            fontSize=12,
            textColor=ClassicalColors.OBSIDIAN_DEEP,
            spaceBefore=24,
            spaceAfter=8,
            leading=14,
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
        )
        build_cover_page(story, self.styles, metadata, doc.width, self.logo_path)

        # Build document sections
        story.extend(self._build_executive_summary())
        story.extend(self._build_section_ornament())
        story.extend(self._build_risk_summary())
        story.extend(self._build_section_ornament())
        story.extend(self._build_anomaly_details())
        story.extend(self._build_section_ornament())
        story.extend(self._build_workpaper_signoff())  # Sprint 53
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
            Spacer(1, 8),
            Paragraph("❧", self.styles["SectionOrnament"]),
            Spacer(1, 8),
        ]

    def _build_executive_summary(self) -> list:
        """Build the executive summary with leader dots and status badge."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles["SectionHeader"]))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))

        # Status Badge (classical seal style)
        is_balanced = self.audit_result.get("balanced", False)

        if is_balanced:
            status_text = "✓  Balanced"
            badge_border = ClassicalColors.SAGE
            status_style = "BalancedStatus"
        else:
            status_text = "⚠  Out of Balance"
            badge_border = ClassicalColors.CLAY
            status_style = "UnbalancedStatus"

        # Create status badge as a table for border effect
        badge_data = [[Paragraph(status_text, self.styles[status_style])]]
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

        elements.append(Spacer(1, 12))
        elements.append(badge_table)
        elements.append(Spacer(1, 16))

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

        return elements

    def _build_risk_summary(self) -> list:
        """Build the risk summary section."""
        elements = []

        elements.append(Paragraph("Risk Assessment", self.styles["SectionHeader"]))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        elements.append(Spacer(1, 12))

        risk_summary = self.audit_result.get("risk_summary", {})
        material_count = self.audit_result.get("material_count", 0)
        immaterial_count = self.audit_result.get("immaterial_count", 0)
        total_anomalies = risk_summary.get("total_anomalies", material_count + immaterial_count)
        high_severity = risk_summary.get("high_severity", material_count)
        low_severity = risk_summary.get("low_severity", immaterial_count)

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
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )

        elements.append(risk_table)
        elements.append(Spacer(1, 12))

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
        elements.append(Spacer(1, 8))

        # Separate by materiality
        material = [ab for ab in abnormal_balances if ab.get("materiality") == "material"]
        immaterial = [ab for ab in abnormal_balances if ab.get("materiality") == "immaterial"]

        if material:
            elements.append(Paragraph(f"Material Exceptions ({len(material)})", self.styles["SubsectionHeader"]))
            elements.append(self._create_ledger_table(material, is_material=True))
            elements.append(Spacer(1, 16))

        if immaterial:
            elements.append(Paragraph(f"Minor Observations ({len(immaterial)})", self.styles["SubsectionHeader"]))
            elements.append(self._create_ledger_table(immaterial, is_material=False))

        return elements

    def _create_ledger_table(self, anomalies: list, is_material: bool) -> Table:
        """
        Create a ledger-style table with horizontal rules only.

        Classic accounting ledger aesthetic:
        - No vertical borders (except left margin rule)
        - Horizontal hairlines between rows
        - Right-aligned amounts
        - Sprint 53: Added reference numbers for workpaper cross-referencing
        """
        cell_style = self.styles["TableCell"]
        header_style = self.styles["TableHeader"]

        # Header row - Sprint 53: Added Ref column
        data = [
            [
                Paragraph("Ref", header_style),
                Paragraph("Account", header_style),
                Paragraph("Classification", header_style),
                Paragraph("Nature of Exception", header_style),
                Paragraph("Amount", header_style),
            ]
        ]

        # Determine reference prefix based on materiality
        ref_prefix = "TB-M" if is_material else "TB-I"

        # Data rows
        total_amount = 0
        for idx, ab in enumerate(anomalies, start=1):
            # Sprint 53: Generate reference number
            ref_num = f"{ref_prefix}{idx:03d}"

            account = ab.get("account", "Unknown")

            if ab.get("sheet_name"):
                account = f"{account} ({ab['sheet_name']})"

            acc_type = ab.get("type", "Unknown")
            issue = Paragraph(ab.get("issue", ""), cell_style)
            amount = ab.get("amount", 0)
            total_amount += abs(amount)

            data.append(
                [
                    Paragraph(ref_num, cell_style),
                    Paragraph(account, cell_style),
                    Paragraph(acc_type, cell_style),
                    issue,
                    Paragraph(f"${amount:,.2f}", cell_style),
                ]
            )

        # Total row
        data.append(
            [
                Paragraph("", cell_style),
                Paragraph("", cell_style),
                Paragraph("", cell_style),
                Paragraph("TOTAL", self.styles["TableHeader"]),
                Paragraph(f"${total_amount:,.2f}", self.styles["TableHeader"]),
            ]
        )

        # Sprint 53: Adjusted column widths to accommodate Ref column
        table = Table(data, colWidths=[0.7 * inch, 1.5 * inch, 1.0 * inch, 2.3 * inch, 1 * inch], repeatRows=1)

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
        return table

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
        """Build the classical document footer."""
        elements = []

        elements.append(Spacer(1, 24))
        elements.append(
            DoubleRule(width=6.5 * inch, color=ClassicalColors.LEDGER_RULE, thick=0.5, thin=0.25, spaceAfter=8)
        )

        # Pacioli motto (Italian)
        elements.append(Paragraph('"Particularis de Computis et Scripturis"', self.styles["FooterMotto"]))

        elements.append(Spacer(1, 8))

        # Generator info
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        elements.append(
            Paragraph(f"Generated by Paciolus® Diagnostic Intelligence  ·  {timestamp}", self.styles["Footer"])
        )

        # Zero-Storage promise
        elements.append(
            Paragraph(
                "Zero-Storage Architecture: Your financial data was processed in-memory and never stored.",
                self.styles["Footer"],
            )
        )

        return elements


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

    for item in statements.balance_sheet:
        if item.is_total:
            # Double rule before total
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
            # Section header
            story.append(Spacer(1, 6))
            story.append(Paragraph(item.label, styles["SubsectionHeader"]))
        else:
            # Regular line item with lead sheet ref
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

    # Section ornament
    story.append(Spacer(1, 8))
    story.append(Paragraph("❧", styles["SectionOrnament"]))
    story.append(Spacer(1, 8))

    # ── INCOME STATEMENT ──
    story.append(Paragraph("Income Statement", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 8))

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
