"""
Shared Testing Memo Base — Sprint 90

Extracted from JE/AP/Payroll testing memo generators.
All three had identical style definitions, risk tier display, and
common section builders (header, scope, results, workpaper, disclaimer).

Each memo generator imports these functions and provides only
domain-specific content (title, test descriptions, conclusion text).
"""

from typing import Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle,
)

from pdf_generator import (
    ClassicalColors, DoubleRule, LedgerRule,
    format_classical_date, create_leader_dots,
    _add_or_replace_style,
)


# =============================================================================
# Risk tier display mapping (identical across all 3 memo generators)
# =============================================================================

RISK_TIER_DISPLAY = {
    "low": ("LOW RISK", ClassicalColors.SAGE),
    "elevated": ("ELEVATED", ClassicalColors.GOLD_INSTITUTIONAL),
    "moderate": ("MODERATE", ClassicalColors.GOLD_INSTITUTIONAL),
    "high": ("HIGH RISK", ClassicalColors.CLAY),
    "critical": ("CRITICAL", ClassicalColors.CLAY),
}


# =============================================================================
# Style creation (identical across all 3 memo generators)
# =============================================================================

def create_memo_styles() -> dict:
    """Create the standard memo style set used by all testing memos."""
    styles = getSampleStyleSheet()

    memo_styles = [
        ParagraphStyle(
            'MemoTitle', fontName='Times-Bold', fontSize=24,
            textColor=ClassicalColors.OBSIDIAN_DEEP, alignment=TA_CENTER,
            spaceAfter=6,
        ),
        ParagraphStyle(
            'MemoSubtitle', fontName='Times-Roman', fontSize=11,
            textColor=ClassicalColors.OBSIDIAN_500, alignment=TA_CENTER,
            spaceAfter=4,
        ),
        ParagraphStyle(
            'MemoRef', fontName='Times-Italic', fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_500, alignment=TA_CENTER,
            spaceAfter=12,
        ),
        ParagraphStyle(
            'MemoSection', fontName='Times-Bold', fontSize=11,
            textColor=ClassicalColors.OBSIDIAN_DEEP, spaceAfter=6,
            spaceBefore=16,
        ),
        ParagraphStyle(
            'MemoBody', fontName='Times-Roman', fontSize=10,
            textColor=ClassicalColors.OBSIDIAN_DEEP, spaceAfter=4,
            leading=14,
        ),
        ParagraphStyle(
            'MemoBodySmall', fontName='Times-Roman', fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_500, spaceAfter=3,
            leading=12,
        ),
        ParagraphStyle(
            'MemoLeader', fontName='Courier', fontSize=10,
            textColor=ClassicalColors.OBSIDIAN_DEEP, spaceAfter=2,
        ),
        ParagraphStyle(
            'MemoTableCell', fontName='Times-Roman', fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_DEEP, leading=11,
        ),
        ParagraphStyle(
            'MemoTableHeader', fontName='Times-Bold', fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_DEEP, leading=11,
        ),
        ParagraphStyle(
            'MemoFooter', fontName='Times-Roman', fontSize=8,
            textColor=ClassicalColors.OBSIDIAN_500, alignment=TA_CENTER,
        ),
        ParagraphStyle(
            'MemoDisclaimer', fontName='Times-Roman', fontSize=7,
            textColor=ClassicalColors.OBSIDIAN_500, alignment=TA_CENTER,
            leading=9, spaceAfter=4,
        ),
    ]

    style_dict = {}
    for s in memo_styles:
        _add_or_replace_style(styles, s)
        style_dict[s.name] = s

    return style_dict


# =============================================================================
# Shared section builders
# =============================================================================

def build_memo_header(
    story: list,
    styles: dict,
    doc_width: float,
    title: str,
    reference: str,
    client_name: Optional[str] = None,
) -> None:
    """Build the standard memo header (title, client, date, reference)."""
    story.append(Paragraph(title, styles['MemoTitle']))
    if client_name:
        story.append(Paragraph(client_name, styles['MemoSubtitle']))
    story.append(Paragraph(
        f"{format_classical_date()} &nbsp;&bull;&nbsp; {reference}",
        styles['MemoRef'],
    ))
    story.append(DoubleRule(doc_width))
    story.append(Spacer(1, 12))


def build_scope_section(
    story: list,
    styles: dict,
    doc_width: float,
    composite: dict[str, Any],
    data_quality: dict[str, Any],
    entry_label: str = "Total Entries Tested",
    period_tested: Optional[str] = None,
) -> None:
    """Build the Scope section (I. SCOPE)."""
    story.append(Paragraph("I. SCOPE", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

    total_entries = composite.get("total_entries", 0)
    tests_run = composite.get("tests_run", 0)

    scope_lines = [
        create_leader_dots(entry_label, f"{total_entries:,}"),
        create_leader_dots("Tests Applied", str(tests_run)),
        create_leader_dots("Data Quality Score", f"{data_quality.get('completeness_score', 0):.0f}%"),
    ]
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))

    for line in scope_lines:
        story.append(Paragraph(line, styles['MemoLeader']))
    story.append(Spacer(1, 8))


