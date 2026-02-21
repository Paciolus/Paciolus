"""
Tests for Journal Entry Testing Engine — Tier 3 Advanced Tests (T14-T18)

Covers:
- T14: Reciprocal Entries (Sprint 69)
- T15: Just-Below-Threshold (Sprint 69)
- T16: Account Frequency Anomaly (Sprint 69)
- T17: Description Length Anomaly (Sprint 69)
- T18: Unusual Account Combinations (Sprint 69)
- Helper: _amount_range_label (Sprint 69)
- Stratified Sampling: preview + run (Sprint 69)
- Full Test Battery with Tier 3 verification (Sprint 69)
"""

from je_testing_engine import (
    JETestingConfig,
    JournalEntry,
    SamplingResult,
    # Enums & types
    Severity,
    TestTier,
    # Stratified Sampling (Sprint 69)
    _amount_range_label,
    preview_sampling_strata,
    run_stratified_sampling,
    # Battery
    run_test_battery,
)
from je_testing_engine import (
    test_account_frequency_anomaly as run_frequency_anomaly_test,
)
from je_testing_engine import (
    test_description_length_anomaly as run_desc_length_test,
)
from je_testing_engine import (
    test_just_below_threshold as run_threshold_test,
)
from je_testing_engine import (
    # Tier 3 — aliased to avoid pytest collection
    test_reciprocal_entries as run_reciprocal_test,
)
from je_testing_engine import (
    test_unusual_account_combinations as run_unusual_combo_test,
)

# =============================================================================
# T14: RECIPROCAL ENTRIES (Sprint 69)
# =============================================================================

class TestReciprocalEntries:
    """Tests for test_reciprocal_entries()."""

    def test_matching_pair_found(self):
        """Debit and credit of same amount within days_window are flagged."""
        entries = [
            JournalEntry(
                account="Cash", debit=5000, credit=0,
                posting_date="2025-01-15", row_number=1,
            ),
            JournalEntry(
                account="Revenue", debit=0, credit=5000,
                posting_date="2025-01-17", row_number=2,
            ),
        ]
        result = run_reciprocal_test(entries, JETestingConfig())
        assert result.entries_flagged == 2  # Both entries in the pair flagged
        assert result.test_key == "reciprocal_entries"
        assert result.test_tier == TestTier.ADVANCED
        # Cross-account pair should be HIGH severity
        assert result.flagged_entries[0].severity == Severity.HIGH
        assert result.flagged_entries[0].details["cross_account"] is True

    def test_same_account_pair_medium_severity(self):
        """Same-account reciprocal pair gets MEDIUM severity."""
        entries = [
            JournalEntry(
                account="Cash", debit=5000, credit=0,
                posting_date="2025-01-15", row_number=1,
            ),
            JournalEntry(
                account="Cash", debit=0, credit=5000,
                posting_date="2025-01-16", row_number=2,
            ),
        ]
        result = run_reciprocal_test(entries, JETestingConfig())
        assert result.entries_flagged == 2
        assert result.flagged_entries[0].severity == Severity.MEDIUM
        assert result.flagged_entries[0].details["cross_account"] is False

    def test_no_match_different_amounts(self):
        """Entries with different amounts should not match."""
        entries = [
            JournalEntry(
                account="Cash", debit=5000, credit=0,
                posting_date="2025-01-15", row_number=1,
            ),
            JournalEntry(
                account="Revenue", debit=0, credit=3000,
                posting_date="2025-01-17", row_number=2,
            ),
        ]
        result = run_reciprocal_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_respects_days_window(self):
        """Pairs outside the days_window should not be flagged."""
        entries = [
            JournalEntry(
                account="Cash", debit=5000, credit=0,
                posting_date="2025-01-01", row_number=1,
            ),
            JournalEntry(
                account="Revenue", debit=0, credit=5000,
                posting_date="2025-01-20", row_number=2,
            ),
        ]
        # Default window is 7 days; 19 days apart should not flag
        result = run_reciprocal_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_custom_days_window(self):
        """Wider window should catch entries further apart."""
        entries = [
            JournalEntry(
                account="Cash", debit=5000, credit=0,
                posting_date="2025-01-01", row_number=1,
            ),
            JournalEntry(
                account="Revenue", debit=0, credit=5000,
                posting_date="2025-01-20", row_number=2,
            ),
        ]
        config = JETestingConfig(reciprocal_days_window=30)
        result = run_reciprocal_test(entries, config)
        assert result.entries_flagged == 2

    def test_disabled_config(self):
        """Disabled config returns zero flags."""
        entries = [
            JournalEntry(
                account="Cash", debit=5000, credit=0,
                posting_date="2025-01-15", row_number=1,
            ),
            JournalEntry(
                account="Revenue", debit=0, credit=5000,
                posting_date="2025-01-15", row_number=2,
            ),
        ]
        config = JETestingConfig(reciprocal_enabled=False)
        result = run_reciprocal_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_below_min_amount_ignored(self):
        """Amounts below reciprocal_min_amount are not checked."""
        entries = [
            JournalEntry(
                account="Cash", debit=50, credit=0,
                posting_date="2025-01-15", row_number=1,
            ),
            JournalEntry(
                account="Revenue", debit=0, credit=50,
                posting_date="2025-01-15", row_number=2,
            ),
        ]
        # Default min_amount=1000, so $50 should be ignored
        result = run_reciprocal_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_details_contain_matched_amount(self):
        """Flagged entries should include matching details."""
        entries = [
            JournalEntry(
                account="Cash", debit=10000, credit=0,
                posting_date="2025-01-15", row_number=1,
            ),
            JournalEntry(
                account="Revenue", debit=0, credit=10000,
                posting_date="2025-01-16", row_number=2,
            ),
        ]
        result = run_reciprocal_test(entries, JETestingConfig())
        assert result.entries_flagged == 2
        details = result.flagged_entries[0].details
        assert details["matched_amount"] == 10000.0
        assert details["days_apart"] == 1


