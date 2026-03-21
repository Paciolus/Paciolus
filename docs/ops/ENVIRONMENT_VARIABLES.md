# Environment Variable Inventory

**Document Classification:** Internal (Operations)
**Version:** 1.0
**Last Updated:** March 20, 2026
**Owner:** Chief Technology Officer
**Review Cycle:** Quarterly (or when environment variables are added/removed)
**Created by:** AUDIT-10 remediation

---

## Purpose

This document is the authoritative inventory of all environment variables required
to operate Paciolus in production. It serves two critical functions:

1. **Disaster recovery:** During a restore, the responder must know every variable
   that needs to be set, where its value is stored, and who can retrieve it.
2. **Onboarding:** New operators can configure a complete environment from this
   single reference.

---

## 1. Secret-Class Variables

These variables contain credentials, keys, or connection strings that must **never**
be committed to version control. They must be stored in a durable secret manager
and rotated on the schedule noted below.

| Variable | Description | Authoritative Storage | Rotation Owner | Rotation Cadence |
|---|---|---|---|---|
| `JWT_SECRET_KEY` | Signs JWT access tokens (HS256, minimum 32 characters) | [DOCUMENT STORAGE] | [ASSIGN] | Every 90 days |
| `CSRF_SECRET_KEY` | HMAC CSRF token signing (must differ from JWT_SECRET_KEY in production) | [DOCUMENT STORAGE] | [ASSIGN] | Every 90 days |
| `DATABASE_URL` | Primary PostgreSQL connection string (see provider dashboard for format) | [DOCUMENT STORAGE] | [ASSIGN] | On credential rotation or instance change |
| `STRIPE_SECRET_KEY` | Stripe API secret key (starts with `sk_live` or `sk_test`) | [DOCUMENT STORAGE] | [ASSIGN] | Per Stripe security policy |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signature verification (starts with `whsec`) — **must be re-registered if the backend endpoint URL changes** | [DOCUMENT STORAGE] | [ASSIGN] | On endpoint URL change |
| `STRIPE_PUBLISHABLE_KEY` | Stripe frontend publishable key (starts with `pk_live` or `pk_test`) | [DOCUMENT STORAGE] | [ASSIGN] | Per Stripe security policy |
| `STRIPE_COUPON_MONTHLY_20` | Stripe coupon ID for 20% off first 3 months promotional pricing | [DOCUMENT STORAGE] | [ASSIGN] | As promotions change |
| `STRIPE_COUPON_ANNUAL_10` | Stripe coupon ID for 10% off first annual invoice promotional pricing | [DOCUMENT STORAGE] | [ASSIGN] | As promotions change |
| `SENDGRID_API_KEY` | SendGrid API key for transactional email delivery | [DOCUMENT STORAGE] | [ASSIGN] | Annually or on suspected compromise |
| `SENTRY_DSN` | Backend Sentry error reporting data source name | [DOCUMENT STORAGE] | [ASSIGN] | Rarely (tied to Sentry project) |
| `ANALYTICS_WRITE_KEY` | Analytics pipeline write key for billing/pricing telemetry | [DOCUMENT STORAGE] | [ASSIGN] | Annually |
| `SENTRY_AUTH_TOKEN` | Sentry auth token for frontend source map uploads (Vercel build-time) | [DOCUMENT STORAGE] | [ASSIGN] | Annually |

### Stripe Price IDs (Secret-Class)

These are Stripe-specific identifiers. They are not cryptographic secrets but are
operationally sensitive and should not be public.

| Variable | Description | Authoritative Storage | Rotation Owner |
|---|---|---|---|
| `STRIPE_PRICE_SOLO_MONTHLY` | Stripe price ID — Solo tier monthly | [DOCUMENT STORAGE] | [ASSIGN] |
| `STRIPE_PRICE_SOLO_ANNUAL` | Stripe price ID — Solo tier annual | [DOCUMENT STORAGE] | [ASSIGN] |
| `STRIPE_PRICE_PROFESSIONAL_MONTHLY` | Stripe price ID — Professional tier monthly | [DOCUMENT STORAGE] | [ASSIGN] |
| `STRIPE_PRICE_PROFESSIONAL_ANNUAL` | Stripe price ID — Professional tier annual | [DOCUMENT STORAGE] | [ASSIGN] |
| `STRIPE_PRICE_ENTERPRISE_MONTHLY` | Stripe price ID — Enterprise tier monthly | [DOCUMENT STORAGE] | [ASSIGN] |
| `STRIPE_PRICE_ENTERPRISE_ANNUAL` | Stripe price ID — Enterprise tier annual | [DOCUMENT STORAGE] | [ASSIGN] |
| `STRIPE_SEAT_PRICE_PRO_MONTHLY` | Professional tier seat add-on price ID (monthly) | [DOCUMENT STORAGE] | [ASSIGN] |
| `STRIPE_SEAT_PRICE_PRO_ANNUAL` | Professional tier seat add-on price ID (annual) | [DOCUMENT STORAGE] | [ASSIGN] |
| `STRIPE_SEAT_PRICE_ENT_MONTHLY` | Enterprise tier seat add-on price ID (monthly) | [DOCUMENT STORAGE] | [ASSIGN] |
| `STRIPE_SEAT_PRICE_ENT_ANNUAL` | Enterprise tier seat add-on price ID (annual) | [DOCUMENT STORAGE] | [ASSIGN] |

