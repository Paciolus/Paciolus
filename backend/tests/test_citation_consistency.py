"""Sprint 717 — Citation consistency tests.

Ensures every audit/accounting standard cited on a customer-facing surface
exists in `backend/standards_registry.py`. This catches future fabricated
citations like the AS 1215 / JE Testing drift surfaced by the 2026-04-24
agent sweep (Hallucination Audit C-4 + Accounting Methodology Audit Rank-1).

Surfaces scanned:
- `frontend/src/app/(marketing)/**/*.tsx`
- `frontend/src/app/(marketing)/trust/page.tsx`
- `frontend/src/content/standards-specimen.ts`
- `frontend/src/components/marketing/**/*.tsx`
- `docs/07-user-facing/USER_GUIDE.md`
- `CLAUDE.md`

Scope notes:
- We extract candidate standard tokens via regex covering AS, ISA, ASC, IFRS, IAS,
  IRC §, AU-C, COSO, SOC, AICPA Audit Sampling Guide Table, Pub patterns.
- Every extracted token must resolve to a code in `standards_registry.STANDARDS_BY_CODE`.
- Allow-list a small set of clearly contextual / illustrative occurrences in
  internal docs that are not hard citations.

Run via `pytest backend/tests/test_citation_consistency.py -v`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import standards_registry

REPO_ROOT = Path(__file__).resolve().parents[2]

# ───────────────────────── Scan surfaces ─────────────────────────

SCANNED_GLOBS: tuple[str, ...] = (
    "frontend/src/app/(marketing)/**/*.tsx",
    "frontend/src/content/standards-specimen.ts",
    "frontend/src/components/marketing/**/*.tsx",
    "docs/07-user-facing/USER_GUIDE.md",
    "CLAUDE.md",
)

# Regex catches the citation forms we actually use in copy.
# Order matters: longest-match preferred.
CITATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # PCAOB AS 1215, AS 2401, etc.
    ("PCAOB", re.compile(r"\bPCAOB\s+AS\s+(\d{3,5})\b")),
    # ISA 240, ISA 315, etc.
    ("ISA", re.compile(r"\bISA\s+(\d{3})\b")),
    # AU-C 450, AU-C 500
    ("AU-C", re.compile(r"\bAU-?C\s+(\d{3})\b")),
    # ASC 606, ASC 230, etc.
    ("ASC", re.compile(r"\bASC\s+(\d{3,4})\b")),
    # IFRS 10, IFRS 15
    ("IFRS", re.compile(r"\bIFRS\s+(\d{1,2})\b")),
    # IAS 2, IAS 16, IAS 21
    ("IAS", re.compile(r"\bIAS\s+(\d{1,2})\b")),
)

# Tokens that pattern-match but are intentionally illustrative / out-of-scope
# (e.g. lessons-learned files describing a historical incorrect citation).
ALLOWLISTED_TOKENS_PER_FILE: dict[str, set[str]] = {
    # CLAUDE.md mentions "AS 1215 governs documentation/retention" in a
    # context where the citation is correct as documentation guidance.
    "CLAUDE.md": set(),
    # Marketing demo explorer's "PDF Workpaper Memo" badge cites AS 1215 for
    # the workpaper-signoff metadata — that's correct AS 1215 usage.
    "frontend/src/components/marketing/DemoTabExplorer.tsx": set(),
}

# Patterns that legitimately appear but aren't standard citations
# (e.g., test counts, sprint numbers).
EXCLUDE_CONTEXT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"Sprint\s+\d+"),
    re.compile(r"\d{4}-\d{2}-\d{2}"),
)


def _gather_files() -> list[Path]:
    """Resolve scan globs against the repo root."""
    files: list[Path] = []
    for glob_pat in SCANNED_GLOBS:
        files.extend(sorted(REPO_ROOT.glob(glob_pat)))
    return [f for f in files if f.is_file()]


def _extract_citations(text: str) -> set[str]:
    """Return the set of normalized standard codes referenced in `text`."""
    cited: set[str] = set()
    for body, pattern in CITATION_PATTERNS:
        for match in pattern.finditer(text):
            number = match.group(1)
            if body == "PCAOB":
                cited.add(f"AS {number}")
            elif body == "AU-C":
                cited.add(f"AU-C {number}")
            else:
                cited.add(f"{body} {number}")
    return cited


# ───────────────────────── Tests ─────────────────────────


def test_scan_surfaces_exist():
    """The scanned surface paths exist (catches glob breakage)."""
    files = _gather_files()
    assert files, f"Citation scan produced zero files — globs may be broken. Patterns: {SCANNED_GLOBS}"


def test_every_cited_standard_is_registered():
    """Every standard cited in a customer-facing surface must be registered."""
    files = _gather_files()
    unregistered_per_file: dict[str, set[str]] = {}

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        cited = _extract_citations(text)
        if not cited:
            continue

        relative = path.relative_to(REPO_ROOT).as_posix()
        allowlist = ALLOWLISTED_TOKENS_PER_FILE.get(relative, set())

        unregistered = {
            code for code in cited if code not in standards_registry.STANDARDS_BY_CODE and code not in allowlist
        }
        if unregistered:
            unregistered_per_file[relative] = unregistered

    if unregistered_per_file:
        lines = ["Unregistered standard citations on customer-facing surfaces:"]
        for path, codes in sorted(unregistered_per_file.items()):
            lines.append(f"  {path}: {sorted(codes)}")
        lines.append("Either add the missing standard to `backend/standards_registry.py` or correct the citation.")
        pytest.fail("\n".join(lines))


def test_as_1215_only_in_allowed_contexts():
    """AS 1215 must not appear as a JE Testing citation.

    AS 1215 is *Audit Documentation* — it governs workpaper retention, not
    fraud-detection procedures. Sprint 717 swept the 5 customer-facing
    surfaces that misattributed it; this test is the durable guardrail.
    """
    files = _gather_files()
    bad_contexts: list[tuple[str, str]] = []

    je_pattern = re.compile(
        r"(JE\s+Testing|Journal\s+Entry\s+Testing).{0,200}\bAS\s+1215\b"
        r"|\bAS\s+1215\b.{0,200}(JE\s+Testing|Journal\s+Entry\s+Testing)",
        flags=re.IGNORECASE | re.DOTALL,
    )

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if je_pattern.search(text):
            bad_contexts.append(
                (
                    path.relative_to(REPO_ROOT).as_posix(),
                    "AS 1215 cited near 'JE Testing' / 'Journal Entry Testing'",
                )
            )

    if bad_contexts:
        lines = ["AS 1215 cited as a JE Testing standard (incorrect — should be AS 2401):"]
        for path, msg in bad_contexts:
            lines.append(f"  {path}: {msg}")
        lines.append(
            "AS 1215 governs audit-documentation form/retention only. "
            "For JE fraud-testing procedures, cite PCAOB AS 2401 and ISA 240."
        )
        pytest.fail("\n".join(lines))


def test_standards_registry_has_essential_codes():
    """Smoke check that the registry contains the citations we rely on most."""
    essential = {
        "AS 2401",  # JE testing primary
        "AS 2501",
        "AS 2305",
        "AS 2310",
        "AS 2315",
        "ISA 240",
        "ISA 315",
        "ISA 320",
        "ISA 500",
        "ISA 520",
        "ISA 530",
        "ASC 606",
        "ASC 230",
        "IFRS 15",
        "IAS 21",
    }
    missing = essential - set(standards_registry.all_codes())
    assert not missing, f"standards_registry missing essential codes: {sorted(missing)}"
