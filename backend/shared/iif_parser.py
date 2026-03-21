"""
Paciolus — IIF (Intuit Interchange Format) File Parser

Hand-rolled IIF parser for QuickBooks transaction exports.
No external dependencies beyond stdlib and pandas.

Design:
- Tab-delimited text; header rows start with `!` (e.g., `!TRNS`, `!SPL`, `!ENDTRNS`)
- `TRNS` = parent transaction line; `SPL` = split/child line; `ENDTRNS` = block delimiter
- `!TRNS` and `!SPL` define **separate** column schemas for their respective data rows
- Other sections (`!ACCNT`, `!CUST`, `!VEND`, `!CLASS`, `!HDR`) are ignored for
  transaction projection but tracked in metadata
- Output: pandas DataFrame with transaction-projection columns compatible with
  JE Testing, Revenue Testing, Statistical Sampling, AP Payment Testing,
  and Bank Reconciliation (GL side)

Security:
- 64KB scan limit for header presence validation
- Encoding fallback: UTF-8 -> Latin-1 (same as OFX parser)
- Binary content rejection handled upstream in helpers.py magic byte guard
"""

import logging
import re
from dataclasses import dataclass, field

import pandas as pd
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

_IIF_HEADER_SCAN_SIZE = 65536

# QuickBooks date formats: MM/DD/YYYY, M/D/YYYY, MM/DD/YY
_DATE_PATTERN = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$")


# ─────────────────────────────────────────────────────────────────────
# Metadata
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class IifMetadata:
    """Non-blocking metadata extracted from IIF file for detection_notes."""

    section_types_found: list[str] = field(default_factory=list)
    transaction_block_count: int = 0
    transaction_row_count: int = 0
    account_list_count: int = 0
    date_range_start: str = ""
    date_range_end: str = ""
    duplicate_references: list[str] = field(default_factory=list)
    malformed_row_count: int = 0
    encoding: str = "utf-8"


# ─────────────────────────────────────────────────────────────────────
# Encoding
# ─────────────────────────────────────────────────────────────────────


def _decode_iif(file_bytes: bytes, filename: str) -> tuple[str, str]:
    """Decode IIF bytes with UTF-8 -> Latin-1 fallback.

    Returns (text, encoding_used).
    """
    for enc in ("utf-8", "latin-1"):
        try:
            return file_bytes.decode(enc), enc
        except UnicodeDecodeError:
            continue

    raise HTTPException(
        status_code=400,
        detail=f"The file '{filename}' contains characters that could not be decoded. Try saving as UTF-8.",
    )


# ─────────────────────────────────────────────────────────────────────
# Presence validation
# ─────────────────────────────────────────────────────────────────────


def _validate_iif_presence(text: str, filename: str) -> None:
    """Ensure !TRNS or !SPL header exists in first 64KB."""
    scan = text[:_IIF_HEADER_SCAN_SIZE].upper()
    if "!TRNS" not in scan and "!SPL" not in scan:
        raise HTTPException(
            status_code=400,
            detail=f"The IIF file '{filename}' does not contain transaction data. "
            "Please export a 'General Journal' or 'Transaction Detail' report "
            "from QuickBooks.",
        )


# ─────────────────────────────────────────────────────────────────────
# Date parsing
# ─────────────────────────────────────────────────────────────────────


def _parse_iif_date(date_str: str) -> str:
    """Convert QuickBooks date format to ISO YYYY-MM-DD.

    Handles: MM/DD/YYYY, M/D/YYYY, MM/DD/YY.
    Returns raw string on parse failure (non-blocking).
    """
    if not date_str or not date_str.strip():
        return ""

    cleaned = date_str.strip()
    match = _DATE_PATTERN.match(cleaned)
    if not match:
        return cleaned

    month_str, day_str, year_str = match.group(1), match.group(2), match.group(3)

    try:
        month = int(month_str)
        day = int(day_str)
        year = int(year_str)
    except ValueError:
        return cleaned

    # Two-digit year: 00-49 -> 2000s, 50-99 -> 1900s (QuickBooks convention)
    if year < 100:
        year = 2000 + year if year < 50 else 1900 + year

    if not (1 <= month <= 12 and 1 <= day <= 31):
        return cleaned

    return f"{year:04d}-{month:02d}-{day:02d}"


# ─────────────────────────────────────────────────────────────────────
# Section parsing
# ─────────────────────────────────────────────────────────────────────


