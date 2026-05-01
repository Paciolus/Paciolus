"""
Memo PDF contract tests (Sprint 749 — Phase 3 Export Rationalization 2/2).

Demonstrates the schema-level contract-test pattern from ADR-016:
extract text from the generated PDF bytes and assert that key section
labels appear. Catches regressions where a section is silently removed
or renamed (which CI/lint cannot detect because the PDF still renders
without errors).

Pattern (replicate per memo):
  1. Build a minimal valid input via the existing test fixtures.
  2. Generate the PDF via the memo generator (or POST through the route
     for end-to-end coverage when needed).
  3. Extract text via `pypdf.PdfReader`.
  4. Assert each required section label appears in the extracted text.

Sprint 749 ships one demo (JE Testing memo). Subsequent sprints extend
to the remaining 17 memos as they're touched. The pattern is documented
inline so reviewers can replicate it without re-deriving the approach.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from pypdf import PdfReader

from accrual_completeness_memo import generate_accrual_completeness_memo
from ap_testing_memo_generator import generate_ap_testing_memo
from ar_aging_memo_generator import generate_ar_aging_memo
from bank_reconciliation_memo_generator import generate_bank_rec_memo
from currency_memo_generator import generate_currency_conversion_memo
from expense_category_memo import generate_expense_category_memo
from fixed_asset_testing_memo_generator import generate_fixed_asset_testing_memo
from flux_expectations_memo import generate_flux_expectations_memo
from inventory_testing_memo_generator import generate_inventory_testing_memo
from je_testing_memo_generator import generate_je_testing_memo
from multi_period_memo_generator import generate_multi_period_memo
from payroll_testing_memo_generator import generate_payroll_testing_memo
from population_profile_memo import generate_population_profile_memo
from preflight_memo_generator import generate_preflight_memo
from revenue_testing_memo_generator import generate_revenue_testing_memo
from sampling_memo_generator import (
    generate_sampling_design_memo,
    generate_sampling_evaluation_memo,
)

# Reuse existing memo fixture builders so contract tests stay anchored
# to the same input schemas the unit tests use.
from tests.test_ap_testing_memo import _make_ap_result
from tests.test_ar_aging_memo import _make_ar_result
from tests.test_bank_rec_memo import _make_rec_result
from tests.test_expense_category_memo import SAMPLE_REPORT as EXPENSE_CATEGORY_SAMPLE
from tests.test_fixed_asset_testing_memo import _make_fa_result
from tests.test_inventory_testing_memo import _make_inv_result
from tests.test_je_testing_memo import _make_je_result
from tests.test_multi_period_memo import _make_comparison_result
from tests.test_payroll_testing_memo import _make_payroll_result
from tests.test_preflight_memo import _make_preflight_result
from tests.test_revenue_testing_memo import _make_revenue_result
from three_way_match_memo_generator import generate_three_way_match_memo


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Concatenate text from every page of a generated PDF."""
    reader = PdfReader(BytesIO(pdf_bytes))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# JE Testing Memo — required section labels (AS 2401 / ISA 240 alignment)
# ---------------------------------------------------------------------------

# Each label MUST appear at least once in the rendered PDF text. Removing
# or renaming a label here without coordinating with the memo generator
# is a contract change that downstream auditors / customers will notice.
# NOTE: pypdf text extraction can split phrases across column boundaries
# in multi-column PDF layouts (e.g., "Risk Tier" may render as "Risk" on
# one line and "Tier" on another, defeating substring search). When
# choosing labels for this list, prefer single-word section anchors over
# multi-word phrases, and verify with `python -c "..."` extraction first.
JE_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Journal Entry Testing",  # title / cover page
    "Tier",  # risk-tier verdict ("elevated" / "moderate" / "high" sections)
    "Conclusion",  # auditor conclusion section
    "Findings",  # findings table or top-findings section
    "Composite",  # composite score / summary band
)


