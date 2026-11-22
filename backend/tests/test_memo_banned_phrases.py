"""
Sprint 843 merge gate (2026-10-28 plan): no memo may speak as an auditor.

Generalises ``test_multi_period_memo.py::TestMultiPeriodMemoGuardrails`` to
every memo generator. A memo reports flag density and test results; the
conclusion is the auditor's. So no memo says "we conclude", calls anything
"satisfactory" or "appears sound", issues a PASS/FAIL verdict, or prints a
"Conclusion" heading over its own text.

Two layers, because each misses what the other catches:

1. **Rendered text.** ``fixtures/memo_render_snapshot.json`` holds the
   extracted text of every memo PDF, and ``test_memo_render_equivalence.py``
   fails if a memo's current output differs from it — so scanning the
   snapshot scans what a customer actually downloads, cover and footer
   included.
2. **Source string literals.** The fixtures exercise one path per memo; the
   other risk tiers and branches only exist as literals in the generator. Every
   ``*memo*.py`` module in ``backend/`` (discovered, so a new generator is
   covered without editing this file) plus the shared memo modules is parsed,
   and every string constant that is not a docstring is scanned.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = Path(__file__).parent / "fixtures" / "memo_render_snapshot.json"

# (pattern, why). Case-insensitive unless the pattern sets its own flags.
BANNED: list[tuple[str, str]] = [
    (r"\bwe (?:have )?conclude[ds]?\b", "the conclusion is the auditor's"),
    (r"\bwe believe\b", "the conclusion is the auditor's"),
    (r"\bwe are satisfied\b", "the conclusion is the auditor's"),
    (r"\bappears? sound\b", "an assessment, not a result"),
    (r"\bsatisfactor(?:y|ily)\b", "an assessment, not a result (H10)"),
    (r"\b(?:fairly stated|present(?:s|ed)? fairly|fairly present(?:s|ed)?)\b", "opinion language"),
    (r"\bno misstatement exists\b", "an assurance claim"),
    (r"\bfinancial statements are correct\b", "an assurance claim"),
    (r"\b(?:clean|unqualified) opinion\b", "opinion language"),
    (r"(?-i:\b(?:PASS|FAIL)(?:ED)?\b)", "a verdict (M2: sampling uses UEL vs TM)"),
    (r"\bis an? (?:pass|fail)\b", "a verdict (M2: sampling uses UEL vs TM)"),
    # Sprint 865 (CEO rule 2026-11-14: a claim we cannot prove is removed). Every
    # memo ended with a "Zero-Storage Architecture ... no client financial data is
    # retained" paragraph that the website had already retired as false.
    (r"zero[- ]storage", "retired claim: summaries, engagement entries and backups are kept"),
    (r"not persisted to any storage", "retired claim: see content/storage-statement.ts"),
    (r"\bnever stored\b", "retired claim: see content/storage-statement.ts"),
    (r"no client financial data is retained", "retired claim: see content/storage-statement.ts"),
    (r"diagnostic intelligence", "generic-AI wording (reports/website-review-2026-11-14.md G-10)"),
    (r"\btests clear\b", "a 'clean' verdict; say 'no exceptions flagged'"),
    (r"\bfindings?\b", "results are flags for review, not findings"),
    # Sprint 887 (OUT-30): result words the product does not use. A test with nothing
    # flagged is "no exceptions flagged" — never clean, passed or verified.
    (r"\bclean\b", "a verdict; say 'no exceptions flagged'"),
    (r"\b(?:not )?passed\b", "a verdict; say what was or was not met"),
    (r"\bverified\b", "a verdict; say what was compared"),
    # Sprint 893: whether anything needs investigating is the auditor's call.
    (r"\bno items requiring (?:further )?investigation\b", "a conclusion; say 'no exceptions flagged'"),
    ("®", "the registered-trademark sign asserts a registration we have not confirmed"),
]
_BANNED_RE = [(re.compile(p, re.IGNORECASE), p, why) for p, why in BANNED]

# A "Conclusion" heading: a rendered line that is only that word.
_CONCLUSION_HEADING = re.compile(r"^\s*conclusions?\s*:?\s*$", re.IGNORECASE | re.MULTILINE)
# The flux memo's "Conclusion:" is a fill-in field for the auditor's own written
# conclusion (Sprint 843 kept it deliberately), not a heading over memo text.
CONCLUSION_FIELD_ALLOWED = {"flux_expectations"}


# Audit terms that contain a banned word but are not result words: a "passed"
# adjusting entry is one the auditor proposed and management did not record.
ALLOWED_TERMS = ("Passed AJE",)


def _hits(text: str) -> list[str]:
    for term in ALLOWED_TERMS:
        text = text.replace(term, "")
    found = []
    for rx, pattern, why in _BANNED_RE:
        for m in rx.finditer(text):
            context = text[max(0, m.start() - 40) : m.end() + 40].replace("\n", " | ")
            found.append(f"{pattern!r} ({why}): …{context}…")
    return found


# ---------------------------------------------------------------------------
# 1. Rendered memo text
# ---------------------------------------------------------------------------


def _snapshot() -> dict:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def _rendered_cases() -> list[tuple[str, str]]:
    cases = []
    for key, value in sorted(_snapshot().items()):
        pages = value.get("pages") if isinstance(value, dict) else None
        if pages:
            cases.append((key, "\n".join(page.get("text", "") for page in pages)))
    return cases


_RENDERED = _rendered_cases()


def test_snapshot_covers_every_memo():
    memos = {key.split("[")[0] for key, _ in _RENDERED}
    # 18 tool memos + the report/diagnostic memos; a shrinking snapshot would
    # silently shrink this gate.
    assert len(memos) >= 18, sorted(memos)


@pytest.mark.parametrize("key, text", _RENDERED, ids=[k for k, _ in _RENDERED])
def test_rendered_memo_has_no_banned_phrase(key, text):
    assert not _hits(text), f"{key} renders banned wording:\n" + "\n".join(_hits(text))


@pytest.mark.parametrize("key, text", _RENDERED, ids=[k for k, _ in _RENDERED])
def test_rendered_memo_has_no_conclusion_heading(key, text):
    if key.split("[")[0] in CONCLUSION_FIELD_ALLOWED:
        return
    assert not _CONCLUSION_HEADING.search(text), f"{key} renders a 'Conclusion' heading"


# ---------------------------------------------------------------------------
# 2. Source string literals (every branch, not only the fixture's)
# ---------------------------------------------------------------------------


def _memo_modules() -> list[Path]:
    modules = sorted(p for p in BACKEND.glob("*memo*.py"))
    modules += [BACKEND / "shared" / "memo_base.py", BACKEND / "shared" / "memo_template.py"]
    # Sprint 887 (OUT-30): label mappings and generated prefixes that reach documents.
    modules += [
        BACKEND / "shared" / "follow_up_procedures.py",
        BACKEND / "shared" / "tb_diagnostic_constants.py",
        BACKEND / "preflight_engine.py",
        BACKEND / "anomaly_summary_generator.py",
    ]
    return modules


def _string_literals(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstrings.add(id(body[0].value))
    return [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
        # Sprint 865: a bare identifier ("findings", "top_findings") is a data
        # key, never rendered text.
        and not re.fullmatch(r"[a-z_]+", node.value)
    ]


_MODULES = _memo_modules()


def test_memo_modules_discovered():
    assert len(_MODULES) >= 20, [p.name for p in _MODULES]
    for path in _MODULES:
        assert path.exists(), path


@pytest.mark.parametrize("path", _MODULES, ids=[p.name for p in _MODULES])
def test_memo_source_has_no_banned_phrase(path):
    found = [f"{path.name}:{line}: {hit}" for line, text in _string_literals(path) for hit in _hits(text)]
    assert not found, "Banned memo wording in source:\n" + "\n".join(found)


_COMMANDS = re.compile(
    r"(?:^|[.;] )(?:Obtain|Verify|Investigate|Request|Confirm|Inspect|Review|Evaluate|Determine|Document)\b"
)


def test_suggested_procedures_are_suggestions():
    """Sprint 887 (OUT-30): every suggestion opens "The auditor may consider" and gives no command."""
    from shared.follow_up_procedures import PROCEDURES

    bad = []
    for tool, tests in PROCEDURES.items():
        for key, variants in tests.items():
            for text in variants:
                opens = text.startswith("The auditor may consider ")
                if not opens or re.search(r"\bmust\b", text) or _COMMANDS.search(text):
                    bad.append(f"{tool}/{key}: {text[:90]}")
    assert not bad, "\n".join(bad)


def test_banned_list_catches_known_bad_wording():
    """The patterns must actually fire, or the gate passes vacuously."""
    for bad in [
        "We conclude that the balances are reasonable.",
        "Internal controls appear sound.",
        "Results are satisfactory.",
        "The accounts are fairly stated.",
        "Evaluation: FAIL",
        "The conclusion is a fail if either limit exceeds TM.",
        "Clean",
        "Pre-check not passed",
        "Net balance column \u2014 verified against debit/credit pair",
        "Material exceptions (3 findings)",
        "To further substantiate the finding, ",
    ]:
        assert _hits(bad), bad
    for fine in ["LLC pass-through status", "UEL > TM", "Summary of Results", "no misstatement is found"]:
        assert not _hits(fine), fine
