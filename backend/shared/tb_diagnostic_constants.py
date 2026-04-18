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
        "STOP — the trial balance does not reconcile. Do not proceed with any "
        "substantive or analytical procedures until total debits equal total "
        "credits within tolerance. Obtain a corrected TB from the client, "
        "compare against the general ledger system of record, and identify the "
        "journal entries or postings that produced the imbalance. Document the "
        "reconciliation in the engagement file before the downstream testing "
        "tools are re-run."
    ),
    "suspense": (
        "Obtain management explanation for uncleared suspense balance; confirm "
        "the item was cleared or properly reclassified prior to the report date. "
        "Document resolution in the engagement file."
    ),
    "concentration_revenue": (
        "Apply revenue concentration procedures; obtain detail of transactions "
        "comprising this account and assess whether concentration represents a "
        "business risk requiring disclosure under ASC 275-10."
    ),
    "concentration_expense": (
        "Obtain breakdown of transactions comprising this account; assess whether "
        "concentration reflects a single vendor or contract that warrants "
        "additional scrutiny."
    ),
    "credit_balance_ar": (
        "Investigate credit balance in the receivable account; determine whether "
        "this represents unapplied customer payments, credit memos awaiting offset, "
        "or a posting error. Obtain the customer subledger detail and confirm "
        "resolution timing."
    ),
    "credit_balance_asset": (
        "Investigate credit balance in an asset account; confirm whether this "
        "represents an overpayment, unapplied credit memo, or posting error. "
        "Obtain supporting documentation."
    ),
    "debit_balance_liability": (
        "Investigate debit balance in a liability account; determine whether this "
        "represents an overpayment to a vendor, a reclassification issue, or a "
        "posting error. Obtain the vendor subledger detail and supporting documentation."
    ),
    "debit_balance_revenue": (
        "Investigate debit balance in a revenue account; assess whether this reflects "
        "a returns and allowances contra-account, a revenue reversal, or a posting error. "
        "Obtain detail of transactions and confirm proper presentation."
    ),
    "round_dollar_single": (
        "Inspect supporting documentation for this round-dollar balance; confirm "
        "the amount reflects an actual invoiced or contracted value and was not "
        "estimated or manually entered as a placeholder."
    ),
    "round_dollar_repeated": (
        "Investigate the repeated round-dollar transaction pattern; determine whether "
        "the recurring amount reflects a standing order, automated entry, or estimation "
        "practice. Obtain supporting documentation for a sample of individual transactions "
        "to confirm amounts are transaction-based rather than estimated."
    ),
    "concentration_intercompany": (
        "Obtain intercompany agreement and confirm balance is supported; assess "
        "whether balance has been or will be eliminated in consolidation."
    ),
    "prepaid_credit": (
        "Investigate credit balance in prepaid account; confirm whether the "
        "prepaid has been fully expensed, reversed, or represents a posting error."
    ),
    # Sprint 526: New detection category procedures (Fix 6)
    "related_party": (
        "Confirm related party balance is properly disclosed under ASC 850 "
        "(Related Party Disclosures). Determine whether the transaction was conducted "
        "at arm's length. Obtain the related party agreement and confirm terms are "
        "consistent with those of unrelated third parties."
    ),
    "intercompany_imbalance": (
        "Investigate the intercompany elimination gap; obtain the intercompany "
        "reconciliation and confirm whether a corresponding offsetting entry exists "
        "in the counterparty's records. Assess impact on consolidated financial "
        "statement presentation."
    ),
    "equity_signal": (
        "Evaluate the equity structure for going concern considerations. Confirm "
        "board authorization for dividends declared against an accumulated deficit. "
        "Assess solvency implications and consider whether additional disclosures "
        "are required under ASC 205-40 (Going Concern)."
    ),
}

DEFAULT_PROCEDURE = "Review supporting documentation and obtain management explanation."