### Cloud Provider Credentials (if applicable)

The `secrets_manager.py` module supports four backends via the `SECRETS_PROVIDER`
variable: `env` (default), `aws`, `gcp`, `azure`. Only one is authoritative for
production.

| Variable | Description | When Required |
|---|---|---|
| `SECRETS_PROVIDER` | Active secrets backend: `env`, `aws`, `gcp`, or `azure` (default: `env`) | Always |
| `GCP_PROJECT_ID` | Google Cloud project ID | Only if `SECRETS_PROVIDER=gcp` |
| `AZURE_VAULT_URL` | Azure Key Vault URL | Only if `SECRETS_PROVIDER=azure` |
| AWS credentials | Standard AWS SDK credential chain | Only if `SECRETS_PROVIDER=aws` |

> **[DOCUMENT WHICH BACKEND IS AUTHORITATIVE FOR PRODUCTION]** — If using `env`
> (environment variables on Render/Vercel), then Render and Vercel are the de facto
> secret managers. Document this explicitly so a DR responder knows where to find
> values during recovery.

---

## 2. Configuration-Class Variables

These are non-sensitive configuration values. They can live in a repo-tracked
`.env.example` file and do not require a secret manager.

### Core Application

| Variable | Default | Description |
|---|---|---|
| `ENV_MODE` | `development` | Environment mode: `development`, `staging`, or `production` |
| `API_HOST` | *(required)* | Host address for API server (`0.0.0.0` for all interfaces) |
| `API_PORT` | *(required)* | Port for API server (typically `8000`, or `${PORT}` on Render) |
| `CORS_ORIGINS` | *(required)* | Comma-separated list of allowed frontend origins |
| `DEBUG` | `false` | Enable debug mode (detailed error messages, never `true` in production) |
| `FRONTEND_URL` | *(not set)* | Frontend URL used in email templates and redirects |

### Authentication

| Variable | Default | Description |
|---|---|---|
| `JWT_EXPIRATION_MINUTES` | `30` | JWT access token expiration time in minutes |
| `REFRESH_TOKEN_EXPIRATION_DAYS` | `7` | Refresh token expiration time in days |
| `TRUSTED_PROXY_IPS` | *(empty)* | Comma-separated list of trusted reverse proxy IPs for X-Forwarded-For |

### Database Connection Pool

| Variable | Default | Description |
|---|---|---|
| `DB_POOL_SIZE` | `10` | Max persistent connections per worker (PostgreSQL only) |
| `DB_MAX_OVERFLOW` | `20` | Burst connections above pool_size (PostgreSQL only) |
| `DB_POOL_RECYCLE` | `3600` | Recycle connections after N seconds to avoid stale TCP (PostgreSQL only) |

### Feature Flags

| Variable | Default | Description |
|---|---|---|
| `ENTITLEMENT_ENFORCEMENT` | `hard` | Tier-based feature gating: `hard` (block access) or `soft` (log only) |
| `SEAT_ENFORCEMENT_MODE` | `hard` | Seat limit enforcement: `hard` (block) or `soft` (log only) |
| `FORMAT_ODS_ENABLED` | `false` | Enable ODS (LibreOffice Calc) file format support |
| `FORMAT_PDF_ENABLED` | `true` | Enable PDF file format support |
| `FORMAT_IIF_ENABLED` | `true` | Enable IIF (Intuit Interchange Format) file format support |
| `FORMAT_OFX_ENABLED` | `true` | Enable OFX (Open Financial Exchange) file format support |
| `FORMAT_QBO_ENABLED` | `true` | Enable QBO (QuickBooks Online) file format support |

### Monitoring & Observability

| Variable | Default | Description |
|---|---|---|
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Fraction of transactions sent to Sentry (0.0–1.0) |
| `REDACT_LOG_TRACEBACKS` | `true` | Redact full tracebacks from logs in production |

### Cleanup Scheduler

