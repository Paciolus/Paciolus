# Claims Review — Legal and Security Language (2026-10-24)

**Readable version (CEO doc):** https://claude.ai/artifact/MFTYHezjA4zakoiKwgnNb2
**Backlog:** Sprints 840–845 in `tasks/todo.md` implement everything below.

Three read-only reviews: (A) marketing, billing and legal copy; (B) security claims checked against the code; (C) professional-standards and professional-liability language. Paths are relative to the repo root. Line numbers are as of `main` @ `5f82d818` — re-locate by quote if they have drifted.

**CEO direction (2026-10-24):** no "tricky" language; accuracy over marketing polish. Counsel will review the Terms, Privacy Policy and DPA **once the website is finalized** — fixing factually wrong sentences does not wait for that review. The CEO is a CPA and owns the practitioner items (2026 1099/W-2 figures, sampling formulas, ISA 315 check).

**Ground truth — what is actually stored:**
- **Database (Neon Postgres, us-east-1 — not Render, not Oregon):** user accounts; client name, industry and fiscal year-end; `diagnostic_summaries` (total assets, revenue, expenses, ratios, total debits/credits per analysis, `backend/models.py` ~352–390); `activity_logs` (total debits/credits, materiality, filename hash + 8-char prefix); `tool_activities` (12-char filename prefix + `summary_json`); `tool_runs.flagged_accounts` (account names, no amounts, `backend/engagement_model.py:256`); engagement content the auditor types (materiality, intercompany mappings, `analytical_expectations` expected/actual, `uncorrected_misstatements` account + DR/CR + amount); `tool_sessions` (adjustments / currency rates, 1–2 h).
- **Cloudflare R2:** full PDF/Excel/CSV bytes of reports shared by link, 24 h (Professional) / 48 h (Enterprise); passcode optional (`backend/routes/export_sharing.py:74`).
- **Disk:** Starlette spools uploads over 1 MB to a temp file during the request (`starlette/formparsers.py:126,209`).
- **Memory caches:** preflight cache holds raw upload bytes 10 min (`backend/shared/preflight_cache.py`); bulk-upload job state with filenames in Redis 2 h.
- **Third parties:** Sentry may receive local variables / exception text (see S2); Render logs receive filenames and parser exception text (S6).
- **Deletion:** retention cleanup, "Clear history" and "delete engagement" are soft deletes (`archived_at` / ARCHIVED; `backend/retention_cleanup.py`, `backend/routes/activity.py:296`, `backend/engagement_manager.py:368`). **No account-deletion or data-export endpoint or UI exists.**
- **The GitHub repo is PUBLIC** (verified `gh repo view` → PUBLIC), so every file under `docs/` is a published claim.

---

## Part 1 — Security defects (Sprint 840)

### High
- **S1. Revenue metrics readable by any paying customer.** `backend/routes/internal_metrics.py:38-70` `_require_owner` passes any org owner or any solo user with an active/trial subscription; the functions query every subscription (`backend/billing/internal_metrics.py:89, 262, 419, 557`) — MRR, ARR, churn, trial funnel, revenue history. A $100 Solo user calling `GET /internal/metrics/revenue` gets them. **Fix:** `Depends(require_superadmin)` like `routes/internal_admin.py`.
- **S2. Sentry can receive client financial data.** `backend/main.py:102-131`: `send_default_pii=False` but `include_local_variables` defaults True (sentry-sdk 2.58 keeps strings up to 100,000 chars, `sentry_sdk/consts.py:9, 1023`). `_before_send` strips `request.data`, `extra`, `contexts` but not frame vars, exception messages or breadcrumbs. Any unhandled exception in an upload route captures `file_bytes`/DataFrames; `backend/routes/export_sharing.py:363` logs an R2 failure with `exc_info` whose frame holds `export_bytes`. **Fix:** `include_local_variables=False`, `max_value_length≈1024`, drop `exception.values[].value`, frame `vars` and breadcrumbs in `before_send` (or `LoggingIntegration(level=None)`).

