#!/usr/bin/env python3
"""
Backup integrity verification — Sprint 457, rewritten for Neon + R2 in Sprint 778b.

The original targeted the Render Postgres API. Production moved to **Neon** in
Phase 1 (2026-04-09) and the Render instance was deleted 2026-04-22, so every
check it made addressed a database that no longer existed. This version checks
the two recovery mechanisms that actually exist:

  1. ``r2_latest_backup``     — the newest pg_dump in ``paciolus-backups`` is
                                complete (dump + manifest), fresh enough, and
                                its bytes hash to the manifest's sha256.
  2. ``neon_pitr_window``     — Neon's *actual* history-retention window, read
                                from the Neon API, is at least the floor. The
                                figure is read live, never assumed from docs.
  3. ``neon_default_branch``  — the production branch reports ``ready``.

Each check is independent: a missing Neon key does not stop the R2 check.

Verdicts and exit codes (same contract as ``scripts/pg_backup.py``):
    0  PASS        — every check ran and passed
    1  FAIL        — at least one check ran and failed
    2  UNVERIFIED  — nothing failed, but at least one check could not run
                     because a secret is unset; the missing names are listed

UNVERIFIED exits non-zero on purpose (Sprint 778a): a check that is green
because it never ran is a false green.

Environment:
    R2_BACKUPS_ENDPOINT, R2_BACKUPS_BUCKET,
    R2_BACKUPS_ACCESS_KEY_ID, R2_BACKUPS_SECRET_ACCESS_KEY   — check 1
    NEON_API_KEY, NEON_PROJECT_ID                              — checks 2, 3
    BACKUP_MAX_AGE_HOURS   optional, default 26 (daily cron + slack)
    PITR_MIN_DAYS          optional, default 1 (must bridge two daily dumps)

Usage:
    python scripts/verify_backup_integrity.py [--save] [--only neon_pitr_window]
        [--json result.json] [--report report.md]

Runbook: docs/runbooks/backup-restore.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pg_backup import (  # noqa: E402 — script-relative import
    DEFAULT_PREFIX,
    EXIT_CODES,
    FAIL,
    PASS,
    R2_ENV,
    UNVERIFIED,
    group_backups,
    list_objects,
    make_r2_client,
    missing_env,
    overall_verdict,
    read_manifest,
    sha256_stream,
    utf8_stdio,
)

NEON_API_BASE = "https://console.neon.tech/api/v2"
NEON_ENV = ("NEON_API_KEY", "NEON_PROJECT_ID")
DEFAULT_MAX_AGE_HOURS = 26.0
DEFAULT_PITR_MIN_DAYS = 1.0
EVIDENCE_DIR = Path(__file__).parent.parent / "docs" / "08-internal" / "soc2-evidence" / "s1"
CHECK_NAMES = ("r2_latest_backup", "neon_pitr_window", "neon_default_branch")

HttpGet = Callable[[str, Mapping[str, str]], tuple[int, Any]]


def _result(check: str, status: str, details: str, **extra: Any) -> dict:
    return {"check": check, "status": status, "details": details, **extra}


def _unverified(check: str, missing: list[str]) -> dict:
    return _result(check, UNVERIFIED, "UNVERIFIED — missing secret " + ", ".join(missing), missing=missing)


# ---------------------------------------------------------------------------
# Check 1: R2
# ---------------------------------------------------------------------------


def check_r2_latest_backup(
    client: Any,
    bucket: str,
    prefix: str = DEFAULT_PREFIX,
    max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
    now: datetime | None = None,
) -> dict:
    name = "r2_latest_backup"
    now = now or datetime.now(timezone.utc)
    try:
        backups = group_backups(list_objects(client, bucket, prefix))
    except Exception as exc:  # noqa: BLE001 — credentials present but unusable is a FAIL
        return _result(name, FAIL, f"R2 listing failed: {type(exc).__name__}: {exc}")
    if not backups:
        return _result(name, FAIL, f"no backups under s3://{bucket}/{prefix} — the pg_dump job has never succeeded")

    newest = backups[0]
    age_h = round((now - newest.ts).total_seconds() / 3600, 2)
    extra = {"stem": newest.stem, "backup_age_hours": age_h, "backup_count": sum(b.complete for b in backups)}
    if not newest.complete:
        part = "manifest" if newest.manifest is None else "dump"
        # An in-flight run has a dump but no manifest yet; fall back to the
        # newest complete set for freshness, but say what was seen.
        complete = [b for b in backups if b.complete]
        if newest.manifest is not None or not complete:
            return _result(name, FAIL, f"newest backup {newest.stem} is missing its {part}", **extra)
        newest = complete[0]
        age_h = round((now - newest.ts).total_seconds() / 3600, 2)
        extra.update(stem=newest.stem, backup_age_hours=age_h)

    if age_h > max_age_hours:
        return _result(name, FAIL, f"newest backup is {age_h}h old (limit {max_age_hours}h): {newest.stem}", **extra)

    try:
        manifest = read_manifest(client, bucket, newest.stem)
        body = client.get_object(Bucket=bucket, Key=f"{newest.stem}.dump")["Body"]
        digest, size = sha256_stream(body)
    except Exception as exc:  # noqa: BLE001
        return _result(name, FAIL, f"could not read {newest.stem}: {type(exc).__name__}: {exc}", **extra)

    extra.update(dump_bytes=size, alembic_version=manifest.get("alembic_version"), tables=manifest.get("table_count"))
    if size != manifest.get("dump_bytes"):
        return _result(name, FAIL, f"size {size} != manifest {manifest.get('dump_bytes')}", **extra)
    if digest != manifest.get("dump_sha256"):
        return _result(name, FAIL, f"sha256 {digest[:16]} != manifest {str(manifest.get('dump_sha256'))[:16]}", **extra)
    return _result(
        name,
        PASS,
        f"{newest.stem} — {age_h}h old, {size:,} bytes, sha256 verified, "
        f"{manifest.get('table_count')} tables / {manifest.get('total_rows')} rows",
        **extra,
    )


# ---------------------------------------------------------------------------
# Checks 2 + 3: Neon API
# ---------------------------------------------------------------------------


def neon_http_get(url: str, headers: Mapping[str, str]) -> tuple[int, Any]:
    req = Request(url, headers=dict(headers))
    try:
        with urlopen(req, timeout=20) as resp:  # noqa: S310 — fixed https base
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else None
    except HTTPError as e:
        return e.code, None
    except URLError as e:
        raise ConnectionError(f"Neon API unreachable: {e.reason}") from e


def _neon(path: str, api_key: str, http_get: HttpGet) -> tuple[int, Any]:
    return http_get(f"{NEON_API_BASE}{path}", {"Authorization": f"Bearer {api_key}", "Accept": "application/json"})


def _neon_error(name: str, code: int) -> dict:
    hint = {
        401: "NEON_API_KEY is invalid or revoked",
        403: "NEON_API_KEY lacks access to the project",
        404: "NEON_PROJECT_ID not found",
    }.get(code, "unexpected response")
    return _result(name, FAIL, f"Neon API HTTP {code}: {hint}")


def check_neon_pitr(api_key: str, project_id: str, min_days: float, http_get: HttpGet = neon_http_get) -> dict:
    """Read ``project.history_retention_seconds`` — the live PITR window."""
    name = "neon_pitr_window"
    try:
        code, data = _neon(f"/projects/{project_id}", api_key, http_get)
    except ConnectionError as exc:
        return _result(name, FAIL, str(exc))
    if code != 200 or not isinstance(data, dict) or "project" not in data:
        return _neon_error(name, code)
    project = data["project"]
    seconds = project.get("history_retention_seconds")
    if seconds is None:
        return _result(name, FAIL, "Neon API returned no history_retention_seconds")
    days = round(int(seconds) / 86400, 2)
    extra = {
        "retention_seconds": int(seconds),
        "retention_days": days,
        "region": project.get("region_id"),
        "pg_version": project.get("pg_version"),
    }
    if days < min_days:
        return _result(name, FAIL, f"PITR window is {days} days, below the {min_days}-day floor", **extra)
    return _result(
        name,
        PASS,
        f"PITR window {days} days (floor {min_days}), region {project.get('region_id')}, "
        f"Postgres {project.get('pg_version')}",
        **extra,
    )


def check_neon_default_branch(api_key: str, project_id: str, http_get: HttpGet = neon_http_get) -> dict:
    name = "neon_default_branch"
    try:
        code, data = _neon(f"/projects/{project_id}/branches", api_key, http_get)
    except ConnectionError as exc:
        return _result(name, FAIL, str(exc))
    if code != 200 or not isinstance(data, dict):
        return _neon_error(name, code)
    default = [b for b in data.get("branches", []) if b.get("default")]
    if not default:
        return _result(name, FAIL, "no default branch on the Neon project")
    branch = default[0]
    state = branch.get("current_state")
    extra = {"branch": branch.get("name"), "branch_state": state}
    if state != "ready":
        return _result(name, FAIL, f"default branch '{branch.get('name')}' is '{state}', expected 'ready'", **extra)
    return _result(name, PASS, f"default branch '{branch.get('name')}' is ready", **extra)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_checks(
    env: Mapping[str, str],
    only: list[str] | None = None,
    r2_factory: Callable[[Mapping[str, str]], Any] = make_r2_client,
    http_get: HttpGet = neon_http_get,
    now: datetime | None = None,
) -> list[dict]:
    wanted = only or list(CHECK_NAMES)
    results: list[dict] = []
    max_age = float(env.get("BACKUP_MAX_AGE_HOURS") or DEFAULT_MAX_AGE_HOURS)
    min_days = float(env.get("PITR_MIN_DAYS") or DEFAULT_PITR_MIN_DAYS)

    if "r2_latest_backup" in wanted:
        missing = missing_env(R2_ENV, env)
        if missing:
            results.append(_unverified("r2_latest_backup", missing))
        else:
            try:
                client = r2_factory(env)
            except Exception as exc:  # noqa: BLE001
                results.append(_result("r2_latest_backup", FAIL, f"R2 client init failed: {type(exc).__name__}"))
            else:
                prefix = env.get("BACKUP_PREFIX") or DEFAULT_PREFIX
                results.append(check_r2_latest_backup(client, env["R2_BACKUPS_BUCKET"].strip(), prefix, max_age, now))

    neon_missing = missing_env(NEON_ENV, env)
    for name in ("neon_pitr_window", "neon_default_branch"):
        if name not in wanted:
            continue
        if neon_missing:
            results.append(_unverified(name, neon_missing))
            continue
        key, project = env["NEON_API_KEY"].strip(), env["NEON_PROJECT_ID"].strip()
        if name == "neon_pitr_window":
            results.append(check_neon_pitr(key, project, min_days, http_get))
        else:
            results.append(check_neon_default_branch(key, project, http_get))
    return results


def build_report(run_ts: datetime, checks: list[dict]) -> tuple[str, str]:
    verdict = overall_verdict(c["status"] for c in checks)
    icon = {PASS: "✅", FAIL: "❌", UNVERIFIED: "⚠️"}
    lines = [
        "# Backup Integrity Check (Neon + R2)",
        f"# Verdict:    {icon[verdict]} {verdict}",
        f"# Timestamp:  {run_ts.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "# Controls:   S1.5 / CC4.2",
        "",
        "## Check Results",
        "",
    ]
    for c in checks:
        lines.append(f"### {icon[c['status']]} {c['check']}")
        lines.append(f"  Status:  {c['status']}")
        lines.append(f"  Details: {c['details']}")
        lines.append("")
    missing = sorted({m for c in checks for m in c.get("missing", [])})
    if missing:
        lines += [
            f"## UNVERIFIED — missing secret {', '.join(missing)}",
            "  Add them under GitHub → Settings → Secrets and variables → Actions.",
            "  docs/runbooks/backup-restore.md §2 says where each value comes from.",
            "",
        ]
    digest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    lines += [
        "## Evidence Integrity",
        f"# SHA-256: {digest}",
        f"# Filing:  docs/08-internal/soc2-evidence/s1/backup-integrity-{run_ts.strftime('%Y%m')}.txt",
        "",
    ]
    return verdict, "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--save", action="store_true", help="write evidence to docs/08-internal/soc2-evidence/s1/")
    parser.add_argument("--only", action="append", choices=CHECK_NAMES, help="run only this check (repeatable)")
    parser.add_argument("--json", dest="json_path", help="write the results + verdict as JSON")
    parser.add_argument("--report", help="also write the text report to this path")
    args = parser.parse_args(argv)
    utf8_stdio()

    run_ts = datetime.now(timezone.utc)
    checks = run_checks(os.environ, args.only)
    verdict, report = build_report(run_ts, checks)
    print(report)

    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
    if args.json_path:
        Path(args.json_path).write_text(json.dumps({"verdict": verdict, "checks": checks}, indent=2), encoding="utf-8")
    if args.save:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        out = EVIDENCE_DIR / f"backup-integrity-{run_ts.strftime('%Y%m')}.txt"
        out.write_text(report, encoding="utf-8")
        print(f"\nEvidence saved: {out}", file=sys.stderr)
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        missing = sorted({m for c in checks for m in c.get("missing", [])})
        with open(gh_out, "a", encoding="utf-8") as fh:
            fh.write(f"verdict={verdict}\nmissing={','.join(missing)}\n")
    return EXIT_CODES[verdict]


if __name__ == "__main__":
    sys.exit(main())
