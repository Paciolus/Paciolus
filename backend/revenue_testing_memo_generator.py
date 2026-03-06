"""
Revenue Testing Memo PDF Generator (Sprint 105, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: ISA 240 / ISA 500 / PCAOB AS 2401 — presumed fraud risk in revenue recognition.
"""

from collections import Counter
from typing import Any, Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer

from pdf_generator import LedgerRule
from shared.drill_down import (
    build_drill_down_table,
    format_currency,
    safe_str_value,
)
from shared.memo_template import TestingMemoConfig, _roman, generate_testing_memo

REVENUE_TEST_DESCRIPTIONS = {
    "large_manual_entries": "Flags manual revenue entries exceeding performance materiality threshold (ISA 240 fraud risk indicator).",
    "year_end_concentration": "Flags revenue concentrated in the last days of the period, a common revenue recognition anomaly indicator.",
    "round_revenue_amounts": "Flags revenue entries at round dollar amounts that may indicate estimates or adjustments.",
    "sign_anomalies": "Flags debit balances in revenue accounts (normally credit), indicating potential mispostings.",
    "unclassified_entries": "Flags revenue entries missing account classification (unmapped to chart of accounts).",
    "zscore_outliers": "Uses z-score analysis to identify statistically unusual revenue amounts.",
    "trend_variance": "Flags significant period-over-period revenue changes that may indicate revenue recognition anomalies.",
    "concentration_risk": "Flags single accounts representing a disproportionate share of total revenue.",
    "cutoff_risk": "Flags revenue entries near period boundaries that may indicate cut-off anomalies.",
    "benford_law": "Applies Benford's Law first-digit analysis to revenue transaction amounts.",
    "duplicate_entries": "Flags revenue entries with identical amount, date, and account — potential duplicate postings.",
    "contra_revenue_anomalies": "Flags elevated returns/allowances relative to gross revenue, a fraud risk indicator.",
    # Contract-aware tests (ASC 606 / IFRS 15 — Sprint 352)
    "recognition_before_satisfaction": "Flags revenue recognized before the obligation satisfaction date — risk indicator for premature recognition per ASC 606-10-25-30 / IFRS 15.38.",
    "missing_obligation_linkage": "Flags entries with incomplete performance obligation linkage — risk indicator for incomplete ASC 606 Step 2 disaggregation / IFRS 15.22.",
    "modification_treatment_mismatch": "Flags contracts with inconsistent modification treatment types — risk indicator for ASC 606-10-25-13 / IFRS 15.18-21 non-compliance.",
    "allocation_inconsistency": "Flags contracts with inconsistent standalone selling price allocation bases — risk indicator for ASC 606-10-32-33 / IFRS 15.73-80 non-compliance.",
}

_REVENUE_CONFIG = TestingMemoConfig(
    title="Revenue Recognition Testing Memo",
    ref_prefix="RVT",
    entry_label="Total Revenue Entries Tested",
    flagged_label="Total Revenue Entries Flagged",
    log_prefix="revenue_memo",
    domain="revenue recognition testing",
    test_descriptions=REVENUE_TEST_DESCRIPTIONS,
    methodology_intro=(
        "The following automated tests were applied to the revenue GL extract "
        "in accordance with professional auditing standards "
        "(ISA 240: Auditor's Responsibilities Relating to Fraud \u2014 "
        "presumed fraud risk in revenue recognition, "
        "ISA 500: Audit Evidence, PCAOB AS 2401: Consideration of Fraud). "
        "Where contract data columns were detected, additional contract-aware tests "
        "were applied per ASC 606 / IFRS 15 revenue recognition standards. "
        "Results represent revenue anomaly indicators, not fraud detection conclusions:"
    ),
    isa_reference="ISA 240 (presumed fraud risk in revenue recognition) and ISA 500",
    tool_domain="revenue_testing",
    risk_assessments={
        "low": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract returned LOW flag density across the automated tests. "
            "No revenue recognition anomalies exceeding the configured thresholds were detected by the automated tests applied."
        ),
        "elevated": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract returned ELEVATED flag density across the automated tests. "
            "Select flagged entries should be reviewed for proper revenue recognition treatment "
            "and supporting documentation."
        ),
        "moderate": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract returned MODERATE flag density across the automated tests. "
            "Flagged entries warrant focused review as revenue recognition anomaly indicators, "
            "particularly year-end concentration and cut-off items."
        ),
        "high": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract returned HIGH flag density across the automated tests. "
            "Significant revenue recognition anomaly indicators were detected that require "
            "detailed investigation. The engagement team should evaluate whether additional "
            "revenue procedures are appropriate per ISA 240 and PCAOB AS 2401."
        ),
    },
)


