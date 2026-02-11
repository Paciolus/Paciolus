"""
Shared Data Quality Assessment — Sprint 152

Config-driven field quality assessment used by JE, AP, Revenue, FA,
Inventory, and Payroll testing engines. Each engine defines domain-specific
field configs and calls the shared assess_data_quality() function.

NOT used by:
- AR Aging (dual-input, unweighted average — structurally different)
- Three-Way Match (13 named fill rates, 3 document types — completely different)
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class FieldQualityConfig:
    """Configuration for a single field's quality assessment.

    Args:
        field_name: Key in the fill_rates dict (e.g., 'date', 'vendor_name')
        accessor: Callable that takes an entry and returns truthy if field is filled
        weight: Explicit weight for required fields (e.g., 0.30). None for optional fields.
        issue_threshold: Fill rate below this triggers an issue. None = no issue checking.
        issue_template: Format string for issue message. Supports {fill_pct} and {unfilled}.
    """
    field_name: str
    accessor: Callable[[Any], Any]
    weight: Optional[float] = None
    issue_threshold: Optional[float] = None
    issue_template: Optional[str] = None


@dataclass
class DataQualityResult:
    """Result of data quality assessment."""
    completeness_score: float  # 0-100
    field_fill_rates: dict[str, float] = field(default_factory=dict)
    detected_issues: list[str] = field(default_factory=list)
    total_rows: int = 0

    def to_dict(self) -> dict:
        return {
            "completeness_score": round(self.completeness_score, 1),
            "field_fill_rates": {k: round(v, 2) for k, v in self.field_fill_rates.items()},
            "detected_issues": self.detected_issues,
            "total_rows": self.total_rows,
        }


def assess_data_quality(
    entries: list[Any],
    field_configs: list[FieldQualityConfig],
    *,
    optional_weight_pool: float = 0.15,
) -> DataQualityResult:
    """Assess data quality using config-driven field definitions.

    Algorithm (extracted from the identical pattern in 6 engines):
    1. Calculate fill rate for each field config
    2. Generate issues for fields below their issue_threshold
    3. Required fields use explicit weights from config
    4. Optional fields split remaining weight pool equally
    5. If no optional fields active, give full credit for optional pool
    6. Score = sum(fill_rate * weight) * 100, capped at 100.0

    Args:
        entries: List of parsed entry objects (domain-specific)
        field_configs: List of FieldQualityConfig defining fields to check
        optional_weight_pool: Total weight allocated to optional fields (default 0.15)

    Returns:
        DataQualityResult with completeness score, fill rates, and issues
    """
    total = len(entries)
    if total == 0:
        return DataQualityResult(completeness_score=0.0, total_rows=0)

    fill_rates: dict[str, float] = {}
    issues: list[str] = []

    # Calculate fill rates
    for cfg in field_configs:
        filled = sum(1 for e in entries if cfg.accessor(e))
        rate = filled / total
        fill_rates[cfg.field_name] = rate

        # Check issue threshold
        if cfg.issue_threshold is not None and rate < cfg.issue_threshold and cfg.issue_template:
            unfilled = total - filled
            issues.append(cfg.issue_template.format(
                fill_pct=f"{rate:.0%}",
                unfilled=unfilled,
                total=total,
            ))

    # Build weights: required fields use explicit weight, optional split pool
    weights: dict[str, float] = {}
    optional_fields: list[str] = []

    for cfg in field_configs:
        if cfg.weight is not None:
            weights[cfg.field_name] = cfg.weight
        else:
            optional_fields.append(cfg.field_name)

    if optional_fields:
        per_optional = optional_weight_pool / len(optional_fields)
        for name in optional_fields:
            weights[name] = per_optional
    else:
        # No optional fields detected — give full credit for optional pool
        # This is achieved by not adding any optional weight (required weights
        # already sum to less than 1.0, so the score naturally accounts for this).
        # To match existing engine behavior: add optional pool as bonus.
        pass

    # Calculate weighted score
    score = sum(fill_rates.get(k, 0) * w for k, w in weights.items()) * 100

    # If no optional fields, add full optional pool credit (existing engine behavior)
    if not optional_fields:
        score += optional_weight_pool * 100

    return DataQualityResult(
        completeness_score=min(score, 100.0),
        field_fill_rates=fill_rates,
        detected_issues=issues,
        total_rows=total,
    )
