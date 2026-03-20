"""
Tests for Rate Limit Coverage — Packet 4

Programmatic verification that all mutating endpoints (POST/PUT/PATCH/DELETE)
have explicit @limiter.limit() decorators. Prevents regression where new
endpoints are added without rate limiting.
"""

import ast
import os
import sys

import pytest

sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "..")))

ROUTES_DIR = os.path.join(os.path.dirname(__file__), "..", "routes")
MUTATING_METHODS = {"post", "put", "patch", "delete"}


# AUDIT-07: Stripe webhook now rate-limited (10/min). No remaining exemptions.
RATE_LIMIT_EXEMPT: set[tuple[str, str, str]] = set()


def _audit_mutating_routes():
    """Parse all route files and return (covered, missing) lists."""
    covered = []
    missing = []

    for fname in sorted(os.listdir(ROUTES_DIR)):
        if not fname.endswith(".py") or fname == "__init__.py":
            continue
        filepath = os.path.join(ROUTES_DIR, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            route_method = None
            route_path = None
            has_limiter = False

            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    attr = dec.func.attr.lower()
                    if (
                        attr in MUTATING_METHODS
                        and isinstance(dec.func.value, ast.Name)
                        and dec.func.value.id == "router"
                    ):
                        route_method = attr.upper()
                        if dec.args and isinstance(dec.args[0], ast.Constant):
                            route_path = dec.args[0].value

                    if (
                        dec.func.attr == "limit"
                        and isinstance(dec.func.value, ast.Name)
                        and dec.func.value.id == "limiter"
                    ):
                        has_limiter = True

            if route_method and route_path:
                entry = (fname, route_method, route_path)
                if has_limiter:
                    covered.append(entry)
                elif entry not in RATE_LIMIT_EXEMPT:
                    missing.append(entry)

    return covered, missing


# Tier constant assertions removed — covered by test_rate_limit_tiered.py
# (TestTieredLimitBackwardCompat and TestTierPolicies)

# =============================================================================
# COVERAGE AUDIT TESTS
# =============================================================================


class TestMutatingEndpointCoverage:
    """Verify all mutating endpoints have explicit rate limit decorators."""

    def test_no_unprotected_mutating_endpoints(self):
        """Every POST/PUT/PATCH/DELETE route must have @limiter.limit()."""
        covered, missing = _audit_mutating_routes()

        if missing:
            msg_lines = ["Mutating endpoints missing @limiter.limit():"]
            for fname, method, path in missing:
                msg_lines.append(f"  {fname}: {method} {path}")
            pytest.fail("\n".join(msg_lines))

    def test_minimum_covered_count(self):
        """Sanity check: at least 80 mutating endpoints should be rate-limited."""
        covered, _ = _audit_mutating_routes()
        assert len(covered) >= 80, f"Expected >= 80 rate-limited mutating endpoints, found {len(covered)}"

    def test_specific_modules_covered(self):
        """Verify the 8 modules that were unprotected before Packet 4."""
        covered, missing = _audit_mutating_routes()
        covered_set = {(f, m, p) for f, m, p in covered}

        expected = [
            ("activity.py", "POST", "/activity/log"),
            ("activity.py", "DELETE", "/activity/clear"),
            ("clients.py", "POST", "/clients"),
            ("clients.py", "PUT", "/clients/{client_id}"),
            ("clients.py", "DELETE", "/clients/{client_id}"),
            ("diagnostics.py", "POST", "/diagnostics/summary"),
            ("engagements.py", "POST", "/engagements"),
            ("engagements.py", "PUT", "/engagements/{engagement_id}"),
            ("engagements.py", "DELETE", "/engagements/{engagement_id}"),
            ("follow_up_items.py", "POST", "/engagements/{engagement_id}/follow-up-items"),
            ("follow_up_items.py", "PUT", "/follow-up-items/{item_id}"),
            ("follow_up_items.py", "DELETE", "/follow-up-items/{item_id}"),
            ("follow_up_items.py", "POST", "/follow-up-items/{item_id}/comments"),
            ("follow_up_items.py", "PATCH", "/comments/{comment_id}"),
            ("follow_up_items.py", "DELETE", "/comments/{comment_id}"),
            ("multi_period.py", "POST", "/audit/compare-periods"),
            ("multi_period.py", "POST", "/audit/compare-three-way"),
            ("prior_period.py", "POST", "/clients/{client_id}/periods"),
            ("prior_period.py", "POST", "/audit/compare"),
            ("settings.py", "PUT", "/settings/practice"),
            ("settings.py", "PUT", "/clients/{client_id}/settings"),
            ("settings.py", "POST", "/settings/materiality/preview"),
        ]

        for fname, method, path in expected:
            assert (fname, method, path) in covered_set, f"Expected {fname} {method} {path} to be rate-limited"


# =============================================================================
# ROUTE REGISTRATION REGRESSION TESTS
# =============================================================================


class TestRouteRegistration:
    """Verify routes are still properly registered after Packet 4 changes."""

    def test_all_touched_routes_registered(self):
        """All routes from touched modules should still be registered."""
        from main import app

        registered = {r.path for r in app.routes if hasattr(r, "path")}

        expected_paths = [
            "/activity/log",
            "/activity/clear",
            "/clients",
            "/diagnostics/summary",
            "/engagements",
            "/follow-up-items/{item_id}",
            "/comments/{comment_id}",
            "/audit/compare-periods",
            "/audit/compare-three-way",
            "/audit/compare",
            "/settings/practice",
            "/settings/materiality/preview",
        ]

        for path in expected_paths:
            assert path in registered, f"Route {path} not found in registered routes"
