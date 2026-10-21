"""
Segregation of Duties route tier-gate tests — Sprint 789.

The engine has its own exhaustive tests in `test_sod_engine.py`; this file
covers the route-layer gating, which was wrong until Sprint 789.

`routes/sod.py` carried a bespoke ``require_enterprise_tier`` dependency — the
only hardcoded tier comparison in any route module — that returned 403 to Solo
and Professional. Meanwhile:

* `shared/entitlements.py` grants every paid tier `_ALL_TOOLS` (empty = all),
* `tools_registry.py` marks `sod_checker` `is_marketing_audit_tool=True`,
* the Terms of Service tier table promises "All 18 tools" to Solo and Professional,
* the pricing page FAQ says outright "Both Solo and Professional include all 18
  diagnostic tools",
* and `UpgradeModal` repeats the claim at the point of purchase.

So two paying tiers were sold a tool the API refused to run. These tests pin the
corrected boundary — paid/Free, the same boundary every other paid tool has —
in the route layer where the old gate lived.
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
    """A one-user matrix that trips JE-01 (create + post journal entries)."""
    return {
        "user_assignments": [
            {"user_id": "u1", "user_name": "Alice", "role_codes": ["accountant"]},
        ],
        "role_permissions": [
            {"role_code": "accountant", "permissions": ["JE_create", "JE_post"]},
        ],
        "extra_rules": [],
    }


def _make_user(db_session, email: str, tier: UserTier) -> User:
    user = User(
        email=email,
        name=f"{tier.value} SoD",
        hashed_password="$2b$12$fakehashvalue",
        tier=tier,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _override(user, db_session) -> None:
    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session


@pytest.mark.usefixtures("bypass_csrf")
class TestSodTierGate:
    @pytest.mark.asyncio
    async def test_free_tier_blocked_on_analyze(self, db_session):
        user = _make_user(db_session, "free_sod@example.com", UserTier.FREE)
        _override(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/sod/analyze", json=_valid_payload())
            assert response.status_code == 403
            detail = response.json()["detail"]
            # The standard entitlement shape, not the old bespoke
            # {"error": "tier_locked", "feature": "sod_checker"} payload.
            assert detail["code"] == "TIER_LIMIT_EXCEEDED"
            assert detail["resource"] == "tool_access"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_free_tier_blocked_on_csv_export(self, db_session):
        user = _make_user(db_session, "free_sod_csv@example.com", UserTier.FREE)
        _override(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/sod/analyze.csv", json=_valid_payload())
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "TIER_LIMIT_EXCEEDED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tier", [UserTier.SOLO, UserTier.PROFESSIONAL, UserTier.ENTERPRISE])
    async def test_every_paid_tier_passes_analyze(self, db_session, tier):
        """The Sprint 789 regression test.

        Solo and Professional are the two that used to 403 despite being sold
        the tool. Enterprise is included so a future change cannot narrow the
        gate back to one tier and still pass.
        """
        user = _make_user(db_session, f"paid_sod_{tier.value}@example.com", tier)
        _override(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/sod/analyze", json=_valid_payload())
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["users_evaluated"] == 1
            assert body["users_with_conflicts"] == 1
            assert any(c["rule_code"] == "JE-01" for c in body["conflicts"])
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tier", [UserTier.SOLO, UserTier.PROFESSIONAL, UserTier.ENTERPRISE])
    async def test_every_paid_tier_passes_csv_export(self, db_session, tier):
        user = _make_user(db_session, f"paid_sod_csv_{tier.value}@example.com", tier)
        _override(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/sod/analyze.csv", json=_valid_payload())
            assert response.status_code == 200, response.text
            assert response.headers["content-type"].startswith("text/csv")
            assert "sod_analysis.csv" in response.headers.get("content-disposition", "")
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_rule_library_is_reference_data_for_any_verified_user(self, db_session):
        """`/audit/sod/rules` exposes the rule library, not an analysis of
        customer data, so it carries no entitlement check — matching
        `/audit/book-to-tax/standard-adjustments`. Free tier may read it."""
        user = _make_user(db_session, "free_sod_rules@example.com", UserTier.FREE)
        _override(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/audit/sod/rules")
            assert response.status_code == 200
            rules = response.json()["rules"]
            # Pinned exactly, not as >=. The page copy claimed "Twelve
            # standards-backed SoD rules" against a library of 11 until
            # Sprint 789; a >= assertion would not have caught that and did
            # not, for the ~6 months the claim was live.
            assert len(rules) == 11
            assert {r["code"] for r in rules} == {
                "AP-01",
                "AP-02",
                "AP-03",
                "JE-01",
                "JE-02",
                "PR-01",
                "PR-02",
                "REV-01",
                "REV-02",
                "INV-01",
                "ADM-01",
            }
        finally:
            app.dependency_overrides.clear()


class TestNoHardcodedTierComparisonsInRoutes:
    """Sprint 789 guard.

    The defect was not that SoD was Enterprise-only — it was that one route
    decided tier access for itself instead of asking `enforce_tool_access`,
    so the entitlements table, the catalog and the pricing copy could all
    disagree with it indefinitely without anything failing. `routes/sod.py`
    was the only offender. This keeps it that way.

    Feature-level gates (export sharing, bulk upload, custom branding) live in
    `shared/entitlement_checks.py` and are not route-local, so they are
    unaffected.
    """

    def test_no_route_module_compares_user_tier_directly(self):
        import ast
        import pathlib

        routes_dir = pathlib.Path(__file__).resolve().parent.parent / "routes"
        offenders: list[str] = []

        for path in sorted(routes_dir.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Compare):
                    continue
                # Match `<anything>.tier <op> UserTier.X` in either direction.
                operands = [node.left, *node.comparators]
                has_tier_attr = any(isinstance(o, ast.Attribute) and o.attr == "tier" for o in operands)
                has_usertier_member = any(
                    isinstance(o, ast.Attribute) and isinstance(o.value, ast.Name) and o.value.id == "UserTier"
                    for o in operands
                )
                if has_tier_attr and has_usertier_member:
                    offenders.append(f"{path.name}:{node.lineno}")

        assert offenders == [], (
            "Route modules must not decide tier access themselves — call "
            "enforce_tool_access(current_user, <slug>, db) so the entitlements "
            "table stays the single source of truth. Sprint 789 removed the last "
            f"one of these from routes/sod.py. Found: {offenders}"
        )
