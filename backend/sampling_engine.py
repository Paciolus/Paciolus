"""
Paciolus — Statistical Sampling Engine (Tool 12)
Sprint 268: Phase XXXVI

ISA 530 / PCAOB AS 2315 compliant statistical sampling:
- MUS (Monetary Unit Sampling) size calculation using Poisson confidence factors
- MUS interval-based selection with CSPRNG random start
- Simple random selection via Fisher-Yates with secrets
- Basic 2-tier stratification (high-value 100% + remainder MUS)
- Stringer bound evaluation (basic precision + projected + incremental)
- Pass/Fail conclusion (UEL vs tolerable misstatement)

Zero-Storage: All data ephemeral — processed in-memory, never persisted.
"""

import logging
import math
import secrets
from dataclasses import dataclass, field
from typing import Optional

from shared.column_detector import (
    ColumnFieldConfig, detect_columns, DetectionResult,
)
from shared.helpers import parse_uploaded_file

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Constants — ISA 530 / PCAOB AS 2315 Confidence Factors
# ═══════════════════════════════════════════════════════════════

# Poisson confidence factors for zero expected misstatements
# Source: AICPA Audit Sampling Guide, Table A-1
CONFIDENCE_FACTORS: dict[float, float] = {
    0.80: 1.61,
    0.85: 1.90,
    0.90: 2.31,
    0.95: 3.00,
    0.97: 3.51,
    0.99: 4.61,
}

# Incremental change factors for Stringer bound calculation
# Used when sample contains misstatements — each successive error
# contributes a decreasing incremental allowance.
# Index 0 = factor for 1st largest tainting, etc.
# Source: AICPA Audit Sampling Guide, Table C-1 (95% confidence)
INCREMENTAL_FACTORS_95: list[float] = [
    1.58, 1.30, 1.15, 1.06, 1.00, 0.95, 0.92, 0.89, 0.87, 0.85, 0.83,
]

# Incremental factors for 90% confidence
INCREMENTAL_FACTORS_90: list[float] = [
    1.10, 0.92, 0.82, 0.76, 0.71, 0.68, 0.65, 0.63, 0.61, 0.60, 0.58,
]


def _get_incremental_factors(confidence_level: float) -> list[float]:
    """Return the appropriate incremental factor table for the confidence level."""
    if confidence_level >= 0.95:
        return INCREMENTAL_FACTORS_95
    return INCREMENTAL_FACTORS_90


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
    misstatement: float
    tainting: float  # misstatement / recorded_amount (capped at 1.0 for overstatements)


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
    total_misstatement: float
    projected_misstatement: float
    basic_precision: float
    incremental_allowance: float
    upper_error_limit: float
    conclusion: str  # "pass" or "fail"
    conclusion_detail: str
    errors: list[SampleError]
    taintings_ranked: list[float]  # Sorted desc for Stringer bound


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
    """Look up the Poisson confidence factor for the given confidence level.

    Falls back to nearest available level if exact match not found.
    """
    if confidence_level in CONFIDENCE_FACTORS:
        return CONFIDENCE_FACTORS[confidence_level]

    # Find nearest
    available = sorted(CONFIDENCE_FACTORS.keys())
    nearest = min(available, key=lambda x: abs(x - confidence_level))
    return CONFIDENCE_FACTORS[nearest]


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
        raise ValueError(
            "Expected misstatement must be less than tolerable misstatement"
        )
    if population_value <= 0:
        raise ValueError("Population value must be positive")

    confidence_factor = get_confidence_factor(confidence_level)

    # Expansion factor for expected misstatement
    # When expected > 0, use the expansion factor approach
    if expected_misstatement > 0:
        expansion_factor = 1.0 + (expected_misstatement / tolerable_misstatement)
        adjusted_factor = confidence_factor * expansion_factor
    else:
        adjusted_factor = confidence_factor

    net_tolerable = tolerable_misstatement - expected_misstatement
    if net_tolerable <= 0:
        raise ValueError("Net tolerable misstatement must be positive")

    sampling_interval = net_tolerable / adjusted_factor * (
        population_value / population_value  # Normalizing — interval = net / factor
    )
    # Standard formula: interval = (Tolerable - Expected) / Confidence Factor
    sampling_interval = net_tolerable / adjusted_factor

    sample_size = math.ceil(population_value / sampling_interval)

    # Ensure at least 1
    sample_size = max(sample_size, 1)

    return sample_size, sampling_interval, confidence_factor


