"""Sprint 887 / 12E (review OUT-20): the anomaly summary reports each tool's real state.

A tool counted as "clean" when it had any run (failed runs included) and no
follow-up item, and the page printed "No anomalies identified. Population
passed all configured test thresholds." under "Tools with Clean Results". A
flagged run whose items were never captured looked clean. Now each catalog tool
is described from its latest successful run and that run's recorded flag count:
failed, not evaluated, results unavailable, no exceptions flagged, or n items
flagged — with the captured follow-up items counted separately.

Section III printed "Assessments Completed: 0" with blank fields even when
dispositions were saved. By default it is now a blank worksheet for the firm to
complete; ``fill_from_saved`` fills it from the dispositions and notes saved in
Paciolus, each with the date it was recorded.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime, timedelta

from engagement_model import ToolName, ToolRun, ToolRunStatus
from follow_up_items_model import FollowUpDisposition, FollowUpSeverity

OLD_WORDING = ("Clean Results", "passed all configured", "No anomalies identified", "Assessments Completed: 0")


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


def _run(db, eng, tool, n, status, flag_count, days_ago):
    run = ToolRun(
        engagement_id=eng.id,
        tool_name=tool,
        run_number=n,
        status=status,
        flag_count=flag_count,
        run_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_ago),
    )
    db.add(run)
    db.flush()
    return run


def _status_line(text: str, tool_label: str) -> str:
    """The tool's row in the Tool Results table."""
    table = text.split("Tool Results", 1)[1]
    return table.split(tool_label, 1)[1][:160]


def _render(db_session, eng, **kwargs) -> str:
    from anomaly_summary_generator import AnomalySummaryGenerator

    return _pdf_text(AnomalySummaryGenerator(db_session).generate_pdf(eng.created_by, eng.id, **kwargs))


class TestToolStates:
    def test_each_state_prints_differently(self, db_session, make_engagement, make_follow_up_item):
        eng = make_engagement()
        # Only failed runs.
        _run(db_session, eng, ToolName.AP_TESTING, 1, ToolRunStatus.FAILED, None, 3)
        _run(db_session, eng, ToolName.AP_TESTING, 2, ToolRunStatus.FAILED, None, 2)
        # A flagged run whose items were never captured as follow-up items.
        _run(db_session, eng, ToolName.PAYROLL_TESTING, 1, ToolRunStatus.COMPLETED, 7, 2)
        # A rerun: the earlier run flagged 5, the latest successful run flagged none,
        # and a failed run after it does not replace it.
        _run(db_session, eng, ToolName.JOURNAL_ENTRY_TESTING, 1, ToolRunStatus.COMPLETED, 5, 5)
        _run(db_session, eng, ToolName.JOURNAL_ENTRY_TESTING, 2, ToolRunStatus.COMPLETED, 0, 3)
        _run(db_session, eng, ToolName.JOURNAL_ENTRY_TESTING, 3, ToolRunStatus.FAILED, None, 1)
        # A true zero-flag run.
        _run(db_session, eng, ToolName.INVENTORY_TESTING, 1, ToolRunStatus.COMPLETED, 0, 1)
        # A run recorded before flag counts were stored.
        _run(db_session, eng, ToolName.AR_AGING, 1, ToolRunStatus.COMPLETED, None, 1)
        make_follow_up_item(engagement=eng, tool_source="ap_testing", description="Captured from an earlier export")

        text = _render(db_session, eng)
        for phrase in OLD_WORDING:
            assert phrase not in text, phrase

        assert _status_line(text, "AP Payment Testing").startswith(" Failed")
        assert "7 items flagged" in _status_line(text, "Payroll")
        assert "0 captured follow-up items" in _status_line(text, "Payroll")
        assert "No exceptions flagged" in _status_line(text, "Journal Entry")
        assert "No exceptions flagged" in _status_line(text, "Inventory")
        assert "Results unavailable" in _status_line(text, "AR Aging")
        assert "Not evaluated" in _status_line(text, "Fixed Asset")

    def test_follow_up_counts_are_called_captured_follow_up_items(
        self, db_session, make_engagement, make_follow_up_item
    ):
        eng = make_engagement()
        _run(db_session, eng, ToolName.AP_TESTING, 1, ToolRunStatus.COMPLETED, 2, 1)
        make_follow_up_item(engagement=eng, tool_source="ap_testing", severity=FollowUpSeverity.HIGH)
        text = _render(db_session, eng)
        assert "Captured Follow-Up Items: 1" in text
        assert "Total Anomalies" not in text


class TestWorksheet:
    def test_default_is_a_blank_worksheet_for_the_firm(self, db_session, make_engagement, make_follow_up_item):
        eng = make_engagement()
        make_follow_up_item(
            engagement=eng,
            tool_source="ap_testing",
            disposition=FollowUpDisposition.INVESTIGATED_NO_ISSUE,
            auditor_notes="Vendor confirmed the credit memo.",
        )
        text = _render(db_session, eng)
        assert "Practitioner Worksheet" in text and "for the firm to complete" in text
        assert "Vendor confirmed the credit memo." not in text
        assert "Assessments Completed" not in text

    def test_fill_from_saved_shows_dispositions_notes_and_dates(self, db_session, make_engagement, make_follow_up_item):
        eng = make_engagement()
        reviewed = make_follow_up_item(
            engagement=eng,
            tool_source="ap_testing",
            disposition=FollowUpDisposition.INVESTIGATED_NO_ISSUE,
            auditor_notes="Vendor confirmed the credit memo.",
        )
        reviewed.updated_at = datetime(2026, 11, 3, 15, 0)
        make_follow_up_item(engagement=eng, tool_source="ap_testing", description="Second item")
        db_session.flush()

        text = _render(db_session, eng, fill_from_saved=True)
        assert "Vendor confirmed the credit memo." in text
        assert "Investigated — No Issue" in text
        assert "recorded in Paciolus on Nov 03, 2026" in text
        assert "Dispositions recorded in Paciolus: 1 of 2" in text
        assert "Not Reviewed" in text
