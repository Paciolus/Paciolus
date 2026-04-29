"""
Flux + Recon domain package (Sprint 753 + 759 follow-up — ADR-018).

Per-tool layout for the flux/recon analysis pair:
  - `analysis.py` — `FluxEngine`, `FluxResult`, `FluxItem`, `FluxRisk`,
    `NEAR_ZERO`. Sprint 759 follow-up: relocated from
    `backend/flux_engine.py`, which is now a shim.
  - `recon.py` — `ReconEngine`, `ReconResult`, `ReconScore`, `RiskBand`.
    Sprint 753 pilot: relocated from `backend/recon_engine.py`, which
    is now a shim.

Both `backend/flux_engine.py` and `backend/recon_engine.py` re-export the
public APIs for backward compatibility — existing
`from flux_engine import ...` and `from recon_engine import ...`
statements continue to work. New code should import from the per-tool
package directly.

The existing `services/audit/flux_service.py` orchestrator can move
under this package as `service.py` in a future sprint.
"""
