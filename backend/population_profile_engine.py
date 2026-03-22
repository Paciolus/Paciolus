"""
Paciolus — TB Population Profile Engine
Sprint 287: Phase XXXIX / Sprint 511: Enrichment

Computes descriptive statistics over a Trial Balance population:
count, mean, median, std dev, percentiles, Gini coefficient,
magnitude histogram, top-10 accounts by absolute balance,
Benford's Law analysis, account type stratification, exception flags,
suggested procedures, and data quality scoring.

Feeds the Statistical Sampling module (Tool 12) for parameter design
and helps auditors understand balance distribution before planning procedures.

Pure-Python engine (stdlib stats + math). Takes pre-aggregated account_balances
dict or raw parsed data from parse_uploaded_file().
"""

import statistics
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from column_detector import detect_columns
from shared.benford import analyze_benford
from shared.parsing_helpers import safe_decimal

# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

MAGNITUDE_BUCKETS = [
    ("Zero (<$0.01)", 0.0, 0.01),
    ("<$1K", 0.01, 1_000),
    ("$1K–$10K", 1_000, 10_000),
    ("$10K–$100K", 10_000, 100_000),
    ("$100K–$1M", 100_000, 1_000_000),
    (">$1M", 1_000_000, float("inf")),
]

# Sprint 511: Updated Gini thresholds per specification
GINI_THRESHOLDS = [
    (0.40, "Low"),
    (0.65, "Moderate"),
]
GINI_HIGH_LABEL = "High"

# Normal balance expectations: Assets & Expenses = Debit (positive net),
# Liabilities, Equity & Revenue = Credit (negative net)
NORMAL_BALANCE_SIGN: dict[str, str] = {
    "asset": "debit",
    "liability": "credit",
    "equity": "credit",
    "revenue": "credit",
    "expense": "debit",
}

# Near-zero threshold for flagging stale/orphaned accounts
NEAR_ZERO_THRESHOLD = 100.0

# Dominant account threshold (% of total population value)
DOMINANT_ACCOUNT_PCT = 10.0

# Account type display order
ACCOUNT_TYPE_ORDER = ["asset", "liability", "equity", "revenue", "expense"]


# ═══════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════


@dataclass
class BucketBreakdown:
    """One row in the magnitude histogram."""

    label: str
    lower: float
    upper: float
    count: int
    sum_abs: float
    percent_count: float

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "lower": self.lower,
            "upper": self.upper if self.upper != float("inf") else None,
            "count": self.count,
            "sum_abs": round(self.sum_abs, 2),
            "percent_count": round(self.percent_count, 2),
        }


@dataclass
class TopAccount:
    """One row in the top-N accounts table."""

    rank: int
    account: str
    category: str
    net_balance: float
    abs_balance: float
    percent_of_total: float
    account_number: str = ""

    def to_dict(self) -> dict:
        result = {
            "rank": self.rank,
            "account": self.account,
            "category": self.category,
            "net_balance": round(self.net_balance, 2),
            "abs_balance": round(self.abs_balance, 2),
            "percent_of_total": round(self.percent_of_total, 2),
        }
        if self.account_number:
            result["account_number"] = self.account_number
        return result


@dataclass
class SectionDensity:
    """Density metrics for one lead sheet section."""

    section_label: str
    section_letters: list[str]
    account_count: int
    section_balance: float  # sum of |net_balance| across section
    balance_per_account: float
    is_sparse: bool  # low account count relative to balance magnitude

    def to_dict(self) -> dict:
        return {
            "section_label": self.section_label,
            "section_letters": self.section_letters,
            "account_count": self.account_count,
            "section_balance": round(self.section_balance, 2),
            "balance_per_account": round(self.balance_per_account, 2),
            "is_sparse": self.is_sparse,
        }


@dataclass
class AccountTypeStratum:
    """One row in the account type stratification table."""

    account_type: str
    count: int
    pct_of_accounts: float
    total_balance: float
    pct_of_population: float

    def to_dict(self) -> dict:
        return {
            "account_type": self.account_type,
            "count": self.count,
            "pct_of_accounts": round(self.pct_of_accounts, 2),
            "total_balance": round(self.total_balance, 2),
            "pct_of_population": round(self.pct_of_population, 2),
        }