def test_je_memo_pdf_contains_all_required_section_labels() -> None:
    """
    Sprint 749 contract test demo: every required section label appears in
    the generated JE Testing memo PDF.

    Regression scenarios this catches:
      - A required section accidentally gated behind a flag that defaults
        to off in production.
      - A section header rename that breaks downstream auditor workflow
        (e.g., search-and-replace tools that locate sections by label).
      - A blank PDF rendered as a no-op fallback when the generator
        raises mid-flight.
    """
    pdf_bytes = generate_je_testing_memo(_make_je_result())
    text = _extract_pdf_text(pdf_bytes)

    missing = [label for label in JE_MEMO_REQUIRED_SECTIONS if label not in text]
    assert not missing, (
        f"JE memo PDF missing required section labels: {missing}. "
        f"Either the generator regressed, or JE_MEMO_REQUIRED_SECTIONS in this "
        f"test needs to be updated to match an intentional schema change."
    )


def test_je_memo_pdf_is_a_valid_pdf_with_pages() -> None:
    """Smoke check: the bytes parse as a non-empty PDF (i.e., the
    extraction itself worked). Catches generator regressions where bytes
    look like a PDF but pypdf rejects them as malformed."""
    pdf_bytes = generate_je_testing_memo(_make_je_result())
    reader = PdfReader(BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1


# ---------------------------------------------------------------------------
# AP Testing Memo (PCAOB AS 2305 / ISA 500)
# ---------------------------------------------------------------------------

AP_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "AP",  # title prefix; multi-word "Accounts Payable" splits across columns
    "Vendor",  # vendor analysis section
    "Tier",  # risk tier
    "Conclusion",
    "Findings",
    "Composite",
)


def test_ap_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_ap_testing_memo(_make_ap_result())
    text = _extract_pdf_text(pdf_bytes)
    missing = [label for label in AP_MEMO_REQUIRED_SECTIONS if label not in text]
    assert not missing, (
        f"AP memo PDF missing required section labels: {missing}. "
        f"Either the generator regressed, or AP_MEMO_REQUIRED_SECTIONS needs "
        f"updating to match an intentional schema change."
    )


# ---------------------------------------------------------------------------
# Payroll Testing Memo (ISA 240 fraud indicators)
# ---------------------------------------------------------------------------

PAYROLL_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Payroll",  # title
    "Employee",  # employee testing section
    "Tier",
    "Conclusion",
    "Findings",
    "Composite",
)


def test_payroll_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_payroll_testing_memo(_make_payroll_result())
    text = _extract_pdf_text(pdf_bytes)
    missing = [label for label in PAYROLL_MEMO_REQUIRED_SECTIONS if label not in text]
    assert not missing, (
        f"Payroll memo PDF missing required section labels: {missing}. "
        f"Either the generator regressed, or PAYROLL_MEMO_REQUIRED_SECTIONS "
        f"needs updating to match an intentional schema change."
    )


# ---------------------------------------------------------------------------
# Revenue Testing Memo (ASC 606 / IFRS 15)
# ---------------------------------------------------------------------------

REVENUE_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Revenue",  # title
    "Contract",  # ASC 606 contract analysis section
    "Tier",
    "Conclusion",
    "Findings",
    "Composite",
)


def test_revenue_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_revenue_testing_memo(_make_revenue_result())
    text = _extract_pdf_text(pdf_bytes)
    missing = [label for label in REVENUE_MEMO_REQUIRED_SECTIONS if label not in text]
    assert not missing, (
        f"Revenue memo PDF missing required section labels: {missing}. "
        f"Either the generator regressed, or REVENUE_MEMO_REQUIRED_SECTIONS "
        f"needs updating to match an intentional schema change."
    )


# ---------------------------------------------------------------------------
# AR Aging Memo (ISA 540 — accounting estimates / collectibility)
# ---------------------------------------------------------------------------

AR_AGING_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "AR",
    "Aging",
    "Tier",
    "Conclusion",
    "Findings",
    "Composite",
)


def test_ar_aging_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_ar_aging_memo(_make_ar_result())
    _assert_labels_present(pdf_bytes, AR_AGING_MEMO_REQUIRED_SECTIONS, "AR Aging")


# ---------------------------------------------------------------------------
# Fixed Asset Testing Memo (ISA 500 / IAS 16 / ASC 360)
# ---------------------------------------------------------------------------

FIXED_ASSET_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Fixed Asset",
    "Tier",
    "Conclusion",
    "Findings",
    "Composite",
)


def test_fixed_asset_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_fixed_asset_testing_memo(_make_fa_result())
    _assert_labels_present(pdf_bytes, FIXED_ASSET_MEMO_REQUIRED_SECTIONS, "Fixed Asset")


# ---------------------------------------------------------------------------
# Inventory Testing Memo (ISA 501 / IAS 2 / ASC 330)
# ---------------------------------------------------------------------------

