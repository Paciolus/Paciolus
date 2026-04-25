"""Sprint 721 — ISA 265 boundary phrasing guardrail.

Memo generators (`backend/*_memo_generator.py`) produce workpaper-style
PDF/text content. Language that drifts toward auditor-judgment territory
(deficiency classification, misstatement conclusions, prescriptive
remediation) exposes Paciolus to the ISA 265 boundary line.

This test scans every memo generator's source for patterns from the
deny list in `docs/03-engineering/auditing-lexicon.md`. Hits fail the
build unless explicitly annotated `# allow-deny-phrase: <reason>` on
the same line.

Coverage scope: backend/*_memo_generator.py (file glob match). The
test scans Python source (which is what reviewers and the model both
edit). It does NOT render the PDF; that's a more expensive integration
test and the source-string check catches the same phrases without
the PDF runtime.

Pattern selection: deny patterns are word-boundary regex matches against
the lexicon table. Adding/removing a pattern requires updating both this
file and the lexicon doc.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"

# Lexicon-aligned deny patterns (case-insensitive).
# Each tuple: (regex, human-readable description used in failure messages)
DENY_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\bdeficienc(y|ies)\b", re.IGNORECASE),
        "ISA 265 deficiency classification — replace with 'anomaly indicator'",
    ),
    (
        re.compile(r"\bcontrol\s+(failure|deficienc(y|ies))\b", re.IGNORECASE),
        "Control-design conclusion — replace with 'control-related signal warrants inquiry'",
    ),
    (
        re.compile(r"\brecommended\s+remediation\b", re.IGNORECASE),
        "Advisory voice — replace with 'auditor may consider'",
    ),
    (
        re.compile(r"\bsystemic\s+review.*recommended\b", re.IGNORECASE | re.DOTALL),
        "Root-cause conclusion — replace with 'auditor judgment required to determine cause'",
    ),
    (re.compile(r"\bwe\s+recommend\b", re.IGNORECASE), "Advisory voice — replace with 'consider whether'"),
    (
        re.compile(r"\b(potential|likely)\s+understatement\s+of\s+\w+\s+expense\b", re.IGNORECASE),
        "Misstatement conclusion — replace with 'signal of potential understatement; auditor to investigate'",
    ),
    (
        re.compile(r"\bis\s+not\s+adequate\b", re.IGNORECASE),
        "Sufficiency conclusion — replace with 'coverage anomaly indicator'",
    ),
    (
        re.compile(r"\bis\s+insufficient\b", re.IGNORECASE),
        "Sufficiency conclusion — replace with 'coverage anomaly indicator'",
    ),
    (re.compile(r"\bmust\s+correct\b", re.IGNORECASE), "Directive — replace with 'warrants inquiry'"),
    (re.compile(r"\brequires\s+correction\b", re.IGNORECASE), "Directive — replace with 'warrants further review'"),
    (re.compile(r"\baudit\s+opinion\b", re.IGNORECASE), "Attestation language — never use in an automated memo"),
    (re.compile(r"\bwe\s+opine\b", re.IGNORECASE), "Attestation language — never use in an automated memo"),
    (
        re.compile(r"\bnot\s+in\s+compliance\s+with\b", re.IGNORECASE),
        "Compliance conclusion — replace with 'signal inconsistent with … expectations'",
    ),
)

ALLOW_ANNOTATION: re.Pattern[str] = re.compile(r"#\s*allow-deny-phrase\s*:")


def _memo_generator_files() -> list[Path]:
    """Every backend/*_memo_generator.py."""
    return sorted(BACKEND_DIR.glob("*_memo_generator.py"))


def _scan_source(path: Path) -> list[tuple[int, str, str, str]]:
    """Return list of (lineno, line_text, pattern_desc, matched_text).

    Skip any line carrying the # allow-deny-phrase: annotation.
    """
    findings: list[tuple[int, str, str, str]] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if ALLOW_ANNOTATION.search(raw):
            continue
        for pattern, desc in DENY_PATTERNS:
            match = pattern.search(raw)
            if match:
                findings.append((lineno, raw.strip(), desc, match.group(0)))
    return findings


# ───────────────────────── Tests ─────────────────────────


def test_at_least_one_memo_generator_exists():
    """Smoke check that the glob yields files."""
    files = _memo_generator_files()
    assert files, "No *_memo_generator.py files found in backend/"


@pytest.mark.parametrize("path", _memo_generator_files(), ids=lambda p: p.name)
def test_memo_generator_uses_allowed_phrasing(path: Path):
    """Memo generator must not contain deny-list phrasing.

    See ``docs/03-engineering/auditing-lexicon.md`` for the canonical
    allow/deny tables. To override (rare), annotate the offending line
    with ``# allow-deny-phrase: <reason>`` and explain in PR review.
    """
    findings = _scan_source(path)
    if findings:
        lines = [f"ISA 265 boundary phrasing in {path.relative_to(REPO_ROOT)}:"]
        for lineno, text, desc, matched in findings:
            lines.append(f"  line {lineno}: matched {matched!r}")
            lines.append(f"    rule: {desc}")
            lines.append(f"    text: {text[:200]}")
        lines.append(
            "Per docs/03-engineering/auditing-lexicon.md: rephrase to anomaly-indicator language, "
            "or annotate the line with `# allow-deny-phrase: <reason>` if the phrase is legitimate "
            "(e.g., quoting a standard's title)."
        )
        pytest.fail("\n".join(lines))


def test_lexicon_doc_exists():
    """The lexicon doc must exist; this test is the single source of truth for the deny list."""
    lexicon = REPO_ROOT / "docs" / "03-engineering" / "auditing-lexicon.md"
    assert lexicon.is_file(), f"Lexicon doc missing: {lexicon}. The CI deny-list test references it."
