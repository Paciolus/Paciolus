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
        upgrade = guard._upgrade_node(tree)
        if upgrade is None:
            continue
        for node in ast.walk(upgrade):
            if not isinstance(node, ast.Call):
                continue
            fname = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if fname not in {"Enum", "ENUM"}:
                continue
            for kw in node.keywords or []:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                    naive.add(guard._norm(str(kw.value.value)))

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


# ---------------------------------------------------------------------------
# Replay semantics — added after the PR #191 review
#
# The first version of this guard unioned every label it saw anywhere in the
# file. Two consequences, both found in review rather than by these tests,
# which is why the coverage check below now covers the SQL path as well as the
# AST one:
#
#   * `e3f4a5b6c7d8` REBUILDS usertier and subscription_tier with
#     `CREATE TYPE ... AS ENUM`, retiring starter/team/organization. A union
#     keeps them forever — reporting drift that does not exist, and being
#     blind to drift a future rebuild introduces.
#   * The same migration's `downgrade()` recreates both types with the OLD
#     labels. Scanning raw file text picks those up and reverses the answer.
# ---------------------------------------------------------------------------


def test_a_type_rebuild_replaces_its_labels_rather_than_unioning():
    """`CREATE TYPE ... AS ENUM` after a RENAME is a replacement, not an addition.

    `e3f4a5b6c7d8_pricing_v3_enum_restructure` retires starter/team/organization
    from both tier enums. A reading that keeps them reports phantom drift —
    which is exactly what the PR #191 review caught.
    """
    declared, _where, _unresolved, _files = guard.scan_migrations()
    for type_name in ("usertier", "subscription_tier"):
        labels = declared.get(type_name, set())
        assert labels, f"{type_name} resolved to no labels at all"
        retired = {"starter", "team", "organization"} & labels
        assert not retired, (
            f"{type_name} still carries retired labels {sorted(retired)} — the rebuild in "
            "e3f4a5b6c7d8 was treated as additive instead of as a replacement"
        )
        assert labels == {"free", "solo", "professional", "enterprise"}, (
            f"{type_name} resolved to {sorted(labels)}; the pricing-v3 rebuild defines exactly "
            "free/solo/professional/enterprise"
        )


def test_downgrade_bodies_are_not_replayed():
    """Only `upgrade()` describes the schema a fresh database gets.

    The downgrade in `e3f4a5b6c7d8` recreates both tier enums with
    team/organization. If those leak in, the guard silently describes a
    database nobody has.
    """
    declared, _where, _unresolved, _files = guard.scan_migrations()
    assert "team" not in declared.get("usertier", set())
    assert "organization" not in declared.get("usertier", set())


def test_dropped_helper_types_do_not_survive_the_replay():
    """`usertier_old` exists only between a RENAME and a DROP."""
    declared, _where, _unresolved, _files = guard.scan_migrations()
    leftovers = sorted(t for t in declared if t.endswith("_old"))
    assert not leftovers, f"temporary rename targets survived the replay: {leftovers}"


def test_every_enum_sql_statement_in_every_upgrade_is_accounted_for():
    """The coverage check for the raw-SQL path — the one that was missing.

    The existing coverage test counted `Enum(..., name=...)` AST calls, so it
    proved nothing about `op.execute("CREATE TYPE ...")`. The first version of
    the guard had **no handler for CREATE TYPE at all** and that test stayed
    green. Coverage of one construct family is not coverage of the chain.

    So: count enum-affecting SQL statements the naive way, and require the
    operation collector to produce an op for each one.
    """
    total_statements = 0
    total_ops = 0
    gaps = []

    for path, tree in guard.ordered_migrations():
        upgrade = guard._upgrade_node(tree)
        if upgrade is None:
            continue
        constants = guard._module_constants(tree)
        ops, _unresolved = guard.collect_operations(upgrade, constants, path.name)
        sql_ops = [o for o in ops if o[1] in {"create", "add", "rename", "drop"}]

        # Count statements in the upgrade() source only.
        segment = ast.get_source_segment(path.read_text(encoding="utf-8"), upgrade) or ""
        statements = guard.RE_ANY_ENUM_SQL.findall(segment)

        total_statements += len(statements)
        total_ops += len(sql_ops)
        if statements and not sql_ops:
            gaps.append(f"{path.name}: {len(statements)} enum SQL statement(s), 0 parsed")

    assert total_statements > 0, "no enum SQL statements found at all — this check covers nothing"
    assert not gaps, "enum SQL present but unparsed:\n  " + "\n  ".join(gaps)
    assert total_ops >= total_statements, (
        f"parsed {total_ops} enum operations from {total_statements} SQL statements — "
        "some statement form is not handled"
    )


def test_migrations_are_replayed_in_revision_order():
    """Order is load-bearing: a rebuild must not be overtaken by an earlier CREATE."""
    ordered = guard.ordered_migrations()
    assert len(ordered) > 30, f"only {len(ordered)} migrations ordered"

    names = [p.name for p, _t in ordered]
    baseline = "e2f21cb79a61_baseline_full_schema_as_of_v1_2_0.py"
    rebuild = "e3f4a5b6c7d8_pricing_v3_enum_restructure.py"
    assert names.index(baseline) < names.index(rebuild), (
        "the v1.2.0 baseline must be replayed before the pricing-v3 rebuild; "
        "filename order happens to agree here, but revision order is what is required"
    )


def test_subscription_tier_agrees_and_is_not_in_the_baseline():
    """Regression proof for the phantom the PR #191 review found.

    It must stay out of KNOWN_DRIFT: listing a type that does not drift is
    just as wrong as omitting one that does, and `test_the_baseline_is_
    tightened_when_drift_is_fixed` enforces that in general. This pins the
    specific case.
    """
    drifting, _details, _unresolved, _stats = guard.compute_drift()
    assert "subscription_tier" not in drifting
    assert "subscription_tier" not in guard.KNOWN_DRIFT
