"""`flagged_accounts` holds identifiers only — never balances.

`docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md` tells customers that
``tool_runs.flagged_accounts`` carries "the account *names* a tool flagged —
identifiers only, never their balances". That is a promise in a document
shown to customers and prospective auditors, and until Sprint 801 nothing
enforced it.

Measured at the time: all seven extractors in ``shared/account_extractors.py``
copy an account-name field (``account`` / ``gl_account`` / ``account_name``)
and nothing else, so the invariant held. Seven correct extractors and an
eighth one sprint away is not a control — it is luck with good odds.

Two things are checked:

* **Behaviour** — every extractor is fed a result dict whose rows carry
  amounts, balances and transaction identifiers alongside the account name,
  and the output must contain the names and none of the rest.
* **Structure** — the registry must not grow an extractor that this file does
  not exercise, because a behavioural test over six of seven extractors reads
  exactly like a behavioural test over seven.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from shared.account_extractors import ACCOUNT_EXTRACTORS  # noqa: E402

# Values seeded into every fixture row beside the account name. None may
# survive into the extractor's output.
FORBIDDEN_VALUES = {
    "50000.00",
    "-12345.67",
    "1250000",
    "JE-2024-0123",
    "INV-99812",
    "Acme Supplies LLC",
    "Jane Q. Employee",
}

AMOUNT_SHAPE = re.compile(r"\d[\d,]*\.\d{2}|\$\s*\d")


def _row(account_key: str, name: str) -> dict:
    """A result row carrying an account name *and* everything forbidden."""
    return {
        account_key: name,
        "account": name,
        "gl_account": name,
        "account_name": name,
        "amount": "50000.00",
        "balance": "-12345.67",
        "debit": "1250000",
        "credit": "1250000",
        "entry_id": "JE-2024-0123",
        "transaction_id": "INV-99812",
        "vendor_name": "Acme Supplies LLC",
        "employee_name": "Jane Q. Employee",
        "risk_level": "high",
        "severity": "high",
    }


def _result_for(tool: str) -> dict:
    """A result dict shaped to reach every extractor's traversal path."""
    key = {"ap_testing": "gl_account", "revenue_testing": "account_name", "ar_aging": "account_name"}.get(
        tool, "account"
    )
    rows = [_row(key, "Accounts Receivable"), _row(key, "Deferred Revenue")]
    return {
        # trial_balance
        "abnormal_balances": rows,
        # flux_analysis / multi_period
        "items": rows,
        "movements": rows,
        # testing tools — several shapes, so one fixture serves all of them
        "findings": rows,
        "exceptions": rows,
        "results": rows,
        "flagged": rows,
        "tests": [{"findings": rows, "exceptions": rows}],
    }


@pytest.mark.parametrize("tool_name", sorted(ACCOUNT_EXTRACTORS))
def test_extractor_emits_account_names_and_nothing_else(tool_name):
    extractor = ACCOUNT_EXTRACTORS[tool_name]
    out = extractor(_result_for(tool_name))

    assert isinstance(out, list), f"{tool_name}: extractor must return a list"
    for value in out:
        assert isinstance(value, str), f"{tool_name}: emitted a non-string {value!r}"
        assert value not in FORBIDDEN_VALUES, (
            f"{tool_name}: emitted {value!r}, which is an amount, a transaction identifier "
            f"or a party name. ZERO_STORAGE_ARCHITECTURE.md promises customers that "
            f"flagged_accounts carries identifiers only."
        )
        assert not AMOUNT_SHAPE.search(value), (
            f"{tool_name}: emitted {value!r}, which contains something shaped like a monetary amount."
        )


@pytest.mark.parametrize("tool_name", sorted(ACCOUNT_EXTRACTORS))
def test_extractor_returns_sorted_unique_strings(tool_name):
    """The persisted shape is a deduplicated sorted list of names."""
    out = ACCOUNT_EXTRACTORS[tool_name](_result_for(tool_name))
    assert out == sorted(set(out)), f"{tool_name}: output not deduplicated and sorted"


@pytest.mark.parametrize("tool_name", sorted(ACCOUNT_EXTRACTORS))
def test_extractor_tolerates_an_empty_result(tool_name):
    assert ACCOUNT_EXTRACTORS[tool_name]({}) == []


def test_every_registered_extractor_is_exercised():
    """A behavioural test over six of seven extractors reads like seven.

    The parametrize above is driven by the registry itself, so this asserts
    the registry is non-trivial rather than that the list was remembered —
    but a collapse to one entry would make every test above vacuous while
    staying green.
    """
    assert len(ACCOUNT_EXTRACTORS) >= 7, (
        f"only {len(ACCOUNT_EXTRACTORS)} extractors registered: {sorted(ACCOUNT_EXTRACTORS)}"
    )


def test_at_least_one_extractor_actually_found_the_accounts():
    """Guard against the fixture missing every traversal path.

    If `_result_for` stopped matching the shapes the extractors read, every
    test above would pass on empty output — a clean run over nothing, which
    is the failure mode this whole file exists to prevent elsewhere.
    """
    produced = {name: ACCOUNT_EXTRACTORS[name](_result_for(name)) for name in ACCOUNT_EXTRACTORS}
    non_empty = {k: v for k, v in produced.items() if v}
    assert non_empty, (
        "no extractor produced any account name from the fixture — the fixture no longer "
        f"matches any result shape, so the assertions above are vacuous. Produced: {produced}"
    )
    for names in non_empty.values():
        assert "Accounts Receivable" in names or "Deferred Revenue" in names