@dataclass
class NormalBalanceViolation:
    """An account whose balance sign contradicts its expected normal balance."""

    account_number: str
    account: str
    account_type: str
    expected: str  # "Debit" or "Credit"
    actual: str  # "Debit" or "Credit"
    balance: float

    def to_dict(self) -> dict:
        return {
            "account_number": self.account_number,
            "account": self.account,
            "account_type": self.account_type,
            "expected": self.expected,
            "actual": self.actual,
            "balance": round(self.balance, 2),
        }


@dataclass
class ZeroBalanceAccount:
    """An account with zero or near-zero balance."""

    account_number: str
    account: str
    account_type: str
    balance: float
    is_zero: bool  # True = exactly zero, False = near-zero

    def to_dict(self) -> dict:
        return {
            "account_number": self.account_number,
            "account": self.account,
            "account_type": self.account_type,
            "balance": round(self.balance, 2),
            "is_zero": self.is_zero,
        }


@dataclass
class DominantAccountFlag:
    """An account exceeding the dominant threshold of total population value."""

    account: str
    account_number: str
    balance: float
    pct_of_total: float
    risk_note: str

    def to_dict(self) -> dict:
        return {
            "account": self.account,
            "account_number": self.account_number,
            "balance": round(self.balance, 2),
            "pct_of_total": round(self.pct_of_total, 2),
            "risk_note": self.risk_note,
        }


@dataclass
class ExceptionFlags:
    """All exception flags for the population profile."""

    normal_balance_violations: list[NormalBalanceViolation] = field(default_factory=list)
    zero_balance_accounts: list[ZeroBalanceAccount] = field(default_factory=list)
    near_zero_accounts: list[ZeroBalanceAccount] = field(default_factory=list)
    dominant_accounts: list[DominantAccountFlag] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "normal_balance_violations": [v.to_dict() for v in self.normal_balance_violations],
            "zero_balance_accounts": [z.to_dict() for z in self.zero_balance_accounts],
            "near_zero_accounts": [z.to_dict() for z in self.near_zero_accounts],
            "dominant_accounts": [d.to_dict() for d in self.dominant_accounts],
        }


@dataclass
class SuggestedProcedure:
    """A dynamically generated suggested audit procedure."""

    priority: str  # "High", "Medium", "Low"
    area: str
    procedure: str

    def to_dict(self) -> dict:
        return {
            "priority": self.priority,
            "area": self.area,
            "procedure": self.procedure,
        }


@dataclass
class DataQualityScore:
    """Computed data quality score for the population."""

    overall_score: float  # 0–100
    completeness_score: float
    violation_score: float
    zero_balance_score: float

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 1),
            "completeness_score": round(self.completeness_score, 1),
            "violation_score": round(self.violation_score, 1),
            "zero_balance_score": round(self.zero_balance_score, 1),
        }


# Section groupings for density analysis (aligned with FS builder categories)
DENSITY_SECTIONS: list[tuple[str, list[str]]] = [
    ("Current Assets", ["A", "B", "C", "D"]),
    ("Non-Current Assets", ["E", "F"]),
    ("Current Liabilities", ["G", "H"]),
    ("Non-Current Liabilities", ["I", "J"]),
    ("Equity", ["K"]),
    ("Revenue", ["L"]),
    ("Cost of Sales", ["M"]),
    ("Operating Expenses", ["N"]),
    ("Other Income/Expense", ["O"]),
]

# Sparse threshold: low account count + balance exceeds materiality
SPARSE_ACCOUNT_THRESHOLD = 3


