"""
Shared Testing Memo Base — Sprint 90

Extracted from JE/AP/Payroll testing memo generators.
All three had identical style definitions, risk tier display, and
common section builders (header, scope, results, workpaper, disclaimer).

Each memo generator imports these functions and provides only
domain-specific content (title, test descriptions, conclusion text).
"""

from typing import Any, Optional

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from pdf_generator import (
    ClassicalColors,
    DoubleRule,
    LedgerRule,
    _add_or_replace_style,
    create_leader_dots,
    format_classical_date,
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
            "MemoTitle",
            fontName="Times-Bold",
            fontSize=24,
            textColor=ClassicalColors.OBSIDIAN_DEEP,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        ParagraphStyle(
            "MemoSubtitle",
            fontName="Times-Roman",
            fontSize=11,
            textColor=ClassicalColors.OBSIDIAN_500,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        ParagraphStyle(
            "MemoRef",
            fontName="Times-Italic",
            fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_500,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        ParagraphStyle(
            "MemoSection",
            fontName="Times-Bold",
            fontSize=11,
            textColor=ClassicalColors.OBSIDIAN_DEEP,
            spaceAfter=6,
            spaceBefore=16,
        ),
        ParagraphStyle(
            "MemoBody",
            fontName="Times-Roman",
            fontSize=10,
            textColor=ClassicalColors.OBSIDIAN_DEEP,
            spaceAfter=4,
            leading=14,
        ),
        ParagraphStyle(
            "MemoBodySmall",
            fontName="Times-Roman",
            fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_500,
            spaceAfter=3,
            leading=12,
        ),
        ParagraphStyle(
            "MemoLeader",
            fontName="Courier",
            fontSize=10,
            textColor=ClassicalColors.OBSIDIAN_DEEP,
            spaceAfter=2,
        ),
        ParagraphStyle(
            "MemoTableCell",
            fontName="Times-Roman",
            fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_DEEP,
            leading=11,
        ),
        ParagraphStyle(
            "MemoTableHeader",
            fontName="Times-Bold",
            fontSize=9,
            textColor=ClassicalColors.OBSIDIAN_DEEP,
            leading=11,
        ),
        ParagraphStyle(
            "MemoFooter",
            fontName="Times-Roman",
            fontSize=8,
            textColor=ClassicalColors.OBSIDIAN_500,
            alignment=TA_CENTER,
        ),
        ParagraphStyle(
            "MemoDisclaimer",
            fontName="Times-Roman",
            fontSize=7,
            textColor=ClassicalColors.OBSIDIAN_500,
            alignment=TA_CENTER,
            leading=9,
            spaceAfter=4,
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
    story.append(Paragraph(title, styles["MemoTitle"]))
    if client_name:
        story.append(Paragraph(client_name, styles["MemoSubtitle"]))
    story.append(
        Paragraph(
            f"{format_classical_date()} &nbsp;&bull;&nbsp; {reference}",
            styles["MemoRef"],
        )
    )
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
    source_document: Optional[str] = None,
    source_document_title: Optional[str] = None,
    planning_materiality: Optional[float] = None,
    performance_materiality: Optional[float] = None,
) -> None:
    """Build the Scope section (I. Scope).

    Sprint 6: source_document and source_document_title are optional.
    If title is present, shown as "Source: <title> (<filename>)".
    If title absent but filename present, shown as "Source: <filename>".

    Materiality context: when planning/performance materiality are provided,
    adds leader-dot lines with a non-assertive qualification note.
    """
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
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

    # Source document transparency (Sprint 6)
    if source_document_title and source_document:
        scope_lines.insert(0, create_leader_dots("Source", f"{source_document_title} ({source_document})"))
    elif source_document_title:
        scope_lines.insert(0, create_leader_dots("Source", source_document_title))
    elif source_document:
        scope_lines.insert(0, create_leader_dots("Source", source_document))

    # Materiality context (Report Quality Improvements)
    if planning_materiality is not None:
        scope_lines.append(create_leader_dots("Planning Materiality", f"${planning_materiality:,.2f}"))
    if performance_materiality is not None:
        scope_lines.append(create_leader_dots("Performance Materiality", f"${performance_materiality:,.2f}"))

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))

    # Materiality qualification note
    if planning_materiality is not None or performance_materiality is not None:
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                "Test thresholds have not been automatically calibrated to materiality; "
                "the auditor should evaluate whether applied thresholds are appropriate "
                "given the above materiality levels.",
                styles["MemoBodySmall"],
            )
        )

    story.append(Spacer(1, 8))


