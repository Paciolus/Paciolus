"""
Paciolus — OFX/QBO File Parser

Hand-rolled OFX parser supporting both SGML v1.x and XML v2.x dialects.
No external dependencies beyond stdlib xml.etree.ElementTree and pandas.

Design:
- Dialect detection: inspect first 4KB for <?xml> declaration
- SGML v1.x: strip OFX header, insert closing tags for leaf elements, feed to ET
- XML v2.x: parse directly with ET (DOCTYPE/ENTITY blocked)
- Transaction extraction: walk BANKMSGSRSV1 + CCSTMTTRNRS paths
- Output: pandas DataFrame with bank-rec-compatible column names

Security:
- DOCTYPE/ENTITY blocking (matches existing XML bomb pattern in helpers.py)
- 64KB scan limit for OFX tag presence
- Encoding fallback: UTF-8 → Latin-1 (+ CHARSET header if present in SGML)
"""

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import pandas as pd
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

_DIALECT_SCAN_SIZE = 4096
_OFX_TAG_SCAN_SIZE = 65536
_XML_BOMB_PATTERNS = (b"<!doctype", b"<!entity")

# OFX transaction paths (bank + credit card statements)
_BANK_TXN_PATHS = [
    ".//BANKMSGSRSV1/STMTTRNRS/STMTRS/BANKTRANLIST/STMTTRN",
    ".//BANKMSGSRSV1/STMTTRNRS/STMTRS/BANKTRANLIST//STMTTRN",
]
_CC_TXN_PATHS = [
    ".//CREDITCARDMSGSRSV1/CCSTMTTRNRS/CCSTMTRS/BANKTRANLIST/STMTTRN",
    ".//CREDITCARDMSGSRSV1/CCSTMTTRNRS/CCSTMTRS/BANKTRANLIST//STMTTRN",
]

# SGML leaf tag pattern: <TAG>value (no closing tag on same or next line)
# Matches: <TAGNAME>content-that-is-not-a-tag
_SGML_LEAF_RE = re.compile(
    r"<(\w+)>([^<\r\n]+)",
)


# ─────────────────────────────────────────────────────────────────────
# Metadata
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class OfxMetadata:
    """Non-blocking metadata extracted from OFX file for detection_notes."""

    dialect: str  # "SGML_V1" or "XML_V2"
    currency: str
    account_id: str  # masked: last 4 chars only
    account_type: str
    date_start: str
    date_end: str
    ledger_balance: str
    transaction_count: int
    duplicate_fitids: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────
# Dialect detection
# ─────────────────────────────────────────────────────────────────────


def _detect_dialect(text: str) -> str:
    """Detect OFX dialect from content.

    Returns 'XML_V2' if <?xml is found in first 4KB, otherwise 'SGML_V1'.
    """
    header = text[:_DIALECT_SCAN_SIZE].lower()
    if "<?xml" in header:
        return "XML_V2"
    return "SGML_V1"


def _validate_ofx_presence(text: str, filename: str) -> None:
    """Ensure <OFX> tag exists in first 64KB."""
    scan = text[:_OFX_TAG_SCAN_SIZE].upper()
    if "<OFX>" not in scan:
        raise HTTPException(
            status_code=400,
            detail=f"The file '{filename}' does not appear to be a valid OFX/QBO file. No <OFX> tag found.",
        )


# ─────────────────────────────────────────────────────────────────────
# Security
# ─────────────────────────────────────────────────────────────────────


def _check_xml_bombs(raw_bytes: bytes) -> None:
    """Block DOCTYPE and ENTITY declarations (XXE / billion laughs)."""
    scan = raw_bytes[:_OFX_TAG_SCAN_SIZE].lower()
    for pattern in _XML_BOMB_PATTERNS:
        if pattern in scan:
            raise HTTPException(
                status_code=400,
                detail="The file contains prohibited XML constructs (DTD/entity declarations) and cannot be processed.",
            )


# ─────────────────────────────────────────────────────────────────────
# Encoding
# ─────────────────────────────────────────────────────────────────────


def _decode_ofx(file_bytes: bytes, filename: str) -> str:
    """Decode OFX bytes with encoding detection.

    Priority: CHARSET header in SGML → UTF-8 → Latin-1.
    """
    # Try to extract CHARSET from SGML header (before <OFX>)
    charset = _extract_sgml_charset(file_bytes[:_DIALECT_SCAN_SIZE])

    encodings = []
    if charset:
        encodings.append(charset)
    encodings.extend(["utf-8", "latin-1"])

    for enc in encodings:
        try:
            return file_bytes.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue

    raise HTTPException(
        status_code=400,
        detail=f"The file '{filename}' contains characters that could not be decoded. Try saving as UTF-8.",
    )


