"""Sprint 889 (CEO brief 14F, review TQ-15): a loss year is never presented as a complete provision.

CEO decision 2026-11-20: recognising a net operating loss is out of scope. For a loss year the tool
says plainly that no NOL deferred tax asset or valuation allowance has been computed. The tool also
has no input for NOL carryforwards from earlier years, so its standing scope note says that a
profitable year after a loss may show too much current tax.
"""

import csv
import io
from decimal import Decimal

import httpx
import pytest

from book_to_tax_engine import (
    LOSS_YEAR_LIMITATION,
    NOL_CARRYFORWARD_SCOPE_NOTE,
    BookToTaxConfig,
    calculate_book_to_tax,
)


def _loss_config() -> BookToTaxConfig:
    return BookToTaxConfig(
        tax_year=2026,
        book_pretax_income=Decimal("-100000"),
        total_assets=Decimal("1000000"),
        federal_tax_rate=Decimal("0.21"),
        adjustments=[],
    )


def _profit_config() -> BookToTaxConfig:
    return BookToTaxConfig(
        tax_year=2026,
        book_pretax_income=Decimal("100000"),
        total_assets=Decimal("1000000"),
        federal_tax_rate=Decimal("0.21"),
        adjustments=[],
    )


class TestEngine:
    def test_loss_of_100000_has_zero_current_tax_and_the_limitation(self):
        p = calculate_book_to_tax(_loss_config()).tax_provision
        assert p.taxable_income == Decimal("-100000.00")
        assert p.current_federal_tax == Decimal("0.00")
        assert p.current_state_tax == Decimal("0.00")
        assert p.is_complete is False
        assert LOSS_YEAR_LIMITATION in p.limitations
        assert "no net operating loss deferred tax asset or valuation allowance has been computed" in (
            LOSS_YEAR_LIMITATION
        )

    def test_profitable_year_carries_only_the_standing_scope_note(self):
        p = calculate_book_to_tax(_profit_config()).tax_provision
        assert p.current_federal_tax == Decimal("21000.00")  # 100,000 x 21%
        assert LOSS_YEAR_LIMITATION not in p.limitations
        assert NOL_CARRYFORWARD_SCOPE_NOTE in p.limitations

    def test_the_scope_note_names_the_missing_carryforward_input(self):
        assert "carryforward" in NOL_CARRYFORWARD_SCOPE_NOTE
        assert "overstated" in NOL_CARRYFORWARD_SCOPE_NOTE

    def test_to_dict_carries_the_limitation(self):
        d = calculate_book_to_tax(_loss_config()).to_dict()["tax_provision"]
        assert d["is_complete"] is False
        assert LOSS_YEAR_LIMITATION in d["limitations"]


_LOSS_PAYLOAD = {
    "tax_year": 2026,
    "book_pretax_income": "-100000",
    "total_assets": "1000000",
    "federal_tax_rate": "0.21",
    "adjustments": [],
}


@pytest.mark.usefixtures("bypass_csrf")
class TestRoutes:
    @pytest.mark.asyncio
    async def test_json_route_carries_the_limitation(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post("/audit/book-to-tax", json=_LOSS_PAYLOAD)
        assert r.status_code == 200, r.text
        provision = r.json()["tax_provision"]
        assert provision["current_federal_tax"] == "0.00"
        assert provision["is_complete"] is False
        assert LOSS_YEAR_LIMITATION in provision["limitations"]

    @pytest.mark.asyncio
    async def test_csv_export_carries_the_limitation(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post("/audit/book-to-tax/export.csv", json=_LOSS_PAYLOAD)
        assert r.status_code == 200, r.text
        cells = [c for row in csv.reader(io.StringIO(r.text.lstrip("﻿"))) for c in row]
        assert LOSS_YEAR_LIMITATION in cells
        assert NOL_CARRYFORWARD_SCOPE_NOTE in cells
