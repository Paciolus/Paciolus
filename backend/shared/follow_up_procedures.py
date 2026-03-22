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
    "twm_full_match_rate": (
        "Investigate the root cause of the non-match rate. Assess whether the cause is "
        "process-related (manual PO entry errors), system-related (ERP matching logic gaps), "
        "or control-related (inadequate segregation of duties in procurement). Recommend "
        "remediation steps to management to bring the match rate above 85%."
    ),
    "twm_unmatched_receipt": (
        "Investigate unmatched receiving documents for goods received but not yet invoiced. "
        "Confirm whether an accrual is required for goods received but not invoiced at period "
        "end. Verify that the receiving log is complete and reconciles to warehouse records."
    ),
    "twm_date_gap": (
        "Obtain the original PO, invoice, and GRN for this transaction. Confirm actual "
        "delivery date and whether the invoice represents goods received. Investigate whether "
        "the invoice date or PO date was altered after original entry. Date gaps exceeding "
        "60 days are a backdating indicator per ISA 240."
    ),
    "twm_duplicate_invoice": (
        "Obtain both invoices sharing the same number. Confirm whether they represent the "
        "same transaction posted twice or distinct transactions with reused numbers. If "
        "duplicate billing, initiate vendor credit memo process."
    ),
    "twm_quantity_variance": (
        "Obtain the GRN and invoice for each flagged item. Confirm whether the quantity "
        "discrepancy represents a partial shipment, a receiving error, or billing for "
        "undelivered goods. Reconcile quantities to physical count records where available."
    ),
    "twm_net_overbilling": (
        "Obtain PO amendment documentation for each HIGH severity variance. Confirm whether "
        "price increases were authorized by an approved PO amendment prior to invoice "
        "submission. For variances lacking authorization, contact the vendor to obtain a "
        "credit memo or corrected invoice."
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
    "apc_revenue_increase": (
        "Obtain detail supporting the revenue increase. Assess whether growth reflects "
        "new contracts, price increases, or volume changes. Cross-reference to revenue "
        "recognition testing results."
    ),
    "apc_revenue_decrease": (
        "Investigate the revenue decline. Determine whether the decrease reflects "
        "lost contracts, price reductions, volume decreases, or changes in revenue "
        "recognition policy. Assess going-concern implications if the decline is material."
    ),
    "apc_cogs_increase": (
        "Assess whether COGS increase is proportional to revenue growth. COGS growth "
        "exceeding revenue growth indicates margin compression — obtain management "
        "explanation and assess whether cost increases are recurring or one-time."
    ),
    "apc_cogs_decrease": (
        "Assess whether the COGS decrease is consistent with revenue trends. A COGS "
        "decrease alongside stable or increasing revenue may indicate improved efficiency, "
        "but could also indicate incomplete cost recognition or period-end cutoff issues."
    ),
    "apc_asset_increase": (
        "Obtain supporting documentation for the asset increase. Confirm the asset is "
        "properly classified and valued per applicable accounting standards."
    ),
    "apc_asset_decrease": (
        "Investigate the asset decrease. Determine whether the reduction reflects "
        "disposal, impairment, depreciation/amortization, or collection of receivables. "
        "Obtain supporting documentation for any disposals or write-downs."
    ),
    "apc_cash_increase": (
        "Cash increases above 50% warrant inquiry. Cross-reference to the cash flow "
        "statement to confirm the source of funds. Assess whether the increase reflects "
        "operating performance, financing activity, or asset disposals."
    ),
    "apc_cash_decrease": (
        "Investigate the significant cash decrease. Cross-reference to the cash flow "
        "statement to identify the use of funds. Assess whether the decrease reflects "
        "debt repayment, capital expenditures, distributions, or operating losses."
    ),
    "apc_liability_increase": (
        "Investigate the liability increase. Determine whether the increase reflects "
        "new borrowings, accruals, or deferred obligations. Obtain supporting documentation "
        "for new debt instruments or material accrual changes."
    ),
    "apc_liability_decrease": (
        "Confirm the liability reduction reflects actual payment or discharge. Obtain "
        "supporting documentation (payoff letter, settlement agreement, or payment records)."
    ),
    "apc_expense_increase": (
        "Obtain management explanation for the expense increase. Assess whether the "
        "increase is consistent with the entity's growth rate and strategic plan. "
        "Increases materially above the revenue growth rate warrant additional inquiry."
    ),
    "apc_expense_decrease": (
        "Investigate the expense decrease. Determine whether the reduction reflects "
        "cost-cutting measures, reclassification, or incomplete accrual of period expenses. "
        "Assess whether the decrease is sustainable or temporary."
    ),
    "apc_sign_change": (
        "Investigate the sign change. Confirm whether the change represents a legitimate "
        "reclassification, a correcting entry, or an error. A sign change in a balance "
        "sheet account may indicate that a debit balance became a credit balance (e.g., "
        "an asset account became a liability through over-payment or negative inventory)."
    ),
    "apc_dormant_account": (
        "For each dormant account, confirm whether the zero balance represents a "
        "legitimate closure (debt paid off, asset disposed, account closed) or an "
        "account that was zeroed out improperly. Obtain management confirmation that "
        "each dormant account has been properly resolved and closed in the chart of "
        "accounts if no longer needed."
    ),
    "apc_closed_account": (
        "For closed accounts, confirm the balance was properly disposed of, transferred, "
        "or written off prior to closure. Obtain documentation supporting the account closure."
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


FOLLOW_UP_PROCEDURES_ALT: dict[str, list[str]] = {
    # JE Testing alternates
    "unbalanced_entries": [
        "Recalculate debit/credit totals from source documents for each unbalanced entry. "
        "If differences persist, examine whether the entry was part of an automated posting "
        "split across periods or cost centers. Document the recalculation and resolution.",
    ],
    "duplicate_entries": [
        "Trace each duplicate entry to the originating system or preparer. Compare timestamps, "
        "user IDs, and posting channels to determine whether the duplication is systemic "
        "(e.g., interface re-run) or manual. Quantify the net impact on affected accounts.",
    ],
    "round_dollar_amounts": [
        "Compare round-dollar entries to the entity's accrual schedule and standard journal "
        "entry templates. Determine whether round amounts correlate with recurring accruals "
        "or represent ad-hoc estimates requiring further support.",
    ],
    "unusual_amounts": [
        "Perform a stratified analysis of flagged amounts by account and preparer. Identify "
        "whether unusual amounts cluster around specific accounts or users, which may indicate "
        "a pattern of estimation or override requiring management inquiry.",
    ],
    "holiday_postings": [
        "Cross-reference holiday entries to system access logs and the entity's authorized "
        "user list. Assess whether the posting time and user credentials are consistent with "
        "expected business operations. Escalate entries without valid business justification.",
    ],
    "weekend_postings": [
        "Review the entity's IT general controls for automated batch postings that may "
        "coincide with weekends. Distinguish between automated system postings (lower risk) "
        "and manual weekend entries (higher risk requiring individual authorization review).",
    ],
    "month_end_clustering": [
        "Compare month-end entry volume to prior-period closing patterns. If the current "
        "period shows a statistically significant increase in month-end activity, perform "
        "targeted testing on the incremental entries with particular focus on revenue "
        "recognition and expense accrual timing.",
    ],
    "benford_law": [
        "Select a judgmental sample of entries with the most deviated leading digits. "
        "Compare each sampled entry to source documents and assess whether the deviation "
        "pattern suggests systematic rounding, threshold-splitting, or estimation.",
    ],
    "missing_fields": [
        "Evaluate the impact of missing field data on the completeness of audit evidence. "
        "If the GL extract cannot be remediated, assess whether alternative procedures "
        "(e.g., vouching to source documents) can compensate for the data gap.",
    ],
    # AP Testing alternates
    "exact_duplicate_payments": [
        "Confirm whether the entity's AP system has duplicate payment detection controls. "
        "For confirmed duplicates, verify the recovery process: credit memo issued, offset "
        "applied, or refund received. If no controls exist, document as a control finding.",
    ],
    "payment_before_invoice": [
        "Evaluate whether pre-payment patterns correlate with specific vendors, buyers, "
        "or contract types. A concentration of pre-payments with a single vendor may "
        "indicate non-arms-length transactions requiring expanded procedures.",
    ],
    "just_below_threshold": [
        "Request the entity's approval authority matrix and compare the AP system's "
        "configured threshold to the documented policy threshold. Analyze the distribution "
        "of payment amounts near the threshold to assess statistical likelihood of deliberate splitting.",
    ],
    "vendor_name_variations": [
        "Run the flagged vendor pairs against the entity's 1099 vendor master to identify "
        "shared tax IDs, bank accounts, or addresses. Vendors sharing these attributes but "
        "listed under different names represent a master data integrity risk.",
    ],
    # AP Testing alternates (continued — BUG-001)
    "missing_critical_fields": [
        "Evaluate whether the missing field data impacts the completeness of the AP "
        "population tested. If the register extract cannot be remediated, assess whether "
        "alternative procedures (e.g., vouching a sample to source invoices) can compensate "
        "for the data gap.",
    ],
    "suspicious_descriptions": [
        "Stratify flagged payments by vendor and preparer. Determine whether suspicious "
        "descriptions cluster around specific preparers or vendors, which may indicate a "
        "pattern warranting expanded fraud-risk procedures per ISA 240.",
    ],
    "high_frequency_vendors": [
        "Obtain the entity's vendor payment terms and compare to the observed payment "
        "frequency. Determine whether high-frequency payments represent legitimate "
        "recurring charges or potential payment splitting to circumvent approval controls.",
    ],
    "check_number_gaps": [
        "Request the void register for the period and reconcile to the identified gaps. "
        "For any unaccounted gaps, expand the inquiry to include bank-cleared check images "
        "to confirm whether the instruments were negotiated.",
    ],
    "round_dollar_amounts_ap": [
        "Stratify round-dollar payments by account code and preparer. Determine whether "
        "round amounts correlate with recurring accruals or represent ad-hoc estimates "
        "requiring supporting documentation.",
    ],
    "unusual_payment_amounts": [
        "Perform a stratified analysis of flagged payments by vendor category. Identify "
        "whether unusual amounts cluster around specific vendors or periods, which may "
        "indicate estimation or pricing anomalies requiring vendor confirmation.",
    ],
    "weekend_payments": [
        "Review the entity's IT general controls for automated payment processing that "
        "may coincide with weekends. Distinguish between automated ACH runs (lower risk) "
        "and manual weekend disbursements (higher risk requiring authorization review).",
    ],
    "fuzzy_duplicate_payments": [
        "Compare fuzzy duplicate pairs to the vendor's standard pricing schedule. "
        "Confirm whether recurring same-amount payments reflect contracted service fees "
        "or indicate potential duplicate processing requiring recovery.",
    ],
    "invoice_number_reuse": [
        "Examine the AP system's duplicate invoice detection controls. Determine whether "
        "the reused number was accepted due to a control gap or represents a legitimate "
        "multi-line invoice split across vendors.",
    ],
    # Revenue Testing alternates
    "cutoff_risk": [
        "Select entries within 5 business days of period end and trace to delivery/acceptance "
        "documentation. For service revenue, confirm that the service period falls within the "
        "reporting period. Quantify any entries where evidence of satisfaction is absent.",
    ],
    "concentration_risk": [
        "Perform a trend analysis of the top customer's revenue share over the past 3 periods. "
        "If concentration is increasing, inquire of management about customer diversification "
        "strategy and assess going-concern implications per ASC 205-40.",
    ],
    # Revenue Testing alternates (continued — BUG-001)
    "large_manual_entries": [
        "Compare flagged manual entries to the entity's standard revenue posting workflow. "
        "Identify whether manual entries bypass automated controls (e.g., billing system "
        "interface) and assess the compensating controls in place for manual overrides.",
    ],
    "year_end_concentration": [
        "Perform a period-over-period comparison of December revenue as a percentage of "
        "annual revenue. If the current-year percentage is significantly higher than the "
        "prior period, inquire of management and corroborate with shipping or delivery "
        "records.",
    ],
    "sign_anomalies": [
        "Obtain a detailed listing of debit-balance revenue accounts. Stratify by customer "
        "and product line to determine whether the pattern reflects a specific return/refund "
        "trend or a systematic misposting requiring reclassification.",
    ],
    "trend_variance": [
        "Compare revenue variances to changes in the entity's key business drivers (volume, "
        "pricing, customer mix). Assess whether unexplained variances warrant expanded "
        "substantive testing of revenue transactions near period end.",
    ],
    "contra_revenue_anomalies": [
        "Stratify returns and allowances by customer and product line. Determine whether "
        "elevated contra-revenue is concentrated in specific channels that may indicate "
        "channel-stuffing reversal or aggressive prior-period recognition.",
    ],
    # AR Aging alternates (BUG-001)
    "past_due_concentration": [
        "Obtain the entity's collection activity log for past-due balances. Assess whether "
        "management's collection efforts are commensurate with the risk, and evaluate the "
        "need to adjust the allowance for doubtful accounts.",
    ],
    "customer_concentration": [
        "Perform a trend analysis of the top customer's AR share over the past 3 periods. "
        "If concentration is increasing, assess credit risk implications and evaluate "
        "whether expanded confirmation procedures are warranted.",
    ],
    "credit_limit_breaches": [
        "Obtain management's credit review documentation for customers exceeding limits. "
        "Assess whether continued shipments reflect approved credit limit increases or "
        "represent an override of the credit control policy.",
    ],
    # Fixed Asset alternates (BUG-001)
    "fully_depreciated": [
        "Obtain a listing of fully depreciated assets still in productive use. Assess "
        "whether useful life estimates require revision per ISA 540 and whether the "
        "carrying amount understates the entity's asset base.",
    ],
    "fa_missing_fields": [
        "Evaluate the impact of incomplete fixed asset records on the population tested. "
        "If the register cannot be remediated, assess whether alternative procedures "
        "(e.g., physical inspection) can compensate for the data gap.",
    ],
    "cost_zscore_outliers": [
        "Compare flagged asset costs to market data or comparable acquisitions. Determine "
        "whether outlier costs reflect legitimate premium purchases, capitalized "
        "installation costs, or potential data entry errors.",
    ],
    # Inventory alternates (BUG-001)
    "slow_moving": [
        "Obtain management's obsolescence reserve methodology and compare to the identified "
        "slow-moving items. Assess whether the current reserve adequately addresses the "
        "risk of NRV decline for these items per ASC 330.",
    ],
    "unit_cost_outliers": [
        "Compare flagged unit costs to the most recent purchase orders and supplier "
        "contracts. Determine whether cost increases reflect legitimate market changes "
        "or require adjustment to the standard cost records.",
    ],
    # Payroll alternates
    "PR-T4": [
        "Cross-reference the termination date per HR records to the last paycheck date. "
        "For payments after termination, obtain documentation of final pay obligations "
        "(accrued PTO, severance) that justify the payment.",
    ],
    "PR-T9": [
        "Request a headcount reconciliation between HR and payroll systems. For any "
        "discrepancies, physically verify employee existence through direct observation "
        "or independent third-party confirmation.",
    ],
}


def get_follow_up_procedure(test_key: str, rotation_index: int = 0) -> str:
    """Get the suggested follow-up procedure for a test key.

    Supports rotation: when multiple procedures exist for a test_key,
    rotation_index selects which alternate to return.  This prevents
    identical procedure text across multiple reports (BUG-001).

    Returns empty string if no procedure is defined for the key.
    """
    primary = FOLLOW_UP_PROCEDURES.get(test_key, "")
    if not primary:
        return ""
    alts = FOLLOW_UP_PROCEDURES_ALT.get(test_key, [])
    if not alts:
        return primary
    all_procedures = [primary] + alts
    return all_procedures[rotation_index % len(all_procedures)]


def get_finding_benchmark(test_key: str) -> str:
    """Get benchmark context text for a finding, if available.

    Returns empty string if no benchmark is defined for the key.
    """
    return FINDING_BENCHMARKS.get(test_key, "")
