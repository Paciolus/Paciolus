"""Sprint 886 / 11H (review OUT-18): memos use the client's reporting framework and say which.

``routes/export_memos.py`` passed no framework and the export models carried
no client or engagement, so every memo used FASB language — even for a client
set to GASB. Now a memo request carries the linked ``engagement_id`` (or
``client_id``); the server checks the user may see it, resolves the framework
with ``resolve_reporting_framework``, passes it to the generator, and the memo
prints which framework it used and why. With nothing linked: FASB, labelled as
the default (CEO, 2026-11-19).
"""

from __future__ import annotations

import inspect
import io
import re

import httpx
import pytest

from tests.test_sprint886_bank_rec_export import BANK_CSV, LEDGER_CSV
from tests.test_sprint886_supplemental_schedules import _ap_csv


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


@pytest.fixture
def engagements(override_auth_verified, make_client, make_engagement, db_session):
    """Two otherwise identical engagements: one FASB client, one GASB client."""
    from models import EntityType, ReportingFramework

    fasb_client = make_client(name="Acme Manufacturing", user=override_auth_verified)
    fasb_client.reporting_framework = ReportingFramework.FASB
    fasb_client.entity_type = EntityType.FOR_PROFIT
    gasb_client = make_client(name="City of Springfield", user=override_auth_verified)
    gasb_client.reporting_framework = ReportingFramework.AUTO
    gasb_client.entity_type = EntityType.GOVERNMENTAL
    db_session.flush()
    return {
        "fasb": make_engagement(client=fasb_client),
        "gasb": make_engagement(client=gasb_client),
    }


async def _ap_screen() -> dict:
    response = await _post("/audit/ap-payments", files={"file": ("ap.csv", _ap_csv(), "text/csv")})
    assert response.status_code == 200, response.text
    return response.json()


async def _bank_screen() -> dict:
    response = await _post(
        "/audit/bank-reconciliation",
        files={"bank_file": ("b.csv", BANK_CSV, "text/csv"), "ledger_file": ("l.csv", LEDGER_CSV, "text/csv")},
    )
    assert response.status_code == 200, response.text
    screen = response.json()
    screen["summary"].pop("matches")
    return screen


ROUTES = {
    "/export/ap-testing-memo": _ap_screen,
    "/export/bank-rec-memo": _bank_screen,
}


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
@pytest.mark.parametrize("route", list(ROUTES))
class TestFrameworkFollowsTheClient:
    async def test_fasb_and_gasb_engagements_get_their_own_language(self, route, engagements):
        screen = await ROUTES[route]()
        texts = {}
        for fw, eng in engagements.items():
            response = await _post(route, json={**screen, "filename": "x", "engagement_id": eng.id})
            assert response.status_code == 200, response.text
            texts[fw] = _pdf_text(response.content)

        assert re.search(r"Reporting Framework\s*\.*\s*FASB \(US GAAP\) — set on the client", texts["fasb"])
        assert re.search(r"Reporting Framework\s*\.*\s*GASB — the client is a governmental entity", texts["gasb"])
        assert "GASB" not in texts["fasb"]
        assert "GASB" in texts["gasb"].replace("Reporting Framework", "")
        # The references and scope text differ, not only the label.
        assert texts["fasb"].replace("FASB", "") != texts["gasb"].replace("GASB", "")

    async def test_nothing_linked_is_fasb_labelled_as_the_default(self, route, override_auth_verified):
        screen = await ROUTES[route]()
        text = _pdf_text((await _post(route, json={**screen, "filename": "x"})).content)
        assert re.search(
            r"Reporting Framework\s*\.*\s*FASB \(US GAAP\) — default; no client or engagement was linked to this run",
            text,
        )

    async def test_client_id_alone_resolves_too(self, route, engagements):
        screen = await ROUTES[route]()
        client_id = engagements["gasb"].client_id
        text = _pdf_text((await _post(route, json={**screen, "filename": "x", "client_id": client_id})).content)
        assert "GASB — the client is a governmental entity" in text

    async def test_someone_elses_engagement_is_refused(self, route, engagements, make_engagement):
        other = make_engagement()  # a client of another user
        screen = await ROUTES[route]()
        response = await _post(route, json={**screen, "filename": "x", "engagement_id": other.id})
        assert response.status_code == 404


def test_every_memo_generator_accepts_the_resolved_framework():
    from routes.export_memos import _FLUX_ENTRY, _SAMPLING_EVAL_ENTRY, _STANDARD_REGISTRY

    entries = [entry for entry, _ in _STANDARD_REGISTRY] + [_FLUX_ENTRY, _SAMPLING_EVAL_ENTRY]
    assert len(entries) == 18
    for entry in entries:
        assert "resolved_framework" in inspect.signature(entry.generator).parameters, entry.route_path


def test_every_memo_input_can_name_the_engagement_or_client():
    from routes.export_memos import _STANDARD_REGISTRY
    from shared.export_schemas import FluxExpectationsMemoInput, SamplingEvaluationMemoInput

    models = [model for _, model in _STANDARD_REGISTRY] + [FluxExpectationsMemoInput, SamplingEvaluationMemoInput]
    for model in models:
        assert {"engagement_id", "client_id"} <= set(model.model_fields), model.__name__