INVENTORY_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Inventory",
    "Tier",
    "Conclusion",
    "Findings",
    "Composite",
)


def test_inventory_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_inventory_testing_memo(_make_inv_result())
    _assert_labels_present(pdf_bytes, INVENTORY_MEMO_REQUIRED_SECTIONS, "Inventory")


# ---------------------------------------------------------------------------
# Three-Way Match Memo (ISA 500 substantive testing)
# ---------------------------------------------------------------------------

# No fixture in tests/test_three_way_match_memo.py — build inline minimal valid
# input matching the route's TWM input contract.
_TWM_FIXTURE = {
    "summary": {
        "total_pos": 156,
        "total_invoices": 148,
        "total_receipts": 139,
        "full_match_count": 118,
        "partial_match_count": 21,
        "unmatched_count": 17,
        "match_score": 0.78,
        "total_pos_value": "1250000",
        "total_invoiced": "1187500",
        "total_received_value": "1198400",
    },
    "discrepancies": [],
    "vendor_summaries": [],
    "discrepancies_by_severity": {"high": 5, "medium": 8, "low": 4},
    "data_quality": {"messages": []},
    "config": {},
    "duplicate_groups": [],
    "duplicate_summary": {"groups": 0, "potential_overpayment": "0"},
    "po_invoice_only": [],
    "spend_concentration": {"top_5_pct": 35.2},
    "deterministic_run_id": "twm_test",
}

THREE_WAY_MATCH_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Three-Way",
    "Match",
    "Invoice",
    "Conclusion",
    "Composite",
)


def test_three_way_match_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_three_way_match_memo(_TWM_FIXTURE)
    _assert_labels_present(pdf_bytes, THREE_WAY_MATCH_MEMO_REQUIRED_SECTIONS, "Three-Way Match")


# ---------------------------------------------------------------------------
# Multi-Period Comparison Memo (ISA 520 trend analysis)
# ---------------------------------------------------------------------------

MULTI_PERIOD_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Period",
    "Tier",
    "Conclusion",
    "Composite",
)


def test_multi_period_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_multi_period_memo(_make_comparison_result())
    _assert_labels_present(pdf_bytes, MULTI_PERIOD_MEMO_REQUIRED_SECTIONS, "Multi-Period")


# ---------------------------------------------------------------------------
# Bank Reconciliation Memo (ISA 500 external confirmation)
# ---------------------------------------------------------------------------

BANK_REC_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Bank",
    "Reconciliation",
    "Conclusion",
    "Composite",
    "Match",
)


def test_bank_rec_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_bank_rec_memo(_make_rec_result())
    _assert_labels_present(pdf_bytes, BANK_REC_MEMO_REQUIRED_SECTIONS, "Bank Rec")


# ---------------------------------------------------------------------------
# Sampling Design Memo (ISA 530 sample design)
# ---------------------------------------------------------------------------

# No reusable fixture for sampling memos — build inline.
_SAMPLING_DESIGN_FIXTURE = {
    "method": "mus",
    "confidence_level": 0.95,
    "confidence_factor": 3.0,
    "tolerable_misstatement": 75000.0,
    "expected_misstatement": 15000.0,
    "population_size": 1240,
    "population_value": 4250000.0,
    "actual_sample_size": 100,
    "selected_items": [],
    "stratification_threshold": None,
    "sample_size_override": None,
    "deterministic_seed": 42,
    "deterministic_run_id": "sampling_test",
}

SAMPLING_DESIGN_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Sampling",
    "MUS",
    "Conclusion",
    "Population",
)


def test_sampling_design_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_sampling_design_memo(_SAMPLING_DESIGN_FIXTURE)
    _assert_labels_present(pdf_bytes, SAMPLING_DESIGN_MEMO_REQUIRED_SECTIONS, "Sampling Design")


# ---------------------------------------------------------------------------
# Sampling Evaluation Memo (ISA 530 sample evaluation)
# ---------------------------------------------------------------------------

_SAMPLING_EVAL_FIXTURE = {
    **_SAMPLING_DESIGN_FIXTURE,
    "errors": [],
    "projected_misstatement": 0.0,
    "upper_error_limit": 0.0,
    "ratio_estimator": 0.0,
    "actual_misstatement": 0.0,
    "conclusion": "pass",
    "conclusion_detail": "UEL within tolerance",
    "uel_methodology": "MUS",
    "stringer_components": [],
}

