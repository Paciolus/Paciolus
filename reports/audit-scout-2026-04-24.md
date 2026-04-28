# MarketScout Audit — 2026-04-24

**Persona:** External-perspective user advocate. Win condition: Time-to-Market.
**Scope:** Phase 3 (functional validation) → Phase 4.1 (Stripe live cutover) → Phase 4.5 launch announcement.
**Vantage point:** Non-technical CPA browsing https://paciolus.com cold, then signing up.

---

## TL;DR

Code is launch-ready. The risk is not engineering — it's marketing/reality drift introduced by Sprint 689g's "12 → 18 tools" bulk sed pass and a Phase 3 checklist that hasn't been updated to match the catalog the CEO is about to validate. Three small data-file fixes close the biggest credibility hole. After that, only Stripe live keys + legal sign-off stand between today and the launch announcement.

---

## 1. MVP Risk — what's delaying launch unnecessarily

### a. Sprint 715 SendGrid 403 root-cause investigation
**Market Value: Low | MVP Risk: NONE | User Persona Impact: zero pre-launch users affected**

Already correctly classified P2 in `tasks/todo.md`. The fix from Sprint 713 (catch the exception, log it) already prevents the user-facing crash. The remaining work is *observability investigation* — figuring out *which* recipients trigger the 403. This must NOT block launch. The trigger condition (CEO signal: warn-log count > 0 after 24h) is correct. **Keep deferred. Do not investigate pre-launch.**

### b. Sprint 689a–g full 12 → 18 tool expansion
**Market Value: High (already shipped) | MVP Risk: Done — but cleanup gap created | User Persona Impact: real (paid tier value prop is now bigger)**

Path B is already COMPLETE per `tasks/archive/sprints-611-714-details.md` and merged via PR #100 (`9cc3171a`). Backend `CANONICAL_TOOL_COUNT = 18`. Pricing/Terms/Footer/About/Demo/Register copy all flipped to "18 tools". CEO's instinct here was correct — 7 new tool surfaces with ~4,500 LoC of working backend already in production was too valuable to throw away.

**However**, the sed pass left two data files behind (see §3). This is the live-site credibility risk.

### c. Phase 4.4 backups (pg_dump cron to R2)
**Market Value: Med (insurance, not feature) | MVP Risk: Should not block launch | User Persona Impact: zero — invisible to users, important for CEO sleep**

Owner is "I" (Claude) — only needs CEO R2 token + IAM creation. Should land in parallel with 4.1, not after. Belt-and-suspenders on top of Neon PITR.

### d. Phase 5 Sentry alert rules + uptime monitor
**Market Value: Low pre-launch | MVP Risk: NONE | User Persona Impact: zero**

Correctly already in Phase 5. Keep there.

### e. SOC 2 deferrals (464, 466, 467, 468, 469)
**Market Value: Low until enterprise demand materializes | MVP Risk: NONE | User Persona Impact: zero — no SOC 2 references on website**

Correctly deferred. Confirm the CEO's 2026-04-24 directive to "schedule any deferred items that are free" only landed Sprint 716 (Loki) — the rest still cost money and stay deferred. **Keep deferred. Do not let SOC 2 scope creep back in.**

---

## 2. User Persona Impact per pending pipeline item

| Item | Helps the cold-CPA-signup persona? | Recommendation |
|---|---|---|
| Sprint 715 (SendGrid 403 RCA) | No — affects an unknown subset of email recipients on a path we can't identify yet | **Defer past launch.** Wait for production signal. |
| Phase 3 functional validation | **Yes — directly.** This is the gate that catches "user clicks button, nothing happens" | **Highest priority.** Update checklist (see §4 punch list). |
| Phase 4.1 Stripe live cutover | **Yes — directly.** This is the gate that turns on revenue | **Highest priority.** Already documented well in ceo-actions.md. |
| Phase 4.2 legal placeholders | **Yes — risk mitigation, regulatory** | **Highest priority.** Counsel sign-off is sequential. |
| Phase 4.3 custom domain | Helpful — `https://paciolus.com` already live for frontend; only `api.paciolus.com` left | Land it, but don't gate launch announcement on it (CORS update is a 5-min config) |
| Phase 4.4 backups | No — invisible to users | Land in parallel, not sequential |
| Phase 4.5 24h smoke test | Yes — final go/no-go | Required gate |

**Items with zero pre-launch persona impact:** Sprint 715. Defer.

---

## 3. Marketing vs Reality Gaps (LIVE PRODUCTION CREDIBILITY RISK)

This is the single largest issue I found. Sprint 689g's bulk sed pass ("12 → 18 tools") flipped the *prose copy* across 34 files but missed two data files. The result: live `https://paciolus.com` says "18 tools" in headers and renders 12 cards directly underneath. **A non-technical CPA who can count rows will spot this in 15 seconds.**

