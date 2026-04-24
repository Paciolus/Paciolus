# Observability Runbook: Grafana Loki

**Sprint:** 716
**Integration:** In-process Python logging handler (stdlib only) → Grafana Cloud Loki HTTPS push.
**Cost:** $0 on Grafana Cloud Free tier (roughly 50 GB/mo ingest, ~14-day retention — verify current limits in the Grafana Cloud console before making assumptions).

This runbook covers how to configure, operate, and troubleshoot the Loki log stream for `paciolus-api`.

---

## 1. Architecture

Application logs flow to two destinations in parallel:

1. **stdout** (unchanged) — captured by Render's log tail for live tailing.
2. **Loki HTTPS push** — via `backend/loki_handler.py`, a background-thread handler that batches records and POSTs JSON to Grafana Cloud.

The handler is **fail-open**: if Loki is unreachable, batches are dropped, a rate-limited warning is written to stderr, and the application continues. No request-path logs block on Loki I/O.

Render's native "Log Streams" integration expects TCP/syslog and is **not** used — the two protocols don't bridge without a sidecar. See Sprint 716 Review for the rationale.

---

## 2. Credentials

| Field | Value | Source |
|---|---|---|
| Push URL | `https://logs-prod-042.grafana.net/loki/api/v1/push` | Grafana Cloud stack `paciolus`, Loki instance `paciolus-logs` |
| Basic Auth user | `1566612` | Loki instance ID |
| Basic Auth password | `glc_…` | Access policy `render-log-drain` (scope: `logs:write`, realm: `paciolus` stack only, no expiry) |
| Cluster region | `prod-us-east-3` (US East, Virginia) | Provisioning 2026-04-24 |

The token is held by the CEO in their password manager. Re-issue by creating a new token under the `render-log-drain` access policy (see `grafana.com/orgs/paciolus/access-policies`). Rotate by issuing a new token, updating Render env vars, then revoking the old token.

---

## 3. Render env vars

Required on `paciolus-api` for the handler to attach. All three must be set; otherwise the handler is a no-op and the app falls back to stdout-only.

| Variable | Value |
|---|---|
| `LOKI_URL` | `https://logs-prod-042.grafana.net/loki/api/v1/push` |
| `LOKI_USER` | `1566612` |
| `LOKI_TOKEN` | `glc_…` (from password manager) |

Restart required after setting (Render auto-restarts on env var change).

Verification after restart:
```
# Render logs should show this startup line:
Observability: sentry=enabled, loki=enabled
```

If it shows `loki=disabled`, one of the three vars is missing or empty.

---

## 4. Saved queries

Create these under **Explore → Loki → Saved queries** in `https://paciolus.grafana.net`. All use the `grafanacloud-paciolus-logs` data source.

| # | Name | LogQL |
|---|------|-------|
| 1 | Auth failures | `{service="paciolus-api"} \|~ "(401\|403)" \|~ "/auth/"` |
| 2 | 5xx errors | `{service="paciolus-api"} \|~ "status.{1,3}5[0-9][0-9]"` |
| 3 | Slow requests (>5s) | `{service="paciolus-api"} \| json \| duration_ms > 5000` |
| 4 | Scheduler errors | `{service="paciolus-api"} \|= "cleanup_scheduler" \| json \| level="ERROR"` |
| 5 | SendGrid 403 | `{service="paciolus-api"} \|= "SendGrid HTTPError status=403"` |
| 6 | Audit-engine warnings | `{service="paciolus-api"} \|= "audit_engine" \| json \| level="WARNING"` |

**Label note:** our handler emits `level` and `logger` as stream labels, but Grafana Cloud's ingest pipeline keeps only `env`, `service`, and `service_name` as indexed stream labels at our traffic volume. Queries that filter on level/logger therefore use a line-filter (`|=` / `|~`) followed by `| json | level="…"` to parse the JSON body and filter on the parsed field, rather than indexed-label selectors. Same result, slightly heavier query cost, but the index overhead is fine at Free-tier volume.

Query #3 will not match anything today — we don't log `duration_ms` yet. Saved as documentation of intent; it will populate once request-duration logging lands.

Query #5 closes the loop on Sprint 715 — once 24h of post-deploy traffic has flowed, the result histogram shows recipient + path patterns triggering the 403.

---

## 5. Free-tier limits

Verify current limits at `grafana.com/orgs/paciolus/my-account/usage` before making plans based on the numbers below.

| Metric | Approximate Free-tier cap |
|---|---|
| Logs ingest | ~50 GB/month |
| Logs retention | ~14 days |
| Query concurrency | Low — not suitable for dashboards with many concurrent panels |

`paciolus-api` currently produces low-single-digit GB/month in normal operation. If Free-tier ingest exceeds the cap:
1. Tighten log levels — production default is `INFO`; consider `WARNING` for noisy modules (`sqlalchemy.engine`, `multipart`) if they leak through.
2. Drop debug/trace labels.
3. Upgrade to Pro (~$0.50/GB ingested) — still deferred under Sprint 716's "free only" constraint; would require a new sprint.

---

## 6. Troubleshooting

### `loki=disabled` at startup
All three env vars must be set and non-empty. Check `/health` endpoint logs for the `Observability: …` line.

### stderr warning: `[LokiHandler] Loki push failed: …`
- **Connection refused / DNS error:** Grafana Cloud is down — check `status.grafana.com`. The app continues on stdout.
- **HTTP 401 / 403:** Token revoked or access policy scope wrong. Regenerate under the `render-log-drain` access policy (must have `logs:write` scope). Don't widen the scope.
- **HTTP 429:** Ingest rate limit — Free-tier limits hit. Tighten log levels or queue up a Pro upgrade sprint.
- **HTTP 5xx:** Transient Grafana-side — the handler drops the batch and the warning is rate-limited to once per 5 minutes; no action needed unless the warning is persistent.

### Logs missing from Loki but present in Render stdout
- Background thread may be backed up: emit queue (10k records) fills when Loki is slow. Silent drops are by design — check stderr for the warning.
- Records with timestamps far in the past (>1h) may be rejected by Loki — this usually means clock skew on the application host.

### Rotating the token
1. Create a new token under access policy `render-log-drain` (grafana.com → Access Policies → render-log-drain → Add token).
2. Update `LOKI_TOKEN` env var on Render.
3. After Render restarts and you've confirmed ingest continues, revoke the old token.

---

## 7. Out of scope (for now)

- **Custom dashboards** — saved queries only. Promote a query to a dashboard panel if it gets reused enough to warrant.
- **Alerting rules** — Sentry handles exception alerting. Loki-based alerting is a separate sprint if Sentry proves insufficient for quiet-anomaly detection.
- **pgBackRest / Secrets Manager / pen test / SOC 2 auditor** — still deferred per CEO directive 2026-04-24. See `tasks/EXECUTIVE_BLOCKERS.md`.
