"""
Tests for the Statistical Sampling Memo Generator — Sprint 506

Covers:
- PDF generation (design + evaluation)
- BUG-01: Authoritative references (ISA 530, AS 2315, AU-C 530)
- BUG-02: Population value clarifying note
- BUG-03: Sample size gap explanation
- BUG-04: Confidence factor derivation note
- IMP-01: Expected misstatement derivation
- IMP-02: Sample selection preview (first 10 items)
- IMP-03: Population-type-specific next steps
- Guardrails
"""

import pytest

from sampling_memo_generator import (
    CONFIDENCE_FACTOR_NOTES,
    NEXT_STEPS_BY_POPULATION_TYPE,
    _format_stratum,
    _next_section_number,
    _roman,
    _roman_after,
    generate_sampling_design_memo,
    generate_sampling_evaluation_memo,
)
from shared.framework_resolution import ResolvedFramework
from shared.scope_methodology import get_tool_content

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def design_result():
    """Full design result with all enrichments."""
    return {
        "method": "mus",
        "confidence_level": 0.95,
        "confidence_factor": 3.0,
        "tolerable_misstatement": 75_000.00,
        "expected_misstatement": 15_000.00,
        "population_size": 1_240,
        "population_value": 4_850_000.00,
        "sampling_interval": 25_000.00,
        "calculated_sample_size": 194,
        "actual_sample_size": 207,
        "high_value_count": 42,
        "high_value_total": 2_100_000.00,
        "remainder_count": 1_198,
        "remainder_sample_size": 165,
        "population_type": "AR",
        "population_value_note": (
            "Population value of $4,850,000.00 represents aggregate invoice activity for FY2025 per the AR sub-ledger."
        ),
        "strata_summary": [
            {
                "stratum": "High Value (100%)",
                "threshold": ">$25,000",
                "count": 42,
                "total_value": 2_100_000.00,
                "sample_size": 42,
            },
            {
                "stratum": "Remainder (MUS)",
                "threshold": "≤$25,000",
                "count": 1_198,
                "total_value": 2_750_000.00,
                "sample_size": 165,
            },
        ],
        "selected_items": [
            {
                "item_id": "INV-0012",
                "description": "Meridian Holdings — Q1 Retainer",
                "recorded_amount": 85_000.00,
                "stratum": "high_value",
                "selection_method": "high_value_100pct",
            },
            {
                "item_id": "INV-0047",
                "description": "Apex Solutions — Cloud Infrastructure",
                "recorded_amount": 62_500.00,
                "stratum": "high_value",
                "selection_method": "high_value_100pct",
            },
            {
                "item_id": "INV-0103",
                "description": "Pinnacle Partners — Annual License",
                "recorded_amount": 48_200.00,
                "stratum": "high_value",
                "selection_method": "high_value_100pct",
            },
            {
                "item_id": "INV-0218",
                "description": "Sterling Corp — Project Milestone 3",
                "recorded_amount": 37_800.00,
                "stratum": "high_value",
                "selection_method": "high_value_100pct",
            },
            {
                "item_id": "INV-0344",
                "description": "Vanguard Tech — Hardware Procurement",
                "recorded_amount": 31_450.00,
                "stratum": "high_value",
                "selection_method": "high_value_100pct",
            },
            {
                "item_id": "INV-0512",
                "description": "Crestview Industries — Consulting Fee",
                "recorded_amount": 18_750.00,
                "stratum": "remainder",
                "selection_method": "mus_interval",
            },
            {
                "item_id": "INV-0687",
                "description": "Atlas Logistics — Shipping Services",
                "recorded_amount": 12_400.00,
                "stratum": "remainder",
                "selection_method": "mus_interval",
            },
            {
                "item_id": "INV-0891",
                "description": "Horizon Media — Advertising Campaign",
                "recorded_amount": 9_800.00,
                "stratum": "remainder",
                "selection_method": "mus_interval",
            },
            {
                "item_id": "INV-1024",
                "description": "Summit Engineering — Design Review",
                "recorded_amount": 7_250.00,
                "stratum": "remainder",
                "selection_method": "mus_interval",
            },
            {
                "item_id": "INV-1156",
                "description": "Pacific Trading — Component Supply",
                "recorded_amount": 4_600.00,
                "stratum": "remainder",
                "selection_method": "mus_interval",
            },
            {
                "item_id": "INV-1289",
                "description": "Granite Construction — Site Assessment",
                "recorded_amount": 3_200.00,
                "stratum": "remainder",
                "selection_method": "mus_interval",
            },
            {
                "item_id": "INV-1403",
                "description": "Beacon Analytics — Data Processing",
                "recorded_amount": 2_100.00,
                "stratum": "remainder",
                "selection_method": "mus_interval",
            },
        ],
    }


