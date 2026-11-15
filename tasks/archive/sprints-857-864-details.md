# Sprints 857–864 Details

> Archived from `tasks/todo.md` Active Phase on 2026-11-15.

---

### Sprint 861: Website claims — remove what we cannot prove
**Status:** COMPLETE 2026-11-14. **Priority:** P0 (before 2026-12-15 launch). **Source:** `WEBSITE_REVIEW.md` §1–2, CEO decisions 2026-11-14.
**Owner:** C. **Rule:** if a claim cannot be proven from the code or a published document, delete it.

Facts established 2026-11-14 from the code (use these, not the older copy):
- Shared links store the **whole export file** (`routes/export_sharing.py`) — rows from the client's file can sit in R2 for
  24 h (Professional) / 48 h (Enterprise). Any "line-level rows are never stored" line is false.
- The 10-minute in-memory cache applies **only to the preview / workbook-inspect flow** (`shared/preflight_cache.py`).
- Analysis summaries are **archived (hidden), not deleted,** after `RETENTION_DAYS` = 365 (`retention_cleanup.py`);
  "Clear history" also only hides. Only account deletion removes them.
- Flagged account names come from the client's chart of accounts and **can contain a person's name**.
- Nothing in our code encrypts shared exports; any encryption is the provider's.
- No production speed benchmark exists.

Marketing — Trust page
- [x] Delete the compliance timeline: SOC 2 "Available", GDPR/CCPA "Compliant", DPA "Available" badges and the
      "Independent Attestation / Compliance Roadmap" section (R-01–R-03). Replace with the plain certification paragraph
      (no certification held or claimed) — links land in Sprint 862.
- [x] Remove "Zero / Raw Data Stored", "Zero raw data persisted", "the evidence to prove it", both "What We NEVER Store"
      headings (→ "What We Don't Keep" + the shared-link exception) (R-05, R-16).
- [x] Remove "PCAOB AS 1215" from the Optional Sign-Off control (R-07); remove "No PII in logs", "Immediate isolation…",
      "No client PII in analysis results" (R-06); replace the four-phase playbook with three plain sentences
      (detection · handled by the founder · notification as the law requires).
- [x] Remove "encrypted" from every marketing surface; remove "nothing at rest to breach" lines (R-21).

Marketing — homepage, About, Approach, Demo, Pricing, metadata
- [x] Hero: delete "Zero data retained." (R-15); new headline "Trial balance and ledger testing for audit teams." with the
      method subline; remove the animated product film and the "3 findings" / "17 PDF Memos" / struck-out tiles (R-09,
      R-24, G-05) — static layout until Sprint 865 supplies the screenshot.
- [x] **No standard names on marketing pages.** Replace ToolLedger chips, `StandardsSpecimen` (incl. AS 1215, R-08),
      the EvidenceBand "ISA · PCAOB · ASC" cell (R-10), About's ISA/PCAOB list and demo tool/Standards-tab citations with
      one line: "Every test cites the rule it applies. See Sources & Methodology." (`/sources` keeps the citations.) SOC 1
      goes with them (R-04).
- [x] Remove every speed claim ("in seconds", "Seconds", "<5 seconds", "Immediate Results") (G-11).
- [x] Render `STORAGE_STATEMENT` verbatim + "See exactly what we keep" link on hero, footer, About, Approach, Pricing,
      Register, Login and `ZeroStorageNotice` (S-03, A-06, A-07). Share-link retention as "up to 24 hours (Professional)
      or 48 hours (Enterprise)" everywhere (R-20). Preview-cache wording per the facts above (R-17). Remove "never saved /
      never kept / destroyed / released after the request / not kept" for exports (R-17–R-19).
- [x] Retention line: "Analysis summaries and engagement entries are kept while your account is open. Deleting your account
      deletes them." Drop "archived on schedule" / "deleted on request". "What we keep" lists note that flagged account
      names can include a person's name.
