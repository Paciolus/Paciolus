"""
Fixed Asset Testing Memo PDF Generator (Sprint 115, simplified Sprint 157,
enriched Sprint 502)

Config-driven wrapper around shared memo template.
Domain: IAS 16 / ISA 500 / ISA 540 / PCAOB AS 2501.

Sprint 502: Added high-severity detail tables (BUG-03), roll-forward (IMP-01),
depreciation rate analysis (IMP-02), fully depreciated dollar value (IMP-03),
category summary (IMP-04), lease indicator (BUG-04), PP&E ampersand fix (BUG-01).
"""

from typing import Any, Optional

from reportlab.lib.units import inch
from reportlab.platypus import Spacer, Table, TableStyle

from pdf import LedgerRule
from shared.drill_down import format_currency
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import build_scope_section
from shared.memo_template import TestingMemoConfig, _roman, generate_testing_memo
from shared.report_styles import ledger_table_style
from shared.safe_paragraph import Paragraph, user_text

FA_TEST_DESCRIPTIONS = {
    "fully_depreciated": "Flags assets where accumulated depreciation equals or exceeds cost (NBV zero or negative), indicating potential ghost assets or items requiring disposal review.",
    "missing_fields": "Flags fixed asset entries missing critical register fields (cost, identifier, acquisition date), a data completeness anomaly indicator.",
    "negative_values": "Flags assets with negative cost or negative accumulated depreciation, indicating data entry errors or improper adjustments.",
    "over_depreciation": "Flags assets where accumulated depreciation exceeds original cost by more than 1%, indicating possible calculation errors or improper depreciation entries.",
    "useful_life_outliers": "Flags assets with useful life estimates outside 0.5–50 years (Paciolus default bounds, configurable). Useful life is an accounting estimate (ISA 540); the bounds themselves are a Paciolus convention, not set by ISA 540.",
    "cost_zscore_outliers": (
        "Uses z-score analysis to identify fixed assets with acquisition costs that "
        "are statistically unusual relative to the population distribution. Assets "
        "exceeding the configured z-score threshold from the mean cost are flagged for review "
        "as potential overstatement or data entry anomalies."
    ),
    "age_concentration": "Flags disproportionate concentration of total asset cost in a single acquisition year, indicating potential bulk capitalization anomalies.",
    "duplicate_assets": "Flags assets with identical cost, description, and acquisition date \u2014 potential duplicate capitalization or double-counting.",
    "residual_value_anomalies": (
        "Flags assets whose recorded residual (salvage) value exceeds 30% of original "
        "cost (a Paciolus default, configurable), or is negative. Residual value is an "
        "accounting estimate (ISA 540); the 30% bound is a Paciolus convention, not set by ISA 540."
    ),
    "lease_indicators": (
        "Scans asset descriptions for keywords suggesting operating or finance leases "
        "(lease, ROU, right-of-use, leasehold). Flagged items should be confirmed for "
        "proper ASC 842 / IFRS 16 right-of-use asset treatment."
    ),
    "depreciation_recalc": (
        "Sprint 682: Recalculates expected depreciation from cost, residual value, "
        "useful life, and depreciation method. Flags variance >5% (straight-line) "
        "or >15% (double-declining balance) from expected accumulated depreciation "
        "per IAS 16 / ASC 360."
    ),
}

_FA_CONFIG = TestingMemoConfig(
    title="Fixed Asset Register Analysis Memo",
    ref_prefix="FAT",
    entry_label="Total Fixed Assets Tested",
    flagged_label="Fixed Assets Flagged (distinct assets)",
    flag_unit="asset",
    log_prefix="fa_memo",
    domain="fixed asset register analysis",
    test_descriptions=FA_TEST_DESCRIPTIONS,
    methodology_intro=(
        "The following automated tests were applied to the fixed asset register "
        "with reference to professional auditing standards "
        "(ASC 360-10: Property, Plant, and Equipment, "
        "ISA 500: Audit Evidence, ISA 540: Auditing Accounting Estimates \u2014 "
        "depreciation methods, useful life, and residual value estimation, "
        "PCAOB AS 2501: Auditing Accounting Estimates). "
        "Results represent fixed asset anomaly indicators, not depreciation adequacy conclusions:"
    ),
    isa_reference="ISA 500 (Audit Evidence) and ISA 540 (Auditing Accounting Estimates)",
    tool_domain="fixed_asset_testing",
)