### Medium
- **S3. "Read-only" impersonation can write.** `backend/security_middleware.py:871-878` only blocks when the header starts exactly with `"Bearer "`; auth also accepts lowercase `bearer` (`backend/auth.py:78`) and the `paciolus_access` cookie (`auth.py:91-93`). `security_middleware.py:901-904` lets writes through once the token is *revoked*, and nothing else rejects revoked impersonation tokens; the stop endpoint (`routes/internal_admin.py:359-421`) is unreachable, so tokens live 15 min. Token in `sessionStorage` (`ImpersonationBanner.tsx:20`). Org-ID impersonation silently falls back to a user ID (`internal_admin.py:323-327`). **Fix:** in `require_current_user`, refuse any token with an `imp` claim on mutating methods and refuse revoked token IDs; remove the "revoked = allowed" branch.
- **S4. CSV formula injection in six exports** (no `sanitize_csv_value` from `backend/shared/filenames.py`): `backend/account_risk_heatmap_engine.py:403` (account_name), `backend/sod_engine.py:481, 510` (user_name), `backend/routes/form_1099.py:188-215` (vendor_name, vendor_id), `backend/routes/intercompany_elimination.py:149+` (entity_name), `backend/routes/book_to_tax.py:190+` (labels), `backend/routes/lease_accounting.py:146` (lease_name). **Fix:** one shared escaped CSV writer used by every export, plus a test that scans export code for unescaped `writer.writerow`.
- **S5. Security events are discarded.** `log_secure_operation` (`backend/security_utils.py:322-337`) appends to an in-memory list capped at 1,000 per worker; `get_security_log` is never called. Failed logins, lockouts, CSRF blocks, XML-bomb detections, refresh-token reuse alerts and impersonation-token creation (`auth.py:195`) vanish on restart. **Fix:** route through `logging` to stdout/Loki; persist critical ones (auth failures, lockouts, token reuse, impersonation) to a DB table.
- **S6. Client data in application logs.** Filename + raw exception text (often traceback with cell values) at `backend/shared/testing_route.py:150`, `backend/routes/sampling.py:279, 372`, `backend/shared/ods_parser.py:88, 107`, `backend/shared/ofx_parser.py:426`, `backend/shared/pdf_parser.py:337`, `backend/shared/docx_parser.py:78`. Ends up in Render logs, Loki and Sentry breadcrumbs. **Fix:** log `type(exc).__name__` only (as `upload_pipeline.py:577, 610` already does); no filenames.
- **S7. Decompression memory exhaustion.** `backend/shared/upload_pipeline.py:66-68` allows 1 GB uncompressed at 100:1; a 10 MB ODS can expand to 1 GB of XML loaded by odfpy. **Fix:** cap ~100–200 MB uncompressed, ratio ~20.
- **S8. R2 share files can be orphaned.** `backend/cleanup_scheduler.py:431-437` deletes the DB row even when the R2 delete fails (`backend/export_share_storage.py:152-167`). **Fix:** delete the row only after R2 confirms; add an R2 lifecycle rule ≤ 2 days (CEO console).

### Low
- Email enumeration: unknown emails return before any bcrypt check (`auth.py:515-519`) — add a dummy `checkpw`; registration of an existing email returns a different response (`backend/services/auth/registration.py:114-116`).
- No `SlowAPIMiddleware`; ~52 of 237 routes have no `@limiter.limit` (e.g. `/audit/chain-verify`, `/auth/me`) — the "global 60/min" claim isn't true (confirm with a test).
- Share-passcode IP throttle uses the proxy IP (`export_sharing.py:521-523` uses `request.client.host`) — use `get_client_ip()` and set `TRUSTED_PROXY_IPS`.
- Preflight cache keeps raw bytes 10 min, read with `get` not pop, token not bound to the user (`routes/audit_pipeline.py:71`).
- Uploads over 1 MB spool to `/tmp` (framework default) — either keep in memory (raise spool threshold within the 100 MB cap) or disclose.
- Adjustment approver name comes from the request body and self-approval is allowed (`routes/adjustments.py:241-242`).
- Lockout is fixed 5 attempts / 15 min, not progressive (`security_middleware.py:640-706`).
- No MFA anywhere, including superadmin.

### Security claims that are accurate (keep saying them)
bcrypt 12 rounds (`auth.py:40-57`); Argon2id share passcodes 64 MiB/t=3/p=4, min 10 chars, POST body, per-token lockout (`shared/passcode_security.py:57, 223`); HttpOnly/Secure/SameSite refresh and access cookies (`routes/auth_routes.py:104-136`); 7-day refresh rotation with reuse detection (`auth.py:682-743`); all sessions revoked on password change (`auth.py:274-288`); HMAC user-bound CSRF + Origin/Sec-Fetch-Site checks (`security_middleware.py:443-632`); nonce CSP with strict-dynamic (`frontend/src/proxy.ts:46-64`); HSTS, `frame-ancestors 'none'`, `no-store` on downloads (`security_middleware.py:60-97`); strict CORS (`config.py:80-92`); DB-backed lockout, uniform 401s; hashed single-use reset tokens (`services/auth/recovery.py:110-154`); disposable-email blocking; upload size/row/zip/signature checks and defusedxml everywhere, PDF 500-page cap; all data lookups scoped to user/org (no IDOR found); 256-bit hashed share tokens; `/metrics` loopback-only; API docs off in prod; Stripe webhook signature verified; prod refuses to start without secrets; soft-delete guards on 5 audit tables.

---

## Part 2 — "Never stored" absolutes (Sprint 841)

**Approved positioning (Option B):** drop "Zero-Storage" as a headline promise; everywhere say: *"Your uploaded files are processed in memory and not kept after analysis. We save your account, client list, analysis summaries and anything you enter in an engagement. [See exactly what we keep.]"* — linking to the Trust page store / never-store lists (`frontend/src/app/(marketing)/trust/page.tsx:245-260`, accurate since Sprint 834; mirror at `approach/page.tsx:96-112`). Option C (make "we keep nothing from your uploads" literally true by dropping `tool_runs.flagged_accounts` etc.) is a later product choice.

