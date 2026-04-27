"""
Sprint 729a — SUM schedule memo PDF generation tests.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engagement_manager import EngagementManager
from sum_schedule_memo_generator import SumScheduleMemoGenerator
from uncorrected_misstatements_manager import UncorrectedMisstatementsManager
from uncorrected_misstatements_model import (
    MisstatementClassification,
    MisstatementSourceType,
)


def _setup(db_session, make_user, make_client, materiality=100000.0):
    user = make_user()
    client = make_client(user=user, name="Acme Corp")
    eng = EngagementManager(db_session).create_engagement(
        user.id,
        client.id,
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 12, 31, tzinfo=UTC),
        materiality_amount=materiality,
    )
    return user, eng


class TestPDF:
    def test_renders_for_empty_engagement(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
        pdf = SumScheduleMemoGenerator(db_session).generate_pdf(user.id, eng.id)
        assert pdf.startswith(b"%PDF")
        assert len(pdf) > 1000

    def test_renders_with_three_classifications(self, db_session, make_user, make_client):
        user, eng = _setup(db_session, make_user, make_client)
        mgr = UncorrectedMisstatementsManager(db_session)

        for cls in [
            MisstatementClassification.FACTUAL,
            MisstatementClassification.JUDGMENTAL,
            MisstatementClassification.PROJECTED,
        ]:
            mgr.create_misstatement(
                user_id=user.id,
                engagement_id=eng.id,
                source_type=MisstatementSourceType.KNOWN_ERROR,
                source_reference=f"{cls.value} test",
                description=f"Test misstatement for {cls.value}",
                accounts_affected=[{"account": "Revenue", "debit_credit": "CR", "amount": 10000}],
                classification=cls,
                fs_impact_net_income=Decimal("-10000.00"),
                fs_impact_net_assets=Decimal("0.00"),
            )

        pdf = SumScheduleMemoGenerator(db_session).generate_pdf(user.id, eng.id)
        assert pdf.startswith(b"%PDF")
        assert len(pdf) > 4000  # multi-section PDF

    def test_renders_material_aggregate_with_warning(self, db_session, make_user, make_client):
        # Build a misstatement that pushes aggregate into MATERIAL bucket
        user, eng = _setup(db_session, make_user, make_client, materiality=100000.0)
        mgr = UncorrectedMisstatementsManager(db_session)
        mgr.create_misstatement(
            user_id=user.id,
            engagement_id=eng.id,
            source_type=MisstatementSourceType.KNOWN_ERROR,
            source_reference="Major reclass",
            description="Pushes aggregate over overall materiality",
            accounts_affected=[{"account": "Equipment", "debit_credit": "DR", "amount": 200000}],
            classification=MisstatementClassification.FACTUAL,
            fs_impact_net_income=Decimal("-200000.00"),
            fs_impact_net_assets=Decimal("-200000.00"),
        )
        pdf = SumScheduleMemoGenerator(db_session).generate_pdf(user.id, eng.id)
        assert pdf.startswith(b"%PDF")

    def test_unknown_engagement_raises(self, db_session, make_user):
        user = make_user()
        with pytest.raises(ValueError, match="not found"):
            SumScheduleMemoGenerator(db_session).generate_pdf(user.id, 9999999)

    def test_other_users_engagement_raises(self, db_session, make_user, make_client):
        user_a, eng = _setup(db_session, make_user, make_client)
        user_b = make_user(email="other-sum-memo@example.com")
        with pytest.raises(ValueError, match="not found"):
            SumScheduleMemoGenerator(db_session).generate_pdf(user_b.id, eng.id)
