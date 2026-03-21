"""
Paciolus Audit Engine — CSV Account Type Resolution Tests (Sprint 528)

Tests for _resolve_csv_type: direct map lookup, suffix fallback, and miss cases.
Also tests end-to-end classification via _resolve_category with CSV-provided types.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from account_classifier import AccountCategory
from audit_engine import StreamingAuditor

# =============================================================================
# Helpers
# =============================================================================


def _make_auditor() -> StreamingAuditor:
    """Create a minimal StreamingAuditor for unit testing."""
    return StreamingAuditor(materiality_threshold=50_000)


# =============================================================================
# _resolve_csv_type — Direct Map Hits (confidence 1.0)
# =============================================================================


class TestResolveCsvTypeDirect:
    """Direct map hits should return (category, 1.0)."""

    @pytest.mark.parametrize(
        "raw_value, expected_category",
        [
            # Original bare words
            ("asset", AccountCategory.ASSET),
            ("Asset", AccountCategory.ASSET),
            ("ASSETS", AccountCategory.ASSET),
            ("liability", AccountCategory.LIABILITY),
            ("Liabilities", AccountCategory.LIABILITY),
            ("equity", AccountCategory.EQUITY),
            ("revenue", AccountCategory.REVENUE),
            ("income", AccountCategory.REVENUE),
            ("expense", AccountCategory.EXPENSE),
            ("expenses", AccountCategory.EXPENSE),
            # Compound asset variants
            ("Current Asset", AccountCategory.ASSET),
            ("current assets", AccountCategory.ASSET),
            ("Non-Current Asset", AccountCategory.ASSET),
            ("noncurrent assets", AccountCategory.ASSET),
            ("Long-Term Assets", AccountCategory.ASSET),
            ("Fixed Asset", AccountCategory.ASSET),
            ("fixed assets", AccountCategory.ASSET),
            ("Other Asset", AccountCategory.ASSET),
            # Compound liability variants
            ("Current Liability", AccountCategory.LIABILITY),
            ("current liabilities", AccountCategory.LIABILITY),
            ("Non-Current Liability", AccountCategory.LIABILITY),
            ("noncurrent liabilities", AccountCategory.LIABILITY),
            ("Long-Term Liability", AccountCategory.LIABILITY),
            ("Other Liabilities", AccountCategory.LIABILITY),
            # Compound equity variants
            ("Stockholders Equity", AccountCategory.EQUITY),
            ("Shareholders Equity", AccountCategory.EQUITY),
            ("Owners Equity", AccountCategory.EQUITY),
            ("Net Assets", AccountCategory.EQUITY),
            # Compound revenue variants
            ("Sales", AccountCategory.REVENUE),
            ("Non-Operating Revenue", AccountCategory.REVENUE),
            ("Non-Operating Income", AccountCategory.REVENUE),
            ("nonoperating revenue", AccountCategory.REVENUE),
            ("Other Income", AccountCategory.REVENUE),
            ("Other Revenue", AccountCategory.REVENUE),
            # Compound expense variants
            ("Cost of Revenue", AccountCategory.EXPENSE),
            ("Cost of Goods Sold", AccountCategory.EXPENSE),
            ("COGS", AccountCategory.EXPENSE),
            ("Operating Expense", AccountCategory.EXPENSE),
            ("Operating Expenses", AccountCategory.EXPENSE),
            ("Non-Operating Expense", AccountCategory.EXPENSE),
            ("nonoperating expense", AccountCategory.EXPENSE),
            ("Other Expense", AccountCategory.EXPENSE),
            ("Other Expenses", AccountCategory.EXPENSE),
            ("Selling General and Administrative", AccountCategory.EXPENSE),
            ("SG&A", AccountCategory.EXPENSE),
        ],
    )
    def test_direct_map_hit(self, raw_value, expected_category):
        auditor = _make_auditor()
        category, confidence = auditor._resolve_csv_type(raw_value)
        assert category == expected_category
        assert confidence == 1.0

    def test_whitespace_stripped(self):
        auditor = _make_auditor()
        category, confidence = auditor._resolve_csv_type("  Current Asset  ")
        assert category == AccountCategory.ASSET
        assert confidence == 1.0

    def test_case_insensitive(self):
        auditor = _make_auditor()
        category, confidence = auditor._resolve_csv_type("COST OF GOODS SOLD")
        assert category == AccountCategory.EXPENSE
        assert confidence == 1.0


# =============================================================================
# _resolve_csv_type — Suffix Fallback (confidence 0.90)
# =============================================================================


class TestResolveCsvTypeSuffix:
    """Values not in the explicit map but ending with a known noun should match at 0.90."""

    @pytest.mark.parametrize(
        "raw_value, expected_category",
        [
            ("Intangible Asset", AccountCategory.ASSET),
            ("Deferred Tax Asset", AccountCategory.ASSET),
            ("Contingent Liability", AccountCategory.LIABILITY),
            ("Accrued Liability", AccountCategory.LIABILITY),
            ("Pension Liabilities", AccountCategory.LIABILITY),
            ("Retained Equity", AccountCategory.EQUITY),
            ("Deferred Revenue", AccountCategory.REVENUE),
            ("Interest Revenue", AccountCategory.REVENUE),
            ("Subscription Revenue", AccountCategory.REVENUE),
            ("Interest Income", AccountCategory.REVENUE),
            ("Depreciation Expense", AccountCategory.EXPENSE),
            ("Administrative Expense", AccountCategory.EXPENSE),
            ("Interest Expenses", AccountCategory.EXPENSE),
        ],
    )
    def test_suffix_fallback(self, raw_value, expected_category):
        auditor = _make_auditor()
        category, confidence = auditor._resolve_csv_type(raw_value)
        assert category == expected_category
        assert confidence == 0.90


# =============================================================================
# _resolve_csv_type — Miss Cases (None, 0.0)
# =============================================================================


class TestResolveCsvTypeMiss:
    """Values that don't match anything should return (None, 0.0)."""

    @pytest.mark.parametrize(
        "raw_value",
        [
            "",
            "  ",
            "Unknown",
            "Other",
            "Miscellaneous",
            "Header Row",
            "Total",
        ],
    )
    def test_miss_returns_none(self, raw_value):
        auditor = _make_auditor()
        category, confidence = auditor._resolve_csv_type(raw_value)
        assert category is None
        assert confidence == 0.0