### Gap 1 — Homepage `<ToolLedger>` (highest visibility)
**File:** `D:\Dev\Paciolus\frontend\src\content\tool-ledger.ts`

- `CANONICAL_TOOL_COUNT = 12` (line 155) — backend was flipped to 18, frontend was missed
- `TOOL_LEDGER` array has 12 entries (line 39–148)
- Component header at `ToolLedger.tsx:69` reads **"Eighteen Tools · One Platform"**
- Component footer at `ToolLedger.tsx:101` reads **"{12} tools · every paid plan · every result cited"** (interpolates the constant)
- `ToolLedger.tsx:61` `aria-label="Twelve audit tools — catalog ledger"` (screen readers contradict the visible header)
- Comment at `tool-ledger.ts:25` literally says "When Sprint 689 reconciles the catalog … update this file" — Sprint 689 happened, file wasn't updated.

**Live on production homepage right now.** This is the fix that matters most.

### Gap 2 — `/demo` page
**File:** `D:\Dev\Paciolus\frontend\src\app\(marketing)\demo\page.tsx`

- Section header line 94: **"All eighteen tools included with every paid plan."**
- Section header line 91: **"The Complete Tool Suite"**
- `DEMO_TOOLS` array (line 33–46) has **12 entries** — same drift as ToolLedger.

### Gap 3 — `/tools` catalog page
**File:** `D:\Dev\Paciolus\frontend\src\app\tools\page.tsx`

- Line 6 docblock: "Browsable catalog of all 12+ diagnostic tools" (forgivable — that "+" is honest)
- `TOOLS` array has **26 entries** including 5 not in `tool-ledger.ts` and not in marketing copy: `composite_risk`, `account_risk_heatmap`, `flux_analysis`, `loan_amortization`, `depreciation`. Plus the 7 promoted tools from 689a–g.
- `ToolShowcase.tsx:136` `const TOTAL_COUNT = TOOLS.length` (= 12, since `ToolShowcase` uses a different separate list of 12)
- `ToolShowcase.tsx:139` filter button hard-coded label: `"All 18 tools"` while computed `TOTAL_COUNT = 12`. Mixed source-of-truth bug.

**The actual product surface is 26 routes.** The marketing claim is 18. The data files render 12. **Three different numbers visible on production simultaneously.**

### Recommended canonical answer
The cleanest story for a CPA is **"18 audit-grade tools, plus calculators."** That bins the situation honestly:
- 18 = the ones in `_ALL_TOOLS` of `entitlements.py` (the marketing claim Stripe is built around)
- The other 5 (heatmap, flux, loan, depreciation, composite-risk) are calculators / diagnostic adjuncts, mostly already entitled and shipped, but not the "audit testing" headline

Whatever the canonical answer is, **all three data sources need to converge on it before launch**.

---

## 4. Minimum Viable Pre-Launch Punch List

In strict order. Estimates assume a single focused session each.

### Pre-launch — must land before Phase 4.5 announcement

1. **HOTFIX: Reconcile tool-count drift** (~2h)
   - Update `frontend/src/content/tool-ledger.ts`: flip `CANONICAL_TOOL_COUNT = 18`, add 6 entries (multi-currency was 689a, the other 5 promoted tools should appear), update the docblock and the `aria-label`.
   - Update `frontend/src/app/(marketing)/demo/page.tsx`: `DEMO_TOOLS` array (add 6 entries) OR change copy to "All twelve testing tools demonstrated; six advanced tools available with every paid plan."
   - Update `frontend/src/components/marketing/ToolShowcase.tsx`: drop the hard-coded "All 18 tools" label or sync with TOOLS data.
   - Single `fix:` commit. No sprint number needed.

2. **Phase 3 checklist update** (~30 min)
   - `tasks/ceo-actions.md` line 55: change "12 testing tools" to match canonical answer + list the 7 promoted tools by name.
   - Add explicit Phase 3 sub-step: "Exercise the 7 newly-promoted tools (multi-currency, sod, intercompany, w2-reconciliation, form-1099, book-to-tax, cash-flow-projector). Each has a backend tier-gate retrofit that has unit-test coverage but has never been exercised by a real user clicking through the UI."
   - The CEO is about to do functional validation on a list that omits a third of the catalog.

3. **Phase 4.1 Stripe live cutover** (CEO calendar, ~2-4h)
   - Already excellently documented. No changes needed.

4. **Phase 4.2 legal sign-off** (CEO + counsel calendar, sequential blocker)
   - Cannot be parallelized.

5. **Phase 4.4 backups** (in parallel with 4.1, ~1h once R2 token is in hand)
   - R2 buckets already provisioned 2026-04-23. Just needs cron + IAM token.

