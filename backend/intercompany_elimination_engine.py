"""
Multi-Entity Intercompany Elimination Engine (Sprint 637).

Consumes multiple entity trial balances in a single call and produces a
consolidation worksheet: pre-elimination totals, elimination journal
entries needed to zero out reciprocal intercompany balances, and
post-elimination consolidated totals. Also emits a mismatch report for
intercompany pairs that don't reconcile — the signal for timing,
currency, or booking-error differences that need manual reconciliation
before consolidation can complete.

Zero-storage: form-input only. The engine does NOT assert elimination
is complete; it shows the gaps so the accountant can reconcile them.

Complementary to the existing single-TB ``detect_intercompany_imbalances``
in ``audit/rules/relationships.py``. That rule flags within-entity
intercompany balance weirdness; this engine handles the multi-entity
consolidation workflow.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

CENT = Decimal("0.01")
ZERO = Decimal("0")

# Tolerance for treating an intercompany pair as balanced after netting.
# Larger than a penny because timing differences routinely produce small
# net residuals at month-end cutoff.
DEFAULT_TOLERANCE = Decimal("1.00")


class IntercompanyDirection(str, Enum):
    RECEIVABLE = "receivable"  # Due from another entity
    PAYABLE = "payable"  # Due to another entity
    REVENUE = "revenue"  # Intercompany revenue / management fee
    EXPENSE = "expense"  # Intercompany cost reimbursement
    INVESTMENT = "investment"  # Parent's investment in subsidiary
    UNKNOWN = "unknown"


class MismatchKind(str, Enum):
    NO_RECIPROCAL = "no_reciprocal"  # Only one side booked
    AMOUNT_MISMATCH = "amount_mismatch"  # Both sides booked, amounts diverge
    DIRECTION_MISMATCH = "direction_mismatch"  # Same direction on both sides


class IntercompanyInputError(ValueError):
    """Raised for invalid intercompany inputs."""


# =============================================================================
# Inputs
# =============================================================================


@dataclass
class EntityAccount:
    account: str
    debit: Decimal = ZERO
    credit: Decimal = ZERO
    counterparty_entity: str | None = None  # Explicit, if known. Else parsed.

    def __post_init__(self) -> None:
        if isinstance(self.debit, (int, float)):
            self.debit = Decimal(str(self.debit))
        if isinstance(self.credit, (int, float)):
            self.credit = Decimal(str(self.credit))
        # Sprint 846 (I5): a negative debit is a credit and vice versa. The net
        # (debit - credit) is unchanged, but the worksheet sums each column
        # separately, so a negative amount left in place understated both totals.
        if self.debit < 0:
            self.credit -= self.debit
            self.debit = ZERO
        if self.credit < 0:
            self.debit -= self.credit
            self.credit = ZERO


@dataclass
class EntityTrialBalance:
    entity_id: str
    entity_name: str
    accounts: list[EntityAccount]


@dataclass
class IntercompanyConfig:
    entities: list[EntityTrialBalance]
    tolerance: Decimal = DEFAULT_TOLERANCE


# =============================================================================
# Outputs
# =============================================================================


@dataclass
class IntercompanyLine:
    """A single intercompany line item on one entity's books."""

    entity_id: str
    account: str
    direction: IntercompanyDirection
    counterparty_entity: str | None
    net_balance: Decimal  # Debit-positive
    debit: Decimal
    credit: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "account": self.account,
            "direction": self.direction.value,
            "counterparty_entity": self.counterparty_entity,
            "net_balance": str(self.net_balance),
            "debit": str(self.debit),
            "credit": str(self.credit),
        }


@dataclass
class EliminationPair:
    """A matched pair of intercompany lines that reconcile under tolerance."""

    entity_a: str
    entity_b: str
    account_a: str
    account_b: str
    direction_a: str
    direction_b: str
    amount_a: Decimal
    amount_b: Decimal
    net_residual: Decimal  # A's receivable - B's payable (Decimal-precise)
    reconciles: bool
    # Whether A carries a debit balance. Used to orient the elimination when
    # neither account name states a direction (not serialised).
    a_has_debit_balance: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_a": self.entity_a,
            "entity_b": self.entity_b,
            "account_a": self.account_a,
            "account_b": self.account_b,
            "direction_a": self.direction_a,
            "direction_b": self.direction_b,
            "amount_a": str(self.amount_a),
            "amount_b": str(self.amount_b),
            "net_residual": str(self.net_residual),
            "reconciles": self.reconciles,
        }


