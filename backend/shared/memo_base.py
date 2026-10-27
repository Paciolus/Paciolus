"""
Shared Testing Memo Base — Sprint 90

Extracted from JE/AP/Payroll testing memo generators.
All three had identical style definitions, risk tier display, and
common section builders (header, scope, results, workpaper, disclaimer).

Each memo generator imports these functions and provides only
domain-specific content (title, test descriptions, conclusion text).
"""

from typing import Any, Optional
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Spacer, Table, TableStyle

from pdf_generator import (
    ClassicalColors,
    DoubleRule,
    LedgerRule,
    _add_or_replace_style,
    create_leader_dots,
    format_classical_date,
)
from shared.report_styles import ledger_table_style
from shared.safe_paragraph import Paragraph

# =============================================================================
# Standard table style (Sprint 527 — consolidated from 3 diagnostic memos)
# =============================================================================


def standard_table_style(
    *,
    right_align_from: int = 1,
    courier_cols: list[int] | None = None,
) -> TableStyle:
    """Build a standard TableStyle for report tables.

    Consolidates the identical ``_standard_table_style()`` helpers that existed
    in ``accrual_completeness_memo``, ``expense_category_memo``, and
    ``population_profile_memo``.

    Args:
        right_align_from: Column index from which all columns are right-aligned.
            Use 99 (or any value beyond the table width) to disable right-alignment.
        courier_cols: Column indices rendered in Courier (monospace) for financial data.
    """
    commands: list = list(ledger_table_style())
    # Right-align columns from specified index onward
    if right_align_from < 99:
        commands.append(("ALIGN", (right_align_from, 0), (-1, -1), "RIGHT"))
    # Courier for financial columns
    for col in courier_cols or []:
        commands.append(("FONTNAME", (col, 1), (col, -1), "Courier"))
        commands.append(("ALIGN", (col, 0), (col, -1), "RIGHT"))
    return TableStyle(commands)


def wrap_table_strings(data: list[list], styles: dict, *, skip_header: bool = True) -> list[list]:
    """Wrap raw string cells in Paragraph objects to enable word-wrapping in PDF tables.

    BUG-003 fix: ReportLab Table cells with raw strings do not word-wrap,
    causing text to overflow column boundaries. Wrapping in Paragraph enables
    proper line breaking within the allocated column width.

    Args:
        data: Table data (list of rows, each a list of cell values).
        styles: Memo styles dict (needs 'MemoTableCell' key).
        skip_header: If True (default), leave the first row (headers) unwrapped.

    Returns:
        New table data with raw strings replaced by Paragraph objects.
    """
    cell_style = styles.get("MemoTableCell") or styles.get("Normal")
    wrapped = []
    for row_idx, row in enumerate(data):
        if skip_header and row_idx == 0:
            wrapped.append(row)
            continue
        wrapped_row = []
        for cell in row:
            if isinstance(cell, str):
                # Sprint 846: table cells carry account names and descriptions from
                # uploaded files — escape fully so they render as text, never markup.
                wrapped_row.append(Paragraph(xml_escape(cell), cell_style))
            else:
                wrapped_row.append(cell)
        wrapped.append(wrapped_row)
    return wrapped


# =============================================================================
# Risk tier display mapping (identical across all 3 memo generators)
# =============================================================================

RISK_TIER_DISPLAY = {
    "low": ("LOW", ClassicalColors.SAGE),
    "moderate": ("MODERATE", ClassicalColors.GOLD_INSTITUTIONAL),
    "elevated": ("ELEVATED", ClassicalColors.GOLD_INSTITUTIONAL),
    "high": ("HIGH", ClassicalColors.CLAY),
}

# Sprint 779: the diagnostic tier label is prominent enough that a practitioner could
# read it as an ISA 315 risk-assessment conclusion. It is not one — it is a function of
# automated flag density. The qualifier is composed into the scale legend so that every
# surface rendering a tier also renders its basis, including surfaces added later.
RISK_TIER_BASIS_NOTE = (
    "Basis: automated flag density, raised where HIGH-severity flags warrant it \u2014 "
    "auditor judgment required per ISA 315. The score, its tiers and those floors are Paciolus conventions, "
    "not measures prescribed by any standard. The diagnostic tier is an indicator, not a risk assessment "
    "or a conclusion on internal control."
)

_RISK_SCORE_SCALE = (
    "Diagnostic Score Scale: 0\u201310 = Low  |  11\u201325 = Moderate  |  26\u201350 = Elevated  |  51\u2013100 = High"
)

