"""Fit custom branding text inside a bounded band — Sprint 885 (review OUT-27).

Enterprise firms may set a header (≤ 200 characters) and a footer (≤ 300).
Both were drawn as one centred line, so text within the allowed length could
run far past both margins and over the page number and the Paciolus
disclaimer.

``draw_fitted_text`` keeps the text inside a ``TextBand`` — a horizontal span
inside the margins and a range of baselines clear of the page number and the
disclaimer:

1. one line at the normal size when it fits (short text is drawn exactly as before);
2. otherwise wrapped onto as many lines as the band holds, shrinking the size
   step by step down to ``min_size``;
3. if even that cannot hold it, the last line ends with an ellipsis.

Words longer than a line are broken between characters (text without spaces,
e.g. Chinese, wraps too).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from reportlab.pdfbase.pdfmetrics import stringWidth

ELLIPSIS = "…"
_LEADING = 1.2
_STEP = 0.5


@dataclass(frozen=True)
class TextBand:
    """Where branding text may go. ``bottom``/``top`` bound the *baselines*."""

    left: float
    right: float
    bottom: float
    top: float
    anchor: float  # baseline of a single line (the pre-Sprint-885 position)
    size: float
    min_size: float

    @property
    def width(self) -> float:
        return self.right - self.left


def _break_word(word: str, font: str, size: float, width: float) -> list[str]:
    pieces, current = [], ""
    for ch in word:
        if current and stringWidth(current + ch, font, size) > width:
            pieces.append(current)
            current = ch
        else:
            current += ch
    if current:
        pieces.append(current)
    return pieces


def wrap_text(text: str, font: str, size: float, width: float) -> list[str]:
    """Greedy word wrap to ``width``; over-long words are broken between characters."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if stringWidth(candidate, font, size) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
        if stringWidth(word, font, size) <= width:
            current = word
        else:
            *full, current = _break_word(word, font, size, width)
            lines.extend(full)
    if current:
        lines.append(current)
    return lines


def fit_text(text: str, font: str, band: TextBand) -> tuple[float, list[str]]:
    """The size and lines that keep ``text`` inside ``band``."""
    text = " ".join(text.split())
    span = band.top - band.bottom
    size = band.size
    while True:
        lines = wrap_text(text, font, size, band.width)
        if (len(lines) - 1) * size * _LEADING <= span + 1e-6:
            return size, lines
        if size <= band.min_size:
            break
        size = max(band.min_size, size - _STEP)
    # Still too long at the minimum size: keep what fits and end with an ellipsis.
    max_lines = int(span // (size * _LEADING)) + 1
    kept = lines[:max_lines]
    last = kept[-1]
    while last and stringWidth(last + ELLIPSIS, font, size) > band.width:
        last = last[:-1]
    kept[-1] = last.rstrip() + ELLIPSIS
    return size, kept


def draw_fitted_text(canvas: Any, text: str, font: str, band: TextBand) -> None:
    """Draw ``text`` centred inside ``band`` (the caller sets the fill colour)."""
    size, lines = fit_text(text, font, band)
    if not lines:
        return
    leading = size * _LEADING
    block = (len(lines) - 1) * leading
    # Centre the block on the single-line position, kept inside the band.
    first = min(band.top, max(band.bottom + block, band.anchor + block / 2))
    centre_x = (band.left + band.right) / 2
    canvas.setFont(font, size)
    for i, line in enumerate(lines):
        canvas.drawCentredString(centre_x, first - i * leading, line)
