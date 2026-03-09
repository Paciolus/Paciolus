"""
engine_framework.py — Shared audit testing engine pipeline (Sprint 519 Phase 3)

Defines AuditEngineBase with the common pipeline sequence:
  detect columns → apply overrides → parse → quality checks →
  enrich → test battery → composite score → build result

Each tool-specific engine (JE, AP, Payroll) extends this base class
and implements only the abstract methods for its domain.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class AuditEngineBase(ABC):
    """Abstract base class for audit testing engines.

    Provides the shared pipeline orchestration via run_pipeline().
    Subclasses implement the tool-specific steps as abstract methods.
    """

    def __init__(self, config: Any = None):
        self.config = config
        self.detection: Any = None  # Set during pipeline execution

    @abstractmethod
    def detect_columns(self, column_names: list[str]) -> Any:
        """Detect column mappings from header names.

        Returns a tool-specific column detection result object.
        """
        ...

    @abstractmethod
    def apply_column_overrides(self, detection: Any, column_mapping: dict) -> Any:
        """Apply manual column mapping overrides to the detection result.

        Must set detection.overall_confidence = 1.0 after applying overrides.
        Returns the (possibly new) detection object.
        """
        ...

    @abstractmethod
    def parse_data(self, rows: list[dict], detection: Any) -> list:
        """Parse raw rows into typed domain objects using detected columns."""
        ...

    @abstractmethod
    def run_quality_checks(self, entries: list, detection: Any) -> Any:
        """Assess data quality of parsed entries."""
        ...

    @abstractmethod
    def run_tests(self, entries: list) -> Any:
        """Run the tool-specific test battery.

        Return type varies by engine (list for AP/Payroll,
        tuple of (results, benford_data) for JE).
        """
        ...

    @abstractmethod
    def compute_score(self, test_results: list, entry_count: int) -> Any:
        """Calculate composite score from test results."""
        ...

    @abstractmethod
    def build_result(
        self,
        composite: Any,
        test_output: Any,
        data_quality: Any,
        detection: Any,
        entries: list,
        enrichment: Any,
    ) -> Any:
        """Assemble the final result object from pipeline outputs."""
        ...

    def extract_test_results(self, test_output: Any) -> list:
        """Extract the test results list from the test battery output.

        Override if run_tests() returns more than a plain list
        (e.g., JE returns (test_results, benford_data) tuple).
        """
        return test_output

    def enrich(self, entries: list) -> Any:
        """Optional post-parse enrichment hook.

        Override for tool-specific enrichment (e.g., multi-currency detection).
        Returns enrichment data or None.
        """
        return None

    def cleanup(self, rows: list[dict]) -> None:
        """Optional cleanup hook after result is built.

        Override for Zero-Storage compliance (e.g., rows.clear()).
        """
        pass

    def run_pipeline(
        self,
        rows: list[dict],
        column_names: list[str],
        column_mapping: Optional[dict] = None,
    ) -> Any:
        """Execute the shared testing pipeline.

        Sequence: detect → override → parse → quality → enrich →
                  test battery → composite score → build result → cleanup
        """
        # 1. Detect columns
        detection = self.detect_columns(column_names)

        # 2. Apply manual overrides if provided
        if column_mapping:
            detection = self.apply_column_overrides(detection, column_mapping)

        # Store detection for subclass access in run_tests()
        self.detection = detection

        # 3. Parse raw data into domain objects
        entries = self.parse_data(rows, detection)

        # 4. Assess data quality
        data_quality = self.run_quality_checks(entries, detection)

        # 5. Optional enrichment
        enrichment = self.enrich(entries)

        # 6. Run test battery
        test_output = self.run_tests(entries)

        # 7. Extract test results list for scoring
        test_results = self.extract_test_results(test_output)

        # 8. Calculate composite score
        composite = self.compute_score(test_results, len(entries))

        # 9. Build final result
        result = self.build_result(
            composite=composite,
            test_output=test_output,
            data_quality=data_quality,
            detection=detection,
            entries=entries,
            enrichment=enrichment,
        )

        # 10. Cleanup
        self.cleanup(rows)

        return result
