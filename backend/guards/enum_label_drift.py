"""Do the Alembic chain and the ORM agree on PostgreSQL enum labels?

Sprint 741d — the static half of Sprint 741c step 4, which needs no database
because it compares two things already in the repository.

WHY THIS MATTERS
`sa.Enum(SomePyEnum)` with no `values_callable` makes SQLAlchemy bind the
member **name** (`ACTIVE`). A migration that spells the same type with
lowercase labels (`active`) produces a database the ORM cannot write to: the
value is simply not a label of the type, and PostgreSQL raises 22P02.

That is not hypothetical. Sprint 741a traced an hourly production failure to
exactly this — `reset_upload_quotas` filtered `WHERE status = 'active'`
against a type whose labels are the names, and the job had never once
succeeded. Sprint 741b found a second, related symptom.

The uncomfortable consequence is about **recovery**, not steady state:
production's schema was built by `create_all()` and stamped, so it matches the
ORM. A database rebuilt from the documented migration chain — a DR restore, a
fresh staging environment — would not. The drift is invisible until the moment
you most need the restore to work.

It is also invisible to the test suite, because SQLite has no enum types: the
column is a plain VARCHAR, every label is accepted, and 9,000 passing tests
say nothing about it. A static check is the only thing that can see this
without a PostgreSQL connection.

WHAT THIS DOES NOT DO
It does not fix the drift, and it does not decide the canonical direction —
that needs a read of `information_schema.enum_range` against production
(CEO ask D-1) and is Sprint 741c steps 1-3. This guard **freezes** the
problem: the known-drifting types are listed in `KNOWN_DRIFT` below, and any
type that drifts without being on that list fails. Fixing a type means
deleting its entry; the guard then holds it fixed.

ON THE PARSER
The label sets are assembled from three constructs, because all three are
used in this chain:

    sa.Enum("a", "b", name="t")              inline literals
    sa.Enum(*_CONSTANT, name="t")            a module-level list
    for v in _CONSTANT:                      a loop emitting ALTER TYPE
        op.execute(f"ALTER TYPE t ADD VALUE IF NOT EXISTS '{v}'")

The first draft handled only the first form and produced a confidently wrong
answer: it reported five enum types where there are twenty-one, invented a
label called `{value}`, and claimed five types had no migration at all. A
parser that silently skips what it cannot read turns a guard into a
rubber stamp — the Sprint 792 defect class. So anything this module cannot
resolve is recorded in `unresolved` and fails the run loudly rather than
quietly shrinking the comparison.
"""

from __future__ import annotations

import ast
import importlib
import re
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
VERSIONS = BACKEND / "migrations" / "alembic" / "versions"

