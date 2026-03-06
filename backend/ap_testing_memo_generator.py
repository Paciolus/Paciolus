"""
AP Testing Memo PDF Generator (Sprint 76, refactored Sprint 90, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: ISA 240 / ISA 500 / PCAOB AS 2401.
"""

from typing import Any, Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer

from pdf_generator import LedgerRule, create_leader_dots
from shared.drill_down import (
    build_drill_down_table,
    format_currency,
    safe_str_value,
)
from shared.follow_up_procedures import get_follow_up_procedure
from shared.memo_template import TestingMemoConfig, _roman, generate_testing_memo

AP_TEST_DESCRIPTIONS = {
    "exact_duplicate_payments": "Identifies payments with identical vendor, invoice number, amount, and payment date.",
    "missing_critical_fields": "Flags payments missing vendor name, amount, or payment date.",
    "check_number_gaps": "Flags gaps in sequential check numbering that may indicate voided or missing payments.",
    "round_dollar_amounts": "Flags payments at round dollar amounts that may indicate estimates or manipulation.",
    "payment_before_invoice": "Flags payments made before the invoice date, indicating prepayment errors or fraud.",
    "fuzzy_duplicate_payments": "Flags payments to the same vendor with matching amounts on different dates within a window.",
    "invoice_number_reuse": "Flags invoice numbers that appear across multiple vendors, indicating possible fraud.",
    "unusual_payment_amounts": "Uses z-score analysis to identify statistically unusual amounts per vendor.",
    "weekend_payments": "Flags payments processed on weekends, indicating unauthorized or unusual activity.",
    "high_frequency_vendors": "Flags vendors receiving an unusually high number of payments in a single day.",
    "vendor_name_variations": "Flags similar vendor names that may indicate ghost vendors or deliberate misspellings.",
    "just_below_threshold": (
        "Flags payments just below approval thresholds and same-vendor same-day splits. "
        "Default threshold applied — confirm against client AP authorization matrix "
        "before drawing conclusions."
    ),
    "suspicious_descriptions": "Flags payments with descriptions containing fraud indicator keywords.",
}

_AP_CONFIG = TestingMemoConfig(
    title="AP Payment Testing Memo",
    ref_prefix="APT",
    entry_label="Total Payments Tested",
    flagged_label="Total Payments Flagged",
    log_prefix="ap_memo",
    domain="AP payment testing",
    test_descriptions=AP_TEST_DESCRIPTIONS,
    methodology_intro=(
        "The following automated tests were applied to the AP payment register "
        "in accordance with professional auditing standards (ISA 240, ISA 500, PCAOB AS 2401):"
    ),
    risk_assessments={
        "low": (
            "Based on the automated AP payment testing procedures applied, "
            "the AP payment register returned LOW flag density across the automated tests. "
            "No anomalies exceeding the configured thresholds were detected by the automated tests applied."
        ),
        "elevated": (
            "Based on the automated AP payment testing procedures applied, "
            "the AP payment register returned ELEVATED flag density across the automated tests. "
            "Select flagged payments should be reviewed for proper authorization and documentation."
        ),
        "moderate": (
            "Based on the automated AP payment testing procedures applied, "
            "the AP payment register returned MODERATE flag density across the automated tests. "
            "Flagged payments warrant focused review, particularly high-severity findings."
        ),
        "high": (
            "Based on the automated AP payment testing procedures applied, "
            "the AP payment register returned HIGH flag density across the automated tests. "
            "Significant anomalies were detected that require detailed investigation. "
            "The engagement team should evaluate whether additional procedures are appropriate."
        ),
    },
    isa_reference="ISA 240 (Fraud), ISA 500 (Audit Evidence), and PCAOB AS 2401",
    tool_domain="ap_payment_testing",
)


