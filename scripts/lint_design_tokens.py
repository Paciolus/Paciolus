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

Sprint 809 added two checks (findings D-2 and D-3)
--------------------------------------------------
The 2026-10-22 full-spectrum review called this "the best-built guard in the repo"
and then walked straight past it, because it only asks whether a colour comes from
a *generic Tailwind* palette. It never asked whether a brand token **exists**, or
whether a brand shade is **legible**.

**D-2 — undefined brand token.** `text-content-muted` had 36 live usages across
checkout, billing, team, shares, branding, admin-dashboard and internal/admin.
`content-muted` is not a token: `tailwind.config.js` defines
primary/secondary/tertiary/disabled, and there is no `--text-muted`. Proven against
the compiled stylesheet, the class emitted **zero** CSS rules, so all 36 elements
silently inherited colour and lost the muted tier of the hierarchy. The gate passed
it. `check_undefined_tokens()` now resolves every `content-*` / `surface-*` /
`border-theme-*` / `theme-*-*` class against the config, which closes the class
rather than the instance.

**D-3 — illegible brand shade.** `sage-500` measures 3.85:1 on the dark page and
4.42:1 on the light page — **below the 4.5:1 AA threshold for normal text in both
themes** — and 61 usages of `text-sage-500` / `text-clay-500` carried no theme
qualifier. `check_contrast()` computes WCAG 2.1 ratios from the palette in the
config and flags a `text-` utility whose shade fails AA on *both* page surfaces,
i.e. one that cannot be legible anywhere.

Deliberate limit on the contrast check: a shade that fails on *one* surface is only
a defect if it renders there, and this gate has no route→theme map to decide. That
map is finding D-4, and closing it is the prerequisite for tightening this rule.
Until then `text-sage-700` (8.18:1 light, 2.08:1 dark) is not flagged, because it is
correct on the light pages where it is in fact used. The rule is narrow on purpose:
two other guards in this repo shipped first drafts that fired mostly false
positives, and a gate nobody trusts gets switched off.

Note on WCAG scope: 4.5:1 (SC 1.4.3) governs *text*; icons and graphical objects
need 3:1 (SC 1.4.11), which `sage-500` does meet. The check only looks at `text-`
utilities for that reason.

Exit codes
----------
    0 — no generic colour classes, no undefined tokens, no illegible shades
    1 — at least one finding
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
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
    """One finding: a generic colour class, an undefined token, or an illegible shade."""

    path: str
    line: int
    match: str
    text: str
    # Sprint 809: which check produced this. Defaulted so existing constructors
    # and the companion test suite keep working unchanged.
    kind: str = "generic_palette"
    detail: str = ""

# =============================================================================
# Sprint 809 — D-2: brand tokens that do not exist
# =============================================================================

TAILWIND_CONFIG = REPO_ROOT / "frontend" / "tailwind.config.js"

# Token groups resolved against the config. A class of the form
# `{utility}-{group}-{name}` where `group` is one of these must name a real member.
RESOLVED_TOKEN_GROUPS = ("content", "surface", "theme-success", "theme-error", "theme-warning", "theme-info")

# Page surfaces the contrast check measures against, by theme. These are the
# `--surface-page` values in globals.css.
PAGE_SURFACES: dict[str, str] = {"dark": "#121212", "light": "#F5F4F2"}

# WCAG 2.1 SC 1.4.3, normal text.
AA_TEXT_RATIO = 4.5

# Brand palettes whose shades the contrast check measures. Generic palettes are
# already a hard finding, so they never reach this check.
CONTRAST_CHECKED_PALETTES = ("sage", "clay", "obsidian", "oatmeal")

# Shade-level exemptions from the contrast check, each with its reason.
#
# Separate from `design_token_allowlist.txt` on purpose: that file exempts a
# *class in a path*, which is the right shape for "this one file may use a
# generic colour". These are exemptions for a *shade everywhere*, which needs a
# different argument. `format_report` prints them on every run, so an exemption
# stays visible rather than becoming invisible permission.
CONTRAST_EXEMPT_SHADES: dict[str, str] = {
    # #757575, the `--text-disabled` value in both themes (4.07:1 dark,
    # 4.19:1 light). WCAG 2.1 SC 1.4.3 exempts text in inactive user interface
    # components, which is exactly what this shade is for. A permanent exemption.
    "obsidian-400": (
        "the --text-disabled value; WCAG 2.1 SC 1.4.3 exempts inactive UI components"
    ),
    # oatmeal-700 (#7F7A6E, 4.38:1 dark / 3.89:1 light) was exempted here while
    # its 48 usages waited on a route->theme map. Sprint 809 built the map and
    # Sprint 828 migrated every usage by surface: obsidian-500 (5.63:1) on the
    # light badge/page surfaces, oatmeal-600 (5.33:1) on dark marketing routes.
    # The exemption is gone, so any new oatmeal-700 text fails this gate.
}


