#!/usr/bin/env python3
"""
Off-provider Postgres backup + restore drill — Sprint 778b.

Production Postgres lives on **Neon**. Neon PITR is one recovery mechanism;
this script is the second: a daily ``pg_dump`` into the Cloudflare R2 bucket
``paciolus-backups``, plus a restore drill that proves the dump comes back.

Subcommands
-----------
``backup``
    Dump the database, upload ``<stem>.dump`` then ``<stem>.manifest.json``
    to R2, verify the upload, then apply retention. The manifest is written
    last, so a backup only *exists* once its manifest does.
``retention``
    Apply retention on its own (``--dry-run`` lists what would go).
``locate``
    Find the newest complete backup and report it for the drill workflow.
``drill``
    Download a backup, check its sha256, ``pg_restore`` it into an empty
    Postgres, and compare tables, row counts, schema fingerprint and alembic
    revision against the manifest.

Consistency: row counts and the schema fingerprint are taken inside the same
``REPEATABLE READ`` snapshot that ``pg_dump --snapshot`` dumps, so the
manifest describes exactly the bytes in the dump even while the app writes.
That needs a session that stays open, which is one reason the dump must use
Neon's **direct** host: the ``-pooler`` host is PgBouncer in transaction mode,
which cannot hold an exported snapshot across statements.

Verdicts and exit codes (shared with ``verify_backup_integrity.py``)
--------------------------------------------------------------------
    0  PASS        — the thing was checked and is good
    1  FAIL        — the thing was checked and is bad
    2  UNVERIFIED  — it could not be checked (a required secret is unset)

UNVERIFIED is deliberately non-zero: an unverified backup is not a passing
one, and a job that is green because it never ran is the false-green Sprint
778a removed. Missing secrets are named in the output.

Secrets (environment variables)
-------------------------------
    NEON_BACKUP_DATABASE_URL       backup only — Neon DIRECT (non-pooler) URL
    R2_BACKUPS_ENDPOINT            https://<account>.r2.cloudflarestorage.com
    R2_BACKUPS_BUCKET              paciolus-backups
    R2_BACKUPS_ACCESS_KEY_ID       R2 token scoped to paciolus-backups
    R2_BACKUPS_SECRET_ACCESS_KEY

No value from these is ever printed. Connection strings reach ``pg_dump``
through the environment, never argv.

Runbook: ``docs/runbooks/backup-restore.md``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PASS = "PASS"
FAIL = "FAIL"
UNVERIFIED = "UNVERIFIED"
EXIT_CODES = {PASS: 0, FAIL: 1, UNVERIFIED: 2}

R2_ENV = (
    "R2_BACKUPS_ENDPOINT",
    "R2_BACKUPS_BUCKET",
    "R2_BACKUPS_ACCESS_KEY_ID",
    "R2_BACKUPS_SECRET_ACCESS_KEY",
)
DB_ENV = "NEON_BACKUP_DATABASE_URL"

DEFAULT_PREFIX = "pg_dump/"
DEFAULT_KEEP_DAILY = 30
DEFAULT_KEEP_MONTHLY = 12
ORPHAN_GRACE_HOURS = 24
MANIFEST_FORMAT_VERSION = 1

_STAMP_FMT = "%Y%m%dT%H%M%SZ"
_KEY_RE = re.compile(r"paciolus-(\d{8}T\d{6}Z)\.(dump|manifest\.json)$")


# ---------------------------------------------------------------------------
# Verdicts + environment
# ---------------------------------------------------------------------------


def overall_verdict(statuses: Iterable[str]) -> str:
    """FAIL dominates, then UNVERIFIED; PASS only if every check passed.

    An empty set of checks is UNVERIFIED — nothing was verified.
    """
    statuses = list(statuses)
    if not statuses:
        return UNVERIFIED
    if FAIL in statuses:
        return FAIL
    if any(s != PASS for s in statuses):
        return UNVERIFIED
    return PASS


def missing_env(names: Iterable[str], env: Mapping[str, str] | None = None) -> list[str]:
    env = os.environ if env is None else env
    return [n for n in names if not (env.get(n) or "").strip()]


def unverified_message(missing: list[str]) -> str:
    return "UNVERIFIED — missing secret " + ", ".join(missing)


def write_github_output(values: Mapping[str, object], path: str | None = None) -> None:
    """Append ``key=value`` lines to ``$GITHUB_OUTPUT`` when running in Actions."""
    path = path or os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        for k, v in values.items():
            fh.write(f"{k}={str(v).replace(chr(10), ' ')}\n")


def redact_url(url: str) -> str:
    """Host/db only — never user or password."""
    try:
        p = urlparse(url)
        return f"{p.hostname or '?'}{p.path or ''}"
    except ValueError:
        return "<unparseable url>"


def is_pooled_neon_host(url: str) -> bool:
    """Neon's PgBouncer endpoints carry ``-pooler`` in the first host label."""
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    return "-pooler" in host.split(".", 1)[0]


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------


