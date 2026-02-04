"""
Paciolus Practice Settings
Sprint 21: Customization & Practice Settings

Defines practice-level configuration for CFOs including:
- Dynamic Materiality Formulas (fixed, percentage-based)
- Global threshold defaults
- Client-specific settings overrides

ZERO-STORAGE COMPLIANCE:
- Stores ONLY the formula/configuration
- NEVER stores the financial data the formula is applied to
- Formula evaluation happens at runtime, results are ephemeral

Uses Pydantic (MIT License) for validation.
"""

import json
from enum import Enum
from typing import Optional, Union, Dict, Any, List
from dataclasses import dataclass, field, asdict
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# MATERIALITY FORMULA TYPES
# =============================================================================

class MaterialityFormulaType(str, Enum):
    """
    Types of materiality calculation formulas.

    These are standard approaches used in accounting practice:
    - Fixed: A specific dollar amount (e.g., $10,000)
    - Percentage of Revenue: Common for income statement focus
    - Percentage of Assets: Common for balance sheet focus
    - Percentage of Equity: Conservative approach for stability
    """
    FIXED = "fixed"
    PERCENTAGE_OF_REVENUE = "percentage_of_revenue"
    PERCENTAGE_OF_ASSETS = "percentage_of_assets"
    PERCENTAGE_OF_EQUITY = "percentage_of_equity"


class MaterialityFormula(BaseModel):
    """
    A materiality calculation formula.

    Examples:
    - Fixed $10,000: {"type": "fixed", "value": 10000}
    - 0.5% of Revenue: {"type": "percentage_of_revenue", "value": 0.5}
    - 1% of Total Assets: {"type": "percentage_of_assets", "value": 1.0}
    """
    type: MaterialityFormulaType = Field(
        default=MaterialityFormulaType.FIXED,
        description="The type of materiality calculation"
    )
    value: float = Field(
        default=500.0,
        ge=0,
        description="The value: dollar amount for fixed, percentage for others"
    )
    min_threshold: Optional[float] = Field(
        default=None,
        ge=0,
        description="Optional minimum threshold floor (for percentage-based)"
    )
    max_threshold: Optional[float] = Field(
        default=None,
        ge=0,
        description="Optional maximum threshold cap (for percentage-based)"
    )

    @field_validator('value')
    @classmethod
    def validate_value(cls, v, info):
        """Validate value based on formula type."""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "type": self.type.value,
            "value": self.value,
            "min_threshold": self.min_threshold,
            "max_threshold": self.max_threshold,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MaterialityFormula":
        """Create from dictionary (e.g., from JSON storage)."""
        if not data:
            return cls()
        return cls(
            type=MaterialityFormulaType(data.get("type", "fixed")),
            value=data.get("value", 500.0),
            min_threshold=data.get("min_threshold"),
            max_threshold=data.get("max_threshold"),
        )

    def get_display_string(self) -> str:
        """Get a human-readable description of the formula."""
        if self.type == MaterialityFormulaType.FIXED:
            return f"Fixed ${self.value:,.2f}"
        elif self.type == MaterialityFormulaType.PERCENTAGE_OF_REVENUE:
            return f"{self.value}% of Revenue"
        elif self.type == MaterialityFormulaType.PERCENTAGE_OF_ASSETS:
            return f"{self.value}% of Total Assets"
        elif self.type == MaterialityFormulaType.PERCENTAGE_OF_EQUITY:
            return f"{self.value}% of Total Equity"
        return f"Unknown formula"


# =============================================================================
# PRACTICE SETTINGS MODEL
# =============================================================================

