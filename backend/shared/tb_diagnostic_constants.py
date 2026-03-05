"""
TB Diagnostic Report Constants

Suggested follow-up procedures and concentration benchmarks for the
Trial Balance Diagnostic Intelligence Summary report.

Changes 1 & 4: Suggested procedures per finding, concentration benchmark language.
"""

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
        "business risk requiring disclosure."
    ),
    "concentration_expense": (
        "Obtain breakdown of transactions comprising this account; assess whether "
        "concentration reflects a single vendor or contract that warrants "
        "additional scrutiny."
    ),
    "credit_balance_asset": (
        "Investigate credit balance in an asset account; confirm whether this "
        "represents an overpayment, unapplied credit memo, or posting error. "
        "Obtain supporting documentation."
    ),
    "round_dollar": (
        "Inspect supporting documentation for round-dollar transactions; confirm "
        "amounts reflect actual invoiced amounts and were not estimated or "
        "manually entered without support."
    ),
    "concentration_intercompany": (
        "Obtain intercompany agreement and confirm balance is supported; assess "
        "whether balance has been or will be eliminated in consolidation."
    ),
    "prepaid_credit": (
        "Investigate credit balance in prepaid account; confirm whether the "
        "prepaid has been fully expensed, reversed, or represents a posting error."
    ),
}

DEFAULT_PROCEDURE = "Review supporting documentation and obtain management explanation."


def get_tb_suggested_procedure(anomaly: dict) -> str:
    """Resolve the suggested procedure for a TB diagnostic finding.

    Matching priority:
    1. Exact anomaly_type match (suspense_account → 'suspense')
    2. Keyword-based fallback on issue text
    3. DEFAULT_PROCEDURE
    """
    anomaly_type = anomaly.get("anomaly_type", "")
    issue = (anomaly.get("issue", "") or "").lower()
    account = (anomaly.get("account", "") or "").lower()
    acc_type = (anomaly.get("type", "") or "").lower()

    # Direct anomaly_type matches
    if anomaly_type == "suspense_account":
        return SUGGESTED_PROCEDURES["suspense"]

    if anomaly_type == "rounding_anomaly":
        return SUGGESTED_PROCEDURES["round_dollar"]

    if anomaly_type == "concentration_risk":
        if "intercompany" in account or "intercompany" in issue:
            return SUGGESTED_PROCEDURES["concentration_intercompany"]
        if acc_type == "revenue" or "revenue" in issue:
            return SUGGESTED_PROCEDURES["concentration_revenue"]
        # Default concentration to expense
        return SUGGESTED_PROCEDURES["concentration_expense"]

    if anomaly_type in ("abnormal_balance", "natural_balance_violation"):
        if "prepaid" in account:
            return SUGGESTED_PROCEDURES["prepaid_credit"]
        if acc_type == "asset" or "asset" in issue:
            return SUGGESTED_PROCEDURES["credit_balance_asset"]

    return DEFAULT_PROCEDURE


# ─────────────────────────────────────────────────────────────────────
# Change 4: Concentration Benchmark Language
# ─────────────────────────────────────────────────────────────────────

CONCENTRATION_BENCHMARKS: dict[str, str] = {
    "revenue": (
        "Single-account revenue concentration exceeding 30% is generally "
        "considered elevated under analytical procedures guidance and may "
        "require disclosure assessment."
    ),
    "expense": (
        "Single-account expense concentration exceeding 40% of total expenses "
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


def compute_tb_risk_score(
    material_count: int,
    minor_count: int,
    coverage_pct: float,
    has_suspense: bool,
    has_credit_balance_asset: bool,
) -> int:
    """Compute composite risk score for the TB Diagnostic report.

    Returns an integer 0–100.
    """
    score = 0
    score += material_count * 8
    score += minor_count * 2
    if coverage_pct >= 50:
        score += 10
    elif coverage_pct >= 25:
        score += 5
    if has_suspense:
        score += 5
    if has_credit_balance_asset:
        score += 3
    return min(score, 100)


def get_risk_tier(score: int) -> str:
    """Map a 0–100 score to a risk tier label."""
    if score <= 10:
        return "low"
    if score <= 25:
        return "moderate"
    if score <= 50:
        return "elevated"
    return "high"