def backup_stem(ts: datetime, prefix: str = DEFAULT_PREFIX) -> str:
    ts = ts.astimezone(timezone.utc)
    return f"{prefix}{ts:%Y/%m}/paciolus-{ts.strftime(_STAMP_FMT)}"


def parse_key(key: str) -> tuple[str, datetime, str] | None:
    """Return ``(stem, timestamp, kind)`` for a backup object key, else None.

    ``kind`` is ``"dump"`` or ``"manifest"``. Keys that do not match are
    never touched by retention.
    """
    m = _KEY_RE.search(key)
    if not m:
        return None
    ts = datetime.strptime(m.group(1), _STAMP_FMT).replace(tzinfo=timezone.utc)
    kind = "dump" if m.group(2) == "dump" else "manifest"
    stem = key[: m.start()] + f"paciolus-{m.group(1)}"
    return stem, ts, kind


@dataclass
class BackupSet:
    stem: str
    ts: datetime
    dump: dict | None = None  # list_objects entry
    manifest: dict | None = None

    @property
    def complete(self) -> bool:
        return self.dump is not None and self.manifest is not None


def group_backups(objects: Iterable[Mapping[str, Any]]) -> list[BackupSet]:
    """Group listed objects by stem, newest first."""
    sets: dict[str, BackupSet] = {}
    for obj in objects:
        parsed = parse_key(obj["Key"])
        if parsed is None:
            continue
        stem, ts, kind = parsed
        bs = sets.setdefault(stem, BackupSet(stem=stem, ts=ts))
        setattr(bs, kind, dict(obj))
    return sorted(sets.values(), key=lambda b: b.ts, reverse=True)


# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------


@dataclass
class RetentionPlan:
    keep: list[str] = field(default_factory=list)  # stems
    delete: list[str] = field(default_factory=list)  # object keys

    def summary(self) -> str:
        return f"keep {len(self.keep)} backups, delete {len(self.delete)} objects"


def select_retention(
    backups: list[BackupSet],
    keep_daily: int = DEFAULT_KEEP_DAILY,
    keep_monthly: int = DEFAULT_KEEP_MONTHLY,
    now: datetime | None = None,
    orphan_grace_hours: int = ORPHAN_GRACE_HOURS,
) -> RetentionPlan:
    """Decide which backups survive.

    - Daily tier: the newest backup of each of the ``keep_daily`` most recent
      days *that have a backup*. Counting backup-days rather than calendar
      days means a cron that stops for six weeks does not age out every copy.
    - Monthly tier: the newest backup of each of the ``keep_monthly`` most
      recent months that have one.
    - The newest complete backup is always kept.
    - A dump without a manifest is an interrupted upload: deleted once it is
      older than ``orphan_grace_hours`` (it may be a run still in flight).
    - A manifest without a dump is kept and left for the integrity check to
      flag — deleting evidence of a broken backup would hide it.
    """
    if keep_daily < 1 or keep_monthly < 0:
        raise ValueError("keep_daily must be >= 1 and keep_monthly >= 0")
    now = now or datetime.now(timezone.utc)
    complete = [b for b in backups if b.complete]  # newest first
    keep: set[str] = set()
    if complete:
        keep.add(complete[0].stem)

    days: list[str] = []
    seen_days: set = set()
    for b in complete:
        day = b.ts.date()
        if day in seen_days:
            continue
        seen_days.add(day)
        if len(days) < keep_daily:
            days.append(b.stem)
    keep.update(days)

    months: list[str] = []
    seen_months: set = set()
    for b in complete:
        month = (b.ts.year, b.ts.month)
        if month in seen_months:
            continue
        seen_months.add(month)
        if len(months) < keep_monthly:
            months.append(b.stem)
    keep.update(months)

    plan = RetentionPlan(keep=sorted(keep, reverse=True))
    grace = timedelta(hours=orphan_grace_hours)
    for b in backups:
        if b.complete:
            if b.stem not in keep:
                plan.delete.extend([b.dump["Key"], b.manifest["Key"]])  # type: ignore[index]
        elif b.dump is not None and now - b.ts > grace:
            plan.delete.append(b.dump["Key"])
    return plan


