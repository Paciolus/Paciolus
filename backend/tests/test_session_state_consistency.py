"""`SESSION_STATE.md` must state each current fact once — Sprint 786b.

`AGENTS.md` names this file as the first thing a new session reads, so a
contradiction in it is read as context before anything else is. It has now
acquired one twice in consecutive PRs, both times the same way: a string
replacement matched the **prefix** of a sentence, so the superseded text
survived attached to its replacement.

| PR | What the line ended up saying |
|----|-------------------------------|
| #194 | 9,094 tests and +105 across four suites, **then** 11m23s and +42 across two |
| #196 | DB latency 27.72 ms, **then** "DB ~9 ms" as though also current |

Both were caught in review rather than by me, which is the recurrence rate
that justifies a guard over a resolution to be careful.

WHY THERE ARE TWO RULES
Measured against the two real defect lines before being written, and neither
rule catches both:

    rule                 #194    #196    false positives on the fixed file
    duplicate figures    miss    catch   0
    duplicate fragment   catch   miss    0

#194 repeated a whole clause verbatim but its *numbers* were legitimately
comparative ("up from 8,989"), so the figures rule reads it as fine. #196
repeated no wording but left two live latency readings. **Two instances of
one defect class with disjoint mechanical signatures** — so the union is the
guard, and a single rule would have given false confidence against the next
one.

Both rules are clean on the corrected file, which is why this exists at all.
The comparable guard considered in the same sprint — "every version in prose
must match its pin" — was measured at 54 disagreements and every inspected
one a false positive, so it was not built. The measurement decides.

TWO CORRECTIONS, BOTH FROM TRYING TO BREAK IT
The figures rule was first written per line, and its regression proof **failed
to fail**: reintroducing the #196 defect produced a green run, because the
corrected summary had since moved the two latency figures onto separate lines.
A per-line rule cannot see a cross-line contradiction, and the defect was
never a property of a line. It is now scoped to the whole file, with the
historical marker required to sit immediately before its figure so that one
"up from" cannot launder every stale number in the paragraph.

Rescoping then made the rule fire on `11m25s` vs `11m26s` — and that was the
rule being wrong, not the file. The suite was deliberately measured twice, so
two runtimes are two honest observations. `runtime` is therefore no longer
checked. The self-check below started failing at the same moment, because with
runtimes included the two rules were no longer disjoint; it told me to correct
the claim rather than let it stand, which is exactly what it is for.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SESSION_STATE = REPO_ROOT / "SESSION_STATE.md"

# A figure presented as superseded is fine — "up from 8,989", "down from 12 ms".
# This is the same principle as Sprint 786b's rule for maintenance claims: a
# historical value must be marked as historical.
# A figure immediately preceded by one of these is explicitly historical —
# "up from 9.35 ms" is a comparison, not a competing claim. Matched against
# the text just BEFORE each figure rather than anywhere on the line, because
# a marker elsewhere in the sentence must not launder an unrelated stale
# value. Anchored at the end so only an adjacent marker counts.
_SUPERSEDED = re.compile(
    r"(up from|down from|was|previously|before the|earlier|prior|rose from|fell from|from)\s*$",
    re.IGNORECASE,
)
_MARKER_WINDOW = 40

# Metrics that describe the CURRENT state and therefore have exactly one
# true value at a time.
#
# `runtime` was in this list and has been removed, because the rule was an
# overreach and the guard said so on its first real run: the file
# legitimately reports two suite runtimes — one for `-p no:randomly`, one
# for the nightly's own invocation — because the suite was deliberately
# measured twice. A runtime is a property of a run, not a fact about the
# project. Latency and test count are facts about the project, and two
# live values of either is a contradiction.
_PATTERNS = {
    "latency": re.compile(r"(\d+(?:\.\d+)?)\s*ms\b"),
    "test count": re.compile(r"\b\d{1,2},\d{3}\b"),
}

_FRAGMENT_WORDS = 6
_WORD = re.compile(r"[A-Za-z0-9,./:~+%-]+")


def _lines() -> list[tuple[int, str]]:
    text = SESSION_STATE.read_text(encoding="utf-8")
    return [(n, line) for n, line in enumerate(text.splitlines(), 1) if line.strip()]


def test_the_session_state_file_is_where_we_think_it_is():
    """A scan of a missing file proves nothing (Sprint 792)."""
    assert SESSION_STATE.is_file(), f"missing {SESSION_STATE}"
    lines = _lines()
    assert len(lines) > 20, f"only {len(lines)} non-blank lines — this check covers nothing"
    assert any("Backend tests:" in line for _n, line in lines), (
        "no `Backend tests:` line found — either the file changed shape or this check lost its target"
    )


def _unmarked_values(text: str, pattern: re.Pattern[str]) -> set[str]:
    """Distinct matches NOT immediately preceded by a superseded-value marker."""
    found: set[str] = set()
    for match in pattern.finditer(text):
        preceding = text[max(0, match.start() - _MARKER_WINDOW) : match.start()]
        if _SUPERSEDED.search(preceding):
            continue
        found.add(match.group(1) if match.groups() else match.group(0))
    return found


def test_the_file_states_one_live_value_per_metric():
    """Caught PR #196: 27.72 ms and ~9 ms presented as both current.

    **Scoped to the whole file, not to a line.** The first draft of this check
    was line-scoped and its regression proof *failed to fail*: restructuring
    the production summary had moved the two latency figures onto separate
    lines, so a per-line rule could not see the contradiction at all. Both
    historical defects happened to be single-line, which is incidental — the
    defect is "two live values for one metric in the current-state summary",
    and that was never a property of a line.

    A second value is fine when marked historical ("up from 9.35 ms"), and the
    marker must sit immediately before the figure so that one comparison
    elsewhere in a paragraph cannot launder an unrelated stale number.
    """
    text = SESSION_STATE.read_text(encoding="utf-8")
    offenders = []
    for label, pattern in _PATTERNS.items():
        values = _unmarked_values(text, pattern)
        if len(values) > 1:
            offenders.append(f"{len(values)} live {label} values: {sorted(values)}")

    assert not offenders, (
        "SESSION_STATE.md states more than one live value for the same metric:\n  "
        + "\n  ".join(offenders)
        + "\n\nIf one supersedes the other, say so immediately before it ('up from X'); otherwise "
        "delete the old one. This file is the first thing a new session reads, so a contradiction "
        "here is absorbed as context before anything else is."
    )


def test_no_line_repeats_a_clause_verbatim():
    """Caught PR #194: a prefix-matching replacement left the old tail attached.

    Six consecutive words appearing twice in one line is not a style a human
    writes on purpose; it is the signature of text concatenated with the
    version it was meant to replace.
    """
    offenders = []
    for lineno, line in _lines():
        words = _WORD.findall(line)
        if len(words) < _FRAGMENT_WORDS * 2:
            continue
        grams = [" ".join(words[i : i + _FRAGMENT_WORDS]) for i in range(len(words) - _FRAGMENT_WORDS + 1)]
        repeated = sorted({g for g in grams if grams.count(g) > 1})
        if repeated:
            offenders.append(f"SESSION_STATE.md:{lineno} repeats {repeated[0]!r}")

    assert not offenders, (
        "lines containing a repeated clause — usually a replacement that matched a prefix and left "
        "the superseded text attached:\n  " + "\n  ".join(offenders)
    )


def test_both_rules_catch_their_respective_historical_defect():
    """The guard against this guard being reassuring rather than useful.

    Each rule is carried by one real defect and blind to the other. If a
    future simplification collapses them into one, this fails and says why.
    """
    defect_194 = (
        "**Backend tests:** **9,094 passed / 0 failed** (11m29s, clean tree, measured after the "
        "last merge). Up from 8,989 at session start; +105 across the four new guard suites. "
        "(11m23s, clean tree, run after the last merge with nothing else touching the tree). "
        "Up from 8,989 at session start; +42 from the two new guards."
    )
    defect_196 = (
        "**Production:** healthy throughout, including after the deploy. DB latency moved 9.35 to "
        "27.72 ms, consistent with a cold pool. /health/ready reports status healthy, DB ~9 ms, "
        "rate_limit_storage redis not degraded; paciolus.com returns 200."
    )

    def flags_figures(line: str) -> bool:
        return any(len(_unmarked_values(line, p)) > 1 for p in _PATTERNS.values())

    def flags_fragment(line: str) -> bool:
        words = _WORD.findall(line)
        grams = [" ".join(words[i : i + _FRAGMENT_WORDS]) for i in range(len(words) - _FRAGMENT_WORDS + 1)]
        return any(grams.count(g) > 1 for g in grams)

    assert flags_fragment(defect_194), "the duplicate-clause rule no longer catches the PR #194 defect"
    assert not flags_figures(defect_194), (
        "the figures rule now also catches #194 — pleasant, but the docstring's claim that the two "
        "rules are disjoint is then wrong and should be corrected rather than left misleading"
    )
    assert flags_figures(defect_196), "the duplicate-figure rule no longer catches the PR #196 defect"
    assert not flags_fragment(defect_196), (
        "the fragment rule now also catches #196 — update the docstring rather than leaving a claim "
        "that measurement no longer supports"
    )
