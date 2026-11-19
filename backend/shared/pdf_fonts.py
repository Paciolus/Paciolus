"""Embedded PDF fonts — Sprint 885 (review OUT-25).

The PDFs used ReportLab's standard Times, Helvetica and Courier fonts. They
are not embedded and carry only a Western encoding, so a Greek or Cyrillic
client name printed as substitute symbols.

The Liberation fonts (SIL Open Font License 1.1, ``backend/fonts/liberation``)
are metric-compatible with those three families — the same character widths —
and cover Latin with accents, Greek and Cyrillic. They are registered **under
the standard names** (``Times-Roman``, ``Times-Bold``, ``Helvetica``,
``Courier-Oblique`` …), so every style, table, canvas call and ReportLab
default that names a standard font gets the embedded font, bold and italic
included, without a layout change. Chinese, Japanese and Korean are deferred
(``tasks/todo.md``, Deferred Items).

Template symbols the Liberation fonts lack (✓ ✗ ⚠ ❧ ◆ ▢ …) are drawn from
DejaVu Sans: ``symbol_fallback`` wraps them in ``<font name="PaciolusSymbols">``
inside every ``Paragraph`` (the standard fonts never had them either — they
printed a substitute box). A character neither font can draw prints as a
visible ``□`` instead of an invisible or misleading glyph, and ``build_pdf``
adds a note at the end of the document saying so.

``register_pdf_fonts()`` runs when this module is imported; ``pdf`` and
``shared.safe_paragraph`` import it, so it is in place before any PDF is built.
"""

from __future__ import annotations

import contextvars
import re
from pathlib import Path
from typing import Any

from reportlab.lib.fonts import addMapping
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts" / "liberation"
SYMBOL_FONT_PATH = Path(__file__).resolve().parent.parent / "fonts" / "dejavu" / "DejaVuSans.ttf"
SYMBOL_FONT = "PaciolusSymbols"

REPLACEMENT_CHARACTER = "□"  # □ — U+FFFD is not in the Liberation fonts
UNSUPPORTED_NOTE = (
    f"Note: some characters in this document are not supported by its fonts and are shown as {REPLACEMENT_CHARACTER}."
)

# standard name → Liberation file stem, per family: (regular, bold, italic, bold italic)
_FAMILIES: dict[str, tuple[tuple[str, str], ...]] = {
    "times": (
        ("Times-Roman", "LiberationSerif-Regular"),
        ("Times-Bold", "LiberationSerif-Bold"),
        ("Times-Italic", "LiberationSerif-Italic"),
        ("Times-BoldItalic", "LiberationSerif-BoldItalic"),
    ),
    "helvetica": (
        ("Helvetica", "LiberationSans-Regular"),
        ("Helvetica-Bold", "LiberationSans-Bold"),
        ("Helvetica-Oblique", "LiberationSans-Italic"),
        ("Helvetica-BoldOblique", "LiberationSans-BoldItalic"),
    ),
    "courier": (
        ("Courier", "LiberationMono-Regular"),
        ("Courier-Bold", "LiberationMono-Bold"),
        ("Courier-Oblique", "LiberationMono-Italic"),
        ("Courier-BoldOblique", "LiberationMono-BoldItalic"),
    ),
}

# The characters replaced while the current document is built (None outside ``build_pdf``).
_replaced: contextvars.ContextVar[set[str] | None] = contextvars.ContextVar("pdf_unsupported_chars", default=None)


class CoverageTTFont(TTFont):
    """A ``TTFont`` that draws ``□`` for any character it has no glyph for, and records it."""

    def _supported(self, text: Any) -> Any:
        if not isinstance(text, str):
            return text
        glyphs = self.face.charToGlyph
        if all(ord(c) in glyphs or c in "\n\r\t\xa0" for c in text):
            return text
        replaced = _replaced.get()
        out = []
        for c in text:
            if ord(c) in glyphs or c in "\n\r\t\xa0":
                out.append(c)
            else:
                out.append(REPLACEMENT_CHARACTER)
                if replaced is not None:
                    replaced.add(c)
        return "".join(out)

    def splitString(self, text: Any, doc: Any, encoding: str = "utf-8") -> Any:  # noqa: N802 (ReportLab API)
        return super().splitString(self._supported(text), doc, encoding)

    def stringWidth(self, text: Any, size: float, encoding: str = "utf8") -> float:  # noqa: N802 (ReportLab API)
        return float(super().stringWidth(self._supported(text), size, encoding))


