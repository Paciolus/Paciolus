"""Sprint 700: cross-registry contract compliance meta-test.

Walks every annotated generator/engine pair in the anomaly-framework
registries and verifies the generator's evidence satisfies the engine's
precondition. Runs in **report-only mode** during Sprints B–D: a
contract violation is logged to stdout and recorded in a summary list,
but the test does not fail. Sprint E will flip this to strict mode.

Why report-only for now?
  * The contract layer (``contract.py``) is new — no engine is annotated
    yet. In strict mode the test would be a no-op.
  * Sprints C and D will add contracts as they fix each known xfail.
    During that migration period we want the meta-test to SURFACE gaps
    (so the fixers know the scope) without BLOCKING commits (so the
    fixers can land partial progress).
  * Flipping to strict is a one-line change in Sprint E once the
    coverage is broad enough to make the gate meaningful.

Annotation discovery is opt-in: the meta-test introspects each engine
module for a module-level ``ENGINE_CONTRACT`` value and each generator
instance for a ``PRODUCES_EVIDENCE`` attribute. Anything without the
annotation is silently skipped.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterable

import pytest

from shared.engine_contract import (
    ContractViolation,
    EngineInputContract,
    GeneratorEvidence,
    check_contract,
)

# Mapping from anomaly-framework "tool" identifier → the engine module
# path. Keep alphabetized. When a new engine grows a contract, add its
# entry here so the meta-test discovers it.
_ENGINE_MODULES: dict[str, str] = {
    "ap": "ap_testing_engine",
    "ar_aging": "ar_aging_engine",
    "bank_reconciliation": "bank_reconciliation",
    "currency": "currency_engine",
    "fixed_asset": "fixed_asset_testing_engine",
    "inventory": "inventory_testing_engine",
    "je": "je_testing_engine",
    "multi_period": "multi_period_comparison",
    "payroll": "payroll_testing_engine",
    "revenue": "revenue_testing_engine",
    "sampling": "sampling_engine",
    "three_way_match": "three_way_match_engine",
}


def _load_engine_contracts() -> dict[str, EngineInputContract]:
    """Import each engine module and collect its ``ENGINE_CONTRACT``.

    Engines that haven't grown a contract yet are silently skipped —
    ``getattr`` returns ``None`` and the dict doesn't gain an entry.
    """
    contracts: dict[str, EngineInputContract] = {}
    for tool, module_path in _ENGINE_MODULES.items():
        try:
            module = importlib.import_module(module_path)
        except ImportError:
            # Module missing — surface via a test warning later rather
            # than crash the whole meta-test.
            continue
        contract = getattr(module, "ENGINE_CONTRACT", None)
        if isinstance(contract, EngineInputContract):
            contracts[tool] = contract
    return contracts


def _load_generator_evidence() -> list[tuple[str, str, GeneratorEvidence]]:
    """Walk the per-tool generator registries and pull any annotated
    ``PRODUCES_EVIDENCE``.

    Returns a list of ``(tool, generator_name, evidence)`` tuples.
    Generators without the annotation are silently skipped — they will
    be caught by Sprint E's strict-mode enforcement once every generator
    has one.
    """
    discoveries: list[tuple[str, str, GeneratorEvidence]] = []

    registry_modules = {
        "ap": "tests.anomaly_framework.generators.ap_generators",
        "ar_aging": "tests.anomaly_framework.generators.ar_generators",
        "currency": "tests.anomaly_framework.generators.currency_generators",
        "fixed_asset": "tests.anomaly_framework.generators.fa_generators",
        "inventory": "tests.anomaly_framework.generators.inv_generators",
        "je": "tests.anomaly_framework.generators.je_generators",
        "payroll": "tests.anomaly_framework.generators.payroll_generators",
        "revenue": "tests.anomaly_framework.generators.revenue_generators",
    }
    # Common registry attribute names used across the framework.
    registry_attrs = ("REGISTRY", "REGISTRY_SMALL")

    for tool, module_path in registry_modules.items():
        try:
            module = importlib.import_module(module_path)
        except ImportError:
            continue
        for base_name in ("AP", "AR", "CURRENCY", "FA", "INV", "JE", "PAYROLL", "REVENUE"):
            for suffix in registry_attrs:
                attr = f"{base_name}_{suffix}"
                registry: Iterable | None = getattr(module, attr, None)
                if registry is None:
                    continue
                for generator in registry:
                    evidence = getattr(generator, "PRODUCES_EVIDENCE", None)
                    if isinstance(evidence, GeneratorEvidence):
                        gen_name = getattr(generator, "name", repr(generator))
                        discoveries.append((tool, gen_name, evidence))

    return discoveries


def _collect_violations() -> list[ContractViolation]:
    """Run the contract check across every annotated pair.

    Pure function — safe to call from both the meta-test and a CI
    reporter script.
    """
    engine_contracts = _load_engine_contracts()
    evidence_records = _load_generator_evidence()

    violations: list[ContractViolation] = []
    for tool, generator_name, evidence in evidence_records:
        contract = engine_contracts.get(tool)
        if contract is None:
            # Engine has no contract yet — skip. This is expected during
            # Sprints B–D; Sprint E turns the skip into a hard failure.
            continue
        violations.extend(check_contract(contract, evidence, generator_name))
    return violations


@pytest.mark.anomaly_contract
def test_generator_engine_contracts_strict():
    """Sprint 703: STRICT mode — any contract violation fails the build.

    Report-only mode ran through Sprints B–D so annotations could land
    incrementally without punishing the engineer adding them. Sprints
    701/702 populated contracts for the tools that had xfailed
    generators (revenue, payroll, ar_aging, fixed_asset, inventory,
    currency) and closed every known drift. This sprint flips the
    gate: any NEW contract violation is a regression and must fail.

    If you hit a failure here:
      * A generator's ``PRODUCES_EVIDENCE`` doesn't satisfy the
        engine's ``DetectionPreconditions`` — reconcile the two (see
        the violation's ``missing_columns`` / ``missing_account_name_
        patterns`` / ``scope_mismatch`` fields for the specific gap).
      * A generator targets a ``test_key`` the engine's contract
        doesn't declare — either the engine's contract is incomplete
        or the generator is aimed at the wrong test.
    """
    violations = _collect_violations()
    if violations:
        lines = [f"{len(violations)} generator ↔ engine contract violation(s):"]
        for v in violations:
            lines.append(f"  • {v}")
        pytest.fail("\n".join(lines))


@pytest.mark.anomaly_contract
def test_every_declared_engine_module_is_importable():
    """Sanity: the tool→module map points at actually-importable modules.

    Sprint 700 guard so a typo in the _ENGINE_MODULES dict surfaces
    immediately rather than silently dropping an engine from compliance
    coverage.
    """
    import importlib as _importlib

    missing: list[str] = []
    for tool, module_path in _ENGINE_MODULES.items():
        try:
            _importlib.import_module(module_path)
        except ImportError:
            missing.append(f"{tool} → {module_path}")
    assert not missing, f"Unreachable engine modules: {missing}"
