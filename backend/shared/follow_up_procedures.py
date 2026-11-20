"""
Follow-Up Procedure Suggestions

Maps each (tool, test) to suggested follow-up procedures. The tool is the
engagement ``ToolName`` value; the test is the ``test_key`` its engine emits
(Sprint 887 / OUT-17: the library was keyed by names the engines did not emit,
shared keys across tools, and the memo guessed the test from the flag's text).
These are suggestions, not requirements; the auditor exercises professional
judgment per ISA 330. Each opens "The auditor may consider" and gives no command
(Sprint 887 / OUT-30).

Selection is stable: a test with several suggestions gets the one chosen by a
CRC-32 of (seed, tool, test) — the same in every process (``hash()`` was not)
and independent of the flag's position in the memo.

ENHANCE-01: Suggested Follow-Up Procedures.
"""

import zlib

# tool -> test_key -> suggestions (the first is the primary; the others are alternates)

PROCEDURES: dict[str, dict[str, tuple[str, ...]]] = {
    "journal_entry_testing": {
        "unbalanced_entries": (
            (
                "The auditor may consider obtaining the preparer's explanation for each unbalanced entry, "
                "establishing whether the difference reflects a rounding policy or calls for a correcting journal"
                " entry, and documenting the resolution in the engagement file."
            ),
            (
                "The auditor may consider recalculating debit/credit totals from source documents for each "
                "unbalanced entry and, where differences persist, examining whether the entry was part of an "
                "automated posting split across periods or cost centers, and documenting the recalculation and "
                "resolution."
            ),
        ),
        "missing_fields": (
            (
                "The auditor may consider requesting the complete GL extract with all expected fields populated "
                "and tracing affected entries to source documents to establish whether the transactions are "
                "complete and properly recorded."
            ),
            (
                "The auditor may consider evaluating the impact of missing field data on the completeness of "
                "audit evidence. Where the GL extract cannot be remediated, it may also consider assessing "
                "whether alternative procedures (e.g., vouching to source documents) can compensate for the data "
                "gap."
            ),
        ),
        "duplicate_entries": (
            (
                "The auditor may consider inspecting each duplicate entry pair and establishing whether the "
                "duplication represents a legitimate correction, a system posting error, or a potentially "
                "fraudulent duplicate transaction."
            ),
            (
                "The auditor may consider tracing each duplicate entry to the originating system or preparer, "
                "comparing timestamps, user IDs, and posting channels to establish whether the duplication is "
                "systemic (e.g., interface re-run) or manual, and quantifying the net impact on affected "
                "accounts."
            ),
        ),
        "unusual_amounts": (
            (
                "The auditor may consider obtaining supporting documentation for statistically unusual amounts "
                "and checking whether amounts reflect actual invoiced or contracted values and were not manually "
                "estimated."
            ),
            (
                "The auditor may consider performing a stratified analysis of flagged amounts by account and "
                "preparer and identifying whether unusual amounts cluster around specific accounts or users, "
                "which may indicate a pattern of estimation or override that may call for management inquiry."
            ),
        ),
        "benford_law": (
            (
                "The auditor may consider evaluating the most deviated digits for patterns of manual entry or "
                "estimation and targeted sampling of entries starting with those digits."
            ),
            (
                "The auditor may consider selecting a judgmental sample of entries with the most deviated leading"
                " digits, comparing each sampled entry to source documents, and assessing whether the deviation "
                "pattern suggests systematic rounding, threshold-splitting, or estimation."
            ),
        ),
        "weekend_postings": (
            (
                "The auditor may consider checking whether weekend-posted entries were authorized and have valid "
                "business justification, and reviewing system access logs if available to establish whether "
                "posting was performed by an authorized user."
            ),
            (
                "The auditor may consider reviewing the entity's IT general controls for automated batch postings"
                " that may coincide with weekends, distinguishing between automated system postings (lower risk) "
                "and manual weekend entries (higher risk, for which an individual authorization review may be "
                "appropriate)."
            ),
        ),
        "month_end_clustering": (
            (
                "The auditor may consider evaluating whether month-end entries represent normal closing activity "
                "or potential earnings management, inquiring of management regarding the business rationale for "
                "the concentration, and performing corroborating procedures on material month-end entries."
            ),
            (
                "The auditor may consider comparing month-end entry volume to prior-period closing patterns. "
                "Where the current period shows a statistically significant increase in month-end activity, the "
                "auditor may consider performing targeted testing on the incremental entries with particular "
                "focus on revenue recognition and expense accrual timing."
            ),
        ),
        "holiday_postings": (
            (
                "The auditor may consider obtaining, for each holiday posting, documentation supporting business "
                "necessity and checking whether the entry received proper authorization and supervisory review "
                "per the client's journal entry policy (ISA 240 journal entry fraud risk indicator)."
            ),
            (
                "The auditor may consider cross-referencing holiday entries to system access logs and the "
                "entity's authorized user list, assessing whether the posting time and user credentials are "
                "consistent with expected business operations, and escalating entries without valid business "
                "justification."
            ),
        ),
        "round_amounts": (
            (
                "The auditor may consider comparing round-dollar entries against supporting documentation "
                "(invoices, contracts) to establish whether amounts are estimates or placeholders."
            ),
            (
                "The auditor may consider comparing round-dollar entries to the entity's accrual schedule and "
                "standard journal entry templates and establishing whether round amounts correlate with recurring"
                " accruals or represent ad-hoc estimates that may call for further support."
            ),
        ),
    },
    "ap_testing": {
        "exact_duplicate_payments": (
            (
                "The auditor may consider pulling original invoices and payment documentation for both duplicate "
                "payments and establishing whether the duplicate was identified and recovered. If not recovered, "
                "it may also consider requesting a vendor credit or initiating the recovery process, and "
                "documenting the resolution."
            ),
            (
                "The auditor may consider establishing whether the entity's AP system has duplicate payment "
                "detection controls and, for confirmed duplicates, checking the recovery process: credit memo "
                "issued, offset applied, or refund received. Where no controls exist, it may also consider "
                "documenting this as a potential control matter."
            ),
        ),
        "fuzzy_duplicate_payments": (
            (
                "The auditor may consider inspecting each fuzzy duplicate pair for business justification and "
                "establishing whether the same-vendor same-amount payments on different dates represent recurring"
                " legitimate charges or potential duplicate disbursements."
            ),
            (
                "The auditor may consider comparing fuzzy duplicate pairs to the vendor's standard pricing "
                "schedule and establishing whether recurring same-amount payments reflect contracted service fees"
                " or potential duplicate processing that may call for recovery."
            ),
        ),
        "payment_before_invoice": (
            (
                "The auditor may consider obtaining management's explanation for each prepayment and establishing"
                " whether a prepayment arrangement was authorized per AP policy and supported by a contract or "
                "purchase order. The absence of authorization documentation may indicate a control gap that the "
                "engagement team may consider as part of its professional assessment of the AP control "
                "environment."
            ),
            (
                "The auditor may consider evaluating whether pre-payment patterns correlate with specific "
                "vendors, buyers, or contract types. A concentration of pre-payments with a single vendor may "
                "indicate non-arms-length transactions, in which case it may also consider expanded procedures."
            ),
        ),
        "just_below_threshold": (
            (
                "The auditor may consider obtaining approval documentation for each payment, comparing the "
                "approval threshold in the current AP policy to the threshold applied in the payment system, and "
                "establishing whether the clustering of payments just below threshold on the same dates "
                "represents intentional threshold avoidance."
            ),
            (
                "The auditor may consider requesting the entity's approval authority matrix, comparing the AP "
                "system's configured threshold to the documented policy threshold, and analyzing the distribution"
                " of payment amounts near the threshold to assess the statistical likelihood of deliberate "
                "splitting."
            ),
        ),
        "invoice_number_reuse": (
            (
                "The auditor may consider obtaining both invoices sharing the reused number and establishing "
                "whether the vendors are the same entity operating under different names, or distinct entities. "
                "If distinct, it may also consider investigating how the same invoice number was accepted by the "
                "AP system for two different vendors."
            ),
            (
                "The auditor may consider examining the AP system's duplicate invoice detection controls and "
                "establishing whether the reused number was accepted due to a control gap or represents a "
                "legitimate multi-line invoice split across vendors."
            ),
        ),
        "vendor_name_variations": (
            (
                "The auditor may consider obtaining vendor master records for each flagged pair, establishing "
                "whether similar vendor names represent the same entity, a legitimate subsidiary, or a potential "
                "ghost vendor, and checking address, tax ID, and bank account details for each."
            ),
            (
                "The auditor may consider running the flagged vendor pairs against the entity's 1099 vendor "
                "master to identify shared tax IDs, bank accounts, or addresses. Vendors sharing these attributes"
                " but listed under different names may represent a master data integrity risk."
            ),
        ),
        "missing_critical_fields": (
            (
                "The auditor may consider requesting the complete AP register with all expected fields populated "
                "for the affected payments and tracing to source documents to establish whether transactions are "
                "complete and properly recorded."
            ),
            (
                "The auditor may consider evaluating whether the missing field data affects the completeness of "
                "the AP population tested. Where the register extract cannot be remediated, it may also consider "
                "assessing whether alternative procedures (e.g., vouching a sample to source invoices) can "
                "compensate for the data gap."
            ),
        ),
        "suspicious_descriptions": (
            (
                "The auditor may consider inspecting each payment flagged for suspicious description keywords, "
                "obtaining supporting documentation and management explanation, and escalating any payments "
                "lacking adequate support per ISA 240 fraud risk procedures."
            ),
            (
                "The auditor may consider stratifying flagged payments by vendor and preparer and establishing "
                "whether suspicious descriptions cluster around specific preparers or vendors, which may indicate"
                " a pattern for which expanded fraud-risk procedures per ISA 240 may be appropriate."
            ),
        ),
        "high_frequency_vendors": (
            (
                "The auditor may consider obtaining detail of all payments to the flagged vendor(s) on the high-"
                "frequency date and checking whether each payment is supported by a distinct invoice and whether "
                "there is any duplication or splitting of a single invoice across multiple payments."
            ),
            (
                "The auditor may consider obtaining the entity's vendor payment terms, comparing them to the "
                "observed payment frequency, and establishing whether high-frequency payments represent "
                "legitimate recurring charges or potential payment splitting to circumvent approval controls."
            ),
        ),
        "check_number_gaps": (
            (
                "The auditor may consider investigating gaps in check sequence, obtaining voided check "
                "documentation for missing numbers, and checking proper authorization and recording of any voided"
                " instruments."
            ),
            (
                "The auditor may consider requesting the void register for the period and reconciling it to the "
                "identified gaps. For any unaccounted gaps, it may also consider expanding the inquiry to include"
                " bank-cleared check images to establish whether the instruments were negotiated."
            ),
        ),
        "unusual_payment_amounts": (
            (
                "The auditor may consider obtaining supporting documentation for statistically unusual payment "
                "amounts and checking whether amounts reflect actual invoiced values and are supported by "
                "approved purchase orders or contracts."
            ),
            (
                "The auditor may consider performing a stratified analysis of flagged payments by vendor category"
                " and identifying whether unusual amounts cluster around specific vendors or periods, which may "
                "indicate estimation or pricing anomalies that may call for vendor confirmation."
            ),
        ),
        "weekend_payments": (
            (
                "The auditor may consider checking whether weekend-processed payments were authorized and have "
                "valid business justification, and reviewing system access logs to establish whether payments "
                "were processed by an authorized user outside normal business hours."
            ),
            (
                "The auditor may consider reviewing the entity's IT general controls for automated payment "
                "processing that may coincide with weekends, distinguishing between automated ACH runs (lower "
                "risk) and manual weekend disbursements (higher risk, for which an authorization review may be "
                "appropriate)."
            ),
        ),
        "round_dollar_amounts": (
            (
                "The auditor may consider comparing round-amount payments against supporting invoices to "
                "establish whether they are estimates or placeholders."
            ),
            (
                "The auditor may consider stratifying round-dollar payments by account code and preparer and "
                "establishing whether round amounts correlate with recurring accruals or represent ad-hoc "
                "estimates that may call for supporting documentation."
            ),
        ),
    },
    "payroll_testing": {
        "PR-T1": (
            (
                "The auditor may consider comparing HR records against the payroll system for each employee ID "
                "associated with multiple names and investigating data entry errors or potential identity "
                "substitution."
            ),
        ),
        "PR-T2": (
            (
                "The auditor may consider requesting the complete payroll register with all expected fields "
                "populated and tracing affected entries to HR authorization records to establish completeness."
            ),
        ),
        "PR-T3": (
            (
                "The auditor may consider obtaining payroll authorization documentation for round-dollar pay "
                "amounts and checking whether amounts reflect approved compensation rather than estimates or "
                "placeholders."
            ),
        ),
        "PR-T4": (
            (
                "The auditor may consider checking post-termination payments for proper authorization and "
                "investigating them for potential ghost employees."
            ),
            (
                "The auditor may consider cross-referencing the termination date per HR records to the last "
                "paycheck date and, for payments after termination, obtaining documentation of final pay "
                "obligations (accrued PTO, severance) that support the payment."
            ),
        ),
        "PR-T5": (
            (
                "The auditor may consider obtaining voided check documentation for missing sequence numbers and "
                "checking proper authorization and recording of any voided instruments."
            ),
        ),
        "PR-T6": (
            (
                "The auditor may consider obtaining supporting authorization for statistically unusual pay "
                "amounts, comparing them to approved salary schedules, and investigating department-level "
                "outliers."
            ),
        ),
        "PR-T7": (
            (
                "The auditor may consider comparing pay cadence against employment contracts for employees with "
                "irregular pay spacing and investigating irregularities for potential ghost employee indicators."
            ),
        ),
        "PR-T8": (
            (
                "The auditor may consider evaluating the most deviated digits in gross pay amounts for patterns "
                "of manual entry or estimation and targeted sampling toward those digits."
            ),
        ),
        "PR-T9": (
            (
                "The auditor may consider investigating ghost employee indicators by tracing to HR records. Where"
                " physical verification of employee existence is performed, it is ordinarily performed by the "
                "engagement team directly and not delegated to management."
            ),
            (
                "The auditor may consider requesting a headcount reconciliation between HR and payroll systems "
                "and, for any discrepancies, physically confirming employee existence through direct observation "
                "or independent third-party confirmation."
            ),
        ),
        "PR-T10": (
            (
                "The auditor may consider checking employees sharing bank accounts or addresses for proper "
                "documentation and business justification."
            ),
        ),
        "PR-T11": (
            (
                "The auditor may consider investigating shared tax IDs for data entry errors or potential "
                "identity fraud. Where identity fraud is confirmed, it may also consider assessing implications "
                "for the entity's payroll tax reporting obligations."
            ),
        ),
        "PR-T12": (
            (
                "The auditor may consider comparing the employees who share a name with HR records (hire "
                "documentation, tax forms and bank details) to establish whether they are different people, and "
                "tracing any payment to an employee whom HR records do not support."
            ),
        ),
        "PR-T13": (
            (
                "The auditor may consider recomputing net pay from gross pay and the recorded deductions for the "
                "flagged entries, and comparing the deductions with the withholdings in the payroll register and "
                "their remittance records."
            ),
        ),
    },
    "revenue_testing": {
        "large_manual_entries": (
            (
                "The auditor may consider obtaining preparer identification and approval documentation for each "
                "large manual revenue entry and checking whether entries were reviewed by a supervisor and "
                "supported by a contract or binding commitment per ISA 240."
            ),
            (
                "The auditor may consider comparing flagged manual entries to the entity's standard revenue "
                "posting workflow, identifying whether manual entries bypass automated controls (e.g., billing "
                "system interface), and assessing the compensating controls in place for manual overrides."
            ),
        ),
        "year_end_concentration": (
            (
                "The auditor may consider evaluating whether December revenue concentration reflects genuine "
                "business activity (e.g., seasonal contracts, milestone completions) or potential period-end "
                "earnings management, and obtaining delivery or acceptance documentation for material December "
                "entries."
            ),
            (
                "The auditor may consider performing a period-over-period comparison of December revenue as a "
                "percentage of annual revenue. Where the current-year percentage is significantly higher than the"
                " prior period, it may also consider inquiring of management and corroborating with shipping or "
                "delivery records."
            ),
        ),
        "cutoff_risk": (
            (
                "The auditor may consider inspecting the underlying contract or delivery documentation for each "
                "flagged entry and establishing whether the performance obligation under ASC 606-10-25-23 was "
                "satisfied prior to the period end. Where an entry lacks supporting evidence of satisfaction "
                "before period end, it may also consider assessing it for potential deferral to the subsequent "
                "period."
            ),
            (
                "The auditor may consider selecting entries within 5 business days of period end and tracing them"
                " to delivery/acceptance documentation, checking for service revenue whether the service period "
                "falls within the reporting period, and quantifying any entries where evidence of satisfaction is"
                " absent."
            ),
        ),
        "concentration_risk": (
            (
                "The auditor may consider assessing single-customer concentration for both revenue recognition "
                "and credit risk implications, obtaining the master contract with this customer, and evaluating "
                "whether the concentration represents a going concern or business continuity risk calling for "
                "disclosure under ASC 275-10."
            ),
            (
                "The auditor may consider performing a trend analysis of the top customer's revenue share over "
                "the past 3 periods. Where concentration is increasing, it may also consider inquiring of "
                "management about customer diversification strategy and assessing going-concern implications per "
                "ASC 205-40."
            ),
        ),
        "sign_anomalies": (
            (
                "The auditor may consider investigating debit balances in revenue accounts, establishing whether "
                "each debit represents a legitimate return, allowance, or contra-revenue entry, or a misposting "
                "that may call for further review, and obtaining supporting documentation for each."
            ),
            (
                "The auditor may consider obtaining a detailed listing of debit-balance revenue accounts and "
                "stratifying it by customer and product line to establish whether the pattern reflects a specific"
                " return/refund trend or a systematic misposting that may call for reclassification."
            ),
        ),
        "trend_variance": (
            (
                "The auditor may consider obtaining management's explanations for significant period-over-period "
                "revenue changes, corroborating explanations with supporting documentation, and assessing whether"
                " variances point to revenue recognition anomalies."
            ),
            (
                "The auditor may consider comparing revenue variances to changes in the entity's key business "
                "drivers (volume, pricing, customer mix) and assessing whether unexplained variances call for "
                "expanded substantive testing of revenue transactions near period end."
            ),
        ),
        "contra_revenue_anomalies": (
            (
                "The auditor may consider calculating the contra-revenue ratio (returns and allowances / gross "
                "revenue), comparing it to the prior period, obtaining detail of returns and allowances, and "
                "assessing whether elevated levels point to channel stuffing reversal or aggressive prior-period "
                "recognition."
            ),
            (
                "The auditor may consider stratifying returns and allowances by customer and product line and "
                "establishing whether elevated contra-revenue is concentrated in specific channels that may "
                "indicate channel-stuffing reversal or aggressive prior-period recognition."
            ),
        ),
        "recognition_before_satisfaction": (
            (
                "The auditor may consider obtaining contract documentation for each flagged entry, identifying "
                "the specific performance obligation(s) associated with each entry, and establishing the "
                "satisfaction date. Where the obligation was satisfied after the recognition date, it may also "
                "consider assessing whether a correcting entry or disclosure is called for under ASC 606-10-25."
            ),
        ),
        "missing_obligation_linkage": (
            (
                "The auditor may consider obtaining management's explanation for revenue entries missing account "
                "classification or performance obligation linkage, checking the GL account assignment, and "
                "reclassifying where appropriate before relying on revenue totals for analytical procedures."
            ),
        ),
        "modification_treatment_mismatch": (
            (
                "The auditor may consider obtaining contract modification documentation for each flagged contract"
                " and establishing whether modifications were properly accounted for as separate contracts or "
                "prospective/cumulative adjustments per ASC 606-10-25-13."
            ),
        ),
        "allocation_inconsistency": (
            (
                "The auditor may consider obtaining standalone selling price documentation for each flagged "
                "contract and checking whether allocation bases are consistent across performance obligations and"
                " reflect observable prices per ASC 606-10-32-33."
            ),
        ),
        "benford_law": (
            (
                "The auditor may consider reviewing the most deviated digits in revenue amounts for manual "
                "estimation patterns."
            ),
        ),
        "duplicate_entries": (
            "The auditor may consider inspecting potential duplicate revenue entries for proper posting.",
        ),
    },
    "ar_aging": {
        "ar_sign_anomalies": (
            (
                "The auditor may consider investigating credit balances in AR for overpayments, "
                "misclassifications, or items that may call for reclassification."
            ),
        ),
        "missing_allowance": (
            (
                "The auditor may consider determining how expected credit losses are measured and recognized "
                "under IFRS 9 / ASC 326, and where they are recorded if no allowance account is present."
            ),
        ),
        "past_due_concentration": (
            (
                "The auditor may consider reviewing past-due accounts for collection activity and assessing "
                "recoverability."
            ),
            (
                "The auditor may consider obtaining the entity's collection activity log for past-due balances, "
                "assessing whether management's collection efforts are commensurate with the risk, and evaluating"
                " whether the allowance for doubtful accounts calls for adjustment."
            ),
        ),
        "customer_concentration": (
            ("The auditor may consider evaluating credit risk concentration and expanding confirmation procedures."),
            (
                "The auditor may consider performing a trend analysis of the top customer's AR share over the "
                "past 3 periods. Where concentration is increasing, it may also consider assessing credit risk "
                "implications and evaluating whether expanded confirmation procedures are appropriate."
            ),
        ),
        "credit_limit_breaches": (
            (
                "The auditor may consider reviewing customers exceeding credit limits for continued "
                "creditworthiness and collection outlook."
            ),
            (
                "The auditor may consider obtaining management's credit review documentation for customers "
                "exceeding limits and assessing whether continued shipments reflect approved credit limit "
                "increases or represent an override of the credit control policy."
            ),
        ),
        "dso_trend": (
            (
                "The auditor may consider investigating DSO increases for changes in collection efficiency or "
                "customer payment behavior."
            ),
        ),
        "allowance_adequacy": (
            (
                "The auditor may consider performing an independent estimate of allowance adequacy using "
                "historical loss rates."
            ),
        ),
    },
    "fixed_asset_testing": {
        "fully_depreciated": (
            (
                "The auditor may consider evaluating whether fully depreciated assets still in use call for "
                "revised useful life estimates."
            ),
            (
                "The auditor may consider obtaining a listing of fully depreciated assets still in productive use"
                " and assessing whether useful life estimates call for revision per ISA 540 and whether the "
                "carrying amount understates the entity's asset base."
            ),
        ),
        "over_depreciation": (
            (
                "The auditor may consider investigating over-depreciation for calculation errors or improper "
                "adjustments."
            ),
        ),
        "useful_life_outliers": (
            (
                "The auditor may consider reviewing unusual useful life estimates against industry norms and "
                "management justification."
            ),
        ),
        "cost_zscore_outliers": (
            (
                "The auditor may consider obtaining supporting documentation for statistically unusual asset "
                "costs and checking whether amounts reflect actual purchase prices and proper capitalization "
                "treatment."
            ),
            (
                "The auditor may consider comparing flagged asset costs to market data or comparable acquisitions"
                " and establishing whether outlier costs reflect legitimate premium purchases, capitalized "
                "installation costs, or potential data entry errors."
            ),
        ),
        "age_concentration": (
            (
                "The auditor may consider evaluating the business rationale for bulk acquisitions concentrated in"
                " a single year and checking whether capitalization thresholds were consistently applied."
            ),
        ),
        "duplicate_assets": (
            (
                "The auditor may consider checking whether duplicate records represent distinct assets or data "
                "entry errors."
            ),
        ),
        "residual_value_anomalies": (
            (
                "The auditor may consider reviewing residual value estimates exceeding 30% of cost against "
                "management's disposal assumptions and industry resale data and assessing reasonableness per ISA "
                "540."
            ),
        ),
        "lease_indicators": (
            (
                "The auditor may consider establishing whether flagged assets represent right-of-use assets under"
                " ASC 842 and checking the lease classification (finance vs. operating), the amortization "
                "schedule, and whether the asset is included in the entity's lease schedule."
            ),
        ),
        "missing_fields": (
            (
                "The auditor may consider requesting the complete fixed asset register with all expected fields "
                "populated and tracing affected entries to source documents (purchase orders, invoices) to "
                "establish completeness."
            ),
            (
                "The auditor may consider evaluating the impact of incomplete fixed asset records on the "
                "population tested. Where the register cannot be remediated, it may also consider assessing "
                "whether alternative procedures (e.g., physical inspection) can compensate for the data gap."
            ),
        ),
        "negative_values": (
            (
                "The auditor may consider investigating assets with negative cost or accumulated depreciation for"
                " data entry errors, improper adjustments, or reversals that may call for reclassification."
            ),
        ),
    },
    "inventory_testing": {
        "slow_moving": (
            (
                "The auditor may consider evaluating slow-moving items for obsolescence indicators and potential "
                "NRV write-down."
            ),
            (
                "The auditor may consider obtaining management's obsolescence reserve methodology, comparing it "
                "to the identified slow-moving items, and assessing whether the current reserve adequately "
                "addresses the risk of NRV decline for these items per ASC 330."
            ),
        ),
        "negative_values": (
            (
                "The auditor may consider investigating negative quantities/values for returns processing, data "
                "errors, or adjustments."
            ),
        ),
        "value_mismatch": (
            (
                "The auditor may consider recalculating extended values and investigating discrepancies with "
                "source pricing data."
            ),
        ),
        "unit_cost_outliers": (
            (
                "The auditor may consider obtaining supporting documentation for statistically unusual unit costs"
                " and checking pricing against purchase orders, supplier contracts, or standard cost records."
            ),
            (
                "The auditor may consider comparing flagged unit costs to the most recent purchase orders and "
                "supplier contracts and establishing whether cost increases reflect legitimate market changes or "
                "call for adjustment to the standard cost records."
            ),
        ),
        "quantity_outliers": (
            (
                "The auditor may consider investigating statistically unusual quantities for potential count "
                "errors, returns in transit, or obsolete stock that may call for NRV evaluation."
            ),
        ),
        "category_concentration": (
            (
                "The auditor may consider evaluating whether disproportionate inventory value concentration in a "
                "single category reflects the entity's business model or potential valuation anomalies."
            ),
        ),
        "duplicate_items": (
            (
                "The auditor may consider checking whether items with identical description and unit cost "
                "represent distinct inventory items or data entry duplicates that may call for correction."
            ),
        ),
        "zero_value_items": (
            (
                "The auditor may consider evaluating items with quantity but zero value for potential write-down "
                "or pricing gaps."
            ),
        ),
        "missing_fields": (
            (
                "The auditor may consider requesting the complete inventory register with all expected fields "
                "populated and tracing affected items to source documents to establish data completeness."
            ),
        ),
    },
    "bank_reconciliation": {
        "exact_match": (
            (
                "The auditor may consider reviewing matched transactions on a sample basis to check whether the "
                "automated matching algorithm correctly paired bank and ledger items, and investigating any "
                "matched pairs where dates differ by more than 3 business days."
            ),
        ),
        "bank_only_items": (
            (
                "The auditor may consider obtaining supporting documentation for all outstanding deposits older "
                "than 10 days. For outstanding checks older than 90 days, it may also consider assessing "
                "escheatment obligations and checking whether the disbursement was properly authorized."
            ),
        ),
        "ledger_only_items": (
            (
                "The auditor may consider investigating ledger-only items for recording errors, timing "
                "differences, or transactions that may call for reclassification, and checking whether "
                "outstanding checks represent valid disbursements with proper authorization."
            ),
        ),
        "stale_deposits": (
            (
                "The auditor may consider obtaining supporting documentation for all outstanding deposits older "
                "than 10 days. Deposits in transit older than 10 days may indicate fictitious deposits recorded "
                "in the ledger but not yet cleared at the bank, and the auditor may also consider checking "
                "deposit slips and bank confirmation of receipt."
            ),
        ),
        "stale_checks": (
            (
                "The auditor may consider reviewing checks outstanding more than 90 days for stale-dated items "
                "and obtaining void confirmations or reissue documentation. Stale checks may be subject to "
                "escheatment review under applicable unclaimed property laws and may indicate fictitious "
                "disbursements recorded in the ledger."
            ),
        ),
        "nsf_items": (
            (
                "The auditor may consider tracing NSF/returned items to subsequent collection or write-off, "
                "assessing whether returned items point to customer financial distress or payment fraud per ISA "
                "240, and checking the recording of the reversal and any subsequent re-presentment."
            ),
        ),
        "interbank_transfers": (
            (
                "The auditor may consider investigating same-day matching debit/credit pairs above $10,000 as "
                "potential check kiting indicators (a fraud risk considered under ISA 240), obtaining "
                "management's explanation and checking the business purpose of each transfer, and checking "
                "whether both sides of the transfer are properly recorded in the correct period."
            ),
        ),
        "high_value_transactions": (
            (
                "The auditor may consider obtaining supporting documentation for transactions exceeding "
                "performance materiality, examining high-value items individually per ISA 500 for proper "
                "authorization and recording, and inspecting underlying contracts, approvals, and bank "
                "confirmations."
            ),
        ),
        "reconciling_difference": (
            (
                "The auditor may consider investigating the reconciling difference, establishing whether the "
                "variance represents a bank error, a GL recording omission, a timing item not captured in the "
                "matching window, or a fraudulent transaction, and documenting the resolution with supporting "
                "evidence."
            ),
        ),
        "outstanding_volume": (
            (
                "The auditor may consider evaluating the volume of outstanding items relative to total "
                "transactions. A high outstanding ratio may indicate systemic recording delays, cut-off issues, "
                "or inadequate reconciliation procedures by the entity."
            ),
        ),
    },
    "three_way_match": {
        "twm_amount_variance": (
            (
                "The auditor may consider obtaining supporting documentation for material variances between PO, "
                "invoice, and receiving amounts and establishing whether variances reflect price adjustments, "
                "quantity discrepancies, or unauthorized changes."
            ),
        ),
        "twm_unmatched_po": (
            (
                "The auditor may consider investigating unmatched purchase orders for goods/services not yet "
                "received, cancelled orders not properly closed, or recording delays."
            ),
        ),
        "twm_unmatched_invoice": (
            (
                "The auditor may consider investigating unmatched invoices for potential unauthorized purchases, "
                "duplicate invoices, or PO-bypass transactions, and obtaining management's explanation for them."
            ),
        ),
        "twm_date_variance": (
            (
                "The auditor may consider evaluating significant date gaps between PO, receipt, and invoice for "
                "cut-off implications and delayed recording anomalies."
            ),
        ),
        "twm_full_match_rate": (
            (
                "The auditor may consider investigating the root cause of the non-match rate, assessing whether "
                "the cause is process-related (manual PO entry errors), system-related (ERP matching logic gaps),"
                " or control-related (inadequate segregation of duties in procurement), and recommending "
                "remediation steps to management to bring the match rate above 85%."
            ),
        ),
        "twm_unmatched_receipt": (
            (
                "The auditor may consider investigating unmatched receiving documents for goods received but not "
                "yet invoiced, establishing whether an accrual is called for on goods received but not invoiced "
                "at period end, and checking whether the receiving log is complete and reconciles to warehouse "
                "records."
            ),
        ),
        "twm_date_gap": (
            (
                "The auditor may consider obtaining the original PO, invoice, and GRN for this transaction, "
                "establishing the actual delivery date and whether the invoice represents goods received, and "
                "investigating whether the invoice date or PO date was altered after original entry. Date gaps "
                "exceeding 60 days are a backdating indicator per ISA 240."
            ),
        ),
        "twm_duplicate_invoice": (
            (
                "The auditor may consider obtaining both invoices sharing the same number and establishing "
                "whether they represent the same transaction posted twice or distinct transactions with reused "
                "numbers. In the case of duplicate billing, it may also consider initiating the vendor credit "
                "memo process."
            ),
        ),
        "twm_quantity_variance": (
            (
                "The auditor may consider obtaining the GRN and invoice for each flagged item, establishing "
                "whether the quantity discrepancy represents a partial shipment, a receiving error, or billing "
                "for undelivered goods, and reconciling quantities to physical count records where available."
            ),
        ),
        "twm_net_overbilling": (
            (
                "The auditor may consider obtaining PO amendment documentation for each HIGH severity variance "
                "and establishing whether price increases were authorized by an approved PO amendment prior to "
                "invoice submission. For variances lacking authorization, it may also consider contacting the "
                "vendor to obtain a credit memo or corrected invoice."
            ),
        ),
    },
    "multi_period": {
        "significant_movement": (
            (
                "The auditor may consider obtaining management's explanation for significant period-over-period "
                "balance changes and corroborating explanations with supporting documentation (contracts, "
                "invoices, board minutes)."
            ),
        ),
        "new_account": (
            (
                "The auditor may consider investigating accounts appearing for the first time, checking for "
                "proper chart-of-accounts authorization, and checking whether the underlying transactions are "
                "properly classified."
            ),
        ),
        "eliminated_account": (
            (
                "The auditor may consider investigating accounts with prior-period balances that are now zero and"
                " establishing whether the elimination reflects legitimate business changes or potential "
                "reclassification errors."
            ),
        ),
        "ratio_trend_change": (
            (
                "The auditor may consider evaluating significant ratio trend changes for underlying drivers and "
                "corroborating them with management inquiry and supporting documentation."
            ),
        ),
        "apc_revenue_increase": (
            (
                "The auditor may consider obtaining detail supporting the revenue increase, assessing whether "
                "growth reflects new contracts, price increases, or volume changes, and cross-referencing to "
                "revenue recognition testing results."
            ),
        ),
        "apc_revenue_decrease": (
            (
                "The auditor may consider investigating the revenue decline and establishing whether the decrease"
                " reflects lost contracts, price reductions, volume decreases, or changes in revenue recognition "
                "policy. Where the decline is material, it may also consider assessing going-concern "
                "implications."
            ),
        ),
        "apc_cogs_increase": (
            (
                "The auditor may consider assessing whether the COGS increase is proportional to revenue growth. "
                "Where COGS growth exceeds revenue growth, which may point to margin compression, the auditor may"
                " consider obtaining management's explanation and assessing whether the cost increases are "
                "recurring or one-time."
            ),
        ),
        "apc_cogs_decrease": (
            (
                "The auditor may consider assessing whether the COGS decrease is consistent with revenue trends. "
                "A COGS decrease alongside stable or increasing revenue may indicate improved efficiency, but "
                "could also indicate incomplete cost recognition or period-end cutoff issues."
            ),
        ),
        "apc_asset_increase": (
            (
                "The auditor may consider obtaining supporting documentation for the asset increase and checking "
                "whether the asset is properly classified and valued per applicable accounting standards."
            ),
        ),
        "apc_asset_decrease": (
            (
                "The auditor may consider investigating the asset decrease, establishing whether the reduction "
                "reflects disposal, impairment, depreciation/amortization, or collection of receivables, and "
                "obtaining supporting documentation for any disposals or write-downs."
            ),
        ),
        "apc_cash_increase": (
            (
                "The auditor may consider inquiring about cash increases above 50%, cross-referencing to the cash"
                " flow statement to establish the source of funds, and assessing whether the increase reflects "
                "operating performance, financing activity, or asset disposals."
            ),
        ),
        "apc_cash_decrease": (
            (
                "The auditor may consider investigating the significant cash decrease, cross-referencing to the "
                "cash flow statement to identify the use of funds, and assessing whether the decrease reflects "
                "debt repayment, capital expenditures, distributions, or operating losses."
            ),
        ),
        "apc_liability_increase": (
            (
                "The auditor may consider investigating the liability increase, establishing whether the increase"
                " reflects new borrowings, accruals, or deferred obligations, and obtaining supporting "
                "documentation for new debt instruments or material accrual changes."
            ),
        ),
        "apc_liability_decrease": (
            (
                "The auditor may consider establishing whether the liability reduction reflects actual payment or"
                " discharge and obtaining supporting documentation (payoff letter, settlement agreement, or "
                "payment records)."
            ),
        ),
        "apc_expense_increase": (
            (
                "The auditor may consider obtaining management's explanation for the expense increase and "
                "assessing whether the increase is consistent with the entity's growth rate and strategic plan. "
                "Where increases are materially above the revenue growth rate, it may also consider additional "
                "inquiry."
            ),
        ),
        "apc_expense_decrease": (
            (
                "The auditor may consider investigating the expense decrease, establishing whether the reduction "
                "reflects cost-cutting measures, reclassification, or incomplete accrual of period expenses, and "
                "assessing whether the decrease is sustainable or temporary."
            ),
        ),
        "apc_sign_change": (
            (
                "The auditor may consider investigating the sign change and establishing whether the change "
                "represents a legitimate reclassification, a correcting entry, or an error. A sign change in a "
                "balance sheet account may indicate that a debit balance became a credit balance (e.g., an asset "
                "account became a liability through over-payment or negative inventory)."
            ),
        ),
        "apc_dormant_account": (
            (
                "The auditor may consider establishing, for each dormant account, whether the zero balance "
                "represents a legitimate closure (debt paid off, asset disposed, account closed) or an account "
                "that was zeroed out improperly, and obtaining management confirmation that each dormant account "
                "has been properly resolved and closed in the chart of accounts if no longer in use."
            ),
        ),
        "apc_closed_account": (
            (
                "The auditor may consider establishing, for closed accounts, whether the balance was properly "
                "disposed of, transferred, or written off prior to closure, and obtaining documentation "
                "supporting the account closure."
            ),
        ),
    },
    "statistical_sampling": {
        "sampling_exception": (
            (
                "The auditor may consider obtaining, for each exception identified in the sample, the source "
                "document and management explanation, and evaluating whether the exception represents an isolated"
                " error or a systematic control deviation."
            ),
        ),
        "projected_misstatement": (
            (
                "The auditor may consider evaluating the projected misstatement against tolerable misstatement. "
                "Where projected misstatement approaches or exceeds tolerable misstatement, it may also consider "
                "expanding the sample or performing alternative procedures."
            ),
        ),
    },
    "currency_conversion": {
        "rate_deviation": (
            (
                "The auditor may consider investigating exchange rate deviations exceeding 1% from published "
                "rates and checking rate source and date alignment per ASC 830 / IAS 21."
            ),
        ),
        "unrealized_gain_loss": (
            (
                "The auditor may consider evaluating significant unrealized foreign currency gains/losses for "
                "proper classification and disclosure and checking the remeasurement methodology."
            ),
        ),
    },
    "preflight": {
        "data_completeness": (
            (
                "The auditor may consider requesting a complete data file addressing identified gaps and checking"
                " that missing columns or incomplete records are resolved before proceeding."
            ),
        ),
        "balance_integrity": (
            (
                "The auditor may consider investigating balance integrity failures (debits not equal to credits) "
                "for extraction errors, partial data, or posting anomalies."
            ),
        ),
    },
    "trial_balance": {
        "rounding_anomaly": (
            (
                "The auditor may consider evaluating round-dollar balances for estimates, accruals, or manual "
                "entries that may indicate placeholder amounts rather than actual transactions."
            ),
        ),
        "natural_balance_violation": (
            (
                "The auditor may consider obtaining management's explanation for accounts with abnormal balance "
                "directions and establishing whether the balance represents a reclassification, offset, or "
                "posting error."
            ),
        ),
        "suspense_account": (
            (
                "The auditor may consider obtaining the transaction detail supporting outstanding suspense "
                "balances, establishing whether items represent unresolved reconciling differences or "
                "reclassifications in progress, and assessing the age of outstanding items."
            ),
        ),
        "concentration_risk_tb": (
            (
                "The auditor may consider evaluating whether disproportionate balance concentration in a single "
                "account reflects the entity's business model or potential classification anomalies."
            ),
        ),
    },
}

# tool -> test_key -> benchmark context shown with the flag
BENCHMARKS: dict[str, dict[str, str]] = {
    "journal_entry_testing": {
        "month_end_clustering": (
            "A clustering rate above 8% in the final 3 business days of the month is a common point at which "
            "auditors inquire whether entries represent legitimate closing activity or potential period-end "
            "earnings management (ISA 240)."
        ),
    },
}


def get_follow_up_procedure(tool: str, test_key: str, *, seed: str = "") -> str:
    """The suggested follow-up for one (tool, test), or "" when none is defined.

    ``seed`` (the client, when known) varies the wording between clients; the
    same seed, tool and test always give the same suggestion.
    """
    variants = PROCEDURES.get(tool, {}).get(test_key, ())
    if not variants:
        return ""
    if len(variants) == 1:
        return variants[0]
    return variants[zlib.crc32(f"{seed}{tool}{test_key}".encode("utf-8")) % len(variants)]


def get_finding_benchmark(tool: str, test_key: str) -> str:
    """Benchmark context for one (tool, test), or "" when none is defined."""
    return BENCHMARKS.get(tool, {}).get(test_key, "")
