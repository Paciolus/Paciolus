"""Intake utilities shared between the preflight and diagnostic pipelines.

Sprint 666 introduces row reconciliation + totals-row exclusion + zero-row
blocking across both pipelines. Before this sprint:

- Totals rows (blank account name, populated debit AND credit) were counted
  as data rows, doubling the reported variance on out-of-balance files and
  creating false null-value warnings on clean files.
- Zero-row ingestion (e.g., tb_no_headers.csv where pandas inferred data row 1
  as the header and then failed column detection) silently returned a
  "balanced / low risk / no exceptions" report.
- Raw row counts were not reconciled against parsed row counts, so rows lost
  to pandas header inference were silently dropped.

This module is the single source of truth for those three behaviors. Both
`preflight_engine.run_preflight` and `audit.pipeline.audit_trial_balance_streaming`
import from here; do not duplicate the heuristics elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.parsing_helpers import parse_amount

# ═══════════════════════════════════════════════════════════════
# Row reconciliation
# ═══════════════════════════════════════════════════════════════


@dataclass
class IntakeSummary:
    """Reconciles every raw row against its disposition in the pipeline.

    Invariant: rows_submitted == rows_accepted + rows_rejected + rows_excluded.
    If the invariant does not hold, downstream analysis is running on an
    unaccounted-for row set and the mismatch must be surfaced to the user.

    `notes` is a list of human-readable strings explaining specific row
    dispositions ("Row 41 excluded as totals row", "Row 1 consumed as header
    row because no valid header was detected", etc.) suitable for the
    PreFlight Memo Data Intake Summary section.
    """

    rows_submitted: int
    rows_accepted: int
    rows_rejected: int = 0
    rows_excluded: int = 0
    notes: list[str] = field(default_factory=list)

    def reconciles(self) -> bool:
        return self.rows_submitted == (self.rows_accepted + self.rows_rejected + self.rows_excluded)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows_submitted": self.rows_submitted,
            "rows_accepted": self.rows_accepted,
            "rows_rejected": self.rows_rejected,
            "rows_excluded": self.rows_excluded,
            "reconciles": self.reconciles(),
            "notes": list(self.notes),
        }


def count_raw_data_rows(file_bytes: bytes, filename: str | None) -> int | None:
    """Count non-empty lines in a raw text file (header inclusive).

    For CSV / TSV / TXT: returns the total non-empty line count.
    For other formats (XLSX, PDF, DOCX, ODS, ...): returns None because the
    raw byte count does not correspond to rows in a meaningful way.

    The caller is responsible for deciding whether to subtract one for a
    header line, because that decision depends on whether column detection
    confirmed real headers. For a file like ``tb_no_headers.csv`` the
    "header" line is actually a data row that pandas has consumed; treating
    it as a header would silently drop it from the reconciliation. See
    ``run_preflight`` for the caller-side header adjustment logic.

    A return value of None means "reconciliation is trivial — submitted and
    accepted are equal by definition." A return value of 0 means "the file
    is empty," which is a blocking condition downstream.
    """
    if not filename or "." not in filename:
        return None
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ("csv", "tsv", "txt"):
        return None

    text: str | None = None
    for encoding in ("utf-8", "latin-1"):
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return None

    non_empty = [line for line in text.splitlines() if line.strip()]
    return len(non_empty)


# ═══════════════════════════════════════════════════════════════
# Totals-row detection
# ═══════════════════════════════════════════════════════════════


# "<na>" is how pandas' missing-value marker (pd.NA) prints.
_BLANK_VALUES = frozenset({"", "nan", "none", "null", "n/a", "na", "<na>"})


def _is_blank(value: Any) -> bool:
    """True if the value is null, missing, or a whitespace/blank string.

    Pandas to_dict("records") emits NaN as float('nan') which is tricky to
    compare. We coerce to string and lowercase then match against a
    canonical blank-value set.
    """
    if value is None:
        return True
    try:
        if isinstance(value, float) and value != value:  # NaN
            return True
    except (TypeError, ValueError):
        pass
    s = str(value).strip().lower()
    return s in _BLANK_VALUES


def _collect_account_identifier_columns(column_names: list[str]) -> list[str]:
    """Return every column name that looks like an account identifier.

    Matches on `account`, `acct`, `gl`, or combinations thereof. The totals-row
    detector needs ALL account-identifier columns to be blank on a candidate
    row (not just the primary one), otherwise a legitimate data row with a
    blank Account Name but a populated Account No would be misidentified as
    a totals row.
    """
    hits: list[str] = []
    for col in column_names:
        if col is None:
            continue
        lower = str(col).lower().strip()
        if not lower:
            continue
        if any(token in lower for token in ("account", "acct", "gl ", "gl\t", "ledger")):
            hits.append(col)
        elif lower in {"code", "no", "no.", "number", "name"}:
            # Standalone "Code" / "No" / "Name" columns are typically account
            # identifiers when present in a TB context. Include them.
            hits.append(col)
    return hits


# Sprint 883 (review ST-02): this module is the single owner of the totals-row
# rule. Preflight applies it to the whole row list; the streaming auditor holds
# back candidate rows until it knows the file's last rows, then asks
# ``select_totals_row`` — so both exclude the same row wherever chunk
# boundaries fall.

TOTALS_ROW_WINDOW = 3
"""A totals row is only recognised among the file's last this-many rows."""


def account_identifier_columns(column_names: list[str]) -> list[str]:
    """The columns whose blankness the totals-row rule checks (all of them)."""
    return _collect_account_identifier_columns(column_names)


def is_totals_row_candidate(
    row: dict[str, Any],
    id_cols: list[str],
    debit_col: str | None,
    credit_col: str | None,
) -> bool:
    """True if ``row`` has the shape of a totals row, wherever it sits.

    Every account-identifier column is blank and both the debit and the credit
    read (under the shared amount policy) as non-zero. A legitimate data row may
    have a blank Account Name (e.g., account code 6055 with no name in
    tb_unusual_accounts.csv) but it keeps its code, and a genuine account with
    both a debit and a credit keeps its identifier. Position is decided
    separately by :func:`select_totals_row`.
    """
    if not id_cols or not debit_col or not credit_col:
        return False
    if not all(_is_blank(row.get(col)) for col in id_cols):
        return False
    return parse_amount(row.get(debit_col)) != 0 and parse_amount(row.get(credit_col)) != 0


def select_totals_row(candidate_positions: list[int], row_count: int) -> int | None:
    """Pick the totals row from candidate positions in a file of ``row_count`` rows.

    Only a candidate among the last ``TOTALS_ROW_WINDOW`` rows qualifies (some
    exports put a separator or signature line after the Grand Total); of those,
    the last one is the totals row. Returns its 0-based position, or None.
    """
    in_window = [p for p in candidate_positions if row_count - TOTALS_ROW_WINDOW <= p < row_count]
    return max(in_window) if in_window else None


def detect_totals_row(
    rows: list[dict[str, Any]],
    column_names: list[str],
    debit_col: str | None,
    credit_col: str | None,
) -> int | None:
    """Detect the summary/totals row of a TB given as a complete row list.

    The row is a totals-row candidate (:func:`is_totals_row_candidate`) and is
    the last candidate in the final ``TOTALS_ROW_WINDOW`` rows
    (:func:`select_totals_row`). Returns its index, or None.
    """
    if not rows:
        return None
    id_cols = account_identifier_columns(column_names)
    n = len(rows)
    candidates = [
        idx
        for idx in range(max(0, n - TOTALS_ROW_WINDOW), n)
        if is_totals_row_candidate(rows[idx], id_cols, debit_col, credit_col)
    ]
    return select_totals_row(candidates, n)


def exclude_totals_row(
    rows: list[dict[str, Any]],
    column_names: list[str],
    debit_col: str | None,
    credit_col: str | None,
) -> tuple[list[dict[str, Any]], int | None]:
    """Convenience wrapper: detect and remove the totals row in one call.

    Returns `(filtered_rows, excluded_index)`. If no totals row is detected,
    returns the original list and None. The original `rows` list is never
    mutated.
    """
    idx = detect_totals_row(rows, column_names, debit_col, credit_col)
    if idx is None:
        return rows, None
    return rows[:idx] + rows[idx + 1 :], idx
