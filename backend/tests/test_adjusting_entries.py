"""
Tests for Adjusting Entry Module - Sprint 52

Tests cover:
- AdjustmentLine validation and creation
- AdjustingEntry balance validation
- AdjustmentSet management
- AdjustedTrialBalance generation
- Entry application logic
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from adjusting_entries import (
    VALID_TRANSITIONS,
    AdjustedAccountBalance,
    AdjustedTrialBalance,
    AdjustingEntry,
    AdjustmentLine,
    AdjustmentSet,
    AdjustmentStatus,
    AdjustmentType,
    InvalidTransitionError,
    apply_adjustments,
    create_simple_entry,
    validate_entry_accounts,
    validate_status_transition,
)


class TestAdjustmentLine:
    """Tests for AdjustmentLine dataclass."""

    def test_create_debit_line(self):
        """Create a valid debit line."""
        line = AdjustmentLine(
            account_name="Accounts Receivable",
            debit=Decimal("1000.00"),
        )
        assert line.account_name == "Accounts Receivable"
        assert line.debit == Decimal("1000.00")
        assert line.credit == Decimal("0.00")
        assert line.net_amount == Decimal("1000.00")

    def test_create_credit_line(self):
        """Create a valid credit line."""
        line = AdjustmentLine(
            account_name="Revenue",
            credit=Decimal("1000.00"),
        )
        assert line.account_name == "Revenue"
        assert line.debit == Decimal("0.00")
        assert line.credit == Decimal("1000.00")
        assert line.net_amount == Decimal("-1000.00")

    def test_numeric_conversion(self):
        """Numeric values are converted to Decimal."""
        line = AdjustmentLine(
            account_name="Cash",
            debit=500.50,  # float input
        )
        assert line.debit == Decimal("500.50")
        assert isinstance(line.debit, Decimal)

    def test_rounding(self):
        """Amounts are rounded to 2 decimal places."""
        line = AdjustmentLine(
            account_name="Cash",
            debit=Decimal("100.999"),
        )
        assert line.debit == Decimal("101.00")

    def test_both_debit_and_credit_raises(self):
        """Cannot have both debit and credit on same line."""
        with pytest.raises(ValueError) as exc_info:
            AdjustmentLine(
                account_name="Cash",
                debit=Decimal("100.00"),
                credit=Decimal("50.00"),
            )
        assert "cannot have both debit and credit" in str(exc_info.value).lower()

    def test_zero_amounts_raises(self):
        """Must have either debit or credit amount."""
        with pytest.raises(ValueError) as exc_info:
            AdjustmentLine(
                account_name="Cash",
                debit=Decimal("0.00"),
                credit=Decimal("0.00"),
            )
        assert "must have either a debit or credit" in str(exc_info.value).lower()

    def test_to_dict(self):
        """Conversion to dictionary."""
        line = AdjustmentLine(
            account_name="Cash",
            debit=Decimal("1000.00"),
            description="Opening balance adjustment",
        )
        result = line.to_dict()
        assert result["account_name"] == "Cash"
        assert result["debit"] == 1000.00
        assert result["credit"] == 0.00
        assert result["description"] == "Opening balance adjustment"


class TestAdjustingEntry:
    """Tests for AdjustingEntry dataclass."""

    def test_create_balanced_entry(self):
        """Create a valid balanced entry."""
        entry = AdjustingEntry(
            reference="AJE-001",
            description="Accrue unbilled revenue",
            adjustment_type=AdjustmentType.ACCRUAL,
            lines=[
                AdjustmentLine(account_name="Accounts Receivable", debit=Decimal("5000.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("5000.00")),
            ],
        )
        assert entry.is_balanced
        assert entry.total_debits == Decimal("5000.00")
        assert entry.total_credits == Decimal("5000.00")
        assert entry.entry_total == Decimal("5000.00")
        assert entry.account_count == 2

    def test_unbalanced_entry_raises(self):
        """Unbalanced entry raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            AdjustingEntry(
                reference="AJE-002",
                description="Bad entry",
                lines=[
                    AdjustmentLine(account_name="Cash", debit=Decimal("1000.00")),
                    AdjustmentLine(account_name="Revenue", credit=Decimal("500.00")),
                ],
            )
        assert "out of balance" in str(exc_info.value).lower()

    def test_multi_line_entry(self):
        """Entry with more than 2 lines."""
        entry = AdjustingEntry(
            reference="AJE-003",
            description="Compound entry",
            lines=[
                AdjustmentLine(account_name="Cash", debit=Decimal("1000.00")),
                AdjustmentLine(account_name="Accounts Receivable", debit=Decimal("2000.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("3000.00")),
            ],
        )
        assert entry.is_balanced
        assert entry.total_debits == Decimal("3000.00")
        assert entry.total_credits == Decimal("3000.00")
        assert entry.account_count == 3

    def test_entry_validation(self):
        """Entry validation returns errors list."""
        # Create entry without validation (bypass __post_init__)
        entry = AdjustingEntry.__new__(AdjustingEntry)
        entry.id = "test-id"
        entry.reference = ""  # Missing
        entry.description = ""  # Missing
        entry.lines = []  # Empty
        entry.status = AdjustmentStatus.PROPOSED
        entry.adjustment_type = AdjustmentType.OTHER
        entry.prepared_by = None
        entry.reviewed_by = None
        entry.created_at = datetime.now(timezone.utc)
        entry.updated_at = None
        entry.notes = None
        entry.is_reversing = False

        errors = entry.validate()
        assert "Reference number is required" in errors
        assert "Description is required" in errors
        assert "Entry must have at least 2 lines" in errors

    def test_entry_status_default(self):
        """New entries default to PROPOSED status."""
        entry = AdjustingEntry(
            reference="AJE-004",
            description="Test entry",
            lines=[
                AdjustmentLine(account_name="Cash", debit=Decimal("100.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("100.00")),
            ],
        )
        assert entry.status == AdjustmentStatus.PROPOSED

    def test_adjustment_types(self):
        """All adjustment types work correctly."""
        for adj_type in AdjustmentType:
            entry = AdjustingEntry(
                reference=f"AJE-{adj_type.value}",
                description=f"Test {adj_type.value}",
                adjustment_type=adj_type,
                lines=[
                    AdjustmentLine(account_name="Cash", debit=Decimal("100.00")),
                    AdjustmentLine(account_name="Revenue", credit=Decimal("100.00")),
                ],
            )
            assert entry.adjustment_type == adj_type

    def test_to_dict(self):
        """Conversion to dictionary."""
        entry = AdjustingEntry(
            reference="AJE-005",
            description="Test serialization",
            lines=[
                AdjustmentLine(account_name="Cash", debit=Decimal("100.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("100.00")),
            ],
            prepared_by="Auditor",
        )
        result = entry.to_dict()
        assert result["reference"] == "AJE-005"
        assert result["total_debits"] == 100.00
        assert result["total_credits"] == 100.00
        assert result["is_balanced"] is True
        assert result["prepared_by"] == "Auditor"
        assert len(result["lines"]) == 2

    def test_from_dict(self):
        """Creation from dictionary."""
        data = {
            "reference": "AJE-006",
            "description": "From dict test",
            "adjustment_type": "accrual",
            "status": "approved",
            "lines": [
                {"account_name": "Cash", "debit": 200, "credit": 0},
                {"account_name": "Revenue", "debit": 0, "credit": 200},
            ],
        }
        entry = AdjustingEntry.from_dict(data)
        assert entry.reference == "AJE-006"
        assert entry.adjustment_type == AdjustmentType.ACCRUAL
        assert entry.status == AdjustmentStatus.APPROVED
        assert entry.is_balanced

    def test_add_line(self):
        """Add line to existing entry."""
        # Start with single line (unbalanced, bypass validation)
        entry = AdjustingEntry.__new__(AdjustingEntry)
        entry.id = "test"
        entry.reference = "AJE-007"
        entry.description = "Adding lines"
        entry.lines = [AdjustmentLine(account_name="Cash", debit=Decimal("500.00"))]
        entry.status = AdjustmentStatus.PROPOSED
        entry.adjustment_type = AdjustmentType.OTHER
        entry.prepared_by = None
        entry.reviewed_by = None
        entry.created_at = datetime.now(timezone.utc)
        entry.updated_at = None
        entry.notes = None
        entry.is_reversing = False

        entry.add_line(AdjustmentLine(account_name="Revenue", credit=Decimal("500.00")))
        assert entry.is_balanced
        assert entry.updated_at is not None

    def test_remove_line(self):
        """Remove line from entry."""
        entry = AdjustingEntry(
            reference="AJE-008",
            description="Removing lines",
            lines=[
                AdjustmentLine(account_name="Cash", debit=Decimal("100.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("100.00")),
            ],
        )
        removed = entry.remove_line("Cash")
        assert removed is True
        assert len(entry.lines) == 1

        # Try removing non-existent account
        removed = entry.remove_line("NonExistent")
        assert removed is False


class TestAdjustmentSet:
    """Tests for AdjustmentSet dataclass."""

    @pytest.fixture
    def sample_entries(self):
        """Create sample adjusting entries."""
        return [
            AdjustingEntry(
                reference="AJE-001",
                description="Entry 1",
                status=AdjustmentStatus.PROPOSED,
                lines=[
                    AdjustmentLine(account_name="Cash", debit=Decimal("1000.00")),
                    AdjustmentLine(account_name="Revenue", credit=Decimal("1000.00")),
                ],
            ),
            AdjustingEntry(
                reference="AJE-002",
                description="Entry 2",
                status=AdjustmentStatus.APPROVED,
                lines=[
                    AdjustmentLine(account_name="Expense", debit=Decimal("500.00")),
                    AdjustmentLine(account_name="Cash", credit=Decimal("500.00")),
                ],
            ),
            AdjustingEntry(
                reference="AJE-003",
                description="Entry 3",
                status=AdjustmentStatus.REJECTED,
                lines=[
                    AdjustmentLine(account_name="Cash", debit=Decimal("200.00")),
                    AdjustmentLine(account_name="Revenue", credit=Decimal("200.00")),
                ],
            ),
        ]

    def test_create_empty_set(self):
        """Create empty adjustment set."""
        adj_set = AdjustmentSet()
        assert adj_set.total_adjustments == 0
        assert adj_set.proposed_count == 0

    def test_add_entries(self, sample_entries):
        """Add entries to set."""
        adj_set = AdjustmentSet()
        for entry in sample_entries:
            adj_set.add_entry(entry)

        assert adj_set.total_adjustments == 3
        assert adj_set.proposed_count == 1
        assert adj_set.approved_count == 1
        assert adj_set.rejected_count == 1

    def test_total_adjustment_amount(self, sample_entries):
        """Total only includes approved/posted entries."""
        adj_set = AdjustmentSet(entries=sample_entries)
        # Only AJE-002 (approved, $500) should count
        assert adj_set.total_adjustment_amount == Decimal("500.00")

    def test_remove_entry(self, sample_entries):
        """Remove entry by ID."""
        adj_set = AdjustmentSet(entries=sample_entries)
        entry_id = sample_entries[0].id

        removed = adj_set.remove_entry(entry_id)
        assert removed is True
        assert adj_set.total_adjustments == 2

        # Try removing again
        removed = adj_set.remove_entry(entry_id)
        assert removed is False

    def test_get_entry(self, sample_entries):
        """Get entry by ID."""
        adj_set = AdjustmentSet(entries=sample_entries)
        entry_id = sample_entries[1].id

        entry = adj_set.get_entry(entry_id)
        assert entry is not None
        assert entry.reference == "AJE-002"

        # Non-existent ID
        entry = adj_set.get_entry("non-existent")
        assert entry is None

    def test_filter_by_status(self, sample_entries):
        """Filter entries by status."""
        adj_set = AdjustmentSet(entries=sample_entries)

        proposed = adj_set.get_entries_by_status(AdjustmentStatus.PROPOSED)
        assert len(proposed) == 1
        assert proposed[0].reference == "AJE-001"

    def test_filter_by_type(self, sample_entries):
        """Filter entries by adjustment type."""
        sample_entries[0].adjustment_type = AdjustmentType.ACCRUAL
        sample_entries[1].adjustment_type = AdjustmentType.ACCRUAL
        sample_entries[2].adjustment_type = AdjustmentType.ERROR_CORRECTION

        adj_set = AdjustmentSet(entries=sample_entries)

        accruals = adj_set.get_entries_by_type(AdjustmentType.ACCRUAL)
        assert len(accruals) == 2

    def test_generate_next_reference(self, sample_entries):
        """Generate sequential reference numbers."""
        adj_set = AdjustmentSet(entries=sample_entries)

        next_ref = adj_set.generate_next_reference("AJE")
        assert next_ref == "AJE-004"

        # Different prefix
        next_ref = adj_set.generate_next_reference("PBC")
        assert next_ref == "PBC-001"

    def test_to_dict(self, sample_entries):
        """Conversion to dictionary."""
        adj_set = AdjustmentSet(
            entries=sample_entries,
            period_label="FY2025",
            client_name="Test Client",
        )
        result = adj_set.to_dict()

        assert result["total_adjustments"] == 3
        assert result["proposed_count"] == 1
        assert result["period_label"] == "FY2025"
        assert result["client_name"] == "Test Client"
        assert len(result["entries"]) == 3


class TestAdjustedAccountBalance:
    """Tests for AdjustedAccountBalance dataclass."""

    def test_debit_account(self):
        """Test debit account balances."""
        account = AdjustedAccountBalance(
            account_name="Cash",
            unadjusted_debit=Decimal("10000.00"),
            unadjusted_credit=Decimal("0.00"),
            adjustment_debit=Decimal("1000.00"),
            adjustment_credit=Decimal("0.00"),
        )
        assert account.unadjusted_balance == Decimal("10000.00")
        assert account.net_adjustment == Decimal("1000.00")
        assert account.adjusted_debit == Decimal("11000.00")
        assert account.adjusted_credit == Decimal("0.00")
        assert account.has_adjustment is True

    def test_credit_account(self):
        """Test credit account balances."""
        account = AdjustedAccountBalance(
            account_name="Revenue",
            unadjusted_debit=Decimal("0.00"),
            unadjusted_credit=Decimal("50000.00"),
            adjustment_debit=Decimal("0.00"),
            adjustment_credit=Decimal("5000.00"),
        )
        assert account.unadjusted_balance == Decimal("-50000.00")
        assert account.net_adjustment == Decimal("-5000.00")
        assert account.adjusted_credit == Decimal("55000.00")

    def test_no_adjustment(self):
        """Account without adjustment."""
        account = AdjustedAccountBalance(
            account_name="Inventory",
            unadjusted_debit=Decimal("25000.00"),
            unadjusted_credit=Decimal("0.00"),
        )
        assert account.has_adjustment is False
        assert account.adjusted_debit == account.unadjusted_debit

    def test_to_dict(self):
        """Conversion to dictionary."""
        account = AdjustedAccountBalance(
            account_name="Cash",
            unadjusted_debit=Decimal("5000.00"),
            unadjusted_credit=Decimal("0.00"),
            adjustment_debit=Decimal("500.00"),
            adjustment_credit=Decimal("0.00"),
        )
        result = account.to_dict()

        assert result["account_name"] == "Cash"
        assert result["unadjusted_debit"] == 5000.00
        assert result["adjusted_debit"] == 5500.00
        assert result["has_adjustment"] is True


class TestApplyAdjustments:
    """Tests for apply_adjustments function."""

    @pytest.fixture
    def sample_trial_balance(self):
        """Sample trial balance data."""
        return [
            {"account": "Cash", "debit": 10000, "credit": 0},
            {"account": "Accounts Receivable", "debit": 5000, "credit": 0},
            {"account": "Inventory", "debit": 15000, "credit": 0},
            {"account": "Accounts Payable", "debit": 0, "credit": 8000},
            {"account": "Revenue", "debit": 0, "credit": 50000},
            {"account": "Expenses", "debit": 28000, "credit": 0},
        ]

    @pytest.fixture
    def sample_adjustments(self):
        """Sample adjustment set."""
        adj_set = AdjustmentSet()
        adj_set.add_entry(AdjustingEntry(
            reference="AJE-001",
            description="Accrue revenue",
            status=AdjustmentStatus.APPROVED,
            lines=[
                AdjustmentLine(account_name="Accounts Receivable", debit=Decimal("2000.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("2000.00")),
            ],
        ))
        adj_set.add_entry(AdjustingEntry(
            reference="AJE-002",
            description="Accrue expense",
            status=AdjustmentStatus.PROPOSED,  # Should be excluded by default
            lines=[
                AdjustmentLine(account_name="Expenses", debit=Decimal("1000.00")),
                AdjustmentLine(account_name="Accounts Payable", credit=Decimal("1000.00")),
            ],
        ))
        return adj_set

    def test_apply_approved_only(self, sample_trial_balance, sample_adjustments):
        """Only approved entries are applied by default."""
        result = apply_adjustments(sample_trial_balance, sample_adjustments)

        # Find accounts receivable
        ar = next(a for a in result.accounts if a.account_name == "Accounts Receivable")
        assert ar.adjusted_debit == Decimal("7000.00")  # 5000 + 2000

        # Revenue
        rev = next(a for a in result.accounts if a.account_name == "Revenue")
        assert rev.adjusted_credit == Decimal("52000.00")  # 50000 + 2000

        # Expenses should be unchanged (proposed entry not applied)
        exp = next(a for a in result.accounts if a.account_name == "Expenses")
        assert exp.adjusted_debit == Decimal("28000.00")

        assert result.adjustment_count == 1

    def test_apply_with_proposed(self, sample_trial_balance, sample_adjustments):
        """Include proposed entries in simulation mode."""
        result = apply_adjustments(
            sample_trial_balance,
            sample_adjustments,
            mode="simulation",
        )

        # Expenses should now be adjusted
        exp = next(a for a in result.accounts if a.account_name == "Expenses")
        assert exp.adjusted_debit == Decimal("29000.00")  # 28000 + 1000

        assert result.adjustment_count == 2

    def test_balance_preserved(self, sample_trial_balance, sample_adjustments):
        """Trial balance remains balanced after adjustments."""
        result = apply_adjustments(sample_trial_balance, sample_adjustments)

        # Original TB was balanced
        orig_debits = sum(r.get("debit", 0) for r in sample_trial_balance)
        orig_credits = sum(r.get("credit", 0) for r in sample_trial_balance)
        assert orig_debits == orig_credits

        # Adjusted TB should also be balanced
        assert result.is_balanced

    def test_new_account_from_adjustment(self, sample_trial_balance):
        """Adjustment can create new account not in original TB."""
        adj_set = AdjustmentSet()
        adj_set.add_entry(AdjustingEntry(
            reference="AJE-NEW",
            description="Create prepaid",
            status=AdjustmentStatus.APPROVED,
            lines=[
                AdjustmentLine(account_name="Prepaid Insurance", debit=Decimal("3000.00")),
                AdjustmentLine(account_name="Cash", credit=Decimal("3000.00")),
            ],
        ))

        result = apply_adjustments(sample_trial_balance, adj_set)

        # New account should exist
        prepaid = next((a for a in result.accounts if a.account_name == "Prepaid Insurance"), None)
        assert prepaid is not None
        assert prepaid.unadjusted_debit == Decimal("0.00")
        assert prepaid.adjusted_debit == Decimal("3000.00")

    def test_accounts_sorted_alphabetically(self, sample_trial_balance, sample_adjustments):
        """Result accounts are sorted alphabetically."""
        result = apply_adjustments(sample_trial_balance, sample_adjustments)

        account_names = [a.account_name for a in result.accounts]
        assert account_names == sorted(account_names, key=str.lower)

    def test_totals_calculation(self, sample_trial_balance, sample_adjustments):
        """Totals are calculated correctly."""
        result = apply_adjustments(sample_trial_balance, sample_adjustments)

        assert result.total_unadjusted_debits == Decimal("58000.00")
        assert result.total_unadjusted_credits == Decimal("58000.00")
        assert result.total_adjustment_debits == Decimal("2000.00")
        assert result.total_adjustment_credits == Decimal("2000.00")

    def test_accounts_with_adjustments_filter(self, sample_trial_balance, sample_adjustments):
        """Filter to only accounts with adjustments."""
        result = apply_adjustments(sample_trial_balance, sample_adjustments)

        adjusted_only = result.accounts_with_adjustments
        assert len(adjusted_only) == 2
        account_names = {a.account_name for a in adjusted_only}
        assert account_names == {"Accounts Receivable", "Revenue"}


class TestCreateSimpleEntry:
    """Tests for create_simple_entry helper function."""

    def test_create_simple_entry(self):
        """Create a simple 2-line entry."""
        entry = create_simple_entry(
            reference="AJE-001",
            description="Record prepaid rent",
            debit_account="Prepaid Rent",
            credit_account="Cash",
            amount=Decimal("12000.00"),
            adjustment_type=AdjustmentType.DEFERRAL,
        )

        assert entry.reference == "AJE-001"
        assert entry.is_balanced
        assert entry.account_count == 2
        assert entry.adjustment_type == AdjustmentType.DEFERRAL

        debit_line = next(l for l in entry.lines if l.debit > 0)
        credit_line = next(l for l in entry.lines if l.credit > 0)

        assert debit_line.account_name == "Prepaid Rent"
        assert credit_line.account_name == "Cash"

    def test_numeric_amount_conversion(self):
        """Numeric amount is converted to Decimal."""
        entry = create_simple_entry(
            reference="AJE-002",
            description="Test",
            debit_account="Cash",
            credit_account="Revenue",
            amount=1500.50,  # float
        )
        assert entry.entry_total == Decimal("1500.50")


class TestValidateEntryAccounts:
    """Tests for validate_entry_accounts function."""

    def test_all_accounts_valid(self):
        """All accounts exist in trial balance."""
        entry = create_simple_entry(
            reference="AJE-001",
            description="Test",
            debit_account="Cash",
            credit_account="Revenue",
            amount=Decimal("1000.00"),
        )
        valid_accounts = {"Cash", "Revenue", "Expenses", "Assets"}

        unknown = validate_entry_accounts(entry, valid_accounts)
        assert unknown == []

    def test_unknown_account(self):
        """Detect unknown account."""
        entry = create_simple_entry(
            reference="AJE-001",
            description="Test",
            debit_account="Prepaid Insurance",
            credit_account="Cash",
            amount=Decimal("1000.00"),
        )
        valid_accounts = {"Cash", "Revenue", "Expenses"}

        unknown = validate_entry_accounts(entry, valid_accounts)
        assert "Prepaid Insurance" in unknown

    def test_case_insensitive(self):
        """Case-insensitive matching."""
        entry = create_simple_entry(
            reference="AJE-001",
            description="Test",
            debit_account="CASH",
            credit_account="revenue",
            amount=Decimal("1000.00"),
        )
        valid_accounts = {"Cash", "Revenue"}

        unknown = validate_entry_accounts(entry, valid_accounts, case_insensitive=True)
        assert unknown == []

    def test_case_sensitive(self):
        """Case-sensitive matching."""
        entry = create_simple_entry(
            reference="AJE-001",
            description="Test",
            debit_account="CASH",
            credit_account="revenue",
            amount=Decimal("1000.00"),
        )
        valid_accounts = {"Cash", "Revenue"}

        unknown = validate_entry_accounts(entry, valid_accounts, case_insensitive=False)
        assert "CASH" in unknown
        assert "revenue" in unknown


class TestAdjustedTrialBalance:
    """Tests for AdjustedTrialBalance dataclass."""

    def test_empty_trial_balance(self):
        """Empty adjusted trial balance."""
        atb = AdjustedTrialBalance()
        assert atb.is_balanced  # 0 = 0
        assert atb.adjustment_count == 0

    def test_to_dict(self):
        """Conversion to dictionary."""
        atb = AdjustedTrialBalance(
            accounts=[
                AdjustedAccountBalance(
                    account_name="Cash",
                    unadjusted_debit=Decimal("5000.00"),
                    unadjusted_credit=Decimal("0.00"),
                ),
                AdjustedAccountBalance(
                    account_name="Revenue",
                    unadjusted_debit=Decimal("0.00"),
                    unadjusted_credit=Decimal("5000.00"),
                ),
            ],
            adjustments_applied=["entry-1", "entry-2"],
        )
        result = atb.to_dict()

        assert len(result["accounts"]) == 2
        assert result["adjustment_count"] == 2
        assert "totals" in result
        assert result["is_balanced"] is True

    def test_is_simulation_default(self):
        """is_simulation defaults to False."""
        atb = AdjustedTrialBalance()
        assert atb.is_simulation is False
        assert atb.to_dict()["is_simulation"] is False

    def test_is_simulation_set(self):
        """is_simulation can be set to True."""
        atb = AdjustedTrialBalance(is_simulation=True)
        assert atb.is_simulation is True
        assert atb.to_dict()["is_simulation"] is True


class TestStatusTransitions:
    """Tests for status transition validation (Phase XLVIII)."""

    def test_valid_transition_proposed_to_approved(self):
        """proposed → approved is allowed."""
        validate_status_transition(AdjustmentStatus.PROPOSED, AdjustmentStatus.APPROVED)

    def test_valid_transition_proposed_to_rejected(self):
        """proposed → rejected is allowed."""
        validate_status_transition(AdjustmentStatus.PROPOSED, AdjustmentStatus.REJECTED)

    def test_valid_transition_approved_to_posted(self):
        """approved → posted is allowed."""
        validate_status_transition(AdjustmentStatus.APPROVED, AdjustmentStatus.POSTED)

    def test_valid_transition_approved_to_rejected(self):
        """approved → rejected is allowed."""
        validate_status_transition(AdjustmentStatus.APPROVED, AdjustmentStatus.REJECTED)

    def test_valid_transition_rejected_to_proposed(self):
        """rejected → proposed (re-proposal) is allowed."""
        validate_status_transition(AdjustmentStatus.REJECTED, AdjustmentStatus.PROPOSED)

    def test_invalid_transition_proposed_to_posted(self):
        """proposed → posted skips approval — must fail."""
        with pytest.raises(InvalidTransitionError) as exc_info:
            validate_status_transition(AdjustmentStatus.PROPOSED, AdjustmentStatus.POSTED)
        assert "proposed" in str(exc_info.value)
        assert "posted" in str(exc_info.value)

    def test_invalid_transition_rejected_to_posted(self):
        """rejected → posted is not allowed."""
        with pytest.raises(InvalidTransitionError) as exc_info:
            validate_status_transition(AdjustmentStatus.REJECTED, AdjustmentStatus.POSTED)
        assert "rejected" in str(exc_info.value)

    def test_invalid_transition_rejected_to_approved(self):
        """rejected → approved is not allowed (must re-propose first)."""
        with pytest.raises(InvalidTransitionError):
            validate_status_transition(AdjustmentStatus.REJECTED, AdjustmentStatus.APPROVED)

    def test_posted_is_terminal(self):
        """posted has no valid exit transitions."""
        for target in AdjustmentStatus:
            if target == AdjustmentStatus.POSTED:
                continue
            with pytest.raises(InvalidTransitionError) as exc_info:
                validate_status_transition(AdjustmentStatus.POSTED, target)
            assert "terminal" in str(exc_info.value)

    def test_valid_transitions_map_completeness(self):
        """VALID_TRANSITIONS covers all statuses."""
        for status in AdjustmentStatus:
            assert status in VALID_TRANSITIONS


class TestApprovalMetadata:
    """Tests for approval metadata fields (Phase XLVIII)."""

    def test_approval_fields_default_none(self):
        """New entries have no approval metadata."""
        entry = AdjustingEntry(
            reference="AJE-001",
            description="Test",
            lines=[
                AdjustmentLine(account_name="Cash", debit=Decimal("100.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("100.00")),
            ],
        )
        assert entry.approved_by is None
        assert entry.approved_at is None

    def test_approval_sets_metadata(self):
        """approved_by and approved_at are included in to_dict."""
        entry = AdjustingEntry(
            reference="AJE-001",
            description="Test",
            lines=[
                AdjustmentLine(account_name="Cash", debit=Decimal("100.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("100.00")),
            ],
            approved_by="reviewer@example.com",
            approved_at=datetime(2026, 2, 20, 12, 0, 0, tzinfo=timezone.utc),
        )
        result = entry.to_dict()
        assert result["approved_by"] == "reviewer@example.com"
        assert result["approved_at"] == "2026-02-20T12:00:00+00:00"

    def test_approval_metadata_roundtrip(self):
        """Approval metadata round-trips through to_dict/from_dict."""
        entry = AdjustingEntry(
            reference="AJE-001",
            description="Test",
            lines=[
                AdjustmentLine(account_name="Cash", debit=Decimal("100.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("100.00")),
            ],
            approved_by="reviewer@example.com",
            approved_at=datetime(2026, 2, 20, 12, 0, 0, tzinfo=timezone.utc),
        )
        data = entry.to_dict()
        restored = AdjustingEntry.from_dict(data)
        assert restored.approved_by == "reviewer@example.com"
        assert restored.approved_at is not None
        assert restored.approved_at.year == 2026

    def test_legacy_data_without_approval_fields(self):
        """from_dict with missing approval fields defaults to None."""
        data = {
            "reference": "AJE-001",
            "description": "Legacy entry",
            "lines": [
                {"account_name": "Cash", "debit": 100, "credit": 0},
                {"account_name": "Revenue", "debit": 0, "credit": 100},
            ],
        }
        entry = AdjustingEntry.from_dict(data)
        assert entry.approved_by is None
        assert entry.approved_at is None


class TestApplyMode:
    """Tests for official/simulation mode in apply_adjustments (Phase XLVIII)."""

    @pytest.fixture
    def tb(self):
        return [
            {"account": "Cash", "debit": 10000, "credit": 0},
            {"account": "Revenue", "debit": 0, "credit": 10000},
        ]

    @pytest.fixture
    def mixed_adjustments(self):
        adj_set = AdjustmentSet()
        adj_set.add_entry(AdjustingEntry(
            reference="AJE-001",
            description="Approved entry",
            status=AdjustmentStatus.APPROVED,
            lines=[
                AdjustmentLine(account_name="Cash", debit=Decimal("500.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("500.00")),
            ],
        ))
        adj_set.add_entry(AdjustingEntry(
            reference="AJE-002",
            description="Posted entry",
            status=AdjustmentStatus.POSTED,
            lines=[
                AdjustmentLine(account_name="Cash", debit=Decimal("300.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("300.00")),
            ],
        ))
        adj_set.add_entry(AdjustingEntry(
            reference="AJE-003",
            description="Proposed entry",
            status=AdjustmentStatus.PROPOSED,
            lines=[
                AdjustmentLine(account_name="Cash", debit=Decimal("200.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("200.00")),
            ],
        ))
        return adj_set

    def test_official_mode_excludes_proposed(self, tb, mixed_adjustments):
        """Official mode does not include proposed entries."""
        result = apply_adjustments(tb, mixed_adjustments, mode="official")
        cash = next(a for a in result.accounts if a.account_name == "Cash")
        # 10000 + 500 (approved) + 300 (posted) = 10800, NOT +200 (proposed)
        assert cash.adjusted_debit == Decimal("10800.00")
        assert result.adjustment_count == 2

    def test_official_mode_includes_approved_and_posted(self, tb, mixed_adjustments):
        """Official mode includes both approved and posted entries."""
        result = apply_adjustments(tb, mixed_adjustments, mode="official")
        assert result.adjustment_count == 2
        applied_refs = set()
        for entry in mixed_adjustments.entries:
            if entry.id in result.adjustments_applied:
                applied_refs.add(entry.reference)
        assert "AJE-001" in applied_refs
        assert "AJE-002" in applied_refs

    def test_simulation_mode_includes_proposed(self, tb, mixed_adjustments):
        """Simulation mode includes proposed entries."""
        result = apply_adjustments(tb, mixed_adjustments, mode="simulation")
        cash = next(a for a in result.accounts if a.account_name == "Cash")
        # 10000 + 500 + 300 + 200 = 11000
        assert cash.adjusted_debit == Decimal("11000.00")
        assert result.adjustment_count == 3

    def test_simulation_mode_tags_response(self, tb, mixed_adjustments):
        """Simulation mode sets is_simulation=True."""
        result = apply_adjustments(tb, mixed_adjustments, mode="simulation")
        assert result.is_simulation is True

    def test_official_mode_tags_response(self, tb, mixed_adjustments):
        """Official mode sets is_simulation=False."""
        result = apply_adjustments(tb, mixed_adjustments, mode="official")
        assert result.is_simulation is False

    def test_default_mode_is_official(self, tb, mixed_adjustments):
        """No mode argument defaults to official behavior."""
        result = apply_adjustments(tb, mixed_adjustments)
        assert result.is_simulation is False
        assert result.adjustment_count == 2
