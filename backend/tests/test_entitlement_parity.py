"""
Entitlement Parity Proof — cross-check backend entitlements against frontend constants.

Parses UpgradeGate.tsx TIER_TOOLS and commandRegistry.ts SOLO_TOOLS/FREE_TOOLS
to assert that frontend and backend tool sets are identical.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import UserTier
from shared.entitlements import TIER_ENTITLEMENTS

# Paths relative to the repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPGRADE_GATE_PATH = os.path.join(REPO_ROOT, "frontend", "src", "components", "shared", "UpgradeGate.tsx")
COMMAND_REGISTRY_PATH = os.path.join(REPO_ROOT, "frontend", "src", "lib", "commandRegistry.ts")
PRICING_PAGE_PATH = os.path.join(REPO_ROOT, "frontend", "src", "app", "(marketing)", "pricing", "page.tsx")


def _parse_js_set(source: str, variable_name: str) -> set[str]:
    """Extract tool names from a JS/TS Set([...]) or new Set([...]) declaration."""
    # Match: `variable_name: new Set([...])` or `const variable_name = new Set([...])`
    # Handles multi-line Set declarations
    pattern = rf"(?:{variable_name}\s*[:=]\s*new\s+Set\(\[|{variable_name}\s*=\s*new\s+Set\(\[)(.*?)\]\)"
    match = re.search(pattern, source, re.DOTALL)
    if not match:
        pytest.fail(f"Could not find Set declaration for '{variable_name}' in source")
    inner = match.group(1)
    # Extract quoted strings
    return set(re.findall(r"'([^']+)'", inner))


def _parse_tier_tools_block(source: str, tier_name: str) -> set[str]:
    """Extract tool names from TIER_TOOLS.<tier>: new Set([...])."""
    return _parse_js_set(source, tier_name)


class TestBackendFrontendParity:
    """Backend entitlements must match frontend guard constants."""

    @pytest.fixture(autouse=True)
    def _load_sources(self):
        with open(UPGRADE_GATE_PATH, encoding="utf-8") as f:
            self.upgrade_gate_source = f.read()
        with open(COMMAND_REGISTRY_PATH, encoding="utf-8") as f:
            self.command_registry_source = f.read()

    def test_solo_tools_match_upgrade_gate(self):
        """Backend _SOLO_TOOLS == UpgradeGate TIER_TOOLS.solo."""
        backend_tools = TIER_ENTITLEMENTS[UserTier.SOLO].tools_allowed
        frontend_tools = _parse_tier_tools_block(self.upgrade_gate_source, "solo")
        assert backend_tools == frontend_tools, (
            f"Mismatch: backend={sorted(backend_tools)}, frontend={sorted(frontend_tools)}"
        )

    def test_free_tools_match_upgrade_gate(self):
        """Backend _BASIC_TOOLS == UpgradeGate TIER_TOOLS.free."""
        backend_tools = TIER_ENTITLEMENTS[UserTier.FREE].tools_allowed
        frontend_tools = _parse_tier_tools_block(self.upgrade_gate_source, "free")
        assert backend_tools == frontend_tools, (
            f"Mismatch: backend={sorted(backend_tools)}, frontend={sorted(frontend_tools)}"
        )

    def test_professional_tools_match_upgrade_gate(self):
        """Backend PROFESSIONAL == UpgradeGate TIER_TOOLS.professional."""
        backend_tools = TIER_ENTITLEMENTS[UserTier.PROFESSIONAL].tools_allowed
        frontend_tools = _parse_tier_tools_block(self.upgrade_gate_source, "professional")
        assert backend_tools == frontend_tools

    def test_solo_tools_match_command_registry(self):
        """Backend _SOLO_TOOLS == commandRegistry SOLO_TOOLS."""
        backend_tools = TIER_ENTITLEMENTS[UserTier.SOLO].tools_allowed
        frontend_tools = _parse_js_set(self.command_registry_source, "SOLO_TOOLS")
        assert backend_tools == frontend_tools, (
            f"Mismatch: backend={sorted(backend_tools)}, registry={sorted(frontend_tools)}"
        )

    def test_free_tools_match_command_registry(self):
        """Backend _BASIC_TOOLS == commandRegistry FREE_TOOLS."""
        backend_tools = TIER_ENTITLEMENTS[UserTier.FREE].tools_allowed
        frontend_tools = _parse_js_set(self.command_registry_source, "FREE_TOOLS")
        assert backend_tools == frontend_tools, (
            f"Mismatch: backend={sorted(backend_tools)}, registry={sorted(frontend_tools)}"
        )


class TestPricingPageConsistency:
    """Pricing page claims must match backend entitlements."""

    def test_solo_tool_count_matches_pricing_claim(self):
        """Pricing page says '5 testing tools' — solo has 6 tool pages minus TB = 5."""
        solo_tools = TIER_ENTITLEMENTS[UserTier.SOLO].tools_allowed
        # Tool pages = tools_allowed minus TB sub-features (prior_period, adjustments, flux_analysis)
        tb_sub_features = {"prior_period", "adjustments", "flux_analysis"}
        tool_pages = solo_tools - tb_sub_features
        # Tool pages includes trial_balance itself, so "TB + N tools" means N = len(tool_pages) - 1
        assert len(tool_pages) - 1 == 5, (
            f"Pricing page claims '5 testing tools' but solo has "
            f"{len(tool_pages) - 1} tool pages beyond TB: {sorted(tool_pages)}"
        )

    def test_solo_diagnostics_limit_matches_pricing(self):
        """Pricing page says '20 uploads per month'."""
        assert TIER_ENTITLEMENTS[UserTier.SOLO].diagnostics_per_month == 20
