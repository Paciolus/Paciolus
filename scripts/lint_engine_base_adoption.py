#!/usr/bin/env python3
"""AuditEngineBase adoption lint (Sprint 726 Phase 1 — warning only).

Scans ``backend/*_engine.py`` and ``backend/*_testing_engine.py`` and reports
any testing-engine module that does not contain a class subclassing
``AuditEngineBase``. The reference is the 10-step pipeline ABC in
``backend/engine_framework.py`` (Sprint 519); subclassing it gives every
engine a uniform pipeline signature and makes drift mechanically visible.

Phase 1 (this script): emit findings to stdout, **exit 0**. Wired into CI
as advisory output so the noise lands in the build log without blocking PRs.

Phase 2 (Sprint 727+): once the migration backfill lands, this script gets
its exit-code switched to 1 on findings, becoming a hard gate. The migration
schedule is sprint-by-sprint per ADR-013 (one engine per sub-sprint).

Usage:
    python scripts/lint_engine_base_adoption.py [--strict]

``--strict`` flips exit code to non-zero on findings (used to manually verify
the gate is working before Sprint 727 promotes it).
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"

# These engines are NOT testing engines — they're domain engines that don't
# fit the AuditEngineBase 10-step pipeline (which is "detect columns → parse
# → quality → tests → score → result" — the testing-tool shape). Excluded
# from the lint by name.
#
# Sprint 727 added the calculator/aggregator/indicator engines to this set
# after per-engine triage. Each entry has a one-line rationale; misclassi-
# fications are recoverable in a future PR.
NON_TESTING_ENGINES: frozenset[str] = frozenset({
    # --- Sprint 726 initial blocklist ---
    "audit_engine.py",                  # Top-level orchestrator, not a tool
    "engine_framework.py",              # The base class itself
    "benchmark_engine.py",              # Reference data, not a test battery
    "composite_risk_engine.py",         # ISA 315 scoring, not a tool
    "currency_engine.py",               # Side-car validation, not a tool
    "engagement_dashboard_engine.py",   # UI surface
    "flux_engine.py",                   # Analytical procedure (different pipeline shape)
    "going_concern_engine.py",          # Indicator engine (different pipeline shape)
    "preflight_engine.py",              # Pre-pipeline data quality
    "recon_engine.py",                  # TB diagnostics scorer
    "leasing_engine.py",                # Indicator engine
    "cutoff_risk_engine.py",            # Indicator engine
    "depreciation_engine.py",           # Helper used by FA testing engine
    "account_risk_heatmap_engine.py",   # Aggregation / view engine
    "form_1099_engine.py",              # Tax form prep, different pipeline
    "form_w2_w3_engine.py",             # Tax form prep, different pipeline
    "book_to_tax_engine.py",            # Reconciliation, different pipeline
    "intercompany_elimination_engine.py",  # Different pipeline
    "segregation_of_duties_engine.py",  # Different pipeline
    "bank_reconciliation_engine.py",    # Different pipeline (matching, not test battery)
    "multi_period_engine.py",           # Comparison, not a test battery

    # --- Sprint 727 triage additions (per-engine rationale below) ---
    "accrual_completeness_engine.py",   # Descriptive metrics + run-rate comparison; no test battery, no composite_score
    "cash_flow_projector_engine.py",    # 30/60/90-day deterministic forecast (calculator); no flagging
    "expense_category_engine.py",       # ISA 520 expense decomposition into ratios; analytical, not a test battery
    "lease_accounting_engine.py",       # ASC 842 classification + amortization (calculator)
    "lease_diagnostic_engine.py",       # Four presence/absence checks; no scoring or flagging
    "loan_amortization_engine.py",      # Period-by-period schedule generator (pure calculator)
    "population_profile_engine.py",     # Descriptive stats (mean/median/Gini/Benford); aggregator, not a test battery
})

# Sprint 727 borderline list — engines that produce some testing-shaped output
# but don't cleanly fit the 10-step pipeline. Surface as findings (NOT in the
# blocklist) so a future migration sprint can decide per-engine whether to
# adapt them or move them to the blocklist. Listed here as documentation for
# the human picking up Sprint 727's actual migrations.
#
#   ratio_engine.py             — Financial ratios with threshold bands (warning/adequate/strong)
#                                 Could adapt: treat each band as a pass/fail "test"; needs design decision
#                                 on whether to emit flagged_entries.
#   sampling_engine.py          — ISA 530 statistical-sampling orchestrator (MUS + Stringer)
#                                 Different pipeline shape (design → select → evaluate → UEL conclusion)
#                                 Possibly its own framework or a future Sprint epic.
#   three_way_match_engine.py   — PO/invoice/receipt matcher with variance flags
#                                 Hybrid: deterministic matching but flagged-entry-shaped output.
#                                 Could fit with adaptation; needs alignment on what counts as a "test".
#   w2_reconciliation_engine.py — Tax-form reconciliation; classification deferred to migration sprint.
BORDERLINE_ENGINES: frozenset[str] = frozenset({
    "ratio_engine.py",
    "sampling_engine.py",
    "three_way_match_engine.py",
    "w2_reconciliation_engine.py",
})


def _is_testing_engine(path: Path) -> bool:
    """Filter to the testing-engine modules the migration targets.

    ``*_testing_engine.py`` always counts. Otherwise, exclude domain engines
    that don't fit the test-battery pipeline shape.
    """
    name = path.name
    if name.endswith("_testing_engine.py"):
        return True
    if not name.endswith("_engine.py"):
        return False
    return name not in NON_TESTING_ENGINES


def _subclasses_audit_engine_base(source: str) -> bool:
    """Return True when the module defines a class with AuditEngineBase as a base."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                # Match both ``AuditEngineBase`` and ``module.AuditEngineBase``.
                if isinstance(base, ast.Name) and base.id == "AuditEngineBase":
                    return True
                if isinstance(base, ast.Attribute) and base.attr == "AuditEngineBase":
                    return True
    return False


def find_off_pattern_engines() -> list[Path]:
    """Return testing-engine modules that don't subclass AuditEngineBase."""
    findings: list[Path] = []
    for path in sorted(BACKEND_ROOT.glob("*_engine.py")):
        if not _is_testing_engine(path):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not _subclasses_audit_engine_base(source):
            findings.append(path)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on findings (default: exit 0 / warning-only).",
    )
    args = parser.parse_args(argv)

    findings = find_off_pattern_engines()

    if not findings:
        print("AuditEngineBase adoption: all testing engines on-pattern.")
        return 0

    print(
        f"AuditEngineBase adoption: {len(findings)} testing engine(s) "
        f"don't subclass AuditEngineBase (Sprint 726 Phase 1 — advisory):"
    )
    for path in findings:
        print(f"  - {path.relative_to(REPO_ROOT)}")
    print()
    print("Migration plan: see docs/03-engineering/adr-013-audit-engine-base.md")
    print("Phase 1 (Sprint 726): warning-only — this script exits 0.")
    print("Phase 2 (Sprint 727): exit-code flips to 1; new off-pattern engines block CI.")

    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
