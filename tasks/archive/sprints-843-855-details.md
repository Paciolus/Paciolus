# Sprints 843–855 Details

> Archived from `tasks/todo.md` Active Phase on 2026-11-14.

---

### Sprint 854: Nightly environment parity
**Status:** COMPLETE 2026-10-28. **Priority:** P1 (Phase 0). **Source:** 2026-10-28 council (Guardian, Critic).

The 2026-10-28 nightly went RED with no defect in the code. `backend/venv` still has fastapi 0.136.1, but Sprint 786
moved `requirements.txt` to `fastapi==0.162.0`, so `tests/helpers/route_inventory.py:22` (`RouteContext`) fails to
import → 99 collection errors in Coverage Sentinel. QA Warden crashed separately on the Jest side.

- [x] Orchestrator **syncs the venv from `requirements.txt` before every run** (`pip install -r`), not a one-off rebuild —
      a hand rebuild rots again (Sprint 786 already flagged this venv as matching neither the pins nor production).
- [x] Pre-flight: fail the nightly RED with a named reason if installed versions still differ from the `==` pins after the sync.
- [x] `scripts/overnight/agents/qa_warden.py:185` — `json.loads(stdout)` with `None` → report "did not run", not a TypeError.
- [x] **Did-it-run check:** an agent whose sentinel is missing or crashed fails the brief visibly (only 43 of 109
      dormant-period nights produced a qa_warden sentinel and nobody noticed).
- [x] The daily brief states the SHA and timestamp it tested, as-of its run time (the 10-28 brief's `a9dfeb69` was
      HEAD at 04:00 — the defect is unstated staleness, not a wrong SHA).
- [x] Report Auditor on 0/0 tests reports **UNVERIFIED**, not GREEN.

**Verification:** `python -m pytest scripts/overnight/tests/` 75 passed (39 new in `test_env_parity.py`); `backend/tests/test_briefing_sha_stamp.py` 8 passed; ruff clean on new/changed lines; live pre-flight against a worktree venv GREEN (17/17 `==` pins, sync 2.5s) and RED with a named reason on a bad path. Jest root cause: `text=True` decoded with cp1252, Jest's `●` (E2 97 8F) killed the reader thread so `stdout` was None (reproduced in-test); fixed with `encoding="utf-8"` + `--outputFile`.

**Commit SHA:** TBD.


---

### Sprint 855: Tool-correctness loose ends from Sprints 826/827 (was PR #254's duplicate "Sprint 846")
**Status:** COMPLETE (2026-10-26), PENDING merge — PR #254. Built 2026-10-26 as a second "Sprint 846" (846 is the merged
memo-markup sprint `826ef50f`); renumbered 855 on 2026-10-29 — commit messages, code comments, `test_sprint_855_*.py`.
**Priority:** P2 (Phase 1).
**Scope:** every open 826/827 item that needs no practitioner figure, CEO policy call or locale decision
(register: `reports/sprint-823-discovery-2026-10-23.md`). Reproduce each before fixing.
Out of scope, unchanged: F5 + figures (793b), B1 (NOL scope), B2 (combined-rate method), D2 tiering of
degenerate custom rules, A6 FA-03 contra call, P-3 locale, I4 investment/payable pairing.

- [x] **A4** — `parse_date` gains opt-in `day_first`; `infer_day_first` decides per column (day-first only
      when some value can only be day-first and none only month-first). FA-07 and FA-T11 read through it.
