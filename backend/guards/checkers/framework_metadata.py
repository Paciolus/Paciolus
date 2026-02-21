"""Rule 5: Framework comparability metadata required.

Verifies that specified dataclass/model classes contain a
`framework_note` annotated field. Uses AST to check class bodies.
"""

import ast
from pathlib import Path

from ..accounting_policy_guard import Violation

RULE = "framework_metadata"


def _class_has_field(cls_node: ast.ClassDef, field_name: str) -> bool:
    """Check if a class body contains an annotated assignment with the given name."""
    for item in cls_node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            if item.target.id == field_name:
                return True
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id == field_name:
                    return True
    return False


def check_framework_metadata_ast(
    tree: ast.Module,
    file_path: str,
    class_name: str,
    required_field: str = "framework_note",
) -> list[Violation]:
    """Check a single AST for framework_note field in a specific class."""
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            if not _class_has_field(node, required_field):
                violations.append(Violation(
                    rule=RULE,
                    file=file_path,
                    line=node.lineno,
                    message=f"Class '{class_name}' missing '{required_field}' field. Comparison outputs must include framework comparability metadata.",
                    severity="error",
                ))
            return violations

    # Class not found in file
    violations.append(Violation(
        rule=RULE,
        file=file_path,
        line=1,
        message=f"Class '{class_name}' not found in {file_path}.",
        severity="error",
    ))
    return violations


def check_framework_metadata(config: dict, backend_root: Path) -> list[Violation]:
    """Run framework_metadata check across all configured targets."""
    violations = []
    targets = config.get("targets", {})
    required_field = config.get("required_field", "framework_note")

    # Cache parsed trees per file
    parsed: dict[str, ast.Module] = {}

    for class_name, filename in targets.items():
        if filename not in parsed:
            filepath = backend_root / filename
            if not filepath.exists():
                violations.append(Violation(
                    rule=RULE,
                    file=filename,
                    line=1,
                    message=f"File '{filename}' not found.",
                    severity="error",
                ))
                continue
            source = filepath.read_text(encoding="utf-8")
            parsed[filename] = ast.parse(source, filename=filename)

        if filename in parsed:
            violations.extend(check_framework_metadata_ast(
                parsed[filename], filename, class_name, required_field,
            ))

    return violations
