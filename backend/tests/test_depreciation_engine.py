"""Tests for depreciation_engine (Sprint 626)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from depreciation_engine import (
    MACRS_HY_150DB,
    MACRS_HY_200DB,
    MACRS_MQ_5YR_200DB,
    AssetConfig,
    BookMethod,
    DepreciationInputError,
    MacrsConvention,
    MacrsSystem,
    generate_depreciation_schedule,
)

# =============================================================================
# Straight-line
# =============================================================================


class TestStraightLine:
    def test_basic_straight_line(self):
        """$10,000 cost, $0 salvage, 5-yr life = $2,000/yr."""
        config = AssetConfig(
            asset_name="Test Asset",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=5,
        )
        result = generate_depreciation_schedule(config)
        assert len(result.book_schedule) == 5
        for entry in result.book_schedule:
            assert entry.depreciation == Decimal("2000.00")
        assert result.book_schedule[-1].ending_book_value == Decimal("0.00")
        assert result.total_book_depreciation == Decimal("10000.00")

    def test_straight_line_with_salvage(self):
        """$10,000 cost, $1,000 salvage, 9-yr life = $1,000/yr."""
        config = AssetConfig(
            asset_name="Test",
            cost=Decimal("10000"),
            salvage_value=Decimal("1000"),
            useful_life_years=9,
        )
        result = generate_depreciation_schedule(config)
        assert all(e.depreciation == Decimal("1000.00") for e in result.book_schedule)
        assert result.book_schedule[-1].ending_book_value == Decimal("1000.00")


# =============================================================================
# Declining balance
# =============================================================================


class TestDecliningBalance:
    def test_double_declining_balance(self):
        """DDB on $10,000 5-yr asset switches to SL and ends at salvage."""
        config = AssetConfig(
            asset_name="Test",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=5,
            book_method=BookMethod.DECLINING_BALANCE,
            db_factor=Decimal("2"),
        )
        result = generate_depreciation_schedule(config)
        # Year 1 = 10000 * 2/5 = 4000
        assert result.book_schedule[0].depreciation == Decimal("4000.00")
        # Year 2 = 6000 * 2/5 = 2400
        assert result.book_schedule[1].depreciation == Decimal("2400.00")
        # Total depreciation = cost - salvage
        assert result.book_schedule[-1].ending_book_value == Decimal("0.00")

    def test_db_does_not_depreciate_below_salvage(self):
        config = AssetConfig(
            asset_name="Test",
            cost=Decimal("10000"),
            salvage_value=Decimal("2000"),
            useful_life_years=5,
            book_method=BookMethod.DECLINING_BALANCE,
            db_factor=Decimal("2"),
        )
        result = generate_depreciation_schedule(config)
        assert result.book_schedule[-1].ending_book_value == Decimal("2000.00")

    def test_150_percent_db(self):
        config = AssetConfig(
            asset_name="Test",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=10,
            book_method=BookMethod.DECLINING_BALANCE,
            db_factor=Decimal("1.5"),
        )
        result = generate_depreciation_schedule(config)
        # Year 1 = 10000 * 1.5/10 = 1500
        assert result.book_schedule[0].depreciation == Decimal("1500.00")
        assert result.book_schedule[-1].ending_book_value == Decimal("0.00")


# =============================================================================
# Sum of Years' Digits
# =============================================================================


class TestSumOfYearsDigits:
    def test_syd_basic(self):
        """SYD on $9,000 / 0 salvage / 3-yr life: sum-of-years = 6.
        Year 1 = 9000*3/6=4500, Year 2 = 9000*2/6=3000, Year 3 = 9000*1/6=1500."""
        config = AssetConfig(
            asset_name="Test",
            cost=Decimal("9000"),
            salvage_value=Decimal("0"),
            useful_life_years=3,
            book_method=BookMethod.SUM_OF_YEARS_DIGITS,
        )
        result = generate_depreciation_schedule(config)
        assert result.book_schedule[0].depreciation == Decimal("4500.00")
        assert result.book_schedule[1].depreciation == Decimal("3000.00")
        assert result.book_schedule[2].depreciation == Decimal("1500.00")
        assert result.total_book_depreciation == Decimal("9000.00")


# =============================================================================
# Units of Production
# =============================================================================


class TestUnitsOfProduction:
    def test_uop_proportional(self):
        """Asset $10,000, 100,000 units, year usage (40k, 30k, 30k)."""
        config = AssetConfig(
            asset_name="Equipment",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=3,
            book_method=BookMethod.UNITS_OF_PRODUCTION,
            units_total=Decimal("100000"),
            units_per_year=[Decimal("40000"), Decimal("30000"), Decimal("30000")],
        )
        result = generate_depreciation_schedule(config)
        # rate = 10000/100000 = 0.1 per unit
        assert result.book_schedule[0].depreciation == Decimal("4000.00")
        assert result.book_schedule[1].depreciation == Decimal("3000.00")
        assert result.book_schedule[-1].ending_book_value == Decimal("0.00")


# =============================================================================
# MACRS GDS Half-Year (200% DB)
# =============================================================================


class TestMacrsHalfYear:
    def test_macrs_5yr_half_year_200db(self):
        """$10,000 5-year property under MACRS HY 200% DB.
        Standard table: 20.00, 32.00, 19.20, 11.52, 11.52, 5.76 (sums to 100)."""
        config = AssetConfig(
            asset_name="Computer",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=5,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
            macrs_convention=MacrsConvention.HALF_YEAR,
        )
        result = generate_depreciation_schedule(config)
        assert len(result.tax_schedule) == 6
        assert result.tax_schedule[0].depreciation == Decimal("2000.00")
        assert result.tax_schedule[1].depreciation == Decimal("3200.00")
        # Final year depreciates remaining basis to zero
        assert result.tax_schedule[-1].ending_book_value == Decimal("0.00")
        # Total tax depreciation = full cost (MACRS ignores salvage)
        assert result.total_tax_depreciation == Decimal("10000.00")

    def test_macrs_7yr_half_year(self):
        config = AssetConfig(
            asset_name="Furniture",
            cost=Decimal("100000"),
            useful_life_years=7,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=7,
            macrs_convention=MacrsConvention.HALF_YEAR,
        )
        result = generate_depreciation_schedule(config)
        # Year 1 = 14.29% of 100k = 14290
        assert result.tax_schedule[0].depreciation == Decimal("14290.00")
        assert len(result.tax_schedule) == 8
        assert result.tax_schedule[-1].ending_book_value == Decimal("0.00")

    def test_macrs_15yr_150db(self):
        """15-year property uses 150% DB tables."""
        config = AssetConfig(
            asset_name="Land Improvements",
            cost=Decimal("100000"),
            useful_life_years=15,
            macrs_system=MacrsSystem.GDS_150,
            macrs_property_class=15,
            macrs_convention=MacrsConvention.HALF_YEAR,
        )
        result = generate_depreciation_schedule(config)
        assert result.tax_schedule[0].depreciation == Decimal("5000.00")  # 5%
        assert result.tax_schedule[-1].ending_book_value == Decimal("0.00")


# =============================================================================
# MACRS Mid-Quarter
# =============================================================================


class TestMacrsMidQuarter:
    def test_mq_q1_5yr(self):
        """5-year asset placed Q1 under mid-quarter convention."""
        config = AssetConfig(
            asset_name="Equipment",
            cost=Decimal("10000"),
            useful_life_years=5,
            placed_in_service_quarter=1,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
            macrs_convention=MacrsConvention.MID_QUARTER,
        )
        result = generate_depreciation_schedule(config)
        # Year 1 Q1 = 35% per IRS Pub 946 Table A-2
        assert result.tax_schedule[0].depreciation == Decimal("3500.00")
        assert result.tax_schedule[-1].ending_book_value == Decimal("0.00")

    def test_mq_q4_5yr(self):
        config = AssetConfig(
            asset_name="Equipment",
            cost=Decimal("10000"),
            useful_life_years=5,
            placed_in_service_quarter=4,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
            macrs_convention=MacrsConvention.MID_QUARTER,
        )
        result = generate_depreciation_schedule(config)
        # Year 1 Q4 = 5% (asset placed late in year gets less Year 1)
        assert result.tax_schedule[0].depreciation == Decimal("500.00")


# =============================================================================
# Book vs Tax comparison
# =============================================================================


class TestBookTaxComparison:
    def test_timing_difference_reverses_to_zero(self):
        """Total timing differences over the asset's life net to zero."""
        config = AssetConfig(
            asset_name="Mixed",
            cost=Decimal("10000"),
            salvage_value=Decimal("0"),
            useful_life_years=5,
            book_method=BookMethod.STRAIGHT_LINE,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
            macrs_convention=MacrsConvention.HALF_YEAR,
            tax_rate=Decimal("0.21"),
        )
        result = generate_depreciation_schedule(config)
        assert len(result.book_tax_comparison) >= 5
        timing_total = sum(c.timing_difference for c in result.book_tax_comparison)
        # Both schedules ultimately depreciate the full $10,000
        assert abs(timing_total) <= Decimal("0.01")
        # Cumulative deferred tax should net to zero (or near-zero) at maturity
        final = result.book_tax_comparison[-1]
        assert abs(final.cumulative_deferred_tax) <= Decimal("0.01")

    def test_tax_dep_higher_in_early_years(self):
        """MACRS DB front-loads vs SL — early-year deferred tax should be positive."""
        config = AssetConfig(
            asset_name="Mixed",
            cost=Decimal("10000"),
            useful_life_years=5,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
            macrs_convention=MacrsConvention.HALF_YEAR,
        )
        result = generate_depreciation_schedule(config)
        # Year 1: tax = 2000 (20%), book SL = 2000 → roughly even
        # Year 2: tax = 3200 (32%), book SL = 2000 → tax exceeds book
        year2 = result.book_tax_comparison[1]
        assert year2.timing_difference > Decimal("0")


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    def test_negative_cost_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(AssetConfig(asset_name="x", cost=Decimal("-1"), useful_life_years=5))

    def test_salvage_exceeds_cost_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(
                AssetConfig(
                    asset_name="x",
                    cost=Decimal("100"),
                    salvage_value=Decimal("200"),
                    useful_life_years=5,
                )
            )

    def test_zero_useful_life_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(AssetConfig(asset_name="x", cost=Decimal("100"), useful_life_years=0))

    def test_macrs_without_class_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(
                AssetConfig(
                    asset_name="x",
                    cost=Decimal("100"),
                    useful_life_years=5,
                    macrs_system=MacrsSystem.GDS_200,
                )
            )

    def test_macrs_unsupported_class_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(
                AssetConfig(
                    asset_name="x",
                    cost=Decimal("100"),
                    useful_life_years=5,
                    macrs_system=MacrsSystem.GDS_200,
                    macrs_property_class=4,  # Not a valid class
                )
            )

    def test_uop_without_units_rejected(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(
                AssetConfig(
                    asset_name="x",
                    cost=Decimal("100"),
                    useful_life_years=5,
                    book_method=BookMethod.UNITS_OF_PRODUCTION,
                )
            )


# =============================================================================
# Serialization
# =============================================================================


class TestSerialization:
    def test_to_dict_round_trip(self):
        config = AssetConfig(
            asset_name="Asset",
            cost=Decimal("5000"),
            useful_life_years=3,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
        )
        result = generate_depreciation_schedule(config)
        payload = result.to_dict()
        assert "book_schedule" in payload
        assert "tax_schedule" in payload
        assert "book_tax_comparison" in payload
        assert payload["total_book_depreciation"] == str(result.total_book_depreciation)


# =============================================================================
# MACRS system dispatch (Sprint 795)
# =============================================================================


class TestMacrsSystemIsHonoured:
    """The selected system must change the output, or be refused.

    Before 2026-10-22 ``_macrs_percentages`` dispatched on convention and
    property class only. ``macrs_system`` was declared, validated, echoed back
    in the API response, and never read — so ``gds_200db``, ``gds_150db`` and
    ``gds_sl`` all returned the 200% declining-balance table, and the frontend
    offered all three. The only test touching ``GDS_150`` used class 15, where
    the 150% table is the sole option, so it passed for a reason unrelated to
    the field under test.
    """

    @staticmethod
    def _cfg(system: MacrsSystem, cls: int, **kw) -> AssetConfig:
        return AssetConfig(
            asset_name="Asset",
            cost=Decimal("100000"),
            useful_life_years=kw.pop("life", 5),
            macrs_system=system,
            macrs_property_class=cls,
            macrs_convention=kw.pop("convention", MacrsConvention.HALF_YEAR),
            **kw,
        )

    def test_200db_half_year_matches_pub946_table_a1(self):
        result = generate_depreciation_schedule(self._cfg(MacrsSystem.GDS_200, 5))
        assert [str(y.depreciation) for y in result.tax_schedule] == [
            "20000.00",
            "32000.00",
            "19200.00",
            "11520.00",
            "11520.00",
            "5760.00",
        ]

    def test_150db_election_for_personal_property_is_refused_not_substituted(self):
        """The defect, stated as a test: this used to return the 200% table."""
        with pytest.raises(DepreciationInputError) as exc:
            generate_depreciation_schedule(self._cfg(MacrsSystem.GDS_150, 5))
        assert "150%" in str(exc.value)
        assert "not available" in str(exc.value)

    def test_straight_line_election_is_refused_not_substituted(self):
        with pytest.raises(DepreciationInputError) as exc:
            generate_depreciation_schedule(self._cfg(MacrsSystem.GDS_SL, 5))
        assert "straight-line" in str(exc.value).lower()

    def test_200db_on_a_150db_class_names_the_right_system(self):
        """15- and 20-year property is 150% DB under GDS. Say so."""
        with pytest.raises(DepreciationInputError) as exc:
            generate_depreciation_schedule(self._cfg(MacrsSystem.GDS_200, 15, life=15))
        assert "gds_150db" in str(exc.value)

    def test_150db_on_its_own_classes_still_works(self):
        result = generate_depreciation_schedule(self._cfg(MacrsSystem.GDS_150, 15, life=15))
        assert result.tax_schedule[0].depreciation == Decimal("5000.00")

    def test_mid_month_is_refused_rather_than_computed_over_the_book_life(self):
        """It used to return a plausible-looking, meaningless schedule.

        For a 5-year asset at $100,000 the old path produced
        [19166.67, 20000, 20000, 20000, 20000, 833.33] — mid-month straight
        line over ``useful_life_years``, which is a book input with no MACRS
        meaning. It summed to cost, so nothing downstream noticed.
        """
        with pytest.raises(DepreciationInputError) as exc:
            generate_depreciation_schedule(self._cfg(MacrsSystem.GDS_200, 5, convention=MacrsConvention.MID_MONTH))
        assert "mid-month" in str(exc.value).lower()
        assert "27.5" in str(exc.value) and "39" in str(exc.value)

    def test_mid_quarter_rejects_non_200db_systems(self):
        with pytest.raises(DepreciationInputError):
            generate_depreciation_schedule(self._cfg(MacrsSystem.GDS_150, 5, convention=MacrsConvention.MID_QUARTER))

    def test_mid_quarter_200db_five_year_still_works(self):
        result = generate_depreciation_schedule(
            self._cfg(MacrsSystem.GDS_200, 5, convention=MacrsConvention.MID_QUARTER, placed_in_service_quarter=1)
        )
        assert result.tax_schedule[0].depreciation == Decimal("35000.00")

    @pytest.mark.parametrize("cls,life", [(3, 3), (5, 5), (7, 7), (10, 10), (15, 15), (20, 20)])
    def test_changing_only_the_system_never_silently_returns_the_same_schedule(self, cls, life):
        """The assertion that cannot pass vacuously.

        **Property class is held constant and only the system varies.** That
        is the whole point: an earlier draft of this test paired each system
        with the classes it serves (200% DB with 3/5/7/10, 150% DB with 15/20)
        and therefore could not have detected the defect at all — the outputs
        differed because the *classes* differed, exactly the orthogonal-fixture
        trap. Holding the class fixed, each system must either produce a
        distinct schedule or refuse. Returning another system's table silently
        is the one outcome forbidden.
        """
        outcomes: dict[str, object] = {}
        for system in (MacrsSystem.GDS_200, MacrsSystem.GDS_150, MacrsSystem.GDS_SL):
            try:
                result = generate_depreciation_schedule(self._cfg(system, cls, life=life))
                outcomes[system.value] = tuple(str(y.depreciation) for y in result.tax_schedule)
            except DepreciationInputError:
                outcomes[system.value] = f"refused:{system.value}"

        computed = [v for v in outcomes.values() if not isinstance(v, str)]
        assert len(computed) >= 1, f"class {cls} is served by no system at all: {outcomes}"
        assert len(set(computed)) == len(computed), (
            f"class {cls}: two different MACRS systems returned the identical schedule, which "
            f"means the selected system is not reaching the lookup — {outcomes}"
        )


class TestMacrsTablesAreInternallyConsistent:
    """Every published table must recover exactly 100% of basis."""

    def test_every_table_sums_to_one_hundred_percent(self):
        tables = {
            **{f"HY_200DB/{k}": v for k, v in MACRS_HY_200DB.items()},
            **{f"HY_150DB/{k}": v for k, v in MACRS_HY_150DB.items()},
            **{f"MQ_5YR_200DB/Q{k}": v for k, v in MACRS_MQ_5YR_200DB.items()},
        }
        assert len(tables) == 10, "table count changed — update this assertion deliberately"
        for name, pcts in tables.items():
            assert sum(pcts) == Decimal("100.00") or sum(pcts) == Decimal("100.000"), (
                f"{name} sums to {sum(pcts)}, not 100"
            )

    def test_every_schedule_fully_depreciates_the_basis(self):
        for system, cls, life in (
            (MacrsSystem.GDS_200, 3, 3),
            (MacrsSystem.GDS_200, 5, 5),
            (MacrsSystem.GDS_200, 7, 7),
            (MacrsSystem.GDS_200, 10, 10),
            (MacrsSystem.GDS_150, 15, 15),
            (MacrsSystem.GDS_150, 20, 20),
        ):
            config = AssetConfig(
                asset_name="A",
                cost=Decimal("123456.78"),
                useful_life_years=life,
                macrs_system=system,
                macrs_property_class=cls,
            )
            result = generate_depreciation_schedule(config)
            assert result.tax_schedule[-1].ending_book_value == Decimal("0.00")
            assert result.total_tax_depreciation == Decimal("123456.78")


class TestDeferredTaxColumnFoots:
    """The cumulative column must equal the sum of the column beside it.

    Measured before Sprint 795: 17 of 48 asset configurations disagreed by a
    cent, because the running total accumulated at full precision while the
    per-year column was rounded for display.
    """

    def test_cumulative_equals_the_sum_of_the_annual_column(self):
        failures = []
        for cost in ("100000", "250000", "37555.55", "812345.67"):
            for cls, life in ((3, 3), (5, 5), (7, 7), (10, 10)):
                for rate in ("0.21", "0.27", "0.105"):
                    config = AssetConfig(
                        asset_name="A",
                        cost=Decimal(cost),
                        useful_life_years=life,
                        macrs_system=MacrsSystem.GDS_200,
                        macrs_property_class=cls,
                        tax_rate=Decimal(rate),
                    )
                    result = generate_depreciation_schedule(config)
                    column = sum(c.deferred_tax_change for c in result.book_tax_comparison)
                    final = result.book_tax_comparison[-1].cumulative_deferred_tax
                    if column != final:
                        failures.append(f"{cost}/{cls}yr/{rate}: column {column} != cumulative {final}")
        assert not failures, f"{len(failures)} deferred-tax breaks:\n" + "\n".join(failures[:10])

    def test_timing_difference_equals_tax_less_book(self):
        config = AssetConfig(
            asset_name="A",
            cost=Decimal("100000"),
            useful_life_years=5,
            macrs_system=MacrsSystem.GDS_200,
            macrs_property_class=5,
        )
        for row in generate_depreciation_schedule(config).book_tax_comparison:
            assert row.timing_difference == row.tax_depreciation - row.book_depreciation


class TestDepreciationScheduleIntegrity:
    """Rows foot, columns reconcile, totals equal their columns.

    Found by ``test_every_schedule_fully_depreciates_the_basis`` while writing
    Sprint 795: a $123,456.78 asset reported $123,456.77 of total depreciation
    against an ending book value of 0.00, because the running book value was
    carried at full precision while the column was rounded for display. Same
    defect class as the loan amortization schedule (Sprint 796), in a second
    engine — which is why this is a sweep rather than one asset.
    """

    @staticmethod
    def _matrix() -> list[tuple[str, AssetConfig]]:
        cases: list[tuple[str, AssetConfig]] = []
        for cost in ("100000", "123456.78", "7777.77", "2500000.01"):
            for salvage in ("0", "1000.33"):
                for life in (3, 5, 7, 15):
                    for method in (
                        BookMethod.STRAIGHT_LINE,
                        BookMethod.DECLINING_BALANCE,
                        BookMethod.SUM_OF_YEARS_DIGITS,
                    ):
                        cases.append(
                            (
                                f"{method.value}-{cost}-s{salvage}-{life}y",
                                AssetConfig(
                                    asset_name="A",
                                    cost=Decimal(cost),
                                    salvage_value=Decimal(salvage),
                                    useful_life_years=life,
                                    book_method=method,
                                ),
                            )
                        )
        cases.append(
            (
                "units-of-production",
                AssetConfig(
                    asset_name="A",
                    cost=Decimal("88888.88"),
                    salvage_value=Decimal("4444.44"),
                    useful_life_years=5,
                    book_method=BookMethod.UNITS_OF_PRODUCTION,
                    units_total=Decimal("100000"),
                    units_per_year=[
                        Decimal("23333"),
                        Decimal("19999"),
                        Decimal("31111"),
                        Decimal("15555"),
                        Decimal("10002"),
                    ],
                ),
            )
        )
        return cases

    def test_book_rows_foot_and_reconcile(self):
        failures: list[str] = []
        rows = 0
        for label, config in self._matrix():
            schedule = generate_depreciation_schedule(config).book_schedule
            for entry in schedule:
                rows += 1
                if entry.beginning_book_value - entry.depreciation != entry.ending_book_value:
                    failures.append(
                        f"{label} y{entry.year_index}: {entry.beginning_book_value} - "
                        f"{entry.depreciation} != {entry.ending_book_value}"
                    )
            for prev, nxt in zip(schedule, schedule[1:]):
                if prev.ending_book_value != nxt.beginning_book_value:
                    failures.append(f"{label} y{prev.year_index}: book value jumps")
        assert rows > 250, f"matrix shrank to {rows} rows — it is the coverage"
        assert not failures, f"{len(failures)} of {rows} rows break:\n" + "\n".join(failures[:10])

    def test_book_schedule_recovers_exactly_cost_less_salvage(self):
        failures: list[str] = []
        for label, config in self._matrix():
            result = generate_depreciation_schedule(config)
            expected = (config.cost - config.salvage_value).quantize(Decimal("0.01"))
            if result.total_book_depreciation != expected:
                failures.append(f"{label}: {result.total_book_depreciation} != {expected}")
            if result.book_schedule[-1].ending_book_value != config.salvage_value.quantize(Decimal("0.01")):
                failures.append(f"{label}: does not land on salvage")
        assert not failures, "\n".join(failures[:10])

    def test_accumulated_column_equals_the_running_sum(self):
        for label, config in self._matrix():
            running = Decimal("0.00")
            for entry in generate_depreciation_schedule(config).book_schedule:
                running += entry.depreciation
                assert entry.accumulated_depreciation == running, f"{label} y{entry.year_index}"

    def test_totals_equal_their_columns(self):
        for label, config in self._matrix():
            result = generate_depreciation_schedule(config)
            assert result.total_book_depreciation == sum(y.depreciation for y in result.book_schedule), label