_MAX_DETAIL_ROWS = 20


def _format_fa_finding(finding: Any) -> str:
    """Format FA finding — enriches fully depreciated finding with dollar value (IMP-03)."""
    text = str(finding)
    return text


# Sprint 886: the roll-forward, depreciation-rate and category-composition
# sections were removed. They read register totals, additions, disposals, TB
# PP&E, depreciation expense, a prior-period rate, a category summary and a
# period label that the fixed-asset engine never computes (the export model
# dropped them too), so they printed only in the sample memo — with an "FY2025"
# fallback label. The tool has no data for them.

# ─────────────────────────────────────────────────────────────────────
# HIGH SEVERITY DETAIL TABLES (BUG-03)
# ─────────────────────────────────────────────────────────────────────

_DETAIL_PROCEDURES = {
    "over_depreciation": (
        "Investigate each asset for calculation errors or improper "
        "depreciation journal entries. Confirm whether excess depreciation was authorized "
        "and whether a correcting entry is required. Assets with accumulated depreciation "
        "materially exceeding cost may require write-off and removal from the register."
    ),
    "duplicate_assets": (
        "Evaluate whether these records represent two distinct physical assets or a single asset "
        "entered twice. If the practitioner concludes it is a duplicate, reverse the duplicate "
        "capitalization entry and corresponding accumulated depreciation. Obtaining the asset "
        "tag or serial number to corroborate the existence of both is a suggested procedure "
        "where engagement risk warrants."
    ),
    "negative_values": (
        "Obtain the original capitalization documentation for this asset. Correct the cost to "
        "the actual acquisition amount and assess whether accumulated depreciation and the "
        "depreciation expense for the period require corresponding correction."
    ),
}

_DETAIL_TABLE_TITLES = {
    "over_depreciation": "Depreciation Exceeds Cost \u2014 Asset Detail",
    "duplicate_assets": "Duplicate Assets \u2014 Asset Detail",
    "negative_values": "Negative Cost \u2014 Asset Detail",
}


def _build_over_depreciation_table(
    story: list,
    styles: dict,
    flagged_entries: list[dict],
) -> None:
    """Render Depreciation Exceeds Cost detail table."""
    table_data = [
        ["Asset ID", "Description", "Category", "Acquisition Date", "Original Cost", "Accum. Depr.", "Excess Amount"]
    ]

    # Sort by excess amount descending
    sorted_entries = sorted(
        flagged_entries,
        key=lambda fe: fe.get("details", {}).get("excess", 0),
        reverse=True,
    )

    for fe in sorted_entries[:_MAX_DETAIL_ROWS]:
        entry = fe.get("entry", {})
        details = fe.get("details", {})
        excess = details.get("excess", 0)
        table_data.append(
            [
                Paragraph(user_text(entry.get("asset_id", "") or ""), styles["MemoTableCell"]),
                Paragraph(user_text(entry.get("description", "") or ""), styles["MemoTableCell"]),
                Paragraph(user_text(entry.get("category", "") or ""), styles["MemoTableCell"]),
                Paragraph(str(entry.get("acquisition_date", "") or ""), styles["MemoTableCell"]),
                Paragraph(format_currency(entry.get("cost", 0)), styles["MemoTableCell"]),
                Paragraph(format_currency(entry.get("accumulated_depreciation", 0)), styles["MemoTableCell"]),
                Paragraph(format_currency(excess), styles["MemoTableCell"]),
            ]
        )

    style_cmds = ledger_table_style() + [("ALIGN", (4, 0), (-1, -1), "RIGHT")]
    table = Table(
        table_data,
        colWidths=[0.6 * inch, 1.5 * inch, 0.7 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch],
        repeatRows=1,
    )
    table.setStyle(TableStyle(style_cmds))
    story.append(table)


