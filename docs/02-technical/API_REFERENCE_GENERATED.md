# API Reference (Generated)

> **Generated from route registry on 2026-03-17.**
> This is the canonical API reference. For each router, endpoint signatures are extracted
> from the codebase. Narrative sections marked "Narrative pending" need human-written
> context.

---

## Health
**Prefix:** _(none)_
**Tag:** `health`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| GET | /health | Legacy health probe. Prefer /health/live (liveness) and /health/ready (readiness). |
| GET | /health/live | Liveness probe -- orchestrator should use this for restart decisions. |
| GET | /health/ready | Readiness probe -- load balancer should use this for traffic routing. |
| POST | /waitlist | Add email to waitlist (database-backed with dedup). |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Auth
**Prefix:** _(none)_
**Tag:** `auth`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /auth/register | Register a new user account. |
| POST | /auth/login | Authenticate user and return JWT token. |
| GET | /auth/me | -- no summary -- |
| GET | /auth/csrf | Generate and return a user-bound CSRF token (requires authentication). |
| POST | /auth/verify-email | Verify email address with token. |
| POST | /auth/resend-verification | Resend verification email. |
| GET | /auth/verification-status | Get current user's email verification status. |
| POST | /auth/refresh | Exchange the HttpOnly refresh cookie for a new access + refresh token pair. |
| POST | /auth/logout | Revoke the HttpOnly refresh cookie (logout). |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Users
**Prefix:** _(none)_
**Tag:** `users`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| PUT | /users/me | Update current user's profile (name and/or email). |
| PUT | /users/me/password | Change current user's password. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Activity
**Prefix:** _(none)_
**Tag:** `activity`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /activity/log | Log audit activity. Stores only aggregate metadata, filename is hashed. |
| GET | /activity/history | Get the authenticated user's audit activity history. |
| DELETE | /activity/clear | Clear all activity history for the user (soft-delete: sets archived_at). |
| GET | /dashboard/stats | Get dashboard statistics for workspace header. |
| GET | /audit/chain-verify | Verify the integrity of the audit log hash chain between two record IDs. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Clients
**Prefix:** _(none)_
**Tag:** `clients`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| GET | /clients/industries | Get available industry options. Static data, cached aggressively. |
| GET | /audit/lead-sheets/options | Get available lead sheet options for UI dropdowns. |
| GET | /clients | Get paginated list of clients for the user. |
| POST | /clients | Create a new client for the authenticated user. |
| GET | /clients/{client_id} | Get a specific client by ID. |
| PUT | /clients/{client_id} | Update a client's information. |
| DELETE | /clients/{client_id} | Delete a client. |
| GET | /clients/{client_id}/resolved-framework | Resolve the reporting framework for a client based on its metadata. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Settings
**Prefix:** _(none)_
**Tag:** `settings`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| GET | /settings/practice | Get the current user's practice settings. |
| PUT | /settings/practice | Update the current user's practice settings. |
| GET | /clients/{client_id}/settings | Get settings for a specific client. |
| PUT | /clients/{client_id}/settings | Update settings for a specific client. |
| POST | /settings/materiality/preview | Preview a materiality calculation. |
| GET | /settings/materiality/resolve | Resolve the effective materiality configuration. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Diagnostics
**Prefix:** _(none)_
**Tag:** `diagnostics`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /diagnostics/summary | Save a diagnostic summary for variance tracking. |
| GET | /diagnostics/summary/{client_id}/previous | Get the most recent diagnostic summary for a client. |
| GET | /diagnostics/summary/{client_id}/history | Get diagnostic summary history for a client. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Audit
**Prefix:** _(none)_
**Tag:** `audit`

_Aggregator router. Composes sub-routers: audit_upload, audit_preview, audit_pipeline, audit_flux, audit_diagnostics._

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/inspect-workbook | Inspect an Excel workbook to retrieve sheet metadata. |
| POST | /audit/preview-pdf | Preview PDF table extraction with quality metrics before full parse. |
| POST | /audit/trial-balance | Analyze a trial balance file for balance validation using streaming processing. |
| POST | /audit/flux | Perform a Flux (Period-over-Period) Analysis. |
| POST | /audit/preflight | Run a lightweight data quality pre-flight assessment on a trial balance file. |
| POST | /audit/population-profile | Compute population profile statistics for a trial balance file. |
| POST | /audit/expense-category-analytics | Compute expense category analytical procedures for a trial balance file. |
| POST | /audit/accrual-completeness | Compute accrual completeness estimator for a trial balance file. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Export
**Prefix:** _(none)_
**Tag:** `export`

