"""Loan Amortization PDF export (Sprint 672).

Renders the amortization schedule as a multi-page PDF suitable for
engagement workpaper evidence. Sections rendered, in order:

  1. Inputs block (principal, rate, term, method, start date, extras)
  2. Summary cards (period payment, total interest, total payments, payoff)
  3. Annual summary table
  4. Period-by-period schedule (paginated — 360 rows must flow across pages)

The Table uses ``repeatRows=1`` so the header row reappears on every page
of the schedule, and the document uses letter landscape to give the eight
schedule columns enough room.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from decimal import Decimal

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from loan_amortization_engine import AmortizationResult
from pdf.components import LedgerRule
from pdf.styles import ClassicalColors, create_classical_styles


def _fmt_money(value: Decimal | str | None) -> str:
    if value is None:
        return "—"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"${num:,.2f}"


def _fmt_pct(value: Decimal | str | None) -> str:
    if value is None:
        return "—"
    try:
        num = float(value) * 100
    except (TypeError, ValueError):
        return str(value)
    return f"{num:.3f}%"


def _inputs_table(result: AmortizationResult, styles: dict) -> Table:
    cfg = result.config
    rows = [
        ["Principal", _fmt_money(cfg.principal)],
        ["Annual Rate", _fmt_pct(cfg.annual_rate)],
        ["Term (periods)", str(cfg.term_periods)],
        ["Payment Frequency", cfg.frequency.title()],
        ["Method", cfg.method.value.replace("_", " ").title()],
        ["Start Date", cfg.start_date.isoformat() if cfg.start_date else "—"],
    ]
    if cfg.balloon_amount:
        rows.append(["Balloon Amount", _fmt_money(cfg.balloon_amount)])
    if cfg.extra_payments:
        rows.append(
            [
                "Extra Payments",
                ", ".join(f"P{e.period_number}: {_fmt_money(e.amount)}" for e in cfg.extra_payments[:10])
                + (f" (+{len(cfg.extra_payments) - 10} more)" if len(cfg.extra_payments) > 10 else ""),
            ]
        )
    if cfg.rate_changes:
        rows.append(
            [
                "Rate Changes",
                ", ".join(f"P{r.period_number}: {_fmt_pct(r.new_annual_rate)}" for r in cfg.rate_changes[:10]),
            ]
        )

    table = Table(rows, colWidths=[2.2 * inch, 6.0 * inch])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), ClassicalColors.OBSIDIAN_DEEP),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _summary_table(result: AmortizationResult) -> Table:
    first_payment = result.schedule[0].scheduled_payment if result.schedule else None
    rows = [
        ["Period Payment", "Total Interest", "Total Payments", "Payoff"],
        [
            _fmt_money(first_payment),
            _fmt_money(result.total_interest),
            _fmt_money(result.total_payments),
            result.payoff_date.isoformat() if result.payoff_date else f"{len(result.schedule)} periods",
        ],
    ]
    table = Table(rows, colWidths=[2.05 * inch] * 4)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_700),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OATMEAL),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, ClassicalColors.OBSIDIAN),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _annual_summary_table(result: AmortizationResult) -> Table:
    headers = ["Year", "Cal. Year", "Total Payments", "Total Interest", "Total Principal", "Ending Balance"]
    rows: list[list[str]] = [headers]
    for entry in result.annual_summary:
        rows.append(
            [
                str(entry.year_index),
                str(entry.calendar_year) if entry.calendar_year else "—",
                _fmt_money(entry.total_payments),
                _fmt_money(entry.total_interest),
                _fmt_money(entry.total_principal),
                _fmt_money(entry.ending_balance),
            ]
        )

    col_widths = [0.7 * inch, 0.9 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch]
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_700),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OATMEAL),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _schedule_table(result: AmortizationResult) -> Table:
    headers = [
        "Period",
        "Date",
        "Beg. Balance",
        "Payment",
        "Interest",
        "Principal",
        "Extra",
        "End. Balance",
    ]
    rows: list[list[str]] = [headers]
    for entry in result.schedule:
        rows.append(
            [
                str(entry.period_number),
                entry.payment_date.isoformat() if entry.payment_date else "—",
                _fmt_money(entry.beginning_balance),
                _fmt_money(entry.scheduled_payment),
                _fmt_money(entry.interest),
                _fmt_money(entry.principal),
                _fmt_money(entry.extra_principal) if entry.extra_principal else "—",
                _fmt_money(entry.ending_balance),
            ]
        )

    col_widths = [
        0.6 * inch,
        0.9 * inch,
        1.2 * inch,
        1.1 * inch,
        1.1 * inch,
        1.1 * inch,
        1.0 * inch,
        1.2 * inch,
    ]
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_700),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OATMEAL),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ClassicalColors.WHITE, ClassicalColors.OATMEAL_PAPER]),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return table


def build_amortization_pdf(result: AmortizationResult) -> bytes:
    """Render the amortization schedule PDF and return bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        title="Loan Amortization Schedule",
    )

    styles = create_classical_styles()
    story: list = []

    story.append(Paragraph("Loan Amortization Schedule", styles["SectionHeader"]))
    story.append(Paragraph(f"Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}", styles["BodyText"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Inputs", styles["SubsectionHeader"]))
    story.append(Spacer(1, 4))
    story.append(_inputs_table(result, styles))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Summary", styles["SubsectionHeader"]))
    story.append(Spacer(1, 4))
    story.append(_summary_table(result))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Annual Summary", styles["SubsectionHeader"]))
    story.append(Spacer(1, 4))
    story.append(_annual_summary_table(result))
    story.append(Spacer(1, 14))

    story.append(Paragraph(f"Period-by-Period Schedule ({len(result.schedule)} periods)", styles["SubsectionHeader"]))
    story.append(Spacer(1, 4))
    story.append(_schedule_table(result))

    doc.build(story)
    return buffer.getvalue()
