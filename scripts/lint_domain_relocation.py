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
    """Return True if the module body is recognizably a shim.

    Two shim patterns are accepted:

    1. **Static re-export** — body is imports (Import / ImportFrom),
       dunder assignments (``__all__ = [...]``), and docstrings only.
       Used by `recon_engine.py`, `flux_engine.py`, `cutoff_risk_engine.py`.

    2. **Dynamic namespace copy** — body imports the canonical module
       as ``_impl``, then loops ``for _name in dir(_impl):`` to re-export
       every non-dunder name (handles 35+ public symbols + private test
       helpers without per-symbol maintenance). Used by the testing
       engine relocations (`ap_testing_engine`, `je_testing_engine`,
       etc.). Detected by presence of a ``for`` loop targeting ``_name``
       with a ``setattr`` call inside.

    Function / class definitions disqualify the module either way —
    those mean the engine still hosts implementation code.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False

    has_dynamic_reexport = _has_dynamic_namespace_copy(tree)

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            # Module / docstring expression
            continue
        if isinstance(node, ast.Assign):
            # Allow `__all__ = [...]` and similar dunder assignments
            if all(
                isinstance(target, ast.Name) and target.id.startswith("__")
                for target in node.targets
            ):
                continue
            # Within a dynamic-namespace shim, allow private (single-
            # underscore) loop-local bindings like `_module = sys.modules[__name__]`.
            if has_dynamic_reexport and all(
                isinstance(target, ast.Name) and target.id.startswith("_")
                for target in node.targets
            ):
                continue
            return False
        if isinstance(node, ast.For) and has_dynamic_reexport:
            # The dynamic namespace copy loop is allowed.
            continue
        if isinstance(node, ast.Delete) and has_dynamic_reexport:
            # The cleanup `del _sys, _module, _name, _impl` after the loop is allowed.
            continue
        # Function or class definition — module owns implementation
        return False
    return True


def _has_dynamic_namespace_copy(tree: ast.Module) -> bool:
    """Detect the dynamic-namespace shim pattern.

    Looks for a ``for _name in dir(<something>):`` loop whose body
    contains a ``setattr(...)`` call. That signature uniquely identifies
    the testing-engine shim pattern; we don't false-positive on regular
    business loops.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        # Loop variable named ``_name``
        if not (isinstance(node.target, ast.Name) and node.target.id == "_name"):
            continue
        # Iterating ``dir(...)``
        iter_call = node.iter
        if not (
            isinstance(iter_call, ast.Call)
            and isinstance(iter_call.func, ast.Name)
            and iter_call.func.id == "dir"
        ):
            continue
        # Body contains ``setattr(...)``
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "setattr"
            ):
                return True
    return False


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
