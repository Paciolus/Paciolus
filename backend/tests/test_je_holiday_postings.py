"""
Tests for Journal Entry Testing Engine — Holiday Posting Detection (T19)

Sprint 356: ISA 240.A40 — entries posted on public holidays as fraud risk indicator.
Complements T7 (Weekend Postings).

Covers:
- Holiday detection across US federal holidays (fixed + floating)
- Amount-weighted severity tiers
- Disabled test returns clean result
- No-date entries are skipped gracefully
- Multi-year period handling
- Integration with full test battery
"""

from je_testing_engine import (
    JETestingConfig,
    JournalEntry,
    Severity,
    TestTier,
    run_test_battery,
)
from je_testing_engine import (
    test_holiday_postings as run_holiday_test,
)
from shared.holiday_calendar import (
    get_holiday_dates,
    get_us_federal_holidays,
)

# =============================================================================
# HOLIDAY CALENDAR UNIT TESTS
# =============================================================================


class TestHolidayCalendar:
    """Tests for shared/holiday_calendar.py."""

    def test_generates_all_federal_holidays(self):
        """Should generate all 11 US federal holidays."""
        holidays = get_us_federal_holidays(2025)
        # 11 holidays, some may have observed dates too
        holiday_names = set(holidays.values())
        # Strip " (Observed)" suffix to count unique holidays
        base_names = {n.replace(" (Observed)", "") for n in holiday_names}
        assert len(base_names) >= 11

    def test_new_years_day(self):
        """New Year's Day is Jan 1."""
        from datetime import date
        holidays = get_us_federal_holidays(2025)
        assert date(2025, 1, 1) in holidays
        assert "New Year" in holidays[date(2025, 1, 1)]

    def test_christmas_day(self):
        """Christmas Day is Dec 25."""
        from datetime import date
        holidays = get_us_federal_holidays(2025)
        assert date(2025, 12, 25) in holidays

    def test_independence_day(self):
        """Independence Day is Jul 4."""
        from datetime import date
        holidays = get_us_federal_holidays(2025)
        assert date(2025, 7, 4) in holidays

    def test_juneteenth(self):
        """Juneteenth is Jun 19."""
        from datetime import date
        holidays = get_us_federal_holidays(2025)
        assert date(2025, 6, 19) in holidays

    def test_mlk_day_third_monday_jan(self):
        """MLK Day is the 3rd Monday of January."""
        from datetime import date
        holidays = get_us_federal_holidays(2025)
        mlk_2025 = date(2025, 1, 20)  # 3rd Monday of Jan 2025
        assert mlk_2025 in holidays
        assert "Martin Luther King" in holidays[mlk_2025]

    def test_thanksgiving_fourth_thursday_nov(self):
        """Thanksgiving is the 4th Thursday of November."""
        from datetime import date
        holidays = get_us_federal_holidays(2025)
        thanksgiving_2025 = date(2025, 11, 27)  # 4th Thursday of Nov 2025
        assert thanksgiving_2025 in holidays
        assert "Thanksgiving" in holidays[thanksgiving_2025]

    def test_memorial_day_last_monday_may(self):
        """Memorial Day is the last Monday of May."""
        from datetime import date
        holidays = get_us_federal_holidays(2025)
        memorial_2025 = date(2025, 5, 26)  # Last Monday of May 2025
        assert memorial_2025 in holidays
        assert "Memorial" in holidays[memorial_2025]

    def test_labor_day_first_monday_sep(self):
        """Labor Day is the 1st Monday of September."""
        from datetime import date
        holidays = get_us_federal_holidays(2025)
        labor_2025 = date(2025, 9, 1)  # 1st Monday of Sep 2025
        assert labor_2025 in holidays
        assert "Labor" in holidays[labor_2025]

    def test_saturday_observed_on_friday(self):
        """When a fixed holiday falls on Saturday, observed date is Friday."""
        from datetime import date
        # Jul 4, 2026 is a Saturday
        holidays = get_us_federal_holidays(2026)
        assert date(2026, 7, 4) in holidays  # Actual date
        assert date(2026, 7, 3) in holidays  # Observed (Friday)
        assert "Observed" in holidays[date(2026, 7, 3)]

    def test_sunday_observed_on_monday(self):
        """When a fixed holiday falls on Sunday, observed date is Monday."""
        from datetime import date
        # Jan 1, 2023 is a Sunday
        holidays = get_us_federal_holidays(2023)
        assert date(2023, 1, 1) in holidays  # Actual date
        assert date(2023, 1, 2) in holidays  # Observed (Monday)
        assert "Observed" in holidays[date(2023, 1, 2)]

    def test_multi_year_generation(self):
        """get_holiday_dates() combines holidays across multiple years."""
        from datetime import date
        holidays = get_holiday_dates({2024, 2025})
        assert date(2024, 12, 25) in holidays
        assert date(2025, 12, 25) in holidays

    def test_empty_years_returns_empty(self):
        """Empty year set returns empty dict."""
        holidays = get_holiday_dates(set())
        assert holidays == {}


