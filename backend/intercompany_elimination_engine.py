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


def _parse_direction(account: str) -> IntercompanyDirection:
    lower = account.lower()
    if any(p in lower for p in _DUE_FROM_PATTERNS):
        return IntercompanyDirection.RECEIVABLE
    if any(p in lower for p in _DUE_TO_PATTERNS):
        return IntercompanyDirection.PAYABLE
    if any(p in lower for p in _IC_REVENUE_PATTERNS):
        return IntercompanyDirection.REVENUE
    if any(p in lower for p in _IC_EXPENSE_PATTERNS):
        return IntercompanyDirection.EXPENSE
    if any(p in lower for p in _INVESTMENT_PATTERNS):
        return IntercompanyDirection.INVESTMENT
    # Still recognised as IC but unknown direction.
    if "intercompany" in lower or " ic " in f" {lower} " or " ic-" in lower:
        return IntercompanyDirection.UNKNOWN
    return IntercompanyDirection.UNKNOWN


_COUNTERPARTY_SUFFIX = re.compile(
    r"(?:from|to|with|in)\s+([A-Za-z0-9&._\- ]+?)\s*$",
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
    # Dash-separated counterparty: "Intercompany - Subsidiary Beta"
    for sep in (" - ", " — ", " – "):
        if sep in account:
            parts = account.split(sep)
            if len(parts) >= 2 and any(ic in parts[0].lower() for ic in ("intercompany", " ic ", "ic-")):
                return parts[-1].strip()
    return None


def _is_intercompany(account: str) -> bool:
    return _parse_direction(account) != IntercompanyDirection.UNKNOWN or "intercompany" in account.lower()


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
    for entity in config.entities:
        for account in entity.accounts:
            if not _is_intercompany(account.account):
                continue
            direction = _parse_direction(account.account)
            counterparty = account.counterparty_entity or _parse_counterparty(account.account)
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
    seen: set[tuple[str, str, str, str]] = set()

    for (entity_a, entity_b), a_lines in grouped.items():
        b_lines = grouped.get((entity_b, entity_a), [])
        if not b_lines:
            # No reciprocal side booked.
            for line in a_lines:
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
            continue

        # Match by reciprocal direction where possible.
        for a in a_lines:
            expected_b_direction = RECIPROCAL_DIRECTIONS.get(a.direction)
            matches = [b for b in b_lines if b.direction == expected_b_direction]
            if not matches and expected_b_direction is None:
                matches = b_lines  # UNKNOWN direction — match any
            if not matches:
                for b in b_lines:
                    pair_key = tuple(sorted([entity_a, entity_b]) + [a.account, b.account])
                    key = (pair_key[0], pair_key[1], pair_key[2], pair_key[3])
                    if key in seen:
                        continue
                    seen.add(key)
                    mismatches.append(
                        Mismatch(
                            kind=MismatchKind.DIRECTION_MISMATCH,
                            entity=a.entity_id,
                            counterparty=a.counterparty_entity,
                            account=a.account,
                            direction=a.direction.value,
                            amount=a.net_balance,
                            message=(
                                f"{a.entity_id}.{a.account} is "
                                f"{a.direction.value} but {b.entity_id}."
                                f"{b.account} is {b.direction.value} — "
                                "expected reciprocal direction."
                            ),
                        )
                    )
                continue

            for b in matches:
                # Sort the entity+account pairs together so we collapse
                # (A, B, acctA, acctB) and (B, A, acctB, acctA) to the
                # same key — otherwise both directions of the group
                # iteration create duplicate pairs.
                key_pair = tuple(
                    sorted(
                        [
                            (a.entity_id, a.account),
                            (b.entity_id, b.account),
                        ]
                    )
                )
                key = (key_pair[0][0], key_pair[0][1], key_pair[1][0], key_pair[1][1])
                if key in seen:
                    continue
                seen.add(key)
                # Net residual: A's receivable (positive net) should equal
                # B's payable (negative net). So A.net + B.net should ~= 0.
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


def _elimination_journal_entries(pairs: list[EliminationPair]) -> list[EliminationJE]:
    """Produce one elimination JE per reconciling pair."""
    jes: list[EliminationJE] = []
    for pair in pairs:
        if not pair.reconciles:
            continue
        amount = min(pair.amount_a, pair.amount_b)
        # The receivable side is debit; the payable side is credit.
        # Determine which is which from the directions.
        if pair.direction_a in ("receivable", "revenue"):
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