SAMPLING_EVAL_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Sampling",
    "MUS",
    "Conclusion",
    "Population",
)


def test_sampling_eval_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_sampling_evaluation_memo(
        _SAMPLING_EVAL_FIXTURE,
        design_result=_SAMPLING_DESIGN_FIXTURE,
    )
    _assert_labels_present(pdf_bytes, SAMPLING_EVAL_MEMO_REQUIRED_SECTIONS, "Sampling Eval")


# ---------------------------------------------------------------------------
# Pre-Flight Memo (data quality pre-pipeline)
# ---------------------------------------------------------------------------

PREFLIGHT_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Pre-Flight",
    "Conclusion",
    "Risk",
)


def test_preflight_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_preflight_memo(_make_preflight_result())
    _assert_labels_present(pdf_bytes, PREFLIGHT_MEMO_REQUIRED_SECTIONS, "Pre-Flight")


# ---------------------------------------------------------------------------
# Population Profile Memo (descriptive statistics aggregator)
# ---------------------------------------------------------------------------

_POPULATION_PROFILE_FIXTURE = {
    "filename": "tb.csv",
    "account_count": 100,
    "total_abs_balance": 500000,
    "mean_abs_balance": 5000,
    "median_abs_balance": 3000,
    "std_dev_abs_balance": 8000,
    "min_abs_balance": 100,
    "max_abs_balance": 50000,
    "p25": 1000,
    "p75": 8000,
    "gini_coefficient": 0.45,
    "gini_interpretation": "Moderate concentration",
    "buckets": [],
    "top_accounts": [],
    "benford_first_digit": None,
}

POPULATION_PROFILE_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Population",
    "Profile",
    "Account",
    "Balance",
)


def test_population_profile_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_population_profile_memo(_POPULATION_PROFILE_FIXTURE)
    _assert_labels_present(pdf_bytes, POPULATION_PROFILE_MEMO_REQUIRED_SECTIONS, "Population Profile")


# ---------------------------------------------------------------------------
# Expense Category Memo (ISA 520 analytical procedures)
# ---------------------------------------------------------------------------

EXPENSE_CATEGORY_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Expense",
    "Category",
    "Materiality",
    "Threshold",
)


def test_expense_category_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_expense_category_memo(EXPENSE_CATEGORY_SAMPLE)
    _assert_labels_present(pdf_bytes, EXPENSE_CATEGORY_MEMO_REQUIRED_SECTIONS, "Expense Category")


# ---------------------------------------------------------------------------
# Accrual Completeness Memo (operating-expense run-rate comparison)
# ---------------------------------------------------------------------------

_ACCRUAL_COMPLETENESS_FIXTURE = {
    "filename": "tb.csv",
    "accrual_account_count": 5,
    "total_accrued_balance": 250000,
    "prior_available": True,
    "prior_operating_expenses": 4000000,
    "monthly_run_rate": 333000,
    "accrual_to_run_rate_pct": 75,
    "threshold_pct": 50,
    "below_threshold": False,
    "accrual_accounts": [],
    "narrative": "Accruals appear complete.",
}

ACCRUAL_COMPLETENESS_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Accrual",
    "Period",
    "Threshold",
    "Balance",
)


def test_accrual_completeness_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_accrual_completeness_memo(_ACCRUAL_COMPLETENESS_FIXTURE)
    _assert_labels_present(pdf_bytes, ACCRUAL_COMPLETENESS_MEMO_REQUIRED_SECTIONS, "Accrual Completeness")


# ---------------------------------------------------------------------------
# Currency Conversion Memo (IAS 21 / ASC 830 — side-car validation)
# ---------------------------------------------------------------------------

_CURRENCY_FIXTURE = {
    "client_name": None,
    "filename": "tb.csv",
    "balance_check_passed": True,
    "balance_imbalance": 0.0,
    "presentation_currency": "USD",
    "currencies_detected": ["USD", "EUR"],
    "rate_source": "manual",
    "as_of_date": "2025-12-31",
    "manual_rates": {"EUR/USD": "1.05"},
    "rates_applied": {"EUR/USD": "1.0523"},
    "conversion_summary": "All converted",
    "currency_exposure": [],
    "decimal_precision": 4,
    "stale_rate_warnings": [],
    "missing_rate_warnings": [],
    "high_volatility_warnings": [],
    "data_quality_warnings": [],
    "manual_rate_overrides_applied": [],
    "rounding_strategy": "halfeven",
    "amounts_converted": 0,
    "convention_evidence": {},
}

