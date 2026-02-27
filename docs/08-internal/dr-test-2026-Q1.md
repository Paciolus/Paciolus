# Backup Restore Test Report — Q1 2026

**Document Classification:** Internal — SOC 2 Evidence Artifact
**Control Reference:** S3.5 / CC4.2 — Backup restore testing
**Evidence Folder:** `docs/08-internal/soc2-evidence/s3/`
**Template Version:** 1.0

---

## 1. Test Metadata

| Field | Value |
|-------|-------|
| **Test type** | Full database backup restore to isolated instance |
| **Test date** | _[CEO ACTION: enter date, e.g., 2026-03-15]_ |
| **Test start time** | _[CEO ACTION: e.g., 14:00 UTC]_ |
| **Test end time** | _[CEO ACTION: e.g., 15:22 UTC]_ |
| **Total duration** | _[CEO ACTION: calculated from start/end]_ |
| **RTO target** | 2 hours |
| **RTO met?** | _[CEO ACTION: Yes / No]_ |
| **Tester / Verifier** | _[CEO ACTION: name + role]_ |
| **Report status** | _[CEO ACTION: COMPLETE — PASS / COMPLETE — FAIL / IN PROGRESS]_ |

---

## 2. Backup Source

| Field | Value |
|-------|-------|
| **Provider** | Render (managed PostgreSQL) |
| **Instance name** | _[CEO ACTION: e.g., `paciolus-prod-db`]_ |
| **Backup timestamp selected** | _[CEO ACTION: e.g., 2026-03-14 03:00 UTC (daily snapshot)]_ |
| **Backup age at test time** | _[CEO ACTION: e.g., ~11 hours]_ |
| **Backup type** | Daily automated snapshot (Render managed backup) |
| **Backup encryption** | AES-256 at rest (provider-managed) |
| **Backup ID / reference** | _[CEO ACTION: Render backup ID from dashboard]_ |

---

## 3. Restore Target

| Field | Value |
|-------|-------|
| **Environment** | Isolated test instance (NOT production) |
| **Provider** | _[CEO ACTION: e.g., Render free-tier test instance / local Docker PostgreSQL]_ |
| **Instance name** | _[CEO ACTION: e.g., `paciolus-dr-test-2026q1`]_ |
| **PostgreSQL version** | _[CEO ACTION: match production version]_ |
| **Region** | _[CEO ACTION: e.g., US-East]_ |
| **Isolation confirmed?** | _[CEO ACTION: Yes — test instance has no inbound connections from production]_ |

---

## 4. Steps Executed

> Complete the steps below as you execute them. Check each box as completed.

### 4.1 Pre-Restore Setup

- [ ] **Step 1:** Provision isolated PostgreSQL test instance (Render dashboard or local Docker)
  - Command/action: _[CEO ACTION: document the command or console action]_
  - Result: _[CEO ACTION: e.g., "Instance `paciolus-dr-test-2026q1` running at `postgres://...`"]_

- [ ] **Step 2:** Note production row counts for comparison (run against production before restore)
  ```sql
  SELECT 'users' AS table_name, COUNT(*) FROM users WHERE archived_at IS NULL
  UNION ALL SELECT 'clients', COUNT(*) FROM clients WHERE archived_at IS NULL
  UNION ALL SELECT 'engagements', COUNT(*) FROM engagements WHERE archived_at IS NULL
  UNION ALL SELECT 'activity_logs', COUNT(*) FROM activity_logs WHERE archived_at IS NULL
  UNION ALL SELECT 'tool_runs', COUNT(*) FROM tool_runs WHERE archived_at IS NULL;
  ```
  - Production counts (pre-restore baseline):

| Table | Production Row Count | Timestamp |
|-------|---------------------|-----------|
| users | _[CEO ACTION]_ | _[CEO ACTION]_ |
| clients | _[CEO ACTION]_ | _[CEO ACTION]_ |
| engagements | _[CEO ACTION]_ | _[CEO ACTION]_ |
| activity_logs | _[CEO ACTION]_ | _[CEO ACTION]_ |
| tool_runs | _[CEO ACTION]_ | _[CEO ACTION]_ |

### 4.2 Restore Execution

- [ ] **Step 3:** Select backup snapshot in Render dashboard
  - Backup ID selected: _[CEO ACTION]_
  - Action taken: _[CEO ACTION: e.g., "Clicked 'Restore' on backup `backup_abc123` in Render dashboard → selected test instance as target"]_
  - Restore initiated at: _[CEO ACTION: time]_

- [ ] **Step 4:** Wait for restore to complete
  - Restore completion confirmed at: _[CEO ACTION: time]_
  - Any errors during restore: _[CEO ACTION: None / describe errors if any]_

- [ ] **Step 5:** Verify connection to restored instance
  - Command: `psql $TEST_DATABASE_URL -c "\conninfo"`
  - Result: _[CEO ACTION: e.g., "Connected to `paciolus-dr-test-2026q1` successfully"]_

### 4.3 Schema Verification

- [ ] **Step 6:** Verify Alembic migration version matches production
  ```sql
  SELECT version_num FROM alembic_version;
  ```
  - Result: _[CEO ACTION: version number, e.g., `ecda5f408617`]_
  - Matches production version? _[CEO ACTION: Yes / No — if No, run `alembic upgrade head`]_

- [ ] **Step 7:** If migration version mismatch, run migrations
  - Command: `alembic upgrade head`
  - Result: _[CEO ACTION: N/A if version matched; else migration output]_

### 4.4 Data Integrity Verification

