# Paciolus Development Roadmap

> **Protocol:** Every directive MUST begin with a Plan Update to this file and end with a Lesson Learned in `lessons.md`.

---

## Phase Lifecycle Protocol

**MANDATORY:** Follow this lifecycle for every phase. This eliminates manual archive requests.

### During a Phase
- Active phase details (audit findings, sprint checklists, reviews) live in this file under `## Active Phase`
- Each sprint gets a checklist section with tasks, status, and review

### On Phase Completion (Wrap Sprint)
1. **Regression:** `pytest` + `npm run build` must pass
2. **Archive:** Move all sprint checklists/reviews to `tasks/archive/phase-<name>-details.md`
3. **Summarize:** Add a one-line summary to `## Completed Phases` below (with test count if changed)
4. **Clean this file:** Delete the entire `## Active Phase` section content, leaving only the header ready for the next phase
5. **Update CLAUDE.md:** Add phase to completed list, update test count + current phase
6. **Update MEMORY.md:** Update project status
7. **Commit:** `Sprint X: Phase Y wrap — regression verified, documentation archived`

**The `## Active Phase` section should ONLY contain the current in-progress phase. Once complete, it becomes empty until the next phase begins.**

---

## Completed Phases

### Phases I–IX (Sprints 1–96) — COMPLETE
> Core platform through Three-Way Match. TB analysis, streaming, classification, 9 ratios, anomaly detection, benchmarks, lead sheets, prior period, adjusting entries, email verification, Multi-Period TB (Tool 2), JE Testing (Tool 3, 18 tests), Financial Statements (Tool 1), AP Testing (Tool 4, 13 tests), Bank Rec (Tool 5), Cash Flow, Payroll Testing (Tool 6, 11 tests), TWM (Tool 7), Classification Validator.

### Phase X (Sprints 96.5–102) — COMPLETE
> Engagement Layer: engagement model + materiality cascade, follow-up items, workpaper index, anomaly summary report, diagnostic package export, engagement workspace frontend.

### Phase XI (Sprints 103–110) — COMPLETE
> Tool-Engagement Integration, Revenue Testing (Tool 8, 12 tests), AR Aging (Tool 9, 11 tests).

### Phase XII (Sprints 111–120) — COMPLETE
> Nav overflow, Finding Comments + Assignments, Fixed Asset Testing (Tool 10, 9 tests), Inventory Testing (Tool 11, 9 tests). **v1.1.0**

### Phase XIII (Sprints 121–130) — COMPLETE
> Dual-theme "The Vault", security hardening, WCAG AAA, 11 PDF memos, 24 rate-limited exports. **v1.2.0. Tests: 2,593 + 128.**

### Phase XIV (Sprints 131–135) — COMPLETE
> 6 public marketing/legal pages, shared MarketingNav/Footer, contact backend.

### Phase XV (Sprints 136–141) — COMPLETE
> Code deduplication: shared parsing helpers, shared types, 4 shared testing components. ~4,750 lines removed.

### Phase XVI (Sprints 142–150) — COMPLETE
> API Hygiene: 15 fetch → apiClient, semantic tokens, Docker hardening.

### Phase XVII (Sprints 151–163) — COMPLETE
> Code Smell Refactoring: 7 backend shared modules, 8 frontend decompositions, 15 new shared files. **Tests: 2,716 + 128.**

### Phase XVIII (Sprints 164–170) — COMPLETE
> Async Architecture: `async def` → `def` for pure-DB, `asyncio.to_thread()` for CPU-bound, `BackgroundTasks`, `memory_cleanup()`.

### Phase XIX (Sprints 171–177) — COMPLETE
> API Contract Hardening: 25 endpoints gain response_model, 16 status codes corrected, trends.py fix, path fixes.

### Phase XX (Sprint 178) — COMPLETE
> Rate Limit Gap Closure: 4 endpoints secured, global 60/min default.

