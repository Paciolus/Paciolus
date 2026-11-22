"""
TB Diagnostic Report Constants

Suggested follow-up procedures and concentration benchmarks for the
Trial Balance Diagnostic Intelligence Summary report.

Changes 1 & 4: Suggested procedures per finding, concentration benchmark language.
"""

from decimal import Decimal, InvalidOperation

from classification_rules import (
    EXPENSE_CONCENTRATION_THRESHOLD,
    REVENUE_CONCENTRATION_THRESHOLD,
)

# ─────────────────────────────────────────────────────────────────────
# Change 1: Suggested Follow-Up Procedures (keyed by anomaly_type)
# ─────────────────────────────────────────────────────────────────────

SUGGESTED_PROCEDURES: dict[str, str] = {
    "tb_out_of_balance": (
        "The trial balance does not reconcile: total debits do not equal total credits within "
        "tolerance, and every substantive and analytical result downstream rests on a balanced "
        "trial balance. The auditor may consider obtaining a corrected TB from the client, "
        "comparing it against the general ledger system of record, identifying the journal "
        "entries or postings that produced the imbalance, and documenting the reconciliation in "
        "the engagement file before the downstream testing tools are re-run."
    ),
    "suspense": (
        "The auditor may consider obtaining management's explanation for the uncleared suspense "
        "balance, establishing whether the item was cleared or properly reclassified prior to the "
        "report date, and documenting the resolution in the engagement file."
    ),
    "concentration_revenue": (
        "The auditor may consider applying revenue concentration procedures, obtaining detail of "
        "the transactions comprising this account, and assessing whether the concentration "
        "represents a business risk requiring disclosure under ASC 275-10."
    ),
    "concentration_expense": (
        "The auditor may consider obtaining a breakdown of the transactions comprising this "
        "account and assessing whether the concentration reflects a single vendor or contract "
        "that warrants additional scrutiny."
    ),
    "credit_balance_ar": (
        "The auditor may consider investigating the credit balance in the receivable account, "
        "establishing whether it represents unapplied customer payments, credit memos awaiting "
        "offset, or a posting error, and obtaining the customer subledger detail to establish the "
        "resolution timing."
    ),
    "credit_balance_asset": (
        "The auditor may consider investigating the credit balance in an asset account, "
        "establishing whether it represents an overpayment, unapplied credit memo, or posting "
        "error, and obtaining supporting documentation."
    ),
    "debit_balance_liability": (
        "The auditor may consider investigating the debit balance in a liability account, "
        "establishing whether it represents an overpayment to a vendor, a reclassification issue, "
        "or a posting error, and obtaining the vendor subledger detail and supporting "
        "documentation."
    ),
    "debit_balance_revenue": (
        "The auditor may consider investigating the debit balance in a revenue account, assessing "
        "whether it reflects a returns and allowances contra-account, a revenue reversal, or a "
        "posting error, and obtaining detail of the transactions to check whether the "
        "presentation is proper."
    ),
    "round_dollar_single": (
        "The auditor may consider inspecting supporting documentation for this round-dollar "
        "balance and checking whether the amount reflects an actual invoiced or contracted value "
        "and was not estimated or manually entered as a placeholder."
    ),
    "round_dollar_repeated": (
        "The auditor may consider investigating the repeated round-dollar transaction pattern, "
        "establishing whether the recurring amount reflects a standing order, automated entry, or "
        "estimation practice, and obtaining supporting documentation for a sample of individual "
        "transactions to establish whether amounts are transaction-based rather than estimated."
    ),
    "concentration_intercompany": (
        "The auditor may consider obtaining the intercompany agreement, checking whether the "
        "balance is supported, and assessing whether the balance has been or will be eliminated "
        "in consolidation."
    ),
    "prepaid_credit": (
        "The auditor may consider investigating the credit balance in the prepaid account and "
        "establishing whether the prepaid has been fully expensed, reversed, or represents a "
        "posting error."
    ),
    # Sprint 526: New detection category procedures (Fix 6)
    "related_party": (
        "The auditor may consider checking whether the related party balance is properly "
        "disclosed under ASC 850 (Related Party Disclosures), establishing whether the "
        "transaction was conducted at arm's length, and obtaining the related party agreement to "
        "check whether its terms are consistent with those of unrelated third parties."
    ),
    "intercompany_imbalance": (
        "The auditor may consider investigating the intercompany elimination gap, obtaining the "
        "intercompany reconciliation and establishing whether a corresponding offsetting entry "
        "exists in the counterparty's records, and assessing the impact on consolidated financial "
        "statement presentation."
    ),
    "equity_signal": (
        "The auditor may consider evaluating the equity structure for going concern "
        "considerations, checking for board authorization of dividends declared against an "
        "accumulated deficit, and assessing solvency implications and whether additional "
        "disclosures are required under ASC 205-40 (Going Concern)."
    ),
}

