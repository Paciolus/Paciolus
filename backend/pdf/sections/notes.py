"""
Notes to Financial Statements section renderer.

Renders the placeholder footnote stubs that the engagement team must
complete before the document is finalized or distributed.
"""

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf.components import LedgerRule
from pdf.styles import ClassicalColors

_FOOTNOTE_STUBS = [
    (
        "Note 1 \u2014 Basis of Presentation",
        "To be completed by management. Describe the basis of accounting, reporting period, "
        "and any significant departures from the applicable financial reporting framework.",
    ),
    (
        "Note 2 \u2014 Significant Accounting Policies",
        "Revenue Recognition: [Describe policy per ASC 606]\n"
        "Inventory Valuation: [Describe method \u2014 FIFO, LIFO, weighted average]\n"
        "Depreciation Method: [Describe method and useful life ranges]\n"
        "Income Taxes: [Describe tax status \u2014 LLC pass-through or corporate]",
    ),
    (
        "Note 3 \u2014 Long-Term Debt",
        "Describe terms, interest rate, maturity date, and collateral for outstanding "
        "long-term debt balances and current portions.",
    ),
    (
        "Note 4 \u2014 Related Party Transactions",
        "Disclose any transactions with related parties during the period, including "
        "intercompany receivable/payable balances identified in the trial balance.",
    ),
    (
        "Note 5 \u2014 Subsequent Events",
        "Disclose any material events occurring after the period end through the date these statements were prepared.",
    ),
]


def render_notes(story: list, styles: dict) -> None:
    """Append the Notes to Financial Statements section to *story*."""

    story.append(Spacer(1, 8))
    story.append(Paragraph("\u2767", styles["SectionOrnament"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Notes to Financial Statements", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 4))

    # Placeholder callout -- bordered box for high visibility
    notes_callout_text = (
        "<b>PLACEHOLDER NOTICE</b><br/><br/>"
        "The following notes are structural placeholders. Paciolus does not generate "
        "note content. The engagement team must complete all note disclosures before "
        "this document is finalized or distributed."
    )
    notes_callout = Table(
        [[Paragraph(notes_callout_text, styles["DocumentRef"])]],
        colWidths=[5.5 * inch],
    )
    notes_callout.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.5, ClassicalColors.GOLD_INSTITUTIONAL),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("BACKGROUND", (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
            ]
        )
    )
    notes_callout.hAlign = "CENTER"
    story.append(notes_callout)
    story.append(Spacer(1, 12))

    for note_title, note_body in _FOOTNOTE_STUBS:
        story.append(Paragraph(f"<b>{note_title}</b>", styles["DocumentRef"]))
        story.append(Spacer(1, 2))
        # Render placeholder text in italics
        for line in note_body.split("\n"):
            story.append(Paragraph(f"<i>{line.strip()}</i>", styles["DocumentRef"]))
        story.append(Spacer(1, 8))
