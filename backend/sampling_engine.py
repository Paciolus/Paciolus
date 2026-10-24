"""
Paciolus — Statistical Sampling Engine (Tool 12)
Sprint 268: Phase XXXVI

ISA 530 / PCAOB AS 2315 compliant statistical sampling:
- MUS (Monetary Unit Sampling) size calculation using Poisson confidence factors
- MUS interval-based selection with CSPRNG random start
- Simple random selection via Fisher-Yates with secrets
- Basic 2-tier stratification (high-value 100% + remainder MUS)
- Stringer bound evaluation (basic precision + projected + incremental)
- Overstatements and understatements bounded separately, never netted (Sprint 825)
- Basic precision reported for a zero-error sample on both methods (Sprint 825)
- Pass/Fail conclusion (each direction's UEL vs tolerable misstatement)

Zero-Storage: All data ephemeral — processed in-memory, never persisted.
"""

import logging
import math
import secrets
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from shared import audit_figure_registry as _registry
from shared.column_detector import (
    ColumnFieldConfig,
    DetectionResult,
    detect_columns,
)
from shared.parsing_helpers import safe_decimal
from shared.upload_pipeline import parse_uploaded_file

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Constants — ISA 530 / PCAOB AS 2315 Confidence Factors
# ═══════════════════════════════════════════════════════════════

# Sprint 805 (findings A-1, A-2, A-9): every published figure below now comes
# from `shared/audit_figure_registry.py`, which carries the source, edition and
# verification stamp with the value and derives the Stringer increments from the
# reliability-factor series instead of tabulating them separately.
#
# What was here before, and why it mattered:
# - `INCREMENTAL_FACTORS_95` / `_90` were cited to "AICPA Audit Sampling Guide,
#   Table C-1" and matched neither the published 95% nor the 90% series. The
#   Stringer incremental allowance is the set of *first differences of the
#   Poisson reliability factors*, which is arithmetic and therefore checkable
#   exactly. Applied as `max(factor - 1.0, 0.0)`, every shipped literal from
#   rank 5 onward was <= 1.00, so the 5th and every later misstatement
#   contributed exactly zero allowance. The error understated the upper error
#   limit — the unconservative direction — and the tool reported `pass` where
#   the Stringer bound reported `fail` at 22, 24 and 26 misstatements on the
#   review's measured engagement.
# - `_get_incremental_factors` returned the 95% table for any confidence level
#   >= 0.95, so 97% and 99% engagements silently used 95% factors.
#
# Minimum non-zero population size for a statistically meaningful sample
MIN_POPULATION_SIZE = 5

# Poisson confidence factors for zero expected misstatements, by confidence
# level. Derived from the registry so there is one series, not two.
CONFIDENCE_FACTORS: dict[float, float] = {
    level: _registry.reliability_factor(level) for level in _registry.supported_confidence_levels()
}


def _get_incremental_factors(confidence_level: float) -> list[float]:
    """
    Return the Stringer incremental allowances for this confidence level.

    These are increments, not factors: the caller applies them directly rather
    than as `factor - 1.0`. Refuses an untabulated confidence level instead of
    substituting the nearest series.
    """
    return list(_registry.stringer_increments(confidence_level))


# ═══════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════


@dataclass
class SamplingConfig:
    """Configuration for sample design."""

    method: str = "mus"  # "mus" or "random"
    confidence_level: float = 0.95
    tolerable_misstatement: float = 0.0
    expected_misstatement: float = 0.0
    stratification_threshold: Optional[float] = None  # None = no stratification
    sample_size_override: Optional[int] = None  # Manual override for random sampling


@dataclass
class PopulationItem:
    """Single item from the uploaded population."""

    row_index: int
    item_id: str
    description: str
    recorded_amount: float
    stratum: str = "remainder"  # "high_value" or "remainder"


@dataclass
class SelectedSample:
    """A selected sample item with selection metadata."""

    item: PopulationItem
    selection_method: str  # "high_value_100pct", "mus_interval", "random"
    interval_position: Optional[float] = None  # For MUS: cumulative dollar position


@dataclass
class SampleError:
    """An error found during sample evaluation."""

    row_index: int
    item_id: str
    recorded_amount: float
    audited_amount: float
    misstatement: float  # recorded - audited: > 0 overstatement, < 0 understatement
    # |misstatement| / |recorded_amount|. Capped at 1.0 for overstatements (an
    # item cannot be overstated by more than its recorded amount); NOT capped
    # for understatements (Sprint 825, S6) — an item recorded at $1,000 and
    # audited at $3,000 is understated by 200%, and capping it at 100% would
    # understate the upper limit. Paciolus convention, chosen as the
    # conservative reading; not prescribed by the standard.
    tainting: float


@dataclass
class SampleDesignResult:
    """Result of the sample design phase."""

    method: str
    confidence_level: float
    confidence_factor: float
    tolerable_misstatement: float
    expected_misstatement: float
    population_size: int
    population_value: float
    sampling_interval: Optional[float]  # For MUS
    calculated_sample_size: int
    actual_sample_size: int  # May differ due to high-value items
    high_value_count: int
    high_value_total: float
    remainder_count: int
    remainder_sample_size: int
    selected_items: list[SelectedSample]
    random_start: Optional[float] = None  # For MUS: the CSPRNG random start
    strata_summary: list[dict] = field(default_factory=list)