DEFAULT_PROCEDURE = (
    "The auditor may consider reviewing supporting documentation and obtaining management's explanation."
)

# Escalated procedures for material-level findings
MATERIAL_PROCEDURE_UPGRADES: dict[str, str] = {
    "tb_out_of_balance": (
        "The trial balance does not reconcile: total debits do not equal total credits within "
        "tolerance, and every substantive and analytical result downstream rests on a balanced "
        "trial balance. The auditor may consider obtaining a corrected TB from the client, "
        "comparing it against the general ledger system of record, and identifying the journal "
        "entries or postings that produced the imbalance. Given that the imbalance invalidates "
        "every downstream test, it may also consider escalating to the engagement partner "
        "immediately and treating the current run as a failed preview, recording no conclusions "
        "against the affected figures until a reconciled TB is obtained and re-processed."
    ),
    "suspense": (
        "The auditor may consider obtaining transaction-level detail for the outstanding suspense "
        "balance and checking whether each item was cleared or reclassified prior to the report "
        "date. Given the material amount, it may also consider escalating to the engagement "
        "partner for further investigation and documenting the resolution with supporting "
        "evidence in the engagement file."
    ),
    "concentration_revenue": (
        "The auditor may consider performing a disaggregated revenue analysis for this account, "
        "including customer-level detail and contract terms, and assessing whether the "
        "concentration represents a going concern or business continuity risk requiring "
        "disclosure under ASC 275-10. Given the material amount, it may also consider expanding "
        "substantive testing to include confirmation procedures and cutoff testing for this "
        "revenue stream."
    ),
    "concentration_expense": (
        "The auditor may consider obtaining a complete transaction listing for this account and "
        "identifying the underlying vendors or contracts driving the concentration. Given the "
        "material amount, it may also consider targeted vouching of the largest transactions and "
        "assessing whether the concentration indicates related-party activity or inadequate "
        "competitive bidding controls."
    ),
    "credit_balance_asset": (
        "The auditor may consider investigating the credit balance in this asset account by "
        "obtaining the transaction detail and tracing it to source documents. Given the material "
        "amount, it may also consider establishing whether a reclassification to liabilities is "
        "required, assessing the impact on financial statement presentation, and escalating to "
        "the engagement partner for further evaluation."
    ),
    "round_dollar": (
        "The auditor may consider inspecting supporting documentation for all round-dollar "
        "transactions comprising this balance. Given the material amount, it may also consider "
        "targeted vouching to establish whether amounts reflect actual invoiced or contracted "
        "values, and assessing whether the pattern indicates estimation rather than "
        "transaction-based recording, which may affect the reliability of the balance for "
        "substantive testing purposes."
    ),
    "concentration_intercompany": (
        "The auditor may consider obtaining the intercompany agreement and reconciliation for "
        "this balance. Given the material amount, it may also consider checking whether "
        "elimination entries are correctly prepared and the balance is supported by corresponding "
        "entries in the counterparty's records, and assessing transfer pricing documentation and "
        "regulatory compliance."
    ),
    "prepaid_credit": (
        "The auditor may consider investigating the credit balance in this prepaid account by "
        "obtaining the amortization schedule and underlying contract. Given the material amount, "
        "it may also consider establishing whether the prepaid has been fully consumed, "
        "improperly reversed, or requires reclassification, assessing the impact on the period's "
        "expense recognition, and escalating to the engagement partner if further investigation "
        "is warranted."
    ),
    # Sprint 526: New detection category escalated procedures
    "related_party": (
        "The auditor may consider expanded related party procedures for this material balance: "
        "obtaining the underlying agreement and checking for arm's-length pricing, and checking "
        "whether the disclosure under ASC 850 is proper, including nature, terms, and amounts. "
        "Given the material amount, it may also consider assessing whether the transaction "
        "materially affects financial statement presentation and expanding confirmation "
        "procedures."
    ),
    "intercompany_imbalance": (
        "The auditor may consider investigating the material intercompany elimination gap by "
        "obtaining the full intercompany reconciliation for both counterparties and establishing "
        "whether elimination entries are correctly prepared for consolidation. Given the material "
        "amount, it may also consider escalating to the engagement partner and assessing the "
        "impact on consolidated financial statement integrity."
    ),
    "equity_signal": (
        "The auditor may consider evaluating the material equity signals for going concern "
        "implications, obtaining board minutes authorizing dividends declared against the "
        "accumulated deficit, and assessing solvency ratios and capital adequacy. Given the "
        "material amount, it may also consider whether substantial doubt exists about the "
        "entity's ability to continue as a going concern under ASC 205-40."
    ),
    "debit_balance_liability": (
        "The auditor may consider investigating the material debit balance in this liability "
        "account by obtaining vendor detail and reconciliation. Given the material amount, it may "
        "also consider establishing whether a reclassification to assets is required, assessing "
        "the impact on financial statement presentation, and escalating for evaluation of a "
        "potential adjusting entry."
    ),
    "debit_balance_revenue": (
        "The auditor may consider investigating the material debit balance in this revenue "
        "account and establishing whether it is a properly classified contra-revenue account or "
        "represents a reversal error. Given the material amount, it may also consider obtaining "
        "supporting documentation and assessing the impact on revenue recognition and financial "
        "statement presentation."
    ),
}


