"""
Practice-level configuration including materiality formulas and client settings.

Sprint 32: Materiality Sophistication
- Added weighted materiality by account type
- Balance Sheet vs Income Statement weights
- Per-account-category multipliers for nuanced thresholds
"""

import json
from enum import Enum
from typing import Optional, Union, Dict, Any, List
from dataclasses import dataclass, field, asdict
from pydantic import BaseModel, Field, field_validator


class AccountCategory(str, Enum):
    """Account categories for weighted materiality (mirrors classification_rules.py)."""
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"
    UNKNOWN = "unknown"


# Sprint 32: Default account type weights
# Values > 1.0 = more scrutiny (lower effective threshold)
# Values < 1.0 = less scrutiny (higher effective threshold)
DEFAULT_ACCOUNT_WEIGHTS: Dict[str, float] = {
    "asset": 1.0,       # Standard scrutiny for assets
    "liability": 1.2,   # Higher scrutiny for obligations
    "equity": 1.5,      # Highest scrutiny for ownership changes
    "revenue": 1.3,     # High scrutiny for revenue recognition
    "expense": 0.8,     # Standard-low for routine expenses
    "unknown": 1.0,     # Default weight for unclassified
}

# Sprint 32: Balance Sheet vs Income Statement weights
DEFAULT_STATEMENT_WEIGHTS = {
    "balance_sheet": 1.0,      # Balance sheet items (persist)
    "income_statement": 0.9,   # Income statement items (periodic)
}


class MaterialityFormulaType(str, Enum):
    """Types of materiality calculation formulas."""
    FIXED = "fixed"
    PERCENTAGE_OF_REVENUE = "percentage_of_revenue"
    PERCENTAGE_OF_ASSETS = "percentage_of_assets"
    PERCENTAGE_OF_EQUITY = "percentage_of_equity"


class MaterialityFormula(BaseModel):
    """A materiality calculation formula (fixed amount or percentage-based)."""
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
    def validate_value(cls, v, info) -> float:
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
        return "Unknown formula"


