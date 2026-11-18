"""Sprint 885 / 10C (review OUT-33): CSV text is protected by what the column is.

The safe CSV writer used to skip escaping for any string that *looked* like a
number, so a text identifier such as "+00123" or "-00123" went out bare and a
spreadsheet turned it into the number 123 (or -123). The writer now decides
by type: a ``str`` is text and is always protected; amounts are passed as
numbers or Decimals and stay numeric.
"""

import csv
import io
from decimal import Decimal

import pytest

from shared.filenames import safe_csv_writer


def _write(row: list[object]) -> list[str]:
    buf = io.StringIO()
    safe_csv_writer(buf).writerow(row)
    return next(csv.reader(io.StringIO(buf.getvalue())))


class TestTextIdentifiers:
    def test_leading_zero_identifier_keeps_its_exact_text(self):
        assert _write(["00123"]) == ["00123"]

    @pytest.mark.parametrize("identifier", ["+00123", "-00123", "-1,234.56", "+12", "-0.5%"])
    def test_signed_text_is_escaped_not_left_to_become_a_number(self, identifier):
        # The escape mark plus the exact original text: never the bare number.
        assert _write([identifier]) == ["'" + identifier]


class TestAmounts:
    @pytest.mark.parametrize("amount", [Decimal("-123.45"), -123.45])
    def test_negative_amount_passed_as_a_number_stays_numeric(self, amount):
        assert _write([amount]) == ["-123.45"]

    def test_ints_and_none(self):
        assert _write([-7, 0, None]) == ["-7", "0", ""]


class TestExportsPassAmountsAsNumbers:
    """No export writes a negative amount as pre-formatted text (it would now be escaped)."""

    def test_tb_csv_negative_net_balance_is_bare(self):
        from export.serializers.csv import serialize_trial_balance_csv
        from shared.schemas import AuditResultInput

        payload = {
            "status": "balanced",
            "balanced": True,
            "total_debits": 100.0,
            "total_credits": 100.0,
            "difference": 0.0,
            "row_count": 2,
            "message": "ok",
            "abnormal_balances": [],
            "has_risk_alerts": False,
            "materiality_threshold": 10.0,
            "material_count": 0,
            "immaterial_count": 0,
            "filename": "tb",
            "all_accounts": [
                {"account": "-00123 Cash", "debit": 100.0, "credit": 0.0, "type": "asset"},
                {"account": "+00456", "debit": 0.0, "credit": 100.0, "type": "liability"},
            ],
        }
        rows = list(
            csv.reader(io.StringIO(serialize_trial_balance_csv(AuditResultInput(**payload)).decode("utf-8-sig")))
        )
        text = "\n".join(",".join(r) for r in rows)
        assert "'-00123 Cash" in text
        assert "'+00456" in text
        assert "-100.00" in text
        assert "'-100.00" not in text


class TestNumberCell:
    def test_same_text_as_the_f_string(self):
        from shared.filenames import number_cell

        assert number_cell(Decimal("-1234.5"), ",.2f") == f"{Decimal('-1234.5'):,.2f}"
        assert _write([number_cell(-0.125, ".1f", "%")]) == [f"{-0.125:.1f}%"]

    def test_text_that_is_not_a_number_is_escaped(self):
        from shared.filenames import number_cell

        assert _write([number_cell(float("-inf"), ".2f")]) == ["'-inf"]


class TestUntypedShareRewrite:
    def test_client_supplied_csv_keeps_numbers_and_escapes_formulas(self):
        from routes.export_sharing import _rewrite_csv_share

        out = _rewrite_csv_share(b"Account,Amount\r\n=1+1,-123.45\r\n").decode("utf-8")
        assert list(csv.reader(io.StringIO(out))) == [["Account", "Amount"], ["'=1+1", "-123.45"]]
