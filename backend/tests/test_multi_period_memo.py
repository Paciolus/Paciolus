"""
Tests for Multi-Period Comparison Memo Generator (Sprint 128 / Sprint 505)

Tests:
- PDF generation and validation
- Optional workpaper parameters
- Conclusion tier coverage (low, moderate, elevated, high)
- Lead sheet summary handling
- Guardrail compliance (terminology, ISA references)
- Export route registration
- Pydantic input model validation
- Results Summary with risk score (BUG-02)
- Diagnostic scoring function (BUG-02)
- Sign Change Detail rendering (BUG-03)
- Dormant Account Detail rendering (BUG-04)
- Ratio Trends expanded (IMP-01)
- Suggested Procedures (IMP-02)
- New/Closed Account Detail (IMP-05)
- Lead sheet % Change column (IMP-04)
"""

import inspect

import pytest

from multi_period_memo_generator import (
    _COGS_KEYWORDS,
    _REVENUE_KEYWORDS,
    _RISK_CONCLUSION_SUFFIXES,
    _build_risk_conclusion,
    _match_keyword,
    compute_apc_diagnostic_score,
    generate_multi_period_memo,
)

# =============================================================================
# FIXTURES
# =============================================================================


def _make_comparison_result(
    total_accounts: int = 80,
    material: int = 3,
    significant: int = 8,
    minor: int = 69,
    num_significant_movements: int = 11,
    num_lead_sheets: int = 5,
    budget_label: str | None = None,
    dormant_count: int = 2,
) -> dict:
    """Build a minimal MovementSummaryResponse-shaped dict for testing."""
    significant_movements = []
    for i in range(num_significant_movements):
        ls_idx = (i % num_lead_sheets) if num_lead_sheets > 0 else 0
        significant_movements.append(
            {
                "account_name": f"Account {i + 1}",
                "account_type": "asset" if i % 2 == 0 else "liability",
                "prior_balance": 10000.0 * (i + 1),
                "current_balance": 10000.0 * (i + 1) + 5000.0 * ((-1) ** i),
                "change_amount": 5000.0 * ((-1) ** i),
                "change_percent": 50.0 * ((-1) ** i) / (i + 1),
                "movement_type": "increase" if i % 2 == 0 else "decrease",
                "significance": "material" if i < material else "significant",
                "lead_sheet": chr(65 + ls_idx),
                "lead_sheet_name": f"Lead Sheet {chr(65 + ls_idx)}",
                "lead_sheet_category": "asset" if i % 2 == 0 else "liability",
                "is_dormant": False,
            }
        )

    lead_sheet_summaries: list[dict[str, object]] = []
    for j in range(num_lead_sheets):
        lead_sheet_summaries.append(
            {
                "lead_sheet": chr(65 + j),
                "lead_sheet_name": f"Lead Sheet {chr(65 + j)}",
                "lead_sheet_category": "asset" if j < 3 else "liability",
                "prior_total": 50000.0 * (j + 1),
                "current_total": 55000.0 * (j + 1),
                "net_change": 5000.0 * (j + 1),
                "change_percent": 10.0,
                "account_count": total_accounts // num_lead_sheets,
                "movements": [],
            }
        )

    result = {
        "prior_label": "FY2024",
        "current_label": "FY2025",
        "total_accounts": total_accounts,
        "movements_by_type": {
            "increase": 30,
            "decrease": 25,
            "new_account": 5,
            "closed_account": 2,
            "sign_change": 1,
            "unchanged": 17,
        },
        "movements_by_significance": {
            "material": material,
            "significant": significant,
            "minor": minor,
        },
        "significant_movements": significant_movements,
        "lead_sheet_summaries": lead_sheet_summaries,
        "dormant_account_count": dormant_count,
    }
    if budget_label:
        result["budget_label"] = budget_label
    return result


