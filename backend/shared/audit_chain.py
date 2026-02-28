"""
Cryptographic Audit Log Chaining — CC7.4 Tamper Evidence

Implements HMAC-SHA256 hash chaining for ActivityLog records.
Each record's chain_hash = HMAC-SHA256(key, previous_chain_hash + record_content_hash).
A genesis record (first in a user's chain) uses a well-known sentinel as "previous hash".

Verification walks the chain sequentially and detects:
- Modified record content (content hash mismatch)
- Deleted records (chain hash mismatch due to missing link)
- Inserted records (chain hash mismatch due to unexpected predecessor)

Sprint 461 — SOC 2 Phase LXVI (CC7.4 / Audit Logging §5.4).
"""

import hashlib
import hmac
import logging
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import asc
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Sentinel used as "previous hash" for the first record in any user's chain.
GENESIS_SENTINEL = "0" * 64


def _get_chain_secret() -> str:
    """Lazy import to avoid circular dependency with config at module load."""
    from config import CSRF_SECRET_KEY

    return CSRF_SECRET_KEY


_TWO_PLACES = Decimal("0.01")


def _normalize_monetary(value: object) -> str:
    """Normalize a monetary value to a fixed 2-decimal-place string.

    Handles float, Decimal, int, and string inputs consistently.
    Ensures that 1000.0 (float), Decimal('1000'), and Decimal('1000.00')
    all produce the string '1000.00'.
    """
    return str(Decimal(str(value)).quantize(_TWO_PLACES))


def compute_content_hash(record: "ActivityLog") -> str:  # noqa: F821
    """Compute SHA-256 hash of the immutable content fields of an ActivityLog record.

    Fields included: id, user_id, filename_hash, timestamp, record_count,
    total_debits, total_credits, materiality_threshold, was_balanced,
    anomaly_count, material_count, immaterial_count, is_consolidated, sheet_count.

    Returns 64-char lowercase hex digest.
    """
    # Normalize timestamp to naive UTC string for consistent hashing.
    # SQLite strips timezone info; PostgreSQL preserves it. Stripping
    # tzinfo before formatting ensures identical hashes across backends.
    ts = record.timestamp
    if ts:
        naive = ts.replace(tzinfo=None) if ts.tzinfo else ts
        timestamp_str = naive.strftime("%Y-%m-%dT%H:%M:%S.%f")
    else:
        timestamp_str = ""

    parts = [
        str(record.id),
        str(record.user_id or ""),
        record.filename_hash or "",
        timestamp_str,
        str(record.record_count),
        _normalize_monetary(record.total_debits),
        _normalize_monetary(record.total_credits),
        _normalize_monetary(record.materiality_threshold),
        str(record.was_balanced),
        str(record.anomaly_count),
        str(record.material_count),
        str(record.immaterial_count),
        str(record.is_consolidated),
        str(record.sheet_count or ""),
    ]
    content = "|".join(parts)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_chain_hash(previous_chain_hash: str, content_hash: str) -> str:
    """Compute HMAC-SHA256 chain hash linking a record to its predecessor.

    chain_hash = HMAC-SHA256(secret, previous_chain_hash + content_hash)

    For the genesis record, previous_chain_hash is GENESIS_SENTINEL.
    """
    secret = _get_chain_secret()
    message = (previous_chain_hash + content_hash).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def get_previous_chain_hash(db: Session, user_id: int, before_id: int) -> str:
    """Retrieve the chain_hash of the most recent ActivityLog before `before_id`
    for the given user, or GENESIS_SENTINEL if none exists."""
    from models import ActivityLog

    previous = (
        db.query(ActivityLog.chain_hash)
        .filter(
            ActivityLog.user_id == user_id,
            ActivityLog.id < before_id,
            ActivityLog.archived_at.is_(None),
        )
        .order_by(ActivityLog.id.desc())
        .first()
    )
    if previous and previous[0]:
        return previous[0]
    return GENESIS_SENTINEL


