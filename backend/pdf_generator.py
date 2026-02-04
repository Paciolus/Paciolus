"""
Paciolus PDF Report Generator
Sprint 18: Diagnostic Fidelity & Batch Intelligence

Generates professional "Diagnostic Summary Reports" using the Oat & Obsidian theme.
Zero-Storage compliant: All generation happens in BytesIO buffers.

Uses ReportLab (BSD License) - see logs/dev-log.md for IP documentation.
"""

import io
import os
from datetime import datetime, UTC
from typing import Any, Optional
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from security_utils import log_secure_operation


# =============================================================================
# OAT & OBSIDIAN COLOR PALETTE
# =============================================================================

class OatObsidianColors:
    """Oat & Obsidian theme colors for PDF generation."""
    # Core palette
    OBSIDIAN = colors.HexColor('#212121')
    OBSIDIAN_700 = colors.HexColor('#303030')
    OBSIDIAN_600 = colors.HexColor('#424242')
    OBSIDIAN_500 = colors.HexColor('#616161')

    OATMEAL = colors.HexColor('#EBE9E4')
    OATMEAL_300 = colors.HexColor('#DDD9D1')
    OATMEAL_400 = colors.HexColor('#C9C3B8')
    OATMEAL_500 = colors.HexColor('#B5AD9F')

    CLAY = colors.HexColor('#BC4749')
    CLAY_400 = colors.HexColor('#D16C6E')
    CLAY_600 = colors.HexColor('#A33D3F')

    SAGE = colors.HexColor('#4A7C59')
    SAGE_400 = colors.HexColor('#6FA882')
    SAGE_600 = colors.HexColor('#3D6649')

    # Semantic
    WHITE = colors.white
    LIGHT_GRAY = colors.HexColor('#F5F4F2')


# =============================================================================
# PDF STYLES
# =============================================================================

def _add_or_replace_style(styles, style: ParagraphStyle) -> None:
    """
    Add a style to the stylesheet, replacing it if it already exists.

    This prevents 'Style already defined' errors when getSampleStyleSheet()
    returns pre-existing styles like 'BodyText'.
    """
    if style.name in [s.name for s in styles.byName.values()]:
        # Style exists - replace it by updating the existing style's attributes
        existing = styles[style.name]
        for attr in ['fontName', 'fontSize', 'textColor', 'alignment',
                     'spaceBefore', 'spaceAfter', 'leading', 'leftIndent',
                     'rightIndent', 'firstLineIndent', 'bulletIndent']:
            if hasattr(style, attr) and getattr(style, attr) is not None:
                setattr(existing, attr, getattr(style, attr))
    else:
        styles.add(style)


def create_styles() -> dict:
    """
    Create Oat & Obsidian styled paragraph styles.

    Uses _add_or_replace_style() to handle pre-existing styles from
    getSampleStyleSheet() (e.g., 'BodyText') without raising errors.
    """
    styles = getSampleStyleSheet()

    # Title style (Merriweather-like serif)
    _add_or_replace_style(styles, ParagraphStyle(
        name='PaciolusTitle',
        fontName='Times-Bold',
        fontSize=24,
        textColor=OatObsidianColors.OBSIDIAN,
        alignment=TA_CENTER,
        spaceAfter=12,
    ))

    # Subtitle
    _add_or_replace_style(styles, ParagraphStyle(
        name='PaciolusSubtitle',
        fontName='Helvetica',
        fontSize=12,
        textColor=OatObsidianColors.OBSIDIAN_500,
        alignment=TA_CENTER,
        spaceAfter=24,
    ))

    # Section header
    _add_or_replace_style(styles, ParagraphStyle(
        name='SectionHeader',
        fontName='Times-Bold',
        fontSize=16,
        textColor=OatObsidianColors.OBSIDIAN,
        spaceBefore=20,
        spaceAfter=12,
    ))

    # Body text - NOTE: This style exists in getSampleStyleSheet(), so we replace it
    _add_or_replace_style(styles, ParagraphStyle(
        name='BodyText',
        fontName='Helvetica',
        fontSize=10,
        textColor=OatObsidianColors.OBSIDIAN_600,
        leading=14,
        spaceAfter=8,
    ))

    # Summary stat
    _add_or_replace_style(styles, ParagraphStyle(
        name='SummaryStat',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=OatObsidianColors.OBSIDIAN,
        alignment=TA_CENTER,
    ))

    # Summary label
    _add_or_replace_style(styles, ParagraphStyle(
        name='SummaryLabel',
        fontName='Helvetica',
        fontSize=10,
        textColor=OatObsidianColors.OBSIDIAN_500,
        alignment=TA_CENTER,
    ))

    # Footer
    _add_or_replace_style(styles, ParagraphStyle(
        name='Footer',
        fontName='Helvetica',
        fontSize=8,
        textColor=OatObsidianColors.OBSIDIAN_500,
        alignment=TA_CENTER,
    ))

    # Balanced status - uses SAGE for success (Tier 2 semantic color)
    _add_or_replace_style(styles, ParagraphStyle(
        name='BalancedStatus',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=OatObsidianColors.SAGE,
        alignment=TA_CENTER,
    ))

    # Unbalanced status - uses CLAY for errors (Tier 2 semantic color)
    _add_or_replace_style(styles, ParagraphStyle(
        name='UnbalancedStatus',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=OatObsidianColors.CLAY,
        alignment=TA_CENTER,
    ))

    # Sprint 18: Legal disclaimer style - appears on every page footer
    _add_or_replace_style(styles, ParagraphStyle(
        name='LegalDisclaimer',
        fontName='Helvetica',
        fontSize=7,
        textColor=OatObsidianColors.OBSIDIAN_500,
        alignment=TA_CENTER,
        leading=9,
    ))

    # Sprint 18: Table cell style for wrapped text in anomaly descriptions
    _add_or_replace_style(styles, ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=8,
        textColor=OatObsidianColors.OBSIDIAN_600,
        leading=10,
    ))

    return styles