# BUG-001 fix: Alternate procedures for rotation across reports
SUGGESTED_PROCEDURES_ALT: dict[str, list[str]] = {
    "suspense": [
        "The auditor may consider obtaining the suspense account subledger detail and aging each "
        "outstanding item. Items older than 30 days may call for individual investigation and "
        "management's explanation for continued suspense classification.",
    ],
    "concentration_revenue": [
        "The auditor may consider performing a disaggregated revenue analysis for this account, "
        "including customer-level detail and period-over-period trend comparison, and assessing "
        "whether revenue concentration is consistent with prior periods.",
    ],
    "concentration_expense": [
        "The auditor may consider reviewing the vendor master file for this account, checking "
        "whether the concentrated balance relates to an authorized contract or purchase order, "
        "and assessing whether competitive bidding requirements were followed.",
    ],
    "credit_balance_ar": [
        "The auditor may consider obtaining the customer statement reconciliation for this "
        "receivable account, tracing the credit balance to specific cash receipts, credit memos, "
        "or billing adjustments, and checking for proper offsetting.",
    ],
    "credit_balance_asset": [
        "The auditor may consider tracing the credit balance to source transactions and "
        "establishing whether reclassification to a liability is required for proper financial "
        "statement presentation.",
    ],
    "debit_balance_liability": [
        "The auditor may consider establishing whether the debit balance represents an advance "
        "payment or overpayment requiring reclassification to assets, and obtaining vendor "
        "correspondence and reconciliation.",
    ],
    "debit_balance_revenue": [
        "The auditor may consider obtaining detail of the debits posted to this revenue account "
        "and assessing whether a separate contra-revenue account should be established and the "
        "impact on gross-to-net revenue presentation.",
    ],
    "round_dollar_single": [
        "The auditor may consider comparing the round-dollar balance to approved accrual "
        "schedules and standard journal entry templates to establish whether the amount reflects "
        "a recurring accrual or an ad-hoc estimate that may call for supporting documentation.",
    ],
    "round_dollar_repeated": [
        "The auditor may consider selecting a sample of the recurring round-dollar entries, "
        "tracing them to underlying contracts or invoices, and assessing whether the pattern "
        "indicates an automated accrual that may mask estimation bias.",
    ],
    "concentration_intercompany": [
        "The auditor may consider obtaining the intercompany reconciliation and checking whether "
        "corresponding entries exist in the counterparty's records and whether elimination "
        "entries are prepared for consolidation.",
    ],
    "prepaid_credit": [
        "The auditor may consider obtaining the amortization schedule for this prepaid account, "
        "comparing it to the contract term, and establishing whether the credit indicates full "
        "consumption or an improper reversal.",
    ],
    "related_party": [
        "The auditor may consider inspecting the related party transaction register, checking "
        "whether all balances are properly disclosed, and assessing whether pricing terms are "
        "consistent with arm's-length standards.",
    ],
    "intercompany_imbalance": [
        "The auditor may consider requesting the intercompany reconciliation from both "
        "counterparties and tracing the difference to specific unrecorded or timing entries.",
    ],
    "equity_signal": [
        "The auditor may consider obtaining board minutes for the period, checking for "
        "authorization of equity transactions, and assessing capital adequacy ratios and going "
        "concern indicators under ASC 205-40.",
    ],
}


