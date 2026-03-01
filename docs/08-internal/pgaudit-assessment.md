# PostgreSQL pgaudit Extension Assessment

> **Sprint:** 460 | **Control:** CC6.8 / CC7.4 | **Date:** 2026-03-01

## Assessment

### pgaudit Availability on Render

Render managed PostgreSQL instances do **not** support the `pgaudit` extension. Render provides a curated set of extensions, and `pgaudit` is not among them. This was verified against Render's documentation as of 2026-03-01.

**Blocker:** Cannot execute `CREATE EXTENSION pgaudit;` on Render-managed instances.

### Compensating Controls

In lieu of database-level audit logging via pgaudit, the following application-layer controls provide equivalent evidence:

| Control | Implementation | Sprint |
|---------|----------------|--------|
| **Application audit log** | `ActivityLog` model with `SoftDeleteMixin` — all records soft-deleted, never physically removed | Phase XLVI (345-349) |
| **ORM deletion guard** | `before_flush` listener blocks `db.delete()` on 5 protected tables; raises `AuditImmutabilityError` | Phase XLVI |
| **Cryptographic chain** | HMAC-SHA512 hash chaining on ActivityLog records; tamper detection via `GET /audit/chain-verify` | Sprint 461 |
| **Structured logging** | JSON-formatted request logs with request ID correlation; sanitized (no PII) | Phase XXVIII |
| **Request ID tracing** | Every HTTP request gets a UUID; appears in all log entries for that request | Phase XXVIII |

### SOC 2 Examiner Talking Points

1. **CC6.8 (Access Monitoring):** Application-level audit logging captures all data-modifying operations. The `ActivityLog` table stores aggregate metadata for every trial balance analysis. All mutations go through the ORM layer, which enforces soft-delete immutability.

2. **CC7.4 (Tamper Evidence):** Cryptographic hash chaining (Sprint 461) provides forward-integrity guarantees. Any retroactive modification of an audit record breaks the chain and is detectable via the verification endpoint.

3. **Why pgaudit is not critical:** Paciolus operates a Zero-Storage architecture — no client financial data is persisted to the database. The database stores only user accounts, subscription metadata, and aggregate audit statistics. The attack surface for database-level tampering is limited to these non-financial records.

### Recommendation

- **Current:** Accept compensating controls as sufficient for SOC 2 Type II.
- **Future:** If Paciolus migrates to self-managed PostgreSQL (e.g., AWS RDS), enable pgaudit at that time. The configuration is documented below for future reference.

### Future pgaudit Configuration (for self-managed PostgreSQL)

```sql
-- Enable extension
CREATE EXTENSION pgaudit;

-- Configure logging scope
ALTER SYSTEM SET pgaudit.log = 'ddl, role, write';
ALTER SYSTEM SET pgaudit.log_catalog = off;
ALTER SYSTEM SET pgaudit.log_relation = on;
ALTER SYSTEM SET pgaudit.log_statement_once = on;
SELECT pg_reload_conf();

-- Verify
SHOW pgaudit.log;
```

**Sensitive tables to scope (when available):**
- `users` — account modifications
- `subscriptions` — billing changes
- `clients` — client metadata
- `engagements` — engagement lifecycle
- `activity_logs` — audit trail (meta-audit)
- `tool_runs` — tool execution records
- `diagnostic_summaries` — diagnostic metadata

### Evidence

- This assessment document serves as evidence of the control gap evaluation
- Compensating controls are documented with sprint references for traceability
- File to: `docs/08-internal/soc2-evidence/cc6/pgaudit-assessment-202603.md`

---

*Sprint 460 — CC6.8 / CC7.4 assessment complete*
