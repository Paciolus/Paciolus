"""
Adjusting Entry Module - Sprint 52

Provides functionality for creating, validating, and applying adjusting journal entries
to trial balance data. Supports proposed adjustments workflow for audit adjustments.

Features:
- AdjustingEntry dataclass for individual journal entries
- AdjustmentSet for grouped entries with debit=credit validation
- AdjustedTrialBalance for before/after comparison
- Zero-Storage compliant: Adjustments are session-only

GAAP/IFRS Compliance:
- Both frameworks require adjusting entries to balance (debits = credits)
- Supports reversing entries for period-end adjustments
- Tracks adjustment types (accrual, deferral, estimate, error correction)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Optional
from uuid import uuid4


class AdjustmentType(str, Enum):
    """Classification of adjusting entry types per GAAP/IFRS."""
    ACCRUAL = "accrual"  # Revenue/expense earned but not recorded
    DEFERRAL = "deferral"  # Revenue/expense recorded but not earned
    ESTIMATE = "estimate"  # Depreciation, bad debt, etc.
    ERROR_CORRECTION = "error_correction"  # Prior period error fix
    RECLASSIFICATION = "reclassification"  # Move between accounts
    OTHER = "other"  # Miscellaneous adjustments


class AdjustmentStatus(str, Enum):
    """Status of an adjusting entry."""
    PROPOSED = "proposed"  # Suggested, pending review
    APPROVED = "approved"  # Approved by client/management
    REJECTED = "rejected"  # Rejected, will not be posted
    POSTED = "posted"  # Applied to the trial balance


# Valid forward transitions — posted is terminal
VALID_TRANSITIONS: dict[AdjustmentStatus, set[AdjustmentStatus]] = {
    AdjustmentStatus.PROPOSED: {AdjustmentStatus.APPROVED, AdjustmentStatus.REJECTED},
    AdjustmentStatus.APPROVED: {AdjustmentStatus.POSTED, AdjustmentStatus.REJECTED},
    AdjustmentStatus.REJECTED: {AdjustmentStatus.PROPOSED},
    AdjustmentStatus.POSTED: set(),
}


class InvalidTransitionError(ValueError):
    """Raised when a status transition violates the approval workflow."""


def validate_status_transition(
    current: AdjustmentStatus, target: AdjustmentStatus,
) -> None:
    """Validate that a status transition is allowed.

    Raises InvalidTransitionError if the transition violates the workflow.
    """
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        if not allowed:
            raise InvalidTransitionError(
                f"Cannot transition from '{current.value}': status is terminal"
            )
        allowed_names = ", ".join(sorted(s.value for s in allowed))
        raise InvalidTransitionError(
            f"Cannot transition from '{current.value}' to '{target.value}'. "
            f"Allowed transitions: {allowed_names}"
        )


@dataclass
class AdjustmentLine:
    """
    Individual line item in an adjusting journal entry.

    Each line represents either a debit or credit to a specific account.
    The account_name should match trial balance accounts for proper application.
    """
    account_name: str
    debit: Decimal = Decimal("0.00")
    credit: Decimal = Decimal("0.00")
    description: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize amounts."""
        # Convert to Decimal if needed
        if not isinstance(self.debit, Decimal):
            self.debit = Decimal(str(self.debit))
        if not isinstance(self.credit, Decimal):
            self.credit = Decimal(str(self.credit))

        # Round to 2 decimal places
        self.debit = self.debit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.credit = self.credit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Validate: can't have both debit and credit on same line
        if self.debit > 0 and self.credit > 0:
            raise ValueError(
                f"Account '{self.account_name}' cannot have both debit and credit. "
                "Use separate lines for each."
            )

        # Validate: must have either debit or credit
        if self.debit == 0 and self.credit == 0:
            raise ValueError(
                f"Account '{self.account_name}' must have either a debit or credit amount."
            )

    @property
    def net_amount(self) -> Decimal:
        """Net amount: positive for debit, negative for credit."""
        return self.debit - self.credit

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "account_name": self.account_name,
            "debit": float(self.debit),
            "credit": float(self.credit),
            "description": self.description,
        }


