"""
Markup-safe ReportLab Paragraph — Sprint 846 (security review M1).

ReportLab's ``Paragraph`` parses its text as markup. Memo and report
templates interpolate account names, descriptions and client names from
uploaded files straight into that text, so a ledger description such as
``<a href="https://evil.example">View ledger</a>`` became a live link in an
exported, Paciolus-branded PDF. ``<font size=0>`` could hide text, and
``<img src=...>`` made the export fail.

This module is the only door to ``Paragraph`` for PDF code (enforced by
``tests/test_safe_paragraph_guard.py``). It keeps the small markup
vocabulary our templates use and escapes everything else, so any tag
arriving inside user data is printed as text:

- ``<b> <i> <u> <strong> <em> <strike> <super> <sup> <sub>`` with no attributes
- ``<br/>``
- ``<font>`` with only ``size`` (6–72) and ``color`` (``#rrggbb`` or ReportLab's ``0xrrggbb``)
- the named entities in ``_ALLOWED_ENTITIES`` and numeric entities

Interpolated user data can still use those formatting tags. Where a value is
known to be user-supplied, prefer ``escape_markup()`` (full escape) at the
call site; ``wrap_table_strings`` and ``build_memo_header`` already do.

If ReportLab still cannot parse the sanitized text (for example an
unbalanced ``<b>`` arriving in user data), the paragraph falls back to the
fully escaped text so the export completes instead of failing.
"""

from __future__ import annotations

import logging
import re
from typing import Any
from xml.sax.saxutils import escape as _xml_escape

from reportlab.platypus import Paragraph as _ReportLabParagraph

logger = logging.getLogger(__name__)

_SIMPLE_TAGS = frozenset({"b", "i", "u", "strong", "em", "strike", "super", "sup", "sub"})
_ALLOWED_ENTITIES = frozenset(
    {"nbsp", "amp", "lt", "gt", "quot", "apos", "bull", "mdash", "ndash", "hellip", "middot", "times", "deg", "copy"}
)

_TAG_RE = re.compile(r"<[^<>]*>")
_SIMPLE_TAG_RE = re.compile(r"</?([a-z]+)>")
_BR_RE = re.compile(r"<br\s*/?>")
_FONT_OPEN_RE = re.compile(r"<font((?:\s+[a-z]+\s*=\s*(?:\"[^\"]*\"|'[^']*'))+)\s*>")
_FONT_ATTR_RE = re.compile(r"([a-z]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')")
_COLOR_RE = re.compile(r"(?:#|0x)[0-9A-Fa-f]{6}")
_ENTITY_RE = re.compile(r"&(#[0-9]{1,7}|#x[0-9A-Fa-f]{1,6}|[A-Za-z]+);")

_MIN_FONT_SIZE = 6.0
_MAX_FONT_SIZE = 72.0


def escape_markup(value: Any) -> str:
    """Escape ``value`` completely so ReportLab renders it as literal text."""
    return _xml_escape(str(value))


def _font_tag_allowed(tag: str) -> bool:
    match = _FONT_OPEN_RE.fullmatch(tag)
    if not match:
        return False
    for name, dq, sq in _FONT_ATTR_RE.findall(match.group(1)):
        value = dq if dq else sq
        if name == "size":
            try:
                size = float(value)
            except ValueError:
                return False
            if not _MIN_FONT_SIZE <= size <= _MAX_FONT_SIZE:
                return False
        elif name == "color":
            if not _COLOR_RE.fullmatch(value):
                return False
        else:
            return False
    return True


def _tag_allowed(tag: str) -> bool:
    if tag == "</font>" or _BR_RE.fullmatch(tag):
        return True
    simple = _SIMPLE_TAG_RE.fullmatch(tag)
    if simple:
        return simple.group(1) in _SIMPLE_TAGS
    return _font_tag_allowed(tag)


def _escape_text_run(run: str) -> str:
    """Escape a run of text between tags, keeping allowed entities."""
    out: list[str] = []
    pos = 0
    for match in _ENTITY_RE.finditer(run):
        body = match.group(1)
        keep = body.startswith("#") or body in _ALLOWED_ENTITIES
        if not keep:
            continue
        out.append(_xml_escape(run[pos : match.start()]))
        out.append(match.group(0))
        pos = match.end()
    out.append(_xml_escape(run[pos:]))
    return "".join(out)


def sanitize_markup(text: str) -> str:
    """Keep the template markup vocabulary; escape every other tag and stray ``<``, ``>`` or ``&``."""
    out: list[str] = []
    pos = 0
    for match in _TAG_RE.finditer(text):
        out.append(_escape_text_run(text[pos : match.start()]))
        tag = match.group(0)
        out.append(tag if _tag_allowed(tag) else _xml_escape(tag))
        pos = match.end()
    out.append(_escape_text_run(text[pos:]))
    return "".join(out)


class Paragraph(_ReportLabParagraph):
    """ReportLab ``Paragraph`` whose text is sanitized before ReportLab parses it."""

    def __init__(self, text: Any, style: Any = None, *args: Any, **kwargs: Any) -> None:
        # ReportLab's own split() re-instantiates with text=None and pre-parsed frags.
        if text is None:
            super().__init__(text, style, *args, **kwargs)
            return
        raw = str(text)
        try:
            super().__init__(sanitize_markup(raw), style, *args, **kwargs)
        except ValueError:
            logger.warning("Paragraph markup could not be parsed; rendering it as plain text")
            super().__init__(escape_markup(raw), style, *args, **kwargs)
