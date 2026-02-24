"""
Framework Resolution Engine — Sprint 1

Deterministic resolution of FASB vs GASB reporting framework
based on client metadata (entity type, jurisdiction, explicit override).

Pure functions — no DB access, no side effects, independently testable.
"""

from dataclasses import dataclass, field
from enum import Enum as PyEnum


class ResolvedFramework(str, PyEnum):
    """The resolved (non-AUTO) framework for report generation."""

    FASB = "fasb"
    GASB = "gasb"


class ResolutionReason(str, PyEnum):
    """Machine-readable reason for framework selection."""

    EXPLICIT_FASB = "explicit_fasb"
    EXPLICIT_GASB = "explicit_gasb"
    ENTITY_TYPE_GOVERNMENTAL = "entity_type_governmental"
    ENTITY_TYPE_FOR_PROFIT = "entity_type_for_profit"
    ENTITY_TYPE_NONPROFIT_US = "entity_type_nonprofit_us"
    JURISDICTION_US_DEFAULT = "jurisdiction_us_default"
    FALLBACK_FASB = "fallback_fasb"


@dataclass(frozen=True)
class ResolvedFrameworkResult:
    """Result of framework resolution with audit trail."""

    framework: ResolvedFramework
    resolution_reason: ResolutionReason
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_gasb(self) -> bool:
        return self.framework == ResolvedFramework.GASB

    @property
    def is_fasb(self) -> bool:
        return self.framework == ResolvedFramework.FASB


def resolve_reporting_framework(
    reporting_framework: str,
    entity_type: str,
    jurisdiction_country: str,
    jurisdiction_state: str | None = None,
) -> ResolvedFrameworkResult:
    """Resolve the authoritative reporting framework for a client.

    Precedence (highest to lowest):
        1. Explicit framework (FASB or GASB) — honor directly
        2. Entity type: governmental → GASB
        3. Entity type: for_profit → FASB
        4. Entity type: nonprofit + US jurisdiction → FASB (FASB ASC 958)
        5. US jurisdiction default → FASB
        6. Fallback → FASB with warning

    Args:
        reporting_framework: The client's configured framework ("auto", "fasb", "gasb")
        entity_type: The client's entity type ("for_profit", "nonprofit", "governmental", "other")
        jurisdiction_country: ISO 3166-1 alpha-2 country code
        jurisdiction_state: Optional sub-national region

    Returns:
        ResolvedFrameworkResult with framework, reason, and any warnings
    """
    warnings: list[str] = []
    fw = reporting_framework.lower().strip() if reporting_framework else "auto"
    et = entity_type.lower().strip() if entity_type else "other"
    country = jurisdiction_country.upper().strip() if jurisdiction_country else "US"

    # --- Precedence 1: Explicit framework override ---
    if fw == "fasb":
        return ResolvedFrameworkResult(
            framework=ResolvedFramework.FASB,
            resolution_reason=ResolutionReason.EXPLICIT_FASB,
        )

    if fw == "gasb":
        if et != "governmental":
            warnings.append(
                f"GASB explicitly selected but entity_type is '{et}', not 'governmental'. "
                "GASB standards are designed for governmental entities."
            )
        return ResolvedFrameworkResult(
            framework=ResolvedFramework.GASB,
            resolution_reason=ResolutionReason.EXPLICIT_GASB,
            warnings=tuple(warnings),
        )

    # --- From here, framework is AUTO — resolve from metadata ---

    # --- Precedence 2: Governmental entity → GASB ---
    if et == "governmental":
        return ResolvedFrameworkResult(
            framework=ResolvedFramework.GASB,
            resolution_reason=ResolutionReason.ENTITY_TYPE_GOVERNMENTAL,
        )

    # --- Precedence 3: For-profit entity → FASB ---
    if et == "for_profit":
        return ResolvedFrameworkResult(
            framework=ResolvedFramework.FASB,
            resolution_reason=ResolutionReason.ENTITY_TYPE_FOR_PROFIT,
        )

    # --- Precedence 4: Nonprofit in US → FASB (ASC 958) ---
    if et == "nonprofit" and country == "US":
        return ResolvedFrameworkResult(
            framework=ResolvedFramework.FASB,
            resolution_reason=ResolutionReason.ENTITY_TYPE_NONPROFIT_US,
        )

    # --- Precedence 5: US jurisdiction → FASB ---
    if country == "US":
        if et == "other":
            warnings.append(
                "Entity type is 'other' — defaulting to FASB for US jurisdiction. "
                "Set entity_type for more precise framework resolution."
            )
        return ResolvedFrameworkResult(
            framework=ResolvedFramework.FASB,
            resolution_reason=ResolutionReason.JURISDICTION_US_DEFAULT,
            warnings=tuple(warnings),
        )

    # --- Precedence 6: Fallback — FASB with warning ---
    warnings.append(
        f"No deterministic rule matched for country='{country}', entity_type='{et}'. "
        "Defaulting to FASB. Set reporting_framework explicitly if GASB is required."
    )
    return ResolvedFrameworkResult(
        framework=ResolvedFramework.FASB,
        resolution_reason=ResolutionReason.FALLBACK_FASB,
        warnings=tuple(warnings),
    )
