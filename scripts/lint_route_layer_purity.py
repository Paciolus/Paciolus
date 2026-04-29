#!/usr/bin/env python3
"""Route layer purity lint (Sprint 756 — advisory).

Per ADR-015 (`docs/03-engineering/adr-015-backend-route-service-boundaries.md`),
route handlers are orchestration-only:

    validate input → call service → return typed response

Routes that import directly from engine internals (`from <tool>_engine
import ...`) bypass the service layer and recreate the orchestration
inline. This lint flags those imports as advisory findings — each one
is a candidate for a service-layer extraction sprint.

The check is **deliberately permissive about types**: `from <tool>_engine
import <Type>` (importing a result dataclass to type-annotate the
service's return) is fine. The hard signal is the import of an *engine
class* or a *runner function* — that's where the orchestration lives.

Phase 1 (this script): emit findings to stdout, **exit 0**. Wired into
CI as advisory output. Mirrors `scripts/lint_engine_base_adoption.py`'s
discipline.

Phase 2 (future): once a critical mass of routes have been thinned, the
exit code flips to 1 and the lint becomes a hard gate.

Detection heuristic:
    A route module under `backend/routes/` triggers a finding when it
    imports a name from `<tool>_engine` whose name ends with `Engine`
    (the canonical class suffix), or starts with `run_` (the canonical
    runner-function prefix), or starts with `process_` (data-processing
    entry points like `process_tb_chunked`).

    Importing dataclasses (`FluxResult`, `ReconScore`, etc.) is allowed —
    routes legitimately need to type-annotate the service boundary.

Usage:
    python scripts/lint_route_layer_purity.py [--strict]
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
ROUTES_DIR = BACKEND_ROOT / "routes"


def _is_engine_module(module: str) -> bool:
    """`flux_engine`, `audit_engine`, `services.audit.flux.recon`, etc."""
    last_segment = module.rsplit(".", 1)[-1]
    return last_segment.endswith("_engine") or last_segment in {"recon"}


def _is_orchestration_symbol(name: str) -> bool:
    """Class or function that drives the engine pipeline."""
    if name.endswith("Engine"):
        return True
    if name.startswith(("run_", "process_", "audit_trial_balance")):
        return True
    return False


def _scan_route_imports(path: Path) -> list[tuple[int, str, str]]:
    """Return (lineno, module, symbol) for each forbidden engine import."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []

    findings: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        module = node.module or ""
        if not _is_engine_module(module):
            continue
        for alias in node.names:
            name = alias.name
            if _is_orchestration_symbol(name):
                findings.append((node.lineno, module, name))
    return findings


def find_route_purity_violations() -> list[tuple[Path, int, str, str]]:
    """Return route modules that import engine orchestration symbols."""
    violations: list[tuple[Path, int, str, str]] = []
    if not ROUTES_DIR.is_dir():
        return violations
    for path in sorted(ROUTES_DIR.glob("*.py")):
        if path.name.startswith("__"):
            continue
        for lineno, module, symbol in _scan_route_imports(path):
            violations.append((path, lineno, module, symbol))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on findings (default: exit 0 / warning-only).",
    )
    args = parser.parse_args(argv)

    violations = find_route_purity_violations()

    if not violations:
        print("Route layer purity: no routes import engine orchestration symbols.")
        return 0

    print(
        f"Route layer purity: {len(violations)} route-to-engine orchestration "
        f"import(s) found (Sprint 756 -- advisory):"
    )
    grouped: dict[Path, list[tuple[int, str, str]]] = {}
    for path, lineno, module, symbol in violations:
        grouped.setdefault(path, []).append((lineno, module, symbol))
    for path in sorted(grouped):
        rel = path.relative_to(REPO_ROOT)
        print(f"  {rel}:")
        for lineno, module, symbol in grouped[path]:
            print(f"    L{lineno}: {symbol} from {module}")
    print()
    print("Move the orchestration to `services/<domain>/<workflow>.py` and have")
    print("the route call the service. See ADR-015")
    print("(docs/03-engineering/adr-015-backend-route-service-boundaries.md).")

    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