- [x] Approach: replace the "Traditional SaaS vs Paciolus" table with the factual what / how-long table (R-23).
- [x] About: replace the CaseWare/TeamMate paragraph with the approved division-of-responsibility sentence (R-12); add
      "not a substitute for your firm's audit documentation and retention obligations" to footer, About and Pricing FAQ
      (S-05); add "Paciolus is developed and operated by Paciolus LLC, a US company."
- [x] Remove "intelligent / intelligence / Surgical Precision / unlocks / Professional-grade" from copy and metadata
      (G-10, G-12, G-13). Demo CTA: "Start 7-day trial" + card-required line (R-25).

App
- [x] "All tests returned clean results" ×7 → "No exceptions flagged." via one constant (R-13); "Top Findings" → "Top
      flagged items" (R-14); "workpaper-ready CSV" (R-11); "Intelligent column detection", "Intelligence Briefing",
      "Flux & Variance Intelligence" (A-04); Archive → Remove on misstatement/expectation rows (A-09).
- [x] `/status`: delete the hard-coded test-results section (keep the health check) (R-26).

Hygiene and checkability
- [x] Rename `ZeroStorageNotice` → `UploadHandlingNotice` and drop "Zero-Storage" from code comments, so the retired
      term stops being copied forward (R-22).
- [x] Every remaining numeric claim (test counts, tool count, standard-setters cited, security-control count) links to
      where it can be checked (`/sources`, the control list) (S-14).
- [x] Sweep the leftovers found during the review: EvidenceBand "None / Uploaded Files Kept", "Every output is exported
      when analysis completes", demo "Workpapers 12 indexed", root metadata "Close Health Reports".

Guard
- [x] Extend `backend/tests/test_storage_claims.py` (or a sibling) with a banned-phrase list for customer-facing copy:
      zero data, never stored/saved/kept, destroyed, not written to disk, clean results, findings (outside negations),
      audit-ready, workpaper-ready, intelligent, SOC 2/SOC 1 outside Sources, compliant, encrypted, in seconds.

**Review (2026-11-14):**
- Facts behind every new sentence checked against the code; a background check of the Trust page's 22 security
  sentences corrected 7 (CSRF scope, no cell-count limit, query scoping, TLS, memory release). Two false claims found
  in *existing* copy along the way and fixed: the diagnostic-package ZIP contents and the activity log "included in
  the package" (`tasks/lessons.md`).
- One source for all data-handling sentences and lists: `frontend/src/content/storage-statement.ts` (Trust and
  Approach render the same lists — S-06 done here, not in 862).
- Removed: animated hero film, standards specimen (incl. AS 1215), ToolLedger standards column, demo Standards tab,
  compliance timeline, playbook, Trust count-ups, `/status` test results. Renamed `ZeroStorageNotice` →
  `UploadHandlingNotice`; retired term gone from frontend comments.
- Leftovers deferred, by design: page layout and decoration (Sprint 864); the hero has no image until Sprint 865;
  Privacy/Terms wording goes through counsel (Sprint 863). `tool-ledger.ts` still carries a `standards` field
  (incl. SOC 1) that nothing renders — left because the catalog tests read it.
- New guard: `backend/tests/test_marketing_claims.py` (banned phrases on every customer-facing surface; no standard
  codes on marketing pages; no hard-coded status results).

**Verification:** `npm run lint` clean · `tsc --noEmit` clean · Jest 2,100/2,100 (210 suites) · `npm run build` passes ·
backend claims/citation/pricing/catalog tests 71 passed · Chrome pass over `/`, `/trust`, `/approach`, `/demo`,
`/status` on a local production build.

**Commit SHA:** `45a6d7df`. (Correction recorded in Sprint 862: the retention sentence shipped here was false for
backups.)
Also missed here: a comment in `HeroProductFilm.tsx` broke `test_doc_consistency_guard.py` (not run) — fixed in
Sprint 862 (`tasks/lessons.md`).


---

