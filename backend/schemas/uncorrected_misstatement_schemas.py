"""
Uncorrected Misstatement API schemas — Sprint 729a (ISA 450).

Pydantic surface for routes/uncorrected_misstatements.py.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from uncorrected_misstatements_model import (
    MisstatementClassification,
    MisstatementDisposition,
    MisstatementSourceType,
)


class AccountAffected(BaseModel):
    account: str = Field(..., min_length=1, max_length=200)
    debit_credit: Literal["DR", "CR"]
    amount: float = Field(..., gt=0)


class UncorrectedMisstatementCreate(BaseModel):
    source_type: MisstatementSourceType
    source_reference: str = Field(..., min_length=1, max_length=2000)
    description: str = Field(..., min_length=1, max_length=4000)
    accounts_affected: list[AccountAffected] = Field(..., min_length=1)
    classification: MisstatementClassification
    fs_impact_net_income: float
    fs_impact_net_assets: float
    cpa_disposition: MisstatementDisposition = MisstatementDisposition.NOT_YET_REVIEWED
    cpa_notes: Optional[str] = Field(default=None, max_length=4000)


class UncorrectedMisstatementUpdate(BaseModel):
    source_reference: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    description: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    accounts_affected: Optional[list[AccountAffected]] = Field(default=None, min_length=1)
    classification: Optional[MisstatementClassification] = None
    fs_impact_net_income: Optional[float] = None
    fs_impact_net_assets: Optional[float] = None
    cpa_disposition: Optional[MisstatementDisposition] = None
    cpa_notes: Optional[str] = Field(default=None, max_length=4000)


class UncorrectedMisstatementResponse(BaseModel):
    id: int
    engagement_id: int
    source_type: Literal["adjusting_entry_passed", "sample_projection", "known_error"]
    source_reference: str
    description: str
    accounts_affected: list[dict]
    classification: Literal["factual", "judgmental", "projected"]
    fs_impact_net_income: float
    fs_impact_net_assets: float
    cpa_disposition: Literal[
        "not_yet_reviewed",
        "auditor_proposes_correction",
        "auditor_accepts_as_immaterial",
    ]
    cpa_notes: Optional[str] = None
    created_by: int
    created_at: str
    updated_by: Optional[int] = None
    updated_at: str


class SumScheduleSubtotals(BaseModel):
    factual_judgmental_net_income: float
    factual_judgmental_net_assets: float
    projected_net_income: float
    projected_net_assets: float


class SumScheduleAggregate(BaseModel):
    net_income: float
    net_assets: float
    driver: float


class SumScheduleMateriality(BaseModel):
    overall: float
    performance: float
    trivial: float


class SumScheduleResponse(BaseModel):
    engagement_id: int
    items: list[UncorrectedMisstatementResponse]
    subtotals: SumScheduleSubtotals
    aggregate: SumScheduleAggregate
    materiality: SumScheduleMateriality
    bucket: Literal["clearly_trivial", "immaterial", "approaching_material", "material"]
    unreviewed_count: int
