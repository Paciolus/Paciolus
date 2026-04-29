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

from ap_testing_memo_generator import generate_ap_testing_memo
from je_testing_memo_generator import generate_je_testing_memo
from payroll_testing_memo_generator import generate_payroll_testing_memo
from revenue_testing_memo_generator import generate_revenue_testing_memo

# Reuse existing memo fixture builders so contract tests stay anchored
# to the same input schemas the unit tests use.
from tests.test_ap_testing_memo import _make_ap_result
from tests.test_je_testing_memo import _make_je_result
from tests.test_payroll_testing_memo import _make_payroll_result
from tests.test_revenue_testing_memo import _make_revenue_result


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
# Shared utilities for follow-up memo contract tests
# ---------------------------------------------------------------------------

# When extending to additional memos:
#
#   1. Create a `<MEMO>_REQUIRED_SECTIONS: tuple[str, ...]` constant with
#      the section labels that MUST appear in the rendered PDF.
#   2. Add a test_<memo>_pdf_contains_all_required_section_labels using
#      the same shape as the JE / AP / Payroll / Revenue tests above.
#      `_extract_pdf_text` is exposed as a module-level helper.
#
# Per ADR-016: any change to a required-section list is a schema-level
# contract change — it should land in the same PR as the generator change
# that motivated it, with a brief note in the PR description.
#
# Coverage today (4/18 memos): JE, AP, Payroll, Revenue. Remaining 14
# memos (AR aging, fixed assets, inventory, three-way match, multi-period,
# bank rec, sampling design, sampling evaluation, preflight, population
# profile, expense category, accrual completeness, currency conversion,
# flux expectations) follow the same pattern when their generator gets
# touched.


@pytest.fixture
def extract_pdf_text():
    """Pytest fixture wrapper for `_extract_pdf_text` so memo contract
    tests can request it via parameter injection if preferred."""
    return _extract_pdf_text