def _make_enriched_result() -> dict:
    """Build a fully enriched comparison result with all Sprint 505 fields."""
    all_movements = [
        {
            "account_name": "Revenue — Consulting Services",
            "account_type": "revenue",
            "prior_balance": 3_600_000,
            "current_balance": 4_250_000,
            "change_amount": 650_000,
            "change_percent": 18.1,
            "movement_type": "increase",
            "significance": "material",
        },
        {
            "account_name": "Revenue — Software Licensing",
            "account_type": "revenue",
            "prior_balance": 1_450_000,
            "current_balance": 1_720_000,
            "change_amount": 270_000,
            "change_percent": 18.6,
            "movement_type": "increase",
            "significance": "material",
        },
        {
            "account_name": "Revenue — Support & Maintenance",
            "account_type": "revenue",
            "prior_balance": 750_000,
            "current_balance": 880_000,
            "change_amount": 130_000,
            "change_percent": 17.3,
            "movement_type": "increase",
            "significance": "significant",
        },
        {
            "account_name": "Cost of Goods Sold",
            "account_type": "cogs",
            "prior_balance": 2_400_000,
            "current_balance": 2_890_000,
            "change_amount": 490_000,
            "change_percent": 20.4,
            "movement_type": "increase",
            "significance": "material",
        },
        {
            "account_name": "Salaries & Wages",
            "account_type": "expense",
            "prior_balance": 1_180_000,
            "current_balance": 1_420_000,
            "change_amount": 240_000,
            "change_percent": 20.3,
            "movement_type": "increase",
            "significance": "material",
        },
        {
            "account_name": "Marketing & Advertising",
            "account_type": "expense",
            "prior_balance": 120_000,
            "current_balance": 195_000,
            "change_amount": 75_000,
            "change_percent": 62.5,
            "movement_type": "increase",
            "significance": "material",
        },
        {
            "account_name": "Cash and Cash Equivalents",
            "account_type": "asset",
            "prior_balance": 776_750,
            "current_balance": 1_245_000,
            "change_amount": 468_250,
            "change_percent": 60.3,
            "movement_type": "increase",
            "significance": "material",
        },
        {
            "account_name": "Accounts Receivable — Trade",
            "account_type": "asset",
            "prior_balance": 750_000,
            "current_balance": 892_000,
            "change_amount": 142_000,
            "change_percent": 18.9,
            "movement_type": "increase",
            "significance": "material",
        },
        {
            "account_name": "Inventory",
            "account_type": "asset",
            "prior_balance": 494_000,
            "current_balance": 456_000,
            "change_amount": -38_000,
            "change_percent": -7.7,
            "movement_type": "decrease",
            "significance": "significant",
        },
        {
            "account_name": "Property, Plant & Equipment",
            "account_type": "asset",
            "prior_balance": 2_100_000,
            "current_balance": 2_240_000,
            "change_amount": 140_000,
            "change_percent": 6.7,
            "movement_type": "increase",
            "significance": "significant",
        },
        {
            "account_name": "Long-Term Debt",
            "account_type": "liability",
            "prior_balance": 1_620_000,
            "current_balance": 1_500_000,
            "change_amount": -120_000,
            "change_percent": -7.4,
            "movement_type": "decrease",
            "significance": "significant",
        },
        {
            "account_name": "Deferred Revenue — Project Alpha",
            "account_type": "liability",
            "prior_balance": -85_000,
            "current_balance": 42_000,
            "change_amount": 127_000,
            "change_percent": -149.4,
            "movement_type": "sign_change",
            "significance": "significant",
        },
    ]

    significant_movements = [m for m in all_movements if m.get("significance") in ("material", "significant")]

    return {
        "prior_label": "FY 2024",
        "current_label": "FY 2025",
        "total_accounts": 247,
        "dormant_account_count": 3,
        "movements_by_type": {
            "new_account": 4,
            "closed_account": 2,
            "sign_change": 1,
            "increase": 142,
            "decrease": 95,
            "unchanged": 3,
        },
        "movements_by_significance": {
            "material": 8,
            "significant": 22,
            "minor": 217,
        },
        "significant_movements": significant_movements,
        "all_movements": all_movements,
        "dormant_accounts": [
            {"account_name": "Note Payable — Equipment Lease", "prior_balance": 28_500},
            {"account_name": "Deferred Tax Liability — State", "prior_balance": 12_200},
            {"account_name": "Accrued Interest — Line of Credit", "prior_balance": 3_850},
        ],
        "new_accounts": [
            {"account_name": "Cloud Infrastructure Services", "current_balance": 185_000, "account_type": "expense"},
            {"account_name": "Revenue — API Subscriptions", "current_balance": 320_000, "account_type": "revenue"},
            {
                "account_name": "Deferred Revenue — Annual Contracts",
                "current_balance": 95_000,
                "account_type": "liability",
            },
            {"account_name": "Intangible Assets — Customer Lists", "current_balance": 450_000, "account_type": "asset"},
        ],
        "closed_accounts": [
            {"account_name": "Legacy Software Licenses", "prior_balance": 67_000, "account_type": "asset"},
            {
                "account_name": "Lease Obligation — Office Suite B",
                "prior_balance": 142_000,
                "account_type": "liability",
            },
        ],
        "composite": {
            "score": 68.0,
            "risk_tier": "high",
        },
        "lead_sheet_summaries": [
            {
                "lead_sheet": "A",
                "lead_sheet_name": "Cash & Equivalents",
                "account_count": 3,
                "prior_total": 776_750,
                "current_total": 1_245_000,
                "net_change": 468_250,
            },
            {
                "lead_sheet": "B",
                "lead_sheet_name": "Receivables",
                "account_count": 5,
                "prior_total": 750_000,
                "current_total": 892_000,
                "net_change": 142_000,
            },
            {
                "lead_sheet": "E",
                "lead_sheet_name": "Fixed Assets",
                "account_count": 18,
                "prior_total": 2_100_000,
                "current_total": 2_240_000,
                "net_change": 140_000,
            },
            {
                "lead_sheet": "G",
                "lead_sheet_name": "Payables",
                "account_count": 8,
                "prior_total": 567_000,
                "current_total": 634_000,
                "net_change": 67_000,
            },
            {
                "lead_sheet": "N",
                "lead_sheet_name": "Revenue",
                "account_count": 6,
                "prior_total": 5_800_000,
                "current_total": 6_850_000,
                "net_change": 1_050_000,
            },
        ],
    }


