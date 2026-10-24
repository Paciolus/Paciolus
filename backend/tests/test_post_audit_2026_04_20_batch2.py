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

from unittest.mock import patch

import pytest

from models import UserTier

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
#
# SPRINT 800 — these four classes used to assert presence, not enforcement.
#
#   TestEntitlementHelpersExist          -> callable(check_export_access) x3
#   TestExportRoutesAreGated             -> >=1 gated route per module, 4 of 6 modules
#   TestFormatAccessWiredOnUploadRoutes  -> callable(check_format_access("qbo"))
#   TestToolRoutesCheckUploadLimit       -> hasattr(testing_route, "enforce_tool_access")
#
# `hasattr(x, "enforce_tool_access")` is `shutil.which` wearing a different
# hat: it answers "is a thing with this name reachable", not "does the thing
# work". The last class was the sharpest case — it was named for a property
# Sprint 790 already records as FALSE (the advertised 100/500 monthly upload
# allowances are unenforced on every paid tier; `check_upload_limit` only
# reads, and `increment_upload_count`'s sole caller is bulk upload). A green
# test class named after a known-broken property is worse than no test,
# because the next reader greps for coverage, finds it, and stops looking.
#
# The behaviour was in fact fine — 79 of 84 export routes carry
# `check_export_access`, and the five that do not gate in-body. So these were
# tests that could not fail, protecting code that happened to be right.
# Replaced with assertions that state the whole property.
#
# One thing the rewrite turned up: the format gate these tests named,
# `check_format_access`, has **no production caller at all**. The real gate is
# `enforce_format_access`, because the format is only known once the file
# arrives — which `enforce_format_access`'s own docstring explains. Four test
# files assert against the unused factory. See
# `TestUploadFormatGateIsWiredNotMerelyImportable` below.
# =============================================================================


class TestEveryExportRouteIsGated:
    """Every export route must be gated, not at least one per module.

    The previous version asserted ``>=1`` gated route per module across 4 of
    the 6 export modules. ``routes/export_memos.py`` alone has 18 endpoints,
    so seventeen of them could lose their gate with the test still green.

    The gate is accepted in either of the two forms the codebase uses: a
    route-level ``Depends(check_export_access)``, or an in-body call
    (``routes/export_sharing.py`` resolves a tier-configurable TTL itself and
    calls ``check_export_sharing_access``). Both are real enforcement;
    recognising only the first would flag five correct routes.
    """

    EXPORT_MODULES = [
        "routes.export_memos",
        "routes.export_diagnostics",
        "routes.export_testing",
        "routes.engagements_exports",
        "routes.export",
        "routes.export_sharing",
    ]

    # In-body gate functions treated as equivalent to the dependency.
    # `test_in_body_gate_allowlist_still_names_real_functions` asserts each
    # still resolves, so this allowlist cannot rot into a lie while the first
    # test keeps passing on its authority.
    IN_BODY_GATES = {
        "shared.entitlement_checks": ["check_export_access", "check_export_sharing_access"],
    }

    # Routes that deliberately carry no *export-access* gate, each with the
    # reason. An unguarded gap that is written down is a decision; the same
    # gap unmentioned is an oversight, and the next reader cannot tell them
    # apart from the code.
    #
    # All four are on the share-link surface, and gating them on export access
    # would be actively wrong rather than merely redundant:
    EXEMPT = {
        # A share link is for a recipient who has no account. Requiring a tier
        # would defeat the entire feature. Protected instead by an unguessable
        # token, an Argon2id passcode, per-IP and per-token brute-force
        # throttling, and expiry.
        ("GET", "/export-sharing/{token}"),
        ("POST", "/export-sharing/{token}/download"),
        # Owner-management of shares that already exist. These require
        # `require_verified_user` and operate only on the caller's own rows.
        # A user who downgrades must still be able to list and revoke what
        # they previously shared — gating revocation behind a paid tier would
        # trap data in a link they can no longer cancel.
        ("DELETE", "/export-sharing/{token}"),
        ("GET", "/export-sharing/"),
    }

    @classmethod
    def _gate_names(cls) -> set[str]:
        return {name for names in cls.IN_BODY_GATES.values() for name in names}

    def _route_is_gated(self, route) -> bool:
        import inspect as _inspect

        from shared.entitlement_checks import check_export_access

        for dep in getattr(route, "dependencies", []) or []:
            if getattr(dep, "dependency", None) is check_export_access:
                return True
        try:
            sig = _inspect.signature(route.endpoint)
        except (TypeError, ValueError):
            sig = None
        if sig is not None:
            for param in sig.parameters.values():
                if getattr(param.default, "dependency", None) is check_export_access:
                    return True
        try:
            source = _inspect.getsource(route.endpoint)
        except (OSError, TypeError):
            # Report rather than assume: an endpoint whose source cannot be
            # read is unverified, not clean.
            return False
        return any(f"{name}(" in source for name in self._gate_names())

    def test_every_export_route_carries_a_tier_gate(self):
        import importlib

        ungated: list[str] = []
        exempt_seen: set[tuple[str, str]] = set()
        total = 0
        for module_name in self.EXPORT_MODULES:
            module = importlib.import_module(module_name)
            router = getattr(module, "router", None)
            assert router is not None, f"{module_name} has no router"
            for route in router.routes:
                if not hasattr(route, "methods"):
                    continue
                total += 1
                for method in route.methods:
                    if (method, route.path) in self.EXEMPT:
                        exempt_seen.add((method, route.path))
                        break
                else:
                    if not self._route_is_gated(route):
                        ungated.append(f"{module_name} {sorted(route.methods)} {route.path}")

        assert total > 70, (
            f"only {total} export routes discovered — the module list has stopped matching "
            f"the tree, which is the same failure as a route losing its gate"
        )
        assert not ungated, f"{len(ungated)} of {total} export routes have no tier gate:\n  " + "\n  ".join(ungated)
        # A stale exemption is an ungated route nobody is looking at.
        stale = self.EXEMPT - exempt_seen
        assert not stale, (
            f"EXEMPT names {sorted(stale)}, which no longer exist. Remove them — an exemption "
            f"for a route that has moved silently stops excusing anything and starts hiding "
            f"whatever took its place."
        )

    def test_in_body_gate_allowlist_still_names_real_functions(self):
        import importlib

        for module_name, names in self.IN_BODY_GATES.items():
            module = importlib.import_module(module_name)
            for name in names:
                assert callable(getattr(module, name, None)), (
                    f"{module_name}.{name} is no longer a callable gate — "
                    f"test_every_export_route_carries_a_tier_gate is passing on its authority"
                )