# =============================================================================
# End-to-end: _resolve_category with CSV-provided compound types
# =============================================================================


class TestResolveCategoryWithCsvTypes:
    """Verify _resolve_category uses expanded map for CSV-provided types."""

    def test_compound_csv_type_overrides_heuristic(self):
        """An account with CSV type 'Current Asset' should resolve as ASSET."""
        auditor = _make_auditor()
        auditor.provided_account_types["1000 - Cash"] = "Current Asset"
        category = auditor._resolve_category("1000 - Cash", 50_000)
        assert category == AccountCategory.ASSET

    def test_suffix_csv_type_overrides_heuristic(self):
        """An account with CSV type 'Deferred Tax Asset' should resolve as ASSET via suffix."""
        auditor = _make_auditor()
        auditor.provided_account_types["1500 - DTA"] = "Deferred Tax Asset"
        category = auditor._resolve_category("1500 - DTA", 30_000)
        assert category == AccountCategory.ASSET

    def test_unrecognized_csv_type_falls_through_to_heuristic(self):
        """An unrecognized type like 'Other' should fall through to the keyword classifier."""
        auditor = _make_auditor()
        auditor.provided_account_types["5000 - Rent Expense"] = "Other"
        # 'Rent Expense' in the account key should let the heuristic classify as EXPENSE
        category = auditor._resolve_category("5000 - Rent Expense", 12_000)
        assert category == AccountCategory.EXPENSE

    def test_cogs_csv_type_resolves_as_expense(self):
        """'Cost of Goods Sold' should map to EXPENSE, not fall through."""
        auditor = _make_auditor()
        auditor.provided_account_types["5100 - COGS"] = "Cost of Goods Sold"
        category = auditor._resolve_category("5100 - COGS", 100_000)
        assert category == AccountCategory.EXPENSE

    def test_operating_expense_csv_type(self):
        auditor = _make_auditor()
        auditor.provided_account_types["6000 - Salaries"] = "Operating Expenses"
        category = auditor._resolve_category("6000 - Salaries", 200_000)
        assert category == AccountCategory.EXPENSE

    def test_net_assets_csv_type_resolves_as_equity(self):
        auditor = _make_auditor()
        auditor.provided_account_types["3000 - Net Assets"] = "Net Assets"
        category = auditor._resolve_category("3000 - Net Assets", -500_000)
        assert category == AccountCategory.EQUITY


# =============================================================================
# End-to-end: get_abnormal_balances confidence with compound CSV types
# =============================================================================


class TestAbnormalBalanceConfidenceWithCsvTypes:
    """Verify confidence values in abnormal balance output reflect CSV type match quality."""

    def _make_auditor_with_data(self, accounts: dict, csv_types: dict) -> StreamingAuditor:
        """Build auditor with pre-populated balances and CSV types."""
        auditor = _make_auditor()
        auditor.account_balances = accounts
        auditor.provided_account_types = csv_types
        return auditor

    def test_direct_map_confidence_1_0(self):
        """Direct map hit should yield confidence=1.0 and CSV_ACCOUNT_TYPE keyword."""
        auditor = self._make_auditor_with_data(
            # Revenue account with debit balance = abnormal
            accounts={"Sales Revenue": {"debit": 10_000, "credit": 0}},
            csv_types={"Sales Revenue": "Revenue"},
        )
        results = auditor.get_abnormal_balances()
        abnormal = [a for a in results if a["anomaly_type"] == "natural_balance_violation"]
        assert len(abnormal) == 1
        assert abnormal[0]["confidence"] == 1.0
        assert abnormal[0]["matched_keywords"] == ["CSV_ACCOUNT_TYPE"]

    def test_suffix_match_confidence_0_90(self):
        """Suffix match should yield confidence=0.90."""
        auditor = self._make_auditor_with_data(
            # Revenue account with debit balance = abnormal
            accounts={"Subscription Rev": {"debit": 60_000, "credit": 0}},
            csv_types={"Subscription Rev": "Subscription Revenue"},
        )
        results = auditor.get_abnormal_balances()
        abnormal = [a for a in results if a["anomaly_type"] == "natural_balance_violation"]
        assert len(abnormal) == 1
        assert abnormal[0]["confidence"] == 0.90
        assert abnormal[0]["matched_keywords"] == ["CSV_ACCOUNT_TYPE"]