# ---------------------------------------------------------------------------
# R2 (S3-compatible) — same client shape as backend/shared/export_share_storage.py
# ---------------------------------------------------------------------------


def make_r2_client(env: Mapping[str, str] | None = None) -> Any:
    env = os.environ if env is None else env
    import boto3  # imported lazily so tests and --help never need it
    from botocore.config import Config as BotoConfig

    return boto3.client(
        "s3",
        endpoint_url=env["R2_BACKUPS_ENDPOINT"],
        aws_access_key_id=env["R2_BACKUPS_ACCESS_KEY_ID"],
        aws_secret_access_key=env["R2_BACKUPS_SECRET_ACCESS_KEY"],
        region_name="auto",  # R2-canonical
        config=BotoConfig(signature_version="s3v4", retries={"max_attempts": 3, "mode": "standard"}),
    )


def list_objects(client: Any, bucket: str, prefix: str) -> list[dict]:
    objects: list[dict] = []
    token: str | None = None
    while True:
        kwargs: dict[str, Any] = {"Bucket": bucket, "Prefix": prefix}
        if token:
            kwargs["ContinuationToken"] = token
        resp = client.list_objects_v2(**kwargs)
        objects.extend(resp.get("Contents", []))
        if not resp.get("IsTruncated"):
            return objects
        token = resp.get("NextContinuationToken")


def delete_keys(client: Any, bucket: str, keys: list[str]) -> None:
    for i in range(0, len(keys), 1000):
        chunk = keys[i : i + 1000]
        resp = client.delete_objects(Bucket=bucket, Delete={"Objects": [{"Key": k} for k in chunk], "Quiet": True})
        errors = resp.get("Errors") or []
        if errors:
            raise RuntimeError(f"R2 delete failed for {len(errors)} object(s), first: {errors[0].get('Key')}")


def read_manifest(client: Any, bucket: str, stem: str) -> dict:
    body = client.get_object(Bucket=bucket, Key=f"{stem}.manifest.json")["Body"].read()
    return json.loads(body)


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha256_stream(body: Any, chunk: int = 1 << 20) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    for block in iter(lambda: body.read(chunk), b""):
        h.update(block)
        n += len(block)
    return h.hexdigest(), n


# ---------------------------------------------------------------------------
# Catalog: tables, row counts, schema fingerprint, alembic revision
# ---------------------------------------------------------------------------

TABLES_SQL = "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
COLUMNS_SQL = (
    "SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns "
    "WHERE table_schema = 'public' ORDER BY table_name, column_name"
)
INDEXES_SQL = (
    "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname"
)


