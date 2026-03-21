"""Anomaly detection integration tests.

Runs each anomaly generator against the audit engine and verifies that the
injected anomaly is detected in the engine's output. Uses parametrize to
test all generators from the registry.
"""

import pytest

from audit_engine import audit_trial_balance_streaming
from tests.anomaly_framework.fixtures.base_trial_balance import BaseTrialBalanceFactory
from tests.anomaly_framework.registry import ANOMALY_REGISTRY


@pytest.fixture
def base_df():
    """Provide a clean, balanced trial balance DataFrame."""
    return BaseTrialBalanceFactory.as_dataframe()


@pytest.mark.parametrize("generator", ANOMALY_REGISTRY, ids=lambda g: g.name)
def test_anomaly_is_detected(generator, base_df):
    """Verify that each generator's injected anomaly is detected by the engine."""
    mutated_df, anomaly_records = generator.inject(base_df, seed=42)
    csv_bytes = mutated_df.to_csv(index=False).encode()

    result = audit_trial_balance_streaming(
        file_bytes=csv_bytes,
        filename="anomaly_test.csv",
        materiality_threshold=0.0,
    )

    assert result.get("status") == "success", (
        f"[{generator.name}] Engine returned non-success status: {result.get('status')}"
    )

    for record in anomaly_records:
        field_value = result.get(record.expected_field)
        assert _evaluate_condition(field_value, record.expected_condition), (
            f"[{generator.name}] Report targets {record.report_targets}: "
            f"Expected result['{record.expected_field}'] to satisfy "
            f"'{record.expected_condition}' but got: {_summarize(field_value)}\n"
            f"Injected at: {record.injected_at}"
        )


def _summarize(value: object) -> str:
    """Create a concise summary of a value for assertion messages."""
    if isinstance(value, list):
        if len(value) == 0:
            return "[] (empty list)"
        if len(value) <= 3:
            return repr(value)
        return f"[{len(value)} items, first: {value[0]!r}]"
    return repr(value)


def _evaluate_condition(value: object, condition: str) -> bool:
    """Evaluate string conditions against a value.

    Supported conditions (no eval — explicit logic only):
        'count > 0'                       → len(value) > 0 if iterable, else value > 0
        'len > 0'                         → len(value) > 0
        'value == True'                   → value is True
        'value == False'                  → value is False
        'not empty'                       → bool(value)
        'any_match key=val'               → any(item.get(key) == val for item in value)
    """
    condition = condition.strip()

    # any_match key=val — check list of dicts for a matching field value
    if condition.startswith("any_match "):
        rest = condition[len("any_match ") :]
        if "=" not in rest:
            raise ValueError(f"any_match condition must have key=value format: {condition}")
        key, val = rest.split("=", 1)
        key = key.strip()
        val = val.strip()
        if not isinstance(value, list):
            return False
        return any(isinstance(item, dict) and str(item.get(key, "")) == val for item in value)

    # count > N
    if condition.startswith("count > "):
        n = int(condition[len("count > ") :])
        if hasattr(value, "__len__"):
            return len(value) > n
        if isinstance(value, (int, float)):
            return value > n
        return False

    # len > N
    if condition.startswith("len > "):
        n = int(condition[len("len > ") :])
        if hasattr(value, "__len__"):
            return len(value) > n
        return False

    # value == True / value == False
    if condition == "value == True":
        return value is True
    if condition == "value == False":
        return value is False

    # not empty
    if condition == "not empty":
        return bool(value)

    raise ValueError(f"Unsupported condition: {condition}")
