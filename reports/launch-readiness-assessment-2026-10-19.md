# Launch Readiness Assessment — Paciolus v2.1.0

**Date:** 2026-10-19
**Commit assessed:** `4a2586ff`
**Scope:** Accounting methodology, technical health, design system, security/resilience, revenue path, commercial validation — plus a sequenced launch plan.
**Basis:** Every status re-verified against current source. Findings in §E/§F derive from configuration and test code, not from a live Stripe or backup environment.
**Readable version:** https://claude.ai/code/artifact/694c6f26-1673-48ee-88d6-4f18c2803b82

> Not an audit opinion, assurance conclusion, or regulatory compliance determination.

---

## A. Verdict

**Engineering is not the blocker.** ~90,019 lines across 1,575 files; 8,700 backend tests at 93.33% coverage; 2,013 frontend tests; 24/24 CI gates; zero production CVEs as of today; design system adopted to zero violations. Two of the three accounting gaps a prior audit called engagement-blocking are now closed.

**Three things stand between the product and revenue, and only one is code:**
1. Billing has never been exercised end-to-end at current prices. Stripe test mode still sits at the previous price list and is documented as abandoned, so the first real-money charge is also the first live test of the billing path.
2. No off-provider database backup exists.
3. Legal placeholders remain unsigned.

**The unlisted gap is demand.** No artifact in 770+ sprints records a practising CPA, unaffiliated with the project, being asked to pay. The nightly lead scout returns zero leads across five themes. That is the largest unvalidated assumption in the system.

### Scorecard

| Dim | Area | Status |
|-----|------|--------|
| B | Accounting methodology | PARTIAL — guardrails strong; 4 workflow gaps open |
| C | Technical health | STRONG |
| D | Design system | STRONG — 150 → 0 generic colour tokens |
| E | Security & resilience | AT RISK — no off-provider backup; DR checks broken |
| F | Revenue path | UNPROVEN — nothing verifies price table against Stripe |
| G | Commercial validation | ABSENT |

---

## B. Accounting & audit methodology

Re-verification of the nine findings from `audit-accounting-methodology-2026-04-24.md`. **Two had closed since; one of my own initial readings was wrong and is corrected below.**