def schema_fingerprint(columns: Iterable[Iterable[Any]], indexes: Iterable[Iterable[Any]]) -> str:
    """Order-independent sha256 over public-schema columns and index definitions."""
    payload = {
        "columns": sorted([list(map(str, r)) for r in columns]),
        "indexes": sorted([list(map(str, r)) for r in indexes]),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def collect_catalog(cur: Any) -> dict:
    """Run the catalog queries on a DB-API cursor. Exact ``count(*)`` per table."""
    cur.execute(TABLES_SQL)
    tables = [r[0] for r in cur.fetchall()]
    counts: dict[str, int] = {}
    for t in tables:
        cur.execute(f"SELECT count(*) FROM public.{_quote_ident(t)}")
        counts[t] = int(cur.fetchone()[0])
    cur.execute(COLUMNS_SQL)
    columns = cur.fetchall()
    cur.execute(INDEXES_SQL)
    indexes = cur.fetchall()
    alembic = None
    if "alembic_version" in counts:
        cur.execute("SELECT version_num FROM public.alembic_version ORDER BY version_num")
        alembic = ",".join(r[0] for r in cur.fetchall()) or None
    return {
        "tables": counts,
        "schema_sha256": schema_fingerprint(columns, indexes),
        "alembic_version": alembic,
    }


def server_version(cur: Any) -> tuple[str, int]:
    cur.execute("SHOW server_version")
    text = str(cur.fetchone()[0]).split()[0]
    cur.execute("SHOW server_version_num")
    num = int(cur.fetchone()[0])
    return text, num


def build_manifest(
    *,
    created_at: datetime,
    stem: str,
    dump_bytes: int,
    dump_sha256: str,
    version_text: str,
    version_num: int,
    catalog: Mapping[str, Any],
    source_host: str,
    snapshot_id: str | None,
    run_url: str | None = None,
) -> dict:
    tables = dict(sorted(catalog["tables"].items()))
    return {
        "format_version": MANIFEST_FORMAT_VERSION,
        "created_at": created_at.astimezone(timezone.utc).isoformat(),
        "stem": stem,
        "dump_key": f"{stem}.dump",
        "dump_bytes": dump_bytes,
        "dump_sha256": dump_sha256,
        "pg_dump_format": "custom",
        "server_version": version_text,
        "server_version_num": version_num,
        "server_major": version_num // 10000,
        "alembic_version": catalog.get("alembic_version"),
        "schema_sha256": catalog["schema_sha256"],
        "table_count": len(tables),
        "total_rows": sum(tables.values()),
        "tables": tables,
        "snapshot_consistent": snapshot_id is not None,
        "source_host": source_host,
        "workflow_run": run_url,
    }


# ---------------------------------------------------------------------------
# Restore comparison
# ---------------------------------------------------------------------------


@dataclass
class Check:
    name: str
    status: str
    detail: str


def compare_restore(
    manifest: Mapping[str, Any],
    observed: Mapping[str, Any],
    revision_known: Callable[[str], bool] | None = None,
) -> list[Check]:
    checks: list[Check] = []
    want = dict(manifest.get("tables") or {})
    got = dict(observed.get("tables") or {})

    missing = sorted(set(want) - set(got))
    extra = sorted(set(got) - set(want))
    if missing or extra:
        checks.append(Check("table_list", FAIL, f"missing={missing or '[]'} extra={extra or '[]'}"))
    else:
        checks.append(Check("table_list", PASS, f"{len(want)} tables match"))

    diffs = [f"{t}: manifest={want[t]} restored={got[t]}" for t in sorted(set(want) & set(got)) if want[t] != got[t]]
    if diffs:
        checks.append(Check("row_counts", FAIL, "; ".join(diffs[:20])))
    elif not want:
        checks.append(Check("row_counts", FAIL, "manifest lists no tables"))
    else:
        checks.append(Check("row_counts", PASS, f"{sum(want.values())} rows across {len(want)} tables match"))

    if manifest.get("schema_sha256") == observed.get("schema_sha256"):
        checks.append(Check("schema_fingerprint", PASS, str(manifest.get("schema_sha256"))[:16]))
    else:
        checks.append(
            Check(
                "schema_fingerprint",
                FAIL,
                f"manifest={str(manifest.get('schema_sha256'))[:16]} restored={str(observed.get('schema_sha256'))[:16]}",
            )
        )

    m_rev, o_rev = manifest.get("alembic_version"), observed.get("alembic_version")
    if not m_rev:
        checks.append(Check("alembic_revision", FAIL, "manifest has no alembic_version"))
    elif m_rev != o_rev:
        checks.append(Check("alembic_revision", FAIL, f"manifest={m_rev} restored={o_rev}"))
    elif revision_known is not None and not all(revision_known(r) for r in m_rev.split(",")):
        checks.append(Check("alembic_revision", FAIL, f"{m_rev} is not a revision in this repo's migration history"))
    else:
        checks.append(Check("alembic_revision", PASS, m_rev))
    return checks


def render_report(title: str, checks: list[Check], context: Mapping[str, Any] | None = None) -> str:
    verdict = overall_verdict(c.status for c in checks)
    lines = [f"## {title}", "", f"**Verdict: {verdict}**", ""]
    for k, v in (context or {}).items():
        lines.append(f"- **{k}:** {v}")
    if context:
        lines.append("")
    lines += ["| Check | Result | Detail |", "|---|---|---|"]
    for c in checks:
        lines.append(f"| {c.name} | {c.status} | {c.detail.replace('|', '/')} |")
    lines.append("")
    if verdict == UNVERIFIED:
        lines.append("Nothing is known to be broken, and nothing was verified either. An unverified")
        lines.append("backup is not a passing one, so this run exits non-zero.")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Subcommand: backup
# ---------------------------------------------------------------------------

PG_DUMP_SCRIPT = (
    'exec "${PG_DUMP_BIN:-pg_dump}" --dbname="$PGDUMP_URL" --format=custom --compress=6 '
    '--snapshot="$PGDUMP_SNAPSHOT" --file="$PGDUMP_FILE"'
)


def pg_dump_command(mode: str, major: int, outdir: Path, filename: str) -> tuple[list[str], str]:
    """Return ``(argv, in-container output path)``. The URL travels in env, not argv.

    ``docker`` mode runs the official ``postgres:<major>`` image so the client
    major always equals the server's — a pg_dump older than the server
    refuses to run, and the runner's preinstalled client is not guaranteed.
    """
    if mode == "docker":
        return (
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "host",
                "-e",
                "PGDUMP_URL",
                "-e",
                "PGDUMP_SNAPSHOT",
                "-e",
                "PGDUMP_FILE",
                "-v",
                f"{outdir.resolve()}:/out",
                f"postgres:{major}",
                "sh",
                "-c",
                PG_DUMP_SCRIPT,
            ],
            f"/out/{filename}",
        )
    if mode == "local":
        return (["sh", "-c", PG_DUMP_SCRIPT], str((outdir / filename).resolve()))
    raise ValueError(f"unknown pg_dump mode {mode!r}")


