"""
Tests for Expense Category Analytical Procedures Memo Generator — Sprint 512
"""

from expense_category_memo import (
    _assign_risk,
    _benchmark_flag,
    _generate_procedures,
    _generate_variance_commentary,
    _pct_change,
    _pct_change_str,
    generate_expense_category_memo,
)

# ═══════════════════════════════════════════════════════════════
# Helper data
# ═══════════════════════════════════════════════════════════════

SAMPLE_CATEGORIES = [
    {
        "label": "Cost of Goods Sold",
        "amount": 2_890_000.00,
        "pct_of_revenue": 42.19,
        "prior_amount": 2_400_000.00,
        "prior_pct_of_revenue": 38.71,
        "dollar_change": 490_000.00,
        "exceeds_threshold": True,
    },
    {
        "label": "Payroll & Benefits",
        "amount": 1_420_000.00,
        "pct_of_revenue": 20.73,
        "prior_amount": 1_180_000.00,
        "prior_pct_of_revenue": 19.03,
        "dollar_change": 240_000.00,
        "exceeds_threshold": True,
    },
    {
        "label": "Depreciation & Amortization",
        "amount": 285_000.00,
        "pct_of_revenue": 4.16,
        "prior_amount": 260_000.00,
        "prior_pct_of_revenue": 4.19,
        "dollar_change": 25_000.00,
        "exceeds_threshold": False,
    },
    {
        "label": "Interest & Tax",
        "amount": 437_750.00,
        "pct_of_revenue": 6.39,
        "prior_amount": 398_000.00,
        "prior_pct_of_revenue": 6.42,
        "dollar_change": 39_750.00,
        "exceeds_threshold": False,
    },
    {
        "label": "Other Operating Expenses",
        "amount": 795_000.00,
        "pct_of_revenue": 11.61,
        "prior_amount": 642_000.00,
        "prior_pct_of_revenue": 10.35,
        "dollar_change": 153_000.00,
        "exceeds_threshold": True,
    },
]

SAMPLE_REPORT = {
    "categories": SAMPLE_CATEGORIES,
    "total_expenses": 5_827_750.00,
    "total_revenue": 6_850_000.00,
    "revenue_available": True,
    "prior_available": True,
    "materiality_threshold": 50_000.00,
    "category_count": 5,
    "prior_revenue": 6_200_000.00,
    "prior_total_expenses": 4_880_000.00,
}


# ═══════════════════════════════════════════════════════════════
# Test _pct_change
# ═══════════════════════════════════════════════════════════════


class TestPctChange:
    def test_positive_change(self):
        assert abs(_pct_change(120, 100) - 20.0) < 0.01

    def test_negative_change(self):
        assert abs(_pct_change(80, 100) - (-20.0)) < 0.01

    def test_zero_prior(self):
        assert _pct_change(100, 0) is None

    def test_near_zero_prior(self):
        assert _pct_change(100, 1e-11) is None

    def test_no_change(self):
        assert abs(_pct_change(100, 100)) < 0.01


# ═══════════════════════════════════════════════════════════════
# Test _pct_change_str
# ═══════════════════════════════════════════════════════════════


class TestPctChangeStr:
    def test_positive(self):
        result = _pct_change_str(20.4)
        assert "20.4%" in result
        assert "\u2191" in result  # up arrow

    def test_negative(self):
        result = _pct_change_str(-15.3)
        assert "15.3%" in result
        assert "\u2193" in result  # down arrow

    def test_zero(self):
        result = _pct_change_str(0.0)
        assert "0.0%" in result
        assert "\u2013" in result  # en-dash

    def test_none(self):
        assert _pct_change_str(None) == "N/A"


# ═══════════════════════════════════════════════════════════════
# Test _assign_risk
# ═══════════════════════════════════════════════════════════════


class TestAssignRisk:
    def test_high_risk(self):
        """>=20% and exceeds materiality → high (RISK_TIER_DISPLAY key)."""
        assert _assign_risk(25.0, True) == "high"
        assert _assign_risk(-20.0, True) == "high"

    def test_moderate_pct_only(self):
        """>=10% but not exceeds materiality → moderate."""
        assert _assign_risk(15.0, False) == "moderate"

    def test_moderate_materiality_only(self):
        """<10% but exceeds materiality → moderate."""
        assert _assign_risk(5.0, True) == "moderate"

    def test_low_risk(self):
        """<10% and not exceeds materiality → low."""
        assert _assign_risk(5.0, False) == "low"

    def test_none_pct(self):
        """None pct_change → low."""
        assert _assign_risk(None, True) == "low"


# ═══════════════════════════════════════════════════════════════
# Test _benchmark_flag
# ═══════════════════════════════════════════════════════════════


