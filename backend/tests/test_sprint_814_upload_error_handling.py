"""
Sprint 814 — malformed numeric input is a 400, never a 500.

1. ``parse_uploaded_file`` crashed with ``OverflowError`` when an identifier
   column (check number, GL account, account number) held ``Infinity`` or
   ``1e999999``: it ran ``int(float(x))`` to strip a trailing ``.0``. Found by
   injecting 13 garbage numerics into every cell of the AP, JE, Payroll,
   Revenue, Fixed Asset and Inventory fixtures — 5 of the 6 tools 500'd.
2. ``run_single_file_testing`` (the six single-file testing tools) never
   received Sprint 713's ``ArithmeticError`` handling, so anything in that
   family escaped as a 500 and was logged at ERROR.
3. Both sampling handlers likewise let ``ArithmeticError`` through. Not
   reproduced from real input (the sampling engine parses through
   ``safe_decimal``) — the handler is defence in depth, pinned here so it
   stays.
"""

from __future__ import annotations

import logging
import sys
from decimal import InvalidOperation
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.testing_route import parse_uploaded_file, run_single_file_testing


@pytest.mark.parametrize("value", ["Infinity", "-inf", "1e999999"])
def test_non_finite_value_in_identifier_column_parses(value):
    csv = f"Check Number,Vendor,Amount\n1001,Acme,100.00\n{value},Acme,200.00\n1003,Beta,300.00\n".encode()

    columns, rows = parse_uploaded_file(csv, "payments.csv")

    assert columns == ["Check Number", "Vendor", "Amount"]
    assert rows[0]["Check Number"] == "1001", "finite integral IDs still lose their trailing .0"
    assert rows[1]["Check Number"] in {"inf", "-inf"}


class _FakeUpload:
    filename = "ap.csv"

    async def read(self) -> bytes:
        return b"x"

    async def seek(self, pos: int) -> None:
        return None


@pytest.mark.asyncio
async def test_testing_route_maps_arithmetic_error_to_400_at_warning(caplog):
    def _engine(rows, cols, mapping, filename):
        raise InvalidOperation("malformed decimal")

    caplog.set_level(logging.DEBUG, logger="shared.testing_route")
    with (
        patch("shared.testing_route.enforce_tool_access"),
        patch("shared.testing_route.check_upload_limit"),
        patch("shared.testing_route.validate_file_size", return_value=b"bytes"),
        patch("shared.testing_route.parse_uploaded_file", return_value=(["a"], [{"a": 1}])),
        patch("shared.testing_route.maybe_record_tool_run") as record,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await run_single_file_testing(
                file=_FakeUpload(),  # type: ignore[arg-type]
                column_mapping=None,
                engagement_id=None,
                current_user=MagicMock(id=1),
                db=MagicMock(),
                background_tasks=MagicMock(),
                tool_name="ap_testing",
                mapping_key="ap_testing",
                log_label="AP",
                error_key="ap_testing_error",
                run_engine=_engine,
            )

    assert exc_info.value.status_code == 400
    assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []
    assert any("ap_testing rejected" in r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)
    record.assert_called_once()  # the failed run is still recorded


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
@pytest.mark.parametrize(
    "path, target, form",
    [
        ("/audit/sampling/design", "_run_design", {"method": "mus", "tolerable_misstatement": "1000"}),
        (
            "/audit/sampling/evaluate",
            "_run_evaluation",
            {"method": "mus", "population_value": "10000", "sample_size": "5", "tolerable_misstatement": "1000"},
        ),
    ],
)
async def test_sampling_maps_arithmetic_error_to_422(override_auth_verified, path, target, form):
    import httpx

    from main import app

    with patch(f"routes.sampling.{target}", side_effect=InvalidOperation("malformed decimal")):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                path, data=form, files={"file": ("sample.csv", b"item_id,recorded_amount\nA,1\n", "text/csv")}
            )

    assert response.status_code == 422, response.text
    assert "malformed decimal" not in response.text, "decimal-module text must not reach the user"


def test_no_tool_run_is_recorded_in_a_background_task():
    """Starlette sends the response body before it awaits background tasks,
    so the client's immediate ``refreshToolRuns()`` raced the insert and could
    cache a run list without the new row (PR #183 fixed six routes; Sprint 814
    the remaining eleven call sites). Record synchronously, always."""
    import ast

    backend = Path(__file__).parent.parent
    offenders = []
    for path in [*backend.glob("routes/*.py"), *backend.glob("shared/*.py"), *backend.glob("services/**/*.py")]:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_task"
                and node.args
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "maybe_record_tool_run"
            ):
                offenders.append(f"{path.relative_to(backend)}:{node.lineno}")
    assert not offenders, f"tool runs recorded after the response is sent: {offenders}"
