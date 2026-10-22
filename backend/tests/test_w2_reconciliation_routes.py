"""
W-2 Reconciliation route tier-gate tests — Sprint 689d.

The engine has its own tests in `test_w2_reconciliation_engine.py`;
this file covers the route-layer gating added when the tool was
promoted to a standalone frontend page.
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
        "employees": [
            {
                "employee_id": "E001",
                "employee_name": "Alice",
                "federal_wages": "80000.00",
                "federal_withholding": "12000.00",
                "ss_wages": "80000.00",
                "ss_tax_withheld": "4960.00",
                "medicare_wages": "80000.00",
                "medicare_tax_withheld": "1160.00",
            }
        ],
        "w2_drafts": [],
        "form_941_quarters": [],
        "tolerance": "1.00",
    }


@pytest.fixture
def free_user(db_session):
    user = User(
        email="free_w2@example.com",
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
        email="pro_w2@example.com",
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
class TestW2ReconciliationTierGate:
    @pytest.mark.asyncio
    async def test_free_tier_blocked_on_analyze(self, free_user, db_session):
        _override(free_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation", json=_valid_payload())
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "TIER_LIMIT_EXCEEDED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_free_tier_blocked_on_csv_export(self, free_user, db_session):
        _override(free_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation/export.csv", json=_valid_payload())
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "TIER_LIMIT_EXCEEDED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_professional_tier_passes_analyze(self, professional_user, db_session):
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation", json=_valid_payload())
            assert response.status_code == 200
            body = response.json()
            assert body["tax_year"] == 2025
            assert "w3_totals" in body
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_professional_tier_passes_csv_export(self, professional_user, db_session):
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation/export.csv", json=_valid_payload())
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/csv")
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sprint 793a — the statutory-limit overrides the API never exposed
# ---------------------------------------------------------------------------
#
# `W2ReconciliationConfig` has had a field for every limit since Sprint 636, and
# that sprint's record states "All thresholds are caller-overridable via
# `W2ReconciliationConfig`". True in the engine and unreachable through the API
# — the request model exposed none of them, so the claim was false where it
# mattered and nothing tested it. These tests exist because that is exactly the
# shape of claim this repo keeps getting wrong: a capability that is real one
# layer down and absent at the layer a customer touches.


def _payload_over_ss_base(ss_wages: str) -> dict:
    """One employee whose SS wages sit between two candidate wage bases."""
    return {
        "tax_year": 2026,
        "employees": [
            {
                "employee_id": "E001",
                "employee_name": "Alice",
                "federal_wages": ss_wages,
                "federal_withholding": "0.00",
                "ss_wages": ss_wages,
                "ss_tax_withheld": "0.00",
                "medicare_wages": ss_wages,
                "medicare_tax_withheld": "0.00",
            }
        ],
        "w2_drafts": [],
        "form_941_quarters": [],
        "tolerance": "1.00",
    }


def _ss_base_findings(body: dict) -> list[dict]:
    return [d for d in body["employee_discrepancies"] if d["kind"] == "ss_wage_base_exceeded"]


@pytest.mark.usefixtures("bypass_csrf")
class TestStatutoryLimitOverrides:
    @pytest.mark.asyncio
    async def test_wages_above_the_default_base_are_flagged_without_an_override(self, professional_user, db_session):
        """Baseline: $180,000 exceeds the engine's built-in $176,100 base."""
        _override(professional_user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation", json=_payload_over_ss_base("180000.00"))
            assert response.status_code == 200, response.text
            assert len(_ss_base_findings(response.json())) == 1
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_an_override_reaches_the_engine_and_changes_the_finding(self, professional_user, db_session):
        """The whole point: a caller-supplied base must actually be applied.

        $180,000 is over the built-in $176,100 and under $184,500, so raising
        the base has to make the finding disappear. If the override were
        silently dropped — the pre-Sprint-793a behaviour — this still returns
        one finding and the test fails.
        """
        _override(professional_user, db_session)
        try:
            payload = _payload_over_ss_base("180000.00")
            payload["statutory_limits"] = {"ss_wage_base": "184500.00"}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation", json=payload)
            assert response.status_code == 200, response.text
            assert _ss_base_findings(response.json()) == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_lowering_the_base_creates_a_finding(self, professional_user, db_session):
        """Both directions, so the test cannot pass by the override being ignored
        in a way that happens to match the expectation."""
        _override(professional_user, db_session)
        try:
            payload = _payload_over_ss_base("150000.00")  # under the default base
            payload["statutory_limits"] = {"ss_wage_base": "140000.00"}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation", json=payload)
            assert response.status_code == 200, response.text
            findings = _ss_base_findings(response.json())
            assert len(findings) == 1
            assert findings[0]["expected"] == "140000.00"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_omitted_fields_keep_the_engine_default(self, professional_user, db_session):
        """Supplying one limit must not blank the other ten.

        The construction forwards only the fields the caller set; a naive
        `**model_dump()` would pass `None` for everything else and override the
        dataclass defaults with nulls.
        """
        _override(professional_user, db_session)
        try:
            payload = _payload_over_ss_base("180000.00")
            payload["statutory_limits"] = {"hsa_family_limit": "8750.00"}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation", json=payload)
            assert response.status_code == 200, response.text
            # ss_wage_base was not supplied, so the default still applies and
            # $180,000 is still over it.
            assert len(_ss_base_findings(response.json())) == 1
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_a_malformed_override_is_a_400_not_a_500(self, professional_user, db_session):
        _override(professional_user, db_session)
        try:
            payload = _payload_over_ss_base("180000.00")
            payload["statutory_limits"] = {"ss_wage_base": "not-a-number"}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation", json=payload)
            assert response.status_code == 400, response.text
        finally:
            app.dependency_overrides.clear()

    def test_every_engine_limit_is_reachable_from_the_request(self):
        """The guard for the original defect.

        Sprint 636 claimed the thresholds were caller-overridable and the API
        exposed none of them. If the engine gains a limit field, it must become
        settable here too — otherwise the same gap reopens silently.
        """
        import dataclasses

        from routes.w2_reconciliation import StatutoryLimitOverrides
        from w2_reconciliation_engine import W2ReconciliationConfig

        structural = {"tax_year", "employees", "w2_drafts", "form_941_quarters", "tolerance"}
        engine_limits = {f.name for f in dataclasses.fields(W2ReconciliationConfig)} - structural
        exposed = set(StatutoryLimitOverrides.model_fields)

        assert engine_limits == exposed, (
            "the engine's statutory limits and the request's overrides have diverged — "
            f"engine-only: {sorted(engine_limits - exposed)}, request-only: {sorted(exposed - engine_limits)}"
        )


# ---------------------------------------------------------------------------
# PR #189 review — non-finite decimals reached the engine as a 500
# ---------------------------------------------------------------------------
#
# `Decimal("NaN")`, `"sNaN"`, `"Infinity"` and `"-Infinity"` all construct
# without raising, so `_to_decimal`'s try/except — which only guarded
# *construction* — let them through. The engine then raised InvalidOperation on
# the first comparison or quantisation, uncaught, as a 500 where the helper's
# entire purpose is to produce a 400.
#
# Found via the Sprint 793a overrides, but the hole is in `_to_decimal` itself
# and predates them: 48 call sites across five promoted routes, every monetary
# field on each. The fix is in the helper, so these cases cover any field.

_NON_FINITE = ["NaN", "sNaN", "Infinity", "-Infinity"]


@pytest.mark.usefixtures("bypass_csrf")
class TestNonFiniteDecimalsAreRejected:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad", _NON_FINITE)
    async def test_non_finite_override_is_a_400(self, professional_user, db_session, bad):
        _override(professional_user, db_session)
        try:
            payload = _payload_over_ss_base("180000.00")
            payload["statutory_limits"] = {"ss_wage_base": bad}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation", json=payload)
            assert response.status_code == 400, f"{bad!r} produced {response.status_code}: {response.text[:200]}"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad", _NON_FINITE)
    async def test_non_finite_payroll_amount_is_a_400(self, professional_user, db_session, bad):
        """The pre-existing half. These fields had the same hole before Sprint
        793a existed, which is why the fix belongs in `_to_decimal` rather than
        in the override loop."""
        _override(professional_user, db_session)
        try:
            payload = _payload_over_ss_base("180000.00")
            payload["employees"][0]["ss_wages"] = bad
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation", json=payload)
            assert response.status_code == 400, f"{bad!r} produced {response.status_code}: {response.text[:200]}"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_a_very_large_but_finite_value_is_still_accepted(self, professional_user, db_session):
        """The guard rejects non-finite, not merely large. `1e999999` parses to
        a finite Decimal and must not be swept up by the fix."""
        _override(professional_user, db_session)
        try:
            payload = _payload_over_ss_base("180000.00")
            payload["statutory_limits"] = {"ss_wage_base": "1e30"}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/w2-reconciliation", json=payload)
            assert response.status_code == 200, response.text
            # A base that large means nothing can exceed it.
            assert _ss_base_findings(response.json()) == []
        finally:
            app.dependency_overrides.clear()


def test_every_promoted_route_guards_non_finite_decimals():
    """All five routes carry their own `_to_decimal`; all five had the hole.

    A new route copying the old three-line helper would reintroduce it, and
    nothing else in the suite would notice — the failure is a 500 on an input
    no existing test sends.
    """
    import pathlib

    routes_dir = pathlib.Path(__file__).resolve().parent.parent / "routes"
    unguarded: list[str] = []
    checked = 0
    for path in sorted(routes_dir.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        if "def _to_decimal(" not in src:
            continue
        checked += 1
        if "is_finite()" not in src:
            unguarded.append(path.name)

    assert checked > 0, "no route defines _to_decimal — this check now covers nothing"
    assert unguarded == [], (
        "These routes parse decimals without rejecting NaN/Infinity, so a syntactically "
        f"valid non-finite value reaches the engine and surfaces as a 500: {unguarded}"
    )
