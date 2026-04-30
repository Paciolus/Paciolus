"""Shared tool-result contracts (Sprint 754b — ADR-019).

Three Protocols document the result shapes Paciolus tools produce. The
Protocols are **structural** (PEP 544) — tools satisfy them by having
the right attributes / methods, no inheritance required. This means:

- Existing dataclasses (FluxResult, ReconResult, CutoffRiskReport,
  JETestingResult, APTestingResult, ...) already conform — no code
  changes needed for the 18 tools to satisfy these contracts.
- New tools can implement either shape (or both) without coordinating
  on a base-class hierarchy.
- Tests in `tests/test_tool_contracts.py` assert specific tools
  conform; type-checkers (mypy / pyright) can flag drift via
  ``isinstance(result, IndicatorResult)`` runtime checks (Protocols
  are ``@runtime_checkable`` here).

## Two shapes observed

**IndicatorResult** — a single analysis signal with aggregated counts.
Examples: FluxResult, ReconResult, CutoffRiskReport. Used for
analytical procedures (ISA 520) and indicator engines that don't run
a test battery.

**TestingBatteryResult** — composite of multiple discrete tests with
an aggregate score and risk tier. Examples: JETestingResult,
APTestingResult, PayrollTestingResult, RevenueTestingResult,
ARAgingResult, FixedAssetTestingResult, InventoryTestingResult.
Used for ISA 240 / ISA 500 substantive testing surfaces.

## Why Protocol, not ABC

The two shapes have meaningful per-tool variation in their fields
(e.g., ``CompositeScore`` has ``flags_by_severity``, ``APCompositeScore``
adds ``duplicate_payment_summary``). Forcing a common base class would
either (a) discard those fields or (b) push them into a base with
``Optional`` everywhere, both worse than today's per-tool dataclasses.

Protocols give us the contract documentation + runtime-isinstance
checking + mypy support without forcing field-set convergence.

## Why not merge into one shape

Tried it; it requires every result to expose either ``items`` or
``test_results`` (depending on shape) plus aggregate counts that mean
different things in each case. The result was a Protocol with so
many ``Optional`` fields it taught nothing. Two narrow Protocols
beat one wide one.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ToolResult(Protocol):
    """Base contract: every tool result must serialize to a dict.

    All Paciolus tools already implement ``to_dict()`` for the
    Pydantic-response and CSV / PDF / Excel export pipelines. This
    Protocol formalizes that minimum surface as a runtime-checkable
    contract.
    """

    def to_dict(self) -> dict[str, Any]: ...


@runtime_checkable
class IndicatorResult(ToolResult, Protocol):
    """A single analytical-procedure result.

    Tools producing one signal (flux, recon, cutoff risk, going concern,
    account risk heatmap, expense category) satisfy this shape:

    - A list of items / scores / flagged accounts (variable name varies
      by domain — ``items``, ``scores``, ``flagged_accounts``).
    - One or more aggregate counts (high/medium/low risk, flag count).
    - ``to_dict()`` for serialization.

    The Protocol intentionally doesn't pin the items-list attribute name —
    that varies by domain idiom (``flagged_accounts`` for cutoff risk,
    ``scores`` for recon, ``items`` for flux). Conformance is verified
    case-by-case in ``tests/test_tool_contracts.py``.
    """

    def to_dict(self) -> dict[str, Any]: ...


@runtime_checkable
class TestingBatteryResult(ToolResult, Protocol):
    """A composite result of multiple discrete tests.

    Tools that run a test battery (JE Testing, AP Testing, Payroll
    Testing, Revenue Testing, AR Aging, Fixed Asset Testing, Inventory
    Testing) satisfy this shape:

    - ``composite_score`` — a ``CompositeScoreLike`` object aggregating
      score, risk_tier, tests_run, etc.
    - ``test_results`` — a list of ``TestResultLike`` items.
    - ``to_dict()`` for serialization.
    """

    __test__ = False  # pytest collection marker — name starts with "Test"

    composite_score: CompositeScoreLike
    test_results: list[TestResultLike]

    def to_dict(self) -> dict[str, Any]: ...


@runtime_checkable
class CompositeScoreLike(Protocol):
    """A testing-battery composite score.

    Every ``<Tool>CompositeScore`` dataclass already exposes these. The
    Protocol formalizes the minimum overlap; tools may add tool-specific
    fields (``flags_by_severity``, ``benford_pass``, etc.) freely.
    """

    score: float
    """0–100, higher = more risk."""

    def to_dict(self) -> dict[str, Any]: ...


@runtime_checkable
class TestResultLike(Protocol):
    """A single test within a testing battery.

    ``test_name``, ``entries_flagged``, and ``total_entries`` are the
    minimum every per-tool ``<Tool>TestResult`` exposes; the Protocol
    captures that contract.
    """

    __test__ = False  # pytest collection marker — name starts with "Test"

    test_name: str
    entries_flagged: int
    total_entries: int

    def to_dict(self) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Error semantics
# ---------------------------------------------------------------------------


class ToolError(ValueError):
    """Base exception for tool-level business-logic failures.

    Sprint 746a established the pattern of ``<Domain>Error(ValueError)``
    subclasses raised by services and mapped to ``HTTPException(400)``
    by routes (e.g., ``PasswordResetError`` in
    ``services/auth/recovery.py``). ``ToolError`` is the analogous base
    for ``services/audit/<tool>/`` services.

    Tools may subclass directly (``CutoffAnalysisError(ToolError)``) or
    inherit from ``ValueError`` directly when the existing pattern is
    already in use. Both are accepted; the route layer's
    ``raise_http_error`` helper handles either.

    Why a shared base: future cross-tool error handlers (e.g., a service
    boundary helper that maps any ``ToolError`` to a uniform 4xx
    response) need a discriminator. Inheritance from ``ValueError``
    preserves existing ``except ValueError`` catch sites.
    """
