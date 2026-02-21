"""Rule 2: No hard-delete on protected audit tables.

Scans Python files for patterns that import a protected model AND
contain db.delete() or .query(Model)...delete() calls referencing it.
Uses text-based scanning (not AST) since the patterns are syntactic.
"""

import re
from pathlib import Path

from ..accounting_policy_guard import Violation

RULE = "no_hard_delete"

# Patterns that indicate a hard-delete call
DB_DELETE_PATTERN = re.compile(r"db\.delete\s*\(")
QUERY_DELETE_PATTERN = re.compile(r"\.query\s*\([^)]*{model}[^)]*\)[^;]*\.delete\s*\(")


def check_hard_delete_source(
    source: str,
    file_path: str,
    protected_models: list[str],
) -> list[Violation]:
    """Check a single source string for hard-delete of protected models."""
    violations = []
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
                violations.append(Violation(
                    rule=RULE,
                    file=file_path,
                    line=line_num,
                    message=f"Potential hard-delete of protected model '{model}'. Use soft_delete() instead.",
                    severity="error",
                ))
                break  # One violation per line is enough

        # Check .query(Model).delete() pattern
        for model in imported_models:
            pattern = re.compile(rf"\.query\s*\(\s*{model}\s*\).*\.delete\s*\(")
            if pattern.search(line):
                violations.append(Violation(
                    rule=RULE,
                    file=file_path,
                    line=line_num,
                    message=f"Potential hard-delete of protected model '{model}'. Use soft_delete() instead.",
                    severity="error",
                ))

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
            violations.extend(check_hard_delete_source(
                source, rel_path, protected_models,
            ))

    return violations