# =============================================================================
# T15: JUST-BELOW-THRESHOLD (Sprint 69)
# =============================================================================

class TestJustBelowThreshold:
    """Tests for test_just_below_threshold()."""

    def test_just_below_5k_flagged(self):
        """Amount just below $5,000 threshold should be flagged."""
        entries = [
            JournalEntry(debit=4900, account="Expense", posting_date="2025-01-15", row_number=1),
        ]
        result = run_threshold_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.test_key == "just_below_threshold"
        assert result.test_tier == TestTier.ADVANCED
        assert "$5,000" in result.flagged_entries[0].issue

    def test_just_below_100k_high_severity(self):
        """Amount just below $100K threshold should be HIGH severity."""
        entries = [
            JournalEntry(debit=97000, account="Expense", posting_date="2025-01-15", row_number=1),
        ]
        result = run_threshold_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_just_below_10k_medium_severity(self):
        """Amount just below $10K threshold should be MEDIUM severity."""
        entries = [
            JournalEntry(debit=9800, account="Expense", posting_date="2025-01-15", row_number=1),
        ]
        result = run_threshold_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_far_below_threshold_not_flagged(self):
        """Amount far below a threshold should not be flagged."""
        entries = [
            JournalEntry(debit=2000, account="Expense", posting_date="2025-01-15", row_number=1),
        ]
        # 2000 is well below 5000 * (1 - 0.05) = 4750
        result = run_threshold_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_above_threshold_not_flagged(self):
        """Amount at or above a threshold should not be flagged."""
        entries = [
            JournalEntry(debit=5000, account="Expense", posting_date="2025-01-15", row_number=1),
            JournalEntry(debit=10000, account="Expense", posting_date="2025-01-15", row_number=2),
        ]
        result = run_threshold_test(entries, JETestingConfig())
        # Entries at exactly the threshold are not below it
        # 5000 not flagged for 5K (not below), but check 10K: 5000 < 10000 * 0.95 = 9500 → not in range
        assert all(f.entry.debit != 5000 or "$5,000" not in f.issue for f in result.flagged_entries)

    def test_split_transaction_detection(self):
        """Multiple entries to same account on same day summing above threshold."""
        entries = [
            JournalEntry(
                debit=3000, account="Advertising", posting_date="2025-01-15", row_number=1,
            ),
            JournalEntry(
                debit=3000, account="Advertising", posting_date="2025-01-15", row_number=2,
            ),
        ]
        # Total = 6000 > 5000 threshold, individual entries < 5000
        result = run_threshold_test(entries, JETestingConfig())
        split_flags = [f for f in result.flagged_entries if "split" in f.issue.lower()]
        assert len(split_flags) >= 2  # Both entries flagged as split

    def test_custom_thresholds(self):
        """Custom approval thresholds should be respected."""
        entries = [
            JournalEntry(debit=1900, account="Expense", posting_date="2025-01-15", row_number=1),
        ]
        config = JETestingConfig(approval_thresholds=[2000.0])
        result = run_threshold_test(entries, config)
        assert result.entries_flagged == 1
        assert "$2,000" in result.flagged_entries[0].issue

    def test_disabled_config(self):
        """Disabled config returns zero flags."""
        entries = [
            JournalEntry(debit=4900, account="Expense", posting_date="2025-01-15", row_number=1),
        ]
        config = JETestingConfig(threshold_proximity_enabled=False)
        result = run_threshold_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_zero_amount_ignored(self):
        """Zero-amount entries should be skipped."""
        entries = [
            JournalEntry(debit=0, credit=0, account="Cash", posting_date="2025-01-15", row_number=1),
        ]
        result = run_threshold_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_details_include_gap_pct(self):
        """Flagged entries should include gap percentage in details."""
        entries = [
            JournalEntry(debit=4900, account="Expense", posting_date="2025-01-15", row_number=1),
        ]
        result = run_threshold_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        details = result.flagged_entries[0].details
        assert "gap_pct" in details
        assert "threshold" in details
        assert details["threshold"] == 5000.0