def get_tb_suggested_procedure(anomaly: dict, *, is_material: bool = False, rotation_index: int = 0) -> str:
    """Resolve the suggested procedure for a TB diagnostic finding.

    When is_material=True, returns escalated procedure language appropriate
    for findings above the materiality threshold.

    BUG-001 fix: rotation_index selects among alternate procedure texts
    so that procedures rotate across reports rather than repeating.

    Matching priority:
    1. Exact anomaly_type match (suspense_account → 'suspense')
    2. Keyword-based fallback on issue text
    3. DEFAULT_PROCEDURE
    """
    anomaly_type = anomaly.get("anomaly_type", "")
    issue = (anomaly.get("issue", "") or "").lower()
    account = (anomaly.get("account", "") or "").lower()
    acc_type = (anomaly.get("type", "") or "").lower()

    procedures = MATERIAL_PROCEDURE_UPGRADES if is_material else SUGGESTED_PROCEDURES

    # Resolve procedure key based on anomaly classification
    proc_key: str | None = None

    if anomaly_type == "tb_out_of_balance":
        proc_key = "tb_out_of_balance"
    elif anomaly_type == "suspense_account":
        proc_key = "suspense"
    elif anomaly_type == "rounding_anomaly":
        if is_material:
            proc_key = "round_dollar"
        else:
            txn_count = anomaly.get("transaction_count", 0)
            is_repeated = (txn_count and txn_count > 1) or "occurrences" in issue or "multiple" in issue
            proc_key = "round_dollar_repeated" if is_repeated else "round_dollar_single"
    elif anomaly_type == "concentration_risk":
        if "intercompany" in account or "intercompany" in issue:
            proc_key = "concentration_intercompany"
        elif acc_type == "revenue" or "revenue" in issue:
            proc_key = "concentration_revenue"
        else:
            proc_key = "concentration_expense"
    elif anomaly_type in ("abnormal_balance", "natural_balance_violation"):
        if "prepaid" in account:
            proc_key = "prepaid_credit"
        elif acc_type == "asset" or "asset" in issue:
            if not is_material and ("receivable" in account or "a/r" in account):
                proc_key = "credit_balance_ar"
            else:
                proc_key = "credit_balance_asset"
        elif acc_type == "liability" or "liability" in issue:
            proc_key = "debit_balance_liability"
        elif acc_type == "revenue" or "revenue" in issue:
            proc_key = "debit_balance_revenue"
    elif anomaly_type == "related_party":
        proc_key = "related_party"
    elif anomaly_type == "intercompany_imbalance":
        proc_key = "intercompany_imbalance"
    elif anomaly_type == "equity_signal":
        proc_key = "equity_signal"

    if proc_key is None:
        if is_material:
            return (
                "The auditor may consider reviewing supporting documentation and obtaining management's "
                "explanation and, given the material amount, escalating to the engagement partner for "
                "further investigation and expanded substantive procedures."
            )
        return DEFAULT_PROCEDURE

    primary = procedures.get(proc_key, DEFAULT_PROCEDURE)

    # BUG-001: Apply rotation using alternate procedures (material procedures
    # don't rotate — they are already escalated language)
    if rotation_index == 0 or is_material:
        return primary
    alts = SUGGESTED_PROCEDURES_ALT.get(proc_key, [])
    if not alts:
        # Sprint 887 (OUT-30): no prefix variation ("To further substantiate the
        # finding, ..."); a test without alternates always reads the same.
        return primary
    all_procedures = [primary, *alts]
    return all_procedures[rotation_index % len(all_procedures)]


