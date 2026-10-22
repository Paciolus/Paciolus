"""Rule 2: No hard-delete on protected audit tables.

Scans Python files for patterns that import a protected model AND contain a
hard-delete call referencing it. Uses text-based scanning (not AST) since the
patterns are syntactic.

THREE DELETE FORMS
------------------
SQLAlchemy 1.x, both long-standing::

    db.delete(row)
    db.query(ActivityLog).filter(...).delete()

SQLAlchemy 2.0, added 2026-10-22::

    db.execute(delete(ActivityLog).where(...))

The 2.0 form was unrecognised until the 2026-10-22 review, which
regression-proved it: injecting ``db.execute(delete(ActivityLog))`` into a
scanned file left the gate green. **Measured at the time: zero such call sites
existed**, so this was a latent gap rather than a live hole in the Phase XLVI
audit-immutability invariant — but the codebase had already migrated to 2.0
style for column declarations (see ``monetary_float.py``), and delete syntax
is the natural next thing to follow.

The checker stays text-based deliberately. The measurement did not justify an
AST rewrite, and a 24-line regex pass that is easy to extend beats a parser
that is easy to narrow.
"""

import re
from pathlib import Path

from ..accounting_policy_guard import Violation

RULE = "no_hard_delete"

# Patterns that indicate a hard-delete call.
# 1.x session-level delete of a loaded instance.
DB_DELETE_PATTERN = re.compile(r"\bdb\.delete\s*\(")
# 2.0 Core delete construct — `delete(Model)` / `sa.delete(Model)`, whether or
# not it is wrapped in `db.execute(...)` on the same line. Matching the
# construct rather than the execute call also catches
# `stmt = delete(ActivityLog)` on one line and `db.execute(stmt)` on another.
CORE_DELETE_PATTERN_TEMPLATE = r"(?<![\w.])(?:sa\.|sqlalchemy\.)?delete\s*\(\s*{model}\b"
# 1.x query-level bulk delete.
QUERY_DELETE_PATTERN_TEMPLATE = r"\.query\s*\(\s*{model}\s*\).*\.delete\s*\("


def check_hard_delete_source(
    source: str,
    file_path: str,
    protected_models: list[str],
) -> list[Violation]:
    """Check a single source string for hard-delete of protected models."""
    violations: list[Violation] = []
    lines = source.splitlines()

    # First pass: detect which protected models are imported
    imported_models: set[str] = set()
    for line in lines:
        for model in protected_models:
            # Match: from X import ..., Model, ...  OR  import Model
            if re.search(rf"\bimport\b.*\b{model}\b", line):
                imported_models.add(model)

    if not imported_models:
        return violations

    # Second pass: look for db.delete() calls
    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Skip comments
        if stripped.startswith("#"):
            continue

        # Check db.delete(...)
        if DB_DELETE_PATTERN.search(line):
            # Try to identify which model variable is being deleted
            for model in imported_models:
                # Look for the model name near the delete call on this line or nearby context
                # Patterns: db.delete(var) where var was assigned from Model query
                # Simple heuristic: flag if any protected model is imported and db.delete is used
                violations.append(
                    Violation(
                        rule=RULE,
                        file=file_path,
                        line=line_num,
                        message=f"Potential hard-delete of protected model '{model}'. Use soft_delete() instead.",
                        severity="error",
                    )
                )
                break  # One violation per line is enough

        # Check .query(Model).delete() — 1.x bulk delete
        for model in imported_models:
            pattern = re.compile(QUERY_DELETE_PATTERN_TEMPLATE.format(model=re.escape(model)))
            if pattern.search(line):
                violations.append(
                    Violation(
                        rule=RULE,
                        file=file_path,
                        line=line_num,
                        message=f"Potential hard-delete of protected model '{model}'. Use soft_delete() instead.",
                        severity="error",
                    )
                )

        # Check delete(Model) — SQLAlchemy 2.0 Core delete construct
        for model in imported_models:
            pattern = re.compile(CORE_DELETE_PATTERN_TEMPLATE.format(model=re.escape(model)))
            if pattern.search(line):
                violations.append(
                    Violation(
                        rule=RULE,
                        file=file_path,
                        line=line_num,
                        message=(
                            f"Potential hard-delete of protected model '{model}' via the SQLAlchemy 2.0 "
                            f"delete() construct. Use soft_delete() instead."
                        ),
                        severity="error",
                    )
                )

    return violations


def check_hard_delete(config: dict, backend_root: Path) -> list[Violation]:
    """Run no_hard_delete check across configured directories."""
    violations = []
    protected_models = config.get("protected_models", [])
    scan_dirs = config.get("scan_dirs", ["."])
    exclude_patterns = config.get("exclude_patterns", [])

    for scan_dir in scan_dirs:
        dir_path = backend_root / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.glob("*.py"):
            rel_path = str(py_file.relative_to(backend_root)).replace("\\", "/")

            # Check exclusions
            skip = False
            for pattern in exclude_patterns:
                if pattern in rel_path:
                    skip = True
                    break
            if skip:
                continue

            source = py_file.read_text(encoding="utf-8")
            violations.extend(
                check_hard_delete_source(
                    source,
                    rel_path,
                    protected_models,
                )
            )

    return violations