@lru_cache(maxsize=4)
def _parse_token_groups(config_path: Path = TAILWIND_CONFIG) -> dict[str, set[str]]:
    """
    Member names for each resolved token group, read out of tailwind.config.js.

    Deliberately a focused regex rather than a JS parser: the shape being read is
    `group: { name: 'value', ... }` inside the `colors` block, and a dependency on
    a JS runtime would make this gate skippable.
    """
    if not config_path.exists():
        return {}
    text = config_path.read_text(encoding="utf-8")
    groups: dict[str, set[str]] = {}
    for group in RESOLVED_TOKEN_GROUPS:
        # Accept both `content: {` and `'theme-success': {`
        pattern = rf"['\"]?{re.escape(group)}['\"]?\s*:\s*\{{(.*?)\}}"
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            continue
        body = match.group(1)
        members = set(re.findall(r"^\s*['\"]?([A-Za-z][A-Za-z0-9_-]*)['\"]?\s*:", body, re.MULTILINE))
        if members:
            groups[group] = members
    return groups


@lru_cache(maxsize=4)
def _parse_palette(config_path: Path = TAILWIND_CONFIG) -> dict[str, dict[str, str]]:
    """Hex values per brand palette shade, read out of tailwind.config.js."""
    if not config_path.exists():
        return {}
    text = config_path.read_text(encoding="utf-8")
    palettes: dict[str, dict[str, str]] = {}
    for palette in CONTRAST_CHECKED_PALETTES:
        match = re.search(rf"\b{re.escape(palette)}\s*:\s*\{{(.*?)\}}", text, re.DOTALL)
        if not match:
            continue
        shades = {
            shade: value
            for shade, value in re.findall(r"['\"]?(\d{2,3})['\"]?\s*:\s*['\"](#[0-9A-Fa-f]{6})['\"]", match.group(1))
        }
        if shades:
            palettes[palette] = shades
    return palettes