def _build_duplicate_assets_table(
    story: list,
    styles: dict,
    flagged_entries: list[dict],
) -> None:
    """Render Duplicate Assets detail table."""
    # Group duplicates into pairs by description+cost+date
    groups: dict[str, list[dict]] = {}
    for fe in flagged_entries:
        entry = fe.get("entry", {})
        details = fe.get("details", {})
        desc = details.get("description", entry.get("description", ""))
        key = f"{desc}|{details.get('cost', entry.get('cost', 0))}|{details.get('acquisition_date', '')}"
        groups.setdefault(key, []).append(fe)

    table_data = [["Asset ID A", "Asset ID B", "Description", "Cost", "Acquisition Date", "Category"]]
    total_dup_cost = 0.0

    for group in groups.values():
        if len(group) < 2:
            continue
        a_entry = group[0].get("entry", {})
        b_entry = group[1].get("entry", {})
        cost = abs(a_entry.get("cost", 0))
        total_dup_cost += cost

        table_data.append(
            [
                Paragraph(user_text(a_entry.get("asset_id", "") or ""), styles["MemoTableCell"]),
                Paragraph(user_text(b_entry.get("asset_id", "") or ""), styles["MemoTableCell"]),
                Paragraph(user_text(a_entry.get("description", "") or ""), styles["MemoTableCell"]),
                Paragraph(format_currency(cost), styles["MemoTableCell"]),
                Paragraph(str(a_entry.get("acquisition_date", "") or ""), styles["MemoTableCell"]),
                Paragraph(user_text(a_entry.get("category", "") or ""), styles["MemoTableCell"]),
            ]
        )

    style_cmds = ledger_table_style() + [("ALIGN", (3, 0), (3, -1), "RIGHT")]
    table = Table(
        table_data,
        colWidths=[0.9 * inch, 0.9 * inch, 1.5 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch],
        repeatRows=1,
    )
    table.setStyle(TableStyle(style_cmds))
    story.append(table)

    if total_dup_cost > 0:
        story.append(
            Paragraph(
                f"Potential duplicate capitalization: {user_text(format_currency(total_dup_cost))} "
                "(if confirmed duplicate, one record requires reversal)",
                styles["MemoBody"],
            )
        )


def _build_negative_cost_table(
    story: list,
    styles: dict,
    flagged_entries: list[dict],
) -> None:
    """Render Negative Cost detail table."""
    table_data = [["Asset ID", "Description", "Category", "Recorded Cost", "Acquisition Date", "Likely Cause"]]

    for fe in flagged_entries[:_MAX_DETAIL_ROWS]:
        entry = fe.get("entry", {})
        table_data.append(
            [
                Paragraph(user_text(entry.get("asset_id", "") or ""), styles["MemoTableCell"]),
                Paragraph(user_text(entry.get("description", "") or ""), styles["MemoTableCell"]),
                Paragraph(user_text(entry.get("category", "") or ""), styles["MemoTableCell"]),
                Paragraph(format_currency(entry.get("cost", 0)), styles["MemoTableCell"]),
                Paragraph(str(entry.get("acquisition_date", "") or ""), styles["MemoTableCell"]),
                Paragraph("Data entry error", styles["MemoTableCell"]),
            ]
        )

    style_cmds = ledger_table_style() + [("ALIGN", (3, 0), (3, -1), "RIGHT")]
    table = Table(
        table_data,
        colWidths=[0.8 * inch, 1.5 * inch, 0.9 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch],
        repeatRows=1,
    )
    table.setStyle(TableStyle(style_cmds))
    story.append(table)


_DETAIL_TABLE_BUILDERS = {
    "over_depreciation": _build_over_depreciation_table,
    "duplicate_assets": _build_duplicate_assets_table,
    "negative_values": _build_negative_cost_table,
}


