"""Sprint 721 — ISA 265 boundary phrasing guardrail.

Memo generators (`backend/*_memo_generator.py`) produce workpaper-style
PDF/text content. Language that drifts toward auditor-judgment territory
(deficiency classification, misstatement conclusions, prescriptive
remediation) exposes Paciolus to the ISA 265 boundary line.

This test scans every memo generator's source for patterns from the
deny list in `docs/03-engineering/auditing-lexicon.md`. Hits fail the
build unless explicitly annotated `# allow-deny-phrase: <reason>` on
the same line, or located inside the module docstring (maintainer
documentation, which never reaches a rendered PDF).

Coverage scope: backend/*_memo_generator.py plus the explicitly named
content producers in EXTRA_SCANNED_FILES. The test scans Python source
(which is what reviewers and the model both edit). It does NOT render
the PDF; that's a more expensive integration test and the source-string
check catches the same phrases without the PDF runtime.

Sprint 779 widened the scope. The glob-only version is why
``generate_sample_reports.py`` still emitted "systemic review of
procure-to-pay controls recommended" months after the shipped generators
were cleaned of it: the sample generator produces the output a prospect
is most likely to read first, and nothing held it to the same rules.

Pattern selection: deny patterns are word-boundary regex matches against
the lexicon table. Adding/removing a pattern requires updating both this
file and the lexicon doc.
"""

from __future__ import annotations

import ast
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


# Content producers that match neither memo glob but emit the
# same practitioner-facing narrative text. Paths are relative to backend/.
EXTRA_SCANNED_FILES: tuple[str, ...] = (
    "generate_sample_reports.py",
    "anomaly_summary_generator.py",
    "shared/follow_up_procedures.py",
    "shared/memo_base.py",
    "shared/memo_template.py",
)


def _memo_generator_files() -> list[Path]:
    """Every backend/*_memo_generator.py and *_memo.py, plus the named extra producers.

    Sprint 813: the ``*_memo.py`` half was missing, so the accrual, expense,
    flux and population-profile memos were never scanned.
    """
    files = sorted({*BACKEND_DIR.glob("*_memo_generator.py"), *BACKEND_DIR.glob("*_memo.py")})
    files.extend(BACKEND_DIR / rel for rel in EXTRA_SCANNED_FILES if (BACKEND_DIR / rel).is_file())
    return files


def _module_docstring_lines(source: str) -> set[int]:
    """Line numbers occupied by the module docstring, if there is one.

    A module docstring is documentation for maintainers and never reaches a
    rendered PDF, so deny-list phrasing in it is not a boundary problem. The
    guardrail docstring in ``anomaly_summary_generator.py`` names the ISA 265
    sections the template deliberately refuses to produce — naming them is
    the whole point of the note.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    body = tree.body
    if not body or not isinstance(body[0], ast.Expr) or not isinstance(body[0].value, ast.Constant):
        return set()
    if not isinstance(body[0].value.value, str):
        return set()
    node = body[0]
    end = node.end_lineno or node.lineno
    return set(range(node.lineno, end + 1))


def _scan_source(path: Path) -> list[tuple[int, str, str, str]]:
    """Return list of (lineno, line_text, pattern_desc, matched_text).

    Skip any line carrying the # allow-deny-phrase: annotation, and any line
    inside the module docstring.
    """
    findings: list[tuple[int, str, str, str]] = []
    source = path.read_text(encoding="utf-8")
    skip_lines = _module_docstring_lines(source)
    for lineno, raw in enumerate(source.splitlines(), start=1):
        if lineno in skip_lines or ALLOW_ANNOTATION.search(raw):
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


def test_extra_scanned_files_all_exist():
    """Every path in EXTRA_SCANNED_FILES must resolve.

    A renamed or moved producer would otherwise drop out of the scan
    silently, which is the failure mode Sprint 779 was fixing.
    """
    missing = [rel for rel in EXTRA_SCANNED_FILES if not (BACKEND_DIR / rel).is_file()]
    assert not missing, (
        f"EXTRA_SCANNED_FILES references files that no longer exist: {missing}. "
        "Update the tuple so the boundary scan keeps its coverage."
    )


def test_lexicon_doc_exists():
    """The lexicon doc must exist; this test is the single source of truth for the deny list."""
    lexicon = REPO_ROOT / "docs" / "03-engineering" / "auditing-lexicon.md"
    assert lexicon.is_file(), f"Lexicon doc missing: {lexicon}. The CI deny-list test references it."