@dataclass
class Mismatch:
    kind: MismatchKind
    entity: str
    counterparty: str | None
    account: str
    direction: str
    amount: Decimal
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "entity": self.entity,
            "counterparty": self.counterparty,
            "account": self.account,
            "direction": self.direction,
            "amount": str(self.amount),
            "message": self.message,
        }


@dataclass
class EliminationJE:
    """A proposed elimination journal entry applied to the consolidation."""

    description: str
    debit_entity: str
    debit_account: str
    credit_entity: str
    credit_account: str
    amount: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "debit_entity": self.debit_entity,
            "debit_account": self.debit_account,
            "credit_entity": self.credit_entity,
            "credit_account": self.credit_account,
            "amount": str(self.amount),
        }


@dataclass
class ConsolidationColumn:
    entity_id: str
    entity_name: str
    debit_total: Decimal
    credit_total: Decimal
    intercompany_gross: Decimal  # Abs-sum of IC balances on this entity

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "debit_total": str(self.debit_total),
            "credit_total": str(self.credit_total),
            "intercompany_gross": str(self.intercompany_gross),
        }


@dataclass
class ConsolidationWorksheet:
    columns: list[ConsolidationColumn]
    total_entity_debits: Decimal
    total_entity_credits: Decimal
    elimination_debits: Decimal
    elimination_credits: Decimal
    consolidated_debits: Decimal
    consolidated_credits: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "columns": [c.to_dict() for c in self.columns],
            "total_entity_debits": str(self.total_entity_debits),
            "total_entity_credits": str(self.total_entity_credits),
            "elimination_debits": str(self.elimination_debits),
            "elimination_credits": str(self.elimination_credits),
            "consolidated_debits": str(self.consolidated_debits),
            "consolidated_credits": str(self.consolidated_credits),
        }


@dataclass
class IntercompanyEliminationResult:
    intercompany_lines: list[IntercompanyLine]
    pairs: list[EliminationPair]
    mismatches: list[Mismatch]
    elimination_journal_entries: list[EliminationJE]
    worksheet: ConsolidationWorksheet
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "intercompany_lines": [line.to_dict() for line in self.intercompany_lines],
            "pairs": [p.to_dict() for p in self.pairs],
            "mismatches": [m.to_dict() for m in self.mismatches],
            "elimination_journal_entries": [je.to_dict() for je in self.elimination_journal_entries],
            "worksheet": self.worksheet.to_dict(),
            "summary": self.summary,
        }


# =============================================================================
# Account parsing
# =============================================================================


_DUE_FROM_PATTERNS = (
    "due from",
    "intercompany receivable",
    "ic receivable",
    "ic ar",
    "receivable from",
)
_DUE_TO_PATTERNS = (
    "due to",
    "intercompany payable",
    "ic payable",
    "ic ap",
    "payable to",
)
_IC_REVENUE_PATTERNS = (
    "intercompany revenue",
    "intercompany sales",
    "management fee revenue",
    "ic revenue",
    "ic mgmt fee",
)
_IC_EXPENSE_PATTERNS = (
    "intercompany expense",
    "intercompany cost",
    "management fee expense",
    "ic expense",
)
_INVESTMENT_PATTERNS = (
    "investment in subsidiary",
    "investment in affiliate",
    "equity investment",
)


def _phrase_pattern(phrases: tuple[str, ...]) -> re.Pattern[str]:
    # Sprint 827 (I4): whole words only. Substring matching read "Electric
    # expense" as "ic expense", "Clinic revenue" as "ic revenue" and "Basic
    # apparel" as "ic ap".
    return re.compile(r"\b(?:" + "|".join(re.escape(p) for p in phrases) + r")\b")