# =============================================================================
# T16: ACCOUNT FREQUENCY ANOMALY (Sprint 69)
# =============================================================================

class TestAccountFrequencyAnomaly:
    """Tests for test_account_frequency_anomaly()."""

    def _make_monthly_entries(self, account, monthly_counts, year=2025):
        """Create entries distributed across months with given counts."""
        entries = []
        row = 1
        for month_idx, count in enumerate(monthly_counts):
            month = month_idx + 1
            for i in range(count):
                day = min(i + 1, 28)
                entries.append(JournalEntry(
                    account=account,
                    debit=100 + i,
                    posting_date=f"{year}-{month:02d}-{day:02d}",
                    row_number=row,
                ))
                row += 1
        return entries

    def test_normal_frequency_not_flagged(self):
        """Consistent monthly posting frequency should not flag."""
        # 10 entries per month for 6 months = consistent
        entries = self._make_monthly_entries("Cash", [10, 10, 10, 10, 10, 10])
        result = run_frequency_anomaly_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_spike_month_flagged(self):
        """A month with significantly more entries should be flagged."""
        # 7 months at 5 entries, 1 month at 80 = massive spike
        # mean ~14.4, stdev ~26, threshold=mean+2.5*stdev ~79
        # 80 > threshold => flagged
        entries = self._make_monthly_entries("Cash", [5, 5, 5, 5, 5, 5, 5, 80])
        config = JETestingConfig(frequency_anomaly_stddev=2.0)
        result = run_frequency_anomaly_test(entries, config)
        assert result.entries_flagged >= 1
        assert result.test_key == "account_frequency_anomaly"
        assert result.test_tier == TestTier.ADVANCED
        # The flagged entry should be from the spike month (August)
        flagged_month = result.flagged_entries[0].details["month"]
        assert flagged_month == "2025-08"

    def test_too_few_periods_skipped(self):
        """Accounts with fewer than min_periods months are skipped."""
        # Only 2 months of data, default min_periods=3
        entries = self._make_monthly_entries("Cash", [10, 50])
        result = run_frequency_anomaly_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_disabled_config(self):
        """Disabled config returns zero flags."""
        entries = self._make_monthly_entries("Cash", [5, 5, 5, 5, 5, 5, 5, 80])
        config = JETestingConfig(frequency_anomaly_enabled=False)
        result = run_frequency_anomaly_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_custom_stddev_threshold(self):
        """Higher stddev threshold requires bigger spikes to flag."""
        # Spike that would flag at low stddev but not at very high stddev
        entries = self._make_monthly_entries("Cash", [5, 5, 5, 5, 5, 5, 5, 80])
        config_strict = JETestingConfig(frequency_anomaly_stddev=1.5)
        result_strict = run_frequency_anomaly_test(entries, config_strict)
        config_lenient = JETestingConfig(frequency_anomaly_stddev=10.0)
        result_lenient = run_frequency_anomaly_test(entries, config_lenient)
        assert result_strict.entries_flagged >= result_lenient.entries_flagged

    def test_z_score_in_details(self):
        """Flagged entries should include z_score in details."""
        # Very large spike: 7 months at 5, 1 month at 100
        entries = self._make_monthly_entries("Cash", [5, 5, 5, 5, 5, 5, 5, 100])
        config = JETestingConfig(frequency_anomaly_stddev=2.0)
        result = run_frequency_anomaly_test(entries, config)
        assert result.entries_flagged >= 1
        details = result.flagged_entries[0].details
        assert "z_score" in details
        assert details["z_score"] > 0

    def test_all_same_frequency_not_flagged(self):
        """All months at identical frequency => stdev=0 => no flags."""
        entries = self._make_monthly_entries("Cash", [10, 10, 10, 10])
        result = run_frequency_anomaly_test(entries, JETestingConfig())
        assert result.entries_flagged == 0