### Phase XXI (Sprints 180–183) — COMPLETE
> Migration Hygiene: Alembic baseline regeneration, datetime deprecation fix.

### Phase XXII (Sprints 184–190) — COMPLETE
> Pydantic Model Hardening: Field constraints, 13 Enum/Literal migrations, model decomposition, v2 syntax.

### Phase XXIII (Sprints 191–194) — COMPLETE
> Pandas Performance: vectorized keyword matching, NEAR_ZERO guards, math.fsum. **Tests: 2,731 + 128.**

### Phase XXIV (Sprint 195) — COMPLETE
> Upload & Export Security: formula injection, column/cell limits, body size middleware. **Tests: 2,750 + 128.**

### Sprint 196 — PDF Generator Critical Fixes — COMPLETE
> Fix `_build_workpaper_signoff()` crash, dynamic tool count, BytesIO leak.

### Phase XXV (Sprints 197–201) — COMPLETE
> JWT Auth Hardening: refresh tokens, CSRF/CORS, bcrypt, jti claim, startup cleanup. **Tests: 2,883 + 128.**

### Phase XXVI (Sprints 202–203) — COMPLETE
> Email Verification Hardening: token cleanup, pending_email re-verification, disposable blocking. **Tests: 2,903 + 128.**

### Phase XXVII (Sprints 204–209) — COMPLETE
> Next.js App Router Hardening: 7 error boundaries, 4 route groups, skeleton components, loading.tsx files.

### Phase XXVIII (Sprints 210–216) — COMPLETE
> Production Hardening: GitHub Actions CI, structured logging + request ID, 46 exceptions narrowed, 45 return types, deprecated patterns migrated.

### Phase XXIX (Sprints 217–223) — COMPLETE
> API Integration Hardening: 102 Pydantic response schemas, apiClient 422 parsing, isAuthError in 3 hooks, downloadBlob→apiClient, CSRF on logout, UI state consistency, 74 contract tests, OpenAPI→TS generation. **Tests: 2,977 + 128.**

### Phase XXX (Sprints 224–230) — COMPLETE
> Frontend Type Safety Hardening: 5 `any` eliminated, 3 tsconfig strict flags, type taxonomy consolidation (Severity/AuditResult/UploadStatus), discriminated unions (BankRec + hook returns), 24 return type annotations, 11 optional chains removed. **Tests: 2,977 + 128.**

### Phase XXXI (Sprints 231–238) — COMPLETE
> Frontend Test Coverage Expansion: 22 pre-existing failures fixed, 20 new test files, 261 new tests added. **Tests: 2,977 + 389.**

### Sprints 239–240 (Standalone) — COMPLETE
> Sprint 239: Tailwind cleanup, 3 shared components (GuestCTA, ZeroStorageNotice, DisclaimerBox), chart theme. Sprint 240: Framer-motion performance & accessibility (MotionConfig, scaleX transforms, CSS keyframes, DURATION/SPRING presets).

### Phase XXXII (Sprints 241–248) — COMPLETE
> Backend Test Suite Hardening: 73 new tests (14 edge case + 59 route integration), 5 monolithic files split into 17 focused files, CSRF fixture opt-in refactor, 1 schema bugfix. **Tests: 3,050 + 389.**

### Phase XXXIII (Sprints 249–254) — COMPLETE
> Error Handling & Configuration Hardening: 131 frontend tests, Docker tuning, global exception handler, 21 sanitize_error migrations, 9 db.commit() gaps closed, secrets_manager integration, .gitignore hardened. **Tests: 3,050 + 520.**

### Phase XXXIV (Sprints 255–260) — COMPLETE
> Multi-Currency Conversion: python-jose → PyJWT security pre-flight, RFC (closing-rate MVP), currency engine with ISO 4217 validation + rate lookup + vectorized conversion, 4 API endpoints, CurrencyRatePanel component, conversion memo PDF, auto-conversion in TB upload. **v1.3.0. Tests: 3,129 + 520.**

