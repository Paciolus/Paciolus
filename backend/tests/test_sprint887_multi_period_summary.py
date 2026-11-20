"""Sprint 887 / 12A (review OUT-07): the multi-period memo states results, not audit conclusions.

A Low score printed "Account balances are consistent with prior period
expectations. No additional substantive procedures are indicated." even when
movements were flagged; the other tiers recommended procedures. The summary now
states the score and tier, the movement counts and the thresholds applied, and
hands over to the auditor. It says nothing about whether more work is needed.
"""

from __future__ import annotations

import io

import httpx
import pytest

# Conclusion wording the memo must never print, whatever the tier.
CONCLUSIONS = (
    "consistent with prior period expectations",
    "No additional substantive procedures",
    "procedures are indicated",
    "procedures are recommended",
    "should be corroborated",
    "require focused investigation",
    "potential misstatement risk",
    "expanded substantive procedures",
)

PRIOR = [
    {"account": "Cash", "debit": 50000, "credit": 0, "type": "asset"},
    {"account": "Accounts Receivable", "debit": 20000, "credit": 0, "type": "asset"},
    {"account": "Office Supplies Expense", "debit": 1000, "credit": 0, "type": "expense"},
    {"account": "Sales Revenue", "debit": 0, "credit": 71000, "type": "revenue"},
]
# Accounts Receivable moves 15% ($3,000): significant on the percentage rule, below $10,000.
CURRENT = [
    {"account": "Cash", "debit": 50100, "credit": 0, "type": "asset"},
    {"account": "Accounts Receivable", "debit": 23000, "credit": 0, "type": "asset"},
    {"account": "Office Supplies Expense", "debit": 1000, "credit": 0, "type": "expense"},
    {"account": "Sales Revenue", "debit": 0, "credit": 74100, "type": "revenue"},
]


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


def _page_body(screen: dict) -> dict:
    """What useMultiPeriodMemoExport sends."""
    return {
        "prior_label": screen["prior_label"],
        "current_label": screen["current_label"],
        "total_accounts": screen["total_accounts"],
        "movements_by_type": screen["movements_by_type"],
        "movements_by_significance": screen["movements_by_significance"],
        "significant_movements": screen["significant_movements"],
        "lead_sheet_summaries": [],
        "dormant_account_count": len(screen["dormant_accounts"]),
        "dormant_accounts": screen["dormant_accounts"],
        "active_thresholds": screen["active_thresholds"],
        "filename": "mp",
    }


def _assert_no_conclusion(text: str) -> None:
    lowered = text.lower()
    for phrase in CONCLUSIONS:
        assert phrase.lower() not in lowered, phrase


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestMultiPeriodSummaryThroughRoutes:
    async def _screen(self, prior: list, current: list, materiality: float = 0.0) -> dict:
        response = await _post(
            "/audit/compare-periods",
            json={
                "prior_accounts": prior,
                "current_accounts": current,
                "prior_label": "FY24",
                "current_label": "FY25",
                "materiality_threshold": materiality,
            },
        )
        assert response.status_code == 200, response.text
        return response.json()

    async def _memo(self, body: dict) -> str:
        response = await _post("/export/multi-period-memo", json=body)
        assert response.status_code == 200, response.text
        return _pdf_text(response.content)

    async def test_low_score_with_a_flagged_movement_states_counts_and_thresholds(self):
        screen = await self._screen(PRIOR, CURRENT, materiality=25000)
        assert screen["movements_by_significance"]["significant"] >= 1
        assert screen["active_thresholds"]["materiality_threshold"] == 25000
        text = await self._memo(_page_body(screen))
        _assert_no_conclusion(text)
        assert "LOW" in text
        significant = screen["movements_by_significance"]["significant"]
        assert f"{significant} significant" in text
        # Thresholds the engine applied, as numbers.
        assert "10.0%" in text and "$10,000.00" in text and "$25,000.00" in text
        assert "The auditor evaluates these results" in text

    async def test_low_score_with_nothing_flagged(self):
        screen = await self._screen(PRIOR, PRIOR)
        assert screen["movements_by_significance"]["significant"] == 0
        text = await self._memo(_page_body(screen))
        _assert_no_conclusion(text)
        assert "0 material, 0 significant" in text
        # No materiality threshold was supplied: say so, never $0.00.
        assert "Materiality threshold: none supplied" in text

    async def test_thresholds_not_sent_print_not_available(self):
        screen = await self._screen(PRIOR, CURRENT)
        body = _page_body(screen)
        del body["active_thresholds"]
        text = await self._memo(body)
        _assert_no_conclusion(text)
        assert "Significance thresholds: Not available" in text


@pytest.mark.parametrize("tier,score", [("low", 4.0), ("moderate", 18.0), ("elevated", 40.0), ("high", 75.0)])
def test_no_tier_states_a_conclusion(tier: str, score: float):
    from multi_period_memo_generator import generate_multi_period_memo

    pdf = generate_multi_period_memo(
        {
            "total_accounts": 4,
            "movements_by_significance": {"material": 1, "significant": 2, "minor": 1},
            "movements_by_type": {"increase": 3, "decrease": 1},
            "significant_movements": [],
            "composite": {"score": score, "risk_tier": tier},
            "active_thresholds": {"significant_variance_percent": 10.0, "significant_variance_amount": 10000.0},
        }
    )
    text = _pdf_text(pdf)
    _assert_no_conclusion(text)
    assert f"{score:.1f}" in text
    assert "1 material, 2 significant, 1 minor" in text