@dataclass
class SampleEvaluationResult:
    """Result of the sample evaluation phase."""

    method: str
    confidence_level: float
    tolerable_misstatement: float
    expected_misstatement: float
    population_value: float
    sample_size: int
    sample_value: float
    errors_found: int
    total_misstatement: float  # signed sum of known misstatements (factual, not an evaluation input)
    # Sprint 825 (S6): projected_misstatement, basic_precision,
    # incremental_allowance, upper_error_limit and taintings_ranked are the
    # OVERSTATEMENT evaluation (basic precision applies to both directions).
    # Their names predate the split and are kept for API compatibility.
    projected_misstatement: float
    basic_precision: float
    incremental_allowance: float
    upper_error_limit: float
    conclusion: str  # "pass" or "fail" — fails if EITHER direction's bound exceeds TM
    conclusion_detail: str
    errors: list[SampleError]
    taintings_ranked: list[float]  # overstatement taintings, sorted desc for the Stringer bound
    # Missing audited amount tracking (FIX-2A)
    skipped_missing_audited: int = 0
    evaluated_count: int = 0
    missing_audited_warning: Optional[str] = None
    # Sprint 825 (S6): overstatements and understatements are evaluated
    # separately, each with its own upper limit, and are never netted against
    # each other (AICPA Audit Sampling Guide, MUS evaluation).
    overstatement_errors_found: int = 0
    understatement_errors_found: int = 0
    total_overstatement: float = 0.0  # positive magnitude
    total_understatement: float = 0.0  # positive magnitude
    understatement_projected_misstatement: float = 0.0
    understatement_basic_precision: float = 0.0
    understatement_incremental_allowance: float = 0.0
    understatement_upper_error_limit: float = 0.0
    understatement_taintings_ranked: list[float] = field(default_factory=list)


@dataclass
class InsufficientPopulationResult:
    """Returned when the non-zero population is too small for meaningful sampling."""

    status: str = "insufficient_population"
    non_zero_count: int = 0
    minimum_required: int = MIN_POPULATION_SIZE
    total_row_count: int = 0
    message: str = ""


# ═══════════════════════════════════════════════════════════════
# Column Detection Patterns for Population Files
# ═══════════════════════════════════════════════════════════════

POPULATION_COLUMN_CONFIGS: list[ColumnFieldConfig] = [
    ColumnFieldConfig(
        field_name="item_id",
        patterns=[
            (r"^(item.?id|id|identifier|ref|reference|doc.?num|number|no\.?|#)$", 0.9, True),
            (r"(invoice|voucher|check|po).?(number|num|no|#|id)", 0.85, False),
            (r"(entry|transaction|record).?(id|num|no)", 0.8, False),
            (r"(id|num|number|no)$", 0.5, False),
        ],
        required=False,
        priority=20,
    ),
    ColumnFieldConfig(
        field_name="description",
        patterns=[
            (r"^(description|desc|memo|narration|particular|detail)s?$", 0.9, True),
            (r"(account.?name|vendor|customer|payee|name)", 0.7, False),
            (r"(description|memo|detail|narrative)", 0.6, False),
        ],
        required=False,
        priority=40,
    ),
    ColumnFieldConfig(
        field_name="recorded_amount",
        patterns=[
            (r"^(amount|balance|value|total|recorded|book)$", 0.9, True),
            (r"(recorded.?amount|book.?value|carrying|extended)", 0.85, False),
            (r"(net|gross|debit|credit|amt|bal|sum)", 0.6, False),
            (r"(amount|value|total|balance)", 0.5, False),
        ],
        required=True,
        missing_note="No amount column detected — required for sampling",
        priority=10,
    ),
    ColumnFieldConfig(
        field_name="audited_amount",
        patterns=[
            (r"^(audited|audit|confirmed|actual|verified|fair)$", 0.9, True),
            (r"(audited.?amount|audit.?value|fair.?value|confirmed.?amount)", 0.95, False),
            (r"(audited|confirmed|verified|actual|fair)", 0.7, False),
        ],
        required=False,
        priority=15,
    ),
]


# ═══════════════════════════════════════════════════════════════
# Core Algorithms
# ═══════════════════════════════════════════════════════════════


def get_confidence_factor(confidence_level: float) -> float:
    """
    Poisson reliability factor for zero expected misstatements.

    Sprint 805 (A-1): refuses an untabulated confidence level rather than
    snapping to the nearest one. Silent substitution is how a 99% engagement
    came to be planned and evaluated on 95% figures.
    """
    return _registry.reliability_factor(confidence_level)


def calculate_mus_sample_size(
    confidence_level: float,
    tolerable_misstatement: float,
    expected_misstatement: float,
    population_value: float,
) -> tuple[int, float, float]:
    """Calculate MUS sample size using the standard formula.

    Formula: n = (Population Value × Confidence Factor) / (Tolerable - Expected)
    Sampling Interval = (Tolerable - Expected) / Confidence Factor

    Returns: (sample_size, sampling_interval, confidence_factor)
    """
    if tolerable_misstatement <= 0:
        raise ValueError("Tolerable misstatement must be positive")
    if expected_misstatement < 0:
        raise ValueError("Expected misstatement cannot be negative")
    if expected_misstatement >= tolerable_misstatement:
        raise ValueError("Expected misstatement must be less than tolerable misstatement")
    if population_value <= 0:
        raise ValueError("Population value must be positive")

    confidence_factor = get_confidence_factor(confidence_level)

    # Sprint 805 (finding A-2): the published expansion factor depends on the
    # risk of incorrect acceptance *alone*, and it scales **expected
    # misstatement** in the denominator:
    #
    #     n = BV x RF / (TM - EM x EF)
    #
    # Sprint 684 had tabulated it two-dimensionally by (confidence level,
    # expected/tolerable), rising to 3.00, and multiplied it into the
    # reliability factor. That oversized samples by up to 1.40x — the
    # conservative direction, so no audit conclusion was endangered, but the
    # client was billed for up to 40% more items than the standard requires,
    # under a citation that does not support the figure. Sprint 684's own commit
    # message argued the *previous* `1 + e/TM` approximation under-sized
    # samples; at e/TM = 0.25 that approximation reproduced the AICPA formula
    # exactly, so 684 replaced a correct result with an incorrect one.
    if expected_misstatement > 0:
        net_tolerable = tolerable_misstatement - expected_misstatement * _registry.expansion_factor(confidence_level)
    else:
        net_tolerable = tolerable_misstatement

    if net_tolerable <= 0:
        raise ValueError(
            "Expected misstatement, expanded by the AICPA expansion factor, "
            "equals or exceeds tolerable misstatement. Monetary unit sampling "
            "cannot produce a meaningful sample at this ratio; consider "
            "substantive testing of the population instead."
        )

    # Standard MUS formula, AICPA Audit Sampling Guide:
    #   interval = (TM - EM x EF) / RF
    sampling_interval = net_tolerable / confidence_factor

    sample_size = math.ceil(population_value / sampling_interval)

    # Ensure at least 1
    sample_size = max(sample_size, 1)

    return sample_size, sampling_interval, confidence_factor