def _build_ap_extra_sections(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    section_counter: int,
) -> int:
    """Build AP-specific drill-down sections (DRILL-02, DRILL-03).

    DRILL-02: High-severity payment detail tables for duplicate_payments,
    payment_before_invoice, just_below_threshold, invoice_reuse.
    DRILL-03: Vendor name variation pairs table.
    """
    test_results = result.get("test_results", [])
    high_sev_tests = [tr for tr in test_results if tr.get("severity") == "high" and tr.get("entries_flagged", 0) > 0]

    has_detail = False

    # DRILL-02: High-severity payment detail
    detail_test_keys = {
        "exact_duplicate_payments",
        "fuzzy_duplicate_payments",
        "payment_before_invoice",
        "just_below_threshold",
        "invoice_number_reuse",
    }
    detail_tests = [tr for tr in high_sev_tests if tr.get("test_key") in detail_test_keys]

    if detail_tests:
        section_label = _roman(section_counter)
        story.append(Paragraph(f"{section_label}. High Severity Payment Detail", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))
        has_detail = True

        for tr in detail_tests:
            test_key = tr.get("test_key", "")
            flagged = tr.get("flagged_entries", [])
            if not flagged:
                continue

            if test_key == "exact_duplicate_payments":
                rows = []
                for fe in flagged:
                    entry = fe.get("entry", {})
                    details = fe.get("details") or {}
                    rows.append(
                        [
                            safe_str_value(entry.get("vendor_name"), "")[:25],
                            safe_str_value(entry.get("invoice_number")),
                            safe_str_value(details.get("payment_1_date", entry.get("payment_date"))),
                            safe_str_value(details.get("payment_2_date", "")),
                            format_currency(entry.get("amount", 0)),
                            safe_str_value(entry.get("check_number")),
                        ]
                    )
                build_drill_down_table(
                    story,
                    styles,
                    doc_width,
                    title=f"Exact Duplicate Payments ({len(flagged)} flagged)",
                    headers=["Vendor", "Invoice #", "Payment 1", "Payment 2", "Amount", "Check #"],
                    rows=rows,
                    total_flagged=len(flagged),
                    col_widths=[1.5 * inch, 0.9 * inch, 0.8 * inch, 0.8 * inch, 0.9 * inch, 0.7 * inch],
                    right_align_cols=[4],
                )
            elif test_key == "payment_before_invoice":
                rows = []
                for fe in flagged:
                    entry = fe.get("entry", {})
                    details = fe.get("details") or {}
                    rows.append(
                        [
                            safe_str_value(entry.get("vendor_name"), "")[:25],
                            safe_str_value(entry.get("invoice_number")),
                            safe_str_value(entry.get("invoice_date")),
                            safe_str_value(entry.get("payment_date")),
                            str(details.get("days_early", "")),
                            format_currency(entry.get("amount", 0)),
                        ]
                    )
                build_drill_down_table(
                    story,
                    styles,
                    doc_width,
                    title=f"Payment Before Invoice ({len(flagged)} flagged)",
                    headers=["Vendor", "Invoice #", "Invoice Date", "Payment Date", "Days Early", "Amount"],
                    rows=rows,
                    total_flagged=len(flagged),
                    col_widths=[1.5 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.7 * inch, 1.0 * inch],
                    right_align_cols=[4, 5],
                )
            elif test_key == "invoice_number_reuse":
                rows = []
                for fe in flagged:
                    entry = fe.get("entry", {})
                    details = fe.get("details") or {}
                    rows.append(
                        [
                            safe_str_value(entry.get("invoice_number")),
                            safe_str_value(details.get("vendor_1_name"), "")[:20],
                            format_currency(details.get("vendor_1_amount", 0)),
                            safe_str_value(details.get("vendor_1_date", "")),
                            safe_str_value(details.get("vendor_2_name"), "")[:20],
                            format_currency(details.get("vendor_2_amount", 0)),
                            safe_str_value(details.get("vendor_2_date", "")),
                        ]
                    )
                build_drill_down_table(
                    story,
                    styles,
                    doc_width,
                    title=f"Invoice Number Reuse ({len(flagged)} flagged)",
                    headers=["Invoice #", "Vendor A", "Amount A", "Date A", "Vendor B", "Amount B", "Date B"],
                    rows=rows,
                    total_flagged=len(flagged),
                    col_widths=[0.7 * inch, 1.2 * inch, 0.8 * inch, 0.7 * inch, 1.2 * inch, 0.8 * inch, 0.7 * inch],
                    right_align_cols=[2, 5],
                )
            elif test_key == "just_below_threshold":
                rows = []
                for fe in flagged:
                    entry = fe.get("entry", {})
                    details = fe.get("details") or {}
                    threshold = details.get("threshold_amount", 10000)
                    amount = entry.get("amount", 0)
                    below = details.get("amount_below_threshold", threshold - amount if threshold else 0)
                    rows.append(
                        [
                            safe_str_value(entry.get("vendor_name"), "")[:25],
                            safe_str_value(entry.get("payment_date")),
                            format_currency(amount),
                            format_currency(threshold),
                            format_currency(below),
                        ]
                    )
                build_drill_down_table(
                    story,
                    styles,
                    doc_width,
                    title=f"Just-Below-Threshold ({len(flagged)} flagged)",
                    headers=["Vendor", "Payment Date", "Amount Paid", "Threshold", "Below By"],
                    rows=rows,
                    total_flagged=len(flagged),
                    col_widths=[1.8 * inch, 0.9 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch],
                    right_align_cols=[2, 3, 4],
                )
            else:
                # Generic high-severity detail table
                rows = []
                for fe in flagged:
                    entry = fe.get("entry", {})
                    rows.append(
                        [
                            safe_str_value(entry.get("vendor_name"), "")[:25],
                            safe_str_value(entry.get("invoice_number")),
                            safe_str_value(entry.get("invoice_date")),
                            safe_str_value(entry.get("payment_date")),
                            format_currency(entry.get("amount", 0)),
                            safe_str_value(entry.get("check_number")),
                        ]
                    )
                build_drill_down_table(
                    story,
                    styles,
                    doc_width,
                    title=f"{tr.get('test_name', test_key)} ({len(flagged)} flagged)",
                    headers=["Vendor", "Invoice #", "Invoice Date", "Payment Date", "Amount", "Check #"],
                    rows=rows,
                    total_flagged=len(flagged),
                    col_widths=[1.5 * inch, 0.9 * inch, 0.8 * inch, 0.8 * inch, 0.9 * inch, 0.7 * inch],
                    right_align_cols=[4],
                )

            # Add suggested procedure below each table
            procedure = get_follow_up_procedure(test_key)
            if procedure:
                from reportlab.platypus import Spacer

                story.append(Paragraph(f"<i>{procedure}</i>", styles["MemoBodySmall"]))
                story.append(Spacer(1, 6))

    # DRILL-03: Vendor name variation pairs
    vendor_var_tests = [
        tr for tr in test_results if tr.get("test_key") == "vendor_name_variations" and tr.get("entries_flagged", 0) > 0
    ]
    if vendor_var_tests:
        flagged = vendor_var_tests[0].get("flagged_entries", [])
        # Deduplicate pairs (each pair generates 2 flagged entries)
        seen_pairs: set[tuple[str, str]] = set()
        rows = []
        for fe in flagged:
            details = fe.get("details") or {}
            name_a = details.get("name_a", "")
            name_b = details.get("name_b", "")
            pair_key = tuple(sorted([name_a, name_b]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            similarity = details.get("similarity", 0)
            total_a = details.get("total_paid_a", 0)
            total_b = details.get("total_paid_b", 0)
            rows.append(
                [
                    safe_str_value(name_a)[:25],
                    safe_str_value(name_b)[:25],
                    f"{similarity:.0%}" if isinstance(similarity, (int, float)) else safe_str_value(similarity),
                    format_currency(total_a),
                    format_currency(total_b),
                ]
            )

        # Sort by combined payment total descending, show top 5
        rows.sort(
            key=lambda r: (
                -(float(r[3].replace("$", "").replace(",", "")) + float(r[4].replace("$", "").replace(",", "")))
            ),
        )
        total_pairs = len(rows)
        display_rows = rows[:5]

        if display_rows:
            if not has_detail:
                section_label = _roman(section_counter)
                story.append(Paragraph(f"{section_label}. Payment Detail Analysis", styles["MemoSection"]))
                story.append(LedgerRule(doc_width))
                has_detail = True

            title_suffix = ", showing top 5 by total payment value" if total_pairs > 5 else ""
            build_drill_down_table(
                story,
                styles,
                doc_width,
                title=f"Vendor Name Variations ({total_pairs} pairs{title_suffix})",
                headers=["Vendor A", "Vendor B", "Similarity", "Total Paid A", "Total Paid B"],
                rows=display_rows,
                total_flagged=total_pairs,
                col_widths=[1.6 * inch, 1.6 * inch, 0.8 * inch, 1.3 * inch, 1.3 * inch],
                right_align_cols=[2, 3, 4],
            )
            procedure = get_follow_up_procedure("vendor_name_variations")
            if procedure:
                from reportlab.platypus import Spacer

                story.append(Paragraph(f"<i>{procedure}</i>", styles["MemoBodySmall"]))
                story.append(Spacer(1, 6))

    if has_detail:
        section_counter += 1

    return section_counter


def _build_ap_scope(
    story: list,
    styles: dict,
    doc_width: float,
    composite: dict[str, Any],
    data_quality: dict[str, Any],
    period_tested: Optional[str],
    *,
    source_document: Optional[str] = None,
    source_document_title: Optional[str] = None,
    dpo_data: Optional[dict[str, Any]] = None,
) -> None:
    """Build AP scope section with optional DPO metric."""
    from shared.memo_base import build_scope_section

    build_scope_section(
        story,
        styles,
        doc_width,
        composite,
        data_quality,
        entry_label="Total Payments Tested",
        period_tested=period_tested,
        source_document=source_document,
        source_document_title=source_document_title,
    )

    # DPO metric (IMPROVEMENT-03)
    if dpo_data and dpo_data.get("dpo") is not None:
        dpo_val = dpo_data["dpo"]
        story.append(
            Paragraph(
                create_leader_dots("Days Payable Outstanding (DPO)", f"{dpo_val:.1f} days"),
                styles["MemoLeader"],
            )
        )
        story.append(
            Paragraph(
                f"<i>A DPO of {dpo_val:.0f} days should be evaluated in the context of "
                f"the entity's industry and vendor payment terms. DPO norms vary significantly "
                f"by sector; confirm the appropriate benchmark for this client.</i>",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 6))
    elif dpo_data and dpo_data.get("unavailable"):
        story.append(
            Paragraph(
                "<i>DPO calculation requires Trial Balance \u2014 upload TB to enable this metric.</i>",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 6))


def generate_ap_testing_memo(
    ap_result: dict[str, Any],
    filename: str = "ap_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    include_signoff: bool = False,
) -> bytes:
    """Generate a PDF testing memo for AP testing results."""
    dpo_data = ap_result.get("dpo_data")

    def _scope_builder(story, styles, doc_width, composite, data_quality, pt):
        _build_ap_scope(
            story,
            styles,
            doc_width,
            composite,
            data_quality,
            pt,
            source_document=filename,
            source_document_title=source_document_title,
            dpo_data=dpo_data,
        )

    return generate_testing_memo(
        ap_result,
        _AP_CONFIG,
        filename=filename,
        client_name=client_name,
        period_tested=period_tested,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        source_document_title=source_document_title,
        source_context_note=source_context_note,
        build_scope=_scope_builder if dpo_data else None,
        build_extra_sections=_build_ap_extra_sections,
        include_signoff=include_signoff,
    )
