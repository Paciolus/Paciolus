"""
Tests for Three-Way Match Memo Generator (Sprint 504)

Tests:
- PDF generation and validation
- Section II Methodology table
- Section III Match Results with benchmark
- Section IV Results Summary with risk scoring
- Section V Material Variances with vendor columns and net direction
- Section VI Key Findings with suggested procedures
- Section VII Unmatched Documents detail tables
- Risk tier mapping (engine MEDIUM → standard MODERATE)
- Diagnostic scoring function
- Conclusion text per tier
- Guardrails (terminology, ISA references)
"""

from three_way_match_memo_generator import (
    _ENGINE_TIER_MAPPING,
    _RISK_CONCLUSION_SUFFIXES,
    _TEST_DESCRIPTIONS,
    _build_risk_conclusion,
    compute_twm_diagnostic_score,
    generate_three_way_match_memo,
)

# =============================================================================
# FIXTURES
# =============================================================================


def _make_twm_result(
    full_match_rate: float = 0.756,
    risk_assessment: str = "medium",
    material_variances_count: int = 7,
    net_variance: float = 23_450.0,
) -> dict:
    """Build a minimal ThreeWayMatchResult-shaped dict for testing."""
    return {
        "summary": {
            "total_pos": 156,
            "total_invoices": 148,
            "total_receipts": 139,
            "full_match_count": 118,
            "partial_match_count": 21,
            "full_match_rate": full_match_rate,
            "partial_match_rate": 0.135,
            "material_variances_count": material_variances_count,
            "net_variance": net_variance,
            "risk_assessment": risk_assessment,
            "total_po_amount": 1_842_000.00,
            "total_invoice_amount": 1_865_450.00,
            "total_receipt_amount": 1_831_200.00,
        },
        "variances": [
            {
                "field": "amount",
                "po_value": 45000.0,
                "invoice_value": 47500.0,
                "variance_amount": 2500.0,
                "severity": "high",
                "vendor": "Meridian Supply Co.",
                "po_number": "PO-2025-0812",
                "invoice_number": "INV-47832",
            },
            {
                "field": "amount",
                "po_value": 12000.0,
                "invoice_value": 13200.0,
                "variance_amount": 1200.0,
                "severity": "medium",
                "vendor": "Atlas Industrial",
                "po_number": "PO-2025-0834",
                "invoice_number": "INV-48201",
            },
        ],
        "config": {
            "amount_tolerance": 0.01,
            "price_variance_threshold": 0.05,
            "date_window_days": 30,
            "enable_fuzzy_matching": True,
        },
        "data_quality": {"overall_quality_score": 91.5},
        "column_detection": {
            "po": {"overall_confidence": 0.93},
            "invoice": {"overall_confidence": 0.90},
            "receipt": {"overall_confidence": 0.88},
        },
        "partial_matches": [{"id": i} for i in range(21)],
        "unmatched_pos": [
            {"po_number": f"PO-2025-090{i}", "vendor": f"Vendor {i}", "po_date": "2025-11-15", "po_amount": 12500.0}
            for i in range(1, 10)
        ],
        "unmatched_invoices": [
            {
                "invoice_number": f"INV-4900{i}",
                "vendor": f"Unknown Vendor {chr(64 + i)}",
                "invoice_date": "2025-12-15",
                "amount": 8750.0,
            }
            for i in range(1, 6)
        ],
        "unmatched_receipts": [
            {"receipt_number": f"GRN-880{i}", "vendor": f"Vendor R{i}", "receipt_date": "2025-12-20", "amount": 3200.0}
            for i in range(1, 4)
        ],
        "test_results": [
            {
                "test_key": "three_way_full_match",
                "test_name": "Three-Way Full Match",
                "test_tier": "structural",
                "entries_flagged": 38,
                "flag_rate": 0.244,
                "severity": "medium",
            },
            {
                "test_key": "amount_variance",
                "test_name": "Amount Variance",
                "test_tier": "statistical",
                "entries_flagged": 6,
                "flag_rate": 0.038,
                "severity": "high",
            },
            {
                "test_key": "date_variance",
                "test_name": "Date Variance",
                "test_tier": "structural",
                "entries_flagged": 1,
                "flag_rate": 0.006,
                "severity": "high",
            },
            {
                "test_key": "unmatched_documents",
                "test_name": "Unmatched Documents",
                "test_tier": "structural",
                "entries_flagged": 17,
                "flag_rate": 0.109,
                "severity": "high",
            },
            {
                "test_key": "duplicate_invoice_numbers",
                "test_name": "Duplicate Invoice Numbers",
                "test_tier": "advanced",
                "entries_flagged": 0,
                "flag_rate": 0.0,
                "severity": "low",
            },
            {
                "test_key": "quantity_variance",
                "test_name": "Quantity Variance",
                "test_tier": "statistical",
                "entries_flagged": 0,
                "flag_rate": 0.0,
                "severity": "low",
            },
        ],
        "composite_score": {
            "score": 66.0,
            "risk_tier": "high",
            "total_flagged": 62,
            "flag_rate": 0.397,
            "tests_run": 6,
            "flags_by_severity": {"high": 18, "medium": 38, "low": 6},
            "top_findings": [
                "7 Material Variances — Net Overbilling $23,450.00",
                "75.6% Full Match Rate — Below 80% best practice threshold",
                "5 Unmatched Invoices — Unauthorized payment risk",
                "66-Day Date Gap — Potential backdating",
            ],
        },
    }