def select_mus_sample(
    items: list[PopulationItem],
    sampling_interval: float,
    random_start: Optional[float] = None,
) -> tuple[list[SelectedSample], float, list[PopulationItem]]:
    """Select sample using Monetary Unit Sampling (interval-based).

    Uses cumulative dollar tracking with CSPRNG random start.
    Each item containing a selection point is selected.

    Sprint 684: negative-balance items are excluded from MUS selection
    (AICPA Audit Sampling Guide §5.06) — MUS applies to positive-balance
    populations only because the proportional-to-size selection
    mechanism assumes monotonic dollar coverage. Negative balances
    (credit memos, contra entries, refunds) require a separate
    stratum for understatement testing. Returns the list of excluded
    items so the caller can surface them in the memo disclosure.

    Returns: (selected_items, random_start_used, negative_items_excluded)
    """
    if sampling_interval <= 0:
        raise ValueError("Sampling interval must be positive")

    # CSPRNG random start within first interval
    if random_start is None:
        random_start = secrets.randbelow(int(sampling_interval * 100)) / 100.0
        if random_start == 0:
            random_start = 0.01  # Avoid zero start

    # Sprint 684: separate negative-balance items up front — MUS is not
    # valid on them. ``item.recorded_amount`` is Decimal or float; do the
    # comparison against zero to catch both.
    negative_items: list[PopulationItem] = [item for item in items if float(item.recorded_amount) < 0]
    positive_items: list[PopulationItem] = [item for item in items if float(item.recorded_amount) >= 0]

    selected: list[SelectedSample] = []
    cumulative = Decimal("0")
    next_selection_point = Decimal(str(random_start))

    # Sort by absolute amount descending for consistent selection.
    # Positive-only — negatives already filtered above.
    sorted_items = sorted(positive_items, key=lambda x: abs(x.recorded_amount), reverse=True)

    for item in sorted_items:
        abs_amount = abs(item.recorded_amount)
        if abs_amount <= 0:
            continue

        cumulative += Decimal(str(abs_amount))

        # Select if this item spans one or more selection points
        while next_selection_point <= cumulative:
            # Avoid duplicates — same item can contain multiple selection points
            if not selected or selected[-1].item.row_index != item.row_index:
                selected.append(
                    SelectedSample(
                        item=item,
                        selection_method="mus_interval",
                        interval_position=float(next_selection_point),
                    )
                )
            next_selection_point += Decimal(str(sampling_interval))

    return selected, random_start, negative_items


def select_random_sample(
    items: list[PopulationItem],
    sample_size: int,
) -> list[SelectedSample]:
    """Select sample using Fisher-Yates shuffle with secrets CSPRNG.

    Guarantees uniform random selection without replacement.
    """
    if sample_size <= 0:
        raise ValueError("Sample size must be positive")

    n = len(items)
    if sample_size >= n:
        # Select entire population
        return [SelectedSample(item=item, selection_method="random") for item in items]

    # Fisher-Yates partial shuffle using secrets for CSPRNG
    indices = list(range(n))
    for i in range(sample_size):
        j = secrets.randbelow(n - i) + i
        indices[i], indices[j] = indices[j], indices[i]

    selected_indices = set(indices[:sample_size])
    return [SelectedSample(item=items[idx], selection_method="random") for idx in sorted(selected_indices)]


def apply_stratification(
    items: list[PopulationItem],
    threshold: float,
) -> tuple[list[PopulationItem], list[PopulationItem]]:
    """Split population into high-value (100% tested) and remainder strata.

    Items with |recorded_amount| >= threshold go to high-value stratum.
    """
    high_value: list[PopulationItem] = []
    remainder: list[PopulationItem] = []

    for item in items:
        if abs(item.recorded_amount) >= threshold:
            item.stratum = "high_value"
            high_value.append(item)
        else:
            item.stratum = "remainder"
            remainder.append(item)

    return high_value, remainder


def _split_by_direction(errors: list[SampleError]) -> tuple[list[SampleError], list[SampleError]]:
    """Separate overstatements (recorded > audited) from understatements.

    Sprint 825 (S6). The AICPA Audit Sampling Guide evaluates the two directions
    separately, each with its own upper limit; they are never netted. Before
    this, the tainting was ``abs(misstatement) / recorded``, so an understatement
    was scored as an overstatement of the same size.
    """
    over = [e for e in errors if e.misstatement > 0]
    under = [e for e in errors if e.misstatement < 0]
    return over, under


