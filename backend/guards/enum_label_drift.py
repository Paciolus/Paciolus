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
succeeded.

The uncomfortable consequence is about **recovery**, not steady state:
production's schema was built by `create_all()` and stamped, so it matches the
ORM. A database rebuilt from the documented migration chain — a DR restore, a
fresh staging environment — would not. The drift is invisible until the moment
you most need the restore to work.

It is also invisible to the test suite, because SQLite has no enum types: the
column is a plain VARCHAR, every label is accepted, and ~9,000 passing tests
say nothing about it. A static check is the only thing that can see this
without a PostgreSQL connection.

WHAT THIS DOES NOT DO
It does not fix the drift, and it does not decide the canonical direction —
that needs a read of `information_schema.enum_range` against production
(CEO ask D-1) and is Sprint 741c steps 1-3. This guard **freezes** the
problem: the known-drifting types are listed in `KNOWN_DRIFT` below, and any
type that drifts without being on that list fails. Fixing a type means
deleting its entry; the guard then holds it fixed.

HOW THE CHAIN IS EVALUATED — read this before changing the parser
The label set a type ends up with is the result of **replaying the chain in
revision order**, not of unioning every label mentioned anywhere. That
distinction is not academic: `e3f4a5b6c7d8_pricing_v3_enum_restructure`
rebuilds `usertier` and `subscription_tier` with

    ALTER TYPE usertier RENAME TO usertier_old
    CREATE TYPE usertier AS ENUM ('free', 'solo', 'professional', 'enterprise')
    DROP TYPE usertier_old

so `starter`, `team` and `organization` are **retired**, not current. A
union-based reading keeps them forever, reports drift that does not exist, and
is simultaneously blind to drift a future rebuild introduces. The PR #191
review caught exactly that.

Two further traps, both of which an earlier draft of this module fell into:

* **Only `upgrade()` counts.** The `downgrade()` in that same migration
  recreates both types with the *old* labels. A scan over raw file text picks
  those up and silently reverses the answer.
* **Order within a file matters too**, because the rebuild above is a
  three-step dance. `ast.walk` is breadth-first, so operations are collected
  with their line numbers and sorted before being replayed.

Anything this module cannot resolve is recorded in `unresolved` and fails the
run loudly rather than quietly shrinking the comparison. That is deliberate:
an earlier draft skipped what it could not read and produced a confident
verdict over a fifth of the schema.
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

# --- raw-SQL enum operations, as they appear inside op.execute(...) ----------
RE_CREATE = re.compile(
    r"CREATE\s+TYPE\s+(?P<type>[\w\".]+)\s+AS\s+ENUM\s*\((?P<labels>[^)]*)\)",
    re.IGNORECASE | re.DOTALL,
)
RE_ADD_VALUE = re.compile(
    r"ALTER\s+TYPE\s+(?P<type>[\w\".]+)\s+ADD\s+VALUE\s+(?:IF\s+NOT\s+EXISTS\s+)?'(?P<label>[^']+)'",
    re.IGNORECASE,
)
RE_ADD_VALUE_DYNAMIC = re.compile(
    r"ALTER\s+TYPE\s+(?P<type>[\w\".]+)\s+ADD\s+VALUE\s+(?:IF\s+NOT\s+EXISTS\s+)?'?\s*$",
    re.IGNORECASE,
)
RE_RENAME = re.compile(
    r"ALTER\s+TYPE\s+(?P<type>[\w\".]+)\s+RENAME\s+TO\s+(?P<new>[\w\".]+)",
    re.IGNORECASE,
)
RE_DROP = re.compile(r"DROP\s+TYPE\s+(?:IF\s+EXISTS\s+)?(?P<type>[\w\".]+)", re.IGNORECASE)
RE_SQL_STRING_LABEL = re.compile(r"'([^']*)'")