# Escalated procedures for material-level findings
MATERIAL_PROCEDURE_UPGRADES: dict[str, str] = {
    "tb_out_of_balance": (
        "STOP — the trial balance does not reconcile. Do not proceed with any "
        "substantive or analytical procedures until total debits equal total "
        "credits within tolerance. Obtain a corrected TB from the client, "
        "compare against the general ledger system of record, and identify the "
        "journal entries or postings that produced the imbalance. Given that "
        "the imbalance invalidates every downstream test, escalate to the "
        "engagement partner immediately and treat the current run as a failed "
        "preview — do not record any conclusions against the affected figures "
        "until a reconciled TB is obtained and re-processed."
    ),
    "suspense": (
        "Obtain transaction-level detail for the outstanding suspense balance and "
        "confirm each item was cleared or reclassified prior to the report date. "
        "Given the material amount, escalate to engagement partner for further "
        "investigation and document resolution with supporting evidence in the "
        "engagement file."
    ),
    "concentration_revenue": (
        "Perform disaggregated revenue analysis for this account, including "
        "customer-level detail and contract terms. Assess whether the concentration "
        "represents a going concern or business continuity risk requiring disclosure "
        "under ASC 275-10. Given the material amount, expand substantive testing "
        "to include confirmation procedures and cutoff testing for this revenue stream."
    ),
    "concentration_expense": (
        "Obtain a complete transaction listing for this account and identify the "
        "underlying vendors or contracts driving the concentration. Given the material "
        "amount, perform targeted vouching of the largest transactions and assess "
        "whether the concentration indicates related-party activity or inadequate "
        "competitive bidding controls."
    ),
    "credit_balance_asset": (
        "Investigate the credit balance in this asset account by obtaining the "
        "transaction detail and tracing to source documents. Given the material amount, "
        "determine whether a reclassification to liabilities is required and assess "
        "the impact on financial statement presentation. Escalate to engagement "
        "partner for further evaluation."
    ),
    "round_dollar": (
        "Inspect supporting documentation for all round-dollar transactions comprising "
        "this balance. Given the material amount, perform targeted vouching to confirm "
        "amounts reflect actual invoiced or contracted values. Assess whether the "
        "pattern indicates estimation rather than transaction-based recording, which "
        "may affect the reliability of the balance for substantive testing purposes."
    ),
    "concentration_intercompany": (
        "Obtain the intercompany agreement and reconciliation for this balance. "
        "Given the material amount, confirm elimination entries are correctly prepared "
        "and the balance is supported by corresponding entries in the counterparty's "
        "records. Assess transfer pricing documentation and regulatory compliance."
    ),
    "prepaid_credit": (
        "Investigate the credit balance in this prepaid account by obtaining the "
        "amortization schedule and underlying contract. Given the material amount, "
        "determine whether the prepaid has been fully consumed, improperly reversed, "
        "or requires reclassification. Assess the impact on the period's expense "
        "recognition and escalate to engagement partner if further investigation "
        "is warranted."
    ),
    # Sprint 526: New detection category escalated procedures
    "related_party": (
        "Perform expanded related party procedures for this material balance. "
        "Obtain the underlying agreement and confirm arm's-length pricing. "
        "Verify proper disclosure under ASC 850 including nature, terms, and amounts. "
        "Given the material amount, assess whether the transaction materially affects "
        "financial statement presentation and expand confirmation procedures."
    ),
    "intercompany_imbalance": (
        "Investigate the material intercompany elimination gap by obtaining the "
        "full intercompany reconciliation for both counterparties. Confirm whether "
        "elimination entries are correctly prepared for consolidation. Given the "
        "material amount, escalate to engagement partner and assess impact on "
        "consolidated financial statement integrity."
    ),
    "equity_signal": (
        "Evaluate the material equity signals for going concern implications. "
        "Obtain board minutes authorizing dividends declared against the accumulated "
        "deficit. Assess solvency ratios and capital adequacy. Given the material "
        "amount, consider whether substantial doubt exists about the entity's ability "
        "to continue as a going concern under ASC 205-40."
    ),
    "debit_balance_liability": (
        "Investigate the material debit balance in this liability account by obtaining "
        "vendor detail and reconciliation. Given the material amount, determine whether "
        "a reclassification to assets is required and assess the impact on financial "
        "statement presentation. Escalate for evaluation of potential adjusting entry."
    ),
    "debit_balance_revenue": (
        "Investigate the material debit balance in this revenue account. Determine whether "
        "this is a properly classified contra-revenue account or represents a reversal error. "
        "Given the material amount, obtain supporting documentation and assess the impact "
        "on revenue recognition and financial statement presentation."
    ),
}