class WeightedMaterialityConfig(BaseModel):
    """
    Sprint 32: Weighted materiality configuration.

    Allows practitioners to apply different materiality thresholds
    to different account categories. Higher weights mean more scrutiny
    (lower effective threshold).

    Example:
        - Equity accounts with 1.5x weight: $500 base -> $333 effective
        - Expense accounts with 0.8x weight: $500 base -> $625 effective
    """
    # Per-account-category weights
    account_weights: Dict[str, float] = Field(
        default_factory=lambda: DEFAULT_ACCOUNT_WEIGHTS.copy(),
        description="Weight multipliers by account category (higher = more scrutiny)"
    )

    # Statement type weights
    balance_sheet_weight: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Weight for balance sheet accounts (assets, liabilities, equity)"
    )
    income_statement_weight: float = Field(
        default=0.9,
        ge=0.1,
        le=5.0,
        description="Weight for income statement accounts (revenue, expense)"
    )

    # Enable/disable weighted materiality
    enabled: bool = Field(
        default=False,
        description="Whether to apply weighted materiality (false = uniform threshold)"
    )

    @field_validator('account_weights')
    @classmethod
    def validate_weights(cls, v) -> dict[str, float]:
        """Ensure all weights are within reasonable bounds."""
        for category, weight in v.items():
            if weight < 0.1 or weight > 5.0:
                raise ValueError(f"Weight for {category} must be between 0.1 and 5.0")
        return v

    def get_effective_weight(self, account_category: str) -> float:
        """
        Calculate the effective weight for an account category.

        Combines account-specific weight with statement type weight.
        """
        if not self.enabled:
            return 1.0

        # Get account category weight
        category_lower = account_category.lower()
        account_weight = self.account_weights.get(category_lower, 1.0)

        # Apply statement type weight
        balance_sheet_categories = {"asset", "liability", "equity"}
        income_statement_categories = {"revenue", "expense"}

        if category_lower in balance_sheet_categories:
            statement_weight = self.balance_sheet_weight
        elif category_lower in income_statement_categories:
            statement_weight = self.income_statement_weight
        else:
            statement_weight = 1.0

        return account_weight * statement_weight

    def calculate_threshold(self, base_threshold: float, account_category: str) -> float:
        """
        Calculate the effective materiality threshold for an account.

        Higher weight = lower threshold (more items flagged as material)

        Args:
            base_threshold: The base materiality threshold
            account_category: The account's category (asset, liability, etc.)

        Returns:
            The adjusted threshold for this account category
        """
        if not self.enabled or base_threshold <= 0:
            return base_threshold

        weight = self.get_effective_weight(account_category)

        # Inverse relationship: higher weight = lower threshold
        # This means more items get flagged as material
        effective_threshold = base_threshold / weight

        return round(effective_threshold, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "account_weights": self.account_weights,
            "balance_sheet_weight": self.balance_sheet_weight,
            "income_statement_weight": self.income_statement_weight,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeightedMaterialityConfig":
        """Create from dictionary."""
        if not data:
            return cls()
        return cls(
            account_weights=data.get("account_weights", DEFAULT_ACCOUNT_WEIGHTS.copy()),
            balance_sheet_weight=data.get("balance_sheet_weight", 1.0),
            income_statement_weight=data.get("income_statement_weight", 0.9),
            enabled=data.get("enabled", False),
        )

    def get_display_summary(self) -> str:
        """Get a human-readable summary of the weight configuration."""
        if not self.enabled:
            return "Uniform materiality (weights disabled)"

        # Find highest and lowest weighted categories
        max_cat = max(self.account_weights.items(), key=lambda x: x[1])
        min_cat = min(self.account_weights.items(), key=lambda x: x[1])

        return f"Weighted: {max_cat[0].title()} ({max_cat[1]}x) to {min_cat[0].title()} ({min_cat[1]}x)"


class PracticeSettings(BaseModel):
    """Practice-level settings defining defaults for all diagnostics."""
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

    # Sprint 32: Weighted materiality configuration
    weighted_materiality: WeightedMaterialityConfig = Field(
        default_factory=WeightedMaterialityConfig,
        description="Account-type-specific materiality weights"
    )

    # Sprint 68: JE Testing thresholds (optional, defaults applied in engine)
    je_testing_config: Optional[dict] = Field(
        default=None,
        description="JE Testing threshold configuration (passed to JETestingConfig)"
    )

    # Sprint 76: AP Testing thresholds (optional, defaults applied in engine)
    ap_testing_config: Optional[dict] = Field(
        default=None,
        description="AP Testing threshold configuration (passed to APTestingConfig)"
    )

    # Sprint 88: Payroll Testing thresholds (optional, defaults applied in engine)
    payroll_testing_config: Optional[dict] = Field(
        default=None,
        description="Payroll Testing threshold configuration (passed to PayrollTestingConfig)"
    )

    # Sprint 94: Three-Way Match thresholds (optional, defaults applied in engine)
    three_way_match_config: Optional[dict] = Field(
        default=None,
        description="Three-Way Match threshold configuration (passed to ThreeWayMatchConfig)"
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
            # Sprint 32: Handle nested WeightedMaterialityConfig
            if "weighted_materiality" in data and isinstance(data["weighted_materiality"], dict):
                data["weighted_materiality"] = WeightedMaterialityConfig.from_dict(data["weighted_materiality"])
            return cls(**data)
        except (json.JSONDecodeError, ValueError):
            return cls()


class ClientSettings(BaseModel):
    """Client-specific settings that override practice-level defaults."""
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


@dataclass
class MaterialityConfig:
    """Runtime configuration combining practice, client, and session settings."""
    formula: MaterialityFormula = field(default_factory=MaterialityFormula)
    session_override: Optional[float] = None  # Direct threshold from UI
    # Sprint 32: Weighted materiality configuration
    weighted_config: Optional[WeightedMaterialityConfig] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "formula": self.formula.to_dict(),
            "session_override": self.session_override,
            "weighted_config": self.weighted_config.to_dict() if self.weighted_config else None,
        }


class MaterialityCalculator:
    """Calculates materiality threshold based on formula and financial data."""

    @staticmethod
    def calculate(
        config: MaterialityConfig,
        total_revenue: float = 0.0,
        total_assets: float = 0.0,
        total_equity: float = 0.0
    ) -> float:
        """Calculate the materiality threshold based on config and financial totals."""
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

    @staticmethod
    def calculate_weighted(
        config: MaterialityConfig,
        account_category: str,
        total_revenue: float = 0.0,
        total_assets: float = 0.0,
        total_equity: float = 0.0
    ) -> float:
        """
        Sprint 32: Calculate weighted materiality threshold for a specific account.

        Args:
            config: The materiality configuration
            account_category: The account's category (asset, liability, etc.)
            total_revenue: Total revenue for percentage calculations
            total_assets: Total assets for percentage calculations
            total_equity: Total equity for percentage calculations

        Returns:
            The effective materiality threshold for this account
        """
        # First calculate base threshold
        base_threshold = MaterialityCalculator.calculate(
            config, total_revenue, total_assets, total_equity
        )

        # Apply weighted adjustment if enabled
        if config.weighted_config and config.weighted_config.enabled:
            return config.weighted_config.calculate_threshold(base_threshold, account_category)

        return base_threshold

    @staticmethod
    def preview_weighted(
        config: MaterialityConfig,
        total_revenue: float = 0.0,
        total_assets: float = 0.0,
        total_equity: float = 0.0
    ) -> Dict[str, Any]:
        """
        Sprint 32: Preview weighted materiality thresholds for all categories.

        Returns effective thresholds for each account type.
        """
        base_threshold = MaterialityCalculator.calculate(
            config, total_revenue, total_assets, total_equity
        )

        categories = ["asset", "liability", "equity", "revenue", "expense", "unknown"]
        weighted_thresholds = {}

        for category in categories:
            weighted_thresholds[category] = MaterialityCalculator.calculate_weighted(
                config, category, total_revenue, total_assets, total_equity
            )

        weighted_enabled = config.weighted_config.enabled if config.weighted_config else False

        return {
            "base_threshold": base_threshold,
            "weighted_enabled": weighted_enabled,
            "thresholds_by_category": weighted_thresholds,
            "formula": config.formula.to_dict(),
            "weighted_config": config.weighted_config.to_dict() if config.weighted_config else None,
        }


def resolve_materiality_config(
    practice_settings: Optional[PracticeSettings] = None,
    client_settings: Optional[ClientSettings] = None,
    session_threshold: Optional[float] = None
) -> MaterialityConfig:
    """Resolve materiality config from session > client > practice > system default."""
    # Start with system default
    formula = MaterialityFormula(type=MaterialityFormulaType.FIXED, value=500.0)
    weighted_config: Optional[WeightedMaterialityConfig] = None

    # Apply practice-level default if available
    if practice_settings:
        if practice_settings.default_materiality:
            formula = practice_settings.default_materiality
        # Sprint 32: Include weighted materiality config
        if practice_settings.weighted_materiality:
            weighted_config = practice_settings.weighted_materiality

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

    return MaterialityConfig(
        formula=formula,
        session_override=session_threshold,
        weighted_config=weighted_config
    )
