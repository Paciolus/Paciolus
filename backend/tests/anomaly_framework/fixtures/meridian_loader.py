"""Meridian Capital Group fixture loader.

Loads QA CSV files from tests/qa/ for use in anomaly testing. These files
represent realistic trial balance data from the Meridian Capital Group, LLC
synthetic client.
"""

from pathlib import Path

import pandas as pd

_QA_DIR = Path(__file__).resolve().parent.parent.parent / "qa"


def list_qa_files() -> list[Path]:
    """Return all CSV files in the tests/qa/ directory."""
    if not _QA_DIR.exists():
        return []
    return sorted(_QA_DIR.glob("*.csv"))


def load_qa_csv(filename: str) -> pd.DataFrame:
    """Load a specific QA CSV file as a DataFrame.

    Args:
        filename: Name of the CSV file (e.g., 'paciolus_test_tb_cascade_fy2025.csv').

    Returns:
        DataFrame with the trial balance data.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = _QA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"QA fixture not found: {path}")
    return pd.read_csv(path)


def load_qa_csv_bytes(filename: str) -> bytes:
    """Load a QA CSV file as raw bytes for audit_trial_balance_streaming.

    Args:
        filename: Name of the CSV file.

    Returns:
        Raw bytes of the CSV file.
    """
    path = _QA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"QA fixture not found: {path}")
    return path.read_bytes()