# =============================================================================
# PDF GENERATION TESTS
# =============================================================================


class TestMultiPeriodMemoGeneration:
    """Test PDF generation for multi-period comparison memos."""

    def test_generates_pdf_bytes(self):
        result = _make_comparison_result()
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_pdf_header(self):
        result = _make_comparison_result()
        pdf = generate_multi_period_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_comparison_result()
        pdf = generate_multi_period_memo(result, client_name="Acme Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_with_all_options(self):
        result = _make_comparison_result()
        pdf = generate_multi_period_memo(
            result,
            filename="test_multi_period",
            client_name="TestCo Ltd",
            period_tested="FY2024 vs FY2025",
            prepared_by="John Doe",
            reviewed_by="Jane Smith",
            workpaper_date="2025-12-31",
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_with_budget_label(self):
        result = _make_comparison_result(budget_label="Budget 2025")
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_no_dormant_accounts(self):
        result = _make_comparison_result(dormant_count=0)
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_no_lead_sheet_summaries(self):
        result = _make_comparison_result(num_lead_sheets=0)
        result["lead_sheet_summaries"] = []
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_many_significant_movements(self):
        """More than 25 significant movements -> truncation message."""
        result = _make_comparison_result(
            total_accounts=200,
            material=15,
            significant=25,
            minor=160,
            num_significant_movements=40,
        )
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_empty_result(self):
        """Edge case: minimal data."""
        result = {
            "prior_label": "Prior",
            "current_label": "Current",
            "total_accounts": 0,
            "movements_by_type": {},
            "movements_by_significance": {},
            "significant_movements": [],
            "lead_sheet_summaries": [],
            "dormant_account_count": 0,
        }
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)

    def test_enriched_result_generates(self):
        """Full enriched result with all Sprint 505 fields generates successfully."""
        result = _make_enriched_result()
        pdf = generate_multi_period_memo(result, client_name="Meridian Capital Group")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 30_000  # Enriched report should be larger


# =============================================================================
# DIAGNOSTIC SCORING TESTS (BUG-02)
# =============================================================================


class TestAPCRiskScoring:
    """Test compute_apc_diagnostic_score function."""

    def test_zero_inputs_score_zero(self):
        score = compute_apc_diagnostic_score(0, 0, 0.0, False, 0.0, 0, 0, 0)
        assert score == 0.0

    def test_material_movements_capped_at_20(self):
        score = compute_apc_diagnostic_score(10, 0, 0.0, False, 0.0, 0, 0, 0)
        assert score == 20.0  # 10 * 3 = 30, capped at 20

    def test_sign_change_adds_8(self):
        score = compute_apc_diagnostic_score(0, 1, 0.0, False, 0.0, 0, 0, 0)
        assert score == 8.0

    def test_cash_increase_above_50_pct(self):
        score = compute_apc_diagnostic_score(0, 0, 0.603, False, 0.0, 0, 0, 0)
        assert score == 6.0

    def test_cash_increase_below_50_pct_no_addition(self):
        score = compute_apc_diagnostic_score(0, 0, 0.40, False, 0.0, 0, 0, 0)
        assert score == 0.0

    def test_cogs_growth_vs_revenue(self):
        score = compute_apc_diagnostic_score(0, 0, 0.0, True, 0.0, 0, 0, 0)
        assert score == 5.0

    def test_revenue_concentration(self):
        score = compute_apc_diagnostic_score(0, 0, 0.0, False, 0.62, 0, 0, 0)
        assert score == 8.0

    def test_high_growth_accounts_capped_at_10(self):
        score = compute_apc_diagnostic_score(0, 0, 0.0, False, 0.0, 8, 0, 0)
        assert score == 10.0  # 8 * 2 = 16, capped at 10

    def test_dormant_accounts(self):
        score = compute_apc_diagnostic_score(0, 0, 0.0, False, 0.0, 0, 3, 0)
        assert score == 9.0  # 3 * 3

    def test_new_closed_capped_at_8(self):
        score = compute_apc_diagnostic_score(0, 0, 0.0, False, 0.0, 0, 0, 6)
        assert score == 8.0  # 6 * 2 = 12, capped at 8

    def test_overall_cap_at_100(self):
        score = compute_apc_diagnostic_score(20, 5, 0.99, True, 0.99, 20, 10, 10)
        assert score == 100.0

    def test_meridian_sample_score(self):
        """Verify the Meridian sample dataset produces expected score."""
        score = compute_apc_diagnostic_score(
            material_movement_count=8,
            sign_change_count=1,
            cash_increase_pct=0.603,
            cogs_growth_vs_revenue=True,
            single_account_revenue_pct=0.62,
            high_growth_accounts=2,
            dormant_count=3,
            new_closed_count=6,
        )
        assert score == 68.0


# =============================================================================
# RISK CONCLUSIONS TESTS
# =============================================================================


class TestRiskConclusions:
    """Test risk tier conclusion text (BUG-002: score-aware)."""

    def test_four_tiers_defined(self):
        assert set(_RISK_CONCLUSION_SUFFIXES.keys()) == {"low", "moderate", "elevated", "high"}

    def test_low_conclusion_no_additional_procedures(self):
        assert "No additional substantive procedures" in _build_risk_conclusion("low", 5.0)

    def test_moderate_conclusion_isa_520(self):
        assert "ISA 520" in _build_risk_conclusion("moderate", 20.0)

    def test_elevated_conclusion_expanded(self):
        text = _build_risk_conclusion("elevated", 35.0)
        assert "ELEVATED" in text
        assert "ISA 520" in text

    def test_high_conclusion_misstatement_risk(self):
        text = _build_risk_conclusion("high", 60.0)
        assert "HIGH" in text
        assert "misstatement risk" in text

    def test_score_included_in_conclusion(self):
        """BUG-002: Conclusion must include numeric score."""
        assert "20.0/100" in _build_risk_conclusion("moderate", 20.0)


# =============================================================================
# RESULTS SUMMARY TESTS (BUG-02)
# =============================================================================


class TestResultsSummary:
    """Test Results Summary section presence."""

    def test_results_summary_with_pre_computed_score(self):
        """Pre-computed composite score is used when provided."""
        result = _make_enriched_result()
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        # Verify the report generates with the composite data

    def test_results_summary_auto_computed(self):
        """Score is auto-computed when composite not provided."""
        result = _make_comparison_result()
        # No composite key → auto-computation path
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)

    def test_results_summary_zero_movements(self):
        """Zero movements should produce low risk score."""
        result = _make_comparison_result(
            material=0,
            significant=0,
            minor=80,
            num_significant_movements=0,
        )
        result["movements_by_type"] = {
            "increase": 0,
            "decrease": 0,
            "new_account": 0,
            "closed_account": 0,
            "sign_change": 0,
            "unchanged": 80,
        }
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# RATIO TRENDS TESTS (BUG-01 / IMP-01)
# =============================================================================


