"""
Reusable Flowable subclasses and small utility functions for Paciolus PDFs.

Contains DoubleRule, LedgerRule, and helper functions (leader dots,
date formatting, reference number generation) that are shared across
all report types.
"""

import re
from datetime import UTC, datetime
from typing import Any, Optional

from reportlab.platypus import Flowable

from pdf.styles import ClassicalColors

# ---------------------------------------------------------------------------
# Custom Flowables
# ---------------------------------------------------------------------------


class DoubleRule(Flowable):
    """
    A double-rule flowable for classical document borders.

    Creates the signature "Goldman Sachs" style header rule:
    thick line + gap + thin line
    """

    def __init__(
        self,
        width: float,
        color: Any = ClassicalColors.GOLD_INSTITUTIONAL,
        thick: float = 2,
        thin: float = 0.5,
        gap: float = 2,
        spaceAfter: float = 12,
    ) -> None:
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thick = thick
        self.thin = thin
        self.gap = gap
        self._spaceAfter = spaceAfter

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)

        # Thick rule
        self.canv.setLineWidth(self.thick)
        self.canv.line(0, self.gap + self.thin, self.width, self.gap + self.thin)

        # Thin rule below
        self.canv.setLineWidth(self.thin)
        self.canv.line(0, 0, self.width, 0)

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self.width = min(self.width, availWidth) if self.width else availWidth
        return (self.width, self.thick + self.gap + self.thin + self._spaceAfter)


class LedgerRule(Flowable):
    """A simple horizontal ledger rule."""

    def __init__(
        self,
        width: Optional[float] = None,
        thickness: float = 0.5,
        color: Any = ClassicalColors.LEDGER_RULE,
        spaceBefore: float = 8,
        spaceAfter: float = 8,
    ) -> None:
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color
        self._spaceBefore = spaceBefore
        self._spaceAfter = spaceAfter

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self.width = min(self.width, availWidth) if self.width else availWidth
        return (self.width, self.thickness + self._spaceBefore + self._spaceAfter)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def format_classical_date(dt: datetime | None = None) -> str:
    """
    Format date in classical style: '4th February 2026'
    """
    if dt is None:
        dt = datetime.now(UTC)

    day = dt.day
    # Ordinal suffix
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    return dt.strftime(f"{day}{suffix} %B %Y")


def generate_reference_number(prefix: str = "PAC") -> str:
    """Generate institutional reference number: ``<prefix>-YYYY-MMDD-NNN``.

    Each memo passes its own prefix (``"APT"``, ``"WP-FE"``, ...); the default
    is the platform-wide ``PAC``.
    """
    now = datetime.now(UTC)
    # Simple sequential based on time (in production, use a proper sequence)
    seq = (now.hour * 3600 + now.minute * 60 + now.second) % 1000
    return f"{prefix}-{now.year}-{now.month:02d}{now.day:02d}-{seq:03d}"


def _shown_length(text: str) -> int:
    """Characters a reader sees: tags dropped, entities counted as one character."""
    return len(re.sub(r"&(?:#\d+|#x[0-9a-fA-F]+|[A-Za-z]+);", "_", re.sub(r"<[^<>]*>", "", text)))


def create_leader_dots(label: str, value: Any, total_chars: int = 55) -> str:
    """
    Create a leader-dot line for financial summaries.

    Example: "Total Debits .......................... $1,234,567.89"

    ``label`` is template markup (``PP&amp;E``, ``<b>Total</b>``); a label that
    is data — an account or statement line name — is passed as
    ``user_text(name)``. ``value`` is data and is escaped here (Sprint 885,
    OUT-24); pass ``template_markup(...)`` for a value that is template
    markup. Dots are counted from the characters a reader sees. The line is
    returned marked as escaped, so ``user_text(line)`` leaves it unchanged.
    """
    from shared.safe_paragraph import EscapedText, user_text

    shown_value = user_text(value)
    label_len = _shown_length(label)
    value_len = _shown_length(shown_value)
    dots_needed = total_chars - label_len - value_len - 2  # -2 for spaces

    if dots_needed < 3:
        dots_needed = 3

    dots = "." * dots_needed
    return EscapedText(f"{label} {dots} {shown_value}")