@dataclass
class PopulationProfileReport:
    """Complete population profile result."""

    account_count: int
    total_abs_balance: float
    mean_abs_balance: float
    median_abs_balance: float
    std_dev_abs_balance: float
    min_abs_balance: float
    max_abs_balance: float
    p25: float
    p75: float
    gini_coefficient: float
    gini_interpretation: str
    buckets: list[BucketBreakdown] = field(default_factory=list)
    top_accounts: list[TopAccount] = field(default_factory=list)
    section_density: list[SectionDensity] = field(default_factory=list)
    category_gini: Optional[list[dict]] = None
    # Sprint 511: New fields
    account_type_stratification: list[AccountTypeStratum] = field(default_factory=list)
    benford_analysis: Optional[dict] = None
    exception_flags: Optional[ExceptionFlags] = None
    suggested_procedures: list[SuggestedProcedure] = field(default_factory=list)
    data_quality: Optional[DataQualityScore] = None

    def to_dict(self) -> dict:
        result = {
            "account_count": self.account_count,
            "total_abs_balance": round(self.total_abs_balance, 2),
            "mean_abs_balance": round(self.mean_abs_balance, 2),
            "median_abs_balance": round(self.median_abs_balance, 2),
            "std_dev_abs_balance": round(self.std_dev_abs_balance, 2),
            "min_abs_balance": round(self.min_abs_balance, 2),
            "max_abs_balance": round(self.max_abs_balance, 2),
            "p25": round(self.p25, 2),
            "p75": round(self.p75, 2),
            "gini_coefficient": round(self.gini_coefficient, 4),
            "gini_interpretation": self.gini_interpretation,
            "buckets": [b.to_dict() for b in self.buckets],
            "top_accounts": [t.to_dict() for t in self.top_accounts],
        }
        if self.section_density:
            result["section_density"] = [s.to_dict() for s in self.section_density]
        if self.category_gini is not None:
            result["category_gini"] = self.category_gini
        if self.account_type_stratification:
            result["account_type_stratification"] = [s.to_dict() for s in self.account_type_stratification]
        if self.benford_analysis is not None:
            result["benford_analysis"] = self.benford_analysis
        if self.exception_flags is not None:
            result["exception_flags"] = self.exception_flags.to_dict()
        if self.suggested_procedures:
            result["suggested_procedures"] = [p.to_dict() for p in self.suggested_procedures]
        if self.data_quality is not None:
            result["data_quality"] = self.data_quality.to_dict()
        return result


# ═══════════════════════════════════════════════════════════════
# Helper: Gini coefficient
# ═══════════════════════════════════════════════════════════════


def _compute_gini(sorted_values: list[float]) -> float:
    """Compute Gini coefficient from already-sorted non-negative values.

    Uses the standard formula:
        G = (2 * sum(i * y_i) / (n * sum(y_i))) - (n + 1) / n
    where y values are sorted ascending and i is 1-indexed.

    Returns 0.0 for empty or single-element lists.
    """
    n = len(sorted_values)
    if n < 2:
        return 0.0

    dec_values = [Decimal(str(v)) if isinstance(v, float) else v for v in sorted_values]
    total = sum(dec_values, Decimal("0"))
    if total == 0:
        return 0.0

    weighted_sum = sum(((i + 1) * v for i, v in enumerate(dec_values)), Decimal("0"))
    return float(Decimal(2) * weighted_sum / (n * total) - Decimal(n + 1) / n)


def _interpret_gini(gini: float) -> str:
    """Return human-readable Gini interpretation."""
    for threshold, label in GINI_THRESHOLDS:
        if gini < threshold:
            return label
    return GINI_HIGH_LABEL


# ═══════════════════════════════════════════════════════════════
# Account Type Stratification
# ═══════════════════════════════════════════════════════════════


def _compute_account_type_stratification(
    entries: list[tuple[str, float, float, str, str]],
    total_abs: float,
) -> list[AccountTypeStratum]:
    """Compute per-account-type count, balance, and percentages.

    Args:
        entries: List of (account, net_balance, abs_balance, category, account_number)
        total_abs: Total absolute balance of all accounts.

    Returns:
        List of AccountTypeStratum, one per account type present.
    """
    type_data: dict[str, dict] = {}
    n_total = len(entries)
    total_abs_dec = safe_decimal(total_abs)

    for _acct, _net, abs_bal, category, _acct_num in entries:
        cat_lower = category.lower() if category else "unknown"
        # Normalize to standard types
        for valid in ACCOUNT_TYPE_ORDER:
            if valid in cat_lower:
                cat_lower = valid
                break

        if cat_lower not in type_data:
            type_data[cat_lower] = {"count": 0, "total_balance": Decimal("0")}
        type_data[cat_lower]["count"] += 1
        type_data[cat_lower]["total_balance"] += safe_decimal(abs_bal)

    strata: list[AccountTypeStratum] = []
    for acct_type in ACCOUNT_TYPE_ORDER:
        data = type_data.get(acct_type)
        if data is None:
            continue
        strata.append(
            AccountTypeStratum(
                account_type=acct_type.capitalize(),
                count=data["count"],
                pct_of_accounts=round(data["count"] / n_total * 100, 2) if n_total > 0 else 0.0,
                total_balance=float(data["total_balance"]),
                pct_of_population=float(round(data["total_balance"] / total_abs_dec * 100, 2))
                if total_abs_dec > 0
                else 0.0,
            )
        )

    # Add "Unknown" if present
    unknown = type_data.get("unknown")
    if unknown and unknown["count"] > 0:
        strata.append(
            AccountTypeStratum(
                account_type="Unknown",
                count=unknown["count"],
                pct_of_accounts=round(unknown["count"] / n_total * 100, 2) if n_total > 0 else 0.0,
                total_balance=float(unknown["total_balance"]),
                pct_of_population=float(round(unknown["total_balance"] / total_abs_dec * 100, 2))
                if total_abs_dec > 0
                else 0.0,
            )
        )

    return strata


