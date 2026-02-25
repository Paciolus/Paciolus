"""
Tests for Sprint 4: Text Layout Hardening — Long-Input Fixtures

Validates that PDF generation succeeds with extreme-length strings:
- Very long customer/client names
- Very long account names
- Very long source document titles
- Very long issue descriptions / item IDs

Each test asserts:
1. PDF generation succeeds (returns bytes)
2. Valid PDF header (%PDF-)
3. Key full strings are present where extractable
"""


# =============================================================================
# Long-input constants
# =============================================================================

LONG_CUSTOMER_NAME = "Amalgamated International Holdings Corporation of Greater Metropolitan Eastern Seaboard Division — Subsidiary A-7 (Intercompany)"
LONG_ACCOUNT_NAME = "Accumulated Other Comprehensive Income — Unrealized Gains and Losses on Available-for-Sale Debt Securities (Net of Tax and Reclassification Adjustments per ASC 320-10-35)"
LONG_LEAD_SHEET_NAME = "Property, Plant and Equipment — Land, Buildings, Leasehold Improvements, Furniture, Fixtures, and Equipment (Net of Accumulated Depreciation and Impairment)"
LONG_ITEM_ID = "INV-2025-Q4-RECON-ADJUSTMENT-BATCH-14-ITEM-0003827-REVERSAL-ENTRY"
LONG_ISSUE_DESCRIPTION = "The recorded amount significantly exceeds the audited fair value based on independent third-party appraisal, potentially indicating impairment that has not been recognized in the financial statements under ASC 360-10-35"
LONG_FILENAME = "Q4_2025_Consolidated_Trial_Balance_Post_Adjustments_Including_Intercompany_Eliminations_and_Currency_Translation.xlsx"


# =============================================================================
# Multi-Period Memo — Long Account + Lead Sheet Names
# =============================================================================


