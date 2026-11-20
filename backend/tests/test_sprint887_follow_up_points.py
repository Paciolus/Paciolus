"""Sprint 887 / 12F (review OUT-21): the engagement indicator is points, every band is reachable.

The anomaly summary computed ``high*3 + medium*2 + low`` plus a coverage
penalty — an unbounded count — and printed it as "{tier} ({score}/100)" under
"Engagement Risk Indicator", with a High tier no input could reach. Decided
(CEO, 2026-11-20): it is "Follow-Up Item Points", printed as points with no
/100; bands "Under 8 points", "8–14 points", "15 points or more", by points
alone; no risk or testing-tier words; weights and band edges printed.
"""

from __future__ import annotations

import io
import re

import pytest

from anomaly_summary_generator import POINT_BANDS, _compute_follow_up_points
from engagement_model import ToolName, ToolRun, ToolRunStatus
from follow_up_items_model import FollowUpSeverity

TIER_WORDS = ("LOW", "MODERATE", "ELEVATED", "HIGH RISK", "/100", "Risk Indicator", "Risk Assessment")


@pytest.mark.parametrize(
    "high,medium,low,not_run,points,band",
    [
        (0, 0, 0, 0, 0, "Under 8 points"),  # zero items
        (0, 0, 0, 5, 7, "Under 8 points"),  # coverage penalty only: int(5 * 1.5) = 7
        (0, 0, 0, 6, 9, "8–14 points"),  # coverage penalty only, next band
        (0, 0, 7, 0, 7, "Under 8 points"),  # edge: 7
        (0, 4, 0, 0, 8, "8–14 points"),  # edge: 8
        (4, 1, 0, 0, 14, "8–14 points"),  # edge: 14
        (5, 0, 0, 0, 15, "15 points or more"),  # edge: 15
        (1, 0, 0, 0, 3, "Under 8 points"),  # one high item no longer forces a band
        (3, 0, 0, 0, 9, "8–14 points"),  # three high items no longer force the top band
        (400, 250, 900, 18, 2627, "15 points or more"),  # a large count
    ],
)
def test_points_and_band(high, medium, low, not_run, points, band):
    assert _compute_follow_up_points(high, medium, low, not_run) == (points, band)


def test_every_band_is_reachable():
    reached = {_compute_follow_up_points(0, 0, n, 0)[1] for n in range(0, 40)}
    assert reached == {label for _, label in POINT_BANDS}


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


def test_memo_prints_points_weights_and_band_edges(db_session, make_engagement, make_follow_up_item):
    from anomaly_summary_generator import AnomalySummaryGenerator

    eng = make_engagement()
    db_session.add(
        ToolRun(engagement_id=eng.id, tool_name=ToolName.AP_TESTING, run_number=1, status=ToolRunStatus.COMPLETED)
    )
    for sev in (FollowUpSeverity.HIGH, FollowUpSeverity.HIGH, FollowUpSeverity.MEDIUM):
        make_follow_up_item(engagement=eng, tool_source="ap_testing", severity=sev)
    db_session.flush()
    text = _pdf_text(AnomalySummaryGenerator(db_session).generate_pdf(eng.created_by, eng.id))

    # 2 high * 3 + 1 medium * 2 + int(17 tools not run * 1.5) = 8 + 25 = 33.
    assert "Follow-Up Item Points: 33 points (band: 15 points or more)" in text
    assert "3 per high-severity, 2 per medium-severity and 1 per low-severity captured follow-up item" in text
    assert "1.5 per catalog tool not run" in text
    assert "Bands: under 8 points | 8–14 points | 15 points or more" in text
    for word in TIER_WORDS:
        assert not re.search(rf"(?<![A-Z-]){re.escape(word)}(?![A-Z])", text), word
