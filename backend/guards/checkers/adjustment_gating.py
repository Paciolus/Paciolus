"""Rule 4: Adjustment gating — POSTED terminal, PROPOSED conditional only.

Parses VALID_TRANSITIONS dict to verify POSTED maps to empty set.
Parses apply_adjustments() body to verify PROPOSED is only added
inside a conditional (if-block), not in the initial valid_statuses set.
"""

import ast
from pathlib import Path

from ..accounting_policy_guard import Violation

RULE = "adjustment_gating"


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    """Find a top-level function definition by name."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _find_assignment(tree: ast.Module, name: str) -> ast.Assign | None:
    """Find a top-level assignment by variable name."""
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return node
    return None


def _check_posted_terminal(assign_node: ast.Assign | ast.AnnAssign, file_path: str) -> list[Violation]:
    """Verify POSTED maps to empty set in VALID_TRANSITIONS."""
    violations = []
    value = assign_node.value if isinstance(assign_node, ast.Assign) else assign_node.value
    if value is None or not isinstance(value, ast.Dict):
        return violations

    for key, val in zip(value.keys, value.values):
        if key is None:
            continue
        # Check if key references POSTED (e.g., AdjustmentStatus.POSTED or "POSTED")
        key_name = ""
        if isinstance(key, ast.Attribute):
            key_name = key.attr
        elif isinstance(key, ast.Constant):
            key_name = str(key.value)
        elif isinstance(key, ast.Name):
            key_name = key.id

        if key_name.upper() == "POSTED":
            # val should be set() or an empty set literal
            is_empty = False
            if isinstance(val, ast.Call):
                # set() call with no args
                if isinstance(val.func, ast.Name) and val.func.id == "set" and not val.args:
                    is_empty = True
            elif isinstance(val, ast.Set) and len(val.elts) == 0:
                is_empty = True

            if not is_empty:
                violations.append(Violation(
                    rule=RULE,
                    file=file_path,
                    line=key.lineno if hasattr(key, "lineno") else assign_node.lineno,
                    message="POSTED status is not terminal in VALID_TRANSITIONS.",
                    severity="error",
                ))

    return violations


def _contains_proposed_ref(node: ast.expr) -> bool:
    """Check if an AST expression references PROPOSED."""
    if isinstance(node, ast.Attribute) and node.attr == "PROPOSED":
        return True
    if isinstance(node, ast.Constant) and str(node.value).upper() == "PROPOSED":
        return True
    if isinstance(node, ast.Name) and node.id == "PROPOSED":
        return True
    return False


def _check_proposed_conditional(func_node: ast.FunctionDef, file_path: str) -> list[Violation]:
    """Verify PROPOSED is not in initial valid_statuses and is only added conditionally."""
    violations = []

    for node in ast.walk(func_node):
        # Check for set literal assignments containing PROPOSED at function body level
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value if isinstance(node, ast.Assign) else node.value
            if value is None:
                continue

            # Get target name
            target_name = ""
            if isinstance(node, ast.Assign) and node.targets:
                t = node.targets[0]
                if isinstance(t, ast.Name):
                    target_name = t.id
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                target_name = node.target.id

            if target_name == "valid_statuses" and isinstance(value, ast.Set):
                # Check if PROPOSED is in the initial set
                for elt in value.elts:
                    if _contains_proposed_ref(elt):
                        violations.append(Violation(
                            rule=RULE,
                            file=file_path,
                            line=node.lineno,
                            message="PROPOSED added to valid_statuses unconditionally in apply_adjustments().",
                            severity="error",
                        ))

        # Check for .add(PROPOSED) outside an if-block
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if (isinstance(call.func, ast.Attribute)
                    and call.func.attr == "add"
                    and call.args):
                if _contains_proposed_ref(call.args[0]):
                    # This .add(PROPOSED) is OK only if it's inside an If node
                    # We check by walking the function body at top level
                    _check_add_in_body(func_node.body, file_path, violations)
                    break  # Only need to check once

    return violations


def _check_add_in_body(body: list[ast.stmt], file_path: str, violations: list[Violation]) -> None:
    """Walk function body to find .add(PROPOSED) not inside an If."""
    for stmt in body:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if (isinstance(call.func, ast.Attribute)
                    and call.func.attr == "add"
                    and call.args
                    and _contains_proposed_ref(call.args[0])):
                violations.append(Violation(
                    rule=RULE,
                    file=file_path,
                    line=stmt.lineno,
                    message="PROPOSED added to valid_statuses unconditionally in apply_adjustments().",
                    severity="error",
                ))
        elif isinstance(stmt, ast.If):
            # .add(PROPOSED) inside an If is OK — that's conditional
            pass
        elif isinstance(stmt, (ast.For, ast.While, ast.With)):
            _check_add_in_body(stmt.body, file_path, violations)


def check_adjustment_gating_ast(
    tree: ast.Module,
    file_path: str,
    transitions_var: str = "VALID_TRANSITIONS",
    apply_fn: str = "apply_adjustments",
) -> list[Violation]:
    """Check a single AST for adjustment gating invariants."""
    violations = []

    # Check A: POSTED terminal in VALID_TRANSITIONS
    assign_node = _find_assignment(tree, transitions_var)
    if assign_node is not None:
        violations.extend(_check_posted_terminal(assign_node, file_path))
    else:
        violations.append(Violation(
            rule=RULE,
            file=file_path,
            line=1,
            message=f"'{transitions_var}' not found at module level.",
            severity="error",
        ))

    # Check B: PROPOSED conditional in apply_adjustments
    func_node = _find_function(tree, apply_fn)
    if func_node is not None:
        violations.extend(_check_proposed_conditional(func_node, file_path))
    else:
        violations.append(Violation(
            rule=RULE,
            file=file_path,
            line=1,
            message=f"Function '{apply_fn}' not found.",
            severity="error",
        ))

    return violations


def check_adjustment_gating(config: dict, backend_root: Path) -> list[Violation]:
    """Run adjustment_gating check."""
    filename = config.get("file", "adjusting_entries.py")
    filepath = backend_root / filename
    if not filepath.exists():
        return [Violation(
            rule=RULE,
            file=filename,
            line=1,
            message=f"File '{filename}' not found.",
            severity="error",
        )]

    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=filename)
    return check_adjustment_gating_ast(
        tree,
        filename,
        transitions_var=config.get("transitions_var", "VALID_TRANSITIONS"),
        apply_fn=config.get("apply_fn", "apply_adjustments"),
    )
