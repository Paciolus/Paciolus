"""
Sprint 810 (finding T-3) — the gate that stops presence-as-capability returning.

The DEC review's F-005 corrected four test classes whose only assertion was
``assert callable(some_function)``. Four months later the full-spectrum review
found **27 occurrences still standing across 10 files**, including
``test_billing_routes.py``, ``test_pricing_integration.py``,
``test_rate_limit_tiered.py`` and ``test_retention_cleanup.py`` — billing and
rate limiting.

Fixing the 27 is the easy half. The pattern came back because nothing was
watching, which is the same shape as findings C-1 (a subprocessor list nothing
checked) and D-4 (a route list nothing checked) in the very same review. So the
fix is this gate, not just the edits.

Every remaining ``assert callable(...)`` in the suite must appear in
``DOCUMENTED_EXEMPTIONS`` below with a reason. A new one fails this test, and the
failure message says what to do instead. The exemptions are real: ``callable`` is
the correct predicate when the thing being tested *is* "does this object expose a
callable attribute" — Protocol conformance, a slowapi dynamic-limit object, an
allowlist that must name real functions.

Use ``tests/helpers/contract_assertions.assert_signature`` for the rest.
"""

from __future__ import annotations

import re
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent

# file -> {line_content_fragment: reason}
#
# Keyed by a fragment of the asserting line rather than a line number, so that
# editing a file above an exemption does not silently re-arm the gate — a
# line-number allowlist is the same brittle shape the review keeps finding.
DOCUMENTED_EXEMPTIONS: dict[str, dict[str, str]] = {
    "test_tool_contracts.py": {
        'callable(getattr(result_cls, "to_dict", None))': (
            "Protocol conformance: the assertion *is* 'this class exposes a to_dict "
            "method', which is what structural subtyping inspects. The surrounding "
            "test also pins the dataclass field names."
        ),
        'callable(getattr(cls, "to_dict", None))': (
            "Protocol conformance, as above, for the composite-score and test-result "
            "classes. Checked across every tool by parametrisation."
        ),
    },
    "test_convergence.py": {
        "callable(func)": (
            "Registry shape check, and the very next line exercises behaviour: "
            "`assert isinstance(func({}), list)`. The callable check is a preamble to "
            "a real assertion, not a substitute for one."
        ),
    },
    "test_rate_limit_tiered.py": {
        "callable(RATE_LIMIT_AUTH)": (
            "slowapi resolves a dynamic limit by calling the object, so being callable "
            "is a genuine interface requirement. Sprint 810 added the call itself and "
            "asserts the resolved limit parses as '<count>/<period>'."
        ),
    },
    "test_rate_limit_slowapi_health.py": {
        "callable(limiter.limit)": (
            "A dependency-surface check against slowapi itself — the library is "
            "unmaintained (last release Oct 2022), so asserting the API we rely on "
            "still exists is the point of the test."
        ),
    },
    "test_legacy_passcode_cleanup.py": {
        "callable(mod.main)": (
            "A no-argument CLI entrypoint: there is no signature to pin, and its "
            "behaviour is covered by the tests above it in the same file."
        ),
    },
}

# ---------------------------------------------------------------------------
# Pre-existing baseline, owned by a different in-flight change.
#
# NOT an exemption. These are genuine presence-as-capability assertions and they
# are wrong for exactly the reasons above — they are simply not this sprint's to
# fix. They are the DEC review's finding **F-005**, and the DEC remediation
# branch (Sprints 795-802) converts them. Fixing them here as well would
# duplicate that work and guarantee a conflict in the one file both touch.
#
# So they are recorded, counted, and allowed not to grow — the same treatment
# Sprint 809 gave the 48 `text-oatmeal-700` usages it could not responsibly
# migrate. The count is asserted *exactly*, not as a ceiling, so this entry
# cannot quietly absorb a new violation in the same file.
#
# When the DEC remediation lands, this count goes to 0 and
# `test_the_pending_baseline_is_still_needed` fails, which is the signal to
# delete this block. It is designed to expire.
PENDING_BASELINE: dict[str, int] = {
    "test_post_audit_2026_04_20_batch2.py": 8,
}


ASSERT_CALLABLE_RE = re.compile(r"^\s*assert callable\(")

GUIDANCE = (
    "\n\nUse tests/helpers/contract_assertions.assert_signature(fn, [...]) instead: it "
    "asserts the function is callable AND takes exactly the named parameters, so a "
    "rename, a reorder or a dropped parameter fails. `assert callable(f)` is a "
    "tautology — the import above it already proved the symbol exists, and every "
    "function satisfies it, including one whose body is `raise NotImplementedError`.\n\n"
    "If `callable` genuinely is the property under test (Protocol conformance, a "
    "dynamic-limit object, an allowlist that must name real functions), add it to "
    "DOCUMENTED_EXEMPTIONS in tests/test_presence_as_capability_gate.py with a reason."
)


