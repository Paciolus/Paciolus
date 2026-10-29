"""
Tax-figure status for the tools that apply built-in statutory figures (Sprint 856).

Sprint 793b (practitioner confirmation of the year-keyed statutory tables) is
still open. Until it closes, every tool that applies a built-in statutory figure
says so on screen and in its export: the export is what a CPA files.

Which tools this covers, verified per tool against the engines (Sprint 856):

* **W-2 / W-3 Reconciliation** (``w2_reconciliation_engine.STATUTORY_LIMITS_BY_YEAR``):
  one table, tax year 2025. Any other year is **refused** unless the caller
  supplies the figures through the ``statutory_limits`` override.
* **Form 1099 Preparation** (``form_1099_engine.THRESHOLDS_BY_TABLE_YEAR``):
  tables for 2025 (the pre-2026 $600 rules) and 2026 (the $2,000 OBBBA figures,
  taken from secondary sources; box 10 flagged ``needs_confirmation``). Years
  before 2025 use the 2025 table; 2027+ reuse the 2026 table with a notice.

Not covered, because they apply no year-indexed figure:

* **Book-to-Tax** — the tax rates are the user's inputs; the only built-in figure
  is the $10M Schedule M-3 total-assets test, which is not year-indexed.
  Standard-adjustment entries are labels; the amounts are entered by the user.
* **Depreciation** — MACRS percentages from IRS Publication 946 Table A-1 etc.,
  which do not vary by tax year. No bonus depreciation or §179 limit is applied.
* **Loan Amortization** — no statutory figure at all.

The banner text below is the single backend source. The frontend copy lives in
``frontend/src/content/tax-figures.ts``; ``tests/test_tax_figures_status.py``
fails if the two drift, if a banner stops matching its engine's tables, or if the
council's decision date passes without a recorded practitioner confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from fastapi import HTTPException

# Council decision, 2026-10-28 (Sprint 856 item 5): if no practitioner has
# confirmed the 2026 figures by this date, the tax tools are to be disabled
# rather than left running on unconfirmed figures behind a banner.
PRACTITIONER_CONFIRMATION_DEADLINE = date(2026, 12, 15)


@dataclass(frozen=True)
class PractitionerConfirmation:
    """A practitioner's sign-off of one tool's 2026 figures (Sprint 793b)."""

    confirmed_by: str
    confirmed_on: date
    tax_year: int


# One entry per covered tool. ``None`` = nobody has confirmed that tool's 2026
# figures yet. Record a confirmation only when a practitioner has actually
# checked the figures against the cited authorities.
PRACTITIONER_CONFIRMATIONS: dict[str, PractitionerConfirmation | None] = {
    "w2_reconciliation": None,
    "form_1099": None,
}

W2_TAX_FIGURES_BANNER = (
    "Statutory limits built in for tax year 2025 only, pending practitioner confirmation — "
    "other years are refused unless you supply the figures. Verify before relying."
)

FORM_1099_TAX_FIGURES_BANNER = (
    "Reporting thresholds built in through tax year 2026; the 2026 figures come from secondary "
    "sources and await practitioner confirmation, and later years reuse them with a notice. "
    "Verify before relying."
)

TAX_FIGURES_BANNERS: dict[str, str] = {
    "w2_reconciliation": W2_TAX_FIGURES_BANNER,
    "form_1099": FORM_1099_TAX_FIGURES_BANNER,
}


def tools_overdue_for_confirmation(today: date) -> list[str]:
    """Covered tools whose 2026 figures are unconfirmed after the deadline.

    Empty on or before the deadline, whatever the confirmation state.
    """
    if today <= PRACTITIONER_CONFIRMATION_DEADLINE:
        return []
    return sorted(tool for tool, confirmation in PRACTITIONER_CONFIRMATIONS.items() if confirmation is None)


def _today() -> date:
    """The current UTC date (a seam so tests can move the clock)."""
    return datetime.now(UTC).date()


def enforce_tax_figures_confirmed(tool_name: str) -> None:
    """Disable a covered tool once the council deadline passes unconfirmed.

    Called at the top of each covered tool's analysis and export routes, so the
    council decision (Sprint 856 item 5) takes effect in the running deployment
    on the day after the deadline — not only in the next CI run. Raises 403
    ``TAX_FIGURES_UNCONFIRMED``; a no-op on or before the deadline, for tools
    with a recorded confirmation, and for tools this module does not cover.
    """
    if tool_name not in tools_overdue_for_confirmation(_today()):
        return
    raise HTTPException(
        status_code=403,
        detail={
            "code": "TAX_FIGURES_UNCONFIRMED",
            "message": (
                "This tool is disabled: its built-in statutory figures were not confirmed by a "
                f"practitioner by {PRACTITIONER_CONFIRMATION_DEADLINE.isoformat()}."
            ),
            "resource": "tool_access",
        },
    )
