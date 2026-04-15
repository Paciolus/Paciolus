"""Tests for backend.shared.tb_layout — Sprint 669."""

from shared.tb_layout import TBLayoutMode, detect_tb_layout


class TestSingleDrCrLayout:
    def test_classic_one_sided_tb(self):
        """The historic default: Account / Debit / Credit."""
        result = detect_tb_layout(["Account", "Debit", "Credit"])
        assert result.mode is TBLayoutMode.SINGLE_DR_CR
        assert result.debit_column is None
        assert result.credit_column is None
        assert result.requires_confirmation is False

    def test_extended_one_sided_tb(self):
        """Account No + Account Name + DR + CR is still single."""
        result = detect_tb_layout(["Account No", "Account Name", "Account Type", "DR", "CR"])
        assert result.mode is TBLayoutMode.SINGLE_DR_CR

    def test_empty_columns(self):
        result = detect_tb_layout([])
        assert result.mode is TBLayoutMode.SINGLE_DR_CR


class TestMultiColumnAdjustedLayout:
    def test_full_three_step_pdf_extracted(self):
        """The tb_hartwell_adjusted.pdf shape with newline-laden headers."""
        cols = [
            "Acct\nNo.",
            "Account Name",
            "Beg Balance\nDebit",
            "Beg Balance\nCredit",
            "Adjustments\nDebit",
            "Adjustments\nCredit",
            "Ending Balance\nDebit",
            "Ending Balance\nCredit",
            "WP\nRef",
        ]
        result = detect_tb_layout(cols)
        assert result.mode is TBLayoutMode.MULTI_COLUMN_ADJUSTED
        assert result.debit_column == "Ending Balance\nDebit"
        assert result.credit_column == "Ending Balance\nCredit"
        # Both Beginning and Adjustments pairs should be in supplementary
        sup_set = {col for pair in result.supplementary_pairs for col in pair}
        assert "Beg Balance\nDebit" in sup_set
        assert "Beg Balance\nCredit" in sup_set
        assert "Adjustments\nDebit" in sup_set
        assert "Adjustments\nCredit" in sup_set

    def test_two_step_beginning_ending(self):
        """Two steps (Beginning + Ending) without Adjustments."""
        cols = ["Account", "Beg Debit", "Beg Credit", "End Debit", "End Credit"]
        result = detect_tb_layout(cols)
        assert result.mode is TBLayoutMode.MULTI_COLUMN_ADJUSTED
        assert result.debit_column == "End Debit"
        assert result.credit_column == "End Credit"

    def test_only_one_pair_falls_back_to_single(self):
        """A single pair (no multi-column triplet) is still single_dr_cr."""
        cols = ["Account", "Beg Balance Debit", "Beg Balance Credit"]
        # Only 1 debit + 1 credit column → can't be multi-column
        result = detect_tb_layout(cols)
        assert result.mode is TBLayoutMode.SINGLE_DR_CR


class TestNetBalanceLayout:
    def test_net_balance_with_dr_cr_indicator(self):
        """The tb_hartwell.docx shape."""
        cols = ["Account Name", "Category", "Net Balance (USD)", "Dr / Cr"]
        result = detect_tb_layout(cols)
        assert result.mode is TBLayoutMode.NET_BALANCE_WITH_INDICATOR
        assert result.debit_column == "Net Balance (USD)"
        assert result.credit_column == "Dr / Cr"
        assert result.indicator_column == "Dr / Cr"
        assert result.requires_confirmation is True

    def test_balance_with_sign_indicator(self):
        cols = ["Account", "Balance", "Sign"]
        result = detect_tb_layout(cols)
        assert result.mode is TBLayoutMode.NET_BALANCE_WITH_INDICATOR

    def test_signed_balance_only_no_indicator_falls_back(self):
        """No indicator column → not net-balance layout."""
        cols = ["Account", "Signed Balance"]
        result = detect_tb_layout(cols)
        # Falls through to single_dr_cr because there's no indicator pair
        assert result.mode is TBLayoutMode.SINGLE_DR_CR

    def test_multi_column_takes_precedence_over_net_balance(self):
        """A file with multiple Debit/Credit columns AND a Balance column
        should be classified as multi-column adjusted, not net-balance.
        """
        cols = [
            "Account",
            "Beg Debit",
            "Beg Credit",
            "Ending Debit",
            "Ending Credit",
            "Net Balance",
        ]
        result = detect_tb_layout(cols)
        assert result.mode is TBLayoutMode.MULTI_COLUMN_ADJUSTED