# `ALTER TYPE <t> ADD VALUE [IF NOT EXISTS] '<label>'`, for the literal form.
ALTER_ADD_LITERAL = re.compile(
    r"ALTER\s+TYPE\s+(?P<type>[\w\".]+)\s+ADD\s+VALUE\s+(?:IF\s+NOT\s+EXISTS\s+)?'(?P<label>[^']+)'",
    re.IGNORECASE,
)
# The same statement built by an f-string, where the label is interpolated.
ALTER_ADD_DYNAMIC = re.compile(
    r"ALTER\s+TYPE\s+(?P<type>[\w\".]+)\s+ADD\s+VALUE\s+(?:IF\s+NOT\s+EXISTS\s+)?'?$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Known drift — Sprint 741c steps 1-3 will empty this list.
#
# Recorded as a baseline rather than fixed here on purpose: correcting a label
# set changes what a fresh database is built with, and the canonical direction
# cannot be confirmed without reading production's actual `enum_range`. What
# this guard buys today is that the list cannot grow silently.
# ---------------------------------------------------------------------------
KNOWN_DRIFT: frozenset[str] = frozenset(
    {
        # --- case-only: the chain spells labels lowercase, the ORM binds NAMES.
        # Equally breaking despite sounding cosmetic — `ACTIVE` is simply not a
        # label of a type whose labels are `active`, and the write is rejected.
        "adminactiontype",
        "billingeventtype",
        "billinginterval",
        "dunningresolution",
        "dunningstate",
        "entitytype",
        "expectationresultstatus",
        "expectationtargettype",
        "invitestatus",
        "misstatementclassification",
        "misstatementdisposition",
        "misstatementsourcetype",
        "orgrole",
        "reportingframework",
        "subscriptionstatus",
        "teamactiontype",
        # --- membership: labels genuinely absent, not merely misspelled. These
        # cannot be resolved by any `values_callable` decision and need an
        # explicit `ALTER TYPE ... ADD VALUE`.
        "engagementstatus",  # ORM binds COMPLETED; NO migration ever adds it
        "subscription_tier",  # chain: starter/team/organization; ORM binds solo
        "toolname",  # chain carries lowercase flux_analysis; ORM binds FLUX_ANALYSIS
        "usertier",  # chain lacks SOLO (the rename added lowercase `solo`)
    }
)


def _module_constants(tree: ast.Module) -> dict[str, list[str]]:
    """Module-level `NAME = [...]` assignments whose value is a sequence of strings.

    `AnnAssign` is handled as well as `Assign`, and that is not a detail:
    `d8b945d0b4e5` declares `NEW_TOOL_NAMES: tuple[str, ...] = (...)`, so an
    Assign-only version could not resolve the six Sprint 689 tool labels and
    reported `toolname` as unreadable. One annotation was the difference
    between reading that migration and not reading it.
    """
    out: dict[str, list[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value_node = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value_node = [node.target], node.value
        else:
            continue
        try:
            value = ast.literal_eval(value_node)
        except (ValueError, SyntaxError):
            continue
        if not isinstance(value, (list, tuple, set)):
            continue
        items = [v for v in value if isinstance(v, str)]
        if len(items) != len(value):
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                out[target.id] = items
    return out


def _kwarg(call: ast.Call, key: str):
    for kw in call.keywords or []:
        if kw.arg == key:
            return kw.value
    return None


def _enum_labels(call: ast.Call, constants: dict[str, list[str]]) -> tuple[list[str], bool]:
    """Labels passed positionally to Enum(...). Returns (labels, fully_resolved)."""
    labels: list[str] = []
    resolved = True
    for arg in call.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            labels.append(arg.value)
        elif isinstance(arg, ast.Starred) and isinstance(arg.value, ast.Name):
            # sa.Enum(*_TARGET_TYPES, name="...")
            found = constants.get(arg.value.id)
            if found is None:
                resolved = False
            else:
                labels.extend(found)
        elif isinstance(arg, ast.Name):
            found = constants.get(arg.id)
            if found is None:
                resolved = False
            else:
                labels.extend(found)
        else:
            resolved = False
    return labels, resolved


def _dynamic_alter_labels(tree: ast.Module, constants: dict[str, list[str]]):
    """`for v in CONST: op.execute(f"ALTER TYPE t ADD VALUE ... '{v}'")`.

    Yields (type_name, labels, resolved).
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        values = constants.get(node.iter.id) if isinstance(node.iter, ast.Name) else None

        for inner in ast.walk(node):
            if not isinstance(inner, ast.JoinedStr):
                continue
            prefix = ""
            for part in inner.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    prefix += part.value
                else:
                    break
            match = ALTER_ADD_DYNAMIC.search(prefix.strip())
            if not match:
                continue
            type_name = match.group("type").strip('"').split(".")[-1].lower()
            if values is None:
                yield type_name, [], False
            else:
                yield type_name, list(values), True


def scan_migrations():
    declared: dict[str, set[str]] = defaultdict(set)
    where: dict[str, set[str]] = defaultdict(set)
    unresolved: list[str] = []
    files = sorted(VERSIONS.glob("*.py"))

    for path in files:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        constants = _module_constants(tree)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fname = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if fname not in {"Enum", "ENUM"}:
                continue
            name_node = _kwarg(node, "name")
            if not isinstance(name_node, ast.Constant):
                continue
            type_name = str(name_node.value)
            labels, ok = _enum_labels(node, constants)
            if labels:
                declared[type_name] |= set(labels)
                where[type_name].add(path.name)
            if not ok:
                unresolved.append(f"{path.name}: Enum(name={type_name!r}) has labels this parser cannot resolve")

        for match in ALTER_ADD_LITERAL.finditer(source):
            label = match.group("label")
            # The literal regex runs over raw source, so an f-string's own
            # placeholder text matches it: `ADD VALUE ... '{value}'` would be
            # recorded as a label literally named `{value}`. It was, and it
            # showed up as phantom drift on two types. The loop handler below
            # resolves those properly; skip them here.
            if "{" in label or "}" in label:
                continue
            type_name = match.group("type").strip('"').split(".")[-1].lower()
            declared[type_name].add(label)
            where[type_name].add(path.name)

        for type_name, labels, ok in _dynamic_alter_labels(tree, constants):
            if ok:
                declared[type_name] |= set(labels)
                where[type_name].add(path.name)
            else:
                unresolved.append(f"{path.name}: ALTER TYPE {type_name} loops over a list this parser cannot resolve")

    return declared, where, unresolved, files


def scan_orm():
    """Every enum type the ORM actually binds.

    Imports every `*_model.py`, not just `models`. Reading `Base.metadata`
    after importing `models` alone finds 5 of 21 types — the models are spread
    across sibling modules and a table is absent from the metadata until its
    module is imported.
    """
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))

    from database import Base

    importlib.import_module("models")
    for path in sorted(BACKEND.glob("*_model.py")):
        importlib.import_module(path.stem)

    orm: dict[str, dict] = {}
    for table in Base.metadata.tables.values():
        for col in table.columns:
            labels = getattr(col.type, "enums", None)
            type_name = getattr(col.type, "name", None)
            if labels is None or not type_name:
                continue
            entry = orm.setdefault(type_name, {"labels": set(), "columns": set()})
            entry["labels"] |= set(labels)
            entry["columns"].add(f"{table.name}.{col.name}")
    return orm


def compute_drift():
    """Return (drifting, details, unresolved, stats)."""
    declared, where, unresolved, files = scan_migrations()
    orm = scan_orm()

    drifting: set[str] = set()
    details: dict[str, dict] = {}

    for type_name in sorted(set(declared) | set(orm)):
        chain = declared.get(type_name, set())
        entry = orm.get(type_name)
        if entry is None:
            # Declared by a migration but bound by no ORM column. Not drift:
            # dropped models and admin-only types legitimately look like this.
            continue
        orm_labels = entry["labels"]
        chain_only = sorted(chain - orm_labels)
        orm_only = sorted(orm_labels - chain)
        if not chain_only and not orm_only:
            continue
        drifting.add(type_name)
        details[type_name] = {
            "chain_only": chain_only,
            "orm_only": orm_only,
            "migrations": sorted(where.get(type_name, [])),
            "columns": sorted(entry["columns"]),
            "no_migration": not chain,
        }

    stats = {
        "migration_files": len(files),
        "migration_types": len(declared),
        "orm_types": len(orm),
    }
    return drifting, details, unresolved, stats


def main() -> int:
    drifting, details, unresolved, stats = compute_drift()

    print("Enum Label Drift Guard (Sprint 741d)")
    print(f"  migrations scanned : {stats['migration_files']}")
    print(f"  enum types in chain: {stats['migration_types']}")
    print(f"  enum types in ORM  : {stats['orm_types']}")
    print(f"  drifting           : {len(drifting)} (known: {len(KNOWN_DRIFT)})")

    failed = False

    if unresolved:
        failed = True
        print("\nERROR: the parser could not read some label sets, so this comparison is incomplete:")
        for item in unresolved:
            print(f"  - {item}")

    new_drift = sorted(drifting - KNOWN_DRIFT)
    if new_drift:
        failed = True
        print("\nERROR: new enum label drift. A database built from the migration chain will")
        print("not match what the ORM binds, and writes to these types will fail on it:")
        for type_name in new_drift:
            d = details[type_name]
            print(f"\n  {type_name}  ({', '.join(d['columns'])})")
            if d["no_migration"]:
                print("    no migration declares this type at all")
            if d["chain_only"]:
                print(f"    only in the chain : {d['chain_only']}")
            if d["orm_only"]:
                print(f"    only in the ORM   : {d['orm_only']}")
            if d["migrations"]:
                print(f"    migrations        : {', '.join(d['migrations'])}")
        print("\nEnum(PyEnum) with no values_callable binds the member NAME. Spell the")
        print("migration's labels the same way. Do NOT add values_callable to the model —")
        print("that flips every binding to lowercase and breaks the existing database.")

    fixed = sorted(KNOWN_DRIFT - drifting)
    if fixed:
        failed = True
        print("\nERROR: these types are listed in KNOWN_DRIFT but no longer drift:")
        for type_name in fixed:
            print(f"  - {type_name}")
        print("\nRemove them from KNOWN_DRIFT so the guard holds them fixed. A baseline that")
        print("is not tightened when the problem shrinks stops being a baseline.")

    if failed:
        return 1

    print("\nNo new drift. The known set is unchanged (Sprint 741c steps 1-3 will empty it).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
