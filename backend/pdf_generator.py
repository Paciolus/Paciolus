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
from pathlib import Path
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Flowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from security_utils import log_secure_operation


class ClassicalColors:
    """
    Classical color palette for Renaissance Ledger aesthetic.

    Extends Oat & Obsidian with institutional warmth.
    """
    # Core Obsidian (deep blacks for authority)
    OBSIDIAN_DEEP = colors.HexColor('#1A1A1A')  # Primary text
    OBSIDIAN = colors.HexColor('#212121')
    OBSIDIAN_700 = colors.HexColor('#303030')
    OBSIDIAN_600 = colors.HexColor('#424242')
    OBSIDIAN_500 = colors.HexColor('#616161')

    # Warm Oatmeal (paper and accents)
    OATMEAL_PAPER = colors.HexColor('#F7F5F0')  # Warm paper background
    OATMEAL = colors.HexColor('#EBE9E4')
    OATMEAL_300 = colors.HexColor('#DDD9D1')
    OATMEAL_400 = colors.HexColor('#C9C3B8')
    OATMEAL_500 = colors.HexColor('#B5AD9F')

    # Ledger elements
    LEDGER_RULE = colors.HexColor('#D4CFC5')  # Subtle horizontal rules
    LEDGER_DOT = colors.HexColor('#C9C3B8')   # Leader dots

    # Semantic colors
    CLAY = colors.HexColor('#BC4749')      # Errors, material risks
    CLAY_400 = colors.HexColor('#D16C6E')
    SAGE = colors.HexColor('#4A7C59')      # Success, balanced
    SAGE_400 = colors.HexColor('#6FA882')

    # Institutional accent
    GOLD_INSTITUTIONAL = colors.HexColor('#B8934C')  # Premium borders
    GOLD_LIGHT = colors.HexColor('#D4B87A')

    # Utilities
    WHITE = colors.white


def _add_or_replace_style(styles, style: ParagraphStyle) -> None:
    """Add a style to the stylesheet, replacing if it already exists."""
    if style.name in [s.name for s in styles.byName.values()]:
        existing = styles[style.name]
        for attr in ['fontName', 'fontSize', 'textColor', 'alignment',
                     'spaceBefore', 'spaceAfter', 'leading', 'leftIndent',
                     'rightIndent', 'firstLineIndent', 'bulletIndent']:
            if hasattr(style, attr) and getattr(style, attr) is not None:
                setattr(existing, attr, getattr(style, attr))
    else:
        styles.add(style)