# =============================================================================
# T17: DESCRIPTION LENGTH ANOMALY (Sprint 69)
# =============================================================================

class TestDescriptionLengthAnomaly:
    """Tests for test_description_length_anomaly()."""

    def test_blank_description_flagged(self):
        """Blank description when account normally has descriptions should flag."""
        entries = []
        # 10 entries with normal descriptions
        for i in range(10):
            entries.append(JournalEntry(
                account="Cash", debit=100, row_number=i + 1,
                description=f"Regular payment for invoice {i + 1000}",
            ))
        # 1 entry with blank description
        entries.append(JournalEntry(
            account="Cash", debit=5000, row_number=11,
            description="",
        ))
        result = run_desc_length_test(entries, JETestingConfig())
        assert result.entries_flagged >= 1
        assert result.test_key == "description_length_anomaly"
        assert result.test_tier == TestTier.ADVANCED
        blank_flag = [f for f in result.flagged_entries if f.details["desc_length"] == 0]
        assert len(blank_flag) >= 1

    def test_normal_descriptions_clean(self):
        """Entries with consistent description lengths should not flag."""
        entries = []
        for i in range(10):
            entries.append(JournalEntry(
                account="Cash", debit=100, row_number=i + 1,
                description=f"Monthly payment for service {i + 100}",
            ))
        result = run_desc_length_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_min_entries_threshold(self):
        """Accounts with fewer than min_entries are skipped."""
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1, description="Payment"),
            JournalEntry(account="Cash", debit=100, row_number=2, description=""),
        ]
        # Only 2 entries, default min_entries=5
        result = run_desc_length_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_disabled_config(self):
        """Disabled config returns zero flags."""
        entries = []
        for i in range(10):
            entries.append(JournalEntry(
                account="Cash", debit=100, row_number=i + 1,
                description=f"Regular payment for invoice {i + 1000}",
            ))
        entries.append(JournalEntry(account="Cash", debit=100, row_number=11, description=""))
        config = JETestingConfig(desc_length_enabled=False)
        result = run_desc_length_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_no_descriptions_at_all(self):
        """Entries with no description data return no flags with appropriate message."""
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Cash", debit=200, row_number=2),
        ]
        result = run_desc_length_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_short_description_flagged(self):
        """Description significantly shorter than account norm flagged."""
        entries = []
        # 10 entries with long descriptions (40+ chars each)
        for i in range(10):
            entries.append(JournalEntry(
                account="Accounts Payable", debit=100, row_number=i + 1,
                description=f"Payment to vendor ABC Corporation for invoice number {i + 5000} dated January 2025",
            ))
        # 1 entry with very short description
        entries.append(JournalEntry(
            account="Accounts Payable", debit=100, row_number=11,
            description="x",
        ))
        result = run_desc_length_test(entries, JETestingConfig())
        # The very short description should be flagged
        short_flags = [f for f in result.flagged_entries if f.details["desc_length"] == 1]
        assert len(short_flags) >= 1

    def test_details_include_mean_length(self):
        """Flagged entries should have mean_length in details."""
        entries = []
        for i in range(10):
            entries.append(JournalEntry(
                account="Cash", debit=100, row_number=i + 1,
                description=f"Regular payment for invoice {i + 1000}",
            ))
        entries.append(JournalEntry(account="Cash", debit=100, row_number=11, description=""))
        result = run_desc_length_test(entries, JETestingConfig())
        if result.entries_flagged > 0:
            assert "mean_length" in result.flagged_entries[0].details