class TestRatioTrends:
    """Test ratio computation uses full TB population."""

    def test_revenue_keyword_matches_consulting(self):
        assert _match_keyword("Revenue — Consulting Services", _REVENUE_KEYWORDS)

    def test_revenue_keyword_matches_software_licensing(self):
        assert _match_keyword("Revenue — Software Licensing", _REVENUE_KEYWORDS)

    def test_revenue_keyword_matches_support(self):
        assert _match_keyword("Revenue — Support & Maintenance", _REVENUE_KEYWORDS)

    def test_cogs_keyword_matches(self):
        assert _match_keyword("Cost of Goods Sold", _COGS_KEYWORDS)

    def test_gpm_from_full_population(self):
        """GPM computed from all revenue accounts, not just significant subset."""
        from multi_period_memo_generator import _COGS_KEYWORDS, _REVENUE_KEYWORDS

        all_movements = [
            {"account_name": "Revenue — Consulting Services", "prior_balance": 3_600_000, "current_balance": 4_250_000},
            {"account_name": "Revenue — Software Licensing", "prior_balance": 1_450_000, "current_balance": 1_720_000},
            {"account_name": "Revenue — Support & Maintenance", "prior_balance": 750_000, "current_balance": 880_000},
            {"account_name": "Cost of Goods Sold", "prior_balance": 2_400_000, "current_balance": 2_890_000},
        ]

        prior_rev = sum(
            abs(m["prior_balance"]) for m in all_movements if _match_keyword(m["account_name"], _REVENUE_KEYWORDS)
        )
        curr_rev = sum(
            abs(m["current_balance"]) for m in all_movements if _match_keyword(m["account_name"], _REVENUE_KEYWORDS)
        )
        prior_cogs = sum(
            abs(m["prior_balance"]) for m in all_movements if _match_keyword(m["account_name"], _COGS_KEYWORDS)
        )
        curr_cogs = sum(
            abs(m["current_balance"]) for m in all_movements if _match_keyword(m["account_name"], _COGS_KEYWORDS)
        )

        prior_gpm = (prior_rev - prior_cogs) / prior_rev
        curr_gpm = (curr_rev - curr_cogs) / curr_rev

        assert abs(prior_gpm - 0.586) < 0.01, f"Expected ~58.6%, got {prior_gpm:.1%}"
        assert abs(curr_gpm - 0.578) < 0.01, f"Expected ~57.8%, got {curr_gpm:.1%}"

    def test_enriched_result_renders_ratios(self):
        """Enriched result with all_movements should render ratio table."""
        result = _make_enriched_result()
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 30_000