def create_classical_styles() -> dict:
    """
    Create Renaissance Ledger styled paragraph styles.

    Typography hierarchy:
    - Display: Times-Bold 28pt (titles)
    - Section: Times-Bold 14pt with small caps effect
    - Body: Times-Roman 10pt
    - Financial: Courier for tabular figures
    """
    styles = getSampleStyleSheet()

    # ═══════════════════════════════════════════════════════════════
    # TITLE STYLES
    # ═══════════════════════════════════════════════════════════════

    # Main document title - Classical serif, commanding presence
    _add_or_replace_style(styles, ParagraphStyle(
        name='ClassicalTitle',
        fontName='Times-Bold',
        fontSize=28,
        textColor=ClassicalColors.OBSIDIAN_DEEP,
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=32,
    ))

    # Subtitle - Lighter weight, institutional
    _add_or_replace_style(styles, ParagraphStyle(
        name='ClassicalSubtitle',
        fontName='Times-Roman',
        fontSize=12,
        textColor=ClassicalColors.OBSIDIAN_500,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))

    # Document reference line (date, ref number)
    _add_or_replace_style(styles, ParagraphStyle(
        name='DocumentRef',
        fontName='Times-Italic',
        fontSize=9,
        textColor=ClassicalColors.OBSIDIAN_500,
        alignment=TA_CENTER,
        spaceAfter=20,
    ))

    # ═══════════════════════════════════════════════════════════════
    # SECTION HEADERS
    # ═══════════════════════════════════════════════════════════════

    # Section header - Small caps effect via letterspacing
    _add_or_replace_style(styles, ParagraphStyle(
        name='SectionHeader',
        fontName='Times-Bold',
        fontSize=12,
        textColor=ClassicalColors.OBSIDIAN_DEEP,
        spaceBefore=24,
        spaceAfter=8,
        leading=14,
    ))

    # Subsection header
    _add_or_replace_style(styles, ParagraphStyle(
        name='SubsectionHeader',
        fontName='Times-Bold',
        fontSize=10,
        textColor=ClassicalColors.OBSIDIAN_600,
        spaceBefore=16,
        spaceAfter=6,
    ))

    # ═══════════════════════════════════════════════════════════════
    # BODY TEXT
    # ═══════════════════════════════════════════════════════════════

    _add_or_replace_style(styles, ParagraphStyle(
        name='BodyText',
        fontName='Times-Roman',
        fontSize=10,
        textColor=ClassicalColors.OBSIDIAN_600,
        leading=14,
        spaceAfter=8,
    ))

    # Leader dot line style (for financial summaries)
    _add_or_replace_style(styles, ParagraphStyle(
        name='LeaderLine',
        fontName='Courier',
        fontSize=10,
        textColor=ClassicalColors.OBSIDIAN_DEEP,
        leading=16,
        spaceAfter=2,
    ))

    # ═══════════════════════════════════════════════════════════════
    # STATUS STYLES
    # ═══════════════════════════════════════════════════════════════

    # Balanced status - Classical seal effect
    _add_or_replace_style(styles, ParagraphStyle(
        name='BalancedStatus',
        fontName='Times-Bold',
        fontSize=14,
        textColor=ClassicalColors.SAGE,
        alignment=TA_CENTER,
    ))

    # Unbalanced status
    _add_or_replace_style(styles, ParagraphStyle(
        name='UnbalancedStatus',
        fontName='Times-Bold',
        fontSize=14,
        textColor=ClassicalColors.CLAY,
        alignment=TA_CENTER,
    ))

    # ═══════════════════════════════════════════════════════════════
    # TABLE STYLES
    # ═══════════════════════════════════════════════════════════════

    _add_or_replace_style(styles, ParagraphStyle(
        name='TableCell',
        fontName='Times-Roman',
        fontSize=9,
        textColor=ClassicalColors.OBSIDIAN_600,
        leading=11,
    ))

    _add_or_replace_style(styles, ParagraphStyle(
        name='TableHeader',
        fontName='Times-Bold',
        fontSize=9,
        textColor=ClassicalColors.OBSIDIAN_DEEP,
    ))

    # ═══════════════════════════════════════════════════════════════
    # FOOTER STYLES
    # ═══════════════════════════════════════════════════════════════

    _add_or_replace_style(styles, ParagraphStyle(
        name='Footer',
        fontName='Times-Roman',
        fontSize=8,
        textColor=ClassicalColors.OBSIDIAN_500,
        alignment=TA_CENTER,
    ))

    _add_or_replace_style(styles, ParagraphStyle(
        name='FooterMotto',
        fontName='Times-Italic',
        fontSize=8,
        textColor=ClassicalColors.GOLD_INSTITUTIONAL,
        alignment=TA_CENTER,
    ))

    _add_or_replace_style(styles, ParagraphStyle(
        name='LegalDisclaimer',
        fontName='Times-Roman',
        fontSize=7,
        textColor=ClassicalColors.OBSIDIAN_500,
        alignment=TA_CENTER,
        leading=9,
    ))

    # Section ornament (centered)
    _add_or_replace_style(styles, ParagraphStyle(
        name='SectionOrnament',
        fontName='Times-Roman',
        fontSize=12,
        textColor=ClassicalColors.SAGE,
        alignment=TA_CENTER,
        spaceBefore=12,
        spaceAfter=12,
    ))

    return styles