_DIRECTION_PATTERNS: tuple[tuple[re.Pattern[str], IntercompanyDirection], ...] = (
    (_phrase_pattern(_DUE_FROM_PATTERNS), IntercompanyDirection.RECEIVABLE),
    (_phrase_pattern(_DUE_TO_PATTERNS), IntercompanyDirection.PAYABLE),
    (_phrase_pattern(_IC_REVENUE_PATTERNS), IntercompanyDirection.REVENUE),
    (_phrase_pattern(_IC_EXPENSE_PATTERNS), IntercompanyDirection.EXPENSE),
    (_phrase_pattern(_INVESTMENT_PATTERNS), IntercompanyDirection.INVESTMENT),
)

# Phrases that say "intercompany" on their own. The generic ones — "due to",
# "receivable from", "payable to" — describe officers, banks and tax
# authorities just as often, so they count only when the counterparty they
# name is an entity in this consolidation (see ``_extract_lines``).
_STRONG_IC = re.compile(
    r"\b(?:intercompany|inter-company|ic|management fee|investment in subsidiary|investment in affiliate)\b"
)


def _parse_direction(account: str) -> IntercompanyDirection:
    lower = account.lower()
    for pattern, direction in _DIRECTION_PATTERNS:
        if pattern.search(lower):
            return direction
    return IntercompanyDirection.UNKNOWN


_COUNTERPARTY_SUFFIX = re.compile(
    # \b: without it "in" matched inside "Dublin", so "Intercompany receivable -
    # Dublin Ltd" named its counterparty "Ltd" (Sprint 827, I4).
    r"\b(?:from|to|with|in)\s+([A-Za-z0-9&._\- ]+?)\s*$",
    re.IGNORECASE,
)


def _parse_counterparty(account: str) -> str | None:
    """Best-effort extraction of the counterparty entity name from the account.

    Picks up forms like "Due from Acme Corp" or "Intercompany AR — Subsidiary
    Beta". Returns None when the account name does not carry a counterparty.
    """
    match = _COUNTERPARTY_SUFFIX.search(account)
    if match:
        candidate = match.group(1).strip(" -–—:")
        # Strip a trailing punctuation run and anything that's clearly not a
        # counterparty (e.g. "from customers" – a generic noun).
        low = candidate.lower()
        if low in {"customer", "customers", "vendor", "vendors", "employees"}:
            return None
        return candidate
    # Dash-separated counterparty: "Intercompany - Subsidiary Beta", "IC AR - Beta",
    # "Management fee revenue - Sub A".
    for sep in (" - ", " — ", " – "):
        if sep in account:
            parts = account.split(sep)
            head = parts[0].lower()
            if len(parts) >= 2 and (_STRONG_IC.search(head) or _parse_direction(head) != IntercompanyDirection.UNKNOWN):
                return parts[-1].strip()
    return None


def _is_intercompany(account: str) -> bool:
    return _parse_direction(account) != IntercompanyDirection.UNKNOWN or bool(_STRONG_IC.search(account.lower()))


def _is_strongly_intercompany(account: str) -> bool:
    return bool(_STRONG_IC.search(account.lower()))


# =============================================================================
# Pair matching
# =============================================================================


RECIPROCAL_DIRECTIONS: dict[IntercompanyDirection, IntercompanyDirection] = {
    IntercompanyDirection.RECEIVABLE: IntercompanyDirection.PAYABLE,
    IntercompanyDirection.PAYABLE: IntercompanyDirection.RECEIVABLE,
    IntercompanyDirection.REVENUE: IntercompanyDirection.EXPENSE,
    IntercompanyDirection.EXPENSE: IntercompanyDirection.REVENUE,
}


def _extract_lines(config: IntercompanyConfig) -> list[IntercompanyLine]:
    lines: list[IntercompanyLine] = []
    known_entities = {e.entity_id.lower() for e in config.entities} | {e.entity_name.lower() for e in config.entities}
    for entity in config.entities:
        for account in entity.accounts:
            # Sprint 827 (I3): an explicit counterparty is the strongest signal
            # there is. Requiring an IC keyword in the account name as well
            # dropped "Loan receivable - related party" with counterparty S, and
            # the consolidation then reported itself complete.
            if not account.counterparty_entity and not _is_intercompany(account.account):
                continue
            direction = _parse_direction(account.account)
            counterparty = account.counterparty_entity or _parse_counterparty(account.account)
            # Sprint 827 (I4): a generic phrase ("Due to officers", "Interest
            # receivable from bank") is intercompany only if it names an entity
            # in this consolidation; otherwise it is an ordinary balance, not a
            # one-sided intercompany line blocking completion.
            if (
                not account.counterparty_entity
                and not _is_strongly_intercompany(account.account)
                and (counterparty is None or counterparty.lower() not in known_entities)
            ):
                continue
            net = account.debit - account.credit
            lines.append(
                IntercompanyLine(
                    entity_id=entity.entity_id,
                    account=account.account,
                    direction=direction,
                    counterparty_entity=counterparty,
                    net_balance=_quantise(net),
                    debit=_quantise(account.debit),
                    credit=_quantise(account.credit),
                )
            )
    return lines