def _build_revenue_extra_sections(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    section_counter: int,
) -> int:
    """Build revenue-specific drill-down sections (DRILL-04, DRILL-06).

    DRILL-04: Cut-off risk entry detail with days from period boundary.
    DRILL-06: Preparer concentration analysis.
    """
    test_results = result.get("test_results", [])
    has_detail = False

    # DRILL-04: Cut-off risk detail
    cutoff_tests = [
        tr for tr in test_results if tr.get("test_key") == "cutoff_risk" and tr.get("entries_flagged", 0) > 0
    ]
    if cutoff_tests:
        flagged = cutoff_tests[0].get("flagged_entries", [])
        rows = []
        for fe in flagged:
            entry = fe.get("entry", {})
            details = fe.get("details") or {}
            # Compute days from boundary if not already present
            days_from = details.get("days_from_boundary")
            if days_from is None:
                entry_date_str = details.get("entry_date") or entry.get("date")
                period_end_str = details.get("period_end")
                if entry_date_str and period_end_str:
                    try:
                        from datetime import datetime

                        ed = datetime.strptime(str(entry_date_str)[:10], "%Y-%m-%d")
                        pe = datetime.strptime(str(period_end_str)[:10], "%Y-%m-%d")
                        days_from = abs((ed - pe).days)
                    except (ValueError, TypeError):
                        days_from = None

            rows.append(
                [
                    safe_str_value(entry.get("reference")),
                    safe_str_value(entry.get("date")),
                    str(days_from) if days_from is not None else "—",
                    safe_str_value(entry.get("account_name"), "")[:20],
                    format_currency(entry.get("amount", 0)),
                    safe_str_value(entry.get("description"), "")[:30],
                ]
            )

        if rows:
            if not has_detail:
                section_label = _roman(section_counter)
                story.append(Paragraph(f"{section_label}. Revenue Detail Analysis", styles["MemoSection"]))
                story.append(LedgerRule(doc_width))
                has_detail = True

            build_drill_down_table(
                story,
                styles,
                doc_width,
                title=f"Cut-Off Risk Entries ({len(flagged)} flagged)",
                headers=["Reference", "Date", "Days From Period End", "Account", "Amount", "Description"],
                rows=rows,
                total_flagged=len(flagged),
                col_widths=[0.8 * inch, 0.7 * inch, 1.0 * inch, 1.2 * inch, 0.9 * inch, 2.0 * inch],
                right_align_cols=[2, 4],
            )

    # DRILL-06: Preparer concentration
    preparer_flagged: Counter[str] = Counter()
    total_flagged_with_preparer = 0
    total_flagged_count = 0

    for tr in test_results:
        for fe in tr.get("flagged_entries", []):
            total_flagged_count += 1
            posted_by = (fe.get("entry") or {}).get("posted_by")
            if posted_by:
                total_flagged_with_preparer += 1
                preparer_flagged[posted_by] += 1

    if total_flagged_count > 0 and total_flagged_with_preparer / total_flagged_count >= 0.6:
        if not has_detail:
            section_label = _roman(section_counter)
            story.append(Paragraph(f"{section_label}. Revenue Detail Analysis", styles["MemoSection"]))
            story.append(LedgerRule(doc_width))
            has_detail = True

        story.append(
            Paragraph(
                f"{total_flagged_with_preparer} of {total_flagged_count} flagged entries "
                f"({total_flagged_with_preparer / total_flagged_count:.0%}) include preparer identification:",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 4))

        rows = []
        for name, flagged_count in preparer_flagged.most_common(5):
            flag_rate = flagged_count / total_flagged_with_preparer if total_flagged_with_preparer > 0 else 0
            rows.append([name, str(flagged_count), f"{flag_rate:.1%}"])

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

    if has_detail:
        section_counter += 1

    return section_counter


def generate_revenue_testing_memo(
    revenue_result: dict[str, Any],
    filename: str = "revenue_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    include_signoff: bool = False,
) -> bytes:
    """Generate a PDF testing memo for revenue testing results."""
    return generate_testing_memo(
        revenue_result,
        _REVENUE_CONFIG,
        filename=filename,
        client_name=client_name,
        period_tested=period_tested,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        source_document_title=source_document_title,
        source_context_note=source_context_note,
        build_extra_sections=_build_revenue_extra_sections,
        include_signoff=include_signoff,
    )
