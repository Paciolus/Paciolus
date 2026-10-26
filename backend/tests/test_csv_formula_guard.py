"""Sprint 840 (claims review S4): every CSV export escapes formula triggers.

Six exports wrote customer-supplied names (account, user, vendor, entity,
lease, adjustment labels) into CSV unescaped. The fix is structural — one
escaping writer, ``shared.filenames.safe_csv_writer`` — and this file keeps it
structural: it fails if application code constructs a raw ``csv.writer`` or
``csv.DictWriter`` anywhere but the sanctioned wrapper.
"""

import ast
import csv
import io
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest

from shared.filenames import safe_csv_writer

BACKEND = Path(__file__).resolve().parent.parent

# Not export code: a developer fixture generator and an operator script whose
# output never reaches a customer.
_EXEMPT = {
    "shared/filenames.py",  # SafeCsvWriter wraps the one raw writer
    "generate_large_tb.py",
    "scripts/invalidate_legacy_passcode_shares.py",
}
_SKIP_DIRS = {"tests", "venv", ".venv", "migrations", "alembic", "__pycache__"}


def _app_modules():
    # Tracked files only — stray scratch trees (``_pytest_tmp``) are not code.
    listed = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=BACKEND, capture_output=True, text=True, check=True
    ).stdout.split()
    for name in listed:
        rel = Path(name)
        if rel.parts[0] in _SKIP_DIRS or rel.as_posix() in _EXEMPT:
            continue
        yield rel, BACKEND / rel


def test_no_raw_csv_writer_in_application_code():
    offenders = []
    for rel, path in _app_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"writer", "DictWriter"}
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "csv"
            ):
                offenders.append(f"{rel.as_posix()}:{node.lineno}")
    assert not offenders, (
        "Raw csv writers bypass formula escaping — use shared.filenames.safe_csv_writer:\n  " + "\n  ".join(offenders)
    )


def test_guard_scans_the_known_export_modules():
    """A scan that silently scans nothing would pass forever."""
    scanned = {rel.as_posix() for rel, _ in _app_modules()}
    for expected in (
        "account_risk_heatmap_engine.py",
        "sod_engine.py",
        "routes/form_1099.py",
        "routes/intercompany_elimination.py",
        "routes/book_to_tax.py",
        "routes/lease_accounting.py",
        "shared/csv_export.py",
    ):
        assert expected in scanned


def _rows(*rows):
    buf = io.StringIO()
    writer = safe_csv_writer(buf)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().splitlines()


@pytest.mark.parametrize(
    "payload",
    ['=HYPERLINK("http://x","y")', "+cmd", "-2+3", "@SUM(A1)", "|calc", "\tTAB", "=1+1"],
)
def test_text_cells_with_formula_triggers_are_escaped(payload):
    (line,) = _rows([payload])
    assert line.lstrip('"').startswith("'"), line


@pytest.mark.parametrize("number", ["-1,234.56", "-500", "+12", "-0.5%", "1000.00"])
def test_plain_number_strings_stay_numeric(number):
    (parsed,) = csv.reader(_rows([number]))
    assert parsed == [number]


def test_non_string_cells_pass_through():
    assert _rows([Decimal("-12.50"), -3, None, 1.5]) == ["-12.50,-3,,1.5"]


def test_already_escaped_value_is_not_double_escaped():
    assert _rows(["'=x"]) == ["'=x"]


def test_writerows():
    buf = io.StringIO()
    safe_csv_writer(buf).writerows([["=a"], ["b"]])
    assert buf.getvalue().splitlines() == ["'=a", "b"]


def test_heatmap_export_escapes_account_names():
    """One of the six exports the review named, end to end."""
    from account_risk_heatmap_engine import RiskSignal, compute_account_heatmap, heatmap_to_csv

    result = compute_account_heatmap(
        [
            RiskSignal(
                account_number="1000",
                account_name='=HYPERLINK("http://evil","x")',
                source="audit",
                severity="high",
                issue="i",
            )
        ]
    )
    rows = list(csv.reader(io.StringIO(heatmap_to_csv(result))))
    names = [r[3] for r in rows[1:]]
    assert names == ["'" + '=HYPERLINK("http://evil","x")']