### Phase XXXV (Sprints 261–266 + T1) — COMPLETE
> In-Memory State Fix + Codebase Hardening: stateless HMAC CSRF, DB-backed lockout + tool sessions, float precision (math.fsum/Decimal), server_default timestamps, 8 dependency upgrades, deep health probe, CI security gates (Bandit/Dependabot/pip-audit), zero-storage language truthfulness. All 8 SESSION_HANDOFF packets validated. **Tests: 3,323 + 724.**

### Phase XXXVI (Sprints 268–272) — COMPLETE
> Statistical Sampling Module (Tool 12): ISA 530 / PCAOB AS 2315, MUS + random sampling, 2-tier stratification, Stringer bound evaluation, two-phase workflow (design + evaluate), PDF memo, CSV export, 12-tool nav. **v1.4.0. Tests: 3,391 + 745.**

### Phase XXXVII (Sprints 273–278) — COMPLETE
> Deployment Hardening: dependency version bumps (pydantic, openpyxl, PyJWT, TypeScript), PostgreSQL connection pool tuning + CI job, Sentry APM integration (Zero-Storage compliant), 23 new frontend test files (173 new tests), coverage threshold raised to 25%. **v1.5.0. Tests: 3,396 + 918.**

### Phase XXXVIII (Sprints 279–286) — COMPLETE
> Security & Accessibility Hardening + Lightweight Features: passlib→bcrypt, CVE patches, typing modernization, ruff rules, back_populates migration, WCAG modals/labels/images/CSP, focus trap, eslint-plugin-jsx-a11y, Data Quality Pre-Flight Report, Account-to-Statement Mapping Trace, users+auth route tests, exception narrowing. **v1.6.0. Tests: 3,440 + 931.**

### Phase XXXIX (Sprints 287–291) — COMPLETE
> Diagnostic Intelligence Features: TB Population Profile (Gini, magnitude buckets), Cross-Tool Account Convergence Index, Expense Category Analytical Procedures (5-category ISA 520), Accrual Completeness Estimator (run-rate ratio). 11 new API endpoints, 4 new TB sections, 4 PDF memos. **v1.7.0. Tests: 3,547 + 931.**

### Phase XL (Sprints 292–299) — COMPLETE
> Diagnostic Completeness & Positioning Hardening: Revenue concentration sub-typing, Cash Conversion Cycle (DPO/DIO/CCC — 12 ratios), interperiod reclassification detection, TB-to-FS arithmetic trace (raw_aggregate + sign_correction), account density profile (9-section sparse flagging), ISA 520 expectation documentation scaffold, L1-L4 language fixes, 46 new frontend tests. **v1.8.0. Tests: 3,644 + 987.**

### Phase XLI (Sprints 308–312) — COMPLETE
> Cross-Tool Workflow Integration: A-Z lead sheet codes, FLUX_ANALYSIS ToolName enum + Alembic migration, flux extractor registration + engagement wiring, convergence coverage fields, pre-flight→column passthrough, materiality cascade passthrough (_resolve_materiality), composite score trend (get_tool_run_trends + TrendIndicator). 5 workflow gaps bridged, 0 new tools. **Tests: 3,780 + 995.**

### Phase XLII (Sprints 313–318) — COMPLETE
> Design Foundation Fixes: shadow/border token repair, opacity/contrast audit, typography/spacing, 3-batch light theme semantic token migration (~30 components). **Tests: 3,780 + 995.**

### Phase XLIII (Sprints 319–324) — COMPLETE
> Homepage "Ferrari" Transformation: cinematic hero with animated data visualization, gradient mesh atmosphere, scroll-orchestrated narrative sections, interactive product preview (DemoZone rewrite), tool grid redesign + social proof, marketing page polish. 4 new components (HeroVisualization, GradientMesh, ProductPreview, ToolShowcase). **v1.9.0. Tests: 3,780 + 995.**

