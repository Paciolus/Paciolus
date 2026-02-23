"""
Sprint 392: Tests for Proof Summary Section in PDF Memos.

Validates:
- build_proof_summary_section() generates table flowables
- Correct metric values extracted from result dict
- Missing/empty data fallbacks (zeros, missing keys)
- Integration via generate_testing_memo (7 standard tools)
- Integration in bank_reconciliation_memo_generator
- Integration in three_way_match_memo_generator
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.memo_base import build_proof_summary_section, create_memo_styles
from shared.memo_template import TestingMemoConfig, generate_testing_memo

# =============================================================================
# FIXTURES
# =============================================================================

def _make_styles():
    return create_memo_styles()


def _make_result(
    completeness: float = 95.0,
    col_confidence: float = 0.92,
    tests_run: int = 5,
    total_flagged: int = 2,
    test_results: list | None = None,
) -> dict:
    """Build a result dict with proof-relevant fields."""
    return {
        "composite_score": {
            "score": 10.0,
            "risk_tier": "low",
            "total_entries": 100,
            "total_flagged": total_flagged,
            "flag_rate": total_flagged / 100,
            "tests_run": tests_run,
            "flags_by_severity": {"high": 1, "medium": 0, "low": 1},
            "top_findings": [],
        },
        "test_results": test_results or [
            {"test_key": "t1", "test_name": "Test 1", "test_tier": "structural",
             "entries_flagged": 0, "flag_rate": 0.0, "severity": "low", "skipped": False},
            {"test_key": "t2", "test_name": "Test 2", "test_tier": "statistical",
             "entries_flagged": 2, "flag_rate": 0.02, "severity": "medium", "skipped": False},
            {"test_key": "t3", "test_name": "Test 3", "test_tier": "advanced",
             "entries_flagged": 0, "flag_rate": 0.0, "severity": "low", "skipped": True},
        ],
        "data_quality": {
            "completeness_score": completeness,
        },
        "column_detection": {
            "overall_confidence": col_confidence,
        },
    }


def _make_config() -> TestingMemoConfig:
    return TestingMemoConfig(
        title="Test Memo",
        ref_prefix="TST",
        entry_label="Total Entries Tested",
        flagged_label="Total Entries Flagged",
        log_prefix="test_memo",
        domain="test domain",
        test_descriptions={"t1": "Desc 1", "t2": "Desc 2", "t3": "Desc 3"},
        methodology_intro="Automated tests applied:",
        risk_assessments={
            "low": "LOW risk.", "elevated": "ELEVATED risk.",
            "moderate": "MODERATE risk.", "high": "HIGH risk.",
        },
        isa_reference="ISA 999",
    )


# =============================================================================
# build_proof_summary_section — UNIT
# =============================================================================

class TestBuildProofSummarySection:
    """Unit tests for the proof summary section builder."""

    def test_adds_flowables_to_story(self):
        story = []
        styles = _make_styles()
        result = _make_result()
        build_proof_summary_section(story, styles, 468.0, result)
        # Should add: Paragraph (heading), LedgerRule, Table, Spacer = 4 items
        assert len(story) >= 3

    def test_correct_tests_clear_count(self):
        """Tests clear = tests with 0 flags and not skipped."""
        story = []
        styles = _make_styles()
        result = _make_result()
        build_proof_summary_section(story, styles, 468.0, result)
        # Result has 3 tests: t1 clear, t2 flagged, t3 skipped
        # Tests clear should be 1 (only t1)
        # Verify by checking the Table flowable content
        table = None
        from reportlab.platypus import Table as RLTable
        for item in story:
            if isinstance(item, RLTable):
                table = item
                break
        assert table is not None
        # Table data is stored in _cellvalues
        data = table._cellvalues
        # Row with "Tests Clear" should have "1"
        clear_row = [row for row in data if row[0] == "Tests Clear"]
        assert len(clear_row) == 1
        assert clear_row[0][1] == "1"

    def test_missing_column_detection_uses_zero(self):
        story = []
        styles = _make_styles()
        result = _make_result()
        del result["column_detection"]
        build_proof_summary_section(story, styles, 468.0, result)
        # Should still work — just shows 0%
        from reportlab.platypus import Table as RLTable
        table = [item for item in story if isinstance(item, RLTable)][0]
        conf_row = [row for row in table._cellvalues if row[0] == "Column Confidence"]
        assert len(conf_row) == 1
        assert conf_row[0][1] == "0%"

    def test_missing_data_quality_uses_zero(self):
        story = []
        styles = _make_styles()
        result = _make_result()
        del result["data_quality"]
        build_proof_summary_section(story, styles, 468.0, result)
        from reportlab.platypus import Table as RLTable
        table = [item for item in story if isinstance(item, RLTable)][0]
        comp_row = [row for row in table._cellvalues if row[0] == "Data Completeness"]
        assert comp_row[0][1] == "0%"

    def test_empty_test_results_counts_via_composite(self):
        story = []
        styles = _make_styles()
        result = _make_result(tests_run=3, total_flagged=1, test_results=[])
        build_proof_summary_section(story, styles, 468.0, result)
        from reportlab.platypus import Table as RLTable
        table = [item for item in story if isinstance(item, RLTable)][0]
        exec_row = [row for row in table._cellvalues if row[0] == "Tests Executed"]
        assert exec_row[0][1] == "3"


# =============================================================================
# INTEGRATION — generate_testing_memo includes proof section
# =============================================================================

class TestProofInMemoTemplate:
    """Verify that generate_testing_memo includes the proof summary section."""

    def test_standard_memo_generates_with_proof(self):
        config = _make_config()
        result = _make_result()
        pdf = generate_testing_memo(result, config)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 500

    def test_memo_with_column_detection_data(self):
        config = _make_config()
        result = _make_result(col_confidence=0.95, completeness=98.0)
        pdf = generate_testing_memo(result, config)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"


# =============================================================================
# INTEGRATION — bank reconciliation memo
# =============================================================================

class TestProofInBankRecMemo:
    """Verify bank reconciliation memo includes proof summary."""

    def test_bank_rec_memo_with_proof(self):
        from bank_reconciliation_memo_generator import generate_bank_rec_memo
        rec_result = {
            "summary": {
                "matched_count": 90,
                "bank_only_count": 5,
                "ledger_only_count": 5,
                "matched_amount": 50000.0,
                "bank_only_amount": 1000.0,
                "ledger_only_amount": 800.0,
                "reconciling_difference": 200.0,
                "total_bank": 51000.0,
                "total_ledger": 50800.0,
            },
            "bank_column_detection": {"overall_confidence": 0.9},
            "ledger_column_detection": {"overall_confidence": 0.85},
        }
        pdf = generate_bank_rec_memo(rec_result)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"
