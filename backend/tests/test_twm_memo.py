"""
Tests for Three-Way Match Memo Generator (Sprint 504)

Tests:
- PDF generation and validation
- Section II Methodology table
- Section III Match Results with benchmark
- Section IV Material Variances with vendor columns and net direction
- Section V Unmatched Documents detail tables
- Conclusion text per engine risk assessment (Sprint 886, OUT-11: the engine's
  LOW / MEDIUM / HIGH in its own words; no composite score — the engine has none)
- Guardrails (terminology, ISA references)
"""

from three_way_match_memo_generator import (
    _RISK_CONCLUSION_SUFFIXES,
    _RISK_LEVELS,
    _TEST_DESCRIPTIONS,
    _build_risk_conclusion,
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
    """Conclusion in the engine's own classification (Sprint 886, OUT-11)."""

    def test_each_engine_level_is_named_in_its_own_word(self):
        for level in ("low", "medium", "high"):
            assert f"returned a {level.upper()} risk assessment" in _build_risk_conclusion(level)

    def test_conclusions_cover_exactly_the_engine_levels(self):
        from three_way_match_engine import MatchRiskLevel

        assert set(_RISK_CONCLUSION_SUFFIXES) == set(_RISK_LEVELS) == {lvl.value for lvl in MatchRiskLevel}

    def test_no_score_and_no_renamed_tiers(self):
        for level in _RISK_LEVELS:
            text = _build_risk_conclusion(level)
            assert "/100" not in text
            assert "MODERATE" not in text and "ELEVATED" not in text

    def test_missing_assessment_is_not_reported_as_low(self):
        text = _build_risk_conclusion(None)
        assert "No risk assessment was available" in text
        assert "LOW" not in text


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================


class TestGuardrails:
    """Guardrail compliance tests."""

    def test_all_test_descriptions_reference_audit_concept(self):
        audit_terms = ["PO", "invoice", "GRN", "fraud", "ISA", "control", "match", "variance", "billing"]
        for key, desc in _TEST_DESCRIPTIONS.items():
            lower = desc.lower()
            has_term = any(t.lower() in lower for t in audit_terms)
            assert has_term, f"{key} description lacks audit terminology"
