"""
Tier-based entitlement configuration.

Sprint 363: Phase L — Pricing Strategy & Billing Infrastructure.

Defines per-tier limits for diagnostics, clients, tools, exports, and features.
Used by entitlement_checks.py dependency functions to gate access.
"""

from dataclasses import dataclass

from models import UserTier


@dataclass(frozen=True)
class TierEntitlements:
    """Immutable per-tier entitlement limits."""

    diagnostics_per_month: int  # 0 = unlimited
    max_clients: int  # 0 = unlimited
    tools_allowed: frozenset[str]  # Empty = all tools
    formats_allowed: frozenset[str]  # Empty = all formats
    max_team_seats: int  # 0 = N/A (solo tiers)
    pdf_export: bool
    excel_export: bool
    csv_export: bool
    workspace: bool  # Engagement workspace access
    priority_support: bool


# Tool route names matching ToolName enum values
_BASIC_TOOLS = frozenset(
    {
        "trial_balance",
        "flux_analysis",
    }
)

_STARTER_TOOLS = frozenset(
    {
        "trial_balance",
        "flux_analysis",
        "journal_entry_testing",
        "multi_period",
        "prior_period",
        "adjustments",
    }
)

_ALL_TOOLS = frozenset()  # Empty = all tools allowed

# Per-tier format access (Sprint 436)
_BASIC_FORMATS = frozenset({"csv", "xlsx", "xls", "tsv", "txt"})

_STARTER_FORMATS = frozenset(
    {
        "csv",
        "xlsx",
        "xls",
        "tsv",
        "txt",
        "qbo",
        "ofx",
        "iif",
        "pdf",
    }
)

_ALL_FORMATS = frozenset()  # Empty = all formats allowed


TIER_ENTITLEMENTS: dict[UserTier, TierEntitlements] = {
    UserTier.FREE: TierEntitlements(
        diagnostics_per_month=10,
        max_clients=3,
        tools_allowed=_BASIC_TOOLS,
        formats_allowed=_BASIC_FORMATS,
        max_team_seats=0,
        pdf_export=True,
        excel_export=False,
        csv_export=False,
        workspace=False,
        priority_support=False,
    ),
    UserTier.STARTER: TierEntitlements(
        diagnostics_per_month=50,
        max_clients=10,
        tools_allowed=_STARTER_TOOLS,
        formats_allowed=_STARTER_FORMATS,
        max_team_seats=0,
        pdf_export=True,
        excel_export=True,
        csv_export=True,
        workspace=False,
        priority_support=False,
    ),
    UserTier.PROFESSIONAL: TierEntitlements(
        diagnostics_per_month=0,  # unlimited
        max_clients=0,  # unlimited
        tools_allowed=_ALL_TOOLS,
        formats_allowed=_ALL_FORMATS,
        max_team_seats=0,
        pdf_export=True,
        excel_export=True,
        csv_export=True,
        workspace=True,
        priority_support=False,
    ),
    UserTier.TEAM: TierEntitlements(
        diagnostics_per_month=0,  # unlimited
        max_clients=0,  # unlimited
        tools_allowed=_ALL_TOOLS,
        formats_allowed=_ALL_FORMATS,
        max_team_seats=3,  # 3 seats included in base price
        pdf_export=True,
        excel_export=True,
        csv_export=True,
        workspace=True,
        priority_support=True,
    ),
    UserTier.ENTERPRISE: TierEntitlements(
        diagnostics_per_month=0,  # unlimited
        max_clients=0,  # unlimited
        tools_allowed=_ALL_TOOLS,
        formats_allowed=_ALL_FORMATS,
        max_team_seats=0,  # unlimited (custom)
        pdf_export=True,
        excel_export=True,
        csv_export=True,
        workspace=True,
        priority_support=True,
    ),
}


def get_entitlements(tier: UserTier) -> TierEntitlements:
    """Get entitlements for a given tier. Defaults to FREE if tier is unknown."""
    return TIER_ENTITLEMENTS.get(tier, TIER_ENTITLEMENTS[UserTier.FREE])
