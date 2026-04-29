"""Engine relocation shim contract tests (ADR-018).

Pins the symbol identity between each top-level shim module and its
canonical relocation target. A future edit that drops or renames a
symbol on the canonical path surfaces here loudly instead of silently
breaking call sites that import via the legacy path.

Mirrors `tests/test_recon_engine_shim.py` (Sprint 753 — first shim).
Added as engines relocate.
"""

from __future__ import annotations

import pytest

SHIM_TARGETS = [
    # (legacy_module, canonical_module, public_symbols)
    (
        "flux_engine",
        "services.audit.flux.analysis",
        ["FluxEngine", "FluxItem", "FluxResult", "FluxRisk", "NEAR_ZERO"],
    ),
    (
        "cutoff_risk_engine",
        "services.audit.cutoff_risk.analysis",
        [
            "CUTOFF_SENSITIVE_KEYWORDS",
            "CutoffFlag",
            "CutoffRiskReport",
            "NEAR_ZERO",
            # Test-private helpers — `tests/test_cutoff_risk.py` imports
            # them directly, so they're part of the documented surface.
            "_is_cutoff_sensitive",
            "_test_round_number",
            "_test_spike",
            "_test_zero_balance",
            "compute_cutoff_risk",
        ],
    ),
]


@pytest.mark.parametrize("legacy,canonical,symbols", SHIM_TARGETS)
def test_shim_re_exports_canonical_symbols(legacy, canonical, symbols):
    """Every public symbol on the canonical path is the same object on the shim."""
    legacy_module = __import__(legacy)
    canonical_module = __import__(canonical, fromlist=["_"])

    for symbol in symbols:
        assert hasattr(canonical_module, symbol), f"{canonical}.{symbol} missing"
        assert hasattr(legacy_module, symbol), f"{legacy}.{symbol} missing"
        assert getattr(legacy_module, symbol) is getattr(canonical_module, symbol), (
            f"{legacy}.{symbol} is not the same object as {canonical}.{symbol}"
        )


@pytest.mark.parametrize("legacy,_canonical,symbols", SHIM_TARGETS)
def test_shim_all_matches_documented_surface(legacy, _canonical, symbols):
    """The legacy shim's `__all__` enumerates exactly the documented surface."""
    legacy_module = __import__(legacy)
    assert hasattr(legacy_module, "__all__"), f"{legacy} missing __all__"
    assert set(legacy_module.__all__) == set(symbols), f"{legacy}.__all__ drifted from documented surface"