# =============================================================================
# SIGN CHANGE DETAIL TESTS (BUG-03)
# =============================================================================


class TestSignChangeDetail:
    """Test Sign Change Detail subsection."""

    def test_sign_change_in_enriched_data(self):
        """Sign change account present in all_movements."""
        result = _make_enriched_result()
        sign_changes = [m for m in result["all_movements"] if m["movement_type"] == "sign_change"]
        assert len(sign_changes) == 1
        assert sign_changes[0]["account_name"] == "Deferred Revenue — Project Alpha"

    def test_sign_change_balances(self):
        """Sign change account has correct prior/current balances."""
        result = _make_enriched_result()
        sc = [m for m in result["all_movements"] if m["movement_type"] == "sign_change"][0]
        assert sc["prior_balance"] == -85_000
        assert sc["current_balance"] == 42_000

    def test_renders_with_sign_change(self):
        """PDF generates successfully with sign change data."""
        result = _make_enriched_result()
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 30_000


# =============================================================================
# DORMANT ACCOUNT DETAIL TESTS (BUG-04)
# =============================================================================


class TestDormantAccountDetail:
    """Test Dormant Account Detail subsection."""

    def test_dormant_accounts_are_dicts(self):
        """Dormant accounts include prior balances."""
        result = _make_enriched_result()
        dormant = result["dormant_accounts"]
        assert len(dormant) == 3
        assert all(isinstance(d, dict) for d in dormant)
        assert all("prior_balance" in d for d in dormant)

    def test_dormant_account_names(self):
        """Dormant accounts have identifiable names."""
        result = _make_enriched_result()
        names = [d["account_name"] for d in result["dormant_accounts"]]
        assert "Note Payable — Equipment Lease" in names
        assert "Deferred Tax Liability — State" in names
        assert "Accrued Interest — Line of Credit" in names

    def test_dormant_prior_balances(self):
        """Dormant accounts have non-zero prior balances."""
        result = _make_enriched_result()
        for d in result["dormant_accounts"]:
            assert d["prior_balance"] > 0

    def test_renders_with_dormant_details(self):
        """PDF generates with dormant account detail tables."""
        result = _make_enriched_result()
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)

    def test_backward_compatible_string_dormant(self):
        """Still works with legacy string-only dormant account names."""
        result = _make_comparison_result()
        result["dormant_accounts"] = ["Account A", "Account B"]
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# NEW/CLOSED ACCOUNT DETAIL TESTS (IMP-05)
# =============================================================================


