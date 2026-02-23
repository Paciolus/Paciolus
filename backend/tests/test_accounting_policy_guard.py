"""Tests for the Accounting Policy Guard — Sprint 378.

Each test class covers one of the 5 rules with synthetic passing and
failing source strings. Tests verify: violation count, rule name,
file path, line number, and message substring.
"""

import ast

import pytest

from guards.checkers.adjustment_gating import check_adjustment_gating_ast
from guards.checkers.contract_fields import check_contract_fields_ast
from guards.checkers.framework_metadata import check_framework_metadata_ast
from guards.checkers.hard_delete import check_hard_delete_source
from guards.checkers.monetary_float import check_monetary_float_ast

# ═══════════════════════════════════════════════════════════════
# Rule 1: no_float_monetary
# ═══════════════════════════════════════════════════════════════


class TestMonetaryFloat:
    """Test Float detection on monetary columns in protected classes."""

    PROTECTED = ["DiagnosticSummary", "ActivityLog"]
    ALLOWLIST = ["current_ratio", "quick_ratio", "composite_score"]

    def test_float_on_monetary_column_flagged(self):
        """Float on a monetary column in a protected class should be flagged."""
        source = """
class DiagnosticSummary(Base):
    __tablename__ = "diagnostic_summaries"
    total_assets = Column(Float, nullable=True)
"""
        tree = ast.parse(source)
        violations = check_monetary_float_ast(tree, "models.py", self.PROTECTED, self.ALLOWLIST)
        assert len(violations) == 1
        v = violations[0]
        assert v.rule == "no_float_monetary"
        assert v.file == "models.py"
        assert v.line == 4
        assert "total_assets" in v.message
        assert "DiagnosticSummary" in v.message
        assert "Numeric(19, 2)" in v.message

    def test_float_on_ratio_column_passes(self):
        """Float on an allowlisted ratio column should pass."""
        source = """
class DiagnosticSummary(Base):
    current_ratio = Column(Float, nullable=True)
    quick_ratio = Column(Float, nullable=True)
    composite_score = Column(Float, nullable=True)
"""
        tree = ast.parse(source)
        violations = check_monetary_float_ast(tree, "models.py", self.PROTECTED, self.ALLOWLIST)
        assert len(violations) == 0

    def test_numeric_column_passes(self):
        """Numeric(19, 2) on a monetary column should pass."""
        source = """
class ActivityLog(Base):
    total_debits = Column(Numeric(19, 2), nullable=False)
    total_credits = Column(Numeric(19, 2), nullable=False)
"""
        tree = ast.parse(source)
        violations = check_monetary_float_ast(tree, "models.py", self.PROTECTED, self.ALLOWLIST)
        assert len(violations) == 0

    def test_non_protected_class_ignored(self):
        """Float in a non-protected class should be ignored."""
        source = """
class SomeOtherModel(Base):
    amount = Column(Float, nullable=True)
"""
        tree = ast.parse(source)
        violations = check_monetary_float_ast(tree, "models.py", self.PROTECTED, self.ALLOWLIST)
        assert len(violations) == 0

    def test_multiple_violations_detected(self):
        """Multiple Float monetary columns should each be flagged."""
        source = """
class DiagnosticSummary(Base):
    total_revenue = Column(Float, nullable=True)
    total_expenses = Column(Float, nullable=True)
    current_ratio = Column(Float, nullable=True)
"""
        tree = ast.parse(source)
        violations = check_monetary_float_ast(tree, "models.py", self.PROTECTED, self.ALLOWLIST)
        # current_ratio is allowlisted, so only 2 violations
        assert len(violations) == 2
        assert violations[0].message.startswith("Column 'total_revenue'")
        assert violations[1].message.startswith("Column 'total_expenses'")


# ═══════════════════════════════════════════════════════════════
# Rule 2: no_hard_delete
# ═══════════════════════════════════════════════════════════════


