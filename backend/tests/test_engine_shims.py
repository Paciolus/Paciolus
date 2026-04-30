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
    # Sprint 753 + post-initiative engine batch — original explicit-list shims.
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


# Testing engine relocations (post-initiative finishing pass) — 7 engines
# with 35–53 public symbols each + several private test helpers. Use a
# spot-check sentinel rather than enumerating the full namespace; the
# dynamic-namespace shim pattern in each legacy module guarantees full
# coverage by construction.
TESTING_ENGINE_SENTINELS = [
    # (legacy_module, canonical_module, sentinel_symbol)
    ("ap_testing_engine", "services.audit.ap_testing.analysis", "APTestingResult"),
    ("ar_aging_engine", "services.audit.ar_aging.analysis", "ARAgingResult"),
    (
        "fixed_asset_testing_engine",
        "services.audit.fixed_asset_testing.analysis",
        "FATestingResult",
    ),
    (
        "inventory_testing_engine",
        "services.audit.inventory_testing.analysis",
        "InvTestingResult",
    ),
    ("je_testing_engine", "services.audit.je_testing.analysis", "JETestingResult"),
    (
        "payroll_testing_engine",
        "services.audit.payroll_testing.analysis",
        "PayrollTestingResult",
    ),
    (
        "revenue_testing_engine",
        "services.audit.revenue_testing.analysis",
        "RevenueTestingResult",
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


@pytest.mark.parametrize("legacy,canonical,sentinel", TESTING_ENGINE_SENTINELS)
def test_testing_engine_shim_re_exports_canonical_namespace(legacy, canonical, sentinel):
    """The dynamic-namespace shim pattern re-exports the canonical surface.

    Spot-check: pick one well-known sentinel symbol per engine, assert it
    appears on both paths and is the same object. Combined with the live
    `dir()` namespace copy in each shim, this guarantees full surface
    coverage without enumerating 35+ symbols per engine.
    """
    legacy_module = __import__(legacy)
    canonical_module = __import__(canonical, fromlist=["_"])

    assert hasattr(canonical_module, sentinel), f"{canonical} missing sentinel {sentinel}"
    assert hasattr(legacy_module, sentinel), f"{legacy} shim didn't re-export sentinel {sentinel}"
    assert getattr(legacy_module, sentinel) is getattr(canonical_module, sentinel), (
        f"{legacy}.{sentinel} is not the same object as {canonical}.{sentinel}"
    )


@pytest.mark.parametrize("legacy,canonical,_sentinel", TESTING_ENGINE_SENTINELS)
def test_testing_engine_shim_exposes_underscore_helpers(legacy, canonical, _sentinel):
    """The dynamic-namespace shim must expose private (underscore-prefixed)
    helpers too — several test files import them directly.

    Verifies that any non-dunder name on the canonical path appears on
    the legacy shim. If a helper is renamed on the canonical, the shim
    drops it and existing imports fail loudly.
    """
    legacy_module = __import__(legacy)
    canonical_module = __import__(canonical, fromlist=["_"])

    canonical_names = {name for name in dir(canonical_module) if not name.startswith("__")}
    legacy_names = {name for name in dir(legacy_module) if not name.startswith("__")}

    missing = canonical_names - legacy_names
    assert not missing, (
        f"{legacy} shim missing names from canonical: {sorted(missing)}. "
        f"The dynamic re-export loop in the shim should have copied these."
    )
