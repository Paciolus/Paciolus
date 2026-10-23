"""
Sprint 805 (finding A-9) — a single source of truth for *published figures*, with
provenance attached.

`standards_registry.py` and `tools_registry.py` already do this for citations and
the tool catalog, and `test_citation_consistency.py` enforces them. Numbers had no
equivalent: published figures lived as bare literals next to a prose citation, with
nothing tying them to the authority they named. Where that pattern exists, **a
free-floating literal is indistinguishable from a verified one, and both read as
cited.** The 2026-10-22 full-spectrum review found four instances of it (A-1, A-2,
A-7, A-8); the DEC review had found a fifth shape in the monetary-precision guard.

Two principles this module exists to enforce:

1. **Provenance travels with the value.** Every figure set carries its source,
   edition, who checked it and when. A figure with no verification stamp is a
   figure nobody has checked, and that is visible rather than invisible.
2. **Derive, don't tabulate.** Where one published series is arithmetically
   determined by another, the derived one is computed, never typed in. The
   Stringer incremental allowances *are* the first differences of the Poisson
   reliability factors, so they are computed from them here. Finding A-1 existed
   precisely because they had been typed in separately and did not agree with any
   published series.

References
----------
AICPA Audit Sampling Guide (2019 edition; values unchanged in the 2023 revision):
Poisson reliability factors for monetary unit sampling, and the expansion factor
for expected misstatement. ISA 530 / PCAOB AS 2315 govern the method.
"""

from __future__ import annotations

from dataclasses import dataclass

# ═══════════════════════════════════════════════════════════════
# Provenance
# ═══════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class FigureSet:
    """
    A published numeric series, with the provenance needed to audit it.

    `verified_by` / `verified_on` are not decoration. A reader of a workpaper
    that cites this figure needs to know who checked it against the authority
    and when, and so does the next engineer who is tempted to edit a literal.
    """

    values: tuple[float, ...]
    source: str
    edition: str
    verified_by: str
    verified_on: str
    note: str = ""

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("a FigureSet must carry at least one value")
        if not self.verified_by or not self.verified_on:
            raise ValueError(f"{self.source}: a figure set without a verification stamp is not usable")


# How the sampling figures below were checked. Recorded once, referenced by each
# figure set, so the provenance statement cannot drift between them.
_RF_VERIFICATION = (
    "Checked against the published Poisson reliability-factor series. The 95%, 90% "
    "and 99% rows were corroborated independently by the 2026-10-22 full-spectrum "
    "review, which restated their first differences (95%: 1.75/1.55/1.46/1.40/1.36/"
    "1.33/1.30; 90%: 1.58/1.44/1.36/1.31/1.28/1.26/1.24; 99% rank 1: 2.03) and found "
    "the shipped tables matched neither. `tests/test_audit_figure_registry.py` pins "
    "every derived increment back to the series it comes from."
)

_RF_UNCORROBORATED = (
    "Standard published Poisson series. Unlike the 95%/90%/99% rows, this row was "
    "not independently restated by the 2026-10-22 review; it is the conventional "
    "table and is used only when an engagement explicitly selects this confidence "
    "level. Flagged for practitioner confirmation alongside Sprint 793b."
)


# ═══════════════════════════════════════════════════════════════
# Poisson reliability factors (monetary unit sampling)
# ═══════════════════════════════════════════════════════════════
#
# Keyed by **risk of incorrect acceptance** (1 − confidence level), which is how
# the published table is keyed. Index i is the factor for i overstatements, so
# index 0 is the zero-misstatement factor used for sample planning and basic
# precision.