# =============================================================================
# PDF GENERATOR
# =============================================================================

class PaciolusReportGenerator:
    """
    Generates Paciolus Audit Reports in PDF format.

    Zero-Storage compliant: Uses BytesIO buffer, never writes to disk.
    """

    def __init__(self, audit_result: dict[str, Any], filename: str = "audit"):
        """
        Initialize the report generator.

        Args:
            audit_result: The audit result dictionary from the API
            filename: Original filename of the audited file
        """
        self.audit_result = audit_result
        self.filename = filename
        self.styles = create_styles()
        self.buffer = io.BytesIO()

        # Find logo path
        self.logo_path = self._find_logo()

        log_secure_operation(
            "pdf_generator_init",
            f"Initializing PDF generator for: {filename}"
        )

    def _find_logo(self) -> Optional[str]:
        """Find the Paciolus logo file. Uses LightBG variant for PDF contrast."""
        # Try multiple possible locations - Sprint 18: Use LightBG for better PDF contrast
        possible_paths = [
            Path(__file__).parent.parent / "frontend" / "public" / "PaciolusLogo_LightBG.png",
            Path(__file__).parent.parent / "PaciolusLogo_LightBG.png",
            Path(__file__).parent / "assets" / "PaciolusLogo_LightBG.png",
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        log_secure_operation("pdf_logo_not_found", "Logo file not found, will skip logo")
        return None

    def generate(self) -> bytes:
        """
        Generate the PDF report.

        Sprint 18: Includes legal disclaimer on every page footer.

        Returns:
            PDF file as bytes (can be streamed directly to response)
        """
        log_secure_operation("pdf_generate_start", "Starting PDF generation")

        # Create document with extra bottom margin for page footer
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=1.0 * inch,  # Extra space for page footer disclaimer
        )

        # Build story (content)
        story = []

        # Header with logo
        story.extend(self._build_header())

        # Executive summary
        story.extend(self._build_executive_summary())

        # Risk summary
        story.extend(self._build_risk_summary())

        # Anomaly details
        story.extend(self._build_anomaly_details())

        # Footer (end of document)
        story.extend(self._build_footer())

        # Sprint 18: Build PDF with page callback for legal disclaimer on every page
        doc.build(story, onFirstPage=self._add_page_footer, onLaterPages=self._add_page_footer)

        # Get bytes from buffer
        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()

        log_secure_operation(
            "pdf_generate_complete",
            f"PDF generated: {len(pdf_bytes)} bytes"
        )

        return pdf_bytes

    def _add_page_footer(self, canvas, doc):
        """
        Sprint 18: Add legal disclaimer to every page footer.

        This is called by ReportLab for each page during PDF generation.
        """
        canvas.saveState()

        # Draw disclaimer at bottom of every page
        disclaimer_text = self._get_legal_disclaimer()

        # Set font and color
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(OatObsidianColors.OBSIDIAN_500)

        # Calculate position (centered at bottom)
        page_width = letter[0]
        text_width = canvas.stringWidth(disclaimer_text, 'Helvetica', 7)

        # If text is too long, wrap it
        if text_width > page_width - (1.5 * inch):
            # Split into two lines
            mid = len(disclaimer_text) // 2
            space_idx = disclaimer_text.rfind(' ', 0, mid + 20)
            if space_idx == -1:
                space_idx = mid

            line1 = disclaimer_text[:space_idx].strip()
            line2 = disclaimer_text[space_idx:].strip()

            canvas.drawCentredString(page_width / 2, 0.5 * inch, line2)
            canvas.drawCentredString(page_width / 2, 0.6 * inch, line1)
        else:
            canvas.drawCentredString(page_width / 2, 0.5 * inch, disclaimer_text)

        canvas.restoreState()

    def _build_header(self) -> list:
        """Build the report header with logo."""
        elements = []

        # Add logo if available - Sprint 18: preserveAspectRatio for proper scaling
        if self.logo_path:
            try:
                logo = Image(
                    self.logo_path,
                    width=1.5 * inch,
                    height=0.5 * inch,
                    kind='proportional'  # Preserves aspect ratio, fits within bounds
                )
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 12))
            except Exception as e:
                log_secure_operation("pdf_logo_error", f"Failed to add logo: {e}")

        # Title - Sprint 18: Terminology update "Audit" → "Diagnostic"
        elements.append(Paragraph(
            "Paciolus Diagnostic Summary",
            self.styles['PaciolusTitle']
        ))

        # Subtitle
        elements.append(Paragraph(
            f"Analysis Intelligence Report for {self.filename}",
            self.styles['PaciolusSubtitle']
        ))

        # Horizontal rule
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=OatObsidianColors.OATMEAL_400,
            spaceAfter=20
        ))

        return elements

    def _build_executive_summary(self) -> list:
        """Build the executive summary section."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))

        # Balance status
        is_balanced = self.audit_result.get('balanced', False)
        status_style = 'BalancedStatus' if is_balanced else 'UnbalancedStatus'
        status_text = "BALANCED" if is_balanced else "OUT OF BALANCE"

        elements.append(Paragraph(status_text, self.styles[status_style]))
        elements.append(Spacer(1, 12))

        # Summary table
        total_debits = self.audit_result.get('total_debits', 0)
        total_credits = self.audit_result.get('total_credits', 0)
        difference = self.audit_result.get('difference', 0)
        row_count = self.audit_result.get('row_count', 0)
        threshold = self.audit_result.get('materiality_threshold', 0)

        summary_data = [
            ['Metric', 'Value'],
            ['Total Debits', f"${total_debits:,.2f}"],
            ['Total Credits', f"${total_credits:,.2f}"],
            ['Difference', f"${difference:,.2f}"],
            ['Rows Analyzed', f"{row_count:,}"],
            ['Materiality Threshold', f"${threshold:,.2f}"],
        ]

        # Check for consolidated audit
        if self.audit_result.get('is_consolidated'):
            sheet_count = self.audit_result.get('sheet_count', 0)
            summary_data.append(['Sheets Consolidated', str(sheet_count)])

        summary_table = Table(summary_data, colWidths=[2.5 * inch, 2 * inch])
        summary_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), OatObsidianColors.OBSIDIAN),
            ('TEXTCOLOR', (0, 0), (-1, 0), OatObsidianColors.OATMEAL),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), OatObsidianColors.LIGHT_GRAY),
            ('TEXTCOLOR', (0, 1), (-1, -1), OatObsidianColors.OBSIDIAN_600),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, OatObsidianColors.OATMEAL_400),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        return elements

    def _build_risk_summary(self) -> list:
        """Build the risk summary section mirroring Day 10 dashboard."""
        elements = []

        elements.append(Paragraph("Risk Summary", self.styles['SectionHeader']))

        risk_summary = self.audit_result.get('risk_summary', {})
        material_count = self.audit_result.get('material_count', 0)
        immaterial_count = self.audit_result.get('immaterial_count', 0)
        total_anomalies = risk_summary.get('total_anomalies', material_count + immaterial_count)
        high_severity = risk_summary.get('high_severity', material_count)
        low_severity = risk_summary.get('low_severity', immaterial_count)

        # Risk stats in a visual layout
        risk_data = [
            ['Total Anomalies', 'High Severity', 'Low Severity'],
            [str(total_anomalies), str(high_severity), str(low_severity)],
        ]

        risk_table = Table(risk_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
        risk_table.setStyle(TableStyle([
            # Labels
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), OatObsidianColors.OBSIDIAN_500),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Values
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 24),
            ('TEXTCOLOR', (0, 1), (0, 1), OatObsidianColors.OBSIDIAN),
            ('TEXTCOLOR', (1, 1), (1, 1), OatObsidianColors.CLAY),
            ('TEXTCOLOR', (2, 1), (2, 1), OatObsidianColors.OBSIDIAN_500),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),

            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))

        elements.append(risk_table)
        elements.append(Spacer(1, 20))

        return elements

    def _build_anomaly_details(self) -> list:
        """Build the detailed anomaly table."""
        elements = []

        abnormal_balances = self.audit_result.get('abnormal_balances', [])

        if not abnormal_balances:
            elements.append(Paragraph(
                "No anomalies detected. Trial balance appears healthy.",
                self.styles['BodyText']
            ))
            return elements

        elements.append(Paragraph("Anomaly Details", self.styles['SectionHeader']))

        # Separate material and immaterial
        material = [ab for ab in abnormal_balances if ab.get('materiality') == 'material']
        immaterial = [ab for ab in abnormal_balances if ab.get('materiality') == 'immaterial']

        # Material anomalies section
        if material:
            elements.append(Paragraph(
                f"Material Risks ({len(material)})",
                self.styles['BodyText']
            ))
            elements.append(self._create_anomaly_table(material, is_material=True))
            elements.append(Spacer(1, 16))

        # Immaterial anomalies section
        if immaterial:
            elements.append(Paragraph(
                f"Indistinct Items ({len(immaterial)})",
                self.styles['BodyText']
            ))
            elements.append(self._create_anomaly_table(immaterial, is_material=False))

        return elements

    def _create_anomaly_table(self, anomalies: list, is_material: bool) -> Table:
        """
        Create a styled table for anomalies.

        Sprint 18: Uses Paragraph objects for Issue column to ensure
        text wraps properly and no content is cut off.
        """
        # Header
        data = [['Account', 'Type', 'Issue', 'Amount']]

        # Get table cell style for wrapped text
        cell_style = self.styles['TableCell']

        # Add rows - Sprint 18: Wrap issue text in Paragraph for proper wrapping
        for ab in anomalies:
            account = ab.get('account', 'Unknown')
            if len(account) > 30:
                account = account[:27] + '...'

            acc_type = ab.get('type', 'Unknown')

            # Sprint 18: Issue description wrapped in Paragraph - NO text cutoff
            issue_text = ab.get('issue', '')
            issue = Paragraph(issue_text, cell_style)

            amount = ab.get('amount', 0)

            # Add sheet name if consolidated
            if ab.get('sheet_name'):
                account = f"{account} ({ab['sheet_name']})"

            data.append([
                account,
                acc_type,
                issue,  # Now a Paragraph object for proper wrapping
                f"${amount:,.2f}"
            ])

        table = Table(data, colWidths=[2 * inch, 1 * inch, 2.5 * inch, 1 * inch])

        # Determine accent color
        accent_color = OatObsidianColors.CLAY if is_material else OatObsidianColors.OBSIDIAN_500

        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), OatObsidianColors.OBSIDIAN),
            ('TEXTCOLOR', (0, 0), (-1, 0), OatObsidianColors.OATMEAL),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), OatObsidianColors.LIGHT_GRAY),
            ('TEXTCOLOR', (0, 1), (-1, -1), OatObsidianColors.OBSIDIAN_600),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),  # Amount column right-aligned

            # Left border accent (premium restraint)
            ('LINEAFTER', (-1, 0), (-1, -1), 0, OatObsidianColors.WHITE),
            ('LINEBEFORE', (0, 1), (0, -1), 3, accent_color),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, OatObsidianColors.OATMEAL_400),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Changed to TOP for wrapped text
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 1), (0, -1), 10),  # Extra padding for accent
        ]))

        return table

    def _build_footer(self) -> list:
        """Build the report footer with legal disclaimer."""
        elements = []

        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=OatObsidianColors.OATMEAL_400,
            spaceBefore=20,
            spaceAfter=12
        ))

        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

        elements.append(Paragraph(
            f"Generated by Paciolus | {timestamp}",
            self.styles['Footer']
        ))

        elements.append(Paragraph(
            "Zero-Storage Architecture: This report was generated in-memory. No data was stored on our servers.",
            self.styles['Footer']
        ))

        # Sprint 18: Mandatory legal disclaimer
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            self._get_legal_disclaimer(),
            self.styles['LegalDisclaimer']
        ))

        return elements

    def _get_legal_disclaimer(self) -> str:
        """
        Sprint 18: Mandatory legal disclaimer text.

        This appears on every page footer per directive requirements.
        """
        return (
            "This output is generated by an automated analytical system and supports "
            "internal evaluation and professional judgment. It does not constitute an audit, "
            "review, or attestation engagement and provides no assurance."
        )


# =============================================================================
# PUBLIC API
# =============================================================================

def generate_audit_report(audit_result: dict[str, Any], filename: str = "audit") -> bytes:
    """
    Generate a PDF audit report from audit results.

    Zero-Storage compliant: Returns bytes directly, never writes to disk.

    Args:
        audit_result: The audit result dictionary from the API
        filename: Original filename of the audited file

    Returns:
        PDF file as bytes
    """
    generator = PaciolusReportGenerator(audit_result, filename)
    return generator.generate()