# ─────────────────────────────────────────────────────────────────────
# Change 4: Concentration Benchmark Language
# ─────────────────────────────────────────────────────────────────────

CONCENTRATION_BENCHMARKS: dict[str, str] = {
    "revenue": (
        f"Single-account revenue concentration exceeding {REVENUE_CONCENTRATION_THRESHOLD:.0%} is generally "
        "considered elevated under analytical procedures guidance and may "
        "require disclosure assessment."
    ),
    "expense": (
        f"Single-account expense concentration exceeding {EXPENSE_CONCENTRATION_THRESHOLD:.0%} of total expenses "
        "warrants inquiry into the nature and terms of the underlying "
        "transactions."
    ),
    "intercompany": (
        "100% concentration in a single intercompany counterparty should be "
        "confirmed against intercompany agreements and assessed for "
        "elimination in consolidation."
    ),
}


def get_concentration_benchmark(anomaly: dict) -> str | None:
    """Return benchmark language for concentration-type findings, or None.

    Only returns text for concentration_risk anomalies.
    """
    if anomaly.get("anomaly_type") != "concentration_risk":
        return None

    issue = (anomaly.get("issue", "") or "").lower()
    account = (anomaly.get("account", "") or "").lower()
    acc_type = (anomaly.get("type", "") or "").lower()

    if "intercompany" in account or "intercompany" in issue:
        return CONCENTRATION_BENCHMARKS["intercompany"]
    if acc_type == "revenue" or "revenue" in issue:
        return CONCENTRATION_BENCHMARKS["revenue"]
    # Default concentration → expense benchmark
    return CONCENTRATION_BENCHMARKS["expense"]


# ─────────────────────────────────────────────────────────────────────
# Change 3: Composite Diagnostic Score for TB Diagnostic
# ─────────────────────────────────────────────────────────────────────


def _describe_material_factor(ab: dict) -> str:
    """Generate a plain-language factor label for a material finding."""
    account = ab.get("account", "Unknown")
    anomaly_type = ab.get("anomaly_type", "")
    issue = ab.get("issue", "")

    if anomaly_type == "suspense_account":
        return f"{account}: uncleared suspense"
    if anomaly_type == "concentration_risk":
        acc_type = (ab.get("type", "") or "").lower()
        acct_lower = account.lower()
        if "intercompany" in acct_lower or "intercompany" in issue.lower():
            return f"{account}: intercompany concentration"
        if acc_type == "revenue" or "revenue" in issue.lower():
            return f"{account}: revenue concentration"
        return f"{account}: expense concentration"
    if anomaly_type in ("abnormal_balance", "natural_balance_violation"):
        acc_type = (ab.get("type", "") or "").lower()
        if "prepaid" in account.lower():
            return f"{account}: credit balance in prepaid"
        if acc_type == "asset":
            return f"{account}: credit balance in asset account"
        if acc_type == "liability":
            return f"{account}: debit balance in liability account"
        if acc_type == "revenue":
            return f"{account}: debit balance in revenue account"
        return f"{account}: abnormal balance"
    if anomaly_type == "rounding_anomaly":
        return f"{account}: round-dollar pattern"
    # Sprint 526: New detection categories
    if anomaly_type == "related_party":
        return f"{account}: related party balance (ASC 850)"
    if anomaly_type == "intercompany_imbalance":
        return f"{account}: intercompany elimination gap"
    if anomaly_type == "equity_signal":
        return f"{account}: deficit with dividends declared"
    return f"{account}: material exception"


