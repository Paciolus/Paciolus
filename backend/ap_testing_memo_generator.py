"""
AP Testing Memo PDF Generator (Sprint 76, refactored Sprint 90, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: ISA 240 / ISA 500 / PCAOB AS 2401.
"""

from typing import Any, Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph

from pdf_generator import LedgerRule
from shared.drill_down import (
    build_drill_down_table,
    format_currency,
    safe_str_value,
)
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
    "just_below_threshold": "Flags payments just below approval thresholds and same-vendor same-day splits.",
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
            "the AP payment register exhibits a LOW risk profile. "
            "No material anomalies requiring further investigation were identified."
        ),
        "elevated": (
            "Based on the automated AP payment testing procedures applied, "
            "the AP payment register exhibits an ELEVATED risk profile. "
            "Select flagged payments should be reviewed for proper authorization and documentation."
        ),
        "moderate": (
            "Based on the automated AP payment testing procedures applied, "
            "the AP payment register exhibits a MODERATE risk profile. "
            "Flagged payments warrant focused review, particularly high-severity findings."
        ),
        "high": (
            "Based on the automated AP payment testing procedures applied, "
            "the AP payment register exhibits a HIGH risk profile. "
            "Significant anomalies were identified that require detailed investigation "
            "and may warrant expanded audit procedures."
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
            combined = details.get("combined_amount", 0)
            rows.append(
                [
                    safe_str_value(name_a)[:25],
                    safe_str_value(name_b)[:25],
                    f"{similarity:.0%}" if isinstance(similarity, (int, float)) else safe_str_value(similarity),
                    format_currency(combined),
                ]
            )

        if rows:
            if not has_detail:
                section_label = _roman(section_counter)
                story.append(Paragraph(f"{section_label}. Payment Detail Analysis", styles["MemoSection"]))
                story.append(LedgerRule(doc_width))
                has_detail = True

            build_drill_down_table(
                story,
                styles,
                doc_width,
                title=f"Vendor Name Variations ({len(rows)} pairs)",
                headers=["Vendor A", "Vendor B", "Similarity", "Combined Payments"],
                rows=rows,
                total_flagged=len(rows),
                col_widths=[2.0 * inch, 2.0 * inch, 0.9 * inch, 1.7 * inch],
                right_align_cols=[2, 3],
            )

    if has_detail:
        section_counter += 1

    return section_counter


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
        build_extra_sections=_build_ap_extra_sections,
        include_signoff=include_signoff,
    )
