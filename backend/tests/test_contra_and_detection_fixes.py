"""Tests for Sprint 530: Contra accounts, detection fixes, and ratio improvements.

Covers:
- Fix 1: Contra account recognition (is_contra_account + abnormal balance inversion)
- Fix 2: Related party keyword tightening
- Fix 3: Suspense/related party mutual exclusivity
- Fix 4: Intercompany counterparty extraction
- Fix 5: Current/non-current subtype stratification
- Fix 6: Lead sheet credits
- Fix 7: Gross margin COGS from subtype
- Fix 8: Concentration finding pluralization
- Fix 9: Score decomposition top-N
"""

import pytest

from audit_engine import StreamingAuditor, _merge_anomalies
from classification_rules import (
    RELATED_PARTY_KEYWORDS,
    SUSPENSE_KEYWORDS,
    AccountCategory,
    is_contra_account,
)
from ratio_engine import CategoryTotals, extract_category_totals
from shared.tb_diagnostic_constants import compute_tb_risk_score

# =============================================================================
# Fix 1: Contra Account Recognition
# =============================================================================


class TestIsContraAccount:
    """Unit tests for is_contra_account()."""

    @pytest.mark.parametrize(
        "name",
        [
            "Accumulated Depreciation — Buildings",
            "accumulated depreciation — equipment",
            "Accumulated Amortization — Patents",
            "Allowance for Doubtful Accounts",
            "Allowance — Bad Debts",
            "Obsolescence Reserve",
            "Valuation Allowance — DTA",
            "Less Accumulated Depreciation",
        ],
    )
    def test_contra_asset_detected(self, name: str) -> None:
        assert is_contra_account(name, AccountCategory.ASSET) is True

    @pytest.mark.parametrize(
        "name",
        [
            "Cash and Equivalents",
            "Accounts Receivable",
            "Prepaid Insurance",
            "Inventory — Raw Materials",
            "Property, Plant and Equipment",
        ],
    )
    def test_non_contra_asset_not_detected(self, name: str) -> None:
        assert is_contra_account(name, AccountCategory.ASSET) is False

    @pytest.mark.parametrize(
        "name",
        [
            "Sales Discounts",
            "Sales Returns and Allowances",
            "Contra Revenue — Adjustments",
            "Trade Discounts Given",
        ],
    )
    def test_contra_revenue_detected(self, name: str) -> None:
        assert is_contra_account(name, AccountCategory.REVENUE) is True

    @pytest.mark.parametrize(
        "name",
        [
            "Product Revenue",
            "Service Revenue",
            "Interest Income",
        ],
    )
    def test_non_contra_revenue_not_detected(self, name: str) -> None:
        assert is_contra_account(name, AccountCategory.REVENUE) is False

    @pytest.mark.parametrize(
        "name",
        [
            "Treasury Stock",
            "Dividends Declared",
            "Drawing — Partner A",
        ],
    )
    def test_contra_equity_detected(self, name: str) -> None:
        assert is_contra_account(name, AccountCategory.EQUITY) is True

    @pytest.mark.parametrize(
        "name",
        [
            "Discount on Bonds Payable",
            "Debt Issuance Costs",
            "Bond Discount — Series A",
        ],
    )
    def test_contra_liability_detected(self, name: str) -> None:
        assert is_contra_account(name, AccountCategory.LIABILITY) is True

    @pytest.mark.parametrize(
        "name",
        [
            "Common Stock",
            "Retained Earnings",
            "Additional Paid-In Capital",
        ],
    )
    def test_non_contra_equity_not_detected(self, name: str) -> None:
        assert is_contra_account(name, AccountCategory.EQUITY) is False

    def test_liability_never_contra(self):
        """Liabilities don't have recognised contra patterns in this system."""
        assert is_contra_account("Accumulated Depreciation", AccountCategory.LIABILITY) is False

    def test_expense_never_contra(self):
        assert is_contra_account("Treasury Stock", AccountCategory.EXPENSE) is False


