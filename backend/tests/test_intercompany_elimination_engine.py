"""Sprint 637 — Multi-Entity Intercompany Elimination tests."""

from decimal import Decimal

from intercompany_elimination_engine import (
    EntityAccount,
    EntityTrialBalance,
    IntercompanyConfig,
    IntercompanyDirection,
    IntercompanyInputError,
    MismatchKind,
    run_intercompany_elimination,
)


def _parent_with_receivable(amount: str = "10000") -> EntityTrialBalance:
    return EntityTrialBalance(
        entity_id="parent",
        entity_name="Parent Corp",
        accounts=[
            EntityAccount(account="1000 Cash", debit=Decimal("50000")),
            EntityAccount(
                account="1500 Due from Subsidiary Beta",
                debit=Decimal(amount),
                counterparty_entity="subsidiary",
            ),
            EntityAccount(account="3000 Equity", credit=Decimal(amount) + Decimal("50000")),
        ],
    )


def _subsidiary_with_payable(amount: str = "10000") -> EntityTrialBalance:
    return EntityTrialBalance(
        entity_id="subsidiary",
        entity_name="Subsidiary Beta",
        accounts=[
            EntityAccount(account="1000 Cash", debit=Decimal("20000")),
            EntityAccount(
                account="2500 Due to Parent",
                credit=Decimal(amount),
                counterparty_entity="parent",
            ),
            EntityAccount(account="3000 Equity", credit=Decimal("10000")),
        ],
    )


class TestHappyPath:
    def test_matching_pair_reconciles(self):
        cfg = IntercompanyConfig(
            entities=[_parent_with_receivable(), _subsidiary_with_payable()],
        )
        result = run_intercompany_elimination(cfg)
        assert len(result.pairs) == 1
        assert result.pairs[0].reconciles is True
        assert result.mismatches == []
        assert result.summary["consolidation_complete"] is True

    def test_reconciling_pair_produces_elimination_je(self):
        cfg = IntercompanyConfig(
            entities=[_parent_with_receivable(), _subsidiary_with_payable()],
        )
        result = run_intercompany_elimination(cfg)
        assert len(result.elimination_journal_entries) == 1
        je = result.elimination_journal_entries[0]
        assert je.amount == Decimal("10000.00")
        assert je.debit_entity == "subsidiary"  # The payable gets debited (eliminated)
        assert je.credit_entity == "parent"  # The receivable gets credited (eliminated)


class TestDirectionParsing:
    def test_due_from_is_receivable(self):
        tb = EntityTrialBalance(
            entity_id="a",
            entity_name="A",
            accounts=[
                EntityAccount(
                    account="Due from B",
                    debit=Decimal("100"),
                    counterparty_entity="b",
                )
            ],
        )
        tb_other = EntityTrialBalance(
            entity_id="b",
            entity_name="B",
            accounts=[
                EntityAccount(
                    account="Due to A",
                    credit=Decimal("100"),
                    counterparty_entity="a",
                )
            ],
        )
        cfg = IntercompanyConfig(entities=[tb, tb_other])
        result = run_intercompany_elimination(cfg)
        assert len(result.intercompany_lines) == 2
        directions = {line.direction for line in result.intercompany_lines}
        assert IntercompanyDirection.RECEIVABLE in directions
        assert IntercompanyDirection.PAYABLE in directions


class TestMismatches:
    def test_no_reciprocal_fires(self):
        parent = _parent_with_receivable("10000")
        sub = EntityTrialBalance(
            entity_id="subsidiary",
            entity_name="Subsidiary Beta",
            accounts=[EntityAccount(account="1000 Cash", debit=Decimal("20000"))],
        )
        cfg = IntercompanyConfig(entities=[parent, sub])
        result = run_intercompany_elimination(cfg)
        kinds = {m.kind for m in result.mismatches}
        assert MismatchKind.NO_RECIPROCAL in kinds
        assert result.summary["consolidation_complete"] is False

    def test_amount_mismatch_fires_when_residual_exceeds_tolerance(self):
        parent = _parent_with_receivable("10000")
        sub = _subsidiary_with_payable("9500")  # $500 residual
        cfg = IntercompanyConfig(entities=[parent, sub])
        result = run_intercompany_elimination(cfg)
        kinds = {m.kind for m in result.mismatches}
        assert MismatchKind.AMOUNT_MISMATCH in kinds
        assert result.pairs[0].reconciles is False

    def test_tolerance_absorbs_small_residual(self):
        parent = _parent_with_receivable("10000")
        # $0.50 residual — within $1.00 tolerance.
        sub = _subsidiary_with_payable("9999.50")
        cfg = IntercompanyConfig(entities=[parent, sub])
        result = run_intercompany_elimination(cfg)
        amount_mismatches = [m for m in result.mismatches if m.kind == MismatchKind.AMOUNT_MISMATCH]
        assert amount_mismatches == []
        assert result.pairs[0].reconciles is True


class TestConsolidationWorksheet:
    def test_worksheet_columns_per_entity(self):
        cfg = IntercompanyConfig(
            entities=[_parent_with_receivable(), _subsidiary_with_payable()],
        )
        result = run_intercompany_elimination(cfg)
        assert len(result.worksheet.columns) == 2
        by_entity = {c.entity_id: c for c in result.worksheet.columns}
        assert "parent" in by_entity
        assert "subsidiary" in by_entity

    def test_elimination_reduces_totals(self):
        cfg = IntercompanyConfig(
            entities=[_parent_with_receivable(), _subsidiary_with_payable()],
        )
        result = run_intercompany_elimination(cfg)
        ws = result.worksheet
        assert ws.elimination_debits == Decimal("10000.00")
        assert ws.elimination_credits == Decimal("10000.00")
        assert ws.consolidated_debits == ws.total_entity_debits - Decimal("10000.00")
        assert ws.consolidated_credits == ws.total_entity_credits - Decimal("10000.00")


