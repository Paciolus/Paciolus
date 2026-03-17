"""
Client Management Schemas — extracted from routes/clients.py (Sprint 544).
"""

from typing import Optional

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    industry: Optional[str] = "other"
    fiscal_year_end: Optional[str] = "12-31"
    reporting_framework: Optional[str] = "auto"
    entity_type: Optional[str] = "other"
    jurisdiction_country: Optional[str] = Field("US", min_length=2, max_length=2)
    jurisdiction_state: Optional[str] = Field(None, max_length=50)
    settings: Optional[str] = "{}"


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    industry: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    reporting_framework: Optional[str] = None
    entity_type: Optional[str] = None
    jurisdiction_country: Optional[str] = Field(None, min_length=2, max_length=2)
    jurisdiction_state: Optional[str] = Field(None, max_length=50)
    settings: Optional[str] = None


class ClientResponse(BaseModel):
    id: int
    user_id: int
    name: str
    industry: str
    fiscal_year_end: str
    reporting_framework: str
    entity_type: str
    jurisdiction_country: str
    jurisdiction_state: Optional[str]
    created_at: str
    updated_at: str
    settings: str


class ResolvedFrameworkResponse(BaseModel):
    framework: str
    resolution_reason: str
    warnings: list[str]


class IndustryOption(BaseModel):
    value: str
    label: str
