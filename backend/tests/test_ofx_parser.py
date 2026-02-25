"""
Tests for shared.ofx_parser — OFX/QBO File Parser.

Tests cover:
- Dialect detection (SGML v1.x vs XML v2.x)
- SGML normalization (leaf tag closing, header stripping)
- OFX date parsing (YYYYMMDD, HHmmss, timezone, invalid)
- Transaction extraction (single/multiple, credit card path, NAME+MEMO, amounts)
- Duplicate FITID detection
- Metadata extraction (currency, account, date range, balance)
- End-to-end parse_ofx (full SGML doc, full XML doc, column names, dtypes)
- Security defenses (no OFX tag, entity expansion, DOCTYPE, binary)
- Encoding (UTF-8, Latin-1, CHARSET header)
"""

import pytest
from fastapi import HTTPException

from shared.ofx_parser import (
    OfxMetadata,
    _check_xml_bombs,
    _detect_dialect,
    _extract_metadata,
    _extract_transactions,
    _normalize_sgml_to_xml,
    _parse_ofx_date,
    _strip_sgml_header,
    _validate_ofx_presence,
    parse_ofx,
)

# =============================================================================
# FIXTURES: Minimal OFX documents
# =============================================================================

SGML_V1_DOC = """\
OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<DTSERVER>20240115120000
<LANGUAGE>ENG
</SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
<STMTTRNRS>
<TRNUID>1001
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<STMTRS>
<CURDEF>USD
<BANKACCTFROM>
<BANKID>021000021
<ACCTID>123456789012
<ACCTTYPE>CHECKING
</BANKACCTFROM>
<BANKTRANLIST>
<DTSTART>20240101
<DTEND>20240131
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20240115
<TRNAMT>-45.99
<FITID>2024011501
<NAME>AMAZON MARKETPLACE
<MEMO>Purchase
</STMTTRN>
<STMTTRN>
<TRNTYPE>CREDIT
<DTPOSTED>20240120
<TRNAMT>3500.00
<FITID>2024012001
<NAME>PAYROLL DEPOSIT
<CHECKNUM>10042
</STMTTRN>
</BANKTRANLIST>
<LEDGERBAL>
<BALAMT>12543.21
<DTASOF>20240131
</LEDGERBAL>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""

XML_V2_DOC = """\
<?xml version="1.0" encoding="UTF-8"?>
<?OFX OFXHEADER="200" VERSION="220" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="NONE"?>
<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>
<DTSERVER>20240115120000</DTSERVER>
<LANGUAGE>ENG</LANGUAGE>
</SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
<STMTTRNRS>
<TRNUID>1001</TRNUID>
<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>
<STMTRS>
<CURDEF>USD</CURDEF>
<BANKACCTFROM>
<BANKID>021000021</BANKID>
<ACCTID>9876543210</ACCTID>
<ACCTTYPE>SAVINGS</ACCTTYPE>
</BANKACCTFROM>
<BANKTRANLIST>
<DTSTART>20240101</DTSTART>
<DTEND>20240131</DTEND>
<STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20240110</DTPOSTED>
<TRNAMT>-120.50</TRNAMT>
<FITID>XML20240110A</FITID>
<NAME>ELECTRIC COMPANY</NAME>
<MEMO>Monthly bill</MEMO>
</STMTTRN>
</BANKTRANLIST>
<LEDGERBAL>
<BALAMT>8750.00</BALAMT>
<DTASOF>20240131</DTASOF>
</LEDGERBAL>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""

CC_XML_DOC = """\
<?xml version="1.0" encoding="UTF-8"?>
<OFX>
<SIGNONMSGSRSV1>
<SONRS><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>
<DTSERVER>20240201</DTSERVER><LANGUAGE>ENG</LANGUAGE></SONRS>
</SIGNONMSGSRSV1>
<CREDITCARDMSGSRSV1>
<CCSTMTTRNRS>
<TRNUID>5001</TRNUID>
<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>
<CCSTMTRS>
<CURDEF>CAD</CURDEF>
<CCACCTFROM>
<ACCTID>4111222233334444</ACCTID>
</CCACCTFROM>
<BANKTRANLIST>
<DTSTART>20240101</DTSTART>
<DTEND>20240131</DTEND>
<STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20240105</DTPOSTED>
<TRNAMT>-25.00</TRNAMT>
<FITID>CC20240105A</FITID>
<NAME>COFFEE SHOP</NAME>
</STMTTRN>
<STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20240108</DTPOSTED>
<TRNAMT>-150.75</TRNAMT>
<FITID>CC20240108B</FITID>
<NAME>GROCERY STORE</NAME>
<MEMO>Weekly groceries</MEMO>
</STMTTRN>
</BANKTRANLIST>
<LEDGERBAL>
<BALAMT>-1250.50</BALAMT>
<DTASOF>20240131</DTASOF>
</LEDGERBAL>
</CCSTMTRS>
</CCSTMTTRNRS>
</CREDITCARDMSGSRSV1>
</OFX>
"""


