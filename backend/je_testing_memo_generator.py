"""
JE Testing Memo PDF Generator (Sprint 67, refactored Sprint 90, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: PCAOB AS 2401 / ISA 240.

Uses build_extra_sections callback for the JE-specific Benford's Law analysis table.
"""

from collections import Counter
from typing import Any, Optional

from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from pdf_generator import (
    ClassicalColors,
    LedgerRule,
    create_leader_dots,
)
from shared.drill_down import (
    build_drill_down_table,
    format_currency,
    safe_str_value,
)
from shared.follow_up_procedures import get_follow_up_procedure
from shared.memo_template import (
    TestingMemoConfig,
    _roman,
    generate_testing_memo,
)

TEST_DESCRIPTIONS = {
    "unbalanced_entries": "Identifies journal entries where total debits do not equal total credits.",
    "missing_fields": "Flags entries missing critical fields (account, date, or amount).",
    "duplicate_entries": "Detects entries with identical account, date, and amount combinations.",
    "round_dollar_amounts": "Flags entries with suspiciously round dollar amounts ($10K+).",
    "unusual_amounts": "Uses z-score analysis to identify statistically unusual amounts per account.",
    "benford_law": "Tests first-digit distribution against Benford's Law expected frequencies.",
    "weekend_postings": "Flags entries posted on Saturdays or Sundays, weighted by amount.",
    "month_end_clustering": "Detects unusual concentration of entries in last 3 days of month.",
    "holiday_postings": "Flags entries posted on US federal holidays (ISA 240 journal entry fraud risk indicator).",
}

_JE_CONFIG = TestingMemoConfig(
    title="Journal Entry Testing Memo",
    ref_prefix="JET",
    entry_label="Total Journal Entries Tested",
    flagged_label="Total Entries Flagged",
    log_prefix="je_memo",
    domain="journal entry testing",
    test_descriptions=TEST_DESCRIPTIONS,
    methodology_intro=(
        "The following automated tests were applied to the General Ledger extract "
        "in accordance with professional auditing standards "
        "(PCAOB AS 2401: Consideration of Fraud in a Financial Statement Audit, "
        "ISA 240: The Auditor's Responsibilities Relating to Fraud):"
    ),
    risk_assessments={
        "low": (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract returned LOW flag density across the automated tests. "
            "No anomalies exceeding the configured thresholds were detected by the automated tests applied."
        ),
        "elevated": (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract returned ELEVATED flag density across the automated tests. "
            "Select flagged entries should be reviewed for proper authorization and documentation."
        ),
        "moderate": (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract returned MODERATE flag density across the automated tests. "
            "Flagged entries warrant focused review, particularly high-severity findings."
        ),
        "high": (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract returned HIGH flag density across the automated tests. "
            "Significant anomalies were detected that require detailed investigation. "
            "The engagement team should evaluate whether additional procedures are appropriate."
        ),
    },
    isa_reference="PCAOB AS 2401 (Fraud) and ISA 240 (Fraud)",
    tool_domain="journal_entry_testing",
)


