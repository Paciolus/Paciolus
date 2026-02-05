"""Centralized number formatting utilities for Paciolus.

This module provides consistent formatting for financial data across the codebase.
Replaces scattered round() calls with semantic formatting methods.

Sprint 41: Performance Quick Wins - Shared Utilities
"""

from typing import Optional


class NumberFormatter:
    """Centralized number formatting with consistent precision across the application.

    Usage:
        from format_utils import fmt

        # Currency formatting
        fmt.currency(1234567.89)  # "$1,234,567.89"

        # Percentage formatting
        fmt.percentage(0.1567)    # "15.7%"

        # Ratio formatting
        fmt.ratio(2.345)          # "2.35x"

        # Days formatting (for DIO, DSO, etc.)
        fmt.days(45.6)            # "46 days"

        # Raw rounding (when you need the number, not string)
        fmt.round_to(123.456789, 2)  # 123.46
    """

    # Precision constants - single source of truth
    PRECISION_CURRENCY = 2
    PRECISION_PERCENTAGE = 1
    PRECISION_RATIO = 2
    PRECISION_DAYS = 0
    PRECISION_GENERIC = 2

    @staticmethod
    def currency(value: Optional[float], decimals: int = PRECISION_CURRENCY) -> str:
        """Format value as currency with thousand separators.

        Args:
            value: The numeric value to format
            decimals: Number of decimal places (default: 2)

        Returns:
            Formatted string like "$1,234,567.89" or "N/A" if value is None
        """
        if value is None:
            return "N/A"
        return f"${value:,.{decimals}f}"

    @staticmethod
    def percentage(
        value: Optional[float],
        decimals: int = PRECISION_PERCENTAGE,
        multiply: bool = True
    ) -> str:
        """Format value as percentage.

        Args:
            value: The numeric value to format
            decimals: Number of decimal places (default: 1)
            multiply: If True, multiply by 100 (value is decimal like 0.15)
                     If False, value is already a percentage (like 15)

        Returns:
            Formatted string like "15.7%" or "N/A" if value is None
        """
        if value is None:
            return "N/A"
        display_value = value * 100 if multiply else value
        return f"{display_value:.{decimals}f}%"

    @staticmethod
    def ratio(value: Optional[float], decimals: int = PRECISION_RATIO) -> str:
        """Format value as ratio with 'x' suffix.

        Args:
            value: The numeric value to format
            decimals: Number of decimal places (default: 2)

        Returns:
            Formatted string like "2.35x" or "N/A" if value is None
        """
        if value is None:
            return "N/A"
        return f"{value:.{decimals}f}x"

    @staticmethod
    def days(value: Optional[float], decimals: int = PRECISION_DAYS) -> str:
        """Format value as days (for DIO, DSO, DPO metrics).

        Args:
            value: The numeric value to format
            decimals: Number of decimal places (default: 0)

        Returns:
            Formatted string like "46 days" or "N/A" if value is None
        """
        if value is None:
            return "N/A"
        return f"{value:.{decimals}f} days"

    @staticmethod
    def round_to(value: Optional[float], places: int = PRECISION_GENERIC) -> Optional[float]:
        """Round value to specified decimal places.

        This is the single source of truth for rounding precision.
        Use this instead of raw round() calls throughout the codebase.

        Args:
            value: The numeric value to round
            places: Number of decimal places (default: 2)

        Returns:
            Rounded float or None if value is None
        """
        if value is None:
            return None
        return round(value, places)

    @staticmethod
    def compact(value: Optional[float]) -> str:
        """Format large numbers in compact notation (K, M, B).

        Args:
            value: The numeric value to format

        Returns:
            Formatted string like "1.2M" or "N/A" if value is None
        """
        if value is None:
            return "N/A"

        abs_value = abs(value)
        sign = "-" if value < 0 else ""

        if abs_value >= 1_000_000_000:
            return f"{sign}{abs_value / 1_000_000_000:.1f}B"
        elif abs_value >= 1_000_000:
            return f"{sign}{abs_value / 1_000_000:.1f}M"
        elif abs_value >= 1_000:
            return f"{sign}{abs_value / 1_000:.1f}K"
        else:
            return f"{sign}{abs_value:.0f}"

    @staticmethod
    def display_value(
        value: Optional[float],
        format_type: str = "currency",
        decimals: Optional[int] = None
    ) -> str:
        """Generic display value formatter with format type selection.

        Args:
            value: The numeric value to format
            format_type: One of "currency", "percentage", "ratio", "days", "compact"
            decimals: Optional override for decimal places

        Returns:
            Formatted string appropriate for the format type
        """
        if value is None:
            return "N/A"

        formatters = {
            "currency": lambda v, d: NumberFormatter.currency(v, d or NumberFormatter.PRECISION_CURRENCY),
            "percentage": lambda v, d: NumberFormatter.percentage(v, d or NumberFormatter.PRECISION_PERCENTAGE),
            "ratio": lambda v, d: NumberFormatter.ratio(v, d or NumberFormatter.PRECISION_RATIO),
            "days": lambda v, d: NumberFormatter.days(v, d or NumberFormatter.PRECISION_DAYS),
            "compact": lambda v, d: NumberFormatter.compact(v),
        }

        formatter = formatters.get(format_type, formatters["currency"])
        return formatter(value, decimals)


# Singleton instance for convenient import
# Usage: from format_utils import fmt
fmt = NumberFormatter()


# Convenience functions for direct import
# Usage: from format_utils import round_to, format_currency
def round_to(value: Optional[float], places: int = 2) -> Optional[float]:
    """Convenience function for NumberFormatter.round_to()."""
    return fmt.round_to(value, places)


def format_currency(value: Optional[float], decimals: int = 2) -> str:
    """Convenience function for NumberFormatter.currency()."""
    return fmt.currency(value, decimals)


def format_percentage(value: Optional[float], decimals: int = 1, multiply: bool = True) -> str:
    """Convenience function for NumberFormatter.percentage()."""
    return fmt.percentage(value, decimals, multiply)


def format_ratio(value: Optional[float], decimals: int = 2) -> str:
    """Convenience function for NumberFormatter.ratio()."""
    return fmt.ratio(value, decimals)