def build_methodology_section(
    story: list,
    styles: dict,
    doc_width: float,
    test_results: list[dict],
    test_descriptions: dict[str, str],
    intro_text: str,
) -> None:
    """Build the Methodology section (II. METHODOLOGY)."""
    story.append(Paragraph("II. METHODOLOGY", styles['MemoSection']))
    story.append(LedgerRule(doc_width))
    story.append(Paragraph(intro_text, styles['MemoBody']))

    method_data = [["Test", "Tier", "Description"]]
    for tr in test_results:
        desc = test_descriptions.get(tr["test_key"], tr.get("description", ""))
        method_data.append([
            Paragraph(tr["test_name"], styles['MemoTableCell']),
            Paragraph(tr["test_tier"].title(), styles['MemoTableCell']),
            Paragraph(desc[:120], styles['MemoTableCell']),
        ])

    method_table = Table(method_data, colWidths=[1.5 * inch, 0.8 * inch, 4.3 * inch])
    method_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
    ]))
    story.append(method_table)
    story.append(Spacer(1, 8))


def build_results_summary_section(
    story: list,
    styles: dict,
    doc_width: float,
    composite: dict[str, Any],
    test_results: list[dict],
    flagged_label: str = "Total Entries Flagged",
) -> None:
    """Build the Results Summary section (III. RESULTS SUMMARY)."""
    story.append(Paragraph("III. RESULTS SUMMARY", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

    risk_tier = composite.get("risk_tier", "low")
    tier_label, _ = RISK_TIER_DISPLAY.get(risk_tier, ("UNKNOWN", ClassicalColors.OBSIDIAN_500))

    story.append(Paragraph(
        create_leader_dots("Composite Risk Score", f"{composite.get('score', 0):.1f} / 100"),
        styles['MemoLeader'],
    ))
    story.append(Paragraph(
        create_leader_dots("Risk Tier", tier_label),
        styles['MemoLeader'],
    ))
    story.append(Paragraph(
        create_leader_dots(flagged_label, f"{composite.get('total_flagged', 0):,}"),
        styles['MemoLeader'],
    ))
    story.append(Paragraph(
        create_leader_dots("Overall Flag Rate", f"{composite.get('flag_rate', 0):.1%}"),
        styles['MemoLeader'],
    ))

    sev = composite.get("flags_by_severity", {})
    story.append(Paragraph(
        create_leader_dots("High Severity Flags", str(sev.get("high", 0))),
        styles['MemoLeader'],
    ))
    story.append(Paragraph(
        create_leader_dots("Medium Severity Flags", str(sev.get("medium", 0))),
        styles['MemoLeader'],
    ))
    story.append(Paragraph(
        create_leader_dots("Low Severity Flags", str(sev.get("low", 0))),
        styles['MemoLeader'],
    ))
    story.append(Spacer(1, 6))

    # Results by test table
    results_data = [["Test", "Flagged", "Rate", "Severity"]]
    for tr in sorted(test_results, key=lambda t: t.get("flag_rate", 0), reverse=True):
        results_data.append([
            tr["test_name"],
            str(tr["entries_flagged"]),
            f"{tr['flag_rate']:.1%}",
            tr["severity"].upper(),
        ])

    results_table = Table(results_data, colWidths=[2.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch])
    results_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
    ]))
    story.append(results_table)
    story.append(Spacer(1, 8))


def build_workpaper_signoff(
    story: list,
    styles: dict,
    doc_width: float,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> None:
    """Build the workpaper sign-off section."""
    if not (prepared_by or reviewed_by):
        return

    story.append(LedgerRule(doc_width))
    signoff_data = [["", "Name", "Date"]]
    wp_date = workpaper_date or format_classical_date()
    if prepared_by:
        signoff_data.append(["Prepared By:", prepared_by, wp_date])
    if reviewed_by:
        signoff_data.append(["Reviewed By:", reviewed_by, ""])
    signoff_table = Table(signoff_data, colWidths=[1.2 * inch, 3.0 * inch, 2.0 * inch])
    signoff_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(signoff_table)
    story.append(Spacer(1, 8))


def build_disclaimer(
    story: list,
    styles: dict,
    domain: str = "testing",
) -> None:
    """Build the standard disclaimer footer."""
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"This memo documents automated {domain} procedures. "
        "Results should be interpreted in the context of the specific engagement "
        "and are not a substitute for professional judgment. "
        "Generated by Paciolus \u2014 Zero-Storage Audit Intelligence.",
        styles['MemoDisclaimer'],
    ))
