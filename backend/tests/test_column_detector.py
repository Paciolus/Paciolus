"""
Tests for shared column detector — Sprint 151

Tests the shared ColumnDetector module that replaces 13 near-identical
detection functions across 9 engines.
"""

from shared.column_detector import (
    ColumnFieldConfig,
    ColumnPattern,
    DetectionResult,
    detect_columns,
    match_column,
)

# =============================================================================
# FIXTURES
# =============================================================================

DATE_PATTERNS: list[ColumnPattern] = [
    (r"^date$", 1.0, True),
    (r"^transaction\s*date$", 0.98, True),
    (r"^posting\s*date$", 0.95, True),
    (r"date", 0.55, False),
]

AMOUNT_PATTERNS: list[ColumnPattern] = [
    (r"^amount$", 0.95, True),
    (r"^transaction\s*amount$", 1.0, True),
    (r"^net\s*amount$", 0.90, True),
    (r"amount", 0.55, False),
]

DESCRIPTION_PATTERNS: list[ColumnPattern] = [
    (r"^description$", 1.0, True),
    (r"^memo$", 0.90, True),
    (r"^narrative$", 0.90, True),
    (r"description", 0.55, False),
]

REFERENCE_PATTERNS: list[ColumnPattern] = [
    (r"^reference$", 1.0, True),
    (r"^ref$", 0.95, True),
    (r"^ref\s*number$", 0.98, True),
    (r"^check\s*number$", 0.90, True),
    (r"reference", 0.55, False),
]

BALANCE_PATTERNS: list[ColumnPattern] = [
    (r"^balance$", 1.0, True),
    (r"^running\s*balance$", 0.98, True),
    (r"^closing\s*balance$", 0.95, True),
    (r"balance", 0.55, False),
]


def make_bank_configs(
    date_priority=30, amount_priority=40, desc_priority=50,
    ref_priority=10, bal_priority=20,
) -> list[ColumnFieldConfig]:
    """Create bank-like column configs with customizable priorities."""
    return [
        ColumnFieldConfig(
            field_name="date_column",
            patterns=DATE_PATTERNS,
            required=True,
            missing_note="Could not identify a Date column",
            priority=date_priority,
        ),
        ColumnFieldConfig(
            field_name="amount_column",
            patterns=AMOUNT_PATTERNS,
            required=True,
            missing_note="Could not identify an Amount column",
            priority=amount_priority,
        ),
        ColumnFieldConfig(
            field_name="description_column",
            patterns=DESCRIPTION_PATTERNS,
            required=False,
            priority=desc_priority,
        ),
        ColumnFieldConfig(
            field_name="reference_column",
            patterns=REFERENCE_PATTERNS,
            required=False,
            priority=ref_priority,
        ),
        ColumnFieldConfig(
            field_name="balance_column",
            patterns=BALANCE_PATTERNS,
            required=False,
            priority=bal_priority,
        ),
    ]


# =============================================================================
# match_column TESTS
# =============================================================================