def _match_pairs(
    lines: list[IntercompanyLine],
    entities_by_id: dict[str, EntityTrialBalance],
    tolerance: Decimal,
) -> tuple[list[EliminationPair], list[Mismatch]]:
    # Group lines by (entity_id, counterparty_entity). Normalise
    # counterparty lookup by both name and id.
    entity_name_to_id: dict[str, str] = {e.entity_name.lower(): e.entity_id for e in entities_by_id.values()}
    for e in entities_by_id.values():
        entity_name_to_id[e.entity_id.lower()] = e.entity_id

    # Organise by (entity_id, counterparty_entity_id) -> list of lines.
    grouped: dict[tuple[str, str], list[IntercompanyLine]] = defaultdict(list)
    unresolved_counterparty: list[IntercompanyLine] = []

    for line in lines:
        if not line.counterparty_entity:
            unresolved_counterparty.append(line)
            continue
        counterparty_id = entity_name_to_id.get(line.counterparty_entity.lower())
        if counterparty_id is None:
            unresolved_counterparty.append(line)
            continue
        grouped[(line.entity_id, counterparty_id)].append(line)

    pairs: list[EliminationPair] = []
    mismatches: list[Mismatch] = []

    def _record_pair(a: IntercompanyLine, b: IntercompanyLine) -> None:
        # Net residual: A's receivable (positive net) should equal B's payable
        # (negative net). So A.net + B.net should ~= 0.
        residual = a.net_balance + b.net_balance
        reconciles = abs(residual) <= tolerance
        pairs.append(
            EliminationPair(
                entity_a=a.entity_id,
                entity_b=b.entity_id,
                account_a=a.account,
                account_b=b.account,
                direction_a=a.direction.value,
                direction_b=b.direction.value,
                amount_a=abs(a.net_balance),
                amount_b=abs(b.net_balance),
                net_residual=_quantise(residual),
                reconciles=reconciles,
                a_has_debit_balance=a.net_balance >= 0,
            )
        )
        if not reconciles:
            mismatches.append(
                Mismatch(
                    kind=MismatchKind.AMOUNT_MISMATCH,
                    entity=a.entity_id,
                    counterparty=b.entity_id,
                    account=a.account,
                    direction=a.direction.value,
                    amount=_quantise(residual),
                    message=(
                        f"Intercompany residual of ${residual:,.2f} between "
                        f"{a.entity_id}.{a.account} and "
                        f"{b.entity_id}.{b.account} exceeds the "
                        f"${tolerance:,.2f} tolerance."
                    ),
                )
            )

    def _no_reciprocal(line: IntercompanyLine) -> None:
        mismatches.append(
            Mismatch(
                kind=MismatchKind.NO_RECIPROCAL,
                entity=line.entity_id,
                counterparty=line.counterparty_entity,
                account=line.account,
                direction=line.direction.value,
                amount=line.net_balance,
                message=(
                    f"{line.entity_id} booked {line.direction.value} "
                    f"of ${abs(line.net_balance):,.2f} against "
                    f"{line.counterparty_entity} but no reciprocal "
                    "entry was found."
                ),
            )
        )

    def _compatible(a: IntercompanyLine, b: IntercompanyLine) -> bool:
        expected = RECIPROCAL_DIRECTIONS.get(a.direction)
        if expected is not None:
            return b.direction == expected
        # UNKNOWN on side A: accept anything not itself claimed by a known
        # reciprocal of a different kind.
        return RECIPROCAL_DIRECTIONS.get(b.direction) in (None, a.direction)

    # Sprint 827 (I2): match one-to-one. The previous loop paired every A line
    # with every compatible B line, so two $500 balances on each side became
    # four pairs and $2,000 of eliminations against $1,000 of balances, while
    # reporting the consolidation complete. Each entity pair is processed once
    # (in canonical order), amount-reconciling matches are taken first, and no
    # line is used twice.
    processed: set[tuple[str, str]] = set()
    for (entity_a, entity_b), a_lines in grouped.items():
        canonical = (min(entity_a, entity_b), max(entity_a, entity_b))
        if canonical in processed:
            continue
        processed.add(canonical)
        b_lines = grouped.get((entity_b, entity_a), [])
        if not b_lines:
            for line in a_lines:
                _no_reciprocal(line)
            continue

        unused_b = list(b_lines)
        leftover_a: list[IntercompanyLine] = []
        # Pass 1: compatible direction and amounts that reconcile.
        for a_line in a_lines:
            match = next(
                (
                    b_line
                    for b_line in unused_b
                    if _compatible(a_line, b_line) and abs(a_line.net_balance + b_line.net_balance) <= tolerance
                ),
                None,
            )
            if match is None:
                leftover_a.append(a_line)
                continue
            unused_b.remove(match)
            _record_pair(a_line, match)

        # Pass 2: compatible direction, amounts differ — a real mismatch.
        still_left: list[IntercompanyLine] = []
        for a_line in leftover_a:
            match = next((b_line for b_line in unused_b if _compatible(a_line, b_line)), None)
            if match is None:
                still_left.append(a_line)
                continue
            unused_b.remove(match)
            _record_pair(a_line, match)

        # Pass 3: anything left has no compatible counterpart.
        for a_line in still_left:
            if unused_b:
                b_line = unused_b[0]
                mismatches.append(
                    Mismatch(
                        kind=MismatchKind.DIRECTION_MISMATCH,
                        entity=a_line.entity_id,
                        counterparty=a_line.counterparty_entity,
                        account=a_line.account,
                        direction=a_line.direction.value,
                        amount=a_line.net_balance,
                        message=(
                            f"{a_line.entity_id}.{a_line.account} is "
                            f"{a_line.direction.value} but {b_line.entity_id}."
                            f"{b_line.account} is {b_line.direction.value} — "
                            "expected reciprocal direction."
                        ),
                    )
                )
            else:
                _no_reciprocal(a_line)
        for b_line in unused_b:
            _no_reciprocal(b_line)

    # Unresolved counterparty — counterparty name didn't match any entity.
    for line in unresolved_counterparty:
        mismatches.append(
            Mismatch(
                kind=MismatchKind.NO_RECIPROCAL,
                entity=line.entity_id,
                counterparty=line.counterparty_entity,
                account=line.account,
                direction=line.direction.value,
                amount=line.net_balance,
                message=(
                    f"{line.entity_id} booked {line.direction.value} "
                    f"of ${abs(line.net_balance):,.2f} but the counterparty "
                    f"({line.counterparty_entity or 'unspecified'}) was not "
                    "found among the entities in this consolidation."
                ),
            )
        )

    return pairs, mismatches