def _stringer_side(
    side_errors: list[SampleError],
    sampling_interval: float,
    increments: list[float],
) -> tuple[float, float, list[float]]:
    """Projected misstatement and incremental allowance for ONE direction.

    Returns ``(projected, incremental_allowance, taintings_ranked)``. Basic
    precision is added by the caller — it is the same for both directions.

    The arithmetic is the Stringer bound as applied in the AICPA Audit Sampling
    Guide; the guide computes the understatement limit the same way as the
    overstatement limit, using the understatement taintings.
    """
    # Sprint 824: an item whose recorded amount is at or above the sampling
    # interval is selected with certainty — it is examined, not sampled. Its
    # actual misstatement enters the projection as-is, with no tainting
    # projection and no sampling-risk allowance (AICPA Audit Sampling Guide).
    # Projecting it as tainting x interval understated a $50,000 error on a
    # $250,000 item at a $70,000 interval as $14,000 — enough to turn a "fail"
    # into a "pass".
    sampled = [e for e in side_errors if abs(e.recorded_amount) < sampling_interval]
    top_stratum = [e for e in side_errors if abs(e.recorded_amount) >= sampling_interval]

    # Rank taintings from largest to smallest (Stringer method)
    taintings_ranked = sorted((e.tainting for e in sampled), reverse=True)

    top_stratum_misstatement = math.fsum(abs(e.misstatement) for e in top_stratum)
    projected = math.fsum(t * sampling_interval for t in taintings_ranked) + top_stratum_misstatement

    # Incremental allowance.
    #
    # Sprint 805 (A-1): `increments` holds the first differences of the Poisson
    # reliability-factor series, derived in the figure registry. The `- 1.0`
    # stays, and it is not cosmetic: the projected-misstatement term above
    # already contributes `tainting x interval` per misstatement, so the
    # allowance contributes only the excess. The identity that pins it is that a
    # fully-tainted sample must satisfy `UEL = interval x RF(k)`:
    #
    #   BP        = interval x RF(0)
    #   projected = k x interval
    #   allowance = interval x sum(dRF_i - 1) = interval x (RF(k) - RF(0) - k)
    #   total     = interval x RF(k)                                  (exactly)
    #
    # What *is* gone is the `max(..., 0.0)` clamp. With the correct series every
    # increment exceeds 1.0 (they approach it from above as the rank grows), so
    # the clamp can never bind — it existed only to stop the mistabulated
    # literals from subtracting, and in doing so it was the mechanism by which
    # the 5th and every later misstatement contributed *exactly zero* allowance,
    # since every shipped literal from rank 5 onward was <= 1.00.
    incremental_allowance = 0.0
    for i, tainting in enumerate(taintings_ranked):
        if i < len(increments):
            increment = increments[i]
        else:
            # Beyond the published series, hold the smallest published increment.
            # The increments decrease monotonically toward 1.0, so this is the
            # conservative choice available without extrapolating a published table.
            increment = increments[-1] if increments else 1.0
        incremental_allowance += tainting * sampling_interval * (increment - 1.0)

    return projected, incremental_allowance, taintings_ranked


def _two_sided_conclusion(
    over_uel: float,
    under_uel: float,
    tolerable_misstatement: float,
    confidence_level: float,
) -> tuple[str, str]:
    """Pass only if NEITHER direction's upper limit exceeds tolerable misstatement.

    Sprint 825 (S6). Each direction is compared with tolerable misstatement on
    its own; the bounds are never netted (AICPA Audit Sampling Guide). Comparing
    the upper limit with tolerable misstatement is how sampling risk is
    evaluated under ISA 530 / PCAOB AS 2315.
    """
    tm = tolerable_misstatement
    bounds = (
        f"The upper misstatement limit is ${over_uel:,.2f} for overstatements and "
        f"${under_uel:,.2f} for understatements, against tolerable misstatement of "
        f"${tm:,.2f} at the {confidence_level:.0%} confidence level. "
        "Overstatements and understatements are evaluated separately and are not "
        "netted against each other (AICPA Audit Sampling Guide). "
    )
    exceeded = [label for label, uel in (("overstatement", over_uel), ("understatement", under_uel)) if uel > tm]
    if not exceeded:
        return "pass", (
            bounds + "Neither upper limit exceeds tolerable misstatement. The auditor should "
            "evaluate this result in the context of other audit evidence obtained and the "
            "overall engagement risk assessment before concluding on the population."
        )
    which = " and ".join(exceeded)
    return "fail", (
        bounds + f"The {which} upper limit exceeds tolerable misstatement. The auditor should "
        "consider expanding the sample, performing alternative procedures, or evaluating "
        "the implications for the overall audit approach."
    )