| Ref | Finding | Status | Evidence |
|-----|---------|--------|----------|
| B-1 | AS 1215 miscited as a JE Testing standard (ranked #1, priority 5.0) | **MOSTLY CLOSED** | Customer-facing surfaces now correct — Trust page cites AS 1215 for export signing; `standards-specimen.ts` explicitly labels it "not a procedure standard". `tests/test_citation_consistency.py` guards it. **Still wrong in 3 internal docs:** `docs/03-product/REPORT_STANDARDS_SPEC.md:440`, `docs/01-product/USER_PERSONAS.md:273`, `docs/02-technical/ARCHITECTURE.md:380`. |
| B-2 | PR-T12 / PR-T13 undocumented in payroll PDF memo | **CLOSED** | Both present in `payroll_testing_memo_generator.py`. |
| B-3 | Three boundary-language instances | **PARTIAL** | AR "understatement of credit loss" gone. 3WM "systemic review of procure-to-pay controls" survives in `generate_sample_reports.py:2266` (sample output). Risk-tier qualifier ("automated flag density — auditor judgment required") never added. |
| B-4 | No ISA 520 / AS 2305.10 expectation-formation workflow | **CLOSED** | Full stack: `analytical_expectations_manager.py`, `analytical_expectations_model.py`, `analytical_expectation_memo_generator.py`, `flux_engine.py`, `flux_expectations_memo.py`, `services/audit/flux/`. |
| B-5 | No ISA 450 Summary of Uncorrected Misstatements | **CLOSED** | `sum_schedule_memo_generator.py`, `uncorrected_misstatements_manager.py`, `uncorrected_misstatements_model.py`, with factual/judgmental/projected classification. |
| B-6 | Three-way match blind to service invoices (no two-way path) | **OPEN** | No two-way/service routing in `three_way_match_engine.py`. Systematically untested population in most commercial clients. |
| B-7 | No impairment-indicator screen (ASC 350 / IAS 36) | **OPEN** | No module. |
| B-8 | No judgmental-sample documentation path (ISA 530.A8) | **OPEN** | *Correction:* initial grep appeared to find this; hits were ISA 450 misstatement **classification** in the SUM generator — a different concept. Verified genuinely absent. |
| B-9 | No assertion-coverage worksheet | **OPEN** | No module. A CPA still cannot see which assertions a given account's procedures address. |

**Reading.** The two findings that made an engagement impossible to conclude (B-4, B-5) are both closed — the most significant product change since the pause. Boundary guardrails are defended at code level, not in prose: banned-phrase regex, structural ISA 265 prohibition, detection-risk disclaimers, and a mechanical test asserting "deficiency"/"material weakness" never appear in narratives. Shipped citation accuracy is sound. The four open items are **workflow completeness, not correctness** — and which of them matters is a question about users (§G), not standards.

---

## C. Technical health

| Measure | Now | Reading |
|---------|-----|---------|
| Backend tests | 8,700 / 0 fail | Green for the first time since 2026-05-31 (the long-red test was a wall-clock time bomb, not a regression) |
| Backend coverage | 93.33% | Flat and high |
| Frontend tests | 2,013 / 0 fail | 207 suites + Playwright E2E in CI |
| Frontend coverage | 50.08% lines | Up from ~37% plateau; still the weaker half |
| Scale | 90,019 lines | 54,565 backend / 798 files; 35,454 frontend / 777 files |
| CI gates | 24 / 24 | Python 3.11 + 3.12 + PostgreSQL 15, SAST, secrets scan, accounting-policy gate |
| mypy baseline | 1,011 | Baselined, systemic, not drifting |
| Architecture debt | 22 engines + 16 routes | Visible intake lane; most explicitly "keep flat" per ADR-018 |

**Singled out:** `billing/webhook_handler.py` is at **59.9% coverage with 174 uncovered statements**. The least-tested critical path is the one that moves money, and the webhook-coverage sprint has been deferred more than once. Address before the first live charge.

---

## D. Design & frontend

- **Oat & Obsidian migration complete:** 0 generic Tailwind colour tokens across 777 frontend files (prior review counted 150). Worth protecting with a lint rule so it cannot regress silently the way the citation drift did.
- Accessibility errors 51 → 0 in the same era; CSP nonce contract re-verified today through a Next.js 16.2.4 → 16.4.2 bump (all routes still `ƒ (Dynamic)`, `ƒ Proxy (Middleware)` active).
- **Funnel is well-designed.** Free tier = trial balance + flux analysis, view-only, 10 uploads/mo, 3 clients. Exports are the paywall — correct, since exports *are* the auditor's deliverable. A demo path with built-in sample data (`DemoZone.tsx`, `demoData.ts`) lets a CPA evaluate without uploading client data on first contact.

---

## E. Security & resilience

**Security: good**, and materially improved today — all six CVE/dependency gates pass, frontend production vulnerabilities 22 → 0, both rotted backend pins current. Auth carries HttpOnly cookie refresh, CSRF, account lockout, Argon2id passcode hashing, nonce-based CSP.

**Resilience: the weak flank.**
- **No off-provider database backup.** Phase 4.4 never implemented; `paciolus-backups` R2 bucket empty since provisioning in April. Neon PITR is the only thing behind customer data.
- **The checks that should have said so cannot run.** Repo has no secrets at all; both DR workflows query the *Render* Postgres API for a DB that has been on **Neon** since 2026-04-09. `DR Test (Monthly)` reports workflow success while its own internal verdict is FAIL. Filed as Sprint 778 (P1).
- **Nothing watched production for ~5.5 months.** Half-fixed: in-repo uptime check is live and CI-verified (probes readiness for 200 **and** a healthy body, since Sprint 774 reports `degraded` behind a 200). But GitHub disables cron workflows after ~60 days idle, so it switches itself off during exactly the quiet period it guards. **An external monitor is still required.**

---

## F. Revenue path

The canonical table in `backend/billing/price_config.py` holds correct current pricing in cents (Solo 10000/100000; Professional 50000/500000; Enterprise 100000/1000000; seats 6500/65000 Pro, 4500/45000 Ent) and `tests/test_pricing_launch_validation.py` carries ~20 assertions over it.

**But those assertions only check the table against itself.** No `stripe.` call, no `unit_amount` retrieval — nothing confirms the amount a customer is charged matches the amount the product intends and the page displays.

Not hypothetical: `tasks/pricing-launch-readiness.md:105` records that Stripe **test mode is still at v2 prices** (Solo $50 vs code/page $100) and is "treated as abandoned". So displayed and charged price already disagree in the only environment where billing has ever run. Live mode is to be built fresh — meaning **the first real card is also the first end-to-end test of current pricing**.

**Fix (~1h, before cutover):** a preflight that reads every `STRIPE_PRICE_*` object and asserts `unit_amount == TIER_PRICES[tier][interval]`, failing loudly on mismatch. Converts a silent mispricing risk into a startup error.

---

## G. Commercial validation — the gap nobody is tracking

Every launch gate in the project plan is engineering or compliance. None is a customer.

- Nightly lead scout: **zero leads across five themes**, for months.
- Phase 3 is defined as the CEO exercising the tools.
- `pricing-launch-readiness.md` carries a GO/NO-GO line awaiting the CEO's own signature.
- No artifact records an unaffiliated practising CPA being asked whether they would pay $100–$1,000/mo.

This is not a criticism of the build. It is that the riskiest assumption has never been tested, while far safer assumptions have been tested 10,713 times.

It also decides something concrete: **B-6 through B-9 are currently ranked by internal priority scores, which are guesses about user behaviour.** Five CPAs running their own TB through the free tier would replace four guesses with observations.

> **The single most important number not in this report:** the current `waitlist_signups` row count. Not readable from here (Neon). Check it before planning anything else.

---

## H. Launch plan

Sequenced so longest-lead and highest-risk items start first. H-1 and H-2 are the only hard blockers to accepting money safely. **H-3 should start today precisely because it finishes last.**

### H-1 — Prove you can be paid correctly (1–2 days)
1. Write the Stripe price-parity preflight **first**, before building live mode.
2. Build live-mode products/prices fresh at current pricing (4 products, 10 prices, 2 coupons). Do not mirror test mode.
3. Raise `billing/webhook_handler.py` off 59.9% — the deferred webhook sprint is now the gating one.
4. Run the Sprint 719 webhook preflight runner, then a real-money Solo monthly charge, then cancel + refund.
5. Archive abandoned test-mode prices so the two lists can never be confused again.

### H-2 — Survive losing the database (half a day)
1. Implement `pg_dump` → R2 cron into the bucket provisioned and empty since April.
2. Perform one real restore drill and record evidence. An untested backup is not a backup.
3. Repoint both DR workflows at Neon + R2; fix the false-green so exit status reflects the job's own verdict.

### H-3 — Start the legal clock, today (external lead time)
1. Send Terms + Privacy to counsel with registered address, agent, and EU-representative decisions resolved.
2. Add the emergency contact number to Security Policy §12.

*Zero engineering dependency and the longest wait of anything here. Every day unsent is a day added to launch.*

### H-4 — Put it in front of five CPAs (in parallel, now)
1. Check the waitlist count. If people are already waiting, start there.
2. Get 5–10 practising CPAs through the demo and free tier on their own TB. Watch where they stall; do not guide them.
3. Ask the price question directly and early.
4. Let the result rank B-6 through B-9. Build the one they actually hit.

### H-5 — Go live (half a day + 24h watch)
1. Custom API domain, DNS, TLS, CORS origin update (`api.paciolus.com` currently 404s).
2. Stand up the external uptime monitor; add `RENDER_API_KEY` so deploy-drift detection arms.
3. Clean-browser run: register → verify → subscribe on a live card → upload → generate memo → cancel → refund.
4. Watch Sentry + Render logs + Stripe webhooks 24h. Then announce.

### Explicitly not in the launch path
B-6 through B-9; the 22-engine relocation; the mypy baseline; the remaining 23 open PRs; dev-only npm advisories. All real; none should delay a first customer. The three internal docs still miscit­ing AS 1215 are a ten-minute fix worth doing because the customer-facing version of that error was ranked the most dangerous finding in the system.

---

## I. Decisions required from the CEO

1. **Is Neon PITR sufficient for launch, or is the off-provider backup a prerequisite?** Either answer is defensible; it needs to be written down rather than left as an unimplemented phase.
2. **How hard is the launch date?** If soft, H-4 should gate H-1 — no point perfecting billing for a price nobody has agreed to. If hard, run them in parallel.
3. **Who reviews code?** Branch protection requires an approving review and GitHub forbids self-approval, so every merge needs an admin bypass. Workable solo, but the review gate is currently decorative — accept explicitly or drop it to zero.
4. **Does the API description still reading "12-Tool Audit Intelligence Suite" get corrected to 18?** Copy decision.

---

*Prepared by Claude Opus 5 · 2026-10-19 · basis: direct code and production verification.*