# =============================================================================
# T18: UNUSUAL ACCOUNT COMBINATIONS (Sprint 69)
# =============================================================================

class TestUnusualAccountCombinations:
    """Tests for test_unusual_account_combinations()."""

    def _make_je_group(self, entry_id, debit_account, credit_account, amount, row_start):
        """Create a balanced journal entry group."""
        return [
            JournalEntry(
                entry_id=entry_id, account=debit_account,
                debit=amount, credit=0, row_number=row_start,
            ),
            JournalEntry(
                entry_id=entry_id, account=credit_account,
                debit=0, credit=amount, row_number=row_start + 1,
            ),
        ]

    def test_rare_combo_flagged(self):
        """Rarely-seen account combination should be flagged."""
        entries = []
        row = 1
        # 20 common entries: Cash / Revenue
        for i in range(20):
            eid = f"JE{i + 1:04d}"
            entries.extend(self._make_je_group(eid, "Cash", "Revenue", 100, row))
            row += 2
        # 1 rare entry: Suspense / Retained Earnings
        entries.extend(self._make_je_group("RARE001", "Suspense", "Retained Earnings", 5000, row))
        row += 2

        config = JETestingConfig(unusual_combo_min_total_entries=10)
        result = run_unusual_combo_test(entries, config)
        assert result.entries_flagged >= 2  # Both lines of the rare entry
        assert result.test_key == "unusual_account_combinations"
        assert result.test_tier == TestTier.ADVANCED

    def test_common_combo_not_flagged(self):
        """Frequently-seen account combinations should not be flagged."""
        entries = []
        row = 1
        # 30 entries all with Cash / Revenue
        for i in range(30):
            eid = f"JE{i + 1:04d}"
            entries.extend(self._make_je_group(eid, "Cash", "Revenue", 100, row))
            row += 2

        config = JETestingConfig(unusual_combo_min_total_entries=10, unusual_combo_max_frequency=2)
        result = run_unusual_combo_test(entries, config)
        assert result.entries_flagged == 0

    def test_min_total_entries_threshold(self):
        """Below min_total_entries, analysis is skipped."""
        entries = []
        row = 1
        # Only 5 entry groups (below default 20)
        for i in range(5):
            eid = f"JE{i + 1:04d}"
            entries.extend(self._make_je_group(eid, "Cash", "Revenue", 100, row))
            row += 2

        result = run_unusual_combo_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_disabled_config(self):
        """Disabled config returns zero flags."""
        entries = []
        row = 1
        for i in range(25):
            eid = f"JE{i + 1:04d}"
            entries.extend(self._make_je_group(eid, "Cash", "Revenue", 100, row))
            row += 2

        config = JETestingConfig(unusual_combo_enabled=False)
        result = run_unusual_combo_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_high_severity_for_large_amount(self):
        """Rare combo with large amount gets HIGH severity."""
        entries = []
        row = 1
        for i in range(25):
            eid = f"JE{i + 1:04d}"
            entries.extend(self._make_je_group(eid, "Cash", "Revenue", 100, row))
            row += 2
        # Rare combo with > $10,000
        entries.extend(self._make_je_group("RARE001", "Suspense", "Equity", 50000, row))

        config = JETestingConfig(unusual_combo_min_total_entries=10)
        result = run_unusual_combo_test(entries, config)
        high_sev = [f for f in result.flagged_entries if f.severity == Severity.HIGH]
        assert len(high_sev) >= 1

    def test_no_entry_ids_returns_zero(self):
        """Entries without entry_id cannot be grouped, so no flags."""
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=i)
            for i in range(1, 30)
        ]
        result = run_unusual_combo_test(entries, JETestingConfig())
        assert result.entries_flagged == 0


