# Secrets Vault Secondary Backup & Recovery Procedure

**Version:** 1.0
**Document Classification:** Internal — Restricted
**Owner:** CEO / CISO
**Effective Date:** 2026-02-28
**Last Updated:** 2026-02-28
**Next Review:** 2026-05-28
**Controls:** CC7.3 / BCP — Key management resilience

---

## 1. Purpose

This procedure defines the secondary backup strategy for all application secrets. The goal is to ensure that if the primary secret storage (Render/Vercel environment variables) becomes inaccessible during an incident, all secrets can be recovered without regeneration.

---

## 2. Primary Secret Storage

All production secrets are stored as environment variables in two providers:

| Provider | Secrets Stored | Access |
|----------|---------------|--------|
| **Render** | `SECRET_KEY`, `DATABASE_URL`, `SENTRY_DSN`, JWT config, CSRF config, `SENDGRID_API_KEY`, Prometheus config | Render Dashboard (CEO account) |
| **Vercel** | `NEXT_PUBLIC_API_URL`, `FRONTEND_URL` | Vercel Dashboard (CEO account) |
| **Stripe Dashboard** | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, price IDs, coupon IDs | Stripe Dashboard (CEO account) |
| **GitHub** | `RENDER_API_KEY` (for CI), deploy tokens | GitHub Settings (CEO account) |

---

## 3. Secret Inventory

The following secrets must be included in the secondary backup:

### 3.1 Backend (Render)

| Secret | Purpose | Rotation Cycle |
|--------|---------|---------------|
| `SECRET_KEY` | JWT signing, CSRF HMAC | Annual or on compromise |
| `DATABASE_URL` | PostgreSQL connection string (includes credentials) | On password rotation |
| `STRIPE_SECRET_KEY` | Stripe API authentication | On regeneration |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signature verification | On endpoint recreation |
| `SENDGRID_API_KEY` | Transactional email delivery | Annual |
| `SENTRY_DSN` | Error reporting endpoint | Rarely changes |
| `FRONTEND_URL` | CORS origin, redirect URLs | On domain change |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token lifetime | Rarely changes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token lifetime | Rarely changes |
| `BCRYPT_ROUNDS` | Password hashing cost factor | Rarely changes |

### 3.2 Frontend (Vercel)

| Secret | Purpose | Rotation Cycle |
|--------|---------|---------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | On domain change |

### 3.3 CI/CD (GitHub)

| Secret | Purpose | Rotation Cycle |
|--------|---------|---------------|
| `RENDER_API_KEY` | DR test automation, deploy hooks | Annual |

---

## 4. Secondary Backup Method

**Method:** GPG-encrypted offline file on encrypted storage medium.

### 4.1 Creation Procedure

1. Create a plaintext file containing all secrets from Section 3 in `KEY=VALUE` format
2. Encrypt using GPG with the CEO's personal GPG key:
   ```bash
   gpg --encrypt --recipient CEO_GPG_KEY_ID secrets-backup.txt
   ```
3. Store the resulting `secrets-backup.txt.gpg` on an encrypted USB drive (LUKS or BitLocker)
4. Store the USB drive in a physically secure location (locked drawer/safe)
5. Securely delete the plaintext file:
   ```bash
   shred -vfz -n 5 secrets-backup.txt
   ```

### 4.2 GPG Key Requirements

- The GPG key used for encryption must be the CEO's personal key
- The private key must NOT be stored on the same USB drive as the backup
- The GPG key fingerprint is recorded in `docs/08-internal/gpg-key-registry.md`

---

## 5. Sync Schedule

| Event | Action Required |
|-------|----------------|
| **Any secret is rotated** | Update secondary backup within 24 hours |
| **Every 90 days** | Verify secondary backup is current (compare against primary) |
| **New secret added** | Add to inventory (Section 3) and update backup |
| **Secret decommissioned** | Remove from backup, note in changelog |

### 5.1 90-Day Sync Verification

1. Decrypt the backup file
2. Compare each value against the current Render/Vercel/Stripe dashboards
3. If any value differs, update the backup and re-encrypt
4. Record verification date in the changelog below (Section 8)

---

## 6. Recovery Procedure

**Scenario:** Primary vault (Render/Vercel dashboard) is inaccessible.

### 6.1 Steps

1. Retrieve encrypted USB drive from secure storage
2. Decrypt the backup:
   ```bash
   gpg --decrypt secrets-backup.txt.gpg > secrets-backup.txt
   ```
3. For each secret, set in the recovery environment:
   - If Render access is restored: paste into Render Dashboard > Environment
   - If migrating to new provider: set as environment variables in new host
4. Verify application boots successfully with recovered secrets
5. Securely delete the decrypted plaintext file after recovery
6. Document the recovery event in `docs/08-internal/secrets-recovery-test-YYYYMM.md`

### 6.2 Verification Checklist

After recovery, confirm:

- [ ] Backend starts without errors
- [ ] Database connection succeeds (health endpoint returns 200)
- [ ] JWT authentication works (login + token refresh)
- [ ] CSRF tokens validate
- [ ] Stripe webhooks process (check Stripe Dashboard for delivery status)
- [ ] Email delivery works (trigger a verification email)
- [ ] Sentry receives test error

---

## 7. Recovery Test

A recovery test must be performed semi-annually to validate this procedure.

### 7.1 Test Procedure

1. Decrypt the backup file
2. Spin up a local or staging environment using ONLY the backup values
3. Run the verification checklist (Section 6.2)
4. Record pass/fail for each check
5. Document results in `docs/08-internal/secrets-recovery-test-YYYYMM.md`
6. Store evidence in `docs/08-internal/soc2-evidence/cc7/`

### 7.2 Test Schedule

| Test | Frequency | Next Due |
|------|-----------|----------|
| Recovery test | Semi-annual | 2026-08-28 |
| Sync verification | 90 days | 2026-05-28 |

---

## 8. Changelog

| Date | Action | Performed By |
|------|--------|-------------|
| 2026-02-28 | Procedure created | Engineering |
| _TBD_ | Initial backup created | CEO |
| _TBD_ | First recovery test | CEO |

---

## 9. Upgrade Path

When the team grows beyond 3 people, migrate to a shared secrets manager (1Password Teams or Bitwarden Teams) for:
- Multi-user access with audit trail
- Automated sync capabilities
- Granular access controls per secret

---

*Paciolus — Internal Document — Do Not Distribute*