class DoubleRule(Flowable):
    """
    A double-rule flowable for classical document borders.

    Creates the signature "Goldman Sachs" style header rule:
    thick line + gap + thin line
    """

    def __init__(self, width, color=ClassicalColors.GOLD_INSTITUTIONAL,
                 thick=2, thin=0.5, gap=2, spaceAfter=12):
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

    def __init__(self, width=None, thickness=0.5, color=ClassicalColors.LEDGER_RULE,
                 spaceBefore=8, spaceAfter=8):
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
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

    return dt.strftime(f'{day}{suffix} %B %Y')


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

    dots = '.' * dots_needed
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
    ):
        self.audit_result = audit_result
        self.filename = filename
        self.styles = create_classical_styles()
        self.buffer = io.BytesIO()
        self.logo_path = self._find_logo()
        self.reference_number = generate_reference_number()
        self.page_count = 0
        # Sprint 53: Workpaper fields
        self.prepared_by = prepared_by
        self.reviewed_by = reviewed_by
        self.workpaper_date = workpaper_date or datetime.now().strftime("%Y-%m-%d")

        log_secure_operation(
            "pdf_generator_init",
            f"Initializing Classical PDF generator for: {filename}"
        )

    def _find_logo(self) -> Optional[str]:
        """Find the Paciolus logo file."""
        possible_paths = [
            Path(__file__).parent.parent / "frontend" / "public" / "PaciolusLogo_LightBG.png",
            Path(__file__).parent.parent / "PaciolusLogo_LightBG.png",
            Path(__file__).parent / "assets" / "PaciolusLogo_LightBG.png",
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        log_secure_operation("pdf_logo_not_found", "Logo file not found")
        return None

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

        # Build document sections
        story.extend(self._build_classical_header())
        story.extend(self._build_executive_summary())
        story.extend(self._build_section_ornament())
        story.extend(self._build_risk_summary())
        story.extend(self._build_section_ornament())
        story.extend(self._build_anomaly_details())
        story.extend(self._build_section_ornament())
        story.extend(self._build_workpaper_signoff())  # Sprint 53
        story.extend(self._build_classical_footer())

        # Build with page decorations
        doc.build(
            story,
            onFirstPage=self._draw_page_decorations,
            onLaterPages=self._draw_page_decorations
        )

        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()

        log_secure_operation(
            "pdf_generate_complete",
            f"Classical PDF generated: {len(pdf_bytes)} bytes"
        )

        return pdf_bytes

    def _draw_page_decorations(self, canvas, doc) -> None:
        """
        Draw page decorations: watermark, borders, page numbers.
        Called for every page.
        """
        canvas.saveState()
        self.page_count += 1

        page_width, page_height = letter

        # ═══════════════════════════════════════════════════════════════
        # PACIOLI WATERMARK
        # ═══════════════════════════════════════════════════════════════
        canvas.saveState()
        canvas.setFillColor(ClassicalColors.OATMEAL_400)
        canvas.setFillAlpha(0.04)  # Very subtle
        canvas.setFont('Times-Italic', 48)

        # Rotate and position watermark
        canvas.translate(page_width / 2, page_height / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "Particularis de Computis")
        canvas.restoreState()

        # ═══════════════════════════════════════════════════════════════
        # TOP GOLD DOUBLE RULE
        # ═══════════════════════════════════════════════════════════════
        canvas.setStrokeColor(ClassicalColors.GOLD_INSTITUTIONAL)

        # Thick rule
        canvas.setLineWidth(2)
        canvas.line(
            0.75 * inch,
            page_height - 0.5 * inch,
            page_width - 0.75 * inch,
            page_height - 0.5 * inch
        )

        # Thin rule below
        canvas.setLineWidth(0.5)
        canvas.line(
            0.75 * inch,
            page_height - 0.55 * inch,
            page_width - 0.75 * inch,
            page_height - 0.55 * inch
        )

        # ═══════════════════════════════════════════════════════════════
        # BOTTOM RULE
        # ═══════════════════════════════════════════════════════════════
        canvas.setStrokeColor(ClassicalColors.LEDGER_RULE)
        canvas.setLineWidth(0.5)
        canvas.line(
            0.75 * inch,
            0.75 * inch,
            page_width - 0.75 * inch,
            0.75 * inch
        )

        # ═══════════════════════════════════════════════════════════════
        # PAGE NUMBER (Classical style: — 1 —)
        # ═══════════════════════════════════════════════════════════════
        canvas.setFont('Times-Roman', 9)
        canvas.setFillColor(ClassicalColors.OBSIDIAN_500)
        page_num_text = f"— {self.page_count} —"
        canvas.drawCentredString(page_width / 2, 0.5 * inch, page_num_text)

        # ═══════════════════════════════════════════════════════════════
        # LEGAL DISCLAIMER (every page)
        # ═══════════════════════════════════════════════════════════════
        canvas.setFont('Times-Roman', 7)
        canvas.setFillColor(ClassicalColors.OBSIDIAN_500)
        disclaimer = self._get_legal_disclaimer()

        # Wrap if too long
        if canvas.stringWidth(disclaimer, 'Times-Roman', 7) > page_width - 1.5 * inch:
            mid = len(disclaimer) // 2
            space_idx = disclaimer.rfind(' ', 0, mid + 20)
            if space_idx == -1:
                space_idx = mid

            line1 = disclaimer[:space_idx].strip()
            line2 = disclaimer[space_idx:].strip()

            canvas.drawCentredString(page_width / 2, 0.35 * inch, line2)
            canvas.drawCentredString(page_width / 2, 0.45 * inch, line1)
        else:
            canvas.drawCentredString(page_width / 2, 0.35 * inch, disclaimer)

        canvas.restoreState()

    def _build_classical_header(self) -> list:
        """Build the classical document header."""
        elements = []

        # Logo (if available)
        if self.logo_path:
            try:
                logo = Image(
                    self.logo_path,
                    width=1.2 * inch,
                    height=0.4 * inch,
                    kind='proportional'
                )
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 8))
            except (OSError, ValueError) as e:
                log_secure_operation("pdf_logo_error", f"Failed to add logo: {e}")

        # Main Title
        elements.append(Paragraph(
            "DIAGNOSTIC INTELLIGENCE SUMMARY",
            self.styles['ClassicalTitle']
        ))

        # Ornamental divider
        elements.append(Paragraph(
            "─── ◆ ───",
            self.styles['SectionOrnament']
        ))

        # Subtitle with client name
        elements.append(Paragraph(
            f"Analysis Report for {self.filename}",
            self.styles['ClassicalSubtitle']
        ))

        # Reference line with classical date
        classical_date = format_classical_date()
        elements.append(Paragraph(
            f"Prepared {classical_date}  ·  Ref: {self.reference_number}",
            self.styles['DocumentRef']
        ))

        # Double rule separator
        elements.append(DoubleRule(
            width=6.5 * inch,
            color=ClassicalColors.GOLD_INSTITUTIONAL,
            spaceAfter=16
        ))

        return elements

    def _build_section_ornament(self) -> list:
        """Build a section break ornament (fleuron)."""
        return [
            Spacer(1, 8),
            Paragraph("❧", self.styles['SectionOrnament']),
            Spacer(1, 8),
        ]

    def _build_executive_summary(self) -> list:
        """Build the executive summary with leader dots and status badge."""
        elements = []

        # Section header with small caps effect
        elements.append(Paragraph(
            "E X E C U T I V E   S U M M A R Y",
            self.styles['SectionHeader']
        ))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))

        # Status Badge (classical seal style)
        is_balanced = self.audit_result.get('balanced', False)

        if is_balanced:
            status_text = "✓   B A L A N C E D"
            badge_border = ClassicalColors.SAGE
            status_style = 'BalancedStatus'
        else:
            status_text = "⚠   O U T   O F   B A L A N C E"
            badge_border = ClassicalColors.CLAY
            status_style = 'UnbalancedStatus'

        # Create status badge as a table for border effect
        badge_data = [[Paragraph(status_text, self.styles[status_style])]]
        badge_table = Table(badge_data, colWidths=[4 * inch])
        badge_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, badge_border),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
        ]))
        badge_table.hAlign = 'CENTER'

        elements.append(Spacer(1, 12))
        elements.append(badge_table)
        elements.append(Spacer(1, 16))

        # Financial summary with leader dots
        total_debits = self.audit_result.get('total_debits', 0)
        total_credits = self.audit_result.get('total_credits', 0)
        difference = self.audit_result.get('difference', 0)
        row_count = self.audit_result.get('row_count', 0)
        threshold = self.audit_result.get('materiality_threshold', 0)

        leader_lines = [
            create_leader_dots("Total Debits", f"${total_debits:,.2f}"),
            create_leader_dots("Total Credits", f"${total_credits:,.2f}"),
            create_leader_dots("Variance", f"${difference:,.2f}"),
            create_leader_dots("Rows Analyzed", f"{row_count:,}"),
            create_leader_dots("Materiality Threshold", f"${threshold:,.2f}"),
        ]

        # Add consolidated info if applicable
        if self.audit_result.get('is_consolidated'):
            sheet_count = self.audit_result.get('sheet_count', 0)
            leader_lines.append(create_leader_dots("Sheets Consolidated", str(sheet_count)))

        for line in leader_lines:
            elements.append(Paragraph(line, self.styles['LeaderLine']))

        elements.append(Spacer(1, 12))

        return elements

    def _build_risk_summary(self) -> list:
        """Build the risk summary section."""
        elements = []

        elements.append(Paragraph(
            "R I S K   A S S E S S M E N T",
            self.styles['SectionHeader']
        ))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        elements.append(Spacer(1, 12))

        risk_summary = self.audit_result.get('risk_summary', {})
        material_count = self.audit_result.get('material_count', 0)
        immaterial_count = self.audit_result.get('immaterial_count', 0)
        total_anomalies = risk_summary.get('total_anomalies', material_count + immaterial_count)
        high_severity = risk_summary.get('high_severity', material_count)
        low_severity = risk_summary.get('low_severity', immaterial_count)

        # Risk metrics table with classical styling
        risk_data = [
            ['Total Findings', 'Material Exceptions', 'Minor Observations'],
            [str(total_anomalies), str(high_severity), str(low_severity)],
        ]

        risk_table = Table(risk_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
        risk_table.setStyle(TableStyle([
            # Header labels
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_500),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Values
            ('FONTNAME', (0, 1), (-1, 1), 'Times-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 24),
            ('TEXTCOLOR', (0, 1), (0, 1), ClassicalColors.OBSIDIAN_DEEP),
            ('TEXTCOLOR', (1, 1), (1, 1), ClassicalColors.CLAY),
            ('TEXTCOLOR', (2, 1), (2, 1), ClassicalColors.OBSIDIAN_500),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),

            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))

        elements.append(risk_table)
        elements.append(Spacer(1, 12))

        return elements

    def _build_anomaly_details(self) -> list:
        """Build the anomaly details with ledger-style tables."""
        elements = []

        abnormal_balances = self.audit_result.get('abnormal_balances', [])

        if not abnormal_balances:
            elements.append(Paragraph(
                "No exceptions identified. The trial balance appears sound.",
                self.styles['BodyText']
            ))
            return elements

        elements.append(Paragraph(
            "E X C E P T I O N   D E T A I L S",
            self.styles['SectionHeader']
        ))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        elements.append(Spacer(1, 8))

        # Separate by materiality
        material = [ab for ab in abnormal_balances if ab.get('materiality') == 'material']
        immaterial = [ab for ab in abnormal_balances if ab.get('materiality') == 'immaterial']

        if material:
            elements.append(Paragraph(
                f"Material Exceptions ({len(material)})",
                self.styles['SubsectionHeader']
            ))
            elements.append(self._create_ledger_table(material, is_material=True))
            elements.append(Spacer(1, 16))

        if immaterial:
            elements.append(Paragraph(
                f"Minor Observations ({len(immaterial)})",
                self.styles['SubsectionHeader']
            ))
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
        cell_style = self.styles['TableCell']
        header_style = self.styles['TableHeader']

        # Header row - Sprint 53: Added Ref column
        data = [[
            Paragraph("Ref", header_style),
            Paragraph("Account", header_style),
            Paragraph("Classification", header_style),
            Paragraph("Nature of Exception", header_style),
            Paragraph("Amount", header_style),
        ]]

        # Determine reference prefix based on materiality
        ref_prefix = "TB-M" if is_material else "TB-I"

        # Data rows
        total_amount = 0
        for idx, ab in enumerate(anomalies, start=1):
            # Sprint 53: Generate reference number
            ref_num = f"{ref_prefix}{idx:03d}"

            account = ab.get('account', 'Unknown')
            if len(account) > 25:
                account = account[:22] + '...'

            if ab.get('sheet_name'):
                account = f"{account} ({ab['sheet_name']})"

            acc_type = ab.get('type', 'Unknown')
            issue = Paragraph(ab.get('issue', ''), cell_style)
            amount = ab.get('amount', 0)
            total_amount += abs(amount)

            data.append([
                Paragraph(ref_num, cell_style),
                Paragraph(account, cell_style),
                Paragraph(acc_type, cell_style),
                issue,
                Paragraph(f"${amount:,.2f}", cell_style),
            ])

        # Total row
        data.append([
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("TOTAL", self.styles['TableHeader']),
            Paragraph(f"${total_amount:,.2f}", self.styles['TableHeader']),
        ])

        # Sprint 53: Adjusted column widths to accommodate Ref column
        table = Table(data, colWidths=[0.7 * inch, 1.5 * inch, 1.0 * inch, 2.3 * inch, 1 * inch])

        # Ledger styling
        accent_color = ClassicalColors.CLAY if is_material else ClassicalColors.OBSIDIAN_500

        style_commands = [
            # Header row
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),

            # Data rows - horizontal rules only (ledger style)
            ('LINEBELOW', (0, 1), (-1, -2), 0.25, ClassicalColors.LEDGER_RULE),

            # Total row
            ('LINEABOVE', (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_600),
            ('FONTNAME', (-2, -1), (-1, -1), 'Times-Bold'),

            # Left margin accent (double line effect)
            ('LINEBEFORE', (0, 1), (0, -1), 2, accent_color),

            # Right-align amounts
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),

            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (0, -1), 8),

            # Vertical alignment
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),

            # Alternating row backgrounds (subtle)
            ('ROWBACKGROUNDS', (0, 1), (-1, -2),
             [ClassicalColors.WHITE, ClassicalColors.OATMEAL_PAPER]),
        ]

        table.setStyle(TableStyle(style_commands))
        return table

    def _build_workpaper_signoff(self) -> list:
        """
        Build workpaper signoff section with prepared/reviewed fields.

        Sprint 53: Professional workpaper fields for audit documentation.
        """
        elements = []

        # Only include if workpaper fields are provided
        if not self.prepared_by and not self.reviewed_by:
            return elements

        elements.append(Spacer(1, 16))
        elements.append(Paragraph(
            "W O R K P A P E R   S I G N - O F F",
            self.styles['SectionHeader']
        ))
        elements.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        elements.append(Spacer(1, 8))

        # Build signoff table
        signoff_data = [["Field", "Name", "Date"]]

        if self.prepared_by:
            signoff_data.append([
                "Prepared By:",
                self.prepared_by,
                self.workpaper_date,
            ])

        if self.reviewed_by:
            signoff_data.append([
                "Reviewed By:",
                self.reviewed_by,
                self.workpaper_date,
            ])

        # Create table
        col_widths = [1.5 * inch, 3.5 * inch, 1.5 * inch]
        table = Table(signoff_data, colWidths=col_widths)

        style_commands = [
            # Header styling
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),

            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), ClassicalColors.OBSIDIAN_600),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),

            # Grid
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, ClassicalColors.LEDGER_RULE),

            # Background alternation
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [ClassicalColors.WHITE, ClassicalColors.OATMEAL_PAPER]),
        ]

        table.setStyle(TableStyle(style_commands))
        elements.append(table)

        return elements

    def _build_classical_footer(self) -> list:
        """Build the classical document footer."""
        elements = []

        elements.append(Spacer(1, 24))
        elements.append(DoubleRule(
            width=6.5 * inch,
            color=ClassicalColors.LEDGER_RULE,
            thick=0.5,
            thin=0.25,
            spaceAfter=8
        ))

        # Pacioli motto (Italian)
        elements.append(Paragraph(
            '"Particularis de Computis et Scripturis"',
            self.styles['FooterMotto']
        ))

        elements.append(Spacer(1, 8))

        # Generator info
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        elements.append(Paragraph(
            f"Generated by Paciolus® Diagnostic Intelligence  ·  {timestamp}",
            self.styles['Footer']
        ))

        # Zero-Storage promise
        elements.append(Paragraph(
            "Zero-Storage Architecture: Your financial data was processed in-memory and never stored.",
            self.styles['Footer']
        ))

        return elements

    def _get_legal_disclaimer(self) -> str:
        """Return the mandatory legal disclaimer text."""
        return (
            "This diagnostic output supports professional judgment and internal evaluation. "
            "It does not constitute an audit, review, or attestation engagement and provides no assurance."
        )


