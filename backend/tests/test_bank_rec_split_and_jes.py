"""Sprint 639 — Bank reconciliation one-to-many split + suggested JEs."""

from decimal import Decimal

from bank_reconciliation import (
    BankRecConfig,
    BankTransaction,
    LedgerTransaction,
    MatchType,
    SuggestedJEKind,
    generate_suggested_journal_entries,
    match_transactions,
)


def _bank(
    row: int, amount: str, date: str = "2026-03-15", description: str = "", reference: str = ""
) -> BankTransaction:
    return BankTransaction(
        row_number=row,
        date=date,
        description=description,
        amount=Decimal(amount),
        reference=reference,
    )


def _ledger(
    row: int, amount: str, date: str = "2026-03-15", description: str = "", reference: str = ""
) -> LedgerTransaction:
    return LedgerTransaction(
        row_number=row,
        date=date,
        description=description,
        amount=Decimal(amount),
        reference=reference,
    )


class TestSplitMatching:
    def test_one_bank_to_two_ledger_reconciles_as_split(self):
        cfg = BankRecConfig(date_tolerance_days=5)
        bank = [_bank(1, "1000.00")]
        ledger = [
            _ledger(1, "600.00"),
            _ledger(2, "400.00"),
        ]
        matches = match_transactions(bank, ledger, cfg)
        split = [m for m in matches if m.match_type == MatchType.SPLIT]
        assert len(split) == 1
        assert len(split[0].ledger_txns) == 2
        # Ledger_only residuals should be cleared because both ledgers consumed.
        assert [m for m in matches if m.match_type == MatchType.LEDGER_ONLY] == []

    def test_one_bank_to_three_ledger_reconciles(self):
        cfg = BankRecConfig(date_tolerance_days=5)
        bank = [_bank(1, "900.00")]
        ledger = [
            _ledger(1, "300.00"),
            _ledger(2, "400.00"),
            _ledger(3, "200.00"),
        ]
        matches = match_transactions(bank, ledger, cfg)
        split = [m for m in matches if m.match_type == MatchType.SPLIT]
        assert len(split) == 1
        assert len(split[0].ledger_txns) == 3

    def test_split_requires_sum_within_tolerance(self):
        cfg = BankRecConfig(amount_tolerance=0.01, date_tolerance_days=5)
        bank = [_bank(1, "1000.00")]
        ledger = [
            _ledger(1, "600.00"),
            _ledger(2, "395.00"),  # Sum = 995, off by 5
        ]
        matches = match_transactions(bank, ledger, cfg)
        assert [m for m in matches if m.match_type == MatchType.SPLIT] == []

    def test_split_respects_date_window(self):
        cfg = BankRecConfig(date_tolerance_days=1)
        bank = [_bank(1, "1000.00", date="2026-03-15")]
        ledger = [
            _ledger(1, "600.00", date="2026-03-15"),
            _ledger(2, "400.00", date="2026-04-15"),  # Outside 1-day window
        ]
        matches = match_transactions(bank, ledger, cfg)
        assert [m for m in matches if m.match_type == MatchType.SPLIT] == []

    def test_greedy_match_preferred_over_split(self):
        cfg = BankRecConfig(date_tolerance_days=5)
        bank = [_bank(1, "1000.00")]
        ledger = [_ledger(1, "1000.00")]  # Single exact match
        matches = match_transactions(bank, ledger, cfg)
        assert any(m.match_type == MatchType.MATCHED for m in matches)
        assert all(m.match_type != MatchType.SPLIT for m in matches)


class TestSuggestedJEs:
    def test_nsf_charge_classified(self):
        cfg = BankRecConfig()
        bank = [_bank(1, "-45.00", description="NSF Fee — returned item check #1234")]
        matches = match_transactions(bank, [], cfg)
        jes = generate_suggested_journal_entries(matches)
        assert len(jes) == 1
        assert jes[0].kind == SuggestedJEKind.NSF_CHARGE
        assert jes[0].debit_account.startswith("Bank Service Fees")
        assert jes[0].amount == 45.0

    def test_interest_income_classified(self):
        cfg = BankRecConfig()
        bank = [_bank(1, "12.47", description="Interest Earned")]
        matches = match_transactions(bank, [], cfg)
        jes = generate_suggested_journal_entries(matches)
        assert len(jes) == 1
        assert jes[0].kind == SuggestedJEKind.INTEREST_INCOME
        # Interest income: bank account goes up → debit Cash, credit Interest Income.
        assert jes[0].debit_account == "Cash / Bank"
        assert jes[0].credit_account == "Interest Income"

    def test_wire_fee_classified(self):
        cfg = BankRecConfig()
        bank = [_bank(1, "-35.00", description="Wire Transfer Fee")]
        matches = match_transactions(bank, [], cfg)
        jes = generate_suggested_journal_entries(matches)
        assert len(jes) == 1
        assert jes[0].kind == SuggestedJEKind.WIRE_FEE

    def test_service_charge_classified(self):
        cfg = BankRecConfig()
        bank = [_bank(1, "-15.00", description="Monthly Service Charge")]
        matches = match_transactions(bank, [], cfg)
        jes = generate_suggested_journal_entries(matches)
        assert len(jes) == 1
        assert jes[0].kind == SuggestedJEKind.SERVICE_CHARGE

    def test_unmatched_vendor_payment_is_not_classified(self):
        cfg = BankRecConfig()
        bank = [_bank(1, "-2500.00", description="Payment to Acme Corp")]
        matches = match_transactions(bank, [], cfg)
        jes = generate_suggested_journal_entries(matches)
        assert jes == []

    def test_only_bank_only_matches_are_considered(self):
        cfg = BankRecConfig()
        bank = [_bank(1, "-15.00", description="Bank Service Fee")]
        ledger = [_ledger(1, "-15.00", description="Service Fee")]  # Will match
        matches = match_transactions(bank, ledger, cfg)
        jes = generate_suggested_journal_entries(matches)
        # Matched — no suggestion needed.
        assert jes == []


class TestBankRecResultShape:
    def test_suggested_jes_serialise_on_to_dict(self):
        cfg = BankRecConfig()
        bank = [_bank(1, "-15.00", description="ATM Fee")]
        matches = match_transactions(bank, [], cfg)
        jes = generate_suggested_journal_entries(matches)
        d = jes[0].to_dict()
        assert d["kind"] == "bank_fee"
        assert "debit_account" in d
        assert "credit_account" in d
        assert "amount" in d
        assert "confidence" in d
