"""
Settings Schemas — extracted from routes/settings.py (Sprint 544).
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from practice_settings import MaterialityFormulaType


class MaterialityFormulaInput(BaseModel):
    type: MaterialityFormulaType = MaterialityFormulaType.FIXED
    value: float = Field(500.0, ge=0)
    min_threshold: Optional[float] = Field(None, ge=0)
    max_threshold: Optional[float] = Field(None, ge=0)


class PracticeSettingsInput(BaseModel):
    default_materiality: Optional[MaterialityFormulaInput] = None
    show_immaterial_by_default: Optional[bool] = None
    default_fiscal_year_end: Optional[str] = None
    theme_preference: Optional[str] = None
    default_export_format: Optional[Literal["pdf", "excel", "csv"]] = None
    auto_save_summaries: Optional[bool] = None


class PracticeSettingsResponse(BaseModel):
    default_materiality: dict
    show_immaterial_by_default: bool
    default_fiscal_year_end: str
    theme_preference: str
    default_export_format: str
    auto_save_summaries: bool


class ClientSettingsInput(BaseModel):
    materiality_override: Optional[MaterialityFormulaInput] = None
    notes: Optional[str] = None
    industry_multiplier: Optional[float] = Field(None, ge=0.1, le=10.0)
    diagnostic_frequency: Optional[Literal["weekly", "monthly", "quarterly", "annually"]] = None


class ClientSettingsResponse(BaseModel):
    materiality_override: Optional[dict]
    notes: str
    industry_multiplier: float
    diagnostic_frequency: str


class MaterialityPreviewInput(BaseModel):
    formula: MaterialityFormulaInput
    total_revenue: float = 0.0
    total_assets: float = 0.0
    total_equity: float = 0.0


class MaterialityPreviewResponse(BaseModel):
    threshold: float
    formula_display: str
    explanation: str
    formula: dict[str, Any]


class MaterialityResolveResponse(BaseModel):
    formula: dict
    formula_display: str
    session_override: Optional[float] = None
    source: str
