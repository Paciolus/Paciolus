"""
AP Testing Memo PDF Generator (Sprint 76, refactored Sprint 90, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: ISA 240 / ISA 500 / PCAOB AS 2401.
"""

from typing import Any, Optional

from shared.memo_template import TestingMemoConfig, generate_testing_memo

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
        include_signoff=include_signoff,
    )