# Rendered through ReportLab Paragraph markup, so <br/> is the line break.
RISK_SCALE_LEGEND = f"{_RISK_SCORE_SCALE}<br/>{RISK_TIER_BASIS_NOTE}"

# The engagement-level indicator in anomaly_summary_generator.py is NOT flag density
# alone: _compute_engagement_risk adds int(tools_not_run * 1.5), so an engagement with
# no anomalies at all can still show a higher tier purely from incomplete coverage.
# Saying "basis: flag density" there would misdescribe the number on the page.
RISK_TIER_BASIS_NOTE_ENGAGEMENT = (
    "Basis: automated flag density <b>and</b> tool-coverage completeness \u2014 auditor judgment required "
    "per ISA 315. Tools not yet run add to the score, so an engagement with no anomalies can still "
    "show a higher tier. The indicator is not a risk assessment or a conclusion on internal control."
)


def validate_risk_tier_coverage(known_tiers: set[str]) -> list[str]:
    """Validate that RISK_TIER_DISPLAY contains a label for every known tier key.

    Args:
        known_tiers: Set of risk tier keys that scoring logic can produce.

    Returns:
        List of tier keys missing from RISK_TIER_DISPLAY.  Empty means complete.
    """
    return [tier for tier in sorted(known_tiers) if tier not in RISK_TIER_DISPLAY]


def format_risk_tier_label(composite: dict) -> tuple[str, Any]:
    """Return (label_with_score, color) from a composite score dict.

    BUG-002 fix: labels now include the numeric score so readers can
    distinguish positions within a tier (e.g. "MODERATE (12/100)" vs
    "MODERATE (24/100)").
    """
    risk_tier = str(composite.get("risk_tier", "low")).lower()
    score = composite.get("score", 0)
    base_label, color = RISK_TIER_DISPLAY.get(risk_tier, ("UNKNOWN", ClassicalColors.OBSIDIAN_500))
    tier_label = f"{base_label} ({score:.0f}/100)"
    return tier_label, color


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
            # Sprint 813: without an explicit leading ReportLab uses 12pt, so the
            # subtitle overprinted this 24pt title in every memo that uses it.
            leading=29,
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
        story.append(Paragraph(xml_escape(client_name), styles["MemoSubtitle"]))
    story.append(
        Paragraph(
            f"{format_classical_date()} &nbsp;&bull;&nbsp; {reference}",
            styles["MemoRef"],
        )
    )
    story.append(DoubleRule(doc_width))
    story.append(Spacer(1, 12))