# =============================================================================
# Dialect Detection
# =============================================================================


class TestOfxDialectDetection:
    """SGML vs XML dialect detection."""

    def test_sgml_detected(self):
        assert _detect_dialect(SGML_V1_DOC) == "SGML_V1"

    def test_xml_detected(self):
        assert _detect_dialect(XML_V2_DOC) == "XML_V2"

    def test_no_xml_declaration_is_sgml(self):
        assert _detect_dialect("<OFX><BODY>test</BODY></OFX>") == "SGML_V1"

    def test_xml_declaration_case_insensitive(self):
        # Our detector lowercases, so both cases match as XML
        assert _detect_dialect('<?XML version="1.0"?><OFX/>') == "XML_V2"
        assert _detect_dialect('<?xml version="1.0"?><OFX/>') == "XML_V2"

    def test_non_ofx_content_defaults_sgml(self):
        assert _detect_dialect("This is just plain text") == "SGML_V1"


class TestOfxPresenceValidation:
    """Validation that <OFX> tag exists."""

    def test_valid_ofx_passes(self):
        _validate_ofx_presence(SGML_V1_DOC, "test.qbo")  # Should not raise

    def test_no_ofx_tag_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_ofx_presence("This is not an OFX file at all", "bad.qbo")
        assert exc_info.value.status_code == 400
        assert "No <OFX> tag" in exc_info.value.detail

    def test_ofx_tag_case_insensitive(self):
        # <ofx> should be found (we search uppercase)
        _validate_ofx_presence("<ofx><body/></ofx>", "test.ofx")

    def test_empty_content_raises(self):
        with pytest.raises(HTTPException):
            _validate_ofx_presence("", "empty.ofx")


# =============================================================================
# SGML Normalization
# =============================================================================


class TestSgmlNormalization:
    """SGML v1.x to XML normalization."""

    def test_header_stripped(self):
        result = _strip_sgml_header(SGML_V1_DOC)
        assert result.startswith("<OFX>")
        assert "OFXHEADER" not in result

    def test_header_stripped_preserves_content(self):
        result = _strip_sgml_header(SGML_V1_DOC)
        assert "AMAZON MARKETPLACE" in result
        assert "BANKMSGSRSV1" in result

    def test_leaf_tags_closed(self):
        sgml = "<TAG1>value1\n<TAG2>value2\n"
        normalized = _normalize_sgml_to_xml("<OFX>\n" + sgml + "</OFX>")
        assert "<TAG1>value1</TAG1>" in normalized
        assert "<TAG2>value2</TAG2>" in normalized

    def test_container_tags_preserved(self):
        """Container tags (with child elements) should not get double-closed."""
        sgml = "<PARENT>\n<CHILD>value\n</PARENT>\n"
        normalized = _normalize_sgml_to_xml("<OFX>\n" + sgml + "</OFX>")
        assert "<CHILD>value</CHILD>" in normalized
        assert "<PARENT>" in normalized

    def test_empty_leaf_not_affected(self):
        """Tags without content should not be modified by leaf regex."""
        sgml = "<EMPTY>\n<NEXT>data\n"
        normalized = _normalize_sgml_to_xml("<OFX>\n" + sgml + "</OFX>")
        # EMPTY has no inline content, so regex won't match it
        assert "<NEXT>data</NEXT>" in normalized

    def test_whitespace_in_values_preserved(self):
        sgml = "<NAME>JOHN DOE CORP\n"
        normalized = _normalize_sgml_to_xml("<OFX>\n" + sgml + "</OFX>")
        assert "<NAME>JOHN DOE CORP</NAME>" in normalized

    def test_xml_declaration_added(self):
        result = _normalize_sgml_to_xml("<OFX></OFX>")
        assert '<?xml version="1.0"?>' in result


# =============================================================================
# Date Parsing
# =============================================================================


