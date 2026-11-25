#!/usr/bin/env python3
"""Fail on destructive Alembic migrations that do not follow expand/contract (Sprint 897, O-9).

Render runs ``alembic upgrade head`` while the previous release is still
serving traffic. A migration that drops, renames or retypes something the old
code still reads breaks that old code for the length of the deploy — and for
good if the new image then fails to start, because Render keeps serving the
old one (the Sprint 768 pattern). The rule, written up in
``docs/runbooks/database-migrations.md``:

  * expand first — add the new column/table, ship code that uses it;
  * contract later — drop or rename only in a later release, once no
    serving code reads the old shape.

This script reads every migration's ``upgrade()`` and flags:

  * ``op.drop_table`` / ``op.drop_column`` / ``op.rename_table``
  * ``op.alter_column(..., new_column_name=...)`` or ``type_=...``
  * the same operations inside ``batch_alter_table`` blocks
  * ``op.execute`` SQL containing DROP TABLE, DROP COLUMN, RENAME or ALTER ... TYPE

A flagged migration passes only when it carries the marker comment

    # expand-contract: contract step — <why no serving code reads the old shape>

anywhere in the file. ``downgrade()`` is never checked — dropping is what it is for.
Migrations that predate this rule are listed in ``GRANDFATHERED`` and are not checked.

Usage: python scripts/check_destructive_migrations.py [versions_dir]
Exit 0 clean, 1 if any unmarked destructive migration is found.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

DEFAULT_VERSIONS_DIR = Path(__file__).resolve().parent.parent / "backend" / "migrations" / "alembic" / "versions"

MARKER = re.compile(r"#\s*expand-contract:\s*contract step\s*[—-]+\s*\S")

DESTRUCTIVE_OPS = {"drop_table", "drop_column", "rename_table"}
DESTRUCTIVE_ALTER_KWARGS = {"new_column_name", "type_"}
DESTRUCTIVE_SQL = re.compile(
    r"\bDROP\s+(TABLE|COLUMN)\b|\bRENAME\b|\bALTER\s+(TABLE\s+\S+\s+)?ALTER\s+(COLUMN\s+)?\S+\s+(SET\s+DATA\s+)?TYPE\b",
    re.IGNORECASE,
)

# Migrations written before Sprint 897 (2026-11-25). Each already ran on
# production; changing them now would change nothing. Frozen: do not add to it.
GRANDFATHERED: frozenset[str] = frozenset(
    {
        "a1b2c3d4e5f6_float_to_numeric_monetary.py",
        "c1a5f0d7b4e2_harden_export_share_passcode.py",
        "c1d2e3f4a5b6_remove_enterprise_tier.py",
        "e3f4a5b6c7d8_pricing_v3_enum_restructure.py",
        "ecda5f408617_hash_email_verification_tokens.py",
    }
)


def _string_value(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
    if isinstance(node, ast.Call) and node.args:
        # sa.text("...") / text("...")
        return _string_value(node.args[0])
    return None


def destructive_operations(source: str) -> list[str]:
    """Return a description of each destructive operation in ``upgrade()``."""
    tree = ast.parse(source)
    upgrade = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "upgrade"),
        None,
    )
    if upgrade is None:
        return []

    found: list[str] = []
    for node in ast.walk(upgrade):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        name = node.func.attr
        line = node.lineno
        if name in DESTRUCTIVE_OPS:
            found.append(f"line {line}: {name}")
        elif name == "alter_column":
            hits = sorted(k.arg for k in node.keywords if k.arg in DESTRUCTIVE_ALTER_KWARGS)
            if hits:
                found.append(f"line {line}: alter_column({', '.join(hits)})")
        elif name == "execute" and node.args:
            sql = _string_value(node.args[0])
            if sql and DESTRUCTIVE_SQL.search(sql):
                found.append(f"line {line}: execute({sql.strip()[:60]!r})")
    return found


def check(versions_dir: Path, grandfathered: frozenset[str] = GRANDFATHERED) -> list[str]:
    problems: list[str] = []
    for path in sorted(versions_dir.glob("*.py")):
        if path.name in grandfathered or path.name == "__init__.py":
            continue
        source = path.read_text(encoding="utf-8")
        ops = destructive_operations(source)
        if ops and not MARKER.search(source):
            problems.append(f"{path.name}: " + "; ".join(ops))
    return problems


def main(argv: list[str]) -> int:
    versions_dir = Path(argv[1]) if len(argv) > 1 else DEFAULT_VERSIONS_DIR
    if not versions_dir.is_dir():
        print(f"ERROR: {versions_dir} is not a directory")
        return 1
    problems = check(versions_dir)
    if not problems:
        print("Destructive-migration check: OK")
        return 0
    print("Destructive migrations without an expand/contract marker:\n")
    for p in problems:
        print(f"  {p}")
    print(
        "\nRender runs migrations while the previous release still serves. Split the change:\n"
        "expand now, contract in a later release. If this IS the contract step and no serving\n"
        "code reads the old shape, add to the migration:\n"
        "    # expand-contract: contract step — <why it is safe>\n"
        "See docs/runbooks/database-migrations.md."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