### Phase XLIV (Sprints 325–329) — COMPLETE
> Tool Pages "Rolls Royce" Refinement: 3-tier card hierarchy (card/elevated/inset) with warm-toned shadows, left-border accent pattern across 6+ components, tabular-nums for financial data, heading-accent with sage dash, paper texture via SVG feTurbulence, prefers-reduced-motion compliance. **v1.9.1. Tests: 3,780 + 995.**

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix, phase-xxx, phase-xxxi, phase-xxxii, phase-xxxiii, phase-xxxiv, phase-xxxv, phase-xxxvi, phase-xxxvii, phase-xxxviii, phase-xxxix, phase-xl, phase-xli, phase-xlii, phase-xliii, phase-xliv)

---

## Post-Sprint Checklist

**MANDATORY:** Complete after EVERY sprint.

- [ ] `npm run build` passes
- [ ] `pytest` passes (if tests modified)
- [ ] Zero-Storage compliance verified (if new data handling)
- [ ] Sprint status → COMPLETE, Review section added
- [ ] Lessons added to `lessons.md` (if corrections occurred)
- [ ] `git add <files> && git commit -m "Sprint X: Description"`

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Multi-Currency Conversion | **COMPLETE — Phase XXXIV (v1.3.0)** | Phase VII |
| Composite Risk Scoring | Requires ISA 315 inputs — auditor-input workflow needed | Phase XI |
| Management Letter Generator | **REJECTED** — ISA 265 boundary, auditor judgment | Phase X |
| Expense Allocation Testing | 2/5 market demand | Phase XII |
| Templates system | Needs user feedback | Phase XII |
| Related Party detection | Needs external APIs | Phase XII |
| Dual-key rate limiting | **RESOLVED** — User-aware keying + tiered policies delivered in Sprint 306 | Phase XX |
| Wire Alembic into startup | Latency + multi-worker race risk; revisit for PostgreSQL | Phase XXI |
| `PaginatedResponse[T]` generic | Complicates OpenAPI schema generation | Phase XXII |
| Dedicated `backend/schemas/` dir | Model count doesn't justify yet | Phase XXII |
| Cookie-based auth (SSR) | Large blast radius; requires JWT → httpOnly cookie migration | Phase XXVII |
| Marketing pages SSG | Requires cookie auth first | Phase XXVII |
| Frontend test coverage (30%+) | **RESOLVED** — 83 suites, 44% statements, 35% branches, 25% threshold | Phase XXXVII |
| ISA 520 Expectation Documentation Framework | **RESOLVED** — Delivered in Phase XL Sprint 297 with blank-only guardrail | Council Review (Phase XL) |
| pandas 3.0 upgrade | CoW + string dtype breaking changes; needs dedicated evaluation sprint | Phase XXXVII |
| React 19 upgrade | Major version with breaking changes; needs own phase | Phase XXXVII |

---

## Active Phase

### Sprint 330: HeroProductFilm — Cinematic Lobby Hero — COMPLETE
> **Focus:** Replace decorative HeroVisualization with narrative product film (Upload→Analyze→Export auto-cycle)
> **Complexity:** 4/10

- [x] Create `HeroProductFilm.tsx` — glass panel, 3-state auto-cycle, hover pause, progress bar
- [x] Update `page.tsx` — swap import, remove `hidden lg:block` for mobile visibility
- [x] Update `index.ts` — replace barrel export
- [x] `npm run build` passes
- [x] Visual: panel cycles through all 3 states on desktop and mobile

---

### Sprint 331: Lobby Brand-Layer Utility System
> **Focus:** Reusable CSS utility classes for lobby section depth rhythm (recessed/raised/accent surfaces, sage glow, vignette, upgraded dividers)
> **Complexity:** 2/10

- [x] Add 6 lobby utility classes to `globals.css` (`@layer utilities`)
- [x] Add reduced-motion selectors for lobby utilities
- [x] Apply section-to-utility mapping in `page.tsx` (4 wrappers + 2 dividers)
- [x] `npm run build` passes
- [ ] Visual verification: A-B-A depth rhythm visible across sections

