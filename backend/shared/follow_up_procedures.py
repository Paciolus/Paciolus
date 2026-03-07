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
        "the client's journal entry policy (ISA 240 journal entry fraud risk indicator)."
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
        "order. The absence of authorization documentation may indicate a control gap "
        "that the engagement team should consider as part of their professional assessment of the AP control environment."
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
    "large_manual_entries": (
        "Obtain preparer identification and approval documentation for each large "
        "manual revenue entry. Confirm entries were reviewed by a supervisor and "
        "supported by a contract or binding commitment per ISA 240."
    ),
    "year_end_concentration": (
        "Evaluate whether December revenue concentration reflects genuine business "
        "activity (e.g., seasonal contracts, milestone completions) or potential "
        "period-end earnings management. Obtain delivery or acceptance documentation "
        "for material December entries."
    ),
    "cutoff_risk": (
        "For each flagged entry, inspect the underlying contract or delivery "
        "documentation. Confirm that the performance obligation under ASC 606-10-25-23 "
        "was satisfied prior to the period end. Entries lacking supporting evidence "
        "of satisfaction before period end should be assessed for potential deferral to "
        "the subsequent period."
    ),
    "concentration_risk": (
        "Assess single-customer concentration for both revenue recognition and "
        "credit risk implications. Obtain the master contract with this customer. "
        "Evaluate whether concentration represents a going concern or business "
        "continuity risk requiring disclosure under ASC 275-10."
    ),
    "sign_anomalies": (
        "Investigate debit balances in revenue accounts. Confirm whether each debit "
        "represents a legitimate return, allowance, or contra-revenue entry, or a "
        "misposting that requires correction. Obtain supporting documentation for each."
    ),
    "trend_variance": (
        "Obtain management explanations for significant period-over-period revenue "
        "changes. Corroborate explanations with supporting documentation and assess "
        "whether variances indicate revenue recognition anomalies."
    ),
    "benford_law_revenue": "Review most deviated digits in revenue amounts for manual estimation patterns.",
    "duplicate_entries_revenue": "Inspect potential duplicate revenue entries for proper posting.",
    "contra_revenue_anomalies": (
        "Calculate the contra-revenue ratio (returns and allowances / gross revenue). "
        "Compare to prior period. Obtain detail of returns and allowances and assess "
        "whether elevated levels indicate channel stuffing reversal or aggressive "
        "prior-period recognition."
    ),
    # Revenue Testing — Contract-Aware (ASC 606 / IFRS 15)
    "recognition_before_satisfaction": (
        "Obtain contract documentation for each flagged entry. Identify the "
        "specific performance obligation(s) associated with each entry and confirm the "
        "satisfaction date. Where the obligation was satisfied after the recognition "
        "date, assess whether a correcting entry or disclosure is required under "
        "ASC 606-10-25."
    ),
    "missing_obligation_linkage": (
        "Obtain management explanation for revenue entries missing account "
        "classification or performance obligation linkage. Confirm correct GL account "
        "assignment and reclassify if necessary before relying on revenue totals for "
        "analytical procedures."
    ),
    "modification_treatment_mismatch": (
        "Obtain contract modification documentation for each flagged contract. "
        "Confirm whether modifications were properly accounted for as separate contracts "
        "or prospective/cumulative adjustments per ASC 606-10-25-13."
    ),
    "allocation_inconsistency": (
        "Obtain standalone selling price documentation for each flagged contract. "
        "Confirm that allocation bases are consistent across performance obligations "
        "and reflect observable prices per ASC 606-10-32-33."
    ),
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
    "fa_missing_fields": (
        "Request the complete fixed asset register with all required fields populated. "
        "Trace affected entries to source documents (purchase orders, invoices) to confirm completeness."
    ),
    "fa_negative_values": (
        "Investigate assets with negative cost or accumulated depreciation for data entry errors, "
        "improper adjustments, or reversals requiring reclassification."
    ),
    "over_depreciation": "Investigate over-depreciation for calculation errors or improper adjustments.",
    "useful_life_outliers": "Review unusual useful life estimates against industry norms and management justification.",
    "cost_zscore_outliers": (
        "Obtain supporting documentation for statistically unusual asset costs. "
        "Confirm amounts reflect actual purchase prices and proper capitalization treatment."
    ),
    "age_concentration": (
        "Evaluate the business rationale for bulk acquisitions concentrated in a single year. "
        "Verify capitalization thresholds were consistently applied."
    ),
    "duplicate_assets": "Verify whether duplicate records represent distinct assets or data entry errors.",
    "residual_value_anomalies": (
        "Review residual value estimates exceeding 30% of cost against management's disposal "
        "assumptions and industry resale data. Assess reasonableness per ISA 540."
    ),
    "lease_indicators": (
        "Confirm whether flagged assets represent right-of-use assets under ASC 842. "
        "Verify lease classification (finance vs. operating), amortization schedule, "
        "and that the asset is included in the entity's lease schedule."
    ),
    # Inventory
    "inv_missing_fields": (
        "Request the complete inventory register with all required fields populated. "
        "Trace affected items to source documents to confirm data completeness."
    ),
    "slow_moving": "Evaluate slow-moving items for obsolescence indicators and potential NRV write-down.",
    "negative_values": "Investigate negative quantities/values for returns processing, data errors, or adjustments.",
    "value_mismatch": "Recalculate extended values and investigate discrepancies with source pricing data.",
    "unit_cost_outliers": (
        "Obtain supporting documentation for statistically unusual unit costs. "
        "Verify pricing against purchase orders, supplier contracts, or standard cost records."
    ),
    "quantity_outliers": (
        "Investigate statistically unusual quantities for potential count errors, "
        "returns in transit, or obsolete stock requiring NRV evaluation."
    ),
    "category_concentration": (
        "Evaluate whether disproportionate inventory value concentration in a single category "
        "reflects the entity's business model or indicates potential valuation anomalies."
    ),
    "duplicate_items": (
        "Verify whether items with identical description and unit cost represent "
        "distinct inventory items or data entry duplicates requiring correction."
    ),
    "zero_value_items": "Evaluate items with quantity but zero value for potential write-down or pricing gaps.",
    # Payroll
    "PR-T1": (
        "Verify HR records against the payroll system for each employee ID associated "
        "with multiple names. Investigate data entry errors or potential identity substitution."
    ),
    "PR-T2": (
        "Request the complete payroll register with all required fields populated. "
        "Trace affected entries to HR authorization records to confirm completeness."
    ),
    "PR-T3": (
        "Obtain payroll authorization documentation for round-dollar pay amounts. "
        "Verify amounts reflect approved compensation rather than estimates or placeholders."
    ),
    "PR-T4": "Verify post-termination payments for proper authorization; investigate for potential ghost employees.",
    "PR-T5": (
        "Obtain voided check documentation for missing sequence numbers. "
        "Confirm proper authorization and recording of any voided instruments."
    ),
    "PR-T6": (
        "Obtain supporting authorization for statistically unusual pay amounts. "
        "Compare to approved salary schedules and investigate department-level outliers."
    ),
    "PR-T7": (
        "Confirm pay cadence against employment contracts for employees with irregular "
        "pay spacing. Investigate irregularities for potential ghost employee indicators."
    ),
    "PR-T8": (
        "Evaluate the most deviated digits in gross pay amounts for patterns of manual "
        "entry or estimation; consider targeted sampling toward those digits."
    ),
    "PR-T9": "Investigate ghost employee indicators by tracing to HR records. Physical verification of employee existence, if warranted, must be performed by the engagement team directly and not delegated to management.",
    "PR-T10": "Verify employees sharing bank accounts or addresses for proper documentation and business justification.",
    "PR-T11": "Investigate shared tax IDs for data entry errors or potential identity fraud. If confirmed, assess implications for the entity's payroll tax reporting obligations.",
    # Bank Reconciliation
    "exact_match": (
        "Review matched transactions on a sample basis to confirm the automated matching "
        "algorithm correctly paired bank and ledger items. Investigate any matched pairs "
        "where dates differ by more than 3 business days."
    ),
    "bank_only_items": (
        "Obtain supporting documentation for all outstanding deposits older than 10 days. "
        "For outstanding checks older than 90 days, assess escheatment obligations and "
        "confirm the disbursement was properly authorized."
    ),
    "ledger_only_items": (
        "Investigate ledger-only items for recording errors, timing differences, or "
        "transactions requiring reclassification. Confirm that outstanding checks represent "
        "valid disbursements with proper authorization."
    ),
    "stale_deposits": (
        "Obtain supporting documentation for all outstanding deposits older than 10 days. "
        "Deposits in transit older than 10 days may indicate fictitious deposits recorded "
        "in the ledger but not yet cleared at the bank. Verify deposit slips and bank "
        "confirmation of receipt."
    ),
    "stale_checks": (
        "Review checks outstanding more than 90 days for stale-dated items. Stale checks "
        "may require escheatment review under applicable unclaimed property laws and may "
        "indicate fictitious disbursements recorded in the ledger. Obtain void confirmations "
        "or reissue documentation."
    ),
    "nsf_items": (
        "Trace NSF/returned items to subsequent collection or write-off. Assess whether "
        "returned items indicate customer financial distress or payment fraud per ISA 240. "
        "Verify proper recording of the reversal and any subsequent re-presentment."
    ),
    "interbank_transfers": (
        "Investigate same-day matching debit/credit pairs above $10,000 as potential check "
        "kiting indicators per ISA 240 (A40). Obtain management explanation and verify "
        "the business purpose of each transfer. Confirm that both sides of the transfer "
        "are properly recorded in the correct period."
    ),
    "high_value_transactions": (
        "Obtain supporting documentation for transactions exceeding performance materiality. "
        "High-value items warrant individual verification per ISA 500 to confirm proper "
        "authorization and recording. Inspect underlying contracts, approvals, and bank "
        "confirmations."
    ),
    "reconciling_difference": (
        "Investigate the reconciling difference. Determine whether the variance represents "
        "a bank error, a GL recording omission, a timing item not captured in the matching "
        "window, or a fraudulent transaction. Document the resolution with supporting evidence."
    ),
    "outstanding_volume": (
        "Evaluate the volume of outstanding items relative to total transactions. A high "
        "outstanding ratio may indicate systemic recording delays, cut-off issues, or "
        "inadequate reconciliation procedures by the entity."
    ),
    # Three-Way Match
    "twm_amount_variance": (
        "Obtain supporting documentation for material variances between PO, invoice, and receiving "
        "amounts. Determine whether variances reflect price adjustments, quantity discrepancies, "
        "or unauthorized changes."
    ),
    "twm_unmatched_po": (
        "Investigate unmatched purchase orders for goods/services not yet received, "
        "cancelled orders not properly closed, or recording delays."
    ),
    "twm_unmatched_invoice": (
        "Investigate unmatched invoices for potential unauthorized purchases, "
        "duplicate invoices, or PO-bypass transactions requiring management explanation."
    ),
    "twm_date_variance": (
        "Evaluate significant date gaps between PO, receipt, and invoice for "
        "cut-off implications and delayed recording anomalies."
    ),
    # Multi-Period Comparison
    "significant_movement": (
        "Obtain management explanation for significant period-over-period balance changes. "
        "Corroborate explanations with supporting documentation (contracts, invoices, board minutes)."
    ),
    "new_account": (
        "Investigate accounts appearing for the first time. Confirm proper chart-of-accounts "
        "authorization and verify the underlying transactions are properly classified."
    ),
    "eliminated_account": (
        "Investigate accounts with prior-period balances that are now zero. Confirm whether "
        "the elimination reflects legitimate business changes or potential reclassification errors."
    ),
    "ratio_trend_change": (
        "Evaluate significant ratio trend changes for underlying drivers. "
        "Corroborate with management inquiry and supporting documentation."
    ),
    # Statistical Sampling
    "sampling_exception": (
        "For each exception identified in the sample, obtain the source document and "
        "management explanation. Evaluate whether the exception represents an isolated "
        "error or a systematic control deviation."
    ),
    "projected_misstatement": (
        "Evaluate the projected misstatement against tolerable misstatement. "
        "If projected misstatement approaches or exceeds tolerable misstatement, "
        "consider expanding the sample or performing alternative procedures."
    ),
    # Multi-Currency
    "rate_deviation": (
        "Investigate exchange rate deviations exceeding 1% from published rates. "
        "Confirm rate source and date alignment per ASC 830 / IAS 21."
    ),
    "unrealized_gain_loss": (
        "Evaluate significant unrealized foreign currency gains/losses for proper "
        "classification and disclosure. Confirm remeasurement methodology."
    ),
    # Data Quality Preflight
    "data_completeness": (
        "Request a complete data file addressing identified gaps. "
        "Verify that missing columns or incomplete records are resolved before proceeding."
    ),
    "balance_integrity": (
        "Investigate balance integrity failures (debits not equal to credits) "
        "for extraction errors, partial data, or posting anomalies."
    ),
    # TB Diagnostic Anomaly Types
    "rounding_anomaly": (
        "Evaluate round-dollar balances for estimates, accruals, or manual entries "
        "that may indicate placeholder amounts rather than actual transactions."
    ),
    "natural_balance_violation": (
        "Obtain management explanation for accounts with abnormal balance directions. "
        "Confirm whether the balance represents a reclassification, offset, or posting error."
    ),
    "suspense_account": (
        "Obtain the transaction detail supporting outstanding suspense balances. "
        "Confirm whether items represent unresolved reconciling differences or "
        "reclassifications in progress. Assess age of outstanding items."
    ),
    "concentration_risk_tb": (
        "Evaluate whether disproportionate balance concentration in a single account "
        "reflects the entity's business model or indicates potential classification anomalies."
    ),
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