class TestContraAbnormalBalanceInversion:
    """Test that contra accounts don't generate false positive abnormal balance findings."""

    def _make_auditor(self, accounts: dict, types: dict | None = None) -> StreamingAuditor:
        auditor = StreamingAuditor(materiality_threshold=10000.0)
        auditor.account_balances = accounts
        if types:
            auditor.provided_account_types = types
        return auditor

    def test_accumulated_depreciation_credit_not_flagged(self):
        """Credit balance in accumulated depreciation is normal for a contra-asset."""
        auditor = self._make_auditor(
            {"Accumulated Depreciation — Buildings": {"debit": 0.0, "credit": 500000.0}},
            {"Accumulated Depreciation — Buildings": "Asset"},
        )
        findings = auditor.get_abnormal_balances()
        assert len(findings) == 0

    def test_accumulated_depreciation_debit_IS_flagged(self):
        """Debit balance in accumulated depreciation IS abnormal — should be flagged."""
        auditor = self._make_auditor(
            {"Accumulated Depreciation — Buildings": {"debit": 500000.0, "credit": 0.0}},
            {"Accumulated Depreciation — Buildings": "Asset"},
        )
        findings = auditor.get_abnormal_balances()
        assert len(findings) == 1
        assert findings[0]["account"] == "Accumulated Depreciation — Buildings"

    def test_allowance_for_doubtful_accounts_credit_not_flagged(self):
        auditor = self._make_auditor(
            {"Allowance for Doubtful Accounts": {"debit": 0.0, "credit": 75000.0}},
            {"Allowance for Doubtful Accounts": "Asset"},
        )
        findings = auditor.get_abnormal_balances()
        assert len(findings) == 0

    def test_sales_returns_debit_not_flagged(self):
        """Debit balance in Sales Returns is normal for a contra-revenue account."""
        auditor = self._make_auditor(
            {"Sales Returns": {"debit": 200000.0, "credit": 0.0}},
            {"Sales Returns": "Revenue"},
        )
        findings = auditor.get_abnormal_balances()
        assert len(findings) == 0

    def test_treasury_stock_debit_not_flagged(self):
        """Debit balance in Treasury Stock is normal for a contra-equity account."""
        auditor = self._make_auditor(
            {"Treasury Stock": {"debit": 1000000.0, "credit": 0.0}},
            {"Treasury Stock": "Equity"},
        )
        findings = auditor.get_abnormal_balances()
        assert len(findings) == 0

    def test_wip_inventory_credit_still_flagged(self):
        """WIP Inventory is NOT a contra account — credit balance is genuinely abnormal."""
        auditor = self._make_auditor(
            {"WIP Inventory": {"debit": 0.0, "credit": 150000.0}},
            {"WIP Inventory": "Asset"},
        )
        findings = auditor.get_abnormal_balances()
        assert len(findings) == 1

    def test_customer_deposits_debit_still_flagged(self):
        """Customer Deposits is a liability — debit balance is genuinely abnormal."""
        auditor = self._make_auditor(
            {"Customer Deposits": {"debit": 50000.0, "credit": 0.0}},
            {"Customer Deposits": "Liability"},
        )
        findings = auditor.get_abnormal_balances()
        assert len(findings) == 1


class TestContraRoundingExclusion:
    """Test that contra accounts don't generate round-number findings."""

    def _make_auditor(self, accounts: dict, types: dict | None = None) -> StreamingAuditor:
        auditor = StreamingAuditor(materiality_threshold=10000.0)
        auditor.account_balances = accounts
        if types:
            auditor.provided_account_types = types
        return auditor

    def test_accumulated_depreciation_round_suppressed(self):
        auditor = self._make_auditor(
            {"Accumulated Depreciation — Buildings": {"debit": 0.0, "credit": 500000.0}},
            {"Accumulated Depreciation — Buildings": "Asset"},
        )
        rounding = auditor.detect_rounding_anomalies()
        assert len(rounding) == 0

    def test_allowance_round_minor(self):
        """Sprint 536+: contra-asset round balances emit a minor observation (not suppressed)."""
        auditor = self._make_auditor(
            {"Allowance for Doubtful Accounts": {"debit": 0.0, "credit": 100000.0}},
            {"Allowance for Doubtful Accounts": "Asset"},
        )
        rounding = auditor.detect_rounding_anomalies()
        assert len(rounding) == 1
        assert rounding[0]["severity"] == "low"


