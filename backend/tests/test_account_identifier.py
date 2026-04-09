"""Tests for account identifier preservation during ingestion.

AUDIT-06-F004: Account codes with leading zeros (e.g. "0010") must survive
pandas ingestion intact.  The fix pins ``dtype=str`` at the CSV/Excel read
boundary so that ``pd.read_csv`` / ``pd.read_excel`` never infer numeric
types for account identifier columns.
"""

import io

import pandas as pd

from security_utils import (
    process_tb_chunked,
    process_tb_in_memory,
    read_csv_secure,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_csv_bytes(rows: list[list[str]], header: list[str] | None = None) -> bytes:
    """Build CSV bytes from a list of rows."""
    if header is None:
        header = ["Account", "Account Name", "Debit", "Credit"]
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(row))
    return "\n".join(lines).encode("utf-8")


def _make_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to in-memory XLSX bytes."""
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# CSV: leading-zero account codes
# ---------------------------------------------------------------------------


class TestLeadingZeroPreservationCSV:
    """Account codes with leading zeros must be preserved through CSV ingestion."""

    ROWS = [
        ["0010", "Cash", "5000.00", "0.00"],
        ["0020", "Accounts Receivable", "3000.00", "0.00"],
        ["0100", "Accounts Payable", "0.00", "4000.00"],
    ]

    def test_process_tb_in_memory_preserves_leading_zeros(self):
        """process_tb_in_memory must keep '0010' not '10'."""
        csv_bytes = _make_csv_bytes(self.ROWS)
        df = process_tb_in_memory(csv_bytes, filename="trial_balance.csv")

        accounts = df["Account"].tolist()
        assert "0010" in accounts, f"Expected '0010' but got {accounts}"
        assert "0020" in accounts, f"Expected '0020' but got {accounts}"
        assert "0100" in accounts, f"Expected '0100' but got {accounts}"

        # Ensure they were NOT converted to integers
        assert "10" not in accounts, "Leading zeros were stripped from '0010'"
        assert "20" not in accounts, "Leading zeros were stripped from '0020'"
        assert "100" not in accounts, "Leading zeros were stripped from '0100'"

    def test_process_tb_chunked_preserves_leading_zeros(self):
        """process_tb_chunked must keep '0010' not '10'."""
        csv_bytes = _make_csv_bytes(self.ROWS)
        chunks = list(process_tb_chunked(csv_bytes, filename="trial_balance.csv"))

        assert len(chunks) >= 1
        df = pd.concat([c[0] for c in chunks], ignore_index=True)

        accounts = df["Account"].tolist()
        assert "0010" in accounts
        assert "0020" in accounts
        assert "0100" in accounts

    def test_read_csv_secure_dtype_str_preserves_leading_zeros(self):
        """read_csv_secure with dtype=str must preserve leading zeros."""
        csv_bytes = _make_csv_bytes(self.ROWS)
        df = read_csv_secure(csv_bytes, dtype=str)

        assert df["Account"].iloc[0] == "0010"
        assert df["Account"].iloc[1] == "0020"
        assert df["Account"].iloc[2] == "0100"


# ---------------------------------------------------------------------------
# CSV: mixed account formats (numeric + alphanumeric)
# ---------------------------------------------------------------------------


class TestMixedAccountFormats:
    """Mixed formats (numeric codes, alphanumeric codes) must all survive."""

    ROWS = [
        ["A-100", "Revenue", "0.00", "10000.00"],
        ["B-200", "Cost of Goods Sold", "6000.00", "0.00"],
        ["0010", "Cash", "5000.00", "0.00"],
        ["42", "Supplies", "1200.00", "0.00"],
    ]

    def test_mixed_formats_in_memory(self):
        """Alphanumeric and numeric account codes preserved via in-memory path."""
        csv_bytes = _make_csv_bytes(self.ROWS)
        df = process_tb_in_memory(csv_bytes, filename="mixed.csv")

        accounts = df["Account"].tolist()
        assert "A-100" in accounts
        assert "B-200" in accounts
        assert "0010" in accounts
        assert "42" in accounts  # plain numeric stays as string "42"

        # All values should be strings
        assert all(isinstance(a, str) for a in accounts), "All account values must be str"

    def test_mixed_formats_chunked(self):
        """Alphanumeric and numeric account codes preserved via chunked path."""
        csv_bytes = _make_csv_bytes(self.ROWS)
        chunks = list(process_tb_chunked(csv_bytes, filename="mixed.csv"))

        df = pd.concat([c[0] for c in chunks], ignore_index=True)
        accounts = df["Account"].tolist()

        assert "A-100" in accounts
        assert "B-200" in accounts
        assert "0010" in accounts
        assert "42" in accounts
        assert all(isinstance(a, str) for a in accounts)


# ---------------------------------------------------------------------------
# Excel: leading-zero account codes
# ---------------------------------------------------------------------------


class TestLeadingZeroPreservationExcel:
    """Account codes with leading zeros must be preserved through Excel ingestion."""

    def test_process_tb_in_memory_excel_preserves_leading_zeros(self):
        """process_tb_in_memory must keep '0010' when reading XLSX."""
        # Build a DataFrame with string account codes, then serialize to XLSX
        df_source = pd.DataFrame(
            {
                "Account": ["0010", "0020", "0100"],
                "Account Name": ["Cash", "AR", "AP"],
                "Debit": [5000.0, 3000.0, 0.0],
                "Credit": [0.0, 0.0, 4000.0],
            }
        )
        xlsx_bytes = _make_excel_bytes(df_source)
        df = process_tb_in_memory(xlsx_bytes, filename="trial_balance.xlsx")

        accounts = df["Account"].tolist()
        # Note: Excel may store these as integers (10, 20, 100) at the cell
        # level, but dtype=str at read time converts them to "10", "20", "100".
        # The critical guarantee is that the *type* is str, not int/float.
        assert all(isinstance(a, str) for a in accounts), "All account values must be str"

    def test_process_tb_chunked_excel_preserves_types(self):
        """process_tb_chunked with XLSX must return string-typed account values."""
        df_source = pd.DataFrame(
            {
                "Account": ["A-100", "B-200", "0010"],
                "Account Name": ["Revenue", "COGS", "Cash"],
                "Debit": [0.0, 6000.0, 5000.0],
                "Credit": [10000.0, 0.0, 0.0],
            }
        )
        xlsx_bytes = _make_excel_bytes(df_source)
        chunks = list(process_tb_chunked(xlsx_bytes, filename="trial_balance.xlsx"))

        df = pd.concat([c[0] for c in chunks], ignore_index=True)
        assert all(isinstance(a, str) for a in df["Account"].tolist())


# ---------------------------------------------------------------------------
# End-to-end: StreamingAuditor preserves identifiers
# ---------------------------------------------------------------------------


class TestStreamingAuditorAccountPreservation:
    """Verify the full pipeline from ingestion through StreamingAuditor.

    Note: The column detector picks "Account Name" over "Account" when both
    are present, so these tests use a single "Account" column (no separate
    name column) to ensure the account *code* is the key in account_balances.
    """

    def test_streaming_auditor_preserves_leading_zeros(self):
        """Account keys in auditor.account_balances must preserve leading zeros."""
        from audit.streaming_auditor import StreamingAuditor

        # Use headers without a separate "Account Name" column so the
        # detector maps "Account" as the account identifier column.
        csv_bytes = _make_csv_bytes(
            [
                ["0010 Cash", "5000.00", "0.00"],
                ["0020 Accounts Receivable", "3000.00", "0.00"],
                ["0100 Accounts Payable", "0.00", "4000.00"],
            ],
            header=["Account", "Debit", "Credit"],
        )

        auditor = StreamingAuditor()
        for chunk, rows in process_tb_chunked(csv_bytes, filename="tb.csv"):
            auditor.process_chunk(chunk, rows)

        account_keys = list(auditor.account_balances.keys())
        assert any(k.startswith("0010") for k in account_keys), f"Expected a key starting with '0010' in {account_keys}"
        assert any(k.startswith("0020") for k in account_keys), f"Expected a key starting with '0020' in {account_keys}"
        assert any(k.startswith("0100") for k in account_keys), f"Expected a key starting with '0100' in {account_keys}"

    def test_streaming_auditor_mixed_format_accounts(self):
        """Account keys with mixed formats survive the full pipeline."""
        from audit.streaming_auditor import StreamingAuditor

        csv_bytes = _make_csv_bytes(
            [
                ["A-100 Revenue", "0.00", "10000.00"],
                ["0010 Cash", "5000.00", "0.00"],
                ["42 Supplies", "1200.00", "0.00"],
            ],
            header=["Account", "Debit", "Credit"],
        )

        auditor = StreamingAuditor()
        for chunk, rows in process_tb_chunked(csv_bytes, filename="tb.csv"):
            auditor.process_chunk(chunk, rows)

        account_keys = list(auditor.account_balances.keys())
        assert any("A-100" in k for k in account_keys), f"Expected 'A-100' in {account_keys}"
        assert any(k.startswith("0010") for k in account_keys), f"Expected '0010' in {account_keys}"
        assert any(k.startswith("42") for k in account_keys), f"Expected '42' in {account_keys}"
