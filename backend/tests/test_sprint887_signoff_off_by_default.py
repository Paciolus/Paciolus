"""Sprint 887 / 12H (review OUT-29): every signature block is off by default; no invented dates.

The flux expectations memo printed its sign-off table even with
``include_signoff=False``; the analytical-expectations and SUM-schedule
workpapers always printed "Auditor: ____ Date: ____"; enabled blocks filled in
today's date, the reviewer's included. Now one switch (``include_signoff``,
off by default) controls every signature block, and an enabled block shows only
the names and the date the firm supplied.
"""

from __future__ import annotations

import io
import re
from datetime import date

import pytest

TODAY_FORMS = (
    date.today().strftime("%Y-%m-%d"),
    date.today().strftime("%d %b %Y"),
    date.today().strftime("%B %d, %Y"),
    date.today().strftime("%b %d, %Y"),
)
SIGNATURE_MARKS = ("Prepared By:", "Prepared by", "Reviewed By:", "Reviewed by", "Auditor: ____", "Partner")


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


def _block(text: str, start: str) -> str:
    """The sign-off block: from ``start`` to the generation stamp that follows it."""
    return text.split(start, 1)[1].split("Generated", 1)[0]


def _body_text(text: str) -> str:
    """The memo without its cover page metadata (where "Prepared by (entered by user)" is a field)."""
    return re.sub(r"Prepared by \(entered by user\)\s*\S*", "", text)


def _flux_result() -> dict:
    return {
        "items": [
            {
                "account": "Rent Expense",
                "current_balance": 1200.0,
                "prior_balance": 1000.0,
                "variance_amount": 200.0,
                "variance_percent": 20.0,
                "risk_level": "high",
            }
        ],
        "summary": {"total_items": 1, "high_risk_count": 1, "medium_risk_count": 0, "low_risk_count": 0},
    }


def _flux(**kwargs) -> str:
    from flux_expectations_memo import generate_flux_expectations_memo

    return _body_text(_pdf_text(generate_flux_expectations_memo(_flux_result(), {}, **kwargs)))


def _testing(**kwargs) -> str:
    from je_testing_memo_generator import generate_je_testing_memo

    result = {"composite_score": {"score": 0.0, "risk_tier": "low"}, "test_results": [], "data_quality": {}}
    return _body_text(_pdf_text(generate_je_testing_memo(result, filename="j", **kwargs)))


class TestDefaultHasNoSignatureBlock:
    def test_flux_default(self):
        text = _flux(prepared_by="Ann Lee", reviewed_by="Bo Chan")
        for mark in SIGNATURE_MARKS:
            assert mark not in text, mark

    def test_testing_memo_default(self):
        text = _testing(prepared_by="Ann Lee", reviewed_by="Bo Chan")
        assert "Prepared By:" not in text and "Reviewed By:" not in text


class TestEnabledShowsOnlySuppliedNamesAndDates:
    def test_flux_enabled_without_a_date_leaves_dates_blank(self):
        text = _flux(prepared_by="Ann Lee", include_signoff=True)
        assert "Prepared by" in text and "Ann Lee" in text
        assert "Reviewed by" not in text and "Partner" not in text
        for form in TODAY_FORMS:
            assert form not in _block(text, "Prepared by")

    def test_flux_enabled_with_a_date(self):
        text = _flux(prepared_by="Ann Lee", reviewed_by="Bo Chan", workpaper_date="2026-11-02", include_signoff=True)
        tail = text.split("Prepared by", 1)[1]
        assert "Ann Lee" in tail and "2026-11-02" in tail and "Bo Chan" in tail

    def test_testing_memo_enabled_does_not_invent_a_date(self):
        text = _testing(prepared_by="Ann Lee", reviewed_by="Bo Chan", include_signoff=True)
        block = _block(text, "Prepared By:")
        assert "Ann Lee" in block and "Bo Chan" in block
        for form in TODAY_FORMS:
            assert form not in block

    def test_shared_pdf_signoff_section_leaves_reviewer_date_blank(self):
        from pdf.sections.workpaper_signoff import build_workpaper_signoff_rows

        rows = build_workpaper_signoff_rows("Ann Lee", "Bo Chan", "2026-11-02")
        assert rows == [["Prepared By:", "Ann Lee", "2026-11-02"], ["Reviewed By:", "Bo Chan", ""]]
        assert build_workpaper_signoff_rows("Ann Lee", None, None) == [["Prepared By:", "Ann Lee", ""]]


@pytest.mark.parametrize("kind", ["analytical", "sum"])
class TestEngagementWorkpapers:
    def _render(self, db_session, make_engagement, kind, **kwargs) -> str:
        if kind == "analytical":
            from analytical_expectation_memo_generator import AnalyticalExpectationMemoGenerator as Gen
        else:
            from sum_schedule_memo_generator import SumScheduleMemoGenerator as Gen
        eng = make_engagement()
        return _body_text(_pdf_text(Gen(db_session).generate_pdf(eng.created_by, eng.id, **kwargs)))

    def test_default_has_no_auditor_line(self, db_session, make_engagement, kind):
        text = self._render(db_session, make_engagement, kind)
        assert "Auditor: ____" not in text and "Date: ____" not in text

    def test_enabled_shows_supplied_name_only(self, db_session, make_engagement, kind):
        text = self._render(db_session, make_engagement, kind, include_signoff=True, prepared_by="Ann Lee")
        assert "Ann Lee" in text
        for form in TODAY_FORMS:
            assert form not in _block(text, "Ann Lee")