@dataclass
class AdjustingEntry:
    """
    Complete adjusting journal entry with multiple line items.

    An adjusting entry must balance (total debits = total credits).
    Entries are proposed by the auditor and may be approved or rejected.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    reference: str = ""  # AJE-001, PBC-001, etc.
    description: str = ""
    adjustment_type: AdjustmentType = AdjustmentType.OTHER
    status: AdjustmentStatus = AdjustmentStatus.PROPOSED
    lines: list[AdjustmentLine] = field(default_factory=list)
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    notes: Optional[str] = None
    is_reversing: bool = False  # Auto-reverse in next period

    def __post_init__(self):
        """Validate entry on creation."""
        if self.lines:
            self._validate_balance()

    def _validate_balance(self) -> None:
        """Ensure debits equal credits."""
        if not self.is_balanced:
            diff = abs(self.total_debits - self.total_credits)
            raise ValueError(
                f"Entry '{self.reference}' is out of balance by ${diff:.2f}. "
                f"Total debits: ${self.total_debits:.2f}, "
                f"Total credits: ${self.total_credits:.2f}"
            )

    @property
    def total_debits(self) -> Decimal:
        """Sum of all debit amounts."""
        return sum((line.debit for line in self.lines), Decimal("0.00"))

    @property
    def total_credits(self) -> Decimal:
        """Sum of all credit amounts."""
        return sum((line.credit for line in self.lines), Decimal("0.00"))

    @property
    def is_balanced(self) -> bool:
        """Check if debits equal credits."""
        return self.total_debits == self.total_credits

    @property
    def entry_total(self) -> Decimal:
        """Total amount of the entry (debits or credits, since balanced)."""
        return self.total_debits

    @property
    def account_count(self) -> int:
        """Number of accounts affected."""
        return len(self.lines)

    def add_line(self, line: AdjustmentLine) -> None:
        """Add a line item to the entry."""
        self.lines.append(line)
        self.updated_at = datetime.now(timezone.utc)

    def remove_line(self, account_name: str) -> bool:
        """Remove all lines for a specific account. Returns True if any removed."""
        original_count = len(self.lines)
        self.lines = [l for l in self.lines if l.account_name != account_name]
        if len(self.lines) != original_count:
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def validate(self) -> list[str]:
        """
        Validate the entry and return list of validation errors.
        Returns empty list if valid.
        """
        errors = []

        if not self.reference:
            errors.append("Reference number is required")

        if not self.description:
            errors.append("Description is required")

        if len(self.lines) < 2:
            errors.append("Entry must have at least 2 lines")

        if not self.is_balanced:
            diff = abs(self.total_debits - self.total_credits)
            errors.append(f"Entry is out of balance by ${diff:.2f}")

        # Check for duplicate accounts (allowed but warn)
        accounts = [l.account_name.lower() for l in self.lines]
        if len(accounts) != len(set(accounts)):
            errors.append("Warning: Duplicate accounts detected (may be intentional)")

        return errors

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "reference": self.reference,
            "description": self.description,
            "adjustment_type": self.adjustment_type.value,
            "status": self.status.value,
            "lines": [line.to_dict() for line in self.lines],
            "total_debits": float(self.total_debits),
            "total_credits": float(self.total_credits),
            "is_balanced": self.is_balanced,
            "entry_total": float(self.entry_total),
            "account_count": self.account_count,
            "prepared_by": self.prepared_by,
            "reviewed_by": self.reviewed_by,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
            "is_reversing": self.is_reversing,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AdjustingEntry":
        """Create an AdjustingEntry from dictionary data."""
        lines = [
            AdjustmentLine(
                account_name=l["account_name"],
                debit=Decimal(str(l.get("debit", 0))),
                credit=Decimal(str(l.get("credit", 0))),
                description=l.get("description"),
            )
            for l in data.get("lines", [])
        ]

        # Parse approved_at if present (backward-compatible with legacy data)
        approved_at_raw = data.get("approved_at")
        approved_at = None
        if approved_at_raw:
            approved_at = datetime.fromisoformat(approved_at_raw)

        return cls(
            id=data.get("id", str(uuid4())),
            reference=data.get("reference", ""),
            description=data.get("description", ""),
            adjustment_type=AdjustmentType(data.get("adjustment_type", "other")),
            status=AdjustmentStatus(data.get("status", "proposed")),
            lines=lines,
            prepared_by=data.get("prepared_by"),
            reviewed_by=data.get("reviewed_by"),
            approved_by=data.get("approved_by"),
            approved_at=approved_at,
            notes=data.get("notes"),
            is_reversing=data.get("is_reversing", False),
        )


@dataclass
class AdjustmentSet:
    """
    Collection of adjusting entries for a single audit/period.

    Provides aggregate statistics and validation across all entries.
    """
    entries: list[AdjustingEntry] = field(default_factory=list)
    period_label: Optional[str] = None
    client_name: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_adjustments(self) -> int:
        """Total number of adjusting entries."""
        return len(self.entries)

    @property
    def proposed_count(self) -> int:
        """Number of proposed entries pending review."""
        return sum(1 for e in self.entries if e.status == AdjustmentStatus.PROPOSED)

    @property
    def approved_count(self) -> int:
        """Number of approved entries."""
        return sum(1 for e in self.entries if e.status == AdjustmentStatus.APPROVED)

    @property
    def rejected_count(self) -> int:
        """Number of rejected entries."""
        return sum(1 for e in self.entries if e.status == AdjustmentStatus.REJECTED)

    @property
    def posted_count(self) -> int:
        """Number of posted entries."""
        return sum(1 for e in self.entries if e.status == AdjustmentStatus.POSTED)

    @property
    def total_adjustment_amount(self) -> Decimal:
        """Sum of all entry totals (for approved/posted entries only)."""
        return sum(
            (e.entry_total for e in self.entries
             if e.status in (AdjustmentStatus.APPROVED, AdjustmentStatus.POSTED)),
            Decimal("0.00")
        )

    def add_entry(self, entry: AdjustingEntry) -> None:
        """Add an adjusting entry to the set."""
        self.entries.append(entry)

    def remove_entry(self, entry_id: str) -> bool:
        """Remove an entry by ID. Returns True if found and removed."""
        original_count = len(self.entries)
        self.entries = [e for e in self.entries if e.id != entry_id]
        return len(self.entries) != original_count

    def get_entry(self, entry_id: str) -> Optional[AdjustingEntry]:
        """Get an entry by ID."""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None

    def get_entries_by_status(self, status: AdjustmentStatus) -> list[AdjustingEntry]:
        """Filter entries by status."""
        return [e for e in self.entries if e.status == status]

    def get_entries_by_type(self, adj_type: AdjustmentType) -> list[AdjustingEntry]:
        """Filter entries by adjustment type."""
        return [e for e in self.entries if e.adjustment_type == adj_type]

    def generate_next_reference(self, prefix: str = "AJE") -> str:
        """Generate next sequential reference number."""
        existing = [e.reference for e in self.entries if e.reference.startswith(prefix)]
        if not existing:
            return f"{prefix}-001"

        # Extract numbers and find max
        numbers = []
        for ref in existing:
            try:
                num = int(ref.split("-")[-1])
                numbers.append(num)
            except (ValueError, IndexError):
                continue

        next_num = max(numbers) + 1 if numbers else 1
        return f"{prefix}-{next_num:03d}"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "entries": [e.to_dict() for e in self.entries],
            "total_adjustments": self.total_adjustments,
            "proposed_count": self.proposed_count,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "posted_count": self.posted_count,
            "total_adjustment_amount": float(self.total_adjustment_amount),
            "period_label": self.period_label,
            "client_name": self.client_name,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AdjustmentSet":
        """Reconstruct an AdjustmentSet from a dictionary (Sprint 262)."""
        entries = [AdjustingEntry.from_dict(e) for e in data.get("entries", [])]
        return cls(
            entries=entries,
            period_label=data.get("period_label"),
            client_name=data.get("client_name"),
        )


@dataclass
class AdjustedAccountBalance:
    """
    Single account with unadjusted and adjusted balances.
    """
    account_name: str
    unadjusted_debit: Decimal
    unadjusted_credit: Decimal
    adjustment_debit: Decimal = Decimal("0.00")
    adjustment_credit: Decimal = Decimal("0.00")

    @property
    def unadjusted_balance(self) -> Decimal:
        """Net unadjusted balance (positive = debit, negative = credit)."""
        return self.unadjusted_debit - self.unadjusted_credit

    @property
    def net_adjustment(self) -> Decimal:
        """Net adjustment amount (positive = debit, negative = credit)."""
        return self.adjustment_debit - self.adjustment_credit

    @property
    def adjusted_debit(self) -> Decimal:
        """Adjusted debit balance."""
        adjusted = self.unadjusted_debit + self.adjustment_debit - self.adjustment_credit
        return max(adjusted, Decimal("0.00"))

    @property
    def adjusted_credit(self) -> Decimal:
        """Adjusted credit balance."""
        adjusted = self.unadjusted_credit + self.adjustment_credit - self.adjustment_debit
        return max(adjusted, Decimal("0.00"))

    @property
    def adjusted_balance(self) -> Decimal:
        """Net adjusted balance."""
        return self.adjusted_debit - self.adjusted_credit

    @property
    def has_adjustment(self) -> bool:
        """Check if account was adjusted."""
        return self.adjustment_debit != 0 or self.adjustment_credit != 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "account_name": self.account_name,
            "unadjusted_debit": float(self.unadjusted_debit),
            "unadjusted_credit": float(self.unadjusted_credit),
            "unadjusted_balance": float(self.unadjusted_balance),
            "adjustment_debit": float(self.adjustment_debit),
            "adjustment_credit": float(self.adjustment_credit),
            "net_adjustment": float(self.net_adjustment),
            "adjusted_debit": float(self.adjusted_debit),
            "adjusted_credit": float(self.adjusted_credit),
            "adjusted_balance": float(self.adjusted_balance),
            "has_adjustment": self.has_adjustment,
        }


@dataclass
class AdjustedTrialBalance:
    """
    Complete trial balance with adjustments applied.

    Shows unadjusted, adjustments, and adjusted columns for each account.
    """
    accounts: list[AdjustedAccountBalance] = field(default_factory=list)
    adjustments_applied: list[str] = field(default_factory=list)  # Entry IDs
    is_simulation: bool = False
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_unadjusted_debits(self) -> Decimal:
        """Sum of unadjusted debit balances."""
        return sum((a.unadjusted_debit for a in self.accounts), Decimal("0.00"))

    @property
    def total_unadjusted_credits(self) -> Decimal:
        """Sum of unadjusted credit balances."""
        return sum((a.unadjusted_credit for a in self.accounts), Decimal("0.00"))

    @property
    def total_adjustment_debits(self) -> Decimal:
        """Sum of adjustment debits."""
        return sum((a.adjustment_debit for a in self.accounts), Decimal("0.00"))

    @property
    def total_adjustment_credits(self) -> Decimal:
        """Sum of adjustment credits."""
        return sum((a.adjustment_credit for a in self.accounts), Decimal("0.00"))

    @property
    def total_adjusted_debits(self) -> Decimal:
        """Sum of adjusted debit balances."""
        return sum((a.adjusted_debit for a in self.accounts), Decimal("0.00"))

    @property
    def total_adjusted_credits(self) -> Decimal:
        """Sum of adjusted credit balances."""
        return sum((a.adjusted_credit for a in self.accounts), Decimal("0.00"))

    @property
    def is_balanced(self) -> bool:
        """Check if adjusted trial balance is balanced."""
        return self.total_adjusted_debits == self.total_adjusted_credits

    @property
    def accounts_with_adjustments(self) -> list[AdjustedAccountBalance]:
        """Get only accounts that have adjustments."""
        return [a for a in self.accounts if a.has_adjustment]

    @property
    def adjustment_count(self) -> int:
        """Number of entries applied."""
        return len(self.adjustments_applied)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "accounts": [a.to_dict() for a in self.accounts],
            "adjustments_applied": self.adjustments_applied,
            "totals": {
                "unadjusted_debits": float(self.total_unadjusted_debits),
                "unadjusted_credits": float(self.total_unadjusted_credits),
                "adjustment_debits": float(self.total_adjustment_debits),
                "adjustment_credits": float(self.total_adjustment_credits),
                "adjusted_debits": float(self.total_adjusted_debits),
                "adjusted_credits": float(self.total_adjusted_credits),
            },
            "is_balanced": self.is_balanced,
            "is_simulation": self.is_simulation,
            "adjustment_count": self.adjustment_count,
            "accounts_with_adjustments_count": len(self.accounts_with_adjustments),
            "generated_at": self.generated_at.isoformat(),
        }


def apply_adjustments(
    trial_balance: list[dict],
    adjustments: AdjustmentSet,
    mode: str = "official",
) -> AdjustedTrialBalance:
    """
    Apply adjusting entries to a trial balance.

    Args:
        trial_balance: List of account dicts with 'account', 'debit', 'credit' keys
        adjustments: AdjustmentSet containing entries to apply
        mode: "official" (approved+posted only) or "simulation" (also includes proposed)

    Returns:
        AdjustedTrialBalance with before/after balances and is_simulation flag
    """
    # Build account map from trial balance
    account_map: dict[str, AdjustedAccountBalance] = {}

    for row in trial_balance:
        account_name = row.get("account", "")
        if not account_name:
            continue

        debit = Decimal(str(row.get("debit", 0) or 0))
        credit = Decimal(str(row.get("credit", 0) or 0))

        # Handle duplicate accounts by summing
        if account_name in account_map:
            existing = account_map[account_name]
            existing.unadjusted_debit += debit
            existing.unadjusted_credit += credit
        else:
            account_map[account_name] = AdjustedAccountBalance(
                account_name=account_name,
                unadjusted_debit=debit,
                unadjusted_credit=credit,
            )

    # Determine which statuses to include based on mode
    valid_statuses = {AdjustmentStatus.APPROVED, AdjustmentStatus.POSTED}
    is_simulation = mode == "simulation"
    if is_simulation:
        valid_statuses.add(AdjustmentStatus.PROPOSED)

    # Apply adjustments
    applied_ids = []
    for entry in adjustments.entries:
        if entry.status not in valid_statuses:
            continue

        for line in entry.lines:
            account_name = line.account_name

            # Create account if it doesn't exist (new account from adjustment)
            if account_name not in account_map:
                account_map[account_name] = AdjustedAccountBalance(
                    account_name=account_name,
                    unadjusted_debit=Decimal("0.00"),
                    unadjusted_credit=Decimal("0.00"),
                )

            # Apply the adjustment
            account_map[account_name].adjustment_debit += line.debit
            account_map[account_name].adjustment_credit += line.credit

        applied_ids.append(entry.id)

    # Sort accounts alphabetically
    sorted_accounts = sorted(account_map.values(), key=lambda a: a.account_name.lower())

    return AdjustedTrialBalance(
        accounts=sorted_accounts,
        adjustments_applied=applied_ids,
        is_simulation=is_simulation,
    )


def create_simple_entry(
    reference: str,
    description: str,
    debit_account: str,
    credit_account: str,
    amount: Decimal,
    adjustment_type: AdjustmentType = AdjustmentType.OTHER,
    notes: Optional[str] = None,
) -> AdjustingEntry:
    """
    Convenience function to create a simple 2-line adjusting entry.

    Args:
        reference: Entry reference number (e.g., "AJE-001")
        description: Entry description
        debit_account: Account to debit
        credit_account: Account to credit
        amount: Amount of the entry
        adjustment_type: Type of adjustment
        notes: Optional notes

    Returns:
        AdjustingEntry with two lines (debit and credit)
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    return AdjustingEntry(
        reference=reference,
        description=description,
        adjustment_type=adjustment_type,
        lines=[
            AdjustmentLine(account_name=debit_account, debit=amount),
            AdjustmentLine(account_name=credit_account, credit=amount),
        ],
        notes=notes,
    )


def validate_entry_accounts(
    entry: AdjustingEntry,
    valid_accounts: set[str],
    case_insensitive: bool = True,
) -> list[str]:
    """
    Validate that entry accounts exist in the trial balance.

    Args:
        entry: The adjusting entry to validate
        valid_accounts: Set of valid account names from trial balance
        case_insensitive: If True, compare accounts case-insensitively

    Returns:
        List of unknown account names (empty if all valid)
    """
    if case_insensitive:
        valid_lower = {a.lower() for a in valid_accounts}
        unknown = [
            line.account_name
            for line in entry.lines
            if line.account_name.lower() not in valid_lower
        ]
    else:
        unknown = [
            line.account_name
            for line in entry.lines
            if line.account_name not in valid_accounts
        ]

    return unknown