def compute_tb_diagnostic_score(
    material_count: int,
    minor_count: int,
    coverage_pct: float,
    has_suspense: bool,
    has_credit_balance_asset: bool,
    *,
    abnormal_balances: list[dict] | None = None,
    informational_count: int = 0,
    tb_out_of_balance: bool = False,
    tb_imbalance_amount: float | Decimal = 0,
) -> tuple[int, list[tuple[str, int]]]:
    """Compute composite diagnostic score for the TB Diagnostic report.

    This score is an anomaly density index — a weighted sum of anomaly
    counts, concentration ratios, and classification quality.  It is NOT
    a risk assessment under ISA 315 and must not be presented as such.

    Sprint 537: Added informational_count — each contributes +1, grouped into
    a single summary line (not individually listed).

    Sprint 667 Issue 3: `tb_out_of_balance` is a dominant high-weight signal.
    When set it prepends a ``"Trial balance out of balance by $X"`` factor
    worth +60 points to the top of the factors list, guaranteeing the
    composite score lands in the High tier (≥51) regardless of other
    contributors. A TB that does not reconcile invalidates every downstream
    test by definition; no combination of "clean" exception counts should
    obscure that. The +60 weight is chosen so an OOB file with zero other
    anomalies still scores 60 (High); an OOB file with multiple material
    findings scores higher and remains High.

    Returns (score, factors) where factors is a list of (name, contribution) tuples.
    When abnormal_balances is provided, material findings appear as individually
    named factor lines instead of an aggregate count.
    """
    factors: list[tuple[str, int]] = []
    score = 0

    # Sprint 667 Issue 3: Dominant out-of-balance signal. Prepended so it
    # anchors the factor decomposition as P1.
    if tb_out_of_balance:
        try:
            imbalance_abs = abs(Decimal(str(tb_imbalance_amount)))
        except (InvalidOperation, ValueError):
            imbalance_abs = Decimal(0)
        factors.append((f"Trial balance out of balance by ${imbalance_abs:,.2f}", 60))
        score += 60

    # Sprint 530 Fix 9: Top-N named factors + summary remainder.
    # Show the 8 highest-amount material findings individually and collapse the
    # rest into a single summary line.  This keeps the decomposition to ~one page.
    _MAX_NAMED_MATERIAL = 8

    material_pts = material_count * 8
    if material_pts > 0:
        material_items = [ab for ab in (abnormal_balances or []) if ab.get("materiality") == "material"]
        if material_items:
            # Sort by amount descending so the most significant appear first
            ranked = sorted(material_items, key=lambda ab: abs(ab.get("amount", 0)), reverse=True)
            top_items = ranked[:_MAX_NAMED_MATERIAL]
            remainder = ranked[_MAX_NAMED_MATERIAL:]

            for ab in top_items:
                label = _describe_material_factor(ab)
                factors.append((label, 8))

            if remainder:
                # Summarise the remaining material findings in one line
                remainder_pts = len(remainder) * 8
                # Describe the mix of anomaly types in the remainder
                remainder_types: set[str] = set()
                for ab in remainder:
                    at = ab.get("anomaly_type", "")
                    if at == "rounding_anomaly":
                        remainder_types.add("round-number patterns")
                    elif at in ("abnormal_balance", "natural_balance_violation"):
                        remainder_types.add("abnormal balances")
                    elif at == "concentration_risk" or at.endswith("_concentration"):
                        remainder_types.add("concentration risks")
                    elif at == "related_party":
                        remainder_types.add("related party balances")
                    elif at == "intercompany_imbalance":
                        remainder_types.add("intercompany gaps")
                    else:
                        remainder_types.add("minor items flagged")
                type_desc = ", ".join(sorted(remainder_types)) if remainder_types else "additional items flagged"
                factors.append((f"{len(remainder)} additional items flagged ({type_desc})", remainder_pts))
        else:
            factors.append((f"Material exceptions ({material_count} items flagged)", material_pts))
    score += material_pts

    # Minor observations: aggregate (each contributes 2 pts, below named threshold)
    minor_pts = minor_count * 2
    if minor_pts > 0:
        factors.append((f"Minor observations ({minor_count} flagged)", minor_pts))
    score += minor_pts

    # Sprint 537: Informational notes — +1 each, capped at 5 (Sprint 538 F-002)
    # Informational findings are definitionally low-signal; their aggregate
    # should not push scores into "elevated" tier on their own.
    informational_pts = min(informational_count, 5)
    if informational_pts > 0:
        cap_note = " (capped)" if informational_count > 5 else ""
        factors.append((f"{informational_count} informational notes{cap_note}", informational_pts))
    score += informational_pts

    if coverage_pct >= 50:
        factors.append(("Anomaly-weighted coverage exceeds 50%", 10))
        score += 10
    elif coverage_pct >= 25:
        factors.append(("Anomaly-weighted coverage exceeds 25%", 5))
        score += 5

    if has_suspense:
        factors.append(("Suspense balance at period end", 5))
        score += 5

    if has_credit_balance_asset:
        factors.append(("Credit balance in asset account", 3))
        score += 3

    # Sprint 526: Score new anomaly types from abnormal_balances data
    if abnormal_balances:
        has_related_party = any(ab.get("anomaly_type") == "related_party" for ab in abnormal_balances)
        has_intercompany_gap = any(ab.get("anomaly_type") == "intercompany_imbalance" for ab in abnormal_balances)
        has_equity_signal = any(ab.get("anomaly_type") == "equity_signal" for ab in abnormal_balances)

        if has_related_party:
            factors.append(("Related party balances requiring disclosure", 5))
            score += 5
        if has_intercompany_gap:
            factors.append(("Intercompany elimination gap", 5))
            score += 5
        if has_equity_signal:
            factors.append(("Deficit with capital distributions", 5))
            score += 5

    # Sprint 535 P2-1: Reconcile factors to the capped score so the
    # decomposition visually sums to the displayed total.
    capped = min(score, 100)
    if score > 100 and factors:
        # Walk backwards (lowest-priority factors last) and trim.
        reconciled: list[tuple[str, int]] = []
        # Accumulate from the top; once we've consumed the cap, zero the rest.
        running = 0
        for name, pts in factors:
            if running >= capped:
                # Already at cap — this factor contributes 0
                reconciled.append((name, 0))
            elif running + pts > capped:
                # Partially contributes
                actual = capped - running
                if "additional items flagged" in name:
                    reconciled.append((f"{name} (to cap)", actual))
                else:
                    reconciled.append((name, actual))
                running = capped
            else:
                reconciled.append((name, pts))
                running += pts
        # Remove 0-contribution lines for cleanliness
        factors = [(n, p) for n, p in reconciled if p > 0]

    return capped, factors


def get_diagnostic_tier(score: int) -> str:
    """Map a 0–100 diagnostic score to a tier label."""
    if score <= 10:
        return "low"
    if score <= 25:
        return "moderate"
    if score <= 50:
        return "elevated"
    return "high"


# Backward-compatible aliases (internal callers may still use old names)