class TestMultipleEntities:
    def test_three_entity_consolidation(self):
        a = EntityTrialBalance(
            entity_id="a",
            entity_name="A",
            accounts=[
                EntityAccount(
                    account="Due from B",
                    debit=Decimal("100"),
                    counterparty_entity="b",
                ),
                EntityAccount(
                    account="Due from C",
                    debit=Decimal("200"),
                    counterparty_entity="c",
                ),
            ],
        )
        b = EntityTrialBalance(
            entity_id="b",
            entity_name="B",
            accounts=[
                EntityAccount(
                    account="Due to A",
                    credit=Decimal("100"),
                    counterparty_entity="a",
                )
            ],
        )
        c = EntityTrialBalance(
            entity_id="c",
            entity_name="C",
            accounts=[
                EntityAccount(
                    account="Due to A",
                    credit=Decimal("200"),
                    counterparty_entity="a",
                )
            ],
        )
        cfg = IntercompanyConfig(entities=[a, b, c])
        result = run_intercompany_elimination(cfg)
        assert len([p for p in result.pairs if p.reconciles]) == 2


class TestInputValidation:
    def test_single_entity_rejected(self):
        try:
            run_intercompany_elimination(IntercompanyConfig(entities=[_parent_with_receivable()]))
        except IntercompanyInputError:
            return
        raise AssertionError("expected IntercompanyInputError")

    def test_duplicate_entity_id_rejected(self):
        try:
            run_intercompany_elimination(
                IntercompanyConfig(
                    entities=[
                        _parent_with_receivable(),
                        EntityTrialBalance(
                            entity_id="parent",  # Duplicate
                            entity_name="Duplicate",
                            accounts=[],
                        ),
                    ]
                )
            )
        except IntercompanyInputError:
            return
        raise AssertionError("expected IntercompanyInputError")


class TestCounterpartyParsing:
    def test_counterparty_parsed_from_account_name_when_unspecified(self):
        parent = EntityTrialBalance(
            entity_id="parent",
            entity_name="Parent Corp",
            accounts=[
                EntityAccount(
                    account="Due from Subsidiary Beta",
                    debit=Decimal("500"),
                )
            ],
        )
        sub = EntityTrialBalance(
            entity_id="subsidiary_beta",
            entity_name="Subsidiary Beta",
            accounts=[
                EntityAccount(
                    account="Due to Parent Corp",
                    credit=Decimal("500"),
                )
            ],
        )
        cfg = IntercompanyConfig(entities=[parent, sub])
        result = run_intercompany_elimination(cfg)
        assert len(result.pairs) == 1
        assert result.pairs[0].reconciles is True


class TestSerialisation:
    def test_to_dict_roundtrip(self):
        cfg = IntercompanyConfig(
            entities=[_parent_with_receivable(), _subsidiary_with_payable()],
        )
        result = run_intercompany_elimination(cfg)
        d = result.to_dict()
        assert set(d).issuperset(
            {
                "intercompany_lines",
                "pairs",
                "mismatches",
                "elimination_journal_entries",
                "worksheet",
                "summary",
            }
        )


class TestNegativeAmounts:
    """Sprint 846 (I5): a negative debit is a credit, and a negative credit is a debit.

    The net balance was always right (``debit - credit``), so matching worked. The
    worksheet sums the debit and credit columns separately, though, so a payable
    keyed as ``debit = -10,000`` understated both of that entity's column totals.
    """

    def _subsidiary_with_negative_debit_payable(self) -> EntityTrialBalance:
        return EntityTrialBalance(
            entity_id="subsidiary",
            entity_name="Subsidiary Beta",
            accounts=[
                EntityAccount(account="1000 Cash", debit=Decimal("20000")),
                EntityAccount(
                    account="2500 Due to Parent",
                    debit=Decimal("-10000"),
                    counterparty_entity="parent",
                ),
                EntityAccount(account="3000 Equity", credit=Decimal("10000")),
            ],
        )

    def test_negative_debit_moves_to_credit(self):
        account = EntityAccount(account="2500 Due to Parent", debit=Decimal("-10000"))
        assert account.debit == Decimal("0")
        assert account.credit == Decimal("10000")

    def test_negative_credit_moves_to_debit(self):
        account = EntityAccount(account="1500 Due from Sub", credit=Decimal("-250.50"))
        assert account.debit == Decimal("250.50")
        assert account.credit == Decimal("0")

    def test_net_balance_is_preserved_when_both_sides_are_present(self):
        account = EntityAccount(account="Due to Parent", debit=Decimal("-100"), credit=Decimal("50"))
        assert account.debit == Decimal("0")
        assert account.credit == Decimal("150")

    def test_worksheet_columns_match_the_positive_presentation(self):
        negative = run_intercompany_elimination(
            IntercompanyConfig(entities=[_parent_with_receivable(), self._subsidiary_with_negative_debit_payable()])
        )
        positive = run_intercompany_elimination(
            IntercompanyConfig(entities=[_parent_with_receivable(), _subsidiary_with_payable()])
        )
        assert negative.worksheet.to_dict() == positive.worksheet.to_dict()
        sub = {c.entity_id: c for c in negative.worksheet.columns}["subsidiary"]
        assert sub.debit_total == Decimal("20000.00")
        assert sub.credit_total == Decimal("20000.00")
        assert len(negative.pairs) == 1
        assert negative.pairs[0].reconciles is True