# =============================================================================
# Fix 2: Related Party Keyword Tightening
# =============================================================================


class TestRelatedPartyKeywordTightening:
    """Verify that insurance and fee accounts don't trigger related party findings."""

    def _make_auditor(self, accounts: dict, types: dict | None = None) -> StreamingAuditor:
        auditor = StreamingAuditor(materiality_threshold=10000.0)
        auditor.account_balances = accounts
        if types:
            auditor.provided_account_types = types
        return auditor

    def test_directors_officers_insurance_excluded(self):
        auditor = self._make_auditor(
            {"6330 — Directors and Officers Insurance": {"debit": 50000.0, "credit": 0.0}},
        )
        findings = auditor.detect_related_party_accounts()
        assert len(findings) == 0

    def test_board_of_directors_fees_excluded(self):
        auditor = self._make_auditor(
            {"6550 — Board of Directors Fees": {"debit": 120000.0, "credit": 0.0}},
        )
        findings = auditor.detect_related_party_accounts()
        assert len(findings) == 0

    def test_legitimate_related_party_still_detected(self):
        auditor = self._make_auditor(
            {"1150 — AR — Related Party": {"debit": 500000.0, "credit": 0.0}},
        )
        findings = auditor.detect_related_party_accounts()
        assert len(findings) == 1
        assert "related party" in findings[0]["matched_keywords"]

    def test_bare_officer_keyword_removed(self):
        """The word 'officer' alone should no longer be a related party keyword."""
        kw_terms = [kw for kw, _w, _p in RELATED_PARTY_KEYWORDS]
        assert "officer" not in kw_terms
        assert "director" not in kw_terms
        assert "shareholder" not in kw_terms

    def test_due_to_officer_IS_keyword(self):
        kw_terms = [kw for kw, _w, _p in RELATED_PARTY_KEYWORDS]
        assert "due to officer" in kw_terms
        assert "due from officer" in kw_terms


# =============================================================================
# Fix 3: Suspense/Related Party Mutual Exclusivity
# =============================================================================


class TestSuspenseRelatedPartyExclusivity:
    """Verify that accounts classified as related party are not also classified as suspense."""

    def test_related_party_account_not_also_suspense(self):
        """An account in the related_party list should be excluded from suspense merge."""
        abnormal = []
        suspense = [
            {
                "account": "1150 — AR — Related Party",
                "severity": "medium",
                "anomaly_type": "suspense_account",
                "confidence": 0.80,
                "matched_keywords": ["clearing"],
            },
        ]
        related_party = [
            {"account": "1150 — AR — Related Party", "severity": "high", "anomaly_type": "related_party"},
        ]

        merged = _merge_anomalies(
            abnormal,
            suspense,
            [],
            [],
            related_party=related_party,
            intercompany=None,
        )

        # The account should appear once, as related party
        accounts = [m["account"] for m in merged]
        assert accounts.count("1150 — AR — Related Party") == 1
        entry = merged[0]
        # The entry comes from related_party (anomaly_type="related_party"),
        # and suspense should NOT be merged in due to exclusivity
        assert entry.get("anomaly_type") == "related_party"
        assert entry.get("is_suspense_account") is not True

    def test_intercompany_suppresses_rounding(self):
        """An intercompany imbalance finding should suppress round-number for the same account."""
        abnormal = []
        rounding = [
            {
                "account": "1810 — IC Receivable — Mexico",
                "severity": "low",
                "anomaly_type": "rounding_anomaly",
                "rounding_pattern": "hundred_thousand",
            },
        ]
        intercompany = [
            {
                "account": "1810 — IC Receivable — Mexico",
                "severity": "high",
                "anomaly_type": "intercompany_imbalance",
                "cross_reference_note": "Net exposure: $1,150,000",
            },
        ]

        merged = _merge_anomalies(
            abnormal,
            [],
            [],
            rounding,
            intercompany=intercompany,
        )

        accounts = [m["account"] for m in merged]
        assert accounts.count("1810 — IC Receivable — Mexico") == 1
        entry = merged[0]
        assert entry.get("anomaly_type") == "intercompany_imbalance"
        assert entry.get("has_rounding_anomaly") is not True


