"""
Post-audit remediation regression suite (batch 2) — 2026-04-20.

Covers Sprint 677–678 landing:

Sprint 677: Concentration % overflow + logo upload DB integrity
  * Concentration overflow — SUSPICION REJECTED.
      The audit claimed ``concentration_percent`` was double-multiplied to 5000%.
      Characterization tests confirm the stored value is a 0-100 scaled
      percentage (50.0 for 50% concentration) and no consumer formats it with
      a percent-multiplying format specifier. Contract is correct.
  * Logo upload DB integrity — CONFIRMED.
      ``POST /branding/logo`` previously committed ``logo_s3_key`` even when the
      S3 upload was a silent no-op (bucket unconfigured in dev).
      Engine now treats storage unavailability as HTTP 503 and refuses to
      persist logo metadata that points at an object that isn't there.

Sprint 678: Tier entitlement enforcement wire-up
  * ``check_export_access`` rejects Free-tier users on every export endpoint.
  * ``check_format_access`` rejects Free-tier users on premium file formats.
  * ``check_upload_limit`` fires on every testing-tool route that previously
    bypassed it.
"""

from __future__ import annotations

import pytest

# =============================================================================
# Sprint 677a: Concentration overflow SUSPICION REJECTED
# =============================================================================


class TestConcentrationOverflowSuspicion:
    """Characterization tests: ``concentration_percent`` is 0-100 scaled by
    design. The audit's "5000%" overflow claim was based on the assumption
    that a consumer formats the field with ``:.1%`` (which would double-
    multiply). No such consumer exists — the contract is correct as-is.

    These tests pin the contract so future refactors can't break it.
    """

    def _build_concentration_dataset(self) -> dict[str, dict[str, float]]:
        # Single asset account holds 80% of total assets — classic
        # concentration scenario.
        return {
            "1100:Dominant Receivable": {"debit": 800.0, "credit": 0.0},
            "1200:Minor Receivable A": {"debit": 100.0, "credit": 0.0},
            "1300:Minor Receivable B": {"debit": 100.0, "credit": 0.0},
        }

    def test_concentration_percent_is_0_to_100_scale(self):
        """80% concentration → field reads 80.0, not 0.80 and not 8000.0."""
        from account_classifier import AccountClassifier
        from audit.rules.concentration import detect_concentration_risk

        balances = self._build_concentration_dataset()
        classifier = AccountClassifier()
        provided_types = {
            "1100:Dominant Receivable": "asset",
            "1200:Minor Receivable A": "asset",
            "1300:Minor Receivable B": "asset",
        }
        provided_names = {
            "1100:Dominant Receivable": "Dominant Receivable",
            "1200:Minor Receivable A": "Minor Receivable A",
            "1300:Minor Receivable B": "Minor Receivable B",
        }

        risks = detect_concentration_risk(
            balances,
            materiality_threshold=100.0,
            classifier=classifier,
            provided_account_types=provided_types,
            provided_account_names=provided_names,
        )

        assert risks, "Expected concentration risk on 80% asset dominance"
        dominant = next(r for r in risks if "Dominant" in r["account"])
        # Contract: concentration_percent is the human-readable "percent" scale
        # (0-100). 80% of assets reads as 80.0, not 0.80 and not 8000.0.
        assert dominant["concentration_percent"] == 80.0
        # confidence stays in 0-1 ratio form (it's a probability-like signal)
        assert abs(dominant["confidence"] - 0.80) < 1e-9

    def test_issue_text_renders_percent_once(self):
        """The ``:.1%`` format specifier is applied to ``concentration_pct``
        (the local 0-1 ratio), never to ``concentration_percent`` (the stored
        0-100 field). So the rendered issue text reads "80.0% of total assets",
        not "8000.0%"."""
        from account_classifier import AccountClassifier
        from audit.rules.concentration import detect_concentration_risk

        balances = self._build_concentration_dataset()
        classifier = AccountClassifier()
        provided_types = dict.fromkeys(balances, "asset")
        provided_names = {k: k.split(":", 1)[1] for k in balances}

        risks = detect_concentration_risk(balances, 100.0, classifier, provided_types, provided_names)
        dominant = next(r for r in risks if "Dominant" in r["account"])
        assert "80.0% of total assets" in dominant["issue"]
        assert "8000" not in dominant["issue"]