def _relative_luminance(hex_colour: str) -> float:
    """WCAG 2.1 relative luminance."""

    def channel(value: int) -> float:
        c = value / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG 2.1 contrast ratio between two hex colours."""
    lf, lb = _relative_luminance(foreground), _relative_luminance(background)
    lighter, darker = max(lf, lb), min(lf, lb)
    return (lighter + 0.05) / (darker + 0.05)


@lru_cache(maxsize=4)
def illegible_text_shades(config_path: Path = TAILWIND_CONFIG) -> dict[str, float]:
    """
    `{palette}-{shade}` combinations that fail AA for normal text on **both** page
    surfaces, mapped to their better of the two ratios.

    Derived from the palette rather than hardcoded, so adjusting a shade in the
    config adjusts the gate.
    """
    results: dict[str, float] = {}
    for palette, shades in _parse_palette(config_path).items():
        for shade, hex_colour in shades.items():
            ratios = [contrast_ratio(hex_colour, surface) for surface in PAGE_SURFACES.values()]
            if max(ratios) < AA_TEXT_RATIO:
                results[f"{palette}-{shade}"] = max(ratios)
    return results


_UNDEFINED_TOKEN_RE = re.compile(
    r"(?<![\w-])"
    + _VARIANT
    + r"(?:"
    + "|".join(COLOUR_UTILITIES)
    + r")-("
    + "|".join(re.escape(g) for g in RESOLVED_TOKEN_GROUPS)
    + r")-([a-z][a-z0-9-]*)"
    + _OPACITY
    + r"(?![\w-])"
)

_TEXT_SHADE_RE = re.compile(
    r"(?<![\w-])" + _VARIANT + r"text-(" + "|".join(CONTRAST_CHECKED_PALETTES) + r")-(\d{2,3})" + _OPACITY + r"(?![\w-])"
)



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
    """
    Return findings for one file: generic palettes, undefined tokens, illegible shades.

    The two config reads below are `lru_cache`d, because this function runs once
    per source file and there are ~780 of them — parsing tailwind.config.js 780
    times to answer the same question is pure waste in a CI gate. Treat the
    returned dicts as read-only: they are the cached objects, not copies.
    """
    rel = _display_path(path)
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    token_groups = _parse_token_groups()
    illegible = illegible_text_shades()

    for lineno, line in enumerate(text.splitlines(), 1):
        for m in VIOLATION_RE.finditer(line):
            if _is_allowed(rel, m.group(0), allowlist):
                continue
            findings.append(Finding(path=rel, line=lineno, match=m.group(0), text=line.strip()[:160]))

        # D-2: a brand token that does not exist emits no CSS at all, so the
        # element silently inherits colour. `text-content-muted` had 36 live
        # usages and this gate passed every one of them.
        for m in _UNDEFINED_TOKEN_RE.finditer(line):
            group, member = m.group(1), m.group(2)
            known = token_groups.get(group)
            if known is None or member in known:
                continue
            if _is_allowed(rel, m.group(0), allowlist):
                continue
            findings.append(
                Finding(
                    path=rel,
                    line=lineno,
                    match=m.group(0),
                    text=line.strip()[:160],
                    kind="undefined_token",
                    detail=f"`{group}` has no member `{member}`. Defined: {', '.join(sorted(known))}",
                )
            )

        # D-3: a shade that fails AA for normal text on both page surfaces
        # cannot be legible anywhere.
        for m in _TEXT_SHADE_RE.finditer(line):
            shade_key = f"{m.group(1)}-{m.group(2)}"
            if shade_key not in illegible or shade_key in CONTRAST_EXEMPT_SHADES:
                continue
            if _is_allowed(rel, m.group(0), allowlist):
                continue
            findings.append(
                Finding(
                    path=rel,
                    line=lineno,
                    match=m.group(0),
                    text=line.strip()[:160],
                    kind="illegible_shade",
                    detail=(
                        f"{shade_key} reaches only {illegible[shade_key]:.2f}:1 against the better "
                        f"of the two page surfaces; WCAG 2.1 AA needs {AA_TEXT_RATIO}:1 for normal text"
                    ),
                )
            )
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


_KIND_LABELS = {
    "generic_palette": "generic colour class",
    "undefined_token": "undefined brand token",
    "illegible_shade": "illegible text shade",
}


def _exemption_notice() -> list[str]:
    """
    The standing contrast exemptions, printed on every run.

    An exemption that is only visible in source is an exemption nobody reviews.
    This repo has the receipts: the AS 1215 citation was swept from every
    customer-facing surface and drifted back into three internal docs within
    months, and finding D-4 is a hand-maintained list that stopped matching.
    """
    if not CONTRAST_EXEMPT_SHADES:
        return []
    lines = ["", "Standing contrast exemptions (shade-level, reviewed on every run):"]
    for shade, reason in sorted(CONTRAST_EXEMPT_SHADES.items()):
        lines.append(f"  {shade} — {reason}")
    return lines


def format_report(findings: list[Finding]) -> str:
    if not findings:
        return "\n".join(
            [
                "Design token lint: ALL CHECKS PASSED "
                "(0 generic colour classes, 0 undefined tokens, 0 illegible text shades)",
                *_exemption_notice(),
            ]
        )

    by_kind: dict[str, int] = {}
    for f in findings:
        by_kind[f.kind] = by_kind.get(f.kind, 0) + 1
    summary = ", ".join(f"{count} {_KIND_LABELS.get(kind, kind)}(es)" for kind, count in sorted(by_kind.items()))

    lines = [f"Design token lint: {len(findings)} finding(s) — {summary}", ""]
    for f in findings:
        lines.append(f"  {f.path}:{f.line}  {f.match}  [{_KIND_LABELS.get(f.kind, f.kind)}]")
        lines.append(f"      {f.detail}" if f.detail else f"      use {_suggestion(f.match)}")
        lines.append(f"      {f.text}")
    lines.append("")
    lines.append(
        "CLAUDE.md mandates the Oat & Obsidian palette and forbids generic Tailwind colours. "
        "Semantic states are covered: sage-* for success/income, clay-* for error/expense. "
        "If an exception is genuinely warranted, add it to scripts/design_token_allowlist.txt "
        "with a reason."
    )
    lines.append(
        "An undefined brand token emits no CSS, so the element inherits colour silently — "
        "resolve it against tailwind.config.js. An illegible shade cannot meet WCAG AA on "
        "either page surface; use the theme-flipping semantic tokens "
        "(text-theme-success-text / text-theme-error-text) or a darker/lighter shade."
    )
    lines.extend(_exemption_notice())
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