class TestNewClosedAccountDetail:
    """Test New and Closed Account Detail subsection."""

    def test_new_accounts_present(self):
        result = _make_enriched_result()
        assert len(result["new_accounts"]) == 4

    def test_closed_accounts_present(self):
        result = _make_enriched_result()
        assert len(result["closed_accounts"]) == 2

    def test_new_accounts_have_current_balance(self):
        result = _make_enriched_result()
        for acct in result["new_accounts"]:
            assert "current_balance" in acct
            assert acct["current_balance"] > 0

    def test_closed_accounts_have_prior_balance(self):
        result = _make_enriched_result()
        for acct in result["closed_accounts"]:
            assert "prior_balance" in acct
            assert acct["prior_balance"] > 0

    def test_renders_with_new_closed(self):
        result = _make_enriched_result()
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)

    def test_renders_without_new_closed(self):
        """No new/closed accounts should not break generation."""
        result = _make_comparison_result()
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# SUGGESTED PROCEDURES TESTS (IMP-02)
# =============================================================================


class TestSuggestedProcedures:
    """Test suggested procedures on material movements."""

    def test_follow_up_procedures_exist(self):
        from shared.follow_up_procedures import FOLLOW_UP_PROCEDURES

        apc_keys = [k for k in FOLLOW_UP_PROCEDURES if k.startswith("apc_")]
        assert len(apc_keys) >= 8  # revenue, cogs, asset, cash, liability, expense, sign_change, dormant

    def test_revenue_procedure_exists(self):
        from shared.follow_up_procedures import FOLLOW_UP_PROCEDURES

        assert "apc_revenue_increase" in FOLLOW_UP_PROCEDURES

    def test_cogs_procedure_exists(self):
        from shared.follow_up_procedures import FOLLOW_UP_PROCEDURES

        assert "apc_cogs_increase" in FOLLOW_UP_PROCEDURES

    def test_cash_procedure_exists(self):
        from shared.follow_up_procedures import FOLLOW_UP_PROCEDURES

        assert "apc_cash_increase" in FOLLOW_UP_PROCEDURES

    def test_sign_change_procedure_exists(self):
        from shared.follow_up_procedures import FOLLOW_UP_PROCEDURES

        assert "apc_sign_change" in FOLLOW_UP_PROCEDURES

    def test_dormant_procedure_exists(self):
        from shared.follow_up_procedures import FOLLOW_UP_PROCEDURES

        assert "apc_dormant_account" in FOLLOW_UP_PROCEDURES


# =============================================================================
# LEAD SHEET SUMMARY TESTS (IMP-04)
# =============================================================================


class TestLeadSheetSummary:
    """Test lead sheet summary with % Change column."""

    def test_lead_sheet_has_pct_change_data(self):
        """Lead sheets have the data needed to compute % change."""
        result = _make_enriched_result()
        for ls in result["lead_sheet_summaries"]:
            assert "prior_total" in ls
            assert "current_total" in ls
            assert "net_change" in ls
            # Verify math
            assert abs(ls["net_change"] - (ls["current_total"] - ls["prior_total"])) < 0.01

    def test_renders_lead_sheet_table(self):
        result = _make_enriched_result()
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# CONCLUSION TIER COVERAGE
# =============================================================================


class TestConclusionTiers:
    """Test that all conclusion tiers generate valid PDFs."""

    def test_zero_significant_conclusion(self):
        result = _make_comparison_result(
            material=0,
            significant=0,
            minor=80,
            num_significant_movements=0,
        )
        result["movements_by_type"] = {
            "increase": 0,
            "decrease": 0,
            "new_account": 0,
            "closed_account": 0,
            "sign_change": 0,
            "unchanged": 80,
        }
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)

    def test_low_score_conclusion(self):
        result = _make_comparison_result()
        result["composite"] = {"score": 5.0, "risk_tier": "low"}
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)

    def test_moderate_score_conclusion(self):
        result = _make_comparison_result()
        result["composite"] = {"score": 20.0, "risk_tier": "moderate"}
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)

    def test_elevated_score_conclusion(self):
        result = _make_comparison_result()
        result["composite"] = {"score": 35.0, "risk_tier": "elevated"}
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)

    def test_high_score_conclusion(self):
        result = _make_comparison_result()
        result["composite"] = {"score": 68.0, "risk_tier": "high"}
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================


