"""
Shared Column Detector — Sprint 151

Provides reusable column detection logic for all testing engines.
Replaces 13 near-identical detection functions across 9 engines with
a single configurable detector.

Pattern format: (regex_pattern: str, weight: float, is_exact: bool)
- regex_pattern: Regex to match against column name (case-insensitive)
- weight: Confidence score (0.0 - 1.0), higher = better match
- is_exact: True = re.match (anchor to start), False = re.search (anywhere)
"""

from dataclasses import dataclass, field
from typing import Optional
import re


# Type alias for the standard pattern tuple used across all engines
ColumnPattern = tuple[str, float, bool]


@dataclass
class ColumnFieldConfig:
    """Configuration for a single column field to detect.

    Args:
        field_name: Internal name for this field (e.g., 'date_column', 'amount_column')
        patterns: List of (regex, weight, is_exact) tuples
        required: If True, missing column adds a note and contributes 0.0 to confidence
        missing_note: Note to add if required field not found
        priority: Lower = assigned first (prevents generic patterns from stealing specific columns)
    """
    field_name: str
    patterns: list[ColumnPattern]
    required: bool = False
    missing_note: str = ""
    priority: int = 50


@dataclass
class DetectionResult:
    """Result of shared column detection.

    assignments: dict mapping field_name -> (column_name, confidence)
    all_columns: original column list
    detection_notes: list of notes generated during detection
    """
    assignments: dict[str, tuple[str, float]] = field(default_factory=dict)
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    def get_column(self, field_name: str) -> Optional[str]:
        """Get the assigned column name for a field, or None."""
        match = self.assignments.get(field_name)
        return match[0] if match else None

    def get_confidence(self, field_name: str) -> float:
        """Get the confidence for a field assignment, or 0.0."""
        match = self.assignments.get(field_name)
        return match[1] if match else 0.0


def match_column(column_name: str, patterns: list[ColumnPattern]) -> float:
    """Match a column name against patterns, return best confidence.

    This is the shared matching logic used by all engines:
    - Normalizes column name to lowercase/stripped
    - For is_exact=True: uses re.match (anchored to start)
    - For is_exact=False: uses re.search (anywhere in string)
    - Returns the highest weight among matching patterns
    """
    normalized = column_name.lower().strip()
    best = 0.0
    for pattern, weight, is_exact in patterns:
        if is_exact:
            if re.match(pattern, normalized, re.IGNORECASE):
                best = max(best, weight)
        else:
            if re.search(pattern, normalized, re.IGNORECASE):
                best = max(best, weight)
    return best


def detect_columns(
    column_names: list[str],
    field_configs: list[ColumnFieldConfig],
    min_confidence: float = 0.0,
) -> DetectionResult:
    """Detect columns using weighted pattern matching with greedy assignment.

    Algorithm:
    1. Strip whitespace from all column names
    2. Score every column against every field's patterns
    3. Sort field configs by priority (lowest first) for specificity ordering
    4. For each field (in priority order), assign the best unassigned column
    5. Generate notes for missing required fields

    Args:
        column_names: List of column headers from the uploaded file
        field_configs: List of ColumnFieldConfig defining what to detect
        min_confidence: Minimum confidence to accept a match (default 0.0)

    Returns:
        DetectionResult with assignments, notes, and column list
    """
    columns = [col.strip() for col in column_names]
    notes: list[str] = []
    assigned: set[str] = set()

    # Score all columns for all field types
    scores: dict[str, dict[str, float]] = {}
    for col in columns:
        scores[col] = {}
        for config in field_configs:
            scores[col][config.field_name] = match_column(col, config.patterns)

    # Sort by priority (lower = first) for specificity ordering
    sorted_configs = sorted(field_configs, key=lambda c: c.priority)

    assignments: dict[str, tuple[str, float]] = {}

    for config in sorted_configs:
        best_col = None
        best_conf = min_confidence
        for col in columns:
            if col in assigned:
                continue
            conf = scores[col].get(config.field_name, 0.0)
            if conf > best_conf:
                best_col = col
                best_conf = conf
        if best_col:
            assigned.add(best_col)
            assignments[config.field_name] = (best_col, best_conf)
        elif config.required and config.missing_note:
            notes.append(config.missing_note)

    return DetectionResult(
        assignments=assignments,
        all_columns=columns,
        detection_notes=notes,
    )
