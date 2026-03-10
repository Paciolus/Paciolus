"""
TB Diagnostic Report Constants

Suggested follow-up procedures and concentration benchmarks for the
Trial Balance Diagnostic Intelligence Summary report.

Changes 1 & 4: Suggested procedures per finding, concentration benchmark language.
"""

from classification_rules import (
    EXPENSE_CONCENTRATION_THRESHOLD,
    REVENUE_CONCENTRATION_THRESHOLD,
)

# ─────────────────────────────────────────────────────────────────────
# Change 1: Suggested Follow-Up Procedures (keyed by anomaly_type)
# ─────────────────────────────────────────────────────────────────────

SUGGESTED_PROCEDURES: dict[str, str] = {
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
    "suspense": (
        "Obtain transaction-level detail for the outstanding suspense balance and "
        "confirm each item was cleared or reclassified prior to the report date. "
        "Given the material amount, escalate to engagement partner and consider "
        "whether the balance represents a potential adjusting entry. Document "
        "resolution with supporting evidence in the engagement file."
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
        "partner for evaluation of potential adjusting entry."
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
        "recognition and consider whether an adjusting entry is warranted."
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


def get_tb_suggested_procedure(anomaly: dict, *, is_material: bool = False) -> str:
    """Resolve the suggested procedure for a TB diagnostic finding.

    When is_material=True, returns escalated procedure language appropriate
    for findings above the materiality threshold.

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

    # Direct anomaly_type matches
    if anomaly_type == "suspense_account":
        return procedures["suspense"]

    if anomaly_type == "rounding_anomaly":
        if is_material:
            return procedures["round_dollar"]
        # Differentiate single vs repeated round-dollar pattern
        txn_count = anomaly.get("transaction_count", 0)
        is_repeated = (txn_count and txn_count > 1) or "occurrences" in issue or "multiple" in issue
        if is_repeated:
            return procedures["round_dollar_repeated"]
        return procedures["round_dollar_single"]

    if anomaly_type == "concentration_risk":
        if "intercompany" in account or "intercompany" in issue:
            return procedures["concentration_intercompany"]
        if acc_type == "revenue" or "revenue" in issue:
            return procedures["concentration_revenue"]
        return procedures["concentration_expense"]

    if anomaly_type in ("abnormal_balance", "natural_balance_violation"):
        if "prepaid" in account:
            return procedures["prepaid_credit"]
        if acc_type == "asset" or "asset" in issue:
            # Differentiate AR credit balance from general asset credit balance
            if not is_material and ("receivable" in account or "a/r" in account):
                return procedures["credit_balance_ar"]
            return procedures.get("credit_balance_asset", DEFAULT_PROCEDURE)
        if acc_type == "liability" or "liability" in issue:
            return procedures.get("debit_balance_liability", DEFAULT_PROCEDURE)
        if acc_type == "revenue" or "revenue" in issue:
            return procedures.get("debit_balance_revenue", DEFAULT_PROCEDURE)

    # Sprint 526: New detection categories
    if anomaly_type == "related_party":
        return procedures.get("related_party", DEFAULT_PROCEDURE)

    if anomaly_type == "intercompany_imbalance":
        return procedures.get("intercompany_imbalance", DEFAULT_PROCEDURE)

    if anomaly_type == "equity_signal":
        return procedures.get("equity_signal", DEFAULT_PROCEDURE)

    if is_material:
        return "Review supporting documentation and obtain management explanation. Given the material amount, escalate to engagement partner for assessment of potential adjusting entry and expanded substantive procedures."
    return DEFAULT_PROCEDURE


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
# Change 3: Composite Risk Score for TB Diagnostic
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


def compute_tb_risk_score(
    material_count: int,
    minor_count: int,
    coverage_pct: float,
    has_suspense: bool,
    has_credit_balance_asset: bool,
    *,
    abnormal_balances: list[dict] | None = None,
) -> tuple[int, list[tuple[str, int]]]:
    """Compute composite risk score for the TB Diagnostic report.

    Returns (score, factors) where factors is a list of (name, contribution) tuples.
    When abnormal_balances is provided, material findings appear as individually
    named factor lines instead of an aggregate count.
    """
    factors: list[tuple[str, int]] = []
    score = 0

    # Material findings: named lines when data available, aggregate fallback
    material_pts = material_count * 8
    if material_pts > 0:
        material_items = [ab for ab in (abnormal_balances or []) if ab.get("materiality") == "material"]
        if material_items:
            for ab in material_items:
                label = _describe_material_factor(ab)
                factors.append((label, 8))
        else:
            factors.append((f"Material exceptions ({material_count} findings)", material_pts))
    score += material_pts

    # Minor observations: aggregate (each contributes 2 pts, below named threshold)
    minor_pts = minor_count * 2
    if minor_pts > 0:
        factors.append((f"Minor observations ({minor_count} findings)", minor_pts))
    score += minor_pts

    if coverage_pct >= 50:
        factors.append(("Risk-weighted coverage exceeds 50%", 10))
        score += 10
    elif coverage_pct >= 25:
        factors.append(("Risk-weighted coverage exceeds 25%", 5))
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

    return min(score, 100), factors


def get_risk_tier(score: int) -> str:
    """Map a 0–100 score to a risk tier label."""
    if score <= 10:
        return "low"
    if score <= 25:
        return "moderate"
    if score <= 50:
        return "elevated"
    return "high"