POISSON_RELIABILITY_FACTORS: dict[float, FigureSet] = {
    0.01: FigureSet(
        values=(4.61, 6.64, 8.41, 10.05, 11.61, 13.11, 14.57, 16.00, 17.41, 18.79, 20.15),
        source="AICPA Audit Sampling Guide — Poisson reliability factors, 1% risk of incorrect acceptance",
        edition="2019 (unchanged 2023)",
        verified_by=_RF_VERIFICATION,
        verified_on="2026-10-23",
    ),
    0.03: FigureSet(
        values=(3.51, 5.33, 6.91, 8.39, 9.81, 11.19, 12.53, 13.85, 15.15, 16.43, 17.70),
        source="AICPA Audit Sampling Guide — Poisson reliability factors, 3% risk of incorrect acceptance",
        edition="2019 (unchanged 2023)",
        verified_by=_RF_UNCORROBORATED,
        verified_on="2026-10-23",
    ),
    0.05: FigureSet(
        values=(3.00, 4.75, 6.30, 7.76, 9.16, 10.52, 11.85, 13.15, 14.44, 15.71, 16.97),
        source="AICPA Audit Sampling Guide — Poisson reliability factors, 5% risk of incorrect acceptance",
        edition="2019 (unchanged 2023)",
        verified_by=_RF_VERIFICATION,
        verified_on="2026-10-23",
        note="The default for Paciolus' MUS flow.",
    ),
    0.10: FigureSet(
        values=(2.31, 3.89, 5.33, 6.69, 8.00, 9.28, 10.54, 11.78, 13.00, 14.21, 15.41),
        source="AICPA Audit Sampling Guide — Poisson reliability factors, 10% risk of incorrect acceptance",
        edition="2019 (unchanged 2023)",
        verified_by=_RF_VERIFICATION,
        verified_on="2026-10-23",
    ),
    0.15: FigureSet(
        values=(1.90, 3.38, 4.73, 6.02, 7.27, 8.50, 9.71, 10.90, 12.08, 13.25, 14.42),
        source="AICPA Audit Sampling Guide — Poisson reliability factors, 15% risk of incorrect acceptance",
        edition="2019 (unchanged 2023)",
        verified_by=_RF_UNCORROBORATED,
        verified_on="2026-10-23",
    ),
    0.20: FigureSet(
        values=(1.61, 3.00, 4.28, 5.52, 6.72, 7.91, 9.08, 10.24, 11.38, 12.52, 13.66),
        source="AICPA Audit Sampling Guide — Poisson reliability factors, 20% risk of incorrect acceptance",
        edition="2019 (unchanged 2023)",
        verified_by=_RF_UNCORROBORATED,
        verified_on="2026-10-23",
    ),
}


# ═══════════════════════════════════════════════════════════════
# Expansion factor for expected misstatement
# ═══════════════════════════════════════════════════════════════
#
# Sprint 805 (finding A-2). The published expansion factor depends on **risk of
# incorrect acceptance alone** — it is one-dimensional. Sprint 684 had tabulated
# it two-dimensionally by (confidence level, expected/tolerable) rising to 3.00,
# and applied it to the reliability factor. It belongs in the denominator,
# scaling expected misstatement:
#
#     n = BV × RF / (TM − EM × EF)
#
# Keyed by risk of incorrect acceptance, ascending.

_EXPANSION_FACTOR_RISKS: tuple[float, ...] = (0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.37, 0.50)

EXPANSION_FACTORS = FigureSet(
    values=(1.9, 1.6, 1.5, 1.4, 1.3, 1.25, 1.2, 1.15, 1.0),
    source="AICPA Audit Sampling Guide — expansion factor for expected misstatement",
    edition="2019 (unchanged 2023)",
    verified_by=(
        "One-dimensional in risk of incorrect acceptance, as restated by the "
        "2026-10-22 full-spectrum review (1.9/1.6/1.5/1.4/1.3/1.25/1.2/1.15/1.0 "
        "for 1%…50%). Replaces the two-dimensional table introduced by Sprint 684, "
        "which oversized samples up to 1.40x under a citation that does not "
        "support the figure."
    ),
    verified_on="2026-10-23",
    note="Indices align with _EXPANSION_FACTOR_RISKS.",
)


# ═══════════════════════════════════════════════════════════════
# Accessors
# ═══════════════════════════════════════════════════════════════


def supported_risks() -> tuple[float, ...]:
    """Risks of incorrect acceptance with a tabulated reliability-factor series."""
    return tuple(sorted(POISSON_RELIABILITY_FACTORS))


def supported_confidence_levels() -> tuple[float, ...]:
    """Confidence levels with a tabulated reliability-factor series."""
    return tuple(sorted(round(1.0 - risk, 10) for risk in POISSON_RELIABILITY_FACTORS))


