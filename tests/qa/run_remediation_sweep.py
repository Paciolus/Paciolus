"""Diagnostic Remediation Test Harness (Sprint 665).

Runs the six TB test files in `tests/evaluatingfiles/` through the full
parse → preflight → diagnostic pipeline and dumps a structured JSON record
per file. Each sprint in the 666–671 series re-runs this script against the
fresh code and diffs the resulting JSON against the Sprint 665 baseline.

Usage:
    python tests/qa/run_remediation_sweep.py [--out <subdir>]

Output:
    reports/remediation/<subdir>/<stem>.json   (default subdir: "baseline")
    One-line summary per file printed to stdout.

This is a CEO-facing validator, not a pytest regression gate. Hardcoded
expected values would fight us across the six remediation sprints; the
diffable JSON is simpler and matches how we'll actually review the fixes.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from audit.pipeline import audit_trial_balance_streaming  # noqa: E402
from preflight_engine import run_preflight  # noqa: E402
from preflight_memo_generator import _build_conclusion  # noqa: E402
from shared.helpers import parse_uploaded_file_by_format  # noqa: E402
from shared.intake_utils import count_raw_data_rows  # noqa: E402

EVALUATING_DIR = ROOT / "tests" / "evaluatingfiles"
REPORTS_DIR = ROOT / "reports" / "remediation"

TEST_FILES: list[str] = [
    "tb_hartwell_clean.csv",
    "tb_hartwell_outofbalance.csv",
    "tb_no_headers.csv",
    "tb_unusual_accounts.csv",
    "tb_hartwell_adjusted.pdf",
    "tb_hartwell.docx",
]


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    if isinstance(obj, bytes):
        return f"<{len(obj)} bytes>"
    return str(obj)


def _capture_error(label: str, exc: BaseException) -> dict:
    return {
        "stage": label,
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(limit=6),
    }


def _slim_diagnostic(diag: dict) -> dict:
    """Keep only the fields the remediation brief asks about.

    The full streaming result is ~100+ keys; most are irrelevant for the
    intake/column/scoring fixes we're validating. This slim view is what
    we'll diff sprint-to-sprint.
    """
    rs = diag.get("risk_summary") or {}
    abnormals = diag.get("abnormal_balances") or []
    return {
        "analysis_failed": diag.get("analysis_failed", False),
        "failure_reason": diag.get("failure_reason"),
        "error_message": diag.get("error_message"),
        "balanced": diag.get("balanced"),
        "total_debits": diag.get("total_debits"),
        "total_credits": diag.get("total_credits"),
        "difference": diag.get("difference"),
        "row_count": diag.get("row_count"),
        "totals_rows_excluded": diag.get("totals_rows_excluded"),
        "material_count": diag.get("material_count"),
        "immaterial_count": diag.get("immaterial_count"),
        "informational_count": diag.get("informational_count"),
        "has_risk_alerts": diag.get("has_risk_alerts"),
        "risk_score": rs.get("risk_score"),
        "risk_tier": rs.get("risk_tier"),
        "risk_factors": rs.get("risk_factors"),
        "coverage_pct": rs.get("coverage_pct"),
        "anomaly_types": rs.get("anomaly_types"),
        "abnormal_balance_count": len(abnormals),
        "abnormal_balances": [
            {
                "account": ab.get("account"),
                "type": ab.get("type"),
                "issue": ab.get("issue"),
                "amount": ab.get("amount"),
                "materiality": ab.get("materiality"),
                "anomaly_type": ab.get("anomaly_type"),
                "severity": ab.get("severity"),
                "confidence": ab.get("confidence"),
            }
            for ab in abnormals[:25]
        ],
        "abnormal_balances_truncated": len(abnormals) > 25,
        "classification_quality": {
            "score": (diag.get("classification_quality") or {}).get("score"),
            "issue_count": len((diag.get("classification_quality") or {}).get("issues", [])),
        }
        if diag.get("classification_quality")
        else None,
    }


def run_one(path: Path) -> dict:
    record: dict[str, Any] = {
        "filename": path.name,
        "size_bytes": path.stat().st_size if path.exists() else None,
        "errors": [],
    }

    try:
        file_bytes = path.read_bytes()
    except OSError as e:
        record["errors"].append(_capture_error("read", e))
        return record

    # ── Parse ──
    column_names: list[str] | None = None
    rows: list[dict] | None = None
    try:
        column_names, rows = parse_uploaded_file_by_format(file_bytes, path.name)
        record["parse"] = {
            "column_names": column_names,
            "row_count": len(rows),
            "first_row_sample": rows[0] if rows else None,
            "last_row_sample": rows[-1] if rows else None,
        }
    except Exception as e:
        record["errors"].append(_capture_error("parse", e))

    # ── PreFlight (only if parse succeeded) ──
    if column_names is not None and rows is not None:
        try:
            raw_count = count_raw_data_rows(file_bytes, path.name)
            preflight = run_preflight(
                column_names, rows, path.name, rows_submitted=raw_count
            )
            preflight_dict = preflight.to_dict()
            # Sprint 667 Issue 4: capture the rendered conclusion so we
            # can grep it for the forbidden phrase and verify the
            # severity-keyed branching landed correctly.
            try:
                preflight_dict["rendered_conclusion"] = _build_conclusion(preflight_dict, path.name)
            except Exception as conclusion_exc:  # noqa: BLE001 — keep harness resilient
                preflight_dict["rendered_conclusion_error"] = str(conclusion_exc)
            record["preflight"] = preflight_dict
        except Exception as e:
            record["errors"].append(_capture_error("preflight", e))

    # ── Diagnostic (always attempt — independent pipeline) ──
    try:
        diag = audit_trial_balance_streaming(file_bytes, path.name)
        record["diagnostic"] = _slim_diagnostic(diag)
    except Exception as e:
        record["errors"].append(_capture_error("diagnostic", e))

    return record


def _one_line_summary(fname: str, record: dict) -> str:
    parts: list[str] = []
    parse = record.get("parse") or {}
    if parse:
        parts.append(f"rows={parse.get('row_count')}")

    preflight = record.get("preflight") or {}
    if preflight:
        intake = preflight.get("intake") or {}
        if intake:
            parts.append(
                f"intake={intake.get('rows_submitted')}/{intake.get('rows_accepted')}/"
                f"{intake.get('rows_rejected')}/{intake.get('rows_excluded')}"
            )
        score = preflight.get("readiness_score")
        label = preflight.get("readiness_label")
        parts.append(f"pf={label}({score})")
        bc = preflight.get("balance_check") or {}
        if bc:
            diff = bc.get("difference") or 0
            parts.append(f"diff=${diff:,.2f}")

    diag = record.get("diagnostic") or {}
    if diag:
        if diag.get("analysis_failed"):
            parts.append(f"DIAG_FAILED[{diag.get('failure_reason')}]")
        else:
            score = diag.get("risk_score")
            tier = diag.get("risk_tier")
            parts.append(f"diag={tier}({score})")
            parts.append(f"mat={diag.get('material_count', 0)}")
            parts.append(f"anom={diag.get('abnormal_balance_count', 0)}")

    errors = record.get("errors") or []
    if errors:
        stages = ",".join(e["stage"] for e in errors)
        parts.append(f"ERRORS[{stages}]")

    return f"  {fname:36s}  " + "  ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description="Diagnostic remediation sweep (Sprint 665)")
    ap.add_argument(
        "--out",
        default="baseline",
        help="Subdirectory under reports/remediation/ to write JSON dumps (default: baseline)",
    )
    args = ap.parse_args()

    out_dir = REPORTS_DIR / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    started = datetime.now(timezone.utc)
    print(f"[{started.isoformat(timespec='seconds')}] Paciolus Diagnostic Remediation Sweep")
    print(f"  source: {EVALUATING_DIR}")
    print(f"  output: {out_dir}")
    print()

    written = 0
    missing = 0
    for fname in TEST_FILES:
        path = EVALUATING_DIR / fname
        if not path.exists():
            print(f"  {fname:36s}  SKIP — file not found")
            missing += 1
            continue

        record = run_one(path)

        json_path = out_dir / f"{path.stem}.json"
        json_path.write_text(
            json.dumps(record, default=_json_default, indent=2, sort_keys=False),
            encoding="utf-8",
        )
        written += 1

        print(_one_line_summary(fname, record))

    print()
    print(f"wrote {written} dumps, missing {missing}, elapsed {(datetime.now(timezone.utc) - started).total_seconds():.1f}s")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