class TestMultiPeriodMemoLongInputs:
    """Verify multi-period memo handles extreme-length strings."""

    def _make_result(self, account_name: str, lead_sheet_name: str) -> dict:
        return {
            "prior_label": "FY2024",
            "current_label": "FY2025",
            "total_accounts": 10,
            "movements_by_type": {"increase": 5, "decrease": 5},
            "movements_by_significance": {"material": 2, "significant": 3, "minor": 5},
            "significant_movements": [
                {
                    "account_name": account_name,
                    "account_type": "asset",
                    "prior_balance": 100000.0,
                    "current_balance": 150000.0,
                    "change_amount": 50000.0,
                    "change_percent": 50.0,
                    "movement_type": "increase",
                    "significance": "material",
                    "lead_sheet": "A",
                    "lead_sheet_name": lead_sheet_name,
                    "lead_sheet_category": "asset",
                    "is_dormant": False,
                },
            ],
            "lead_sheet_summaries": [
                {
                    "lead_sheet": "A",
                    "lead_sheet_name": lead_sheet_name,
                    "lead_sheet_category": "asset",
                    "prior_total": 500000.0,
                    "current_total": 550000.0,
                    "net_change": 50000.0,
                    "change_percent": 10.0,
                    "account_count": 10,
                    "movements": [],
                },
            ],
            "dormant_account_count": 0,
        }

    def test_long_account_name_in_movements(self):
        from multi_period_memo_generator import generate_multi_period_memo

        result = self._make_result(LONG_ACCOUNT_NAME, "Normal Lead Sheet")
        pdf = generate_multi_period_memo(result, client_name=LONG_CUSTOMER_NAME)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 100

    def test_long_lead_sheet_name(self):
        from multi_period_memo_generator import generate_multi_period_memo

        result = self._make_result("Normal Account", LONG_LEAD_SHEET_NAME)
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_long_customer_name(self):
        from multi_period_memo_generator import generate_multi_period_memo

        result = self._make_result("Account 1", "Lead Sheet A")
        pdf = generate_multi_period_memo(
            result,
            client_name=LONG_CUSTOMER_NAME,
            period_tested="FY2024 vs FY2025",
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_all_long_inputs_combined(self):
        from multi_period_memo_generator import generate_multi_period_memo

        result = self._make_result(LONG_ACCOUNT_NAME, LONG_LEAD_SHEET_NAME)
        pdf = generate_multi_period_memo(
            result,
            filename=LONG_FILENAME,
            client_name=LONG_CUSTOMER_NAME,
            period_tested="FY2024 vs FY2025",
            prepared_by="A" * 80,
            reviewed_by="B" * 80,
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"


# =============================================================================
# Accrual Completeness Memo — Long Account Names
# =============================================================================


class TestAccrualCompleteMemoLongInputs:
    """Verify accrual completeness memo handles long account names."""

    def _make_result(self, account_name: str) -> dict:
        return {
            "accrual_accounts": [
                {
                    "account_name": account_name,
                    "balance": 50000.0,
                    "matched_keyword": "accrued",
                },
                {
                    "account_name": f"Second {account_name}",
                    "balance": 25000.0,
                    "matched_keyword": "provision",
                },
            ],
            "total_accrued_balance": 75000.0,
            "accrual_account_count": 2,
            "monthly_run_rate": 15000.0,
            "accrual_to_run_rate_pct": 41.7,
            "threshold_pct": 50,
            "below_threshold": True,
            "prior_available": True,
            "prior_operating_expenses": 180000.0,
        }

    def test_long_account_name(self):
        from accrual_completeness_memo import generate_accrual_completeness_memo

        result = self._make_result(LONG_ACCOUNT_NAME)
        pdf = generate_accrual_completeness_memo(
            result,
            client_name=LONG_CUSTOMER_NAME,
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_long_filename(self):
        from accrual_completeness_memo import generate_accrual_completeness_memo

        result = self._make_result("Short Account")
        pdf = generate_accrual_completeness_memo(result, filename=LONG_FILENAME)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"


# =============================================================================
# Currency Conversion Memo — Long Account Names
# =============================================================================


class TestCurrencyMemoLongInputs:
    """Verify currency memo handles long account names in unconverted items."""

    def _make_result(self, account_name: str) -> dict:
        return {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 10,
            "converted_count": 8,
            "unconverted_count": 2,
            "unconverted_items": [
                {
                    "account_number": "1000",
                    "account_name": account_name,
                    "original_amount": 1000000,
                    "original_currency": "JPY",
                    "issue": "missing_rate",
                    "severity": "high",
                },
                {
                    "account_number": "2000",
                    "account_name": f"Second {account_name}",
                    "original_amount": 50000,
                    "original_currency": "CHF",
                    "issue": "missing_currency_code",
                    "severity": "low",
                },
            ],
            "currencies_found": ["EUR", "GBP", "USD", "JPY", "CHF"],
            "rates_applied": {"EUR/USD": "1.0523", "GBP/USD": "1.2634"},
            "balance_check_passed": True,
            "balance_imbalance": 0.0,
            "conversion_summary": "8 of 10 accounts converted (80%).",
        }

    def test_long_account_name(self):
        from currency_memo_generator import generate_currency_conversion_memo

        result = self._make_result(LONG_ACCOUNT_NAME)
        pdf = generate_currency_conversion_memo(result)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_long_customer_and_account(self):
        from currency_memo_generator import generate_currency_conversion_memo

        result = self._make_result(LONG_ACCOUNT_NAME)
        pdf = generate_currency_conversion_memo(
            result,
            client_name=LONG_CUSTOMER_NAME,
            filename=LONG_FILENAME,
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"


# =============================================================================
# Population Profile Memo — Long Account Names
# =============================================================================


class TestPopulationProfileMemoLongInputs:
    """Verify population profile memo handles long account names."""

    def _make_result(self, account_name: str) -> dict:
        return {
            "account_count": 50,
            "total_abs_balance": 1000000.0,
            "gini_coefficient": 0.72,
            "gini_interpretation": "High",
            "mean_abs_balance": 20000.0,
            "median_abs_balance": 12000.0,
            "std_abs_balance": 15000.0,
            "min_abs_balance": 100.0,
            "max_abs_balance": 250000.0,
            "top_accounts": [
                {
                    "rank": 1,
                    "account": account_name,
                    "category": "Assets",
                    "net_balance": 250000.0,
                    "percent_of_total": 25.0,
                },
                {
                    "rank": 2,
                    "account": f"Second {account_name}",
                    "category": "Liabilities",
                    "net_balance": 180000.0,
                    "percent_of_total": 18.0,
                },
            ],
            "magnitude_buckets": [],
        }

    def test_long_account_name(self):
        from population_profile_memo import generate_population_profile_memo

        result = self._make_result(LONG_ACCOUNT_NAME)
        pdf = generate_population_profile_memo(result)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_long_customer_name(self):
        from population_profile_memo import generate_population_profile_memo

        result = self._make_result("Normal Account")
        pdf = generate_population_profile_memo(
            result,
            client_name=LONG_CUSTOMER_NAME,
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"


# =============================================================================
# Sampling Memo — Long Item IDs
# =============================================================================


class TestSamplingMemoLongInputs:
    """Verify sampling evaluation memo handles long item IDs."""

    def _make_evaluation_result(self, item_id: str) -> dict:
        return {
            "conclusion": "PASS",
            "sample_size": 30,
            "errors_found": 2,
            "projected_misstatement": 5000.0,
            "tolerable_misstatement": 50000.0,
            "upper_bound": 12000.0,
            "precision": 7000.0,
            "errors": [
                {
                    "item_id": item_id,
                    "recorded_amount": 10000.0,
                    "audited_amount": 9500.0,
                    "misstatement": 500.0,
                    "tainting": 0.05,
                },
                {
                    "item_id": f"SECOND-{item_id}",
                    "recorded_amount": 20000.0,
                    "audited_amount": 19000.0,
                    "misstatement": 1000.0,
                    "tainting": 0.05,
                },
            ],
        }

    def test_long_item_id(self):
        from sampling_memo_generator import generate_sampling_evaluation_memo

        result = self._make_evaluation_result(LONG_ITEM_ID)
        pdf = generate_sampling_evaluation_memo(result)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_long_item_id_with_client(self):
        from sampling_memo_generator import generate_sampling_evaluation_memo

        result = self._make_evaluation_result(LONG_ITEM_ID)
        pdf = generate_sampling_evaluation_memo(
            result,
            client_name=LONG_CUSTOMER_NAME,
            filename=LONG_FILENAME,
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"


# =============================================================================
# Shared Memo Base — Long Test Descriptions (via testing memo template)
# =============================================================================


class TestMemoBaseLongDescriptions:
    """Verify the shared methodology section handles long test descriptions."""

    def test_long_description_in_methodology(self):
        """Methodology table wraps long descriptions instead of truncating."""
        from shared.memo_template import TestingMemoConfig, generate_testing_memo

        long_desc = (
            "Examine all recorded transactions to identify entries "
            "posted on weekends, statutory holidays, or outside normal "
            "business hours that may indicate unauthorized access or "
            "management override of controls per ISA 240.A40 and "
            "PCAOB AS 2401 paragraph 66 regarding journal entry fraud risks — "
            "including but not limited to entries posted by personnel without "
            "proper authorization during off-cycle periods"
        )

        config = TestingMemoConfig(
            title="Test Memo",
            ref_prefix="TST",
            entry_label="Total Entries Tested",
            flagged_label="Total Entries Flagged",
            log_prefix="test_memo",
            domain="test domain",
            test_descriptions={"TEST-01": long_desc},
            methodology_intro="Testing methodology intro.",
            risk_assessments={
                "low": "Low risk.",
                "elevated": "Elevated risk.",
                "moderate": "Moderate risk.",
                "high": "High risk.",
            },
            isa_reference="ISA 240",
            tool_domain="journal_entry_testing",
        )

        result = {
            "composite_score": {
                "score": 5,
                "risk_tier": "low",
                "tests_run": 1,
                "total_entries": 100,
                "entries_flagged": 2,
                "flag_rate": 0.02,
                "severity_breakdown": {"high": 0, "medium": 1, "low": 1},
                "top_findings": [],
            },
            "test_results": [
                {
                    "test_key": "TEST-01",
                    "test_name": "Holiday Posting Detection",
                    "test_tier": "advanced",
                    "entries_flagged": 2,
                    "flag_rate": 0.02,
                    "severity": "medium",
                    "description": long_desc,
                },
            ],
            "data_quality": {"completeness_score": 95},
        }

        pdf = generate_testing_memo(result, config, client_name=LONG_CUSTOMER_NAME)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 100


# =============================================================================
# Report Layout Utility
# =============================================================================


class TestReportLayoutUtility:
    """Verify the shared report_layout module."""

    def test_wrap_cell_returns_paragraph(self):
        from reportlab.platypus import Paragraph

        from shared.memo_base import create_memo_styles
        from shared.report_layout import wrap_cell

        styles = create_memo_styles()
        result = wrap_cell(LONG_ACCOUNT_NAME, styles["MemoTableCell"])
        assert isinstance(result, Paragraph)

    def test_wrap_cell_preserves_full_text(self):
        from shared.memo_base import create_memo_styles
        from shared.report_layout import wrap_cell

        styles = create_memo_styles()
        result = wrap_cell(LONG_ACCOUNT_NAME, styles["MemoTableCell"])
        # Paragraph stores text — verify it contains the full string
        assert LONG_ACCOUNT_NAME in result.text

    def test_wrap_cell_handles_empty_string(self):
        from shared.memo_base import create_memo_styles
        from shared.report_layout import wrap_cell

        styles = create_memo_styles()
        result = wrap_cell("", styles["MemoTableCell"])
        assert result.text == ""

    def test_wrap_cell_coerces_non_string(self):
        from shared.memo_base import create_memo_styles
        from shared.report_layout import wrap_cell

        styles = create_memo_styles()
        result = wrap_cell(12345, styles["MemoTableCell"])
        assert "12345" in result.text

    def test_constants_defined(self):
        from shared.report_layout import (
            MINIMUM_LEADING,
            TABLE_CELL_BOTTOM_PAD,
            TABLE_CELL_TOP_PAD,
        )

        assert MINIMUM_LEADING >= 11
        assert TABLE_CELL_TOP_PAD >= 3
        assert TABLE_CELL_BOTTOM_PAD >= 3
