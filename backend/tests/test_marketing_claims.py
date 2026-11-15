"""Sprint 861: claims we cannot prove stay off the website and out of the app.

CEO decision 2026-11-14 (website review, `reports/website-review-2026-11-14.md`): a claim we
cannot prove from the code or a published document is removed, not reworded.
This guard fails the build if any of the removed claims come back.

Two scopes:

1. Every customer-facing surface (website and app): banned phrases — the
   generic-AI wording, absolute data-handling claims, unproven test-result
   language, certification-style wording and speed claims.
2. Marketing pages only: no standard codes (ISA 240, PCAOB AS 2401, ASC 606,
   SOC 1 …). Citations live on `/sources`, where each one has its context. The
   one allowed exception is the Trust page sentence that says which
   certifications we do *not* hold.

The Privacy Policy and Terms are excluded until counsel signs off the Sprint
863 corrections; `test_storage_claims.py` still scans them for the older
retired absolutes.
"""

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

CUSTOMER_FACING_PREFIXES = (
    "frontend/src/app/",
    "frontend/src/components/",
    "frontend/src/content/",
    "frontend/src/domain/",
)
MARKETING_PREFIXES = (
    "frontend/src/app/(marketing)/",
    "frontend/src/components/marketing/",
    "frontend/src/components/trust/",
    "frontend/src/content/trust.ts",
    "frontend/src/content/storage-statement.ts",
)
# Sprint 863: legal pages are corrected through counsel, not here.
LEGAL_PAGES = (
    "frontend/src/app/(marketing)/privacy/",
    "frontend/src/app/(marketing)/terms/",
)
# /sources is where citations belong.
CITATION_PAGES = ("frontend/src/app/(marketing)/sources/",)

BANNED_EVERYWHERE = (
    # Absolute data-handling claims (facts: content/storage-statement.ts).
    "zero data",
    "zero raw data",
    "zero-storage",
    "zero storage",
    "data destroyed",
    "what we never store",
    "never saved",
    "never kept",
    "exports are generated on demand and not kept",
    "does not store your exported files",
    "entire lifecycle",
    # Unproven test-result language.
    "clean results",
    "top findings",
    "3 findings",
    "workpaper-ready",
    "audit-ready",
    "audit-grade",
    "ready to attach",
    # Certification-style and security superlatives.
    "bank-grade",
    "enterprise-grade",
    "soc 2 ready",
    "soc 2 planned",
    "independent attestation",
    "evidence to prove it",
    "no pii in logs",
    "immediate isolation",
    # Generic-AI and unquantified wording.
    "intelligent",
    "diagnostic intelligence",
    "intelligence briefing",
    "surgical precision",
    "supercharge",
    "reimagine",
    "revolutioniz",
    "save hours",
    "10x faster",
    "in seconds",
    "professional-grade",
    "unlocks",
)

# Standard codes, as the citation registry writes them. Body names (IAASB,
# PCAOB, FASB …) are organizations, not standards, and are allowed.
STANDARD_CODE = re.compile(r"\b(ISA \d{3}|AS \d{4}|ASC \d{3}|IFRS \d{1,2}|IAS \d{1,2}|AU-C \d{3}|SOC [12]|ISO 27001)\b")
# The only standard names allowed on marketing pages: the Trust page's statement
# of certifications we do NOT hold, and the Trust FAQ answer the CEO brief
# requires (AU-C 230 and PCAOB AS 1215, named only in answer to a direct
# question, AU-C 230 first).
ALLOWED_STANDARD_LINES = (
    "holds no SOC 1, SOC 2, ISO 27001 or other third-party certification",
    "None held or claimed (no SOC 1, SOC 2 or ISO 27001).",
    "Does Paciolus hold a SOC 2 report or any other certification?",
    "Does Paciolus satisfy AU-C 230 or PCAOB AS 1215?",
    "No. AU-C 230 and PCAOB AS 1215 set documentation and retention duties for audit firms",
)

COMMENT_LINE = re.compile(r"^\s*(\*|//|/\*|\{/\*)")


def _files(prefixes: tuple[str, ...]) -> list[str]:
    listed = subprocess.run(
        ["git", "ls-files", *prefixes], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split("\n")
    return [f for f in listed if f.endswith((".ts", ".tsx")) and "__tests__" not in f and not f.startswith(LEGAL_PAGES)]


def _lines(rel: str):
    for n, line in enumerate((REPO / rel).read_text(encoding="utf-8").splitlines(), start=1):
        if not COMMENT_LINE.match(line):
            yield n, line


def test_scan_covers_the_surfaces():
    files = set(_files(CUSTOMER_FACING_PREFIXES))
    for expected in (
        "frontend/src/components/marketing/hero/HeroProductFilm.tsx",
        "frontend/src/app/(marketing)/trust/page.tsx",
        "frontend/src/content/trust.ts",
        "frontend/src/components/shared/testing/TestingScoreCard.tsx",
        "frontend/src/app/status/page.tsx",
    ):
        assert expected in files, expected


def test_banned_phrases_stay_out_of_customer_facing_copy():
    pattern = re.compile("|".join(re.escape(p) for p in BANNED_EVERYWHERE), re.IGNORECASE)
    hits = []
    for rel in _files(CUSTOMER_FACING_PREFIXES):
        for n, line in _lines(rel):
            # Identifiers such as IntelligenceCanvas are code, not copy.
            text = re.sub(r"\b[A-Za-z]+Intelligen\w*|\bintelligen\w*[A-Z]\w*", "", line)
            m = pattern.search(text)
            if m:
                hits.append(f"{rel}:{n}: {m.group(0)!r}")
    assert not hits, "Removed claims are back (reports/website-review-2026-11-14.md, Sprint 861):\n" + "\n".join(hits)


def test_marketing_pages_name_no_standard():
    hits = []
    for rel in _files(MARKETING_PREFIXES):
        if rel.startswith(CITATION_PAGES):
            continue
        for n, line in _lines(rel):
            if any(allowed in line for allowed in ALLOWED_STANDARD_LINES):
                continue
            m = STANDARD_CODE.search(line)
            if m:
                hits.append(f"{rel}:{n}: {m.group(0)!r}")
    assert not hits, "Standard codes belong on /sources, not marketing pages:\n" + "\n".join(hits)


def test_documentation_standards_are_named_only_in_the_trust_faq():
    """AU-C 230 / AS 1215 appear on marketing surfaces only in the Trust FAQ, AU-C 230 first."""
    pattern = re.compile(r"AU-C 230|AS 1215")
    for rel in _files(MARKETING_PREFIXES):
        for n, line in _lines(rel):
            if pattern.search(line):
                assert rel == "frontend/src/content/trust.ts", f"{rel}:{n} names a documentation standard"
                assert line.find("AU-C 230") < line.find("AS 1215"), f"{rel}:{n}: AU-C 230 must come first"


def test_status_page_shows_no_hard_coded_test_results():
    source = (REPO / "frontend/src/app/status/page.tsx").read_text(encoding="utf-8")
    assert "LAST_TEST_RUN" not in source
    assert "passed: true" not in source
