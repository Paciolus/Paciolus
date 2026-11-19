"""Sprint 886 / 11G (review OUT-16): documents say where the materiality figure came from.

The trial balance page starts at the $500 software default, may take a saved
practice setting or the engagement's performance materiality, or the user types
a figure. ``resolve_materiality`` labelled every positive amount "manual", and
the export dropped the source. Now the analysis carries a ``materiality_basis``
(amount, purpose, origin) and every document prints all three.

The page says how it set the figure (``materiality_origin``: "default",
"engagement" or "entered"); the server checks each claim it can check — the
user's saved setting, the engagement's performance materiality, the software
default — and anything it cannot confirm is reported as entered for this run.
"""

from __future__ import annotations

import io
import json
import re

import httpx
import pytest

from tests.test_sprint886_tb_export_fidelity import TB_CSV


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


def _xlsx_text(data: bytes) -> str:
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(data))
    return " ".join(str(c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None)


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


async def _analyse(**form: str) -> dict:
    response = await _post(
        "/audit/trial-balance",
        files={"file": ("tb.csv", TB_CSV, "text/csv")},
        data={"force_resubmit": "true", **form},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _documents(screen: dict) -> tuple[str, str]:
    pdf = await _post("/export/pdf", json=screen)
    xlsx = await _post("/export/excel", json=screen)
    assert pdf.status_code == 200 and xlsx.status_code == 200
    return _pdf_text(pdf.content), _xlsx_text(xlsx.content)


def _save_practice_materiality(user, db_session, value: float) -> None:
    user.settings = json.dumps({"default_materiality": {"type": "fixed", "value": value}})
    db_session.flush()


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
class TestEachOriginIsNamed:
    async def test_first_use_software_default(self, override_auth_verified):
        screen = await _analyse(materiality_threshold="500", materiality_origin="default")
        assert screen["materiality_basis"] == {
            "amount": 500.0,
            "purpose": "test_threshold",
            "origin": "software_default",
        }

        pdf, xlsx = await _documents(screen)
        assert re.search(r"Materiality Threshold\s*\.*\s*\$500\.00", pdf)
        assert re.search(r"Materiality Source\s*\.*\s*Test threshold — Paciolus default", pdf)
        assert "Test threshold — Paciolus default" in xlsx

    async def test_saved_firm_setting(self, override_auth_verified, db_session):
        _save_practice_materiality(override_auth_verified, db_session, 2500.0)
        screen = await _analyse(materiality_threshold="2500", materiality_origin="default")
        assert screen["materiality_basis"]["origin"] == "firm_setting"

        pdf, xlsx = await _documents(screen)
        assert re.search(r"Materiality Threshold\s*\.*\s*\$2,500\.00", pdf)
        assert re.search(r"Materiality Source\s*\.*\s*Test threshold — Saved firm setting", pdf)
        assert "Test threshold — Saved firm setting" in xlsx

    async def test_engagement_performance_materiality(self, override_auth_verified, make_engagement):
        from engagement_model import MaterialityBasis

        eng = make_engagement(
            user=override_auth_verified, materiality_basis=MaterialityBasis.MANUAL, materiality_amount=2000.0
        )
        # The page pre-fills the engagement's performance materiality (1,500) and sends it.
        screen = await _analyse(
            materiality_threshold="1500", materiality_origin="engagement", engagement_id=str(eng.id)
        )
        assert screen["materiality_basis"] == {
            "amount": 1500.0,
            "purpose": "performance_materiality",
            "origin": "engagement",
        }

        pdf, xlsx = await _documents(screen)
        assert re.search(r"Materiality Threshold\s*\.*\s*\$1,500\.00", pdf)
        assert re.search(r"Materiality Source\s*\.*\s*Performance materiality — Engagement", pdf)
        assert "Performance materiality — Engagement" in xlsx

    async def test_entered_for_this_run(self, override_auth_verified):
        screen = await _analyse(materiality_threshold="750", materiality_origin="entered")
        assert screen["materiality_basis"]["origin"] == "entered"

        pdf, xlsx = await _documents(screen)
        assert re.search(r"Materiality Threshold\s*\.*\s*\$750\.00", pdf)
        assert re.search(r"Materiality Source\s*\.*\s*Test threshold — Entered for this run", pdf)
        assert "Test threshold — Entered for this run" in xlsx


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
class TestClaimsAreChecked:
    async def test_a_default_claim_that_matches_nothing_is_entered(self, override_auth_verified):
        screen = await _analyse(materiality_threshold="740", materiality_origin="default")
        assert screen["materiality_basis"]["origin"] == "entered"

    async def test_an_engagement_claim_with_another_amount_is_entered(self, override_auth_verified, make_engagement):
        from engagement_model import MaterialityBasis

        eng = make_engagement(
            user=override_auth_verified, materiality_basis=MaterialityBasis.MANUAL, materiality_amount=2000.0
        )
        screen = await _analyse(materiality_threshold="900", materiality_origin="engagement", engagement_id=str(eng.id))
        assert screen["materiality_basis"]["origin"] == "entered"
        assert screen["materiality_basis"]["purpose"] == "test_threshold"

    async def test_no_origin_sent_is_entered_never_default(self, override_auth_verified):
        screen = await _analyse(materiality_threshold="500")
        assert screen["materiality_basis"]["origin"] == "entered"

    async def test_engagement_fills_in_when_no_amount_is_sent(self, override_auth_verified, make_engagement):
        from engagement_model import MaterialityBasis

        eng = make_engagement(
            user=override_auth_verified, materiality_basis=MaterialityBasis.MANUAL, materiality_amount=2000.0
        )
        screen = await _analyse(engagement_id=str(eng.id))
        assert screen["materiality_basis"] == {
            "amount": 1500.0,
            "purpose": "performance_materiality",
            "origin": "engagement",
        }


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_basis_not_supplied_prints_not_available(override_auth_verified):
    screen = await _analyse(materiality_threshold="750", materiality_origin="entered")
    screen.pop("materiality_basis")
    screen.pop("materiality_source")
    pdf, _ = await _documents(screen)
    assert re.search(r"Materiality Source\s*\.*\s*Not available", pdf)
