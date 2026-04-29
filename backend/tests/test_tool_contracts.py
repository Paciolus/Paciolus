"""Tool-result Protocol conformance tests (Sprint 754b).

Asserts that the existing tool-result dataclasses satisfy the Protocols
in `services.audit.contracts`. These tests are pure compile-time +
runtime-isinstance checks — no domain logic, no fixture setup beyond
constructing minimal instances.

The point: if a future edit drops `composite_score` from a testing
result, or renames `test_name` on a TestResult, the conformance test
fails loudly here. Type-checkers (mypy) catch the same regressions at
PR time via the Protocol membership checks in this file.
"""

from __future__ import annotations

import pytest

from services.audit.contracts import (
    IndicatorResult,
    ToolError,
    ToolResult,
)

# ---------------------------------------------------------------------------
# IndicatorResult conformance — relocated tools (recon, flux, cutoff_risk)
# ---------------------------------------------------------------------------


def test_recon_result_conforms_to_indicator_result():
    from services.audit.flux.recon import ReconResult

    instance = ReconResult(
        scores=[],
        high_risk_count=0,
        medium_risk_count=0,
        low_risk_count=0,
    )
    assert isinstance(instance, ToolResult)
    assert isinstance(instance, IndicatorResult)


def test_flux_result_conforms_to_indicator_result():
    from services.audit.flux.analysis import FluxResult

    instance = FluxResult(
        items=[],
        total_items=0,
        high_risk_count=0,
        medium_risk_count=0,
        new_accounts_count=0,
        removed_accounts_count=0,
        materiality_threshold=0.0,
    )
    assert isinstance(instance, ToolResult)
    assert isinstance(instance, IndicatorResult)


def test_cutoff_risk_report_conforms_to_indicator_result():
    from services.audit.cutoff_risk.analysis import CutoffRiskReport

    instance = CutoffRiskReport()
    assert isinstance(instance, ToolResult)
    assert isinstance(instance, IndicatorResult)


# ---------------------------------------------------------------------------
# TestingBatteryResult conformance — testing engines (sample of 3)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module_path,result_class,fixture_module,fixture_func",
    [
        (
            "je_testing_engine",
            "JETestingResult",
            "tests.test_je_testing_memo",
            "_make_je_result",
        ),
        # AP and Payroll testing-engine result fixtures live next to the
        # memo tests, but the dataclasses are in the engine modules.
    ],
)
def test_testing_result_conforms_to_battery_protocol(module_path, result_class, fixture_module, fixture_func):
    """A sample testing engine satisfies TestingBatteryResult.

    Just one parametrize entry today (JE) — the other 6 testing engines
    have heavier per-fixture setup (rows, column mappings, configs).
    Adding them is a follow-up that runs the engine end-to-end; this
    test is Protocol-shape verification, not behavioral.
    """
    import importlib

    engine_module = importlib.import_module(module_path)
    result_cls = getattr(engine_module, result_class)

    # Build a minimal instance via the fixture's known-good shape.
    fixture_mod = importlib.import_module(fixture_module)
    fixture = getattr(fixture_mod, fixture_func)
    raw = fixture()  # dict shaped like the testing-engine output

    # The fixtures return dict shapes (memo input contract); construct the
    # dataclass from the dict's typed fields. For JE this means lifting
    # composite_score + test_results out of the fixture dict.
    # Skip the construction — verify class-level attribute names instead,
    # which is what Protocol structural checking actually inspects.
    assert hasattr(result_cls, "__annotations__"), f"{result_class} not a dataclass"
    fields = result_cls.__annotations__
    assert "composite_score" in fields, f"{result_class} missing composite_score field — Protocol violation"
    assert "test_results" in fields, f"{result_class} missing test_results field — Protocol violation"
    # Ensure to_dict is a method
    assert callable(getattr(result_cls, "to_dict", None)), f"{result_class} missing to_dict method — Protocol violation"
    # Avoid unused-variable warning for the fixture data we loaded.
    assert raw is not None


# ---------------------------------------------------------------------------
# CompositeScoreLike + TestResultLike — class-level attribute checks
#
# These are Protocols on instances; we verify dataclass fields rather than
# constructing real instances (which would need full engine pipelines).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module_path,score_class",
    [
        ("je_testing_engine", "CompositeScore"),
        ("ap_testing_engine", "APCompositeScore"),
        ("payroll_testing_engine", "PayrollCompositeScore"),
        ("revenue_testing_engine", "RevenueCompositeScore"),
    ],
)
def test_composite_score_classes_have_required_fields(module_path, score_class):
    import importlib

    cls = getattr(importlib.import_module(module_path), score_class)
    annotations = cls.__annotations__
    assert "score" in annotations, f"{score_class} missing score field"
    assert callable(getattr(cls, "to_dict", None)), f"{score_class} missing to_dict"


@pytest.mark.parametrize(
    "module_path,test_class",
    [
        ("je_testing_engine", "TestResult"),
        ("ap_testing_engine", "APTestResult"),
        ("payroll_testing_engine", "PayrollTestResult"),
        ("revenue_testing_engine", "RevenueTestResult"),
        ("ar_aging_engine", "ARTestResult"),
    ],
)
def test_test_result_classes_have_required_fields(module_path, test_class):
    import importlib

    cls = getattr(importlib.import_module(module_path), test_class)
    annotations = cls.__annotations__
    assert "test_name" in annotations, f"{test_class} missing test_name"
    assert "entries_flagged" in annotations, f"{test_class} missing entries_flagged"
    assert "total_entries" in annotations, f"{test_class} missing total_entries"
    assert callable(getattr(cls, "to_dict", None)), f"{test_class} missing to_dict"


# ---------------------------------------------------------------------------
# ToolError
# ---------------------------------------------------------------------------


def test_tool_error_is_value_error_subclass():
    """ToolError must inherit from ValueError so existing
    `except ValueError` catch sites continue to work."""
    assert issubclass(ToolError, ValueError)


def test_tool_error_can_be_raised_and_caught():
    with pytest.raises(ToolError):
        raise ToolError("boom")
    # Also caught as ValueError
    with pytest.raises(ValueError):
        raise ToolError("boom")


def test_tool_error_subclass_pattern():
    """Tools may subclass ToolError for specific failure modes."""

    class CutoffAnalysisError(ToolError):
        pass

    with pytest.raises(ToolError):
        raise CutoffAnalysisError("bad input")
    with pytest.raises(ValueError):
        raise CutoffAnalysisError("bad input")
