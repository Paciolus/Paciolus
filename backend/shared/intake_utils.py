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
from decimal import Decimal, InvalidOperation
from typing import Any

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


_BLANK_VALUES = frozenset({"", "nan", "none", "null", "n/a", "na"})


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


def _to_decimal(value: Any) -> Decimal:
    """Best-effort Decimal coercion for accounting-style values.

    Handles $1,234.56, (1,234.56), -500, bare numerics, and blanks. Never
    raises — unparseable values become Decimal("0"). This is a reconciliation
    helper, not a validator; precision issues are handled at the monetary
    layer.
    """
    if value is None:
        return Decimal(0)
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    if isinstance(value, float):
        if value != value:  # NaN
            return Decimal(0)
        return Decimal(str(value))
    s = str(value).strip()
    if not s:
        return Decimal(0)
    negative = s.startswith("(") and s.endswith(")")
    if negative:
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").replace("€", "").replace("£", "").strip()
    if not s or s == "-":
        return Decimal(0)
    try:
        result = Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal(0)
    return -result if negative else result


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


def detect_totals_row(
    rows: list[dict[str, Any]],
    column_names: list[str],
    debit_col: str | None,
    credit_col: str | None,
) -> int | None:
    """Detect a summary/totals row at the end of the TB data.

    Heuristic (ALL conditions must hold):

    1. The row is in the final three rows of the dataset.
    2. Every account-identifier column on the row is blank.
    3. Both the debit and credit columns have non-zero numeric values.

    Condition 3 is the tight part: a legitimate data row may have a blank
    Account Name (e.g., account code 6055 with no name in tb_unusual_accounts.csv)
    but it will be one-sided (debit OR credit, not both). A totals row is
    two-sided by construction — it sums both columns independently.

    Returns the index of the detected totals row, or None if no row matches.

    Rationale for "last three rows": some TB exports produce Grand Total
    plus a separator + signature line; allowing a small window lets us catch
    the totals row even when trailing non-data rows follow it.
    """
    if not rows or not debit_col or not credit_col:
        return None

    id_cols = _collect_account_identifier_columns(column_names)
    if not id_cols:
        return None

    n = len(rows)
    start = max(0, n - 3)

    for idx in range(n - 1, start - 1, -1):  # scan from the end backwards
        row = rows[idx]

        all_blank = True
        for col in id_cols:
            if not _is_blank(row.get(col)):
                all_blank = False
                break
        if not all_blank:
            continue

        debit_val = _to_decimal(row.get(debit_col))
        credit_val = _to_decimal(row.get(credit_col))

        if debit_val != 0 and credit_val != 0:
            return idx

    return None


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
