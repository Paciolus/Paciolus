"""
Paciolus API — Practice & Client Settings Routes
"""
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
from models import User, Client
from auth import require_current_user
from client_manager import ClientManager
from practice_settings import (
    PracticeSettings, ClientSettings, MaterialityFormula, MaterialityFormulaType,
    MaterialityCalculator, resolve_materiality_config
)
from shared.helpers import require_client

router = APIRouter(tags=["settings"])


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


class MaterialityResolveResponse(BaseModel):
    formula: dict
    formula_display: str
    session_override: Optional[float] = None
    source: str


@router.get("/settings/practice", response_model=PracticeSettingsResponse)
def get_practice_settings(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's practice settings."""
    log_secure_operation(
        "get_practice_settings",
        f"User {current_user.id} fetching practice settings"
    )

    settings = PracticeSettings.from_json(current_user.settings or "{}")

    return PracticeSettingsResponse(
        default_materiality=settings.default_materiality.to_dict(),
        show_immaterial_by_default=settings.show_immaterial_by_default,
        default_fiscal_year_end=settings.default_fiscal_year_end,
        theme_preference=settings.theme_preference,
        default_export_format=settings.default_export_format,
        auto_save_summaries=settings.auto_save_summaries,
    )


@router.put("/settings/practice", response_model=PracticeSettingsResponse)
def update_practice_settings(
    settings_input: PracticeSettingsInput,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's practice settings."""
    log_secure_operation(
        "update_practice_settings",
        f"User {current_user.id} updating practice settings"
    )

    current_settings = PracticeSettings.from_json(current_user.settings or "{}")

    if settings_input.default_materiality:
        formula_input = settings_input.default_materiality
        current_settings.default_materiality = MaterialityFormula(
            type=formula_input.type,
            value=formula_input.value,
            min_threshold=formula_input.min_threshold,
            max_threshold=formula_input.max_threshold,
        )

    if settings_input.show_immaterial_by_default is not None:
        current_settings.show_immaterial_by_default = settings_input.show_immaterial_by_default

    if settings_input.default_fiscal_year_end is not None:
        current_settings.default_fiscal_year_end = settings_input.default_fiscal_year_end

    if settings_input.theme_preference is not None:
        current_settings.theme_preference = settings_input.theme_preference

    if settings_input.default_export_format is not None:
        current_settings.default_export_format = settings_input.default_export_format

    if settings_input.auto_save_summaries is not None:
        current_settings.auto_save_summaries = settings_input.auto_save_summaries

    current_user.settings = current_settings.to_json()
    db.commit()

    log_secure_operation(
        "practice_settings_updated",
        f"User {current_user.id} practice settings saved"
    )

    return PracticeSettingsResponse(
        default_materiality=current_settings.default_materiality.to_dict(),
        show_immaterial_by_default=current_settings.show_immaterial_by_default,
        default_fiscal_year_end=current_settings.default_fiscal_year_end,
        theme_preference=current_settings.theme_preference,
        default_export_format=current_settings.default_export_format,
        auto_save_summaries=current_settings.auto_save_summaries,
    )


@router.get("/clients/{client_id}/settings", response_model=ClientSettingsResponse)
def get_client_settings(
    client: Client = Depends(require_client)
):
    """Get settings for a specific client."""
    settings = ClientSettings.from_json(client.settings or "{}")

    return ClientSettingsResponse(
        materiality_override=settings.materiality_override.to_dict() if settings.materiality_override else None,
        notes=settings.notes,
        industry_multiplier=settings.industry_multiplier,
        diagnostic_frequency=settings.diagnostic_frequency,
    )


@router.put("/clients/{client_id}/settings", response_model=ClientSettingsResponse)
def update_client_settings(
    settings_input: ClientSettingsInput,
    client: Client = Depends(require_client),
    db: Session = Depends(get_db)
):
    """Update settings for a specific client."""
    log_secure_operation(
        "update_client_settings",
        f"User {client.user_id} updating settings for client {client.id}"
    )

    current_settings = ClientSettings.from_json(client.settings or "{}")

    if settings_input.materiality_override:
        formula_input = settings_input.materiality_override
        current_settings.materiality_override = MaterialityFormula(
            type=formula_input.type,
            value=formula_input.value,
            min_threshold=formula_input.min_threshold,
            max_threshold=formula_input.max_threshold,
        )
    elif settings_input.materiality_override is None and 'materiality_override' in (settings_input.model_dump(exclude_unset=True) or {}):
        current_settings.materiality_override = None

    if settings_input.notes is not None:
        current_settings.notes = settings_input.notes

    if settings_input.industry_multiplier is not None:
        current_settings.industry_multiplier = settings_input.industry_multiplier

    if settings_input.diagnostic_frequency is not None:
        current_settings.diagnostic_frequency = settings_input.diagnostic_frequency

    client.settings = current_settings.to_json()
    db.commit()

    log_secure_operation(
        "client_settings_updated",
        f"Client {client.id} settings saved for user {client.user_id}"
    )

    return ClientSettingsResponse(
        materiality_override=current_settings.materiality_override.to_dict() if current_settings.materiality_override else None,
        notes=current_settings.notes,
        industry_multiplier=current_settings.industry_multiplier,
        diagnostic_frequency=current_settings.diagnostic_frequency,
    )


@router.post("/settings/materiality/preview", response_model=dict)
def preview_materiality(
    preview_input: MaterialityPreviewInput,
    current_user: User = Depends(require_current_user)
):
    """Preview a materiality calculation."""
    formula = MaterialityFormula(
        type=MaterialityFormulaType(preview_input.formula.type),
        value=preview_input.formula.value,
        min_threshold=preview_input.formula.min_threshold,
        max_threshold=preview_input.formula.max_threshold,
    )

    preview = MaterialityCalculator.preview(
        formula=formula,
        total_revenue=preview_input.total_revenue,
        total_assets=preview_input.total_assets,
        total_equity=preview_input.total_equity,
    )

    return preview


@router.get("/settings/materiality/resolve", response_model=MaterialityResolveResponse)
def resolve_materiality(
    client_id: Optional[int] = Query(default=None),
    session_threshold: Optional[float] = Query(default=None),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Resolve the effective materiality configuration."""
    practice_settings = PracticeSettings.from_json(current_user.settings or "{}")

    client_settings = None
    if client_id:
        manager = ClientManager(db)
        client = manager.get_client(current_user.id, client_id)
        if client:
            client_settings = ClientSettings.from_json(client.settings or "{}")

    config = resolve_materiality_config(
        practice_settings=practice_settings,
        client_settings=client_settings,
        session_threshold=session_threshold
    )

    return {
        "formula": config.formula.to_dict(),
        "formula_display": config.formula.get_display_string(),
        "session_override": config.session_override,
        "source": "session" if config.session_override else (
            "client" if client_settings and client_settings.materiality_override else "practice"
        ),
    }