- [ ] **Step 8:** Run row count verification on restored instance
  ```sql
  SELECT 'users' AS table_name, COUNT(*) FROM users WHERE archived_at IS NULL
  UNION ALL SELECT 'clients', COUNT(*) FROM clients WHERE archived_at IS NULL
  UNION ALL SELECT 'engagements', COUNT(*) FROM engagements WHERE archived_at IS NULL
  UNION ALL SELECT 'activity_logs', COUNT(*) FROM activity_logs WHERE archived_at IS NULL
  UNION ALL SELECT 'tool_runs', COUNT(*) FROM tool_runs WHERE archived_at IS NULL;
  ```

| Table | Production Count | Restored Count | Delta | Within RPO Window? |
|-------|-----------------|----------------|-------|-------------------|
| users | _[from Step 2]_ | _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION: Yes/No]_ |
| clients | _[from Step 2]_ | _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION: Yes/No]_ |
| engagements | _[from Step 2]_ | _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION: Yes/No]_ |
| activity_logs | _[from Step 2]_ | _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION: Yes/No]_ |
| tool_runs | _[from Step 2]_ | _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION: Yes/No]_ |

> **Expected delta:** Records created in the window between backup timestamp and test time will not appear in the restored instance. This is expected behavior and not a failure condition, provided the delta is within the RPO window (≤1 hour).

- [ ] **Step 9:** Zero-Storage compliance verification (confirm no financial data in backup)
  ```sql
  -- These tables should NOT exist in the restored database
  SELECT table_name FROM information_schema.tables
  WHERE table_schema = 'public'
  AND table_name IN ('trial_balances', 'financial_data', 'uploaded_files', 'tb_entries');
  ```
  - Result: _[CEO ACTION: "0 rows returned — no financial data tables found" or describe what was found]_
  - Zero-Storage compliance confirmed? _[CEO ACTION: Yes / No]_

### 4.5 Application Smoke Test (Optional but Recommended)

- [ ] **Step 10:** Point a local backend instance at the test DB and verify health endpoint
  - Command: `DATABASE_URL=$TEST_DATABASE_URL uvicorn main:app --port 8001`
  - `GET /health` response: _[CEO ACTION: e.g., `{"status": "healthy", "db": "connected"}`]_
  - Auth smoke test (login + token refresh): _[CEO ACTION: Pass / Fail / Skipped]_

### 4.6 Teardown

- [ ] **Step 11:** Tear down isolated test instance
  - Action: _[CEO ACTION: deleted test instance from Render dashboard / stopped Docker container]_
  - Confirmed deleted at: _[CEO ACTION: time]_
  - Verified no residual data accessible: _[CEO ACTION: Yes]_

---

## 5. Duration Measurement

| Milestone | Time | Elapsed |
|-----------|------|---------|
| Test started | _[CEO ACTION]_ | 0 min |
| Restore initiated | _[CEO ACTION]_ | _[CEO ACTION]_ |
| Restore complete (DB usable) | _[CEO ACTION]_ | _[CEO ACTION]_ |
| Data integrity verified | _[CEO ACTION]_ | _[CEO ACTION]_ |
| Test complete | _[CEO ACTION]_ | _[CEO ACTION]_ |

**Total elapsed time:** _[CEO ACTION]_
**RTO target (2 hours):** _[CEO ACTION: MET / NOT MET]_

---

## 6. Issues Encountered

_[CEO ACTION: List any issues encountered during the test, or write "None"]_

| Issue | Steps Affected | Resolution | Impact on Test |
|-------|---------------|------------|----------------|
| _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION]_ |

---

## 7. Pass / Fail Determination

| Criterion | Target | Result | Pass/Fail |
|-----------|--------|--------|-----------|
| Restore completed without errors | No errors | _[CEO ACTION]_ | _[CEO ACTION]_ |
| RTO met | ≤ 2 hours | _[CEO ACTION]_ | _[CEO ACTION]_ |
| Row counts within RPO window | Delta ≤ 1 hour of data | _[CEO ACTION]_ | _[CEO ACTION]_ |
| Alembic version correct | Matches production | _[CEO ACTION]_ | _[CEO ACTION]_ |
| Zero-Storage compliance | No financial data tables | _[CEO ACTION]_ | _[CEO ACTION]_ |
| Test instance fully torn down | No residual access | _[CEO ACTION]_ | _[CEO ACTION]_ |

**Overall result:** _[CEO ACTION: PASS / FAIL]_

---

## 8. Remediation Actions (If Applicable)

_[CEO ACTION: If any criterion failed, document the remediation action and target date, or write "N/A"]_

| Criterion Failed | Remediation Action | Owner | Target Date |
|-----------------|-------------------|-------|-------------|
| _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION]_ |

---

## 9. Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| **Tester** | _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION]_ |
| **CTO (reviewer)** | _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION]_ |

---

## 10. Next Test

| Field | Value |
|-------|-------|
| **Next scheduled restore test** | _[CEO ACTION: e.g., 2026-09-30 (semi-annual)]_ |
| **Calendar reminder set?** | _[CEO ACTION: Yes / No]_ |
| **Reminder recurrence** | Semi-annual (Jun 30 + Dec 31) |

---

## Related Documents

| Document | Relationship |
|----------|-------------|
| [BCP/DR Plan](../../04-compliance/BUSINESS_CONTINUITY_DISASTER_RECOVERY.md) | §7.2 defines the test procedure this report follows |
| [Incident Response Plan](../../04-compliance/INCIDENT_RESPONSE_PLAN.md) | Referenced for P0 escalation during restore failures |
| [Zero-Storage Architecture](../../04-compliance/ZERO_STORAGE_ARCHITECTURE.md) | Confirms financial data scope exclusion (Step 9) |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
*Evidence artifact for SOC 2 Type II — Control S3.5 / CC4.2*
