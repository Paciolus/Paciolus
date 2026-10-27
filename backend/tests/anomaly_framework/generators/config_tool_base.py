"""Base for generators of the tools whose input is a config, not rows.

Sprint 823 item 3. The six tools Sprint 689 added after the framework was
built (SoD, intercompany, W-2/W-3, Form 1099, book-to-tax, cash flow
projector) take engine dataclasses — role matrices, entity trial balances,
W-2 drafts, vendor payments, adjustment lists, aging buckets — not the
uploaded rows the twelve row-shaped tools take. The pattern is the same:
a clean baseline, a deterministic injection, and an assertion about the
engine's own output. Only the input and the check change shape:

* ``ToolHarness.baseline()`` builds the clean config (a fresh object per call);
* ``ConfigGenerator.inject(config)`` returns a mutated copy plus the
  ``AnomalyRecord``;
* ``ConfigGenerator.detected(result)`` reads the engine's ``to_dict()``.

The detection test asserts ``detected`` is **False on the baseline** and
**True after injection**, so a generator cannot pass against an engine that
flags everything — the A-5 failure mode (a check that returned ``0.0`` happily
for the life of the product) is what the negative half is for.
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from tests.anomaly_framework.base import AnomalyRecord


@dataclass(frozen=True)
class ToolHarness:
    """How to build a clean input for one tool and run its engine on it."""

    tool: str  # tools_registry slug
    engine: str  # "module.function", for the coverage map
    baseline: Callable[[], Any]
    run: Callable[[Any], dict[str, Any]]


class ConfigGenerator:
    """One injected anomaly against a config-shaped engine input."""

    name: str
    target: str  # the output field the check reads, for the coverage map
    report_targets: list[str] = []
    injected_at: str = ""

    def mutate(self, config: Any) -> None:
        """Mutate ``config`` in place (it is already a deep copy)."""
        raise NotImplementedError

    def detected(self, result: dict[str, Any]) -> bool:
        raise NotImplementedError

    def inject(self, config: Any, seed: int = 42) -> tuple[Any, list[AnomalyRecord]]:
        mutated = deepcopy(config)
        self.mutate(mutated)
        record = AnomalyRecord(
            anomaly_type=self.name,
            report_targets=list(self.report_targets),
            injected_at=self.injected_at,
            expected_field=self.target,
            expected_condition="detected(result) is True; False on the clean baseline",
        )
        return mutated, [record]