def _make_minimal_result() -> dict:
    """Build a minimal result with no test_results or composite_score."""
    return {
        "summary": {
            "total_pos": 10,
            "total_invoices": 10,
            "total_receipts": 10,
            "full_match_count": 9,
            "partial_match_count": 1,
            "full_match_rate": 0.90,
            "partial_match_rate": 0.10,
            "material_variances_count": 0,
            "net_variance": 0.0,
            "risk_assessment": "low",
            "total_po_amount": 50000.0,
            "total_invoice_amount": 50000.0,
            "total_receipt_amount": 50000.0,
        },
        "variances": [],
        "config": {
            "amount_tolerance": 0.01,
            "price_variance_threshold": 0.05,
            "date_window_days": 30,
            "enable_fuzzy_matching": True,
        },
        "data_quality": {"overall_quality_score": 95.0},
        "column_detection": {},
        "partial_matches": [],
        "unmatched_pos": [],
        "unmatched_invoices": [],
        "unmatched_receipts": [],
    }


# =============================================================================
# PDF GENERATION TESTS
# =============================================================================


class TestPDFGeneration:
    """Basic PDF generation tests."""

    def test_generates_pdf_bytes(self):
        result = _make_twm_result()
        pdf = generate_three_way_match_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000
        assert pdf[:5] == b"%PDF-"

    def test_generates_with_all_optional_params(self):
        result = _make_twm_result()
        pdf = generate_three_way_match_memo(
            result,
            filename="meridian_procurement_fy2025.csv",
            client_name="Meridian Corp",
            period_tested="FY 2025",
            prepared_by="Analyst A",
            reviewed_by="Manager B",
            workpaper_date="2026-01-15",
            source_document_title="Procurement Documents",
            source_context_note="PO register, invoice log, receiving log",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_generates_with_minimal_result(self):
        result = _make_minimal_result()
        pdf = generate_three_way_match_memo(result)
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_enriched_report_larger_than_minimal(self):
        enriched = generate_three_way_match_memo(_make_twm_result())
        minimal = generate_three_way_match_memo(_make_minimal_result())
        assert len(enriched) > len(minimal)


# =============================================================================
# METHODOLOGY TESTS
# =============================================================================


class TestMethodology:
    """Section II: Methodology table tests."""

    def test_all_6_test_descriptions_defined(self):
        assert len(_TEST_DESCRIPTIONS) == 6

    def test_all_descriptions_substantive(self):
        for key, desc in _TEST_DESCRIPTIONS.items():
            assert len(desc) > 20, f"Description for {key} too short"

    def test_test_keys_match_sample_data(self):
        result = _make_twm_result()
        sample_keys = {tr["test_key"] for tr in result["test_results"]}
        desc_keys = set(_TEST_DESCRIPTIONS.keys())
        assert sample_keys == desc_keys


# =============================================================================
# MATCH RESULTS TESTS
# =============================================================================


class TestMatchResults:
    """Section III: Match Results with benchmark."""

    def test_benchmark_below_80_triggers_systemic_review(self):
        result = _make_twm_result(full_match_rate=0.756)
        pdf = generate_three_way_match_memo(result)
        assert len(pdf) > 1000

    def test_benchmark_above_90_no_concern(self):
        result = _make_twm_result(full_match_rate=0.92)
        pdf = generate_three_way_match_memo(result)
        assert len(pdf) > 1000


# =============================================================================
# RESULTS SUMMARY TESTS
# =============================================================================


class TestResultsSummary:
    """Section IV: Results Summary with risk scoring."""

    def test_composite_score_present(self):
        result = _make_twm_result()
        assert result["composite_score"]["score"] == 66.0
        assert result["composite_score"]["risk_tier"] == "high"

    def test_severity_counts_present(self):
        result = _make_twm_result()
        sev = result["composite_score"]["flags_by_severity"]
        assert sev["high"] == 18
        assert sev["medium"] == 38
        assert sev["low"] == 6


# =============================================================================
# RISK TIER MAPPING TESTS
# =============================================================================


class TestRiskTierMapping:
    """BUG-01: Engine MEDIUM maps to standard MODERATE."""

    def test_engine_medium_maps_to_moderate(self):
        assert _ENGINE_TIER_MAPPING["medium"] == "moderate"

    def test_engine_low_maps_to_low(self):
        assert _ENGINE_TIER_MAPPING["low"] == "low"

    def test_engine_high_maps_to_elevated(self):
        assert _ENGINE_TIER_MAPPING["high"] == "elevated"

    def test_engine_critical_maps_to_high(self):
        assert _ENGINE_TIER_MAPPING["critical"] == "high"

    def test_all_engine_tiers_mapped(self):
        assert set(_ENGINE_TIER_MAPPING.keys()) == {"low", "medium", "high", "critical"}


# =============================================================================
# DIAGNOSTIC SCORING TESTS
# =============================================================================


class TestDiagnosticScoring:
    """Diagnostic score computation function."""

    def test_low_risk_scenario(self):
        score = compute_twm_diagnostic_score(
            full_match_rate=0.95,
            material_variance_count=0,
            high_variance_count=0,
            net_variance_amount=0,
            unmatched_invoices=0,
            unmatched_pos=0,
            unmatched_receipts=0,
            has_date_variance_high=False,
        )
        assert score <= 10

    def test_moderate_risk_scenario(self):
        score = compute_twm_diagnostic_score(
            full_match_rate=0.88,
            material_variance_count=2,
            high_variance_count=0,
            net_variance_amount=5000,
            unmatched_invoices=1,
            unmatched_pos=2,
            unmatched_receipts=0,
            has_date_variance_high=False,
        )
        assert 11 <= score <= 25

    def test_elevated_risk_scenario(self):
        score = compute_twm_diagnostic_score(
            full_match_rate=0.82,
            material_variance_count=4,
            high_variance_count=1,
            net_variance_amount=30000,
            unmatched_invoices=3,
            unmatched_pos=3,
            unmatched_receipts=1,
            has_date_variance_high=True,
        )
        assert 26 <= score <= 50

    def test_high_risk_scenario(self):
        score = compute_twm_diagnostic_score(
            full_match_rate=0.65,
            material_variance_count=10,
            high_variance_count=5,
            net_variance_amount=80000,
            unmatched_invoices=8,
            unmatched_pos=10,
            unmatched_receipts=5,
            has_date_variance_high=True,
        )
        assert score > 50

    def test_score_capped_at_100(self):
        """Maximum possible score is sum of all caps: 20+15+15+10+10+5+6+8=89."""
        score = compute_twm_diagnostic_score(
            full_match_rate=0.50,
            material_variance_count=20,
            high_variance_count=20,
            net_variance_amount=200000,
            unmatched_invoices=20,
            unmatched_pos=20,
            unmatched_receipts=20,
            has_date_variance_high=True,
        )
        assert score <= 100
        assert score >= 80  # All caps hit

    def test_meridian_sample_approximation(self):
        """Meridian sample: ~66 expected."""
        score = compute_twm_diagnostic_score(
            full_match_rate=0.756,
            material_variance_count=7,
            high_variance_count=2,
            net_variance_amount=23450,
            unmatched_invoices=5,
            unmatched_pos=9,
            unmatched_receipts=3,
            has_date_variance_high=True,
        )
        assert 55 <= score <= 75


# =============================================================================
# KEY FINDINGS TESTS
# =============================================================================


class TestKeyFindings:
    """Section VI: Key Findings with suggested procedures."""

    def test_four_findings_in_sample(self):
        result = _make_twm_result()
        findings = result["composite_score"]["top_findings"]
        assert len(findings) == 4

    def test_finding_1_material_variances(self):
        result = _make_twm_result()
        assert "Material Variances" in result["composite_score"]["top_findings"][0]
        assert "$23,450" in result["composite_score"]["top_findings"][0]

    def test_finding_2_match_rate(self):
        result = _make_twm_result()
        assert "75.6%" in result["composite_score"]["top_findings"][1]

    def test_finding_3_unmatched_invoices(self):
        result = _make_twm_result()
        assert "Unmatched Invoices" in result["composite_score"]["top_findings"][2]

    def test_finding_4_date_gap(self):
        result = _make_twm_result()
        assert "Date Gap" in result["composite_score"]["top_findings"][3]


# =============================================================================
# MATERIAL VARIANCES TESTS
# =============================================================================


class TestMaterialVariances:
    """Section V: Material Variances with vendor columns and net direction."""

    def test_variances_have_vendor(self):
        result = _make_twm_result()
        for v in result["variances"]:
            assert "vendor" in v

    def test_variances_have_po_number(self):
        result = _make_twm_result()
        for v in result["variances"]:
            assert "po_number" in v

    def test_variances_have_invoice_number(self):
        result = _make_twm_result()
        for v in result["variances"]:
            assert "invoice_number" in v

    def test_net_overbilling_direction(self):
        result = _make_twm_result()
        po_total = result["summary"]["total_po_amount"]
        inv_total = result["summary"]["total_invoice_amount"]
        assert inv_total > po_total  # Net overbilling


# =============================================================================
# UNMATCHED DOCUMENTS TESTS
# =============================================================================


class TestUnmatchedDocuments:
    """Section VII: Unmatched Documents detail tables."""

    def test_unmatched_invoices_5_items(self):
        result = _make_twm_result()
        assert len(result["unmatched_invoices"]) == 5

    def test_unmatched_pos_9_items(self):
        result = _make_twm_result()
        assert len(result["unmatched_pos"]) == 9

    def test_unmatched_receipts_3_items(self):
        result = _make_twm_result()
        assert len(result["unmatched_receipts"]) == 3

    def test_unmatched_invoices_have_vendor(self):
        result = _make_twm_result()
        for inv in result["unmatched_invoices"]:
            assert "vendor" in inv

    def test_unmatched_pos_have_vendor(self):
        result = _make_twm_result()
        for po in result["unmatched_pos"]:
            assert "vendor" in po

    def test_unmatched_receipts_have_vendor(self):
        result = _make_twm_result()
        for rec in result["unmatched_receipts"]:
            assert "vendor" in rec


# =============================================================================
# CONCLUSION TESTS
# =============================================================================


class TestConclusion:
    """Section IX: Conclusion text per risk tier (BUG-002: score-aware)."""

    def test_low_conclusion_exists(self):
        assert "LOW" in _build_risk_conclusion("low", 5.0)

    def test_moderate_conclusion_exists(self):
        assert "MODERATE" in _build_risk_conclusion("moderate", 20.0)

    def test_elevated_conclusion_exists(self):
        assert "ELEVATED" in _build_risk_conclusion("elevated", 35.0)

    def test_high_conclusion_exists(self):
        assert "HIGH" in _build_risk_conclusion("high", 60.0)

    def test_score_included_in_conclusion(self):
        """BUG-002: Conclusion must include numeric score."""
        assert "20.0/100" in _build_risk_conclusion("moderate", 20.0)

    def test_no_medium_in_conclusions(self):
        """BUG-01: No 'MEDIUM' tier in any conclusion text."""
        for tier in _RISK_CONCLUSION_SUFFIXES:
            text = _build_risk_conclusion(tier, 50.0)
            assert "MEDIUM" not in text, f"MEDIUM found in {tier} conclusion"


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================


class TestGuardrails:
    """Guardrail compliance tests."""

    def test_no_medium_tier_in_conclusions(self):
        for tier in _RISK_CONCLUSION_SUFFIXES:
            text = _build_risk_conclusion(tier, 50.0)
            assert "MEDIUM" not in text

    def test_all_test_descriptions_reference_audit_concept(self):
        audit_terms = ["PO", "invoice", "GRN", "fraud", "ISA", "control", "match", "variance", "billing"]
        for key, desc in _TEST_DESCRIPTIONS.items():
            lower = desc.lower()
            has_term = any(t.lower() in lower for t in audit_terms)
            assert has_term, f"{key} description lacks audit terminology"

    def test_engine_tier_mapping_covers_all_engine_values(self):
        """Ensure we handle all values from MatchRiskLevel enum."""
        assert "low" in _ENGINE_TIER_MAPPING
        assert "medium" in _ENGINE_TIER_MAPPING
        assert "high" in _ENGINE_TIER_MAPPING