- [x] **A5** — FA-T11 computes expected depreciation by actual days *and* under half-year (fiscal year ends on
      the reference date's month/day), flags against the nearer, and reports which matched. The comment that
      claimed the 5% tolerance absorbed the convention was false and is gone. Mid-quarter/mid-month: not modelled.
- [x] **A8** — useful-life headers naming months (months/mos/mths) are divided by 12, mapped headers included.
- [x] **C2** — AP a scenario leaves unpaid is paid evenly over the 30 days after its bucket window
      (`AP_DEFERRAL_DAYS`), disclosed per scenario as `ap_deferral_rule` (shown on the scenario card).
- [x] **C3** — each displayed component is the change in its rounded running total, so every row foots.
- [x] **C5** — a negative aging bucket is a 400 (a credit has no payment date to schedule); it used to be
      netted in the total but ignored by the projection. **C6** — an overdrawn opening balance is projected.
- [x] **W4** — the 941 sum is compared with the W-3 as well as payroll YTD (`compared_with`); 941 fields are
      optional, and a figure not supplied every quarter is skipped with a `checks_not_run` notice (also ends the
      false HIGH when a 941 CSV had no Medicare column). **W8** — no drafts → `w3_totals: null` + `w3_status`.
      **W9** — missing/duplicate 941 quarters listed; the annual tie-out is then not run, and says so.
- [x] **I5** — debit/credit accept `(1,000.00)`, `$(1,000.00)`, `1000-` via `shared/request_decimal.parse_request_amount`
      (unparseable is still a 400, never a silent zero); a negative debit becomes a credit (and vice versa), which
      fixes the worksheet column totals (net matching was already right).

**Existing tests changed (each asserted the defect):** `test_negative_opening_balance_rejected` (C6),
`test_941_totals_diverging_flags_high_severity` (supplied Q1 only — the W9 defect).
**Verification:** frontend build + 2,078 Jest pass; full backend suite 10,006 passed, 0 failed (2026-10-26).

- [x] Renumber PR #254's commits, comments and test files from 846 to 855.
- [x] Rebase onto the 843 → 844 → 845 stack (2026-10-29, after the 843 banned-phrase gate).
- [ ] Retitle PR #254; merge after #237; full backend suite on the merged result.

**Commit SHA:** TBD.


---

### Sprint 843: Professional positioning, memo wording and disclaimers
**Status:** COMPLETE 2026-10-24. **Priority:** P1. **Source:** report Part 4 (H1–H13, M1–M12, L1–L10, disclaimer set).

- [x] Homepage hero (H1 "Diagnostics in Seconds. Your Judgment, Better Informed."; H2), WelcomeModal (H3; also its
      "12 tools / 19 fraud indicators" → 18 tools / 19 tests), demo memo card + AS 1215 badge → "PDF" (H4), About
      (H5, M5, L9), feature pillars (H6), M4 ("Every test names the rule it applies, or says when a threshold is our
      own convention" on EvidenceBand, BottomProof, demo). M6 was done in 841.
- [x] H7: nine tool-page hero badges → "References …" ("Bank-to-book matching" for bank rec); tools index references
      stripped of descriptive claims ("ISA 500 External Confirmation" was wrong for bank rec); demo strip.
- [x] Memo cover (H8): "Prepared by / Reviewer / Status (entered by user)" + the standard cover line; input labels say
      "(shown on the memo cover)", no "Jane Smith, CPA" placeholder. "Conclusion" → "Summary of Results" in the shared
      template and bank rec, TWM, currency, multi-period, preflight (H9); fallback text says "flag-density indicator
      … not a risk assessment". Bank rec / TWM low-tier "immaterial / satisfactory" removed (H10). TB report: "Diagnostic
      Score", "Items Flagged", "Above / Below Materiality", "No items exceeded the configured thresholds" (H11). Memo
      footer is the standard memo footer (M1). Sampling: PASS/FAIL → "UEL ≤ TM" / "UEL > TM", "Evaluation Result",
      "Suggested close-out steps" (M2). Demo PASS chips gone, "Low flag density — N items flagged" (M3). The flux
      memo keeps its "Conclusion:" field — that one is the auditor's own written conclusion.
- [x] H12 relabelled: the 4×4 RMM table is a **Paciolus convention**; ISA 315 (Revised 2019) requires separate IR/CR
      assessment and prescribes no matrix (its Appendix 1 is about understanding the entity). Engine disclaimer,
      docstrings, standards registry usage, specimen, pages, CLAUDE.md, and a new `methodology-sources.ts` rule.
      **CEO: confirm against your copy of ISA 315** — removing the attribution is the safe direction either way.
- [x] H13: "Form 1099 Preparation" → "1099 Vendor Threshold Review" across registry, taxonomy, workpaper index,
      ledger, pages, toolbar, command palette, methodology, docs and tests.
- [x] M7 "detection" → "indicators" / "patterns associated with fraud schemes"; M8 tax disclaimer on 1099, W-2,
      Book-to-Tax, Depreciation and Loan Amortization; M9 USER_GUIDE "compliant", "client-ready", "Guarantees";
      M11 independence note on intercompany, adjusting entries, financial statements (book-to-tax via the tax text).
- [x] Standard disclaimer set in `frontend/src/content/disclaimers.ts`: site footer, every tool page (inside
      `DisclaimerBox`, above the tool's own text), tax tools; memo cover + footer in the backend.
- [x] L1 test counts derived (`testCountFor()` on six tool pages and practice settings, demo, hero); L3/L7 hero
      animation copy; L4 → "6 Standard-Setters Cited" (pinned to the registry); L5 naming (`main.py`, email footer,
      memo footer; about/approach meta in 841); L10 memo title "(ref. ISA 520)". M12 (CPA advertising) is counsel's.
- [x] **Merge gate (2026-10-28 plan):** a banned-phrase test across **every** memo generator ("we conclude", "appears
      sound", "satisfactory", a "Conclusion" heading, …), generalising `test_multi_period_memo.py:875-890`, lands in
      #235 **before** it merges. Re-locate H10 by symbol: bank-rec is now near `bank_reconciliation_memo_generator.py:945`
      (the claims review cites `:985`), TWM near `three_way_match_memo_generator.py:109`.
      **Done 2026-10-29:** `tests/test_memo_banned_phrases.py` scans (1) the rendered text of all 48 memo snapshots
      (held to live output by `test_memo_render_equivalence.py`) and (2) every non-docstring string literal in every
      discovered `*memo*.py` generator plus `shared/memo_base.py` / `memo_template.py`. It caught one survivor of M2:
      sampling's two-sided notes said "The conclusion is a fail if …" → "The result is UEL > TM if …". H10 confirmed:
      no bank-rec / TWM "satisfactory" remains.

**Commit SHA:** TBD.


---

### Sprint 844: Privacy promises and legal-page accuracy (account deletion feature)
**Status:** COMPLETE 2026-10-24. **Priority:** P1. **Source:** report Part 5. Counsel reviews the finished pages at website-final.

- [x] **Built** self-service deletion + data export (`services/account_erasure.py`): `POST /auth/account/delete`
      (password + typing DELETE) hard-deletes the user, clients, engagements, expectations, misstatements, follow-ups
      and comments, tool runs, summaries, activity logs, sessions, tokens, shares (R2 objects first) and the
      subscription (Stripe cancelled first; a provider failure deletes nothing). Billing history kept with the user
      unlinked; a security-log row records the erasure. Refused (409) for superadmins, owners of orgs that still have
      members, and authors of entries inside someone else's engagement. `GET /auth/account/export` returns JSON of
      everything stored (no password hashes or token material). Superadmin `POST /internal/admin/users/{id}/erase`
      (audit-logged; migration `b9d3f6a2c418` adds `ACCOUNT_ERASED`) honours emailed requests and terminations with
      the same code. Settings → Profile → Your Data has both controls. The no-hard-delete policy exempts exactly this
      module, with the justification in `accounting_policy.toml`.
- [x] Privacy: deletion section describes the real feature + what is kept; "clear history" disclosed as archival;
      DPO → "Privacy Contact"; processors (Vercel, Render, Render Key Value, Neon, Cloudflare R2, Stripe, SendGrid,
      Sentry) and regions (Neon us-east-1; Render/Vercel Virginia); "SCCs" → provider's standard terms; access right
      points at the export; CPRA rights added; analytics claims (session duration, screen resolution) removed.
- [x] Checkout DPA checkbox removed (it linked to a page calling the DPA "planned"); replaced with "request one".
      Trust: GDPR/CCPA "2024" and DPA "2025" years removed; SOC 2 "No audit performed or scheduled".
- [x] Website Terms/Privacy authoritative: the markdown copies moved to `docs/04-compliance/archive/` and replaced by
      pointers (they had drifted on dates, arbitration body, refunds, seat caps, CCPA days, "[State]", placeholders,
      non-existent /history routes).
- [x] Breach notice "without undue delay, and regulators as the law requires"; Terms service description (18 tools,
      10 formats); termination wording covers summaries and engagement entries.
- [x] Trust security claims: 15-minute tokens, "5 attempts, 15 minutes", rate limits on every route, app-level account
      scoping (no RLS claim), TLS 1.2+, "released from memory", optional sign-off block, monitoring = Sentry + 15-minute
      uptime probe + no 24/7 on-call. (Share-link exception and "enterprise-grade" were done in 841.)
- **Open — CEO:** legal entity (Paciolus LLC on Privacy vs Paciolus, Inc. on Terms and footer) is still unresolved and
      deliberately not guessed. Provider DPAs / regions are stated as engineering understands them — verify in the
      consoles (report "Verify in console").
- **Left for 845:** provider lists inside `SUBPROCESSOR_LIST.md`, `DATA_PROCESSING_ADDENDUM.md`, `SECURITY_POLICY.md`
      (those documents are rewritten there).

**Commit SHA:** TBD.


---

### Sprint 845: Honest compliance documents (the repo is public)
**Status:** COMPLETE 2026-10-24. **Priority:** P1. **Source:** report Part 6.

- [x] `docs/04-compliance/` rewritten as short, accurate solo-operator documents (Security Policy 3.0, Data Handling
      Architecture 3.0, Subprocessor List 2.0, Incident Response 2.0, BCP/DR 2.0, Access Control 2.0, Secure SDL 2.0,
      VDP 2.0, Audit Logging 2.0, DPA 2.0-draft). Each opens with what the old version claimed that was false. SOC 2:
      "none performed or scheduled"; no pen test / bug bounty / PGP; disclose.io-style safe harbor instead of
      CFAA/CMA/DMCA "authorization"; incidents = founder best-effort + 15-minute probe + Sentry, no on-call; BCP/DR =
      Neon PITR only, no SLA/RTO/RPO, independent backup and restore testing not done (778b); audit logging as built
      (840/845); no in-app MFA; impersonation role described; Neon not Render; branch protection as configured (no
      required approval). Superseded versions in `archive/` with `_pre-sprint-845` names; stale `.docx` exports
      removed; index and changelog rewritten.
- [x] Code the docs depend on: the audit chain now links **and** verifies per user with archived rows included
      (`shared/audit_chain.previous_chain_hash`), still accepts legacy cross-user links so existing rows verify, and
      reports unchained (pre-Sprint-461) rows instead of skipping them; the admin audit log is under the deletion
      guard (ORM + `accounting_policy.toml`).
- [x] DR workflows: already report honestly (778a — UNVERIFIED rather than false-green); the Neon + R2 rewrite needs
      credentials and stays in **Sprint 778b**.
- [ ] **CEO:** repository visibility. Private is the safer default before launch (`gh repo edit --visibility private`
      is a CEO action — outward-facing); git history keeps the old text for anyone who cloned it. `docs/08-internal/`
      (SOC 2 evidence drafts, readiness assessment) is also public and was out of this sprint's scope.

**Commit SHA:** TBD.


---

