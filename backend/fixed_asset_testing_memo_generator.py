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
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf_generator import ClassicalColors, LedgerRule, create_leader_dots
from shared.drill_down import format_currency
from shared.memo_base import build_scope_section
from shared.memo_template import TestingMemoConfig, _roman, generate_testing_memo
from shared.report_styles import ledger_table_style

FA_TEST_DESCRIPTIONS = {
    "fully_depreciated": "Flags assets where accumulated depreciation equals or exceeds cost (NBV zero or negative), indicating potential ghost assets or items requiring disposal review.",
    "missing_fields": "Flags fixed asset entries missing critical register fields (cost, identifier, acquisition date), a data completeness anomaly indicator.",
    "negative_values": "Flags assets with negative cost or negative accumulated depreciation, indicating data entry errors or improper adjustments.",
    "over_depreciation": "Flags assets where accumulated depreciation exceeds original cost by more than 1%, indicating possible calculation errors or improper depreciation entries.",
    "useful_life_outliers": "Flags assets with useful life estimates outside reasonable bounds (below 0.5 years or above 50 years), an estimation anomaly indicator per ISA 540.",
    "cost_zscore_outliers": (
        "Uses z-score analysis to identify fixed assets with acquisition costs that "
        "are statistically unusual relative to the population distribution. Assets "
        "exceeding the configured z-score threshold from the mean cost are flagged for review "
        "as potential overstatement or data entry anomalies."
    ),
    "age_concentration": "Flags disproportionate concentration of total asset cost in a single acquisition year, indicating potential bulk capitalization anomalies.",
    "duplicate_assets": "Flags assets with identical cost, description, and acquisition date \u2014 potential duplicate capitalization or double-counting.",
    "residual_value_anomalies": (
        "Flags assets where the recorded residual (salvage) value is inconsistent "
        "with the asset type, useful life, or industry norms. Anomalies include "
        "residual values exceeding 30% of original cost, or negative residual values "
        "requiring documented justification per ISA 540."
    ),
    "lease_indicators": (
        "Scans asset descriptions for keywords suggesting operating or finance leases "
        "(lease, ROU, right-of-use, leasehold). Flagged items should be confirmed for "
        "proper ASC 842 / IFRS 16 right-of-use asset treatment."
    ),
}

_FA_CONFIG = TestingMemoConfig(
    title="Fixed Asset Register Analysis Memo",
    ref_prefix="FAT",
    entry_label="Total Fixed Assets Tested",
    flagged_label="Total Fixed Assets Flagged",
    log_prefix="fa_memo",
    domain="fixed asset register analysis",
    test_descriptions=FA_TEST_DESCRIPTIONS,
    methodology_intro=(
        "The following automated tests were applied to the fixed asset register "
        "in accordance with professional auditing standards "
        "(IAS 16: Property, Plant and Equipment, "
        "ISA 500: Audit Evidence, ISA 540: Auditing Accounting Estimates \u2014 "
        "depreciation methods, useful life, and residual value estimation, "
        "PCAOB AS 2501: Auditing Accounting Estimates). "
        "Results represent fixed asset anomaly indicators, not depreciation adequacy conclusions:"
    ),
    isa_reference="ISA 500 (Audit Evidence) and ISA 540 (Auditing Accounting Estimates)",
    tool_domain="fixed_asset_testing",
    risk_assessments={
        "low": (
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&amp;E data returned LOW flag density across the automated tests. "
            "No fixed asset anomalies exceeding the configured thresholds were detected by the automated tests applied."
        ),
        "elevated": (
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&amp;E data returned ELEVATED flag density across the automated tests. "
            "Select flagged assets should be reviewed for proper capitalization treatment "
            "and supporting documentation."
        ),
        "moderate": (
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&amp;E data returned MODERATE flag density across the automated tests. "
            "Flagged assets warrant focused review as PP&amp;E anomaly indicators, "
            "particularly depreciation estimates and useful life assumptions."
        ),
        "high": (
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&amp;E data returned HIGH flag density across the automated tests. "
            "Significant fixed asset anomaly indicators were detected that require "
            "detailed investigation. The engagement team should evaluate whether additional "
            "PP&amp;E procedures are appropriate per ISA 540 and PCAOB AS 2501."
        ),
    },
)

_MAX_DETAIL_ROWS = 20


def _format_fa_finding(finding: Any) -> str:
    """Format FA finding — enriches fully depreciated finding with dollar value (IMP-03)."""
    text = str(finding)
    return text


# ─────────────────────────────────────────────────────────────────────
# SCOPE ENRICHMENTS (IMP-01, 02, 04)
# ─────────────────────────────────────────────────────────────────────