class TestUploadFormatGateIsWiredNotMerelyImportable:
    """The format gate must be called by the upload entry points.

    The previous class was named "FormatAccessWiredOnUploadRoutes", claimed in
    its docstring that ``check_format_access`` "should be invoked ... on the
    TB/bulk upload entry points", and then asserted only
    ``callable(check_format_access("qbo"))`` — admitting in a comment that it
    was "minimal smoke".

    It also named the wrong function. ``check_format_access`` is a dependency
    factory that needs the format at route-definition time, which does not fit
    an upload where the format is only known once the file arrives. Its own
    sibling ``enforce_format_access`` says so in its docstring, and that is
    what the routes actually call. ``check_format_access`` has **no production
    caller**; it is retained for now because four test files reference it, and
    removing it is a separate decision from fixing this test.
    """

    # The entry points that accept a user-supplied file and must therefore
    # check the format against the tier. Bulk upload is deliberately absent:
    # it is Enterprise-gated by `check_bulk_upload_access`, and Enterprise has
    # an empty `formats_allowed` (= all formats), so there is nothing for a
    # format gate to decide. If bulk upload is ever opened below Enterprise
    # this list must grow — which `test_format_gated_entry_points_still_exist`
    # will not tell you, so it is written down here instead.
    FORMAT_GATED_ENTRY_POINTS = ("routes.audit_upload", "routes.audit_pipeline")

    def test_each_upload_entry_point_calls_the_format_gate(self):
        import importlib
        import inspect as _inspect

        missing = []
        for module_name in self.FORMAT_GATED_ENTRY_POINTS:
            module = importlib.import_module(module_name)
            source = _inspect.getsource(module)
            if "enforce_format_access(" not in source:
                missing.append(module_name)
        assert not missing, (
            f"{missing} accept file uploads but never call enforce_format_access — "
            f"Free tier could post premium formats through them"
        )

    def test_the_gate_actually_rejects_a_premium_format_for_free_tier(self):
        """Behaviour, not presence: drive the function with a Free-tier user."""
        from unittest.mock import MagicMock

        from fastapi import HTTPException

        from shared.entitlement_checks import enforce_format_access

        user = MagicMock()
        user.id = 1
        user.tier = UserTier.FREE

        with patch("shared.entitlement_checks.get_effective_entitlements") as mock_ent:
            mock_ent.return_value = MagicMock(formats_allowed={"csv", "xlsx"})
            # An allowed format passes.
            enforce_format_access(user, MagicMock(), "trial_balance.csv")
            # A premium one does not.
            with pytest.raises(HTTPException) as exc:
                enforce_format_access(user, MagicMock(), "bank.qbo")
            assert exc.value.status_code in (402, 403)

    def test_an_empty_allowed_set_means_all_formats(self):
        """Paid tiers carry an empty `formats_allowed`, meaning unrestricted.

        Asserted explicitly because an empty collection is exactly the value a
        broken entitlement lookup would also produce, and the two must not be
        confused by a future change.
        """
        from unittest.mock import MagicMock

        from shared.entitlement_checks import enforce_format_access

        user = MagicMock()
        user.id = 1
        user.tier = UserTier.PROFESSIONAL
        with patch("shared.entitlement_checks.get_effective_entitlements") as mock_ent:
            mock_ent.return_value = MagicMock(formats_allowed=set())
            for name in ("x.qbo", "x.ofx", "x.pdf", "x.ods", "x.iif"):
                enforce_format_access(user, MagicMock(), name)