class TestHardDelete:
    """Test hard-delete detection on protected models."""

    PROTECTED = ["ActivityLog", "DiagnosticSummary", "ToolRun"]

    def test_db_delete_flagged(self):
        """db.delete() in file that imports a protected model should be flagged."""
        source = """from models import ActivityLog, User

def cleanup(db, record):
    db.delete(record)
    db.commit()
"""
        violations = check_hard_delete_source(source, "routes/cleanup.py", self.PROTECTED)
        assert len(violations) >= 1
        v = violations[0]
        assert v.rule == "no_hard_delete"
        assert v.file == "routes/cleanup.py"
        assert v.line == 4
        assert "hard-delete" in v.message.lower() or "soft_delete" in v.message

    def test_db_delete_non_protected_passes(self):
        """db.delete() with only non-protected imports should pass."""
        source = """from models import User, Client

def cleanup(db, record):
    db.delete(record)
    db.commit()
"""
        violations = check_hard_delete_source(source, "routes/users.py", self.PROTECTED)
        assert len(violations) == 0

    def test_soft_delete_passes(self):
        """soft_delete() calls should not trigger violations."""
        source = """from models import ActivityLog
from shared.soft_delete import soft_delete

def archive(db, record):
    soft_delete(db, record, user_id=1, reason="cleanup")
"""
        violations = check_hard_delete_source(source, "routes/cleanup.py", self.PROTECTED)
        assert len(violations) == 0

    def test_query_delete_flagged(self):
        """Query-based .delete() on a protected model should be flagged."""
        source = """from models import ToolRun

def purge_old(db):
    db.query(ToolRun).filter(ToolRun.created_at < cutoff).delete()
"""
        violations = check_hard_delete_source(source, "routes/admin.py", self.PROTECTED)
        assert len(violations) >= 1
        assert any("ToolRun" in v.message for v in violations)

    def test_comment_lines_ignored(self):
        """Comments containing db.delete should not be flagged."""
        source = """from models import ActivityLog

# Previously used db.delete(record) — replaced by soft_delete
def archive(db, record):
    soft_delete(db, record, user_id=1, reason="cleanup")
"""
        violations = check_hard_delete_source(source, "routes/cleanup.py", self.PROTECTED)
        assert len(violations) == 0


# ═══════════════════════════════════════════════════════════════
# Rule 3: revenue_contract_fields
# ═══════════════════════════════════════════════════════════════


class TestContractFields:
    """Test contract field retention in revenue testing engine."""

    REQUIRED = [
        "contract_id", "performance_obligation_id", "recognition_method",
        "contract_modification", "allocation_basis", "obligation_satisfaction_date",
    ]

    def test_all_fields_present_passes(self):
        """All 6 contract fields in both classes should pass."""
        source = """
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RevenueColumnDetection:
    date_column: Optional[str] = None
    contract_id_column: Optional[str] = None
    performance_obligation_id_column: Optional[str] = None
    recognition_method_column: Optional[str] = None
    contract_modification_column: Optional[str] = None
    allocation_basis_column: Optional[str] = None
    obligation_satisfaction_date_column: Optional[str] = None

@dataclass
class RevenueEntry:
    date: Optional[str] = None
    contract_id: Optional[str] = None
    performance_obligation_id: Optional[str] = None
    recognition_method: Optional[str] = None
    contract_modification: Optional[str] = None
    allocation_basis: Optional[str] = None
    obligation_satisfaction_date: Optional[str] = None

@dataclass
class ContractEvidenceLevel:
    level: str
    confidence_modifier: float
    total_contract_fields: int = 6
"""
        tree = ast.parse(source)
        violations = check_contract_fields_ast(
            tree, "revenue_testing_engine.py",
            self.REQUIRED, "RevenueColumnDetection", "RevenueEntry",
            "ContractEvidenceLevel", 6,
        )
        assert len(violations) == 0

    def test_missing_field_flagged(self):
        """Missing a contract field should be flagged with the class line."""
        source = """
@dataclass
class RevenueColumnDetection:
    date_column: Optional[str] = None
    contract_id_column: Optional[str] = None
    # Missing: performance_obligation_id_column

@dataclass
class RevenueEntry:
    date: Optional[str] = None
    contract_id: Optional[str] = None
    performance_obligation_id: Optional[str] = None
    recognition_method: Optional[str] = None
    contract_modification: Optional[str] = None
    allocation_basis: Optional[str] = None
    obligation_satisfaction_date: Optional[str] = None

@dataclass
class ContractEvidenceLevel:
    level: str
    total_contract_fields: int = 6
"""
        tree = ast.parse(source)
        violations = check_contract_fields_ast(
            tree, "revenue_testing_engine.py",
            self.REQUIRED, "RevenueColumnDetection", "RevenueEntry",
            "ContractEvidenceLevel", 6,
        )
        # Missing fields in RevenueColumnDetection: 5 missing (_column suffix)
        detection_violations = [v for v in violations if "RevenueColumnDetection" in v.message]
        assert len(detection_violations) >= 1
        assert any("performance_obligation_id_column" in v.message for v in detection_violations)

    def test_wrong_total_contract_fields_flagged(self):
        """Wrong total_contract_fields default should be flagged."""
        source = """
@dataclass
class RevenueColumnDetection:
    contract_id_column: Optional[str] = None
    performance_obligation_id_column: Optional[str] = None
    recognition_method_column: Optional[str] = None
    contract_modification_column: Optional[str] = None
    allocation_basis_column: Optional[str] = None
    obligation_satisfaction_date_column: Optional[str] = None

@dataclass
class RevenueEntry:
    contract_id: Optional[str] = None
    performance_obligation_id: Optional[str] = None
    recognition_method: Optional[str] = None
    contract_modification: Optional[str] = None
    allocation_basis: Optional[str] = None
    obligation_satisfaction_date: Optional[str] = None

@dataclass
class ContractEvidenceLevel:
    level: str
    total_contract_fields: int = 5
"""
        tree = ast.parse(source)
        violations = check_contract_fields_ast(
            tree, "revenue_testing_engine.py",
            self.REQUIRED, "RevenueColumnDetection", "RevenueEntry",
            "ContractEvidenceLevel", 6,
        )
        total_violations = [v for v in violations if "total_contract_fields" in v.message]
        assert len(total_violations) == 1
        assert "defaults to 5" in total_violations[0].message
        assert "expected 6" in total_violations[0].message

    def test_missing_class_flagged(self):
        """Missing expected class entirely should be flagged."""
        source = """
@dataclass
class SomeOtherClass:
    field: str = "value"
"""
        tree = ast.parse(source)
        violations = check_contract_fields_ast(
            tree, "revenue_testing_engine.py",
            self.REQUIRED, "RevenueColumnDetection", "RevenueEntry",
            "ContractEvidenceLevel", 6,
        )
        assert len(violations) >= 3  # All three classes missing