_Aggregator router. Composes sub-routers: export_diagnostics, export_testing, export_memos._

### Endpoints -- Diagnostics
| Method | Path | Summary |
|--------|------|---------|
| POST | /export/pdf | Generate and stream a PDF audit report. |
| POST | /export/excel | Generate and stream an Excel workpaper. |
| POST | /export/csv/trial-balance | Export trial balance data as CSV. |
| POST | /export/csv/anomalies | Export anomaly list as CSV. |
| POST | /export/leadsheets | Generate Excel Lead Sheets from analysis result. |
| POST | /export/financial-statements | Generate and download financial statements as PDF or Excel. |
| POST | /export/csv/preflight-issues | Export pre-flight quality issues as CSV. |
| POST | /export/csv/population-profile | Export population profile data as CSV. |
| POST | /export/csv/expense-category-analytics | Export expense category analytics data as CSV. |
| POST | /export/csv/accrual-completeness | Export accrual completeness data as CSV. |

### Endpoints -- Testing CSV
| Method | Path | Summary |
|--------|------|---------|
| POST | /export/csv/je-testing | Export flagged journal entries as CSV. |
| POST | /export/csv/ap-testing | Export flagged AP payments as CSV. |
| POST | /export/csv/payroll-testing | Export flagged payroll entries as CSV. |
| POST | /export/csv/revenue-testing | Export flagged revenue entries as CSV. |
| POST | /export/csv/ar-aging | Export flagged AR aging items as CSV. |
| POST | /export/csv/fixed-assets | Export flagged fixed assets as CSV. |
| POST | /export/csv/inventory | Export flagged inventory items as CSV. |
| POST | /export/csv/three-way-match | Export three-way match results as CSV. |
| POST | /export/csv/sampling-selection | Export selected sample items as CSV with blank 'Audited Amount' column. |

