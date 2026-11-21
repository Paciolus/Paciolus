"""
Tier-based entitlement configuration.

Phase LXIX: Pricing Restructure v3.
- 4 tiers: Free, Solo, Professional, Enterprise
- All paid tiers get all 18 tools
- FREE tier = view only (TB + Flux Analysis, no exports)
- New boolean feature entitlements: export_sharing, activity_logs, admin_dashboard, bulk_upload, custom_branding

Defines per-tier limits for uploads, clients, tools, exports, and features.
Used by entitlement_checks.py dependency functions to gate access.
"""

# CANONICAL TOOL COUNT: 18
# This is the single source of truth for Paciolus tool count across all docs, copy,
# and marketing surfaces. If tools are added or removed, update this comment and all
# references identified in docs/archive/COHESION_REMEDIATION.md before merging.

import json
from dataclasses import dataclass
from pathlib import Path

from models import UserTier


@dataclass(frozen=True)
class TierEntitlements:
    """Immutable per-tier entitlement limits."""

    uploads_per_month: int  # 0 = unlimited
    max_clients: int  # 0 = unlimited
    tools_allowed: frozenset[str]  # Empty = all tools
    formats_allowed: frozenset[str]  # Empty = all formats
    max_team_seats: int  # Max self-serve seats (0 = N/A)
    seats_included: int  # Base seats included in plan price
    pdf_export: bool
    excel_export: bool
    csv_export: bool
    workspace: bool  # Engagement workspace access
    priority_support: bool
    # Phase LXIX: New feature entitlements
    export_sharing: bool
    activity_logs: bool
    admin_dashboard: bool
    bulk_upload: bool
    custom_branding: bool
    # Sprint 593: Tier-configurable share link TTL (0 = no sharing)
    share_ttl_hours: int


# Sprint 891 (CEO brief 16B): limits and gates come from shared/plans.json, the one plan file
# (prices, seat rates and seat ceilings live there too). Lists become frozensets; an empty set
# still means "all".
_PLANS_PATH = Path(__file__).with_name("plans.json")
PLANS: dict = json.loads(_PLANS_PATH.read_text(encoding="utf-8"))


def _entitlements_from(raw: dict) -> TierEntitlements:
    values = dict(raw)
    values["tools_allowed"] = frozenset(values["tools_allowed"])
    values["formats_allowed"] = frozenset(values["formats_allowed"])
    return TierEntitlements(**values)


TIER_ENTITLEMENTS: dict[UserTier, TierEntitlements] = {
    UserTier(tier): _entitlements_from(plan["entitlements"]) for tier, plan in PLANS["tiers"].items()
}


def get_entitlements(tier: UserTier) -> TierEntitlements:
    """Get entitlements for a given tier. Defaults to FREE if tier is unknown."""
    return TIER_ENTITLEMENTS.get(tier, TIER_ENTITLEMENTS[UserTier.FREE])