class TestBenchmarkFlag:
    def test_within_range(self):
        assert _benchmark_flag("COGS Ratio", 40.0) == "Within Range"

    def test_below_range(self):
        assert _benchmark_flag("COGS Ratio", 25.0) == "Below Range"

    def test_above_range(self):
        assert _benchmark_flag("COGS Ratio", 60.0) == "Above Range"

    def test_unknown_ratio(self):
        assert _benchmark_flag("Unknown Ratio", 50.0) == "N/A"

    def test_payroll_within(self):
        assert _benchmark_flag("Payroll Ratio", 20.0) == "Within Range"

    def test_other_operating_above(self):
        assert _benchmark_flag("Other Operating Ratio", 15.0) == "Above Range"


# ═══════════════════════════════════════════════════════════════
# Test _generate_variance_commentary
# ═══════════════════════════════════════════════════════════════


class TestGenerateVarianceCommentary:
    def test_cogs_commentary(self):
        result = _generate_variance_commentary("Cost of Goods Sold", 20.4, 490_000, 42.19, 6_850_000)
        assert "20.4%" in result
        assert "$490,000" in result
        assert "Gross margin" in result

    def test_payroll_commentary(self):
        result = _generate_variance_commentary("Payroll & Benefits", 20.3, 240_000, 20.73, 6_850_000)
        assert "headcount" in result

    def test_depreciation_commentary(self):
        result = _generate_variance_commentary("Depreciation & Amortization", 9.6, 25_000, 4.16, 6_850_000)
        assert "capital expenditure" in result

    def test_interest_tax_commentary(self):
        result = _generate_variance_commentary("Interest & Tax", 10.0, 39_750, 6.39, 6_850_000)
        assert "debt" in result or "tax" in result

    def test_other_operating_commentary(self):
        result = _generate_variance_commentary("Other Operating Expenses", 23.8, 153_000, 11.61, 6_850_000)
        assert "sub-ledger" in result

    def test_decrease_direction(self):
        result = _generate_variance_commentary("Cost of Goods Sold", -10.0, -100_000, 40.0, 5_000_000)
        assert "decreased" in result


# ═══════════════════════════════════════════════════════════════
# Test _generate_procedures
# ═══════════════════════════════════════════════════════════════


class TestGenerateProcedures:
    def test_cogs_procedure(self):
        findings = [{"category": "Cost of Goods Sold", "risk": "high"}]
        cats = [{"label": "Cost of Goods Sold", "dollar_change": 490_000, "_pct_change": 20.4, "pct_of_revenue": 42.19}]
        procs = _generate_procedures(findings, cats)
        assert len(procs) >= 1
        cogs_proc = next(p for p in procs if p["area"] == "COGS Variance")
        assert "vendor invoices" in cogs_proc["procedure"]
        assert cogs_proc["priority"] == "high"

    def test_payroll_procedure(self):
        findings = [{"category": "Payroll & Benefits", "risk": "moderate"}]
        cats = [{"label": "Payroll & Benefits", "dollar_change": 240_000, "_pct_change": 20.3, "pct_of_revenue": 20.73}]
        procs = _generate_procedures(findings, cats)
        payroll_proc = next(p for p in procs if p["area"] == "Payroll Variance")
        assert "Report 05" in payroll_proc["procedure"]

    def test_other_operating_procedure(self):
        findings = [{"category": "Other Operating Expenses", "risk": "moderate"}]
        cats = [
            {
                "label": "Other Operating Expenses",
                "dollar_change": 153_000,
                "_pct_change": 23.8,
                "pct_of_revenue": 11.61,
            }
        ]
        procs = _generate_procedures(findings, cats)
        other_proc = next(p for p in procs if p["area"] == "Other Operating Expenses")
        assert "sub-ledger" in other_proc["procedure"]

    def test_benchmark_procedure_added(self):
        """Benchmark above-range should generate a procedure."""
        findings = []
        cats = [{"label": "Other Operating Expenses", "pct_of_revenue": 15.0, "dollar_change": 0, "_pct_change": 0}]
        procs = _generate_procedures(findings, cats)
        assert any("benchmark" in p["area"].lower() for p in procs)

    def test_priority_sorting(self):
        """Procedures should be sorted high → moderate."""
        findings = [
            {"category": "Payroll & Benefits", "risk": "moderate"},
            {"category": "Cost of Goods Sold", "risk": "high"},
        ]
        cats = [
            {"label": "Cost of Goods Sold", "dollar_change": 490_000, "_pct_change": 20.4, "pct_of_revenue": 42.19},
            {"label": "Payroll & Benefits", "dollar_change": 240_000, "_pct_change": 20.3, "pct_of_revenue": 20.73},
        ]
        procs = _generate_procedures(findings, cats)
        assert procs[0]["priority"] == "high"

    def test_empty_findings(self):
        """No findings, no benchmark issues → no procedures."""
        procs = _generate_procedures([], [{"label": "Cost of Goods Sold", "pct_of_revenue": 40.0}])
        assert len(procs) == 0


# ═══════════════════════════════════════════════════════════════
# Test PDF Generation
# ═══════════════════════════════════════════════════════════════


