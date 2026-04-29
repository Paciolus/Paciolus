"""
Sprint 753: pin the `recon_engine` backward-compat shim.

Per ADR-018, the implementation moved to `services.audit.flux.recon`.
The legacy `recon_engine` module re-exports the public API. This test
asserts the two import paths return identical objects, so a future
edit that drops or renames a symbol in the new location surfaces here
loudly instead of silently breaking the ~6 existing call sites.
"""

import recon_engine
from services.audit.flux import recon as canonical


def test_shim_re_exports_all_public_symbols():
    """Every public symbol on the canonical path is re-exported by the shim."""
    canonical_symbols = {"ReconEngine", "ReconResult", "ReconScore", "RiskBand"}
    for symbol in canonical_symbols:
        assert hasattr(canonical, symbol), f"canonical missing {symbol}"
        assert hasattr(recon_engine, symbol), f"shim missing {symbol}"
        assert getattr(recon_engine, symbol) is getattr(canonical, symbol), (
            f"shim's {symbol} is not the same object as the canonical one"
        )


def test_shim_all_matches_canonical_public_symbols():
    """`__all__` on the shim matches the relocated public surface."""
    assert set(recon_engine.__all__) == {
        "ReconEngine",
        "ReconResult",
        "ReconScore",
        "RiskBand",
    }


def test_recon_engine_class_constructible_via_shim():
    engine = recon_engine.ReconEngine(materiality_threshold=1000.0)
    assert engine.materiality_threshold == 1000.0
