"""
Tests for legacy column detector adapter — Sprint 416

Verifies that the adapter (column_detector.py) delegating to shared.column_detector
produces correct results for all TB column detection scenarios. This is a parity
test suite ensuring the refactored adapter preserves the original behavior.
"""

from column_detector import ColumnMapping, ColumnType, detect_columns

# =============================================================================
# STANDARD DETECTION — high confidence exact matches
# =============================================================================

class TestStandardDetection:
    """Standard TB headers should be detected with full confidence."""

    def test_standard_tb_columns(self):
        """Account Name / Debit / Credit — all 1.0 confidence."""
        result = detect_columns(["Account Name", "Debit", "Credit"])
        assert result.account_column == "Account Name"
        assert result.debit_column == "Debit"
        assert result.credit_column == "Credit"
        assert result.account_confidence == 1.0
        assert result.debit_confidence == 1.0
        assert result.credit_confidence == 1.0
        assert result.overall_confidence == 1.0

    def test_gl_account_variant(self):
        """GL Account / Debits / Credits variant."""
        result = detect_columns(["GL Account", "Debits", "Credits"])
        assert result.account_column == "GL Account"
        assert result.debit_column == "Debits"
        assert result.credit_column == "Credits"
        assert result.account_confidence == 0.95
        assert result.debit_confidence == 0.98
        assert result.credit_confidence == 0.98

    def test_dr_cr_shorthand(self):
        """Account / Dr / Cr — exact shorthand match."""
        result = detect_columns(["Account", "Dr", "Cr"])
        assert result.account_column == "Account"
        assert result.debit_column == "Dr"
        assert result.credit_column == "Cr"
        assert result.debit_confidence == 0.95
        assert result.credit_confidence == 0.95

    def test_amount_variants(self):
        """Debit Amount / Credit Amount columns."""
        result = detect_columns(["Account Title", "Debit Amount", "Credit Amount"])
        assert result.account_column == "Account Title"
        assert result.debit_column == "Debit Amount"
        assert result.credit_column == "Credit Amount"
        assert result.debit_confidence == 0.95
        assert result.credit_confidence == 0.95

    def test_requires_mapping_false_for_high_confidence(self):
        """High confidence result should not require mapping."""
        result = detect_columns(["Account Name", "Debit", "Credit"])
        assert result.requires_mapping is False

    def test_no_detection_notes_for_standard(self):
        """Standard columns should produce no notes."""
        result = detect_columns(["Account Name", "Debit", "Credit"])
        assert result.detection_notes == []


# =============================================================================
# PARTIAL / LOW CONFIDENCE MATCHES
# =============================================================================

class TestPartialMatches:
    """Partial/substring matches should produce appropriate confidence."""

    def test_partial_match_with_extra_columns(self):
        """GL as account should match at lower confidence."""
        result = detect_columns(["GL", "Dr Amount", "Cr Amount"])
        assert result.account_column == "GL"
        assert result.account_confidence == 0.35
        assert result.debit_column == "Dr Amount"
        assert result.credit_column == "Cr Amount"

    def test_low_confidence_notes_generated(self):
        """Item column should trigger low-confidence note."""
        result = detect_columns(["Item", "Dr", "Cr"])
        assert result.account_column == "Item"
        assert result.account_confidence == 0.30
        assert any("low confidence" in n and "Item" in n for n in result.detection_notes)

    def test_requires_mapping_true_for_low_confidence(self):
        """Low debit/credit confidence should trigger requires_mapping."""
        result = detect_columns(["Account Name", "Dr Amount", "Cr Amount"])
        # Dr Amount matches via \bdr\b at 0.70 (higher than dr.*amount at 0.65)
        assert result.debit_confidence == 0.70
        assert result.requires_mapping is True

    def test_substring_debit_match(self):
        """Column containing 'debit' as substring."""
        result = detect_columns(["Account", "Total Debit", "Credit"])
        assert result.debit_column == "Total Debit"
        assert result.debit_confidence == 0.80


# =============================================================================
# MISSING COLUMNS — fallback and error notes
# =============================================================================