class PracticeSettings(BaseModel):
    """
    Practice-level settings for a CFO user.

    These settings define defaults that apply across all diagnostics
    unless overridden at the client level.

    ZERO-STORAGE COMPLIANCE:
    - Stores configuration/formulas only
    - Never stores financial data
    """
    # Default materiality formula
    default_materiality: MaterialityFormula = Field(
        default_factory=lambda: MaterialityFormula(
            type=MaterialityFormulaType.FIXED,
            value=500.0
        ),
        description="Default materiality formula for all diagnostics"
    )

    # Show/hide immaterial items by default
    show_immaterial_by_default: bool = Field(
        default=False,
        description="Whether to show immaterial (indistinct) items by default"
    )

    # Default fiscal year end for new clients
    default_fiscal_year_end: str = Field(
        default="12-31",
        pattern=r"^\d{2}-\d{2}$",
        description="Default fiscal year end (MM-DD format)"
    )

    # UI preferences
    theme_preference: str = Field(
        default="oat_obsidian",
        description="UI theme preference"
    )

    # Export preferences
    default_export_format: str = Field(
        default="pdf",
        description="Default export format (pdf, excel)"
    )

    # Auto-save diagnostic summaries for variance tracking
    auto_save_summaries: bool = Field(
        default=True,
        description="Automatically save diagnostic summaries for clients"
    )

    def to_json(self) -> str:
        """Serialize to JSON string for database storage."""
        return json.dumps(self.model_dump(), default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "PracticeSettings":
        """Deserialize from JSON string."""
        if not json_str or json_str == "{}":
            return cls()
        try:
            data = json.loads(json_str)
            # Handle nested MaterialityFormula
            if "default_materiality" in data and isinstance(data["default_materiality"], dict):
                data["default_materiality"] = MaterialityFormula.from_dict(data["default_materiality"])
            return cls(**data)
        except (json.JSONDecodeError, ValueError):
            return cls()


class ClientSettings(BaseModel):
    """
    Client-specific settings that override practice-level defaults.

    ZERO-STORAGE COMPLIANCE:
    - Stores configuration only
    - Never stores client financial data
    """
    # Override materiality formula for this client
    materiality_override: Optional[MaterialityFormula] = Field(
        default=None,
        description="Client-specific materiality formula (overrides practice default)"
    )

    # Client-specific notes (for CFO reference only)
    notes: str = Field(
        default="",
        max_length=2000,
        description="Private notes about this client"
    )

    # Industry-specific threshold adjustments
    industry_multiplier: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Multiplier for industry-specific threshold adjustment"
    )

    # Preferred diagnostic frequency
    diagnostic_frequency: str = Field(
        default="monthly",
        description="Expected diagnostic frequency (weekly, monthly, quarterly, annually)"
    )

    def to_json(self) -> str:
        """Serialize to JSON string for database storage."""
        return json.dumps(self.model_dump(), default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "ClientSettings":
        """Deserialize from JSON string."""
        if not json_str or json_str == "{}":
            return cls()
        try:
            data = json.loads(json_str)
            # Handle nested MaterialityFormula
            if "materiality_override" in data and isinstance(data["materiality_override"], dict):
                data["materiality_override"] = MaterialityFormula.from_dict(data["materiality_override"])
            return cls(**data)
        except (json.JSONDecodeError, ValueError):
            return cls()


# =============================================================================
# MATERIALITY CALCULATOR
# =============================================================================

@dataclass
class MaterialityConfig:
    """
    Runtime configuration for materiality calculation.

    This is the resolved configuration that combines:
    1. Practice-level defaults
    2. Client-level overrides
    3. Session-level adjustments

    ZERO-STORAGE: This object is created at runtime and never persisted.
    """
    formula: MaterialityFormula = field(default_factory=MaterialityFormula)
    session_override: Optional[float] = None  # Direct threshold from UI

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "formula": self.formula.to_dict(),
            "session_override": self.session_override,
        }


