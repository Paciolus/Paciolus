"""Trial Balance Layout Detection — Sprint 669

Distinguishes the three TB column layouts Paciolus needs to handle:

1. ``single_dr_cr`` — the historic default. One Debit and one Credit
   column per row. Every other Paciolus engine assumes this layout.
2. ``multi_column_adjusted`` — adjusting-trial-balance layout with
   Beginning / Adjustments / Ending balance triples. Each balance step
   has its own Debit and Credit column pair. Ending Balance is the
   period-end view that downstream calculations should use.
3. ``net_balance_with_indicator`` — a single signed numeric balance
   column paired with a separate Dr/Cr indicator column that tells
   the reader whether each row is debit-natured or credit-natured.

Detection is purely string-based. It runs against the column header
list and does not inspect row content. The audit pipeline can react
to the detected layout in two ways:

* For ``multi_column_adjusted``, prefer the Ending Balance pair when
  assigning the canonical Debit/Credit roles, so downstream balance
  checks and exception detection run against period-end values.
* For ``net_balance_with_indicator``, recognise both the balance and
  indicator columns as Found (so preflight does not emit a missing-
  credit warning), and surface a ``requires_confirmation`` flag so
  the user can verify the sign convention before the analytical
  engine consumes a derived view.

This module deliberately knows nothing about pandas, the streaming
auditor, or the preflight engine. It returns a small dataclass that
the column detector can fold into ``ColumnDetectionResult``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class TBLayoutMode(Enum):
    """The three trial balance column layouts Paciolus recognises."""

    SINGLE_DR_CR = "single_dr_cr"
    MULTI_COLUMN_ADJUSTED = "multi_column_adjusted"
    NET_BALANCE_WITH_INDICATOR = "net_balance_with_indicator"


@dataclass
class TBLayoutDetection:
    """Result of layout detection.

    ``debit_column`` / ``credit_column`` are the columns the column
    detector should map to the canonical core roles given the detected
    layout. For ``single_dr_cr`` they are ``None`` so the existing
    pattern-based detection runs unchanged.
    ``indicator_column`` is populated only for ``net_balance_with_indicator``
    layouts and names the Dr/Cr indicator column.
    ``supplementary_pairs`` lists the secondary balance pairs (e.g.
    Beginning Balance, Adjustments) for transparency in the report.
    """

    mode: TBLayoutMode
    debit_column: str | None = None
    credit_column: str | None = None
    indicator_column: str | None = None
    supplementary_pairs: list[tuple[str, str]] = field(default_factory=list)
    requires_confirmation: bool = False
    notes: list[str] = field(default_factory=list)


# Step regexes for multi-column adjusted TB columns. Each pattern uses
# word boundaries so common short forms ("Beg Bal Debit", "Adj Debit",
# "Ending Bal Dr") are recognised without false-matching unrelated
# tokens like "begging" or "endpoint."
_ENDING_RE = re.compile(
    r"\b(ending|end|period[\s\-_]*end|year[\s\-_]*end|ytd|closing)\b",
    re.IGNORECASE,
)
_ADJUSTMENTS_RE = re.compile(r"\b(adjust(?:ment)?s?|adj|ja|je\s*adj)\b", re.IGNORECASE)
_BEGINNING_RE = re.compile(
    r"\b(beg(?:in(?:ning)?)?|opening|open|prior[\s\-_]*year|py)\b",
    re.IGNORECASE,
)

# Tokens that identify a column as a Debit or Credit role within a
# multi-column adjusted layout.
_DEBIT_HINT_RE = re.compile(r"\b(debit|debits|dr)\b", re.IGNORECASE)
_CREDIT_HINT_RE = re.compile(r"\b(credit|credits|cr)\b", re.IGNORECASE)

# Net balance / indicator detection
_NET_BALANCE_RE = re.compile(r"\b(net\s*balance|balance|amount|net\s*amt|signed\s*balance)\b", re.IGNORECASE)
_DR_CR_INDICATOR_RE = re.compile(
    r"^\s*(dr\s*[/\-]\s*cr|debit\s*[/\-]\s*credit|sign|nature|side|indicator)\s*$",
    re.IGNORECASE,
)


def _normalise(name: str) -> str:
    """Collapse whitespace (including newlines from PDF extraction)."""
    return re.sub(r"\s+", " ", str(name)).strip()


def _classify_step(norm: str) -> str:
    """Classify a column header into a multi-column step bucket.

    Order matters: the ending check runs before adjustments and
    beginning so "Ending Adjustments" (an unusual but plausible label)
    sorts as ending. Returns "unknown" when no token fires.
    """
    if _ENDING_RE.search(norm):
        return "ending"
    if _ADJUSTMENTS_RE.search(norm):
        return "adjustments"
    if _BEGINNING_RE.search(norm):
        return "beginning"
    return "unknown"


def detect_tb_layout(column_names: list[str]) -> TBLayoutDetection:
    """Inspect column headers and return the detected layout.

    The default return is ``TBLayoutMode.SINGLE_DR_CR`` with no column
    suggestions, which means the standard pattern-based column
    detector should run unchanged.
    """
    if not column_names:
        return TBLayoutDetection(mode=TBLayoutMode.SINGLE_DR_CR)

    normalised = [(orig, _normalise(orig)) for orig in column_names]

    # ─────────────────────────────────────────────────────────
    # Path A: net_balance_with_indicator
    # ─────────────────────────────────────────────────────────
    # Recognised when there is exactly one column whose header looks
    # like a balance/amount column AND a separate indicator column.
    # We require the indicator column to use a recognised vocabulary
    # so we do not misclassify a regular "Description" column.
    balance_candidates = [(orig, norm) for orig, norm in normalised if _NET_BALANCE_RE.search(norm)]
    indicator_candidates = [(orig, norm) for orig, norm in normalised if _DR_CR_INDICATOR_RE.match(norm)]
    if len(balance_candidates) == 1 and len(indicator_candidates) == 1:
        debit_dr_pair_count = sum(1 for _, n in normalised if _DEBIT_HINT_RE.search(n) or _CREDIT_HINT_RE.search(n))
        # If there are ALSO multiple debit/credit-named columns in the
        # file then this is a multi-column TB — fall through to Path B.
        if debit_dr_pair_count <= 2:
            balance_col = balance_candidates[0][0]
            indicator_col = indicator_candidates[0][0]
            return TBLayoutDetection(
                mode=TBLayoutMode.NET_BALANCE_WITH_INDICATOR,
                debit_column=balance_col,
                credit_column=indicator_col,
                indicator_column=indicator_col,
                requires_confirmation=True,
                notes=[
                    "Net balance layout detected — single signed balance column "
                    "paired with a Dr/Cr indicator. Confirm the sign convention "
                    "before downstream testing.",
                ],
            )

    # ─────────────────────────────────────────────────────────
    # Path B: multi_column_adjusted
    # ─────────────────────────────────────────────────────────
    # Recognised when at least one Debit AND one Credit column carries
    # an Ending / Beginning / Adjustments token (multiple balance steps).
    debit_columns = [(orig, norm) for orig, norm in normalised if _DEBIT_HINT_RE.search(norm)]
    credit_columns = [(orig, norm) for orig, norm in normalised if _CREDIT_HINT_RE.search(norm)]

    if len(debit_columns) >= 2 and len(credit_columns) >= 2:
        ending_debit = next((orig for orig, n in debit_columns if _classify_step(n) == "ending"), None)
        ending_credit = next((orig for orig, n in credit_columns if _classify_step(n) == "ending"), None)

        # Multi-column layout requires AT LEAST one full Ending pair.
        if ending_debit and ending_credit:
            supplementary: list[tuple[str, str]] = []
            for step in ("beginning", "adjustments"):
                d = next((orig for orig, n in debit_columns if _classify_step(n) == step), None)
                c = next((orig for orig, n in credit_columns if _classify_step(n) == step), None)
                if d and c:
                    supplementary.append((d, c))
            return TBLayoutDetection(
                mode=TBLayoutMode.MULTI_COLUMN_ADJUSTED,
                debit_column=ending_debit,
                credit_column=ending_credit,
                supplementary_pairs=supplementary,
                notes=[
                    "Multi-column adjusted TB layout detected. Ending Balance "
                    "Debit/Credit are mapped as primary; Beginning Balance and "
                    "Adjustments columns are surfaced for transparency but are "
                    "not used in downstream balance verification.",
                ],
            )

    # ─────────────────────────────────────────────────────────
    # Default
    # ─────────────────────────────────────────────────────────
    return TBLayoutDetection(mode=TBLayoutMode.SINGLE_DR_CR)
