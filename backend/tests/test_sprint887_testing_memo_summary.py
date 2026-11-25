"""Sprint 887 / 12C (review OUT-13): a testing memo's summary agrees with what the tests flagged.

The seven testing memos chose their summary from the risk tier alone, and each
Low text said "No anomalies exceeding the configured thresholds were detected"
— yet a Low score can carry flagged items. The other tiers told the auditor
what to review or investigate. Now one summary, built from the results, gives
the score and the counts; "no exceptions flagged" is printed only when the
executed tests flagged nothing; and the summary hands over to the auditor.
"""

from __future__ import annotations

import io
import re

import httpx
import pytest

from tests.test_sprint886_supplemental_schedules import _ap_csv

# Wording no tier may print any more.
OLD_TIER_TEXT = (
    "anomalies exceeding the configured thresholds",
    "require detailed investigation",
    "warrant focused review",
    "should be reviewed",
    "should evaluate whether additional procedures",
)


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


def _summary(text: str) -> str:
    """The Summary of Results paragraph (up to the limitations section)."""
    tail = text.split("Summary of Results", 1)[1]
    return tail.split("Limitations", 1)[0]


def _generators():
    from ap_testing_memo_generator import generate_ap_testing_memo
    from ar_aging_memo_generator import generate_ar_aging_memo
    from fixed_asset_testing_memo_generator import generate_fixed_asset_testing_memo
    from inventory_testing_memo_generator import generate_inventory_testing_memo
    from je_testing_memo_generator import generate_je_testing_memo
    from payroll_testing_memo_generator import generate_payroll_testing_memo
    from revenue_testing_memo_generator import generate_revenue_testing_memo

    return {
        "je": (generate_je_testing_memo, "GL lines"),  # Sprint 869: JE counts GL lines
        "ap": (generate_ap_testing_memo, "payments"),
        "payroll": (generate_payroll_testing_memo, "entries"),
        "revenue": (generate_revenue_testing_memo, "entries"),
        "ar": (generate_ar_aging_memo, "items"),
        "fixed_asset": (generate_fixed_asset_testing_memo, "assets"),
        "inventory": (generate_inventory_testing_memo, "items"),
    }


TOOLS = ["je", "ap", "payroll", "revenue", "ar", "fixed_asset", "inventory"]


def _result(tier: str, score: float, flagged: int, high: int = 0, medium: int = 0, low: int = 0) -> dict:
    tests = [
        {
            "test_name": "Alpha Test",
            "test_key": "alpha_test",
            "test_tier": "structural",
            "entries_flagged": flagged,
            "total_entries": 200,
            "flag_rate": flagged / 200,
            "severity": "low",
            "description": "Alpha",
            "flagged_entries": [],
        },
        {
            "test_name": "Beta Test",
            "test_key": "beta_test",
            "test_tier": "structural",
            "entries_flagged": 0,
            "total_entries": 200,
            "flag_rate": 0.0,
            "severity": "low",
            "description": "Beta",
            "flagged_entries": [],
        },
    ]
    return {
        "composite_score": {
            "score": score,
            "risk_tier": tier,
            "tests_run": 2,
            "total_entries": 200,
            "total_flagged": flagged,
            "flag_rate": flagged / 200,
            "flags_by_severity": {"high": high, "medium": medium, "low": low},
            "top_findings": [],
        },
        "test_results": tests,
        "data_quality": {"completeness_score": 100.0, "total_rows": 200},
    }


@pytest.mark.parametrize("tool", TOOLS)
def test_low_with_flags_gives_counts_and_never_says_no_exceptions(tool: str):
    generate, units = _generators()[tool]
    text = _pdf_text(generate(_result("low", 3.2, flagged=3, low=4), filename="t"))
    summary = _summary(text)
    assert "LOW" in summary and "3.2 of 100" in summary
    assert f"1 of 2 tests executed flagged 3 distinct {units} (4 flags: 0 high, 0 medium, 4 low severity)" in summary
    # (The Proof Summary's per-test count "Tests with no exceptions flagged" is a different, true figure.)
    assert "no exceptions flagged" not in summary.lower()
    for phrase in OLD_TIER_TEXT:
        assert phrase not in text, phrase
    assert "The auditor evaluates these results." in summary


@pytest.mark.parametrize("tool", TOOLS)
def test_low_with_nothing_flagged_says_no_exceptions_flagged(tool: str):
    generate, units = _generators()[tool]
    text = _pdf_text(generate(_result("low", 0.0, flagged=0), filename="t"))
    summary = _summary(text)
    assert f"No exceptions flagged: the 2 tests executed flagged no {units}." in summary
    for phrase in OLD_TIER_TEXT:
        assert phrase not in text, phrase


@pytest.mark.parametrize("tier,score", [("moderate", 18.0), ("elevated", 40.0), ("high", 70.0)])
def test_other_tiers_state_counts_not_directions(tier: str, score: float):
    generate, _ = _generators()["je"]
    text = _pdf_text(generate(_result(tier, score, flagged=20, high=5, medium=10, low=5), filename="t"))
    summary = _summary(text)
    assert tier.upper() in summary and "1 of 2 tests executed flagged 20 distinct GL lines" in summary
    for phrase in OLD_TIER_TEXT:
        assert phrase not in text, phrase


def test_results_not_sent_say_not_available():
    generate, _ = _generators()["je"]
    result = _result("low", 0.0, flagged=0)
    result["test_results"] = []
    summary = _summary(_pdf_text(generate(result, filename="t")))
    assert "Test results: Not available." in summary
    assert "no exceptions flagged" not in summary.lower()


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
async def test_real_ap_run_summary_matches_its_counts():
    response = await _post("/audit/ap-payments", files={"file": ("ap.csv", _ap_csv(), "text/csv")})
    assert response.status_code == 200, response.text
    screen = response.json()
    composite = screen["composite_score"]
    assert composite["total_flagged"] > 0
    memo = await _post("/export/ap-testing-memo", json={**screen, "filename": "ap"})
    assert memo.status_code == 200, memo.text
    summary = _summary(_pdf_text(memo.content))
    flags = sum(composite["flags_by_severity"].values())
    assert re.search(rf"flagged {composite['total_flagged']} distinct payments \({flags} flags", summary), summary
    assert "no exceptions flagged" not in summary.lower()