### High — rewrite each
| # | Quote | Location |
|---|---|---|
| A1 | "Your financial data is never stored at rest." | `frontend/src/app/(marketing)/trust/layout.tsx:5` (SEO) |
| A2 | "…processed in-memory and never stored at rest" | `frontend/src/app/(marketing)/privacy/layout.tsx:5,8` |
| A3 | "Raw financial files are processed in-memory and not stored at rest." | `frontend/src/app/layout.tsx:49` (site SEO; also "Eliminate sign errors and misclassifications" → "Flags likely sign errors…") |
| A4 | "We never store your financial data" | `privacy/page.tsx:21` |
| A5 | Trial balance data / Account Balances / Anomaly Details marked not stored | `privacy/page.tsx:172-215` (181, 208) — split into "uploaded rows: not stored" vs "totals/ratios/flagged account names: stored" |
| A6 | "All data is immediately destroyed…", "No database to breach, no files to leak", "no PI to delete", "Zero financial data retention" | `privacy/page.tsx:335, 343, 347, 351` |
| A7 | "We do not write to disk, cache layers… streamed directly to your browser" | `privacy/page.tsx:356` — add temp buffer for large uploads, preview cache, share links |
| A8 | "No persistent storage = no data breach risk" | `privacy/page.tsx:521` |
| A9 | Retention table "<5 seconds (ephemeral)" incl. "Anomaly Details" | `privacy/page.tsx:977-1019` |
| A10 | "never written to disk, databases, or logs"; "No financial data is logged, cached, or retained" | `terms/page.tsx:347, 380` (legal doc — fix the facts; counsel reviews later) |
| A11 | "Paciolus never stores: … account numbers, descriptions, or balances … line items or totals" | `terms/page.tsx:421-446` (434, 446) |
| A12 | "Aggregate activity logs (… no financial amounts)" | `terms/page.tsx:413` |
| A13 | "never at risk of being exposed through a Paciolus data breach" | `terms/page.tsx:479` — delete |
| A14 | "No financial data in database to breach" | `approach/page.tsx:75` |
| A15 | "Nothing is written to disk…zero retention", "never touches a database", "Not a platform that stores your financial data" | `about/page.tsx:209-212, 280, 45` |
| A16 | "Never written to disk. Never retained… Zero exposure", "the architecture makes it impossible" | `frontend/src/components/marketing/FeaturePillars.tsx:47-49, 124` |
| A17 | "Zero / Lines Stored / Client data never written to disk" | `frontend/src/components/marketing/EvidenceBand.tsx:44-46` |
| A18 | "never written to disk or database" | `components/marketing/DemoZone.tsx:150, 185`; `(auth)/login/page.tsx:168` |
| A19 | "Only credentials are saved securely." | `(auth)/register/page.tsx:228` |
| A20 | Email footer "Zero-Storage Architecture - Your financial data is never stored." | `backend/templates/verification_email.html:72` + `.txt`; `password_reset_email.html:72` + `.txt` |
| A21 | "never saved to any disk or server" | `frontend/src/app/tools/trial-balance/page.tsx:242` |
| A22 | Subprocessor list Zero-Storage section ("no line-level account names… ever written", "No financial data reaches Sentry", "Vercel: no personal data") | `docs/04-compliance/SUBPROCESSOR_LIST.md` |
| A23 | DPA §2.3 / §11.3 ("never stored", breach impact) — v1.0 predates R2 | `docs/04-compliance/DATA_PROCESSING_ADDENDUM.md:86, 342` |
| A24 | "Account Names Parsed From an Upload — Never Stored"; "exported file never touches persistent storage" | `docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md:115, 512` (contradicts its own line 56; no R2 section) |
| A25 | User Guide "never written to disk", "aggregate, non-attributable", "Clear All Activity History (GDPR Right to Erasure)", "Is my data safe? Yes… never stored" | `docs/07-user-facing/USER_GUIDE.md:13, 16, 1116-1118, 1308-1310, 1352` — "Clear" is a soft delete |
| A26 | "Financial data breach is architecturally impossible"; "No employee can access… architecturally impossible"; "No admin override / god mode" | `docs/04-compliance/SECURITY_POLICY.md:25, 101, 122, 474`; `ACCESS_CONTROL_POLICY.md:22, 50, 225` (superadmin impersonation exists, `routes/internal_admin.py:309`) |