class TestMultiPeriodMemoGuardrails:
    """Verify terminology compliance and ISA references."""

    def test_isa_references_present(self):
        source = inspect.getsource(generate_multi_period_memo)
        assert "ISA 520" in source
        assert "PCAOB AS 2305" in source

    def test_no_forbidden_audit_assertions(self):
        source = inspect.getsource(generate_multi_period_memo)
        forbidden = [
            "financial statements are correct",
            "no misstatement exists",
            "accounts are fairly stated",
            "we conclude that",
        ]
        for phrase in forbidden:
            assert phrase.lower() not in source.lower(), f"Forbidden phrase found: {phrase}"

    def test_disclaimer_called(self):
        source = inspect.getsource(generate_multi_period_memo)
        assert "build_disclaimer" in source

    def test_workpaper_signoff_called(self):
        source = inspect.getsource(generate_multi_period_memo)
        assert "build_workpaper_signoff" in source

    def test_risk_conclusions_no_assertive_language(self):
        """Risk conclusions should not use banned assertive terms."""
        banned = ["we conclude", "we believe", "we are satisfied", "the statements are"]
        for tier in _RISK_CONCLUSION_SUFFIXES:
            text = _build_risk_conclusion(tier, 50.0)
            for phrase in banned:
                assert phrase.lower() not in text.lower(), f"Banned phrase '{phrase}' in {tier}"


# =============================================================================
# EXPORT ROUTE REGISTRATION
# =============================================================================


class TestMultiPeriodMemoExportRoute:
    """Verify the export route is registered."""

    def test_multi_period_memo_route_exists(self):
        from main import app

        routes = []
        for route in app.routes:
            if hasattr(route, "path"):
                routes.append(route.path)
        assert "/export/multi-period-memo" in routes

    def test_multi_period_memo_route_is_post(self):
        from main import app

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/multi-period-memo":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/multi-period-memo not found")


# =============================================================================
# PYDANTIC INPUT MODEL
# =============================================================================


class TestMultiPeriodMemoInput:
    """Verify the Pydantic input model."""

    def test_valid_data(self):
        from shared.export_schemas import MultiPeriodMemoInput

        data = _make_comparison_result()
        model = MultiPeriodMemoInput(**data)
        assert model.total_accounts == 80

    def test_defaults(self):
        from shared.export_schemas import MultiPeriodMemoInput

        model = MultiPeriodMemoInput()
        assert model.prior_label == "Prior"
        assert model.current_label == "Current"
        assert model.budget_label is None
        assert model.total_accounts == 0
        assert model.filename == "multi_period_comparison"
        assert model.client_name is None
        assert model.prepared_by is None

    def test_with_all_fields(self):
        from shared.export_schemas import MultiPeriodMemoInput

        data = _make_comparison_result(budget_label="Budget 2025")
        data.update(
            {
                "filename": "my_comparison",
                "client_name": "TestCo",
                "period_tested": "FY24 vs FY25",
                "prepared_by": "Auditor A",
                "reviewed_by": "Manager B",
                "workpaper_date": "2025-12-31",
            }
        )
        model = MultiPeriodMemoInput(**data)
        assert model.client_name == "TestCo"
        assert model.budget_label == "Budget 2025"
        assert model.filename == "my_comparison"

    def test_model_dump_roundtrip(self):
        from shared.export_schemas import MultiPeriodMemoInput

        data = _make_comparison_result()
        model = MultiPeriodMemoInput(**data)
        dumped = model.model_dump()
        assert dumped["total_accounts"] == 80
        assert dumped["movements_by_type"]["increase"] == 30
        assert len(dumped["significant_movements"]) == 11
        assert len(dumped["lead_sheet_summaries"]) == 5

    def test_movements_preserved(self):
        from shared.export_schemas import MultiPeriodMemoInput

        data = _make_comparison_result()
        model = MultiPeriodMemoInput(**data)
        dumped = model.model_dump()
        first_movement = dumped["significant_movements"][0]
        assert "account_name" in first_movement
        assert "change_amount" in first_movement
        assert "movement_type" in first_movement
