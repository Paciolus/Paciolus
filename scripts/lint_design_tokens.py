#!/usr/bin/env python3
"""Oat & Obsidian design-token lint (Sprint 782a).

`CLAUDE.md` mandates the Oat & Obsidian palette — `obsidian-*`, `oatmeal-*`, `clay-*`,
`sage-*` — and forbids Tailwind's generic palettes. The codebase reached **zero** generic
colour classes across 777 frontend files, down from about 150, and nothing protected that
zero except discipline. This is the same shape as the AS 1215 citation, which was swept
from every customer-facing surface in Sprint 717 and then drifted back into three internal
docs within months.

So this is a **hard gate from day one** (exit 1 on any finding), not an advisory phase
like `lint_engine_base_adoption.py`. An advisory phase makes sense when a migration is
outstanding; here there is nothing to migrate.

What counts as a violation
--------------------------
A Tailwind colour utility built from one of the 22 generic palettes with a numeric scale —
``text-blue-500``, ``bg-slate-800``, ``border-gray-200``, ``hover:ring-emerald-500/40``.

Matching is deliberately narrow. The pattern requires a **utility prefix** (``bg-``,
``text-``, ``border-``, …), optionally preceded by variant prefixes (``hover:``, ``dark:``,
``md:``, ``group-hover:``). Bare occurrences are ignored, so prose and data survive: a test
fixture containing the string ``"sky-500"``, a comment mentioning ``red-500``, or an account
named "Blue-500 Industries" are not findings. The first draft of two other guards in this
repo fired mostly false positives by matching substrings instead of syntax; that is the
mistake this avoids.

Semantic colour is not an exception. `sage-*` is the success/positive token and `clay-*` is
the error/expense token — the mandate already supplies both, so "but it's an error state"
is not a reason to reach for `red-500`.

Commented-out code is still a finding. A bare palette word in prose is not matched, but
``// className="bg-slate-800"`` is, because that is nearly always a class on its way back
in rather than a note about one.

Allowlist
---------
`scripts/design_token_allowlist.txt` — one ``path:pattern`` or ``path`` per line, ``#``
comments permitted. An entry must carry a reason in a trailing comment; the companion test
asserts that. The file ships empty: every exception should have to argue for itself.

Usage
-----
    python scripts/lint_design_tokens.py            # repo root or anywhere
    python scripts/lint_design_tokens.py --json     # machine-readable findings

Exit codes
----------
    0 — no generic colour classes
    1 — at least one finding
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
ALLOWLIST_PATH = Path(__file__).resolve().parent / "design_token_allowlist.txt"

SCANNED_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".css", ".mdx")

# Tailwind's generic palettes. The Oat & Obsidian scales (obsidian, oatmeal, clay, sage)
# are deliberately absent, as are semantic aliases defined in tailwind.config.js.
GENERIC_PALETTES = (
    "slate",
    "gray",
    "grey",
    "zinc",
    "neutral",
    "stone",
    "red",
    "orange",
    "amber",
    "yellow",
    "lime",
    "green",
    "emerald",
    "teal",
    "cyan",
    "sky",
    "blue",
    "indigo",
    "violet",
    "purple",
    "fuchsia",
    "pink",
    "rose",
)

# Colour-bearing Tailwind utilities. A generic palette after any of these is a class,
# not prose.
COLOUR_UTILITIES = (
    "bg",
    "text",
    # Directional and axis variants are separate utilities in Tailwind:
    # `border-l-red-500`, `divide-x-blue-200`, `border-t-slate-700`. The first draft
    # listed only the base names, so every directional colour slipped through — caught
    # in review on PR #176.
    "border",
    "border-x",
    "border-y",
    "border-s",
    "border-e",
    "border-t",
    "border-r",
    "border-b",
    "border-l",
    "divide-x",
    "divide-y",
    "outline-t",
    "outline-r",
    "outline-b",
    "outline-l",
    "ring",
    "ring-offset",
    "divide",
    "outline",
    "decoration",
    "shadow",
    "accent",
    "caret",
    "fill",
    "stroke",
    "placeholder",
    "from",
    "via",
    "to",
)

_VARIANT = r"(?:[a-z][a-z0-9-]*:)*"  # hover: dark: md: group-hover: peer-focus: …

# Longest-first. Regex alternation is leftmost-first, so `(?:50|...)` would match the
# "50" inside "500" and report `bg-red-50` for `bg-red-500` — the gate still fires, but
# names a class that does not exist, which is worse than useless in an error message.
_SCALE = r"(?:950|[1-9]00|50)"
_OPACITY = r"(?:/(?:\d{1,3}|\[[^\]]+\]))?"

VIOLATION_RE = re.compile(
    r"(?<![\w-])"
    + _VARIANT
    + r"(?:"
    + "|".join(COLOUR_UTILITIES)
    + r")-(?:"
    + "|".join(GENERIC_PALETTES)
    + r")-"
    + _SCALE
    + r"(?!\d)"  # so bg-blue-5000 is not read as bg-blue-500
    + _OPACITY
    + r"(?![\w-])"
)


@dataclass(frozen=True)
class Finding:
    """One generic colour class."""

    path: str
    line: int
    match: str
    text: str


def load_allowlist(path: Path = ALLOWLIST_PATH) -> list[tuple[str, str | None]]:
    """Parse the allowlist into (path_fragment, pattern_or_None) entries."""
    if not path.exists():
        return []
    entries: list[tuple[str, str | None]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" in line:
            path_part, pattern = line.split(":", 1)
            entries.append((path_part.strip(), pattern.strip() or None))
        else:
            entries.append((line, None))
    return entries


def _is_allowed(rel_path: str, match: str, allowlist: list[tuple[str, str | None]]) -> bool:
    for path_fragment, pattern in allowlist:
        if path_fragment not in rel_path:
            continue
        if pattern is None or pattern == match:
            return True
    return False


def _display_path(path: Path) -> str:
    """Repo-relative path where possible, absolute otherwise.

    Callers outside the repo (unit tests, ad-hoc runs on a copy) must not crash on
    `relative_to`.
    """
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def scan_file(path: Path, allowlist: list[tuple[str, str | None]]) -> list[Finding]:
    """Return findings for one file."""
    rel = _display_path(path)
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in VIOLATION_RE.finditer(line):
            if _is_allowed(rel, m.group(0), allowlist):
                continue
            findings.append(Finding(path=rel, line=lineno, match=m.group(0), text=line.strip()[:160]))
    return findings


def scan(root: Path = FRONTEND_SRC) -> list[Finding]:
    """Scan every supported file under `root`."""
    allowlist = load_allowlist()
    findings: list[Finding] = []
    if not root.exists():
        return findings
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in SCANNED_SUFFIXES:
            findings.extend(scan_file(path, allowlist))
    return findings


SUGGESTIONS = {
    "red": "clay-* (errors, expenses, abnormal balances)",
    "rose": "clay-*",
    "orange": "clay-* or oatmeal-*",
    "green": "sage-* (success, income, positive states)",
    "emerald": "sage-*",
    "lime": "sage-*",
    "teal": "sage-*",
    "slate": "obsidian-* (dark) or oatmeal-* (light)",
    "gray": "obsidian-* or oatmeal-*",
    "grey": "obsidian-* or oatmeal-*",
    "zinc": "obsidian-* or oatmeal-*",
    "neutral": "obsidian-* or oatmeal-*",
    "stone": "oatmeal-*",
}


def _suggestion(match: str) -> str:
    for palette, hint in SUGGESTIONS.items():
        if f"-{palette}-" in match:
            return hint
    return "an Oat & Obsidian token: obsidian-* / oatmeal-* / clay-* / sage-*"


def format_report(findings: list[Finding]) -> str:
    if not findings:
        return "Design token lint: ALL CHECKS PASSED (0 generic colour classes)"
    lines = [f"Design token lint: {len(findings)} generic colour class(es) found", ""]
    for f in findings:
        lines.append(f"  {f.path}:{f.line}  {f.match}")
        lines.append(f"      use {_suggestion(f.match)}")
        lines.append(f"      {f.text}")
    lines.append("")
    lines.append(
        "CLAUDE.md mandates the Oat & Obsidian palette and forbids generic Tailwind colours. "
        "Semantic states are covered: sage-* for success/income, clay-* for error/expense. "
        "If an exception is genuinely warranted, add it to scripts/design_token_allowlist.txt "
        "with a reason."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint for generic Tailwind colour classes.")
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    args = parser.parse_args(argv)

    findings = scan()

    if args.json:
        print(json.dumps([f.__dict__ for f in findings], indent=2))
    else:
        for f in findings:
            print(f"::error file={f.path},line={f.line}::[design_token] {f.match} — use {_suggestion(f.match)}")
        if findings:
            print()
        print(format_report(findings))

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