# Any statement that touches an enum type. Used by the coverage self-check to
# confirm the replay accounted for every one present in an upgrade() body —
# the AST-level check cannot see these, which is how the first version shipped
# with no handler for CREATE TYPE at all.
RE_ANY_ENUM_SQL = re.compile(
    r"(?:CREATE\s+TYPE\s+[\w\".]+\s+AS\s+ENUM"
    r"|ALTER\s+TYPE\s+[\w\".]+\s+ADD\s+VALUE"
    r"|ALTER\s+TYPE\s+[\w\".]+\s+RENAME\s+TO"
    r"|DROP\s+TYPE\s+[\w\".]+)",
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
        "usertier",  # chain: free/solo/professional/enterprise; ORM binds the NAMES
        # --- membership: labels genuinely absent, not merely misspelled. These
        # cannot be resolved by any `values_callable` decision and need an
        # explicit `ALTER TYPE ... ADD VALUE`.
        "engagementstatus",  # ORM binds COMPLETED; NO migration ever adds it
        "toolname",  # chain carries lowercase flux_analysis; ORM binds FLUX_ANALYSIS
        #
        # NOT listed, and worth knowing why: `subscription_tier` agrees. The
        # PR #191 review caught it being reported as drift by a union-based
        # reading that kept `starter`/`team`/`organization` alive after
        # `e3f4a5b6c7d8` retired them. Its model binds lowercase while
        # `usertier` — the same four tiers, one table over — binds NAMES, so
        # the ORM is internally inconsistent about two parallel enums. That is
        # a useful input to 741c's canonical-direction decision.
    }
)


def _norm(name: str) -> str:
    return name.strip().strip('"').split(".")[-1].lower()


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


def _revision_ids(tree: ast.Module) -> tuple[str | None, list[str]]:
    """`revision` and `down_revision` (a string, None, or a tuple at a mergepoint)."""
    revision: str | None = None
    down: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value_node = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value_node = [node.target], node.value
        else:
            continue
        names = {t.id for t in targets if isinstance(t, ast.Name)}
        try:
            value = ast.literal_eval(value_node)
        except (ValueError, SyntaxError):
            continue
        if "revision" in names and isinstance(value, str):
            revision = value
        elif "down_revision" in names:
            if isinstance(value, str):
                down = [value]
            elif isinstance(value, (list, tuple)):
                down = [v for v in value if isinstance(v, str)]
            else:
                down = []
    return revision, down


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


def _upgrade_node(tree: ast.Module):
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
            return node
    return None


