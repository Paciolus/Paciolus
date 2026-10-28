"""Sprint 846 (security review M1): user text cannot inject ReportLab markup.

ReportLab's ``Paragraph`` parses its text as markup, and memo templates
interpolate account names and client names from uploaded files into it. A
ledger description of ``<a href="https://evil.example">…</a>`` used to become
a live, Paciolus-branded link in the exported PDF.

The fix is structural: ``shared.safe_paragraph.Paragraph`` is the only
``Paragraph`` PDF code may use. It keeps the template vocabulary (``<b>``,
``<i>``, ``<br/>``, ``<font size/color>``) and escapes every other tag. This
file pins the sanitizer, guards the import boundary, and drives malicious
account names through two real generators to confirm no link reaches a PDF.
"""

import ast
import io
import subprocess
from pathlib import Path

import pytest
from pypdf import PdfReader
from reportlab.lib.styles import getSampleStyleSheet

from shared.safe_paragraph import Paragraph, escape_markup, sanitize_markup

BACKEND = Path(__file__).resolve().parent.parent
_STYLE = getSampleStyleSheet()["Normal"]

LINK_PAYLOAD = '<a href="https://evil.example/login" color="blue">View source ledger</a>'
INJECTION_PAYLOADS = [
    LINK_PAYLOAD,
    '<link href="https://evil.example">x</link>',
    '<img src="https://evil.example/pixel.png" width="1" height="1"/>',
    '<font size="0">hidden</font>',
    '<font size=0 color="#ffffff">hidden</font>',
    '<onDraw name="setFont" label="x"/>',
    '<span backColor="#ffffff">x</span>',
    "Unbalanced <b>bold",
    "Revenue < 5% & R&D > 2",
]


def _uri_annotations(pdf_bytes: bytes) -> list[str]:
    uris = []
    for page in PdfReader(io.BytesIO(pdf_bytes)).pages:
        for annot in page.get("/Annots") or []:
            action = annot.get_object().get("/A")
            if action is not None and "/URI" in action:
                uris.append(str(action["/URI"]))
    return uris


def _pdf_text(pdf_bytes: bytes) -> str:
    return "".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf_bytes)).pages)


# ---------------------------------------------------------------------------
# Sanitizer
# ---------------------------------------------------------------------------


class TestSanitizeMarkup:
    @pytest.mark.parametrize(
        "template",
        [
            "<b>Total:</b> 12",
            "<i>Suggested Procedure: confirm balances</i>",
            "Line one<br/>line two",
            '<font size="7" color="#616161"><i>Asset</i></font>',
            "<font color='0x616161'>tie</font>",
            "<strong>Note</strong> &nbsp;&bull;&nbsp; ref &amp; more &#x2713;",
        ],
    )
    def test_template_vocabulary_is_untouched(self, template):
        assert sanitize_markup(template) == template

    @pytest.mark.parametrize(
        "tag",
        [
            '<a href="https://evil.example">',
            "<link href='x'>",
            '<img src="x"/>',
            '<font size="0">',
            '<font size="200">',
            '<font face="Courier">',
            '<font color="white">',
            '<font color="#ffffff" onClick="x">',
            '<onDraw name="x"/>',
            "<span>",
            "<para>",
        ],
    )
    def test_other_tags_are_escaped(self, tag):
        out = sanitize_markup(tag)
        assert "<" not in out and ">" not in out
        assert out.startswith("&lt;")

    def test_stray_angle_brackets_and_ampersands_are_escaped(self):
        assert sanitize_markup("a < b & c > d") == "a &lt; b &amp; c &gt; d"

    def test_unknown_named_entity_is_escaped(self):
        assert sanitize_markup("&evil;") == "&amp;evil;"

    def test_escape_markup_escapes_everything(self):
        assert escape_markup("<b>x</b> & y") == "&lt;b&gt;x&lt;/b&gt; &amp; y"


class TestSafeParagraph:
    @pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
    def test_payloads_render_without_error(self, payload):
        Paragraph(f"Account: {payload}", _STYLE).wrap(400, 800)

    def test_link_payload_renders_as_literal_text(self):
        para = Paragraph(LINK_PAYLOAD, _STYLE)
        assert para.getPlainText() == LINK_PAYLOAD

    def test_unbalanced_markup_falls_back_to_plain_text(self):
        para = Paragraph("Unbalanced <b>bold", _STYLE)
        assert para.getPlainText() == "Unbalanced <b>bold"

    def test_template_markup_still_formats(self):
        para = Paragraph("<b>Total:</b> 12", _STYLE)
        assert para.getPlainText() == "Total: 12"


# ---------------------------------------------------------------------------
# Import boundary guard
# ---------------------------------------------------------------------------

_SKIP_DIRS = {"tests", "venv", ".venv", "migrations", "alembic", "__pycache__"}
_EXEMPT = {"shared/safe_paragraph.py"}


def test_no_module_imports_reportlab_paragraph_directly():
    listed = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=BACKEND, capture_output=True, text=True, check=True
    ).stdout.split()
    offenders = []
    for name in listed:
        rel = Path(name)
        if rel.parts[0] in _SKIP_DIRS or rel.as_posix() in _EXEMPT:
            continue
        tree = ast.parse((BACKEND / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("reportlab.platypus"):
                if any(alias.name == "Paragraph" for alias in node.names):
                    offenders.append(f"{rel.as_posix()}:{node.lineno}")
            elif isinstance(node, ast.Attribute) and node.attr == "Paragraph":
                if isinstance(node.value, ast.Attribute) and node.value.attr == "platypus":
                    offenders.append(f"{rel.as_posix()}:{node.lineno}")
    assert not offenders, (
        "ReportLab's Paragraph parses markup from user data — import it from shared.safe_paragraph:\n  "
        + "\n  ".join(offenders)
    )


# ---------------------------------------------------------------------------
# End to end: malicious account names through real generators
# ---------------------------------------------------------------------------


class TestGeneratedPdfsCarryNoInjectedLinks:
    def test_accrual_memo_table_cells_and_client_name(self):
        from accrual_completeness_memo import generate_accrual_completeness_memo

        report = {
            "accrual_accounts": [
                {
                    "account_name": LINK_PAYLOAD,
                    "balance": 5000,
                    "matched_keyword": '<font size="0">hidden</font>',
                    "classification": "Accrued Liability",
                },
            ],
            "total_accrued_balance": 5000,
            "accrual_account_count": 1,
            "narrative": "Test.",
        }
        pdf = generate_accrual_completeness_memo(report, "test.csv", client_name=LINK_PAYLOAD)
        assert pdf[:4] == b"%PDF"
        assert _uri_annotations(pdf) == []
        assert "evil.example" in _pdf_text(pdf)

    def test_diagnostic_report_fstring_templates(self):
        from pdf_generator import generate_audit_report

        result = {
            "balanced": False,
            "total_debits": 100000.0,
            "total_credits": 99000.0,
            "difference": 1000.0,
            "row_count": 50,
            "materiality_threshold": 500.0,
            "abnormal_balances": [
                {
                    "account": LINK_PAYLOAD,
                    "type": '<img src="https://evil.example/p.png"/>',
                    "issue": "Suspense account with balance",
                    "amount": 1000.0,
                    "materiality": "material",
                }
            ],
            "risk_summary": {"total_anomalies": 1, "high_severity": 1, "low_severity": 0},
            "material_count": 1,
            "immaterial_count": 0,
        }
        pdf = generate_audit_report(result, LINK_PAYLOAD)
        assert pdf[:5] == b"%PDF-"
        assert _uri_annotations(pdf) == []
