"""Sprint 885 / 10D (review OUT-24): uploaded or user text cannot restyle a PDF.

``safe_paragraph.Paragraph`` keeps a small formatting vocabulary (``<b>``,
``<i>``, ``<font size/color>``) so templates can use it — but it was applied
*after* user values were joined into the template, so an uploaded account
name ``<font color="#ffffff">…</font>`` printed white (invisible) in an
exported, Paciolus-branded memo. Every value from an upload or a user is now
fully escaped before it is joined to template markup; the filter stays as a
second layer.

The detector: every memo the sample-report script renders is rendered again
with a white-text ``<font>`` tag appended to each free-text input (account
names, descriptions, client name, file name, period, preparer …). Escaped,
the tag prints literally and text extraction shows it; obeyed, only the bare
marker survives. Every marker must arrive with its tag.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import functools
import io
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from freezegun import freeze_time
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).parent.parent))

MARK = "TZQ"
TAINT = f'<font color="#ffffff">{MARK}</font>'
# What extraction shows for an escaped tag: the run never wraps (no spaces in it).
ESCAPED_RUN = f'"#ffffff">{MARK}'

# Machine values a generator branches on: enum-like tokens, dates, numbers.
_LOGIC_VALUE = re.compile(r"^(?:[a-z0-9_]*|\d{4}-\d{2}-\d{2}(?:[T ][\d:.]+Z?)?|[-+]?[\d,.]+%?)$")
# Keys whose values are labels/codes a generator looks up, not free text.
_LOGIC_KEYS = {
    "test_key",
    "test_tier",
    "severity",
    "risk_tier",
    "risk_level",
    "tier",
    "band",
    "materiality",
    "anomaly_type",
    "status",
    "category_key",
    "lead_sheet",
    "method",
    "currency",
    "from_currency",
    "to_currency",
    "base_currency",
    "presentation_currency",
    "source_currency",
    "conclusion",
    "direction",
    "tool",
    "tool_name",
    "key",
}


def _taint(value: Any, key: str | None = None) -> Any:
    if isinstance(value, str):
        if key in _LOGIC_KEYS or _LOGIC_VALUE.match(value) or len(value) < 3:
            return value
        return value + TAINT
    if isinstance(value, dict):
        return {k: _taint(v, k if isinstance(k, str) else None) for k, v in value.items()}
    if isinstance(value, list):
        return [_taint(v, key) for v in value]
    if isinstance(value, tuple) and not hasattr(value, "_fields"):
        return tuple(_taint(v, key) for v in value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        clone = copy.copy(value)
        for f in dataclasses.fields(value):
            try:
                setattr(clone, f.name, _taint(getattr(value, f.name), f.name))
            except (AttributeError, dataclasses.FrozenInstanceError):
                pass
        return clone
    if isinstance(value, SimpleNamespace):
        return SimpleNamespace(**{k: _taint(v, k) for k, v in vars(value).items()})
    return value


def _sample_targets() -> dict[str, list[tuple[str, str]]]:
    """gen_* function → the (module, generator) pairs it imports and calls."""
    src = (Path(__file__).parent.parent / "generate_sample_reports.py").read_text(encoding="utf-8")
    out: dict[str, list[tuple[str, str]]] = {}
    for fn in ast.parse(src).body:
        if isinstance(fn, ast.FunctionDef) and fn.name.startswith("gen_"):
            for node in ast.walk(fn):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for alias in node.names:
                        if (
                            alias.name.startswith(("generate_", "render_"))
                            and alias.name != "generate_reference_number"
                        ):
                            out.setdefault(fn.name, []).append((node.module, alias.name))
    return out


SAMPLES = _sample_targets()


def _render_tainted(gen_name: str, monkeypatch: pytest.MonkeyPatch) -> bytes:
    import importlib

    import generate_sample_reports as samples

    for module_name, func_name in SAMPLES[gen_name]:
        module = importlib.import_module(module_name)
        original = getattr(module, func_name)

        @functools.wraps(original)
        def wrapper(*args: Any, __original: Any = original, **kwargs: Any) -> Any:
            return __original(*[_taint(a) for a in args], **{k: _taint(v, k) for k, v in kwargs.items()})

        monkeypatch.setattr(module, func_name, wrapper)

    captured: list[bytes] = []
    monkeypatch.setattr(samples, "save_pdf", lambda _name, pdf: captured.append(pdf))
    with freeze_time("2026-03-02 09:30:15"):
        getattr(samples, gen_name)()
    assert len(captured) == 1
    return captured[0]


def _text(pdf: bytes) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf)).pages)


@pytest.mark.parametrize("gen_name", sorted(SAMPLES))
def test_user_markup_prints_literally(gen_name, monkeypatch):
    text = _text(_render_tainted(gen_name, monkeypatch))
    # Case-insensitive: some values are shown upper-cased after escaping.
    compact = re.sub(r"\s+", "", text).lower()
    markers = compact.count(MARK.lower())
    escaped = compact.count(ESCAPED_RUN.replace(" ", "").lower())
    assert markers > 0, "no tainted input reached the PDF — the detector is not exercising this memo"
    assert markers == escaped, f"{markers - escaped} user value(s) were parsed as markup in {gen_name}"


# ─────────────────────────── the paragraph layer ───────────────────────────


class TestEscapingHelpers:
    def test_uploaded_tags_print_literally(self):
        from reportlab.lib.styles import getSampleStyleSheet

        from shared.report_styles import FONT_BODY  # noqa: F401  (fonts registered)
        from shared.safe_paragraph import Paragraph, user_text

        hostile = '<font color="#ffffff">hidden</font>'
        p = Paragraph(f"<b>Account:</b> {user_text(hostile)}", getSampleStyleSheet()["Normal"])
        plain = "".join(f.text for f in p.frags)
        assert '<font color="#ffffff">hidden</font>' in plain

    def test_template_emphasis_still_renders(self):
        from reportlab.lib.styles import getSampleStyleSheet

        from shared.safe_paragraph import Paragraph, user_text

        p = Paragraph(f"<b>Account:</b> {user_text('Cash')}", getSampleStyleSheet()["Normal"])
        bold = [f for f in p.frags if "Account:" in f.text]
        assert bold and bold[0].fontName.endswith(("Bold", "-Bold", "BD"))

    def test_ampersand_prints_once(self):
        from reportlab.lib.styles import getSampleStyleSheet

        from shared.safe_paragraph import Paragraph, user_text

        p = Paragraph(f"Line: {user_text('PP&E')}", getSampleStyleSheet()["Normal"])
        assert "".join(f.text for f in p.frags) == "Line: PP&E"

    def test_already_escaped_value_is_not_double_escaped(self):
        from shared.safe_paragraph import user_text

        assert user_text(user_text("PP&E")) == "PP&amp;E"


# ─────────────── memos built from engagement records, not the sample script ───────────────


def _assert_all_escaped(pdf: bytes) -> None:
    compact = re.sub(r"\s+", "", _text(pdf)).lower()
    markers = compact.count(MARK.lower())
    assert markers > 0
    assert markers == compact.count(ESCAPED_RUN.replace(" ", "").lower())


def _tainted_engagement(request):
    from datetime import UTC, datetime

    from engagement_manager import EngagementManager

    db = request.getfixturevalue("db_session")
    user = request.getfixturevalue("make_user")()
    client = request.getfixturevalue("make_client")(user=user, name="Acme Corp" + TAINT)
    eng = EngagementManager(db).create_engagement(
        user.id,
        client.id,
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 12, 31, tzinfo=UTC),
        materiality_amount=100000.0,
    )
    return db, user, eng


def test_analytical_expectations_memo(request):
    from analytical_expectation_memo_generator import AnalyticalExpectationMemoGenerator
    from analytical_expectations_manager import AnalyticalExpectationsManager
    from analytical_expectations_model import ExpectationTargetType

    db, user, eng = _tainted_engagement(request)
    mgr = AnalyticalExpectationsManager(db)
    exp = mgr.create_expectation(
        user_id=user.id,
        engagement_id=eng.id,
        procedure_target_type=ExpectationTargetType.BALANCE,
        procedure_target_label="Cash and equivalents" + TAINT,
        expected_range_low=100000.0,
        expected_range_high=125000.0,
        precision_threshold_amount=5000.0,
        corroboration_basis_text="Budget review" + TAINT,
        corroboration_tags=["budget"],
        cpa_notes="Spike from a pre-payment." + TAINT,
    )
    mgr.update_expectation(user_id=user.id, expectation_id=exp.id, result_actual_value=140000.0)
    _assert_all_escaped(AnalyticalExpectationMemoGenerator(db).generate_pdf(user.id, eng.id))


def test_sum_schedule_memo(request):
    from decimal import Decimal

    from sum_schedule_memo_generator import SumScheduleMemoGenerator
    from uncorrected_misstatements_manager import UncorrectedMisstatementsManager
    from uncorrected_misstatements_model import MisstatementClassification, MisstatementSourceType

    db, user, eng = _tainted_engagement(request)
    UncorrectedMisstatementsManager(db).create_misstatement(
        user_id=user.id,
        engagement_id=eng.id,
        source_type=MisstatementSourceType.KNOWN_ERROR,
        source_reference="JE-77" + TAINT,
        description="Cut-off error" + TAINT,
        accounts_affected=[{"account": "Revenue" + TAINT, "debit_credit": "CR", "amount": 10000}],
        classification=MisstatementClassification.FACTUAL,
        fs_impact_net_income=Decimal("-10000.00"),
        fs_impact_net_assets=Decimal("0.00"),
    )
    _assert_all_escaped(SumScheduleMemoGenerator(db).generate_pdf(user.id, eng.id))


def test_engagement_dashboard_memo():
    from engagement_dashboard_memo import generate_engagement_dashboard_memo
    from tests.test_engagement_dashboard_memo import _make_dashboard_result

    pdf = generate_engagement_dashboard_memo(
        _taint(_make_dashboard_result()),
        client_name="Meridian Capital Group" + TAINT,
        period_tested="FY 2025" + TAINT,
        prepared_by="John Doe" + TAINT,
        reviewed_by="Jane Smith" + TAINT,
        workpaper_date="2025-12-31",
        include_signoff=True,
    )
    _assert_all_escaped(pdf)
