"""
Sprint 856 (793b): the tax-figures banner, and the council's hard date.

Four things are pinned here:

1. Each banner says what its engine's tables actually hold. If a table gains or
   loses a year, the banner test fails so the wording is revisited, not left
   stale.
2. The frontend copy (``frontend/src/content/tax-figures.ts``) matches the
   backend text verbatim, so the page and the export say the same thing.
3. Each covered tool's CSV export carries its banner as the first line (pinned
   in ``test_w2_reconciliation_routes.py`` / ``test_form_1099_routes.py``).
4. The council deadline: after ``PRACTITIONER_CONFIRMATION_DEADLINE`` a covered
   tool with no recorded practitioner confirmation fails
   ``test_council_deadline_2026_figures_confirmed_or_tools_disabled``. That test
   reads the real date on purpose. It cannot fail before the deadline, and its
   failure message says exactly what the decision requires.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

import tax_figures_status as tfs
from form_1099_engine import THRESHOLDS_BY_TABLE_YEAR, FormType
from w2_reconciliation_engine import STATUTORY_LIMITS_BY_YEAR

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_COPY = REPO_ROOT / "frontend" / "src" / "content" / "tax-figures.ts"


# ---------------------------------------------------------------------------
# 1. Each banner is true of its engine
# ---------------------------------------------------------------------------


class TestBannerMatchesTables:
    def test_w2_banner_claims_2025_only_and_the_table_is_2025_only(self):
        assert sorted(STATUTORY_LIMITS_BY_YEAR) == [2025], (
            "W-2 statutory tables changed. Rewrite W2_TAX_FIGURES_BANNER (backend/tax_figures_status.py and "
            "frontend/src/content/tax-figures.ts) to match the years now tabulated, then update this test."
        )
        assert "tax year 2025 only" in tfs.W2_TAX_FIGURES_BANNER
        assert "refused" in tfs.W2_TAX_FIGURES_BANNER

    def test_1099_banner_claims_through_2026_and_the_tables_are_2025_and_2026(self):
        assert sorted(THRESHOLDS_BY_TABLE_YEAR) == [2025, 2026], (
            "Form 1099 threshold tables changed. Rewrite FORM_1099_TAX_FIGURES_BANNER (backend and frontend) "
            "to match the years now tabulated, then update this test."
        )
        assert "through tax year 2026" in tfs.FORM_1099_TAX_FIGURES_BANNER
        # The banner says the 2026 figures are from secondary sources; the table must still say so.
        nec_2026 = next(i for i in THRESHOLDS_BY_TABLE_YEAR[2026] if i.form_type == FormType.NEC)
        assert nec_2026.amount == Decimal("2000")
        assert "secondary sources" in nec_2026.basis

    def test_every_covered_tool_has_a_banner_and_a_confirmation_slot(self):
        assert (
            set(tfs.TAX_FIGURES_BANNERS)
            == set(tfs.PRACTITIONER_CONFIRMATIONS)
            == {
                "w2_reconciliation",
                "form_1099",
            }
        )
        for banner in tfs.TAX_FIGURES_BANNERS.values():
            assert banner.endswith("Verify before relying.")


# ---------------------------------------------------------------------------
# 2. Frontend copy matches
# ---------------------------------------------------------------------------


def _frontend_constant(name: str) -> str:
    text = FRONTEND_COPY.read_text(encoding="utf-8")
    match = re.search(rf"export const {name}\s*=\s*'([^']*)'", text)
    assert match, f"{name} not found as a single-quoted string in {FRONTEND_COPY}"
    return match.group(1)


@pytest.mark.parametrize(
    "name, backend_text",
    [
        ("W2_TAX_FIGURES_BANNER", tfs.W2_TAX_FIGURES_BANNER),
        ("FORM_1099_TAX_FIGURES_BANNER", tfs.FORM_1099_TAX_FIGURES_BANNER),
    ],
)
def test_frontend_banner_matches_backend(name, backend_text):
    assert _frontend_constant(name) == backend_text


# ---------------------------------------------------------------------------
# 4. The council's hard date
# ---------------------------------------------------------------------------


class TestDeadlineLogic:
    """The overdue check, exercised at dates relative to the deadline."""

    def test_nothing_overdue_on_or_before_deadline(self, monkeypatch):
        monkeypatch.setattr(tfs, "PRACTITIONER_CONFIRMATIONS", {"w2_reconciliation": None, "form_1099": None})
        deadline = tfs.PRACTITIONER_CONFIRMATION_DEADLINE
        assert tfs.tools_overdue_for_confirmation(deadline - timedelta(days=30)) == []
        assert tfs.tools_overdue_for_confirmation(deadline) == []

    def test_unconfirmed_tools_overdue_after_deadline(self, monkeypatch):
        monkeypatch.setattr(tfs, "PRACTITIONER_CONFIRMATIONS", {"w2_reconciliation": None, "form_1099": None})
        after = tfs.PRACTITIONER_CONFIRMATION_DEADLINE + timedelta(days=1)
        assert tfs.tools_overdue_for_confirmation(after) == ["form_1099", "w2_reconciliation"]

    def test_confirmed_tool_not_overdue(self, monkeypatch):
        confirmation = tfs.PractitionerConfirmation(
            confirmed_by="Example CPA", confirmed_on=date.today(), tax_year=2026
        )
        monkeypatch.setattr(tfs, "PRACTITIONER_CONFIRMATIONS", {"w2_reconciliation": confirmation, "form_1099": None})
        after = tfs.PRACTITIONER_CONFIRMATION_DEADLINE + timedelta(days=1)
        assert tfs.tools_overdue_for_confirmation(after) == ["form_1099"]

    def test_recorded_confirmations_are_for_2026(self):
        for tool, confirmation in tfs.PRACTITIONER_CONFIRMATIONS.items():
            if confirmation is not None:
                assert confirmation.tax_year == 2026, tool
                assert confirmation.confirmed_by.strip(), tool


def test_council_deadline_2026_figures_confirmed_or_tools_disabled():
    """Reads the real date deliberately — this is the hard date, not a fixture.

    Passes on or before 2026-12-15 regardless of state. After it, fails for each
    covered tool whose 2026 figures no practitioner has confirmed.
    """
    overdue = tfs.tools_overdue_for_confirmation(date.today())
    assert not overdue, (
        f"COUNCIL DECISION (2026-10-28, Sprint 856 item 5 / Sprint 793b): the deadline "
        f"{tfs.PRACTITIONER_CONFIRMATION_DEADLINE.isoformat()} has passed and no practitioner has confirmed "
        f"the 2026 statutory figures for: {', '.join(overdue)}. The decision is to DISABLE these tools "
        f"unless a practitioner has confirmed the 2026 figures. Do one of: (a) record the practitioner's "
        f"confirmation in backend/tax_figures_status.py PRACTITIONER_CONFIRMATIONS (and add the confirmed "
        f"tables), or (b) disable the tools and remove them from PRACTITIONER_CONFIRMATIONS / "
        f"TAX_FIGURES_BANNERS in the same change. Do not move the deadline without a council decision."
    )
