# Memory Pressure Runbook

**Sprint:** 722

This runbook is for engineers responding to the `memo.memory.threshold_breach`
log line, the Sentry "Memo memory threshold exceeded" warning, or a Render
worker that OOM-kills mid-export.

The platform's memo generators (ReportLab + openpyxl + pdfplumber pipelines)
allocate aggressively and rely on Python GC for cleanup. On Render Standard
(2 GB / worker) the bloat does not matter for a single export, but a session
that fires multiple memos back-to-back can climb past the soft headroom we
keep for request payloads, SQLAlchemy session caches, and OS slab. Sprint 722
added a uniform RSS probe + GC sweep at every memo route boundary so that
pressure is visible before OOM-kill.

## 1. Architecture

| Component | Path | Purpose |
|---|---|---|
| Probe + soft threshold | `backend/shared/memory_budget.py` | `track_memo_memory(label)` context manager. Logs RSS before/after, runs `gc.collect()`, fires Sentry warning when post-RSS > `MEMO_RSS_WARN_MB`. |
| Wired into memo handler | `backend/routes/export_memos.py::_memo_export_handler` | Wraps every memo PDF generation. New memo routes inherit the probe automatically. |
| Regression tests | `backend/tests/test_memo_memory_budget.py` | Unit-tests the probe + a `slow`-marked bound on RSS growth across 5 sequential JE memo generations. |

## 2. Configuration

| Env var | Default | Notes |
|---|---|---|
| `MEMO_RSS_WARN_MB` | `1500` | Threshold (MB) above which a Sentry warning fires. Render Standard exposes 2 GB / worker; the default keeps ~500 MB headroom. Set lower in staging to flush leaks; set higher only with a documented justification. |

There is **no** Render-side recycle config in this repo (Render is managed
via the dashboard). Operational `maxRequestsPerWorker` / `gunicorn.max_requests`
should be set per-environment in the Render service config; the recommended
starting value is `200` with `max_requests_jitter=50` so workers recycle before
fragmentation accumulates.

## 3. Reading the logs

Every memo export emits two structured lines plus optional warning:

```
INFO  memo.memory.before  label=Revenue Testing memo  rss_mb=412.3
INFO  memo.memory.after   label=Revenue Testing memo  rss_mb=489.7  delta_mb=+77.4  elapsed_ms=1820
WARN  memo.memory.threshold_breach label=Revenue Testing memo rss_mb=1612.0 threshold_mb=1500
```

In Loki (Grafana Cloud), the saved query for memo memory pressure is:

```logql
{service="paciolus-api"} |= "memo.memory" | json | level="warning"
```

To see RSS-deltas-by-memo over the last hour:

```logql
{service="paciolus-api"} |= "memo.memory.after"
  | regexp `label=(?P<label>[A-Za-z0-9 ]+) rss_mb=[0-9.]+ delta_mb=(?P<delta>[+-][0-9.]+)`
  | unwrap delta
```

## 4. Response by symptom

### 4a. Single Sentry warning, no OOM kill
Most likely a single tenant generated a heavy memo (e.g., revenue testing on a
12-month TB with high transaction volume). Action: check `delta_mb` on the
`memo.memory.after` line that preceded the breach. If `delta_mb` is unusually
large for that memo type, capture the input shape (no PII — engagement_id is
fine) for offline reproduction.

### 4b. Repeated warnings on the same worker
Indicates either (a) `gc.collect()` was removed / regressed, or (b) a real
leak in a generator's ReportLab construction (e.g., un-closed StoryBuilder).
Action: deploy a build with `MEMO_RSS_WARN_MB=600` to staging and run the
nightly slow test against the suspect generator:

```bash
cd backend && python -m pytest tests/test_memo_memory_budget.py -m slow -v
```

If the test fails, the leak is in the generator. If the test passes, the leak
is in a memo not covered by the slow test — expand coverage to that memo.

### 4c. Worker OOM-kill (Render dashboard, exit code 137)
The probe didn't catch it in time — RSS climbed past the threshold faster than
a single export's window. Action sequence:
1. **Immediate:** lower `MEMO_RSS_WARN_MB` to `1200` (more headroom for the
   per-export burst) and confirm Render's worker recycle is set to ≤200.
2. **Short-term:** look for a single tenant who hit ≥3 memo exports in <60s
   in admin dashboard / structured logs. Their memo input is likely the
   adversarial fixture worth adding to the slow test.
3. **Medium-term:** if the same memo type repeatedly drives the OOM, that
   generator is leaking and needs profiling. Use `tracemalloc.start()` /
   `tracemalloc.take_snapshot()` around the failing call and ship the
   summary in a new sprint.

## 5. Why the probe is in `_memo_export_handler` and not in each generator

Wrapping every generator individually would have meant 18 places to remember,
plus a coupling between domain code and observability. The handler is the
single chokepoint that all 18 memo exports already pass through, so wiring it
once gives uniform coverage and free inheritance for any new memo endpoint
added in a future sprint.

The trade-off: memos invoked outside the route layer (e.g., engagement-export
ZIP, batch jobs) bypass the probe. As of Sprint 722 there is exactly one such
path — `engagement_export.py::generate_zip` — and it generates a single
anomaly summary PDF, not 18 memos. If that surface ever grows to bundle the
full memo set, it should call `track_memo_memory(label)` directly.

## 6. Related

- Sprint 712: nightly false-green incident — the lesson "verify against the
  live system" applies when interpreting RSS metrics from staging vs prod.
- Sprint 716: Loki ingestion runbook — the LogQL pattern above relies on the
  line-filter approach documented there (level/logger are not indexed labels).