### Endpoints -- Memo PDFs
| Method | Path | Summary |
|--------|------|---------|
| POST | /export/je-testing-memo | Generate and download a JE Testing Memo PDF. |
| POST | /export/ap-testing-memo | Generate and download an AP Testing Memo PDF. |
| POST | /export/payroll-testing-memo | Generate and download a Payroll Testing Memo PDF. |
| POST | /export/three-way-match-memo | Generate and download a Three-Way Match Memo PDF. |
| POST | /export/revenue-testing-memo | Generate and download a Revenue Testing Memo PDF. |
| POST | /export/ar-aging-memo | Generate and download an AR Aging Analysis Memo PDF. |
| POST | /export/fixed-asset-memo | Generate and download a Fixed Asset Testing Memo PDF. |
| POST | /export/inventory-memo | Generate and download an Inventory Testing Memo PDF. |
| POST | /export/bank-rec-memo | Generate and download a Bank Reconciliation Memo PDF. |
| POST | /export/multi-period-memo | Generate and download a Multi-Period Comparison Memo PDF. |
| POST | /export/currency-conversion-memo | Generate and download a Currency Conversion Memo PDF. |
| POST | /export/sampling-design-memo | Generate and download a Sampling Design Memo PDF. |
| POST | /export/preflight-memo | Generate and download a Pre-Flight Report Memo PDF. |
| POST | /export/population-profile-memo | Generate and download a Population Profile Memo PDF. |
| POST | /export/expense-category-memo | Generate and download an Expense Category Analytical Procedures Memo PDF. |
| POST | /export/accrual-completeness-memo | Generate and download an Accrual Completeness Estimator Memo PDF. |
| POST | /export/sampling-evaluation-memo | Generate and download a Sampling Evaluation Memo PDF. |
| POST | /export/flux-expectations-memo | Generate and download ISA 520 Flux Expectations Memo PDF. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Benchmarks
**Prefix:** _(none)_
**Tag:** `benchmarks`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| GET | /benchmarks/industries | Get list of industries with available benchmark data. |
| GET | /benchmarks/sources | Get benchmark data source attribution information. |
| GET | /benchmarks/{industry} | Get benchmark data for a specific industry. |
| POST | /benchmarks/compare | Compare client ratios to industry benchmarks. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Trends
**Prefix:** _(none)_
**Tag:** `trends`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| GET | /clients/{client_id}/trends | Get trend analysis for a client's historical diagnostic data. |
| GET | /clients/{client_id}/industry-ratios | Get industry-specific ratios for a client. |
| GET | /clients/{client_id}/rolling-analysis | Get rolling window analysis for a client's historical data. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Prior Period
**Prefix:** _(none)_
**Tag:** `prior_period`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /clients/{client_id}/periods | Save current audit data as a prior period for future comparison. |
| GET | /clients/{client_id}/periods | List saved prior periods for a client. |
| POST | /audit/compare | Compare current audit results to a saved prior period. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Multi-Period
**Prefix:** _(none)_
**Tag:** `multi_period`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/compare-periods | Compare two trial balance datasets at the account level. |
| POST | /audit/compare-three-way | Compare three trial balance datasets: Prior vs Current vs Budget/Forecast. |
| POST | /export/csv/movements | Export movement comparison data as CSV. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Adjustments
**Prefix:** _(none)_
**Tag:** `adjustments`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/adjustments | Create a new adjusting journal entry. |
| GET | /audit/adjustments | List all adjusting entries in the current session. |
| GET | /audit/adjustments/reference/next | Get the next sequential reference number for adjusting entries. |
| GET | /audit/adjustments/types | Get available adjustment types for UI dropdowns. |
| GET | /audit/adjustments/statuses | Get available adjustment statuses for UI dropdowns. |
| GET | /audit/adjustments/{entry_id} | Get a specific adjusting entry by ID. |
| PUT | /audit/adjustments/{entry_id}/status | Update the status of an adjusting entry. |
| DELETE | /audit/adjustments/{entry_id} | Delete an adjusting entry from the session. |
| POST | /audit/adjustments/apply | Apply adjusting entries to a trial balance. |
| DELETE | /audit/adjustments | Clear all adjusting entries from the session. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## JE Testing
**Prefix:** _(none)_
**Tag:** `je_testing`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/journal-entries | Run automated journal entry testing on a General Ledger extract. |
| POST | /audit/journal-entries/sample | Run stratified random sampling on a General Ledger extract. |
| POST | /audit/journal-entries/sample/preview | Preview stratum counts without running sampling. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## AP Testing
**Prefix:** _(none)_
**Tag:** `ap_testing`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/ap-payments | Run automated AP payment testing on an accounts payable extract. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Bank Reconciliation
**Prefix:** _(none)_
**Tag:** `bank_reconciliation`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/bank-reconciliation | Reconcile bank statement against general ledger. |
| POST | /export/csv/bank-rec | Export bank reconciliation results as CSV. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Payroll Testing
**Prefix:** _(none)_
**Tag:** `payroll_testing`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/payroll-testing | Run automated payroll & employee testing on a payroll register. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Three-Way Match
**Prefix:** _(none)_
**Tag:** `three_way_match`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/three-way-match | Run three-way match validation across PO, Invoice, and Receipt files. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Revenue Testing
**Prefix:** _(none)_
**Tag:** `revenue_testing`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/revenue-testing | Run automated revenue recognition testing on a revenue GL extract. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## AR Aging
**Prefix:** _(none)_
**Tag:** `ar_aging`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/ar-aging | Run AR aging analysis on trial balance + optional sub-ledger. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Fixed Asset Testing
**Prefix:** _(none)_
**Tag:** `fixed_asset_testing`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/fixed-assets | Run automated fixed asset register testing. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Inventory Testing
**Prefix:** _(none)_
**Tag:** `inventory_testing`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/inventory-testing | Run automated inventory register testing. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Engagements
**Prefix:** _(none)_
**Tag:** `engagements`

_Aggregator router. Composes sub-routers: engagements_analytics, engagements_exports._

### Endpoints -- CRUD
| Method | Path | Summary |
|--------|------|---------|
| POST | /engagements | Create a new engagement for a client. |
| GET | /engagements | List engagements with optional filters. |
| GET | /engagements/{engagement_id} | Get a specific engagement with ownership check. |
| PUT | /engagements/{engagement_id} | Update an engagement. |
| DELETE | /engagements/{engagement_id} | Archive an engagement (soft delete). |

