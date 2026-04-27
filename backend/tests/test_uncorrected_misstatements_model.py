"""
Sprint 729a — UncorrectedMisstatement model schema, defaults, soft-delete.
"""

import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import inspect as sa_inspect

sys.path.insert(0, str(Path(__file__).parent.parent))

from uncorrected_misstatements_model import (
    MaterialityBucket,
    MisstatementClassification,
    MisstatementDisposition,
    MisstatementSourceType,
    UncorrectedMisstatement,
)


class TestEnumValues:
    def test_source_type(self):
        assert MisstatementSourceType.ADJUSTING_ENTRY_PASSED.value == "adjusting_entry_passed"
        assert MisstatementSourceType.SAMPLE_PROJECTION.value == "sample_projection"
        assert MisstatementSourceType.KNOWN_ERROR.value == "known_error"

    def test_classification(self):
        assert MisstatementClassification.FACTUAL.value == "factual"
        assert MisstatementClassification.JUDGMENTAL.value == "judgmental"
        assert MisstatementClassification.PROJECTED.value == "projected"

    def test_disposition(self):
        assert MisstatementDisposition.NOT_YET_REVIEWED.value == "not_yet_reviewed"
        assert MisstatementDisposition.AUDITOR_PROPOSES_CORRECTION.value == "auditor_proposes_correction"
        assert MisstatementDisposition.AUDITOR_ACCEPTS_AS_IMMATERIAL.value == "auditor_accepts_as_immaterial"

    def test_bucket(self):
        assert MaterialityBucket.CLEARLY_TRIVIAL.value == "clearly_trivial"
        assert MaterialityBucket.IMMATERIAL.value == "immaterial"
        assert MaterialityBucket.APPROACHING_MATERIAL.value == "approaching_material"
        assert MaterialityBucket.MATERIAL.value == "material"


class TestSchema:
    def test_table_columns(self, db_engine):
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("uncorrected_misstatements")}
        expected = {
            "id",
            "engagement_id",
            "source_type",
            "source_reference",
            "description",
            "accounts_affected_json",
            "classification",
            "fs_impact_net_income",
            "fs_impact_net_assets",
            "cpa_disposition",
            "cpa_notes",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
            "archived_at",
            "archived_by",
            "archive_reason",
        }
        assert expected.issubset(columns), f"Missing: {expected - columns}"

    def test_no_prohibited_transactional_columns(self, db_engine):
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("uncorrected_misstatements")}
        prohibited = {
            "account_number",
            "transaction_id",
            "vendor_name",
            "employee_name",
        }
        assert columns.isdisjoint(prohibited), f"Prohibited cols: {columns & prohibited}"


class TestDefaultsAndDict:
    def _make(self, db_session, make_engagement):
        engagement = make_engagement()
        m = UncorrectedMisstatement(
            engagement_id=engagement.id,
            source_type=MisstatementSourceType.KNOWN_ERROR,
            source_reference="Cutoff error in revenue, Dec 31",
            description="$10k of December revenue posted in January",
            accounts_affected_json='[{"account": "Revenue", "debit_credit": "CR", "amount": "10000.00"}]',
            classification=MisstatementClassification.FACTUAL,
            fs_impact_net_income=Decimal("10000.00"),
            fs_impact_net_assets=Decimal("10000.00"),
            created_by=engagement.created_by,
        )
        db_session.add(m)
        db_session.flush()
        return m

    def test_default_disposition(self, db_session, make_engagement):
        m = self._make(db_session, make_engagement)
        assert m.cpa_disposition == MisstatementDisposition.NOT_YET_REVIEWED

    def test_to_dict_round_trip(self, db_session, make_engagement):
        m = self._make(db_session, make_engagement)
        d = m.to_dict()
        assert d["source_type"] == "known_error"
        assert d["classification"] == "factual"
        assert d["fs_impact_net_income"] == "10000.00"
        assert d["accounts_affected"] == [{"account": "Revenue", "debit_credit": "CR", "amount": "10000.00"}]
        assert d["cpa_disposition"] == "not_yet_reviewed"

    def test_to_dict_handles_malformed_json(self, db_session, make_engagement):
        m = self._make(db_session, make_engagement)
        m.accounts_affected_json = "{broken"
        db_session.flush()
        assert m.to_dict()["accounts_affected"] == []

    def test_repr(self, db_session, make_engagement):
        m = self._make(db_session, make_engagement)
        r = repr(m)
        assert "UncorrectedMisstatement" in r
        assert "factual" in r
        assert "not_yet_reviewed" in r


class TestSoftDelete:
    def test_archive_sets_archived_at(self, db_session, make_engagement, make_user):
        engagement = make_engagement()
        archiver = make_user(email="archiver-sum@example.com")
        m = UncorrectedMisstatement(
            engagement_id=engagement.id,
            source_type=MisstatementSourceType.KNOWN_ERROR,
            source_reference="x",
            description="y",
            accounts_affected_json='[{"account": "A", "debit_credit": "DR", "amount": "1.00"}]',
            classification=MisstatementClassification.FACTUAL,
            fs_impact_net_income=Decimal("1.00"),
            fs_impact_net_assets=Decimal("1.00"),
            created_by=engagement.created_by,
        )
        db_session.add(m)
        db_session.flush()

        from shared.soft_delete import soft_delete

        soft_delete(db_session, m, user_id=archiver.id, reason="duplicate")
        assert m.archived_at is not None
        assert m.archived_by == archiver.id
        assert m.archive_reason == "duplicate"


class TestRelationship:
    def test_back_populates(self, db_session, make_engagement):
        engagement = make_engagement()
        m = UncorrectedMisstatement(
            engagement_id=engagement.id,
            source_type=MisstatementSourceType.KNOWN_ERROR,
            source_reference="x",
            description="y",
            accounts_affected_json='[{"account": "A", "debit_credit": "DR", "amount": "1.00"}]',
            classification=MisstatementClassification.FACTUAL,
            fs_impact_net_income=Decimal("1.00"),
            fs_impact_net_assets=Decimal("1.00"),
            created_by=engagement.created_by,
        )
        db_session.add(m)
        db_session.flush()
        db_session.refresh(engagement)
        assert m in engagement.uncorrected_misstatements
        assert m.engagement.id == engagement.id
