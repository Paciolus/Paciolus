"""Rule 1: No Float for monetary columns.

Walks AST of model files and flags Column(Float, ...) assignments
in protected classes, unless the column name is in the float allowlist
(ratio/percentage columns that legitimately use Float).
"""

import ast
from dataclasses import dataclass
from pathlib import Path

from ..accounting_policy_guard import Violation

RULE = "no_float_monetary"


def _is_float_column(node: ast.Assign | ast.AnnAssign) -> tuple[str | None, bool]:
    """Check if an assignment is a Column(Float, ...) call.

    Returns (column_name, is_float_column).
    """
    # Get the value node
    if isinstance(node, ast.AnnAssign):
        value = node.value
        target = node.target
    else:
        value = node.value
        target = node.targets[0] if node.targets else None

    if value is None or target is None:
        return None, False

    # Get column name
    col_name = None
    if isinstance(target, ast.Name):
        col_name = target.id
    elif isinstance(target, ast.Attribute):
        col_name = target.attr

    if col_name is None:
        return None, False

    # Check if it's a Column(...) call
    if not isinstance(value, ast.Call):
        return col_name, False

    func = value.func
    if isinstance(func, ast.Name) and func.id == "Column":
        # Check first arg or keyword for Float
        for arg in value.args:
            if isinstance(arg, ast.Name) and arg.id == "Float":
                return col_name, True
            if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == "Float":
                return col_name, True
        for kw in value.keywords:
            if isinstance(kw.value, ast.Name) and kw.value.id == "Float":
                return col_name, True

    return col_name, False


def check_monetary_float_ast(
    tree: ast.Module,
    file_path: str,
    protected_classes: list[str],
    float_allowlist: list[str],
) -> list[Violation]:
    """Check a single AST for Float columns in protected classes."""
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in protected_classes:
            for item in node.body:
                if isinstance(item, (ast.Assign, ast.AnnAssign)):
                    col_name, is_float = _is_float_column(item)
                    if is_float and col_name and col_name not in float_allowlist:
                        violations.append(Violation(
                            rule=RULE,
                            file=file_path,
                            line=item.lineno,
                            message=f"Column '{col_name}' in {node.name} uses Float. Monetary columns must use Numeric(19, 2).",
                            severity="error",
                        ))

    return violations


def check_monetary_float(config: dict, backend_root: Path) -> list[Violation]:
    """Run no_float_monetary check across configured files."""
    violations = []
    files = config.get("files", [])
    protected_classes = config.get("protected_classes", [])
    float_allowlist = config.get("float_allowlist", [])

    for filename in files:
        filepath = backend_root / filename
        if not filepath.exists():
            continue
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=filename)
        violations.extend(check_monetary_float_ast(
            tree, filename, protected_classes, float_allowlist,
        ))

    return violations
