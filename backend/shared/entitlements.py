"""
Tier-based entitlement configuration.

Phase LXIX: Pricing Restructure v3.
- 4 tiers: Free, Solo, Professional, Enterprise
- All paid tiers get all 12 tools
- FREE tier = view only (TB + Flux Analysis, no exports)
- New boolean feature entitlements: export_sharing, activity_logs, admin_dashboard, bulk_upload, custom_branding

Defines per-tier limits for uploads, clients, tools, exports, and features.
Used by entitlement_checks.py dependency functions to gate access.
"""

# CANONICAL TOOL COUNT: 12
# This is the single source of truth for Paciolus tool count across all docs, copy,
# and marketing surfaces. If tools are added or removed, update this comment and all
# references identified in COHESION_REMEDIATION.md before merging.

from dataclasses import dataclass

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


# Tool route names matching ToolName enum values
_FREE_TOOLS = frozenset(
    {
        "trial_balance",
        "flux_analysis",
    }
)

_ALL_TOOLS: frozenset[str] = frozenset()  # Empty = all tools allowed

# Per-tier format access
_FREE_FORMATS = frozenset({"csv", "xlsx", "xls", "tsv", "txt"})

_ALL_FORMATS: frozenset[str] = frozenset()  # Empty = all formats allowed


TIER_ENTITLEMENTS: dict[UserTier, TierEntitlements] = {
    UserTier.FREE: TierEntitlements(
        uploads_per_month=10,
        max_clients=3,
        tools_allowed=_FREE_TOOLS,
        formats_allowed=_FREE_FORMATS,
        max_team_seats=0,
        seats_included=1,
        pdf_export=False,  # Free = view only, no exports
        excel_export=False,
        csv_export=False,
        workspace=False,
        priority_support=False,
        export_sharing=False,
        activity_logs=False,
        admin_dashboard=False,
        bulk_upload=False,
        custom_branding=False,
        share_ttl_hours=0,
    ),
    UserTier.SOLO: TierEntitlements(
        uploads_per_month=100,
        max_clients=0,  # unlimited
        tools_allowed=_ALL_TOOLS,  # All 12 tools
        formats_allowed=_ALL_FORMATS,  # All formats
        max_team_seats=0,  # No team features
        seats_included=1,
        pdf_export=True,
        excel_export=True,
        csv_export=True,
        workspace=True,
        priority_support=False,
        export_sharing=False,
        activity_logs=False,
        admin_dashboard=False,
        bulk_upload=False,
        custom_branding=False,
        share_ttl_hours=0,
    ),
    UserTier.PROFESSIONAL: TierEntitlements(
        uploads_per_month=500,
        max_clients=0,  # unlimited
        tools_allowed=_ALL_TOOLS,
        formats_allowed=_ALL_FORMATS,
        max_team_seats=20,
        seats_included=7,
        pdf_export=True,
        excel_export=True,
        csv_export=True,
        workspace=True,
        priority_support=True,
        export_sharing=True,
        activity_logs=True,
        admin_dashboard=True,
        bulk_upload=False,
        custom_branding=False,
        share_ttl_hours=24,
    ),
    UserTier.ENTERPRISE: TierEntitlements(
        uploads_per_month=0,  # unlimited
        max_clients=0,  # unlimited
        tools_allowed=_ALL_TOOLS,
        formats_allowed=_ALL_FORMATS,
        max_team_seats=100,
        seats_included=20,
        pdf_export=True,
        excel_export=True,
        csv_export=True,
        workspace=True,
        priority_support=True,
        export_sharing=True,
        activity_logs=True,
        admin_dashboard=True,
        bulk_upload=True,
        custom_branding=True,
        share_ttl_hours=48,
    ),
}


def get_entitlements(tier: UserTier) -> TierEntitlements:
    """Get entitlements for a given tier. Defaults to FREE if tier is unknown."""
    return TIER_ENTITLEMENTS.get(tier, TIER_ENTITLEMENTS[UserTier.FREE])
