"""Cryptographic audit log chaining for tamper-resistant evidence (SOC 2 CC7.4).

Sprint 461: HMAC-SHA512 hash chain on ActivityLog records.
Each new record's chain_hash = HMAC(key, previous_chain_hash | serialized_record).
Verification traverses the chain and recomputes each hash to detect tampering.

Secret domain separation: Uses AUDIT_CHAIN_SECRET_KEY (independent from JWT).
Backward-compatible verification falls back to JWT_SECRET_KEY for pre-rotation records.
"""

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any, Optional

from config import AUDIT_CHAIN_SECRET_KEY, JWT_SECRET_KEY

# The genesis hash for the first record in the chain (128 hex zeros = SHA-512 output length)
GENESIS_HASH = "0" * 128


def _serialize_record(record: Any) -> str:
    """Serialize ActivityLog record fields into a deterministic string for hashing.

    Uses pipe-delimited fields in a fixed order. All fields are converted to
    their string representation to ensure deterministic serialization regardless
    of the underlying Python type (e.g., Decimal vs float for Numeric columns).
    """
    fields = [
        str(record.id),
        str(record.user_id or ""),
        record.filename_hash or "",
        str(record.record_count),
        str(record.total_debits),
        str(record.total_credits),
        str(record.materiality_threshold),
        str(record.was_balanced),
        str(record.anomaly_count),
        str(record.material_count),
        str(record.immaterial_count),
        str(record.is_consolidated),
        str(record.sheet_count or ""),
        record.timestamp.isoformat() if record.timestamp else "",
    ]
    return "|".join(fields)


def _compute_hash_with_key(key: str, previous_hash: str, record: Any) -> str:
    """Compute HMAC-SHA512 chain hash with a specific key."""
    content = previous_hash + "|" + _serialize_record(record)
    return hmac.new(
        (key or "").encode("utf-8"),
        content.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()


def compute_chain_hash(previous_hash: str, record: Any) -> str:
    """Compute HMAC-SHA512 chain hash: HMAC(key, previous_hash | serialized_record).

    Uses SHA-512 for 128-char hex output.
    Uses AUDIT_CHAIN_SECRET_KEY (separate security domain from JWT).
    """
    return _compute_hash_with_key(AUDIT_CHAIN_SECRET_KEY, previous_hash, record)


def previous_chain_hash(db: Any, record: Any) -> str:
    """The hash a new record links to: the same user's latest chained record.

    Sprint 845 (claims review Part 6): the chain used to link to the latest
    chained record of *any* user while verification walked one user's records,
    so the first time two users' activity interleaved, verification reported a
    break. It also skipped archived rows on both sides, so archiving a record
    after it was linked broke the chain. Both sides now use the same rule:
    per user, archived rows included.
    """
    from models import ActivityLog  # Avoid circular import

    prev = (
        db.query(ActivityLog.chain_hash)
        .filter(
            ActivityLog.id < record.id,
            ActivityLog.user_id == record.user_id,
            ActivityLog.chain_hash.isnot(None),
        )
        .order_by(ActivityLog.id.desc())
        .first()
    )
    return prev[0] if prev else GENESIS_HASH


def _legacy_previous_hash(db: Any, record: Any) -> str:
    """Predecessor under the pre-Sprint-845 rule (any user, non-archived).

    Rows written before Sprint 845 were linked this way. Verification accepts
    either link so those rows still verify; both are keyed HMACs, so accepting
    two predecessors does not let anyone without the key forge a record.
    """
    from models import ActivityLog  # Avoid circular import

    prev = (
        db.query(ActivityLog.chain_hash)
        .filter(
            ActivityLog.id < record.id,
            ActivityLog.archived_at.is_(None),
            ActivityLog.chain_hash.isnot(None),
        )
        .order_by(ActivityLog.id.desc())
        .first()
    )
    return prev[0] if prev else GENESIS_HASH


@dataclass
class ChainVerificationResult:
    """Result of audit chain verification."""

    is_valid: bool
    records_checked: int
    first_broken_id: Optional[int] = None
    error_message: Optional[str] = None
    # Sprint 845: rows in range with no chain hash (pre-Sprint-461) are reported,
    # not silently skipped.
    unchained_records: int = 0


def _matches(record: Any, previous_hash: str) -> bool:
    if record.chain_hash == compute_chain_hash(previous_hash, record):
        return True
    # Records created before AUDIT_CHAIN_SECRET_KEY was separated from JWT_SECRET_KEY.
    if AUDIT_CHAIN_SECRET_KEY != JWT_SECRET_KEY:
        return record.chain_hash == _compute_hash_with_key(JWT_SECRET_KEY, previous_hash, record)
    return False


def verify_audit_chain(db: Any, start_id: int, end_id: int, user_id: int) -> ChainVerificationResult:
    """Verify the integrity of one user's audit log chain between two record IDs.

    SECURITY: Scoped to user_id — only that user's records are read, and the
    chain is per user, so verification never depends on another tenant's rows.
    Archived (soft-deleted) records stay in the chain.
    """
    from models import ActivityLog  # Avoid circular import

    in_range = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.id >= start_id,
            ActivityLog.id <= end_id,
            ActivityLog.user_id == user_id,
        )
        .order_by(ActivityLog.id.asc())
        .all()
    )
    records = [r for r in in_range if r.chain_hash is not None]
    unchained = len(in_range) - len(records)

    if not records:
        return ChainVerificationResult(
            is_valid=True,
            records_checked=0,
            error_message="No chained records found in the specified range.",
            unchained_records=unchained,
        )

    previous_hash = previous_chain_hash(db, records[0])
    for idx, record in enumerate(records):
        if not (_matches(record, previous_hash) or _matches(record, _legacy_previous_hash(db, record))):
            return ChainVerificationResult(
                is_valid=False,
                records_checked=idx + 1,
                first_broken_id=record.id,
                error_message=f"Chain broken at record {record.id}: hash mismatch.",
                unchained_records=unchained,
            )
        previous_hash = record.chain_hash

    message = f"{unchained} record(s) in range predate chaining and were not checked." if unchained else None
    return ChainVerificationResult(
        is_valid=True,
        records_checked=len(records),
        error_message=message,
        unchained_records=unchained,
    )
