"""
Flux + Recon domain package (Sprint 753 — ADR-018 pilot).

Hosts the per-tool layout for the flux/recon analysis pair:
  - `recon.py` — `ReconEngine`, `ReconResult`, `ReconScore`, `RiskBand`.
    (Sprint 753 pilot — relocated from `backend/recon_engine.py` which
    is now a backward-compat shim re-exporting from here.)

Future sub-sprints can co-locate `flux_engine.py` here as `analysis.py`
and the existing `services/audit/flux_service.py` orchestrator can move
under this package as `service.py` once the engine relocates.
"""
