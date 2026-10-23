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


# ---------------------------------------------------------------------------
# Sprint 809 — D-2: brand tokens that do not exist
# ---------------------------------------------------------------------------
#
# `text-content-muted` had 36 live usages across checkout, billing, team,
# shares, branding, admin-dashboard and internal/admin. `content-muted` is not a
# token — the config defines primary/secondary/tertiary/disabled — so the class
# emitted zero CSS and every one of those elements silently inherited colour.
# This gate passed all 36, because it only ever asked whether a colour came from
# a *generic Tailwind* palette, never whether a brand token existed.


def test_the_config_token_groups_are_parsed():
    groups = linter._parse_token_groups()

    assert "content" in groups
    assert {"primary", "secondary", "tertiary", "disabled"} <= groups["content"]
    assert "muted" not in groups["content"]


def test_an_undefined_content_token_is_flagged(tmp_path: Path):
    path = _write(tmp_path, "Card.tsx", '<p className="text-content-muted">x</p>')
    findings = linter.scan_file(path, [])

    assert len(findings) == 1
    assert findings[0].kind == "undefined_token"
    assert findings[0].match == "text-content-muted"
    assert "no member `muted`" in findings[0].detail


def test_a_defined_content_token_is_not_flagged(tmp_path: Path):
    path = _write(tmp_path, "Card.tsx", '<p className="text-content-tertiary">x</p>')
    assert linter.scan_file(path, []) == []


def test_undefined_tokens_in_other_groups_are_flagged(tmp_path: Path):
    path = _write(
        tmp_path,
        "Card.tsx",
        '<div className="bg-surface-nonexistent text-theme-success-nope">x</div>',
    )
    findings = linter.scan_file(path, [])

    assert {f.match for f in findings} == {"bg-surface-nonexistent", "text-theme-success-nope"}
    assert all(f.kind == "undefined_token" for f in findings)


def test_a_variant_prefixed_undefined_token_is_flagged(tmp_path: Path):
    path = _write(tmp_path, "Card.tsx", '<p className="hover:text-content-muted">x</p>')
    findings = linter.scan_file(path, [])

    assert len(findings) == 1
    assert findings[0].kind == "undefined_token"


def test_an_unknown_group_is_not_guessed_at(tmp_path: Path):
    """
    Only groups the config actually defines are resolved. A class naming some
    other group is left to the generic-palette rule, rather than this check
    inventing an opinion about it.
    """
    path = _write(tmp_path, "Card.tsx", '<p className="text-whatever-muted">x</p>')
    assert linter.scan_file(path, []) == []


def test_the_frontend_has_no_undefined_brand_tokens():
    """The repo-level assertion. 36 usages existed before Sprint 809."""
    findings = [f for f in linter.scan() if f.kind == "undefined_token"]
    assert findings == [], f"{len(findings)} undefined brand tokens: {[f.match for f in findings]}"


# ---------------------------------------------------------------------------
# Sprint 809 — D-3: shades that cannot be legible on either surface
# ---------------------------------------------------------------------------


def test_contrast_ratio_matches_published_wcag_values():
    """Anchors: pure black on white is 21:1, and a colour against itself is 1:1."""
    assert linter.contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0, rel=1e-3)
    assert linter.contrast_ratio("#121212", "#121212") == pytest.approx(1.0, rel=1e-6)


def test_the_measured_sage_and_clay_ratios_reproduce_the_review():
    """
    The review measured `sage-500` at 3.85:1 on the dark page and 4.42:1 on the
    light page, and `clay-500` at 3.69:1 dark. Both below the 4.5:1 AA threshold
    for normal text where they were used unqualified.
    """
    palette = linter._parse_palette()

    assert linter.contrast_ratio(palette["sage"]["500"], "#121212") == pytest.approx(3.85, abs=0.02)
    assert linter.contrast_ratio(palette["sage"]["500"], "#F5F4F2") == pytest.approx(4.42, abs=0.02)
    assert linter.contrast_ratio(palette["clay"]["500"], "#121212") == pytest.approx(3.69, abs=0.02)
    # And the shades the 61 usages were migrated to do pass.
    assert linter.contrast_ratio(palette["sage"]["700"], "#F5F4F2") == pytest.approx(8.18, abs=0.02)
    assert linter.contrast_ratio(palette["clay"]["700"], "#F5F4F2") == pytest.approx(7.65, abs=0.02)


