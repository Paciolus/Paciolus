"""
Sprint 813 — every PDF the product ships carries its page chrome on every page.

Two defects shipped in customer PDFs because 14 of the 20 memo modules build
their page setup by hand rather than through ``generate_testing_memo``:

1. Six memos passed only ``onFirstPage`` to ``doc.build``. The cover always
   ends in a page break, so **every** content page lacked its page number
   and disclaimer.
2. Eleven memos never read the Enterprise ``PDFBrandingContext`` the route
   scopes for them, so a firm's header/footer appeared on some memos and
   not others.

These tests render all 21 sample reports through the real generators, under
an active branding context, and read the text back out of each page. They
check the output rather than the source, so they hold however a memo is
built.
"""

import io
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.memo_base import create_memo_styles
from shared.pdf_branding import PDFBrandingContext, apply_pdf_branding

HEADER = "ACME Audit Partners LLP"
FOOTER = "Confidential - Prepared for ACME Client Corp."
EXPECTED_REPORT_COUNT = 21


@pytest.fixture(scope="module")
def branded_reports(tmp_path_factory) -> dict[str, list[str]]:
    """Render every sample report under Enterprise branding → per-page text."""
    import generate_sample_reports as samples

    captured: dict[str, bytes] = {}
    original_save = samples.save_pdf
    samples.save_pdf = lambda name, pdf_bytes: captured.__setitem__(name, pdf_bytes)
    try:
        branding = PDFBrandingContext(tier_has_branding=True, header_text=HEADER, footer_text=FOOTER)
        with apply_pdf_branding(branding):
            for _label, generate in samples.GENERATORS:
                generate()
    finally:
        samples.save_pdf = original_save

    return {
        name: [page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf)).pages] for name, pdf in captured.items()
    }


def test_every_sample_report_was_rendered(branded_reports):
    assert len(branded_reports) == EXPECTED_REPORT_COUNT, sorted(branded_reports)


def test_every_content_page_is_numbered(branded_reports):
    missing = {
        name: [n for n, text in enumerate(pages[1:], start=2) if f"— {n} —" not in text]
        for name, pages in branded_reports.items()
    }
    missing = {name: pages for name, pages in missing.items() if pages}
    assert not missing, f"content pages without a page number (cover excluded): {missing}"


def test_every_content_page_carries_the_paciolus_disclaimer(branded_reports):
    missing = {
        name: [n for n, text in enumerate(pages[1:], start=2) if "not constitute an audit" not in text]
        for name, pages in branded_reports.items()
    }
    missing = {name: pages for name, pages in missing.items() if pages}
    assert not missing, f"content pages without the footer disclaimer: {missing}"


@pytest.mark.parametrize("text, label", [(HEADER, "header"), (FOOTER, "footer")])
def test_every_content_page_carries_enterprise_branding(branded_reports, text, label):
    missing = {
        name: [n for n, page in enumerate(pages[1:], start=2) if text not in page]
        for name, pages in branded_reports.items()
    }
    missing = {name: pages for name, pages in missing.items() if pages}
    assert not missing, f"content pages ignoring the firm's branded {label}: {missing}"


def test_memo_modules_build_through_render_memo():
    """Item 3: page setup, cover and page chrome live in one place,
    ``shared.memo_base.render_memo``. A memo that builds its own
    ``SimpleDocTemplate`` is how items 1 and 2 shipped."""
    backend = Path(__file__).parent.parent
    memo_modules = sorted(
        {*backend.glob("*_memo_generator.py"), *backend.glob("*_memo.py")}
        | {backend / "anomaly_summary_generator.py", backend / "shared" / "memo_template.py"}
    )
    assert len(memo_modules) >= 21, [p.name for p in memo_modules]
    hand_built = [p.name for p in memo_modules if "SimpleDocTemplate(" in p.read_text(encoding="utf-8")]
    assert not hand_built, f"memos building their own page setup instead of render_memo: {hand_built}"


def test_memo_styles_never_set_leading_below_font_size():
    """A 24pt ``MemoTitle`` on ReportLab's default 12pt leading was overprinted
    by the subtitle beneath it in every memo that used it."""
    styles = create_memo_styles()
    cramped = {
        name: (style.fontSize, style.leading) for name, style in styles.items() if style.leading < style.fontSize
    }
    assert not cramped, f"styles whose next line overprints them (fontSize, leading): {cramped}"