def generate_financial_statements_pdf(
    statements,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """
    Generate a PDF with Balance Sheet and Income Statement.

    Sprint 71: Financial Statements PDF using Renaissance Ledger aesthetic.

    Args:
        statements: FinancialStatements dataclass from FinancialStatementBuilder
        prepared_by: Name of preparer (optional)
        reviewed_by: Name of reviewer (optional)
        workpaper_date: Date for workpaper signoff (optional)
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

    def draw_fs_decorations(canvas, doc) -> None:
        """Page decorations for financial statements PDF."""
        canvas.saveState()
        page_counter[0] += 1
        page_width, page_height = letter

        # Watermark
        canvas.saveState()
        canvas.setFillColor(ClassicalColors.OATMEAL_400)
        canvas.setFillAlpha(0.04)
        canvas.setFont('Times-Italic', 48)
        canvas.translate(page_width / 2, page_height / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "Particularis de Computis")
        canvas.restoreState()

        # Top gold double rule
        canvas.setStrokeColor(ClassicalColors.GOLD_INSTITUTIONAL)
        canvas.setLineWidth(2)
        canvas.line(0.75 * inch, page_height - 0.5 * inch,
                    page_width - 0.75 * inch, page_height - 0.5 * inch)
        canvas.setLineWidth(0.5)
        canvas.line(0.75 * inch, page_height - 0.55 * inch,
                    page_width - 0.75 * inch, page_height - 0.55 * inch)

        # Bottom rule
        canvas.setStrokeColor(ClassicalColors.LEDGER_RULE)
        canvas.setLineWidth(0.5)
        canvas.line(0.75 * inch, 0.75 * inch,
                    page_width - 0.75 * inch, 0.75 * inch)

        # Page number
        canvas.setFont('Times-Roman', 9)
        canvas.setFillColor(ClassicalColors.OBSIDIAN_500)
        canvas.drawCentredString(page_width / 2, 0.5 * inch,
                                 f"— {page_counter[0]} —")

        # Disclaimer
        canvas.setFont('Times-Roman', 7)
        disclaimer = (
            "This output supports professional judgment and internal evaluation. "
            "It does not constitute an audit, review, or attestation engagement."
        )
        canvas.drawCentredString(page_width / 2, 0.35 * inch, disclaimer)
        canvas.restoreState()

    # ── HEADER ──
    entity_name = statements.entity_name or "Financial Statements"
    story.append(Paragraph("FINANCIAL STATEMENTS", styles['ClassicalTitle']))
    story.append(Paragraph("─── ◆ ───", styles['SectionOrnament']))
    story.append(Paragraph(entity_name, styles['ClassicalSubtitle']))

    if statements.period_end:
        story.append(Paragraph(
            f"Period Ending {statements.period_end}",
            styles['DocumentRef']
        ))

    ref_number = generate_reference_number()
    classical_date = format_classical_date()
    story.append(Paragraph(
        f"Prepared {classical_date}  ·  Ref: {ref_number}",
        styles['DocumentRef']
    ))
    story.append(DoubleRule(width=6.5 * inch, color=ClassicalColors.GOLD_INSTITUTIONAL, spaceAfter=16))

    # ── BALANCE SHEET ──
    story.append(Paragraph("B A L A N C E   S H E E T", styles['SectionHeader']))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 8))

    for item in statements.balance_sheet:
        if item.is_total:
            # Double rule before total
            story.append(LedgerRule(thickness=0.5, spaceBefore=4, spaceAfter=2))
            line = create_leader_dots(f"  {item.label}", f"${item.amount:,.2f}")
            story.append(Paragraph(f"<b>{line}</b>", styles['LeaderLine']))
            story.append(DoubleRule(width=6.5 * inch, color=ClassicalColors.OBSIDIAN_600,
                                   thick=1, thin=0.5, gap=1, spaceAfter=12))
        elif item.is_subtotal:
            line = create_leader_dots(f"    {item.label}", f"${item.amount:,.2f}")
            story.append(Paragraph(f"<b>{line}</b>", styles['LeaderLine']))
            story.append(LedgerRule(thickness=0.25, spaceBefore=2, spaceAfter=4))
        elif item.indent_level == 0 and not item.lead_sheet_ref:
            # Section header
            story.append(Spacer(1, 6))
            story.append(Paragraph(item.label, styles['SubsectionHeader']))
        else:
            # Regular line item with lead sheet ref
            ref = f" ({item.lead_sheet_ref})" if item.lead_sheet_ref else ""
            line = create_leader_dots(f"      {item.label}{ref}", f"${item.amount:,.2f}")
            story.append(Paragraph(line, styles['LeaderLine']))

    # ── BALANCE VERIFICATION ──
    story.append(Spacer(1, 12))
    if statements.is_balanced:
        badge_text = "✓   B A L A N C E D"
        badge_style = 'BalancedStatus'
        badge_border = ClassicalColors.SAGE
    else:
        badge_text = f"⚠   OUT OF BALANCE (${statements.balance_difference:,.2f})"
        badge_style = 'UnbalancedStatus'
        badge_border = ClassicalColors.CLAY

    badge_data = [[Paragraph(badge_text, styles[badge_style])]]
    badge_table = Table(badge_data, colWidths=[4 * inch])
    badge_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, badge_border),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
    ]))
    badge_table.hAlign = 'CENTER'
    story.append(badge_table)

    # Section ornament
    story.append(Spacer(1, 8))
    story.append(Paragraph("❧", styles['SectionOrnament']))
    story.append(Spacer(1, 8))

    # ── INCOME STATEMENT ──
    story.append(Paragraph("I N C O M E   S T A T E M E N T", styles['SectionHeader']))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 8))

    for item in statements.income_statement:
        if item.is_total:
            story.append(LedgerRule(thickness=0.5, spaceBefore=4, spaceAfter=2))
            line = create_leader_dots(f"  {item.label}", f"${item.amount:,.2f}")
            story.append(Paragraph(f"<b>{line}</b>", styles['LeaderLine']))
            story.append(DoubleRule(width=6.5 * inch, color=ClassicalColors.OBSIDIAN_600,
                                   thick=1, thin=0.5, gap=1, spaceAfter=12))
        elif item.is_subtotal:
            line = create_leader_dots(f"    {item.label}", f"${item.amount:,.2f}")
            story.append(Paragraph(f"<b>{line}</b>", styles['LeaderLine']))
            story.append(LedgerRule(thickness=0.25, spaceBefore=2, spaceAfter=4))
        else:
            ref = f" ({item.lead_sheet_ref})" if item.lead_sheet_ref else ""
            line = create_leader_dots(f"  {item.label}{ref}", f"${item.amount:,.2f}")
            story.append(Paragraph(line, styles['LeaderLine']))

    # ── CASH FLOW STATEMENT (Sprint 84) ──
    if statements.cash_flow_statement is not None:
        cf = statements.cash_flow_statement
        story.append(Spacer(1, 8))
        story.append(Paragraph("❧", styles['SectionOrnament']))
        story.append(Spacer(1, 8))

        story.append(Paragraph(
            "C A S H   F L O W   S T A T E M E N T",
            styles['SectionHeader']
        ))
        story.append(Paragraph(
            "(Indirect Method)",
            styles['DocumentRef']
        ))
        story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        story.append(Spacer(1, 8))

        for section in [cf.operating, cf.investing, cf.financing]:
            story.append(Paragraph(section.label, styles['SubsectionHeader']))
            story.append(Spacer(1, 4))
            for item in section.items:
                line = create_leader_dots(f"      {item.label}", f"${item.amount:,.2f}")
                story.append(Paragraph(line, styles['LeaderLine']))
            # Subtotal
            line = create_leader_dots(f"    Net {section.label}", f"${section.subtotal:,.2f}")
            story.append(Paragraph(f"<b>{line}</b>", styles['LeaderLine']))
            story.append(LedgerRule(thickness=0.25, spaceBefore=2, spaceAfter=8))

        # Net Change in Cash
        story.append(LedgerRule(thickness=0.5, spaceBefore=4, spaceAfter=2))
        line = create_leader_dots("  NET CHANGE IN CASH", f"${cf.net_change:,.2f}")
        story.append(Paragraph(f"<b>{line}</b>", styles['LeaderLine']))
        story.append(DoubleRule(width=6.5 * inch, color=ClassicalColors.OBSIDIAN_600,
                               thick=1, thin=0.5, gap=1, spaceAfter=8))

        # Reconciliation
        if cf.has_prior_period:
            story.append(Spacer(1, 4))
            line = create_leader_dots("  Beginning Cash", f"${cf.beginning_cash:,.2f}")
            story.append(Paragraph(line, styles['LeaderLine']))
            line = create_leader_dots("  Net Change in Cash", f"${cf.net_change:,.2f}")
            story.append(Paragraph(line, styles['LeaderLine']))
            story.append(LedgerRule(thickness=0.5, spaceBefore=2, spaceAfter=2))
            line = create_leader_dots("  ENDING CASH", f"${cf.ending_cash:,.2f}")
            story.append(Paragraph(f"<b>{line}</b>", styles['LeaderLine']))
            story.append(DoubleRule(width=6.5 * inch, color=ClassicalColors.OBSIDIAN_600,
                                   thick=1, thin=0.5, gap=1, spaceAfter=8))

            # Reconciliation badge
            if cf.is_reconciled:
                recon_text = "✓   R E C O N C I L E D"
                recon_style = 'BalancedStatus'
                recon_border = ClassicalColors.SAGE
            else:
                recon_text = f"⚠   UNRECONCILED (${cf.reconciliation_difference:,.2f})"
                recon_style = 'UnbalancedStatus'
                recon_border = ClassicalColors.CLAY

            recon_data = [[Paragraph(recon_text, styles[recon_style])]]
            recon_table = Table(recon_data, colWidths=[4 * inch])
            recon_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 2, recon_border),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
            ]))
            recon_table.hAlign = 'CENTER'
            story.append(recon_table)

        # Notes
        if cf.notes:
            story.append(Spacer(1, 8))
            for note in cf.notes:
                story.append(Paragraph(
                    f"<i>Note: {note}</i>",
                    styles['DocumentRef']
                ))

    # ── WORKPAPER SIGNOFF ──
    if prepared_by or reviewed_by:
        story.append(Spacer(1, 8))
        story.append(Paragraph("❧", styles['SectionOrnament']))
        story.append(Spacer(1, 8))

        story.append(Paragraph(
            "W O R K P A P E R   S I G N - O F F",
            styles['SectionHeader']
        ))
        story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
        story.append(Spacer(1, 8))

        wp_date = workpaper_date or datetime.now().strftime("%Y-%m-%d")
        signoff_data = [["Field", "Name", "Date"]]
        if prepared_by:
            signoff_data.append(["Prepared By:", prepared_by, wp_date])
        if reviewed_by:
            signoff_data.append(["Reviewed By:", reviewed_by, wp_date])

        signoff_table = Table(signoff_data, colWidths=[1.5 * inch, 3.5 * inch, 1.5 * inch])
        signoff_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), ClassicalColors.OBSIDIAN_600),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, ClassicalColors.LEDGER_RULE),
        ]))
        story.append(signoff_table)

    # ── FOOTER ──
    story.append(Spacer(1, 24))
    story.append(DoubleRule(
        width=6.5 * inch, color=ClassicalColors.LEDGER_RULE,
        thick=0.5, thin=0.25, spaceAfter=8
    ))
    story.append(Paragraph(
        '"Particularis de Computis et Scripturis"',
        styles['FooterMotto']
    ))
    story.append(Spacer(1, 8))
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(
        f"Generated by Paciolus® Financial Statement Builder  ·  {timestamp}",
        styles['Footer']
    ))
    story.append(Paragraph(
        "Zero-Storage Architecture: Your financial data was processed in-memory and never stored.",
        styles['Footer']
    ))

    doc.build(story, onFirstPage=draw_fs_decorations, onLaterPages=draw_fs_decorations)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation(
        "financial_statements_pdf_complete",
        f"Financial statements PDF generated: {len(pdf_bytes)} bytes"
    )

    return pdf_bytes


def generate_audit_report(
    audit_result: dict[str, Any],
    filename: str = "diagnostic",
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """
    Generate a PDF diagnostic report from audit results.

    Sprint 53: Added workpaper fields for professional documentation.

    Args:
        audit_result: The audit result dictionary
        filename: Base filename for the report
        prepared_by: Name of preparer (optional)
        reviewed_by: Name of reviewer (optional)
        workpaper_date: Date for workpaper signoff (optional, defaults to today)
    """
    generator = PaciolusReportGenerator(
        audit_result,
        filename,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
    )
    return generator.generate()
