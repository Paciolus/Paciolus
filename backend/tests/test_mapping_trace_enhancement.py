"""
Sprint 295: TB-to-FS Arithmetic Trace Enhancement

Tests:
- raw_aggregate and sign_correction_applied fields on MappingTraceEntry
- SIGN_CORRECTED_LETTERS constant correctness
- math.fsum precision for raw_aggregate
- sign correction: debit-normal letters (A-F, M, N) = False
- sign correction: credit-normal letters (G-K, L, O) = True
- to_dict() serialization includes new fields
- empty lead sheet entries default correctly
"""

import pytest

from financial_statement_builder import (
    FinancialStatementBuilder,
)

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def grouping_with_accounts():
    """Lead sheet grouping with account-level detail for trace testing."""
    return {
        "summaries": [
            {
                "lead_sheet": "A",
                "name": "Cash and Cash Equivalents",
                "category": "Current Assets",
                "total_debit": 80000.0,
                "total_credit": 0.0,
                "net_balance": 80000.0,
                "account_count": 2,
                "accounts": [
                    {"account": "Cash at Bank", "debit": 50000.0, "credit": 0.0, "confidence": 0.95},
                    {"account": "Petty Cash", "debit": 30000.0, "credit": 0.0, "confidence": 1.0},
                ],
            },
            {
                "lead_sheet": "G",
                "name": "AP & Accrued Liabilities",
                "category": "Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 40000.0,
                "net_balance": -40000.0,
                "account_count": 2,
                "accounts": [
                    {"account": "Accounts Payable", "debit": 0.0, "credit": 25000.0, "confidence": 1.0},
                    {"account": "Accrued Expenses", "debit": 0.0, "credit": 15000.0, "confidence": 0.9},
                ],
            },
            {
                "lead_sheet": "K",
                "name": "Stockholders' Equity",
                "category": "Equity",
                "total_debit": 0.0,
                "total_credit": 40000.0,
                "net_balance": -40000.0,
                "account_count": 1,
                "accounts": [
                    {"account": "Common Stock", "debit": 0.0, "credit": 40000.0, "confidence": 1.0},
                ],
            },
            {
                "lead_sheet": "L",
                "name": "Revenue",
                "category": "Revenue",
                "total_debit": 0.0,
                "total_credit": 100000.0,
                "net_balance": -100000.0,
                "account_count": 1,
                "accounts": [
                    {"account": "Sales Revenue", "debit": 0.0, "credit": 100000.0, "confidence": 1.0},
                ],
            },
            {
                "lead_sheet": "M",
                "name": "Cost of Goods Sold",
                "category": "Cost of Sales",
                "total_debit": 60000.0,
                "total_credit": 0.0,
                "net_balance": 60000.0,
                "account_count": 1,
                "accounts": [
                    {"account": "COGS", "debit": 60000.0, "credit": 0.0, "confidence": 1.0},
                ],
            },
            {
                "lead_sheet": "N",
                "name": "Operating Expenses",
                "category": "Operating Expenses",
                "total_debit": 40000.0,
                "total_credit": 0.0,
                "net_balance": 40000.0,
                "account_count": 1,
                "accounts": [
                    {"account": "Rent Expense", "debit": 40000.0, "credit": 0.0, "confidence": 1.0},
                ],
            },
        ],
        "total_debits": 230000.0,
        "total_credits": 180000.0,
        "unclassified_count": 0,
    }


# ═══════════════════════════════════════════════════════════════
# SIGN_CORRECTED_LETTERS Constant
# ═══════════════════════════════════════════════════════════════

class TestSignCorrectedLetters:
    """Verify SIGN_CORRECTED_LETTERS matches the FS builder sign conventions."""

    def test_credit_normal_letters_in_set(self):
        """G-K (liabilities, equity), L (revenue), O (other income) are sign-corrected."""
        expected = {'G', 'H', 'I', 'J', 'K', 'L', 'O'}
        assert FinancialStatementBuilder.SIGN_CORRECTED_LETTERS == expected

    def test_debit_normal_letters_not_in_set(self):
        """A-F (assets), M (COGS), N (OpEx) are NOT sign-corrected."""
        debit_normal = {'A', 'B', 'C', 'D', 'E', 'F', 'M', 'N'}
        for letter in debit_normal:
            assert letter not in FinancialStatementBuilder.SIGN_CORRECTED_LETTERS


# ═══════════════════════════════════════════════════════════════
# Raw Aggregate & Sign Correction in Mapping Trace
# ═══════════════════════════════════════════════════════════════