def _extract_sgml_charset(header_bytes: bytes) -> str | None:
    """Extract CHARSET value from OFX SGML header block."""
    try:
        header_text = header_bytes.decode("ascii", errors="ignore")
    except Exception:
        return None

    for line in header_text.splitlines():
        if line.strip().upper().startswith("CHARSET:"):
            value = line.split(":", 1)[1].strip()
            # Map OFX charset codes to Python encoding names
            charset_map = {
                "1252": "cp1252",
                "ISO-8859-1": "latin-1",
                "UTF-8": "utf-8",
                "NONE": None,
                "": None,
            }
            return charset_map.get(value.upper(), value.lower())
    return None


# ─────────────────────────────────────────────────────────────────────
# SGML v1.x normalization
# ─────────────────────────────────────────────────────────────────────


def _strip_sgml_header(text: str) -> str:
    """Remove everything before <OFX> tag (SGML header block)."""
    upper = text.upper()
    idx = upper.find("<OFX>")
    if idx == -1:
        return text
    return text[idx:]


def _normalize_sgml_to_xml(sgml_text: str) -> str:
    """Convert SGML v1.x OFX to well-formed XML.

    Strategy: insert closing tags for leaf elements.
    A leaf element is one where <TAG>value appears without a matching </TAG>.
    """
    sgml_body = _strip_sgml_header(sgml_text)

    # Insert closing tags for leaf elements
    def _close_leaf(match: re.Match) -> str:
        tag = match.group(1)
        value = match.group(2).strip()
        return f"<{tag}>{value}</{tag}>"

    normalized = _SGML_LEAF_RE.sub(_close_leaf, sgml_body)

    # Wrap in XML declaration for parser
    if not normalized.strip().startswith("<?xml"):
        normalized = '<?xml version="1.0"?>\n' + normalized

    return normalized


# ─────────────────────────────────────────────────────────────────────
# Date parsing
# ─────────────────────────────────────────────────────────────────────


def _parse_ofx_date(date_str: str | None) -> str:
    """Convert OFX date format to ISO string.

    OFX format: YYYYMMDD[HHmmss[.XXX]][TZ]
    Output: YYYY-MM-DD
    """
    if not date_str:
        return ""

    # Strip timezone info (e.g., [-5:EST])
    cleaned = re.sub(r"\[.*?\]", "", date_str).strip()

    if len(cleaned) < 8:
        return date_str.strip()

    try:
        year = cleaned[0:4]
        month = cleaned[4:6]
        day = cleaned[6:8]
        # Validate
        int(year)
        m = int(month)
        d = int(day)
        if not (1 <= m <= 12 and 1 <= d <= 31):
            return date_str.strip()
        return f"{year}-{month}-{day}"
    except (ValueError, IndexError):
        return date_str.strip()


# ─────────────────────────────────────────────────────────────────────
# Transaction extraction
# ─────────────────────────────────────────────────────────────────────


def _get_element_text(txn: ET.Element, tag: str) -> str:
    """Get text content of a child element, or empty string."""
    el = txn.find(tag)
    if el is not None and el.text:
        return el.text.strip()
    return ""


def _extract_transactions(root: ET.Element) -> list[dict]:
    """Extract transactions from OFX ElementTree root.

    Searches both bank statement and credit card statement paths.
    """
    transactions = []

    # Collect from all known paths
    found_txns: list[ET.Element] = []
    for path in _BANK_TXN_PATHS + _CC_TXN_PATHS:
        found_txns.extend(root.findall(path))

    # Deduplicate by identity (same element object)
    seen_ids: set[int] = set()
    unique_txns: list[ET.Element] = []
    for txn in found_txns:
        if id(txn) not in seen_ids:
            seen_ids.add(id(txn))
            unique_txns.append(txn)

    for txn in unique_txns:
        fitid = _get_element_text(txn, "FITID")
        trntype = _get_element_text(txn, "TRNTYPE")
        dtposted = _get_element_text(txn, "DTPOSTED")
        trnamt = _get_element_text(txn, "TRNAMT")
        name = _get_element_text(txn, "NAME")
        memo = _get_element_text(txn, "MEMO")
        checknum = _get_element_text(txn, "CHECKNUM")

        # Combine NAME + MEMO for description (bank rec column detection expects this)
        description_parts = [p for p in (name, memo) if p]
        description = " - ".join(description_parts) if description_parts else ""

        # Parse amount
        amount = None
        if trnamt:
            try:
                amount = float(trnamt)
            except ValueError:
                amount = None

        transactions.append(
            {
                "Date": _parse_ofx_date(dtposted),
                "Amount": amount,
                "Description": description,
                "Reference": fitid,
                "Type": trntype,
                "Check_Number": checknum,
            }
        )

    return transactions