# ═══════════════════════════════════════════════════════════════
# Exception Flags
# ═══════════════════════════════════════════════════════════════


def _compute_exception_flags(
    entries: list[tuple[str, float, float, str, str]],
    total_abs: float,
) -> ExceptionFlags:
    """Compute normal balance violations, zero/near-zero, and dominant accounts.

    Args:
        entries: List of (account, net_balance, abs_balance, category, account_number)
        total_abs: Total absolute balance of all accounts.
    """
    flags = ExceptionFlags()

    for acct, net, abs_bal, category, acct_num in entries:
        cat_lower = category.lower() if category else "unknown"
        # Normalize category
        normalized = "unknown"
        for valid in ACCOUNT_TYPE_ORDER:
            if valid in cat_lower:
                normalized = valid
                break

        # V-A: Normal balance violations
        expected_sign = NORMAL_BALANCE_SIGN.get(normalized)
        if expected_sign and net != 0.0:
            actual_sign = "debit" if net > 0 else "credit"
            if actual_sign != expected_sign:
                flags.normal_balance_violations.append(
                    NormalBalanceViolation(
                        account_number=acct_num,
                        account=acct,
                        account_type=normalized.capitalize(),
                        expected=expected_sign.capitalize(),
                        actual=actual_sign.capitalize(),
                        balance=net,
                    )
                )

        # V-B: Zero and near-zero balances
        if abs_bal == 0.0:
            flags.zero_balance_accounts.append(
                ZeroBalanceAccount(
                    account_number=acct_num,
                    account=acct,
                    account_type=normalized.capitalize(),
                    balance=net,
                    is_zero=True,
                )
            )
        elif abs_bal <= NEAR_ZERO_THRESHOLD:
            flags.near_zero_accounts.append(
                ZeroBalanceAccount(
                    account_number=acct_num,
                    account=acct,
                    account_type=normalized.capitalize(),
                    balance=net,
                    is_zero=False,
                )
            )

        # V-C: Dominant account risk flags
        if total_abs > 0:
            pct = abs_bal / total_abs * 100
            if pct > DOMINANT_ACCOUNT_PCT:
                flags.dominant_accounts.append(
                    DominantAccountFlag(
                        account=acct,
                        account_number=acct_num,
                        balance=net,
                        pct_of_total=pct,
                        risk_note=(
                            f"Account represents {pct:.1f}% of total population value. "
                            "Apply substantive procedures and obtain management representation."
                        ),
                    )
                )

    # Sort dominant accounts by pct descending
    flags.dominant_accounts.sort(key=lambda d: d.pct_of_total, reverse=True)

    return flags


# ═══════════════════════════════════════════════════════════════
# Suggested Procedures
# ═══════════════════════════════════════════════════════════════


