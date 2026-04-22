"""Sprint 700: Generator ↔ Engine contract layer.

The anomaly-injection framework (``tests/anomaly_framework/``) ships 100+
generators that mutate clean fixture data to exercise specific detection
paths in the 12 testing-tool engines. Prior to Sprint 700 there was no
formal boundary between the shape a generator produces and the shape an
engine actually inspects — when the two drifted, the only signal was a
test assertion failing, at which point the fix would get an ``xfail``
marker and sit unaddressed.

The contract layer makes the boundary explicit so:

  1. Every engine declares what columns it reads and what preconditions
     each of its test_keys requires.
  2. Every generator can declare what evidence it injects (which columns
     it populates, which test_keys it expects to trip).
  3. A meta-test walks every (generator, engine) pair in the registry
     and verifies the generator's evidence satisfies the engine's
     preconditions for its declared target test_key. Any mismatch is
     surfaced as a contract violation, not a silent xfail.

Annotations are **opt-in**: an engine or generator with no contract
annotation is simply skipped by the meta-test. That keeps this sprint's
deliverable the infrastructure + one worked example; Sprints C/D add
contracts for the specific mismatches they close; Sprint E flips the
meta-test from "report violations" to "fail on violations" once coverage
is meaningful.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Scope = Literal["tb", "sub_ledger", "standalone", "either"]
"""Where an engine expects to find the evidence for a given detection.

* ``tb`` — the evidence must live in trial-balance rows (e.g. AR sign
  mismatch is a TB-level concept).
* ``sub_ledger`` — the evidence must live in sub-ledger / detail rows
  (e.g. invoice-level AR aging; bank-reconciliation bank-statement rows).
* ``standalone`` — single-source engines (JE, Revenue, AP, etc.).
* ``either`` — the engine accepts the evidence from either side. Used
  sparingly; most real detections care about one side specifically.
