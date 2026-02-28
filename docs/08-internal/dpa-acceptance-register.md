# DPA Acceptance Register

**Version:** 1.0
**Document Classification:** Internal
**Owner:** CISO / Legal
**Effective Date:** 2026-02-27
**Last Updated:** 2026-02-27
**Controls:** PI1.3 — Data Processing Agreement execution evidence; C2.1 — Customer data commitments

---

## Purpose

This register is the authoritative record of Data Processing Addendum (DPA) acceptance by Paciolus business customers. SOC 2 Type II examiners will review this register to verify that enterprise customers have executed a DPA before processing their data.

**DPA Document:** `docs/04-compliance/DATA_PROCESSING_ADDENDUM.md` (v1.0, effective 2026-02-27)

---

## Acceptance Methods

| Method | Implementation | Evidence |
|--------|---------------|----------|
| **In-product checkout** (primary) | Checkbox "I accept the Data Processing Addendum" on Team/Organisation checkout page. Acceptance timestamp recorded in `subscriptions.dpa_accepted_at`, version in `subscriptions.dpa_version`. | Database record; visible in billing settings page |
| **Manual** (fallback for customers onboarded before Sprint 459) | Email DPA PDF to customer for wet or e-signature, receive signed copy | Signed PDF stored in `docs/08-internal/customer-dpa-archive/` |

---

## Database Source of Truth

Programmatic acceptances are stored in the `subscriptions` table:

```sql
SELECT
    u.email,
    u.id          AS user_id,
    s.tier,
    s.dpa_accepted_at,
    s.dpa_version,
    s.created_at  AS subscription_created_at
FROM subscriptions s
JOIN users u ON u.id = s.user_id
WHERE s.dpa_accepted_at IS NOT NULL
ORDER BY s.dpa_accepted_at;
```

Run this query quarterly as part of the access review to generate the acceptance roster.

---

## Manual Acceptance Log

Record manual DPA executions here (customers onboarded before Sprint 459 or enterprise customers who require a countersigned PDF).

| Customer Account | User ID | Acceptance Date | DPA Version | Method | Stored Location |
|-----------------|---------|-----------------|-------------|--------|----------------|
| _(none yet)_ | — | — | — | — | — |

---

## DPA Version History

| Version | Effective Date | Key Changes |
|---------|---------------|-------------|
| 1.0 | 2026-02-27 | Initial DPA — GDPR Art. 28, controller/processor roles, SCCs, audit rights |

---

## Quarterly Review Checklist

As part of the quarterly access review (`docs/08-internal/access-review-YYYY-QN.md`), the CISO/Legal owner must:

- [ ] Run the database query above to generate the acceptance roster
- [ ] Verify all active Team/Organisation subscriptions have `dpa_accepted_at IS NOT NULL`
- [ ] If gaps found: follow up with affected customers (email DPA for manual execution)
- [ ] File query output as `docs/08-internal/soc2-evidence/pi1/dpa-roster-YYYYQN.txt`
- [ ] Update the Manual Acceptance Log above for any manual executions this quarter

---

## Customer DPA Archive (Manual Executions)

Signed PDF copies of manually executed DPAs are stored in `docs/08-internal/customer-dpa-archive/`.

File naming convention: `dpa-v{VERSION}-{customer-slug}-{YYYY-MM-DD}.pdf`

Example: `dpa-v1.0-acme-corp-2026-03-15.pdf`

---

## Version History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-27 | Engineering | Initial register — Sprint 459 / PI1.3 / C2.1 |

---

**Document Owner:** CISO / Legal
**Version:** 1.0 — 2026-02-27