### Sprint 862: Publish the compliance documents; rebuild the Trust page's proof
**Status:** COMPLETE 2026-11-14. **Priority:** P0. **Source:** `WEBSITE_REVIEW.md` S-02, S-06, S-08, S-09; live-site check 2026-11-14.
**Owner:** C. **Depends on:** Sprint 861 (Trust page cleared); Security Policy wording from Sprint 863 before it is published.

- [x] Publish `SECURITY_POLICY.md`, `SUBPROCESSOR_LIST.md` and the architecture document as site pages (rendered from
      the markdown, one source), linked from the Trust page, footer and certification paragraph. `/security` and
      `/subprocessors` resolve (they 404 today).
- [x] Rename `ZERO_STORAGE_ARCHITECTURE.md` → `DATA_HANDLING_ARCHITECTURE.md` (title too) before linking it — the
      retired term must not be in a customer-facing URL or title. Update references.
- [x] Certification paragraph, final: "Paciolus holds no SOC 1, SOC 2, ISO 27001 or other third-party certification,
      and does not claim one." + links to the three documents.
- [x] Vendor-review facts block: hosting ("Uploads are processed, and your account data is stored, in the eastern United
      States. Every service we use, and where it operates, is in our Subprocessor List." — Render Virginia, Neon
      us-east-1, R2 Eastern North America; re-check against the Subprocessor List at build time), DPA on request
      (stays "on request" — `DATA_PROCESSING_ADDENDUM.md` is 2.0-draft), support response 1–2 business days.
- [x] Trust FAQ: "Does Paciolus satisfy AU-C 230 or PCAOB AS 1215?" — answer per `WEBSITE_REVIEW.md` S-09 (AU-C 230 first).
- [x] One "what we keep" source in `content/`, rendered identically on Trust `#transparency` and Approach (S-06).
- [x] Two-path data-flow diagram in the palette (built in HTML, not an SVG image, so it reflows and reads as two ordered lists), on Trust and Approach (S-02): A — upload → in memory
      (preview cache up to 10 min) → results returned → uploaded file discarded; B — share link → stored up to 24 h
      (Professional) / 48 h (Enterprise) → deleted.
- [x] Backend: in production, shared exports **fail** rather than fall back to a DB blob when R2 is unavailable
      (`routes/export_sharing.py`), so "stored with our storage provider" stays true. Test it.
- Deferred (CEO 2026-11-14): security-questionnaire pack (after the Security Policy update) · curated release notes.

**Review (2026-11-14):**
- **New facts found and fixed while publishing.** The daily backup to R2 went live today (backup and DR runs green
  2026-11-14), and nothing customer-facing said so: (1) the Security Policy said "no off-provider backup exists";
  (2) the Subprocessor List said GitHub "handles no customer data", but GitHub Actions now runs the dump and the restore
  tests, and Cloudflare was listed for shared reports only; (3) Sprint 861's retention line "Deleting your account
  deletes them" was false — copies stay in backups up to 12 months (30 daily + 12 monthly). All three corrected
  (Security Policy 3.1, Subprocessor List 2.1, Data Handling Architecture 3.1, site copy). **CEO note:** the
  Subprocessor List promises to be updated *before* a subprocessor is added; GitHub was added for backups without
  that. No customers yet, so nobody was owed notice — but the promise was broken once.
- **Why the lint missed it:** `scripts/lint_subprocessors.py` read buckets from backend code only. It now also reads
  CI workflows and scripts, and fails if a workflow uses a customer-data secret while GitHub is unlisted (proved: the
  old list fails, the new one passes).
- Documents are the single source: `scripts/sync_policy_docs.py` → `frontend/src/content/policies.generated.ts`;
  `backend/tests/test_policy_docs_published.py` fails if they drift. Renderer `components/policy/PolicyMarkdown.tsx`
  (no new dependency); links to unpublished documents render as text. New pages `/security`, `/subprocessors`,
  `/data-handling`, registered in `theme-routes.ts` and the sitemap, linked from the footer and Trust.
