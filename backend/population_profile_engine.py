"""
Paciolus — TB Population Profile Engine
Sprint 287: Phase XXXIX

Computes descriptive statistics over a Trial Balance population:
count, mean, median, std dev, percentiles, Gini coefficient,
magnitude histogram, and top-10 accounts by absolute balance.

Feeds the Statistical Sampling module (Tool 12) for parameter design
and helps auditors understand balance distribution before planning procedures.

Pure-Python engine (stdlib stats + math). Takes pre-aggregated account_balances
dict or raw parsed data from parse_uploaded_file().
"""

import math
import statistics
from dataclasses import dataclass, field
from typing import Optional

from column_detector import detect_columns

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

GINI_THRESHOLDS = [
    (0.3, "Low"),
    (0.5, "Moderate"),
    (0.7, "High"),
]
GINI_VERY_HIGH_LABEL = "Very High"


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

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "account": self.account,
            "category": self.category,
            "net_balance": round(self.net_balance, 2),
            "abs_balance": round(self.abs_balance, 2),
            "percent_of_total": round(self.percent_of_total, 2),
        }


@dataclass
class SectionDensity:
    """Density metrics for one lead sheet section."""
    section_label: str
    section_letters: list[str]
    account_count: int
    section_balance: float       # sum of |net_balance| across section
    balance_per_account: float
    is_sparse: bool              # low account count relative to balance magnitude

    def to_dict(self) -> dict:
        return {
            "section_label": self.section_label,
            "section_letters": self.section_letters,
            "account_count": self.account_count,
            "section_balance": round(self.section_balance, 2),
            "balance_per_account": round(self.balance_per_account, 2),
            "is_sparse": self.is_sparse,
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

    total = math.fsum(sorted_values)
    if total == 0:
        return 0.0

    weighted_sum = math.fsum((i + 1) * v for i, v in enumerate(sorted_values))
    return (2.0 * weighted_sum) / (n * total) - (n + 1) / n


def _interpret_gini(gini: float) -> str:
    """Return human-readable Gini interpretation."""
    for threshold, label in GINI_THRESHOLDS:
        if gini < threshold:
            return label
    return GINI_VERY_HIGH_LABEL


# ═══════════════════════════════════════════════════════════════
# Core computation
# ═══════════════════════════════════════════════════════════════

def compute_population_profile(
    account_balances: dict[str, dict[str, float]],
    classified_accounts: Optional[dict[str, str]] = None,
    top_n: int = 10,
) -> PopulationProfileReport:
    """Compute population profile from pre-aggregated account balances.

    Args:
        account_balances: {account_name: {"debit": float, "credit": float}}
        classified_accounts: Optional {account_name: category_string}
        top_n: Number of top accounts to include (default 10)

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

    # Build list of (account, net_balance, abs_balance, category)
    entries: list[tuple[str, float, float, str]] = []
    for acct, bals in account_balances.items():
        net = bals["debit"] - bals["credit"]
        abs_bal = abs(net)
        category = (classified_accounts or {}).get(acct, "Unknown")
        entries.append((acct, net, abs_bal, category))

    abs_values = [e[2] for e in entries]
    n = len(abs_values)

    # Descriptive statistics
    total_abs = math.fsum(abs_values)
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
        sum_abs = math.fsum(bucket_items)
        pct = (count / n * 100) if n > 0 else 0.0
        buckets.append(BucketBreakdown(
            label=label, lower=lower, upper=upper,
            count=count, sum_abs=sum_abs, percent_count=pct,
        ))

    # Top-N accounts by absolute balance
    sorted_entries = sorted(entries, key=lambda e: e[2], reverse=True)
    top_accounts: list[TopAccount] = []
    for rank_idx, (acct, net, abs_bal, cat) in enumerate(sorted_entries[:top_n]):
        pct_of_total = (abs_bal / total_abs * 100) if total_abs > 0 else 0.0
        top_accounts.append(TopAccount(
            rank=rank_idx + 1,
            account=acct,
            category=cat,
            net_balance=net,
            abs_balance=abs_bal,
            percent_of_total=pct_of_total,
        ))

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
            net_bal = summary.get("net_balance", 0.0)
            balance_values.append(abs(net_bal))

        section_balance = math.fsum(balance_values)
        balance_per_acct = section_balance / total_count if total_count > 0 else 0.0
        is_sparse = (
            total_count < SPARSE_ACCOUNT_THRESHOLD
            and section_balance > materiality_threshold
            and total_count > 0  # empty sections aren't sparse
        )

        sections.append(SectionDensity(
            section_label=label,
            section_letters=letters,
            account_count=total_count,
            section_balance=section_balance,
            balance_per_account=balance_per_acct,
            is_sparse=is_sparse,
        ))

    return sections


# ═══════════════════════════════════════════════════════════════
# Standalone entry point (for /audit/population-profile endpoint)
# ═══════════════════════════════════════════════════════════════

def run_population_profile(
    column_names: list[str],
    rows: list[dict],
    filename: str,
) -> PopulationProfileReport:
    """Run population profile from raw parsed file data.

    Uses column_detector.detect_columns() to find account/debit/credit
    columns, then accumulates per-account balances before computing profile.

    Args:
        column_names: Column headers from parse_uploaded_file().
        rows: List of row dicts from parse_uploaded_file().
        filename: Original filename (unused, kept for API consistency).

    Returns:
        PopulationProfileReport with all statistics computed.
    """
    detection = detect_columns(column_names)
    account_col = detection.account_column
    debit_col = detection.debit_column
    credit_col = detection.credit_column

    if not account_col or not debit_col or not credit_col:
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

    # Accumulate per-account balances
    account_balances: dict[str, dict[str, float]] = {}
    for row in rows:
        acct = row.get(account_col)
        if acct is None:
            continue
        acct_str = str(acct).strip()
        if not acct_str:
            continue

        try:
            debit = float(row.get(debit_col) or 0)
        except (ValueError, TypeError):
            debit = 0.0
        try:
            credit = float(row.get(credit_col) or 0)
        except (ValueError, TypeError):
            credit = 0.0

        if acct_str not in account_balances:
            account_balances[acct_str] = {"debit": 0.0, "credit": 0.0}
        account_balances[acct_str]["debit"] += debit
        account_balances[acct_str]["credit"] += credit

    return compute_population_profile(account_balances)