class TestMappingTraceEnhancement:
    """Verify raw_aggregate and sign_correction_applied in mapping trace entries."""

    def test_asset_not_sign_corrected(self, grouping_with_accounts):
        """Letter A (asset) should have sign_correction_applied=False."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()

        a_entry = next(e for e in stmts.mapping_trace if e.lead_sheet_ref == "A")
        assert a_entry.sign_correction_applied is False

    def test_asset_raw_aggregate(self, grouping_with_accounts):
        """Letter A raw_aggregate should equal sum of account net balances."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()

        a_entry = next(e for e in stmts.mapping_trace if e.lead_sheet_ref == "A")
        # 50000 + 30000 = 80000
        assert a_entry.raw_aggregate == pytest.approx(80000.0)

    def test_liability_sign_corrected(self, grouping_with_accounts):
        """Letter G (liability) should have sign_correction_applied=True."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()

        g_entry = next(e for e in stmts.mapping_trace if e.lead_sheet_ref == "G")
        assert g_entry.sign_correction_applied is True

    def test_liability_raw_aggregate_is_negative(self, grouping_with_accounts):
        """Letter G raw_aggregate = sum of (debit-credit) = -40000 (credit-normal)."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()

        g_entry = next(e for e in stmts.mapping_trace if e.lead_sheet_ref == "G")
        # 0-25000 + 0-15000 = -40000
        assert g_entry.raw_aggregate == pytest.approx(-40000.0)

    def test_equity_sign_corrected(self, grouping_with_accounts):
        """Letter K (equity) should have sign_correction_applied=True."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()

        k_entry = next(e for e in stmts.mapping_trace if e.lead_sheet_ref == "K")
        assert k_entry.sign_correction_applied is True

    def test_revenue_sign_corrected(self, grouping_with_accounts):
        """Letter L (revenue) should have sign_correction_applied=True."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()

        l_entry = next(e for e in stmts.mapping_trace if e.lead_sheet_ref == "L")
        assert l_entry.sign_correction_applied is True
        assert l_entry.raw_aggregate == pytest.approx(-100000.0)

    def test_cogs_not_sign_corrected(self, grouping_with_accounts):
        """Letter M (COGS) should have sign_correction_applied=False."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()

        m_entry = next(e for e in stmts.mapping_trace if e.lead_sheet_ref == "M")
        assert m_entry.sign_correction_applied is False
        assert m_entry.raw_aggregate == pytest.approx(60000.0)

    def test_opex_not_sign_corrected(self, grouping_with_accounts):
        """Letter N (OpEx) should have sign_correction_applied=False."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()

        n_entry = next(e for e in stmts.mapping_trace if e.lead_sheet_ref == "N")
        assert n_entry.sign_correction_applied is False

    def test_empty_lead_sheet_defaults(self, grouping_with_accounts):
        """Missing lead sheet (e.g., B) should have raw_aggregate=0 and correct sign flag."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()

        # B is not in the fixture summaries
        b_entry = next(e for e in stmts.mapping_trace if e.lead_sheet_ref == "B")
        assert b_entry.raw_aggregate == 0.0
        assert b_entry.sign_correction_applied is False  # B is debit-normal
        assert b_entry.account_count == 0

    def test_empty_liability_has_sign_flag(self, grouping_with_accounts):
        """Missing credit-normal lead sheet (H) should still have sign_correction_applied=True."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()

        h_entry = next(e for e in stmts.mapping_trace if e.lead_sheet_ref == "H")
        assert h_entry.sign_correction_applied is True
        assert h_entry.raw_aggregate == 0.0

    def test_statement_amount_matches_sign_corrected_aggregate(self, grouping_with_accounts):
        """Statement amount should equal -raw_aggregate for sign-corrected, raw_aggregate otherwise."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()

        for entry in stmts.mapping_trace:
            if entry.account_count == 0:
                continue  # Skip empty entries
            if entry.sign_correction_applied:
                expected = -entry.raw_aggregate
            else:
                expected = entry.raw_aggregate
            assert entry.statement_amount == pytest.approx(expected, abs=0.01), (
                f"{entry.lead_sheet_ref}: statement_amount={entry.statement_amount} "
                f"!= expected={expected} (raw={entry.raw_aggregate}, corrected={entry.sign_correction_applied})"
            )


# ═══════════════════════════════════════════════════════════════
# to_dict() Serialization
# ═══════════════════════════════════════════════════════════════

class TestMappingTraceSerialization:
    """Verify to_dict() includes new fields."""

    def test_to_dict_includes_raw_aggregate(self, grouping_with_accounts):
        """to_dict mapping_trace entries should contain raw_aggregate."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()
        d = stmts.to_dict()

        for entry_dict in d["mapping_trace"]:
            assert "raw_aggregate" in entry_dict

    def test_to_dict_includes_sign_correction(self, grouping_with_accounts):
        """to_dict mapping_trace entries should contain sign_correction_applied."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()
        d = stmts.to_dict()

        for entry_dict in d["mapping_trace"]:
            assert "sign_correction_applied" in entry_dict

    def test_to_dict_sign_correction_values(self, grouping_with_accounts):
        """Serialized sign_correction_applied should match letter convention."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        stmts = builder.build()
        d = stmts.to_dict()

        for entry_dict in d["mapping_trace"]:
            ref = entry_dict["lead_sheet_ref"]
            expected = ref in {'G', 'H', 'I', 'J', 'K', 'L', 'O'}
            assert entry_dict["sign_correction_applied"] is expected, f"Letter {ref}"


# ═══════════════════════════════════════════════════════════════
# math.fsum Precision
# ═══════════════════════════════════════════════════════════════

class TestFsumPrecision:
    """Verify math.fsum is used for raw_aggregate computation."""

    def test_fsum_precision_avoids_float_drift(self):
        """Values that cause naive summation drift should be precise with fsum."""
        # Construct a grouping where naive sum would differ from fsum
        accounts = [
            {"account": f"Acct{i}", "debit": 0.1, "credit": 0.0}
            for i in range(10)
        ]
        grouping = {
            "summaries": [
                {
                    "lead_sheet": "A",
                    "name": "Cash",
                    "net_balance": 1.0,
                    "account_count": 10,
                    "accounts": accounts,
                },
                # Need balanced grouping for builder
                {
                    "lead_sheet": "K",
                    "name": "Equity",
                    "net_balance": -1.0,
                    "account_count": 0,
                    "accounts": [],
                },
            ],
        }
        builder = FinancialStatementBuilder(grouping)
        stmts = builder.build()

        a_entry = next(e for e in stmts.mapping_trace if e.lead_sheet_ref == "A")
        # math.fsum([0.1]*10) == 1.0 exactly
        assert a_entry.raw_aggregate == pytest.approx(1.0, abs=1e-10)