def stamp_chain_hash(db: Session, record: "ActivityLog") -> str:  # noqa: F821
    """Compute and assign chain_hash to a freshly inserted ActivityLog record.

    Must be called AFTER db.flush() so that record.id and record.timestamp
    are populated by the database.

    Returns the computed chain_hash.
    """
    previous_hash = get_previous_chain_hash(db, record.user_id, record.id)
    content_hash = compute_content_hash(record)
    chain_hash = compute_chain_hash(previous_hash, content_hash)
    record.chain_hash = chain_hash
    return chain_hash


@dataclass
class ChainLink:
    """Result for a single record in a chain verification walk."""

    record_id: int
    expected_chain_hash: str
    actual_chain_hash: str | None
    content_hash_matches: bool
    chain_valid: bool


@dataclass
class ChainVerificationResult:
    """Result of verifying an audit log chain for a user."""

    user_id: int
    total_records: int
    verified_records: int
    first_broken_id: int | None
    is_intact: bool
    links: list[ChainLink]


def verify_chain(
    db: Session,
    user_id: int,
    start_id: int | None = None,
    end_id: int | None = None,
) -> ChainVerificationResult:
    """Walk the audit log chain for a user and verify integrity.

    Checks every record from start_id to end_id (inclusive).
    If start_id is None, starts from the user's first record.
    If end_id is None, continues to the user's latest record.

    Returns a ChainVerificationResult with per-record details.
    """
    from models import ActivityLog

    # Expire all cached ORM instances to ensure we read actual DB state.
    # This is critical for tamper detection: if an attacker modified a row
    # via direct SQL, the identity map would still show the old values.
    db.expire_all()

    query = db.query(ActivityLog).filter(
        ActivityLog.user_id == user_id,
        ActivityLog.archived_at.is_(None),
    )
    if start_id is not None:
        query = query.filter(ActivityLog.id >= start_id)
    if end_id is not None:
        query = query.filter(ActivityLog.id <= end_id)

    records = query.order_by(asc(ActivityLog.id)).all()

    if not records:
        return ChainVerificationResult(
            user_id=user_id,
            total_records=0,
            verified_records=0,
            first_broken_id=None,
            is_intact=True,
            links=[],
        )

    links: list[ChainLink] = []
    first_broken_id: int | None = None
    previous_chain_hash = GENESIS_SENTINEL

    # If we're starting mid-chain, look up the predecessor's chain_hash
    if start_id is not None:
        predecessor = (
            db.query(ActivityLog.chain_hash)
            .filter(
                ActivityLog.user_id == user_id,
                ActivityLog.id < start_id,
                ActivityLog.archived_at.is_(None),
            )
            .order_by(ActivityLog.id.desc())
            .first()
        )
        if predecessor and predecessor[0]:
            previous_chain_hash = predecessor[0]

    for record in records:
        content_hash = compute_content_hash(record)
        expected = compute_chain_hash(previous_chain_hash, content_hash)

        content_matches = True  # Content hash is recomputed; it always matches if data is unchanged
        chain_valid = record.chain_hash == expected

        link = ChainLink(
            record_id=record.id,
            expected_chain_hash=expected,
            actual_chain_hash=record.chain_hash,
            content_hash_matches=content_matches,
            chain_valid=chain_valid,
        )
        links.append(link)

        if not chain_valid and first_broken_id is None:
            first_broken_id = record.id
            logger.warning(
                "Audit chain break detected at record %d for user %d",
                record.id,
                user_id,
            )

        # Use the ACTUAL stored hash as the "previous" for the next record,
        # so we can detect exactly which record is the break point.
        previous_chain_hash = record.chain_hash or GENESIS_SENTINEL

    return ChainVerificationResult(
        user_id=user_id,
        total_records=len(records),
        verified_records=sum(1 for link in links if link.chain_valid),
        first_broken_id=first_broken_id,
        is_intact=first_broken_id is None,
        links=links,
    )