def _generate_suggested_procedures(
    gini: float,
    gini_interp: str,
    top_accounts: list[TopAccount],
    exception_flags: ExceptionFlags,
    benford_result: Optional[dict],
) -> list[SuggestedProcedure]:
    """Generate dynamic audit procedures based on findings."""
    procedures: list[SuggestedProcedure] = []

    # Benford nonconformance
    if benford_result and benford_result.get("passed_prechecks"):
        conformity = benford_result.get("conformity_level", "")
        if conformity in ("nonconforming", "marginally_acceptable"):
            deviated = benford_result.get("most_deviated_digits", [])
            chi_sq = benford_result.get("chi_squared", 0)
            procedures.append(
                SuggestedProcedure(
                    priority="High",
                    area="Benford's Law Deviation",
                    procedure=(
                        f"Investigate {len(deviated)} first-digit anomalies. "
                        f"Chi-square statistic of {chi_sq:.2f} exceeds conformance threshold. "
                        "Consider targeted journal entry testing for digits with largest deviation."
                    ),
                )
            )

    # Normal balance violations
    violations = exception_flags.normal_balance_violations
    if violations:
        procedures.append(
            SuggestedProcedure(
                priority="High",
                area="Normal Balance Violations",
                procedure=(
                    f"{len(violations)} account(s) carry balances contrary to "
                    "their expected normal balance. Obtain management explanation and verify "
                    "intentionality (e.g., contra accounts, reclassifications)."
                ),
            )
        )

    # Concentration risk
    if top_accounts:
        top_name = top_accounts[0].account
        top_pct = top_accounts[0].percent_of_total
        procedures.append(
            SuggestedProcedure(
                priority="High",
                area="Concentration Risk",
                procedure=(
                    f"Gini coefficient of {gini:.4f} indicates {gini_interp} concentration. "
                    f"Top account ({top_name}) represents {top_pct:.1f}% of population. "
                    "Apply substantive procedures to accounts exceeding 10% of total population value."
                ),
            )
        )

    # Dominant accounts
    dominant = exception_flags.dominant_accounts
    if dominant:
        procedures.append(
            SuggestedProcedure(
                priority="High",
                area="Dominant Accounts",
                procedure=(
                    f"{len(dominant)} account(s) exceed 10% of total population value. "
                    "Perform detailed testing on each dominant account, including independent "
                    "substantive analytical procedures per AS 2305."
                ),
            )
        )

    # Zero-balance accounts
    zeros = exception_flags.zero_balance_accounts
    if zeros:
        procedures.append(
            SuggestedProcedure(
                priority="Low",
                area="Zero-Balance Accounts",
                procedure=(
                    f"{len(zeros)} zero-balance account(s) identified. "
                    "Confirm whether accounts should be closed or retained for ongoing activity."
                ),
            )
        )

    # Near-zero accounts
    near_zeros = exception_flags.near_zero_accounts
    if near_zeros:
        procedures.append(
            SuggestedProcedure(
                priority="Low",
                area="Near-Zero Accounts",
                procedure=(
                    f"{len(near_zeros)} near-zero account(s) (balance ≤ ${NEAR_ZERO_THRESHOLD:,.0f}) identified. "
                    "Evaluate whether these represent stale or orphaned accounts."
                ),
            )
        )

    # Sort by priority (High first, then Medium, then Low)
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    procedures.sort(key=lambda p: priority_order.get(p.priority, 1))

    return procedures


# ═══════════════════════════════════════════════════════════════
# Data Quality Score
# ═══════════════════════════════════════════════════════════════


def _compute_data_quality(
    entries: list[tuple[str, float, float, str, str]],
    exception_flags: ExceptionFlags,
    missing_names: int = 0,
    missing_balances: int = 0,
) -> DataQualityScore:
    """Compute data quality score from population metrics.

    Components:
    - Completeness: Penalize for missing account names or balance fields
    - Normal balance violation rate: Penalize for balance sign violations
    - Zero-balance account rate: Penalize for zero-balance accounts
    """
    n = len(entries)
    if n == 0:
        return DataQualityScore(
            overall_score=0.0,
            completeness_score=0.0,
            violation_score=0.0,
            zero_balance_score=0.0,
        )

    # Completeness (40% weight): ratio of complete records
    total_fields = n * 2  # name + balance per account
    missing = missing_names + missing_balances
    completeness = max(0.0, (total_fields - missing) / total_fields * 100) if total_fields > 0 else 100.0

    # Violation rate (35% weight): normal balance violations as % of classified accounts
    classified = sum(1 for _, _, _, cat, _ in entries if cat.lower() in NORMAL_BALANCE_SIGN)
    violation_count = len(exception_flags.normal_balance_violations)
    if classified > 0:
        violation_rate = violation_count / classified
        violation_score = max(0.0, (1.0 - violation_rate) * 100)
    else:
        violation_score = 100.0  # No classified accounts = no violations possible

    # Zero-balance rate (25% weight)
    zero_count = len(exception_flags.zero_balance_accounts)
    zero_rate = zero_count / n if n > 0 else 0.0
    zero_score = max(0.0, (1.0 - zero_rate) * 100)

    overall = completeness * 0.40 + violation_score * 0.35 + zero_score * 0.25

    return DataQualityScore(
        overall_score=overall,
        completeness_score=completeness,
        violation_score=violation_score,
        zero_balance_score=zero_score,
    )


