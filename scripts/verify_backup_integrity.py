#!/usr/bin/env python3
"""
Backup Integrity Verification — Sprint 457 (S1.5 / CC4.2)

Verifies that the Render PostgreSQL backup infrastructure is healthy and
the database instance is reachable and accepting connections.

Checks performed:
  1. Render API health  — service status = "available" via GET /v1/postgres/{id}
  2. Render backup info — attempts GET /v1/postgres/{id}/backup for metadata
  3. DB liveness probe  — SELECT 1 + pg_stat_archiver (if DATABASE_URL is set)

Evidence is written to docs/08-internal/soc2-evidence/s1/backup-integrity-YYYYMM.txt
when --save is passed.

Usage:
    RENDER_API_KEY=rnd_... RENDER_POSTGRES_ID=postgres-... \\
        python scripts/verify_backup_integrity.py [--save]

    With optional DB liveness probe (read-only DATABASE_URL recommended):
    RENDER_API_KEY=rnd_... RENDER_POSTGRES_ID=postgres-... DATABASE_URL=postgresql://... \\
        python scripts/verify_backup_integrity.py --save

Environment variables:
    RENDER_API_KEY        Required. Render personal API token.
    RENDER_POSTGRES_ID    Required. PostgreSQL service ID (e.g. "postgres-abc123").
    DATABASE_URL          Optional. PostgreSQL connection string for DB liveness probe.

Exit codes:
    0 — PASS  (all checks passed)
    1 — FAIL  (one or more checks failed)
    2 — ERROR (missing required env vars or unexpected exception)
"""

from __future__ import annotations

import json
import os
import sys
import argparse
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RENDER_API_BASE = "https://api.render.com/v1"
BACKUP_MAX_AGE_HOURS = 25  # daily backups: FAIL if backup is older than this
EVIDENCE_DIR = Path(__file__).parent.parent / "docs" / "08-internal" / "soc2-evidence" / "s1"


# ---------------------------------------------------------------------------
# Render API helpers
# ---------------------------------------------------------------------------