# =============================================================================
# Fix 4: Intercompany Counterparty Extraction
# =============================================================================


class TestIntercompanyCounterpartyExtraction:
    """Test that counterparty names are extracted with various separators."""

    def _make_auditor(self, accounts: dict) -> StreamingAuditor:
        auditor = StreamingAuditor(materiality_threshold=10000.0)
        auditor.account_balances = accounts
        return auditor

    def test_em_dash_with_spaces(self):
        """Standard format: 'Intercompany Receivable — Cascade Mexico S.A.'"""
        auditor = self._make_auditor(
            {
                "1810 — Intercompany Receivable — Cascade Mexico S.A.": {"debit": 1150000.0, "credit": 0.0},
            }
        )
        auditor.provided_account_names = {"1810": "Intercompany Receivable — Cascade Mexico S.A."}
        findings = auditor.detect_intercompany_imbalances()
        # Should detect imbalance — no matching payable
        assert len(findings) >= 1

    def test_hyphen_separator(self):
        auditor = self._make_auditor(
            {
                "IC Receivable - SomeCo Ltd": {"debit": 500000.0, "credit": 0.0},
            }
        )
        findings = auditor.detect_intercompany_imbalances()
        assert len(findings) >= 1


# =============================================================================
# Fix 5 & 7: Subtype-driven stratification and COGS
# =============================================================================