# ═══════════════════════════════════════════════════════════════
# Core computation
# ═══════════════════════════════════════════════════════════════


def compute_population_profile(
    account_balances: dict[str, dict[str, float]],
    classified_accounts: Optional[dict[str, str]] = None,
    account_numbers: Optional[dict[str, str]] = None,
    top_n: int = 10,
    missing_names: int = 0,
    missing_balances: int = 0,
) -> PopulationProfileReport:
    """Compute population profile from pre-aggregated account balances.

    Args:
        account_balances: {account_name: {"debit": float, "credit": float}}
        classified_accounts: Optional {account_name: category_string}
        account_numbers: Optional {account_name: account_number_string}
        top_n: Number of top accounts to include (default 10)
        missing_names: Count of rows with blank/missing account names (BUG-006)
        missing_balances: Count of rows with zero/missing debit and credit (BUG-006)

    Returns:
        PopulationProfileReport with all statistics computed.
    """
    if not account_balances:
        return PopulationProfileReport(
            account_count=0,
            total_abs_balance=0.0,
            mean_abs_balance=0.0,
            median_abs_balance=0.0,
            std_dev_abs_balance=0.0,
            min_abs_balance=0.0,
            max_abs_balance=0.0,
            p25=0.0,
            p75=0.0,
            gini_coefficient=0.0,
            gini_interpretation="Low",
        )

    # Build list of (account, net_balance, abs_balance, category, account_number)
    entries: list[tuple[str, float, float, str, str]] = []
    for acct, bals in account_balances.items():
        net = safe_decimal(bals["debit"]) - safe_decimal(bals["credit"])
        abs_bal = abs(net)
        category = (classified_accounts or {}).get(acct, "Unknown")
        acct_num = (account_numbers or {}).get(acct, "")
        entries.append((acct, float(net), float(abs_bal), category, acct_num))

    abs_values = [e[2] for e in entries]
    n = len(abs_values)

    # Descriptive statistics
    total_abs = sum(abs_values)
    mean_abs = total_abs / n if n > 0 else 0.0
    median_abs = statistics.median(abs_values)

    if n >= 2:
        std_dev = statistics.stdev(abs_values)
    else:
        std_dev = 0.0

    min_abs = min(abs_values)
    max_abs = max(abs_values)

    # Percentiles (P25, P75)
    if n >= 2:
        quantiles = statistics.quantiles(abs_values, n=4)
        p25 = quantiles[0]
        p75 = quantiles[2]
    else:
        p25 = abs_values[0] if n == 1 else 0.0
        p75 = abs_values[0] if n == 1 else 0.0

    # Gini coefficient
    sorted_abs = sorted(abs_values)
    gini = _compute_gini(sorted_abs)
    gini_interp = _interpret_gini(gini)

    # Magnitude buckets
    buckets: list[BucketBreakdown] = []
    for label, lower, upper in MAGNITUDE_BUCKETS:
        bucket_items = [v for v in abs_values if lower <= v < upper]
        count = len(bucket_items)
        sum_abs_bucket = sum(bucket_items)
        pct = (count / n * 100) if n > 0 else 0.0
        buckets.append(
            BucketBreakdown(
                label=label,
                lower=lower,
                upper=upper,
                count=count,
                sum_abs=sum_abs_bucket,
                percent_count=pct,
            )
        )

    # Top-N accounts by absolute balance
    sorted_entries = sorted(entries, key=lambda e: e[2], reverse=True)
    top_accounts: list[TopAccount] = []
    for rank_idx, (acct_name, net_bal, abs_bal_f, cat, acct_num) in enumerate(sorted_entries[:top_n]):
        pct_of_total = (abs_bal_f / total_abs * 100) if total_abs > 0 else 0.0
        top_accounts.append(
            TopAccount(
                rank=rank_idx + 1,
                account=acct_name,
                category=cat,
                net_balance=net_bal,
                abs_balance=abs_bal_f,
                percent_of_total=float(pct_of_total),
                account_number=acct_num,
            )
        )

    # Account type stratification
    stratification = _compute_account_type_stratification(entries, total_abs)

    # Benford's Law analysis (use shared module with relaxed prechecks for populations)
    net_values = [abs(e[1]) for e in entries if e[1] != 0.0]
    benford_result = None
    if net_values:
        benford = analyze_benford(
            net_values,
            total_count=n,
            min_entries=10,  # Relaxed for population profiles
            min_amount=0.01,
        )
        benford_result = benford.to_dict()

    # Exception flags
    exception_flags = _compute_exception_flags(entries, total_abs)

    # Suggested procedures
    procedures = _generate_suggested_procedures(gini, gini_interp, top_accounts, exception_flags, benford_result)

    # Data quality score (BUG-006: pass missing field counts for accurate completeness)
    data_quality = _compute_data_quality(entries, exception_flags, missing_names, missing_balances)

    return PopulationProfileReport(
        account_count=n,
        total_abs_balance=total_abs,
        mean_abs_balance=mean_abs,
        median_abs_balance=median_abs,
        std_dev_abs_balance=std_dev,
        min_abs_balance=min_abs,
        max_abs_balance=max_abs,
        p25=p25,
        p75=p75,
        gini_coefficient=gini,
        gini_interpretation=gini_interp,
        buckets=buckets,
        top_accounts=top_accounts,
        account_type_stratification=stratification,
        benford_analysis=benford_result,
        exception_flags=exception_flags,
        suggested_procedures=procedures,
        data_quality=data_quality,
    )