- Security Policy 3.1 also narrows four sentences to the code (CSRF scope, query scoping, upload limits, transport);
  those factual edits go to counsel with Sprint 863 for review, since the document is now on the site.
- Backend: in production a share is stored in R2 or refused (503) — no silent database fallback. **After deploy,
  confirm the four `R2_EXPORTS_*` env vars are still set on Render, or sharing will refuse.**

**Verification:** full backend suite 10,633 passed / 1 failed — `test_sprint819_route_snapshots.py::test_engagement_export_routes_unchanged` (`content-encoding` gzip vs null), which fails identically on `main` in a clean worktree, so pre-existing and not this sprint · Jest 2,108/2,108 (211 suites) · lint and `tsc` clean · build passes (three new routes) · backend
claims, policy-drift, data-disclosure, extractor and all export-sharing tests pass (48 sharing) · subprocessor lint
passes · Chrome pass on `/subprocessors` and the Trust diagram and vendor-review sections (a `/security` tab froze in
Chrome; the page itself returned 200 in 22 ms with the right content via curl).

**Commit SHA:** `7a1529cc`.


---

### Sprint 864: Strip the decorative layer
**Status:** COMPLETE 2026-11-15. **Priority:** P1. **Source:** `WEBSITE_REVIEW.md` G-01–G-09, S-11, S-12. **Owner:** C. CEO-directed — freeze-exempt.

- [x] Remove the four stock-photo backgrounds (`public/backgrounds/background1/2/3/5.jpg`; CEO: royalty-free downloads,
      no license records kept — remove rather than rely on them) and their `.lobby-atmosphere-*` utilities.
- [x] Remove gradient text, `.lobby-glow-sage`, glow shadows, inner-glow overlays, pulsing dots, gradient hairlines,
      `backdrop-blur` glass, `ScanlineOverlay`, emoji tab icons (G-01–G-04, G-09).
- [x] Remove parallax, magnetic buttons, spin-ins, clip wipes and count-ups (the live Trust page loads showing
      "2 Security Controls / 1 Control Domains" mid-count); keep ≤200 ms opacity fades only (G-06).
- [x] Replace the three-icon-card rows (FeaturePillars, ProcessTimeline, About cards) with numbered, hairline-ruled
      input → mechanism → output rows (G-07, S-04); left-aligned demo hero without the pill (G-08).
- [x] Tabular lining figures on every price and stat; app-matching button and card shapes (S-11, S-12).

**Review (2026-11-15):** shared CSS utilities flattened (solid surfaces, plain hairline dividers; glow halo,
vignette and photo layers deleted) so every page changed consistently; four stock images deleted; parallax,
magnetic buttons, spin-ins, clip wipes, count-ups, scan-line effect, glass panels, glow shadows and emoji icons
removed; marketing fades capped at 0.2 s with no delays (the shared `Reveal`/`lib/motion` app presets were left
alone — app motion is out of scope); FeaturePillars, ProcessTimeline, EvidenceBand and the About cards rebuilt as
numbered hairline rows; demo hero left-aligned without the pill; marketing radius aligned to the app's
`rounded-lg`; prices and stats set in tabular lining figures. Dead code deleted: `DemoZone`, `ScanlineOverlay`.

**Verification:** Jest 2,104/2,104 (211 suites) · lint and `tsc` clean · build passes · design-token lint passes ·
copy guards 102 passed · Chrome pass on `/` and `/demo` (local production build).

**Commit SHA:** the commit that archived this file (see `git log --grep "Sprint 864"`).


---

### Sprint 857: State-doc drift check (narrowed)
**Status:** COMPLETE 2026-10-28. **Priority:** P3 (Phase 5; freeze-exempt). **Complexity:** 2/10. **Source:** Q5 tiebreak, Critic's narrowing.