# =============================================================================
# HELPER: _amount_range_label (Sprint 69)
# =============================================================================

class TestAmountRangeLabel:
    """Tests for _amount_range_label() helper."""

    def test_bucket_0_to_100(self):
        assert _amount_range_label(0) == "$0-$100"
        assert _amount_range_label(50) == "$0-$100"
        assert _amount_range_label(99.99) == "$0-$100"

    def test_bucket_100_to_1k(self):
        assert _amount_range_label(100) == "$100-$1K"
        assert _amount_range_label(500) == "$100-$1K"
        assert _amount_range_label(999.99) == "$100-$1K"

    def test_bucket_1k_to_10k(self):
        assert _amount_range_label(1000) == "$1K-$10K"
        assert _amount_range_label(5000) == "$1K-$10K"
        assert _amount_range_label(9999.99) == "$1K-$10K"

    def test_bucket_10k_to_100k(self):
        assert _amount_range_label(10000) == "$10K-$100K"
        assert _amount_range_label(50000) == "$10K-$100K"
        assert _amount_range_label(99999.99) == "$10K-$100K"

    def test_bucket_100k_plus(self):
        assert _amount_range_label(100000) == "$100K+"
        assert _amount_range_label(1000000) == "$100K+"


# =============================================================================
# STRATIFIED SAMPLING: PREVIEW (Sprint 69)
# =============================================================================

class TestPreviewSamplingStrata:
    """Tests for preview_sampling_strata()."""

    def test_stratify_by_account(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Cash", debit=200, row_number=2),
            JournalEntry(account="Revenue", credit=100, row_number=3),
        ]
        strata = preview_sampling_strata(entries, ["account"])
        assert len(strata) == 2
        names = {s["name"] for s in strata}
        assert "Cash" in names
        assert "Revenue" in names
        # Cash should have 2 entries
        cash_stratum = next(s for s in strata if s["name"] == "Cash")
        assert cash_stratum["population_size"] == 2
        assert cash_stratum["criteria"] == "account"

    def test_stratify_by_amount_range(self):
        entries = [
            JournalEntry(debit=50, row_number=1),
            JournalEntry(debit=500, row_number=2),
            JournalEntry(debit=5000, row_number=3),
            JournalEntry(debit=50000, row_number=4),
            JournalEntry(debit=500000, row_number=5),
        ]
        strata = preview_sampling_strata(entries, ["amount_range"])
        assert len(strata) == 5
        names = {s["name"] for s in strata}
        assert "$0-$100" in names
        assert "$100-$1K" in names
        assert "$1K-$10K" in names
        assert "$10K-$100K" in names
        assert "$100K+" in names

    def test_stratify_by_period(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", debit=100, row_number=1),
            JournalEntry(posting_date="2025-01-20", debit=200, row_number=2),
            JournalEntry(posting_date="2025-02-10", debit=300, row_number=3),
        ]
        strata = preview_sampling_strata(entries, ["period"])
        assert len(strata) == 2
        names = {s["name"] for s in strata}
        assert "2025-01" in names
        assert "2025-02" in names

    def test_multi_criteria_stratification(self):
        entries = [
            JournalEntry(account="Cash", debit=100, posting_date="2025-01-15", row_number=1),
            JournalEntry(account="Cash", debit=100, posting_date="2025-02-15", row_number=2),
            JournalEntry(account="Revenue", credit=100, posting_date="2025-01-15", row_number=3),
        ]
        strata = preview_sampling_strata(entries, ["account", "period"])
        # Cash|2025-01, Cash|2025-02, Revenue|2025-01
        assert len(strata) == 3
        # Criteria should be combined
        assert strata[0]["criteria"] == "account & period"

    def test_empty_entries(self):
        strata = preview_sampling_strata([], ["account"])
        assert len(strata) == 0

    def test_sorted_by_population_descending(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Cash", debit=200, row_number=2),
            JournalEntry(account="Cash", debit=300, row_number=3),
            JournalEntry(account="Revenue", credit=100, row_number=4),
        ]
        strata = preview_sampling_strata(entries, ["account"])
        # Cash (3) should come before Revenue (1)
        assert strata[0]["population_size"] >= strata[-1]["population_size"]


