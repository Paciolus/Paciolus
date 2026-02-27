# Usage Metrics Review — Sprint 446

**Date:** 2026-02-26
**Scope:** Local observability signals (code-level analysis). Live Sentry/Stripe dashboard access required for full review — flagged below where live data is needed.

---

## Prometheus / Backend Observability

### Metrics Inventory (from `shared/parser_metrics.py`)

| Metric | Type | Labels | Status |
|--------|------|--------|--------|
| `paciolus_parse_total` | Counter | format, stage | Active — instrumented in file_formats.py |
| `paciolus_parse_errors_total` | Counter | format, stage, error_code | Active — instrumented in file_formats.py |
| `paciolus_parse_duration_seconds` | Histogram | format, stage | Active — instrumented in file_formats.py |
| `paciolus_active_parses` | Gauge | format | Active — incremented/decremented in file_formats.py |
| `paciolus_pricing_v2_checkouts_total` | Counter | tier, interval | Active — instrumented in billing/checkout.py |
| `paciolus_billing_events_total` | Counter | event_type, tier | Active — instrumented in billing/webhook_handler.py |
| `paciolus_active_trials` | Gauge | (none) | Active — set in subscription_manager.py |
| `paciolus_active_subscriptions` | Gauge | tier | Active — set in subscription_manager.py |

**All 8 metrics are wired. No dead-code risk detected from static analysis.**

### Alert Thresholds Review (`backend/guards/parser_alerts.toml`)

| Format | Error Rate Threshold | Latency P95 | Assessment |
|--------|---------------------|-------------|------------|
| CSV/TSV/TXT | 5.0% | 2.0s | Appropriately strict for well-structured formats |
| XLSX/XLS | 8.0% | 5.0s | Reasonable — Excel files can be large |
| ODS | 15.0% | 10.0s | Higher tolerance flagged as "rollout period" — **review after 30 days in production** |
| PDF | 20.0% | 15.0s | High tolerance appropriate for PDF variability |
| QBO/OFX/IIF | 10.0% | 3.0s | Reasonable for financial bank formats |

**Recommendation:** ODS threshold (15% / 10s) was set for rollout; reduce to 10% / 5.0s once stable adoption is confirmed in production.

### Request-ID Correlation

Structured logging with request-ID correlation was implemented in Phase XXVIII (Sprint 213). All log lines emitted via `logging_config.py`'s JSON formatter include `request_id`. Code review confirms this is applied in:
- `middleware/request_id.py` — sets `X-Request-ID` on every response
- `main.py` — registers middleware in lifespan

**No gaps detected from static analysis.**

---

## Sentry APM

**⚠️ LIVE DATA REQUIRED** — Cannot query Sentry dashboard from local analysis. Items below are code-level checks only.

### Zero-Storage Compliance (Code Review)
- `logging_config.py` sanitizes structured log output via `shared/log_sanitizer.py`
- Sentry integration (`sentry_integration.py`) reviewed: no user financial data in breadcrumbs
- `test_sentry_integration.py` at 94% coverage (2 uncovered lines: 51, 61 — error callback edge cases)

### Sanitize-Error Allow-List
`shared/log_sanitizer.py` maintains an allow-list of exception classes. Coverage gap at `test_sentry_integration.py:51,61` corresponds to the Sentry `before_send` callback edge cases (DSN not set). Low risk.

### Action Items (Require Live Sentry Access)
- [ ] Review top 5 errors by occurrence — especially `routes/export_diagnostics.py` (17% coverage, high likelihood of uncaught edge cases)
- [ ] Check P95 response times for `/audit/run` and `/tools/*/run` endpoints
- [ ] Verify no `ValueError` or `KeyError` from `workbook_inspector.py` (21% coverage)
- [ ] Confirm no financial data in any captured stack frame

---

## Stripe Billing Analytics

**⚠️ LIVE DATA REQUIRED** — Cannot query Stripe dashboard from local analysis. Items below are code-level checks only.

### BillingEvent Table Health (Code Review)
- `BillingEvent` model is append-only (no UPDATE/DELETE paths in routes or ORM)
- 10 event types covered: `subscription_created`, `subscription_updated`, `subscription_cancelled`, `trial_started`, `trial_ended`, `payment_succeeded`, `payment_failed`, `seat_added`, `seat_removed`, `plan_changed`
- Alembic migration `b590bb0555c3` confirmed in migration chain

### Webhook Delivery (Code Review)
- `billing/webhook_handler.py` at 85.2% coverage — 23 lines uncovered, likely in `handle_invoice_payment_failed` and `handle_customer_subscription_deleted` edge cases
- `test_billing_routes.py` at 100% coverage

### Action Items (Require Live Stripe Access)
- [ ] Review MRR breakdown by tier (Free/Solo/Team/Organization)
- [ ] Check trial conversion rate since billing launch
- [ ] Confirm webhook delivery rate ≥ 99% in Stripe Dashboard
- [ ] Verify `BillingEvent` row count matches Stripe event log total

---

## Signal Snapshot (Local)

| Signal | Value | Source |
|--------|-------|--------|
| Backend test coverage | 92.8% statements | pytest --cov (5,444 tests) |
| Frontend test coverage | 42.9% statements | jest --coverage (1,333 tests) |
| Prometheus metric count | 8 metrics (4 counters + 2 gauges + 1 histogram + 1 gauge) | parser_metrics.py |
| Sentry integration | Configured, 94% test coverage | test_sentry_integration.py |
| Request-ID logging | All routes via middleware | logging_config.py |

---

## Top 3 Reliability Risks

1. **Export Routes Untested (P1)** — `routes/export_diagnostics.py` (17%) and `routes/export_testing.py` (19%) are the two lowest-covered production route files. Any edge case in the 15+ export endpoints could surface as a runtime error in production with no test safety net.

2. **Billing Entitlement Gaps (P1)** — `shared/entitlement_checks.py` at 40.5% means tier boundary conditions and tool-access gating are partially untested. A logic error here could result in free-tier users accessing paid features.

3. **PDF/ODS Parser Edge Cases (P2)** — `workbook_inspector.py` (21%) handles the preview/inspection flow for all 10 file formats. Uncovered paths + high PDF error tolerance (20%) is a risk if malformed files reach production.

---

## Top 3 Product/Growth Signals

1. **File Format Adoption** — All 10 format parsers instrumented with Prometheus counters. Once live, `paciolus_parse_total{format="pdf"}` and `paciolus_parse_total{format="iif"}` will reveal which non-CSV formats are actually used.

2. **Trial Conversion** — `paciolus_active_trials` gauge + `paciolus_billing_events_total{event_type="trial_ended"}` will give trial→paid conversion rate once sufficient traffic flows.

3. **Seat Expansion** — `paciolus_billing_events_total{event_type="seat_added"}` tracks Team/Organization tier expansion; high values indicate healthy team growth.

---

## Ranked Action List

### Immediate (This Sprint)
- None from local analysis — no P0 reliability risks detected in code

### Next Sprint
- Add route integration tests for `export_diagnostics.py` and `export_testing.py` (P1 coverage gap)
- Add entitlement boundary tests for `shared/entitlement_checks.py` (P1 coverage gap)
- Pull live Sentry top-5 errors and add to this review

### Deferred
- ODS alert threshold review after 30 days production data
- Webhook handler edge case tests (`billing/webhook_handler.py` 85% → 95%)
- PDF parser `workbook_inspector.py` coverage (21% → 60%)
