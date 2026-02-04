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
import os
from datetime import datetime, UTC
from typing import Any, Optional
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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

    def draw(self):
        self.canv.setStrokeColor(self.color)

        # Thick rule
        self.canv.setLineWidth(self.thick)
        self.canv.line(0, self.gap + self.thin, self.width, self.gap + self.thin)

        # Thin rule below
        self.canv.setLineWidth(self.thin)
        self.canv.line(0, 0, self.width, 0)

    def wrap(self, availWidth, availHeight):
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

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

    def wrap(self, availWidth, availHeight):
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

    def __init__(self, audit_result: dict[str, Any], filename: str = "diagnostic"):
        self.audit_result = audit_result
        self.filename = filename
        self.styles = create_classical_styles()
        self.buffer = io.BytesIO()
        self.logo_path = self._find_logo()
        self.reference_number = generate_reference_number()
        self.page_count = 0

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

    def _draw_page_decorations(self, canvas, doc):
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
            except Exception as e:
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
        """
        cell_style = self.styles['TableCell']
        header_style = self.styles['TableHeader']

        # Header row
        data = [[
            Paragraph("Account", header_style),
            Paragraph("Classification", header_style),
            Paragraph("Nature of Exception", header_style),
            Paragraph("Amount", header_style),
        ]]

        # Data rows
        total_amount = 0
        for ab in anomalies:
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
                Paragraph(account, cell_style),
                Paragraph(acc_type, cell_style),
                issue,
                Paragraph(f"${amount:,.2f}", cell_style),
            ])

        # Total row
        data.append([
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("TOTAL", self.styles['TableHeader']),
            Paragraph(f"${total_amount:,.2f}", self.styles['TableHeader']),
        ])

        table = Table(data, colWidths=[1.8 * inch, 1.2 * inch, 2.5 * inch, 1 * inch])

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


def generate_audit_report(audit_result: dict[str, Any], filename: str = "diagnostic") -> bytes:
    """Generate a PDF diagnostic report from audit results."""
    generator = PaciolusReportGenerator(audit_result, filename)
    return generator.generate()