def evaluate_mus_sample_stringer(
    errors: list[SampleError],
    sampling_interval: float,
    confidence_level: float,
    tolerable_misstatement: float,
    population_value: float,
    sample_size: int,
    sample_items: list[SelectedSample] | None = None,
    *,
    expected_misstatement: float = 0.0,
    sample_value: float | None = None,
) -> SampleEvaluationResult:
    """Evaluate MUS sample using the Stringer bound method.

    Stringer bound = Basic Precision + Projected Misstatement + Incremental Allowance

    Basic Precision = Sampling Interval × Confidence Factor
    Projected Misstatement = sum(tainting_i × sampling_interval) for each error
    Incremental Allowance = sum(tainting_i × interval × increment_i)
        where taintings are ranked largest to smallest

    Sprint 684: ``sample_items`` is the new optional full selected-sample
    list (including non-error items). When supplied, ``sample_value`` is
    computed as the sum of recorded amounts across ALL selected items —
    the auditor-facing "dollar coverage" of the test. Previously
    ``sample_value`` was only the sum of error items' recorded amounts,
    which under-stated coverage for any sample with < 100% error rate.

    Sprint 825 (S6): overstatements and understatements are evaluated
    separately, each with its own upper limit, and never netted (AICPA Audit
    Sampling Guide). Both limits include basic precision. The existing
    ``projected_misstatement`` / ``incremental_allowance`` /
    ``upper_error_limit`` / ``taintings_ranked`` fields carry the overstatement
    side; the ``understatement_*`` fields carry the other. The conclusion fails
    if either limit exceeds tolerable misstatement.

    Sprint 825 (S3): basic precision is reported even when no misstatement is
    found — it is the sampling-risk allowance of a clean sample (AICPA Audit
    Sampling Guide, basic precision with zero misstatements = zero-error
    confidence factor x sampling interval). This path already did so.
    """
    confidence_factor = get_confidence_factor(confidence_level)
    incremental_factors = _get_incremental_factors(confidence_level)

    # Basic precision (even with zero errors). AICPA Audit Sampling Guide:
    # confidence factor for zero misstatements x sampling interval. Applies to
    # each direction's upper limit.
    basic_precision = sampling_interval * confidence_factor

    over_errors, under_errors = _split_by_direction(errors)
    total_misstatement = math.fsum(e.misstatement for e in errors)

    projected_misstatement, incremental_allowance, taintings_ranked = _stringer_side(
        over_errors, sampling_interval, incremental_factors
    )
    under_projected, under_incremental, under_taintings = _stringer_side(
        under_errors, sampling_interval, incremental_factors
    )

    upper_error_limit = basic_precision + projected_misstatement + incremental_allowance
    under_upper_error_limit = basic_precision + under_projected + under_incremental

    # Sample value — Sprint 684: prefer the full selected-sample sum when
    # supplied. Sprint 824: ``evaluate_sample`` now passes the evaluated
    # sample's total directly; the error-only fallback remains for callers
    # that supply neither.
    if sample_value is not None:
        pass
    elif sample_items is not None:
        sample_value = math.fsum(abs(s.recorded_amount) for s in sample_items)
    else:
        sample_value = math.fsum(e.recorded_amount for e in errors) if errors else 0.0

    conclusion, conclusion_detail = _two_sided_conclusion(
        upper_error_limit, under_upper_error_limit, tolerable_misstatement, confidence_level
    )

    return SampleEvaluationResult(
        method="mus",
        confidence_level=confidence_level,
        tolerable_misstatement=tolerable_misstatement,
        expected_misstatement=expected_misstatement,
        population_value=population_value,
        sample_size=sample_size,
        sample_value=sample_value,
        errors_found=len(errors),
        total_misstatement=total_misstatement,
        projected_misstatement=projected_misstatement,
        basic_precision=basic_precision,
        incremental_allowance=incremental_allowance,
        upper_error_limit=upper_error_limit,
        conclusion=conclusion,
        conclusion_detail=conclusion_detail,
        errors=errors,
        taintings_ranked=taintings_ranked,
        overstatement_errors_found=len(over_errors),
        understatement_errors_found=len(under_errors),
        total_overstatement=math.fsum(e.misstatement for e in over_errors),
        total_understatement=math.fsum(-e.misstatement for e in under_errors),
        understatement_projected_misstatement=under_projected,
        understatement_basic_precision=basic_precision,
        understatement_incremental_allowance=under_incremental,
        understatement_upper_error_limit=under_upper_error_limit,
        understatement_taintings_ranked=under_taintings,
    )


# ═══════════════════════════════════════════════════════════════
# High-Level Entry Points
# ═══════════════════════════════════════════════════════════════


def _parse_population(
    rows: list[dict],
    column_names: list[str],
    column_mapping: Optional[dict[str, str]] = None,
) -> tuple[list[PopulationItem], DetectionResult]:
    """Parse uploaded population data into PopulationItem list."""
    detection = detect_columns(column_names, POPULATION_COLUMN_CONFIGS)

    # Apply manual mapping overrides
    if column_mapping:
        for field_name, col_name in column_mapping.items():
            if col_name in column_names:
                detection.assignments[field_name] = (col_name, 1.0)

    amount_col = detection.get_column("recorded_amount")
    if not amount_col:
        raise ValueError("No amount column found. Please provide a column mapping.")

    id_col = detection.get_column("item_id")
    desc_col = detection.get_column("description")

    items: list[PopulationItem] = []
    skipped = 0

    for i, row in enumerate(rows):
        raw_amount = row.get(amount_col)
        if raw_amount is None:
            skipped += 1
            continue
        try:
            amount = safe_decimal(raw_amount)
        except (ValueError, TypeError):
            skipped += 1
            continue

        if amount == 0.0:
            continue

        item_id = str(row.get(id_col, "")) if id_col else str(i + 1)
        description = str(row.get(desc_col, "")) if desc_col else ""

        items.append(
            PopulationItem(
                row_index=i + 1,
                item_id=item_id or str(i + 1),
                description=description[:200],
                recorded_amount=float(amount),
            )
        )

    if skipped > 0:
        detection.detection_notes.append(f"{skipped} rows skipped due to non-numeric amount values")

    if not items:
        raise ValueError("No valid items found in the population. Ensure the file contains rows with numeric amounts.")

    return items, detection


