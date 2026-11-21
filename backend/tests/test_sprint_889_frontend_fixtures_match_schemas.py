"""Sprint 889 (CEO brief 14D, review TQ-09): frontend fixtures are responses the backend could send.

The JE page test mocked ``composite_score`` and ``data_quality`` as empty objects, which
``JETestingResponse`` rejects. The success-case fixture the page test now renders is validated
here, so a fixture that drifts from the schema (a renamed or dropped required field) fails CI.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from shared.testing_response_schemas import JETestingResponse

FIXTURES = Path(__file__).resolve().parents[2] / "frontend" / "src" / "__tests__" / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_je_success_fixture_is_a_valid_response():
    parsed = JETestingResponse.model_validate(_load("je-testing-response.json"))
    assert parsed.composite_score.total_entries == 1200
    assert parsed.test_results[0].entries_flagged == len(parsed.test_results[0].flagged_entries)


@pytest.mark.parametrize("field", ["score", "risk_tier", "tests_run", "total_entries", "total_flagged", "flag_rate"])
def test_dropping_a_required_score_field_is_rejected(field):
    body = _load("je-testing-response.json")
    del body["composite_score"][field]
    with pytest.raises(ValidationError):
        JETestingResponse.model_validate(body)


def test_the_old_empty_object_mock_was_never_a_valid_response():
    with pytest.raises(ValidationError):
        JETestingResponse.model_validate(
            {"composite_score": {}, "test_results": [], "data_quality": {}, "benford_result": None}
        )
