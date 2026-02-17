"""
Tests for Journal Entry Testing Engine — Tier 1 Structural Tests (T1-T5)

Covers:
- T1: Unbalanced Entries
- T2: Missing Fields
- T3: Duplicate Entries
- T4: Round Dollar Amounts
- T5: Unusual Amounts
"""

from je_testing_engine import (
    JETestingConfig,
    JournalEntry,
    # Enums & types
    Severity,
    TestTier,
)
from je_testing_engine import (
    test_duplicate_entries as run_duplicate_test,
)
from je_testing_engine import (
    test_missing_fields as run_missing_fields_test,
)
from je_testing_engine import (
    test_round_amounts as run_round_amounts_test,
)
from je_testing_engine import (
    # Tier 1 Structural — aliased to avoid pytest collection
    test_unbalanced_entries as run_unbalanced_test,
)
from je_testing_engine import (
    test_unusual_amounts as run_unusual_amounts_test,
)

# =============================================================================
# T1: UNBALANCED ENTRIES
# =============================================================================

class TestUnbalancedEntries:
    """Tests for test_unbalanced_entries()."""

    def test_balanced_entries_no_flags(self):
        entries = [
            JournalEntry(entry_id="JE001", debit=1000, credit=0, row_number=1),
            JournalEntry(entry_id="JE001", debit=0, credit=1000, row_number=2),
        ]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_unbalanced_entry_flagged(self):
        entries = [
            JournalEntry(entry_id="JE001", debit=1000, credit=0, row_number=1),
            JournalEntry(entry_id="JE001", debit=0, credit=500, row_number=2),
        ]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.entries_flagged == 2  # Both lines of the entry flagged
        assert result.flagged_entries[0].severity == Severity.MEDIUM  # diff=500, between 10-1000

    def test_rounding_tolerance(self):
        entries = [
            JournalEntry(entry_id="JE001", debit=100.005, credit=0, row_number=1),
            JournalEntry(entry_id="JE001", debit=0, credit=100.00, row_number=2),
        ]
        result = run_unbalanced_test(entries, JETestingConfig(balance_tolerance=0.01))
        assert result.entries_flagged == 0  # Within tolerance

    def test_multiple_groups(self):
        entries = [
            JournalEntry(entry_id="JE001", debit=100, credit=0, row_number=1),
            JournalEntry(entry_id="JE001", debit=0, credit=100, row_number=2),
            JournalEntry(entry_id="JE002", debit=200, credit=0, row_number=3),
            JournalEntry(entry_id="JE002", debit=0, credit=150, row_number=4),
        ]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.entries_flagged == 2  # Only JE002 lines flagged

    def test_fallback_to_reference(self):
        entries = [
            JournalEntry(reference="REF001", debit=100, credit=0, row_number=1),
            JournalEntry(reference="REF001", debit=0, credit=50, row_number=2),
        ]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.entries_flagged == 2

    def test_severity_based_on_difference(self):
        # Small difference = low severity
        entries = [
            JournalEntry(entry_id="JE001", debit=100, credit=0, row_number=1),
            JournalEntry(entry_id="JE001", debit=0, credit=95, row_number=2),
        ]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_test_key(self):
        entries = [JournalEntry(entry_id="JE001", debit=100, credit=0, row_number=1)]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.test_key == "unbalanced_entries"
        assert result.test_tier == TestTier.STRUCTURAL


# =============================================================================
# T2: MISSING FIELDS
# =============================================================================