def select_mus_sample(
    items: list[PopulationItem],
    sampling_interval: float,
    random_start: Optional[float] = None,
) -> tuple[list[SelectedSample], float]:
    """Select sample using Monetary Unit Sampling (interval-based).

    Uses cumulative dollar tracking with CSPRNG random start.
    Each item containing a selection point is selected.

    Returns: (selected_items, random_start_used)
    """
    if sampling_interval <= 0:
        raise ValueError("Sampling interval must be positive")

    # CSPRNG random start within first interval
    if random_start is None:
        random_start = secrets.randbelow(int(sampling_interval * 100)) / 100.0
        if random_start == 0:
            random_start = 0.01  # Avoid zero start

    selected: list[SelectedSample] = []
    cumulative = 0.0
    next_selection_point = random_start

    # Sort by absolute amount descending for consistent selection
    sorted_items = sorted(items, key=lambda x: abs(x.recorded_amount), reverse=True)

    for item in sorted_items:
        abs_amount = abs(item.recorded_amount)
        if abs_amount <= 0:
            continue

        cumulative += abs_amount

        # Select if this item spans one or more selection points
        while next_selection_point <= cumulative:
            # Avoid duplicates — same item can contain multiple selection points
            if not selected or selected[-1].item.row_index != item.row_index:
                selected.append(SelectedSample(
                    item=item,
                    selection_method="mus_interval",
                    interval_position=next_selection_point,
                ))
            next_selection_point += sampling_interval

    return selected, random_start


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
        return [
            SelectedSample(item=item, selection_method="random")
            for item in items
        ]

    # Fisher-Yates partial shuffle using secrets for CSPRNG
    indices = list(range(n))
    for i in range(sample_size):
        j = secrets.randbelow(n - i) + i
        indices[i], indices[j] = indices[j], indices[i]

    selected_indices = set(indices[:sample_size])
    return [
        SelectedSample(item=items[idx], selection_method="random")
        for idx in sorted(selected_indices)
    ]


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


