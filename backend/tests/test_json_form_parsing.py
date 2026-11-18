"""Sprint 883 (review ST-09): a mapping of the wrong JSON shape is a 400, not a 500.

``parse_json_mapping`` ran ``json.loads`` and then ``mapping.keys()``, catching
only ``JSONDecodeError``: valid JSON of the wrong shape (``[]``, ``null``,
``"text"``) raised ``AttributeError`` and became a 500. Malformed JSON was
silently treated as "no mapping", so the request ran on auto-detected columns.

Now: not supplied → ``None``; supplied but not an object whose keys and values
are strings → one consistent 400 naming the field. ``parse_json_list`` gets the
same treatment where the element type matters.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from shared.helpers import parse_json_list, parse_json_mapping

WRONG_SHAPE_MAPPINGS = [
    "[]",
    '["Account"]',
    "null",
    '"text"',
    "5",
    "true",
    '{"account_column": 1}',
    '{"account_column": null}',
    '{"account_column": ["Account"]}',
    '{"account_column": {"x": "y"}}',
    "not json",
    "{",
]


def _mapping_detail(field: str) -> str:
    return f"Invalid {field}: expected a JSON object whose keys and values are strings."


class TestParseJsonMapping:
    @pytest.mark.parametrize("raw", [None, ""])
    def test_not_supplied_is_none(self, raw):
        assert parse_json_mapping(raw, "m") is None

    def test_valid_object(self):
        assert parse_json_mapping('{"account_column": "Acct", "debit_column": "Dr"}', "m") == {
            "account_column": "Acct",
            "debit_column": "Dr",
        }

    def test_empty_object_is_valid(self):
        assert parse_json_mapping("{}", "m") == {}

    @pytest.mark.parametrize("raw", WRONG_SHAPE_MAPPINGS)
    def test_invalid_is_one_400(self, raw):
        with pytest.raises(HTTPException) as exc:
            parse_json_mapping(raw, "m", field="column_mapping")
        assert exc.value.status_code == 400
        assert exc.value.detail == _mapping_detail("column_mapping")


class TestParseJsonList:
    @pytest.mark.parametrize("raw", [None, ""])
    def test_not_supplied_is_none(self, raw):
        assert parse_json_list(raw, "l") is None

    def test_untyped_list_keeps_elements(self):
        assert parse_json_list("[1, 2, 3]", "l") == [1, 2, 3]

    def test_typed_list(self):
        assert parse_json_list('["Sheet1", "Sheet2"]', "l", item_type=str) == ["Sheet1", "Sheet2"]

    @pytest.mark.parametrize("raw", ["{}", "null", '"Sheet1"', "not json"])
    def test_not_a_list_is_400(self, raw):
        with pytest.raises(HTTPException) as exc:
            parse_json_list(raw, "l", field="selected_sheets")
        assert exc.value.status_code == 400
        assert exc.value.detail == "Invalid selected_sheets: expected a JSON array."

    @pytest.mark.parametrize("raw", ["[1]", '["Sheet1", null]', '[["Sheet1"]]'])
    def test_wrong_element_type_is_400(self, raw):
        with pytest.raises(HTTPException) as exc:
            parse_json_list(raw, "l", field="selected_sheets", item_type=str)
        assert exc.value.status_code == 400
        assert exc.value.detail == "Invalid selected_sheets: expected a JSON array of strings."


# ---------------------------------------------------------------------------
# Every caller, over HTTP
# ---------------------------------------------------------------------------

_TB_CSV = b"Account,Debit,Credit\nCash,100,\nRevenue,,100\n"
_PAYMENTS_CSV = b"Invoice Number,Vendor Name,Amount,Payment Date\nINV-1,Acme,100.00,2026-01-15\n"
_JE_CSV = (
    b"Entry ID,Date,Account,Debit,Credit,Description\nJE-1,2026-01-15,Cash,100,,x\nJE-1,2026-01-15,Revenue,,100,x\n"
)
_BANK_CSV = b"Date,Description,Amount\n2026-01-15,Deposit,100.00\n"
_SAMPLE_CSV = b"Item ID,Description,Amount\n1,A,100.00\n2,B,200.00\n"


def _file(name: str, data: bytes) -> tuple[str, bytes, str]:
    return (name, data, "text/csv")


# (case id, path, form fields, files, mapping field names)
MAPPING_CALLERS = [
    ("trial_balance", "/audit/trial-balance", {}, {"file": _file("tb.csv", _TB_CSV)}, ["column_mapping"]),
    ("testing_route_ap", "/audit/ap-payments", {}, {"file": _file("ap.csv", _PAYMENTS_CSV)}, ["column_mapping"]),
    ("je_testing", "/audit/journal-entries", {}, {"file": _file("je.csv", _JE_CSV)}, ["column_mapping"]),
    ("je_sample", "/audit/journal-entries/sample", {}, {"file": _file("je.csv", _JE_CSV)}, ["column_mapping"]),
    (
        "je_sample_preview",
        "/audit/journal-entries/sample/preview",
        {},
        {"file": _file("je.csv", _JE_CSV)},
        ["column_mapping"],
    ),
    (
        "bank_reconciliation",
        "/audit/bank-reconciliation",
        {},
        {"bank_file": _file("bank.csv", _BANK_CSV), "ledger_file": _file("gl.csv", _BANK_CSV)},
        ["bank_column_mapping", "ledger_column_mapping"],
    ),
    (
        "ar_aging",
        "/audit/ar-aging",
        {},
        {"tb_file": _file("tb.csv", _TB_CSV)},
        ["tb_column_mapping", "sl_column_mapping"],
    ),
    (
        "sampling_design",
        "/audit/sampling/design",
        {"tolerable_misstatement": "1000"},
        {"file": _file("pop.csv", _SAMPLE_CSV)},
        ["column_mapping"],
    ),
    (
        "sampling_evaluate",
        "/audit/sampling/evaluate",
        {"tolerable_misstatement": "1000", "population_value": "300", "sample_size": "2"},
        {"file": _file("sample.csv", _SAMPLE_CSV)},
        ["column_mapping"],
    ),
]

_ROUTE_BAD_MAPPINGS = ["[]", "null", '"text"', '{"account_column": 1}', "not json"]


async def _post(path: str, data: dict[str, str], files: dict) -> tuple[int, object]:
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(path, data=data, files=files)
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return response.status_code, body


@pytest.mark.asyncio
@pytest.mark.usefixtures("override_auth_verified", "bypass_csrf")
@pytest.mark.parametrize("raw", _ROUTE_BAD_MAPPINGS)
@pytest.mark.parametrize(
    ("path", "form", "files", "fields"),
    [c[1:] for c in MAPPING_CALLERS],
    ids=[c[0] for c in MAPPING_CALLERS],
)
async def test_every_mapping_caller_returns_one_400(path, form, files, fields, raw):
    for field in fields:
        status, body = await _post(path, {**form, field: raw}, files)
        assert status == 400, (field, status, body)
        assert isinstance(body, dict)
        assert body["detail"] == _mapping_detail(field)


@pytest.mark.asyncio
@pytest.mark.usefixtures("override_auth_verified", "bypass_csrf")
@pytest.mark.parametrize("raw", ["[1]", '{"Sheet1": true}', "null", "not json"])
async def test_selected_sheets_of_the_wrong_shape_is_400(raw):
    status, body = await _post("/audit/trial-balance", {"selected_sheets": raw}, {"file": _file("tb.csv", _TB_CSV)})
    assert status == 400, body
    assert isinstance(body, dict) and body["detail"].startswith("Invalid selected_sheets: expected a JSON array")


@pytest.mark.asyncio
@pytest.mark.usefixtures("override_auth_verified", "bypass_csrf")
@pytest.mark.parametrize("path", ["/audit/journal-entries/sample", "/audit/journal-entries/sample/preview"])
@pytest.mark.parametrize("raw", ["[1]", "[null]", '{"account": 1}', "null", "not json"])
async def test_stratify_by_of_the_wrong_shape_is_400(path, raw):
    status, body = await _post(path, {"stratify_by": raw}, {"file": _file("je.csv", _JE_CSV)})
    assert status == 400, body
    assert isinstance(body, dict) and body["detail"].startswith("Invalid stratify_by: expected a JSON array")