def _build_high_severity_detail(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    section_counter: int,
) -> int:
    """BUG-03: Build High Severity Asset Detail section."""
    test_results = result.get("test_results", [])

    high_tests = [
        tr
        for tr in test_results
        if tr.get("severity") == "high" and tr.get("entries_flagged", 0) > 0 and tr.get("flagged_entries")
    ]

    if not high_tests:
        return section_counter

    label = _roman(section_counter)
    story.append(Paragraph(f"{user_text(label)}. High Severity Asset Detail", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    for tr in high_tests:
        test_key = tr.get("test_key", "")
        flagged = tr.get("flagged_entries", [])
        count = tr.get("entries_flagged", 0)

        title = _DETAIL_TABLE_TITLES.get(
            test_key,
            f"{tr.get('test_name', '')} \u2014 Asset Detail",
        )
        story.append(Paragraph(f"<b>{user_text(title)} ({user_text(count)} items)</b>", styles["MemoBody"]))
        story.append(Spacer(1, 4))

        if not flagged:
            # BUG-007: entries_flagged > 0 but flagged_entries not populated
            story.append(
                Paragraph(
                    f"<i>No entry-level detail available for: {user_text(title)}</i>",
                    styles["MemoBodySmall"],
                )
            )
        else:
            builder = _DETAIL_TABLE_BUILDERS.get(test_key)
            if builder:
                builder(story, styles, flagged)
            else:
                # BUG-007 fix: generic detail table for tests without a dedicated builder
                gen_data = [
                    [
                        Paragraph("Asset ID", styles["MemoTableHeader"]),
                        Paragraph("Description", styles["MemoTableHeader"]),
                        Paragraph("Issue", styles["MemoTableHeader"]),
                        Paragraph("Amount", styles["MemoTableHeader"]),
                    ]
                ]
                for fe in flagged[:_MAX_DETAIL_ROWS]:
                    entry = fe.get("entry", {})
                    details = fe.get("details", {})
                    amt = entry.get("cost") or entry.get("amount") or details.get("amount", "")
                    amt_str = format_currency(amt) if isinstance(amt, (int, float)) else str(amt)
                    gen_data.append(
                        [
                            Paragraph(str(entry.get("asset_id", "") or ""), styles["MemoTableCell"]),
                            Paragraph(
                                str(entry.get("description", "") or entry.get("category", "") or ""),
                                styles["MemoTableCell"],
                            ),
                            Paragraph(user_text(str(fe.get("issue", ""))), styles["MemoTableCell"]),
                            Paragraph(amt_str, styles["MemoTableCell"]),
                        ]
                    )
                gen_table = Table(
                    gen_data,
                    colWidths=[1.0 * inch, 1.8 * inch, 2.2 * inch, 1.0 * inch],
                    repeatRows=1,
                )
                gen_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (3, 0), (3, -1), "RIGHT")]))
                story.append(gen_table)

        procedure = _DETAIL_PROCEDURES.get(test_key, "")
        if procedure:
            story.append(Paragraph(f"<i>{user_text(procedure)}</i>", styles["MemoBodySmall"]))

        story.append(Spacer(1, 8))

    return section_counter + 1


# ─────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────


def generate_fixed_asset_testing_memo(
    fa_result: dict[str, Any],
    filename: str = "fixed_asset_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    fiscal_year_end: Optional[str] = None,
    resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
    include_signoff: bool = False,
) -> bytes:
    """Generate a PDF testing memo for fixed asset testing results."""

    def _fa_scope(
        story: Any, styles: Any, doc_width: Any, composite: Any, data_quality: Any, period_tested_arg: Any
    ) -> None:
        build_scope_section(
            story,
            styles,
            doc_width,
            composite,
            data_quality,
            entry_label="Total Fixed Assets Tested",
            period_tested=period_tested_arg,
            source_document=filename,
            source_document_title=source_document_title,
        )

    return generate_testing_memo(
        fa_result,
        _FA_CONFIG,
        filename=filename,
        client_name=client_name,
        period_tested=period_tested,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        source_document_title=source_document_title,
        source_context_note=source_context_note,
        fiscal_year_end=fiscal_year_end,
        build_scope=_fa_scope,
        build_extra_sections=_build_high_severity_detail,
        format_finding=_format_fa_finding,
        resolved_framework=resolved_framework,  # Sprint 886 (OUT-18)
        include_signoff=include_signoff,
    )
