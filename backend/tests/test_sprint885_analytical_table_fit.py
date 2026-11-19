"""Sprint 885 / 10H (review OUT-26): the analytical-expectations schedule fits the page.

The schedule's columns added up to 7.5in on a 7in frame, so the right-hand
columns ran past the margin; on later pages the table had no header row, and
a type heading could be stranded at the foot of a page. Now the columns are
sized from the real frame width, the header row repeats on every page, and
the heading stays with the first data row.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime

import pytest
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter

LONG_LABEL = "Accrued liabilities — professional fees, legal retainers and contingent settlements " * 2


@pytest.fixture
def schedule(request):
    """A multi-page schedule: 45 expectations with long labels and wide amounts."""
    from analytical_expectations_manager import AnalyticalExpectationsManager
    from analytical_expectations_model import ExpectationTargetType
    from engagement_manager import EngagementManager

    db = request.getfixturevalue("db_session")
    user = request.getfixturevalue("make_user")()
    client = request.getfixturevalue("make_client")(user=user, name="Wide Corp")
    eng = EngagementManager(db).create_engagement(
        user.id, client.id, datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC), materiality_amount=1e9
    )
    mgr = AnalyticalExpectationsManager(db)
    for i in range(45):
        exp = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label=f"{i:02d} {LONG_LABEL}",
            expected_range_low=123_456_789_012.34,
            expected_range_high=987_654_321_098.76,
            precision_threshold_amount=55_555_555_555.55,
            corroboration_basis_text="Budget review",
            corroboration_tags=["budget", "prior_period", "industry_data"],
        )
        mgr.update_expectation(user_id=user.id, expectation_id=exp.id, result_actual_value=-999_999_999_999.99)
    return db, user, eng


def _render(schedule, monkeypatch):
    import analytical_expectation_memo_generator as gen

    tables = []
    original = gen.Table

    def capture(*args, **kwargs):
        t = original(*args, **kwargs)
        tables.append(t)
        return t

    monkeypatch.setattr(gen, "Table", capture)
    db, user, eng = schedule
    pdf = gen.AnalyticalExpectationMemoGenerator(db).generate_pdf(user.id, eng.id)
    return pdf, tables


def _runs(pdf: bytes) -> list[list[tuple[float, str]]]:
    pages = []
    for page in PdfReader(io.BytesIO(pdf)).pages:
        runs: list[tuple[float, str]] = []

        def visit(text, cm, tm, font_dict, font_size, runs=runs):
            if text.strip():
                runs.append((cm[4] + tm[4] * cm[0], text))

        page.extract_text(visitor_text=visit)
        pages.append(runs)
    return pages


def test_columns_fit_the_frame(schedule, monkeypatch):
    from shared.memo_base import MEMO_MARGINS

    _pdf, tables = _render(schedule, monkeypatch)
    frame = letter[0] - MEMO_MARGINS.left - MEMO_MARGINS.right
    schedule_tables = [t for t in tables if len(t._cellvalues[0]) == 7]
    assert schedule_tables
    for t in schedule_tables:
        assert sum(t._colWidths) <= frame + 0.01, (sum(t._colWidths), frame)
        assert t.repeatRows == 1


def test_text_stays_inside_the_margins(schedule, monkeypatch):
    from shared.memo_base import MEMO_MARGINS

    pdf, _ = _render(schedule, monkeypatch)
    right = letter[0] - MEMO_MARGINS.right
    for runs in _runs(pdf)[1:]:  # the cover is full-bleed by design
        for x, text in runs:
            assert MEMO_MARGINS.left - 1 <= x <= right, (x, text)


def test_header_row_on_every_schedule_page_and_heading_kept_with_first_row(schedule, monkeypatch):
    pdf, _ = _render(schedule, monkeypatch)
    # Whitespace removed: a wide amount wraps inside its cell.
    texts = ["".join((p.extract_text() or "").split()) for p in PdfReader(io.BytesIO(pdf)).pages]
    # Table rows carry the actual amount; the narratives after the table do not.
    table_pages = [t for t in texts if "999,999,999,999.99" in t]
    assert len(table_pages) >= 2, "the fixture must span pages"
    for t in table_pages:
        for header in ("Target", "Expected", "Threshold", "Actual", "Variance", "Status"):
            assert header in t, header
    heading_page = next(t for t in texts if "Account(45)" in t)
    assert "00Accrued" in heading_page and "999,999,999,999.99" in heading_page