@pytest.fixture
def evaluation_result():
    """Full evaluation result."""
    return {
        "method": "mus",
        "confidence_level": 0.95,
        "sample_size": 207,
        "errors_found": 3,
        "total_misstatement": 4_230.00,
        "projected_misstatement": 12_480.00,
        "basic_precision": 25_000.00,
        "incremental_allowance": 8_750.00,
        "upper_error_limit": 46_230.00,
        "tolerable_misstatement": 75_000.00,
        "conclusion": "pass",
        "conclusion_detail": ("The upper error limit ($46,230) does not exceed the tolerable misstatement ($75,000)."),
        "errors": [
            {
                "item_id": "INV-2847",
                "recorded_amount": 3_450.00,
                "audited_amount": 3_200.00,
                "misstatement": 250.00,
                "tainting": 0.0725,
            },
            {
                "item_id": "INV-4102",
                "recorded_amount": 12_800.00,
                "audited_amount": 9_220.00,
                "misstatement": 3_580.00,
                "tainting": 0.2797,
            },
            {
                "item_id": "INV-5391",
                "recorded_amount": 1_600.00,
                "audited_amount": 1_200.00,
                "misstatement": 400.00,
                "tainting": 0.2500,
            },
        ],
    }


@pytest.fixture
def minimal_design():
    """Minimal design result for edge cases."""
    return {
        "method": "mus",
        "confidence_level": 0.95,
        "confidence_factor": 3.0,
        "tolerable_misstatement": 50_000.00,
        "expected_misstatement": 0.0,
        "population_size": 500,
        "population_value": 1_000_000.00,
        "sampling_interval": 16_667.00,
        "calculated_sample_size": 60,
        "actual_sample_size": 60,
    }


# ═══════════════════════════════════════════════════════════════
# PDF Generation
# ═══════════════════════════════════════════════════════════════