"""


@dataclass(frozen=True)
class DetectionPreconditions:
    """What an engine's test_key needs to see to fire.

    Every entry in ``EngineInputContract.detection_targets`` maps a
    test_key (the string the engine uses to identify a specific test,
    e.g. ``"revenue_contra_detection"``) to one of these records.

    A generator "satisfies" the precondition when:

      * Every name in ``requires_columns`` appears in the generator's
        produced row keys.
      * If ``account_name_patterns`` is non-empty, at least one of the
        generator-emitted account-name values matches one of the
        patterns (case-insensitive substring match).
      * The generator's declared ``scope`` equals the precondition's
        ``scope`` (or the precondition's scope is ``"either"``).

    Any unmet predicate is reported by the meta-test as a named
    contract violation so the gap is debuggable instead of just "xfail".
    """

    # Columns that must be present in the row dicts the engine receives.
    # Match is by exact column name (case-sensitive) — upstream ingestion
    # normalises case/whitespace before the engine sees the data.
    requires_columns: frozenset[str] = field(default_factory=frozenset)

    # Optional: substring(s) in the Account Name that activate this test.
    # Used for pattern-based detections like contra-revenue ("Returns",
    # "Allowances", "Refunds"). Empty set = the test doesn't gate on
    # account-name content.
    account_name_patterns: frozenset[str] = field(default_factory=frozenset)

    # Where the evidence must live. Drives generator/engine wiring for
    # dual-source engines (AR Aging: TB + sub-ledger; Bank Rec: bank +
    # GL). Default ``"standalone"`` matches the majority of engines.
    scope: Scope = "standalone"

    # Free-form text: what this detection is looking for, and the
    # auditing-standard or fraud-taxonomy citation that justifies it.
    # This is the most load-bearing field when an auditor pulls the
    # memo and asks "why did this fire?" — we want the answer in the
    # contract, not buried in the engine.
    description: str = ""

    # Optional: name(s) of flags/fields the engine populates on success
    # (e.g. ``reversal_category``, ``concentration_percent``). Surfaced
    # in the meta-test output so downstream consumers can audit contract
    # drift without reading the engine.
    emits_fields: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class EngineInputContract:
    """Declarative contract for a single testing-tool engine.

    Attach one of these to an engine module by assigning a module-level
    ``ENGINE_CONTRACT = EngineInputContract(...)`` value. The meta-test
    auto-discovers it by module name.

    ``detection_targets`` is the core data — a dict keyed on the
    engine's canonical test_key (matching the ``test_key`` string the
    engine emits in its ``TestResult``). Keep this in lock-step with
    the engine's actual test registry; Sprint 703's CI gate will fail
    the build if a contract references a test_key the engine doesn't
    emit, or vice versa.
    """

    # Human-readable engine identifier (``"revenue"``, ``"payroll"``, …).
    # Matches the convention used in the anomaly-framework registries.
    tool: str

    # Columns the engine's main entry point reads. The meta-test verifies
    # every generator targeting this engine emits rows containing at
    # least these columns.
    required_columns: frozenset[str]

    # Columns the engine tolerates but does not require. Included so the
    # contract is complete — an auditor reading the memo shouldn't be
    # surprised by a column they didn't see documented.
    optional_columns: frozenset[str] = field(default_factory=frozenset)

    # Per-test preconditions. Key = engine's canonical test_key.
    detection_targets: dict[str, DetectionPreconditions] = field(default_factory=dict)

    # Free-form: where the engine's entry point lives, so the meta-test
    # can produce a jump-to-source link in its violation report.
    entry_point: str = ""


@dataclass(frozen=True)
class GeneratorEvidence:
    """What a single generator promises to inject.

    Attach to a generator instance as a class attribute
    ``PRODUCES_EVIDENCE = GeneratorEvidence(...)`` (or let it default to
    an empty evidence record — the meta-test will then skip the
    precondition check for that generator).
    """

    # test_key the generator is designed to trip. Matches the key used
    # in the engine's contract.detection_targets.
    target_test_key: str

    # Columns the generator guarantees it populates in every injected row.
    # Compared against ``DetectionPreconditions.requires_columns``.
    populates_columns: frozenset[str] = field(default_factory=frozenset)

    # Account-name substrings the generator writes into injected rows.
    # Compared against ``DetectionPreconditions.account_name_patterns``.
    account_name_values: frozenset[str] = field(default_factory=frozenset)

    # Where the generator writes the evidence. Matches the scope model
    # in ``DetectionPreconditions``.
    scope: Scope = "standalone"

    # Optional free-form: a short explanation of the injection shape.
    # Appears in the meta-test's violation report if the contract check
    # fails.
    notes: str = ""


@dataclass(frozen=True)
class ContractViolation:
    """Structured record of a single generator/engine contract mismatch.

    Emitted by the meta-test when it walks the registries and finds a
    generator whose evidence does not satisfy its target engine's
    precondition. The meta-test aggregates these into a report that
    later sprints consume as a worklist.
    """

    tool: str
    generator_name: str
    test_key: str
    missing_columns: frozenset[str] = field(default_factory=frozenset)
    missing_account_name_patterns: frozenset[str] = field(default_factory=frozenset)
    scope_mismatch: tuple[Scope, Scope] | None = None  # (engine_scope, generator_scope)
    notes: str = ""

    def __str__(self) -> str:  # pragma: no cover — diagnostic formatting
        parts = [f"[{self.tool}/{self.generator_name} → {self.test_key}]"]
        if self.missing_columns:
            parts.append(f"missing columns: {sorted(self.missing_columns)}")
        if self.missing_account_name_patterns:
            parts.append(f"missing account-name patterns: {sorted(self.missing_account_name_patterns)}")
        if self.scope_mismatch is not None:
            parts.append(f"scope mismatch: engine={self.scope_mismatch[0]} generator={self.scope_mismatch[1]}")
        if self.notes:
            parts.append(self.notes)
        return " | ".join(parts)


def check_contract(
    engine_contract: EngineInputContract,
    generator_evidence: GeneratorEvidence,
    generator_name: str,
) -> list[ContractViolation]:
    """Verify a generator's evidence satisfies an engine's precondition.

    Returns a list of ``ContractViolation`` records — empty list means
    the generator satisfies the contract. Multiple violations can be
    returned per (generator, engine) pair so the meta-test can surface
    every gap in one pass rather than "fix one, discover the next".

    The function is deliberately pure (no imports, no side effects) so
    it can be unit-tested in isolation and so Sprint E's CI gate can
    call it in a tight loop over hundreds of generator/engine pairs.
    """
    violations: list[ContractViolation] = []

    precondition = engine_contract.detection_targets.get(generator_evidence.target_test_key)
    if precondition is None:
        # The generator targets a test_key the engine doesn't declare.
        # Surface as a first-class violation — either the test_key was
        # renamed, the generator targets the wrong test, or the engine's
        # contract is incomplete.
        return [
            ContractViolation(
                tool=engine_contract.tool,
                generator_name=generator_name,
                test_key=generator_evidence.target_test_key,
                notes=(
                    f"engine '{engine_contract.tool}' has no contract entry "
                    f"for test_key '{generator_evidence.target_test_key}'"
                ),
            )
        ]

    missing_cols = precondition.requires_columns - generator_evidence.populates_columns

    # Pattern match is substring-based (case-insensitive): a pattern is
    # "satisfied" if at least one generator-emitted value contains the
    # pattern string. This is the shape real-world account-name
    # detection works — engines look for "returns" anywhere in the
    # account name, not for an exact equality.
    lowered_values = {v.lower() for v in generator_evidence.account_name_values}
    missing_patterns = {
        pattern
        for pattern in precondition.account_name_patterns
        if not any(pattern in value for value in lowered_values)
    }

    scope_mismatch: tuple[Scope, Scope] | None = None
    if precondition.scope != "either" and precondition.scope != generator_evidence.scope:
        scope_mismatch = (precondition.scope, generator_evidence.scope)

    if missing_cols or missing_patterns or scope_mismatch:
        violations.append(
            ContractViolation(
                tool=engine_contract.tool,
                generator_name=generator_name,
                test_key=generator_evidence.target_test_key,
                missing_columns=frozenset(missing_cols),
                missing_account_name_patterns=frozenset(missing_patterns),
                scope_mismatch=scope_mismatch,
                notes=generator_evidence.notes,
            )
        )

    return violations
