# Data Deletion Procedure

**Version:** 1.0
**Document Classification:** Internal
**Owner:** privacy@paciolus.com
**Effective Date:** 2026-02-27
**Last Updated:** 2026-02-27
**Next Review:** 2026-08-27
**Controls:** PI4.3 / CC7.4 — Data subject rights (deletion) / GDPR Art. 17 / CCPA §1798.105

---

## 1. Purpose and Scope

This procedure defines how Paciolus fulfills data deletion requests from data subjects. It covers both **self-service deletions** (initiated through the product) and **email-based deletion requests** processed manually by the privacy team.

All deletion requests are fulfilled within the SLA defined in §3 and logged for audit purposes.

---

## 2. Request Intake Methods

### 2.1 Self-Service (Immediate)

Users may delete their own account directly within the product:

1. Navigate to **Settings → Account → Delete Account**
2. Confirm deletion in the dialog box
3. The system executes an automated deletion sequence (Steps 3–8 below) in a single database transaction
4. A confirmation email is sent automatically

Self-service deletions are **immediate** — no manual processing is required.

### 2.2 Email-Based Request

Data subjects may submit deletion requests by email:

- **To:** privacy@paciolus.com
- **Subject:** "Account Deletion Request"
- **Include:** Email address associated with the account

Email-based requests are subject to the 30-day SLA and require manual identity verification (Step 2).

---

## 3. Service Level Agreement

| Request Method | Target Completion | Maximum Completion |
|----------------|-------------------|--------------------|
| Self-service (in-product) | Immediate (< 60 seconds) | N/A — automated |
| Email-based request | 5 business days | 30 days from receipt |

**Legal basis:** GDPR Article 17 requires fulfillment "without undue delay" and no later than one month from receipt. CCPA §1798.105 requires fulfillment within 45 days.

---

## 4. Deletion Procedure — Email-Based Requests

### Step 1: Receive and Log Request

On receipt of a deletion request email:

1. Create a new file in `docs/08-internal/deletion-requests/` named `deletion-YYYYMMDD-[ticket#].md` (see §7 for template)
2. Record in the tracker:
   - Date and time request received (UTC)
   - Requester's stated email address
   - Request method (email)
   - Assigned processor (your name/initials)
   - 30-day deadline (receipt date + 30 days)

**Note:** Do not store the full email body in the tracker — record only the email address (pseudonymised) and timestamp. PII minimization applies.

### Step 2: Verify Requester Identity

Before executing deletion:

1. Reply to the requester's email:
   > *"We have received your account deletion request. To verify your identity before proceeding, please confirm: (1) the email address associated with your account, and (2) the approximate date you registered."*
2. Cross-reference the response against the `users` table record
3. If identity cannot be confirmed within 5 business days: send a follow-up. If no response within 15 days, log as "identity unverified — request closed" and close the tracker entry

**Do not proceed with deletion until identity is verified.**

### Step 3: Execute User Account Soft-Delete

Execute in the PostgreSQL production database (use `psql` via Render dashboard or a secured admin connection):

```sql
-- Verify the account exists and is active
SELECT id, email, created_at, is_active
FROM users
WHERE email = '<requester_email>'
  AND archived_at IS NULL;
```

Record the `user_id` returned. Then execute the soft-delete:

```sql
-- Soft-delete the user account
UPDATE users
SET
  archived_at  = NOW() AT TIME ZONE 'UTC',
  archived_by  = <admin_user_id>,   -- your internal admin user ID
  archive_reason = 'user_deletion_request'
WHERE email = '<requester_email>'
  AND archived_at IS NULL;
```

### Step 4: Soft-Delete All Associated Records

Execute all of the following in a single transaction or sequentially, replacing `<user_id>` with the value from Step 3:

```sql
BEGIN;

-- 1. Clients
UPDATE clients
SET archived_at = NOW() AT TIME ZONE 'UTC',
    archived_by = <admin_user_id>,
    archive_reason = 'user_deletion_request'
WHERE user_id = <user_id>
  AND archived_at IS NULL;

-- 2. Engagements
UPDATE engagements
SET archived_at = NOW() AT TIME ZONE 'UTC',
    archived_by = <admin_user_id>,
    archive_reason = 'user_deletion_request'
WHERE user_id = <user_id>
  AND archived_at IS NULL;

-- 3. Activity logs
UPDATE activity_logs
SET archived_at = NOW() AT TIME ZONE 'UTC',
    archived_by = <admin_user_id>,
    archive_reason = 'user_deletion_request'
WHERE user_id = <user_id>
  AND archived_at IS NULL;

-- 4. Diagnostic summaries
UPDATE diagnostic_summaries
SET archived_at = NOW() AT TIME ZONE 'UTC',
    archived_by = <admin_user_id>,
    archive_reason = 'user_deletion_request'
WHERE user_id = <user_id>
  AND archived_at IS NULL;

-- 5. Tool runs
UPDATE tool_runs
SET archived_at = NOW() AT TIME ZONE 'UTC',
    archived_by = <admin_user_id>,
    archive_reason = 'user_deletion_request'
WHERE engagement_id IN (
  SELECT id FROM engagements WHERE user_id = <user_id>
)
AND archived_at IS NULL;

-- 6. Follow-up items
UPDATE follow_up_items
SET archived_at = NOW() AT TIME ZONE 'UTC',
    archived_by = <admin_user_id>,
    archive_reason = 'user_deletion_request'
WHERE engagement_id IN (
  SELECT id FROM engagements WHERE user_id = <user_id>
)
AND archived_at IS NULL;

-- 7. Follow-up item comments
UPDATE follow_up_item_comments
SET archived_at = NOW() AT TIME ZONE 'UTC',
    archived_by = <admin_user_id>,
    archive_reason = 'user_deletion_request'
WHERE follow_up_item_id IN (
  SELECT fi.id FROM follow_up_items fi
  JOIN engagements e ON fi.engagement_id = e.id
  WHERE e.user_id = <user_id>
)
AND archived_at IS NULL;

COMMIT;
```

### Step 5: Revoke All Active JWT Refresh Tokens

```sql
-- Revoke all active refresh tokens for this user
UPDATE refresh_tokens
SET revoked_at = NOW() AT TIME ZONE 'UTC'
WHERE user_id = <user_id>
  AND revoked_at IS NULL;
```

This immediately invalidates all active sessions. The in-memory access token will expire within 30 minutes (next silent-refresh attempt will fail with 401).

### Step 6: Invalidate HttpOnly Refresh Cookie

The refresh token cookie (`paciolus_refresh`) is `HttpOnly/Secure/SameSite=Lax` and is invalidated automatically when the token record is revoked in Step 5. The browser cookie will be cleared on the next request to `/auth/refresh` (401 response triggers client-side logout).

No additional action required for the cookie beyond Step 5.

### Step 7: Cancel Billing Subscription (If Active)

Check whether the user has an active subscription:

```sql
SELECT id, tier, status, stripe_subscription_id
FROM subscriptions
WHERE user_id = <user_id>;
```

If `status` is `active` or `trialing` and `stripe_subscription_id` is not null:

1. Log into the **Stripe Dashboard → Customers** → search by customer email
2. Navigate to the active subscription → click **Cancel subscription**
3. Select **Cancel immediately** (not at period end, since this is a deletion request)
4. Under **Payment methods** → remove all saved payment methods
5. Note the Stripe customer ID and cancellation timestamp in the deletion tracker

**Billing records retention:** Stripe transaction and invoice records are retained for **7 years** in Stripe's systems to comply with financial reporting obligations. This data is held by Stripe (our payment processor), not by Paciolus. This exception is disclosed in the Privacy Policy §6.3 and §4.1.

```sql
-- Optionally mark subscription as canceled in our DB
UPDATE subscriptions
SET status = 'canceled',
    cancel_at_period_end = FALSE
WHERE user_id = <user_id>
  AND status NOT IN ('canceled', 'incomplete_expired');
```

### Step 8: Confirm Deletion — Row Count Verification

Run these queries to verify all user-linked active records have been archived:

```sql
-- Each of these should return 0 rows
SELECT 'users' AS tbl, COUNT(*) AS active_rows
  FROM users WHERE id = <user_id> AND archived_at IS NULL
UNION ALL
SELECT 'clients', COUNT(*)
  FROM clients WHERE user_id = <user_id> AND archived_at IS NULL
UNION ALL
SELECT 'engagements', COUNT(*)
  FROM engagements WHERE user_id = <user_id> AND archived_at IS NULL
UNION ALL
SELECT 'activity_logs', COUNT(*)
  FROM activity_logs WHERE user_id = <user_id> AND archived_at IS NULL
UNION ALL
SELECT 'diagnostic_summaries', COUNT(*)
  FROM diagnostic_summaries WHERE user_id = <user_id> AND archived_at IS NULL
UNION ALL
SELECT 'refresh_tokens', COUNT(*)
  FROM refresh_tokens WHERE user_id = <user_id> AND revoked_at IS NULL;
```

**Expected result:** All counts should be `0`. If any row shows `> 0`, investigate and archive those records before proceeding.

Record the verification query output in the deletion tracker.

### Step 9: Send Confirmation Email

Reply to the requester's original email:

> Subject: **Your Paciolus account has been deleted**
>
> Dear [Name],
>
> We have completed the deletion of your Paciolus account and all associated data in response to your request received on [date].
>
> The following data has been deleted:
> - Your user account and login credentials
> - All client records you created
> - All engagement and diagnostic records
> - All activity history
> - All active sessions
>
> **Note on financial records:** If you had an active paid subscription, Stripe (our payment processor) retains invoice and transaction records for 7 years to comply with financial regulations. This data is held by Stripe under their Privacy Policy, not by Paciolus.
>
> If you have any questions, please contact privacy@paciolus.com.
>
> Paciolus Privacy Team

### Step 10: Log Completion

Update the deletion tracker file with:

- Completion date and time (UTC)
- Verification query results (Step 8)
- Stripe action taken (Step 7) — yes/no
- Confirmation email sent — yes/no
- Processor name/initials
- Any exceptions or deviations from this procedure

Move the tracker entry status to `COMPLETED`.

---

## 5. Retention Exceptions

The following data is **not deleted** in response to a deletion request due to legal retention obligations:

| Data | Retention Period | Legal Basis |
|------|-----------------|-------------|
| Stripe billing records (invoices, charges, refunds) | 7 years | Tax and financial reporting regulations |
| Soft-archived audit records (activity logs, tool runs) | Up to 7 years from archival | Legal hold / compliance investigations |
| Anonymized aggregate analytics | Indefinite | Cannot be re-identified; not personal data |

All retained data is disclosed to data subjects in the deletion confirmation email (Step 9) and in Privacy Policy §6.3.

---

## 6. Requestor Rights to Object or Appeal

If a data subject believes their deletion request was not fulfilled completely:

1. They may email privacy@paciolus.com with subject "Deletion Dispute"
2. Paciolus will investigate and respond within **5 business days**
3. GDPR data subjects may lodge a complaint with their national supervisory authority (see Privacy Policy §12.4)

---

## 7. Deletion Request Tracker Template

Each request gets one file: `docs/08-internal/deletion-requests/deletion-YYYYMMDD-[#].md`

```markdown
# Deletion Request — [YYYYMMDD-###]

**Status:** OPEN | VERIFYING | EXECUTING | COMPLETED | CLOSED-UNVERIFIED
**Received:** YYYY-MM-DD HH:MM UTC
**Requester:** [email domain only, e.g., @example.com — do not store full email in version control]
**Account Email Hash:** [SHA-256 of requester email, for correlation without storing PII]
**Method:** Email | Self-service
**30-day deadline:** YYYY-MM-DD
**Assigned:** [initials]

## Verification
- [ ] Identity verification email sent: YYYY-MM-DD
- [ ] Identity confirmed: YYYY-MM-DD
- [ ] User ID resolved: ___

## Execution
- [ ] Step 3 — User soft-deleted: YYYY-MM-DD HH:MM
- [ ] Step 4 — Associated records soft-deleted: YYYY-MM-DD HH:MM
- [ ] Step 5 — Refresh tokens revoked: YYYY-MM-DD HH:MM
- [ ] Step 7 — Stripe subscription canceled (if applicable): N/A | YYYY-MM-DD
- [ ] Step 8 — Row count verification: all zeros: Yes | No (explain below)

## Verification Query Output
[Paste Step 8 query output here]

## Confirmation
- [ ] Confirmation email sent: YYYY-MM-DD
- [ ] Completed by: [initials]
- [ ] Completion logged: YYYY-MM-DD

## Notes
[Any deviations, exceptions, or escalations]
```

---

## 8. Evidence Retention

Completed deletion request tracker files are retained for **3 years** from completion date, then deleted.

Evidence copies are filed to `docs/08-internal/soc2-evidence/pi4/` for SOC 2 audit purposes:

```
docs/08-internal/soc2-evidence/pi4/
  deletion-summary-YYYY.md         ← Annual summary log (count + dates, no PII)
  deletion-YYYYMMDD-NNN.md         ← Individual request files (sanitized of PII)
```

---

## 9. Related Documents

- [Privacy Policy §6.3](../04-compliance/PRIVACY_POLICY.md#63-deletion-gdpr-article-17-ccpa-17981050) — public-facing deletion rights statement
- [AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md](../04-compliance/AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md) — soft-delete archival model
- [ZERO_STORAGE_ARCHITECTURE.md](../04-compliance/ZERO_STORAGE_ARCHITECTURE.md) — why financial data is not subject to deletion
- [DATA_PROCESSING_ADDENDUM.md](../04-compliance/DATA_PROCESSING_ADDENDUM.md) — processor data handling obligations

---

**Document Owner:** privacy@paciolus.com
**Version:** 1.0 — 2026-02-27