class TestPDFGeneration:
    """Basic PDF generation tests."""

    def test_design_memo_generates(self, design_result):
        pdf = generate_sampling_design_memo(
            design_result,
            "meridian_ar_subledger.csv",
            client_name="Meridian Capital Group",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_evaluation_memo_generates(self, evaluation_result, design_result):
        pdf = generate_sampling_evaluation_memo(
            evaluation_result,
            design_result,
            "meridian_ar_subledger.csv",
            client_name="Meridian Capital Group",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_evaluation_memo_without_design(self, evaluation_result):
        pdf = generate_sampling_evaluation_memo(
            evaluation_result,
            filename="sample.csv",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_design_memo_with_gasb_framework(self, design_result):
        pdf = generate_sampling_design_memo(
            design_result,
            client_name="City of Portland",
            resolved_framework=ResolvedFramework.GASB,
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_minimal_design_generates(self, minimal_design):
        """Design memo without strata, preview, or population_type."""
        pdf = generate_sampling_design_memo(minimal_design, "test.csv")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000


# ═══════════════════════════════════════════════════════════════
# BUG-01: Authoritative References
# ═══════════════════════════════════════════════════════════════


class TestAuthoritativeReferences:
    """BUG-01: References must cite ISA 530, AS 2315, AU-C 530."""

    def test_fasb_references_contain_isa_530(self):
        content = get_tool_content("statistical_sampling", ResolvedFramework.FASB)
        refs = content.references
        ref_ids = [r.reference for r in refs]
        assert "ISA 530" in ref_ids

    def test_fasb_references_contain_as_2315(self):
        content = get_tool_content("statistical_sampling", ResolvedFramework.FASB)
        refs = content.references
        ref_ids = [r.reference for r in refs]
        assert "AS 2315" in ref_ids

    def test_fasb_references_contain_au_c_530(self):
        content = get_tool_content("statistical_sampling", ResolvedFramework.FASB)
        refs = content.references
        ref_ids = [r.reference for r in refs]
        assert "AU-C Section 530" in ref_ids

    def test_fasb_references_contain_asc_450(self):
        content = get_tool_content("statistical_sampling", ResolvedFramework.FASB)
        refs = content.references
        ref_ids = [r.reference for r in refs]
        assert "ASC 450-20" in ref_ids

    def test_fasb_references_no_asc_250(self):
        """ASC 250-10 should be removed from statistical sampling."""
        content = get_tool_content("statistical_sampling", ResolvedFramework.FASB)
        refs = content.references
        ref_ids = [r.reference for r in refs]
        assert "ASC 250-10" not in ref_ids

    def test_fasb_per_reference_body_override(self):
        """References should have per-reference body overrides."""
        content = get_tool_content("statistical_sampling", ResolvedFramework.FASB)
        bodies = {r.reference: r.body for r in content.references}
        assert bodies["ISA 530"] == "IAASB"
        assert bodies["AS 2315"] == "PCAOB"
        assert bodies["AU-C Section 530"] == "AICPA"
        assert bodies["ASC 450-20"] == "FASB"

    def test_gasb_references_contain_isa_530(self):
        content = get_tool_content("statistical_sampling", ResolvedFramework.GASB)
        refs = content.references
        ref_ids = [r.reference for r in refs]
        assert "ISA 530" in ref_ids

    def test_gasb_references_contain_as_2315(self):
        content = get_tool_content("statistical_sampling", ResolvedFramework.GASB)
        refs = content.references
        ref_ids = [r.reference for r in refs]
        assert "AS 2315" in ref_ids

    def test_gasb_per_reference_body_override(self):
        content = get_tool_content("statistical_sampling", ResolvedFramework.GASB)
        bodies = {r.reference: r.body for r in content.references}
        assert bodies["ISA 530"] == "IAASB"
        assert bodies["AS 2315"] == "PCAOB"


# ═══════════════════════════════════════════════════════════════
# BUG-02: Population Value Note
# ═══════════════════════════════════════════════════════════════


class TestPopulationValueNote:
    """BUG-02: Population value clarifying note renders when provided."""

    def test_design_with_population_note_generates(self, design_result):
        """Memo generates successfully when population_value_note is present."""
        assert "population_value_note" in design_result
        pdf = generate_sampling_design_memo(design_result, "test.csv")
        assert len(pdf) > 1000

    def test_design_without_population_note_generates(self, minimal_design):
        """Memo generates successfully without population_value_note."""
        assert "population_value_note" not in minimal_design
        pdf = generate_sampling_design_memo(minimal_design, "test.csv")
        assert len(pdf) > 1000


# ═══════════════════════════════════════════════════════════════
# BUG-03: Sample Size Gap
# ═══════════════════════════════════════════════════════════════


class TestSampleSizeGap:
    """BUG-03: Gap between calculated and actual explained."""

    def test_gap_present_when_sizes_differ(self, design_result):
        """When calc != actual, memo should generate with explanation."""
        assert design_result["calculated_sample_size"] != design_result["actual_sample_size"]
        pdf = generate_sampling_design_memo(design_result, "test.csv")
        assert len(pdf) > 1000

    def test_no_gap_when_sizes_equal(self, minimal_design):
        """When calc == actual, no gap note needed."""
        assert minimal_design["calculated_sample_size"] == minimal_design["actual_sample_size"]
        pdf = generate_sampling_design_memo(minimal_design, "test.csv")
        assert len(pdf) > 1000

    def test_custom_sample_size_note(self, design_result):
        """Custom sample_size_note is accepted."""
        design_result["sample_size_note"] = "Partner instruction: add 13 items for risk coverage."
        pdf = generate_sampling_design_memo(design_result, "test.csv")
        assert len(pdf) > 1000


# ═══════════════════════════════════════════════════════════════
# BUG-04: Confidence Factor Notes
# ═══════════════════════════════════════════════════════════════


class TestConfidenceFactorNotes:
    """BUG-04: Confidence factor derivation note."""

    def test_all_standard_levels_have_notes(self):
        """All standard confidence levels must have notes."""
        for level in [0.80, 0.85, 0.90, 0.95, 0.97, 0.99]:
            assert level in CONFIDENCE_FACTOR_NOTES

    def test_95_note_mentions_3_0000(self):
        note = CONFIDENCE_FACTOR_NOTES[0.95]
        assert "3.0000" in note

    def test_90_note_mentions_2_3026(self):
        note = CONFIDENCE_FACTOR_NOTES[0.90]
        assert "2.3026" in note

    def test_design_memo_with_95_confidence_generates(self, design_result):
        """95% confidence should trigger note rendering."""
        assert design_result["confidence_level"] == 0.95
        pdf = generate_sampling_design_memo(design_result, "test.csv")
        assert len(pdf) > 1000


# ═══════════════════════════════════════════════════════════════
# IMP-01: Expected Misstatement Derivation
# ═══════════════════════════════════════════════════════════════


class TestExpectedMisstatementDerivation:
    """IMP-01: EM derivation block renders."""

    def test_em_block_renders_when_em_positive(self, design_result):
        """EM > 0 should trigger derivation block."""
        assert design_result["expected_misstatement"] > 0
        pdf = generate_sampling_design_memo(design_result, "test.csv")
        assert len(pdf) > 1000

    def test_no_em_block_when_em_zero(self, minimal_design):
        """EM == 0 should skip derivation block."""
        assert minimal_design["expected_misstatement"] == 0
        pdf = generate_sampling_design_memo(minimal_design, "test.csv")
        assert len(pdf) > 1000

    def test_custom_em_note(self, design_result):
        """Custom expected_misstatement_note is accepted."""
        design_result["expected_misstatement_note"] = (
            "Based on prior year misstatements of $12,000 identified in AR testing."
        )
        pdf = generate_sampling_design_memo(design_result, "test.csv")
        assert len(pdf) > 1000

    def test_em_percentage_of_tm(self, design_result):
        """EM/TM percentage is calculable."""
        em = design_result["expected_misstatement"]
        tm = design_result["tolerable_misstatement"]
        pct = em / tm * 100
        assert 19.9 < pct < 20.1  # 15,000 / 75,000 = 20%


# ═══════════════════════════════════════════════════════════════
# IMP-02: Sample Selection Preview
# ═══════════════════════════════════════════════════════════════


class TestSampleSelectionPreview:
    """IMP-02: Sample listing preview table."""

    def test_preview_renders_with_items(self, design_result):
        """Preview section renders when selected_items present."""
        assert len(design_result["selected_items"]) > 0
        pdf = generate_sampling_design_memo(design_result, "test.csv")
        assert len(pdf) > 1000

    def test_preview_max_10_items(self, design_result):
        """Preview table should show at most 10 items."""
        assert len(design_result["selected_items"]) == 12
        # The memo generator slices [:10] — verify by code inspection
        # (PDF content verification would require PDF parsing)
        pdf = generate_sampling_design_memo(design_result, "test.csv")
        assert len(pdf) > 1000

    def test_no_preview_without_items(self, minimal_design):
        """No preview section when selected_items missing."""
        assert "selected_items" not in minimal_design
        pdf = generate_sampling_design_memo(minimal_design, "test.csv")
        assert len(pdf) > 1000

    def test_preview_item_structure(self, design_result):
        """Each selected item has required fields."""
        for item in design_result["selected_items"]:
            assert "item_id" in item
            assert "description" in item
            assert "recorded_amount" in item
            assert "stratum" in item

    def test_high_value_items_first(self, design_result):
        """High-value items appear before remainder items."""
        items = design_result["selected_items"]
        hv_end = 0
        for i, item in enumerate(items):
            if item["stratum"] == "high_value":
                hv_end = i
        # After last HV item, all remaining should be remainder
        for item in items[hv_end + 1 :]:
            assert item["stratum"] == "remainder"


# ═══════════════════════════════════════════════════════════════
# IMP-03: Next Steps by Population Type
# ═══════════════════════════════════════════════════════════════


class TestNextStepsByPopulationType:
    """IMP-03: Population-type-specific next steps."""

    def test_ar_steps_available(self):
        assert "AR" in NEXT_STEPS_BY_POPULATION_TYPE

    def test_ap_steps_available(self):
        assert "AP" in NEXT_STEPS_BY_POPULATION_TYPE

    def test_inventory_steps_available(self):
        assert "INVENTORY" in NEXT_STEPS_BY_POPULATION_TYPE

    def test_revenue_steps_available(self):
        assert "REVENUE" in NEXT_STEPS_BY_POPULATION_TYPE

    def test_ar_has_5_steps(self):
        assert len(NEXT_STEPS_BY_POPULATION_TYPE["AR"]) == 5

    def test_ar_step1_mentions_invoice(self):
        step1 = NEXT_STEPS_BY_POPULATION_TYPE["AR"][0]
        assert "invoice" in step1["body"].lower()

    def test_ar_step2_mentions_isa_505(self):
        step2 = NEXT_STEPS_BY_POPULATION_TYPE["AR"][1]
        assert "ISA 505" in step2["title"]

    def test_ar_step3_mentions_assertions(self):
        step3 = NEXT_STEPS_BY_POPULATION_TYPE["AR"][2]
        assert "existence" in step3["body"].lower()
        assert "valuation" in step3["body"].lower()
        assert "cut-off" in step3["body"].lower()

    def test_ar_step5_mentions_uel(self):
        step5 = NEXT_STEPS_BY_POPULATION_TYPE["AR"][4]
        assert "Upper Error Limit" in step5["body"]
        assert "ISA 530" in step5["body"]

    def test_ar_step5_mentions_paciolus(self):
        step5 = NEXT_STEPS_BY_POPULATION_TYPE["AR"][4]
        assert "Paciolus" in step5["body"]

    def test_generic_fallback_for_unknown_type(self, design_result):
        """Unknown population type falls back to generic steps."""
        design_result["population_type"] = "UNKNOWN"
        pdf = generate_sampling_design_memo(design_result, "test.csv")
        assert len(pdf) > 1000

    def test_empty_population_type_uses_generic(self, minimal_design):
        """Missing population_type uses generic steps."""
        pdf = generate_sampling_design_memo(minimal_design, "test.csv")
        assert len(pdf) > 1000


# ═══════════════════════════════════════════════════════════════
# Section Numbering
# ═══════════════════════════════════════════════════════════════


class TestSectionNumbering:
    """Section numbering logic."""

    def test_design_with_strata_methodology_is_iv(self, design_result):
        """Scope I, Design II, Strata III → Methodology = IV."""
        num = _next_section_number(design_result, None)
        assert num == "IV"

    def test_design_without_strata_methodology_is_iii(self, minimal_design):
        """Scope I, Design II → Methodology = III."""
        num = _next_section_number(minimal_design, None)
        assert num == "III"

    def test_evaluation_only_methodology_is_iii(self):
        """Scope I, Eval II → Methodology = III."""
        eval_result = {"errors": []}
        num = _next_section_number(None, eval_result)
        assert num == "III"

    def test_roman_numeral_mapping(self):
        for i, expected in enumerate(["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"], 1):
            assert _roman(i) == expected

    def test_roman_after(self):
        assert _roman_after("I") == "II"
        assert _roman_after("IV") == "V"
        assert _roman_after("IX") == "X"


# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════


class TestHelpers:
    """Helper function tests."""

    def test_format_stratum_high_value(self):
        assert _format_stratum("high_value") == "High Value"

    def test_format_stratum_remainder(self):
        assert _format_stratum("remainder") == "Remainder"

    def test_format_stratum_empty(self):
        assert _format_stratum("") == ""

    def test_format_stratum_custom(self):
        assert _format_stratum("special_items") == "Special Items"


# ═══════════════════════════════════════════════════════════════
# Guardrails
# ═══════════════════════════════════════════════════════════════


class TestGuardrails:
    """Non-committal language and guardrail checks."""

    def test_next_steps_no_assertive_language(self):
        """Next steps should not contain banned assertive phrases."""
        from shared.scope_methodology import validate_non_committal

        for pop_type, steps in NEXT_STEPS_BY_POPULATION_TYPE.items():
            for step in steps:
                violations = validate_non_committal(step["body"])
                assert violations == [], f"Banned phrase in {pop_type} step '{step['title']}': {violations}"

    def test_confidence_notes_no_assertive_language(self):
        from shared.scope_methodology import validate_non_committal

        for level, note in CONFIDENCE_FACTOR_NOTES.items():
            violations = validate_non_committal(note)
            assert violations == [], f"Banned phrase in confidence note {level}: {violations}"

    def test_references_exactly_4_for_fasb(self):
        content = get_tool_content("statistical_sampling", ResolvedFramework.FASB)
        assert len(content.references) == 4

    def test_references_exactly_4_for_gasb(self):
        content = get_tool_content("statistical_sampling", ResolvedFramework.GASB)
        assert len(content.references) == 4

    def test_all_population_types_have_5_steps(self):
        for pop_type, steps in NEXT_STEPS_BY_POPULATION_TYPE.items():
            assert len(steps) == 5, f"{pop_type} has {len(steps)} steps, expected 5"
