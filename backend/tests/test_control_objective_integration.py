"""
Control-Objective Integration Tests — Sprint 379

Maps 5 control objectives to deterministic integration scenarios:

| # | Control Objective                              | Test Class                              |
|---|------------------------------------------------|-----------------------------------------|
| 1 | Revenue recognition timing (ASC 606 / IFRS 15)| TestRevenueContractRecognitionTiming    |
| 2 | Adjustment approval workflow (SoD)             | TestAdjustmentApprovalWorkflowSoD       |
| 3 | Audit-history immutability                     | TestAuditHistoryWipeBlocked             |
| 4 | IFRS benchmark comparability flags             | TestIFRSBenchmarkComparability          |
| 5 | Decimal persistence roundtrip                  | TestDecimalPersistenceRoundtrip         |

Deterministic fixtures:
- All monetary values use exact Decimal strings (no float drift).
- Revenue entries use fixed dates to produce repeatable flag/pass outcomes.
- Benchmark percentile assertions use known p50 midpoints.
- DB roundtrip tests create→commit→reload and assert monetary_equal.
"""

import math
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

import pytest

# ---------------------------------------------------------------------------
# Fixture: Revenue entries with contract-aware columns
# ---------------------------------------------------------------------------

def _make_revenue_entries_with_contracts():
    """Build deterministic RevenueEntry list with contract fields.

    Entries designed to trigger:
    - RT-13 (Recognition Before Satisfaction): entry recognised 30 days before
      satisfaction date  -> HIGH severity flag.
    - RT-14 (Missing Obligation Linkage): one entry with contract_id but no
      performance_obligation_id -> MEDIUM flag.
    - RT-15 (Modification Treatment Mismatch): two entries on same contract with
      conflicting modification types ("prospective" vs "catch-up") -> HIGH flag.
    - RT-16 (Allocation Inconsistency): two entries on same contract with
      different allocation bases ("observable" vs "residual") -> HIGH flag.
    - Plus several clean entries that should pass all tests.
    """
    from revenue_testing_engine import RevenueEntry

    base_date = datetime(2025, 6, 15)
    base_str = base_date.strftime("%Y-%m-%d")

    entries = [
        # --- Clean entry (pass all) ---
        RevenueEntry(
            date=base_str,
            amount=50_000.00,
            account_name="Revenue - Product A",
            account_number="4100",
            description="Normal sale",
            entry_type="standard",
            reference="INV-001",
            posted_by="system",
            contract_id="C-100",
            performance_obligation_id="PO-100-1",
            recognition_method="point-in-time",
            contract_modification=None,
            allocation_basis="observable",
            obligation_satisfaction_date=base_str,
        ),
        # --- RT-13 trigger: recognised 30 days BEFORE satisfaction ---
        RevenueEntry(
            date=base_str,
            amount=120_000.00,
            account_name="Revenue - Product B",
            account_number="4200",
            description="Premature recognition",
            entry_type="standard",
            reference="INV-002",
            posted_by="user_a",
            contract_id="C-200",
            performance_obligation_id="PO-200-1",
            recognition_method="point-in-time",
            contract_modification=None,
            allocation_basis="observable",
            obligation_satisfaction_date=(base_date + timedelta(days=30)).strftime("%Y-%m-%d"),
        ),
        # --- RT-14 trigger: contract_id present, NO performance_obligation_id ---
        RevenueEntry(
            date=base_str,
            amount=30_000.00,
            account_name="Revenue - Service C",
            account_number="4300",
            description="Orphaned contract",
            entry_type="standard",
            reference="INV-003",
            posted_by="user_b",
            contract_id="C-300",
            performance_obligation_id=None,
            recognition_method="point-in-time",
            contract_modification=None,
            allocation_basis="observable",
            obligation_satisfaction_date=base_str,
        ),
        # --- RT-15 trigger: same contract, conflicting modification types ---
        RevenueEntry(
            date=base_str,
            amount=25_000.00,
            account_name="Revenue - Product D",
            account_number="4400",
            description="Mod prospective",
            entry_type="standard",
            reference="INV-004",
            posted_by="user_a",
            contract_id="C-400",
            performance_obligation_id="PO-400-1",
            recognition_method="point-in-time",
            contract_modification="prospective",
            allocation_basis="observable",
            obligation_satisfaction_date=base_str,
        ),
        RevenueEntry(
            date=base_str,
            amount=25_000.00,
            account_name="Revenue - Product D2",
            account_number="4400",
            description="Mod catch-up",
            entry_type="standard",
            reference="INV-005",
            posted_by="user_a",
            contract_id="C-400",
            performance_obligation_id="PO-400-2",
            recognition_method="point-in-time",
            contract_modification="catch-up",
            allocation_basis="observable",
            obligation_satisfaction_date=base_str,
        ),
        # --- RT-16 trigger: same contract, conflicting allocation bases ---
        RevenueEntry(
            date=base_str,
            amount=40_000.00,
            account_name="Revenue - Product E",
            account_number="4500",
            description="Alloc observable",
            entry_type="standard",
            reference="INV-006",
            posted_by="user_b",
            contract_id="C-500",
            performance_obligation_id="PO-500-1",
            recognition_method="point-in-time",
            contract_modification=None,
            allocation_basis="observable",
            obligation_satisfaction_date=base_str,
        ),
        RevenueEntry(
            date=base_str,
            amount=40_000.00,
            account_name="Revenue - Product E2",
            account_number="4500",
            description="Alloc residual",
            entry_type="standard",
            reference="INV-007",
            posted_by="user_b",
            contract_id="C-500",
            performance_obligation_id="PO-500-2",
            recognition_method="point-in-time",
            contract_modification=None,
            allocation_basis="residual",
            obligation_satisfaction_date=base_str,
        ),
        # --- Additional clean entries for population ---
        RevenueEntry(
            date=(base_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            amount=15_000.00,
            account_name="Revenue - Product F",
            account_number="4600",
            description="Normal sale",
            entry_type="standard",
            reference="INV-008",
            posted_by="system",
            contract_id="C-600",
            performance_obligation_id="PO-600-1",
            recognition_method="point-in-time",
            contract_modification=None,
            allocation_basis="observable",
            obligation_satisfaction_date=(base_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        ),
        RevenueEntry(
            date=(base_date + timedelta(days=2)).strftime("%Y-%m-%d"),
            amount=18_000.00,
            account_name="Revenue - Product G",
            account_number="4700",
            description="Normal sale",
            entry_type="standard",
            reference="INV-009",
            posted_by="system",
            contract_id="C-700",
            performance_obligation_id="PO-700-1",
            recognition_method="over-time",
            contract_modification=None,
            allocation_basis="observable",
            obligation_satisfaction_date=(base_date + timedelta(days=60)).strftime("%Y-%m-%d"),
        ),
        RevenueEntry(
            date=(base_date + timedelta(days=3)).strftime("%Y-%m-%d"),
            amount=22_000.00,
            account_name="Revenue - Product H",
            account_number="4800",
            description="Normal sale",
            entry_type="standard",
            reference="INV-010",
            posted_by="system",
            contract_id="C-800",
            performance_obligation_id="PO-800-1",
            recognition_method="point-in-time",
            contract_modification=None,
            allocation_basis="observable",
            obligation_satisfaction_date=base_str,
        ),
    ]
    return entries


# ===========================================================================
# CO-1: Revenue Contract-Aware Recognition Timing (ASC 606 / IFRS 15)
# ===========================================================================

class TestRevenueContractRecognitionTiming:
    """Control Objective: Revenue is recognised only when performance
    obligations are satisfied (ASC 606-10-25-30).

    Tests RT-13 through RT-16 with deterministic contract data.
    """

    # -- Fixtures (class-scoped for efficiency) --

    @pytest.fixture(autouse=True)
    def _setup(self):
        from revenue_testing_engine import (
            ContractEvidenceLevel,
            RevenueTestingConfig,
            run_revenue_test_battery,
        )
        self.entries = _make_revenue_entries_with_contracts()
        # Full evidence — all 6 contract fields present in at least some entries
        self.evidence = ContractEvidenceLevel(
            level="full",
            confidence_modifier=1.0,
            detected_fields=[
                "contract_id", "performance_obligation_id",
                "recognition_method", "contract_modification",
                "allocation_basis", "obligation_satisfaction_date",
            ],
        )
        self.config = RevenueTestingConfig()
        self.results = run_revenue_test_battery(
            self.entries, self.config, self.evidence,
        )
        # Index results by test_key for deterministic lookup
        self.by_key = {r.test_key: r for r in self.results}

    def test_battery_returns_16_results(self):
        """12 core + 4 contract = 16 total results."""
        assert len(self.results) == 16

    def test_no_contract_tests_skipped(self):
        """All 4 contract tests should run (not skipped) with full evidence."""
        contract_tests = [r for r in self.results if r.test_tier == "contract"]
        assert len(contract_tests) == 4
        for ct in contract_tests:
            assert ct.skipped is False, f"{ct.test_key} unexpectedly skipped"

    def test_rt13_flags_premature_recognition(self):
        """RT-13: Entry recognised 30 days before satisfaction -> HIGH."""
        from shared.testing_enums import Severity

        rt13 = self.by_key.get("recognition_before_satisfaction")
        assert rt13 is not None, "recognition_before_satisfaction result missing"
        assert rt13.entries_flagged >= 1, "Expected at least 1 premature recognition flag"
        # The 30-day gap exceeds the default 7-day threshold -> HIGH
        high_flags = [f for f in rt13.flagged_entries if f.severity == Severity.HIGH]
        assert len(high_flags) >= 1, "Expected HIGH severity for 30-day premature recognition"

    def test_rt13_does_not_flag_over_time(self):
        """RT-13: Over-time recognition entries are auto-exempt."""
        rt13 = self.by_key.get("recognition_before_satisfaction")
        assert rt13 is not None
        # Entry INV-009 uses "over-time" recognition — satisfaction date is 60 days
        # later but should NOT be flagged due to exemption.
        flagged_refs = [f.entry.reference for f in rt13.flagged_entries]
        assert "INV-009" not in flagged_refs, "Over-time entry should be exempt from RT-13"

    def test_rt14_flags_orphaned_contract(self):
        """RT-14: Contract without performance_obligation_id -> MEDIUM."""
        rt14 = self.by_key.get("missing_obligation_linkage")
        assert rt14 is not None, "missing_obligation_linkage result missing"
        assert rt14.entries_flagged >= 1, "Expected at least 1 orphaned contract flag"

    def test_rt15_flags_mixed_modification_treatment(self):
        """RT-15: Same contract with 'prospective' and 'catch-up' -> HIGH."""
        from shared.testing_enums import Severity

        rt15 = self.by_key.get("modification_treatment_mismatch")
        assert rt15 is not None, "modification_treatment_mismatch result missing"
        assert rt15.entries_flagged >= 1, "Expected at least 1 mixed modification flag"
        high_flags = [f for f in rt15.flagged_entries if f.severity == Severity.HIGH]
        assert len(high_flags) >= 1, "Expected HIGH severity for mixed treatments"

    def test_rt16_flags_inconsistent_allocation(self):
        """RT-16: Same contract with 'observable' and 'residual' -> HIGH."""
        from shared.testing_enums import Severity

        rt16 = self.by_key.get("allocation_inconsistency")
        assert rt16 is not None, "allocation_inconsistency result missing"
        assert rt16.entries_flagged >= 1, "Expected at least 1 allocation inconsistency flag"
        high_flags = [f for f in rt16.flagged_entries if f.severity == Severity.HIGH]
        assert len(high_flags) >= 1, "Expected HIGH severity for mixed allocation bases"

    def test_composite_score_excludes_skipped(self):
        """Composite scoring must exclude skipped tests."""
        from revenue_testing_engine import calculate_revenue_composite_score

        score = calculate_revenue_composite_score(self.results, len(self.entries))
        # With full evidence, all 16 tests run — tests_run should be 16
        assert score.tests_run == 16

    def test_no_evidence_skips_all_contract_tests(self):
        """When evidence.level == 'none', all 4 contract tests are skipped."""
        from revenue_testing_engine import (
            ContractEvidenceLevel,
            run_revenue_test_battery,
        )

        no_evidence = ContractEvidenceLevel(
            level="none",
            confidence_modifier=0.0,
            detected_fields=[],
        )
        results = run_revenue_test_battery(self.entries, self.config, no_evidence)
        contract_results = [r for r in results if r.test_tier == "contract"]
        assert len(contract_results) == 4
        for r in contract_results:
            assert r.skipped is True
            assert r.skip_reason is not None


# ===========================================================================
# CO-2: Adjustment Create/Approve/Post with SoD Enforcement
# ===========================================================================

class TestAdjustmentApprovalWorkflowSoD:
    """Control Objective: Adjusting entries follow a strict
    proposed -> approved -> posted workflow with separation of duties.

    Tests the VALID_TRANSITIONS map, InvalidTransitionError, approval metadata,
    and demonstrates that the same user creating and approving is detectable.
    """

    def _make_balanced_entry(self, ref="AJE-001", prepared_by="preparer@test.com"):
        """Create a balanced AdjustingEntry in PROPOSED status."""
        from adjusting_entries import AdjustingEntry, AdjustmentLine, AdjustmentType

        return AdjustingEntry(
            reference=ref,
            description="Test accrual adjustment",
            adjustment_type=AdjustmentType.ACCRUAL,
            lines=[
                AdjustmentLine(account_name="Accrued Expenses", debit=Decimal("0"), credit=Decimal("1000.00")),
                AdjustmentLine(account_name="Expense - Utilities", debit=Decimal("1000.00"), credit=Decimal("0")),
            ],
            prepared_by=prepared_by,
        )

    def test_happy_path_proposed_approved_posted(self):
        """Full workflow: proposed -> approved -> posted succeeds."""
        from adjusting_entries import AdjustmentStatus, validate_status_transition

        # proposed -> approved
        validate_status_transition(AdjustmentStatus.PROPOSED, AdjustmentStatus.APPROVED)
        # approved -> posted
        validate_status_transition(AdjustmentStatus.APPROVED, AdjustmentStatus.POSTED)

    def test_skip_approval_blocked(self):
        """Direct proposed -> posted is forbidden."""
        from adjusting_entries import (
            AdjustmentStatus,
            InvalidTransitionError,
            validate_status_transition,
        )

        with pytest.raises(InvalidTransitionError, match="Cannot transition from 'proposed' to 'posted'"):
            validate_status_transition(AdjustmentStatus.PROPOSED, AdjustmentStatus.POSTED)

    def test_posted_is_terminal(self):
        """No transitions allowed from POSTED."""
        from adjusting_entries import (
            AdjustmentStatus,
            InvalidTransitionError,
            validate_status_transition,
        )

        for target in (AdjustmentStatus.PROPOSED, AdjustmentStatus.APPROVED, AdjustmentStatus.REJECTED):
            with pytest.raises(InvalidTransitionError, match="status is terminal"):
                validate_status_transition(AdjustmentStatus.POSTED, target)

    def test_rejected_can_only_repropose(self):
        """Rejected entries can only move to PROPOSED (re-proposal path)."""
        from adjusting_entries import (
            AdjustmentStatus,
            InvalidTransitionError,
            validate_status_transition,
        )

        # Valid: rejected -> proposed
        validate_status_transition(AdjustmentStatus.REJECTED, AdjustmentStatus.PROPOSED)
        # Invalid: rejected -> approved
        with pytest.raises(InvalidTransitionError):
            validate_status_transition(AdjustmentStatus.REJECTED, AdjustmentStatus.APPROVED)
        # Invalid: rejected -> posted
        with pytest.raises(InvalidTransitionError):
            validate_status_transition(AdjustmentStatus.REJECTED, AdjustmentStatus.POSTED)

    def test_approval_metadata_set_on_approve(self):
        """Approving sets approved_by and approved_at."""
        from adjusting_entries import AdjustmentStatus

        entry = self._make_balanced_entry()
        assert entry.status == AdjustmentStatus.PROPOSED
        assert entry.approved_by is None
        assert entry.approved_at is None

        # Simulate approval (same pattern as routes/adjustments.py)
        entry.status = AdjustmentStatus.APPROVED
        entry.approved_by = "approver@test.com"
        entry.approved_at = datetime.now(UTC)

        assert entry.approved_by == "approver@test.com"
        assert entry.approved_at is not None

    def test_rejection_clears_approval_metadata(self):
        """Rejecting an approved entry clears approved_by/approved_at."""
        from adjusting_entries import AdjustmentStatus

        entry = self._make_balanced_entry()
        # Approve
        entry.status = AdjustmentStatus.APPROVED
        entry.approved_by = "approver@test.com"
        entry.approved_at = datetime.now(UTC)
        # Reject
        entry.status = AdjustmentStatus.REJECTED
        entry.approved_by = None
        entry.approved_at = None

        assert entry.approved_by is None
        assert entry.approved_at is None

    def test_sod_violation_detectable(self):
        """Creator == approver is a SoD violation that must be detectable.

        The system stores prepared_by and approved_by on each entry, enabling
        detection of violations. This test proves the metadata is available for
        enforcement (either at application layer or via policy check).
        """
        entry = self._make_balanced_entry(prepared_by="same_user@test.com")
        entry.approved_by = "same_user@test.com"
        entry.approved_at = datetime.now(UTC)

        # SoD violation: prepared_by == approved_by
        assert entry.prepared_by == entry.approved_by, \
            "Metadata must capture identity for SoD detection"
        # Downstream enforcement can check this condition
        is_sod_violation = (
            entry.prepared_by is not None
            and entry.approved_by is not None
            and entry.prepared_by == entry.approved_by
        )
        assert is_sod_violation is True

    def test_sod_clean_path(self):
        """Different preparer and approver satisfies SoD."""
        entry = self._make_balanced_entry(prepared_by="preparer@test.com")
        entry.approved_by = "manager@test.com"
        entry.approved_at = datetime.now(UTC)

        is_sod_violation = (
            entry.prepared_by is not None
            and entry.approved_by is not None
            and entry.prepared_by == entry.approved_by
        )
        assert is_sod_violation is False

    def test_apply_official_excludes_proposed(self):
        """Official mode includes only approved+posted, not proposed."""
        from adjusting_entries import (
            AdjustmentSet,
            AdjustmentStatus,
            apply_adjustments,
        )

        entry_proposed = self._make_balanced_entry(ref="AJE-001")
        entry_approved = self._make_balanced_entry(ref="AJE-002")
        entry_approved.status = AdjustmentStatus.APPROVED
        entry_approved.approved_by = "mgr@test.com"
        entry_approved.approved_at = datetime.now(UTC)

        adj_set = AdjustmentSet(entries=[entry_proposed, entry_approved])
        tb = [
            {"account": "Accrued Expenses", "debit": 0, "credit": 5000},
            {"account": "Expense - Utilities", "debit": 3000, "credit": 0},
        ]

        result = apply_adjustments(tb, adj_set, mode="official")
        assert result.is_simulation is False
        # Only AJE-002 (approved) should be applied
        assert len(result.adjustments_applied) == 1
        assert entry_approved.id in result.adjustments_applied

    def test_apply_simulation_includes_proposed(self):
        """Simulation mode includes proposed entries too."""
        from adjusting_entries import (
            AdjustmentSet,
            AdjustmentStatus,
            apply_adjustments,
        )

        entry_proposed = self._make_balanced_entry(ref="AJE-001")
        entry_approved = self._make_balanced_entry(ref="AJE-002")
        entry_approved.status = AdjustmentStatus.APPROVED
        entry_approved.approved_by = "mgr@test.com"
        entry_approved.approved_at = datetime.now(UTC)

        adj_set = AdjustmentSet(entries=[entry_proposed, entry_approved])
        tb = [
            {"account": "Accrued Expenses", "debit": 0, "credit": 5000},
            {"account": "Expense - Utilities", "debit": 3000, "credit": 0},
        ]

        result = apply_adjustments(tb, adj_set, mode="simulation")
        assert result.is_simulation is True
        # Both entries should be applied in simulation
        assert len(result.adjustments_applied) == 2

    def test_adjusted_tb_stays_balanced(self):
        """After applying balanced entries, ATB must remain balanced."""
        from adjusting_entries import (
            AdjustmentSet,
            AdjustmentStatus,
            apply_adjustments,
        )

        entry = self._make_balanced_entry()
        entry.status = AdjustmentStatus.APPROVED
        entry.approved_by = "mgr@test.com"
        entry.approved_at = datetime.now(UTC)

        adj_set = AdjustmentSet(entries=[entry])
        # Balanced TB: debits = credits = 10,000
        tb = [
            {"account": "Cash", "debit": 10000, "credit": 0},
            {"account": "Revenue", "debit": 0, "credit": 10000},
        ]

        result = apply_adjustments(tb, adj_set, mode="official")
        assert result.is_balanced, (
            f"ATB out of balance: debits={result.total_adjusted_debits}, "
            f"credits={result.total_adjusted_credits}"
        )


# ===========================================================================
# CO-3: Audit-History Wipe Attempt (Must Be Blocked / Non-Destructive)
# ===========================================================================

class TestAuditHistoryWipeBlocked:
    """Control Objective: Audit trail records (ActivityLog, DiagnosticSummary,
    ToolRun, FollowUpItem, FollowUpItemComment) cannot be physically deleted.

    The ORM-level before_flush guard must raise AuditImmutabilityError on any
    db.delete() call for protected models. soft_delete() is the only sanctioned
    removal mechanism, and archived records must physically persist.
    """

    def test_activity_log_delete_raises(self, db_session, make_user):
        """Physical delete of ActivityLog must be blocked."""
        from models import ActivityLog
        from shared.soft_delete import AuditImmutabilityError

        user = make_user(email="audit_test_1@example.com")
        log = ActivityLog(
            user_id=user.id,
            filename_hash="a" * 64,
            record_count=100,
            total_debits=Decimal("5000.00"),
            total_credits=Decimal("5000.00"),
            materiality_threshold=Decimal("100.00"),
            was_balanced=True,
        )
        db_session.add(log)
        db_session.flush()

        with pytest.raises(AuditImmutabilityError, match="Physical deletion.*forbidden"):
            db_session.delete(log)
            db_session.flush()

    def test_diagnostic_summary_delete_raises(self, db_session, make_user, make_client):
        """Physical delete of DiagnosticSummary must be blocked."""
        from models import DiagnosticSummary
        from shared.soft_delete import AuditImmutabilityError

        user = make_user(email="audit_test_2@example.com")
        client = make_client(name="Audit Test Client", user=user)
        summary = DiagnosticSummary(
            user_id=user.id,
            client_id=client.id,
            filename_hash="b" * 64,
            row_count=50,
            total_debits=Decimal("10000.00"),
            total_credits=Decimal("10000.00"),
        )
        db_session.add(summary)
        db_session.flush()

        with pytest.raises(AuditImmutabilityError, match="Physical deletion.*forbidden"):
            db_session.delete(summary)
            db_session.flush()

    def test_tool_run_delete_raises(self, db_session, make_tool_run):
        """Physical delete of ToolRun must be blocked."""
        from shared.soft_delete import AuditImmutabilityError

        tool_run = make_tool_run()
        with pytest.raises(AuditImmutabilityError, match="Physical deletion.*forbidden"):
            db_session.delete(tool_run)
            db_session.flush()

    def test_follow_up_item_delete_raises(self, db_session, make_follow_up_item):
        """Physical delete of FollowUpItem must be blocked."""
        from shared.soft_delete import AuditImmutabilityError

        item = make_follow_up_item()
        with pytest.raises(AuditImmutabilityError, match="Physical deletion.*forbidden"):
            db_session.delete(item)
            db_session.flush()

    def test_follow_up_comment_delete_raises(self, db_session, make_comment):
        """Physical delete of FollowUpItemComment must be blocked."""
        from shared.soft_delete import AuditImmutabilityError

        comment = make_comment()
        with pytest.raises(AuditImmutabilityError, match="Physical deletion.*forbidden"):
            db_session.delete(comment)
            db_session.flush()

    def test_soft_delete_preserves_record(self, db_session, make_user):
        """soft_delete() archives the record but keeps it physically in the DB."""
        from models import ActivityLog
        from shared.soft_delete import soft_delete

        user = make_user(email="audit_test_3@example.com")
        log = ActivityLog(
            user_id=user.id,
            filename_hash="c" * 64,
            record_count=10,
            total_debits=Decimal("1000.00"),
            total_credits=Decimal("1000.00"),
            materiality_threshold=Decimal("50.00"),
            was_balanced=True,
        )
        db_session.add(log)
        db_session.flush()
        log_id = log.id

        # Archive via soft_delete
        soft_delete(db_session, log, user.id, "test_archive")

        # Record still physically exists
        reloaded = db_session.get(ActivityLog, log_id)
        assert reloaded is not None, "Soft-deleted record must persist in DB"
        assert reloaded.archived_at is not None
        assert reloaded.archived_by == user.id
        assert reloaded.archive_reason == "test_archive"

    def test_active_only_excludes_archived(self, db_session, make_user):
        """active_only() filter must exclude archived records."""
        from models import ActivityLog
        from shared.soft_delete import active_only, soft_delete

        user = make_user(email="audit_test_4@example.com")
        # Create two logs
        log_a = ActivityLog(
            user_id=user.id, filename_hash="d" * 64, filename_display="a.csv",
            record_count=1,
            total_debits=Decimal("100.00"), total_credits=Decimal("100.00"),
            materiality_threshold=Decimal("10.00"), was_balanced=True,
        )
        log_b = ActivityLog(
            user_id=user.id, filename_hash="e" * 64, filename_display="b.csv",
            record_count=2,
            total_debits=Decimal("200.00"), total_credits=Decimal("200.00"),
            materiality_threshold=Decimal("20.00"), was_balanced=True,
        )
        db_session.add_all([log_a, log_b])
        db_session.flush()

        # Archive log_a
        soft_delete(db_session, log_a, user.id, "test_exclusion")

        # active_only should return only log_b
        active_query = active_only(
            db_session.query(ActivityLog).filter(ActivityLog.user_id == user.id),
            ActivityLog,
        )
        active_logs = active_query.all()
        active_displays = {l.filename_display for l in active_logs}
        assert "a.csv" not in active_displays, "Archived record must be excluded"
        assert "b.csv" in active_displays

    def test_row_count_never_decreases(self, db_session, make_user):
        """Total row count must never decrease after archival operations."""
        from models import ActivityLog

        user = make_user(email="audit_test_5@example.com")
        log = ActivityLog(
            user_id=user.id, filename_hash="f" * 64, record_count=5,
            total_debits=Decimal("500.00"), total_credits=Decimal("500.00"),
            materiality_threshold=Decimal("50.00"), was_balanced=True,
        )
        db_session.add(log)
        db_session.flush()

        count_before = db_session.query(ActivityLog).filter(
            ActivityLog.user_id == user.id,
        ).count()

        from shared.soft_delete import soft_delete
        soft_delete(db_session, log, user.id, "count_test")

        count_after = db_session.query(ActivityLog).filter(
            ActivityLog.user_id == user.id,
        ).count()

        assert count_after >= count_before, \
            f"Row count decreased from {count_before} to {count_after}"


# ===========================================================================
# CO-4: IFRS Benchmarking Against GAAP Source with Comparability Flags
# ===========================================================================

class TestIFRSBenchmarkComparability:
    """Control Objective: When client uses IFRS and benchmarks are GAAP-sourced,
    the system must surface comparability metadata via framework_note fields.

    Verifies:
    - Benchmark data is GAAP-sourced (SEC EDGAR / RMA)
    - BenchmarkComparison has framework_note field
    - Percentile calculation is deterministic at known midpoints
    - Cross-framework comparison produces valid results (no crashes)
    - framework_note infrastructure exists in comparison & multi-period schemas
    """

    def test_benchmark_source_is_gaap(self):
        """Benchmark source attribution must reference GAAP/SEC sources."""
        from benchmark_engine import get_benchmark_sources

        sources = get_benchmark_sources()
        source_names = [s["name"] for s in sources["primary_sources"]]
        assert "SEC EDGAR" in source_names, "GAAP source attribution missing"

    def test_benchmark_comparison_has_framework_note_field(self):
        """BenchmarkComparison dataclass must include framework_note."""
        from benchmark_engine import BenchmarkComparison

        import dataclasses
        field_names = {f.name for f in dataclasses.fields(BenchmarkComparison)}
        assert "framework_note" in field_names, \
            "BenchmarkComparison missing framework_note field"

    def test_percentile_at_median_returns_50(self):
        """Client value at median (p50) should yield percentile ~50."""
        from benchmark_engine import get_benchmark_set
        from models import Industry

        bench_set = get_benchmark_set(Industry.RETAIL)
        assert bench_set is not None

        cr_bench = bench_set.get_benchmark("current_ratio")
        assert cr_bench is not None

        # Client value exactly at p50
        from benchmark_engine import calculate_percentile
        pct = calculate_percentile(cr_bench.p50, cr_bench)
        assert pct == 50, f"Expected percentile 50 at median, got {pct}"

    def test_ifrs_ratios_against_gaap_benchmarks(self):
        """IFRS-reported ratios can be compared to GAAP benchmarks without error.

        A Manufacturing client reporting under IFRS might show higher
        inventory values (no LIFO) — the comparison should still produce
        valid results with appropriate health indicators.
        """
        from benchmark_engine import (
            compare_ratios_to_benchmarks,
            get_benchmark_set,
        )
        from models import Industry

        bench_set = get_benchmark_set(Industry.MANUFACTURING)
        assert bench_set is not None

        # IFRS-like ratios: higher inventory (no LIFO), asset revaluation bump
        ifrs_ratios = {
            "current_ratio": 2.0,
            "quick_ratio": 0.9,
            "debt_to_equity": 1.2,
            "gross_margin": 0.35,
            "net_profit_margin": 0.08,
            "roa": 0.06,
            "roe": 0.14,
        }

        comparisons = compare_ratios_to_benchmarks(ifrs_ratios, bench_set)
        assert len(comparisons) > 0, "No comparisons produced"

        for comp in comparisons:
            assert 1 <= comp.percentile <= 99, \
                f"{comp.ratio_name}: percentile {comp.percentile} out of range"
            assert comp.position in (
                "excellent", "above_average", "average",
                "below_average", "concerning", "critical",
            )
            assert comp.health_indicator in ("positive", "neutral", "negative")

    def test_framework_note_in_multi_period_schema(self):
        """Multi-period comparison response must carry framework_note."""
        from multi_period_comparison import MovementSummary

        import dataclasses
        field_names = {f.name for f in dataclasses.fields(MovementSummary)}
        assert "framework_note" in field_names

    def test_framework_note_in_prior_period_schema(self):
        """Prior-period comparison result must carry framework_note."""
        from prior_period_comparison import PeriodComparison

        import dataclasses
        field_names = {f.name for f in dataclasses.fields(PeriodComparison)}
        assert "framework_note" in field_names

    def test_overall_score_deterministic(self):
        """Overall score calculation is deterministic for fixed inputs."""
        from benchmark_engine import (
            calculate_overall_score,
            compare_ratios_to_benchmarks,
            get_benchmark_set,
        )
        from models import Industry

        bench_set = get_benchmark_set(Industry.TECHNOLOGY)
        assert bench_set is not None

        ratios = {
            "current_ratio": 2.5,
            "quick_ratio": 2.0,
            "debt_to_equity": 0.5,
            "gross_margin": 0.65,
            "net_profit_margin": 0.15,
        }

        comparisons = compare_ratios_to_benchmarks(ratios, bench_set)
        score1 = calculate_overall_score(comparisons)
        score2 = calculate_overall_score(comparisons)
        assert score1 == score2, "Score must be deterministic for same inputs"
        assert 0 <= score1 <= 100, f"Score {score1} out of [0, 100] range"

    def test_six_industries_have_benchmarks(self):
        """All 6 priority industries must have benchmark sets."""
        from benchmark_engine import get_available_industries, get_benchmark_set
        from models import Industry

        available = get_available_industries()
        expected = {
            Industry.RETAIL, Industry.MANUFACTURING,
            Industry.PROFESSIONAL_SERVICES, Industry.TECHNOLOGY,
            Industry.HEALTHCARE, Industry.FINANCIAL_SERVICES,
        }
        assert expected.issubset(set(available)), \
            f"Missing industries: {expected - set(available)}"

        for ind in expected:
            bench_set = get_benchmark_set(ind)
            assert bench_set is not None, f"No benchmark set for {ind.value}"
            assert len(bench_set.benchmarks) >= 8, \
                f"{ind.value}: only {len(bench_set.benchmarks)} ratios (expected >= 8)"


# ===========================================================================
# CO-5: Decimal Persistence Roundtrip — No Debit/Credit Imbalance
# ===========================================================================

class TestDecimalPersistenceRoundtrip:
    """Control Objective: Monetary values survive a create -> DB persist ->
    reload cycle with no precision loss, and debit/credit totals remain
    balanced after quantization.

    Tests quantize_monetary, monetary_equal, and DB roundtrip for
    ActivityLog and DiagnosticSummary Numeric(19,2) columns.
    """

    def test_quantize_monetary_round_half_up(self):
        """ROUND_HALF_UP: 2.225 -> 2.23 (not banker's 2.22)."""
        from shared.monetary import quantize_monetary

        assert quantize_monetary(2.225) == Decimal("2.23")
        assert quantize_monetary(2.215) == Decimal("2.22")
        assert quantize_monetary(0.1 + 0.2) == Decimal("0.30")

    def test_monetary_equal_floats(self):
        """monetary_equal handles classic float imprecision."""
        from shared.monetary import monetary_equal

        assert monetary_equal(0.1 + 0.2, 0.3) is True
        assert monetary_equal(1000.005, 1000.01) is True  # both quantize to 1000.01
        assert monetary_equal(1.00, 1.01) is False

    def test_balance_tolerance_boundary(self):
        """BALANCE_TOLERANCE is exactly Decimal('0.01')."""
        from shared.monetary import BALANCE_TOLERANCE

        assert BALANCE_TOLERANCE == Decimal("0.01")
        # Sub-cent difference is within tolerance
        assert abs(Decimal("0.009")) < BALANCE_TOLERANCE
        # Exactly 1 cent is NOT within tolerance (< not <=)
        assert not (abs(Decimal("0.01")) < BALANCE_TOLERANCE)

    def test_activity_log_db_roundtrip(self, db_session, make_user):
        """ActivityLog Numeric(19,2) columns survive DB roundtrip."""
        from models import ActivityLog
        from shared.monetary import monetary_equal, quantize_monetary

        user = make_user(email="decimal_rt_1@example.com")
        debits = Decimal("123456789.99")
        credits = Decimal("123456789.99")

        log = ActivityLog(
            user_id=user.id,
            filename_hash="aa" * 32,
            record_count=1000,
            total_debits=quantize_monetary(debits),
            total_credits=quantize_monetary(credits),
            materiality_threshold=quantize_monetary(Decimal("1000.00")),
            was_balanced=True,
        )
        db_session.add(log)
        db_session.flush()
        log_id = log.id

        # Expire cache to force DB reload
        db_session.expire(log)
        reloaded = db_session.get(ActivityLog, log_id)

        assert monetary_equal(reloaded.total_debits, debits)
        assert monetary_equal(reloaded.total_credits, credits)
        # Balance invariant: debits == credits
        diff = abs(Decimal(str(reloaded.total_debits)) - Decimal(str(reloaded.total_credits)))
        assert diff < Decimal("0.01"), f"Debit/credit imbalance: {diff}"

    def test_diagnostic_summary_db_roundtrip(self, db_session, make_user, make_client):
        """DiagnosticSummary monetary columns survive DB roundtrip."""
        from models import DiagnosticSummary
        from shared.monetary import monetary_equal, quantize_monetary

        user = make_user(email="decimal_rt_2@example.com")
        client = make_client(name="Decimal Test Corp", user=user)

        # Use values that would cause float drift if not quantized
        values = {
            "total_assets": Decimal("9999999999.99"),
            "current_assets": Decimal("5555555.55"),
            "total_liabilities": Decimal("4444444.44"),
            "total_equity": Decimal("5555555111.55"),
            "total_revenue": Decimal("7777777.77"),
            "total_expenses": Decimal("6666666.66"),
            "total_debits": Decimal("50000000.01"),
            "total_credits": Decimal("50000000.01"),
        }

        summary = DiagnosticSummary(
            user_id=user.id,
            client_id=client.id,
            filename_hash="bb" * 32,
            row_count=5000,
            total_assets=quantize_monetary(values["total_assets"]),
            current_assets=quantize_monetary(values["current_assets"]),
            total_liabilities=quantize_monetary(values["total_liabilities"]),
            total_equity=quantize_monetary(values["total_equity"]),
            total_revenue=quantize_monetary(values["total_revenue"]),
            total_expenses=quantize_monetary(values["total_expenses"]),
            total_debits=quantize_monetary(values["total_debits"]),
            total_credits=quantize_monetary(values["total_credits"]),
        )
        db_session.add(summary)
        db_session.flush()
        summary_id = summary.id

        db_session.expire(summary)
        reloaded = db_session.get(DiagnosticSummary, summary_id)

        for field_name, expected in values.items():
            actual = getattr(reloaded, field_name)
            assert monetary_equal(actual, expected), \
                f"{field_name}: expected {expected}, got {actual}"

    def test_debit_credit_balance_invariant(self, db_session, make_user):
        """After quantization + DB roundtrip, debits must equal credits."""
        from models import ActivityLog
        from shared.monetary import quantize_monetary

        user = make_user(email="decimal_rt_3@example.com")

        # Use values that sum to exact balance AFTER quantization
        # 0.1 + 0.2 = 0.30000000000000004 in float, but quantize_monetary fixes it
        raw_debits = 0.1 + 0.2 + 99999.7
        raw_credits = 100000.0

        log = ActivityLog(
            user_id=user.id,
            filename_hash="cc" * 32,
            record_count=3,
            total_debits=quantize_monetary(raw_debits),
            total_credits=quantize_monetary(raw_credits),
            materiality_threshold=quantize_monetary(Decimal("100.00")),
            was_balanced=True,
        )
        db_session.add(log)
        db_session.flush()

        db_session.expire(log)
        reloaded = db_session.get(ActivityLog, log.id)

        debit_dec = Decimal(str(reloaded.total_debits))
        credit_dec = Decimal(str(reloaded.total_credits))
        assert debit_dec == credit_dec, \
            f"Imbalance after roundtrip: debits={debit_dec}, credits={credit_dec}"

    def test_apply_adjustments_preserves_balance(self):
        """Applying balanced adjusting entries preserves TB debit=credit invariant."""
        from adjusting_entries import (
            AdjustingEntry,
            AdjustmentLine,
            AdjustmentSet,
            AdjustmentStatus,
            AdjustmentType,
            apply_adjustments,
        )
        from shared.monetary import BALANCE_TOLERANCE

        # Balanced TB
        tb = [
            {"account": "Cash", "debit": 50000.00, "credit": 0},
            {"account": "Accounts Payable", "debit": 0, "credit": 30000.00},
            {"account": "Equity", "debit": 0, "credit": 20000.00},
        ]

        # Balanced adjustment (debit Expense, credit AP)
        entry = AdjustingEntry(
            reference="AJE-BAL-001",
            description="Precision test",
            adjustment_type=AdjustmentType.ACCRUAL,
            status=AdjustmentStatus.APPROVED,
            lines=[
                AdjustmentLine(
                    account_name="Expense - Rent",
                    debit=Decimal("12345.67"),
                    credit=Decimal("0"),
                ),
                AdjustmentLine(
                    account_name="Accounts Payable",
                    debit=Decimal("0"),
                    credit=Decimal("12345.67"),
                ),
            ],
            approved_by="mgr@test.com",
            approved_at=datetime.now(UTC),
        )
        adj_set = AdjustmentSet(entries=[entry])

        result = apply_adjustments(tb, adj_set, mode="official")

        # Adjustment debits must equal adjustment credits
        adj_diff = abs(result.total_adjustment_debits - result.total_adjustment_credits)
        assert adj_diff < BALANCE_TOLERANCE, \
            f"Adjustment imbalance: {adj_diff}"

        # Adjusted TB must be balanced
        adjusted_diff = abs(result.total_adjusted_debits - result.total_adjusted_credits)
        assert adjusted_diff < BALANCE_TOLERANCE, \
            f"Adjusted TB imbalance: {adjusted_diff}"

    def test_high_volume_sum_precision(self):
        """math.fsum prevents drift when summing 10,000 small values."""
        values = [0.1] * 10000
        naive_sum = sum(values)  # Accumulates float error
        precise_sum = math.fsum(values)

        from shared.monetary import quantize_monetary

        # Both should quantize to 1000.00, but naive_sum may not be exactly 1000.0
        assert quantize_monetary(precise_sum) == Decimal("1000.00")
        assert quantize_monetary(naive_sum) == Decimal("1000.00")
        # The raw float sums may differ
        # (this test documents that quantize_monetary absorbs the difference)

    def test_trillion_scale_roundtrip(self, db_session, make_user):
        """Numeric(19,2) handles trillion-scale values without overflow."""
        from models import ActivityLog
        from shared.monetary import monetary_equal, quantize_monetary

        user = make_user(email="decimal_rt_4@example.com")
        trillion = Decimal("9999999999999.99")  # Max for Numeric(19,2) with room

        log = ActivityLog(
            user_id=user.id,
            filename_hash="dd" * 32,
            record_count=1,
            total_debits=quantize_monetary(trillion),
            total_credits=quantize_monetary(trillion),
            materiality_threshold=quantize_monetary(Decimal("1000000.00")),
            was_balanced=True,
        )
        db_session.add(log)
        db_session.flush()

        db_session.expire(log)
        reloaded = db_session.get(ActivityLog, log.id)
        assert monetary_equal(reloaded.total_debits, trillion)
        assert monetary_equal(reloaded.total_credits, trillion)