_registered = False
_text_glyphs: frozenset[int] = frozenset()
_symbol_glyphs: frozenset[int] = frozenset()


def register_pdf_fonts() -> None:
    """Register the Liberation fonts under the standard font names (idempotent)."""
    global _registered
    if _registered:
        return
    for family, members in _FAMILIES.items():
        for name, stem in members:
            pdfmetrics.registerFont(CoverageTTFont(name, str(FONT_DIR / f"{stem}.ttf")))
        (regular, _), (bold, _), (italic, _), (bold_italic, _) = members
        # <b>/<i> inside a Paragraph resolve through these mappings, by family
        # and by the regular font's own name.
        for key in {family, regular.lower()}:
            addMapping(key, 0, 0, regular)
            addMapping(key, 1, 0, bold)
            addMapping(key, 0, 1, italic)
            addMapping(key, 1, 1, bold_italic)
        pdfmetrics.registerFontFamily(regular, normal=regular, bold=bold, italic=italic, boldItalic=bold_italic)
    symbols = TTFont(SYMBOL_FONT, str(SYMBOL_FONT_PATH))
    pdfmetrics.registerFont(symbols)
    pdfmetrics.registerFontFamily(
        SYMBOL_FONT, normal=SYMBOL_FONT, bold=SYMBOL_FONT, italic=SYMBOL_FONT, boldItalic=SYMBOL_FONT
    )
    global _text_glyphs, _symbol_glyphs
    # A character every text face has (checked on the narrowest set: all twelve).
    faces = [pdfmetrics.getFont(name).face.charToGlyph for members in _FAMILIES.values() for name, _ in members]
    _text_glyphs = frozenset(set.intersection(*(set(f) for f in faces)))
    _symbol_glyphs = frozenset(symbols.face.charToGlyph)
    _registered = True


_TAG = re.compile(r"(<[^<>]*>|&#[xX]?[0-9A-Fa-f]+;)")


def _needs_symbol_font(code: int) -> bool:
    return code > 0x7E and code not in _text_glyphs and code in _symbol_glyphs


def symbol_fallback(markup: str) -> str:
    """Wrap characters only the symbol font has in ``<font name="PaciolusSymbols">`` (Paragraph markup)."""
    if all(ord(c) < 0x7F for c in markup) and "&#" not in markup:
        return markup
    out: list[str] = []
    for part in _TAG.split(markup):
        if not part:
            continue
        if part.startswith("&#"):
            body = part[2:-1]
            code = int(body[1:], 16) if body[:1] in "xX" else int(body)
            out.append(f'<font name="{SYMBOL_FONT}">{part}</font>' if _needs_symbol_font(code) else part)
        elif part.startswith("<"):
            out.append(part)
        else:
            out.append(
                "".join(f'<font name="{SYMBOL_FONT}">{c}</font>' if _needs_symbol_font(ord(c)) else c for c in part)
            )
    return "".join(out)


class _UnsupportedCharactersNote(Flowable):
    """Last flowable of a document: the note, only if a character was replaced.

    ReportLab draws each flowable as it is placed, so by the time this one is
    laid out every earlier line of the document has been drawn (and recorded).
    """

    def __init__(self, replaced: set[str], style: ParagraphStyle) -> None:
        super().__init__()
        self._replaced = replaced
        self._style = style
        self._para: Any = None

    def wrap(self, avail_width: float, avail_height: float) -> tuple[float, float]:
        if not self._replaced:
            return 0, 0
        from shared.safe_paragraph import Paragraph  # lazy: safe_paragraph imports this module

        self._para = Paragraph(UNSUPPORTED_NOTE, self._style)
        w, h = self._para.wrap(avail_width, avail_height)
        return w, h + 6

    def draw(self) -> None:
        if self._para is not None:
            self._para.drawOn(self.canv, 0, 0)


_NOTE_STYLE = ParagraphStyle("_UnsupportedCharsNote", fontName="Times-Italic", fontSize=8, leading=10)


def build_pdf(doc: Any, story: list, **build_kwargs: Any) -> None:
    """``doc.build(story, **build_kwargs)``, adding the unsupported-characters note when needed."""
    replaced: set[str] = set()
    token = _replaced.set(replaced)
    try:
        doc.build([*story, _UnsupportedCharactersNote(replaced, _NOTE_STYLE)], **build_kwargs)
    finally:
        _replaced.reset(token)


register_pdf_fonts()