# BUG-001 fix: Alternate procedures for rotation across reports
SUGGESTED_PROCEDURES_ALT: dict[str, list[str]] = {
    "suspense": [
        "Obtain the suspense account subledger detail and age each outstanding item. "
        "Items older than 30 days require individual investigation and management "
        "explanation for continued suspense classification.",
    ],
    "concentration_revenue": [
        "Perform disaggregated revenue analysis for this account, including "
        "customer-level detail and period-over-period trend comparison. Assess "
        "whether revenue concentration is consistent with prior periods.",
    ],
    "concentration_expense": [
        "Review vendor master file for this account and confirm the concentrated "
        "balance relates to an authorized contract or purchase order. Assess whether "
        "competitive bidding requirements were followed.",
    ],
    "credit_balance_ar": [
        "Obtain customer statement reconciliation for this receivable account. "
        "Trace the credit balance to specific cash receipts, credit memos, or "
        "billing adjustments and confirm proper offsetting.",
    ],
    "credit_balance_asset": [
        "Trace the credit balance to source transactions and confirm whether "
        "reclassification to a liability is required for proper financial "
        "statement presentation.",
    ],
    "debit_balance_liability": [
        "Confirm whether the debit balance represents an advance payment or "
        "overpayment requiring reclassification to assets. Obtain vendor "
        "correspondence and reconciliation.",
    ],
    "debit_balance_revenue": [
        "Obtain detail of the debits posted to this revenue account. Confirm "
        "whether a separate contra-revenue account should be established and "
        "assess impact on gross-to-net revenue presentation.",
    ],
    "round_dollar_single": [
        "Compare the round-dollar balance to approved accrual schedules and "
        "standard journal entry templates to determine whether the amount "
        "reflects a recurring accrual or an ad-hoc estimate requiring "
        "supporting documentation.",
    ],
    "round_dollar_repeated": [
        "Select a sample of the recurring round-dollar entries and trace to "
        "underlying contracts or invoices. Assess whether the pattern indicates "
        "an automated accrual that may mask estimation bias.",
    ],
    "concentration_intercompany": [
        "Obtain the intercompany reconciliation and confirm corresponding "
        "entries exist in the counterparty's records. Verify elimination "
        "entries are prepared for consolidation.",
    ],
    "prepaid_credit": [
        "Obtain the amortization schedule for this prepaid account and compare "
        "to the contract term. Confirm whether the credit indicates full "
        "consumption or an improper reversal.",
    ],
    "related_party": [
        "Inspect the related party transaction register and confirm all "
        "balances are properly disclosed. Assess whether pricing terms are "
        "consistent with arm's-length standards.",
    ],
    "intercompany_imbalance": [
        "Request the intercompany reconciliation from both counterparties "
        "and trace the difference to specific unrecorded or timing entries.",
    ],
    "equity_signal": [
        "Obtain board minutes for the period and confirm authorization for "
        "equity transactions. Assess capital adequacy ratios and going "
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
                "Review supporting documentation and obtain management explanation. "
                "Given the material amount, escalate to engagement partner for further "
                "investigation and expanded substantive procedures."
            )
        return DEFAULT_PROCEDURE

    primary = procedures.get(proc_key, DEFAULT_PROCEDURE)

    # BUG-001: Apply rotation using alternate procedures (material procedures
    # don't rotate — they are already escalated language)
    if rotation_index == 0 or is_material:
        return primary
    alts = SUGGESTED_PROCEDURES_ALT.get(proc_key, [])
    if not alts:
        # No explicit alternates — apply deterministic prefix variation so
        # consecutive reports do not display identical text (BUG-001 fix).
        if rotation_index == 0:
            return primary
        prefixes = [
            "As a priority follow-up action, ",
            "Building on the initial assessment, ",
            "To further substantiate the finding, ",
        ]
        prefix = prefixes[(rotation_index - 1) % len(prefixes)]
        return prefix + primary[0].lower() + primary[1:]
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
                        remainder_types.add("minor findings")
                type_desc = ", ".join(sorted(remainder_types)) if remainder_types else "additional findings"
                factors.append((f"{len(remainder)} additional findings ({type_desc})", remainder_pts))
        else:
            factors.append((f"Material exceptions ({material_count} findings)", material_pts))
    score += material_pts

    # Minor observations: aggregate (each contributes 2 pts, below named threshold)
    minor_pts = minor_count * 2
    if minor_pts > 0:
        factors.append((f"Minor observations ({minor_count} findings)", minor_pts))
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
                if "additional findings" in name:
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
compute_tb_risk_score = compute_tb_diagnostic_score
get_risk_tier = get_diagnostic_tier
