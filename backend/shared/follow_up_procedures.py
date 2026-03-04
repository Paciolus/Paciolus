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
    "unbalanced_entries": "Obtain and inspect the original journal entry documentation for proper approval and investigate the source of the imbalance.",
    "missing_fields": "Request the complete GL extract with all required fields populated; trace missing entries to source documents.",
    "duplicate_entries": "Inspect the original entries to determine whether they represent valid transactions or require reversal.",
    "round_dollar_amounts": "Verify round-dollar entries against supporting documentation (invoices, contracts) to confirm amounts are not estimates.",
    "unusual_amounts": "Investigate unusual amounts by obtaining supporting documentation and comparing to prior period activity for the same account.",
    "benford_law": "Evaluate the most deviated digits for patterns of manual entry or estimation; consider targeted sampling of entries starting with those digits.",
    "weekend_postings": "Verify weekend-posted entries were authorized and have valid business justification; review system access logs.",
    "month_end_clustering": "Evaluate whether month-end entries represent normal closing activity or potential earnings management.",
    "holiday_postings": "Investigate entries posted on holidays for proper authorization; review system access logs for the posting date.",
    # AP Testing
    "exact_duplicate_payments": "Trace both payments to supporting invoices and confirm whether one should be reversed or recovered.",
    "fuzzy_duplicate_payments": "Compare payment details to determine if similar payments represent distinct transactions or potential duplicates.",
    "payment_before_invoice": "Obtain the invoice and verify the actual receipt date; investigate whether the payment was properly authorized.",
    "just_below_threshold": "Review same-vendor same-day payments for potential split-payment circumvention of approval controls.",
    "invoice_number_reuse": "Trace the invoice number across vendors to determine if invoices are legitimate or potentially fraudulent.",
    "vendor_name_variations": "Verify vendor master data for similar names; investigate whether they represent the same or related entities.",
    "suspicious_descriptions": "Review the flagged transaction descriptions and obtain supporting documentation.",
    "high_frequency_vendors": "Analyze high-frequency vendor payments for proper authorization and business justification.",
    "check_number_gaps": "Investigate missing check numbers for voided or cancelled checks; verify proper documentation exists.",
    "round_dollar_amounts_ap": "Verify round-amount payments against supporting invoices to confirm they are not estimates.",
    "unusual_payment_amounts": "Obtain supporting documentation for statistically unusual payment amounts.",
    "weekend_payments": "Verify weekend-processed payments were authorized; review system access logs.",
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


def get_follow_up_procedure(test_key: str) -> str:
    """Get the suggested follow-up procedure for a test key.

    Returns empty string if no procedure is defined for the key.
    """
    return FOLLOW_UP_PROCEDURES.get(test_key, "")