### Medium
- `approach/page.tsx:31, 51, 80` ("Destroyed", "Seconds (raw data)") — qualify to "uploaded file"; `:85` "metadata cleaned on schedule" (it's archival); `:117`, `trust/page.tsx:214` (R2 is a file-level surface); `trust/page.tsx:688, 479`; `approach/page.tsx:122` + `components/marketing/DemoTabExplorer.tsx:245` ("No saved analysis history" vs About `:323` and stored summaries); `components/shared/WelcomeModal.tsx:34`; `components/workspace/WorkspaceFooter.tsx:16`; `app/(workspace)/portfolio/page.tsx:257` ("Only client metadata is saved"); `app/tools/multi-currency/page.tsx:92` (rates are in `tool_sessions` 2 h); error pages `app/error.tsx:47`, `app/tools/error.tsx:46`, `global-error.tsx:124`, `(diagnostic)/error.tsx:46` ("nothing was persisted" — unverified); `trust/page.tsx:193` ("Sentry… Zero-Storage compliant") and `:148` ("No PII in logs") — true only after S2/S6; "<5 seconds" (Privacy) vs "3-5 seconds" (`terms/page.tsx:362`) — unmeasured, use "for the duration of the request".

---

## Part 3 — Billing, pricing and business claims (Sprint 842)

| Sev | Quote | Location | Fix |
|---|---|---|---|
| High | "7-day free trial … no credit card required" | `frontend/src/domain/pricing.ts:273`; `(marketing)/pricing/page.tsx:128` | Checkout collects a card (`backend/billing/checkout.py:99-108`). "7-day free trial. Card required; we charge $X on [date] unless you cancel." Show on `(auth)/checkout/page.tsx` (currently only "Cancel anytime", :164). Auto-renewal/ROSCA disclosure. |
| High | "If you have not added a payment method by day 8 … read-only … download previously exported files … No data is deleted" | `domain/pricing.ts:277` | Flow doesn't exist; describe day-7 conversion. |
| High | "Most Popular" | `domain/pricing.ts:206` → `components/pricing/PricingCard.tsx:37` | Remove or "Recommended for teams". |
| High | "30-day money-back guarantee (Solo, Team, or Organization)" vs "No refunds for partial billing periods" | `terms/page.tsx:650` vs `docs/04-compliance/TERMS_OF_SERVICE.md:314` | One policy (CEO decision), current tier names; refunds are manual (`backend/billing/admin_customers.py:488`). |
| Med | "no hard row limit — 50,000+ rows processed routinely" | `domain/pricing.ts` ~309 | "Up to 500,000 rows and 100 MB per file" (`backend/shared/upload_pipeline.py:61`). |
| Med | "billed at the start of each calendar month" | `domain/pricing.ts:269` | "Billed monthly from your start date." |
| Med | "Annual plans can also be invoiced… custom payment terms" | `domain/pricing.ts` payment FAQ | "Contact us about invoicing" (card-only checkout). |
| Med | "Existing exports … remain accessible" on downgrade | `domain/pricing.ts` downgrade FAQ | Exports aren't stored → "client metadata remains". |
| Med | "Dedicated account manager", "Custom SLA & priority support", "8 hr response", "next business day"; support-time conflicts | `domain/pricing.ts:174, 196, 216-217, 251-253`; `USER_GUIDE.md:1394`; `(marketing)/contact/layout.tsx:5` vs `contact/page.tsx:85, 223` | One standard (CEO decision; default "Email support; we aim to reply within 1–2 business days"). |
| Med | "140+ Automated Tests" | `components/marketing/EvidenceBand.tsx:30`; `BottomProof.tsx:32` | Registry sums to 97 — derive from `tools_registry` / `tool-ledger.ts`. |
| Med | "< 3s Diagnostic Runtime / Average analysis time under three seconds" | `EvidenceBand.tsx:51`; `ProcessTimeline.tsx:293`; `HeroFilmFrame.tsx:222` | It's a p95 alert target (`utils/constants.ts:41`) → "Most analyses finish in seconds". |
| Med | "What used to take days now takes seconds" | `FeaturePillars.tsx:124` | Drop or soften. |
| Med | "Interactive demo of all 18 audit diagnostic tools"; workspace mock "of 12" | `(marketing)/demo/layout.tsx:5`; `demo/page.tsx:79`; `DemoTabExplorer.tsx:157` | "Interactive demo and an overview of all 18 tools"; fix "of 12". |
| Med | User Guide prices/limits wrong: seats "$80/$70, 8–22"; "50 MB"; Professional "unlimited uploads"; ODS "Team and above" | `USER_GUIDE.md:1094, 125/1325/1381, 1345, 121` | $65/seat up to 20 (Pro), $45 up to 100 (Ent); 100 MB; Pro 500 uploads (`backend/shared/entitlements.py:105`). |
| Med | "passcode-protected link" | `SUBPROCESSOR_LIST.md` R2 row | "optionally passcode-protected". |
| Low | "Ten formats: CSV, Excel, TSV, TXT, QBO, OFX, IIF, PDF, and ODS" | `ProcessTimeline.tsx:48` | Say "(.xlsx/.xls)". |
| Low | "Branded and ready for delivery"; "Ready to file directly into your working papers" | `ProcessTimeline.tsx:66`; `about/page.tsx:284` | Branding is Enterprise-only; "Formatted for your workpapers, after your review". |

Accurate already: prices $100/$500/$1,000 and annual $1,000/$5,000/$10,000; uploads 10/100/500/unlimited; Free = 2 tools, 3 clients, no exports; seats 7→20, 20→100; 100 MB; 7-day trial length (`backend/billing/price_config.py:127-130`). No testimonials, logos, "trusted by", ratings, "bank-grade", "military-grade", HIPAA or ISO claims.

---

## Part 4 — Professional positioning and disclaimers (Sprint 843)

### High
| # | Quote | Location | Safer wording |
|---|---|---|---|
| H1 | "The Workpapers / Write Themselves" (homepage H1) | `frontend/src/components/marketing/hero/HeroProductFilm.tsx:87-91` | "Diagnostics in seconds. Your judgment, better informed." |
| H2 | "Get ISA/PCAOB-methodology diagnostics and workpapers in seconds." | `HeroProductFilm.tsx:99` | "Get diagnostics that cite the standards they draw on, with exports you can review and file." |
| H3 | "Export Audit-Ready Memos" / "PDF memos aligned with PCAOB and ISA standards … Professional deliverables" | `frontend/src/components/shared/WelcomeModal.tsx:55-56` | "Export Analysis Memos — PDF memos that cite the relevant standards, plus Excel and CSV, for your review." |
| H4 | "PDF Workpaper Memo … auditor sign-off block. Ready to attach to workpapers." + "PCAOB AS 1215" badge | `components/marketing/DemoTabExplorer.tsx:199-201` (sign-off is off by default, `backend/shared/memo_base.py:647-653`) | Badge "PDF"; "Structured memo of test results with standards references, for your review." |
| H5 | "Ready to file directly into your working papers." / "Workpaper Ready … with signoff lines" / "A workpaper-ready export system" | `(marketing)/about/page.tsx:284, 68-69, 37` | "Formatted for your working papers after your review." |
| H6 | "Formatted and ready to file the moment analysis completes." / "Every output is report-ready…" | `components/marketing/FeaturePillars.tsx:75, 124` | "Exported when analysis completes, ready for your review." |
| H7 | Standard names as hero badges ("ISA 240 / PCAOB AS 2401", "ISA 530 / PCAOB AS 2315", "ISA 500 Substantive Testing", "ISA 500 Audit Evidence", "ISA 520 Analytical Procedures", "ISA 240 Revenue Analysis", "ISA 500 Procurement Validation", "ISA 315 (Revised 2019)…") | `app/tools/journal-entry-testing/page.tsx:92`, `statistical-sampling/page.tsx:164`, `ap-testing/page.tsx:79`, `payroll-testing/page.tsx:81`, `bank-rec/page.tsx:150`, `trial-balance/page.tsx:81`, `revenue-testing/page.tsx:100`, `three-way-match/page.tsx:101`, `composite-risk/page.tsx:110`; `app/tools/page.tsx:48-56` (`reference:`); `DemoTabExplorer.tsx:132` | Quiet "References ISA 240 · AS 2401" line; "ISA 500 Audit Evidence" → "Bank-to-book matching". |
| H8 | Memo cover "Engagement Practitioner", "Engagement Reviewer", "Report Status" (can be "Final"), placeholder "Jane Smith, CPA" | `backend/shared/report_chrome.py:426-428`; `frontend/src/components/diagnostic/EngagementDetailsPanel.tsx:121-155` | "Prepared for (entered by user)", "Status (entered by user)"; cover line "Generated analytics. Not reviewed by Paciolus. Not an audit, review or attestation." |
| H9 | Memo heading "Conclusion" with "overall risk is assessed as {tier} … given the assessed risk level" | `backend/shared/memo_template.py:368-383` | "Summary of Results": "The automated tests returned a {tier} flag-density indicator. This is not a risk assessment." |
| H10 | "The reconciling difference is immaterial and the match rate is satisfactory." / "Match rates are satisfactory" | `backend/bank_reconciliation_memo_generator.py:985`; `backend/three_way_match_memo_generator.py:120` | "Below the materiality you entered; match rate {x}%; no items exceeded the configured thresholds." |
| H11 | "No exceptions identified. The trial balance appears sound." + sections "Risk Assessment", "Total Findings", "Material Exceptions (n)" | `backend/pdf/sections/diagnostic.py:523, 395, 473, 557` | "No items exceeded the configured thresholds."; rename to "Diagnostic Score", "Items Flagged", "High-Severity Items" ("Findings" breaks the project vocabulary rule). |
| H12 | "Combined risk (RMM) is computed per ISA 315 (Revised 2019) Appendix 1 — the 4×4 matrix" / "via the ISA 315 RMM matrix" | `backend/composite_risk_engine.py:29-37`; `app/tools/composite-risk/page.tsx:118`; `app/tools/page.tsx:56` | **CEO to verify against ISA 315.** Likely: "Combined using a Paciolus 4×4 convention; ISA 315 requires separate IR/CR assessment but prescribes no matrix." Add composite risk to `methodology-sources.ts`. |
| H13 | Tool named "Form 1099 Preparation" while Terms say no "tax … preparation" | `backend/tools_registry.py:205`; `frontend/src/content/tool-ledger.ts:189`; `terms/page.tsx:153`; `demo/page.tsx:50` | "1099 Vendor Threshold Review" (update catalog tests). |

### Medium
- **M1** memo disclaimer "does not constitute audit evidence sufficient to support an opinion" (`backend/shared/memo_base.py:790-791`) → "This memo reports automated analytics. It is not audit evidence and does not support an opinion."
- **M2** sampling PASS/FAIL block under "Conclusion"; "obtain a PASS / FAIL conclusion"; "actions are required to close out the sampling workpaper" (`backend/sampling_memo_generator.py:1150-1175, 1416-1425, 1891, 171, 386-404`) → "UEL ≤ TM" / "UEL > TM", "Evaluation Result", "suggested close-out steps".
- **M3** demo "Composite Diagnostic Score — Low Risk — 54 tests passed across 4 tools" + green PASS chips (`DemoTabExplorer.tsx:101, 115`) → "Low flag density — N items flagged"; no PASS chips.
- **M4** "Every memo follows ISA/PCAOB format" / "Every result traceable to a published… standard" / "Every output cites the governing… standard" (`components/marketing/EvidenceBand.tsx:78`; `BottomProof.tsx:66-69`; `demo/page.tsx:80`) → "Every test names the rule it applies, or says when a threshold is our own convention."
- **M5** "Built with ISA and PCAOB Standards in Mind … Every workflow reflects how audit teams document substantive analytical procedures" / "designed for substantive audit procedures" (`about/page.tsx:50-51, 35`) → "Designed to support auditors' analytical work."
- **M6** "with ISA and PCAOB alignment" / "aligned to ISA and PCAOB standards" (`(marketing)/approach/layout.tsx:5, 8`) → "with references to the standards each test draws on".
- **M7** "Ghost-employee detection", "fraud indicators", "ISA 240 Fraud Indicators" (`backend/tools_registry.py:138`; `tool-ledger.ts:98,125`; `app/tools/page.tsx:48,51`; `ap-testing/page.tsx:86`; `payroll-testing/page.tsx:88`; `demo/page.tsx:38-42`; `content/dashboard-tools.ts:53,57`) → "indicators" / "patterns associated with fraud schemes".
- **M8** tax tools: Depreciation (MACRS) and Loan Amortization pages have no DisclaimerBox; 1099/W-2/Book-to-Tax lack a plain "not tax advice, not a return" line → add the tax disclaimer below to all five.
- **M9** USER_GUIDE "PCAOB AS 2315 compliant", "Client-ready PDF memos … with workpaper signoff", "Data Handling Guarantees" (`USER_GUIDE.md:301, 677, 697, 20, 1112`) → "designed to support", "PDF memos for your review", "Data Handling Commitments".
- **M10** covered in Part 2 (FeaturePillars/EvidenceBand absolutes).
- **M11** independence line on intercompany, adjusting-entry, book-to-tax and FS tools: "If the entity is your attest client, preparing entries or a tax provision is a nonattest service — check your independence rules first."
- **M12** CPA advertising (consider): no founder-CPA claim today; before adding one, check the state board rules (counsel review at website-final).

### Low
- **L1** stale test counts: `ap-testing/page.tsx:85,153` (13→14); `payroll-testing/page.tsx:87,155` (11→13); `revenue-testing/page.tsx:106` (16→18); `ar-aging/page.tsx:88,202,220,236,311` (11→12); `fixed-assets/page.tsx:69,137` (9→11); `inventory-testing/page.tsx:137` (9→10); `app/settings/practice/page.tsx:299` (JE 13→19), `:316` (AP 13→14), `:333` (Payroll 11→13); `DemoTabExplorer.tsx:106-111`; `USER_GUIDE.md:420,499,558,601,640` → derive from `tools_registry` test counts and add a consistency test.
- **L2** "140+" (see Part 3). **L3** "108 tests run across 9 tools" / "108 tests. Your file, read in full." (`HeroFilmFrame.tsx:341,361`; `useHeroAnimation.ts:26`). **L4** "7 Standards Referenced" (`BottomProof.tsx:44-47`).
- **L5** "Audit Intelligence" naming in `about/layout.tsx:4,7`, `approach/layout.tsx:4,7`, `backend/main.py:243`, `backend/email_service.py:577`, `memo_base.py:795` → per CEO naming decision (default "Diagnostic Intelligence for Financial Professionals", already used in root meta).
- **L6** see A3. **L7** "Complete engagement package" / "Take the workpapers" / "See the findings" (`useHeroAnimation.ts:21-27`) → "Export package", "Take the exports", "See what's flagged".
- **L8** refund clause tier names (see Part 3). **L9** "Defensible answer" (`about/page.tsx:127`) → "a well-documented answer". **L10** memo title "ISA 520 Flux & Expectation Documentation" (`backend/flux_expectations_memo.py:195`) → "Flux & Expectation Documentation (ref. ISA 520)".

### Standard disclaimer set (adopt verbatim unless the CEO edits)
- **Site footer:** "Paciolus is data-analytics software for accounting and audit professionals. It does not perform audits, reviews, compilations or attestation, give opinions or tax advice, or produce audit evidence. Paciolus is not affiliated with or endorsed by the IAASB, PCAOB, AICPA, FASB, IASB or IRS. We cite their standards so you can read the source; thresholds no standard sets are our own conventions (Sources & Methodology). You remain responsible for every judgment and conclusion."
- **Tool pages (above the per-tool box):** "Results are automated flags for you to review, not findings or conclusions. A flag doesn't mean something is wrong, and no flag doesn't mean nothing is. Decide what to rely on after your own procedures."
- **Memo cover:** "Generated analytics, not reviewed by Paciolus. Not an audit, review, compilation or attestation. Prepared-for, reviewer and status fields are entered by the user."
- **Memo footer:** "This memo reports automated analytics. It is not audit evidence, a risk assessment, or a conclusion on internal control, fraud or misstatement. Standards are cited for reference. Paciolus is not affiliated with any standard-setter, and thresholds marked 'Paciolus convention' are ours."
- **Tax tools (1099, W-2/W-3, Book-to-Tax, Depreciation/MACRS, Loan Amortization):** "This is a calculator, not tax advice or a tax return. Paciolus is not a tax preparer and does not file anything with the IRS, SSA or any state. Thresholds, limits and rates come from the tax year you select and may change. Check them against current IRS guidance. Classification, filing decisions and any position taken are yours. If the entity is your attest client, check your independence rules before preparing entries or provisions for it."

### Existing disclaimers that are good (anchors)
`frontend/src/components/marketing/MarketingFooter.tsx:175-178`; Terms §1.2/§1.3/§9 (`terms/page.tsx:135-175, ~680-705`); `/sources` intro (`sources/page.tsx:83-93`); memo Limitations (`memo_base.py:820-840`); `RISK_TIER_BASIS_NOTE` (`memo_base.py:113-135`); memo "not a standard-setter" sentence (`memo_base.py:792-794`); workspace banner "NOT AN AUDIT ENGAGEMENT" (`app/(workspace)/portfolio/[clientId]/workspace/[engagementId]/page.tsx:35-39`); About "What it is not" (`about/page.tsx:41-46`); Revenue / Bank Rec / SoD / Cash Flow / Book-to-Tax tool disclaimers; USER_GUIDE `:968`, `:916`.

---

## Part 5 — Privacy promises and legal-document accuracy (Sprint 844)

Fix the facts now; the counsel review of Terms/Privacy/DPA as contracts happens at website-final (CEO action).

| Sev | Issue | Location | Fix |
|---|---|---|---|
| High | Self-service account deletion promised ("immediate and irreversible"; "Settings → Account → Delete Account (< 60 seconds)"; "delete it anytime") — **doesn't exist** | `privacy/page.tsx:24, 465`; `docs/04-compliance/PRIVACY_POLICY.md:20, 309`; `terms/page.tsx:822` | Now: "Email privacy@paciolus.com; we delete within 30 days." Then **build** account deletion (hard-delete user, clients, engagements, summaries, tool runs, sessions; cancel Stripe; R2 shares) + data export. |
| High | "All stored metadata … deleted within 30 days" on termination; engagement delete / clear history described as deletion | `terms/page.tsx:869`; `PRIVACY_POLICY.md:200-204`; `DATA_PROCESSING_ADDENDUM.md:285` | Disclose archival; implement hard-delete on request / termination job. |
| High | "Contact our Data Protection Officer" (none; MD says "[To be appointed]") | `privacy/page.tsx:763`; `PRIVACY_POLICY.md:469` | "Privacy contact: privacy@paciolus.com". |
| High | Checkout requires "I accept the Data Processing Addendum (v1.0)" but links to `/trust`, which calls the DPA "planned" | `(auth)/checkout/page.tsx:296-306`; `trust/page.tsx:153-172` | Publish the DPA at a real URL (updated for Neon, R2, actual stored data) or remove the checkbox until it exists. |
| High | Entity "Paciolus LLC" vs "Paciolus, Inc." | `privacy/page.tsx:720` vs `terms/page.tsx:726, 778`; `MarketingFooter.tsx:181` | CEO decision → use everywhere. |
| High | Database "PostgreSQL (Render)" / "United States (Oregon)"; Render "Oregon"; Neon, SendGrid, Cloudflare R2, Render Key Value (holds filenames) missing; Loki/Grafana if enabled | `privacy/page.tsx:381-403, 565-576`; `SUBPROCESSOR_LIST.md`; `DATA_PROCESSING_ADDENDUM.md:165, 227-228`; `SECURITY_POLICY.md:31, 121, 127` | Neon us-east-1; Render region per console (memory says virginia); list every processor. |
| Med | Website vs markdown policy copies disagree (dates, JAMS vs AAA, refunds, seat caps "25 self-service", CCPA 30 vs 45 days, governing law "[State]") | `terms/page.tsx:14, 890, 897`; `TERMS_OF_SERVICE.md:291, 476, 487`; `PRIVACY_POLICY.md:525` | Website pages authoritative; delete or sync the markdown copies. |
| Med | Placeholders "[Address to be added]" | `PRIVACY_POLICY.md:441`; `TERMS_OF_SERVICE.md:585` | Fill or remove (address is a CEO item). |
| Med | "Version history: paciolus.com/terms/history" / "/privacy/history" (routes don't exist) | `TERMS_OF_SERVICE.md:609`; `PRIVACY_POLICY.md:423` | Remove. |
| Med | "Notify affected users within 72 hours (GDPR requirement)" | `privacy/page.tsx:537`; `PRIVACY_POLICY.md:367`; `SECURITY_POLICY.md:568`; `trust/page.tsx:225` | "Without undue delay, and regulators as the law requires" (72 h is the authority deadline, Art. 33). |
| Med | "DPA Signed ✅", "SCCs signed with Vercel, Render"; "User credentials (encrypted)" | `PRIVACY_POLICY.md:235-239, 388`; `privacy/page.tsx:567-572` | "Covered by the provider's standard DPA" (verify); passwords are hashed, not encrypted. |
| Med | Collection of "session duration", "screen resolution", "anonymized usage statistics" (no analytics runs; telemetry no-op without a key, `frontend/src/utils/telemetry.ts`) | `privacy/page.tsx:120-150`; `trust/page.tsx:252` | Remove. |
| Med | Trust "GDPR compliant 2024 / CCPA compliant 2024 (self-assessed)"; "DPA planned 2025" | `trust/page.tsx:153-172` | Remove years; DPA status per above. |
| Low | "session storage … for authentication tokens" | `PRIVACY_POLICY.md:71` | HttpOnly refresh cookie + in-memory access token. |
| Low | CCPA section lacks CPRA rights (correct, limit sensitive data, "sharing") | `privacy/page.tsx:890-900` | Add or state applicability thresholds. |
| Low | Terms service description "Trial balance upload and analysis (CSV/Excel format)" | `terms/page.tsx:90-100` | 18 tools, 10 formats. |

### Security-page claims to correct (Trust, Privacy, Security Policy)
"30-minute access tokens" (`trust/page.tsx:100-101, 131`; `ACCESS_CONTROL_POLICY.md:167`) → 15-minute (`backend/config.py:155-156`; verify `JWT_EXPIRATION_MINUTES` on Render). "Progressive lockout" (`trust:89, 134`) → "5 attempts, 15 minutes". "Per-endpoint and global 60/min" (`trust:137`) → "on authentication, upload, export and write endpoints". "Row-level security / segregated at the database level" (`trust:102, 140`; `privacy:520`; `SECURITY_POLICY.md:70, 253`) → "every query scoped in application code". "No cross-tenant data leakage" → "designed to prevent". "TLS 1.3 … end-to-end" (`trust:73, 136`; `privacy:517`; Nginx config `SECURITY_POLICY.md:106-114`) → "TLS 1.2+ (1.3 where supported), terminated at Vercel/Render". "All exports sanitized" (`trust:104, 143`) → true after S4. "Memory purge" (`trust:116, 147`) → "released from memory". "Exports streamed directly to your browser" (`privacy:355`; `ZERO_STORAGE_ARCHITECTURE.md:507`) → add share-link exception. "Enterprise-grade encryption" (`trust/layout.tsx:5, 8`) → "TLS in transit; provider-managed encryption at rest". "Automated monitoring and anomaly detection", "rate limit breach alerting" (`trust:190, 194, 227`) → "Errors go to Sentry; uptime checked every 15 minutes; no 24/7 on-call". Process promises to confirm a solo operator can keep: breach notice, disclosure response times, data-request deadlines, post-incident reports.

---

## Part 6 — Public compliance documents (Sprint 845)

The repo is public, so `docs/04-compliance/*` are published claims. False today:
- SOC 2 Type II "planned for 2026" / "Q4 2026 — In progress"; "GDPR Article 42" certification Q3 2027 (`trust/page.tsx:180`; `SECURITY_POLICY.md:845, 847`) — SOC 2 deferred since 2026-03-23 → "No SOC 2 audit has been performed and none is currently scheduled."
- Annual pen test, "Recent test: [Planned for Q2 2026]" (`SECURITY_POLICY.md:84, 611-619`); bug bounty "planned for Q4 2026"; PGP key "available at security.txt" (`VULNERABILITY_DISCLOSURE_POLICY.md:75, 84, 290, 301`) — none exist.
- Disclosure policy claims research is "Authorized under the CFAA … UK Computer Misuse Act … Exempt from DMCA §1201" (`VULNERABILITY_DISCLOSURE_POLICY.md:153-155`) → disclose.io safe-harbor wording ("we will not pursue claims…").
- PagerDuty/Datadog, 2-engineer on-call, 5-minute acknowledgement, status page, post-incident reports (`INCIDENT_RESPONSE_PLAN.md:120-143`; Security Policy) → founder best-effort, 15-minute uptime probe, Sentry.
- Terms .md "100% uptime (target: 99.9% monthly)" (`TERMS_OF_SERVICE.md:374`); BCP/DR "99.9% SLA", daily backups, 28-day retention, RPO 1 h / RTO 2 h, tested restores (`BUSINESS_CONTINUITY_DISASTER_RECOVERY.md:19-21, 57, 83-111, 179-183`); DR workflows query the Render Postgres API (`.github/workflows/dr-test-monthly.yml:57-58, 97-98`; `backup-integrity-check.yml:48-49`; Q1 DR evidence is a template) → "We rely on Neon point-in-time recovery (N days, verify); independent backups and restore testing are in progress (Sprint 778)."
- Audit logging: auth events kept 365 days in DB; tamper-evident HMAC chain (`AUDIT_LOGGING_POLICY.md:20, 76, 263-275, 301`) — auth events aren't stored (S5); the chain covers `ActivityLog` only, links across all users on write (`routes/activity.py:153-163`) but verifies per user (`shared/audit_chain.py:85-118`) so verification breaks when users interleave; NULL-hash rows skipped; admin audit log has no deletion guard (`main.py:149`); rows archived not deleted. → fix the chain bug (code) and describe it accurately.
- MFA required for production/admin, quarterly access reviews (`ACCESS_CONTROL_POLICY.md:21, 131-149`) — no in-app MFA; Q1 review is a draft → "MFA on infrastructure accounts (verify); in-app MFA planned."
- AES-256 on "Render managed PostgreSQL", verified monthly (`SECURITY_POLICY.md:31, 121, 127`) — Neon; verification file is an unfilled template.
- "Financial data breach is architecturally impossible"; "No admin override / god mode" — see A26.

**Options (CEO decision):** rewrite as short, honest solo-operator documents (recommended either way), and/or make the repository private (git history keeps the old text; private is the safer default before launch).

---

## Verify in console (CEO)
Legal entity type (LLC vs Inc.); Neon region and PITR window; Render service region; R2 lifecycle rule; Sentry DSN set in prod and its retention; whether Loki is enabled (Grafana Labs would be an unlisted processor); Render log retention; MFA on GitHub, Render, Vercel, Stripe, Sentry, Neon, Cloudflare, SendGrid; whether provider DPAs/SCCs were accepted; `JWT_EXPIRATION_MINUTES` and `TRUSTED_PROXY_IPS` on Render; TLS minimum on Vercel/Render; manual invoicing process; help@ / privacy@ / security@ mailboxes exist.
