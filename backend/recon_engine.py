"""Backward-compatibility shim for the recon engine (Sprint 753, ADR-018).

The implementation moved to `services.audit.flux.recon` as the pilot
relocation under ADR-018's per-tool domain package layout. This module
re-exports the public API so existing `from recon_engine import ...`
statements continue to work without modification.

New code should import directly from the per-tool package:

    from services.audit.flux.recon import ReconEngine, ReconResult

See `docs/03-engineering/adr-018-domain-package-relocation.md` for the
migration approach.
"""

from services.audit.flux.recon import (  # noqa: F401
    ReconEngine,
    ReconResult,
    ReconScore,
    RiskBand,
)

__all__ = [
    "ReconEngine",
    "ReconResult",
    "ReconScore",
    "RiskBand",
]