CURRENCY_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Currency",
    "Conversion",
    "Conclusion",
)


def test_currency_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_currency_conversion_memo(_CURRENCY_FIXTURE)
    _assert_labels_present(pdf_bytes, CURRENCY_MEMO_REQUIRED_SECTIONS, "Currency Conversion")


# ---------------------------------------------------------------------------
# Flux Expectations Memo (ISA 520 / AU-C 520 — analytical procedures)
# ---------------------------------------------------------------------------

# Inline fixture: the generator takes plain dicts (`flux_result` + `expectations`),
# not nested Pydantic sub-models. One high-risk flagged item with practitioner
# expectation text exercises the full template path (cover, scope, expectations
# block with conclusion checkboxes, sign-off, disclaimer).
_FLUX_EXPECTATIONS_FIXTURE = {
    "flux_result": {
        "items": [
            {
                "account": "Revenue",
                "type": "Revenue",
                "current": 500000,
                "prior": 300000,
                "delta_amount": 200000,
                "delta_percent": 66.67,
                "display_percent": "66.7%",
                "is_new": False,
                "is_removed": False,
                "sign_flip": False,
                "risk_level": "high",
                "variance_indicators": ["Large % Variance"],
            },
        ],
        "summary": {
            "total_items": 1,
            "high_risk_count": 1,
            "medium_risk_count": 0,
            "new_accounts": 0,
            "removed_accounts": 0,
            "threshold": 10000,
        },
    },
    "expectations": {
        "Revenue": {
            "auditor_expectation": "Expected 15% growth based on industry trend",
            "auditor_explanation": "Actual growth exceeded due to new contract",
        },
    },
}

FLUX_EXPECTATIONS_MEMO_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Flux",  # title prefix ("ISA 520 Flux & Expectation Documentation")
    "Expectation",  # core concept; appears in title + section II
    "Scope",  # section I header
    "Variance",  # observed-variance block label
    "Conclusion",  # per-item conclusion checkbox block
    "Practitioner",  # ISA 520 disclaimer + section II header
)


def test_flux_expectations_memo_pdf_contains_all_required_section_labels() -> None:
    pdf_bytes = generate_flux_expectations_memo(
        flux_result=_FLUX_EXPECTATIONS_FIXTURE["flux_result"],
        expectations=_FLUX_EXPECTATIONS_FIXTURE["expectations"],
        client_name="Acme",
        period_tested="FY2025",
    )
    _assert_labels_present(pdf_bytes, FLUX_EXPECTATIONS_MEMO_REQUIRED_SECTIONS, "Flux Expectations")


# ---------------------------------------------------------------------------
# Shared utilities + coverage status
# ---------------------------------------------------------------------------

# Coverage: 18/18 memos (Sprint 762 closed the flux_expectations gap).
#
# When extending to new memos:
#   1. Create a `<MEMO>_REQUIRED_SECTIONS: tuple[str, ...]` constant
#      with verified labels (run the generator + extract text first).
#   2. Add a test_<memo>_pdf_contains_all_required_section_labels using
#      the same `_assert_labels_present` helper.
#
# Per ADR-016: any change to a required-section list is a schema-level
# contract change — it should land in the same PR as the generator
# change that motivated it.


def _assert_labels_present(
    pdf_bytes: bytes,
    required_labels: tuple[str, ...],
    memo_name: str,
) -> None:
    """Common assertion: every required label appears in the rendered PDF.

    Extracted to keep the per-memo test bodies one-liners. ADR-016
    contract-test pattern.
    """
    text = _extract_pdf_text(pdf_bytes)
    missing = [label for label in required_labels if label not in text]
    assert not missing, (
        f"{memo_name} memo PDF missing required section labels: {missing}. "
        f"Either the generator regressed, or the *_REQUIRED_SECTIONS constant "
        f"needs updating to match an intentional schema change."
    )


@pytest.fixture
def extract_pdf_text():
    """Pytest fixture wrapper for `_extract_pdf_text` so memo contract
    tests can request it via parameter injection if preferred."""
    return _extract_pdf_text