class MaterialityCalculator:
    """
    Calculates materiality threshold based on formula and financial data.

    ZERO-STORAGE COMPLIANCE:
    - Takes financial totals as INPUT parameters
    - Does NOT store or persist any financial data
    - Returns calculated threshold as OUTPUT

    The formula is stored; the data it operates on is ephemeral.
    """

    @staticmethod
    def calculate(
        config: MaterialityConfig,
        total_revenue: float = 0.0,
        total_assets: float = 0.0,
        total_equity: float = 0.0
    ) -> float:
        """
        Calculate the materiality threshold.

        Args:
            config: The materiality configuration
            total_revenue: Total revenue (for percentage_of_revenue)
            total_assets: Total assets (for percentage_of_assets)
            total_equity: Total equity (for percentage_of_equity)

        Returns:
            Calculated materiality threshold in dollars
        """
        # Priority 1: Session override (direct UI input)
        if config.session_override is not None:
            return config.session_override

        formula = config.formula

        # Calculate based on formula type
        if formula.type == MaterialityFormulaType.FIXED:
            threshold = formula.value

        elif formula.type == MaterialityFormulaType.PERCENTAGE_OF_REVENUE:
            if total_revenue <= 0:
                # Fall back to fixed value if no revenue data
                threshold = formula.value
            else:
                threshold = total_revenue * (formula.value / 100.0)

        elif formula.type == MaterialityFormulaType.PERCENTAGE_OF_ASSETS:
            if total_assets <= 0:
                threshold = formula.value
            else:
                threshold = total_assets * (formula.value / 100.0)

        elif formula.type == MaterialityFormulaType.PERCENTAGE_OF_EQUITY:
            if total_equity <= 0:
                threshold = formula.value
            else:
                threshold = total_equity * (formula.value / 100.0)

        else:
            # Default fallback
            threshold = 500.0

        # Apply min/max bounds if specified
        if formula.min_threshold is not None:
            threshold = max(threshold, formula.min_threshold)
        if formula.max_threshold is not None:
            threshold = min(threshold, formula.max_threshold)

        return round(threshold, 2)

    @staticmethod
    def preview(
        formula: MaterialityFormula,
        total_revenue: float = 0.0,
        total_assets: float = 0.0,
        total_equity: float = 0.0
    ) -> Dict[str, Any]:
        """
        Preview the materiality calculation with explanation.

        Returns a dict with the calculated value and explanation for UI display.
        """
        config = MaterialityConfig(formula=formula)
        threshold = MaterialityCalculator.calculate(
            config, total_revenue, total_assets, total_equity
        )

        explanation = formula.get_display_string()

        if formula.type == MaterialityFormulaType.PERCENTAGE_OF_REVENUE and total_revenue > 0:
            explanation += f" (${total_revenue:,.2f} * {formula.value}% = ${threshold:,.2f})"
        elif formula.type == MaterialityFormulaType.PERCENTAGE_OF_ASSETS and total_assets > 0:
            explanation += f" (${total_assets:,.2f} * {formula.value}% = ${threshold:,.2f})"
        elif formula.type == MaterialityFormulaType.PERCENTAGE_OF_EQUITY and total_equity > 0:
            explanation += f" (${total_equity:,.2f} * {formula.value}% = ${threshold:,.2f})"

        return {
            "threshold": threshold,
            "formula_display": formula.get_display_string(),
            "explanation": explanation,
            "formula": formula.to_dict(),
        }


# =============================================================================
# SETTINGS RESOLUTION
# =============================================================================

def resolve_materiality_config(
    practice_settings: Optional[PracticeSettings] = None,
    client_settings: Optional[ClientSettings] = None,
    session_threshold: Optional[float] = None
) -> MaterialityConfig:
    """
    Resolve the final materiality configuration from multiple sources.

    Priority (highest to lowest):
    1. Session threshold (UI slider override)
    2. Client-specific materiality formula
    3. Practice-level default materiality formula
    4. System default (Fixed $500)

    ZERO-STORAGE: This function operates on in-memory objects only.
    """
    # Start with system default
    formula = MaterialityFormula(type=MaterialityFormulaType.FIXED, value=500.0)

    # Apply practice-level default if available
    if practice_settings and practice_settings.default_materiality:
        formula = practice_settings.default_materiality

    # Apply client-level override if available
    if client_settings and client_settings.materiality_override:
        formula = client_settings.materiality_override
        # Apply industry multiplier if not 1.0
        if client_settings.industry_multiplier != 1.0:
            formula = MaterialityFormula(
                type=formula.type,
                value=formula.value * client_settings.industry_multiplier,
                min_threshold=formula.min_threshold,
                max_threshold=formula.max_threshold,
            )

    return MaterialityConfig(formula=formula, session_override=session_threshold)