# =============================================================================
# JT-19: HOLIDAY POSTINGS TEST
# =============================================================================


class TestHolidayPostings:
    """Tests for test_holiday_postings() — JT-19."""

    def test_no_holidays_clean(self):
        """Entries on normal business days should not be flagged."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-01-15", debit=1000, row_number=1),
            JournalEntry(account="Cash", posting_date="2025-02-10", debit=2000, row_number=2),
            JournalEntry(account="Cash", posting_date="2025-03-20", debit=500, row_number=3),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.test_key == "holiday_postings"
        assert result.test_tier == TestTier.STATISTICAL
        assert result.entries_flagged == 0
        assert result.flag_rate == 0.0

    def test_christmas_day_flagged(self):
        """Entry on Christmas Day should be flagged."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-12-25", debit=5000, row_number=1),
            JournalEntry(account="Revenue", posting_date="2025-12-26", credit=5000, row_number=2),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].details["holiday"] == "Christmas Day"

    def test_new_years_day_flagged(self):
        """Entry on New Year's Day should be flagged."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-01-01", debit=3000, row_number=1),
            JournalEntry(account="Revenue", posting_date="2025-01-02", credit=3000, row_number=2),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "New Year" in result.flagged_entries[0].details["holiday"]

    def test_independence_day_flagged(self):
        """Entry on July 4th should be flagged."""
        entries = [
            JournalEntry(account="Supplies", posting_date="2025-07-04", debit=800, row_number=1),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "Independence" in result.flagged_entries[0].details["holiday"]

    def test_thanksgiving_flagged(self):
        """Entry on Thanksgiving (floating holiday) should be flagged."""
        # Thanksgiving 2025 = Nov 27 (4th Thursday)
        entries = [
            JournalEntry(account="Cash", posting_date="2025-11-27", debit=15000, row_number=1),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "Thanksgiving" in result.flagged_entries[0].details["holiday"]

    def test_observed_holiday_flagged(self):
        """Entry on an observed holiday date should also be flagged."""
        # Jul 4, 2026 is Saturday → observed on Friday Jul 3
        entries = [
            JournalEntry(account="Cash", posting_date="2026-07-03", debit=5000, row_number=1),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "Observed" in result.flagged_entries[0].details["holiday"]

    def test_severity_high_for_large_amount(self):
        """Large amounts on holidays should get HIGH severity."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-12-25", debit=50000, row_number=1),
        ]
        config = JETestingConfig(holiday_large_amount_threshold=10000.0)
        result = run_holiday_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_severity_medium_for_moderate_amount(self):
        """Moderate amounts on holidays should get MEDIUM severity."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-12-25", debit=3000, row_number=1),
        ]
        config = JETestingConfig(holiday_large_amount_threshold=10000.0)
        result = run_holiday_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_severity_low_for_small_amount(self):
        """Small amounts on holidays should get LOW severity."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-12-25", debit=100, row_number=1),
        ]
        config = JETestingConfig(holiday_large_amount_threshold=10000.0)
        result = run_holiday_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_disabled_returns_zero_flags(self):
        """Disabled test should return clean result with zero flags."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-12-25", debit=50000, row_number=1),
        ]
        config = JETestingConfig(holiday_posting_enabled=False)
        result = run_holiday_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_no_dates_skipped_gracefully(self):
        """Entries with no parseable dates should be skipped."""
        entries = [
            JournalEntry(account="Cash", debit=1000, row_number=1),
            JournalEntry(account="Revenue", credit=1000, row_number=2),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_entry_date_fallback(self):
        """Should use entry_date when posting_date is missing."""
        entries = [
            JournalEntry(account="Cash", entry_date="2025-12-25", debit=5000, row_number=1),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_multiple_holidays_flagged(self):
        """Multiple entries on different holidays should all be flagged."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-01-01", debit=1000, row_number=1),
            JournalEntry(account="Cash", posting_date="2025-07-04", debit=2000, row_number=2),
            JournalEntry(account="Cash", posting_date="2025-12-25", debit=3000, row_number=3),
            JournalEntry(account="Cash", posting_date="2025-06-15", debit=4000, row_number=4),  # Normal day
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.entries_flagged == 3

    def test_multi_year_entries(self):
        """Entries spanning multiple years should generate holidays for all years."""
        entries = [
            JournalEntry(account="Cash", posting_date="2024-12-25", debit=1000, row_number=1),
            JournalEntry(account="Cash", posting_date="2025-01-01", debit=2000, row_number=2),
            JournalEntry(account="Cash", posting_date="2025-06-15", debit=3000, row_number=3),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.entries_flagged == 2  # Christmas 2024 + New Year 2025

    def test_flag_rate_calculation(self):
        """Flag rate should be flagged/total."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-12-25", debit=1000, row_number=1),
            JournalEntry(account="Cash", posting_date="2025-06-15", debit=2000, row_number=2),
            JournalEntry(account="Cash", posting_date="2025-08-20", debit=3000, row_number=3),
            JournalEntry(account="Cash", posting_date="2025-09-10", debit=4000, row_number=4),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flag_rate == 1 / 4

    def test_details_contain_required_fields(self):
        """Flagged entry details should contain holiday, date, and amount."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-12-25", debit=5000, row_number=1),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        details = result.flagged_entries[0].details
        assert "holiday" in details
        assert "date" in details
        assert "amount" in details
        assert details["date"] == "2025-12-25"
        assert details["amount"] == 5000

    def test_issue_message_format(self):
        """Issue message should contain holiday name, date, and amount."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-12-25", debit=5000, row_number=1),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        issue = result.flagged_entries[0].issue
        assert "Christmas" in issue
        assert "2025-12-25" in issue
        assert "$5,000.00" in issue

    def test_confidence_value(self):
        """Flagged entries should have 0.85 confidence."""
        entries = [
            JournalEntry(account="Cash", posting_date="2025-12-25", debit=1000, row_number=1),
        ]
        result = run_holiday_test(entries, JETestingConfig())
        assert result.flagged_entries[0].confidence == 0.85


# =============================================================================
# INTEGRATION: FULL BATTERY INCLUDES T19
# =============================================================================


class TestHolidayInBattery:
    """Tests that JT-19 is included in the full test battery."""

    def test_battery_includes_holiday_test(self):
        """run_test_battery() should include holiday_postings in results."""
        entries = [
            JournalEntry(
                entry_id="JE001", account="Cash", posting_date="2025-06-15",
                debit=1000, description="Normal entry", row_number=1,
            ),
            JournalEntry(
                entry_id="JE001", account="Revenue", posting_date="2025-06-15",
                credit=1000, description="Normal entry", row_number=2,
            ),
        ]
        results, _ = run_test_battery(entries)
        test_keys = [r.test_key for r in results]
        assert "holiday_postings" in test_keys

    def test_battery_count_is_19(self):
        """Full battery should now contain 19 tests."""
        entries = [
            JournalEntry(
                entry_id="JE001", account="Cash", posting_date="2025-06-15",
                debit=1000, description="Normal entry", row_number=1,
            ),
            JournalEntry(
                entry_id="JE001", account="Revenue", posting_date="2025-06-15",
                credit=1000, description="Normal entry", row_number=2,
            ),
        ]
        results, _ = run_test_battery(entries)
        assert len(results) == 19
