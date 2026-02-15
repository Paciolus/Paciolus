"""
Tests for Journal Entry Testing Engine — Tier 2 Tests (T9-T13)

Covers:
- Helper functions: _extract_hour, _extract_number (Sprint 68)
- T9: Single-User High Volume (Sprint 68)
- T10: After-Hours Postings (Sprint 68)
- T11: Sequential Numbering Gaps (Sprint 68)
- T12: Backdated Entries (Sprint 68)
- T13: Suspicious Keywords (Sprint 68)
"""

import pytest
from je_testing_engine import (
    JournalEntry,
    JETestingConfig,
    # Tier 2 — aliased to avoid pytest collection
    test_single_user_high_volume as run_single_user_test,
    test_after_hours_postings as run_after_hours_test,
    test_numbering_gaps as run_numbering_gaps_test,
    test_backdated_entries as run_backdated_test,
    test_suspicious_keywords as run_suspicious_keywords_test,
    SUSPICIOUS_KEYWORDS,
    _extract_hour,
    _extract_number,
    # Enums & types
    Severity,
    TestTier,
)


# =============================================================================
# TIER 2 HELPERS: _extract_hour and _extract_number (Sprint 68)
# =============================================================================

class TestExtractHour:
    """Tests for _extract_hour() helper."""

    def test_iso_datetime(self):
        assert _extract_hour("2025-01-15 14:30:00") == 14

    def test_midnight(self):
        assert _extract_hour("2025-01-15 00:00:00") == 0

    def test_late_night(self):
        assert _extract_hour("2025-01-15 23:59:00") == 23

    def test_date_only_returns_none(self):
        assert _extract_hour("2025-01-15") is None

    def test_none_returns_none(self):
        assert _extract_hour(None) is None

    def test_empty_string_returns_none(self):
        assert _extract_hour("") is None

    def test_us_datetime_format(self):
        assert _extract_hour("01/15/2025 09:30:00") == 9

    def test_iso_t_separator(self):
        assert _extract_hour("2025-01-15T18:00:00") == 18

    def test_no_seconds(self):
        assert _extract_hour("2025-01-15 14:30") == 14


class TestExtractNumber:
    """Tests for _extract_number() helper."""

    def test_prefixed_id(self):
        assert _extract_number("JE-001") == 1

    def test_plain_number(self):
        assert _extract_number("1234") == 1234

    def test_none_returns_none(self):
        assert _extract_number(None) is None

    def test_empty_string_returns_none(self):
        assert _extract_number("") is None

    def test_no_numeric_returns_none(self):
        assert _extract_number("ABC") is None

    def test_hash_prefix(self):
        assert _extract_number("#500") == 500

    def test_gj_prefix(self):
        assert _extract_number("GJ-0042") == 42

    def test_jv_prefix(self):
        assert _extract_number("JV100") == 100


# =============================================================================
# T9: SINGLE-USER HIGH VOLUME (Sprint 68)
# =============================================================================

class TestSingleUserHighVolume:
    """Tests for test_single_user_high_volume()."""

    def test_no_posted_by_data(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Revenue", credit=100, row_number=2),
        ]
        result = run_single_user_test(entries, JETestingConfig())
        assert result.entries_flagged == 0
        assert "posted_by" in result.description.lower()

    def test_evenly_distributed_users_no_flags(self):
        entries = []
        users = ["alice", "bob", "carol", "dave"]
        for i, user in enumerate(users):
            for j in range(10):
                entries.append(JournalEntry(
                    account="Cash", debit=100, posted_by=user,
                    row_number=i * 10 + j + 1,
                ))
        result = run_single_user_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_single_user_above_threshold_flagged(self):
        entries = []
        # alice posts 30 out of 40 entries = 75%
        for i in range(30):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="alice", row_number=i + 1,
            ))
        for i in range(10):
            entries.append(JournalEntry(
                account="Revenue", credit=100, posted_by="bob", row_number=31 + i,
            ))
        result = run_single_user_test(entries, JETestingConfig())
        assert result.entries_flagged > 0
        assert result.flagged_entries[0].details["user"] == "alice"

    def test_severity_high_above_50_pct(self):
        entries = []
        # alice = 60%, bob = 40%
        for i in range(60):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="alice", row_number=i + 1,
            ))
        for i in range(40):
            entries.append(JournalEntry(
                account="Revenue", credit=100, posted_by="bob", row_number=61 + i,
            ))
        result = run_single_user_test(entries, JETestingConfig())
        assert result.entries_flagged > 0
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_severity_medium_below_50_pct(self):
        entries = []
        # alice = 30%, bob = 35%, carol = 35%
        for i in range(30):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="alice", row_number=i + 1,
            ))
        for i in range(35):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="bob", row_number=31 + i,
            ))
        for i in range(35):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="carol", row_number=66 + i,
            ))
        result = run_single_user_test(entries, JETestingConfig())
        assert result.entries_flagged > 0
        for f in result.flagged_entries:
            assert f.severity == Severity.MEDIUM

    def test_max_flags_per_user_respected(self):
        entries = []
        # alice posts 50 entries out of 60 (83%)
        for i in range(50):
            entries.append(JournalEntry(
                account="Cash", debit=100 + i, posted_by="alice", row_number=i + 1,
            ))
        for i in range(10):
            entries.append(JournalEntry(
                account="Revenue", credit=100, posted_by="bob", row_number=51 + i,
            ))
        config = JETestingConfig(single_user_max_flags=5)
        result = run_single_user_test(entries, config)
        assert result.entries_flagged <= 5

    def test_custom_volume_threshold(self):
        entries = []
        # alice = 15%, bob = 85%: with threshold at 10%, alice gets flagged too
        for i in range(15):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="alice", row_number=i + 1,
            ))
        for i in range(85):
            entries.append(JournalEntry(
                account="Revenue", credit=100, posted_by="bob", row_number=16 + i,
            ))
        config = JETestingConfig(single_user_volume_pct=0.10)
        result = run_single_user_test(entries, config)
        # Both alice (15%) and bob (85%) exceed 10%
        flagged_users = {f.details["user"] for f in result.flagged_entries}
        assert "alice" in flagged_users
        assert "bob" in flagged_users

    def test_test_key_and_tier(self):
        entries = [JournalEntry(account="Cash", debit=100, row_number=1)]
        result = run_single_user_test(entries, JETestingConfig())
        assert result.test_key == "single_user_high_volume"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# T10: AFTER-HOURS POSTINGS (Sprint 68)