class TestOfxDateParsing:
    """OFX date format to ISO conversion."""

    def test_basic_date(self):
        assert _parse_ofx_date("20240115") == "2024-01-15"

    def test_date_with_time(self):
        assert _parse_ofx_date("20240115120000") == "2024-01-15"

    def test_date_with_milliseconds(self):
        assert _parse_ofx_date("20240115120000.000") == "2024-01-15"

    def test_date_with_timezone(self):
        assert _parse_ofx_date("20240115120000[-5:EST]") == "2024-01-15"

    def test_date_with_positive_timezone(self):
        assert _parse_ofx_date("20240115120000[+1:CET]") == "2024-01-15"

    def test_empty_date(self):
        assert _parse_ofx_date("") == ""
        assert _parse_ofx_date(None) == ""

    def test_short_date_passthrough(self):
        assert _parse_ofx_date("2024") == "2024"

    def test_invalid_month(self):
        # Month 13 is invalid, should passthrough
        assert _parse_ofx_date("20241301") == "20241301"

    def test_invalid_day(self):
        # Day 32 is invalid, should passthrough
        assert _parse_ofx_date("20240132") == "20240132"


# =============================================================================
# Transaction Extraction
# =============================================================================


class TestTransactionExtraction:
    """Transaction extraction from parsed ElementTree."""

    def _parse_xml(self, text: str):
        """Helper to parse XML text into ElementTree root."""
        import xml.etree.ElementTree as ET

        return ET.fromstring(text)

    def test_single_bank_transaction(self):
        root = self._parse_xml(XML_V2_DOC)
        txns = _extract_transactions(root)
        assert len(txns) == 1
        assert txns[0]["Date"] == "2024-01-10"
        assert txns[0]["Amount"] == -120.50
        assert "ELECTRIC COMPANY" in txns[0]["Description"]
        assert txns[0]["Reference"] == "XML20240110A"

    def test_name_and_memo_combined(self):
        root = self._parse_xml(XML_V2_DOC)
        txns = _extract_transactions(root)
        assert txns[0]["Description"] == "ELECTRIC COMPANY - Monthly bill"

    def test_credit_card_path(self):
        root = self._parse_xml(CC_XML_DOC)
        txns = _extract_transactions(root)
        assert len(txns) == 2
        assert txns[0]["Description"] == "COFFEE SHOP"
        assert txns[1]["Amount"] == -150.75

    def test_checknum_extracted(self):
        """CHECKNUM should be extracted when present."""
        xml = """\
<?xml version="1.0"?>
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><BANKTRANLIST>
<STMTTRN>
<TRNTYPE>CHECK</TRNTYPE>
<DTPOSTED>20240115</DTPOSTED>
<TRNAMT>-500.00</TRNAMT>
<FITID>CHK001</FITID>
<NAME>RENT PAYMENT</NAME>
<CHECKNUM>1042</CHECKNUM>
</STMTTRN>
</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>
"""
        root = self._parse_xml(xml)
        txns = _extract_transactions(root)
        assert len(txns) == 1
        assert txns[0]["Check_Number"] == "1042"

    def test_amount_parsing(self):
        root = self._parse_xml(XML_V2_DOC)
        txns = _extract_transactions(root)
        assert isinstance(txns[0]["Amount"], float)

    def test_invalid_amount_becomes_none(self):
        xml = """\
<?xml version="1.0"?>
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20240115</DTPOSTED>
<TRNAMT>INVALID</TRNAMT>
<FITID>BAD001</FITID>
<NAME>BAD TXN</NAME>
</STMTTRN>
</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>
"""
        root = self._parse_xml(xml)
        txns = _extract_transactions(root)
        assert txns[0]["Amount"] is None

    def test_no_transactions_returns_empty(self):
        xml = '<?xml version="1.0"?><OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><BANKTRANLIST></BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>'
        root = self._parse_xml(xml)
        txns = _extract_transactions(root)
        assert txns == []

    def test_name_only_no_memo(self):
        """Transaction with NAME but no MEMO should use NAME as description."""
        root = self._parse_xml(CC_XML_DOC)
        txns = _extract_transactions(root)
        assert txns[0]["Description"] == "COFFEE SHOP"  # No memo

    def test_memo_only_no_name(self):
        xml = """\
<?xml version="1.0"?>
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20240115</DTPOSTED>
<TRNAMT>-10.00</TRNAMT>
<FITID>M001</FITID>
<MEMO>Service charge</MEMO>
</STMTTRN>
</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>
"""
        root = self._parse_xml(xml)
        txns = _extract_transactions(root)
        assert txns[0]["Description"] == "Service charge"


# =============================================================================
# Duplicate FITID Detection
# =============================================================================