# ═══════════════════════════════════════════════════════════════
# Rule 4: adjustment_gating
# ═══════════════════════════════════════════════════════════════


class TestAdjustmentGating:
    """Test POSTED terminal and PROPOSED conditional invariants."""

    def test_posted_terminal_passes(self):
        """POSTED mapping to set() should pass."""
        source = """
from enum import Enum

class AdjustmentStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"

VALID_TRANSITIONS = {
    AdjustmentStatus.PROPOSED: {AdjustmentStatus.APPROVED, AdjustmentStatus.REJECTED},
    AdjustmentStatus.APPROVED: {AdjustmentStatus.POSTED, AdjustmentStatus.REJECTED},
    AdjustmentStatus.REJECTED: {AdjustmentStatus.PROPOSED},
    AdjustmentStatus.POSTED: set(),
}

def apply_adjustments(entries, mode="official"):
    valid_statuses = {AdjustmentStatus.APPROVED, AdjustmentStatus.POSTED}
    is_simulation = mode == "simulation"
    if is_simulation:
        valid_statuses.add(AdjustmentStatus.PROPOSED)
    return [e for e in entries if e.status in valid_statuses]
"""
        tree = ast.parse(source)
        violations = check_adjustment_gating_ast(tree, "adjusting_entries.py")
        assert len(violations) == 0

    def test_posted_not_terminal_flagged(self):
        """POSTED with non-empty transitions should be flagged."""
        source = """
from enum import Enum

class AdjustmentStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"

VALID_TRANSITIONS = {
    AdjustmentStatus.PROPOSED: {AdjustmentStatus.APPROVED},
    AdjustmentStatus.APPROVED: {AdjustmentStatus.POSTED},
    AdjustmentStatus.REJECTED: {AdjustmentStatus.PROPOSED},
    AdjustmentStatus.POSTED: {AdjustmentStatus.REJECTED},
}

def apply_adjustments(entries, mode="official"):
    valid_statuses = {AdjustmentStatus.APPROVED, AdjustmentStatus.POSTED}
    if mode == "simulation":
        valid_statuses.add(AdjustmentStatus.PROPOSED)
    return [e for e in entries if e.status in valid_statuses]
"""
        tree = ast.parse(source)
        violations = check_adjustment_gating_ast(tree, "adjusting_entries.py")
        terminal_violations = [v for v in violations if "POSTED" in v.message and "terminal" in v.message.lower()]
        assert len(terminal_violations) == 1
        assert terminal_violations[0].rule == "adjustment_gating"

    def test_proposed_conditional_passes(self):
        """PROPOSED added inside if-block should pass."""
        source = """
VALID_TRANSITIONS = {
    "POSTED": set(),
}

def apply_adjustments(entries, mode="official"):
    valid_statuses = {"APPROVED", "POSTED"}
    if mode == "simulation":
        valid_statuses.add("PROPOSED")
    return entries
"""
        tree = ast.parse(source)
        violations = check_adjustment_gating_ast(tree, "adjusting_entries.py")
        assert len(violations) == 0

    def test_proposed_unconditional_in_set_flagged(self):
        """PROPOSED in the initial valid_statuses set literal should be flagged."""
        source = """
VALID_TRANSITIONS = {
    "POSTED": set(),
}

def apply_adjustments(entries, mode="official"):
    valid_statuses = {"APPROVED", "POSTED", "PROPOSED"}
    return entries
"""
        tree = ast.parse(source)
        violations = check_adjustment_gating_ast(tree, "adjusting_entries.py")
        unconditional_violations = [v for v in violations if "unconditionally" in v.message.lower()]
        assert len(unconditional_violations) == 1