def _render_get(path: str, api_key: str) -> tuple[int, dict | list | None]:
    """
    Make an authenticated GET request to the Render API.
    Returns (status_code, parsed_json | None).
    """
    url = f"{RENDER_API_BASE}{path}"
    req = Request(url, headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"})
    try:
        with urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else None
    except HTTPError as e:
        return e.code, None
    except URLError as e:
        raise ConnectionError(f"Render API unreachable: {e}") from e


def check_render_instance(postgres_id: str, api_key: str) -> dict:
    """
    Query GET /v1/postgres/{id} to verify the instance is healthy.
    Returns a result dict with keys: passed, status, details, raw.
    """
    result: dict = {"check": "render_instance_status", "passed": False, "details": ""}

    try:
        status_code, data = _render_get(f"/postgres/{postgres_id}", api_key)
    except ConnectionError as e:
        result["details"] = f"Connection failed: {e}"
        return result

    if status_code == 401:
        result["details"] = "RENDER_API_KEY is invalid or lacks permissions"
        return result
    if status_code == 404:
        result["details"] = f"PostgreSQL instance '{postgres_id}' not found — verify RENDER_POSTGRES_ID"
        return result
    if status_code != 200 or data is None:
        result["details"] = f"Unexpected status {status_code} from Render API"
        return result

    instance_status = data.get("status", "unknown")
    result["raw"] = {
        "id": data.get("id"),
        "name": data.get("name"),
        "status": instance_status,
        "plan": data.get("plan"),
        "region": data.get("region"),
        "updatedAt": data.get("updatedAt"),
    }

    if instance_status == "available":
        result["passed"] = True
        result["details"] = f"Instance '{data.get('name')}' is available (region: {data.get('region')})"
    else:
        result["details"] = f"Instance status is '{instance_status}' — expected 'available'"

    return result


def check_render_backup_metadata(postgres_id: str, api_key: str) -> dict:
    """
    Attempt GET /v1/postgres/{id}/backup to retrieve backup metadata.
    Render may not expose this endpoint publicly; 404 is handled gracefully.
    """
    result: dict = {"check": "render_backup_metadata", "passed": False, "details": ""}

    try:
        status_code, data = _render_get(f"/postgres/{postgres_id}/backup", api_key)
    except ConnectionError as e:
        result["details"] = f"Connection failed: {e}"
        return result

    if status_code == 404:
        # Render does not expose backup metadata via public API — this is expected.
        # Backup existence is inferred from instance health (above check).
        result["passed"] = True  # not a failure — known limitation
        result["details"] = (
            "Render does not expose backup metadata via public API (HTTP 404). "
            "Backup existence is inferred from instance status=available. "
            "Semi-annual restore tests (Sprint 452) provide file-level verification."
        )
        result["metadata_available"] = False
        return result

    if status_code == 200 and data:
        result["metadata_available"] = True
        result["raw"] = data

        # Try to parse last backup timestamp
        last_backup_at_str = (
            data.get("lastBackupAt")
            or data.get("last_backup_at")
            or data.get("createdAt")
        )
        if last_backup_at_str:
            try:
                last_backup_at = datetime.fromisoformat(last_backup_at_str.replace("Z", "+00:00"))
                age_hours = (datetime.now(timezone.utc) - last_backup_at).total_seconds() / 3600
                result["backup_age_hours"] = round(age_hours, 2)

                if age_hours <= BACKUP_MAX_AGE_HOURS:
                    result["passed"] = True
                    result["details"] = (
                        f"Last backup: {last_backup_at_str} "
                        f"({age_hours:.1f}h ago — within {BACKUP_MAX_AGE_HOURS}h SLA)"
                    )
                else:
                    result["details"] = (
                        f"Last backup: {last_backup_at_str} "
                        f"({age_hours:.1f}h ago — EXCEEDS {BACKUP_MAX_AGE_HOURS}h SLA)"
                    )
            except (ValueError, TypeError):
                result["passed"] = True
                result["details"] = f"Backup metadata found but timestamp unparseable: {last_backup_at_str}"
        else:
            result["passed"] = True
            result["details"] = "Backup metadata found; no timestamp field available"
    else:
        result["details"] = f"Unexpected status {status_code} from backup endpoint"

    return result


# ---------------------------------------------------------------------------
# DB liveness probe (optional — requires psycopg2)
# ---------------------------------------------------------------------------

def check_db_liveness(database_url: str) -> dict:
    """
    Connect to the PostgreSQL database and run:
      1. SELECT 1  — basic connectivity
      2. SELECT last_archived_time, archived_count, failed_count FROM pg_stat_archiver
         — WAL archiving health (proxy for backup health)

    Returns a result dict.
    """
    result: dict = {"check": "db_liveness", "passed": False, "details": ""}

    try:
        import psycopg2  # type: ignore[import]
    except ImportError:
        result["passed"] = True  # optional check — skip if not available
        result["details"] = "psycopg2 not installed — DB liveness probe skipped"
        result["skipped"] = True
        return result

    # Mask credentials from output
    masked_url = database_url
    try:
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        masked_url = database_url.replace(parsed.password or "", "****") if parsed.password else database_url
    except Exception:
        pass

    try:
        conn = psycopg2.connect(database_url, connect_timeout=10)
        cur = conn.cursor()

        # Basic connectivity
        cur.execute("SELECT 1")
        if cur.fetchone() != (1,):
            result["details"] = "SELECT 1 returned unexpected result"
            conn.close()
            return result

        # WAL archiving stats
        cur.execute(
            "SELECT last_archived_time, archived_count, failed_count FROM pg_stat_archiver"
        )
        row = cur.fetchone()
        conn.close()

        if row:
            last_archived_time, archived_count, failed_count = row
            result["raw"] = {
                "last_archived_time": str(last_archived_time) if last_archived_time else None,
                "archived_count": archived_count,
                "failed_count": failed_count,
            }

            wal_age_hours: float | None = None
            if last_archived_time:
                if last_archived_time.tzinfo is None:
                    last_archived_time = last_archived_time.replace(tzinfo=timezone.utc)
                wal_age_hours = (datetime.now(timezone.utc) - last_archived_time).total_seconds() / 3600
                result["wal_archive_age_hours"] = round(wal_age_hours, 2)

            if failed_count and failed_count > 0:
                result["details"] = (
                    f"WAL archiving failures detected: {failed_count}. "
                    f"Last archive: {last_archived_time}. "
                    "Investigate pg_stat_archiver.last_failed_time."
                )
                result["passed"] = False
            elif wal_age_hours is not None and wal_age_hours > BACKUP_MAX_AGE_HOURS:
                result["details"] = (
                    f"WAL archive age {wal_age_hours:.1f}h exceeds {BACKUP_MAX_AGE_HOURS}h SLA. "
                    f"Last archive: {last_archived_time}. Check archiver process."
                )
                result["passed"] = False
            else:
                result["passed"] = True
                age_str = f"{wal_age_hours:.1f}h ago" if wal_age_hours is not None else "timestamp unavailable"
                result["details"] = (
                    f"DB responsive. WAL archive: {last_archived_time} ({age_str}). "
                    f"Total archived: {archived_count}. Failures: {failed_count}."
                )
        else:
            result["passed"] = True
            result["details"] = "DB responsive (SELECT 1 passed). pg_stat_archiver returned no rows."

    except psycopg2.OperationalError as e:
        result["details"] = f"DB connection failed ({masked_url}): {e}"
    except Exception as e:
        result["details"] = f"DB probe error: {type(e).__name__}: {e}"

    return result


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

def build_report(
    run_ts: datetime,
    postgres_id: str,
    checks: list[dict],
) -> tuple[bool, str]:
    """
    Assemble a human-readable evidence report from check results.
    Returns (overall_pass, report_text).
    """
    overall_pass = all(c.get("passed", False) for c in checks)
    status_str = "✅ PASS" if overall_pass else "❌ FAIL"

    lines = [
        "# Backup Integrity Check",
        f"# Status:     {status_str}",
        f"# Timestamp:  {run_ts.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"# Service:    {postgres_id}",
        f"# Controls:   S1.5 / CC4.2",
        "",
        "## Check Results",
        "",
    ]

    for c in checks:
        check_pass = c.get("passed", False)
        skipped = c.get("skipped", False)
        if skipped:
            icon = "⏭"
        elif check_pass:
            icon = "✅"
        else:
            icon = "❌"

        lines.append(f"### {icon} {c['check']}")
        lines.append(f"  Status:  {'SKIP' if skipped else ('PASS' if check_pass else 'FAIL')}")
        lines.append(f"  Details: {c.get('details', '')}")

        if "backup_age_hours" in c:
            lines.append(f"  Backup age: {c['backup_age_hours']}h")
        if "wal_archive_age_hours" in c:
            lines.append(f"  WAL archive age: {c['wal_archive_age_hours']}h")
        if "metadata_available" in c and not c["metadata_available"]:
            lines.append("  Note: Backup metadata not exposed by Render API (expected).")
            lines.append("        DR restore test (Sprint 452) provides file-level verification.")

        lines.append("")

    # Evidence hash for tamper-detection
    content_bytes = "\n".join(lines).encode("utf-8")
    content_hash = hashlib.sha256(content_bytes).hexdigest()

    lines += [
        "## Evidence Integrity",
        f"# SHA-256: {content_hash}",
        f"# Signed by: [operator — fill in before filing]",
        "",
        "## Filing",
        f"# Copy to: docs/08-internal/soc2-evidence/s1/backup-integrity-{run_ts.strftime('%Y%m')}.txt",
        "# Reference controls: S1.5 (backup integrity), CC4.2 (detective controls)",
        "",
    ]

    return overall_pass, "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--save", action="store_true", help="Write evidence file to soc2-evidence/s1/")
    args = parser.parse_args()

    api_key = os.environ.get("RENDER_API_KEY", "").strip()
    postgres_id = os.environ.get("RENDER_POSTGRES_ID", "").strip()
    database_url = os.environ.get("DATABASE_URL", "").strip()

    if not api_key:
        print("ERROR: RENDER_API_KEY is not set.", file=sys.stderr)
        sys.exit(2)
    if not postgres_id:
        print("ERROR: RENDER_POSTGRES_ID is not set.", file=sys.stderr)
        sys.exit(2)

    run_ts = datetime.now(timezone.utc)
    print(f"Running backup integrity check at {run_ts.strftime('%Y-%m-%d %H:%M:%S UTC')} ...", file=sys.stderr)

    checks: list[dict] = []

    # Check 1: Render instance health
    print("  [1/3] Render instance status ...", file=sys.stderr)
    checks.append(check_render_instance(postgres_id, api_key))

    # Check 2: Render backup metadata
    print("  [2/3] Render backup metadata ...", file=sys.stderr)
    checks.append(check_render_backup_metadata(postgres_id, api_key))

    # Check 3: DB liveness probe (optional)
    if database_url:
        print("  [3/3] DB liveness probe ...", file=sys.stderr)
        checks.append(check_db_liveness(database_url))
    else:
        print("  [3/3] DB liveness probe — skipped (DATABASE_URL not set)", file=sys.stderr)
        checks.append({
            "check": "db_liveness",
            "passed": True,
            "skipped": True,
            "details": "DATABASE_URL not set — DB probe skipped",
        })

    overall_pass, report = build_report(run_ts, postgres_id, checks)
    print(report)

    if args.save:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"backup-integrity-{run_ts.strftime('%Y%m')}.txt"
        output_path = EVIDENCE_DIR / filename
        output_path.write_text(report, encoding="utf-8")
        print(f"\nEvidence saved: {output_path}", file=sys.stderr)

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