class TestDuplicateFitidDetection:
    """Duplicate FITID detection in metadata."""

    def test_unique_fitids_no_duplicates(self):
        txns = [
            {"Reference": "A001"},
            {"Reference": "A002"},
            {"Reference": "A003"},
        ]
        metadata = _extract_metadata(self._empty_root(), "SGML_V1", txns)
        assert metadata.duplicate_fitids == []

    def test_duplicate_fitids_detected(self):
        txns = [
            {"Reference": "A001"},
            {"Reference": "A001"},
            {"Reference": "A002"},
        ]
        metadata = _extract_metadata(self._empty_root(), "SGML_V1", txns)
        assert metadata.duplicate_fitids == ["A001"]

    def test_multiple_duplicates(self):
        txns = [
            {"Reference": "A001"},
            {"Reference": "A001"},
            {"Reference": "A002"},
            {"Reference": "A002"},
        ]
        metadata = _extract_metadata(self._empty_root(), "SGML_V1", txns)
        assert set(metadata.duplicate_fitids) == {"A001", "A002"}

    def test_empty_fitids_ignored(self):
        txns = [
            {"Reference": ""},
            {"Reference": ""},
            {"Reference": "A001"},
        ]
        metadata = _extract_metadata(self._empty_root(), "SGML_V1", txns)
        # Empty strings are falsy, filtered out before duplicate check
        assert metadata.duplicate_fitids == []

    def _empty_root(self):
        import xml.etree.ElementTree as ET

        return ET.fromstring("<OFX/>")


# =============================================================================
# Metadata Extraction
# =============================================================================


