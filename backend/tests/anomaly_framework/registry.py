"""Anomaly generator registry.

Central registry of all available anomaly generators. Used by test
parametrization to run detection tests against every generator.
"""

from tests.anomaly_framework.generators.abnormal_balance import AbnormalBalanceGenerator
from tests.anomaly_framework.generators.duplicate_entry import DuplicateEntryGenerator
from tests.anomaly_framework.generators.missing_offset import MissingOffsetGenerator
from tests.anomaly_framework.generators.round_number import RoundNumberGenerator
from tests.anomaly_framework.generators.suspense_account import SuspenseAccountGenerator
from tests.anomaly_framework.generators.weekend_posting import WeekendPostingGenerator

ANOMALY_REGISTRY: list = [
    RoundNumberGenerator(),
    DuplicateEntryGenerator(),
    WeekendPostingGenerator(),
    SuspenseAccountGenerator(),
    AbnormalBalanceGenerator(),
    MissingOffsetGenerator(),
]


def get_generator(name: str) -> object:
    """Look up a generator by name.

    Args:
        name: The generator's name attribute.

    Returns:
        The matching AnomalyGenerator instance.

    Raises:
        KeyError: If no generator matches the name.
    """
    for g in ANOMALY_REGISTRY:
        if g.name == name:
            return g
    raise KeyError(f"No generator named '{name}'")