---

### Sprint 332: ToolShowcase Outcome Clusters — Accordion Progressive Disclosure
> **Focus:** Refactor ToolShowcase 2-category flat grid → 4 outcome clusters with accordion expand
> **Complexity:** 4/10

- [x] Replace `ToolCategory`/`TOOL_CATEGORIES` with `OutcomeCluster`/`OUTCOME_CLUSTERS` (4 groups of 3)
- [x] Add `activeCluster` state + toggle logic (one-at-a-time accordion)
- [x] Render 2x2 cluster header grid (desktop) / 1-column stack (mobile) with left accent borders
- [x] AnimatePresence expand panel below grid (3 tool cards, md:grid-cols-3)
- [x] Chevron animation, aria-expanded/aria-controls, keyboard accessible
- [x] Update subtitle copy ("Four outcomes. Twelve tools.")
- [x] `npm run build` passes
- [x] All 12 tool links accessible via cluster expand

---

### Sprint 333: BrandIcon Shared Component — Marketing Icon Deduplication
> **Focus:** Extract ~25 inline SVGs from 4 marketing files into `<BrandIcon name="..." />` shared component
> **Complexity:** 3/10

- [x] Create `components/shared/BrandIcon.tsx` — 21 icon paths, `BrandIconName` type, consistent strokeWidth=1.5, aria-hidden
- [x] Add `BrandIcon` + `BrandIconName` export to `shared/index.ts`
- [x] Migrate ToolShowcase.tsx — 17 inline SVGs → `<BrandIcon>` (keep motion.svg chevron-down inline)
- [x] Migrate FeaturePillars.tsx — 3 inline SVGs → `<BrandIcon>`
- [x] Migrate ProcessTimeline.tsx — 3 inline SVGs → `<BrandIcon>`
- [x] Migrate page.tsx — 2 trust indicator SVGs → `<BrandIcon>`
- [x] `npm run build` passes
- [x] No inline `<svg>` remains in target files (except motion.svg chevron)

---

### Sprint 334: Trust Architecture — Social Proof Blocks
> **Focus:** ProofStrip (credibility band) + BottomProof (testimonials + CTA) — two social proof modules for the homepage
> **Complexity:** 3/10

- [x] Create `ProofStrip.tsx` — 6 industry badges + 4 outcome metric cards, stagger animation
- [x] Create `BottomProof.tsx` — 3 testimonials (left-border accent), 3 CountUp metrics, auth-aware CTA
- [x] Update `index.ts` — add 2 barrel exports
- [x] Update `page.tsx` — insert ProofStrip after hero, BottomProof after ProductPreview
- [x] `npm run build` passes
- [x] All elements use Oat & Obsidian tokens only

---

### Sprint 335: Pricing Estimator + Persona Toggles
> **Focus:** Interactive plan estimator with persona toggles that dynamically recommends a "best fit" tier
> **Complexity:** 3/10

- [x] Add estimator types (`Uploads`, `Tools`, `TeamSize`, `PersonaKey`, `TierName`)
- [x] Add 3 persona definitions with default selections
- [x] Add `getRecommendedTier()` pure recommendation logic
- [x] Add `PersonaIcon` SVG component (calculator/building/users)
- [x] Add `SegmentedSelector` generic local component
- [x] Add estimator state (`uploads`, `tools`, `teamSize`, `activePersona`)
- [x] Insert Plan Estimator section between hero and pricing cards
- [x] Persona toggles pre-fill estimator inputs + clear on manual change
- [x] AnimatePresence recommendation line with crossfade
- [x] Dynamic "Best Fit for You" badge on recommended tier card
- [x] Dynamic sage highlight on recommended tier (replaces static `highlighted`)
- [x] "Most Popular" badge preserved on Professional when NOT best fit
- [x] Remove static `highlighted` field from Tier interface + data
- [x] `npm run build` passes
- [x] All elements use Oat & Obsidian tokens only

