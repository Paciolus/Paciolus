"""
Follow-Up Procedure Suggestions

Maps test_key identifiers to suggested follow-up audit procedures.
Used by memo generators to provide actionable next steps for each
flagged finding. These are suggestions, not requirements — the auditor
must exercise professional judgment per ISA 330.

ENHANCE-01: Suggested Follow-Up Procedures.
"""

FOLLOW_UP_PROCEDURES: dict[str, str] = {
    # JE Testing
    "unbalanced_entries": (
        "Obtain preparer explanation for each unbalanced entry. Confirm whether the "
        "difference represents a rounding policy or requires a correcting journal entry. "
        "Document resolution in the engagement file."
    ),
    "missing_fields": (
        "Request the complete GL extract with all required fields populated. Trace "
        "affected entries to source documents to confirm the transactions are complete "
        "and properly recorded."
    ),
    "duplicate_entries": (
        "Inspect each duplicate entry pair and confirm whether the duplication "
        "represents a legitimate correction, a system posting error, or a potentially "
        "fraudulent duplicate transaction."
    ),
    "round_dollar_amounts": (
        "Verify round-dollar entries against supporting documentation (invoices, "
        "contracts) to confirm amounts are not estimates or placeholders."
    ),
    "unusual_amounts": (
        "Obtain supporting documentation for statistically unusual amounts. Confirm "
        "that amounts reflect actual invoiced or contracted values and were not "
        "manually estimated."
    ),
    "benford_law": (
        "Evaluate the most deviated digits for patterns of manual entry or estimation; "
        "consider targeted sampling of entries starting with those digits."
    ),
    "weekend_postings": (
        "Verify weekend-posted entries were authorized and have valid business "
        "justification. Review system access logs if available to confirm posting "
        "was performed by an authorized user."
    ),
    "month_end_clustering": (
        "Evaluate whether month-end entries represent normal closing activity or "
        "potential earnings management. Inquire of management regarding the business "
        "rationale for the concentration and perform corroborating procedures on "
        "material month-end entries."
    ),
    "holiday_postings": (
        "For each holiday posting, obtain documentation supporting business necessity "
        "and confirm the entry received proper authorization and supervisory review per "
        "the client's journal entry policy (ISA 240.A40)."
    ),
    # AP Testing
    "exact_duplicate_payments": (
        "Pull original invoices and payment documentation for both duplicate payments. "
        "Confirm whether the duplicate was identified and recovered. If not recovered, "
        "request vendor credit or initiate recovery process. Document resolution."
    ),
    "fuzzy_duplicate_payments": (
        "Inspect each fuzzy duplicate pair for business justification. Confirm whether "
        "the same-vendor same-amount payments on different dates represent recurring "
        "legitimate charges or potential duplicate disbursements."
    ),
    "payment_before_invoice": (
        "Obtain management explanation for each prepayment. Confirm whether a prepayment "
        "arrangement was authorized per AP policy and supported by a contract or purchase "
        "order. Payments lacking authorization documentation represent a potential control "
        "failure under ISA 240."
    ),
    "just_below_threshold": (
        "Obtain approval documentation for each payment. Compare the approval threshold "
        "in the current AP policy to the threshold applied in the payment system. "
        "Determine whether the clustering of payments just below threshold on the same "
        "dates represents intentional threshold avoidance."
    ),
    "invoice_number_reuse": (
        "Obtain both invoices sharing the reused number. Confirm whether the vendors "
        "are the same entity operating under different names, or distinct entities. "
        "If distinct, investigate how the same invoice number was accepted by the AP "
        "system for two different vendors."
    ),
    "vendor_name_variations": (
        "Obtain vendor master records for each flagged pair. Confirm whether similar "
        "vendor names represent the same entity, a legitimate subsidiary, or a potential "
        "ghost vendor. Verify address, tax ID, and bank account details for each."
    ),
    "missing_critical_fields": (
        "Request the complete AP register with all required fields populated for the "
        "affected payments. Trace to source documents to confirm transactions are "
        "complete and properly recorded."
    ),
    "suspicious_descriptions": (
        "Inspect each payment flagged for suspicious description keywords. Obtain "
        "supporting documentation and management explanation. Escalate any payments "
        "lacking adequate support per ISA 240 fraud risk procedures."
    ),
    "high_frequency_vendors": (
        "Obtain detail of all payments to the flagged vendor(s) on the high-frequency "
        "date. Confirm each payment is supported by a distinct invoice and there is no "
        "duplication or splitting of a single invoice across multiple payments."
    ),
    "check_number_gaps": (
        "Investigate gaps in check sequence. Obtain voided check documentation for "
        "missing numbers. Confirm proper authorization and recording of any voided "
        "instruments."
    ),
    "round_dollar_amounts_ap": (
        "Verify round-amount payments against supporting invoices to confirm they are not estimates or placeholders."
    ),
    "unusual_payment_amounts": (
        "Obtain supporting documentation for statistically unusual payment amounts. "
        "Confirm amounts reflect actual invoiced values and are supported by approved "
        "purchase orders or contracts."
    ),
    "weekend_payments": (
        "Verify weekend-processed payments were authorized and have valid business "
        "justification. Review system access logs to confirm payments were processed "
        "by an authorized user outside normal business hours."
    ),
    # Revenue Testing
    "large_manual_entries": "Inspect supporting documentation (contracts, delivery evidence) for large manual revenue entries.",
    "year_end_concentration": "Evaluate whether year-end revenue concentrations reflect genuine business activity or potential acceleration.",
    "cutoff_risk": "Inspect shipping/delivery documentation to confirm revenue was recognized in the correct period.",
    "concentration_risk": "Evaluate customer/account concentration for credit risk and going concern implications.",
    "sign_anomalies": "Investigate debit balances in revenue accounts for mispostings or contra-revenue issues.",
    "trend_variance": "Obtain management explanations for significant period-over-period revenue changes.",
    "benford_law_revenue": "Review most deviated digits in revenue amounts for manual estimation patterns.",
    "duplicate_entries_revenue": "Inspect potential duplicate revenue entries for proper posting.",
    "contra_revenue_anomalies": "Analyze elevated returns/allowances for underlying causes; review customer complaint trends.",
    # AR Aging
    "ar_sign_anomalies": "Investigate credit balances in AR for overpayments, misclassifications, or needed reclassification.",
    "missing_allowance": "Evaluate the need for an allowance for doubtful accounts per IFRS 9 / ASC 326.",
    "past_due_concentration": "Review past-due accounts for collection activity and assess recoverability.",
    "customer_concentration": "Evaluate credit risk concentration; consider expanded confirmation procedures.",
    "credit_limit_breaches": "Review customers exceeding credit limits for continued creditworthiness and collection outlook.",
    "dso_trend": "Investigate DSO increases for changes in collection efficiency or customer payment behavior.",
    "allowance_adequacy": "Perform independent estimate of allowance adequacy using historical loss rates.",
    # Fixed Assets
    "fully_depreciated": "Evaluate whether fully depreciated assets still in use require revised useful life estimates.",
    "over_depreciation": "Investigate over-depreciation for calculation errors or improper adjustments.",
    "useful_life_outliers": "Review unusual useful life estimates against industry norms and management justification.",
    "duplicate_assets": "Verify whether duplicate records represent distinct assets or data entry errors.",
    # Inventory
    "slow_moving": "Evaluate slow-moving items for obsolescence indicators and potential NRV write-down.",
    "negative_values": "Investigate negative quantities/values for returns processing, data errors, or adjustments.",
    "value_mismatch": "Recalculate extended values and investigate discrepancies with source pricing data.",
    "zero_value_items": "Evaluate items with quantity but zero value for potential write-down or pricing gaps.",
    # Payroll
    "PR-T4": "Verify post-termination payments for proper authorization; investigate for potential ghost employees.",
    "PR-T9": "Investigate ghost employee indicators by tracing to HR records and physical verification.",
    "PR-T10": "Verify employees sharing bank accounts or addresses for proper documentation and business justification.",
    "PR-T11": "Investigate shared tax IDs for data entry errors or potential identity fraud.",
    # Bank Reconciliation
    "stale_deposits": "Investigate deposits outstanding more than 10 days for recording delays or potential misstatements.",
    "stale_checks": "Review checks outstanding more than 90 days for stale-dated items requiring write-off or investigation.",
    "nsf_items": "Trace NSF/returned items to subsequent collection or write-off; assess credit risk.",
    "high_value_transactions": "Obtain supporting documentation for transactions exceeding materiality threshold.",
}


FINDING_BENCHMARKS: dict[str, str] = {
    "month_end_clustering": (
        "A clustering rate above 8% in the final 3 business days of the month "
        "warrants inquiry into whether entries represent legitimate closing activity "
        "or potential period-end earnings management (ISA 240)."
    ),
}


def get_follow_up_procedure(test_key: str) -> str:
    """Get the suggested follow-up procedure for a test key.

    Returns empty string if no procedure is defined for the key.
    """
    return FOLLOW_UP_PROCEDURES.get(test_key, "")


def get_finding_benchmark(test_key: str) -> str:
    """Get benchmark context text for a finding, if available.

    Returns empty string if no benchmark is defined for the key.
    """
    return FINDING_BENCHMARKS.get(test_key, "")