def build_methodology_section(
    story: list,
    styles: dict,
    doc_width: float,
    test_results: list[dict],
    test_descriptions: dict[str, str],
    intro_text: str,
    test_parameters: Optional[dict[str, str]] = None,
    test_assertions: Optional[dict[str, list[str]]] = None,
) -> None:
    """Build the Methodology section (II. Methodology).

    Optionally includes Parameters and Assertions columns when provided.
    """
    story.append(Paragraph("II. Methodology", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))
    story.append(Paragraph(intro_text, styles["MemoBody"]))

    has_params = bool(test_parameters)
    has_assertions = bool(test_assertions)

    # Build header row dynamically
    header = ["Test", "Tier", "Description"]
    if has_params:
        header.append("Parameters")
    if has_assertions:
        header.append("Assertions")

    method_data = [header]
    for tr in test_results:
        key = tr["test_key"]
        desc = test_descriptions.get(key, tr.get("description", ""))
        row: list = [
            Paragraph(tr["test_name"], styles["MemoTableCell"]),
            Paragraph(tr["test_tier"].title(), styles["MemoTableCell"]),
            Paragraph(desc, styles["MemoTableCell"]),
        ]
        if has_params:
            param = test_parameters.get(key, "\u2014") if test_parameters else "\u2014"
            row.append(Paragraph(param, styles["MemoTableCell"]))
        if has_assertions:
            assertion_keys = test_assertions.get(key, []) if test_assertions else []
            abbrevs = ", ".join(ASSERTION_LABELS.get(a, a) for a in assertion_keys) if assertion_keys else "\u2014"
            row.append(Paragraph(abbrevs, styles["MemoTableCell"]))
        method_data.append(row)

    # Column widths adapt to optional columns
    if has_params and has_assertions:
        col_widths = [1.2 * inch, 0.6 * inch, 2.5 * inch, 1.2 * inch, 0.7 * inch]
    elif has_params:
        col_widths = [1.3 * inch, 0.7 * inch, 3.5 * inch, 1.1 * inch]
    elif has_assertions:
        col_widths = [1.3 * inch, 0.7 * inch, 3.7 * inch, 0.9 * inch]
    else:
        col_widths = [1.5 * inch, 0.8 * inch, 4.3 * inch]

    method_table = Table(method_data, colWidths=col_widths, repeatRows=1)
    method_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(method_table)

    # Parameter disclaimer note
    if has_params:
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                "Parameters represent platform defaults. The auditor should evaluate "
                "appropriateness for the specific engagement.",
                styles["MemoBodySmall"],
            )
        )

    story.append(Spacer(1, 8))


def build_results_summary_section(
    story: list,
    styles: dict,
    doc_width: float,
    composite: dict[str, Any],
    test_results: list[dict],
    flagged_label: str = "Total Entries Flagged",
) -> None:
    """Build the Results Summary section (III. Results Summary)."""
    story.append(Paragraph("III. Results Summary", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    risk_tier = composite.get("risk_tier", "low")
    tier_label, _ = RISK_TIER_DISPLAY.get(risk_tier, ("UNKNOWN", ClassicalColors.OBSIDIAN_500))

    story.append(
        Paragraph(
            create_leader_dots("Composite Risk Score", f"{composite.get('score', 0):.1f} / 100"),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Risk Tier", tier_label),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots(flagged_label, f"{composite.get('total_flagged', 0):,}"),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Overall Flag Rate", f"{composite.get('flag_rate', 0):.1%}"),
            styles["MemoLeader"],
        )
    )

    sev = composite.get("flags_by_severity", {})
    story.append(
        Paragraph(
            create_leader_dots("High Severity Flags", str(sev.get("high", 0))),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Medium Severity Flags", str(sev.get("medium", 0))),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Low Severity Flags", str(sev.get("low", 0))),
            styles["MemoLeader"],
        )
    )
    story.append(Spacer(1, 6))

    # Results by test table
    results_data = [["Test", "Flagged", "Rate", "Severity"]]
    for tr in sorted(test_results, key=lambda t: t.get("flag_rate", 0), reverse=True):
        results_data.append(
            [
                tr["test_name"],
                str(tr["entries_flagged"]),
                f"{tr['flag_rate']:.1%}",
                tr["severity"].upper(),
            ]
        )

    results_table = Table(results_data, colWidths=[2.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch], repeatRows=1)
    results_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(results_table)
    story.append(Spacer(1, 8))