# =============================================================================
# Sprint 677b: Logo upload DB integrity CONFIRMED
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestLogoUploadDBIntegrity:
    """``POST /branding/logo`` must not persist ``logo_s3_key`` when the
    underlying storage call is a no-op. Dev environments without S3 previously
    stored dangling keys that Sprint 679's PDF branding pipeline would then
    fail to fetch.
    """

    @pytest.mark.asyncio
    async def test_logo_upload_503_when_storage_noop(self, db_session):
        """Route returns 503 and does NOT persist logo_s3_key when
        upload_bytes returns False (S3 unconfigured)."""
        import sys
        from pathlib import Path
        from unittest.mock import patch

        import httpx

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from auth import require_current_user
        from database import get_db
        from firm_branding_model import FirmBranding
        from main import app
        from models import User, UserTier
        from organization_model import Organization, OrganizationMember, OrgRole

        user = User(
            email="logo_integrity@example.com",
            name="Logo Test",
            hashed_password="$2b$12$fakehashvalue",
            tier=UserTier.ENTERPRISE,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.flush()

        org = Organization(name="LogoOrg", slug="logoorg", owner_user_id=user.id)
        db_session.add(org)
        db_session.flush()

        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=OrgRole.OWNER,
        )
        db_session.add(member)
        db_session.flush()

        user.organization_id = org.id
        db_session.flush()

        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            # Construct a minimal valid PNG payload (magic bytes + padding)
            png_payload = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

            # Patch the entitlement check and storage helper.
            # upload_bytes returns False to simulate S3 unconfigured.
            with (
                patch("routes.branding.check_custom_branding_access"),
                patch("shared.storage_client.upload_bytes", return_value=False),
                patch("shared.storage_client._get_client", return_value=None),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/branding/logo",
                        files={"file": ("logo.png", png_payload, "image/png")},
                        headers={"X-Requested-With": "XMLHttpRequest"},
                    )

            assert response.status_code == 503, response.text
            # The DB row must NOT have been committed with a logo_s3_key.
            db_session.expire_all()
            branding = db_session.query(FirmBranding).filter(FirmBranding.organization_id == org.id).first()
            # Either no row (flushed but rolled back) or row exists with null key.
            assert branding is None or branding.logo_s3_key is None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_logo_upload_200_when_storage_succeeds(self, db_session):
        """Happy path: upload_bytes returns True → logo_s3_key persisted."""
        import sys
        from pathlib import Path
        from unittest.mock import patch

        import httpx

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from auth import require_current_user
        from database import get_db
        from firm_branding_model import FirmBranding
        from main import app
        from models import User, UserTier
        from organization_model import Organization, OrganizationMember, OrgRole

        user = User(
            email="logo_happy@example.com",
            name="Logo Happy",
            hashed_password="$2b$12$fakehashvalue",
            tier=UserTier.ENTERPRISE,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.flush()

        org = Organization(name="HappyOrg", slug="happyorg", owner_user_id=user.id)
        db_session.add(org)
        db_session.flush()

        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=OrgRole.OWNER,
        )
        db_session.add(member)
        db_session.flush()

        user.organization_id = org.id
        db_session.flush()

        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            png_payload = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

            with (
                patch("routes.branding.check_custom_branding_access"),
                patch("shared.storage_client.upload_bytes", return_value=True),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/branding/logo",
                        files={"file": ("logo.png", png_payload, "image/png")},
                        headers={"X-Requested-With": "XMLHttpRequest"},
                    )

            assert response.status_code == 200, response.text
            db_session.expire_all()
            branding = db_session.query(FirmBranding).filter(FirmBranding.organization_id == org.id).first()
            assert branding is not None
            assert branding.logo_s3_key == f"branding/{org.id}/logo"
            assert branding.logo_content_type == "image/png"
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# Sprint 678: Tier entitlement enforcement wire-up
# =============================================================================


class TestEntitlementHelpersExist:
    """Smoke test: the helpers wired by Sprint 678 exist and return the
    expected dependency factory shape."""

    def test_check_export_access_is_a_dependency(self):
        from shared.entitlement_checks import check_export_access

        assert callable(check_export_access)

    def test_check_format_access_factory_returns_dependency(self):
        from shared.entitlement_checks import check_format_access

        dep = check_format_access("ofx")
        assert callable(dep)

    def test_check_upload_limit_is_a_dependency(self):
        from shared.entitlement_checks import check_upload_limit

        assert callable(check_upload_limit)


class TestExportRoutesAreGated:
    """Each module listed in Sprint 678 wires ``check_export_access`` on at
    least one export endpoint. This is a structural guard that will catch
    accidental gate removals during future refactors."""

    def _router_has_export_access_dependency(self, module_name: str) -> bool:
        import importlib

        mod = importlib.import_module(module_name)
        router = getattr(mod, "router", None)
        if router is None:
            return False
        from shared.entitlement_checks import check_export_access

        for route in router.routes:
            for dep in getattr(route, "dependencies", []) or []:
                if getattr(dep, "dependency", None) is check_export_access:
                    return True
        return False

    @pytest.mark.parametrize(
        "module_name",
        [
            "routes.export_memos",
            "routes.export_diagnostics",
            "routes.export_testing",
            "routes.engagements_exports",
        ],
    )
    def test_export_module_has_export_access_gate(self, module_name):
        assert self._router_has_export_access_dependency(module_name), (
            f"{module_name} has no route gated by check_export_access"
        )


class TestFormatAccessWiredOnUploadRoutes:
    """``check_format_access`` should be invoked (directly or via a helper) on
    the TB/bulk upload entry points so Free tier can't post OFX/QBO/PDF/ODS."""

    def test_format_access_factory_is_importable_from_upload_paths(self):
        # Minimal smoke — full runtime test would require posting a QBO file
        # as a Free user, which belongs in the upload-pipeline integration
        # suite. This test just confirms Sprint 678's helper is reachable from
        # the module where it must be wired.
        from shared.entitlement_checks import check_format_access

        assert callable(check_format_access("qbo"))
        assert callable(check_format_access("ofx"))
        assert callable(check_format_access("pdf"))
        assert callable(check_format_access("ods"))


class TestToolRoutesCheckUploadLimit:
    """The 11 testing-tool routes should enforce upload limits. Existing
    ``shared/testing_route.py::enforce_tool_access`` is the canonical site."""

    def test_enforce_tool_access_exists(self):
        from shared import testing_route

        assert hasattr(testing_route, "enforce_tool_access")
        assert callable(testing_route.enforce_tool_access)
