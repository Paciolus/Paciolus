"""Sprint 885 / 10I (review OUT-27): long branding text stays on the page.

Custom header (≤ 200 characters) and footer (≤ 300) text was drawn as one
centred line, so text within the allowed length could run far off both edges
and over the page number and the Paciolus disclaimer. It is now fitted inside
a bounded band — shrunk down to a minimum size, then wrapped onto as many
lines as the band holds, with an ellipsis if even that is not enough.

Checked on the rendered PDF: every character of the branding text lies inside
the margins and inside its band, clear of the page number and disclaimer.
"""

from __future__ import annotations

import io

import pytest
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth

HEADER = ("WMW Wide Header Partners LLP " * 10)[:200]
FOOTER = ("ЖШЩ Широкий нижний колонтитул — Confidential " * 10)[:300]
HEADER_WIDE_NO_SPACES = "W" * 200
FOOTER_WIDE_NO_SPACES = "Ж" * 300

_FONTS = {"LiberationSerif": "Times-Roman", "LiberationSans": "Helvetica", "LiberationMono": "Courier"}


def _font_name(font_dict) -> str:
    base = str(font_dict.get("/BaseFont", "")).split("+")[-1]
    for key, value in _FONTS.items():
        if base.startswith(key):
            suffix = base[len(key) :]
            return {"": value, "-Bold": value + "-Bold" if value != "Times-Roman" else "Times-Bold"}.get(suffix, value)
    return "Times-Roman"


def _runs(pdf: bytes, page_index: int) -> list[tuple[float, float, float, float, str]]:
    """(x0, x1, y, size, text) for every text run on one page."""
    out = []
    page = PdfReader(io.BytesIO(pdf)).pages[page_index]

    def visit(text, cm, tm, font_dict, font_size, out=out):
        if not text.strip() or font_dict is None:
            return
        size = font_size * (tm[0] or 1) * (cm[0] or 1)
        x = cm[4] + tm[4] * cm[0]
        y = cm[5] + tm[5] * cm[3]
        width = stringWidth(text.rstrip("\n"), _font_name(font_dict), size)
        out.append((x, x + width, y, size, text))

    page.extract_text(visitor_text=visit)
    return out


def _memo(header: str, footer: str) -> bytes:
    from je_testing_memo_generator import generate_je_testing_memo
    from shared.pdf_branding import PDFBrandingContext, apply_pdf_branding
    from tests.test_sprint819_output_snapshots import CASES

    branding = PDFBrandingContext(tier_has_branding=True, header_text=header, footer_text=footer)
    with apply_pdf_branding(branding):
        return generate_je_testing_memo(CASES["je"](), filename="gl")


def _fs(header: str, footer: str) -> bytes:
    from export.serializers.pdf import serialize_financial_statements_pdf
    from financial_statement_builder import FinancialStatementBuilder
    from shared.export_schemas import FinancialStatementsInput
    from shared.pdf_branding import PDFBrandingContext, apply_pdf_branding

    payload = FinancialStatementsInput(
        lead_sheet_grouping={"summaries": [{"lead_sheet": "A", "name": "Cash", "net_balance": 100.0, "accounts": []}]},
        entity_name="Wide Co",
    )
    statements = FinancialStatementBuilder(payload.lead_sheet_grouping.model_dump(exclude_unset=True)).build()
    branding = PDFBrandingContext(tier_has_branding=True, header_text=header, footer_text=footer)
    with apply_pdf_branding(branding):
        return serialize_financial_statements_pdf(payload, statements)


def _check(pdf: bytes, header: str, footer: str, page_index: int = 1, kind: str = "memo") -> None:
    from shared.report_chrome import branding_bands

    bands = branding_bands(kind)
    page_w = letter[0]
    runs = _runs(pdf, page_index)
    hdr_chars = set(header.replace(" ", ""))
    ftr_chars = set(footer.replace(" ", ""))
    header_runs = [r for r in runs if r[2] > letter[1] - 60 and set(r[4].strip().replace(" ", "")) <= hdr_chars | {"…"}]
    footer_runs = [r for r in runs if r[2] < 60 and set(r[4].strip().replace(" ", "")) <= ftr_chars | {"…"}]
    assert header_runs and footer_runs
    for x0, x1, y, size, text in header_runs + footer_runs:
        assert x0 >= bands.left - 0.5 and x1 <= page_w - bands.right + 0.5, (x0, x1, text[:20])
        assert size >= bands.min_size - 0.01
    for _x0, _x1, y, _size, _t in header_runs:
        assert bands.header_bottom - 0.5 <= y <= bands.header_top, y
    for _x0, _x1, y, _size, _t in footer_runs:
        assert bands.footer_bottom - 0.5 <= y <= bands.footer_top, y
    others = [r for r in runs if r not in header_runs and r not in footer_runs and r[2] < 60]
    page_number = [r for r in others if "—" in r[4] and any(ch.isdigit() for ch in r[4])]
    disclaimer = [r for r in others if "Paciolus" in r[4] or "attestation" in r[4]]
    assert page_number and disclaimer
    for _x0, _x1, y, size, _t in footer_runs:
        for _a, _b, oy, osize, _ot in page_number + disclaimer:
            # baselines at least one text height apart: no overlap
            assert abs(y - oy) >= min(size, osize) * 0.9, (y, oy)


@pytest.mark.parametrize(
    ("header", "footer"),
    [(HEADER, FOOTER), (HEADER_WIDE_NO_SPACES, FOOTER_WIDE_NO_SPACES)],
    ids=["words", "no_spaces"],
)
def test_memo_branding_text_fits(header, footer):
    _check(_memo(header, footer), header, footer)


def test_memo_short_text_is_unchanged_in_size():
    from shared.report_chrome import branding_bands

    runs = _runs(_memo("ACME Audit Partners LLP", "Confidential"), 1)
    header = [r for r in runs if "ACME Audit Partners LLP" in r[4]]
    assert header and header[0][3] == branding_bands().header_size


def test_financial_statements_branding_text_fits():
    _check(_fs(HEADER, FOOTER), HEADER, FOOTER, kind="fs")