class TestMatchColumn:
    """Tests for the match_column function."""

    def test_exact_match_highest_weight(self):
        """Exact match 'date' should return 1.0."""
        assert match_column("date", DATE_PATTERNS) == 1.0

    def test_exact_match_with_spaces(self):
        """'transaction date' should match with 0.98."""
        assert match_column("transaction date", DATE_PATTERNS) == 0.98

    def test_substring_match_fallback(self):
        """'some_date_field' should match substring pattern at 0.55."""
        assert match_column("some_date_field", DATE_PATTERNS) == 0.55

    def test_no_match_returns_zero(self):
        """Completely unrelated column name should return 0.0."""
        assert match_column("vendor_name", DATE_PATTERNS) == 0.0

    def test_case_insensitive(self):
        """Matching should be case-insensitive."""
        assert match_column("DATE", DATE_PATTERNS) == 1.0
        assert match_column("Transaction Date", DATE_PATTERNS) == 0.98

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace should be stripped."""
        assert match_column("  date  ", DATE_PATTERNS) == 1.0

    def test_multiple_patterns_returns_best(self):
        """When multiple patterns match, return the highest weight."""
        # 'transaction date' matches both exact (0.98) and substring (0.55)
        assert match_column("transaction date", DATE_PATTERNS) == 0.98

    def test_exact_vs_search(self):
        """Exact match (re.match) should not match substrings."""
        # '^date$' should not match 'update_date'
        # but 'date' as search pattern should
        result = match_column("update_date", DATE_PATTERNS)
        assert result == 0.55  # Only substring match

    def test_empty_patterns(self):
        """Empty patterns list should return 0.0."""
        assert match_column("date", []) == 0.0

    def test_empty_column_name(self):
        """Empty column name should return 0.0 for most patterns."""
        assert match_column("", AMOUNT_PATTERNS) == 0.0


# =============================================================================
# detect_columns TESTS
# =============================================================================

class TestDetectColumns:
    """Tests for the detect_columns function."""

    def test_basic_detection(self):
        """Standard bank columns should be detected correctly."""
        columns = ["Date", "Amount", "Description", "Reference", "Balance"]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)

        assert result.get_column("date_column") == "Date"
        assert result.get_column("amount_column") == "Amount"
        assert result.get_column("description_column") == "Description"
        assert result.get_column("reference_column") == "Reference"
        assert result.get_column("balance_column") == "Balance"

    def test_all_columns_preserved(self):
        """all_columns should contain the original (stripped) column names."""
        columns = ["  Date  ", "Amount", "Other"]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)
        assert result.all_columns == ["Date", "Amount", "Other"]

    def test_missing_required_generates_note(self):
        """Missing required column should generate a note."""
        columns = ["Description", "Reference"]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)
        assert "Could not identify a Date column" in result.detection_notes
        assert "Could not identify an Amount column" in result.detection_notes

    def test_missing_optional_no_note(self):
        """Missing optional column should not generate a note."""
        columns = ["Date", "Amount"]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)
        assert result.get_column("date_column") == "Date"
        assert result.get_column("amount_column") == "Amount"
        assert result.get_column("description_column") is None
        # No note about missing description (optional)
        assert not any("Description" in n for n in result.detection_notes)

    def test_greedy_prevents_double_assignment(self):
        """A column should only be assigned to one field."""
        # 'Transaction Amount' could match both date (via 'date' substring) and amount
        columns = ["Transaction Amount", "Transaction Date"]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)

        date_col = result.get_column("date_column")
        amount_col = result.get_column("amount_column")
        assert date_col != amount_col
        assert date_col == "Transaction Date"
        assert amount_col == "Transaction Amount"

    def test_specificity_ordering(self):
        """Higher-priority fields should be assigned first."""
        # 'Ref Number' matches both reference (high priority=10) and description (low priority=50)
        # Reference should claim it first
        columns = ["Ref Number", "Date", "Amount"]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)
        assert result.get_column("reference_column") == "Ref Number"

    def test_priority_prevents_greedy_stealing(self):
        """Lower priority number = assigned first, preventing generic patterns from stealing specific columns."""
        # Without specificity ordering, 'Balance' might be stolen by 'amount' substring
        columns = ["Running Balance", "Amount", "Date"]
        configs = make_bank_configs(bal_priority=10, amount_priority=20)
        result = detect_columns(columns, configs)
        assert result.get_column("balance_column") == "Running Balance"
        assert result.get_column("amount_column") == "Amount"

    def test_min_confidence_threshold(self):
        """Columns below min_confidence should not be assigned."""
        columns = ["some_date_field", "Amount"]
        configs = make_bank_configs()
        # 'some_date_field' matches at 0.55; setting min to 0.60 should reject it
        result = detect_columns(columns, configs, min_confidence=0.60)
        assert result.get_column("date_column") is None
        assert result.get_column("amount_column") == "Amount"

    def test_confidence_values(self):
        """Confidence values should reflect the pattern weight."""
        columns = ["Date", "Amount"]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)
        assert result.get_confidence("date_column") == 1.0
        assert result.get_confidence("amount_column") == 0.95

    def test_unmatched_field_confidence_zero(self):
        """Unmatched field should return 0.0 confidence."""
        columns = ["Date"]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)
        assert result.get_confidence("description_column") == 0.0

    def test_empty_columns(self):
        """Empty column list should produce no assignments."""
        configs = make_bank_configs()
        result = detect_columns([], configs)
        assert len(result.assignments) == 0
        assert "Could not identify a Date column" in result.detection_notes
        assert "Could not identify an Amount column" in result.detection_notes

    def test_empty_configs(self):
        """Empty config list should produce no assignments."""
        result = detect_columns(["Date", "Amount"], [])
        assert len(result.assignments) == 0
        assert result.all_columns == ["Date", "Amount"]

    def test_case_insensitive_detection(self):
        """Column detection should be case-insensitive."""
        columns = ["DATE", "AMOUNT", "DESCRIPTION"]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)
        assert result.get_column("date_column") == "DATE"
        assert result.get_column("amount_column") == "AMOUNT"

    def test_whitespace_handling(self):
        """Column names with whitespace should be stripped before matching."""
        columns = ["  Date  ", "  Amount  "]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)
        assert result.get_column("date_column") == "Date"
        assert result.get_column("amount_column") == "Amount"

    def test_many_unrelated_columns(self):
        """Unrelated columns should not interfere with detection."""
        columns = ["ID", "Date", "Name", "Amount", "Status", "Notes", "Balance"]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)
        assert result.get_column("date_column") == "Date"
        assert result.get_column("amount_column") == "Amount"
        assert result.get_column("balance_column") == "Balance"

    def test_duplicate_column_names(self):
        """Duplicate column names: first occurrence should be assigned."""
        columns = ["Date", "Amount", "Date"]
        configs = [
            ColumnFieldConfig(
                field_name="date1", patterns=DATE_PATTERNS, priority=10,
            ),
            ColumnFieldConfig(
                field_name="date2", patterns=DATE_PATTERNS, priority=20,
            ),
        ]
        result = detect_columns(columns, configs)
        # First 'Date' claimed by date1, second 'Date' by date2
        assert result.get_column("date1") == "Date"
        # The second 'Date' has the same string so set membership prevents assignment
        # This is a known limitation: duplicate column names share same set key
        # In practice, pandas would suffix them (Date, Date.1)

    def test_detection_result_get_column_none(self):
        """get_column for non-existent field returns None."""
        result = DetectionResult()
        assert result.get_column("nonexistent") is None

    def test_detection_result_get_confidence_zero(self):
        """get_confidence for non-existent field returns 0.0."""
        result = DetectionResult()
        assert result.get_confidence("nonexistent") == 0.0

    def test_all_required_missing(self):
        """All required fields missing should generate all notes."""
        columns = ["foo", "bar", "baz"]
        configs = [
            ColumnFieldConfig(
                field_name="date", patterns=DATE_PATTERNS,
                required=True, missing_note="Missing date",
            ),
            ColumnFieldConfig(
                field_name="amount", patterns=AMOUNT_PATTERNS,
                required=True, missing_note="Missing amount",
            ),
        ]
        result = detect_columns(columns, configs)
        assert "Missing date" in result.detection_notes
        assert "Missing amount" in result.detection_notes


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case tests for robustness."""

    def test_single_column_single_config(self):
        """Single column matching single config should work."""
        result = detect_columns(
            ["Date"],
            [ColumnFieldConfig(field_name="date", patterns=DATE_PATTERNS)],
        )
        assert result.get_column("date") == "Date"

    def test_more_configs_than_columns(self):
        """More configs than columns: only available columns assigned."""
        columns = ["Date"]
        configs = make_bank_configs()
        result = detect_columns(columns, configs)
        # Only date should be assigned (best match)
        assigned_count = len(result.assignments)
        assert assigned_count == 1

    def test_more_columns_than_configs(self):
        """Extra columns should be ignored (not assigned)."""
        columns = ["Date", "Amount", "Extra1", "Extra2", "Extra3"]
        configs = [
            ColumnFieldConfig(field_name="date", patterns=DATE_PATTERNS),
            ColumnFieldConfig(field_name="amount", patterns=AMOUNT_PATTERNS),
        ]
        result = detect_columns(columns, configs)
        assert len(result.assignments) == 2

    def test_patterns_with_special_regex_chars(self):
        """Patterns with regex special chars should work correctly."""
        patterns: list[ColumnPattern] = [
            (r"^invoice\s*#$", 0.95, True),
            (r"^amount\s*\(\$\)$", 0.90, True),
        ]
        config = [ColumnFieldConfig(field_name="inv", patterns=patterns)]
        result = detect_columns(["Invoice #"], config)
        assert result.get_column("inv") == "Invoice #"

    def test_required_with_empty_missing_note(self):
        """Required field with empty missing_note should not add empty string to notes."""
        columns = ["foo"]
        configs = [
            ColumnFieldConfig(
                field_name="date", patterns=DATE_PATTERNS,
                required=True, missing_note="",
            ),
        ]
        result = detect_columns(columns, configs)
        assert "" not in result.detection_notes

    def test_zero_weight_pattern(self):
        """Pattern with weight 0.0 should match but not exceed min_confidence."""
        patterns: list[ColumnPattern] = [(r"^date$", 0.0, True)]
        configs = [ColumnFieldConfig(field_name="date", patterns=patterns)]
        result = detect_columns(["Date"], configs, min_confidence=0.0)
        # Weight 0.0 is not > min_confidence 0.0, so no assignment
        assert result.get_column("date") is None