class TestMissingColumns:
    """Missing columns should produce appropriate fallbacks and notes."""

    def test_missing_debit(self):
        """Missing debit column should produce note and low overall."""
        result = detect_columns(["Account", "Credit"])
        assert result.debit_column is None
        assert result.debit_confidence == 0.0
        assert "Could not identify Debit column" in result.detection_notes
        # Only credit confidence contributes to overall
        assert result.overall_confidence == 1.0

    def test_missing_credit(self):
        """Missing credit column should produce note."""
        result = detect_columns(["Account", "Debit"])
        assert result.credit_column is None
        assert "Could not identify Credit column" in result.detection_notes
        assert result.overall_confidence == 1.0

    def test_missing_both_debit_credit(self):
        """Missing both required columns produces 0.0 overall."""
        result = detect_columns(["Account", "Foo", "Bar"])
        assert result.debit_column is None
        assert result.credit_column is None
        assert result.overall_confidence == 0.0
        assert "Cannot process file: missing required Debit/Credit columns" in result.detection_notes

    def test_empty_columns(self):
        """Empty column list produces 0.0 overall with notes."""
        result = detect_columns([])
        assert result.account_column is None
        assert result.debit_column is None
        assert result.credit_column is None
        assert result.overall_confidence == 0.0
        assert result.all_columns == []

    def test_account_fallback_to_first_column(self):
        """No account match should fall back to first column at 0.30."""
        result = detect_columns(["Foo", "Debit", "Credit"])
        assert result.account_column == "Foo"
        assert result.account_confidence == 0.30
        assert any("fallback" in n for n in result.detection_notes)
        assert any("low confidence" in n and "Foo" in n for n in result.detection_notes)

    def test_fallback_strips_whitespace(self):
        """Fallback column should be stripped."""
        result = detect_columns(["  Foo  ", "Debit", "Credit"])
        assert result.account_column == "Foo"


# =============================================================================
# to_dict SHAPE VALIDATION
# =============================================================================

class TestToDict:
    """to_dict() output must match the expected API contract."""

    def test_dict_keys(self):
        """to_dict() should contain all expected keys."""
        result = detect_columns(["Account Name", "Debit", "Credit"])
        d = result.to_dict()
        expected_keys = {
            "account_column", "debit_column", "credit_column",
            "account_confidence", "debit_confidence", "credit_confidence",
            "overall_confidence", "requires_mapping", "all_columns",
            "detection_notes",
        }
        assert set(d.keys()) == expected_keys

    def test_dict_values_standard(self):
        """to_dict() values for standard columns."""
        result = detect_columns(["Account Name", "Debit", "Credit"])
        d = result.to_dict()
        assert d["account_column"] == "Account Name"
        assert d["debit_column"] == "Debit"
        assert d["credit_column"] == "Credit"
        assert d["account_confidence"] == 1.0
        assert d["debit_confidence"] == 1.0
        assert d["credit_confidence"] == 1.0
        assert d["overall_confidence"] == 1.0
        assert d["requires_mapping"] is False
        assert d["all_columns"] == ["Account Name", "Debit", "Credit"]
        assert d["detection_notes"] == []

    def test_dict_confidence_rounding(self):
        """to_dict() should round confidence to 2 decimal places."""
        result = detect_columns(["GL", "Debit", "Credit"])
        d = result.to_dict()
        # GL matches at 0.35 — should be 0.35 after rounding
        assert d["account_confidence"] == 0.35

    def test_dict_with_none_columns(self):
        """to_dict() handles None columns."""
        result = detect_columns(["Account"])
        d = result.to_dict()
        assert d["debit_column"] is None
        assert d["credit_column"] is None


# =============================================================================
# COLUMN MAPPING
# =============================================================================

