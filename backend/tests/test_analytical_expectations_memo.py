"""
Sprint 728a — Analytical-expectations workpaper PDF generation tests.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from analytical_expectation_memo_generator import (
    AnalyticalExpectationMemoGenerator,
)
from analytical_expectations_manager import AnalyticalExpectationsManager
from analytical_expectations_model import ExpectationTargetType
from engagement_manager import EngagementManager


def _setup(db_session, make_user, make_client):
    user = make_user()
    client = make_client(user=user, name="Acme Corp")
    eng = EngagementManager(db_session).create_engagement(
        user.id,
        client.id,
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 12, 31, tzinfo=UTC),
        materiality_amount=100000.0,
    )
    return user, eng


class TestPDFGeneration:
    def test_pdf_renders_for_empty_engagement(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
        gen = AnalyticalExpectationMemoGenerator(db_session)
        pdf_bytes = gen.generate_pdf(user.id, eng.id)
        assert pdf_bytes.startswith(b"%PDF"), "expected PDF byte signature"
        assert len(pdf_bytes) > 1000, "PDF should be non-trivial"

    def test_pdf_renders_with_mixed_status_expectations(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
        mgr = AnalyticalExpectationsManager(db_session)

        # NOT_EVALUATED
        mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.ACCOUNT,
            procedure_target_label="Revenue",
            expected_value=1000.0,
            precision_threshold_amount=50.0,
            corroboration_basis_text="Prior-period growth",
            corroboration_tags=["prior_period"],
        )

        # WITHIN
        e_within = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.RATIO,
            procedure_target_label="Current ratio",
            expected_value=2.0,
            precision_threshold_percent=10.0,
            corroboration_basis_text="Industry median",
            corroboration_tags=["industry_data", "prior_period"],
        )
        mgr.update_expectation(user_id=user.id, expectation_id=e_within.id, result_actual_value=2.05)

        # EXCEEDS
        e_exceeds = mgr.create_expectation(
            user_id=user.id,
            engagement_id=eng.id,
            procedure_target_type=ExpectationTargetType.BALANCE,
            procedure_target_label="Cash and equivalents",
            expected_range_low=100000.0,
            expected_range_high=125000.0,
            precision_threshold_amount=5000.0,
            corroboration_basis_text="Budget review",
            corroboration_tags=["budget"],
            cpa_notes="Spike attributable to year-end customer pre-payment.",
        )
        mgr.update_expectation(
            user_id=user.id,
            expectation_id=e_exceeds.id,
            result_actual_value=140000.0,
        )

        gen = AnalyticalExpectationMemoGenerator(db_session)
        pdf_bytes = gen.generate_pdf(user.id, eng.id)
        assert pdf_bytes.startswith(b"%PDF")
        # Multi-section PDF should be substantially larger than the empty-case PDF
        assert len(pdf_bytes) > 3000

    def test_unknown_engagement_raises(self, db_session, make_user):
        user = make_user()
        gen = AnalyticalExpectationMemoGenerator(db_session)
        with pytest.raises(ValueError, match="not found"):
            gen.generate_pdf(user.id, 9999999)

    def test_other_users_engagement_raises(self, db_session, make_user, make_client):
        user_a, eng = _setup(db_session, make_user, make_client)
        user_b = make_user(email="other@example.com")
        gen = AnalyticalExpectationMemoGenerator(db_session)
        with pytest.raises(ValueError, match="not found"):
            gen.generate_pdf(user_b.id, eng.id)
