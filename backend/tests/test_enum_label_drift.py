"""The enum label drift guard — Sprint 741d.

`sa.Enum(SomePyEnum)` with no `values_callable` binds the member **name**. A
migration spelling the same type lowercase builds a database the ORM cannot
write to. Sprint 741a traced an hourly production failure to exactly that.

The suite cannot see this on its own: SQLite has no enum types, so the column
is a VARCHAR, every label is accepted, and ~9,000 passing tests say nothing
about whether the chain and the ORM agree. That is why the check is static.

Three claims are tested, and the middle one is the one that has bitten this
session repeatedly:

1. The guard's verdict matches the recorded baseline.
2. **The parser read everything it claims to have read.** A parser that
   silently skips a construct shrinks the comparison without shrinking the
   confidence — the guard still prints "no new drift".
3. New drift fails, and fixed drift also fails until the baseline is tightened.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"
GUARD_PATH = BACKEND / "guards" / "enum_label_drift.py"
VERSIONS = BACKEND / "migrations" / "alembic" / "versions"


def _load_guard():
    spec = importlib.util.spec_from_file_location("enum_label_drift_guard", GUARD_PATH)
    assert spec and spec.loader, "could not load the guard module"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_guard()


# ---------------------------------------------------------------------------
# 1. The verdict matches the baseline
# ---------------------------------------------------------------------------


def test_no_enum_drift_beyond_the_recorded_baseline():
    """The whole point: the known-bad set must not grow.

    A new entry here means someone added a migration whose labels disagree
    with what the ORM binds. On PostgreSQL that type's writes fail; on SQLite
    nothing happens, so no other test will tell you.
    """
    drifting, details, _unresolved, _stats = guard.compute_drift()
    new = sorted(drifting - guard.KNOWN_DRIFT)
    assert not new, "enum types drifting but not in KNOWN_DRIFT: " + ", ".join(
        f"{t} (chain-only={details[t]['chain_only']}, orm-only={details[t]['orm_only']})" for t in new
    )


def test_the_baseline_is_tightened_when_drift_is_fixed():
    """A baseline that is never shrunk stops being a baseline.

    Sprint 741c steps 1-3 will fix these types; each fix must remove its entry,
    otherwise the list silently becomes a permanent allowlist.
    """
    drifting, _details, _unresolved, _stats = guard.compute_drift()
    stale = sorted(guard.KNOWN_DRIFT - drifting)
    assert not stale, "listed in KNOWN_DRIFT but no longer drifting — remove them: " + ", ".join(stale)


def test_the_parser_resolved_every_label_set_it_found():
    """Unreadable constructs must fail loudly, never be skipped quietly."""
    _drifting, _details, unresolved, _stats = guard.compute_drift()
    assert not unresolved, "the comparison is incomplete:\n  " + "\n  ".join(unresolved)


# ---------------------------------------------------------------------------
# 2. The parser read everything — the coverage self-check
# ---------------------------------------------------------------------------


def test_the_scan_actually_scanned_something():
    """A glob that matches nothing proves nothing (Sprint 792)."""
    _d, _det, _u, stats = guard.compute_drift()
    assert stats["migration_files"] > 30, f"only {stats['migration_files']} migrations seen"
    assert stats["migration_types"] > 20, f"only {stats['migration_types']} enum types found in the chain"
    assert stats["orm_types"] > 20, f"only {stats['orm_types']} enum types found in the ORM"


def test_every_named_enum_in_every_migration_is_accounted_for():
    """Count `Enum(..., name=...)` the naive way; the parser must see them all.

    This is the test the first draft needed and did not have. That draft
    handled only inline string literals, so it missed
    `sa.Enum(*_TARGET_TYPES, name=...)` and the `ALTER TYPE` loops — and
    reported 5 enum types where there are 26, with a phantom label named
    `{value}`, while printing a confident verdict.
    """
    naive: set[str] = set()
    for path in sorted(VERSIONS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fname = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if fname not in {"Enum", "ENUM"}:
                continue
            for kw in node.keywords or []:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                    naive.add(str(kw.value.value))

    declared, _where, _unresolved, _files = guard.scan_migrations()
    assert naive, "no named Enum(...) calls found at all — this check covers nothing"

    # Asserted with no exemptions. An earlier draft carved out
    # `Enum(name="x").drop(...)` in downgrades, on the theory that naming a
    # type without labels is legitimate — but measuring showed all 26 named
    # types resolve to labels anyway, so the carve-out was dead code. A dead
    # escape hatch in a coverage check is precisely the thing that hides the
    # first real miss, so it is gone and the claim is the strong one.
    missing = sorted(naive - set(declared))
    assert not missing, f"named in a migration but missing from the parser's output: {missing}"


def test_no_phantom_labels_from_fstring_placeholders():
    """`ADD VALUE '{value}'` in source is an interpolation, not a label.

    The literal regex runs over raw text, so it matched the placeholder and
    recorded a label called `{value}` on two types — inventing drift that did
    not exist while hiding the real labels behind it.
    """
    declared, _where, _unresolved, _files = guard.scan_migrations()
    phantoms = {t: sorted(l for l in labels if "{" in l or "}" in l) for t, labels in declared.items()}
    phantoms = {t: v for t, v in phantoms.items() if v}
    assert not phantoms, f"unresolved f-string placeholders recorded as labels: {phantoms}"


def test_the_sprint_689_tool_labels_are_resolved():
    """Regression proof for the AnnAssign gap.

    `d8b945d0b4e5` declares `NEW_TOOL_NAMES: tuple[str, ...] = (...)`. Handling
    only `ast.Assign` made those six labels invisible and `toolname`
    unreadable — one type annotation was the difference.
    """
    declared, _where, _unresolved, _files = guard.scan_migrations()
    toolname = declared.get("toolname", set())
    for label in ("SOD_CHECKER", "W2_RECONCILIATION", "CASH_FLOW_PROJECTOR"):
        assert label in toolname, f"{label} missing — the AnnAssign constant was not resolved"


def test_the_orm_scan_sees_models_outside_models_py():
    """Importing `models` alone registers 5 of 26 types.

    The rest live in sibling `*_model.py` modules and are absent from
    `Base.metadata` until imported. A scan that skipped them would compare a
    fifth of the schema and report success — the Sprint 792 defect class.
    """
    orm = guard.scan_orm()
    for type_name in ("subscriptionstatus", "dunningstate", "orgrole", "misstatementclassification"):
        assert type_name in orm, f"{type_name} missing — a *_model.py module was not imported"


# ---------------------------------------------------------------------------
# 3. The guard fails when it should
# ---------------------------------------------------------------------------


def test_guard_reports_new_drift(monkeypatch):
    """Shrink the baseline by one and the guard must object."""
    shrunk = frozenset(guard.KNOWN_DRIFT - {"toolname"})
    monkeypatch.setattr(guard, "KNOWN_DRIFT", shrunk)
    assert guard.main() == 1


def test_guard_reports_a_stale_baseline_entry(monkeypatch):
    """Add a type that does not drift and the guard must object."""
    padded = frozenset(guard.KNOWN_DRIFT | {"a_type_that_does_not_exist"})
    monkeypatch.setattr(guard, "KNOWN_DRIFT", padded)
    assert guard.main() == 1


def test_guard_passes_as_configured():
    assert guard.main() == 0


@pytest.mark.parametrize(
    "source,expected",
    [
        ('X = ["a", "b"]', {"X": ["a", "b"]}),
        ('X: tuple[str, ...] = ("a", "b")', {"X": ["a", "b"]}),
        ("X = [1, 2]", {}),
        ("X = SOMETHING_DYNAMIC", {}),
    ],
)
def test_module_constant_resolution(source, expected):
    assert guard._module_constants(ast.parse(source)) == expected
