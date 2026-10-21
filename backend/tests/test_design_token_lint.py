"""Sprint 782a — the Oat & Obsidian palette as a CI gate.

The design system reached **zero** generic Tailwind colour classes across 777 frontend
files, down from about 150, and nothing protected that zero. `CLAUDE.md` attaches an audit
penalty to deviation, which is discipline, not enforcement — and the AS 1215 citation
showed what discipline alone is worth: swept from every customer-facing surface in Sprint
717, back in three internal docs within months.

Running the lint from a backend test rather than a new CI job is deliberate: the Backend
Tests gate is already required on `main` for Python 3.11, 3.12 and PostgreSQL 15, so the
check is enforced on every PR without touching `ci.yml`. The lint itself is pure stdlib
and reads files, so it needs nothing from the backend runtime.

Half the tests below pin the **false-positive set**. Two guards written earlier today fired
mostly false on their first draft by matching substrings rather than syntax, and a noisy
gate gets disabled rather than fixed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "lint_design_tokens.py"
ALLOWLIST_PATH = REPO_ROOT / "scripts" / "design_token_allowlist.txt"


def _load_linter():
    """Import the lint script by path (scripts/ is not a package)."""
    spec = importlib.util.spec_from_file_location("lint_design_tokens", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


linter = _load_linter()


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# The gate itself
# ---------------------------------------------------------------------------


def test_frontend_has_no_generic_colour_classes():
    """The property this sprint exists to protect."""
    findings = linter.scan()
    assert findings == [], linter.format_report(findings)


def test_script_exists_and_is_executable_as_a_module():
    assert SCRIPT_PATH.is_file()
    assert linter.main([]) == 0


def test_allowlist_file_exists():
    """A missing allowlist must not silently become 'allow everything'."""
    assert ALLOWLIST_PATH.is_file()


def test_allowlist_ships_empty():
    """Every exception should have to argue for itself in review.

    If this fails, someone added an entry — read it and decide whether the palette
    genuinely lacked what they needed. sage-* covers success/income and clay-* covers
    error/expense, which is where most of the temptation comes from.
    """
    assert linter.load_allowlist() == []


# ---------------------------------------------------------------------------
# True positives
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "snippet",
    [
        'className="text-blue-500"',
        'className="bg-slate-800 p-4"',
        'className="border border-gray-200"',
        'className="hover:bg-red-100"',
        'className="dark:text-zinc-400"',
        'className="md:hover:ring-emerald-500"',
        'className="ring-sky-500/40"',
        'className="bg-gradient-to-r from-purple-500 to-pink-500"',
        'className="divide-y divide-neutral-200"',
        'className="shadow-lg shadow-indigo-500/50"',
        'className="placeholder-stone-400"',
        'className="fill-rose-600"',
        # Directional and axis border/divide utilities — PR #176 review: the first
        # pattern set listed only the base names, so every one of these slipped through.
        'className="border-l-red-500"',
        'className="hover:border-t-blue-200"',
        'className="border-x-slate-700"',
        'className="divide-x-gray-200"',
        'className="md:divide-y-zinc-300"',
        'className="border-b-2 border-b-emerald-500"',
        "const cls = `text-${x} bg-amber-200`",
        ".foo { @apply bg-teal-600; }",
    ],
)
def test_generic_colour_classes_are_flagged(tmp_path: Path, snippet: str):
    path = _write(tmp_path, "src/Comp.tsx", snippet + "\n")
    findings = linter.scan_file(path, [])
    assert findings, f"not flagged: {snippet}"


def test_finding_carries_path_line_and_match(tmp_path: Path):
    path = _write(tmp_path, "src/Comp.tsx", 'a\nb\n<div className="bg-red-500" />\n')
    findings = linter.scan_file(path, [])
    assert len(findings) == 1
    assert findings[0].line == 3
    assert findings[0].match == "bg-red-500"


def test_multiple_violations_on_one_line_all_reported(tmp_path: Path):
    path = _write(tmp_path, "src/Comp.tsx", 'className="bg-blue-500 text-gray-100"\n')
    assert len(linter.scan_file(path, [])) == 2


# ---------------------------------------------------------------------------
# False positives — the half that keeps the gate alive
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "snippet",
    [
        # Oat & Obsidian tokens, the whole point of the mandate
        'className="bg-obsidian-800 text-oatmeal-200"',
        'className="text-clay-500 border-sage-400"',
        'className="hover:bg-sage-500/10"',
        # Prose and data that merely contain a palette word
        "// red-500 used to be here before the migration",
        "/** Do not use blue-500; prefer sage-500. */",
        'const vendor = "Blue-500 Industries Ltd"',
        'expect(label).toBe("sky-500")',
        # Non-colour utilities that share a numeric scale
        'className="z-50 w-500 duration-500 delay-300"',
        'className="font-medium text-sm leading-500"',
        # Colour utilities with non-generic palettes
        'className="bg-brand-500 text-accent-700"',
        # A scale value Tailwind does not define for colours
        'className="bg-blue-250"',
        # Hyphen-joined words that are not utility-palette-scale
        'className="group-data-[state=open]:bg-sage-500"',
        # Directional utilities on theme tokens stay clean
        'className="border-l-clay-500 divide-y-oatmeal-300"',
    ],
)
def test_non_violations_are_not_flagged(tmp_path: Path, snippet: str):
    path = _write(tmp_path, "src/Comp.tsx", snippet + "\n")
    findings = linter.scan_file(path, [])
    assert findings == [], f"false positive on: {snippet} -> {[f.match for f in findings]}"


# ---------------------------------------------------------------------------
# Allowlist behaviour
# ---------------------------------------------------------------------------


def test_allowlist_narrow_entry_exempts_only_that_class(tmp_path: Path):
    """An entry naming one class must not exempt the rest of the file."""
    path = _write(tmp_path, "src/Legacy.tsx", 'className="bg-red-500 text-blue-500"\n')
    allowlist = [("src/Legacy.tsx", "bg-red-500")]

    remaining = linter.scan_file(path, allowlist)
    assert [f.match for f in remaining] == ["text-blue-500"]


def test_allowlist_bare_path_entry_exempts_the_whole_file():
    allowlist = [("src/Legacy.tsx", None)]
    assert linter._is_allowed("src/Legacy.tsx", "bg-red-500", allowlist) is True
    assert linter._is_allowed("src/Legacy.tsx", "text-blue-500", allowlist) is True
    assert linter._is_allowed("src/Other.tsx", "bg-red-500", allowlist) is False


def test_allowlist_parses_comments_and_blank_lines(tmp_path: Path):
    path = _write(
        tmp_path,
        "allow.txt",
        "# a comment\n\n  src/Legacy.tsx:bg-red-500  # legacy brand lockup\nsrc/Other.tsx\n",
    )
    assert linter.load_allowlist(path) == [
        ("src/Legacy.tsx", "bg-red-500"),
        ("src/Other.tsx", None),
    ]


def test_missing_allowlist_is_treated_as_empty(tmp_path: Path):
    assert linter.load_allowlist(tmp_path / "nope.txt") == []


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def test_report_suggests_the_right_token(tmp_path: Path):
    """An error message that names the replacement is the difference between a gate
    people fix and a gate people suppress."""
    assert "clay-*" in linter._suggestion("bg-red-500")
    assert "sage-*" in linter._suggestion("text-emerald-600")
    assert "obsidian-*" in linter._suggestion("bg-slate-900")
    assert "oatmeal-*" in linter._suggestion("bg-stone-100")


def test_report_mentions_the_allowlist_route(tmp_path: Path):
    findings = [linter.Finding(path="src/A.tsx", line=1, match="bg-red-500", text="x")]
    report = linter.format_report(findings)
    assert "design_token_allowlist.txt" in report
    assert "clay-*" in report


def test_clean_report_states_the_zero():
    assert "0 generic colour classes" in linter.format_report([])