def evaluate_mus_sample_stringer(
    errors: list[SampleError],
    sampling_interval: float,
    confidence_level: float,
    tolerable_misstatement: float,
    population_value: float,
    sample_size: int,
) -> SampleEvaluationResult:
    """Evaluate MUS sample using the Stringer bound method.

    Stringer bound = Basic Precision + Projected Misstatement + Incremental Allowance

    Basic Precision = Sampling Interval × Confidence Factor
    Projected Misstatement = sum(tainting_i × sampling_interval) for each error
    Incremental Allowance = sum(tainting_i × interval × (incremental_factor_i - 1))
        where taintings are ranked largest to smallest
    """
    confidence_factor = get_confidence_factor(confidence_level)
    incremental_factors = _get_incremental_factors(confidence_level)

    # Basic precision (even with zero errors)
    basic_precision = sampling_interval * confidence_factor

    # Calculate taintings
    taintings: list[float] = []
    total_misstatement = 0.0

    for error in errors:
        total_misstatement += error.misstatement
        taintings.append(error.tainting)

    # Rank taintings from largest to smallest (Stringer method)
    taintings_ranked = sorted(taintings, reverse=True)

    # Projected misstatement
    projected_misstatement = math.fsum(
        t * sampling_interval for t in taintings_ranked
    )

    # Incremental allowance
    incremental_allowance = 0.0
    for i, tainting in enumerate(taintings_ranked):
        if i < len(incremental_factors):
            factor = incremental_factors[i]
        else:
            # Beyond table — use the last factor
            factor = incremental_factors[-1] if incremental_factors else 0.0
        incremental_allowance += tainting * sampling_interval * max(factor - 1.0, 0.0)

    # Upper Error Limit
    upper_error_limit = basic_precision + projected_misstatement + incremental_allowance

    # Sample value
    sample_value = math.fsum(e.recorded_amount for e in errors) if errors else 0.0

    # Conclusion
    if upper_error_limit <= tolerable_misstatement:
        conclusion = "pass"
        conclusion_detail = (
            f"The upper error limit (${upper_error_limit:,.2f}) does not exceed "
            f"tolerable misstatement (${tolerable_misstatement:,.2f}). "
            f"The population is accepted at the {confidence_level:.0%} confidence level."
        )
    else:
        conclusion = "fail"
        conclusion_detail = (
            f"The upper error limit (${upper_error_limit:,.2f}) exceeds "
            f"tolerable misstatement (${tolerable_misstatement:,.2f}). "
            f"The population cannot be accepted at the {confidence_level:.0%} confidence level. "
            "Consider expanding the sample or performing alternative procedures."
        )

    return SampleEvaluationResult(
        method="mus",
        confidence_level=confidence_level,
        tolerable_misstatement=tolerable_misstatement,
        expected_misstatement=0.0,
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
        try:
            amount = float(raw_amount) if raw_amount is not None else 0.0
        except (ValueError, TypeError):
            skipped += 1
            continue

        if amount == 0.0:
            continue

        item_id = str(row.get(id_col, "")) if id_col else str(i + 1)
        description = str(row.get(desc_col, "")) if desc_col else ""

        items.append(PopulationItem(
            row_index=i + 1,
            item_id=item_id or str(i + 1),
            description=description[:200],
            recorded_amount=amount,
        ))

    if skipped > 0:
        detection.detection_notes.append(
            f"{skipped} rows skipped due to non-numeric amount values"
        )

    if not items:
        raise ValueError(
            "No valid items found in the population. "
            "Ensure the file contains rows with numeric amounts."
        )

    return items, detection


def design_sample(
    file_bytes: bytes,
    filename: str,
    config: SamplingConfig,
    column_mapping: Optional[dict[str, str]] = None,
) -> SampleDesignResult:
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

    population_value = math.fsum(abs(item.recorded_amount) for item in items)
    population_size = len(items)

    # Stratification
    high_value_items: list[PopulationItem] = []
    remainder_items = items
    strata_summary: list[dict] = []

    if config.stratification_threshold and config.stratification_threshold > 0:
        high_value_items, remainder_items = apply_stratification(
            items, config.stratification_threshold
        )
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
    high_value_selected = [
        SelectedSample(item=item, selection_method="high_value_100pct")
        for item in high_value_items
    ]

    # Calculate sample size and select remainder
    remainder_selected: list[SelectedSample] = []
    sampling_interval: Optional[float] = None
    confidence_factor = get_confidence_factor(config.confidence_level)
    calculated_sample_size = 0
    random_start: Optional[float] = None

    if config.method == "mus":
        remainder_value = math.fsum(
            abs(item.recorded_amount) for item in remainder_items
        )

        if remainder_value > 0 and config.tolerable_misstatement > 0:
            calculated_sample_size, sampling_interval, confidence_factor = (
                calculate_mus_sample_size(
                    confidence_level=config.confidence_level,
                    tolerable_misstatement=config.tolerable_misstatement,
                    expected_misstatement=config.expected_misstatement,
                    population_value=remainder_value,
                )
            )

            remainder_selected, random_start = select_mus_sample(
                remainder_items, sampling_interval
            )
        elif remainder_value <= 0:
            logger.info("Remainder stratum has zero value — no MUS selection needed")
        else:
            raise ValueError("Tolerable misstatement must be positive for MUS sampling")

    elif config.method == "random":
        if config.sample_size_override and config.sample_size_override > 0:
            calculated_sample_size = config.sample_size_override
        elif config.tolerable_misstatement > 0:
            remainder_value = math.fsum(
                abs(item.recorded_amount) for item in remainder_items
            )
            if remainder_value > 0:
                calculated_sample_size, _, confidence_factor = (
                    calculate_mus_sample_size(
                        confidence_level=config.confidence_level,
                        tolerable_misstatement=config.tolerable_misstatement,
                        expected_misstatement=config.expected_misstatement,
                        population_value=remainder_value,
                    )
                )
        else:
            raise ValueError(
                "For random sampling, provide either sample_size_override or tolerable_misstatement"
            )

        if calculated_sample_size > 0:
            remainder_selected = select_random_sample(
                remainder_items, calculated_sample_size
            )
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
        high_value_total=round(
            math.fsum(abs(i.recorded_amount) for i in high_value_items), 2
        ),
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
) -> list[SampleError]:
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
            "No audited amount column found. The evaluation file must include "
            "a column with audited/confirmed amounts."
        )

    errors: list[SampleError] = []

    for i, row in enumerate(rows):
        try:
            recorded = float(row.get(recorded_col, 0))
            raw_audited = row.get(audited_col)
            if raw_audited is None or str(raw_audited).strip() == "":
                continue  # Skip rows without audited amount
            audited = float(raw_audited)
            # Pandas reads blank cells as NaN
            if math.isnan(audited) or math.isnan(recorded):
                continue
        except (ValueError, TypeError):
            continue

        misstatement = recorded - audited
        if abs(misstatement) < 0.005:  # Tolerance for rounding
            continue

        # Tainting = misstatement / recorded (capped at 1.0 for 100% overstatement)
        if abs(recorded) > 0:
            tainting = min(abs(misstatement) / abs(recorded), 1.0)
        else:
            tainting = 1.0

        item_id = str(row.get(id_col, "")) if id_col else str(i + 1)

        errors.append(SampleError(
            row_index=i + 1,
            item_id=item_id or str(i + 1),
            recorded_amount=recorded,
            audited_amount=audited,
            misstatement=misstatement,
            tainting=tainting,
        ))

    return errors


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
    3. Calculate Stringer bound (MUS) or simple projection (random)
    4. Determine Pass/Fail vs tolerable misstatement
    """
    column_names, rows = parse_uploaded_file(file_bytes, filename)
    errors = _parse_evaluation_errors(rows, column_names, column_mapping)

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

        return evaluate_mus_sample_stringer(
            errors=errors,
            sampling_interval=sampling_interval,
            confidence_level=config.confidence_level,
            tolerable_misstatement=config.tolerable_misstatement,
            population_value=population_value,
            sample_size=sample_size,
        )

    elif config.method == "random":
        # Simple ratio projection for random sampling
        confidence_factor = get_confidence_factor(config.confidence_level)

        total_misstatement = math.fsum(e.misstatement for e in errors)
        sample_value = math.fsum(
            abs(e.recorded_amount) for e in errors
        ) if errors else 0.0

        # Ratio projection: projected = (total_misstatement / sample_value) * population_value
        if sample_value > 0:
            projected_misstatement = (
                abs(total_misstatement) / sample_value * population_value
            )
        else:
            projected_misstatement = 0.0

        # Basic precision for random = projected * (confidence_factor / sqrt(n))
        if sample_size > 0:
            basic_precision = projected_misstatement * (
                confidence_factor / math.sqrt(sample_size)
            )
        else:
            basic_precision = 0.0

        upper_error_limit = projected_misstatement + basic_precision

        if upper_error_limit <= config.tolerable_misstatement:
            conclusion = "pass"
            conclusion_detail = (
                f"The projected misstatement plus precision "
                f"(${upper_error_limit:,.2f}) does not exceed "
                f"tolerable misstatement (${config.tolerable_misstatement:,.2f})."
            )
        else:
            conclusion = "fail"
            conclusion_detail = (
                f"The projected misstatement plus precision "
                f"(${upper_error_limit:,.2f}) exceeds "
                f"tolerable misstatement (${config.tolerable_misstatement:,.2f}). "
                "Consider expanding the sample or performing alternative procedures."
            )

        taintings = sorted(
            [e.tainting for e in errors], reverse=True
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
            projected_misstatement=projected_misstatement,
            basic_precision=basic_precision,
            incremental_allowance=0.0,
            upper_error_limit=upper_error_limit,
            conclusion=conclusion,
            conclusion_detail=conclusion_detail,
            errors=errors,
            taintings_ranked=taintings,
        )

    else:
        raise ValueError(f"Unsupported evaluation method: {config.method}")
