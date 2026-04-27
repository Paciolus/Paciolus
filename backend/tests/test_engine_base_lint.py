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
    BORDERLINE_ENGINES,
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
    """Engines that already subclass AuditEngineBase MUST NOT appear in findings.

    Sprint 519: JE / AP / Payroll.
    Sprint 727a: Inventory (first sub-sprint migration).

    A regression here means either the AST detection broke or the subclass
    declaration was inadvertently removed from one of the migrated engines.
    """

    def test_known_migrated_engines_not_in_findings(self):
        findings = find_off_pattern_engines()
        finding_names = {p.name for p in findings}
        for migrated in (
            "je_testing_engine.py",
            "ap_testing_engine.py",
            "payroll_testing_engine.py",
            "inventory_testing_engine.py",  # Sprint 727a
        ):
            assert migrated not in finding_names, (
                f"{migrated} appeared in off-pattern findings but should be on-pattern"
            )


# ---------------------------------------------------------------------------
# Sprint 727 triage outcome — blocklist & borderline classification
# ---------------------------------------------------------------------------


class TestSprint727Triage:
    """Sprint 727 triaged the 16 lint-flagged engines into migration targets,
    blocklist additions (calculators / aggregators / indicators that don't
    fit the testing-tool pipeline), and borderline cases that need design
    decisions before migration. These tests pin the classification so a
    future "rip out the blocklist to clean up the lint output" PR has to
    explain why it's removing a per-engine triage decision."""

    def test_sprint_727_blocklist_additions(self):
        # Each of these had a Sprint 727 rationale (descriptive stats /
        # calculator / indicator-only). Removing one without re-classifying
        # the engine should fail this test as a forcing function.
        for name in (
            "accrual_completeness_engine.py",
            "cash_flow_projector_engine.py",
            "expense_category_engine.py",
            "lease_accounting_engine.py",
            "lease_diagnostic_engine.py",
            "loan_amortization_engine.py",
            "population_profile_engine.py",
        ):
            assert name in NON_TESTING_ENGINES, f"{name} should be in NON_TESTING_ENGINES (Sprint 727 triage)"

    def test_sprint_727_migration_targets_still_in_findings(self):
        # The A-classified engines are the migration backlog Sprint 727+
        # actually picks up. Each remaining one MUST appear in findings —
        # disappearing without a corresponding migration commit means the
        # lint regressed or someone added it to the blocklist without
        # rationale.
        #
        # Sprint 727a migrated inventory_testing_engine — it's now on-pattern
        # and is asserted in TestKnownMigrated above. The four remaining
        # targets are listed here.
        findings = find_off_pattern_engines()
        finding_names = {p.name for p in findings}
        for migration_target in (
            "ar_aging_engine.py",
            "fixed_asset_testing_engine.py",
            "revenue_testing_engine.py",
            "sod_engine.py",
        ):
            assert migration_target in finding_names, (
                f"{migration_target} (Sprint 727 migration target) should be in findings"
            )

    def test_borderline_engines_in_findings_not_blocklist(self):
        # Borderline engines (ratio, sampling, three_way_match, w2_recon) are
        # surfaced as findings (so they can't be silently forgotten) but NOT
        # in the blocklist (the per-engine decision hasn't been made yet).
        findings = find_off_pattern_engines()
        finding_names = {p.name for p in findings}
        for borderline in BORDERLINE_ENGINES:
            assert borderline in finding_names, (
                f"{borderline} (borderline) should be in findings until per-engine decision lands"
            )
            assert borderline not in NON_TESTING_ENGINES, (
                f"{borderline} (borderline) should NOT be in blocklist; classify per engine first"
            )

    def test_post_triage_finding_count(self):
        # Sprint 727 brought the count from 16 → 9 (5 migration targets + 4
        # borderline). A future migration sprint that lands one engine should
        # bring this to 8; if a future PR adds another off-pattern engine
        # without thinking, this test makes the count visible.
        findings = find_off_pattern_engines()
        # Allow some flex for new engines added after Sprint 727 — assertion
        # is a reasonable upper bound, not an exact count.
        assert 5 <= len(findings) <= 12, (
            f"Off-pattern engine count {len(findings)} outside expected post-Sprint-727 range. "
            "Either a migration landed (count down), a new engine was added (count up), "
            "or the lint script regressed."
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
