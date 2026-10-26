"""Sprint 841: the retired "never stored" absolutes stay retired.

CEO decision 2026-10-24 (claims review, Option B): Paciolus does not promise
"Zero-Storage". Uploaded files are processed in memory and not kept; the
database does keep accounts, client lists, analysis summaries (totals, ratios,
flagged account names) and engagement content, and R2 holds shared reports for
up to 48 hours. Copy that says otherwise is a false statement to customers.

This scans every customer-facing surface — the website and app, email
templates, the published compliance documents (the repository is public) and
the user guide — and fails on any of the phrases the claims review retired.
The approved wording lives in ``frontend/src/content/storage-statement.ts``.
"""

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

SCANNED_PREFIXES = (
    "frontend/src/app/",
    "frontend/src/components/",
    "frontend/src/content/",
    "frontend/src/domain/",
    "backend/templates/",
    "docs/04-compliance/",
    "docs/07-user-facing/",
)
# Dated, superseded versions kept for the record; each is labelled as such.
EXCLUDED_PREFIXES = ("docs/04-compliance/archive/",)
SCANNED_SUFFIXES = (".ts", ".tsx", ".md", ".html", ".txt")

RETIRED_PHRASES = (
    "never stored",
    "not stored at rest",
    "never written to disk",
    "nothing is written to disk",
    "never saved to any disk",
    "never touches a database",
    "never touches our database",
    "no database to breach",
    "no financial data in database",
    "architecturally impossible",
    "the architecture makes it impossible",
    "zero exposure",
    "zero-storage compliant",
    "zero retention",
    "zero data retention",
    "zero financial data retention",
    "lines stored",
    "only credentials are saved",
    "only client metadata is saved",
    "immediately destroyed",
    "nothing was persisted",
    "no data is stored",
)
_PATTERN = re.compile("|".join(re.escape(p) for p in RETIRED_PHRASES), re.IGNORECASE)


def _scanned_files() -> list[str]:
    listed = subprocess.run(
        ["git", "ls-files", *SCANNED_PREFIXES], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split("\n")
    return [
        f
        for f in listed
        if f.endswith(SCANNED_SUFFIXES) and not f.startswith(EXCLUDED_PREFIXES) and "__tests__" not in f
    ]


def test_scan_covers_the_customer_facing_surfaces():
    files = set(_scanned_files())
    for expected in (
        "frontend/src/app/(marketing)/privacy/page.tsx",
        "frontend/src/app/(marketing)/terms/page.tsx",
        "frontend/src/components/marketing/FeaturePillars.tsx",
        "backend/templates/verification_email.html",
        "docs/07-user-facing/USER_GUIDE.md",
        "docs/04-compliance/DATA_PROCESSING_ADDENDUM.md",
    ):
        assert expected in files, expected


def test_no_retired_storage_absolutes():
    hits = []
    for rel in _scanned_files():
        for lineno, line in enumerate((REPO / rel).read_text(encoding="utf-8").splitlines(), 1):
            match = _PATTERN.search(line)
            if match:
                hits.append(f"{rel}:{lineno}: {match.group(0)!r}")
    assert not hits, (
        "Retired storage claims (see frontend/src/content/storage-statement.ts for the approved wording):\n  "
        + "\n  ".join(hits)
    )


# "Zero-Storage" as a product claim is retired on the surfaces customers read.
# The compliance documents are rewritten in Sprint 845 and still use the name
# (including the ZERO_STORAGE_ARCHITECTURE.md filename), so they are not in
# scope here; code comments are not customer-facing and are skipped.
_TERM = re.compile(r"zero[- ]storage", re.IGNORECASE)
_TERM_PREFIXES = (
    "frontend/src/app/",
    "frontend/src/components/",
    "frontend/src/content/",
    "frontend/src/domain/",
    "backend/templates/",
    "docs/07-user-facing/",
)
_COMMENT = re.compile(r"^\s*(//|\*|/\*|\{/\*)")


def test_zero_storage_is_not_used_as_a_customer_facing_claim():
    hits = []
    for rel in _scanned_files():
        if not rel.startswith(_TERM_PREFIXES):
            continue
        for lineno, line in enumerate((REPO / rel).read_text(encoding="utf-8").splitlines(), 1):
            if _TERM.search(line) and not _COMMENT.match(line):
                hits.append(f"{rel}:{lineno}")
    assert not hits, "'Zero-Storage' used as a claim:\n  " + "\n  ".join(hits)
