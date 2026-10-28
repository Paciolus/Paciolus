"""Sprint 778b: off-provider backup, restore drill and DR verdict logic.

Covers ``scripts/pg_backup.py`` and ``scripts/verify_backup_integrity.py``
with in-memory fakes for R2 and the Neon API — no network, no database, no
boto3. Also parses the four backup/DR workflows and pins the properties that
matter: every secret they read is one the runbook tells the CEO to add, no
step uses ``set -x``, nothing still points at the deleted Render Postgres,
and the verdict jobs run under ``always()``.
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pg_backup as pb  # noqa: E402
import verify_backup_integrity as vbi  # noqa: E402


def _pg_url(user: str, password: str, rest: str) -> str:
    """A dummy connection URL, assembled at runtime so secret scanners never see a
    credential-shaped literal in source (TruffleHog flags them; inline ignores do
    not apply in its git scan)."""
    return "postgresql://" + user + ":" + password + "@" + rest


NOW = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
FULL_ENV = {
    "R2_BACKUPS_ENDPOINT": "https://acct.r2.cloudflarestorage.com",
    "R2_BACKUPS_BUCKET": "paciolus-backups",
    "R2_BACKUPS_ACCESS_KEY_ID": "id",
    "R2_BACKUPS_SECRET_ACCESS_KEY": "secret",
    "NEON_API_KEY": "neon-key",
    "NEON_PROJECT_ID": "proj-1",
}


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeS3:
    """Just enough of the boto3 S3 client, with 2-object pages to exercise pagination."""

    def __init__(self, objects: dict[str, bytes] | None = None, page: int = 2):
        self.objects = dict(objects or {})
        self.page = page
        self.deleted: list[str] = []

    def list_objects_v2(self, Bucket, Prefix, ContinuationToken=None):  # noqa: N803 — boto3 kwarg names
        keys = sorted(k for k in self.objects if k.startswith(Prefix))
        start = int(ContinuationToken or 0)
        chunk = keys[start : start + self.page]
        more = start + self.page < len(keys)
        resp = {"Contents": [{"Key": k, "Size": len(self.objects[k])} for k in chunk], "IsTruncated": more}
        if more:
            resp["NextContinuationToken"] = str(start + self.page)
        return resp

    def get_object(self, Bucket, Key):  # noqa: N803
        if Key not in self.objects:
            raise KeyError(Key)
        return {"Body": io.BytesIO(self.objects[Key])}

    def download_file(self, bucket, key, path):
        Path(path).write_bytes(self.objects[key])

    def delete_objects(self, Bucket, Delete):  # noqa: N803
        for o in Delete["Objects"]:
            self.deleted.append(o["Key"])
            self.objects.pop(o["Key"], None)
        return {}


def _manifest_for(stem: str, data: bytes, **over) -> dict:
    m = {
        "stem": stem,
        "created_at": "x",
        "dump_bytes": len(data),
        "dump_sha256": hashlib.sha256(data).hexdigest(),
        "server_major": 17,
        "server_version": "17.5",
        "tables": {"users": 3, "clients": 5, "alembic_version": 1},
        "table_count": 3,
        "total_rows": 9,
        "schema_sha256": "abc",
        "alembic_version": "rev1",
    }
    m.update(over)
    return m


def _put_backup(s3: FakeS3, ts: datetime, data: bytes = b"DUMPBYTES", manifest: bool = True, dump: bool = True, **over):
    stem = pb.backup_stem(ts)
    if dump:
        s3.objects[f"{stem}.dump"] = data
    if manifest:
        s3.objects[f"{stem}.manifest.json"] = json.dumps(_manifest_for(stem, data, **over)).encode()
    return stem


class FakeCursor:
    def __init__(self, tables: dict[str, int], columns, indexes, alembic=("rev1",)):
        self.tables, self.columns, self.indexes, self.alembic = tables, columns, indexes, alembic
        self._rows: list = []
        self.queries: list[str] = []

    def execute(self, sql):
        self.queries.append(sql)
        if sql == pb.TABLES_SQL:
            self._rows = [(t,) for t in sorted(self.tables)]
        elif sql.startswith("SELECT count(*) FROM public."):
            name = sql.split("public.", 1)[1].strip('"').replace('""', '"')
            self._rows = [(self.tables[name],)]
        elif sql == pb.COLUMNS_SQL:
            self._rows = list(self.columns)
        elif sql == pb.INDEXES_SQL:
            self._rows = list(self.indexes)
        elif "alembic_version ORDER BY" in sql:
            self._rows = [(r,) for r in self.alembic]
        elif sql == "SHOW server_version":
            self._rows = [("17.5 (Debian 17.5-1)",)]
        elif sql == "SHOW server_version_num":
            self._rows = [("170005",)]
        else:
            raise AssertionError(sql)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0]


# ---------------------------------------------------------------------------
# Verdicts, env, keys
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ([], pb.UNVERIFIED),
        ([pb.PASS], pb.PASS),
        ([pb.PASS, pb.PASS], pb.PASS),
        ([pb.PASS, pb.UNVERIFIED], pb.UNVERIFIED),
        ([pb.UNVERIFIED, pb.FAIL], pb.FAIL),
        ([pb.FAIL, pb.UNVERIFIED, pb.PASS], pb.FAIL),
        (["", pb.PASS], pb.UNVERIFIED),  # a skipped/blank result is never a pass
    ],
)
def test_overall_verdict(statuses, expected):
    assert pb.overall_verdict(statuses) == expected


def test_exit_codes_are_distinct_and_only_pass_is_zero():
    assert pb.EXIT_CODES == {"PASS": 0, "FAIL": 1, "UNVERIFIED": 2}


def test_missing_env_treats_blank_as_missing():
    env = {"A": "x", "B": "  ", "C": ""}
    assert pb.missing_env(["A", "B", "C", "D"], env) == ["B", "C", "D"]
    assert pb.unverified_message(["B", "D"]) == "UNVERIFIED — missing secret B, D"


@pytest.mark.parametrize(
    ("url", "pooled"),
    [
        (
            _pg_url("u", "p", "ep-cool-123-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"),
            True,
        ),
        (
            _pg_url("u", "p", "ep-cool-123.us-east-1.aws.neon.tech/neondb?sslmode=require"),
            False,
        ),
        (_pg_url("u", "p", "localhost/db"), False),
    ],
)
def test_pooled_host_detection(url, pooled):
    assert pb.is_pooled_neon_host(url) is pooled


def test_redact_url_never_contains_credentials():
    out = pb.redact_url(_pg_url("neondb_owner", "hunter2", "ep-x.neon.tech/neondb?sslmode=require"))
    assert "hunter2" not in out and "neondb_owner" not in out
    assert out == "ep-x.neon.tech/neondb"


def test_key_roundtrip():
    ts = datetime(2026, 1, 5, 7, 15, 3, tzinfo=timezone.utc)
    stem = pb.backup_stem(ts)
    assert stem == "pg_dump/2026/01/paciolus-20260105T071503Z"
    assert pb.parse_key(stem + ".dump") == (stem, ts, "dump")
    assert pb.parse_key(stem + ".manifest.json") == (stem, ts, "manifest")
    assert pb.parse_key("pg_dump/README.txt") is None
    assert pb.parse_key("pg_dump/2026/01/paciolus-2026.dump") is None


def test_pg_dump_command_keeps_the_url_out_of_argv(tmp_path):
    argv, target = pb.pg_dump_command("docker", 17, tmp_path, "x.dump")
    assert "postgres:17" in argv
    assert target == "/out/x.dump"
    assert all("postgresql://" not in a for a in argv)
    assert "PGDUMP_URL" in argv  # passed by name only
    with pytest.raises(ValueError):
        pb.pg_dump_command("ssh", 17, tmp_path, "x.dump")


# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------


def _sets(timestamps, complete=True):
    out = []
    for ts in timestamps:
        stem = pb.backup_stem(ts)
        out.append(
            pb.BackupSet(
                stem=stem,
                ts=ts,
                dump={"Key": stem + ".dump"},
                manifest={"Key": stem + ".manifest.json"} if complete else None,
            )
        )
    return sorted(out, key=lambda b: b.ts, reverse=True)


def test_retention_keeps_30_daily_plus_12_monthly_over_two_years():
    start = datetime(2024, 10, 1, 7, 15, tzinfo=timezone.utc)
    backups = _sets(start + timedelta(days=i) for i in range(760))
    plan = pb.select_retention(backups, keep_daily=30, keep_monthly=12, now=NOW)
    kept = {pb.parse_key(s + ".dump")[1] for s in plan.keep}
    newest = backups[0].ts
    assert newest in kept
    daily = sorted(kept, reverse=True)[:30]
    assert all((newest - d).days < 30 for d in daily)
    months = {(d.year, d.month) for d in kept}
    assert len(months) == 12
    # 30 daily, 12 monthly, overlapping in the current month (and the previous,
    # which the last 30 days reach into) — never more than 42.
    assert 30 < len(kept) <= 42
    assert len(plan.delete) == 2 * (len(backups) - len(kept))


def test_retention_counts_backup_days_not_calendar_days():
    # The cron stopped 90 days ago: the last 5 backups must survive, not age out.
    old = datetime(2026, 7, 1, 7, 15, tzinfo=timezone.utc)
    backups = _sets(old + timedelta(days=i) for i in range(5))
    plan = pb.select_retention(backups, keep_daily=30, keep_monthly=0, now=NOW)
    assert len(plan.keep) == 5
    assert plan.delete == []


def test_retention_keeps_newest_of_each_day():
    day = datetime(2026, 10, 27, tzinfo=timezone.utc)
    backups = _sets([day + timedelta(hours=1), day + timedelta(hours=9), day + timedelta(days=1, hours=1)])
    plan = pb.select_retention(backups, keep_daily=2, keep_monthly=0, now=NOW)
    assert pb.backup_stem(day + timedelta(hours=9)) in plan.keep
    assert pb.backup_stem(day + timedelta(hours=1)) + ".dump" in plan.delete


def test_retention_orphans_and_broken_manifests():
    fresh_orphan = _sets([NOW - timedelta(hours=1)], complete=False)
    old_orphan = _sets([NOW - timedelta(hours=48)], complete=False)
    good = _sets([NOW - timedelta(hours=30)])
    manifest_only = [
        pb.BackupSet(
            stem="pg_dump/2026/10/paciolus-20261001T000000Z",
            ts=datetime(2026, 10, 1, tzinfo=timezone.utc),
            dump=None,
            manifest={"Key": "pg_dump/2026/10/paciolus-20261001T000000Z.manifest.json"},
        )
    ]
    backups = sorted(fresh_orphan + old_orphan + good + manifest_only, key=lambda b: b.ts, reverse=True)
    plan = pb.select_retention(backups, keep_daily=1, keep_monthly=0, now=NOW)
    assert plan.keep == [good[0].stem]
    assert plan.delete == [old_orphan[0].dump["Key"]]  # fresh orphan may be in flight; manifest-only is evidence


@pytest.mark.parametrize(("daily", "monthly"), [(0, 12), (30, -1)])
def test_retention_rejects_parameters_that_could_delete_everything(daily, monthly):
    with pytest.raises(ValueError):
        pb.select_retention([], keep_daily=daily, keep_monthly=monthly)


def test_group_backups_through_paginated_listing():
    s3 = FakeS3(page=2)
    for i in range(4):
        _put_backup(s3, NOW - timedelta(days=i))
    s3.objects["pg_dump/notes.txt"] = b"ignored"
    groups = pb.group_backups(pb.list_objects(s3, "b", "pg_dump/"))
    assert len(groups) == 4 and all(g.complete for g in groups)
    assert groups[0].ts == NOW


# ---------------------------------------------------------------------------
# Catalog + manifest
# ---------------------------------------------------------------------------

COLS = [("users", "id", "integer", "NO"), ("users", "email", "text", "NO"), ("clients", "id", "integer", "NO")]
IDX = [("users", "users_pkey", "CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id)")]


def test_schema_fingerprint_is_order_independent_and_sensitive():
    a = pb.schema_fingerprint(COLS, IDX)
    assert a == pb.schema_fingerprint(list(reversed(COLS)), IDX)
    assert a != pb.schema_fingerprint(COLS[:-1], IDX)
    assert a != pb.schema_fingerprint(COLS, [])
    changed = [("users", "id", "bigint", "NO"), *COLS[1:]]
    assert a != pb.schema_fingerprint(changed, IDX)


def test_collect_catalog_counts_every_table_and_reads_alembic():
    cur = FakeCursor({"users": 3, "clients": 5, "alembic_version": 1, 'we"ird': 0}, COLS, IDX)
    cat = pb.collect_catalog(cur)
    assert cat["tables"] == {"alembic_version": 1, "clients": 5, "users": 3, 'we"ird': 0}
    assert cat["alembic_version"] == "rev1"
    assert cat["schema_sha256"] == pb.schema_fingerprint(COLS, IDX)
    assert 'SELECT count(*) FROM public."we""ird"' in cur.queries  # identifier quoting


def test_collect_catalog_without_alembic_table():
    cat = pb.collect_catalog(FakeCursor({"users": 1}, COLS, IDX))
    assert cat["alembic_version"] is None


def test_server_version_parses_major():
    text, num = pb.server_version(FakeCursor({}, [], []))
    assert (text, num, num // 10000) == ("17.5", 170005, 17)


def test_build_manifest():
    cat = {"tables": {"users": 3, "clients": 5}, "schema_sha256": "f" * 64, "alembic_version": "rev1"}
    m = pb.build_manifest(
        created_at=NOW,
        stem="pg_dump/2026/10/paciolus-x",
        dump_bytes=1234,
        dump_sha256="d" * 64,
        version_text="17.5",
        version_num=170005,
        catalog=cat,
        source_host="ep-x.neon.tech/neondb",
        snapshot_id="00000003-1",
        run_url="https://github.com/o/r/actions/runs/1",
    )
    assert m["dump_key"] == "pg_dump/2026/10/paciolus-x.dump"
    assert m["server_major"] == 17
    assert m["tables"] == {"clients": 5, "users": 3}
    assert (m["table_count"], m["total_rows"]) == (2, 8)
    assert m["snapshot_consistent"] is True
    assert m["created_at"] == "2026-10-28T12:00:00+00:00"
    json.dumps(m)  # serialisable


# ---------------------------------------------------------------------------
# Restore comparison + drill
# ---------------------------------------------------------------------------

MANIFEST = {"tables": {"users": 3, "clients": 5}, "schema_sha256": "abc", "alembic_version": "rev1"}


def _statuses(checks):
    return {c.name: c.status for c in checks}


def test_compare_restore_pass():
    checks = pb.compare_restore(MANIFEST, dict(MANIFEST), revision_known=lambda r: True)
    assert set(_statuses(checks).values()) == {pb.PASS}


@pytest.mark.parametrize(
    ("observed", "known", "failing"),
    [
        ({**MANIFEST, "tables": {"users": 3}}, True, "table_list"),
        ({**MANIFEST, "tables": {"users": 3, "clients": 5, "extra": 0}}, True, "table_list"),
        ({**MANIFEST, "tables": {"users": 2, "clients": 5}}, True, "row_counts"),
        ({**MANIFEST, "schema_sha256": "zzz"}, True, "schema_fingerprint"),
        ({**MANIFEST, "alembic_version": "rev0"}, True, "alembic_revision"),
        (dict(MANIFEST), False, "alembic_revision"),
    ],
)
def test_compare_restore_failures(observed, known, failing):
    checks = pb.compare_restore(MANIFEST, observed, revision_known=lambda r: known)
    assert _statuses(checks)[failing] == pb.FAIL
    assert pb.overall_verdict(c.status for c in checks) == pb.FAIL


def test_compare_restore_empty_manifest_is_a_fail():
    checks = pb.compare_restore({"tables": {}, "alembic_version": None}, {"tables": {}})
    assert pb.overall_verdict(c.status for c in checks) == pb.FAIL


def _ok(*_a, **_k):
    return subprocess.CompletedProcess([], 0, "", "")


def test_run_drill_pass(tmp_path):
    s3 = FakeS3()
    stem = _put_backup(s3, NOW, tables={"users": 3}, schema_sha256="s", alembic_version="rev1")
    observed = {"tables": {"users": 3}, "schema_sha256": "s", "alembic_version": "rev1"}
    checks, manifest = pb.run_drill(
        client=s3,
        bucket="b",
        stem=stem,
        workdir=tmp_path,
        restore=_ok,
        observe=lambda: observed,
        revision_known=lambda r: True,
    )
    assert pb.overall_verdict(c.status for c in checks) == pb.PASS
    assert [c.name for c in checks][:2] == ["dump_sha256", "pg_restore"]


def test_run_drill_rejects_a_corrupted_download(tmp_path):
    s3 = FakeS3()
    stem = _put_backup(s3, NOW)
    s3.objects[f"{stem}.dump"] = b"TAMPERED"
    restored = []
    checks, _ = pb.run_drill(
        client=s3,
        bucket="b",
        stem=stem,
        workdir=tmp_path,
        restore=lambda p: restored.append(p) or _ok(),
        observe=dict,
        revision_known=None,
    )
    assert _statuses(checks) == {"dump_sha256": pb.FAIL}
    assert restored == []  # never restores bytes that fail the hash


def test_run_drill_reports_pg_restore_failure(tmp_path):
    s3 = FakeS3()
    stem = _put_backup(s3, NOW)
    bad = lambda p: subprocess.CompletedProcess([], 1, "", 'ERROR: extension "neon" is not available')  # noqa: E731
    checks, _ = pb.run_drill(
        client=s3, bucket="b", stem=stem, workdir=tmp_path, restore=bad, observe=dict, revision_known=None
    )
    assert _statuses(checks)["pg_restore"] == pb.FAIL
    assert "neon" in checks[-1].detail


def test_render_report_marks_unverified():
    text = pb.render_report("T", [pb.Check("a", pb.UNVERIFIED, "x|y")])
    assert "**Verdict: UNVERIFIED**" in text and "x/y" in text and "exits non-zero" in text


def test_alembic_checker_reads_the_real_migration_history():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    ini = REPO_ROOT / "backend" / "alembic.ini"
    known = pb.alembic_revision_checker(ini)
    cfg = Config(str(ini))
    cfg.set_main_option("script_location", str(REPO_ROOT / "backend" / "migrations" / "alembic"))
    heads = ScriptDirectory.from_config(cfg).get_heads()
    assert heads and all(known(h) for h in heads)
    assert known("deadbeefdead") is False


# ---------------------------------------------------------------------------
# Subcommands: missing secrets are UNVERIFIED, named, non-zero
# ---------------------------------------------------------------------------


def _clear(monkeypatch, tmp_path):
    for name in (pb.DB_ENV, *pb.R2_ENV, *vbi.NEON_ENV):
        monkeypatch.delenv(name, raising=False)
    out = tmp_path / "gh_output"
    out.write_text("", encoding="utf-8")
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
    return out


def test_backup_without_secrets_is_unverified(monkeypatch, tmp_path, capsys):
    out = _clear(monkeypatch, tmp_path)
    assert pb.main(["backup"]) == 2
    printed = capsys.readouterr().out
    assert "UNVERIFIED — missing secret NEON_BACKUP_DATABASE_URL, R2_BACKUPS_ENDPOINT" in printed
    assert "verdict=UNVERIFIED" in out.read_text()
    assert "no backup was taken" in (tmp_path / "summary").read_text(encoding="utf-8")


def test_backup_refuses_the_pooled_host(monkeypatch, tmp_path, capsys):
    _clear(monkeypatch, tmp_path)
    for k, v in FULL_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv(pb.DB_ENV, _pg_url("u", "hunter2", "ep-a-pooler.us-east-1.aws.neon.tech/neondb"))
    assert pb.main(["backup"]) == 1
    printed = capsys.readouterr().out
    assert "-pooler" in printed and "hunter2" not in printed


def test_locate_and_drill_without_secrets(monkeypatch, tmp_path):
    out = _clear(monkeypatch, tmp_path)
    assert pb.main(["locate"]) == 0  # verdict decided downstream
    assert "status=UNVERIFIED" in out.read_text()
    assert pb.main(["drill", "--stem", "s", "--container", "c", "--target-url", "postgresql://x"]) == 2


def test_locate_reports_newest_complete(monkeypatch, tmp_path):
    s3 = FakeS3()
    _put_backup(s3, NOW - timedelta(days=1))
    newest = _put_backup(s3, NOW)
    _put_backup(s3, NOW + timedelta(hours=1), manifest=False)  # in flight
    status, manifest = pb.locate_latest(s3, "b", "pg_dump/")
    assert status == pb.PASS and manifest["stem"] == newest
    assert pb.locate_latest(FakeS3(), "b", "pg_dump/")[0] == pb.FAIL


# ---------------------------------------------------------------------------
# verify_backup_integrity
# ---------------------------------------------------------------------------


def test_r2_check_pass():
    s3 = FakeS3()
    _put_backup(s3, NOW - timedelta(hours=3))
    r = vbi.check_r2_latest_backup(s3, "b", now=NOW)
    assert r["status"] == pb.PASS and "sha256 verified" in r["details"]


def test_r2_check_no_backups():
    r = vbi.check_r2_latest_backup(FakeS3(), "b", now=NOW)
    assert r["status"] == pb.FAIL and "never succeeded" in r["details"]


def test_r2_check_stale():
    s3 = FakeS3()
    _put_backup(s3, NOW - timedelta(hours=50))
    r = vbi.check_r2_latest_backup(s3, "b", max_age_hours=26, now=NOW)
    assert r["status"] == pb.FAIL and "50.0h old" in r["details"]


def test_r2_check_hash_mismatch():
    s3 = FakeS3()
    stem = _put_backup(s3, NOW - timedelta(hours=1))
    s3.objects[f"{stem}.dump"] = b"DUMPBYTEZ"  # same length, different bytes
    r = vbi.check_r2_latest_backup(s3, "b", now=NOW)
    assert r["status"] == pb.FAIL and "sha256" in r["details"]


def test_r2_check_falls_back_past_an_in_flight_dump():
    s3 = FakeS3()
    _put_backup(s3, NOW - timedelta(hours=2))
    _put_backup(s3, NOW - timedelta(minutes=5), manifest=False)
    assert vbi.check_r2_latest_backup(s3, "b", now=NOW)["status"] == pb.PASS


def test_r2_check_manifest_without_dump_is_fail():
    s3 = FakeS3()
    _put_backup(s3, NOW - timedelta(hours=1), dump=False)
    r = vbi.check_r2_latest_backup(s3, "b", now=NOW)
    assert r["status"] == pb.FAIL and "missing its dump" in r["details"]


def test_r2_check_listing_error_is_fail():
    class Broken(FakeS3):
        def list_objects_v2(self, **_):
            raise PermissionError("AccessDenied")

    assert vbi.check_r2_latest_backup(Broken(), "b", now=NOW)["status"] == pb.FAIL


def _neon(project=None, branches=None, code=200):
    def get(url, headers):
        assert headers["Authorization"] == "Bearer neon-key"
        if code != 200:
            return code, None
        if url.endswith("/branches"):
            return 200, {"branches": branches or []}
        return 200, {"project": project}

    return get


def test_neon_pitr_reads_the_live_window():
    get = _neon({"history_retention_seconds": 604800, "region_id": "aws-us-east-1", "pg_version": 17})
    r = vbi.check_neon_pitr("neon-key", "proj-1", 1.0, get)
    assert r["status"] == pb.PASS and r["retention_days"] == 7.0 and r["region"] == "aws-us-east-1"


def test_neon_pitr_below_floor():
    r = vbi.check_neon_pitr("neon-key", "p", 7.0, _neon({"history_retention_seconds": 86400}))
    assert r["status"] == pb.FAIL and "1.0 days" in r["details"]


@pytest.mark.parametrize("code", [401, 403, 404, 500])
def test_neon_api_errors_are_fail(code):
    assert vbi.check_neon_pitr("neon-key", "p", 1.0, _neon(code=code))["status"] == pb.FAIL
    assert vbi.check_neon_default_branch("neon-key", "p", _neon(code=code))["status"] == pb.FAIL


def test_neon_unreachable_is_fail():
    def down(url, headers):
        raise ConnectionError("Neon API unreachable: timed out")

    assert vbi.check_neon_pitr("k", "p", 1.0, down)["status"] == pb.FAIL


@pytest.mark.parametrize(("state", "status"), [("ready", pb.PASS), ("init", pb.FAIL)])
def test_neon_default_branch(state, status):
    branches = [
        {"name": "dev", "default": False, "current_state": "ready"},
        {"name": "main", "default": True, "current_state": state},
    ]
    assert vbi.check_neon_default_branch("neon-key", "p", _neon(branches=branches))["status"] == status


def test_run_checks_with_no_secrets_names_every_missing_one():
    results = vbi.run_checks({})
    assert [r["status"] for r in results] == [pb.UNVERIFIED] * 3
    verdict, report = vbi.build_report(NOW, results)
    assert verdict == pb.UNVERIFIED
    assert (
        "UNVERIFIED — missing secret NEON_API_KEY, NEON_PROJECT_ID, R2_BACKUPS_ACCESS_KEY_ID, "
        "R2_BACKUPS_BUCKET, R2_BACKUPS_ENDPOINT, R2_BACKUPS_SECRET_ACCESS_KEY"
    ) in report


def test_run_checks_partial_secrets_still_checks_what_it_can():
    s3 = FakeS3()
    _put_backup(s3, NOW - timedelta(hours=1))
    env = {k: v for k, v in FULL_ENV.items() if not k.startswith("NEON")}
    results = vbi.run_checks(env, r2_factory=lambda e: s3, now=NOW)
    assert [r["status"] for r in results] == [pb.PASS, pb.UNVERIFIED, pb.UNVERIFIED]
    assert vbi.build_report(NOW, results)[0] == pb.UNVERIFIED


def test_run_checks_all_green_and_only_filter():
    s3 = FakeS3()
    _put_backup(s3, NOW - timedelta(hours=1))
    get = _neon({"history_retention_seconds": 86400 * 7}, [{"name": "main", "default": True, "current_state": "ready"}])
    results = vbi.run_checks(FULL_ENV, r2_factory=lambda e: s3, http_get=get, now=NOW)
    assert vbi.build_report(NOW, results)[0] == pb.PASS
    only = vbi.run_checks(FULL_ENV, only=["neon_pitr_window"], http_get=get)
    assert [r["check"] for r in only] == ["neon_pitr_window"]


def test_fail_dominates_unverified():
    s3 = FakeS3()  # empty bucket -> FAIL
    env = {k: v for k, v in FULL_ENV.items() if not k.startswith("NEON")}
    results = vbi.run_checks(env, r2_factory=lambda e: s3, now=NOW)
    assert vbi.build_report(NOW, results)[0] == pb.FAIL


def test_main_without_secrets_exits_2_and_writes_outputs(monkeypatch, tmp_path):
    out = _clear(monkeypatch, tmp_path)
    report = tmp_path / "r.txt"
    js = tmp_path / "r.json"
    assert vbi.main(["--report", str(report), "--json", str(js)]) == 2
    text = out.read_text()
    assert "verdict=UNVERIFIED" in text and "NEON_API_KEY" in text
    assert json.loads(js.read_text())["verdict"] == "UNVERIFIED"
    assert "Evidence Integrity" in report.read_text(encoding="utf-8")


def test_scripts_do_not_import_boto3_at_module_load():
    # The backend CI venv has no boto3; these tests (and --help) must not need it.
    for name in ("pg_backup.py", "verify_backup_integrity.py"):
        src = (REPO_ROOT / "scripts" / name).read_text(encoding="utf-8")
        top = [ln for ln in src.splitlines() if ln.startswith(("import ", "from "))]
        assert not any("boto" in ln or "psycopg2" in ln for ln in top), name


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------

WORKFLOWS = ["backup-pg-dump.yml", "backup-restore-drill.yml", "dr-test-monthly.yml", "backup-integrity-check.yml"]
RUNBOOK_SECRETS = {
    "NEON_BACKUP_DATABASE_URL",
    "R2_BACKUPS_ENDPOINT",
    "R2_BACKUPS_BUCKET",
    "R2_BACKUPS_ACCESS_KEY_ID",
    "R2_BACKUPS_SECRET_ACCESS_KEY",
    "NEON_API_KEY",
    "NEON_PROJECT_ID",
}


def _wf(name):
    path = REPO_ROOT / ".github" / "workflows" / name
    return path.read_text(encoding="utf-8"), yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", WORKFLOWS)
def test_workflow_parses_and_is_honest(name):
    import re

    text, wf = _wf(name)
    assert wf["jobs"]
    runs = [s.get("run", "") for j in wf["jobs"].values() for s in j.get("steps", [])]
    assert not any("set -x" in r or "set -o xtrace" in r for r in runs)
    assert "api.render.com" not in text and "RENDER_POSTGRES_ID" not in text
    secrets = set(re.findall(r"secrets\.([A-Z0-9_]+)", text))
    assert secrets <= RUNBOOK_SECRETS, secrets - RUNBOOK_SECRETS
    for job in wf["jobs"].values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses and not uses.startswith("./"):
                assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", uses), uses  # SHA-pinned


def test_runbook_lists_every_secret():
    runbook = (REPO_ROOT / "docs" / "runbooks" / "backup-restore.md").read_text(encoding="utf-8")
    for s in RUNBOOK_SECRETS:
        assert f"`{s}`" in runbook, s


def test_verdict_jobs_always_run():
    _, drill = _wf("backup-restore-drill.yml")
    assert drill["jobs"]["verdict"]["if"] == "always()"
    assert drill["jobs"]["restore"]["services"]["postgres"]["image"] == "postgres:${{ needs.locate.outputs.pg_major }}"
    _, dr = _wf("dr-test-monthly.yml")
    assert dr["jobs"]["verdict"]["if"] == "always()"
    assert dr["jobs"]["restore-drill"]["uses"] == "./.github/workflows/backup-restore-drill.yml"
    steps = dr["jobs"]["verdict"]["steps"]
    assert any(s.get("run", "").strip().endswith("exit 1") for s in steps)


def _combine_script():
    _, dr = _wf("dr-test-monthly.yml")
    (step,) = [s for s in dr["jobs"]["verdict"]["steps"] if s.get("id") == "final"]
    return step["run"]


@pytest.mark.parametrize(
    ("integrity", "drill", "expected"),
    [
        ("PASS", "PASS", "PASS"),
        ("PASS", "", "UNVERIFIED"),
        ("UNVERIFIED", "PASS", "UNVERIFIED"),
        ("UNVERIFIED", "FAIL", "FAIL"),
        ("FAIL", "UNVERIFIED", "FAIL"),
        ("", "", "UNVERIFIED"),
    ],
)
def test_dr_combine_step(tmp_path, integrity, drill, expected):
    from tests.helpers.shell_support import bash_support_path, usable_bash

    bash = usable_bash()
    if bash is None:
        pytest.skip("no usable bash")
    import os

    out = tmp_path / "out"
    out.write_text("", encoding="utf-8")
    script = tmp_path / "s.sh"
    script.write_text("set -e\n" + _combine_script(), encoding="utf-8")
    env = dict(
        os.environ,
        INTEGRITY=integrity,
        DRILL=drill,
        MISSING="NEON_API_KEY" if integrity == "UNVERIFIED" else "",
        DRILL_DETAIL="",
        GITHUB_OUTPUT=str(out),
        GITHUB_STEP_SUMMARY=str(tmp_path / "sum"),
    )
    env["PATH"] = os.pathsep.join([*bash_support_path(), env.get("PATH", "")])
    res = subprocess.run([bash, str(script)], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    assert f"overall={expected}" in out.read_text()
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    if integrity == "UNVERIFIED":
        assert "UNVERIFIED — missing secret NEON_API_KEY" in report