def design_sample(
    file_bytes: bytes,
    filename: str,
    config: SamplingConfig,
    column_mapping: Optional[dict[str, str]] = None,
) -> SampleDesignResult | InsufficientPopulationResult:
    """Main entry point for Phase 1 — Design and select a sample.

    1. Parse uploaded population file
    2. Detect columns (amount, ID, description)
    3. Apply stratification if threshold provided
    4. Calculate sample size (MUS formula or manual)
    5. Select sample items
    6. Return result with all selected items
    """
    column_names, rows = parse_uploaded_file(file_bytes, filename)
    items, detection = _parse_population(rows, column_names, column_mapping)

    # Check minimum viable population size after zero-amount filtering
    if len(items) < MIN_POPULATION_SIZE:
        return InsufficientPopulationResult(
            non_zero_count=len(items),
            minimum_required=MIN_POPULATION_SIZE,
            total_row_count=len(rows),
            message=(
                f"Insufficient non-zero population for statistical sampling: "
                f"{len(items)} non-zero items found (minimum required: {MIN_POPULATION_SIZE}, "
                f"total rows before filtering: {len(rows)}). "
                f"Consider expanding the population or using alternative audit procedures."
            ),
        )

    population_value = math.fsum(abs(item.recorded_amount) for item in items)
    population_size = len(items)

    # Stratification
    high_value_items: list[PopulationItem] = []
    remainder_items = items
    strata_summary: list[dict] = []

    if config.stratification_threshold and config.stratification_threshold > 0:
        high_value_items, remainder_items = apply_stratification(items, config.stratification_threshold)
        hv_total = math.fsum(abs(i.recorded_amount) for i in high_value_items)
        rem_total = math.fsum(abs(i.recorded_amount) for i in remainder_items)
        strata_summary = [
            {
                "stratum": "High Value (100%)",
                "threshold": f">= ${config.stratification_threshold:,.2f}",
                "count": len(high_value_items),
                "total_value": round(hv_total, 2),
                "sample_size": len(high_value_items),
            },
            {
                "stratum": "Remainder (Sampled)",
                "threshold": f"< ${config.stratification_threshold:,.2f}",
                "count": len(remainder_items),
                "total_value": round(rem_total, 2),
                "sample_size": 0,  # Updated below
            },
        ]

    # High-value items selected 100%
    high_value_selected = [SelectedSample(item=item, selection_method="high_value_100pct") for item in high_value_items]

    # Calculate sample size and select remainder
    remainder_selected: list[SelectedSample] = []
    sampling_interval: Optional[float] = None
    confidence_factor = get_confidence_factor(config.confidence_level)
    calculated_sample_size = 0
    random_start: Optional[float] = None

    if config.method == "mus":
        remainder_value = math.fsum(abs(item.recorded_amount) for item in remainder_items)

        if remainder_value > 0 and config.tolerable_misstatement > 0:
            calculated_sample_size, sampling_interval, confidence_factor = calculate_mus_sample_size(
                confidence_level=config.confidence_level,
                tolerable_misstatement=config.tolerable_misstatement,
                expected_misstatement=config.expected_misstatement,
                population_value=remainder_value,
            )

            remainder_selected, random_start, mus_negative_excluded = select_mus_sample(
                remainder_items, sampling_interval
            )
            if mus_negative_excluded:
                # Sprint 684: surface the negative-balance exclusion so the
                # memo can disclose that MUS didn't cover them. AICPA
                # Audit Sampling Guide §5.06.
                logger.info(
                    "MUS excluded %d negative-balance items; consider a separate stratum for understatement testing.",
                    len(mus_negative_excluded),
                )
        elif remainder_value <= 0:
            logger.info("Remainder stratum has zero value — no MUS selection needed")
        else:
            raise ValueError("Tolerable misstatement must be positive for MUS sampling")

    elif config.method == "random":
        if config.sample_size_override and config.sample_size_override > 0:
            calculated_sample_size = config.sample_size_override
        elif config.tolerable_misstatement > 0:
            remainder_value = math.fsum(abs(item.recorded_amount) for item in remainder_items)
            if remainder_value > 0:
                calculated_sample_size, _, confidence_factor = calculate_mus_sample_size(
                    confidence_level=config.confidence_level,
                    tolerable_misstatement=config.tolerable_misstatement,
                    expected_misstatement=config.expected_misstatement,
                    population_value=remainder_value,
                )
        else:
            raise ValueError("For random sampling, provide either sample_size_override or tolerable_misstatement")

        if calculated_sample_size > 0:
            remainder_selected = select_random_sample(remainder_items, calculated_sample_size)
    else:
        raise ValueError(f"Unsupported sampling method: {config.method}")

    # Update strata summary
    if strata_summary and len(strata_summary) > 1:
        strata_summary[1]["sample_size"] = len(remainder_selected)

    all_selected = high_value_selected + remainder_selected

    return SampleDesignResult(
        method=config.method,
        confidence_level=config.confidence_level,
        confidence_factor=confidence_factor,
        tolerable_misstatement=config.tolerable_misstatement,
        expected_misstatement=config.expected_misstatement,
        population_size=population_size,
        population_value=round(population_value, 2),
        sampling_interval=round(sampling_interval, 2) if sampling_interval else None,
        calculated_sample_size=calculated_sample_size,
        actual_sample_size=len(all_selected),
        high_value_count=len(high_value_items),
        high_value_total=round(math.fsum(abs(i.recorded_amount) for i in high_value_items), 2),
        remainder_count=len(remainder_items),
        remainder_sample_size=len(remainder_selected),
        selected_items=all_selected,
        random_start=round(random_start, 2) if random_start is not None else None,
        strata_summary=strata_summary,
    )


