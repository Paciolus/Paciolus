"""Account sequence gap detection — forensic signal for suppressed accounts.

Sprint 632: Gaps in numeric account number sequences can reveal accounts
that were renumbered or removed from the chart without explanation. A
typical chart of accounts uses sequential or regularly-spaced numbers
within a category block (e.g. 1000–1999 for Assets). Unexplained gaps
inside a block — particularly where the surrounding accounts are tightly
packed — are a fraud / data-integrity signal worth surfacing.

This rule is complementary to, not a replacement for, the CV-4 check in
``classification_validator.py``. CV-4 flags every gap above a fixed
threshold. This rule is tuned for *suspicious* gaps: it ignores category
boundaries (1999→2000), ignores isolated singleton accounts, and only
fires where the adjacent accounts cluster tightly against the gap edges.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Default sensitivity. A chart with accounts 1100, 1110, 1120, 1130 can
# plausibly jump to 1200 (a new sub-block). But 1100, 1110, 1120, 1130
# then 1200 with the next six neighbours at 1210, 1220, 1230, 1240, 1250,
# 1260 implies the old 1140–1190 range was in use and is now suppressed.
DEFAULT_MIN_GAP = 10
# Maximum "step" between consecutive numbered accounts inside a tight
# cluster. Standard charts increment by 10 within a sub-block, so a step
# of 10 or less qualifies as "clustered"; 20+ is considered sparse and is
# excluded from the gap heuristic.
DEFAULT_CLUSTER_STEP = 10
# Legacy alias retained for callers that imported the old name.
DEFAULT_BOUNDARY_PROXIMITY = DEFAULT_CLUSTER_STEP

# Category block boundaries — standard US chart of accounts. Gaps that
# cross these lines are routine (end of the Asset block → start of the
# Liability block) and must not be flagged as suppression signals.
_CATEGORY_BLOCK_BOUNDARIES: tuple[int, ...] = (
    1000,  # Assets
    2000,  # Liabilities
    3000,  # Equity
    4000,  # Revenue
    5000,  # COGS / Expense
    6000,  # Operating Expenses
    7000,  # Other Income
    8000,  # Other Expense
    9000,  # Extraordinary / memo
)

# Strip "1000 - Cash" / "1000.00 Cash" / "1000-Cash" prefixes down to a
# plain integer. Falls back to None for non-numeric account names.
_LEADING_DIGITS = re.compile(r"^(\d{3,6})")


@dataclass
class AccountGap:
    """A single suppressed-account gap candidate."""

    prev_number: int
    next_number: int
    gap_size: int
    prev_account: str
    next_account: str
    category_block_start: int  # Block start (1000, 2000, ...)
    severity: str  # "high", "medium", "low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "prev_number": self.prev_number,
            "next_number": self.next_number,
            "gap_size": self.gap_size,
            "prev_account": self.prev_account,
            "next_account": self.next_account,
            "category_block_start": self.category_block_start,
            "severity": self.severity,
        }


def _extract_account_number(account: str) -> int | None:
    match = _LEADING_DIGITS.match(account.strip())
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _block_start_for(number: int) -> int:
    """Return the nearest category block start (floor to nearest 1000)."""
    if number < _CATEGORY_BLOCK_BOUNDARIES[0]:
        return 0
    block = (number // 1000) * 1000
    return block


def _crosses_category_boundary(prev_num: int, next_num: int) -> bool:
    """Return True when the gap spans a standard category block."""
    prev_block = _block_start_for(prev_num)
    next_block = _block_start_for(next_num)
    return prev_block != next_block


def detect_account_number_gaps(
    account_names: list[str],
    *,
    min_gap: int = DEFAULT_MIN_GAP,
    cluster_step: int | None = None,
    boundary_proximity: int | None = None,
) -> tuple[list[AccountGap], dict[str, int]]:
    """Detect suspicious gaps in the account number sequence.

    Args:
        account_names: List of account names (numeric prefix expected).
        min_gap: Minimum raw gap size to consider.
        cluster_step: Maximum increment between consecutive accounts for
            them to count as a "cluster". Defaults to 10 (standard chart
            convention). A gap qualifies only when the accounts on both
            sides of it belong to a cluster stepping by ``cluster_step``
            or less — sparse numbering on either side is excluded.
        boundary_proximity: Deprecated alias for ``cluster_step``.

    Returns:
        (list of AccountGap findings, stats dict with 'total_gaps',
        'high_severity', 'medium_severity', 'low_severity').

    The rule fires only when:
      1. The gap is >= ``min_gap``.
      2. The gap does not cross a 1000-boundary category change.
      3. Both neighbours sit within ``cluster_step`` of another
         numbered account on the same side of the gap (tight cluster
         on each side).

    Severity:
      * high    — gap >= 100 with tight clusters on both sides
      * medium  — gap >= 50
      * low     — anything else meeting the firing criteria
    """
    # Resolve the active proximity value, preferring the new name but
    # accepting the legacy argument for backwards compatibility.
    resolved = cluster_step if cluster_step is not None else boundary_proximity
    if resolved is None:
        resolved = DEFAULT_CLUSTER_STEP

    numbers_by_name: list[tuple[int, str]] = []
    for name in account_names:
        num = _extract_account_number(name)
        if num is not None:
            numbers_by_name.append((num, name))

    numbers_by_name.sort(key=lambda pair: pair[0])
    gaps: list[AccountGap] = []
    stats = {
        "total_gaps": 0,
        "high_severity": 0,
        "medium_severity": 0,
        "low_severity": 0,
    }

    if len(numbers_by_name) < 3:
        return gaps, stats

    numbers = [n for n, _ in numbers_by_name]

    for i in range(1, len(numbers_by_name)):
        prev_num, prev_name = numbers_by_name[i - 1]
        next_num, next_name = numbers_by_name[i]
        gap_size = next_num - prev_num

        # The gap must be both >= the raw threshold and strictly greater
        # than the cluster step. A uniform 10-step sequence produces
        # "gaps" of 10 at every step; those are expected spacing, not
        # suppression candidates.
        if gap_size < min_gap or gap_size <= resolved:
            continue
        if _crosses_category_boundary(prev_num, next_num):
            continue

        prev_cluster_distance = prev_num - numbers[i - 2] if i >= 2 else resolved + 1
        next_cluster_distance = numbers[i + 1] - next_num if i + 1 < len(numbers) else resolved + 1

        if prev_cluster_distance > resolved or next_cluster_distance > resolved:
            # One of the neighbours is isolated — the "gap" is just sparse
            # numbering, not a suppression pattern.
            continue

        if gap_size >= 100:
            severity = "high"
            stats["high_severity"] += 1
        elif gap_size >= 50:
            severity = "medium"
            stats["medium_severity"] += 1
        else:
            severity = "low"
            stats["low_severity"] += 1

        gaps.append(
            AccountGap(
                prev_number=prev_num,
                next_number=next_num,
                gap_size=gap_size,
                prev_account=prev_name,
                next_account=next_name,
                category_block_start=_block_start_for(prev_num),
                severity=severity,
            )
        )
        stats["total_gaps"] += 1

    return gaps, stats
