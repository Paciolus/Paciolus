# Agent Sweep — Consolidated Punch List (2026-04-24)

8 agents dispatched in parallel while CEO ran Phase 3. This is the synthesis.

**Source reports** (all in `reports/`):
- `audit-project-auditor-2026-04-24.md` — Project Auditor (workflow health: **4.9 / 5.0 🟢**)
- `audit-security-2026-04-24.md` — Security review (0 Critical / 1 High / 3 Medium / 3 Low / 2 Info)
- `audit-critic-2026-04-24.md` — BackendCritic (portfolio: **paying debt down**)
- `audit-scout-2026-04-24.md` — MarketScout (launch-blocker findings)
- `audit-guardian-2026-04-24.md` — QualityGuardian (failure-mode audit)
- `audit-accounting-methodology-2026-04-24.md` — Accounting methodology gaps
- `audit-hallucination-2026-04-24.md` — Copy/doc drift (4 Critical / 10 Medium / 5 Low)
- `audit-deadcode-2026-04-24.md` — Dead-code sweep (essentially clean)

**Cross-checks performed before publishing:**
- Sprint 689a–g landed (commit `9cc3171a`, PR #100) → tool-count drift is real
- `routes/bulk_upload.py:37` module-global → confirmed
- `billing/webhook_handler.py:978` off-by-one → confirmed (judgment call, not bug)

---

## Tier 1 — Fix BEFORE Stripe live cutover (Phase 4.1)

These are the items where independent agents converge or where the production blast radius is high enough to block the next gate.

### 1.1  Tool-count drift on production marketing/legal surfaces — 🔴 customer-visible
**Confirmed by Scout + Hallucination Audit + cross-check.** Sprint 689a–g landed but the marketing/legal/checklist flip is half-done.

| File | Line | Wrong | Right |
|---|---|---|---|
| `frontend/src/components/marketing/ToolLedger.tsx` | 69 | "Eighteen Tools · One Platform" header | renders 12 cards underneath |
| `frontend/src/content/tool-ledger.ts` | 155 | `CANONICAL_TOOL_COUNT = 12` runtime assert | should be 18 |
| `frontend/src/app/(marketing)/pricing/page.tsx` | 381, 402, 482, 608 | "All 18 diagnostic tools" | catalog still 12 |
| `frontend/src/app/(marketing)/terms/page.tsx` | 616, 621, 626 | "18 tools" — **legal surface** | catalog still 12 |
| `frontend/src/app/tools/page.tsx` | 47-52 | Test counts: AP=13, Rev=16, AR=11, Pay=11, FA=9, Inv=9 | Actual: 14, 18, 12, 13, 11, 10 |
| `frontend/src/components/marketing/BottomProof.tsx` | 35, 38, 69 | Three different tool numbers in one component | Pick one |
| `frontend/src/app/(marketing)/demo/page.tsx` | — | Same 12/18 mismatch | Aligned with ToolLedger |
| `frontend/src/components/marketing/ToolShowcase.tsx` | — | Same 12/18 mismatch | Aligned |
| `tasks/ceo-actions.md` | 55 | "12 testing tools" Phase 3 checklist | 18 tools — missing 7 newly-promoted from CEO walkthrough |
| `CLAUDE.md` | "Key Capabilities" | Test counts and tool count | Sync |
| `memory/MEMORY.md` | Project Status | "Sprint 689 Path B locked … pre-requisite" | "Sprint 689a–g landed `9cc3171a`" |

**Fix:** ~2-3h coordinated find-replace. Bump `CANONICAL_TOOL_COUNT`, refresh test counts, regenerate `tool-ledger.ts` data, sync protocol docs, update Phase 3 checklist with the 7 new tool names.
**Why this can't wait:** Stripe live-mode customers will see contradictions on pricing/ToS pages.

### 1.2  AS 1215 fabricated citation across 5 customer-facing files
**Confirmed by Hallucination Audit + Accounting Methodology Audit.** Backend memos are clean, but the public-facing claim is wrong.

PCAOB AS 1215 is *Audit Documentation*; the correct standard for JE Testing is **AS 2401** (Consideration of Fraud). Files:
- `CLAUDE.md` — Key Capabilities (private; sets agent context)
- `features/status.json`
- `docs/07-user-facing/USER_GUIDE.md`
- `frontend/src/content/standards-specimen.ts`
- `frontend/src/app/(marketing)/trust/page.tsx` ← **highest risk; PCAOB-registered firms read this**

**Fix:** Multi-file find/replace `AS 1215` → `AS 2401` (verify each occurrence in context — a few may legitimately reference workpaper-retention rules, in which case AS 1215 is correct there). ~30 min.

### 1.3  CSRF user-binding silently disabled for browser cookie auth — 🔐 H-01
**Security Review.** `backend/security_middleware.py:485-509` (`_extract_user_id_from_auth`) only reads `Authorization: Bearer`. Production browser path uses HttpOnly cookies → `expected_user_id=None` → CSRF binding short-circuits at line 427 → leaked CSRF token is replayable for any user for 30 min.

**Fix:** Read `ACCESS_COOKIE_NAME` cookie when no Bearer header present. ~1h.
**Why this can't wait:** Stripe live mode means real-money POSTs are about to fly through this code path.

### 1.4  Bulk upload broken on multi-worker Render — 🚧 production bug
**Guardian (cross-checked).** `_bulk_jobs` is a module-global `OrderedDict` at `backend/routes/bulk_upload.py:37`. POST hits Worker A; status poll hits Worker B → 404. `asyncio.create_task` is also fire-and-forget, lost on worker recycle.

**Fix options (pick one):**
- **(A)** Migrate job state to Postgres (job + per-file status rows).
- **(B)** Document Enterprise tier as "single-worker only" + set `Render: numInstances=1, gunicorn workers=1` via env. Quick mitigation, defers proper fix.
**Why this can't wait:** CEO is about to test bulk upload in Phase 3; this WILL fail. Either fix or skip the Phase 3 step until fix lands.

### 1.5  Stripe webhook secret-mismatch is silent — operational hazard for Phase 4.1
**Guardian.** If the test-mode webhook secret gets pasted into live env vars, every webhook returns 400 silently. Customers won't appear in admin dashboard, churn doesn't downgrade, dispute events miss SLA.

**Fix:** Add to Phase 4.1 checklist:
- Mandatory `stripe trigger checkout.session.completed --api-key <live>` test event before real-money smoke
- Sentry alert on log message `Webhook signature verification failed`
- 24h rolling 4xx-rate alert on `/billing/webhook` at >5%

~30 min checklist edit + Sentry alert config.

### 1.6  Off-by-one in stale-event guard — 🐞 ambiguous-time edge case
**Guardian (cross-checked at `backend/billing/webhook_handler.py:978`).** `if event_time < sub_updated:` — equal-time events bypass the staleness guard. Probability is low but non-zero on second-precision Stripe timestamps.

**Fix:** Change to `<=` and add fixture replay test for equal-time. ~10 min.

---

## Tier 2 — Fix BEFORE first paying customer hits 18 memos / engagement layer

### 2.1  18-memo back-to-back OOM risk
**Guardian.** ReportLab + openpyxl accumulate in RAM on Render Standard 2 GB. CEO running all 18 memos consecutively in Phase 3 will hit it.

**Fix:** Add `gc.collect()` between memo generations + Render `maxRequestsPerWorker` recycling. ~1h.

### 2.2  PR-T12 / PR-T13 missing from payroll memo `PAYROLL_TEST_DESCRIPTIONS`
**Accounting Methodology Audit.** Payroll engine ships 13 tests; memo only documents T1–T11. Findings on T12 (Duplicate Names ghost-employee) and T13 (Gross-to-Net Reconciliation) appear in tool output without methodology workpaper entry.

**Fix:** Two-line add to `payroll_testing_memo_generator.py` `PAYROLL_TEST_DESCRIPTIONS`. ~10 min.

### 2.3  ISA 265 boundary language in two memos
**Accounting Methodology Audit.**
- `three_way_match_memo_generator.py` — "systemic review of procure-to-pay controls recommended" near deficiency-classification line.
- `ar_aging_memo_generator.py` — "potential understatement of credit loss expense" is a misstatement conclusion.

**Fix:** Rephrase to anomaly-indicator language. Existing `BANNED_PATTERNS` regex catches the hard cases; soften these. ~30 min.

### 2.4  Per-IP failure tracker is in-memory only — M-03
**Security Review.** `backend/security_middleware.py:619-674` `_ip_failure_tracker` is a process-local `dict`. Not cross-worker, resets on deploy. Attackers time credential-stuffing to deploy windows. Per-account DB lockout still holds; only the per-IP layer (Sprint 698) is degraded.

**Fix:** Move to Redis using existing slowapi storage URI. ~1.5h.

### 2.5  Share endpoint leaks existence of passcode-protected shares — M-02
**Security Review.** `backend/routes/export_sharing.py:471-481` returns 403 with "requires a passcode" for protected shares vs 404 for unknown — token-existence enumeration.

**Fix:** Collapse 403 path to 404. ~15 min.

### 2.6  Export-share passcode lockout has no admin unlock
**Guardian.** If CEO triggers per-IP throttle during Phase 3 export-sharing testing, no recovery path exists.

**Fix:** Add a CEO-only `/admin/unlock-passcode-throttle` endpoint, OR grant CEO IP a bypass for the throttle. ~30 min.

---

## Tier 3 — Pre-Sprint-689-aware cleanup (architectural)

### 3.1  AuditEngineBase only adopted by 3 of 12 testing engines — 🏗️ Critic Veto 8/10
**BackendCritic.** `engine_framework.py` defines a 10-step pipeline ABC; only JE/AP/Payroll subclass it. The other 9 (Revenue 2,509 LoC, AR 2,179, FA 1,666, Inventory 1,534, 3-way match 1,476, accrual completeness, population profile, sampling, cash flow projector) re-implement the pipeline procedurally.

**Note:** Critic flagged this as "before Sprint 689 lands." 689 already shipped, so this is now retrospective consolidation work.

**Fix:** Convert one engine per sprint. Sequence: Revenue → AR → FA → Inventory → 3-way → remaining 4. ~2-3 sprints.

### 3.2  `shared/helpers.py` re-export shim still owns the call graph — Critic 7/10
**BackendCritic.** Module was decomposed 2026-04-20 but re-exports 35+ symbols (incl. private `_XLS_MAGIC`, `_parse_csv`, `_log_tool_activity`). 62 call sites use the shim vs 6 direct.

**Fix:** Sweep call sites, update imports, delete shim. ~3h.

### 3.3  `routes/export_diagnostics.py` (689 LoC) has 7 copy-pasted CSV endpoints — Critic 7/10
**BackendCritic.** Sister `routes/export_testing.py` already collapsed the same pattern via `csv_export_handler()` (Sprints 218-219). Diagnostics didn't get the same treatment.

**Fix:** Apply `csv_export_handler()` pattern. ~2h.

### 3.4  Webhook handler at 57.4% coverage
**Guardian.** Dispute (`charge.dispute.created`/`closed`), proration, tier upgrade/downgrade, and the off-by-one above are all in uncovered paths. Live mode WILL fire dispute events.

**Fix:** Fixture-replay tests targeting 80% of `backend/billing/webhook_handler.py`. ~4h.

### 3.5  `workbook_inspector.py` at 18.6% coverage — first-touch on every upload
**Guardian.** Password-protected xlsx, malformed ods, XML bombs hit unexercised exception paths. CEO uploading real client TBs in Phase 3 will surface edge cases.

**Fix:** Adversarial-fixture corpus + parametrized tests. ~3h.

---

## Tier 4 — Methodology gaps (post-launch product roadmap)

### 4.1  No ISA 520 expectation-formation workflow
**Accounting Methodology Audit.** Analytical tools (flux, ratio, multi-period) produce observed-vs-prior comparisons but no structured expectation with stated precision and corroboration basis. Required by ISA 520.5(a) / AS 2305.10 when analytics are a primary substantive procedure.

**Why this matters post-launch:** No competing tool addresses this. Product-differentiation opportunity. Likely a Sprint 720+ feature.

### 4.2  No Summary of Uncorrected Misstatements (SUM) schedule
**Accounting Methodology Audit.** Required by ISA 450 / AU-C 450 to consolidate passed adjustments + sample-projected misstatements + aggregate vs materiality. Platform has adjusting entries (approval-gated) and sampling UEL output, but no consolidation surface.

**Why this matters post-launch:** Every CPA completing an engagement will reach for this and find nothing. Engagement layer feature.

---

## Tier 5 — Operational / monitoring (Phase 5 polish)

- **Redis (Upstash) blip → slowapi fail-open.** Add `/health` Redis ping + Sentry alert on RedisStorage exceptions.
- **R2 regional outage → mass 410s look like permanent data loss.** Distinguish transient 5xx (→ 503) from permanent 404 (→ 410) in `export_share_storage.download()`. Add `/health/r2` sentinel GET.
- **Sprint Shepherd YELLOW false-positive.** Today's risk signal was a hotfix description containing the literal substring "TODO." Fix the regex.
- **Two security-relevant patches available.** fastapi 0.136.0 → 0.136.1 (patch), stripe 15.0.1 → 15.1.0 (minor). Roll into next dep-hygiene hotfix.
- **Project Auditor's "consolidate verify-against-live lessons":** Three near-duplicate lessons in 24h. Roll up into one canonical "Trust the live system over the documented contract" lesson + 4-line sprint-close checklist.

---

## Tier 6 — Confirmed clean (no action needed)

- Stripe webhook signature verification + atomic dedup ✓
- Upload pipeline 10-step defense (archive-bomb scan, defusedxml on OFX, formula-injection sanitization) ✓
- Argon2id passcode KDF (OWASP 2024) ✓
- No hardcoded secrets, no `dangerouslySetInnerHTML`, no f-string SQL ✓
- Refresh-token atomic CAS for race safety ✓
- 0 TODO/FIXME/HACK markers in source ✓
- 0 confirmed unused Python symbols, 0 orphan React components, 0 orphan migrations ✓
- 205 type suppressions all in legitimate complexity zones ✓
- Backend memo citations (PCAOB AS 2401/2501/2305/2310, ISA 240/315/320/450/505/520/530/540/570/580, ASC 606-10) all verified accurate ✓
- 18 memo PDF endpoints, 9 CSV testing exports, 6 benchmark industries, JE 19 / AR 12 / FA 11 / Inv 10 counts all verified ✓
- 20 sampled hotfix SHAs in `tasks/todo.md` all resolve in `git log` ✓

---

## Recommended sequencing

| When | Items | Effort |
|---|---|---|
| **Today (during Phase 3)** | 1.1 tool-count drift, 1.2 AS 1215, 1.3 CSRF binding, 1.4 bulk-upload (defer or quick-fix), 1.5 webhook-secret checklist, 1.6 off-by-one | ~5h |
| **Before Stripe live cutover** | 2.5 share-endpoint enumeration, 2.6 admin unlock, 2.4 Redis IP tracker | ~2h |
| **First week post-launch** | 2.1 OOM mitigation, 2.2 PR-T12/T13 memo, 2.3 ISA 265 phrasing, Tier 5 operational polish | ~3h |
| **Sprint 717+** | Tier 3 architectural cleanup (AuditEngineBase, helpers shim, export_diagnostics) | 2-3 sprints |
| **Sprint 720+** | Tier 4 methodology gaps (ISA 520 expectations, SUM schedule) | feature-sized |

---

*Generated 2026-04-24 by IntegratorLead synthesis of 8-agent parallel sweep.*
