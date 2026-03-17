"""
Shared page-chrome helpers for Paciolus PDF reports.

Provides page-level decoration callbacks (watermark, header rules, footer,
page numbers) used by the diagnostic and financial-statements orchestrators.
These callbacks are passed as onFirstPage / onLaterPages to ReportLab's
SimpleDocTemplate.build().
"""

from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

from pdf.styles import ClassicalColors

# ---------------------------------------------------------------------------
# Diagnostic report chrome
# ---------------------------------------------------------------------------


def draw_diagnostic_watermark(canvas: Any, _doc: Any = None) -> None:
    """Draw the Pacioli watermark -- diagonal Latin text unique to the
    diagnostic intelligence summary."""
    page_width, page_height = letter

    canvas.saveState()
    canvas.setFillColor(ClassicalColors.OATMEAL_400)
    canvas.setFillAlpha(0.04)  # Very subtle
    canvas.setFont("Times-Italic", 48)
    canvas.translate(page_width / 2, page_height / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "Particularis de Computis")
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Financial-statements report chrome
# ---------------------------------------------------------------------------


def draw_fs_decorations(canvas: Any, doc: Any, page_counter: list[int]) -> None:
    """Page decorations for financial statements PDF.

    *page_counter* is a mutable single-element list so the caller can track
    the current page number across calls.
    """
    canvas.saveState()
    page_counter[0] += 1
    page_width, page_height = letter

    # Watermark
    canvas.saveState()
    canvas.setFillColor(ClassicalColors.OATMEAL_400)
    canvas.setFillAlpha(0.04)
    canvas.setFont("Times-Italic", 48)
    canvas.translate(page_width / 2, page_height / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "Particularis de Computis")
    canvas.restoreState()

    # Top gold double rule
    canvas.setStrokeColor(ClassicalColors.GOLD_INSTITUTIONAL)
    canvas.setLineWidth(2)
    canvas.line(0.75 * inch, page_height - 0.5 * inch, page_width - 0.75 * inch, page_height - 0.5 * inch)
    canvas.setLineWidth(0.5)
    canvas.line(0.75 * inch, page_height - 0.55 * inch, page_width - 0.75 * inch, page_height - 0.55 * inch)

    # Bottom rule
    canvas.setStrokeColor(ClassicalColors.LEDGER_RULE)
    canvas.setLineWidth(0.5)
    canvas.line(0.75 * inch, 0.75 * inch, page_width - 0.75 * inch, 0.75 * inch)

    # Page number
    canvas.setFont("Times-Roman", 9)
    canvas.setFillColor(ClassicalColors.OBSIDIAN_500)
    canvas.drawCentredString(page_width / 2, 0.5 * inch, f"\u2014 {page_counter[0]} \u2014")

    # Disclaimer
    canvas.setFont("Times-Roman", 7)
    disclaimer = (
        "This output supports professional judgment and internal evaluation. "
        "It does not constitute an audit, review, or attestation engagement."
    )
    canvas.drawCentredString(page_width / 2, 0.35 * inch, disclaimer)
    canvas.restoreState()
