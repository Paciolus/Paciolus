"""Backward-compatibility shim for the flux engine.

The implementation moved to ``services.audit.flux.analysis`` per ADR-018
(Sprint 753 pattern, Sprint 748b/759 follow-up). This module re-exports
the public API so existing ``from flux_engine import ...`` statements
continue to work without modification.

New code should import directly from the per-tool package:

    from services.audit.flux.analysis import FluxEngine, FluxResult

See ``docs/03-engineering/adr-018-domain-package-relocation.md`` for the
migration approach.
"""

from services.audit.flux.analysis import (  # noqa: F401
    NEAR_ZERO,
    FluxEngine,
    FluxItem,
    FluxResult,
    FluxRisk,
)

__all__ = [
    "FluxEngine",
    "FluxItem",
    "FluxResult",
    "FluxRisk",
    "NEAR_ZERO",
]