def build_workpaper_signoff(
    story: list,
    styles: dict,
    doc_width: float,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    *,
    include_signoff: bool = False,
) -> None:
    """Build the workpaper sign-off section.

    Deprecated by default (Sprint 7): signoff is no longer rendered unless
    ``include_signoff=True`` is explicitly passed.  The prepared_by,
    reviewed_by, and workpaper_date parameters are retained for backward
    compatibility but have no effect when include_signoff is False.
    """
    if not include_signoff:
        return
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
    signoff_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(signoff_table)
    story.append(Spacer(1, 8))


def build_proof_summary_section(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
) -> None:
    """Build the Proof Summary section — compact evidence quality table.

    Inserted between SCOPE and METHODOLOGY in standard memos.
    Extracts data completeness, column confidence, and test coverage
    from the existing tool result dict. No new computation.

    Sprint 392: Phase LIII — Proof Architecture.
    """
    composite = result.get("composite_score", {})
    data_quality = result.get("data_quality", {})
    column_detection = result.get("column_detection", {})

    # Extract metrics with safe defaults
    completeness = data_quality.get("completeness_score", 0)
    col_confidence = column_detection.get("overall_confidence", 0) if column_detection else 0
    tests_run = composite.get("tests_run", 0)
    total_flagged = composite.get("total_flagged", 0)
    tests_clear = max(0, tests_run - (1 if total_flagged > 0 else 0))

    # For standard tools, count tests with zero flags for "clear" count
    test_results = result.get("test_results", [])
    if test_results:
        tests_clear = sum(
            1 for tr in test_results if tr.get("entries_flagged", 0) == 0 and not tr.get("skipped", False)
        )

    story.append(Paragraph("Proof Summary", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    proof_data = [
        ["Metric", "Value"],
        ["Data Completeness", f"{completeness:.0f}%"],
        ["Column Confidence", f"{col_confidence:.0%}" if isinstance(col_confidence, (int, float)) else "N/A"],
        ["Tests Executed", str(tests_run)],
        ["Tests With No Flags", str(tests_clear)],
        ["Items for Review", str(total_flagged)],
    ]

    proof_table = Table(proof_data, colWidths=[3.0 * inch, 3.0 * inch])
    proof_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(proof_table)
    story.append(Spacer(1, 8))


def build_intelligence_stamp(
    story: list,
    styles: dict,
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
) -> None:
    """Build the 'Paciolus Intelligence' stamp between signoff and disclaimer.

    Format: Paciolus Intelligence  |  Generated <date> UTC  |  [client]  |  Period: [period]
    Sprint 409: Phase LVII — Dynamic Intelligence Watermark.
    """
    from datetime import datetime, timezone

    parts = ["Paciolus Intelligence"]
    timestamp = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    parts.append(f"Generated {timestamp}")
    if client_name:
        parts.append(client_name)
    if period_tested:
        parts.append(f"Period: {period_tested}")

    stamp_text = " &nbsp;&bull;&nbsp; ".join(parts)
    story.append(Spacer(1, 6))
    story.append(Paragraph(stamp_text, styles["MemoFooter"]))
    story.append(Spacer(1, 4))


# =============================================================================
# Assertion vocabulary (ISA 315 / PCAOB AS 1105)
# =============================================================================

ASSERTION_LABELS = {
    "existence": "E",
    "occurrence": "O",
    "completeness": "C",
    "valuation": "V",
    "rights_obligations": "R&O",
    "presentation": "P&D",
    "accuracy": "A",
    "cutoff": "Cut",
}

ASSERTION_FULL_NAMES = {
    "existence": "Existence",
    "occurrence": "Occurrence",
    "completeness": "Completeness",
    "valuation": "Valuation & Allocation",
    "rights_obligations": "Rights & Obligations",
    "presentation": "Presentation & Disclosure",
    "accuracy": "Accuracy",
    "cutoff": "Cutoff",
}


# =============================================================================
# New section builders — Report Quality Improvements
# =============================================================================


def build_auditor_conclusion_block(
    story: list,
    styles: dict,
    doc_width: float,
) -> None:
    """Build a blank practitioner assessment block for auditor completion.

    Always rendered (not gated by include_signoff). Closes ISA 230.7 /
    PCAOB AS 1215.6 documentation gap by providing a designated area
    for the engagement team to record their own conclusion.
    """
    story.append(LedgerRule(doc_width))
    story.append(
        Paragraph(
            "Practitioner Assessment",
            styles["MemoSection"],
        )
    )
    story.append(
        Paragraph(
            "The section below is to be completed by the engagement team. "
            "The auditor should document their assessment of the findings above, "
            "including any implications for the audit approach and additional "
            "procedures deemed necessary.",
            styles["MemoBodySmall"],
        )
    )
    story.append(Spacer(1, 6))

    # 4 blank ruled lines for practitioner notes
    blank_rows = [[""] for _ in range(4)]
    blank_table = Table(blank_rows, colWidths=[doc_width])
    blank_table.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(blank_table)
    story.append(Spacer(1, 8))

    # Signature line
    story.append(
        Paragraph(
            "Signature: ________________________&nbsp;&nbsp;&nbsp;&nbsp;"
            "Date: ________________________",
            styles["MemoBodySmall"],
        )
    )
    story.append(Spacer(1, 12))


def build_skipped_tests_section(
    story: list,
    styles: dict,
    doc_width: float,
    test_results: list[dict],
) -> None:
    """Build the 'Tests Not Performed' section for skipped tests.

    Per ISA 230.8(c), documents departures from expected procedures.
    Only renders when at least one test was skipped.
    """
    skipped = [tr for tr in test_results if tr.get("skipped", False)]
    if not skipped:
        return

    story.append(
        Paragraph(
            "Tests Not Performed",
            styles["MemoSection"],
        )
    )
    story.append(LedgerRule(doc_width))
    story.append(
        Paragraph(
            "The following tests were not performed due to data or population constraints. "
            "The engagement team should evaluate whether alternative procedures are warranted.",
            styles["MemoBodySmall"],
        )
    )
    story.append(Spacer(1, 4))

    skip_data = [["Test", "Reason for Omission"]]
    for tr in skipped:
        reason = tr.get("skip_reason", "Data prerequisites not met")
        skip_data.append(
            [
                Paragraph(tr.get("test_name", tr.get("test_key", "")), styles["MemoTableCell"]),
                Paragraph(reason, styles["MemoTableCell"]),
            ]
        )

    skip_table = Table(skip_data, colWidths=[2.2 * inch, 4.4 * inch], repeatRows=1)
    skip_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(skip_table)
    story.append(Spacer(1, 8))


def build_assertion_summary(
    story: list,
    styles: dict,
    doc_width: float,
    test_results: list[dict],
    test_assertions: dict[str, list[str]],
) -> None:
    """Build assertion coverage summary after Results Summary.

    Shows which financial statement assertions were addressed by the
    test battery and how many had findings.
    """
    if not test_assertions:
        return

    # Collect all assertions addressed
    addressed: set[str] = set()
    flagged_assertions: set[str] = set()
    for tr in test_results:
        if tr.get("skipped", False):
            continue
        key = tr.get("test_key", "")
        assertions = test_assertions.get(key, [])
        addressed.update(assertions)
        if tr.get("entries_flagged", 0) > 0:
            flagged_assertions.update(assertions)

    if not addressed:
        return

    clean = addressed - flagged_assertions
    addressed_names = ", ".join(
        sorted(ASSERTION_FULL_NAMES.get(a, a) for a in addressed)
    )
    total_possible = len(ASSERTION_FULL_NAMES)

    story.append(
        Paragraph(
            create_leader_dots(
                "Assertions Addressed",
                f"{addressed_names} ({len(addressed)} of {total_possible})",
            ),
            styles["MemoLeader"],
        )
    )
    if clean:
        clean_names = ", ".join(sorted(ASSERTION_FULL_NAMES.get(a, a) for a in clean))
        story.append(
            Paragraph(
                create_leader_dots("Assertions With No Flags", clean_names),
                styles["MemoLeader"],
            )
        )
    if flagged_assertions:
        flagged_names = ", ".join(
            sorted(ASSERTION_FULL_NAMES.get(a, a) for a in flagged_assertions)
        )
        story.append(
            Paragraph(
                create_leader_dots("Assertions With Findings", flagged_names),
                styles["MemoLeader"],
            )
        )
    story.append(Spacer(1, 6))


def build_structured_findings_table(
    story: list,
    styles: dict,
    doc_width: float,
    findings: list,
    section_label: str,
    performance_materiality: Optional[float] = None,
) -> None:
    """Build a structured findings table replacing plain-text findings.

    Supports both structured dicts (preferred) and plain strings (fallback).
    Structured format: [{account, amount, date, test, severity}, ...]
    """
    if not findings:
        return

    story.append(Paragraph(f"{section_label}. Key Findings", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Check if findings are structured dicts
    is_structured = isinstance(findings[0], dict) and "account" in findings[0]

    if is_structured:
        # Sort by severity (HIGH first), then by amount descending
        severity_order = {"high": 0, "medium": 1, "low": 2}
        sorted_findings = sorted(
            findings,
            key=lambda f: (
                severity_order.get(f.get("severity", "low").lower(), 3),
                -(abs(f.get("amount", 0)) if isinstance(f.get("amount"), (int, float)) else 0),
            ),
        )

        # Cap at 20
        display_findings = sorted_findings[:20]
        truncated = len(sorted_findings) > 20

        find_data = [["#", "Account", "Amount", "Test", "Severity"]]
        aggregate_amount = 0.0
        for i, f in enumerate(display_findings, 1):
            amt = f.get("amount", 0) if isinstance(f.get("amount"), (int, float)) else 0
            aggregate_amount += abs(amt)
            sev = f.get("severity", "low").upper()
            # Severity color
            if sev == "HIGH":
                sev_color = ClassicalColors.CLAY
            elif sev == "MEDIUM":
                sev_color = ClassicalColors.GOLD_INSTITUTIONAL
            else:
                sev_color = ClassicalColors.SAGE

            find_data.append(
                [
                    str(i),
                    Paragraph(str(f.get("account", "")), styles["MemoTableCell"]),
                    f"${abs(amt):,.2f}" if amt else "\u2014",
                    Paragraph(str(f.get("test", "")), styles["MemoTableCell"]),
                    Paragraph(f'<font color="#{sev_color.hexval()[2:]}">{sev}</font>', styles["MemoTableCell"]),
                ]
            )

        find_table = Table(
            find_data,
            colWidths=[0.3 * inch, 2.0 * inch, 1.2 * inch, 2.0 * inch, 0.8 * inch],
            repeatRows=1,
        )
        find_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                ]
            )
        )
        story.append(find_table)

        # Aggregate amount footer
        agg_text = f"Aggregate flagged amount: ${aggregate_amount:,.2f}"
        if performance_materiality and performance_materiality > 0:
            pct = (aggregate_amount / performance_materiality) * 100
            agg_text += f" ({pct:.1f}% of performance materiality)"
        story.append(Spacer(1, 4))
        story.append(Paragraph(agg_text, styles["MemoBodySmall"]))

        if truncated:
            story.append(
                Paragraph(
                    f"Showing 20 of {len(sorted_findings)} total findings. "
                    "See CSV export for the complete listing.",
                    styles["MemoBodySmall"],
                )
            )
    else:
        # Fallback: plain text findings (backwards compatibility)
        for i, finding in enumerate(findings[:5], 1):
            story.append(Paragraph(f"{i}. {finding}", styles["MemoBody"]))

    story.append(Spacer(1, 8))


def build_disclaimer(
    story: list,
    styles: dict,
    domain: str = "testing",
    isa_reference: str = "applicable professional standards",
) -> None:
    """Build the strengthened disclaimer footer (Sprint 101)."""
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            f"This memo documents automated {domain} testing procedures per {isa_reference}. "
            "Results represent data anomalies identified through analytics and are not "
            "conclusions regarding internal control effectiveness, fraud, or material "
            "misstatement risk. The auditor must evaluate each flagged item in the context "
            "of the engagement and perform additional procedures as necessary per professional "
            "standards. This memo does not constitute audit evidence sufficient to support "
            "an opinion without corroborating procedures. "
            "Generated by Paciolus \u2014 Zero-Storage Audit Intelligence.",
            styles["MemoDisclaimer"],
        )
    )
