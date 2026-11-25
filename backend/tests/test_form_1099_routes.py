"""
Form 1099 route tier-gate tests — Sprint 689e.
"""

import sys

import httpx
import pytest

sys.path.insert(0, "..")

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import User, UserTier


def _valid_payload() -> dict:
    return {
        "tax_year": 2025,
        "vendors": [
            {
                "vendor_id": "V001",
                "vendor_name": "ACME Consulting LLC",
                "tin": "12-3456789",
                "entity_type": "llc",
            }
        ],
        "payments": [
            {
                "vendor_id": "V001",
                "amount": "750.00",
                "payment_category": "nonemployee_comp",
                "payment_method": "check",
            }
        ],
    }


@pytest.fixture
def free_user(db_session):
    user = User(
        email="free_1099@example.com",
        name="Free",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.FREE,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def professional_user(db_session):
    user = User(
        email="pro_1099@example.com",
        name="Pro",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _override(user, db_session):
    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session


@pytest.mark.usefixtures("bypass_csrf")
class TestForm1099TierGate:
    @pytest.mark.asyncio
    async def test_free_tier_blocked_on_analyze(self, free_user, db_session):
        _override(free_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/form-1099", json=_valid_payload())
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "TIER_LIMIT_EXCEEDED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_free_tier_blocked_on_csv_export(self, free_user, db_session):
        _override(free_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/form-1099/export.csv", json=_valid_payload())
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "TIER_LIMIT_EXCEEDED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_professional_tier_passes_analyze(self, professional_user, db_session):
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/form-1099", json=_valid_payload())
            assert response.status_code == 200
            body = response.json()
            assert body["tax_year"] == 2025
            assert "candidates" in body
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_professional_tier_passes_csv_export(self, professional_user, db_session):
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/form-1099/export.csv", json=_valid_payload())
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/csv")
        finally:
            app.dependency_overrides.clear()


class TestSprint837ThresholdTransparency:
    """Sprint 837: the API and the CSV carry the year's thresholds, notices and
    the payees below the year's threshold."""

    @pytest.mark.asyncio
    async def test_2026_response_and_csv_carry_below_threshold_payees_and_notices(self, professional_user, db_session):
        payload = _valid_payload()
        payload["tax_year"] = 2026
        payload["payments"][0]["amount"] = "1500.00"
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                analyzed = await client.post("/audit/form-1099", json=payload)
                exported = await client.post("/audit/form-1099/export.csv", json=payload)
            assert analyzed.status_code == 200
            body = analyzed.json()
            assert body["candidates"] == []
            assert [p["vendor_id"] for p in body["below_threshold_payees"]] == ["V001"]
            assert body["notices"]
            assert body["thresholds"]["figures_from_tax_year"] == 2026

            assert exported.status_code == 200
            text = exported.text
            assert "Below the 2026 reporting threshold" in text
            assert "V001" in text
            assert "Notices" in text
            assert "Thresholds applied for tax year 2026" in text
            assert "IRS Instructions for Forms 1099-MISC" in text
        finally:
            app.dependency_overrides.clear()


class TestSprint856TaxFiguresBanner:
    """Sprint 856 (793b): the export is what gets filed, so its first line is
    the same tax-figures banner the page shows."""

    @pytest.mark.asyncio
    async def test_csv_first_line_is_tax_figures_banner(self, professional_user, db_session):
        import csv as _csv
        import io as _io

        from tax_figures_status import FORM_1099_TAX_FIGURES_BANNER

        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/form-1099/export.csv", json=_valid_payload())
            assert response.status_code == 200, response.text
            rows = list(_csv.reader(_io.StringIO(response.text)))
            assert rows[0] == [FORM_1099_TAX_FIGURES_BANNER]
            assert rows[1] == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("path", ["/audit/form-1099", "/audit/form-1099/export.csv"])
    async def test_refused_after_grace_when_not_signed_off(self, professional_user, db_session, monkeypatch, path):
        """Sprint 860: an unsigned year runs through 2026-12-15, and is refused after it."""
        from datetime import timedelta

        import tax_figures_status as tfs
        import tax_tables

        monkeypatch.setattr(tfs, "_today", lambda: tfs.UNSIGNED_GRACE_UNTIL + timedelta(days=1))
        monkeypatch.setattr(tax_tables, "is_signed_off", lambda tool, year: False)
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(path, json=_valid_payload())
            assert response.status_code == 403, response.text
            assert response.json()["detail"]["code"] == "TAX_YEAR_NOT_SIGNED_OFF"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_runs_after_grace_once_signed_off(self, professional_user, db_session, monkeypatch):
        from datetime import timedelta

        import tax_figures_status as tfs
        import tax_tables

        monkeypatch.setattr(tfs, "_today", lambda: tfs.UNSIGNED_GRACE_UNTIL + timedelta(days=1))
        monkeypatch.setattr(tax_tables, "is_signed_off", lambda tool, year: tool == "form_1099")
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/form-1099", json=_valid_payload())
            assert response.status_code == 200, response.text
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_a_year_after_the_latest_table_is_refused(self, professional_user, db_session):
        """Sprint 860: 2027 has no table; it used to reuse 2026's with a notice."""
        payload = _valid_payload()
        payload["tax_year"] = 2027
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/form-1099", json=payload)
            assert response.status_code == 400, response.text
            assert response.json()["detail"]["code"] == "TAX_YEAR_NOT_AVAILABLE"
        finally:
            app.dependency_overrides.clear()
