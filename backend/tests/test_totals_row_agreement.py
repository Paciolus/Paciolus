"""Sprint 883 (review ST-02): preflight and analysis exclude the same totals row.

Preflight excluded a totals row only in the file's last three rows, and only
when every account-identifier column was blank. The streaming auditor zeroed
any row, in any chunk, whose one selected account column was blank and whose
debit and credit were both non-zero — so preflight could approve a set of rows
that analysis then changed, and where a chunk boundary fell changed the result.

``shared.intake_utils`` now owns the rule. Each case below runs the same file
through preflight (the route's parser) and through the streaming auditor at
several chunk sizes; both must exclude the same row and agree on the balance
totals, the account set and the data-quality counts.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from audit.pipeline import audit_trial_balance_streaming
from audit.streaming_auditor import StreamingAuditor
from preflight_engine import run_preflight
from security_utils import process_tb_chunked
from shared.parsing_helpers import parse_amount
from shared.upload_pipeline import parse_uploaded_file

HEADER = "Account,Account Code,Debit,Credit"
BASE = ["Cash,1000,1000,", "Revenue,4000,,600", "Accounts Payable,2000,,400"]


def _csv(lines: list[str]) -> bytes:
    return ("\n".join([HEADER, *lines]) + "\n").encode()


def _preflight(data: bytes):
    columns, rows = parse_uploaded_file(data, "tb.csv")
    return run_preflight(columns, rows, "tb.csv")


def _stream(data: bytes, chunk_size: int) -> tuple[dict, StreamingAuditor]:
    auditor = StreamingAuditor(chunk_size=chunk_size)
    for chunk, rows_so_far in process_tb_chunked(data, "tb.csv", chunk_size):
        auditor.process_chunk(chunk, rows_so_far)
    return auditor.get_balance_result(), auditor


# (name, data rows, rows excluded, total debits, total credits)
CASES = [
    # A totals-shaped row at the start of the file is not a totals row.
    ("totals_shape_at_start_kept", [",,50,50", *BASE], 0, "1050", "1050"),
    # At the end it is: dropped by both.
    ("totals_row_at_end_dropped", [*BASE, ",,1000,1000"], 1, "1000", "1000"),
    # Followed by a trailing blank line inside the three-row window: still dropped.
    ("totals_row_then_blank_row_dropped", [*BASE, ",,1000,1000", ",,,"], 1, "1000", "1000"),
    # Mid-file (and, at chunk size 2, the last row of the first chunk): kept.
    (
        "totals_shape_mid_file_kept",
        ["Cash,1000,1000,", ",,50,50", "Revenue,4000,,600", "AP,2000,,400", "Eq,3000,,"],
        0,
        "1050",
        "1050",
    ),
    # Blank account name but a populated account code: an account, not a total.
    ("blank_name_with_code_kept", [*BASE, ",9999,25,25"], 0, "1025", "1025"),
    # A genuine account carrying both a debit and a credit stays included.
    ("two_sided_account_kept", [*BASE, "Suspense,1999,100,100"], 0, "1100", "1100"),
    # Two totals-shaped rows in the window: only the last is the totals row.
    ("only_last_of_two_candidates_dropped", [*BASE, ",,10,10", ",,1010,1010"], 1, "1010", "1010"),
]


@pytest.mark.parametrize(("name", "lines", "excluded", "debits", "credits"), CASES, ids=[c[0] for c in CASES])
@pytest.mark.parametrize("chunk_size", [1, 2, 3, 4, 1000])
def test_preflight_and_streaming_agree(name, lines, excluded, debits, credits, chunk_size):
    data = _csv(lines)
    pre = _preflight(data)
    stream, auditor = _stream(data, chunk_size)

    # Row disposition
    assert pre.intake is not None
    assert pre.intake.rows_excluded == excluded
    assert stream["totals_rows_excluded"] == excluded

    # Balance totals
    assert pre.balance_check is not None
    assert Decimal(str(pre.balance_check.total_debits)) == Decimal(debits)
    assert Decimal(str(pre.balance_check.total_credits)) == Decimal(credits)
    assert Decimal(stream["total_debits"]) == Decimal(debits)
    assert Decimal(stream["total_credits"]) == Decimal(credits)

    # Row reconciliation: every submitted row is accepted or excluded
    assert stream["row_count"] == len(lines)
    assert pre.row_count == len(lines) - excluded

    # Data-quality counts over the same accepted rows
    assert auditor.missing_balances_count == pre.zero_balance_count
    assert auditor.account_col is not None
    assert auditor.missing_names_count == pre.null_counts.get(auditor.account_col, 0)

    # Account aggregation: the same accepted rows, grouped by account. Rows
    # with a blank account value are left out on both sides — the streaming
    # auditor does not aggregate them (pre-existing; see Sprint 883 notes).
    _, rows = parse_uploaded_file(data, "tb.csv")
    expected: dict[str, list[Decimal]] = {}
    for row in rows:
        key = str(row.get(auditor.account_col) or "").strip()
        if not key or key.lower() == "nan":
            continue
        bucket = expected.setdefault(key, [Decimal(0), Decimal(0)])
        bucket[0] += parse_amount(row.get("Debit"))
        bucket[1] += parse_amount(row.get("Credit"))
    actual = {k: [v["debit"], v["credit"]] for k, v in auditor.account_balances.items()}
    assert actual == expected


@pytest.mark.parametrize("chunk_size", [1, 2, 4, 1000])
def test_pipeline_result_matches_preflight(chunk_size):
    """The analysis route's entry point reports the same exclusion and totals."""
    data = _csv(["Cash,1000,1000,", ",,50,50", "Revenue,4000,,600", "AP,2000,,400", ",,1050,1050"])
    pre = _preflight(data)
    result = audit_trial_balance_streaming(data, "tb.csv", chunk_size=chunk_size)
    assert pre.intake is not None and pre.balance_check is not None
    assert result["totals_rows_excluded"] == pre.intake.rows_excluded == 1
    assert Decimal(result["total_debits"]) == Decimal(str(pre.balance_check.total_debits)) == Decimal("1050")
    assert Decimal(result["total_credits"]) == Decimal(str(pre.balance_check.total_credits)) == Decimal("1050")
    assert result["balanced"] is True and pre.balance_check.balanced is True
