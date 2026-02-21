"""Accounting Policy Guard — Sprint 378.

Standalone AST-based static analysis enforcing 5 accounting invariants.
Zero external dependencies (stdlib only: ast, tomllib, pathlib, dataclasses).

Usage:
    python guards/accounting_policy_guard.py          # from backend/
    python backend/guards/accounting_policy_guard.py  # from project root

Exit codes:
    0 — all rules pass
    1 — one or more violations found
"""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Violation:
    """A single policy violation with file/line diagnostic."""
    rule: str       # e.g. "no_float_monetary"
    file: str       # relative path from backend/
    line: int       # 1-indexed
    message: str
    severity: str   # "error"


def load_config(config_path: Path) -> dict:
    """Load and return TOML configuration."""
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def run_checks(config: dict, backend_root: Path) -> list[Violation]:
    """Run all enabled checks and return collected violations."""
    # Import checkers here to avoid circular imports at module level
    from .checkers.monetary_float import check_monetary_float
    from .checkers.hard_delete import check_hard_delete
    from .checkers.contract_fields import check_contract_fields
    from .checkers.adjustment_gating import check_adjustment_gating
    from .checkers.framework_metadata import check_framework_metadata

    violations: list[Violation] = []
    rules = config.get("rules", {})

    checker_map = {
        "no_float_monetary": check_monetary_float,
        "no_hard_delete": check_hard_delete,
        "revenue_contract_fields": check_contract_fields,
        "adjustment_gating": check_adjustment_gating,
        "framework_metadata": check_framework_metadata,
    }

    for rule_name, check_fn in checker_map.items():
        rule_config = rules.get(rule_name, {})
        if not rule_config.get("enabled", True):
            continue
        violations.extend(check_fn(rule_config, backend_root))

    return violations


def format_github_annotations(violations: list[Violation]) -> str:
    """Format violations as GitHub Actions ::error annotations."""
    lines = []
    for v in violations:
        lines.append(f"::error file=backend/{v.file},line={v.line}::[{v.rule}] {v.message}")
    return "\n".join(lines)


def format_summary(violations: list[Violation]) -> str:
    """Format a human-readable summary table."""
    if not violations:
        return "Accounting Policy Guard: ALL 5 RULES PASSED"

    lines = [
        f"Accounting Policy Guard: {len(violations)} violation(s) found",
        "",
        f"{'Rule':<30} {'File':<40} {'Line':>5}  Message",
        "-" * 120,
    ]
    for v in violations:
        lines.append(f"{v.rule:<30} {v.file:<40} {v.line:>5}  {v.message}")

    return "\n".join(lines)


def main() -> int:
    """Entry point. Returns exit code."""
    # Resolve paths — support running from backend/ or project root
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir / "accounting_policy.toml"
    backend_root = script_dir.parent  # guards/ is inside backend/

    if not config_path.exists():
        print(f"::error::Config not found: {config_path}", file=sys.stderr)
        return 1

    config = load_config(config_path)
    violations = run_checks(config, backend_root)

    # Output
    if violations:
        print(format_github_annotations(violations))
        print()
    print(format_summary(violations))

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