class TestMissingFields:
    """Tests for test_missing_fields()."""

    def test_complete_entries_no_flags(self):
        entries = [
            JournalEntry(account="Cash", posting_date="2025-01-15", debit=100, row_number=1),
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_missing_account_flagged(self):
        entries = [
            JournalEntry(account="", posting_date="2025-01-15", debit=100, row_number=1),
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "account" in result.flagged_entries[0].issue

    def test_missing_date_flagged(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "date" in result.flagged_entries[0].issue

    def test_zero_amount_flagged(self):
        entries = [
            JournalEntry(account="Cash", posting_date="2025-01-15", debit=0, credit=0, row_number=1),
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "amount" in result.flagged_entries[0].issue

    def test_entry_date_sufficient(self):
        entries = [
            JournalEntry(account="Cash", entry_date="2025-01-15", debit=100, row_number=1),
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 0  # entry_date counts

    def test_multiple_missing_fields(self):
        entries = [
            JournalEntry(row_number=1),  # Missing everything
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        details = result.flagged_entries[0].details
        assert "account" in details["missing_fields"]
        assert "date" in details["missing_fields"]
        assert "amount" in details["missing_fields"]


# =============================================================================
# T3: DUPLICATE ENTRIES
# =============================================================================

class TestDuplicateEntries:
    """Tests for test_duplicate_entries()."""

    def test_no_duplicates(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="A", row_number=1),
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=200, description="B", row_number=2),
        ]
        result = run_duplicate_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_exact_duplicates_flagged(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Payment", row_number=1),
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Payment", row_number=2),
        ]
        result = run_duplicate_test(entries, JETestingConfig())
        assert result.entries_flagged == 2  # Both entries flagged

    def test_different_amounts_not_duplicate(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Payment", row_number=1),
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=101, description="Payment", row_number=2),
        ]
        result = run_duplicate_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_three_duplicates(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Pay", row_number=1),
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Pay", row_number=2),
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Pay", row_number=3),
        ]
        result = run_duplicate_test(entries, JETestingConfig())
        assert result.entries_flagged == 3
        assert result.flagged_entries[0].details["duplicate_count"] == 3

    def test_case_insensitive_matching(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Payment", row_number=1),
            JournalEntry(posting_date="2025-01-15", account="CASH", debit=100, description="payment", row_number=2),
        ]
        result = run_duplicate_test(entries, JETestingConfig())
        assert result.entries_flagged == 2


# =============================================================================
# T4: ROUND DOLLAR AMOUNTS
# =============================================================================

class TestRoundAmounts:
    """Tests for test_round_amounts()."""

    def test_no_round_amounts(self):
        entries = [
            JournalEntry(debit=1234.56, row_number=1),
            JournalEntry(debit=789.01, row_number=2),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_hundred_thousand_flagged(self):
        entries = [
            JournalEntry(debit=100000, row_number=1),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_fifty_thousand_flagged(self):
        entries = [
            JournalEntry(debit=50000, row_number=1),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_ten_thousand_flagged(self):
        entries = [
            JournalEntry(debit=10000, row_number=1),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_below_threshold_not_flagged(self):
        entries = [
            JournalEntry(debit=5000, row_number=1),  # Below default 10K threshold
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_custom_threshold(self):
        entries = [
            JournalEntry(debit=5000, row_number=1),
        ]
        config = JETestingConfig(round_amount_threshold=1000.0)
        result = run_round_amounts_test(entries, config)
        # 5000 is not divisible by 10000/50000/100000, so still no flag
        assert result.entries_flagged == 0

    def test_max_flags_respected(self):
        entries = [JournalEntry(debit=100000, row_number=i) for i in range(1, 100)]
        config = JETestingConfig(round_amount_max_flags=5)
        result = run_round_amounts_test(entries, config)
        assert result.entries_flagged <= 5

    def test_credit_amount_detected(self):
        entries = [
            JournalEntry(credit=200000, row_number=1),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_sorted_by_amount_descending(self):
        entries = [
            JournalEntry(debit=10000, row_number=1),
            JournalEntry(debit=100000, row_number=2),
            JournalEntry(debit=50000, row_number=3),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        amounts = [f.entry.abs_amount for f in result.flagged_entries]
        assert amounts == sorted(amounts, reverse=True)


# =============================================================================
# T5: UNUSUAL AMOUNTS
# =============================================================================

class TestUnusualAmounts:
    """Tests for test_unusual_amounts()."""

    def test_normal_amounts_no_flags(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=i)
            for i in range(1, 11)
        ]
        result = run_unusual_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_outlier_flagged(self):
        # 29 normal entries + 1 huge outlier (need enough entries so stdev stays small)
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=i)
            for i in range(1, 30)
        ]
        entries.append(JournalEntry(account="Cash", debit=100000, row_number=30))
        result = run_unusual_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].entry.debit == 100000

    def test_min_entries_threshold(self):
        # Only 3 entries, below min_entries of 5
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Cash", debit=100, row_number=2),
            JournalEntry(account="Cash", debit=100000, row_number=3),
        ]
        result = run_unusual_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_custom_stddev_threshold(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=i)
            for i in range(1, 10)
        ]
        entries.append(JournalEntry(account="Cash", debit=500, row_number=10))
        # With strict threshold (1 stddev), should flag more
        config = JETestingConfig(unusual_amount_stddev=1.0, unusual_amount_min_entries=3)
        result = run_unusual_amounts_test(entries, config)
        assert result.entries_flagged >= 1

    def test_per_account_grouping(self):
        # Two accounts, outlier in one — use 25 normal Cash + 1 outlier
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=i)
            for i in range(1, 26)
        ]
        entries.append(JournalEntry(account="Cash", debit=100000, row_number=26))
        entries.extend([
            JournalEntry(account="Revenue", debit=50000, row_number=i)
            for i in range(27, 34)
        ])
        result = run_unusual_amounts_test(entries, JETestingConfig())
        # Only Cash outlier should be flagged (Revenue amounts are consistent)
        flagged_accounts = {f.entry.account for f in result.flagged_entries}
        assert "Cash" in flagged_accounts

    def test_z_score_in_details(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=i)
            for i in range(1, 30)
        ]
        entries.append(JournalEntry(account="Cash", debit=100000, row_number=30))
        result = run_unusual_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged > 0
        assert "z_score" in result.flagged_entries[0].details

    def test_zero_amounts_excluded(self):
        entries = [
            JournalEntry(account="Cash", debit=0, credit=0, row_number=i)
            for i in range(1, 10)
        ]
        entries.append(JournalEntry(account="Cash", debit=100, row_number=10))
        result = run_unusual_amounts_test(entries, JETestingConfig())
        # Only 1 non-zero entry, below min_entries threshold
        assert result.entries_flagged == 0