Two deterministic checks only, run in CI. No prose matching of "pending merge" — that would false-alarm and get muted.

- [x] `SESSION_STATE.md`'s named `main` SHA must be an ancestor of HEAD. (`scripts/check_state_docs.py`; one line `**Main SHA:** \`<sha>\`` documented at the top of `SESSION_STATE.md`; runs in the required Lint Baseline Gate job with `fetch-depth: 0`.)
- [x] No sprint number may appear in two `### Sprint N:` titles with different subjects. 11 historical collisions (1–4, 527, 677, 699–703) allowlisted; sub-sprint ids distinct. PR titles not checked (needs a token in CI).
- [x] Manual post-merge checklist line added to `tasks/PROTOCOL.md` for the rest (status → COMPLETE, SHA recorded).

**Verification:** `python scripts/check_state_docs.py` passes; `pytest tests/test_state_docs_check.py` 16 passed (82 with test_design_token_lint.py); ruff clean.

**Commit SHA:** `275ee5c7` (on `main`).


---

### Sprint 858: Solo-only checkout gating
**Status:** COMPLETE 2026-10-28. **Priority:** P1 (Phase 3 — must ship before Sprint 447 goes live). **Source:** Q1 (8–0), Executor amendment.

The launch sells Solo only until Sprint 853 makes clients firm-owned. Nothing in the code enforces that yet.

- [x] Pricing page, `UpgradeGate` CTAs and the upgrade flow show **"Contact us"** for Professional and Enterprise.
      (Pricing cards, `UpgradeModal`, `/checkout?plan=professional|enterprise`, `FeatureGate` — the gate that
      actually names those tiers — and the Settings → Billing "Add Seat" button all go to
      `/contact?inquiry=Organization`. `UpgradeGate` only gates Free-tier tools and links to `/pricing`, where Solo
      is still self-serve, so it is unchanged.)
- [x] Backend **rejects** checkout-session creation for Professional/Enterprise price IDs behind a single flag that
      Sprint 853 flips (test: request a Pro session → 4xx). Flag: `SELF_SERVE_TEAM_TIERS_ENABLED = False` in
      `backend/billing/price_config.py`, mirrored in `frontend/src/domain/pricing.ts` and pinned by
      `tests/test_pricing_copy_consistency.py`. Checkout (new or Solo→Pro upgrade) → **403** before any Stripe call;
      `POST /billing/add-seats` on a Pro/Enterprise subscription → 403; the subscription created/updated webhooks
      still sync what Stripe billed but log a warning (a Billing Portal plan switch is the remaining path — see
      CEO note). Sprint 853: flip both constants together; tests opt in with the `self_serve_team_tiers` fixture.
- [x] Copy check: no marketing surface promises self-serve Professional/Enterprise purchase while the flag is off.
      ("Every paid plan starts with a 7-day free trial" on the pricing page and FAQ now name Solo; Pro/Enterprise
      trial lines and comparison cells drop the trial; a "How do I sign up for Professional or Enterprise?" FAQ; a
      USER_GUIDE §21.3 note. Generic "Start Free Trial" → `/register` CTAs are Solo-true and stay.)
- **CEO note:** the Stripe Billing Portal must not offer plan switching to Professional/Enterprise (Stripe
  dashboard → Billing Portal → Subscriptions); that path is outside the code and only logged.

**Verification:** backend billing/pricing subset 1,011 passed; full backend suite 10,308 passed / 3 failed, all environmental (hypothesis
200 ms deadline flake in `test_anomaly_properties.py`, 13/13 on rerun; two `test_model_registry.py` checks that glob
the worktree venv placed at `backend/.venv-wt`); ruff clean; mypy
clean on touched files; frontend `tsc --noEmit` clean, `npm run lint` clean, Jest 2,086/2,086 (209 suites);
`npm run build` not run in the worktree (Turbopack cannot build through the node_modules junction) — run from the
main checkout.

**Commit SHA:** `48691fcb` (on `main`).


---