| Variable | Default | Description |
|---|---|---|
| `CLEANUP_SCHEDULER_ENABLED` | `true` | Master switch for background cleanup scheduler |
| `CLEANUP_REFRESH_TOKEN_INTERVAL_MINUTES` | `60` | Interval for expired refresh token cleanup (minutes) |
| `CLEANUP_VERIFICATION_TOKEN_INTERVAL_MINUTES` | `60` | Interval for expired verification token cleanup (minutes) |
| `CLEANUP_TOOL_SESSION_INTERVAL_MINUTES` | `30` | Interval for expired tool session cleanup (minutes) |
| `CLEANUP_RETENTION_INTERVAL_HOURS` | `24` | Interval for activity log and diagnostic summary retention cleanup (hours) |

### Email

| Variable | Default | Description |
|---|---|---|
| `SENDGRID_FROM_EMAIL` | `noreply@paciolus.com` | From email address for SendGrid messages |
| `SENDGRID_FROM_NAME` | `Paciolus` | From name for SendGrid messages |
| `CONTACT_EMAIL` | `contact@paciolus.com` | Destination email for contact form submissions |

### Frontend (NEXT_PUBLIC_)

All `NEXT_PUBLIC_` variables are embedded at build time and exposed to the browser.

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_SENTRY_DSN` | *(empty)* | Sentry DSN for client-side error tracking |
| `NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Sentry performance sampling rate |
| `NEXT_PUBLIC_ANALYTICS_WRITE_KEY` | *(empty)* | Analytics pipeline write key |
| `NEXT_TELEMETRY_DISABLED` | *(empty)* | Set to `1` to disable Next.js telemetry |

### Gunicorn / Docker

| Variable | Default | Description |
|---|---|---|
| `WEB_CONCURRENCY` | `(2 * CPU) + 1` | Gunicorn worker count |
| `GUNICORN_TIMEOUT` | `120` | Gunicorn worker timeout in seconds |
| `GUNICORN_GRACEFUL_TIMEOUT` | `30` | Graceful shutdown timeout in seconds |
| `GUNICORN_KEEP_ALIVE` | `5` | Keep-alive timeout in seconds |
| `GUNICORN_MAX_REQUESTS` | `1000` | Worker recycling after N requests (0 to disable) |

### Rate Limiting (Dynamic)

Rate limits can be overridden per tier and category via environment variables
following the pattern `RATE_LIMIT_{TIER}_{CATEGORY}` (e.g.,
`RATE_LIMIT_PROFESSIONAL_AUDIT=50/minute`). See `backend/config.py` for the
default rate limit matrix.

---

## 3. GitHub Actions Secrets

These secrets are used exclusively in CI/CD workflows and are **not** required for
application runtime. They are stored in GitHub repository settings (Settings →
Secrets and variables → Actions).

| Secret | Workflow | Description |
|---|---|---|
| `RENDER_API_KEY` | `dr-test-monthly.yml`, `backup-integrity-check.yml` | Render personal API token |
| `RENDER_POSTGRES_ID` | `dr-test-monthly.yml`, `backup-integrity-check.yml` | PostgreSQL service ID (from Render dashboard URL) |
| `DATABASE_URL_READONLY` | `dr-test-monthly.yml` | Optional read-only DB connection string for liveness probe |
| `RESTORE_TEST_BACKUP_URL` | `dr-test-monthly.yml` (restore-validation job) | URL to downloadable backup artifact for restore testing. Updated when a new backup is exported from Render. The backup file should be uploaded to a secure, access-controlled location (e.g., a private S3 bucket or Render object storage) and the URL placed here. |

---

## 4. Break-Glass / Skeleton Key Recovery

If the primary secret manager account credentials are lost, the following
out-of-band recovery path applies:

- **Account ownership:** [DOCUMENT WHO HOLDS THE MASTER SECRET MANAGER ACCOUNT]
- **MFA escrow:** [DOCUMENT WHERE BACKUP MFA CODES ARE STORED, e.g., printed and
  locked, secondary admin account, etc.]
- **Backup secret admin:** [DOCUMENT WHO HAS SECONDARY ADMIN ACCESS]
- **Last resort:** [DOCUMENT PROVIDER-LEVEL ACCOUNT RECOVERY PROCESS]

This section must be reviewed and updated any time account ownership changes.
Last reviewed: [DATE]

---

## Related Documents

| Document | Relationship |
|----------|-------------|
| [BCP/DR Plan](../04-compliance/BUSINESS_CONTINUITY_DISASTER_RECOVERY.md) | Recovery procedure references this variable inventory (Step 4) |
| [Deployment Architecture](../02-technical/DEPLOYMENT_ARCHITECTURE.md) | Section 3 covers environment configuration |
| [Security Policy](../04-compliance/SECURITY_POLICY.md) | Secrets management requirements |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
