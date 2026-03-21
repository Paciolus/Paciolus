"""Base classes for the Synthetic Anomaly Testing Framework.

Defines the AnomalyRecord data structure and AnomalyGenerator abstract base class
that all anomaly generators must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class AnomalyRecord:
    """Describes a single injected anomaly and the expected detection outcome.

    Attributes:
        anomaly_type: The type of anomaly injected (e.g., 'round_number').
        report_targets: List of report IDs this anomaly should appear in.
        injected_at: Human-readable description of where the anomaly was injected.
        expected_field: The key in the audit result dict to check for detection.
        expected_condition: A string condition to evaluate against the field value.
        metadata: Additional context about the injection (amounts, accounts, etc.).
    """

    anomaly_type: str
    report_targets: list[str]
    injected_at: str
    expected_field: str
    expected_condition: str
    metadata: dict = field(default_factory=dict)


class AnomalyGenerator(ABC):
    """Abstract base class for anomaly generators.

    Subclasses must set `name` and `report_targets` as class attributes and
    implement the `inject` method.
    """

    name: str
    report_targets: list[str]

    @abstractmethod
    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        """Inject an anomaly into a valid trial balance DataFrame.

        Args:
            df: A valid, balanced trial balance DataFrame with columns:
                Account, Account Name, Account Type, Debit, Credit.
            seed: Random seed for deterministic behavior.

        Returns:
            A tuple of (mutated_df_copy, list_of_AnomalyRecords).
            Must not alter the input DataFrame in-place — always return a copy.
            Must be deterministic given the same seed.
        """