def _static_sql(node: ast.AST) -> str | None:
    """The literal prefix of a string or f-string, or None if neither."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = ""
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                out += part.value
            else:
                break
        return out
    return None


def collect_operations(upgrade, constants: dict[str, list[str]], filename: str):
    """Ordered (lineno, kind, payload) enum operations inside one upgrade()."""
    ops: list[tuple[int, str, tuple]] = []
    unresolved: list[str] = []

    # Which loop (if any) each node sits inside, and what that loop iterates.
    loop_values: dict[int, list[str] | None] = {}
    for node in ast.walk(upgrade):
        if isinstance(node, ast.For):
            values = constants.get(node.iter.id) if isinstance(node.iter, ast.Name) else None
            for inner in ast.walk(node):
                loop_values[id(inner)] = values

    for node in ast.walk(upgrade):
        if isinstance(node, ast.Call):
            fname = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if fname in {"Enum", "ENUM"}:
                name_node = _kwarg(node, "name")
                if isinstance(name_node, ast.Constant):
                    type_name = _norm(str(name_node.value))
                    labels, ok = _enum_labels(node, constants)
                    if labels:
                        ops.append((node.lineno, "define", (type_name, set(labels))))
                    if not ok:
                        unresolved.append(f"{filename}:{node.lineno}: Enum(name={type_name!r}) has unreadable labels")
            continue

        if not isinstance(node, (ast.Constant, ast.JoinedStr)):
            continue
        sql = _static_sql(node)
        if not sql or "TYPE" not in sql.upper():
            continue
        line = node.lineno

        for m in RE_CREATE.finditer(sql):
            labels = set(RE_SQL_STRING_LABEL.findall(m.group("labels")))
            ops.append((line, "create", (_norm(m.group("type")), labels)))
        for m in RE_RENAME.finditer(sql):
            ops.append((line, "rename", (_norm(m.group("type")), _norm(m.group("new")))))
        for m in RE_DROP.finditer(sql):
            ops.append((line, "drop", (_norm(m.group("type")),)))
        for m in RE_ADD_VALUE.finditer(sql):
            label = m.group("label")
            if "{" in label or "}" in label:
                continue  # an f-string placeholder; the loop branch resolves it
            ops.append((line, "add", (_norm(m.group("type")), {label})))

        if isinstance(node, ast.JoinedStr):
            m = RE_ADD_VALUE_DYNAMIC.search(sql)
            if m:
                type_name = _norm(m.group("type"))
                values = loop_values.get(id(node))
                if values is None:
                    unresolved.append(
                        f"{filename}:{line}: ALTER TYPE {type_name} ADD VALUE interpolates a value "
                        "this parser cannot resolve"
                    )
                else:
                    ops.append((line, "add", (type_name, set(values))))

    ops.sort(key=lambda item: item[0])
    return ops, unresolved


def ordered_migrations():
    """Migration files in revision order — topological, deterministic."""
    parsed: dict[str, tuple[Path, ast.Module, list[str]]] = {}
    for path in sorted(VERSIONS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        rev, down = _revision_ids(tree)
        if rev is None:
            continue
        parsed[rev] = (path, tree, down)

    ordered: list[tuple[Path, ast.Module]] = []
    placed: set[str] = set()
    remaining = dict(parsed)
    while remaining:
        ready = sorted(
            rev for rev, (_p, _t, down) in remaining.items() if all(d in placed or d not in parsed for d in down)
        )
        if not ready:
            # A cycle or a dangling down_revision. Fall back to filename order
            # for whatever is left rather than dropping it — dropping would
            # shrink the comparison silently, which is the one thing this
            # module exists not to do.
            ready = sorted(remaining)
        for rev in ready:
            path, tree, _down = remaining.pop(rev)
            ordered.append((path, tree))
            placed.add(rev)
    return ordered


def scan_migrations():
    """Replay every upgrade()'s enum operations in revision order.

    Returns (labels_by_type, touched_by, unresolved, files).
    """
    labels: dict[str, set[str]] = {}
    where: dict[str, set[str]] = defaultdict(set)
    unresolved: list[str] = []

    ordered = ordered_migrations()

    for path, tree in ordered:
        constants = _module_constants(tree)
        upgrade = _upgrade_node(tree)
        if upgrade is None:
            continue
        ops, file_unresolved = collect_operations(upgrade, constants, path.name)
        unresolved.extend(file_unresolved)

        for _line, kind, payload in ops:
            if kind == "create":
                type_name, new_labels = payload
                labels[type_name] = set(new_labels)  # a rebuild REPLACES
                where[type_name].add(path.name)
            elif kind == "define":
                # `sa.Enum(..., name=...)` in create_table creates the type only
                # when it does not already exist, so it must not clobber a
                # rebuild that came earlier in the chain.
                type_name, new_labels = payload
                if type_name not in labels:
                    labels[type_name] = set(new_labels)
                    where[type_name].add(path.name)
            elif kind == "add":
                type_name, new_labels = payload
                labels.setdefault(type_name, set()).update(new_labels)
                where[type_name].add(path.name)
            elif kind == "rename":
                old, new = payload
                if old in labels:
                    labels[new] = labels.pop(old)
                    where[new] |= where.pop(old, set())
                    where[new].add(path.name)
            elif kind == "drop":
                (type_name,) = payload
                labels.pop(type_name, None)
                where.pop(type_name, None)

    files = [p for p, _t in ordered]
    return dict(labels), dict(where), unresolved, files


def scan_orm():
    """Every enum type the ORM actually binds.

    Imports every `*_model.py`, not just `models`. Reading `Base.metadata`
    after importing `models` alone finds 5 of 26 types — the models are spread
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
            entry = orm.setdefault(_norm(type_name), {"labels": set(), "columns": set()})
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
    print(f"  migrations replayed: {stats['migration_files']}")
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
