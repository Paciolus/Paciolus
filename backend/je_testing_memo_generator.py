"""
JE Testing Memo PDF Generator (Sprint 67, refactored Sprint 90, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: PCAOB AS 1215 / ISA 530.

Uses build_extra_sections callback for the JE-specific Benford's Law analysis table.
"""

from typing import Any, Optional

from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle,
)

from pdf_generator import (
    ClassicalColors, LedgerRule, create_leader_dots,
)
from shared.memo_template import (
    TestingMemoConfig, generate_testing_memo, _roman,
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
        "in accordance with professional auditing standards (PCAOB AS 1215, ISA 530):"
    ),
    risk_assessments={
        "low": (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract exhibits a LOW risk profile. "
            "No material anomalies requiring further investigation were identified."
        ),
        "elevated": (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract exhibits an ELEVATED risk profile. "
            "Select flagged entries should be reviewed for proper authorization and documentation."
        ),
        "moderate": (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract exhibits a MODERATE risk profile. "
            "Flagged entries warrant focused review, particularly high-severity findings."
        ),
        "high": (
            "Based on the automated journal entry testing procedures applied, "
            "the General Ledger extract exhibits a HIGH risk profile. "
            "Significant anomalies were identified that require detailed investigation "
            "and may warrant expanded audit procedures."
        ),
    },
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
    story.append(Paragraph(f"{section_label}. BENFORD'S LAW ANALYSIS", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

    story.append(Paragraph(
        create_leader_dots("Eligible Entries", f"{benford.get('eligible_count', 0):,}"),
        styles['MemoLeader'],
    ))
    story.append(Paragraph(
        create_leader_dots("MAD Score", f"{benford.get('mad', 0):.5f}"),
        styles['MemoLeader'],
    ))
    conformity = benford.get("conformity_level", "").replace("_", " ").title()
    story.append(Paragraph(
        create_leader_dots("Conformity Level", conformity),
        styles['MemoLeader'],
    ))
    story.append(Spacer(1, 6))

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
            benford_data.append([
                str(d),
                f"{exp_val:.2%}",
                f"{act_val:.2%}",
                f"{dev_val:+.2%}",
            ])

        benford_table = Table(benford_data, colWidths=[0.8 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
        benford_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(benford_table)
    story.append(Spacer(1, 8))

    return section_counter + 1


def generate_je_testing_memo(
    je_result: dict[str, Any],
    filename: str = "je_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for JE testing results."""
    return generate_testing_memo(
        je_result, _JE_CONFIG,
        filename=filename, client_name=client_name,
        period_tested=period_tested, prepared_by=prepared_by,
        reviewed_by=reviewed_by, workpaper_date=workpaper_date,
        build_extra_sections=_build_benford_section,
    )