class TestUploadAllowanceEnforcement:
    """Paid-tier upload allowances are metered (Sprint 790).

    This class was ``TestUploadAllowanceEnforcementIsHonestlyReported`` and
    pinned the gap: ``increment_upload_count`` had a single caller, bulk upload,
    so ``check_upload_limit`` was inert for every paid tier on every other route.
    It was written to fail the moment Sprint 790 landed, and it did.

    It now pins the shape that closed the gap: the counter is advanced from
    exactly one place — the tool-run recorder's success path, behind
    ``consumes_upload=True``. Bulk upload's old per-file increment was removed:
    that path runs no engine, so it charged allowance for no analysis. The
    per-route pairing of check and increment is held by
    ``tests/test_sprint_790_upload_metering.py``.
    """

    def test_increment_upload_count_is_called_only_by_the_recorder(self):
        import pathlib

        backend_root = pathlib.Path(__file__).resolve().parent.parent
        callers = []
        for path in backend_root.rglob("*.py"):
            if any(p in path.parts for p in ("venv", "tests", "__pycache__", "migrations")):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "increment_upload_count(" in text and "def increment_upload_count" not in text:
                callers.append(str(path.relative_to(backend_root)).replace("\\", "/"))

        assert sorted(callers) == ["shared/tool_run_recorder.py"], (
            f"increment_upload_count callers changed to {callers}. Metering belongs in the "
            f"recorder's success path (consumes_upload=True), not in individual routes — a "
            f"route-level call next to a consuming recorder call would count one run twice."
        )

    # Functions that call `enforce_tool_access` on a route's behalf. A route
    # that calls one of these is gated just as surely as one that calls the
    # gate directly — "no reference in the file" is evidence of delegation,
    # not of a defect (Sprint 791). Verified by
    # `test_delegating_functions_really_do_enforce` so this list cannot rot
    # into a lie while the test above keeps passing on its authority.
    #
    # `services.audit.file_tool_scaffold.execute_file_tool` was in this list
    # in a first draft and is deliberately not: it is a file-handling
    # scaffold (size validation, threading, run recording) and does **not**
    # call the gate. `test_delegating_functions_really_do_enforce` caught
    # that, which is the whole reason the second test exists.
    DELEGATING_GATES = {
        "shared.testing_route": ["run_single_file_testing"],
    }

    def test_enforce_tool_access_is_the_canonical_gate_and_is_actually_called(self):
        """What the old `hasattr` check should have asserted.

        My first version of this asserted ">= 20 route modules call
        enforce_tool_access" and failed at 12 — because most tool routes
        delegate through `run_single_file_testing` rather than calling the
        gate themselves. The floor was a guess, and resolving delegation by
        the *module imported* rather than the *function called* is exactly
        what made Sprint 787b's guard a tautology. Counting both forms, and
        verifying the delegates below.
        """
        import pathlib

        routes_dir = pathlib.Path(__file__).resolve().parent.parent / "routes"
        delegate_names = [n for names in self.DELEGATING_GATES.values() for n in names]

        direct, delegated = [], []
        for path in sorted(routes_dir.glob("*.py")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "enforce_tool_access(" in text:
                direct.append(path.name)
            elif any(f"{n}(" in text for n in delegate_names):
                delegated.append(path.name)

        # Measured inventory, not a guessed floor.
        #
        # The first version of this assertion said ">= 20" and failed at 18,
        # because the number was invented rather than measured. A count is
        # also the weaker assertion: it cannot say *which* route stopped
        # gating, and a module added elsewhere masks one that regressed.
        #
        # So the property is **no shrinkage, by name**. Adding a tool route
        # does not fail this; a route dropping its gate fails it and says
        # which. When you add a tool, add it here — that edit is the point at
        # which someone confirms the new route gates at all.
        EXPECTED_GATED = {
            # direct — call enforce_tool_access themselves
            "ar_aging.py",
            "bank_reconciliation.py",
            "book_to_tax.py",
            "cash_flow_projector.py",
            "currency.py",
            "form_1099.py",
            "intercompany_elimination.py",
            "multi_period.py",
            "sampling.py",
            "sod.py",
            "three_way_match.py",
            "w2_reconciliation.py",
            # delegated — via shared.testing_route.run_single_file_testing
            "ap_testing.py",
            "fixed_asset_testing.py",
            "inventory_testing.py",
            "je_testing.py",
            "payroll_testing.py",
            "revenue_testing.py",
        }
        gated = set(direct) | set(delegated)
        lost = sorted(EXPECTED_GATED - gated)
        assert not lost, (
            f"{len(lost)} route module(s) no longer gate tool access: {lost}. "
            f"Entitlement is supposed to be decided in one place "
            f"(shared/entitlements.py via enforce_tool_access); a route that stops asking "
            f"can contradict the entitlements table indefinitely — see Sprint 789, where "
            f"Solo and Professional were sold a tool the API refused to run for six months."
        )
        # Trial Balance Diagnostics is the 18th catalog tool and is gated by a
        # different family (`check_diagnostic_limit` + `enforce_format_access`
        # in routes/audit_pipeline.py), so it is deliberately absent above.
        # `depreciation.py`, `loan_amortization.py`, `lease_accounting.py`,
        # `composite_risk.py` and `account_risk_heatmap.py` are supporting
        # calculators, not entries in `tools_registry`'s marketing catalog,
        # and carry `require_verified_user` only.

    def test_delegating_functions_really_do_enforce(self):
        """The allowlist above claims these gate. Check that they do."""
        import importlib
        import inspect as _inspect

        for module_name, names in self.DELEGATING_GATES.items():
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError:
                pytest.fail(
                    f"{module_name} is named as a delegating gate but no longer exists — "
                    f"remove it from DELEGATING_GATES or the count above is inflated"
                )
            for name in names:
                fn = getattr(module, name, None)
                assert fn is not None, f"{module_name}.{name} no longer exists"
                source = _inspect.getsource(fn)
                assert "enforce_tool_access(" in source, (
                    f"{module_name}.{name} is listed as delegating to enforce_tool_access "
                    f"but does not call it — every route relying on it is now ungated"
                )

    def test_no_route_module_compares_a_tier_directly(self):
        """The structural fix Sprint 789 called for and nobody built.

        `routes/sod.py` once held the only hardcoded `user.tier != UserTier.X`
        comparison in any route module, and it contradicted the entitlements
        table for six months — Solo and Professional were sold a tool the API
        refused to run. One route deciding entitlement for itself is what made
        indefinite disagreement possible.

        Reading `.tier` is fine (billing and admin surfaces display it); what
        is banned is *comparing* it to a `UserTier` member inside a route.
        """
        import ast
        import pathlib

        routes_dir = pathlib.Path(__file__).resolve().parent.parent / "routes"

        def _is_tier_attr(node: ast.AST) -> bool:
            return isinstance(node, ast.Attribute) and node.attr == "tier"

        def _is_usertier_member(node: ast.AST) -> bool:
            return isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "UserTier"

        violations: list[str] = []
        scanned = 0
        for path in sorted(routes_dir.glob("*.py")):
            scanned += 1
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Compare):
                    operands = [node.left, *node.comparators]
                    has_tier = any(_is_tier_attr(o) for o in operands)
                    has_member = any(_is_usertier_member(o) for o in operands)
                    if has_tier and has_member:
                        violations.append(f"{path.name}:{node.lineno}")

        assert scanned > 50, f"only scanned {scanned} route modules — the glob has broken"
        assert not violations, (
            "Route-local tier comparison(s) found at "
            + ", ".join(violations)
            + ". Entitlement belongs to shared/entitlements.py via enforce_tool_access, so the "
            "entitlements table cannot be contradicted by one route. See Sprint 789."
        )
