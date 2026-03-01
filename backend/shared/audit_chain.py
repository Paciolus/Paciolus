"""Cryptographic audit log chaining for tamper-resistant evidence (SOC 2 CC7.4).

Sprint 461: HMAC-SHA512 hash chain on ActivityLog records.
Each new record's chain_hash = HMAC(key, previous_chain_hash | serialized_record).
Verification traverses the chain and recomputes each hash to detect tampering.
"""

import hashlib
import hmac
from dataclasses import dataclass
from typing import Optional

from config import JWT_SECRET_KEY

# The genesis hash for the first record in the chain (128 hex zeros = SHA-512 output length)
GENESIS_HASH = "0" * 128


def _serialize_record(record) -> str:
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


def compute_chain_hash(previous_hash: str, record) -> str:
    """Compute HMAC-SHA512 chain hash: HMAC(key, previous_hash | serialized_record).

    Uses SHA-512 for 128-char hex output.
    The JWT_SECRET_KEY is used as HMAC key for domain separation.
    """
    content = previous_hash + "|" + _serialize_record(record)
    return hmac.new(
        JWT_SECRET_KEY.encode("utf-8"),
        content.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()


@dataclass
class ChainVerificationResult:
    """Result of audit chain verification."""

    is_valid: bool
    records_checked: int
    first_broken_id: Optional[int] = None
    error_message: Optional[str] = None


def verify_audit_chain(db, start_id: int, end_id: int) -> ChainVerificationResult:
    """Verify the integrity of the audit log chain between two record IDs.

    Checks that each record's chain_hash matches the expected HMAC of the
    previous hash + current record content. Returns verification result.
    """
    from models import ActivityLog  # Avoid circular import

    records = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.id >= start_id,
            ActivityLog.id <= end_id,
            ActivityLog.archived_at.is_(None),
            ActivityLog.chain_hash.isnot(None),
        )
        .order_by(ActivityLog.id.asc())
        .all()
    )

    if not records:
        return ChainVerificationResult(
            is_valid=True,
            records_checked=0,
            error_message="No chained records found in the specified range.",
        )

    # Get the hash of the record immediately before start_id (or genesis)
    previous_record = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.id < records[0].id,
            ActivityLog.archived_at.is_(None),
            ActivityLog.chain_hash.isnot(None),
        )
        .order_by(ActivityLog.id.desc())
        .first()
    )
    previous_hash = previous_record.chain_hash if previous_record else GENESIS_HASH

    for idx, record in enumerate(records):
        expected_hash = compute_chain_hash(previous_hash, record)
        if record.chain_hash != expected_hash:
            return ChainVerificationResult(
                is_valid=False,
                records_checked=idx + 1,
                first_broken_id=record.id,
                error_message=f"Chain broken at record {record.id}: hash mismatch.",
            )
        previous_hash = record.chain_hash

    return ChainVerificationResult(
        is_valid=True,
        records_checked=len(records),
    )