6. **Phase 4.5 24h smoke test + announcement**

### Defer to Phase 5 / post-launch

- Sprint 715 SendGrid 403 RCA — defer to 24h post-launch as already planned
- Sentry alert rules — Phase 5
- Uptime monitor — Phase 5
- Any SOC 2 deferrals — keep deferred
- DMARC `p=quarantine` → `p=reject` — already on a 30-day natural cadence

**Cuttable from any pre-launch milestone:** anything not on lines 1–6 above.

---

## 5. Friction Points for a Cold CPA Signup

Walking the funnel as a non-technical 15-year-experienced auditor at a 12-person firm landing on `paciolus.com` from a Google search:

### Bounce risk: HIGH — homepage tool count contradiction
**Where:** Homepage `<ToolLedger>` (immediately below hero) — header says "Eighteen Tools" with 12 cards beneath.
**Why this matters for this persona:** CPAs *count things*. It's the job. A claim that doesn't tie out is a credibility hit before they even read the value prop.
**Fix:** Punch list item #1.

### Bounce risk: MED — `/demo` page same gap
**Where:** "All eighteen tools included with every paid plan" header over 12 cards.
**Why this matters:** Demo page is the natural second click after the homepage. Same mismatch reinforces "this team isn't detail-oriented" — which is the worst possible vibe to project to an auditor.
**Fix:** Punch list item #1.

### Bounce risk: MED — `/tools` catalog page docstring
**Where:** Comment in source code reads "all 12+ diagnostic tools" — not visible to users but speaks to internal source-of-truth confusion.
**Fix:** Punch list item #1 cleanup.

### Bounce risk: LOW — pricing page
The pricing page is in good shape. "All 18 diagnostic tools" claim, seat calculator works, FAQ is honest, 7-day trial is prominent, "no credit card required to start" is the right hook. **No friction here.**

### Bounce risk: LOW — register flow
"Seven-day trial. All eighteen tools. Raw financial files are never stored." — **excellent copy.** The Zero-Storage badge is a strong differentiator for a CPA worried about client confidentiality. No friction.

### Bounce risk: LOW — empty-state experience
Once registered, the dashboard / tools catalog likely renders the 26-tool list. CPAs are unlikely to bounce here — abundance is good — but they may be confused by which 18 are "the audit tools" and which 5 are "calculators". A category label cleanup on `/tools` would help (`Core Analysis | Testing Suite | Advanced` exists; promoting `Calculators` as a fourth category would clarify).

### Bounce risk: MED — first-tool flow on the 7 newly-promoted tools
**Where:** SoD / Intercompany / W-2 / 1099 / Book-to-Tax / Cash-Flow-Projector pages. Per Sprint 689g notes, these have backend tier-gate retrofits that were tested with unit tests but **never exercised end-to-end by a real CPA in production**.
**Why this matters:** A 403 / surprise paywall / parser failure on one of these tools is the kind of thing that gets caught only by Phase 3 functional validation. The current Phase 3 checklist (line 55 of ceo-actions.md) doesn't mention them by name, so they may get skipped.
**Fix:** Punch list item #2.

---

## Output Summary

| Item | Market Value | MVP Risk | User Persona Impact |
|---|---|---|---|
| Sprint 715 (SendGrid 403 RCA) | Low | None — already deferred correctly | Zero pre-launch |
| Sprint 689a–g (already DONE) | High | Done; cleanup gap remains | Real — bigger value prop |
| **Tool-count drift fix (NEW HOTFIX)** | **High** | **Pre-launch credibility risk** | **High — visible on production homepage today** |
| **Phase 3 checklist update (NEW HOTFIX)** | **High** | **Risk of skipping 7 untested tools** | **High — first paying users are the canaries otherwise** |
| Phase 4.1 Stripe live cutover | High | Sequential blocker | Real — turns on revenue |
| Phase 4.2 legal sign-off | High | Sequential blocker | Real — regulatory |
| Phase 4.3 custom domain (api subdomain) | Med | Not announcement-blocking | Cosmetic |
| Phase 4.4 backups | Med | Should run in parallel | Zero (insurance) |
| Phase 5 alerts + uptime | Low | None — Phase 5 | Zero pre-launch |
| SOC 2 deferrals | Low | None — deferred | Zero — no website refs |

---

## Final word

The CEO's instinct to ship 18 tools rather than 12 was the right call commercially. The execution missed two data files. Fix those two files, name-list the 7 promoted tools in the Phase 3 checklist, and the punch list to launch is just legal + Stripe live keys. The product is ready. The pipeline is ready. The marketing surface needs 2 hours of cleanup and then the launch story is internally consistent.

— MarketScout, 2026-04-24
