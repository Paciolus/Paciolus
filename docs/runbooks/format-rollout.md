# Format Rollout / Rollback Playbook

## Overview
This playbook covers the operational procedures for enabling a new file format parser in production, monitoring its health during rollout, performing rollback if issues arise, and the pre-launch checklist for any new format addition. It applies to all parser formats (CSV, XLSX, ODS, PDF, OFX/QBO, IIF, TSV/TXT) and any future format additions.

## Enabling a New Format

### Step 1: Feature Flag Activation
Each format has a feature flag in the environment configuration:

```
FORMAT_CSV_ENABLED=true
FORMAT_XLSX_ENABLED=true
FORMAT_ODS_ENABLED=true
FORMAT_PDF_ENABLED=true
FORMAT_OFX_ENABLED=true
FORMAT_IIF_ENABLED=true
FORMAT_TSV_ENABLED=true
```

To enable a new format:
1. Set `FORMAT_<X>_ENABLED=true` in the `.env` file
2. Restart the backend service
3. Verify the format appears in the `/health` endpoint's supported formats list

### Step 2: Tier Gating via Entitlements
New formats can be gated by user tier using the entitlements system:

- `shared/entitlements.py` defines `TierEntitlements` with format access lists per tier
- `shared/entitlement_checks.py` provides `check_tool_access()` for route-level enforcement
- During initial rollout, a format can be restricted to higher tiers (e.g., Professional and above) before opening to all users

**Rollout progression example:**
1. **Week 1-2**: Enterprise only (internal testing with real user data patterns)
2. **Week 3-4**: Professional + Enterprise (broader exposure, still paying users)
3. **Week 5+**: All tiers (general availability)

To adjust tier access:
1. Update the format's tier mapping in `shared/entitlements.py`
2. Restart the backend service
3. Verify access by testing with accounts at each tier level

### Step 3: Alert Threshold Configuration
Configure format-specific alert thresholds in `guards/parser_alerts.toml`:

```toml
[format_name]
error_rate_percent = 10
p95_latency_seconds = 5
max_concurrent = 50
```

New formats should start with **higher thresholds** (1.5x-2x the expected steady-state values) and be tightened as production data validates the parser's reliability.

## Monitoring During Rollout

### Key Metrics
Monitor these metrics in the first 48 hours after enabling a new format:

| Metric | What to Watch |
|--------|--------------|
| `paciolus_parse_total{format="X"}` | Volume -- is the format being used? |
| `paciolus_parse_errors_total{format="X"}` | Error count -- is it within threshold? |
| `paciolus_parse_duration_seconds{format="X"}` | Latency -- any outliers or trends? |
| `paciolus_active_parses{format="X"}` | Concurrency -- any stuck parses? |

### Health Checks
- `/health` endpoint includes parser status for each enabled format
- `/metrics` endpoint exposes Prometheus metrics for dashboards and alerting

### What to Look For
1. **Error clustering**: Are errors coming from a single user/client, or distributed?
2. **Latency trends**: Is P95 latency stable or increasing over time?
3. **Stuck parses**: Is `active_parses` ever non-zero for extended periods (>60s)?
4. **Memory pressure**: Are large files in the new format causing memory spikes?
5. **Tier distribution**: Which user tiers are uploading this format most?

## Rollback Procedure

### Immediate Rollback (< 5 minutes)
1. Set `FORMAT_<X>_ENABLED=false` in `.env`
2. Restart the backend service
3. Verify `/metrics` shows zero active parses for the format
4. Verify `/health` no longer lists the format as supported
5. Notify affected users via support channels if the format was publicly available

### Graceful Rollback (allowing in-flight parses to complete)
1. Set `FORMAT_<X>_ENABLED=false` in `.env` (new uploads rejected)
2. Wait for `paciolus_active_parses{format="X"}` to reach zero (in-flight parses complete)
3. Restart the backend service
4. Verify the format is fully disabled

### Post-Rollback Actions
1. Collect sample files that caused failures for reproduction
2. Document the root cause in the format's parser runbook
3. File a bug with reproduction steps
4. Determine if the issue is a parser bug (fixable) or a fundamental format limitation (may need user-facing guidance)

## New Format Launch Checklist

Before enabling any new format in production, verify all items:

### Parser Implementation
- [ ] Parser module exists in `backend/shared/` or `backend/` with full error handling
- [ ] All known error conditions return HTTP 422 with descriptive error messages
- [ ] File size limits enforced (global body size middleware)
- [ ] Cell/row/column limits enforced where applicable
- [ ] Security guards in place (archive bomb, XML bomb, formula injection as applicable)
- [ ] Parser runs via `asyncio.to_thread()` if CPU-bound

### Testing
- [ ] Unit tests cover happy path and all documented error conditions
- [ ] Malformed fixture files exist in `tests/fixtures/` for each error type
- [ ] Resource guard tests verify memory and time limits
- [ ] Integration tests verify end-to-end upload and parse flow

### Observability
- [ ] Prometheus metrics instrumented (`parse_total`, `parse_errors_total`, `parse_duration_seconds`, `active_parses`)
- [ ] Alert thresholds configured in `guards/parser_alerts.toml`
- [ ] Parser runbook created in `docs/runbooks/parser-<format>.md`

### Configuration
- [ ] Feature flag added: `FORMAT_<X>_ENABLED` (default `false`)
- [ ] Tier gating configured in `shared/entitlements.py`
- [ ] Format added to `/health` endpoint's supported formats list

### Rollout Plan
- [ ] Initial tier restriction decided (e.g., Enterprise-only for week 1)
- [ ] Alert thresholds set to rollout values (higher than steady-state)
- [ ] Monitoring dashboard updated with new format panels
- [ ] Rollback procedure tested in staging
- [ ] Support team briefed on new format and common error resolutions

## Escalation Matrix

| Severity | Condition | Action |
|----------|-----------|--------|
| **P3** | Error rate above threshold but below 2x | Monitor for 1 hour. If stable, investigate root cause during business hours. |
| **P2** | Error rate above 2x threshold, or latency above 2x threshold | Page on-call engineer. Begin investigation immediately. Consider graceful rollback if no fix within 30 minutes. |
| **P1** | Active parses stuck > 0 for more than 60 seconds, or service-wide degradation | Immediate rollback. Page on-call engineer. Post-incident review required. |

## Steady-State Threshold Targets

After a format has been in production for 30+ days with stable metrics, tighten alert thresholds to these targets:

| Format | Error Rate | P95 Latency |
|--------|-----------|-------------|
| CSV | 5% | 2s |
| XLSX/XLS | 8% | 5s |
| ODS | 8% | 5s |
| PDF | 20% | 15s |
| OFX/QBO | 10% | 3s |
| IIF | 10% | 3s |
| TSV/TXT | 5% | 2s |
