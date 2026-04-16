"""Sprint 632 — Account Sequence Gap Detector tests.

Exercises the forensic ``detect_account_number_gaps`` rule in
``backend/audit/rules/gaps.py`` and verifies the
``check_suspicious_sequence_gaps`` integration in
``classification_validator.py``.
"""

from audit.rules.gaps import (
    DEFAULT_BOUNDARY_PROXIMITY,
    DEFAULT_MIN_GAP,
    AccountGap,
    detect_account_number_gaps,
)
from classification_validator import (
    ClassificationIssueType,
    check_suspicious_sequence_gaps,
    run_classification_validation,
)


class TestGapDetectorBasics:
    def test_no_gaps_on_sequential_series(self):
        names = [
            "1000 Cash",
            "1010 Accounts Receivable",
            "1020 Inventory",
            "1030 Prepaid Expenses",
            "1040 Fixed Assets",
        ]
        gaps, stats = detect_account_number_gaps(names)
        assert gaps == []
        assert stats["total_gaps"] == 0

    def test_suppressed_range_fires(self):
        # Dense Asset block with a clean suppression between 1050 and 1200.
        names = [
            "1010 Cash A",
            "1020 Cash B",
            "1030 Cash C",
            "1040 Cash D",
            "1050 Cash E",
            # 1060–1190 suppressed
            "1200 AR A",
            "1210 AR B",
            "1220 AR C",
            "1230 AR D",
        ]
        gaps, stats = detect_account_number_gaps(names)
        assert len(gaps) == 1
        gap = gaps[0]
        assert isinstance(gap, AccountGap)
        assert gap.prev_number == 1050
        assert gap.next_number == 1200
        assert gap.gap_size == 150
        assert gap.category_block_start == 1000
        assert gap.severity == "high"
        assert stats["high_severity"] == 1

    def test_category_boundary_does_not_fire(self):
        # Natural jump from Assets (1xxx) to Liabilities (2xxx).
        names = [
            "1010 Cash",
            "1020 AR",
            "1030 Inventory",
            # Category boundary — expected
            "2010 Accounts Payable",
            "2020 Accrued Expenses",
            "2030 Notes Payable",
        ]
        gaps, stats = detect_account_number_gaps(names)
        assert gaps == []
        assert stats["total_gaps"] == 0

    def test_isolated_neighbour_does_not_fire(self):
        # Prev neighbour is isolated (no account within proximity before it).
        names = [
            "1010 Cash",
            "1200 AR A",
            "1210 AR B",
            "1220 AR C",
        ]
        gaps, _ = detect_account_number_gaps(names)
        assert gaps == []

    def test_too_few_accounts_returns_empty(self):
        names = ["1000 Cash", "2000 AP"]
        gaps, stats = detect_account_number_gaps(names)
        assert gaps == []
        assert stats["total_gaps"] == 0

    def test_medium_severity_gap(self):
        # Gap of ~60 with clustered neighbours.
        names = [
            "1010 Cash A",
            "1020 Cash B",
            "1030 Cash C",
            # 1031–1089 suppressed
            "1090 Cash D",
            "1095 Cash E",
        ]
        gaps, stats = detect_account_number_gaps(names)
        assert len(gaps) == 1
        assert gaps[0].severity == "medium"
        assert stats["medium_severity"] == 1

    def test_cluster_step_tuning(self):
        # With strict cluster_step = 5 the cluster test fails because
        # the 1010→1020 steps are 10 apart.
        names = [
            "1010 A",
            "1020 B",
            "1030 C",
            "1200 D",
            "1210 E",
            "1220 F",
        ]
        gaps_loose, _ = detect_account_number_gaps(names)
        gaps_strict, _ = detect_account_number_gaps(names, cluster_step=5)
        assert len(gaps_loose) == 1
        assert gaps_strict == []

    def test_legacy_boundary_proximity_alias_still_works(self):
        names = [
            "1010 A",
            "1020 B",
            "1030 C",
            "1200 D",
            "1210 E",
            "1220 F",
        ]
        gaps_via_alias, _ = detect_account_number_gaps(names, boundary_proximity=5)
        assert gaps_via_alias == []


class TestClassificationValidatorIntegration:
    def test_suspicious_gap_surfaces_as_number_gap_issue(self):
        accounts = {
            "1010 Cash A": {"debit": 100.0, "credit": 0.0},
            "1020 Cash B": {"debit": 200.0, "credit": 0.0},
            "1030 Cash C": {"debit": 300.0, "credit": 0.0},
            "1040 Cash D": {"debit": 400.0, "credit": 0.0},
            "1050 Cash E": {"debit": 500.0, "credit": 0.0},
            "1200 AR A": {"debit": 100.0, "credit": 0.0},
            "1210 AR B": {"debit": 200.0, "credit": 0.0},
            "1220 AR C": {"debit": 300.0, "credit": 0.0},
            "1230 AR D": {"debit": 400.0, "credit": 0.0},
        }
        issues = check_suspicious_sequence_gaps(accounts)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == ClassificationIssueType.NUMBER_GAP
        assert issue.severity == "high"
        assert "1050" in issue.description
        assert "1200" in issue.description
        assert "suppressed" in issue.suggested_action.lower() or "renumber" in issue.suggested_action.lower()

    def test_run_classification_validation_includes_gap_check(self):
        accounts = {
            "1010 Cash A": {"debit": 100.0, "credit": 0.0},
            "1020 Cash B": {"debit": 200.0, "credit": 0.0},
            "1030 Cash C": {"debit": 300.0, "credit": 0.0},
            "1040 Cash D": {"debit": 400.0, "credit": 0.0},
            "1050 Cash E": {"debit": 500.0, "credit": 0.0},
            "1200 AR A": {"debit": 100.0, "credit": 0.0},
            "1210 AR B": {"debit": 200.0, "credit": 0.0},
            "1220 AR C": {"debit": 300.0, "credit": 0.0},
            "1230 AR D": {"debit": 400.0, "credit": 0.0},
        }
        classifications = {name: "asset" for name in accounts}
        result = run_classification_validation(accounts, classifications)

        gap_issues = [
            i
            for i in result.issues
            if i.issue_type == ClassificationIssueType.NUMBER_GAP and "suspicious" in i.description.lower()
        ]
        assert len(gap_issues) == 1

    def test_clean_tb_produces_no_suspicious_gap_issues(self):
        accounts = {
            "1000 Cash": {"debit": 100.0, "credit": 0.0},
            "2000 AP": {"debit": 0.0, "credit": 50.0},
            "3000 Equity": {"debit": 0.0, "credit": 25.0},
            "4000 Revenue": {"debit": 0.0, "credit": 125.0},
            "5000 COGS": {"debit": 50.0, "credit": 0.0},
        }
        issues = check_suspicious_sequence_gaps(accounts)
        assert issues == []


class TestConstants:
    def test_defaults_exported(self):
        assert DEFAULT_MIN_GAP == 10
        # DEFAULT_BOUNDARY_PROXIMITY is a legacy alias for the cluster step.
        assert DEFAULT_BOUNDARY_PROXIMITY == 10