def _build_benford_section(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    section_counter: int,
) -> int:
    """Build the JE-specific Benford's Law Analysis section.

    Returns the updated section_counter (incremented if section was added).
    """
    benford = result.get("benford_result")
    if not benford or not benford.get("passed_prechecks"):
        return section_counter

    section_label = _roman(section_counter)
    story.append(Paragraph(f"{section_label}. Benford's Law Analysis", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    story.append(
        Paragraph(
            create_leader_dots("Eligible Entries", f"{benford.get('eligible_count', 0):,}"),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("MAD Score", f"{benford.get('mad', 0):.5f}"),
            styles["MemoLeader"],
        )
    )
    conformity = benford.get("conformity_level", "").replace("_", " ").title()
    story.append(
        Paragraph(
            create_leader_dots("Conformity Level", conformity),
            styles["MemoLeader"],
        )
    )
    story.append(Spacer(1, 6))

    # Positive conformity interpretation (IMPROVEMENT-02)
    mad_val = benford.get("mad", 0)
    if mad_val < 0.006:
        story.append(
            Paragraph(
                f"<i>First-digit distribution closely conforms to Benford's Law "
                f"(MAD = {mad_val:.5f}, below the Close Conformity threshold of 0.006). "
                f"This is one indicator the engagement team may consider alongside other "
                f"procedures when evaluating the population.</i>",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 4))

    expected = benford.get("expected_distribution", {})
    actual = benford.get("actual_distribution", {})
    deviation = benford.get("deviation_by_digit", {})

    if expected and actual:
        benford_data = [["Digit", "Expected", "Actual", "Deviation"]]
        for d in range(1, 10):
            key = str(d)
            exp_val = expected.get(key, 0)
            act_val = actual.get(key, 0)
            dev_val = deviation.get(key, 0)
            benford_data.append(
                [
                    str(d),
                    f"{exp_val:.3%}",
                    f"{act_val:.3%}",
                    f"{dev_val:+.3%}",
                ]
            )

        benford_table = Table(benford_data, colWidths=[0.8 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
        benford_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Courier"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(benford_table)
    story.append(Spacer(1, 8))

    return section_counter + 1


def _build_high_severity_detail(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    section_counter: int,
) -> int:
    """Build detail tables for high-severity flagged entries (DRILL-01).

    Shows entry-level detail for unbalanced entries, holiday postings, and
    other high-severity tests where drill-down aids investigation.
    """
    test_results = result.get("test_results", [])
    high_sev_tests = [
        tr
        for tr in test_results
        if tr.get("severity") == "high" and tr.get("entries_flagged", 0) > 0 and tr.get("flagged_entries")
    ]
    if not high_sev_tests:
        return section_counter

    section_label = _roman(section_counter)
    story.append(Paragraph(f"{section_label}. High Severity Entry Detail", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    for tr in high_sev_tests:
        test_key = tr.get("test_key", "")
        flagged = tr.get("flagged_entries", [])
        if not flagged:
            continue

        if test_key == "unbalanced_entries":
            rows = []
            for fe in flagged:
                entry = fe.get("entry", {})
                details = fe.get("details") or {}
                rows.append(
                    [
                        safe_str_value(entry.get("entry_id")),
                        safe_str_value(entry.get("entry_date")),
                        safe_str_value(entry.get("account")),
                        format_currency(entry.get("debit", 0)),
                        format_currency(entry.get("credit", 0)),
                        format_currency(details.get("difference", entry.get("debit", 0) - entry.get("credit", 0))),
                        safe_str_value(entry.get("description"), "")[:40],
                    ]
                )
            build_drill_down_table(
                story,
                styles,
                doc_width,
                title=f"Unbalanced Entries ({len(flagged)} flagged)",
                headers=["JE #", "Date", "Account", "Debit", "Credit", "Difference", "Description"],
                rows=rows,
                total_flagged=len(flagged),
                col_widths=[0.7 * inch, 0.7 * inch, 1.2 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 1.6 * inch],
                right_align_cols=[3, 4, 5],
            )
            procedure = get_follow_up_procedure("unbalanced_entries", rotation_index=1)
            if procedure:
                story.append(Paragraph(f"<i>{procedure}</i>", styles["MemoBodySmall"]))
                story.append(Spacer(1, 6))
        elif test_key == "holiday_postings":
            rows = []
            for fe in flagged:
                entry = fe.get("entry", {})
                details = fe.get("details") or {}
                amt = max(entry.get("debit", 0), entry.get("credit", 0))
                rows.append(
                    [
                        safe_str_value(entry.get("entry_id")),
                        safe_str_value(entry.get("entry_date")),
                        safe_str_value(entry.get("account")),
                        format_currency(amt),
                        safe_str_value(details.get("holiday"), ""),
                        safe_str_value(entry.get("description"), "")[:30],
                        safe_str_value(entry.get("posted_by"), ""),
                    ]
                )
            build_drill_down_table(
                story,
                styles,
                doc_width,
                title=f"Holiday Postings ({len(flagged)} flagged)",
                headers=["JE #", "Date", "Account", "Amount", "Holiday", "Description", "Posted By"],
                rows=rows,
                total_flagged=len(flagged),
                col_widths=[0.6 * inch, 0.7 * inch, 1.0 * inch, 0.8 * inch, 1.0 * inch, 1.2 * inch, 1.3 * inch],
                right_align_cols=[3],
            )
            procedure = get_follow_up_procedure("holiday_postings", rotation_index=1)
            if procedure:
                story.append(Paragraph(f"<i>{procedure}</i>", styles["MemoBodySmall"]))
                story.append(Spacer(1, 6))
        else:
            # Generic high-severity detail table
            rows = []
            for fe in flagged:
                entry = fe.get("entry", {})
                amt = max(entry.get("debit", 0), entry.get("credit", 0))
                rows.append(
                    [
                        safe_str_value(entry.get("entry_id")),
                        safe_str_value(entry.get("entry_date")),
                        safe_str_value(entry.get("account")),
                        format_currency(amt),
                        safe_str_value(fe.get("issue"), "")[:50],
                    ]
                )
            build_drill_down_table(
                story,
                styles,
                doc_width,
                title=f"{tr.get('test_name', test_key)} ({len(flagged)} flagged)",
                headers=["JE #", "Date", "Account", "Amount", "Issue"],
                rows=rows,
                total_flagged=len(flagged),
                col_widths=[0.7 * inch, 0.7 * inch, 1.2 * inch, 0.9 * inch, 3.1 * inch],
                right_align_cols=[3],
            )

    return section_counter + 1


def _build_preparer_analysis(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    section_counter: int,
) -> int:
    """Build Preparer Concentration analysis section (DRILL-06).

    Only rendered if >60% of flagged entries have a posted_by value.
    Shows top 5 preparers by flagged entry count.
    """
    test_results = result.get("test_results", [])
    total_entries = result.get("composite_score", {}).get("total_entries", 0)

    # Collect all flagged entries with preparer info
    preparer_flagged: Counter[str] = Counter()
    preparer_total: Counter[str] = Counter()
    total_flagged_with_preparer = 0
    total_flagged_count = 0

    for tr in test_results:
        for fe in tr.get("flagged_entries", []):
            total_flagged_count += 1
            posted_by = (fe.get("entry") or {}).get("posted_by")
            if posted_by:
                total_flagged_with_preparer += 1
                preparer_flagged[posted_by] += 1

    # Only render if >60% of flagged entries have preparer info
    if total_flagged_count == 0 or total_flagged_with_preparer / total_flagged_count < 0.6:
        return section_counter

    section_label = _roman(section_counter)
    story.append(Paragraph(f"{section_label}. Preparer Concentration Analysis", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    story.append(
        Paragraph(
            f"{total_flagged_with_preparer} of {total_flagged_count} flagged entries "
            f"({total_flagged_with_preparer / total_flagged_count:.0%}) include preparer identification. "
            "The following table shows the top preparers by flagged entry count:",
            styles["MemoBody"],
        )
    )
    story.append(Spacer(1, 4))

    top_preparers = preparer_flagged.most_common(5)
    rows = []
    for name, flagged_count in top_preparers:
        flag_rate = flagged_count / total_flagged_with_preparer if total_flagged_with_preparer > 0 else 0
        rows.append(
            [
                name,
                str(flagged_count),
                f"{flag_rate:.1%}",
            ]
        )

    build_drill_down_table(
        story,
        styles,
        doc_width,
        title="",
        headers=["Preparer", "Flagged Entries", "% of Flagged"],
        rows=rows,
        col_widths=[3.0 * inch, 1.5 * inch, 2.1 * inch],
        right_align_cols=[1, 2],
    )

    return section_counter + 1


def _build_je_extra_sections(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    section_counter: int,
) -> int:
    """Chain all JE extra sections: high-severity detail, Benford, preparer."""
    section_counter = _build_high_severity_detail(story, styles, doc_width, result, section_counter)
    section_counter = _build_benford_section(story, styles, doc_width, result, section_counter)
    section_counter = _build_preparer_analysis(story, styles, doc_width, result, section_counter)
    return section_counter


def generate_je_testing_memo(
    je_result: dict[str, Any],
    filename: str = "je_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    fiscal_year_end: Optional[str] = None,
    include_signoff: bool = False,
) -> bytes:
    """Generate a PDF testing memo for JE testing results."""
    return generate_testing_memo(
        je_result,
        _JE_CONFIG,
        filename=filename,
        client_name=client_name,
        period_tested=period_tested,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        source_document_title=source_document_title,
        source_context_note=source_context_note,
        fiscal_year_end=fiscal_year_end,
        build_extra_sections=_build_je_extra_sections,
        include_signoff=include_signoff,
    )