def source_line(
    source_document_title: Optional[str],
    filename: Optional[str],
    *,
    filename_label: str = "Source",
    always: bool = False,
) -> Optional[str]:
    """Leader-dot "Source" line for a memo's scope block (Sprint 813).

    * title and filename → ``Source ... <title> (<filename>)``
    * title only         → ``Source ... <title>``
    * filename only      → ``<filename_label> ... <filename>``

    With neither, returns ``None`` — unless ``always`` is set, in which case
    the filename line is emitted regardless (the diagnostic memos label it
    "Source File" and always print it).
    """
    if source_document_title and filename:
        return create_leader_dots("Source", f"{source_document_title} ({filename})")
    if source_document_title:
        return create_leader_dots("Source", source_document_title)
    if filename or always:
        return create_leader_dots(filename_label, filename or "")
    return None


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
) -> None:
    """Build the Scope section (I. Scope).

    Sprint 6: source_document and source_document_title are optional.
    If title is present, shown as "Source: <title> (<filename>)".
    If title absent but filename present, shown as "Source: <filename>".
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
    source = source_line(source_document_title, source_document)
    if source:
        scope_lines.insert(0, source)

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 8))


def build_methodology_section(
    story: list,
    styles: dict,
    doc_width: float,
    test_results: list[dict],
    test_descriptions: dict[str, str],
    intro_text: str,
) -> None:
    """Build the Methodology section (II. Methodology)."""
    story.append(Paragraph("II. Methodology", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))
    story.append(Paragraph(intro_text, styles["MemoBody"]))

    method_data = [["Test", "Tier", "Description"]]
    for tr in test_results:
        desc = test_descriptions.get(tr["test_key"], tr.get("description", ""))
        method_data.append(
            [
                Paragraph(tr["test_name"], styles["MemoTableCell"]),
                Paragraph(tr["test_tier"].title(), styles["MemoTableCell"]),
                Paragraph(desc, styles["MemoTableCell"]),
            ]
        )

    method_table = Table(method_data, colWidths=[1.5 * inch, 0.8 * inch, 4.3 * inch], repeatRows=1)
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
    story.append(Spacer(1, 8))


def _format_setting_value(value: Any) -> str:
    """Render one saved-setting value for the memo (Sprint 836)."""
    if isinstance(value, bool):
        return "Enabled" if value else "Disabled"
    if isinstance(value, (list, tuple)):
        return ", ".join(_format_setting_value(v) for v in value) or "(none)"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        if isinstance(value, int):
            return f"{value:,}"
        if abs(value) >= 1000:
            return f"{value:,.2f}"
        return f"{value:g}"
    return str(value)


def _setting_label(key: str) -> str:
    return key.replace("_", " ").strip().capitalize()


def _settings_table(values: dict[str, Any], defaults: dict[str, Any], styles: dict) -> Table:
    """Setting / this-run value / Paciolus default table for the disclosure."""
    rows: list[list[Any]] = [["Setting", "This run", "Paciolus default"]]
    for key in sorted(values):
        default_text = _format_setting_value(defaults[key]) if key in defaults else "—"
        rows.append(
            [
                Paragraph(xml_escape(_setting_label(str(key))), styles["MemoTableCell"]),
                Paragraph(xml_escape(_format_setting_value(values[key])), styles["MemoTableCell"]),
                Paragraph(xml_escape(default_text), styles["MemoTableCell"]),
            ]
        )
    table = Table(rows, colWidths=[2.9 * inch, 1.9 * inch, 1.8 * inch], repeatRows=1)
    table.setStyle(
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
    return table


def build_saved_settings_disclosure(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    defaults: Optional[dict[str, Any]] = None,
) -> None:
    """State which thresholds differed from the Paciolus defaults (Sprint 836).

    ``result["settings_applied"]`` maps engine field -> value for every saved
    practice setting that differed from the engine default on this run;
    ``result["settings_ignored"]`` lists saved keys that were not applied.
    When the result carries neither field (an older client) nothing is drawn;
    when it carries an empty ``settings_applied`` the memo says only that no
    threshold differed from the defaults through these settings — never that
    every threshold was a default (PR #229 review).
    ``result["settings_run_overrides"]`` (Sprint 839) maps engine field ->
    value for thresholds supplied for this run only; they are stated first,
    in their own table.
    """
    applied = result.get("settings_applied")
    ignored = result.get("settings_ignored") or []
    # Sprint 839: values the preparer supplied for this run only.
    run_overrides = result.get("settings_run_overrides") or {}
    if applied is None and not ignored and not run_overrides:
        return
    applied = applied or {}
    defaults = defaults or {}

    heading = (
        "Thresholds set for this run and from saved settings"
        if run_overrides
        else "Thresholds that differed from the Paciolus defaults"
    )
    story.append(Paragraph(f"<b>{heading}</b>", styles["MemoBody"]))
    if run_overrides:
        count = len(run_overrides)
        noun = "threshold was" if count == 1 else "thresholds were"
        story.append(
            Paragraph(
                f"{count} {noun} set by the preparer for this run only; these values replace any saved "
                "setting and the Paciolus default.",
                styles["MemoBodySmall"],
            )
        )
        story.append(_settings_table(run_overrides, defaults, styles))
    if not applied and not run_overrides:
        story.append(
            Paragraph(
                "No saved setting (or per-run tolerance, where the tool accepts one) changed a threshold from the "
                "Paciolus default for this run.",
                styles["MemoBodySmall"],
            )
        )
    elif applied:
        count = len(applied)
        noun = "threshold" if count == 1 else "thresholds"
        story.append(
            Paragraph(
                f"{count} {noun} differed from the Paciolus defaults on this run through the preparer's saved "
                "settings. Results above and below reflect these values, not the defaults.",
                styles["MemoBodySmall"],
            )
        )
        story.append(_settings_table(applied, defaults, styles))
    if ignored:
        count = len(ignored)
        noun = "setting was" if count == 1 else "settings were"
        story.append(
            Paragraph(
                f"{count} saved {noun} not applied:",
                styles["MemoBodySmall"],
            )
        )
        for item in ignored:
            key = str(item.get("key", "")) if isinstance(item, dict) else str(item)
            reason = str(item.get("reason", "")) if isinstance(item, dict) else ""
            story.append(
                Paragraph(
                    f"<i>{xml_escape(key)}</i>: {xml_escape(reason)}",
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

    tier_label, _ = format_risk_tier_label(composite)

    story.append(
        Paragraph(
            create_leader_dots("Composite Diagnostic Score", f"{composite.get('score', 0):.1f} / 100"),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Diagnostic Tier", tier_label),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            RISK_SCALE_LEGEND,
            styles["MemoBodySmall"],
        )
    )
    # Sprint 831: every floor that raised the score, so the page explains its own number.
    for reason in composite.get("score_basis") or []:
        story.append(Paragraph(f"<i>{xml_escape(str(reason))}</i>", styles["MemoBodySmall"]))
    story.append(Spacer(1, 2))
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

    # Results by test table — wrap cells in Paragraph for word-wrapping (BUG-003)
    results_data = [
        [
            Paragraph("Test", styles.get("MemoTableHeader", styles.get("MemoBody"))),
            Paragraph("Flagged", styles.get("MemoTableHeader", styles.get("MemoBody"))),
            Paragraph("Rate", styles.get("MemoTableHeader", styles.get("MemoBody"))),
            Paragraph("Severity", styles.get("MemoTableHeader", styles.get("MemoBody"))),
        ]
    ]
    cell_style = styles.get("MemoTableCell", styles.get("MemoBody"))
    for tr in sorted(test_results, key=lambda t: t.get("flag_rate", 0), reverse=True):
        results_data.append(
            [
                Paragraph(tr["test_name"], cell_style),
                Paragraph(str(tr["entries_flagged"]), cell_style),
                Paragraph(f"{tr['flag_rate']:.1%}", cell_style),
                Paragraph(tr["severity"].upper(), cell_style),
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
        ["Tests Clear", str(tests_clear)],
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


def build_disclaimer(
    story: list,
    styles: dict,
    domain: str = "testing",
    isa_reference: str = "applicable professional standards",
) -> None:
    """Build the strengthened disclaimer footer (Sprint 101)."""
    story.append(Spacer(1, 12))
    domain_clause = f"{domain} testing" if not domain.endswith("testing") else domain
    story.append(
        Paragraph(
            f"This memo documents automated {domain_clause} procedures with reference to {isa_reference}. "
            "Results represent data anomalies identified through analytics and are not "
            "conclusions regarding internal control effectiveness, fraud, or material "
            "misstatement risk. The auditor must evaluate each flagged item in the context "
            "of the engagement and perform additional procedures as necessary per professional "
            "standards. This memo does not constitute audit evidence sufficient to support "
            "an opinion without corroborating procedures. "
            # Sprint 835: Paciolus cites authorities; it is not one.
            "Paciolus is not a standard-setter: standards are cited so the reader can consult the source, "
            "and thresholds that no standard sets are Paciolus conventions (see paciolus.com/sources). "
            "Generated by Paciolus \u2014 Zero-Storage Audit Intelligence.",
            styles["MemoDisclaimer"],
        )
    )


def build_limitations_section(
    story: list,
    styles: dict,
    doc_width: float,
) -> None:
    """Build the formal Limitations section on the final page of the report.

    This provides the full institutional-grade limitation statement, replacing
    the abbreviated footer-only disclaimer. The footer retains a short version;
    this section contains the complete statement.

    Fix 10: Upgrade disclaimer language.
    """
    from pdf_generator import LedgerRule

    story.append(Spacer(1, 16))
    story.append(Paragraph("Limitations", styles.get("MemoSection", styles.get("SectionHeader", styles["MemoBody"]))))
    story.append(LedgerRule(doc_width))

    limitation_text = (
        "This report was prepared using Paciolus Diagnostic Intelligence and is intended to "
        "support the professional judgment of the engagement practitioner. The procedures "
        "reflected herein are analytical and diagnostic in nature and do not constitute an "
        "audit, review, compilation, or attestation engagement as defined under AICPA "
        "professional standards or PCAOB auditing standards. Findings and observations "
        "require independent corroboration before conclusions may be drawn."
    )

    story.append(Paragraph(limitation_text, styles.get("MemoBody", styles["MemoBody"])))
    story.append(Spacer(1, 4))

    # Part 3: Practitioner liability boundary
    practitioner_text = (
        "Practitioner information appearing on the cover of this report is provided by the "
        "user and reflects the engagement team responsible for applying professional judgment "
        "to this output. Paciolus does not review, endorse, certify, or assume responsibility "
        "for conclusions drawn by the engagement practitioner. The presence of practitioner "
        "credentials in this report does not constitute a representation by Paciolus regarding "
        "the quality or completeness of any professional engagement."
    )
    story.append(Paragraph(practitioner_text, styles.get("MemoBody", styles["MemoBody"])))
    story.append(Spacer(1, 4))

    zero_storage_text = (
        "Zero-Storage Architecture: All financial data was processed in-memory during this "
        "analysis session and was not persisted to any storage medium. No client financial "
        "data is retained by Paciolus after the analysis session concludes."
    )
    story.append(Paragraph(zero_storage_text, styles.get("MemoBodySmall", styles.get("MemoBody"))))
