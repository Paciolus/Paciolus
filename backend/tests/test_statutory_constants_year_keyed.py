"""
Sprint 793b item 6 — a guard for the class: no tax module may hold a bare
statutory constant without a year key.

Sprint 793 was one bug in two engines: a flat block of statutory figures
(SS wage base, HSA/401(k) limits, 1099 thresholds) applied to every
``tax_year`` from 2000 to 2099. Sprints 811 and 837 replaced both blocks with
year-keyed tables. This test stops the shape coming back.

**The rule.** In every backend module that handles a ``tax_year`` (engines and
routes, discovered rather than listed), every ``Decimal("<number>")`` literal
must be one of:

1. inside a dict literal keyed by tax years (``{2025: ..., 2026: ...}``), or
   assigned to a name that such a dict references (``_2026_ITEMS``), or
2. listed in ``ALLOWED_BARE`` below with the reason it is not year-selected.

Module-level bare ``int``/``float`` constants are held to the same rule, so the
table cannot be dodged by writing ``176100`` instead of ``Decimal("176100")``.

The allow-list is exact — module, enclosing name and literal value — and
stale entries fail, so it can only shrink silently, never grow. It changes no
figure: the statutory values themselves still await practitioner confirmation
(Sprint 781 / 793b), and are deliberately not touched here.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
_EXCLUDED_DIRS = {"tests", "venv", ".venv", "migrations", "alembic", "__pycache__", "scripts"}
_YEAR_RANGE = range(1990, 2101)

# (module relative path, enclosing top-level name, literal value) -> reason.
# "Enclosing name" is the assigned constant, or the function/class the literal
# sits in. Split into what is not statutory at all and what is statutory but
# knowingly flat, so the second list reads as the debt it is.
NOT_STATUTORY: dict[tuple[str, str, str], str] = {
    ("w2_reconciliation_engine.py", "CENT", "0.01"): "rounding unit",
    ("w2_reconciliation_engine.py", "ZERO", "0"): "zero",
    ("w2_reconciliation_engine.py", "DEFAULT_TOLERANCE", "1.00"): "rounding tolerance, caller-overridable",
    ("w2_reconciliation_engine.py", "_severity_for_diff", "100"): "severity band multiplier on the tolerance",
    ("form_1099_engine.py", "CENT", "0.01"): "rounding unit",
    ("form_1099_engine.py", "ZERO", "0"): "zero",
    ("book_to_tax_engine.py", "CENT", "0.01"): "rounding unit",
    ("book_to_tax_engine.py", "ZERO", "0"): "zero",
    ("book_to_tax_engine.py", "calculate_book_to_tax", "1"): "rate-range validation (0..1)",
    ("book_to_tax_engine.py", "calculate_book_to_tax", "0.0001"): "effective-rate rounding unit",
}

KNOWN_FLAT_STATUTORY: dict[tuple[str, str, str], str] = {
    # Sprint 837 kept these as the labelled pre-2026 figures. The engine resolves
    # the run's thresholds through `thresholds_for_year()`, not these.
    ("form_1099_engine.py", "FORM_THRESHOLDS", "600"): "pre-2026 NEC/MISC; read by tests only",
    ("form_1099_engine.py", "FORM_THRESHOLDS", "10"): "pre-2026 INT; read by tests only",
    ("form_1099_engine.py", "MISC_BOX_THRESHOLDS", "600"): "pre-2026 per-box MISC; unreferenced",
    ("form_1099_engine.py", "MISC_BOX_THRESHOLDS", "10"): "pre-2026 royalties; unreferenced",
    # The $600 floor of the "below the run year's threshold, listed for review"
    # band — named as the legacy figure on purpose (Sprint 837).
    ("form_1099_engine.py", "LEGACY_GENERAL_THRESHOLD", "600"): "review band floor, pre-2026 by name",
    # Schedule M-3 applies at $10M total assets (Form 1120 instructions); the
    # figure has not changed since M-3 was introduced, but it is not year-keyed.
    ("book_to_tax_engine.py", "M3_THRESHOLD_TOTAL_ASSETS", "10000000"): "Schedule M-3 trigger, not year-keyed",
}

ALLOWED_BARE = {**NOT_STATUTORY, **KNOWN_FLAT_STATUTORY}


def _tax_modules() -> list[Path]:
    found = []
    for path in BACKEND.rglob("*.py"):
        if _EXCLUDED_DIRS.intersection(path.relative_to(BACKEND).parts):
            continue
        if "tax_year" in path.read_text(encoding="utf-8"):
            found.append(path)
    return sorted(found)


def _is_year_keyed_dict(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Dict)
        and bool(node.keys)
        and all(isinstance(k, ast.Constant) and type(k.value) is int and k.value in _YEAR_RANGE for k in node.keys)
    )


def _top_level_name(stmt: ast.stmt) -> str:
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return stmt.name
    targets = stmt.targets if isinstance(stmt, ast.Assign) else [getattr(stmt, "target", None)]
    for target in targets:
        if isinstance(target, ast.Name):
            return target.id
    return f"<line {stmt.lineno}>"


def _decimal_literal(node: ast.AST) -> str | None:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Decimal"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    ):
        try:
            Decimal(node.args[0].value)
        except ArithmeticError:
            return None
        return node.args[0].value
    return None


def bare_statutory_literals(source: str) -> tuple[list[tuple[str, str, int]], list[str]]:
    """Return ``(offenders, year_keyed_tables)`` for one module's source.

    ``offenders`` are ``(enclosing_name, literal, lineno)`` for every Decimal
    literal (and module-level numeric constant) not reached through a
    year-keyed table. Allow-listing is the caller's job.
    """
    tree = ast.parse(source)

    year_tables: list[str] = []
    year_keyed_ids: set[int] = set()
    referenced_names: set[str] = set()
    for stmt in tree.body:
        for node in ast.walk(stmt):
            if _is_year_keyed_dict(node):
                year_tables.append(_top_level_name(stmt))
                for sub in ast.walk(node):
                    year_keyed_ids.add(id(sub))
                    if isinstance(sub, ast.Name):
                        referenced_names.add(sub.id)

    offenders: list[tuple[str, str, int]] = []
    for stmt in tree.body:
        name = _top_level_name(stmt)
        if name in referenced_names:
            continue  # e.g. `_2026_ITEMS`, referenced by THRESHOLDS_BY_TABLE_YEAR
        for node in ast.walk(stmt):
            literal = _decimal_literal(node)
            if literal is not None and id(node) not in year_keyed_ids:
                offenders.append((name, literal, node.lineno))
        value = getattr(stmt, "value", None)
        if (
            isinstance(stmt, (ast.Assign, ast.AnnAssign))
            and isinstance(value, ast.Constant)
            and type(value.value) in (int, float)
            and value.value not in _YEAR_RANGE
            and value.value not in (0, 1)
        ):
            offenders.append((name, str(value.value), stmt.lineno))
    return offenders, year_tables


# --- the scanner, proved on synthetic source first ---------------------------


def test_scanner_flags_a_bare_statutory_decimal():
    offenders, _ = bare_statutory_literals('SS_WAGE_BASE = Decimal("176100")\n')
    assert offenders == [("SS_WAGE_BASE", "176100", 1)]


def test_scanner_flags_a_bare_numeric_constant():
    offenders, _ = bare_statutory_literals("SS_WAGE_BASE = 176100\nFIRST_YEAR = 2025\n")
    assert offenders == [("SS_WAGE_BASE", "176100", 1)]


def test_scanner_flags_a_literal_inside_a_function():
    offenders, _ = bare_statutory_literals('def f(x):\n    return x > Decimal("600")\n')
    assert offenders == [("f", "600", 2)]


def test_scanner_accepts_year_keyed_tables_and_what_they_reference():
    source = (
        '_ITEMS_2026 = (Item(Decimal("2000")),)\nLIMITS = {2025: Limits(base=Decimal("176100")), 2026: _ITEMS_2026}\n'
    )
    offenders, tables = bare_statutory_literals(source)
    assert offenders == []
    assert tables == ["LIMITS"]


def test_scanner_does_not_treat_a_non_year_keyed_dict_as_a_table():
    offenders, tables = bare_statutory_literals('BOX = {1: Decimal("600"), 2: Decimal("10")}\n')
    assert tables == []
    assert {o[1] for o in offenders} == {"600", "10"}


# --- the guard ----------------------------------------------------------------


def test_tax_modules_are_discovered():
    """Non-vacuity: the three tax engines (and their routes) are in scope."""
    names = {p.name for p in _tax_modules()}
    assert {"w2_reconciliation_engine.py", "form_1099_engine.py", "book_to_tax_engine.py"} <= names


def test_both_statutory_engines_select_figures_through_a_year_keyed_table():
    tables = {}
    for path in _tax_modules():
        tables[path.name] = bare_statutory_literals(path.read_text(encoding="utf-8"))[1]
    assert "STATUTORY_LIMITS_BY_YEAR" in tables["w2_reconciliation_engine.py"]
    assert "THRESHOLDS_BY_TABLE_YEAR" in tables["form_1099_engine.py"]


def test_no_tax_module_holds_a_bare_statutory_constant():
    offenders = []
    for path in _tax_modules():
        rel = path.relative_to(BACKEND).as_posix()
        for name, literal, lineno in bare_statutory_literals(path.read_text(encoding="utf-8"))[0]:
            if (rel, name, literal) not in ALLOWED_BARE:
                offenders.append(f"{rel}:{lineno} {name} = {literal}")
    assert not offenders, (
        "Statutory figures must be selected by tax year — put them in the module's year-keyed table "
        "(STATUTORY_LIMITS_BY_YEAR / THRESHOLDS_BY_TABLE_YEAR), or, if the literal is genuinely not "
        f"statutory, add it to NOT_STATUTORY with the reason: {offenders}"
    )


def test_allow_list_has_no_stale_entries():
    present = set()
    for path in _tax_modules():
        rel = path.relative_to(BACKEND).as_posix()
        present.update((rel, name, literal) for name, literal, _ in bare_statutory_literals(path.read_text("utf-8"))[0])
    stale = sorted(set(ALLOWED_BARE) - present)
    assert not stale, f"remove allow-list entries that no longer exist: {stale}"
