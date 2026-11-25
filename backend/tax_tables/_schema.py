"""Shapes of a tax-year table — Sprint 860.

Plain data only: the engines (``w2_reconciliation_engine``, ``form_1099_engine``)
import these tables and build their own types from them, so nothing here imports
an engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Figure:
    """One statutory figure and where it was read.

    ``citation`` names the authority (statute section, notice, revenue
    procedure, form instructions). ``source_url`` is the page it was read from.
    ``excerpt`` is the sentence that states the figure, quoted, so a reviewer
    can check the value against the source without opening it.
    """

    value: Decimal
    citation: str
    source_url: str
    excerpt: str = ""


@dataclass(frozen=True)
class SignOff:
    """A practitioner's sign-off of one tool's figures for one tax year.

    A table counts as signed off only when all three are set: who, when, and
    that every source it was read from is a final (not draft) document.
    Record a sign-off only when the person has checked each figure against its
    source.
    """

    signed_off_by: str | None = None
    signed_off_on: date | None = None
    sources_final: bool = False

    @property
    def is_signed(self) -> bool:
        return bool(self.signed_off_by and self.signed_off_by.strip()) and (
            self.signed_off_on is not None and self.sources_final
        )


@dataclass(frozen=True)
class W2Figures:
    """Federal payroll figures the W-2 / W-3 reconciliation applies."""

    ss_wage_base: Figure
    ss_rate: Figure
    medicare_rate: Figure
    additional_medicare_rate: Figure
    additional_medicare_threshold: Figure
    hsa_self_only: Figure
    hsa_family: Figure
    limit_401k_elective: Figure
    limit_401k_catchup_50: Figure
    limit_401k_catchup_60_63: Figure
    limit_simple_ira: Figure
    # Summary text the engine prints as the statutory set's provenance.
    source: str
    verified_by: str
    # Optional catch-ups (Sprint 826): a year may leave them out.
    hsa_catchup_55: Figure | None = None
    limit_simple_catchup_50: Figure | None = None
    limit_simple_catchup_60_63: Figure | None = None
    catchup_source: str | None = None

    def figures(self) -> dict[str, Figure]:
        """Every figure this year holds, by field name."""
        return {f.name: getattr(self, f.name) for f in fields(self) if isinstance(getattr(self, f.name), Figure)}


@dataclass(frozen=True)
class ThresholdFigure:
    """One information-return reporting threshold."""

    form: str  # "1099-NEC" | "1099-MISC" | "1099-INT"
    box: int
    description: str
    amount: Figure
    needs_confirmation: bool = False

    @property
    def key(self) -> str:
        return f"{self.form} box {self.box}"


@dataclass(frozen=True)
class TaxYearTable:
    """Everything Paciolus applies for one tax year, with its sign-offs.

    ``sign_offs`` is keyed by tool (``w2_reconciliation``, ``form_1099``).
    ``acknowledged_large_moves`` names figures that moved more than 10% from the
    prior year, with the reason, so the year-over-year test passes only for a
    move a person has looked at.
    """

    tax_year: int
    w2: W2Figures | None
    form_1099: tuple[ThresholdFigure, ...] | None
    sign_offs: dict[str, SignOff] = field(default_factory=dict)
    acknowledged_large_moves: dict[str, str] = field(default_factory=dict)

    def sign_off(self, tool: str) -> SignOff:
        return self.sign_offs.get(tool, SignOff())