# =============================================================================
# Helpers
# =============================================================================


def _quantise(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _consolidation_worksheet(
    entities: list[EntityTrialBalance],
    lines: list[IntercompanyLine],
    pairs: list[EliminationPair],
) -> ConsolidationWorksheet:
    # Per-entity columns
    columns: list[ConsolidationColumn] = []
    for entity in entities:
        debit_sum = sum((a.debit for a in entity.accounts), ZERO)
        credit_sum = sum((a.credit for a in entity.accounts), ZERO)
        ic_gross = sum(
            (abs(line.net_balance) for line in lines if line.entity_id == entity.entity_id),
            ZERO,
        )
        columns.append(
            ConsolidationColumn(
                entity_id=entity.entity_id,
                entity_name=entity.entity_name,
                debit_total=_quantise(debit_sum),
                credit_total=_quantise(credit_sum),
                intercompany_gross=_quantise(ic_gross),
            )
        )

    total_debits = sum((c.debit_total for c in columns), ZERO)
    total_credits = sum((c.credit_total for c in columns), ZERO)

    # Elimination total = sum of matched-pair amounts on the receivable side.
    elim_amount = ZERO
    for pair in pairs:
        if pair.reconciles:
            elim_amount += min(pair.amount_a, pair.amount_b)
    elim_amount = _quantise(elim_amount)

    consolidated_debits = _quantise(total_debits - elim_amount)
    consolidated_credits = _quantise(total_credits - elim_amount)

    return ConsolidationWorksheet(
        columns=columns,
        total_entity_debits=_quantise(total_debits),
        total_entity_credits=_quantise(total_credits),
        elimination_debits=elim_amount,
        elimination_credits=elim_amount,
        consolidated_debits=consolidated_debits,
        consolidated_credits=consolidated_credits,
    )


_DEBIT_NATURAL = frozenset({"receivable", "expense", "investment"})
_CREDIT_NATURAL = frozenset({"payable", "revenue"})


def _elimination_journal_entries(pairs: list[EliminationPair]) -> list[EliminationJE]:
    """Produce one elimination JE per reconciling pair."""
    jes: list[EliminationJE] = []
    for pair in pairs:
        if not pair.reconciles:
            continue
        amount = min(pair.amount_a, pair.amount_b)
        # An elimination reverses each side's natural balance: it credits the
        # side that carries a debit balance (receivable, expense, investment)
        # and debits the side that carries a credit balance (payable, revenue).
        # Sprint 827 (I1): revenue was grouped with receivable, so the
        # revenue/expense entry came out Dr expense / Cr revenue — booking it
        # would have doubled both sides instead of removing them.
        if pair.direction_a in _DEBIT_NATURAL or pair.direction_b in _CREDIT_NATURAL:
            credit_a = True
        elif pair.direction_a in _CREDIT_NATURAL or pair.direction_b in _DEBIT_NATURAL:
            credit_a = False
        else:
            # Neither name states a direction — lines admitted on an explicit
            # counterparty alone (Sprint 827, I3). Orient by balance: credit
            # whichever side carries the debit. Entity order put Dr receivable /
            # Cr payable here, doubling both (PR #206 review).
            credit_a = pair.a_has_debit_balance
        if credit_a:
            debit_entity = pair.entity_b
            debit_account = pair.account_b
            credit_entity = pair.entity_a
            credit_account = pair.account_a
        else:
            debit_entity = pair.entity_a
            debit_account = pair.account_a
            credit_entity = pair.entity_b
            credit_account = pair.account_b
        jes.append(
            EliminationJE(
                description=(
                    f"Eliminate intercompany {pair.direction_a} / {pair.direction_b} "
                    f"between {pair.entity_a} and {pair.entity_b}"
                ),
                debit_entity=debit_entity,
                debit_account=debit_account,
                credit_entity=credit_entity,
                credit_account=credit_account,
                amount=_quantise(amount),
            )
        )
    return jes


# =============================================================================
# Public entry point
# =============================================================================


def run_intercompany_elimination(config: IntercompanyConfig) -> IntercompanyEliminationResult:
    if len(config.entities) < 2:
        raise IntercompanyInputError(
            f"At least two entities are required for multi-entity consolidation (got {len(config.entities)})."
        )

    entity_ids = [e.entity_id for e in config.entities]
    if len(entity_ids) != len(set(entity_ids)):
        raise IntercompanyInputError("Entity IDs must be unique across the consolidation.")

    entities_by_id = {e.entity_id: e for e in config.entities}
    lines = _extract_lines(config)
    pairs, mismatches = _match_pairs(lines, entities_by_id, config.tolerance)
    jes = _elimination_journal_entries(pairs)
    worksheet = _consolidation_worksheet(config.entities, lines, pairs)

    reconciling_pairs = sum(1 for p in pairs if p.reconciles)
    summary = {
        "entity_count": len(config.entities),
        "intercompany_line_count": len(lines),
        "matched_pair_count": len(pairs),
        "reconciling_pair_count": reconciling_pairs,
        "mismatch_count": len(mismatches),
        "elimination_je_count": len(jes),
        "consolidation_complete": len(mismatches) == 0,
    }

    return IntercompanyEliminationResult(
        intercompany_lines=lines,
        pairs=pairs,
        mismatches=mismatches,
        elimination_journal_entries=jes,
        worksheet=worksheet,
        summary=summary,
    )