class TestSubtypeDrivenCategoryTotals:
    """Test that CSV subtypes drive current/non-current and COGS classification."""

    def test_current_asset_subtype(self):
        balances = {"Cash": {"debit": 100000.0, "credit": 0.0}}
        classified = {"Cash": "asset"}
        subtypes = {"Cash": "Current Asset"}
        totals = extract_category_totals(balances, classified, account_subtypes=subtypes)
        assert totals.current_assets == 100000.0

    def test_non_current_asset_subtype_excluded_from_current(self):
        balances = {"Equipment": {"debit": 500000.0, "credit": 0.0}}
        classified = {"Equipment": "asset"}
        subtypes = {"Equipment": "Non-Current Asset"}
        totals = extract_category_totals(balances, classified, account_subtypes=subtypes)
        assert totals.total_assets == 500000.0
        assert totals.current_assets == 0.0

    def test_current_liability_subtype(self):
        balances = {"AP": {"debit": 0.0, "credit": 200000.0}}
        classified = {"AP": "liability"}
        subtypes = {"AP": "Current Liability"}
        totals = extract_category_totals(balances, classified, account_subtypes=subtypes)
        assert totals.current_liabilities == 200000.0

    def test_non_current_liability_subtype_excluded(self):
        balances = {"Bonds Payable": {"debit": 0.0, "credit": 1000000.0}}
        classified = {"Bonds Payable": "liability"}
        subtypes = {"Bonds Payable": "Non-Current Liability"}
        totals = extract_category_totals(balances, classified, account_subtypes=subtypes)
        assert totals.total_liabilities == 1000000.0
        assert totals.current_liabilities == 0.0

    def test_cogs_from_subtype(self):
        balances = {"Materials": {"debit": 500000.0, "credit": 0.0}}
        classified = {"Materials": "expense"}
        subtypes = {"Materials": "Cost of Revenue"}
        totals = extract_category_totals(balances, classified, account_subtypes=subtypes)
        assert totals.cost_of_goods_sold == 500000.0

    def test_cogs_from_keyword_fallback(self):
        """Without subtype, fall back to keyword matching."""
        balances = {"Cost of Goods Sold": {"debit": 500000.0, "credit": 0.0}}
        classified = {"Cost of Goods Sold": "expense"}
        totals = extract_category_totals(balances, classified)
        assert totals.cost_of_goods_sold == 500000.0

    def test_keyword_fallback_when_no_subtype(self):
        """Without subtypes, current/non-current still uses keywords."""
        balances = {"Cash": {"debit": 100000.0, "credit": 0.0}}
        classified = {"Cash": "asset"}
        totals = extract_category_totals(balances, classified)
        assert totals.current_assets == 100000.0

    def test_gross_margin_with_cogs_subtype(self):
        """Verify that gross margin calculates correctly when COGS uses subtype."""
        from ratio_engine import RatioEngine

        totals = CategoryTotals(
            total_revenue=27600000.0,
            cost_of_goods_sold=20800000.0,
            total_expenses=25000000.0,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_gross_margin()
        assert result.is_calculable
        # (27.6M - 20.8M) / 27.6M = 24.6%
        assert 24.0 <= result.value <= 25.0

    def test_current_ratio_with_subtype(self):
        totals = CategoryTotals(
            total_assets=5000000.0,
            current_assets=2000000.0,
            total_liabilities=3000000.0,
            current_liabilities=1000000.0,
        )
        from ratio_engine import RatioEngine

        engine = RatioEngine(totals)
        result = engine.calculate_current_ratio()
        assert result.is_calculable
        assert result.value == 2.0


# =============================================================================
# Fix 6: Lead Sheet Credits
# =============================================================================


class TestLeadSheetCredits:
    """Test that the post-processor passes raw debit/credit to lead sheet grouping."""

    def test_credit_balance_preserved(self):
        from shared.tb_post_processor import apply_lead_sheet_grouping

        result = {
            "abnormal_balances": [
                {
                    "account": "Trade Accounts Payable",
                    "type": "Liability",
                    "issue": "Test",
                    "amount": 500000.0,
                    "debit": 0.0,
                    "credit": 500000.0,
                    "materiality": "material",
                    "severity": "high",
                    "anomaly_type": "concentration_risk",
                },
            ],
        }
        apply_lead_sheet_grouping(result, 10000.0)
        grouping = result.get("lead_sheet_grouping", {})
        summaries = grouping.get("summaries", [])
        # At least one lead sheet should have non-zero credit
        total_credit = sum(s.get("total_credit", 0) for s in summaries)
        assert total_credit > 0, "Credits column should not be all zeros"


# =============================================================================
# Fix 8: Concentration Pluralization
# =============================================================================


class TestConcentrationPluralization:
    def _make_auditor(self, accounts: dict, types: dict | None = None) -> StreamingAuditor:
        auditor = StreamingAuditor(materiality_threshold=10000.0)
        auditor.account_balances = accounts
        if types:
            auditor.provided_account_types = types
        return auditor

    def test_liability_plural(self):
        """Should say 'liabilities' not 'liabilitys'."""
        auditor = self._make_auditor(
            {
                "Big Loan": {"debit": 0.0, "credit": 900000.0},
                "Small AP": {"debit": 0.0, "credit": 100000.0},
            },
            {"Big Loan": "Liability", "Small AP": "Liability"},
        )
        findings = auditor.detect_concentration_risk()
        for f in findings:
            if "liabilit" in f["issue"].lower():
                assert "liabilitys" not in f["issue"]
                assert "liabilities" in f["issue"]

    def test_asset_plural(self):
        auditor = self._make_auditor(
            {
                "Cash": {"debit": 900000.0, "credit": 0.0},
                "Prepaid": {"debit": 100000.0, "credit": 0.0},
            },
            {"Cash": "Asset", "Prepaid": "Asset"},
        )
        findings = auditor.detect_concentration_risk()
        for f in findings:
            if "asset" in f["issue"].lower():
                assert "assets" in f["issue"]


# =============================================================================
# Fix 9: Score Decomposition Top-N
# =============================================================================


class TestScoreDecompositionTopN:
    """Test that score decomposition limits named factors to 8 + summary."""

    def test_top_8_with_summary(self):
        """With 15 material findings, should get 8 named + 1 summary line."""
        findings = []
        for i in range(15):
            findings.append(
                {
                    "account": f"Account {i}",
                    "anomaly_type": "rounding_anomaly",
                    "materiality": "material",
                    "amount": (15 - i) * 100000,
                    "type": "Asset",
                    "issue": f"Round number #{i}",
                }
            )
        score, factors = compute_tb_risk_score(
            material_count=15,
            minor_count=0,
            coverage_pct=30.0,
            has_suspense=False,
            has_credit_balance_asset=False,
            abnormal_balances=findings,
        )
        # Named material factors: 8 individual + 1 summary for remaining 7
        material_factors = [f for f in factors if f[1] == 8 or "additional findings" in f[0]]
        named_factors = [f for f in material_factors if "additional findings" not in f[0]]
        summary_factors = [f for f in material_factors if "additional findings" in f[0]]

        assert len(named_factors) == 8
        assert len(summary_factors) == 1
        assert "7 additional findings" in summary_factors[0][0]

    def test_few_findings_no_summary(self):
        """With <= 8 material findings, all should be named (no summary line)."""
        findings = [
            {
                "account": f"Account {i}",
                "anomaly_type": "rounding_anomaly",
                "materiality": "material",
                "amount": 100000,
                "type": "Asset",
                "issue": "Round",
            }
            for i in range(5)
        ]
        score, factors = compute_tb_risk_score(
            material_count=5,
            minor_count=0,
            coverage_pct=10.0,
            has_suspense=False,
            has_credit_balance_asset=False,
            abnormal_balances=findings,
        )
        material_factors = [f for f in factors if f[1] == 8]
        assert len(material_factors) == 5
        assert not any("additional findings" in f[0] for f in factors)

    def test_total_reconciles(self):
        """Total score must reconcile regardless of decomposition structure."""
        findings = [
            {
                "account": f"A{i}",
                "anomaly_type": "natural_balance_violation",
                "materiality": "material",
                "amount": 50000 * (i + 1),
                "type": "Asset",
                "issue": "Test",
            }
            for i in range(12)
        ]
        score, factors = compute_tb_risk_score(
            material_count=12,
            minor_count=3,
            coverage_pct=55.0,
            has_suspense=True,
            has_credit_balance_asset=True,
            abnormal_balances=findings,
        )
        factor_total = sum(pts for _, pts in factors)
        # Score is capped at 100
        assert score == min(factor_total, 100)


# =============================================================================
# Suspense keyword removal verification
# =============================================================================


class TestSuspenseKeywordCleanup:
    """Verify vague terms were removed from suspense keywords."""

    def test_holding_removed(self):
        kw_terms = [kw for kw, _w, _p in SUSPENSE_KEYWORDS]
        assert "holding" not in kw_terms
        assert "hold account" in kw_terms  # Specific term kept

    def test_other_removed(self):
        kw_terms = [kw for kw, _w, _p in SUSPENSE_KEYWORDS]
        assert "other" not in kw_terms

    def test_general_removed(self):
        kw_terms = [kw for kw, _w, _p in SUSPENSE_KEYWORDS]
        assert "general" not in kw_terms

    def test_unidentified_removed(self):
        kw_terms = [kw for kw, _w, _p in SUSPENSE_KEYWORDS]
        assert "unidentified" not in kw_terms

    def test_wash_account_added(self):
        kw_terms = [kw for kw, _w, _p in SUSPENSE_KEYWORDS]
        assert "wash account" in kw_terms