### Endpoints -- Analytics
| Method | Path | Summary |
|--------|------|---------|
| GET | /engagements/{engagement_id}/materiality | Compute materiality cascade for an engagement. |
| GET | /engagements/{engagement_id}/tool-runs | List tool runs for an engagement. |
| GET | /engagements/{engagement_id}/workpaper-index | Generate workpaper index for an engagement. |
| GET | /engagements/{engagement_id}/convergence | Get cross-tool account convergence index for an engagement. |
| GET | /engagements/{engagement_id}/tool-run-trends | Get per-tool score trends for an engagement. |

### Endpoints -- Exports
| Method | Path | Summary |
|--------|------|---------|
| POST | /engagements/{engagement_id}/export/anomaly-summary | Generate anomaly summary PDF for an engagement. |
| POST | /engagements/{engagement_id}/export/package | Generate and stream diagnostic package ZIP for an engagement. |
| POST | /engagements/{engagement_id}/export/convergence-csv | Export convergence index as CSV. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Follow-Up Items
**Prefix:** _(none)_
**Tag:** `follow_up_items`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /engagements/{engagement_id}/follow-up-items | Create a follow-up item for an engagement. |
| GET | /engagements/{engagement_id}/follow-up-items | List follow-up items for an engagement with optional filters. |
| GET | /engagements/{engagement_id}/follow-up-items/summary | Get follow-up item counts grouped by severity, disposition, and tool source. |
| PUT | /follow-up-items/{item_id} | Update a follow-up item's disposition, notes, or severity. |
| DELETE | /follow-up-items/{item_id} | Delete a follow-up item. |
| GET | /engagements/{engagement_id}/follow-up-items/my-items | Get follow-up items assigned to the current user. |
| GET | /engagements/{engagement_id}/follow-up-items/unassigned | Get follow-up items with no assignee. |
| POST | /follow-up-items/{item_id}/comments | Create a comment on a follow-up item. |
| GET | /follow-up-items/{item_id}/comments | List all comments for a follow-up item. |
| PATCH | /comments/{comment_id} | Update a comment's text. Only the author can edit. |
| DELETE | /comments/{comment_id} | Delete a comment. Only the author can delete. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Contact
**Prefix:** `/contact`
**Tag:** `contact`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /contact/submit | Submit a contact form inquiry. Public endpoint -- no auth required. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Currency
**Prefix:** _(none)_
**Tag:** `currency`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/currency-rates | Upload a CSV rate table for multi-currency conversion. |
| POST | /audit/currency-rate | Add a single exchange rate for simple conversions. |
| GET | /audit/currency-rates | Check if the user has an active rate table in their session. |
| DELETE | /audit/currency-rates | Clear the user's rate table from the session. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Sampling
**Prefix:** _(none)_
**Tag:** `sampling`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /audit/sampling/design | Design and select a statistical sample from an uploaded population. |
| POST | /audit/sampling/evaluate | Evaluate a completed sample and determine Pass/Fail. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Billing
**Prefix:** `/billing`
**Tag:** `billing`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /billing/create-checkout-session | Create a Stripe Checkout Session for upgrading to a paid plan. |
| GET | /billing/subscription | Get the current user's subscription details. |
| POST | /billing/cancel | Cancel the current subscription at the end of the billing period. |
| POST | /billing/reactivate | Reactivate a subscription that was scheduled for cancellation. |
| POST | /billing/add-seats | Add seats to the current subscription. Stripe prorates automatically. |
| POST | /billing/remove-seats | Remove seats from the current subscription. Cannot go below base seats. |
| GET | /billing/portal-session | Get a Stripe Billing Portal URL for self-service management. |
| GET | /billing/usage | Get current usage stats for entitlement display. |
| GET | /billing/analytics/weekly-review | Weekly pricing review -- 5 decision metrics with period-over-period deltas. |
| POST | /billing/webhook | Stripe webhook endpoint. No auth -- uses Stripe signature verification. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Metrics
**Prefix:** _(none)_
**Tag:** `metrics`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| GET | /metrics | Prometheus metrics endpoint. Returns text/plain with parser metrics. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Organization
**Prefix:** `/organization`
**Tag:** `organization`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /organization | Create an organization. User becomes the owner. |
| GET | /organization | Get the current user's organization. |
| PUT | /organization | Update organization name. Owner or admin only. |
| POST | /organization/invite | Send an organization invite. Owner/admin only. Checks seat limit. |
| GET | /organization/invites | List pending invites. Owner/admin only. |
| DELETE | /organization/invites/{invite_id} | Revoke a pending invite. Owner/admin only. |
| POST | /organization/invite/accept/{token} | Accept an organization invite. Links the current user to the org. |
| GET | /organization/members | List organization members. |
| PUT | /organization/members/{member_id}/role | Change a member's role. Owner only. |
| DELETE | /organization/members/{member_id} | Remove a member from the organization. Reverts their tier to free. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Export Sharing
**Prefix:** `/export-sharing`
**Tag:** `export-sharing`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /export-sharing/create | Create a shareable export link. Professional+ only. |
| GET | /export-sharing/{token} | Download a non-passcode shared export. Public (no auth). Returns **403** with an instructional message if the share is passcode-protected — callers must switch to the POST variant below. |
| POST | /export-sharing/{token}/download | Download a passcode-protected shared export. Public (no auth). Body: `{"passcode": "..."}`. |
| DELETE | /export-sharing/{token} | Revoke a share link. Creator only. |
| GET | /export-sharing/ | List current user's active share links. |