def _parse_evaluation_errors(
    rows: list[dict],
    column_names: list[str],
    column_mapping: Optional[dict[str, str]] = None,
) -> tuple[list[SampleError], int, int]:
    """Parse completed sample file into SampleError list.

    Expects columns: item_id, recorded_amount, audited_amount.
    Only rows where recorded != audited are treated as errors.
    """
    detection = detect_columns(column_names, POPULATION_COLUMN_CONFIGS)

    if column_mapping:
        for field_name, col_name in column_mapping.items():
            if col_name in column_names:
                detection.assignments[field_name] = (col_name, 1.0)

    recorded_col = detection.get_column("recorded_amount")
    audited_col = detection.get_column("audited_amount")
    id_col = detection.get_column("item_id")

    if not recorded_col:
        raise ValueError("No recorded amount column found in evaluation file")
    if not audited_col:
        raise ValueError(
            "No audited amount column found. The evaluation file must include a column with audited/confirmed amounts."
        )

    errors: list[SampleError] = []
    evaluated_count = 0
    skipped_missing_audited = 0
    evaluated_recorded_total = Decimal("0")

    for i, row in enumerate(rows):
        try:
            raw_recorded = row.get(recorded_col)
            raw_audited = row.get(audited_col)
            if raw_recorded is None or str(raw_recorded).strip() == "":
                continue
            if isinstance(raw_recorded, float) and math.isnan(raw_recorded):
                continue

            # Row has a valid recorded amount — check if audited is missing
            if raw_audited is None or str(raw_audited).strip() == "":
                skipped_missing_audited += 1
                continue
            if isinstance(raw_audited, float) and math.isnan(raw_audited):
                skipped_missing_audited += 1
                continue

            # Sprint 824: parse with no default. An audited value that is not a
            # number ("see note", "Infinity") used to become 0 and be scored as a
            # 100% misstatement; it is an unassessed item, not an error.
            recorded = safe_decimal(raw_recorded, default=None)
            audited = safe_decimal(raw_audited, default=None)
        except (ValueError, TypeError):
            continue
        if recorded is None:
            continue
        if audited is None:
            skipped_missing_audited += 1
            continue

        evaluated_count += 1
        evaluated_recorded_total += abs(recorded)

        misstatement = recorded - audited
        if abs(misstatement) < 0.005:  # Tolerance for rounding
            continue

        # Tainting = |misstatement| / |recorded|. Capped at 1.0 for overstatements
        # only (an item cannot be overstated by more than its recorded amount).
        # Sprint 825 (S6): understatement taintings are not capped — capping a
        # 200% understatement at 100% would understate its upper limit.
        # Paciolus convention (the conservative reading); not prescribed by the
        # standard. Direction is carried by the sign of `misstatement`.
        if abs(recorded) > 0:
            ratio = abs(misstatement) / abs(recorded)
            tainting = float(min(ratio, Decimal("1")) if misstatement > 0 else ratio)
        else:
            tainting = 1.0

        item_id = str(row.get(id_col, "")) if id_col else str(i + 1)

        errors.append(
            SampleError(
                row_index=i + 1,
                item_id=item_id or str(i + 1),
                recorded_amount=float(recorded),
                audited_amount=float(audited),
                misstatement=float(misstatement),
                tainting=float(tainting),
            )
        )

    return errors, evaluated_count, skipped_missing_audited, float(evaluated_recorded_total)


def _evaluate_random_sample(
    *,
    errors: list[SampleError],
    config: SamplingConfig,
    population_value: float,
    sample_size: int,
    evaluated_count: int,
    evaluated_value: float,
    skipped_missing_audited: int,
    missing_audited_warning: Optional[str],
) -> SampleEvaluationResult:
    """Evaluate a simple-random (non-MUS) sample, one direction at a time.

    For each direction d (overstatement, understatement):

        n         = min(sample_size, evaluated_count)
        BP        = population_value x CF(0) / n                       (S3)
        projected = (sum of |misstatement| in direction d / sample value)
                    x population_value                       (ratio estimate)
        allowance = projected x CF(0) / sqrt(n)
        UEL_d     = BP + projected + allowance

    and the conclusion fails if either UEL_d exceeds tolerable misstatement.

    Provenance of each term (read before changing any of them):

    * **Basic precision (Sprint 825, S3).** ISA 530 / PCAOB AS 2315 require the
      auditor to consider sampling risk when evaluating a sample, and a sample
      with no misstatements still carries it. Before Sprint 825 this path
      computed precision as ``projected x CF/sqrt(n)``, which is 0 when nothing
      is found, so a clean sample of 5 read exactly like a clean sample of 200:
      UEL $0, "pass". The AICPA Audit Sampling Guide's basic precision for a
      monetary-unit sample with zero misstatements is the zero-error confidence
      factor x the sampling interval. A simple random sample has no sampling
      interval, so Paciolus uses the average dollars per sampled item,
      ``population_value / n``, in its place. **That substitution is a Paciolus
      convention, not prescribed by the standard.** It was chosen because it is
      consistent with how this tool *designs* a random sample: the size comes
      from the same formula, ``n = BV x CF / TM``, so a clean sample of at
      least the designed size passes and a smaller clean sample fails. The
      tool must never report more assurance than the data supports.
    * **n = min(sample_size, evaluated_count).** Items whose audited amount was
      missing or unreadable were not assessed and give no assurance. Paciolus
      convention (the conservative reading).
    * **Ratio projection.** Misstatement rate of the evaluated sample's dollars,
      applied to the population (Sprint 824 fixed its denominator).
    * **Allowance ``projected x CF/sqrt(n)``.** Retained from the engine's
      pre-Sprint-825 evaluation, which reported it as "basic precision". It is a
      Paciolus convention, not a formula prescribed by the standard; it is kept
      (and now reported as ``incremental_allowance``) so that no sample with
      misstatements reports a lower upper limit than before.
    * **Two directions (Sprint 825, S6).** Overstatements and understatements are
      projected and bounded separately and never netted; previously the ratio
      used ``abs(sum of misstatements)``, so a $1,000 overstatement and a $1,000
      understatement projected to $0. Separate evaluation follows the AICPA
      Audit Sampling Guide's treatment of the two directions.
    """
    confidence_factor = get_confidence_factor(config.confidence_level)

    over_errors, under_errors = _split_by_direction(errors)
    total_misstatement = math.fsum(e.misstatement for e in errors)
    total_over = math.fsum(e.misstatement for e in over_errors)
    total_under = math.fsum(-e.misstatement for e in under_errors)

    # Sprint 824: the ratio estimate's denominator is the whole evaluated
    # sample, not the error rows. One $1,000 error on an $8,372 item in a
    # $1.03M sample projected to $597,198 instead of ~$4,868.
    sample_value = evaluated_value

    n_effective = min(sample_size, evaluated_count) if evaluated_count > 0 else sample_size
    if n_effective <= 0:
        raise ValueError("Sample size must be positive to evaluate a random sample.")

    basic_precision = population_value * confidence_factor / n_effective

    def _side(total: float) -> tuple[float, float]:
        projected = total / sample_value * population_value if sample_value > 0 else 0.0
        allowance = projected * (confidence_factor / math.sqrt(n_effective))
        return projected, allowance

    over_projected, over_allowance = _side(total_over)
    under_projected, under_allowance = _side(total_under)

    over_uel = basic_precision + over_projected + over_allowance
    under_uel = basic_precision + under_projected + under_allowance

    conclusion, conclusion_detail = _two_sided_conclusion(
        over_uel, under_uel, config.tolerable_misstatement, config.confidence_level
    )

    return SampleEvaluationResult(
        method="random",
        confidence_level=config.confidence_level,
        tolerable_misstatement=config.tolerable_misstatement,
        expected_misstatement=config.expected_misstatement,
        population_value=population_value,
        sample_size=sample_size,
        sample_value=sample_value,
        errors_found=len(errors),
        total_misstatement=total_misstatement,
        projected_misstatement=over_projected,
        basic_precision=basic_precision,
        incremental_allowance=over_allowance,
        upper_error_limit=over_uel,
        conclusion=conclusion,
        conclusion_detail=conclusion_detail,
        errors=errors,
        taintings_ranked=sorted((e.tainting for e in over_errors), reverse=True),
        skipped_missing_audited=skipped_missing_audited,
        evaluated_count=evaluated_count,
        missing_audited_warning=missing_audited_warning,
        overstatement_errors_found=len(over_errors),
        understatement_errors_found=len(under_errors),
        total_overstatement=total_over,
        total_understatement=total_under,
        understatement_projected_misstatement=under_projected,
        understatement_basic_precision=basic_precision,
        understatement_incremental_allowance=under_allowance,
        understatement_upper_error_limit=under_uel,
        understatement_taintings_ranked=sorted((e.tainting for e in under_errors), reverse=True),
    )