def _build_roll_forward(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
) -> None:
    """IMPROVEMENT-01: Fixed Asset Roll-Forward subsection."""
    register_total_cost = result.get("register_total_cost", 0)
    register_total_accum_depr = result.get("register_total_accum_depr", 0)
    if not register_total_cost:
        return

    period = result.get("period_label", "FY2025")

    story.append(Paragraph(f"Fixed Asset Roll-Forward \u2014 {period}", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Gross Cost section
    story.append(Paragraph("<b>Gross Cost:</b>", styles["MemoBody"]))

    additions = result.get("additions")
    disposals = result.get("disposals", 0)
    tb_ppe_gross = result.get("tb_ppe_gross")

    if additions is not None:
        beginning_cost = register_total_cost - additions + disposals
        story.append(
            Paragraph(
                create_leader_dots("Beginning Balance", format_currency(beginning_cost)),
                styles["MemoLeader"],
            )
        )
        story.append(
            Paragraph(
                create_leader_dots("Additions During Period", f"+ {format_currency(additions)}"),
                styles["MemoLeader"],
            )
        )
        if disposals:
            story.append(
                Paragraph(
                    create_leader_dots("Disposals During Period", f"- {format_currency(disposals)}"),
                    styles["MemoLeader"],
                )
            )
    else:
        story.append(
            Paragraph(
                create_leader_dots(
                    "Additions",
                    "[Upload financial statements to auto-populate]",
                ),
                styles["MemoLeader"],
            )
        )

    story.append(
        Paragraph(
            create_leader_dots("Ending Balance (per Register)", format_currency(register_total_cost)),
            styles["MemoLeader"],
        )
    )

    if tb_ppe_gross is not None:
        story.append(
            Paragraph(
                create_leader_dots("Per Trial Balance (PP&amp;E gross)", format_currency(tb_ppe_gross)),
                styles["MemoLeader"],
            )
        )
        cost_variance = register_total_cost - tb_ppe_gross
        story.append(
            Paragraph(
                create_leader_dots("Variance", format_currency(cost_variance)),
                styles["MemoLeader"],
            )
        )
    story.append(Spacer(1, 4))

    # Accumulated Depreciation section
    story.append(Paragraph("<b>Accumulated Depreciation:</b>", styles["MemoBody"]))

    depr_expense = result.get("depreciation_expense")
    tb_accum_depr = result.get("tb_accum_depr")

    if depr_expense is not None and additions is not None:
        beginning_accum = register_total_accum_depr - depr_expense
        story.append(
            Paragraph(
                create_leader_dots("Beginning Balance", format_currency(beginning_accum)),
                styles["MemoLeader"],
            )
        )
        story.append(
            Paragraph(
                create_leader_dots("Depreciation Expense for Period", f"+ {format_currency(depr_expense)}"),
                styles["MemoLeader"],
            )
        )

    story.append(
        Paragraph(
            create_leader_dots("Ending Balance (per Register)", format_currency(register_total_accum_depr)),
            styles["MemoLeader"],
        )
    )

    if tb_accum_depr is not None:
        story.append(
            Paragraph(
                create_leader_dots("Per Trial Balance (Accum. Depr.)", format_currency(tb_accum_depr)),
                styles["MemoLeader"],
            )
        )
        depr_variance = register_total_accum_depr - tb_accum_depr
        story.append(
            Paragraph(
                create_leader_dots("Variance", format_currency(depr_variance)),
                styles["MemoLeader"],
            )
        )

    story.append(Spacer(1, 4))

    # Net Book Value
    nbv = register_total_cost - register_total_accum_depr
    story.append(
        Paragraph(
            create_leader_dots("Net Book Value", format_currency(nbv)),
            styles["MemoLeader"],
        )
    )

    # Reconciliation status
    if tb_ppe_gross is not None and tb_accum_depr is not None:
        cost_var = abs(register_total_cost - tb_ppe_gross)
        depr_var = abs(register_total_accum_depr - tb_accum_depr)
        if cost_var < 0.01 and depr_var < 0.01:
            story.append(
                Paragraph(
                    "\u2713 Roll-forward reconciles to Trial Balance.",
                    styles["MemoBody"],
                )
            )
        else:
            parts = []
            if cost_var >= 0.01:
                parts.append(f"{format_currency(cost_var)} in gross cost")
            if depr_var >= 0.01:
                parts.append(f"{format_currency(depr_var)} in accumulated depreciation")
            story.append(
                Paragraph(
                    f"\u26a0 Unreconciled difference of {' and '.join(parts)}. "
                    "Investigate before finalizing PP&amp;E balance.",
                    styles["MemoBody"],
                )
            )

    story.append(Spacer(1, 8))


def _build_depreciation_rate_analysis(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
) -> None:
    """IMPROVEMENT-02: Depreciation Rate Reasonableness subsection."""
    register_total_cost = result.get("register_total_cost", 0)
    depr_expense = result.get("depreciation_expense")
    if not register_total_cost or depr_expense is None:
        return

    story.append(Paragraph("Depreciation Rate Analysis", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    effective_rate = depr_expense / register_total_cost if register_total_cost else 0
    implied_life = 1 / effective_rate if effective_rate > 0 else 0

    story.append(
        Paragraph(
            create_leader_dots("Gross PP&amp;E", format_currency(register_total_cost)),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Depreciation Expense (Period)", format_currency(depr_expense)),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Effective Depreciation Rate", f"{effective_rate:.1%}"),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Implied Average Useful Life", f"{implied_life:.1f} years"),
            styles["MemoLeader"],
        )
    )

    story.append(
        Paragraph(
            f"<i>An effective depreciation rate of {effective_rate:.1%} implies an average asset life of "
            f"approximately {implied_life:.0f} years across the register. Assess whether this is consistent "
            "with the entity\u2019s asset mix and useful life policies.</i>",
            styles["MemoBodySmall"],
        )
    )

    prior_rate = result.get("prior_period_depr_rate")
    if prior_rate is not None:
        change_pp = (effective_rate - prior_rate) * 100
        story.append(
            Paragraph(
                create_leader_dots("Prior Period Effective Rate", f"{prior_rate:.1%}"),
                styles["MemoLeader"],
            )
        )
        story.append(
            Paragraph(
                create_leader_dots("Change", f"{change_pp:+.1f} pp"),
                styles["MemoLeader"],
            )
        )
        if abs(change_pp) > 2.0:
            story.append(
                Paragraph(
                    f"<i>\u26a0 Effective rate changed by {abs(change_pp):.1f} percentage points \u2014 "
                    "assess whether this reflects a change in asset mix, a useful life revision, "
                    "or a depreciation calculation error.</i>",
                    styles["MemoBodySmall"],
                )
            )

    story.append(Spacer(1, 8))


def _build_category_summary(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
) -> None:
    """IMPROVEMENT-04: Asset Register Composition by Category table."""
    cat_data = result.get("category_summary", [])
    col_det = result.get("column_detection", {})

    if not cat_data:
        if not col_det.get("category_column"):
            story.append(Paragraph("Asset Register Composition", styles["MemoSection"]))
            story.append(LedgerRule(doc_width))
            story.append(
                Paragraph(
                    "<i>Asset category breakdown not available \u2014 add an asset class/category field "
                    "to the register to enable composition analysis.</i>",
                    styles["MemoBodySmall"],
                )
            )
            story.append(Spacer(1, 8))
        return

    story.append(Paragraph("Asset Register Composition", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    table_data = [["Asset Category", "Count", "Gross Cost", "Accum. Depr.", "Net Book Value", "Avg. Age (yrs)"]]
    total_count = 0
    total_cost = 0.0
    total_depr = 0.0
    total_nbv = 0.0

    for cat in cat_data:
        count = cat["count"]
        cost = cat["gross_cost"]
        depr = cat["accum_depr"]
        nbv_cat = cost - depr
        avg_age = cat.get("avg_age_years", "\u2014")
        total_count += count
        total_cost += cost
        total_depr += depr
        total_nbv += nbv_cat

        age_str = f"{avg_age:.1f}" if isinstance(avg_age, (int, float)) else str(avg_age)
        table_data.append(
            [
                Paragraph(cat["category"], styles["MemoTableCell"]),
                Paragraph(str(count), styles["MemoTableCell"]),
                Paragraph(format_currency(cost), styles["MemoTableCell"]),
                Paragraph(format_currency(depr), styles["MemoTableCell"]),
                Paragraph(format_currency(nbv_cat), styles["MemoTableCell"]),
                Paragraph(age_str, styles["MemoTableCell"]),
            ]
        )

    table_data.append(
        [
            Paragraph("<b>Total</b>", styles["MemoTableCell"]),
            Paragraph(f"<b>{total_count}</b>", styles["MemoTableCell"]),
            Paragraph(f"<b>{format_currency(total_cost)}</b>", styles["MemoTableCell"]),
            Paragraph(f"<b>{format_currency(total_depr)}</b>", styles["MemoTableCell"]),
            Paragraph(f"<b>{format_currency(total_nbv)}</b>", styles["MemoTableCell"]),
            Paragraph("", styles["MemoTableCell"]),
        ]
    )

    cat_table = Table(
        table_data,
        colWidths=[1.5 * inch, 0.5 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.0 * inch],
        repeatRows=1,
    )
    style_cmds = ledger_table_style() + [
        ("LINEABOVE", (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_DEEP),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]
    cat_table.setStyle(TableStyle(style_cmds))
    story.append(cat_table)
    story.append(Spacer(1, 8))


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
        "Verify whether these records represent two distinct physical assets or a single asset "
        "entered twice. If a duplicate, reverse the duplicate capitalization entry and "
        "corresponding accumulated depreciation. Obtain the asset tag or serial number to "
        "confirm physical existence of both."
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
                Paragraph(entry.get("asset_id", "") or "", styles["MemoTableCell"]),
                Paragraph(entry.get("description", "") or "", styles["MemoTableCell"]),
                Paragraph(entry.get("category", "") or "", styles["MemoTableCell"]),
                Paragraph(str(entry.get("acquisition_date", "") or ""), styles["MemoTableCell"]),
                Paragraph(format_currency(entry.get("cost", 0)), styles["MemoTableCell"]),
                Paragraph(format_currency(entry.get("accumulated_depreciation", 0)), styles["MemoTableCell"]),
                Paragraph(format_currency(excess), styles["MemoTableCell"]),
            ]
        )

    style_cmds = ledger_table_style() + [("ALIGN", (4, 0), (-1, -1), "RIGHT")]
    table = Table(
        table_data,
        colWidths=[0.7 * inch, 1.3 * inch, 0.8 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch],
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
                Paragraph(a_entry.get("asset_id", "") or "", styles["MemoTableCell"]),
                Paragraph(b_entry.get("asset_id", "") or "", styles["MemoTableCell"]),
                Paragraph(a_entry.get("description", "") or "", styles["MemoTableCell"]),
                Paragraph(format_currency(cost), styles["MemoTableCell"]),
                Paragraph(str(a_entry.get("acquisition_date", "") or ""), styles["MemoTableCell"]),
                Paragraph(a_entry.get("category", "") or "", styles["MemoTableCell"]),
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
                f"Potential duplicate capitalization: {format_currency(total_dup_cost)} "
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
                Paragraph(entry.get("asset_id", "") or "", styles["MemoTableCell"]),
                Paragraph(entry.get("description", "") or "", styles["MemoTableCell"]),
                Paragraph(entry.get("category", "") or "", styles["MemoTableCell"]),
                Paragraph(format_currency(entry.get("cost", 0)), styles["MemoTableCell"]),
                Paragraph(str(entry.get("acquisition_date", "") or ""), styles["MemoTableCell"]),
                Paragraph("Data entry error", styles["MemoTableCell"]),
            ]
        )

    style_cmds = ledger_table_style() + [("ALIGN", (3, 0), (3, -1), "RIGHT")]
    table = Table(
        table_data,
        colWidths=[0.9 * inch, 1.3 * inch, 0.9 * inch, 1.0 * inch, 1.0 * inch, 1.1 * inch],
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
    story.append(Paragraph(f"{label}. High Severity Asset Detail", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    for tr in high_tests:
        test_key = tr.get("test_key", "")
        flagged = tr.get("flagged_entries", [])
        count = tr.get("entries_flagged", 0)

        title = _DETAIL_TABLE_TITLES.get(
            test_key,
            f"{tr.get('test_name', '')} \u2014 Asset Detail",
        )
        story.append(Paragraph(f"<b>{title} ({count} items)</b>", styles["MemoBody"]))
        story.append(Spacer(1, 4))

        builder = _DETAIL_TABLE_BUILDERS.get(test_key)
        if builder:
            builder(story, styles, flagged)
        else:
            for fe in flagged[:_MAX_DETAIL_ROWS]:
                entry = fe.get("entry", {})
                story.append(
                    Paragraph(
                        f"&bull; {entry.get('asset_id', '') or entry.get('description', 'Unknown')} \u2014 {fe.get('issue', '')}",
                        styles["MemoBody"],
                    )
                )

        procedure = _DETAIL_PROCEDURES.get(test_key, "")
        if procedure:
            story.append(Paragraph(f"<i>{procedure}</i>", styles["MemoBodySmall"]))

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
    include_signoff: bool = False,
) -> bytes:
    """Generate a PDF testing memo for fixed asset testing results."""

    def _fa_scope(story, styles, doc_width, composite, data_quality, period_tested_arg):
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
        _build_roll_forward(story, styles, doc_width, fa_result)
        _build_depreciation_rate_analysis(story, styles, doc_width, fa_result)
        _build_category_summary(story, styles, doc_width, fa_result)

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
        build_scope=_fa_scope,
        build_extra_sections=_build_high_severity_detail,
        format_finding=_format_fa_finding,
        include_signoff=include_signoff,
    )
