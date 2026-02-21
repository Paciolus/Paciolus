"""Rule 3: Revenue contract field retention.

Parses RevenueColumnDetection and RevenueEntry dataclass bodies to verify
all 6 ASC 606/IFRS 15 contract fields are present. Also verifies
ContractEvidenceLevel.total_contract_fields defaults to the expected count.
"""

import ast
from pathlib import Path

from ..accounting_policy_guard import Violation

RULE = "revenue_contract_fields"


def _get_class_fields(node: ast.ClassDef) -> dict[str, int]:
    """Extract field names and their line numbers from a class body."""
    fields: dict[str, int] = {}
    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            fields[item.target.id] = item.lineno
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    fields[target.id] = item.lineno
    return fields


def _get_field_default(node: ast.ClassDef, field_name: str) -> int | None:
    """Get the integer default value for a field in a class body."""
    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            if item.target.id == field_name and item.value is not None:
                if isinstance(item.value, ast.Constant) and isinstance(item.value.value, int):
                    return item.value.value
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id == field_name:
                    if isinstance(item.value, ast.Constant) and isinstance(item.value.value, int):
                        return item.value.value
    return None


def check_contract_fields_ast(
    tree: ast.Module,
    file_path: str,
    required_fields: list[str],
    detection_class: str,
    entry_class: str,
    evidence_class: str,
    expected_total: int,
) -> list[Violation]:
    """Check a single AST for contract field retention."""
    violations = []

    classes: dict[str, ast.ClassDef] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes[node.name] = node

    # Check detection class has all contract column fields
    for cls_name, suffix in [(detection_class, "_column"), (entry_class, "")]:
        cls_node = classes.get(cls_name)
        if cls_node is None:
            violations.append(Violation(
                rule=RULE,
                file=file_path,
                line=1,
                message=f"Class '{cls_name}' not found. ASC 606/IFRS 15 regression.",
                severity="error",
            ))
            continue

        fields = _get_class_fields(cls_node)
        for req_field in required_fields:
            full_field = f"{req_field}{suffix}"
            if full_field not in fields:
                violations.append(Violation(
                    rule=RULE,
                    file=file_path,
                    line=cls_node.lineno,
                    message=f"Missing contract field '{full_field}' in {cls_name}. ASC 606/IFRS 15 regression.",
                    severity="error",
                ))

    # Check ContractEvidenceLevel.total_contract_fields default
    evidence_node = classes.get(evidence_class)
    if evidence_node is not None:
        actual_total = _get_field_default(evidence_node, "total_contract_fields")
        if actual_total is not None and actual_total != expected_total:
            violations.append(Violation(
                rule=RULE,
                file=file_path,
                line=evidence_node.lineno,
                message=f"{evidence_class}.total_contract_fields defaults to {actual_total}, expected {expected_total}. ASC 606/IFRS 15 regression.",
                severity="error",
            ))
    elif evidence_class in [detection_class, entry_class]:
        pass  # Already reported above
    else:
        # Only report if not already found
        if evidence_class not in classes:
            violations.append(Violation(
                rule=RULE,
                file=file_path,
                line=1,
                message=f"Class '{evidence_class}' not found. ASC 606/IFRS 15 regression.",
                severity="error",
            ))

    return violations


def check_contract_fields(config: dict, backend_root: Path) -> list[Violation]:
    """Run revenue_contract_fields check."""
    filename = config.get("file", "revenue_testing_engine.py")
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
    return check_contract_fields_ast(
        tree,
        filename,
        required_fields=config.get("required_fields", []),
        detection_class=config.get("detection_class", "RevenueColumnDetection"),
        entry_class=config.get("entry_class", "RevenueEntry"),
        evidence_class=config.get("evidence_class", "ContractEvidenceLevel"),
        expected_total=config.get("expected_total", 6),
    )
