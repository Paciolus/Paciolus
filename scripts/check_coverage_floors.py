#!/usr/bin/env python3
"""Per-file coverage floor enforcement (Sprint 723).

Reads ``backend/coverage_floors.toml`` and a coverage report (the JSON output
of ``pytest --cov --cov-report=json``) and asserts every floored file is at or
above its declared minimum. The global ``--cov-fail-under=80`` already wired
into CI catches *aggregate* regressions; this script catches *targeted*
regressions in files where coverage is the highest-risk gap.

Exit codes:
    0 — all floors met (or no floors configured)
    1 — at least one floor breached, or a floored file is missing from the
        coverage report (the ``--missing-ok`` flag downgrades the latter to a
        warning, used during transition windows when a file is renamed)
    2 — usage / IO error (missing coverage.json, unparseable TOML)

Path matching: floors use forward slashes; coverage.json paths from CI use
forward slashes; coverage.json paths from Windows local dev use backslashes.
This script normalizes both sides to forward slashes before comparison.

Usage:
    python scripts/check_coverage_floors.py <coverage.json> [<floors.toml>]

If ``<floors.toml>`` is omitted, defaults to ``backend/coverage_floors.toml``.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

EXIT_OK = 0
EXIT_FLOOR_BREACH = 1
EXIT_USAGE_ERROR = 2

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FLOORS_PATH = REPO_ROOT / "backend" / "coverage_floors.toml"


def _normalize(path: str) -> str:
    """Normalize a coverage path for comparison: forward slashes, lowercase, no leading ./.

    Coverage.json on Linux uses ``foo/bar.py``; on Windows it can be ``foo\\bar.py``.
    Some pytest invocations also prefix with ``./``. Lowercasing is conservative
    against case-insensitive Windows filesystems creating false negatives.
    """
    p = path.replace("\\", "/").lower()
    if p.startswith("./"):
        p = p[2:]
    return p


def load_floors(floors_path: Path) -> dict[str, int]:
    """Load the floors map from TOML. Returns ``{normalized_path: min_pct}``.

    Any TOML parse error or missing ``[floors]`` table raises and is surfaced as
    EXIT_USAGE_ERROR by ``main()``.
    """
    raw = floors_path.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))
    floors_section = data.get("floors") or {}
    if not isinstance(floors_section, dict):
        raise ValueError(f"{floors_path}: [floors] is not a table")
    out: dict[str, int] = {}
    for path, value in floors_section.items():
        if not isinstance(value, (int, float)):
            raise ValueError(f"{floors_path}: '{path}' floor must be a number, got {type(value).__name__}")
        if not 0 <= value <= 100:
            raise ValueError(f"{floors_path}: '{path}' floor {value} outside 0..100")
        out[_normalize(path)] = int(value)
    return out


def load_coverage(coverage_path: Path) -> dict[str, float]:
    """Load coverage.json and return ``{normalized_path: percent_covered}``."""
    data = json.loads(coverage_path.read_bytes().decode("utf-8"))
    files = data.get("files") or {}
    if not isinstance(files, dict):
        raise ValueError(f"{coverage_path}: 'files' is not a dict")
    out: dict[str, float] = {}
    for path, entry in files.items():
        if not isinstance(entry, dict):
            continue
        summary = entry.get("summary") or {}
        pct = summary.get("percent_covered")
        if pct is None:
            continue
        out[_normalize(path)] = float(pct)
    return out


def check(
    floors: dict[str, int],
    coverage: dict[str, float],
    *,
    missing_ok: bool = False,
) -> tuple[list[str], list[str]]:
    """Compare floors against coverage. Returns ``(failures, warnings)``.

    A *failure* is a floor breach (current pct < floor pct) or a missing-coverage
    entry when ``missing_ok=False``. A *warning* is a missing-coverage entry when
    ``missing_ok=True``. Failures cause non-zero exit; warnings do not.
    """
    failures: list[str] = []
    warnings: list[str] = []
    for path, floor_pct in sorted(floors.items()):
        actual_pct = coverage.get(path)
        if actual_pct is None:
            msg = f"{path}: not present in coverage report (file renamed or excluded?)"
            if missing_ok:
                warnings.append(msg)
            else:
                failures.append(msg)
            continue
        if actual_pct < floor_pct:
            failures.append(
                f"{path}: {actual_pct:.2f}% below floor {floor_pct}% "
                f"(deficit {floor_pct - actual_pct:.2f}pp)"
            )
    return failures, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("coverage_json", type=Path, help="Path to pytest coverage.json")
    parser.add_argument(
        "floors_toml",
        nargs="?",
        default=DEFAULT_FLOORS_PATH,
        type=Path,
        help=f"Path to coverage_floors.toml (default: {DEFAULT_FLOORS_PATH})",
    )
    parser.add_argument(
        "--missing-ok",
        action="store_true",
        help="Treat missing-coverage entries as warnings (used during file-rename windows).",
    )
    args = parser.parse_args(argv)

    if not args.coverage_json.exists():
        print(f"ERROR: coverage report not found: {args.coverage_json}", file=sys.stderr)
        return EXIT_USAGE_ERROR
    if not args.floors_toml.exists():
        print(f"ERROR: floors file not found: {args.floors_toml}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    try:
        floors = load_floors(args.floors_toml)
    except (tomllib.TOMLDecodeError, ValueError) as exc:
        print(f"ERROR: failed to load floors: {exc}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    try:
        coverage = load_coverage(args.coverage_json)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: failed to load coverage report: {exc}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    if not floors:
        print(f"No floors configured in {args.floors_toml} — nothing to check.")
        return EXIT_OK

    failures, warnings = check(floors, coverage, missing_ok=args.missing_ok)

    print(f"Coverage Floor Check — {len(floors)} floor(s) configured")
    for path in sorted(floors):
        actual = coverage.get(path)
        floor = floors[path]
        if actual is None:
            mark = "??" if args.missing_ok else "FAIL"
            print(f"  [{mark}] {path}: missing from coverage")
        elif actual < floor:
            print(f"  [FAIL] {path}: {actual:.2f}% < {floor}%")
        else:
            print(f"  [ OK ] {path}: {actual:.2f}% >= {floor}%")

    if warnings:
        print()
        print(f"WARNINGS ({len(warnings)}):", file=sys.stderr)
        for w in warnings:
            print(f"  ⚠ {w}", file=sys.stderr)

    if failures:
        print()
        print(f"FAILURES ({len(failures)}):", file=sys.stderr)
        for f in failures:
            print(f"  ✗ {f}", file=sys.stderr)
        print(file=sys.stderr)
        print("Coverage floor check FAILED.", file=sys.stderr)
        print(
            "To raise a floor after a coverage backfill: edit "
            "backend/coverage_floors.toml.",
            file=sys.stderr,
        )
        return EXIT_FLOOR_BREACH

    print()
    print(f"All {len(floors)} coverage floors met.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------------
# Public test surface — these helpers are imported by
# backend/tests/test_coverage_floors.py.
# ---------------------------------------------------------------------------

__all__ = ["load_floors", "load_coverage", "check", "main", "_normalize"]


# Type-stub silencer for ``check`` since pytest discovery and type checkers
# both look at the public surface.
_AnyDict = dict[str, Any]
