"""Property-based tests for anomaly generators.

Uses Hypothesis to verify that anomaly generators produce valid output
across a range of parameters and seeds. These tests focus on robustness
(no crashes, valid structure) rather than detection accuracy.
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from audit_engine import audit_trial_balance_streaming
from tests.anomaly_framework.fixtures.base_trial_balance import BaseTrialBalanceFactory
from tests.anomaly_framework.generators.duplicate_entry import DuplicateEntryGenerator
from tests.anomaly_framework.generators.round_number import RoundNumberGenerator


@given(
    seed=st.integers(min_value=0, max_value=9999),
    num_duplicates=st.integers(min_value=2, max_value=8),
)
@settings(max_examples=25, suppress_health_check=[HealthCheck.too_slow])
def test_duplicate_detection_is_seed_independent(seed, num_duplicates):
    """Verify duplicate injection works across seeds and duplicate counts."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    gen = DuplicateEntryGenerator(num_duplicates=num_duplicates)
    mutated_df, records = gen.inject(base_df, seed=seed)

    # Structural checks on the generator output
    assert len(mutated_df) == len(base_df) + num_duplicates
    assert len(records) == 1
    assert records[0].anomaly_type == "duplicate_entry"

    # Engine processes without error
    csv_bytes = mutated_df.to_csv(index=False).encode()
    result = audit_trial_balance_streaming(file_bytes=csv_bytes, filename="prop_test.csv")
    assert result.get("row_count", 0) > 0


@given(amount_scale=st.floats(min_value=100.0, max_value=1_000_000.0))
@settings(max_examples=25, suppress_health_check=[HealthCheck.too_slow])
def test_round_number_detection_across_scales(amount_scale):
    """Verify round number injection works across amount scales."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    gen = RoundNumberGenerator(amount_scale=amount_scale)
    mutated_df, records = gen.inject(base_df, seed=0)

    # Structural checks
    assert len(mutated_df) == len(base_df)
    assert len(records) == 1
    assert records[0].anomaly_type == "round_number"

    # Engine processes without error
    csv_bytes = mutated_df.to_csv(index=False).encode()
    result = audit_trial_balance_streaming(file_bytes=csv_bytes, filename="prop_test.csv")
    assert result.get("row_count", 0) > 0
