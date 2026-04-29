"""Sprint 756 — route layer purity lint script tests.

Covers the engine-module + orchestration-symbol heuristics, the CLI flow, and
a smoke-check that the lint actually runs against the repo without errors.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lint_route_layer_purity import (  # noqa: E402 (path manipulation above)
    _is_engine_module,
    _is_orchestration_symbol,
    find_route_purity_violations,
    main,
)

# ---------------------------------------------------------------------------
# _is_engine_module
# ---------------------------------------------------------------------------


class TestIsEngineModule:
    def test_top_level_engine_module(self):
        assert _is_engine_module("flux_engine")
        assert _is_engine_module("ap_testing_engine")
        assert _is_engine_module("audit_engine")

    def test_dotted_engine_path(self):
        assert _is_engine_module("services.audit.flux.recon")
        assert _is_engine_module("subdir.flux_engine")

    def test_non_engine_module(self):
        assert not _is_engine_module("auth")
        assert not _is_engine_module("models")
        assert not _is_engine_module("shared.helpers")
        assert not _is_engine_module("services.auth.recovery")


# ---------------------------------------------------------------------------
# _is_orchestration_symbol
# ---------------------------------------------------------------------------


class TestIsOrchestrationSymbol:
    def test_engine_class_suffix(self):
        assert _is_orchestration_symbol("FluxEngine")
        assert _is_orchestration_symbol("ReconEngine")

    def test_run_prefix(self):
        assert _is_orchestration_symbol("run_je_testing")
        assert _is_orchestration_symbol("run_payroll_testing")

    def test_process_prefix(self):
        assert _is_orchestration_symbol("process_tb_chunked")

    def test_audit_trial_balance_entry_points(self):
        assert _is_orchestration_symbol("audit_trial_balance_streaming")
        assert _is_orchestration_symbol("audit_trial_balance_multi_sheet")

    def test_dataclass_imports_are_allowed(self):
        # These are types — routes legitimately import them for annotations.
        assert not _is_orchestration_symbol("FluxResult")
        assert not _is_orchestration_symbol("ReconScore")
        assert not _is_orchestration_symbol("RiskBand")
        assert not _is_orchestration_symbol("FluxItem")


# ---------------------------------------------------------------------------
# find_route_purity_violations (smoke check against the actual repo)
# ---------------------------------------------------------------------------


class TestFindViolations:
    def test_returns_tuples_of_path_lineno_module_symbol(self):
        violations = find_route_purity_violations()
        for path, lineno, module, symbol in violations:
            assert isinstance(path, Path)
            assert isinstance(lineno, int) and lineno > 0
            assert isinstance(module, str) and module
            assert isinstance(symbol, str) and symbol

    def test_does_not_flag_typed_dataclass_imports(self):
        """Routes that import only result dataclasses (FluxResult, etc.) for
        type annotations should NOT show up — those are the allowed boundary."""
        violations = find_route_purity_violations()
        for _path, _lineno, _module, symbol in violations:
            # The lint shouldn't have flagged a pure dataclass import.
            assert not symbol.endswith("Result"), f"Pure dataclass {symbol} was flagged — heuristic is too broad."
            assert not symbol.endswith("Score"), f"Pure dataclass {symbol} was flagged — heuristic is too broad."


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCli:
    def test_default_exit_zero(self, capsys):
        rc = main([])
        assert rc == 0  # Advisory mode — exit 0 regardless of findings.

    def test_strict_exit_reflects_findings(self, capsys):
        rc = main(["--strict"])
        # With several routes still importing run_<tool>() directly, --strict
        # currently exits 1. As routes thin out per ADR-015 it'll flip to 0.
        violations = find_route_purity_violations()
        if violations:
            assert rc == 1
        else:
            assert rc == 0

    def test_header_appears_in_output(self, capsys):
        main([])
        out = capsys.readouterr().out
        assert "Route layer purity" in out