class TestPDFGeneration:
    def test_generates_pdf_bytes(self):
        """Should return non-empty bytes."""
        result = generate_expense_category_memo(SAMPLE_REPORT, "test.csv")
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_pdf_with_client_name(self):
        result = generate_expense_category_memo(SAMPLE_REPORT, "test.csv", client_name="Test Corp")
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_pdf_without_prior(self):
        """Report without prior data should still generate."""
        report = {
            "categories": [
                {"label": "Cost of Goods Sold", "amount": 500, "pct_of_revenue": 50.0},
            ],
            "total_expenses": 500,
            "total_revenue": 1000,
            "revenue_available": True,
            "prior_available": False,
            "materiality_threshold": 100,
            "category_count": 1,
        }
        result = generate_expense_category_memo(report, "test.csv")
        assert isinstance(result, bytes)
        assert len(result) > 500

    def test_pdf_without_revenue(self):
        """Report without revenue should still generate."""
        report = {
            "categories": [
                {"label": "Cost of Goods Sold", "amount": 500, "pct_of_revenue": None},
            ],
            "total_expenses": 500,
            "total_revenue": 0,
            "revenue_available": False,
            "prior_available": False,
            "materiality_threshold": 100,
            "category_count": 1,
        }
        result = generate_expense_category_memo(report, "test.csv")
        assert isinstance(result, bytes)

    def test_full_report_larger_than_basic(self):
        """Full report with prior data should be significantly larger than without."""
        full = generate_expense_category_memo(SAMPLE_REPORT, "test.csv")
        basic_report = {
            "categories": [
                {"label": "Cost of Goods Sold", "amount": 500, "pct_of_revenue": 50.0},
            ],
            "total_expenses": 500,
            "total_revenue": 1000,
            "revenue_available": True,
            "prior_available": False,
            "materiality_threshold": 100,
            "category_count": 1,
        }
        basic = generate_expense_category_memo(basic_report, "test.csv")
        assert len(full) > len(basic)

    def test_signoff_parameter(self):
        result = generate_expense_category_memo(
            SAMPLE_REPORT,
            "test.csv",
            prepared_by="Analyst",
            reviewed_by="Manager",
            workpaper_date="2026-03-07",
            include_signoff=True,
        )
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_empty_categories(self):
        """Empty categories should produce a valid PDF."""
        report = {
            "categories": [],
            "total_expenses": 0,
            "total_revenue": 0,
            "revenue_available": False,
            "prior_available": False,
            "materiality_threshold": 0,
            "category_count": 0,
        }
        result = generate_expense_category_memo(report, "test.csv")
        assert isinstance(result, bytes)


# ═══════════════════════════════════════════════════════════════
# Test Scope Statement (doubled word fix)
# ═══════════════════════════════════════════════════════════════


class TestScopeStatement:
    def test_no_doubled_procedures(self):
        """Scope statement should not contain 'procedures procedures'."""
        from shared.framework_resolution import ResolvedFramework
        from shared.scope_methodology import get_tool_content

        content = get_tool_content("expense_category", ResolvedFramework.FASB, "expense category analytical")
        assert "procedures procedures" not in content.scope_statement.lower()
        assert "expense category analytical procedures" in content.scope_statement.lower()


# ═══════════════════════════════════════════════════════════════
# Test Authoritative References
# ═══════════════════════════════════════════════════════════════


class TestAuthoritativeReferences:
    def test_fasb_references(self):
        """FASB should include AU-C 520, AS 2305, ASC 220-10, ASC 720-10."""
        from shared.framework_resolution import ResolvedFramework
        from shared.scope_methodology import get_tool_content

        content = get_tool_content("expense_category", ResolvedFramework.FASB)
        ref_ids = [r.reference for r in content.references]
        assert "AU-C § 520" in ref_ids
        assert "AS 2305" in ref_ids
        assert "ASC 220-10" in ref_ids
        assert "ASC 720-10" in ref_ids

    def test_no_asc_250_10(self):
        """ASC 250-10 should NOT be present."""
        from shared.framework_resolution import ResolvedFramework
        from shared.scope_methodology import get_tool_content

        content = get_tool_content("expense_category", ResolvedFramework.FASB)
        ref_ids = [r.reference for r in content.references]
        assert "ASC 250-10" not in ref_ids

    def test_aicpa_pcaob_bodies(self):
        """AICPA and PCAOB body overrides should be correct."""
        from shared.framework_resolution import ResolvedFramework
        from shared.scope_methodology import get_tool_content

        content = get_tool_content("expense_category", ResolvedFramework.FASB)
        auc_ref = next(r for r in content.references if r.reference == "AU-C § 520")
        assert auc_ref.body == "AICPA"
        as_ref = next(r for r in content.references if r.reference == "AS 2305")
        assert as_ref.body == "PCAOB"

    def test_gasb_references(self):
        """GASB should include AU-C 520, AS 2305, and a GASB statement."""
        from shared.framework_resolution import ResolvedFramework
        from shared.scope_methodology import get_tool_content

        content = get_tool_content("expense_category", ResolvedFramework.GASB)
        ref_ids = [r.reference for r in content.references]
        assert "AU-C § 520" in ref_ids
        assert "AS 2305" in ref_ids