# ─────────────────────────────────────────────────────────────────────
# Metadata extraction
# ─────────────────────────────────────────────────────────────────────


def _extract_metadata(root: ET.Element, dialect: str, transactions: list[dict]) -> OfxMetadata:
    """Extract non-blocking metadata from OFX tree."""
    # Currency
    currency = ""
    for path in (".//CURDEF", ".//STMTRS/CURDEF", ".//CCSTMTRS/CURDEF"):
        el = root.find(path)
        if el is not None and el.text:
            currency = el.text.strip()
            break

    # Account ID (masked)
    account_id = ""
    for path in (".//ACCTID", ".//BANKACCTFROM/ACCTID", ".//CCACCTFROM/ACCTID"):
        el = root.find(path)
        if el is not None and el.text:
            raw = el.text.strip()
            account_id = f"****{raw[-4:]}" if len(raw) >= 4 else "****"
            break

    # Account type
    account_type = ""
    for path in (".//ACCTTYPE", ".//BANKACCTFROM/ACCTTYPE"):
        el = root.find(path)
        if el is not None and el.text:
            account_type = el.text.strip()
            break
    # Credit card detection
    if not account_type and root.find(".//CCSTMTTRNRS") is not None:
        account_type = "CREDITCARD"

    # Date range
    date_start = ""
    date_end = ""
    dtstart = root.find(".//DTSTART")
    dtend = root.find(".//DTEND")
    if dtstart is not None and dtstart.text:
        date_start = _parse_ofx_date(dtstart.text.strip())
    if dtend is not None and dtend.text:
        date_end = _parse_ofx_date(dtend.text.strip())

    # Ledger balance
    ledger_balance = ""
    balamt = root.find(".//LEDGERBAL/BALAMT")
    if balamt is not None and balamt.text:
        ledger_balance = balamt.text.strip()

    # Duplicate FITID detection
    fitids = [t["Reference"] for t in transactions if t.get("Reference")]
    seen: set[str] = set()
    duplicates: list[str] = []
    for fid in fitids:
        if fid in seen and fid not in duplicates:
            duplicates.append(fid)
        seen.add(fid)

    return OfxMetadata(
        dialect=dialect,
        currency=currency,
        account_id=account_id,
        account_type=account_type,
        date_start=date_start,
        date_end=date_end,
        ledger_balance=ledger_balance,
        transaction_count=len(transactions),
        duplicate_fitids=duplicates,
    )


# ─────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────


def parse_ofx(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse OFX/QBO file bytes into a bank-rec-compatible DataFrame.

    Handles both SGML v1.x and XML v2.x dialects.

    Returns DataFrame with columns:
        Date, Amount, Description, Reference, Type, Check_Number

    Raises HTTPException(400) on:
        - No <OFX> tag found
        - No transactions found
        - XML parse failure
        - DOCTYPE/ENTITY detected
    """
    # Security: block XML bombs before any parsing
    _check_xml_bombs(file_bytes)

    # Decode
    text = _decode_ofx(file_bytes, filename)

    # Validate OFX presence
    _validate_ofx_presence(text, filename)

    # Detect dialect
    dialect = _detect_dialect(text)

    # Parse to ElementTree
    if dialect == "SGML_V1":
        xml_text = _normalize_sgml_to_xml(text)
    else:
        # XML v2.x — strip any processing instructions before <OFX>
        xml_text = _strip_sgml_header(text)
        if not xml_text.strip().startswith("<?xml"):
            xml_text = '<?xml version="1.0"?>\n' + xml_text

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning("OFX XML parse failed for '%s': %s", filename, e)
        raise HTTPException(
            status_code=400,
            detail=f"The OFX/QBO file '{filename}' could not be parsed. Please verify it is a valid OFX file.",
        )

    # Extract transactions
    transactions = _extract_transactions(root)

    if not transactions:
        raise HTTPException(
            status_code=400,
            detail=f"The OFX/QBO file '{filename}' contains no transactions. "
            "Please verify the file contains bank statement data.",
        )

    # Extract metadata (non-blocking)
    metadata = _extract_metadata(root, dialect, transactions)

    # Log metadata for observability
    logger.info(
        "OFX parsed: dialect=%s, currency=%s, account=%s, type=%s, txns=%d, date_range=%s..%s, duplicates=%d",
        metadata.dialect,
        metadata.currency,
        metadata.account_id,
        metadata.account_type,
        metadata.transaction_count,
        metadata.date_start,
        metadata.date_end,
        len(metadata.duplicate_fitids),
    )

    # Build DataFrame
    df = pd.DataFrame(transactions)

    # Store metadata as DataFrame attribute for downstream access
    # (detection_notes passthrough in bank rec column detector)
    df.attrs["ofx_metadata"] = metadata

    return df
