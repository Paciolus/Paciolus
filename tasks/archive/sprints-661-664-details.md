# Sprints 661–664 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-16.

---

### Sprint 661: Impersonation Token Expiry Asymmetry
**Status:** COMPLETE
**Source:** Critic — asymmetric revocation risk
**File:** `backend/security_middleware.py:841-869`, `backend/routes/internal_admin.py:357-421`, `backend/shared/impersonation_revocation.py` (new), `docs/04-compliance/SECURE_SDL_CHANGE_MANAGEMENT.md:246-265`, `backend/tests/test_impersonation_middleware.py:186-220`
**Problem:** `ImpersonationMiddleware` decodes impersonation JWTs with `verify_exp=False` so expired tokens continue to trigger the read-only 403. The 15-minute `jti` was issued but never registered in any revocation store — a leaked token's blocking behavior was effectively permanent with no server-side release path.
**Changes:**
- [x] `shared/impersonation_revocation.py` — Redis-first revocation store with per-process fallback, TTL clamped to ≤24h
- [x] Middleware: when `imp: true` token seen, check `is_revoked(jti)` and pass through on match
- [x] `POST /internal/admin/impersonate/stop` — admin submits the impersonation token, handler adds its `jti` to the store and writes `IMPERSONATION_END` to `admin_audit_logs`
- [x] SECURE_SDL §5.3 — new "Impersonation Token Semantics" section documents the asymmetric block, the revoke-stop flow, and the multi-worker Redis requirement
- [x] Test `test_revoked_imp_token_stops_blocking_mutations`: 403 before revoke, 200 after — full 10/10 suite green

**Review:**
- Cluster note in SECURE_SDL is load-bearing — the memory fallback only works for a single worker. Production (Render Standard) runs 2+ workers, so `REDIS_URL` must be set for revocation to behave correctly. The existing rate-limit strict-mode check already enforces Redis presence in prod, so this shares infrastructure rather than adding a second dependency.
- The stop endpoint decodes with `verify_exp=False` so an admin can explicitly close an already-expired session (e.g., forcing the audit record to be written even if the token aged out).
- TTL = `max(60, exp - now + 60)` — at least one minute, at most the token's remaining life plus a minute buffer, hard-capped at 24h inside the store.

---

### Sprint 662: Payroll Memo "Physical Existence" Language Reframe
**Status:** COMPLETE
**Source:** Accounting Auditor — assurance-adjacent procedure language
**File:** `backend/payroll_testing_memo_generator.py:386-394`, `backend/fixed_asset_testing_memo_generator.py:445-451`
**Problem:** `_DETAIL_PROCEDURES["PR-T9"]` directed the practitioner to "Confirm physical existence of employee" — field-audit imperative voice inside a diagnostic memo. Fixed-asset `duplicate_assets` procedure used similar "confirm physical existence of both" voice.
**Changes:**
- [x] PR-T9 rewritten as suggested procedure: the engagement team evaluates whether evidence supports a bona-fide employee, and physical verification is an auditor-judgment call based on engagement risk
- [x] Fixed-asset `duplicate_assets` rewritten in parallel — obtaining the asset tag to corroborate existence is now "a suggested procedure where engagement risk warrants"
- [x] Swept other memo generators — sampling-memo inventory-count voice is correctly auditor-directed (ISA 501 observation plan), left as-is

**Review:**
- The "must be performed by the engagement team directly and not delegated to management" phrasing stays — it's guidance on *how* to perform the procedure if chosen, not a directive that it must be performed.
- 34/34 payroll memo tests and 58/58 fixed-asset memo tests green without edits; the procedure text lives in private module dicts and is not asserted verbatim.

---

### Sprint 663: Anomaly Generator "Control Testing" Checkbox Reframe
**Status:** COMPLETE
**Source:** Accounting Auditor — platform-directed audit methodology implication
**File:** `backend/anomaly_summary_generator.py:625-644`
**Problem:** The per-anomaly response block offered a checkbox menu that included "Add control testing procedures" — the platform was effectively suggesting a methodology switch (substantive → control reliance) that is squarely auditor judgment.
**Changes:**
- [x] Replaced the 5-option checkbox block with a single free-text "Planned Response" field
- [x] Instructional italic text lists the common responses as *examples only*, explicitly noting that whether control testing is appropriate is auditor judgment and the platform does not direct methodology

**Review:**
- Column width, table style, and surrounding fields unchanged — this is purely a content swap inside the "Implication for Audit" row.
- 63/63 anomaly summary tests green; none asserted the checkbox strings.

---

### Sprint 664: accrual_completeness "Legal Counsel" Language Reframe
**Status:** COMPLETE
**Source:** Accounting Auditor — legal-adjacency risk
**File:** `backend/accrual_completeness_engine.py:477-502`, `backend/generate_sample_reports.py:3694,3716,3727`
**Problem:** `driver_source = "Requires legal counsel confirmation"` embedded a legal-requirement determination inside automated engine output. If a practitioner treated the platform's output as authoritative, it could create liability. Similar "Requires X" imperatives were peppered across the accrual driver classifier.
**Changes:**
- [x] Legal/litigation driver_source: "Legal obligations may be present — practitioner should evaluate whether legal confirmation is warranted"
- [x] Warranty, bonus/incentive, vacation/PTO, tax, insurance, interest: reframed as "Reasonableness typically relies on X — practitioner should evaluate whether X is available"
- [x] Sample-report fixture in `generate_sample_reports.py` updated to the matching strings so sample PDFs mirror production copy

**Review:**
- Pattern used consistently: acknowledge the data dependency + defer the judgment to the practitioner. No "Requires X" imperative voice remains in the accrual engine classifier.
- 74/74 accrual-completeness tests green without edits — assertions are on numeric behavior and account inclusion, not driver-source text.
