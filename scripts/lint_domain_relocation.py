#!/usr/bin/env python3
"""Domain package relocation lint (Sprint 756 — advisory).

Per ADR-018 (`docs/03-engineering/adr-018-domain-package-relocation.md`),
top-level `backend/*_engine.py` modules should incrementally migrate to
the per-tool layout `backend/services/audit/<tool>/{analysis,schemas,export}.py`.
Sprint 753 shipped the pattern + the recon pilot; this lint surfaces the
remaining migration backlog.

Phase 1 (this script): emit findings to stdout, **exit 0**. Wired into
CI as advisory output so the noise lands in the build log without
blocking PRs. Mirrors `scripts/lint_engine_base_adoption.py`'s
discipline.

Phase 2 (future sprint): once a critical mass of engines have migrated,
the exit code flips to 1 and the lint becomes a hard gate. Each sub-
sprint ships one engine relocation per ADR-018.

A module qualifies as "migrated" when its body is just a re-export shim
pointing at the new home — i.e., it imports from `services.audit.<tool>`.
The check is conservative: a module that has any non-import code outside
`__all__` is treated as still housing the implementation.

Usage:
    python scripts/lint_domain_relocation.py [--strict]

`--strict` flips exit code to non-zero on findings.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"

# Engines that don't fit the per-tool relocation. Two cases:
#   1. The engine is the audit pipeline orchestrator itself (`audit_engine.py`,
#      `engine_framework.py`) — already a package shim or owned by the
#      framework boundary.
#   2. The engine is genuinely top-level cross-cutting (e.g., the benchmark
#      reference data engine that doesn't belong under any one tool).
#
# Each entry has a one-line rationale. Misclassifications are recoverable
# in a future PR.
NON_RELOCATABLE_ENGINES: frozenset[str] = frozenset({
    "audit_engine.py",       # Backward-compat shim for the `audit/` package
    "engine_framework.py",   # AuditEngineBase ABC — not a tool
    "benchmark_engine.py",   # Cross-cutting reference data, not tool-specific
})


def _is_relocation_candidate(path: Path) -> bool:
    """A `*_engine.py` at backend top-level that isn't blocked."""
    name = path.name
    if not name.endswith("_engine.py"):
        return False
    return name not in NON_RELOCATABLE_ENGINES


def _is_shim(source: str) -> bool:
    """Return True if the module body is essentially just import + __all__.

    A shim's source contains imports (Import / ImportFrom), assignments
    that target `__all__`, and nothing else of substance. Function /
    class definitions disqualify the module.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            # Module / docstring expression
            continue
        if isinstance(node, ast.Assign):
            # Allow `__all__ = [...]` and similar simple assignments
            if all(
                isinstance(target, ast.Name) and target.id.startswith("__")
                for target in node.targets
            ):
                continue
            return False
        # Function or class definition — module owns implementation
        return False
    return True


def find_unrelocated_engines() -> list[Path]:
    """Return engines that are still top-level implementations (not shims)."""
    findings: list[Path] = []
    for path in sorted(BACKEND_ROOT.glob("*_engine.py")):
        if not _is_relocation_candidate(path):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not _is_shim(source):
            findings.append(path)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on findings (default: exit 0 / warning-only).",
    )
    args = parser.parse_args(argv)

    findings = find_unrelocated_engines()

    if not findings:
        print("Domain relocation: every relocatable engine is now a shim.")
        return 0

    print(
        f"Domain relocation: {len(findings)} engine(s) not yet relocated to "
        f"services/audit/<tool>/ (Sprint 753+ -- advisory):"
    )
    for path in findings:
        print(f"  - {path.relative_to(REPO_ROOT)}")
    print()
    print("Migration approach: see docs/03-engineering/adr-018-domain-package-relocation.md")
    print("Each engine is a separate sub-sprint. Default: keep flat unless reorganization adds clear value.")

    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
