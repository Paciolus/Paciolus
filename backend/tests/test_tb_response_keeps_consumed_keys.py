"""Sprint 873: a key the pipeline emits and a consumer reads must survive the response model.

`AbnormalBalanceResponse` ignores undeclared fields, so a flag a rule adds is
silently dropped from every API response. The app then sends that stripped
payload back for the TB PDF. `coverage_analysis` and `cross_reference_note` were
both lost this way while the PDF code that reads them looked correct.

The consumer side is read from the PDF section's source (every ``ab.get("...")``);
the producer side is every TB anomaly generator run through the real pipeline.
"""

import re
from pathlib import Path

import pytest

from audit_engine import audit_trial_balance_streaming
from shared.diagnostic_response_schemas import AbnormalBalanceResponse
from tests.anomaly_framework.fixtures.base_trial_balance import BaseTrialBalanceFactory
from tests.anomaly_framework.registry import ANOMALY_REGISTRY

PDF_SECTION = Path(__file__).resolve().parents[1] / "pdf" / "sections" / "diagnostic.py"


def _pdf_consumed_keys() -> set[str]:
    return set(re.findall(r'\bab\.get\("([a-z_]+)"', PDF_SECTION.read_text(encoding="utf-8")))


@pytest.fixture(scope="module")
def emitted_keys() -> set[str]:
    keys: set[str] = set()
    for generator in ANOMALY_REGISTRY:
        df, _ = generator.inject(BaseTrialBalanceFactory.as_dataframe(), seed=42)
        result = audit_trial_balance_streaming(df.to_csv(index=False).encode(), "tb.csv", materiality_threshold=0.0)
        for row in result.get("abnormal_balances", []):
            keys |= set(row)
    return keys


def test_the_parser_finds_the_pdf_consumers():
    """Self-check: an empty or shrunken key set would make the gate pass vacuously."""
    consumed = _pdf_consumed_keys()
    assert {"coverage_analysis", "cross_reference_note", "severity", "materiality"} <= consumed
    assert len(consumed) >= 8


def test_generators_exercise_the_flags_this_gate_exists_for(emitted_keys):
    assert {"coverage_analysis", "cross_reference_note"} <= emitted_keys


def test_every_emitted_key_the_pdf_reads_is_declared(emitted_keys):
    declared = set(AbnormalBalanceResponse.model_fields)
    missing = sorted((_pdf_consumed_keys() & emitted_keys) - declared)
    assert missing == [], f"AbnormalBalanceResponse strips keys the TB PDF reads: {missing}"


def test_declared_keys_survive_serialization(emitted_keys):
    """Through the real model, not just its field list."""
    df, _ = next(g for g in ANOMALY_REGISTRY if g.name.endswith("concentration")).inject(
        BaseTrialBalanceFactory.as_dataframe(), seed=42
    )
    result = audit_trial_balance_streaming(df.to_csv(index=False).encode(), "tb.csv", materiality_threshold=0.0)
    rows = [AbnormalBalanceResponse.model_validate(r).model_dump() for r in result["abnormal_balances"]]
    assert any(r.get("coverage_analysis") is True for r in rows)