class TestColumnMapping:
    """ColumnMapping dataclass for user overrides."""

    def test_from_dict(self):
        """from_dict() creates mapping correctly."""
        data = {
            "account_column": "GL Account",
            "debit_column": "Dr",
            "credit_column": "Cr",
        }
        mapping = ColumnMapping.from_dict(data)
        assert mapping.account_column == "GL Account"
        assert mapping.debit_column == "Dr"
        assert mapping.credit_column == "Cr"

    def test_from_dict_missing_keys(self):
        """from_dict() defaults to empty string for missing keys."""
        mapping = ColumnMapping.from_dict({})
        assert mapping.account_column == ""
        assert mapping.debit_column == ""
        assert mapping.credit_column == ""

    def test_is_valid_success(self):
        """is_valid() returns True when all columns exist."""
        mapping = ColumnMapping(
            account_column="Account",
            debit_column="Debit",
            credit_column="Credit",
        )
        valid, errors = mapping.is_valid(["Account", "Debit", "Credit"])
        assert valid is True
        assert errors == []

    def test_is_valid_case_insensitive(self):
        """is_valid() is case-insensitive."""
        mapping = ColumnMapping(
            account_column="ACCOUNT",
            debit_column="debit",
            credit_column="Credit",
        )
        valid, errors = mapping.is_valid(["Account", "Debit", "Credit"])
        assert valid is True

    def test_is_valid_failure(self):
        """is_valid() returns errors for missing columns."""
        mapping = ColumnMapping(
            account_column="Missing",
            debit_column="Debit",
            credit_column="Credit",
        )
        valid, errors = mapping.is_valid(["Account", "Debit", "Credit"])
        assert valid is False
        assert len(errors) == 1
        assert "Missing" in errors[0]

    def test_is_valid_all_missing(self):
        """is_valid() returns 3 errors when no columns match."""
        mapping = ColumnMapping(
            account_column="A",
            debit_column="B",
            credit_column="C",
        )
        valid, errors = mapping.is_valid(["X", "Y", "Z"])
        assert valid is False
        assert len(errors) == 3


# =============================================================================
# COLUMN TYPE ENUM
# =============================================================================

class TestColumnType:
    """ColumnType enum should still be importable and correct."""

    def test_enum_values(self):
        assert ColumnType.ACCOUNT.value == "account"
        assert ColumnType.DEBIT.value == "debit"
        assert ColumnType.CREDIT.value == "credit"
        assert ColumnType.UNKNOWN.value == "unknown"


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge cases for robustness."""

    def test_all_columns_preserved(self):
        """all_columns should contain stripped original column names."""
        result = detect_columns(["  Account  ", "  Debit  ", "  Credit  "])
        assert result.all_columns == ["Account", "Debit", "Credit"]

    def test_many_extra_columns(self):
        """Extra columns should not interfere with detection."""
        result = detect_columns(["ID", "Account Name", "Code", "Debit", "Credit", "Notes"])
        assert result.account_column == "Account Name"
        assert result.debit_column == "Debit"
        assert result.credit_column == "Credit"
        assert result.overall_confidence == 1.0

    def test_case_insensitive_detection(self):
        """Detection should be case-insensitive."""
        result = detect_columns(["ACCOUNT NAME", "DEBIT", "CREDIT"])
        assert result.account_column == "ACCOUNT NAME"
        assert result.debit_column == "DEBIT"
        assert result.credit_column == "CREDIT"
        assert result.account_confidence == 1.0

    def test_overall_is_min_of_required(self):
        """Overall confidence should be min of debit and credit."""
        result = detect_columns(["Account Name", "Dr Amount", "Credit"])
        # Dr Amount matches \bdr\b at 0.70, Credit at 1.0 → min is 0.70
        assert result.overall_confidence == 0.70

    def test_ledger_account_variant(self):
        """Ledger Account exact match."""
        result = detect_columns(["Ledger Account", "Debit Balance", "Credit Balance"])
        assert result.account_column == "Ledger Account"
        assert result.account_confidence == 0.90
        assert result.debit_column == "Debit Balance"
        assert result.credit_column == "Credit Balance"

    def test_greedy_prevents_double_assignment(self):
        """Shared detector's greedy assignment prevents a column from being used twice."""
        # "Debit" should only be assigned to debit_column, not credit_column
        result = detect_columns(["Account", "Debit", "Credit"])
        assert result.debit_column == "Debit"
        assert result.credit_column == "Credit"
        assert result.debit_column != result.credit_column

    def test_single_column_only(self):
        """Single column file should trigger fallback and missing notes."""
        result = detect_columns(["Total"])
        # No account pattern matches "Total", so fallback to first column
        assert result.account_column == "Total"
        assert result.account_confidence == 0.30
        assert result.debit_column is None
        assert result.credit_column is None
        assert result.overall_confidence == 0.0
