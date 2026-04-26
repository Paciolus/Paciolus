"""Sprint 726 — AuditEngineBase adoption lint script tests.

Covers the AST detection (subclass + alias forms), the testing-engine filter
(includes the right files, excludes the right ones), and the CLI flow
(warning-only by default, --strict flips exit code).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lint_engine_base_adoption import (  # noqa: E402  (path manipulation above)
    NON_TESTING_ENGINES,
    _is_testing_engine,
    _subclasses_audit_engine_base,
    find_off_pattern_engines,
    main,
)

# ---------------------------------------------------------------------------
# AST subclass detection
# ---------------------------------------------------------------------------


class TestSubclassDetection:
    def test_direct_subclass_detected(self):
        source = "from engine_framework import AuditEngineBase\nclass MyEngine(AuditEngineBase):\n    pass\n"
        assert _subclasses_audit_engine_base(source) is True

    def test_aliased_subclass_detected(self):
        source = "import engine_framework\nclass MyEngine(engine_framework.AuditEngineBase):\n    pass\n"
        assert _subclasses_audit_engine_base(source) is True

    def test_no_subclass_returns_false(self):
        source = "def run_my_tool(rows):\n    return []\n"
        assert _subclasses_audit_engine_base(source) is False

    def test_subclass_of_unrelated_base_returns_false(self):
        source = "class MyEngine(SomethingElse):\n    pass\n"
        assert _subclasses_audit_engine_base(source) is False

    def test_syntax_error_returns_false(self):
        # Malformed Python — should not raise; return False so the file
        # surfaces as off-pattern (which it is).
        source = "this is not valid python {{{ "
        assert _subclasses_audit_engine_base(source) is False


# ---------------------------------------------------------------------------
# Testing-engine filter
# ---------------------------------------------------------------------------


class TestTestingEngineFilter:
    def test_testing_engine_suffix_always_included(self):
        # Any *_testing_engine.py file is in scope, regardless of NON_TESTING_ENGINES.
        for name in ("revenue_testing_engine.py", "ap_testing_engine.py", "fake_testing_engine.py"):
            assert _is_testing_engine(Path(name)) is True

    def test_engine_suffix_excluded_when_in_blocklist(self):
        for name in NON_TESTING_ENGINES:
            assert _is_testing_engine(Path(name)) is False

    def test_engine_suffix_included_when_not_blocklisted(self):
        # ``revenue_engine.py`` (hypothetical, not the testing variant) — not in
        # NON_TESTING_ENGINES, so should be included.
        assert _is_testing_engine(Path("revenue_engine.py")) is True

    def test_non_engine_files_excluded(self):
        for name in ("models.py", "main.py", "engine_framework.py"):
            assert _is_testing_engine(Path(name)) is False


# ---------------------------------------------------------------------------
# Repo state — known migrated engines should NOT appear in findings
# ---------------------------------------------------------------------------


class TestKnownMigrated:
    def test_je_ap_payroll_not_in_findings(self):
        """JE / AP / Payroll subclass AuditEngineBase (Sprint 519). They MUST
        NOT appear in the off-pattern findings — that would mean either the
        AST detection broke or the engines were de-migrated."""
        findings = find_off_pattern_engines()
        finding_names = {p.name for p in findings}
        for migrated in ("je_testing_engine.py", "ap_testing_engine.py", "payroll_testing_engine.py"):
            assert migrated not in finding_names, (
                f"{migrated} appeared in off-pattern findings but should be on-pattern"
            )


# ---------------------------------------------------------------------------
# CLI exit codes
# ---------------------------------------------------------------------------


class TestCli:
    def test_default_exits_zero_with_findings(self, capsys: pytest.CaptureFixture):
        # Phase 1 contract: warning-only. Exit 0 even when findings exist.
        rc = main([])
        assert rc == 0
        # If findings exist, the output should mention Phase 1 + ADR pointer.
        captured = capsys.readouterr()
        # At least one of: "all testing engines on-pattern" (no findings)
        # or "Phase 1" (findings present with advisory note).
        assert ("on-pattern" in captured.out) or ("Phase 1" in captured.out)

    def test_strict_exits_nonzero_on_findings(self):
        # --strict flips exit code so Sprint 727 can validate the gate before
        # promoting it. As of Sprint 726 there are findings (16 off-pattern
        # engines per the initial run), so --strict should exit 1.
        rc = main(["--strict"])
        # If findings list is empty (after Sprint 727 migrations), this would
        # be 0 — that's the success state. Either way, the rc matches strict
        # expectation.
        findings = find_off_pattern_engines()
        if findings:
            assert rc == 1
        else:
            assert rc == 0