# ═══════════════════════════════════════════════════════════════
# Rule 5: framework_metadata
# ═══════════════════════════════════════════════════════════════


class TestFrameworkMetadata:
    """Test framework_note field presence in comparison classes."""

    def test_framework_note_present_passes(self):
        """Class with framework_note annotated field should pass."""
        source = """
from dataclasses import dataclass
from typing import Optional

@dataclass
class BenchmarkComparison:
    ratio_name: str
    client_value: float
    framework_note: Optional[str] = None
"""
        tree = ast.parse(source)
        violations = check_framework_metadata_ast(tree, "benchmark_engine.py", "BenchmarkComparison")
        assert len(violations) == 0

    def test_framework_note_missing_flagged(self):
        """Class without framework_note should be flagged with class line."""
        source = """
@dataclass
class BenchmarkComparison:
    ratio_name: str
    client_value: float
"""
        tree = ast.parse(source)
        violations = check_framework_metadata_ast(tree, "benchmark_engine.py", "BenchmarkComparison")
        assert len(violations) == 1
        v = violations[0]
        assert v.rule == "framework_metadata"
        assert v.file == "benchmark_engine.py"
        assert v.line == 3  # Class definition line
        assert "BenchmarkComparison" in v.message
        assert "framework_note" in v.message

    def test_class_not_found_flagged(self):
        """Missing class entirely should be flagged."""
        source = """
@dataclass
class SomeOtherClass:
    field: str = "value"
"""
        tree = ast.parse(source)
        violations = check_framework_metadata_ast(tree, "benchmark_engine.py", "BenchmarkComparison")
        assert len(violations) == 1
        assert "not found" in violations[0].message

    def test_multiple_classes_in_same_file(self):
        """Two classes in one file — one with, one without — should flag only the missing one."""
        source = """
from dataclasses import dataclass
from typing import Optional

@dataclass
class MovementSummary:
    prior_label: str
    framework_note: Optional[str] = None

@dataclass
class ThreeWayMovementSummary:
    prior_label: str
    budget_label: str
"""
        tree = ast.parse(source)
        v1 = check_framework_metadata_ast(tree, "multi_period_comparison.py", "MovementSummary")
        v2 = check_framework_metadata_ast(tree, "multi_period_comparison.py", "ThreeWayMovementSummary")
        assert len(v1) == 0
        assert len(v2) == 1
        assert "ThreeWayMovementSummary" in v2[0].message


# ═══════════════════════════════════════════════════════════════
# Integration: full config-driven run
# ═══════════════════════════════════════════════════════════════


class TestIntegration:
    """Test the guard against the actual codebase (sanity check)."""

    def test_guard_passes_on_current_codebase(self):
        """The guard should produce zero violations on the current codebase."""
        from pathlib import Path

        from guards.accounting_policy_guard import load_config, run_checks

        script_dir = Path(__file__).resolve().parent.parent / "guards"
        config_path = script_dir / "accounting_policy.toml"
        backend_root = script_dir.parent

        config = load_config(config_path)
        violations = run_checks(config, backend_root)

        if violations:
            details = "\n".join(f"  [{v.rule}] {v.file}:{v.line} — {v.message}" for v in violations)
            pytest.fail(f"Guard found {len(violations)} violation(s):\n{details}")
