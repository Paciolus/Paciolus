"""
AICPA Audit Sampling Guide lookups.

**Sprint 805 (finding A-2) rewrote this module.** It is now a thin, compatible
surface over `shared/audit_figure_registry.py`, which holds the published figures
with their provenance. Nothing here tabulates a number.

What was wrong, and why it is worth recording:

Sprint 684 replaced a homemade `1 + e/TM` approximation with a *two-dimensional*
expansion-factor table keyed by `(confidence_level, expected/tolerable)`, rising
to 3.00, cited to "Appendix A Table A-1", and multiplied it into the reliability
factor. The published AICPA expansion factor is one-dimensional — it depends only
on the **risk of incorrect acceptance** (1.9 / 1.6 / 1.5 / 1.4 / 1.3 / 1.25 / 1.2
/ 1.15 / 1.0 for 1%…50%) — and it enters the sample-size formula in the
denominator, scaling expected misstatement:

    n = BV x RF / (TM - EM x EF)

Measured consequence at BV $10M, TM $500k, 95%: sample sizes ran 1.06x to
**1.40x** the size the standard requires. The direction is conservative, so no
audit conclusion was endangered — but the client was billed for up to 40% more
items than the method calls for, under a citation that does not support the
figure. And Sprint 684's own commit message argued that the *previous*
approximation under-sized samples; at e/TM = 0.25 that approximation reproduced
the AICPA formula exactly, so Sprint 684 replaced a correct result with an
incorrect one on the strength of a table that does not exist in the form
described.

That is the pattern finding A-9 is about, and the registry is the response to it.

References
----------
AICPA Audit Sampling Guide (2019 edition; values unchanged in the 2023 revision).
ISA 530 / PCAOB AS 2315 govern the method.
"""

from __future__ import annotations

from shared.audit_figure_registry import expansion_factor as _registry_expansion_factor
from shared.audit_figure_registry import reliability_factor as _registry_reliability_factor

__all__ = ["expansion_factor", "reliability_factor"]


def expansion_factor(confidence_level: float) -> float:
    """
    Published expansion factor for expected misstatement.

    Depends on the risk of incorrect acceptance alone. Applied to **expected
    misstatement** in the denominator of the sample-size formula, not to the
    reliability factor.

    Note the signature change from Sprint 684's
    `expansion_factor(confidence_level, expected_misstatement,
    tolerable_misstatement)`: the expected/tolerable ratio is not an input to the
    published table, so accepting it invited exactly the two-dimensional
    tabulation that was wrong.
    """
    return _registry_expansion_factor(confidence_level)


def reliability_factor(confidence_level: float, overstatements: int = 0) -> float:
    """Poisson reliability factor for monetary unit sampling."""
    return _registry_reliability_factor(confidence_level, overstatements)