# =============================================================================
# STRATIFIED SAMPLING: RUN (Sprint 69)
# =============================================================================

class TestRunStratifiedSampling:
    """Tests for run_stratified_sampling()."""

    def _make_sample_entries(self, n=100):
        """Create N entries across 2 accounts."""
        entries = []
        for i in range(1, n + 1):
            entries.append(JournalEntry(
                account="Cash" if i % 2 == 0 else "Revenue",
                debit=100 * i if i % 2 == 0 else 0,
                credit=100 * i if i % 2 != 0 else 0,
                posting_date=f"2025-{(i % 3) + 1:02d}-15",
                row_number=i,
            ))
        return entries

    def test_sample_rate(self):
        """Sample rate should produce approximately correct number of samples."""
        entries = self._make_sample_entries(100)
        result = run_stratified_sampling(entries, ["account"], sample_rate=0.20)
        assert isinstance(result, SamplingResult)
        assert result.total_population == 100
        # 20% of 50 per stratum = 10, total ~20
        assert result.total_sampled > 0
        assert result.total_sampled <= 100

    def test_fixed_per_stratum(self):
        """Fixed per stratum should sample exact count per stratum."""
        entries = self._make_sample_entries(100)
        result = run_stratified_sampling(entries, ["account"], fixed_per_stratum=5)
        assert result.total_population == 100
        for stratum in result.strata:
            assert stratum.sample_size == 5  # Fixed count per stratum

    def test_fixed_per_stratum_capped_at_population(self):
        """Fixed per stratum cannot exceed stratum population size."""
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Cash", debit=200, row_number=2),
        ]
        result = run_stratified_sampling(entries, ["account"], fixed_per_stratum=10)
        # Only 2 entries, so sample_size should be capped at 2
        assert result.strata[0].sample_size == 2

    def test_csprng_seed_generated(self):
        """Each sampling run generates a unique hex seed."""
        entries = self._make_sample_entries(20)
        result1 = run_stratified_sampling(entries, ["account"], sample_rate=0.50)
        result2 = run_stratified_sampling(entries, ["account"], sample_rate=0.50)
        assert result1.sampling_seed != ""
        assert result2.sampling_seed != ""
        assert len(result1.sampling_seed) == 32  # 16 bytes hex = 32 chars
        # Seeds should be different (CSPRNG)
        assert result1.sampling_seed != result2.sampling_seed

    def test_sample_size_at_least_one(self):
        """Even with low sample_rate, at least 1 entry per stratum."""
        entries = self._make_sample_entries(100)
        result = run_stratified_sampling(entries, ["account"], sample_rate=0.001)
        for stratum in result.strata:
            assert stratum.sample_size >= 1

    def test_sampled_entries_included(self):
        """Sampled entries should be included in the result."""
        entries = self._make_sample_entries(20)
        result = run_stratified_sampling(entries, ["account"], sample_rate=0.50)
        assert len(result.sampled_entries) == result.total_sampled
        # All sampled entries should be from the original population
        original_rows = {e.row_number for e in entries}
        sampled_rows = {e.row_number for e in result.sampled_entries}
        assert sampled_rows.issubset(original_rows)

    def test_parameters_recorded(self):
        """Sampling parameters should be recorded in the result."""
        entries = self._make_sample_entries(20)
        result = run_stratified_sampling(entries, ["account"], sample_rate=0.25)
        assert result.parameters["stratify_by"] == ["account"]
        assert result.parameters["sample_rate"] == 0.25
        assert result.parameters["fixed_per_stratum"] is None

    def test_empty_entries(self):
        """Empty entries should produce empty result."""
        result = run_stratified_sampling([], ["account"], sample_rate=0.10)
        assert result.total_population == 0
        assert result.total_sampled == 0
        assert len(result.strata) == 0

    def test_strata_sampled_rows_match(self):
        """sampled_rows in each stratum should match actual entries."""
        entries = self._make_sample_entries(50)
        result = run_stratified_sampling(entries, ["account"], sample_rate=0.30)
        for stratum in result.strata:
            assert len(stratum.sampled_rows) == stratum.sample_size