# ═══════════════════════════════════════════════════════════════
# Section density computation
# ═══════════════════════════════════════════════════════════════


def compute_section_density(
    lead_sheet_grouping: dict,
    materiality_threshold: float = 0.0,
) -> list[SectionDensity]:
    """Compute account density per lead sheet section.

    Args:
        lead_sheet_grouping: Serialized lead sheet grouping dict (summaries list).
        materiality_threshold: Balance above which a sparse section is flagged.

    Returns:
        List of SectionDensity, one per section in DENSITY_SECTIONS.
    """
    # Index summaries by lead sheet letter
    summary_index: dict[str, dict] = {}
    for summary in lead_sheet_grouping.get("summaries", []):
        letter = summary.get("lead_sheet", "")
        if letter:
            summary_index[letter] = summary

    sections: list[SectionDensity] = []
    for label, letters in DENSITY_SECTIONS:
        total_count = 0
        balance_values: list[float] = []

        for letter in letters:
            summary = summary_index.get(letter)
            if summary is None:
                continue
            total_count += summary.get("account_count", 0)
            net_bal = summary.get("net_balance", Decimal("0"))
            balance_values.append(abs(Decimal(str(net_bal)) if isinstance(net_bal, float) else net_bal))

        section_balance = sum(balance_values, Decimal("0"))
        balance_per_acct = section_balance / total_count if total_count > 0 else Decimal("0")
        is_sparse = (
            total_count < SPARSE_ACCOUNT_THRESHOLD
            and section_balance > materiality_threshold
            and total_count > 0  # empty sections aren't sparse
        )

        sections.append(
            SectionDensity(
                section_label=label,
                section_letters=letters,
                account_count=total_count,
                section_balance=float(section_balance),
                balance_per_account=float(balance_per_acct),
                is_sparse=is_sparse,
            )
        )

    return sections


# ═══════════════════════════════════════════════════════════════
# Standalone entry point (for /audit/population-profile endpoint)
# ═══════════════════════════════════════════════════════════════