class TestMetadataExtraction:
    """Metadata extraction from OFX tree."""

    def test_currency_extracted(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring(XML_V2_DOC)
        txns = _extract_transactions(root)
        metadata = _extract_metadata(root, "XML_V2", txns)
        assert metadata.currency == "USD"

    def test_account_id_masked(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring(XML_V2_DOC)
        txns = _extract_transactions(root)
        metadata = _extract_metadata(root, "XML_V2", txns)
        assert metadata.account_id == "****3210"

    def test_account_type_extracted(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring(XML_V2_DOC)
        txns = _extract_transactions(root)
        metadata = _extract_metadata(root, "XML_V2", txns)
        assert metadata.account_type == "SAVINGS"

    def test_credit_card_account_type(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring(CC_XML_DOC)
        txns = _extract_transactions(root)
        metadata = _extract_metadata(root, "XML_V2", txns)
        assert metadata.account_type == "CREDITCARD"
        assert metadata.currency == "CAD"

    def test_date_range_extracted(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring(XML_V2_DOC)
        txns = _extract_transactions(root)
        metadata = _extract_metadata(root, "XML_V2", txns)
        assert metadata.date_start == "2024-01-01"
        assert metadata.date_end == "2024-01-31"

    def test_ledger_balance_extracted(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring(XML_V2_DOC)
        txns = _extract_transactions(root)
        metadata = _extract_metadata(root, "XML_V2", txns)
        assert metadata.ledger_balance == "8750.00"

    def test_transaction_count(self):
        import xml.etree.ElementTree as ET

        root = ET.fromstring(CC_XML_DOC)
        txns = _extract_transactions(root)
        metadata = _extract_metadata(root, "XML_V2", txns)
        assert metadata.transaction_count == 2

    def test_metadata_is_frozen(self):
        metadata = OfxMetadata(
            dialect="XML_V2",
            currency="USD",
            account_id="****1234",
            account_type="CHECKING",
            date_start="2024-01-01",
            date_end="2024-01-31",
            ledger_balance="1000.00",
            transaction_count=5,
        )
        with pytest.raises(AttributeError):
            metadata.currency = "EUR"  # type: ignore[misc]


# =============================================================================
# End-to-End: parse_ofx
# =============================================================================


class TestParseOfxEndToEnd:
    """Full parse_ofx entry point tests."""

    def test_sgml_v1_full_parse(self):
        df = parse_ofx(SGML_V1_DOC.encode("utf-8"), "statement.qbo")
        assert len(df) == 2
        assert list(df.columns) == ["Date", "Amount", "Description", "Reference", "Type", "Check_Number"]

    def test_sgml_column_values(self):
        df = parse_ofx(SGML_V1_DOC.encode("utf-8"), "statement.qbo")
        assert df.iloc[0]["Date"] == "2024-01-15"
        assert df.iloc[0]["Amount"] == -45.99
        assert "AMAZON" in df.iloc[0]["Description"]
        assert df.iloc[0]["Reference"] == "2024011501"

    def test_sgml_second_transaction(self):
        df = parse_ofx(SGML_V1_DOC.encode("utf-8"), "statement.qbo")
        assert df.iloc[1]["Amount"] == 3500.00
        assert df.iloc[1]["Check_Number"] == "10042"

    def test_xml_v2_full_parse(self):
        df = parse_ofx(XML_V2_DOC.encode("utf-8"), "statement.ofx")
        assert len(df) == 1
        assert df.iloc[0]["Amount"] == -120.50

    def test_credit_card_parse(self):
        df = parse_ofx(CC_XML_DOC.encode("utf-8"), "cc_statement.qbo")
        assert len(df) == 2

    def test_metadata_attached(self):
        df = parse_ofx(XML_V2_DOC.encode("utf-8"), "statement.ofx")
        metadata = df.attrs.get("ofx_metadata")
        assert metadata is not None
        assert isinstance(metadata, OfxMetadata)
        assert metadata.dialect == "XML_V2"
        assert metadata.currency == "USD"

    def test_no_transactions_raises(self):
        xml = '<?xml version="1.0"?><OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><BANKTRANLIST></BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>'
        with pytest.raises(HTTPException) as exc_info:
            parse_ofx(xml.encode("utf-8"), "empty.ofx")
        assert exc_info.value.status_code == 400
        assert "no transactions" in exc_info.value.detail.lower()

    def test_latin1_encoding(self):
        """Latin-1 encoded OFX should parse via encoding fallback."""
        sgml = SGML_V1_DOC.replace("AMAZON MARKETPLACE", "CAF\u00c9 SHOP")
        df = parse_ofx(sgml.encode("latin-1"), "latin1.qbo")
        assert len(df) == 2
        assert "CAF" in df.iloc[0]["Description"]


# =============================================================================
# Security Defenses
# =============================================================================


class TestOfxSecurityDefenses:
    """Security defenses in OFX parser."""

    def test_no_ofx_tag_rejected(self):
        content = b"This is not an OFX file at all. Just random text."
        with pytest.raises(HTTPException) as exc_info:
            parse_ofx(content, "not_ofx.qbo")
        assert exc_info.value.status_code == 400
        assert "No <OFX> tag" in exc_info.value.detail

    def test_entity_expansion_blocked(self):
        xml = b'<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe "boom">]><OFX>&xxe;</OFX>'
        with pytest.raises(HTTPException) as exc_info:
            parse_ofx(xml, "bomb.ofx")
        assert exc_info.value.status_code == 400
        assert "prohibited XML" in exc_info.value.detail

    def test_doctype_blocked(self):
        xml = b'<?xml version="1.0"?><!DOCTYPE foo SYSTEM "http://evil.com"><OFX></OFX>'
        with pytest.raises(HTTPException) as exc_info:
            parse_ofx(xml, "xxe.ofx")
        assert exc_info.value.status_code == 400
        assert "prohibited XML" in exc_info.value.detail

    def test_binary_content_rejected(self):
        content = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08"
        with pytest.raises(HTTPException) as exc_info:
            parse_ofx(content, "binary.qbo")
        assert exc_info.value.status_code == 400

    def test_check_xml_bombs_direct(self):
        with pytest.raises(HTTPException):
            _check_xml_bombs(b"<!DOCTYPE foo>")
        with pytest.raises(HTTPException):
            _check_xml_bombs(b"<!ENTITY x>")

    def test_clean_content_passes_bomb_check(self):
        _check_xml_bombs(b"<?xml version='1.0'?><OFX></OFX>")  # Should not raise

    def test_malformed_xml_rejected(self):
        content = b"<OFX><BROKEN><TAG>value</OFX>"
        with pytest.raises(HTTPException) as exc_info:
            parse_ofx(content, "malformed.ofx")
        assert exc_info.value.status_code == 400
        assert "could not be parsed" in exc_info.value.detail


# =============================================================================
# Encoding Edge Cases
# =============================================================================


class TestOfxEncoding:
    """Encoding detection and fallback."""

    def test_utf8_bom(self):
        """UTF-8 with BOM should parse correctly."""
        content = b"\xef\xbb\xbf" + XML_V2_DOC.encode("utf-8")
        df = parse_ofx(content, "bom.ofx")
        assert len(df) == 1

    def test_cp1252_charset_header(self):
        """SGML with CHARSET:1252 should decode correctly."""
        # The fixture already has CHARSET:1252 in header
        content = SGML_V1_DOC.encode("cp1252")
        df = parse_ofx(content, "cp1252.qbo")
        assert len(df) == 2
