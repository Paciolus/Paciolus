"""
Sprint 856 → 860: the tax-figures banner, and the per-year sign-off gate.

1. Each banner says what the tax tables hold and which years are signed off.
2. The frontend copy (``frontend/src/content/tax-figures.ts``) matches the
   backend text verbatim, so the page and the export say the same thing.
3. Each covered tool's CSV export carries its banner as the first line (pinned
   in ``test_w2_reconciliation_routes.py`` / ``test_form_1099_routes.py``).
4. The gate: an unsigned table runs through ``UNSIGNED_GRACE_UNTIL`` (the
   council's 2026-12-15 date) and is refused after it; Form 1099 refuses a year
   after its latest table.

The season check (warn from Nov 1, fail from Jan 1) is in
``test_sprint860_tax_tables.py``.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException

import tax_figures_status as tfs
import tax_tables

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_COPY = REPO_ROOT / "frontend" / "src" / "content" / "tax-figures.ts"
FRONTEND_TRANSPORT = REPO_ROOT / "frontend" / "src" / "utils" / "transport.ts"


# ---------------------------------------------------------------------------
# 1. Each banner is true of the tables
# ---------------------------------------------------------------------------


class TestBannerMatchesTables:
    def test_w2_banner_names_the_tabulated_and_signed_off_years(self):
        assert "tax years 2025 and 2026" in tfs.W2_TAX_FIGURES_BANNER
        signed = tax_tables.signed_off_years("w2_reconciliation")
        assert f"signed off by a practitioner: {tfs._join_years(signed)}." in tfs.W2_TAX_FIGURES_BANNER
        assert "refused" in tfs.W2_TAX_FIGURES_BANNER

    def test_1099_banner_names_the_tabulated_and_signed_off_years(self):
        assert "through 2026" in tfs.FORM_1099_TAX_FIGURES_BANNER
        signed = tax_tables.signed_off_years("form_1099")
        assert f"signed off by a practitioner: {tfs._join_years(signed)}." in tfs.FORM_1099_TAX_FIGURES_BANNER
        assert "Later years are refused" in tfs.FORM_1099_TAX_FIGURES_BANNER

    def test_banner_follows_a_sign_off(self, monkeypatch):
        monkeypatch.setattr(tax_tables, "is_signed_off", lambda tool, year: year == 2026)
        assert "signed off by a practitioner: 2026." in tfs.w2_banner()
        assert "signed off by a practitioner: 2026." in tfs.form_1099_banner()

    def test_every_covered_tool_has_a_banner(self):
        assert set(tfs.TAX_FIGURES_BANNERS) == set(tfs.COVERED_TOOLS) == {"w2_reconciliation", "form_1099"}
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
    """A sign-off changes the banner: update tax-figures.ts in the same commit."""
    assert _frontend_constant(name) == backend_text


@pytest.mark.parametrize("code", ["TAX_YEAR_NOT_SIGNED_OFF", "TAX_YEAR_NOT_AVAILABLE"])
def test_frontend_maps_the_gate_codes(code):
    """#308 Codex finding: a coded refusal fell through to "Something went wrong"."""
    assert re.search(rf"^\s*{code}:", FRONTEND_TRANSPORT.read_text(encoding="utf-8"), re.MULTILINE)


# ---------------------------------------------------------------------------
# 4. The gate
# ---------------------------------------------------------------------------


def _code(exc: pytest.ExceptionInfo[HTTPException]) -> str:
    return exc.value.detail["code"]  # type: ignore[index]


class TestGate:
    @pytest.fixture
    def after_grace(self, monkeypatch):
        monkeypatch.setattr(tfs, "_today", lambda: tfs.UNSIGNED_GRACE_UNTIL + timedelta(days=1))

    @pytest.fixture
    def unsigned(self, monkeypatch):
        monkeypatch.setattr(tax_tables, "is_signed_off", lambda tool, year: False)

    @pytest.mark.parametrize("tool", ["w2_reconciliation", "form_1099"])
    def test_unsigned_runs_through_the_grace_date(self, monkeypatch, unsigned, tool):
        monkeypatch.setattr(tfs, "_today", lambda: tfs.UNSIGNED_GRACE_UNTIL)
        tfs.enforce_tax_year_signed_off(tool, 2026)

    @pytest.mark.parametrize("tool", ["w2_reconciliation", "form_1099"])
    def test_unsigned_refused_after_the_grace_date(self, after_grace, unsigned, tool):
        with pytest.raises(HTTPException) as exc:
            tfs.enforce_tax_year_signed_off(tool, 2026)
        assert exc.value.status_code == 403
        assert _code(exc) == "TAX_YEAR_NOT_SIGNED_OFF"

    def test_signed_year_runs_after_the_grace_date(self, monkeypatch, after_grace):
        monkeypatch.setattr(tax_tables, "is_signed_off", lambda tool, year: year == 2026)
        tfs.enforce_tax_year_signed_off("w2_reconciliation", 2026)
        with pytest.raises(HTTPException):
            tfs.enforce_tax_year_signed_off("w2_reconciliation", 2025)

    def test_1099_earlier_years_need_the_2025_sign_off(self, monkeypatch, after_grace):
        monkeypatch.setattr(tax_tables, "is_signed_off", lambda tool, year: year == 2025)
        assert tfs.table_year_for("form_1099", 2019) == 2025
        tfs.enforce_tax_year_signed_off("form_1099", 2019)

    def test_1099_year_after_latest_table_is_not_available(self):
        with pytest.raises(HTTPException) as exc:
            tfs.enforce_tax_year_signed_off("form_1099", 2027)
        assert exc.value.status_code == 400
        assert _code(exc) == "TAX_YEAR_NOT_AVAILABLE"

    def test_w2_year_without_a_table_is_left_to_the_engine(self, after_grace, unsigned):
        # The engine refuses it, or the caller supplied every figure.
        tfs.enforce_tax_year_signed_off("w2_reconciliation", 2027)

    def test_runnable_years(self, monkeypatch, unsigned):
        monkeypatch.setattr(tfs, "_today", lambda: tfs.UNSIGNED_GRACE_UNTIL)
        assert tfs.runnable_years("w2_reconciliation") == [2025, 2026]
        monkeypatch.setattr(tfs, "_today", lambda: tfs.UNSIGNED_GRACE_UNTIL + timedelta(days=1))
        assert tfs.runnable_years("w2_reconciliation") == []

    def test_grace_date_is_the_council_date(self):
        assert tfs.UNSIGNED_GRACE_UNTIL == date(2026, 12, 15)


class TestSignOffRecord:
    def test_a_sign_off_needs_who_when_and_final_sources(self):
        S = tax_tables.SignOff
        assert not S().is_signed
        assert not S(signed_off_by="A CPA", signed_off_on=date(2026, 12, 1), sources_final=False).is_signed
        assert not S(signed_off_by="  ", signed_off_on=date(2026, 12, 1), sources_final=True).is_signed
        assert not S(signed_off_by="A CPA", signed_off_on=None, sources_final=True).is_signed
        assert S(signed_off_by="A CPA", signed_off_on=date(2026, 12, 1), sources_final=True).is_signed

    def test_recorded_sign_offs_are_complete(self):
        for year, table in tax_tables.TABLES.items():
            for tool in tax_tables.TOOLS:
                record = table.sign_off(tool)
                if record.signed_off_by or record.signed_off_on:
                    assert record.is_signed, f"{year} {tool}: a partial sign-off record"