def evaluate_sample(
    file_bytes: bytes,
    filename: str,
    config: SamplingConfig,
    population_value: float,
    sample_size: int,
    sampling_interval: Optional[float] = None,
    column_mapping: Optional[dict[str, str]] = None,
) -> SampleEvaluationResult:
    """Main entry point for Phase 2 — Evaluate completed sample.

    1. Parse completed sample file (with audited amounts)
    2. Identify misstatements (recorded - audited)
    3. Calculate Stringer bound (MUS) or ratio projection (random), separately
       for overstatements and understatements
    4. Determine Pass/Fail: fail if either direction's bound exceeds TM
    """
    column_names, rows = parse_uploaded_file(file_bytes, filename)
    errors, evaluated_count, skipped_missing_audited, evaluated_value = _parse_evaluation_errors(
        rows, column_names, column_mapping
    )

    # A conclusion needs at least one assessed item. Since unreadable audited
    # amounts became "unassessed" rather than 100% misstatements, a file in
    # which none could be read would otherwise evaluate an empty sample and
    # report "pass" (PR #205 review).
    if evaluated_count == 0:
        raise ValueError(
            "No sample item could be evaluated: every row is missing a readable recorded or audited "
            "amount. Check the audited amount column before drawing a conclusion."
        )

    # Build missing audited amount warning if threshold exceeded
    MISSING_AUDITED_THRESHOLD = 0.10  # 10% of evaluated population
    missing_audited_warning: Optional[str] = None
    total_assessable = evaluated_count + skipped_missing_audited
    if total_assessable > 0 and skipped_missing_audited / total_assessable > MISSING_AUDITED_THRESHOLD:
        missing_audited_warning = (
            f"{skipped_missing_audited} of {total_assessable} evaluated items were missing "
            f"audited amounts and could not be assessed."
        )

    if config.method == "mus":
        # For MUS, need sampling interval
        if sampling_interval is None or sampling_interval <= 0:
            # Recalculate from parameters
            if config.tolerable_misstatement > 0 and population_value > 0:
                _, sampling_interval, _ = calculate_mus_sample_size(
                    confidence_level=config.confidence_level,
                    tolerable_misstatement=config.tolerable_misstatement,
                    expected_misstatement=config.expected_misstatement,
                    population_value=population_value,
                )
            else:
                raise ValueError(
                    "Sampling interval required for MUS evaluation. "
                    "Provide tolerable_misstatement and population_value."
                )

        result = evaluate_mus_sample_stringer(
            errors=errors,
            sampling_interval=sampling_interval,
            confidence_level=config.confidence_level,
            tolerable_misstatement=config.tolerable_misstatement,
            population_value=population_value,
            sample_size=sample_size,
            expected_misstatement=config.expected_misstatement,
            sample_value=evaluated_value,
        )
        result.skipped_missing_audited = skipped_missing_audited
        result.evaluated_count = evaluated_count
        result.missing_audited_warning = missing_audited_warning
        return result

    elif config.method == "random":
        return _evaluate_random_sample(
            errors=errors,
            config=config,
            population_value=population_value,
            sample_size=sample_size,
            evaluated_count=evaluated_count,
            evaluated_value=evaluated_value,
            skipped_missing_audited=skipped_missing_audited,
            missing_audited_warning=missing_audited_warning,
        )

    else:
        raise ValueError(f"Unsupported evaluation method: {config.method}")