def cmd_backup(args: argparse.Namespace) -> int:
    missing = missing_env((DB_ENV, *R2_ENV))
    if missing:
        msg = unverified_message(missing)
        print(f"::error::{msg} — no backup was taken.")
        _summary(f"## pg_dump → R2 backup\n\n**{msg}** — no backup was taken. See docs/runbooks/backup-restore.md.\n")
        write_github_output({"verdict": UNVERIFIED, "missing": ",".join(missing)})
        return EXIT_CODES[UNVERIFIED]

    db_url = os.environ[DB_ENV].strip()
    if is_pooled_neon_host(db_url):
        print(f"::error::{DB_ENV} points at a Neon -pooler host ({redact_url(db_url)}). Use the direct host.")
        write_github_output({"verdict": FAIL})
        return EXIT_CODES[FAIL]

    import psycopg2  # type: ignore[import-untyped]

    bucket = os.environ["R2_BACKUPS_BUCKET"].strip()
    client = make_r2_client()
    now = datetime.now(timezone.utc)
    stem = backup_stem(now, args.prefix)
    workdir = Path(args.workdir or tempfile.mkdtemp(prefix="pgdump-"))
    workdir.mkdir(parents=True, exist_ok=True)
    filename = Path(stem).name + ".dump"
    local_dump = workdir / filename

    conn = psycopg2.connect(db_url, connect_timeout=20, application_name="paciolus-backup")
    try:
        conn.set_session(isolation_level="REPEATABLE READ", readonly=True)
        cur = conn.cursor()
        version_text, version_num = server_version(cur)
        cur.execute("SELECT pg_export_snapshot()")
        snapshot_id = cur.fetchone()[0]
        catalog = collect_catalog(cur)
        major = version_num // 10000
        argv, target = pg_dump_command(args.pg_dump_mode, major, workdir, filename)
        env = dict(os.environ, PGDUMP_URL=db_url, PGDUMP_SNAPSHOT=snapshot_id, PGDUMP_FILE=target)
        print(
            f"pg_dump: server {version_text}, client postgres:{major} ({args.pg_dump_mode}), {len(catalog['tables'])} tables"
        )
        proc = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=args.timeout)
        if proc.returncode != 0:
            # stderr from pg_dump never contains the password; it can contain the host.
            print(f"::error::pg_dump exited {proc.returncode}: {proc.stderr.strip()[-2000:]}")
            write_github_output({"verdict": FAIL})
            return EXIT_CODES[FAIL]
    finally:
        conn.rollback()
        conn.close()

    size = local_dump.stat().st_size
    digest = sha256_file(local_dump)
    manifest = build_manifest(
        created_at=now,
        stem=stem,
        dump_bytes=size,
        dump_sha256=digest,
        version_text=version_text,
        version_num=version_num,
        catalog=catalog,
        source_host=redact_url(db_url),
        snapshot_id=snapshot_id,
        run_url=_run_url(),
    )

    client.upload_file(str(local_dump), bucket, f"{stem}.dump", ExtraArgs={"Metadata": {"sha256": digest}})
    head = client.head_object(Bucket=bucket, Key=f"{stem}.dump")
    if int(head["ContentLength"]) != size:
        print(f"::error::uploaded size {head['ContentLength']} != local size {size}")
        write_github_output({"verdict": FAIL})
        return EXIT_CODES[FAIL]
    client.put_object(
        Bucket=bucket,
        Key=f"{stem}.manifest.json",
        Body=json.dumps(manifest, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    local_dump.unlink(missing_ok=True)

    plan = select_retention(
        group_backups(list_objects(client, bucket, args.prefix)), args.keep_daily, args.keep_monthly
    )
    if stem not in plan.keep:  # defensive: the run that just succeeded is never deleted
        raise RuntimeError("retention selected the new backup for deletion")
    if plan.delete and not args.dry_run_retention:
        delete_keys(client, bucket, plan.delete)

    report = render_report(
        "pg_dump → R2 backup",
        [Check("backup", PASS, f"{stem}.dump")],
        {
            "Server": version_text,
            "Size": f"{size:,} bytes",
            "sha256": digest,
            "Tables / rows": f"{manifest['table_count']} / {manifest['total_rows']:,}",
            "Alembic": manifest["alembic_version"],
            "Retention": f"{plan.summary()} (daily={args.keep_daily}, monthly={args.keep_monthly}"
            + (", DRY RUN)" if args.dry_run_retention else ")"),
        },
    )
    print(report)
    _summary(report)
    write_github_output({"verdict": PASS, "stem": stem})
    return EXIT_CODES[PASS]


def cmd_retention(args: argparse.Namespace) -> int:
    missing = missing_env(R2_ENV)
    if missing:
        print(unverified_message(missing))
        return EXIT_CODES[UNVERIFIED]
    bucket = os.environ["R2_BACKUPS_BUCKET"].strip()
    client = make_r2_client()
    plan = select_retention(
        group_backups(list_objects(client, bucket, args.prefix)), args.keep_daily, args.keep_monthly
    )
    print(plan.summary())
    for k in plan.delete:
        print(f"  {'would delete' if args.dry_run else 'delete'} {k}")
    if plan.delete and not args.dry_run:
        delete_keys(client, bucket, plan.delete)
    return 0


# ---------------------------------------------------------------------------
# Subcommand: locate (drill job 1)
# ---------------------------------------------------------------------------


def locate_latest(client: Any, bucket: str, prefix: str, stem: str | None = None) -> tuple[str, dict | str]:
    """Return ``(PASS, manifest)`` or ``(FAIL, reason)``."""
    if stem:
        try:
            return PASS, read_manifest(client, bucket, stem)
        except Exception as exc:  # noqa: BLE001 — botocore raises many subclasses
            return FAIL, f"manifest for {stem} unreadable: {type(exc).__name__}"
    backups = [b for b in group_backups(list_objects(client, bucket, prefix)) if b.complete]
    if not backups:
        return FAIL, f"no complete backup under s3://{bucket}/{prefix}"
    return PASS, read_manifest(client, bucket, backups[0].stem)


def cmd_locate(args: argparse.Namespace) -> int:
    missing = missing_env(R2_ENV)
    if missing:
        msg = unverified_message(missing)
        print(msg)
        write_github_output({"status": UNVERIFIED, "detail": msg})
        return 0  # the drill's verdict job turns this into a red, named UNVERIFIED
    bucket = os.environ["R2_BACKUPS_BUCKET"].strip()
    try:
        status, result = locate_latest(make_r2_client(), bucket, args.prefix, args.stem or None)
    except Exception as exc:  # noqa: BLE001
        status, result = FAIL, f"R2 listing failed: {type(exc).__name__}: {exc}"
    if status != PASS:
        print(f"FAIL: {result}")
        write_github_output({"status": FAIL, "detail": result})
        return 0
    manifest = result
    assert isinstance(manifest, dict)
    major = int(manifest["server_major"])
    print(f"latest backup: {manifest['stem']} ({manifest['created_at']}, postgres {major})")
    write_github_output(
        {"status": "ok", "stem": manifest["stem"], "pg_major": major, "created_at": manifest["created_at"]}
    )
    return 0


# ---------------------------------------------------------------------------
# Subcommand: drill (drill job 2)
# ---------------------------------------------------------------------------


def alembic_revision_checker(ini_path: Path) -> Callable[[str], bool]:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config(str(ini_path))
    loc = Path(cfg.get_main_option("script_location") or "")
    if not loc.is_absolute():
        cfg.set_main_option("script_location", str((ini_path.parent / loc).resolve()))
    script = ScriptDirectory.from_config(cfg)

    def known(rev: str) -> bool:
        try:
            return script.get_revision(rev) is not None
        except Exception:  # noqa: BLE001 — alembic raises CommandError / ResolutionError
            return False

    return known


def run_drill(
    *,
    client: Any,
    bucket: str,
    stem: str,
    workdir: Path,
    restore: Callable[[Path], subprocess.CompletedProcess],
    observe: Callable[[], dict],
    revision_known: Callable[[str], bool] | None,
) -> tuple[list[Check], dict]:
    checks: list[Check] = []
    manifest = read_manifest(client, bucket, stem)
    local = workdir / (Path(stem).name + ".dump")
    client.download_file(bucket, f"{stem}.dump", str(local))
    digest = sha256_file(local)
    if digest != manifest.get("dump_sha256"):
        checks.append(
            Check("dump_sha256", FAIL, f"downloaded {digest[:16]} != manifest {str(manifest.get('dump_sha256'))[:16]}")
        )
        return checks, manifest
    checks.append(Check("dump_sha256", PASS, digest[:16]))

    proc = restore(local)
    if proc.returncode != 0:
        checks.append(Check("pg_restore", FAIL, f"exit {proc.returncode}: {(proc.stderr or '').strip()[-500:]}"))
        return checks, manifest
    checks.append(Check("pg_restore", PASS, "restored with --exit-on-error"))

    checks.extend(compare_restore(manifest, observe(), revision_known))
    return checks, manifest


def cmd_drill(args: argparse.Namespace) -> int:
    missing = missing_env(R2_ENV)
    if missing:
        msg = unverified_message(missing)
        print(msg)
        write_github_output({"verdict": UNVERIFIED, "detail": msg})
        return EXIT_CODES[UNVERIFIED]
    import psycopg2  # type: ignore[import-untyped]

    bucket = os.environ["R2_BACKUPS_BUCKET"].strip()
    workdir = Path(args.workdir or tempfile.mkdtemp(prefix="drill-"))
    workdir.mkdir(parents=True, exist_ok=True)

    def restore(dump: Path) -> subprocess.CompletedProcess:
        inside = "/tmp/drill.dump"
        cp = subprocess.run(["docker", "cp", str(dump), f"{args.container}:{inside}"], capture_output=True, text=True)
        if cp.returncode != 0:
            return cp
        return subprocess.run(
            [
                "docker",
                "exec",
                args.container,
                "pg_restore",
                "--username",
                "postgres",
                "--dbname",
                args.target_db,
                "--no-owner",
                "--no-privileges",
                "--exit-on-error",
                inside,
            ],
            capture_output=True,
            text=True,
            timeout=args.timeout,
        )

    def observe() -> dict:
        conn = psycopg2.connect(args.target_url)
        try:
            cur = conn.cursor()
            cat = collect_catalog(cur)
            cat["server_version"] = server_version(cur)[0]
            return cat
        finally:
            conn.close()

    revision_known = alembic_revision_checker(Path(args.alembic_ini)) if args.alembic_ini else None
    try:
        checks, manifest = run_drill(
            client=make_r2_client(),
            bucket=bucket,
            stem=args.stem,
            workdir=workdir,
            restore=restore,
            observe=observe,
            revision_known=revision_known,
        )
    except Exception as exc:  # noqa: BLE001 — any crash is a failed drill, reported as one
        checks, manifest = [Check("drill", FAIL, f"{type(exc).__name__}: {exc}")], {}

    verdict = overall_verdict(c.status for c in checks)
    report = render_report(
        "Restore drill (R2 pg_dump)",
        checks,
        {
            "Backup": args.stem,
            "Taken at": manifest.get("created_at", "?"),
            "Source server": manifest.get("server_version", "?"),
            "Tables / rows": f"{manifest.get('table_count', '?')} / {manifest.get('total_rows', '?')}",
        },
    )
    print(report)
    Path(args.report).write_text(report, encoding="utf-8")
    _summary(report)
    write_github_output({"verdict": verdict})
    return EXIT_CODES[verdict]


# ---------------------------------------------------------------------------
# Plumbing
# ---------------------------------------------------------------------------


def _summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


def _run_url() -> str | None:
    server, repo, run = (os.environ.get(k) for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID"))
    return f"{server}/{repo}/actions/runs/{run}" if server and repo and run else None


def _env_int(name: str, default: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    return int(raw) if raw else default


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prefix", default=os.environ.get("BACKUP_PREFIX", DEFAULT_PREFIX))
    sub = p.add_subparsers(dest="command", required=True)

    def retention_args(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--keep-daily", type=int, default=_env_int("BACKUP_KEEP_DAILY", DEFAULT_KEEP_DAILY))
        sp.add_argument("--keep-monthly", type=int, default=_env_int("BACKUP_KEEP_MONTHLY", DEFAULT_KEEP_MONTHLY))

    b = sub.add_parser("backup", help="pg_dump -> R2, manifest, retention")
    retention_args(b)
    b.add_argument("--pg-dump-mode", choices=("docker", "local"), default="docker")
    b.add_argument("--workdir")
    b.add_argument("--timeout", type=int, default=1800)
    b.add_argument("--dry-run-retention", action="store_true")
    b.set_defaults(func=cmd_backup)

    r = sub.add_parser("retention", help="apply retention only")
    retention_args(r)
    r.add_argument("--dry-run", action="store_true")
    r.set_defaults(func=cmd_retention)

    loc = sub.add_parser("locate", help="find the newest complete backup")
    loc.add_argument("--stem", default="")
    loc.set_defaults(func=cmd_locate)

    d = sub.add_parser("drill", help="restore a backup into a scratch Postgres and compare")
    d.add_argument("--stem", required=True)
    d.add_argument("--container", required=True, help="docker id of the scratch Postgres")
    d.add_argument("--target-db", default="drill")
    d.add_argument("--target-url", required=True)
    d.add_argument("--alembic-ini", default="")
    d.add_argument("--workdir")
    d.add_argument("--report", default="drill-report.md")
    d.add_argument("--timeout", type=int, default=1800)
    d.set_defaults(func=cmd_drill)
    return p


def utf8_stdio() -> None:
    """Reports contain em dashes and ticks; a cp1252 console must not turn UNVERIFIED into a crash."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except Exception:  # noqa: BLE001, S110 — best effort; captured/redirected streams may refuse
            pass


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
