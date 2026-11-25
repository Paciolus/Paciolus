# Paciolus Council Audit — 2026-11-25

**Scope:** production `main` at `209e5039`, the day after 166 commits landed together (#333) and Sprint 870 fixed rate
limiting. Six members read the code in parallel without running suites (the machine was short of memory):
- **Guardian** (security);
- **Accounting Expert** (methodology);
- **Critic** (backend correctness and the merge seams);
- **Designer** (frontend, UX and accessibility);
- **Scout** (CI, operations and reliability);
- **Compliance** (claims versus code).

Each was told to skip anything already in `tasks/todo.md` and to cite file:line with a concrete failure.

**Verification.** Findings marked **✔ verified** were re-read in the code by the IntegratorLead before this report.
The rest are *reported*: the member cited code, but nobody has re-checked them. Each sprint below starts by
re-checking its reported items.

## 1) Executive summary

- **One launch blocker, fixed tonight:** passcode-protected share links could not be downloaded by anyone (G-01).
- **Today's rate-limit fix exposed two latent defects:**
  - signed-in browsers were limited as anonymous users, by IP (G-02);
  - the Stripe webhook limit was low enough to reject Stripe's own bursts (G-03).
  - Both were harmless while limits never fired. Both are fixed in Sprint 896 (PR, this branch).
- **A data-loss bug from the merge seam:** a firm member deleting their account deleted the firm's clients and colleagues'
  engagements (C-01). Sprint 853 moved ownership to the firm; Sprint 844's erasure still scoped by creator. Fixed in 896,
  with a guard test for every column that references `users.id`.
- **Methodology, statistical sampling:**
  - credit balances drop out of an MUS selection silently (A-F1);
  - the 97% reliability row is not from the AICPA guide and understates (A-F7);
  - several ISA paragraph citations are wrong (A-F3);
  - the memo describes a factor method the engine no longer uses (A-F4).
- **Operations is thin for a launch:**
  - one instance with no Render health check;
  - 4 workers in a 2 GB container that can take 100 MB uploads;
  - uptime checks that GitHub throttles to every 4–12 hours;
  - no 5xx alert.
- **Claims:** the site still lists ODS, which is disabled, and the data export promises "everything" but misses 8 tables.

| Severity | Count | Fixed tonight (896) |
|---|---|---|
| P0 | 1 | 1 |
| P1 | 10 | 2 |
| P2 | 21 | 3 |
| P3 | 17 | 0 |
| **Total** | **49** | **6** |

## 2) Findings

### Fixed in Sprint 896 (all ✔ verified)

| ID | Sev | Finding | Fix |
|---|---|---|---|
| G-01 | P0 | Passcode shares undownloadable. The GET returns 404 for a passcode share (`export_sharing.py:612`) while the page waits for 403 (`shared/[token]/page.tsx:78`). The passcode POST is CSRF-checked, and an anonymous recipient cannot obtain a token. Backend tests all used `bypass_csrf`; the frontend test mocked a 403 the backend no longer sends. | Exempt exactly `/export-sharing/<token>/download` from CSRF. The page shows the passcode form on a GET 404 and lets the POST decide. Tests run without `bypass_csrf`. |
| G-02 | P1 | `RateLimitIdentityMiddleware` read only `Authorization: Bearer`, but browsers authenticate with the HttpOnly cookie (`security_middleware.py:269`). Paid tiers got anonymous limits, and a firm on one office address shared one bucket. | Use `_extract_access_token` (header, then cookie). |
| G-03 | P2 | Stripe webhook limit 10/minute per source address. Stripe sends about 6 events per checkout from a shared pool. | 300/minute. |
| C-01 | P1 | A member's erasure deletes firm clients they created, with colleagues' engagements (`account_erasure.py:122`). | Delete personal clients plus clients of firms the user owns. Firm clients elsewhere stay and pass to the firm owner. |
| C-02 | P2 | A sole owner's erasure fails on the firm's RESTRICT key after Stripe is cancelled. | Covered by C-01's scope. |
| C-03 | P2 | `analytical_expectations.actual_captured_by` is not cleared, so erasure returns 500. | Added; guard test over all `users.id` foreign keys. |

### Security (Guardian) — remaining

| ID | Sev | Finding | Status |
|---|---|---|---|
| G-04 | P3 | A successful login resets the IP's cross-account failure counter (`services/auth/identity.py:96,112,122`). Spray 19 guesses, log into your own account, repeat. Per-account and per-token limits still hold. | reported |

The member found these sound: client and firm scoping, org roles, refresh rotation with reuse detection, admin and
impersonation, share hashing and lockout, upload limits (zip, XML, OFX), CSV escaping, CORS, and `get_client_ip`.

### Methodology (Accounting Expert)

| ID | Sev | Finding | Status |
|---|---|---|---|
| A-F1 | P1 | MUS drops credit-balance items from selection but keeps them in the population value and the interval. The exclusion is only logged (`sampling_engine.py:375, 773, 826`). The memo and response say nothing. | ✔ verified (only a `logger.info`) |
| A-F2 | P2 | The covenant debt-to-equity test cannot flag negative equity: `dte` is negative, so `dte > ceiling` is false (`going_concern_engine.py:337`). | ✔ verified |
| A-F3 | P2 | Wrong ISA paragraph citations. "ISA 530.17" does not exist (requirements end at 15). 530.14 is cited for evaluation (that is 530.15). Tolerable misstatement is attributed to "ISA 320.11" instead of 530.5(l). (`sampling_memo_generator.py:161…1452, 692, 716`) | reported; check against IAASB text |
| A-F4 | P2 | The memo says the expansion factor comes from "Table A-1 with interpolation between expected-to-tolerable buckets". Sprint 805 removed that method (`sampling_memo_generator.py:724`). | reported |
| A-F5 | P2 | Ratios assume a 12-month TB: DSO/DIO/DPO use ×365 and ROA/ROE use period-to-date flows, with no period length (`ratio_engine.py:1132…`). A 6-month TB doubles DSO. | reported |
| A-F6 | P2 | The memo says MUS "was applied in accordance with ISA 530 and PCAOB AS 2315" (`sampling_memo_generator.py:1043, 1367`). The tool cannot attest compliance. | reported |
| A-F7 | P3 | The 97% Poisson row is not in the AICPA guide and understates: rank 3 gives 8.39 against an exact 8.51; rank 10 gives 17.70 against 18.02 (`audit_figure_registry.py:101`). `confidence_level` is free input. | ✔ verified (recomputed) |
| A-F8 | P3 | Going-concern counts negative equity twice (Net Liability Position and High Leverage). "Recurring Losses" fires on one period. | reported |
| A-F9 | P3 | ROE narrative is wrong for a profitable entity with negative equity (`ratio_engine.py:1049`). | reported |
| A-F10 | P3 | The SOCE keyword `"oci"` is a bare substring, so "Associates' Capital" and "Social…" are misfiled (`financial_statement_builder.py:1411`). | reported |

The member found these sound:
- Stringer bound, increments and expansion factors;
- the 1/5/10/15/20% Poisson rows;
- Benford MAD bands and the χ² test;
- the indirect cash flow;
- pre-closing equity;
- 1099/W-2 year keying.

### Backend correctness (Critic) — remaining

| ID | Sev | Finding | Status |
|---|---|---|---|
| C-04 | P2 | Sprint 890's move off the event loop stopped partway. The TB route and six others still do blocking DB work in `async def` (`routes/audit_pipeline.py:49`, `ar_aging.py`, `audit_flux.py`, `bank_reconciliation.py`, `three_way_match.py`, `sampling.py`, `currency.py`). | reported |
| C-05 | P3 | The hourly quota reset zeroes `uploads_used_current_period` without moving `uploads_window_start`, so a subscriber whose renewal webhook is late has no cap (`cleanup_scheduler.py:396`). | reported |
| C-06 | P3 | A single-use share is revoked before its bytes are fetched. An R2 blip loses the report for good (`export_sharing.py:551`). | reported |

The member found these sound:
- organization service commits and the seat lock;
- `session_scope` metering;
- the preflight cache;
- share upload ordering;
- checkout admission;
- the Decimal port;
- the linear migration chain;
- Zero-Storage.

### Frontend and UX (Designer)

| ID | Sev | Finding | Status |
|---|---|---|---|
| D-1 | P1 | On the dark `/checkout` route, the price, total and promo error use sage-600/clay-600 at about 1.9:1 contrast (WCAG needs 4.5) (`checkout/page.tsx:187…318`). | reported |
| D-2 | P1 | `/checkout/success` says "Your account has been upgraded" without checking. The tier arrives by webhook, and `refreshUser` returns early with no token after the Stripe redirect. | reported |
| D-3 | P2 | "Continue to Checkout" is enabled before the trial/renewal terms load, and stays so if they never load. | reported |
| D-4 | P2 | The cancel-trial dialog says access ends immediately, but the backend cancels at period end (`CancelModal.tsx:89`). | reported |
| D-5 | P2 | Cancel, Upgrade and Create-Misstatement modals have no dialog role, focus trap or Escape (WCAG 2.1.2/2.4.3). | reported |
| D-6 | P2 | After a single-use download, the share page says "remains valid" and offers "Download again". | reported |
| D-7 | P3 | The adjusting-entry form says "balanced" on raw floats while the server compares rounded cents. Its line inputs have no accessible name. | reported |
| D-8 | P3 | Any engagement load error says "Workspace not found." with no retry. | reported |
| D-9 | P3 | Promo codes `MONTHLY20`/`ANNUAL10` are in the public bundle. | reported |
| D-10 | P3 | The register terms checkbox (a `div role=checkbox` in a label) has no accessible name. | reported |

### Operations (Scout)

| ID | Sev | Finding | Status |
|---|---|---|---|
| O-1 | P1 | No Render health check path and one instance: a hung worker is never restarted. | reported (Render API) |
| O-2 | P1 | 4 workers in a 2 GB, 1-CPU container. Memory docs assume 2 GB per worker, uploads go up to 100 MB, and parses have no concurrency limit. Two big uploads can OOM the whole service. | reported (Render metrics) |
| O-3 | P1 | Monitoring is thin. Uptime runs every 4–12 hours in practice (throttled). The planned external monitor targets `/health`, not `/health/ready`. There is no Sentry 5xx alert. | reported |
| O-4 | P2 | `bulk_job_store` and `ip_failure_tracker` pin to per-worker memory after one Redis failure (no retry, unlike Sprint 877). | reported |
| O-5 | P2 | Security state (impersonation revocations, IP counters) sits on a free, non-persistent, `allkeys_lru` Key Value. An eviction can un-revoke a token. | reported |
| O-6 | P2 | CI never builds or starts the Docker image. A broken startup is found only in production (the Sprint 768 pattern). | reported |
| O-7 | P2 | `gunicorn==21.2.0` is installed in the Dockerfile, outside requirements, so audits and Dependabot never see it (CVE-2024-1135, CVE-2024-6827). Dependabot has no `docker` ecosystem. | reported |
| O-8 | P3 | A failed daily backup alerts nobody until the weekly check. | reported |
| O-9 | P3 | Migrations run while the old instance serves. There is no expand/contract rule or CI check for destructive migrations. | reported |

### Claims (Compliance)

| ID | Sev | Finding | Status |
|---|---|---|---|
| L-1 | P1 | Homepage, About and Terms list ODS, which is disabled (`FORMAT_ODS_ENABLED` defaults false). Word, which is enabled, is not named. | reported |
| L-2 | P1 | Privacy says the JSON export is "everything we hold", but `export_account` leaves out 8 tables: billing events, checkout attempts, promo redemptions, security events, org members, invites, team activity, firm branding. | reported |
| L-3 | P2 | Currency rate-table rows are kept for 2 hours (and can reach backups), contradicting "the rows in your uploads … not kept". | reported |
| L-4 | P2 | Privacy says erasure keeps "a security-log entry that a deletion happened", but all security events are kept, unlinked, for up to 365 days. | reported |
| L-5 | P2 | The billing page says "DPA acceptance is captured at checkout"; it never is, and the version is hard-coded 1.0 against a 2.0-draft DPA. | reported |
| L-6 | P2 | The trust "what we keep" list claims to be exact but misses adjustments, rate tables, filename prefixes, user-agent, security events, billing, branding and invites. | reported |
| L-7 | P3 | "Reply within 1–2 business days" is stated as fact; the Contact page says "aim". | reported |
| L-8 | P3 | Privacy cites GDPR Art. 15 for the 30-day deadline; that is Art. 12(3), "one month". | reported (counsel) |
| L-9 | P3 | `/sources` says bank rec "produces audit evidence"; the disclaimers say Paciolus does not. | reported |
| L-10 | P3 | The pricing table implies Professional gets more export formats than Solo; it doesn't. | reported |

## 3) Tensions and resolutions

- **Guardian vs. the Sprint 718 design (G-01).** Sprint 718 made the GET hide passcode shares, which is right. Exempting the
  POST from CSRF looks like a weakening, but the route has no session to forge: it is unauthenticated, called with
  `credentials: 'omit'`, and gated by the passcode and its throttles. Resolution: exempt by exact path shape and
  keep everything else checked (a test proves `/export-sharing/create` still needs CSRF).
- **Critic vs. Compliance on erasure (C-01).** Compliance wants deletion to be complete ("immediate and
  irreversible"). The Critic wants the firm's records to survive. The firm owns firm clients (Sprint 853), so a member's
  erasure removes the member, not the firm's work. A member who created engagements on firm clients is refused and
  referred to privacy@ instead of having firm work deleted. That is less self-service, but nothing is lost.
- **Scout vs. the freeze.** O-1, O-2 and O-3 are operations, not features. They are launch-readiness work, so they are exempt.
- **Webhook limit (G-03): remove it or raise it?** The Guardian accepts either. Raised to 300/minute so the route keeps a
  ceiling (AUDIT-07's rule that no unauthenticated route is unlimited).

## 4) Proposed sprints (filed in `tasks/todo.md`)

- **Sprint 897 — launch operations (P1).**
  - Render health check `/health/live`.
  - `WEB_CONCURRENCY` 2–3 plus a parse semaphore.
  - External monitor on `/health/ready` with a body match, and a Sentry 5xx alert (CEO: accounts).
  - gunicorn into requirements, and the Docker ecosystem in Dependabot.
  - Redis-retry for the two stores.
  - A CI image build and boot.
- **Sprint 898 — sampling and ratio methodology (P1/P2).**
  - Disclose or stratify MUS credits.
  - Remove or compute the 97% row.
  - Fix the ISA citations and the stale factor wording.
  - Replace "in accordance with".
  - Covenant and going-concern fixes; ROE narrative; SOCE `oci` matching.
  - Period length for the ratios (CEO: is a TB always annual?).
- **Sprint 899 — checkout, claims and accessibility (P1/P2).**
  - D-1/D-2/D-3/D-4/D-5/D-6.
  - L-1/L-2/L-5/L-6/L-7/L-9/L-10.
  - Legal items L-3/L-4/L-8 go to the counsel package.
- **Later (P3):** G-04, C-04 (needs the freeze lifted: it is a performance change), C-05, C-06, D-7…D-10, O-4/O-5/O-8/O-9.

## 5) Agent coverage

| Member | Read | Not reviewed |
|---|---|---|
| Guardian | routes (auth, org, clients, engagements, sharing, admin, billing), CSRF/identity middleware, uploads | live requests (none made) |
| Accounting Expert | sampling, Benford, going concern, ratios, FS builder, cash flow, W-2/1099 | bank rec, 3-way match, payroll, revenue, book-to-tax in depth |
| Critic | the 166-commit merge seams, erasure, scheduler, migrations, sharing, checkout | webhook→attempt ordering |
| Designer | checkout, billing, share page, modals, workspace, register, adjustments | long TB upload hook, batch upload |
| Scout | workflows, Dockerfile, Render service/metrics/Key Value, Sentry rules, backups | — |
| Compliance | marketing/legal pages, trust and storage content, memos, export vs. erasure | counsel-branch text beyond the diff |