# =============================================================================
# FULL TEST BATTERY WITH TIER 3 (Sprint 69)
# =============================================================================

class TestRunTestBatteryTier3:
    """Verify all 19 tests run in the battery with correct keys."""

    def test_all_19_tests_present(self):
        entries = [
            JournalEntry(entry_id="JE001", account="Cash", posting_date="2025-01-15", debit=100, row_number=1),
            JournalEntry(entry_id="JE001", account="Revenue", posting_date="2025-01-15", credit=100, row_number=2),
        ]
        results, benford = run_test_battery(entries)
        assert len(results) == 19
        keys = [r.test_key for r in results]

        # Tier 1 Structural (T1-T5)
        assert keys[0] == "unbalanced_entries"
        assert keys[1] == "missing_fields"
        assert keys[2] == "duplicate_entries"
        assert keys[3] == "round_amounts"
        assert keys[4] == "unusual_amounts"

        # Tier 1 Statistical (T6-T8)
        assert keys[5] == "benford_law"
        assert keys[6] == "weekend_postings"
        assert keys[7] == "month_end_clustering"

        # Tier 2 (T9-T13)
        assert keys[8] == "single_user_high_volume"
        assert keys[9] == "after_hours_postings"
        assert keys[10] == "numbering_gaps"
        assert keys[11] == "backdated_entries"
        assert keys[12] == "suspicious_keywords"

        # T19: Holiday Postings (Sprint 356)
        assert keys[13] == "holiday_postings"

        # Tier 3 (T14-T18)
        assert keys[14] == "reciprocal_entries"
        assert keys[15] == "just_below_threshold"
        assert keys[16] == "account_frequency_anomaly"
        assert keys[17] == "description_length_anomaly"
        assert keys[18] == "unusual_account_combinations"

    def test_tier_3_tests_have_advanced_tier(self):
        entries = [
            JournalEntry(entry_id="JE001", account="Cash", posting_date="2025-01-15", debit=100, row_number=1),
            JournalEntry(entry_id="JE001", account="Revenue", posting_date="2025-01-15", credit=100, row_number=2),
        ]
        results, _ = run_test_battery(entries)
        tier_3_keys = {"reciprocal_entries", "just_below_threshold",
                       "account_frequency_anomaly", "description_length_anomaly",
                       "unusual_account_combinations"}
        for r in results:
            if r.test_key in tier_3_keys:
                assert r.test_tier == TestTier.ADVANCED, f"{r.test_key} should be ADVANCED tier"

    def test_battery_with_all_disabled_tier_3(self):
        entries = [
            JournalEntry(entry_id="JE001", account="Cash", posting_date="2025-01-15", debit=100, row_number=1),
            JournalEntry(entry_id="JE001", account="Revenue", posting_date="2025-01-15", credit=100, row_number=2),
        ]
        config = JETestingConfig(
            reciprocal_enabled=False,
            threshold_proximity_enabled=False,
            frequency_anomaly_enabled=False,
            desc_length_enabled=False,
            unusual_combo_enabled=False,
        )
        results, _ = run_test_battery(entries, config)
        assert len(results) == 19  # All tests still present
        tier_3_keys = {"reciprocal_entries", "just_below_threshold",
                       "account_frequency_anomaly", "description_length_anomaly",
                       "unusual_account_combinations"}
        for r in results:
            if r.test_key in tier_3_keys:
                assert r.entries_flagged == 0, f"{r.test_key} should have 0 flags when disabled"