def test_sage_500_is_derived_as_illegible():
    illegible = linter.illegible_text_shades()

    assert "sage-500" in illegible
    assert illegible["sage-500"] < linter.AA_TEXT_RATIO


def test_clay_500_is_not_claimed_to_be_illegible_everywhere():
    """
    Honesty about the measurement: `clay-500` reaches 4.62:1 on the light page,
    which passes AA. It fails on dark (3.69:1), but this gate has no route→theme
    map, so it cannot say whether a given usage renders there. Claiming otherwise
    would be the false-positive failure mode that gets a gate switched off.
    """
    assert "clay-500" not in linter.illegible_text_shades()


def test_an_illegible_text_shade_is_flagged(tmp_path: Path):
    path = _write(tmp_path, "Card.tsx", '<p className="text-sage-500">x</p>')
    findings = linter.scan_file(path, [])

    assert len(findings) == 1
    assert findings[0].kind == "illegible_shade"
    assert "4.42:1" in findings[0].detail


def test_a_legible_shade_on_its_own_theme_is_not_flagged(tmp_path: Path):
    """
    `text-sage-700` is 8.18:1 on the light surface, where it is in fact used.
    Flagging it would require knowing the route's theme — finding D-4.
    """
    path = _write(tmp_path, "Card.tsx", '<p className="text-sage-700">x</p>')
    assert linter.scan_file(path, []) == []


def test_a_non_text_utility_is_not_contrast_checked(tmp_path: Path):
    """
    WCAG 2.1 scopes 4.5:1 to text (SC 1.4.3); non-text graphics need 3:1
    (SC 1.4.11), which sage-500 meets. Only `text-` utilities are checked.
    """
    path = _write(tmp_path, "Card.tsx", '<div className="bg-sage-500 border-sage-500" />')
    assert linter.scan_file(path, []) == []


def test_exempt_shades_are_not_flagged(tmp_path: Path):
    path = _write(tmp_path, "Card.tsx", '<p className="text-obsidian-400">disabled</p>')
    assert linter.scan_file(path, []) == []


def test_every_exemption_carries_a_reason():
    """An exemption without an argument is just permission."""
    assert linter.CONTRAST_EXEMPT_SHADES
    for shade, reason in linter.CONTRAST_EXEMPT_SHADES.items():
        assert reason.strip(), shade
        assert len(reason) > 30, f"{shade}: reason is too thin to review"


def test_exemptions_are_printed_on_every_run():
    """
    Including the clean run. An exemption visible only in source is an exemption
    nobody reviews.
    """
    clean = linter.format_report([])

    assert "Standing contrast exemptions" in clean
    for shade in linter.CONTRAST_EXEMPT_SHADES:
        assert shade in clean


def test_oatmeal_700_is_no_longer_exempt():
    """Sprint 828 migrated its 48 usages by surface once the route->theme map
    existed. The exemption was always described as temporary; it is gone, so a
    new oatmeal-700 text usage fails the repo-level check below."""
    assert "oatmeal-700" not in linter.CONTRAST_EXEMPT_SHADES


def test_the_frontend_has_no_illegible_text_shades():
    """The repo-level assertion. 61 unqualified usages existed before Sprint 809."""
    findings = [f for f in linter.scan() if f.kind == "illegible_shade"]
    assert findings == [], f"{len(findings)} illegible text shades: {[f.match for f in findings]}"


def test_the_report_distinguishes_the_three_kinds(tmp_path: Path):
    path = _write(
        tmp_path,
        "Card.tsx",
        '<p className="text-content-muted text-sage-500 bg-slate-800">x</p>',
    )
    report = linter.format_report(linter.scan_file(path, []))

    assert "generic colour class" in report
    assert "undefined brand token" in report
    assert "illegible text shade" in report