def _find_assertions() -> list[tuple[str, int, str]]:
    """Every `assert callable(...)` in the suite, as (filename, line_no, text)."""
    found: list[tuple[str, int, str]] = []
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if ASSERT_CALLABLE_RE.match(line):
                found.append((path.name, lineno, line.strip()))
    return found


def _is_exempt(filename: str, text: str) -> bool:
    for fragment in DOCUMENTED_EXEMPTIONS.get(filename, {}):
        if fragment in text:
            return True
    return False


def test_no_undocumented_presence_as_capability_assertions():
    """The gate. 27 of these existed before Sprint 810."""
    offenders = [
        f"{filename}:{lineno}  {text}"
        for filename, lineno, text in _find_assertions()
        if not _is_exempt(filename, text) and filename not in PENDING_BASELINE
    ]
    assert offenders == [], (
        f"{len(offenders)} undocumented `assert callable(...)` assertion(s):\n  " + "\n  ".join(offenders) + GUIDANCE
    )


def test_every_exemption_still_corresponds_to_a_real_assertion():
    """
    The other direction, and the one that matters more over time: an exemption
    whose assertion has been deleted or rewritten is dead permission sitting in
    the allowlist, waiting to excuse something it was never argued for. This is
    the failure mode of every stale list this review found.
    """
    present = {(filename, text) for filename, _lineno, text in _find_assertions()}
    stale: list[str] = []
    for filename, fragments in DOCUMENTED_EXEMPTIONS.items():
        for fragment in fragments:
            if not any(f == filename and fragment in t for f, t in present):
                stale.append(f"{filename}: {fragment}")
    assert stale == [], (
        "exemptions with no matching assertion — remove them rather than leaving "
        "unearned permission in the allowlist:\n  " + "\n  ".join(stale)
    )


def test_every_exemption_carries_a_reason():
    for filename, fragments in DOCUMENTED_EXEMPTIONS.items():
        for fragment, reason in fragments.items():
            assert reason.strip(), f"{filename}: {fragment} has no reason"
            assert len(reason) > 60, (
                f"{filename}: {fragment} — the reason is too thin to review. "
                "State what property is actually under test."
            )


def test_the_scan_finds_something(tmp_path: Path):
    """
    Guards the gate itself. A regex that silently matches nothing would make
    every assertion above pass vacuously — which is how a gate stops gating,
    and the exact shape of the defect the PR #185 review found.
    """
    assert _find_assertions(), "the scan found no `assert callable` at all — check the regex"

    assert ASSERT_CALLABLE_RE.match("    assert callable(foo)")
    assert ASSERT_CALLABLE_RE.match("assert callable(foo.bar)")
    # Not a bare presence assertion: a comment, or callable used in an expression.
    assert not ASSERT_CALLABLE_RE.match("# assert callable(foo)")
    assert not ASSERT_CALLABLE_RE.match("    assert x and callable(foo)")



def test_the_pending_baseline_does_not_grow():
    """
    The baselined files are allowed their recorded count and not one more.

    Asserted exactly rather than as a ceiling: a ceiling would let a new
    violation slip in behind a number nobody re-reads, which is the failure mode
    this whole gate exists to prevent.
    """
    counts: dict[str, int] = {}
    for filename, _lineno, _text in _find_assertions():
        if filename in PENDING_BASELINE:
            counts[filename] = counts.get(filename, 0) + 1

    for filename, expected in PENDING_BASELINE.items():
        actual = counts.get(filename, 0)
        assert actual == expected, (
            f"{filename}: baseline records {expected} presence-as-capability "
            f"assertion(s), found {actual}.\n"
            f"If this went UP, the new one is a regression — fix it, do not raise the number.\n"
            f"If it went DOWN, the DEC remediation (F-005) has landed: delete the entry "
            f"from PENDING_BASELINE in this file."
        )


def test_the_pending_baseline_is_still_needed():
    """
    A baseline whose violations are gone is dead weight that would silence a
    future regression in the same file. It must be deleted, not left to rot —
    the same argument as `test_every_exemption_still_corresponds_to_a_real_assertion`.
    """
    present = {filename for filename, _lineno, _text in _find_assertions()}
    stale = [f for f in PENDING_BASELINE if f not in present]
    assert stale == [], (
        "PENDING_BASELINE names files with no remaining presence-as-capability "
        f"assertions: {stale}. The other change has landed — delete these entries."
    )