### Passcode contract (Sprints 696/697/698, 2026-04-20)

Create-side (`POST /export-sharing/create`):
- `passcode` (optional) — must be **10+ characters** across **3+ character classes** (upper, lower, digit, special). Weak passcodes are rejected at create time with 422.
- Hash format: **Argon2id** (OWASP 2024 params). bcrypt retained on verify for the ≤48h share-TTL transition window.

Download-side (`POST /export-sharing/{token}/download`):
- For passcode-protected shares the body **must** include `{"passcode": "..."}`. Non-passcode shares accept this endpoint too and ignore `body.passcode`, letting clients use a single call pattern.
- The **GET** variant is retained for non-passcode shares only. The historical `GET /export-sharing/{token}?passcode=…` pattern has been **removed** — query-string passcodes leak via access logs, browser history, and proxies.

Lockout + throttle (Sprint 698):
- **Per-token:** 5 consecutive failures → 5-minute lockout scoped to the share token, doubling thereafter. Response is 429 with `Retry-After: <seconds>`.
- **Per-IP:** independent per-IP failure tracker bounds credential-stuffing across many share tokens from one network. Response is 429 with `Retry-After: 900` (15-minute default).

### Error shapes

| Status | Meaning |
|--------|---------|
| 200 | Bytes streamed; `Content-Disposition` carries the filename. |
| 403 | Missing / invalid passcode, or GET hit a passcode-protected share. |
| 404 | Share not found or revoked. |
| 410 | Share expired (past TTL). |
| 422 | Create-side: passcode below strength threshold. |
| 429 | Lockout active (per-token or per-IP). `Retry-After` header present. |

### Migration notes for callers

- **Query-string passcodes are removed.** Any client constructing `?passcode=X` URLs will receive 403 with an instructional message. Migrate to POST body.
- **Pre-Sprint-696 SHA-256 hashes** are rejected at verification. The nightly retention cleanup (Sprint 700) revokes them proactively, so owners see "revoked" in their dashboard rather than recipients seeing a silent 403. TTL-expired shares drain within ≤48h anyway.

---

## Admin Dashboard
**Prefix:** `/admin`
**Tag:** `admin`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| GET | /admin/overview | Overview: seats, uploads this month, active members. |
| GET | /admin/team-activity | Filterable team activity log. |
| GET | /admin/usage-by-member | Per-member upload counts for the current month. |
| GET | /admin/export-activity-csv | Export team activity as CSV. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Branding
**Prefix:** `/branding`
**Tag:** `branding`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| GET | /branding/ | Get current branding configuration. |
| PUT | /branding/ | Update header/footer text. |
| POST | /branding/logo | Upload a logo image. Enterprise only. Max 500KB, PNG/JPG. |
| DELETE | /branding/logo | Remove the logo. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.

---

## Bulk Upload
**Prefix:** `/upload/bulk`
**Tag:** `bulk-upload`

### Endpoints
| Method | Path | Summary |
|--------|------|---------|
| POST | /upload/bulk | Accept up to 5 files for bulk processing. Enterprise only. |
| GET | /upload/bulk/{job_id}/status | Poll bulk upload job progress. |

> **Narrative pending:** Add usage context, request/response examples, and integration notes here.