def _parse_sections(lines: list[str]) -> tuple[list[dict], IifMetadata]:
    """Parse IIF lines into transaction records and metadata.

    Tracks !TRNS and !SPL headers separately, maps data rows against
    their respective header schemas, groups within TRNS...ENDTRNS blocks.
    """
    trns_headers: list[str] = []
    spl_headers: list[str] = []
    section_types: set[str] = set()
    account_count = 0
    transactions: list[dict] = []
    malformed_count = 0

    block_id = 0
    in_block = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        parts = stripped.split("\t")
        first = parts[0].upper()

        # Header rows
        if first == "!TRNS":
            trns_headers = [p.upper() for p in parts]
            section_types.add("TRNS")
            continue
        if first == "!SPL":
            spl_headers = [p.upper() for p in parts]
            section_types.add("SPL")
            continue
        if first == "!ENDTRNS":
            continue

        # Other section headers (e.g., !ACCNT, !CUST, !VEND, !CLASS, !HDR)
        if first.startswith("!"):
            section_name = first[1:]
            section_types.add(section_name)
            continue

        # Data rows
        if first == "TRNS":
            if not trns_headers:
                malformed_count += 1
                continue
            if len(parts) != len(trns_headers):
                malformed_count += 1
                continue
            block_id += 1
            in_block = True
            row = dict(zip(trns_headers, parts))
            row["_LINE_TYPE"] = "TRNS"
            row["_BLOCK_ID"] = block_id
            transactions.append(row)
            continue

        if first == "SPL":
            if not spl_headers:
                malformed_count += 1
                continue
            if len(parts) != len(spl_headers):
                malformed_count += 1
                continue
            row = dict(zip(spl_headers, parts))
            row["_LINE_TYPE"] = "SPL"
            row["_BLOCK_ID"] = block_id if in_block else 0
            transactions.append(row)
            continue

        if first == "ENDTRNS":
            in_block = False
            continue

        # Account list rows (ACCNT section data)
        if first == "ACCNT":
            account_count += 1
            continue

    # Build metadata
    dates: list[str] = []
    references: list[str] = []
    for txn in transactions:
        date_val = txn.get("DATE", "")
        if date_val:
            parsed = _parse_iif_date(date_val)
            if parsed and re.match(r"^\d{4}-\d{2}-\d{2}$", parsed):
                dates.append(parsed)
        ref_val = txn.get("DOCNUM", "")
        if ref_val:
            references.append(ref_val)

    # Detect duplicate references
    seen_refs: set[str] = set()
    dup_refs: list[str] = []
    for ref in references:
        if ref in seen_refs and ref not in dup_refs:
            dup_refs.append(ref)
        seen_refs.add(ref)

    dates.sort()
    metadata = IifMetadata(
        section_types_found=sorted(section_types),
        transaction_block_count=block_id,
        transaction_row_count=len(transactions),
        account_list_count=account_count,
        date_range_start=dates[0] if dates else "",
        date_range_end=dates[-1] if dates else "",
        duplicate_references=dup_refs,
        malformed_row_count=malformed_count,
    )

    return transactions, metadata


# ─────────────────────────────────────────────────────────────────────
# Transaction projection
# ─────────────────────────────────────────────────────────────────────


def _project_transactions(raw_transactions: list[dict]) -> list[dict]:
    """Map raw IIF transaction dicts to standardized output columns."""
    projected = []
    for txn in raw_transactions:
        # Parse amount
        amount_str = txn.get("AMOUNT", "")
        amount = None
        if amount_str:
            try:
                amount = float(amount_str)
            except ValueError:
                amount = None

        projected.append(
            {
                "Date": _parse_iif_date(txn.get("DATE", "")),
                "Account": txn.get("ACCNT", ""),
                "Amount": amount,
                "Description": txn.get("MEMO", ""),
                "Reference": txn.get("DOCNUM", ""),
                "Type": txn.get("TRNSTYPE", ""),
                "Name": txn.get("NAME", ""),
                "Line_Type": txn.get("_LINE_TYPE", ""),
                "Block_ID": txn.get("_BLOCK_ID", 0),
            }
        )
    return projected


# ─────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────


def parse_iif(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse IIF file bytes into a transaction-projection DataFrame.

    Returns DataFrame with columns:
        Date, Account, Amount, Description, Reference, Type, Name,
        Line_Type, Block_ID

    Raises HTTPException(400) on:
        - No !TRNS/!SPL headers found
        - Headers found but zero transaction data rows
        - Encoding failure
    """
    # Decode
    text, encoding = _decode_iif(file_bytes, filename)

    # Validate presence
    _validate_iif_presence(text, filename)

    # Parse sections
    lines = text.splitlines()
    raw_transactions, metadata = _parse_sections(lines)

    if not raw_transactions:
        raise HTTPException(
            status_code=400,
            detail=f"The IIF file '{filename}' contains headers but no transaction data. "
            "Please verify the file contains journal entries or transaction detail.",
        )

    # Project to standardized columns
    projected = _project_transactions(raw_transactions)

    # Update metadata with encoding
    metadata = IifMetadata(
        section_types_found=metadata.section_types_found,
        transaction_block_count=metadata.transaction_block_count,
        transaction_row_count=metadata.transaction_row_count,
        account_list_count=metadata.account_list_count,
        date_range_start=metadata.date_range_start,
        date_range_end=metadata.date_range_end,
        duplicate_references=metadata.duplicate_references,
        malformed_row_count=metadata.malformed_row_count,
        encoding=encoding,
    )

    # Log metadata
    logger.info(
        "IIF parsed: sections=%s, blocks=%d, rows=%d, accounts=%d, "
        "date_range=%s..%s, duplicates=%d, malformed=%d, encoding=%s",
        metadata.section_types_found,
        metadata.transaction_block_count,
        metadata.transaction_row_count,
        metadata.account_list_count,
        metadata.date_range_start,
        metadata.date_range_end,
        len(metadata.duplicate_references),
        metadata.malformed_row_count,
        metadata.encoding,
    )

    # Build DataFrame
    df = pd.DataFrame(projected)

    # Store metadata as DataFrame attribute
    df.attrs["iif_metadata"] = metadata

    return df
