"""Sprint 885 / 10G (review OUT-25): PDF fonts show accented Latin, Greek and Cyrillic.

The PDFs used the standard Times, Helvetica and Courier fonts, which carry no
Greek or Cyrillic (and print substitute symbols for them). The Liberation
fonts (SIL Open Font License) now stand in for all three families, bold and
italic included. A character they still cannot draw — Chinese, Japanese or
Korean, deferred by CEO decision — prints as a visible "□", and the document
says so in a note.
"""

from __future__ import annotations

import io

import pytest
from pypdf import PdfReader

ACCENTED = "Société Générale — Zürich Ærø Łódź Ñandú"
GREEK = "Αθήνα Ελληνική Εταιρεία"
CYRILLIC = "ООО «Москва» Отчёт"
CJK = "北京有限公司"


def _text(pdf: bytes) -> str:
    return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(pdf)).pages)


def _fonts(pdf: bytes) -> set[str]:
    names: set[str] = set()
    for page in PdfReader(io.BytesIO(pdf)).pages:
        for font in (page.get("/Resources", {}).get("/Font", {}) or {}).values():
            names.add(str(font.get_object().get("/BaseFont")))
    return names


def _memo(client_name: str, **kw) -> bytes:
    from je_testing_memo_generator import generate_je_testing_memo
    from tests.test_sprint819_output_snapshots import CASES

    return generate_je_testing_memo(CASES["je"](), filename="gl", client_name=client_name, **kw)


@pytest.mark.parametrize("sample", [ACCENTED, GREEK, CYRILLIC], ids=["accented", "greek", "cyrillic"])
def test_text_renders_and_extracts(sample):
    pdf = _memo(sample, period_tested=sample, prepared_by=sample, include_signoff=True)
    text = _text(pdf)
    assert sample in text
    assert "□" not in text
    assert "not supported" not in text


def test_bold_and_italic_use_the_embedded_family():
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate

    from shared.safe_paragraph import Paragraph

    buf = io.BytesIO()
    style = ParagraphStyle("t", fontName="Times-Roman", fontSize=10)
    SimpleDocTemplate(buf).build([Paragraph(f"<b>{CYRILLIC}</b> <i>{GREEK}</i> {ACCENTED}", style)])
    pdf = buf.getvalue()
    text = _text(pdf)
    for sample in (CYRILLIC, GREEK, ACCENTED):
        assert sample in text
    fonts = " ".join(_fonts(pdf))
    assert "LiberationSerif-Bold" in fonts and "LiberationSerif-Italic" in fonts
    assert "Times" not in fonts  # no standard (non-embedded) font left


def test_courier_and_helvetica_are_covered_too():
    from reportlab.pdfgen.canvas import Canvas

    buf = io.BytesIO()
    c = Canvas(buf)
    for i, name in enumerate(("Courier", "Courier-Bold", "Helvetica", "Helvetica-Oblique")):
        c.setFont(name, 10)
        c.drawString(72, 700 - 20 * i, CYRILLIC)
    c.save()
    assert _text(buf.getvalue()).count(CYRILLIC) == 4


def test_unsupported_script_shows_the_replacement_and_a_note():
    text = _text(_memo(CJK))
    assert "□" * len(CJK) in text
    assert CJK not in text
    assert "not supported" in text


def test_reports_carry_the_note_too():
    from pdf import generate_audit_report

    audit = {
        "status": "balanced",
        "balanced": True,
        "total_debits": 1.0,
        "total_credits": 1.0,
        "difference": 0.0,
        "row_count": 1,
        "message": "ok",
        "abnormal_balances": [
            {"account": CJK, "type": "asset", "issue": "x", "amount": 1.0, "materiality": "material"}
        ],
        "has_risk_alerts": True,
        "materiality_threshold": 1.0,
        "material_count": 1,
        "immaterial_count": 0,
    }
    text = _text(generate_audit_report(audit, CJK))
    assert "□" in text and "not supported" in text


def test_no_note_when_every_character_is_supported():
    assert "not supported" not in _text(_memo("Plain Client LLC"))