# =============================================================================

class TestAfterHoursPostings:
    """Tests for test_after_hours_postings()."""

    def test_business_hours_no_flags(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 10:30:00", debit=100, row_number=1),
            JournalEntry(posting_date="2025-01-15 14:00:00", debit=200, row_number=2),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_after_hours_evening_flagged(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 22:00:00", debit=100, row_number=1),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "22:00" in result.flagged_entries[0].issue

    def test_early_morning_flagged(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 03:00:00", debit=100, row_number=1),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_no_time_component_returns_requires_timestamp(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", debit=100, row_number=1),
            JournalEntry(posting_date="2025-01-16", debit=200, row_number=2),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 0
        assert "timestamp" in result.description.lower()

    def test_disabled_returns_test_disabled(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 22:00:00", debit=100, row_number=1),
        ]
        config = JETestingConfig(after_hours_enabled=False)
        result = run_after_hours_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_large_amount_high_severity(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 23:00:00", debit=50000, row_number=1),
        ]
        config = JETestingConfig(after_hours_large_threshold=10000.0)
        result = run_after_hours_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_medium_amount_medium_severity(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 23:00:00", debit=5000, row_number=1),
        ]
        config = JETestingConfig(after_hours_large_threshold=10000.0)
        result = run_after_hours_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_small_amount_low_severity(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 23:00:00", debit=50, row_number=1),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_boundary_start_of_business_not_flagged(self):
        # 06:00 is start of business hours (after_hours_end=6)
        entries = [
            JournalEntry(posting_date="2025-01-15 06:00:00", debit=100, row_number=1),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_boundary_end_of_business_flagged(self):
        # 18:00 is after_hours_start, so it's outside hours
        entries = [
            JournalEntry(posting_date="2025-01-15 18:00:00", debit=100, row_number=1),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_test_key_and_tier(self):
        entries = [JournalEntry(posting_date="2025-01-15", debit=100, row_number=1)]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.test_key == "after_hours_postings"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# T11: SEQUENTIAL NUMBERING GAPS (Sprint 68)
# =============================================================================

class TestNumberingGaps:
    """Tests for test_numbering_gaps()."""

    def test_sequential_ids_no_flags(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-002", debit=200, row_number=2),
            JournalEntry(entry_id="JE-003", debit=300, row_number=3),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_gap_detected(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-005", debit=200, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "gap" in result.flagged_entries[0].issue.lower()

    def test_no_entry_ids_returns_requires_column(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Revenue", credit=100, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 0
        assert "entry_id" in result.description.lower()

    def test_disabled_returns_test_disabled(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-100", debit=200, row_number=2),
        ]
        config = JETestingConfig(numbering_gap_enabled=False)
        result = run_numbering_gaps_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_large_gap_high_severity(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-200", debit=200, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_medium_gap_medium_severity(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-020", debit=200, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_small_gap_low_severity(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-005", debit=200, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_custom_min_gap_size(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-003", debit=200, row_number=2),
        ]
        # Gap of 2 (001 -> 003), default min_size=2 flags it
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        # With min_size=5, gap of 2 should NOT be flagged
        config = JETestingConfig(numbering_gap_min_size=5)
        result2 = run_numbering_gaps_test(entries, config)
        assert result2.entries_flagged == 0

    def test_gap_details_include_surrounding_numbers(self):
        entries = [
            JournalEntry(entry_id="JE-010", debit=100, row_number=1),
            JournalEntry(entry_id="JE-025", debit=200, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        details = result.flagged_entries[0].details
        assert details["prev_number"] == 10
        assert details["curr_number"] == 25

    def test_test_key_and_tier(self):
        entries = [JournalEntry(entry_id="JE-001", debit=100, row_number=1)]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.test_key == "numbering_gaps"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# T12: BACKDATED ENTRIES (Sprint 68)
# =============================================================================

class TestBackdatedEntries:
    """Tests for test_backdated_entries()."""

    def test_no_dual_dates_returns_requires(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", debit=100, row_number=1),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 0
        assert "dual dates" in result.description.lower()

    def test_close_dates_no_flags(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-15", entry_date="2025-01-14",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_backdated_beyond_threshold_flagged(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-03-15",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_disabled_returns_test_disabled(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-06-01",
                debit=100, row_number=1,
            ),
        ]
        config = JETestingConfig(backdate_enabled=False)
        result = run_backdated_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_severity_high_above_90_days(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-06-01",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_severity_medium_31_to_90_days(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-02-15",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_severity_low_at_threshold(self):
        # Exactly 30 days with default threshold of 30
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-01-31",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_custom_days_threshold(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-01-20",
                debit=100, row_number=1,
            ),
        ]
        # Default 30 days threshold won't flag 19 day diff
        result_default = run_backdated_test(entries, JETestingConfig())
        assert result_default.entries_flagged == 0
        # Custom 10 day threshold will flag it
        config = JETestingConfig(backdate_days_threshold=10)
        result_custom = run_backdated_test(entries, config)
        assert result_custom.entries_flagged == 1

    def test_details_include_dates_and_diff(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-04-01",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        details = result.flagged_entries[0].details
        assert "days_diff" in details
        assert details["days_diff"] == 90
        assert details["posting_date"] == "2025-01-01"
        assert details["entry_date"] == "2025-04-01"

    def test_test_key_and_tier(self):
        entries = [JournalEntry(posting_date="2025-01-15", debit=100, row_number=1)]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.test_key == "backdated_entries"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# T13: SUSPICIOUS KEYWORDS (Sprint 68)
# =============================================================================

class TestSuspiciousKeywords:
    """Tests for test_suspicious_keywords()."""

    def test_no_descriptions_returns_no_data(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Revenue", credit=100, row_number=2),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 0
        assert "description" in result.description.lower()

    def test_clean_descriptions_no_flags(self):
        entries = [
            JournalEntry(description="Regular sales transaction", debit=100, row_number=1),
            JournalEntry(description="Monthly rent payment", debit=2000, row_number=2),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_manual_adjustment_flagged(self):
        entries = [
            JournalEntry(description="Manual adjustment for Q4", debit=5000, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "manual adjustment" in result.flagged_entries[0].issue.lower()

    def test_correction_keyword_flagged(self):
        entries = [
            JournalEntry(description="Error correction for invoice 1234", debit=800, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].details["matched_keyword"] in ("error correction", "correction")

    def test_reversal_keyword_flagged(self):
        entries = [
            JournalEntry(description="Reversal of prior period entry", debit=3000, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_dummy_keyword_flagged(self):
        entries = [
            JournalEntry(description="Dummy entry for testing", debit=100, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_related_party_flagged(self):
        entries = [
            JournalEntry(description="Related party transaction with XYZ Corp", debit=50000, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].details["matched_keyword"] == "related party"

    def test_disabled_returns_test_disabled(self):
        entries = [
            JournalEntry(description="Manual adjustment", debit=100, row_number=1),
        ]
        config = JETestingConfig(suspicious_keyword_enabled=False)
        result = run_suspicious_keywords_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_below_confidence_threshold_not_flagged(self):
        # "intercompany" has weight 0.60, raise threshold above it
        entries = [
            JournalEntry(description="Intercompany transfer", debit=100, row_number=1),
        ]
        config = JETestingConfig(suspicious_keyword_threshold=0.70)
        result = run_suspicious_keywords_test(entries, config)
        assert result.entries_flagged == 0

    def test_severity_high_for_high_confidence_large_amount(self):
        entries = [
            JournalEntry(description="Manual adjustment for year-end", debit=50000, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        # manual adjustment = 0.90 confidence, amount > 10000 => HIGH
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_severity_medium_for_moderate_confidence(self):
        entries = [
            JournalEntry(description="Correction entry", debit=100, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        # correction = 0.75 confidence, amount < 5000 => MEDIUM (confidence >= 0.70)
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_suspicious_keywords_list_not_empty(self):
        assert len(SUSPICIOUS_KEYWORDS) > 0
        for keyword, weight, is_phrase in SUSPICIOUS_KEYWORDS:
            assert isinstance(keyword, str)
            assert 0 < weight <= 1.0
            assert isinstance(is_phrase, bool)

    def test_test_key_and_tier(self):
        entries = [JournalEntry(description="Normal entry", debit=100, row_number=1)]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.test_key == "suspicious_keywords"
        assert result.test_tier == TestTier.STATISTICAL
