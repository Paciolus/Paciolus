#!/usr/bin/env python3
"""Dead-route guardrail for backend/routes/*.py modules.

A route module is considered "wired" when it is imported either:
    1. Directly in backend/routes/__init__.py (registered in all_routers), or
    2. By a known aggregator module that is itself imported in __init__.py.

Aggregators include sub-routers from audit.py, export.py, engagements.py -- these
are the known router-composition files that mount sub-routers on a parent
router before the parent is registered via __init__.py.

Usage:
    python scripts/check_route_wiring.py

Exit codes:
    0 -- all route modules are wired (pass)
    1 -- one or more route modules are truly unreferenced (fail)
    2 -- cannot locate backend/routes/ (environment error)

Sprint 677: dead-code hygiene pass.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTES_DIR = REPO_ROOT / "backend" / "routes"

AGGREGATOR_MODULES: tuple[str, ...] = (
    "audit.py",
    "export.py",
    "engagements.py",
)

IMPORT_PATTERN = re.compile(
    r"^\s*(?:from\s+routes\.(?P<mod1>[A-Za-z_][A-Za-z0-9_]*)"
    r"|import\s+routes\.(?P<mod2>[A-Za-z_][A-Za-z0-9_]*))",
    re.MULTILINE,
)


def _collect_imported_modules(py_file: Path) -> set[str]:
    """Return the set of routes.<name> modules imported by a given file."""
    text = py_file.read_text(encoding="utf-8")
    names: set[str] = set()
    for match in IMPORT_PATTERN.finditer(text):
        name = match.group("mod1") or match.group("mod2")
        if name:
            names.add(name)
    return names


def main() -> int:
    if not ROUTES_DIR.is_dir():
        print(f"ERROR: routes directory not found: {ROUTES_DIR}", file=sys.stderr)
        return 2

    init_file = ROUTES_DIR / "__init__.py"
    if not init_file.is_file():
        print(f"ERROR: routes/__init__.py not found: {init_file}", file=sys.stderr)
        return 2

    all_modules: set[str] = {
        p.stem for p in ROUTES_DIR.glob("*.py") if p.name != "__init__.py"
    }
    aggregator_stems: set[str] = {Path(a).stem for a in AGGREGATOR_MODULES}

    init_imports = _collect_imported_modules(init_file)

    aggregator_imports: set[str] = set()
    for agg_name in AGGREGATOR_MODULES:
        agg_path = ROUTES_DIR / agg_name
        if agg_path.is_file():
            aggregator_imports |= _collect_imported_modules(agg_path)

    # A module is wired if it is:
    #   - imported directly from routes/__init__.py, OR
    #   - imported by a known aggregator that is itself wired in __init__.py.
    wired: set[str] = set(init_imports) | set(aggregator_imports)

    # Aggregators themselves must be imported from __init__.py. We don't
    # treat them as orphaned even if their sub-modules are imported only
    # by the aggregator, but we DO require the aggregator to be wired.
    unreferenced: set[str] = set()
    for mod in sorted(all_modules):
        if mod in wired:
            continue
        # An aggregator is "wired" via init_imports only.
        if mod in aggregator_stems and mod in init_imports:
            continue
        unreferenced.add(mod)

    print("Paciolus route wiring check")
    print("=" * 40)
    print(f"Route modules scanned:       {len(all_modules)}")
    print(f"Imported by __init__.py:     {len(init_imports & all_modules)}")
    print(f"Imported by aggregators:     {len(aggregator_imports & all_modules)}")
    print(f"Aggregators checked:         {', '.join(sorted(aggregator_stems))}")
    print()

    if unreferenced:
        print(f"FAIL -- {len(unreferenced)} unreferenced route module(s):")
        for mod in sorted(unreferenced):
            print(f"  - routes/{mod}.py")
        print()
        print("Either register the module in routes/__init__.py,")
        print("import it from a known aggregator, or delete it.")
        return 1

    print("PASS -- all route modules are wired.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