def run_population_profile(
    column_names: list[str],
    rows: list[dict],
    filename: str,
    classified_accounts: Optional[dict[str, str]] = None,
) -> "PopulationProfileReport":
    """Run population profile from raw parsed file data.

    Uses column_detector.detect_columns() to find account/debit/credit
    columns, then accumulates per-account balances before computing profile.

    Args:
        column_names: Column headers from parse_uploaded_file().
        rows: List of row dicts from parse_uploaded_file().
        filename: Original filename (unused, kept for API consistency).
        classified_accounts: Optional {account_name: category_string} for
            per-category Gini analysis.

    Returns:
        PopulationProfileReport with all statistics computed.
    """
    detection = detect_columns(column_names)
    account_col = detection.account_column
    debit_col = detection.debit_column
    credit_col = detection.credit_column

    if not account_col or not debit_col or not credit_col:
        empty_report = PopulationProfileReport(
            account_count=0,
            total_abs_balance=0.0,
            mean_abs_balance=0.0,
            median_abs_balance=0.0,
            std_dev_abs_balance=0.0,
            min_abs_balance=0.0,
            max_abs_balance=0.0,
            p25=0.0,
            p75=0.0,
            gini_coefficient=0.0,
            gini_interpretation="Low",
        )
        if classified_accounts is not None:
            empty_report.category_gini = []
        return empty_report

    # Accumulate per-account balances, tracking missing fields (BUG-006)
    account_balances: dict[str, dict[str, float]] = {}
    missing_names = 0
    missing_balances = 0
    for row in rows:
        acct = row.get(account_col)
        if acct is None or str(acct).strip() == "":
            missing_names += 1
            continue
        acct_str = str(acct).strip()

        debit = safe_decimal(row.get(debit_col))
        credit = safe_decimal(row.get(credit_col))

        if float(debit) == 0.0 and float(credit) == 0.0:
            missing_balances += 1

        if acct_str not in account_balances:
            account_balances[acct_str] = {"debit": 0.0, "credit": 0.0}
        account_balances[acct_str]["debit"] += float(debit)
        account_balances[acct_str]["credit"] += float(credit)

    profile = compute_population_profile(
        account_balances,
        classified_accounts,
        missing_names=missing_names,
        missing_balances=missing_balances,
    )

    if classified_accounts is not None:
        profile.category_gini = compute_category_gini(
            account_balances,
            classified_accounts,
        )

    return profile


# ═══════════════════════════════════════════════════════════════
# Per-Category Gini Coefficient
# ═══════════════════════════════════════════════════════════════

VALID_CATEGORIES = {"asset", "liability", "equity", "revenue", "expense"}


def compute_category_gini(
    account_balances: dict[str, dict[str, float]],
    classified_accounts: dict[str, str],
) -> list[dict]:
    """Compute Gini coefficient and descriptive statistics per classification category.

    Groups accounts by their classification (asset, liability, equity, revenue,
    expense) and computes concentration metrics for each category with 2+ accounts.

    Args:
        account_balances: {account_name: {"debit": float, "credit": float}}
        classified_accounts: {account_name: category_string}

    Returns:
        List of dicts with category-level Gini coefficients and statistics.
    """
    if not account_balances or not classified_accounts:
        return []

    # Group accounts by category: {category: [(account_name, abs_balance)]}
    category_groups: dict[str, list[tuple[str, float]]] = {}
    for acct, bals in account_balances.items():
        category = classified_accounts.get(acct, "unknown").lower()
        if category not in VALID_CATEGORIES:
            continue

        net = bals.get("debit", 0.0) - bals.get("credit", 0.0)
        abs_bal = abs(net)

        if category not in category_groups:
            category_groups[category] = []
        category_groups[category].append((acct, abs_bal))

    results: list[dict] = []
    for category in sorted(category_groups.keys()):
        entries = category_groups[category]
        if len(entries) < 2:
            continue

        abs_values = [e[1] for e in entries]
        n = len(abs_values)
        total_abs = sum(abs_values)
        mean_bal = total_abs / n
        std_dev = statistics.stdev(abs_values)

        # Gini coefficient
        sorted_abs = sorted(abs_values)
        gini = _compute_gini(sorted_abs)
        gini_label = _interpret_gini(gini)

        # Top 3 accounts by absolute balance
        sorted_entries = sorted(entries, key=lambda e: e[1], reverse=True)
        top_accounts: list[dict] = []
        for rank_idx, (acct, abs_bal) in enumerate(sorted_entries[:3]):
            pct_of_cat = (abs_bal / total_abs * 100) if total_abs > 0 else 0.0
            top_accounts.append(
                {
                    "rank": rank_idx + 1,
                    "account": acct,
                    "abs_balance": round(abs_bal, 2),
                    "percent_of_category": round(pct_of_cat, 2),
                }
            )

        results.append(
            {
                "category": category,
                "gini": round(gini, 4),
                "gini_label": gini_label,
                "account_count": n,
                "total_abs_balance": round(total_abs, 2),
                "mean_balance": round(mean_bal, 2),
                "std_dev": round(std_dev, 2),
                "top_accounts": top_accounts,
            }
        )

    return results