def _risk_for(confidence_level: float) -> float:
    """
    Map a confidence level to its tabulated risk of incorrect acceptance.

    Refuses rather than substituting. Finding A-1's third compounding defect was
    `_get_incremental_factors` returning the 95% table for *any* confidence level
    at or above 95%, so a 99% engagement silently used 95% factors — the
    published 99% rank-1 increment is 2.03 against 95%'s 1.75.
    """
    risk = round(1.0 - confidence_level, 10)
    for candidate in POISSON_RELIABILITY_FACTORS:
        if abs(candidate - risk) < 1e-9:
            return candidate
    raise ValueError(
        f"No published reliability-factor series for a confidence level of "
        f"{confidence_level:.4g}. Supported levels: "
        f"{', '.join(f'{lvl:.0%}' for lvl in supported_confidence_levels())}. "
        f"Substituting the nearest table would misstate the upper error limit."
    )


def reliability_factor(confidence_level: float, overstatements: int = 0) -> float:
    """
    Poisson reliability factor for `overstatements` overstatements.

    Raises ValueError for an untabulated confidence level, or for a count beyond
    the published series — an engagement with that many misstatements needs
    judgement, not an extrapolated factor.
    """
    if overstatements < 0:
        raise ValueError("overstatements cannot be negative")
    figures = POISSON_RELIABILITY_FACTORS[_risk_for(confidence_level)]
    if overstatements >= len(figures.values):
        raise ValueError(
            f"The published series stops at {len(figures.values) - 1} overstatements; {overstatements} were requested."
        )
    return figures.values[overstatements]


def stringer_increments(confidence_level: float) -> tuple[float, ...]:
    """
    Incremental allowance factors for the Stringer bound, **derived** from the
    reliability-factor series rather than tabulated separately.

    The Stringer bound's incremental allowance for the i-th largest tainting is
    `RF(i) − RF(i−1)`, i.e. the first differences of the series. Returning them
    as `increment` (not `factor − 1`) means the caller applies them directly:

        incremental_allowance = Σ tainting_i × interval × increment_i

    Finding A-1 existed because these were typed in as free-floating literals
    that matched neither published series, and were then applied as
    `max(factor − 1.0, 0.0)` — which, because every literal from rank 5 onward
    was ≤ 1.00, meant **the 5th and every subsequent misstatement contributed
    exactly zero incremental allowance**. Deriving them makes that class of
    disagreement impossible: there is only one series, and the increments are
    its differences.
    """
    series = POISSON_RELIABILITY_FACTORS[_risk_for(confidence_level)].values
    return tuple(round(series[i + 1] - series[i], 10) for i in range(len(series) - 1))


def expansion_factor(confidence_level: float) -> float:
    """
    Published expansion factor for expected misstatement, by risk of incorrect
    acceptance. Interpolated linearly between tabulated risks; clamped at the ends.

    It scales *expected misstatement* in the denominator of the sample-size
    formula — `n = BV × RF / (TM − EM × EF)` — and is not a multiplier on the
    reliability factor.
    """
    risk = round(1.0 - confidence_level, 10)
    risks = _EXPANSION_FACTOR_RISKS
    factors = EXPANSION_FACTORS.values

    if risk <= risks[0]:
        return factors[0]
    if risk >= risks[-1]:
        return factors[-1]
    for i in range(len(risks) - 1):
        if risks[i] <= risk <= risks[i + 1]:
            span = risks[i + 1] - risks[i]
            frac = (risk - risks[i]) / span
            return factors[i] + frac * (factors[i + 1] - factors[i])
    raise AssertionError("unreachable: risk is bracketed by the tabulated range")


def provenance() -> dict[str, dict[str, str]]:
    """
    Every figure set's provenance, for the citation-consistency gate and for
    printing a statutory/authoritative basis onto a workpaper.
    """
    entries: dict[str, dict[str, str]] = {}
    for risk, figures in sorted(POISSON_RELIABILITY_FACTORS.items()):
        entries[f"poisson_reliability_factors_ria_{risk:g}"] = {
            "source": figures.source,
            "edition": figures.edition,
            "verified_by": figures.verified_by,
            "verified_on": figures.verified_on,
            "note": figures.note,
        }
    entries["expansion_factors"] = {
        "source": EXPANSION_FACTORS.source,
        "edition": EXPANSION_FACTORS.edition,
        "verified_by": EXPANSION_FACTORS.verified_by,
        "verified_on": EXPANSION_FACTORS.verified_on,
        "note": EXPANSION_FACTORS.note,
    }
    return entries
