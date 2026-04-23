# Lessons Learned

> **Protocol:** After ANY correction from the CEO or discovery of a better pattern, document it here. Review at session start.

---

## Screenshotting a Render env-var edit form leaks secrets into the tool log (session 2026-04-23)

During R2 provisioning, after pasting the `paciolus-exports-rw` Access Key ID and Secret Access Key into a Render env-var Edit form, I took a screenshot to show the "Save, rebuild, and deploy" button location — and Render's edit mode renders every value as a plain `<textarea>` with the raw text exposed, so both secrets landed in the screenshot and therefore in the tool-result log. The view-mode surface is safe (values are masked as `••••••••••` until the eye icon is explicitly clicked), but the edit-mode surface is not. Mitigation took a full Cloudflare token roll (Roll → re-copy → re-paste) before the compromised values could be saved to Render. The earlier 2026-04-22 DATABASE_URL screenshot leak during the orphan-DB investigation was the same failure mode; this is a recurring class of bug that warrants a standing rule.

**Pattern:** Never screenshot a cloud-provider env-var page (Render, Vercel, Cloudflare Workers, AWS, etc.) while in edit mode. To drive a button on an edit form, use `find` + `ref_id` click, or DOM-based `querySelector` + JS coordinate extraction, never a pixel screenshot. Before every screenshot on a credentials-adjacent surface, ask "is any form field on this page in edit mode?" If yes, do not screenshot — use JS DOM extraction with a strict allowlist (labels/counts only, never values, never lengths that imply value shape beyond generic format classes). Safe alternatives: masked view-mode screenshots (values show as dots), JS-only length-and-regex checks (e.g. `valueLength: 32, looksLikeHex32: true`), or narrating the UI position from DOM rect data. When a credential does leak: the remediation order is **(1) do not Save the form** (containment — keep the exposure DOM-only), **(2) rotate the credential at the issuer**, **(3) re-paste into the still-open form with the rotated value**, **(4) only then Save** — this prevents the compromised value from reaching the secrets store, where recovery is much harder than rolling a single token.

---

## A coverage-sentinel gap can be dead code, not a testing gap (Sprint 676)

Sprint 676 targeted three 0%-coverage files from the nightly Coverage Sentinel report. Investigation showed `services/organization_service.py` (180 statements, 0%) had **zero imports anywhere** — Sprint 546's archive claimed "Refactor 5: organization.py → services/organization_service.py + thin routes" but only created the service module, never wired the routes to use it. Writing tests for the orphan would have inflated the coverage number without improving safety; deletion was the right move. **Pattern:** Before writing tests to fix a coverage gap, `grep -r <module_name>` across the whole repo. If nothing imports it, the gap isn't a test gap — it's dead code from an incomplete refactor. The sentinel report doesn't distinguish between "untested" and "unused"; you have to.

---

## Overnight scanners can scan the wrong Python (Sprint 675)

The Dependency Sentinel was executing `pip list --outdated` against `C:/Python312/python.exe` (system Python), not `backend/venv/Scripts/python.exe` (the venv that mirrors production `requirements.txt`). System Python had drifted: `fastapi 0.135.2` vs. venv `0.135.3`, `stripe 15.0.0` vs. venv `15.0.1`, `SQLAlchemy 2.0.48` vs. venv `2.0.49`. The nightly report flagged packages as "outdated" that were actually current in production — three nights of false YELLOW. Root cause: a pre-existing `PYTHON_BIN` constant in `scripts/overnight/config.py` pointed at the venv but was unused; `SYSTEM_PYTHON` was used instead. **Pattern:** Any CI/nightly tool that scans the environment (pip, npm, bundler) must scan the *same* environment that production installs into. When two Python interpreters exist on a machine, pin the scanner to the one backing the app, and make the fallback explicit.

---

## A nightly pytest subprocess timeout is a ticking clock, not a background concern (Sprint 674)

2026-04-17 nightly ran RED because backend pytest hit the 600s subprocess timeout at 601.8s — first time ever. 2026-04-18 completed in 581.2s. Test count growth was 7,405 → 7,804 across three days. At that growth rate, a fixed per-suite timeout will fail again inside a sprint or two. **Pattern:** When the nightly driver subprocess timeout is within 5% of the observed runtime, treat it as a same-week fix, not a future problem — the next test-adding sprint will re-trigger it. The bias should be toward *more* headroom (2×–3× of current runtime), not less; a sleeping wait that could have been shorter costs nothing, but a re-triggered timeout costs a lost nightly signal.

---

## Diagnostic ingestion bypasses the parser dispatcher (Sprint 665)

While building the Sprint 665 remediation harness, every PDF and DOCX input failed the diagnostic pipeline with an incongruous pandas error (`'io.excel.zip.reader'` / `Excel file format cannot be determined`). Root cause: `backend/audit/pipeline.py:73` calls `process_tb_chunked(file_bytes, filename, chunk_size)` in `security_utils.py:201`, which only attempts `read_csv_chunked` → falls back to `read_excel_chunked`. It never dispatches to `parse_uploaded_file_by_format` (`backend/shared/helpers.py:797`), which is the correct entry point that knows about PDF, DOCX, ODS, OFX, QBO, IIF, TSV, TXT. PreFlight uses the dispatcher; diagnostic does not. Every file format the brief says is "supported" is actually only supported on the preflight side. **Pattern:** Two-pipeline features (preflight + diagnostic) need the same ingestion entry point, not parallel copies that drift apart. When a format is added, `grep` every place that accepts `file_bytes + filename` to ensure *all* ingestion paths route through the shared dispatcher.

---

## Remediation harness over pytest when expected values are moving (Sprint 665)

For CEO-facing sequential remediation work where each sprint will change the expected output of the preceding sprint, a pytest regression suite is the wrong tool. Hardcoded expected values in assertions would fight us across six sprints. Instead: a single Python script that parses, runs both pipelines, and writes one diffable JSON per test file per sprint (`reports/remediation/sprint-NNN/<stem>.json`). Diff is done in review, not in code. Expected results live in the sprint review sections, not in `assert` lines. **Pattern:** When the "expected" side of a test is going to change N times in the next N sprints, capture state to diffable artifacts instead of asserting. Pytest is for regression; this pattern is for progression.

---

## Audit the file before auditing the code on a misdiagnosed bug report (Sprint 666)

The CEO remediation brief v6 Issue 9 attributed `tb_unusual_accounts.csv`'s $306,262 variance to "RFC 4180 quoted field handling" — claiming account names with embedded commas caused column shift and phantom imbalances. Before touching the CSV parser I ran pandas directly on the file: every quoted field parses cleanly (none actually contain embedded commas — just parentheses, question marks, slashes which are not CSV-special), every row lands in the right columns, and the data-only sum is $5,791,962 debit / $5,490,500 credit for a genuine $301,462 imbalance. The file was never built to balance. The totals row in the file claims $5,681,962 each side but the actual data sums to different numbers. After Sprint 666's totals-row exclusion the reported variance is $306,262 — unchanged from baseline but now for the right reason (real data imbalance, not a totals-inclusive artifact).

**Pattern:** When a bug report attributes a number to a parser/algorithm cause, verify the number by computing it against the source data by hand before writing a "fix." A misdiagnosed report can waste a sprint building defenses against a non-existent bug, leaving the real cause untouched. The right first step on any "parser is mishandling X" claim is a 5-minute manual sum in a REPL — not a dive into `pd.read_csv` options.

---

## Silent-success bugs surface only when you explicitly test the failure mode (Sprint 666)

The Sprint 666 zero-row guard uncovered a pre-existing pytest case (`test_audit_core::TestEdgeCases::test_empty_file`) that was *validating* the silent-success bug itself — it asserted `status == "success"`, `balanced == True`, `row_count == 0` on a headers-only file. The test was green for however many sprints that bug existed, because nobody had asked "is returning 'balanced' on a zero-row ingestion the right behavior?" The bug was structural, the test was its fossil record. **Pattern:** When fixing a silent-success class of bug, grep for tests that assert the silent-success shape and rewrite them to the post-fix contract BEFORE running the full suite. A green test that encodes a wrong invariant is worse than a missing test — it will actively defend the bug against any fix. Look for tests with names like `test_empty_*`, `test_zero_*`, `test_missing_*` when the bug is about input edge cases.

---

## Breaking API shape changes require simultaneous backend + frontend + test updates (Sprint 544)

When changing a response shape (e.g., `clients` → `items` in PaginatedResponse), ALL consumers must be updated atomically: backend routes, frontend types, frontend hooks, AND test mocks. In Sprint 544, changing the list key from domain-specific (`clients`, `engagements`, `activities`) to generic (`items`) required updating 4 routes, 4 hooks, 3 type files, and 4 test files. Missing any one creates silent data loss (hook reads `data.items` but API returns `data.clients` → empty list). **Pattern:** Before making a breaking shape change, `grep` for ALL consumers of the old key across both backend and frontend.

---

## Mypy error counts can explode silently with test file growth (Sprint 543)

A deferred item from Sprint 475 said "68 errors across 2 files." By Sprint 543, the same `mypy tests/` command showed 804 errors across 135 files because 133 test files had been added since the original estimate. **Pattern:** Deferred items with numeric estimates should include a "last measured" date. Re-measure before committing to a sprint scope.

---

## Cover page metadata must propagate through ALL code paths, not just one (Sprint 541)

When a fix is applied to a shared field (like `fiscal_year_end` on `ReportMetadata`), verify every code path that constructs that metadata — not just the one that triggered the bug report. Sprint 540 fixed `fiscal_year_end` for financial statements only (`pdf_generator.py`), missing the 17 testing/tool memo generators that construct `ReportMetadata` via a different path (`generate_testing_memo()` + custom generators). **Pattern:** When fixing a shared data structure, `grep` for ALL constructor call sites. If N call sites exist and only 1 was fixed, the remaining N-1 are still broken.

---

## New severity tiers require three-layer propagation: engine → score → UI (Sprint 538)

1. **Tier cascade ordering must respect keyword intent over general-purpose rules.** Sprint 537 added an "informational" tier for transactional accounts (Cash, AR, AP), but placed the keyword check AFTER the 10%-of-TB escalation. For entities with concentrated cash positions (>10% of TB), Cash would be escalated to "material" before the informational check could downgrade it — defeating the Sprint 537 design intent entirely. **Pattern:** When adding a new classification tier with explicit keyword lists, the keyword check must precede any general-purpose escalation rule. Keyword assignments are specific; escalation rules are general. Specific should override general.

2. **New severity tiers need score contribution caps.** Each informational finding contributed +1 risk point with no cap. For a bank with 30 transactional accounts, that's 30 points from informational findings alone — pushing the score into "elevated" (threshold: 26). Informational findings are definitionally low-signal; their aggregate should never independently change the risk tier. **Pattern:** When adding a new lowest-severity tier, always cap its score contribution (e.g., `min(count, 5)`) so the tier cannot overwhelm the scoring model.

3. **Bare substring keywords need scope validation against other detection systems.** The bare keyword `"cash"` in the informational list matched "Cash Clearing" (a suspense concern) and "Cash — Intercompany" (a related-party concern). Similarly, `"loan"` in the suppress list matched "Shareholder Loan" (a related-party concern). **Pattern:** When adding keywords to any classification list, grep all other keyword lists (suspense, related-party, carve-outs) for conflicts. If the same account name triggers contradictory signals, narrow the keyword or add a carve-out.

---

## PDF report totals must match displayed detail rows (Sprint 522)

The Minor Observations total was summing `abs(amount)` while detail rows displayed signed values. Any CPA would catch a total of $107,900 when the visible amounts sum to $58,900. **Pattern:** When a total row summarizes a visible column, the aggregation function must match the display function exactly — no silent transformations. If signed display is confusing in context, add a footnote rather than silently changing the math.

---

## Risk scores require transparency — unexplained numbers are arbitrary (Sprint 522)

A composite risk score (52/100 — HIGH RISK) presented without decomposition invites skepticism. Returning factor-level contributions from `compute_tb_risk_score()` as a tuple `(score, factors)` was a minimal change (10 lines) that made the output auditable. **Pattern:** Any computed metric in a professional deliverable should expose its inputs. If the scoring function returns a single number, refactor it to return `(result, explanation)`.

---

## Directive Protocol is non-negotiable — urgency does not waive documentation (Audit 29)

Sprint 520 fixed a CRITICAL cross-tenant data leakage vulnerability and 3 other billing security findings — the most security-sensitive sprint in the project's history — with zero todo.md presence. Sprint 516 (DEC remediation, 17 findings) had the same gap. Both bypassed the Directive Protocol entirely: no plan, no checklist, no verification section, no commit SHA recorded, no lessons captured. Sprint 519 (architectural refactoring) in the same cycle got full lifecycle tracking.

**Root cause:** Urgency bias. Security-critical work feels time-sensitive, creating a "just commit it" impulse that skips documentation. But security sprints warrant MORE documentation discipline, not less — they are the sprints most likely to be audited, questioned, or referenced later.

**Enforcement:** A `commit-msg` hook now rejects any commit matching `Sprint N:` unless `tasks/todo.md` is staged. This makes the protocol mechanically enforced, not discipline-dependent. Hotfix commits (`fix:` prefix) are exempt by design.

**Pattern:** Never skip the Directive Protocol for any sprint-classified work. If the work is urgent, write a minimal todo.md entry (sprint number, goal, verification result, SHA) — 5 lines takes 2 minutes and creates an audit trail. The commit-msg hook is the backstop, not the primary discipline.

---

## Billing security patterns — tenant isolation, Stripe line items, webhook idempotency (Sprint 520)

1. **Billing analytics endpoints must scope queries by user_id/org_id from the start.** The analytics module (`billing/analytics.py`) had 5 metric queries that returned global aggregates — any verified user could see all customers' billing data. The fix (`_resolve_scoped_user_ids()`) resolves org membership and scopes every query. **Rule:** When writing any new billing analytics query, always accept a `user_id` or `user_ids` parameter and filter by it. Never write an unscoped aggregate in billing code.

2. **Stripe subscription line items must be matched by price ID, not by index.** `add_seats` and `remove_seats` assumed the seat add-on was always `subscription.items[0]`. For subscriptions with multiple line items (plan + seat add-on), this targeted the wrong item — mutating the plan price instead of the seat quantity. **Rule:** Use `_find_seat_addon_item()` with `get_all_seat_price_ids()` to find the correct line item. Only fall back to `items[0]` for single-item subscriptions. Raise `ValueError` for ambiguous multi-item subscriptions rather than guessing.

3. **Webhook handlers must deduplicate by event ID before dispatch.** Stripe can replay webhook events (retries, manual resends). Without deduplication, the same event could be processed twice — creating duplicate billing events, double-counting revenue, or applying discounts twice. **Rule:** Record `stripe_event_id` in a `ProcessedWebhookEvent` table before dispatch. Return 200 immediately for duplicates. This is a Stripe best practice that should have been implemented from Sprint 362 (initial webhook handler).

4. **Billing event enum variants must match Stripe event semantics precisely.** `handle_subscription_trial_will_end` was recording `TRIAL_EXPIRED` — but the trial hasn't expired yet, it's about to end. This mislabels the billing timeline and corrupts analytics. **Rule:** When mapping Stripe webhook event types to internal enums, the enum value must describe the state AT the time the event fires, not a future state.

---

## Procedure text and score labels must be contextually differentiated, not template-driven (Sprint 524)

Sprint 522 introduced suggested procedures and risk decomposition, but the initial implementation used generic templates. All round-dollar findings got the same procedure language regardless of whether it was a single $100K balance or an 8-occurrence pattern. Score decomposition showed "Material exceptions (3 × 8)" — a formula, not a finding. A CPA reviewer reads the procedure as guidance for their next step; if two findings with different risk profiles receive identical procedures, the output looks machine-generated rather than analytically informed.

**Pattern:** When generating professional deliverable text (procedures, labels, descriptions), the function must inspect enough anomaly context (anomaly_type, account name, transaction_count, issue text) to produce differentiated output. If two findings produce identical text, that's a design defect. Split procedure keys by relevant sub-patterns (single vs. repeated, AR vs. general asset) and use data-driven dispatch.

---

## Council deferral vs. CEO override — respect the decision hierarchy (Sprint 519)

The council (Critic + Guardian) recommended deferring Phase 5 service extraction due to diminishing ROI. The CEO overrode: "I also want architectural purity." The council's analysis was sound — the extractions were incremental, not transformative — but the CEO's architectural preference is a legitimate priority that outweighs marginal ROI calculations. **Pattern: council advises, CEO decides. When the CEO overrides, execute fully without half-measures. Log the override in todo.md for future context.**

---

## Task Management Archival Discipline (Audit 28 / Council Decision)

1. **Passive thresholds fail during sustained campaigns**: The 5-sprint archival threshold rule existed but was silently violated 12 times across 12 consecutive directive cycles during the Report Enrichment campaign (Sprints 499-515). A passive rule with no active trigger point is insufficient when sprint velocity is high. Fix: a proactive self-check added to Directive Protocol step 1 — "If Active Phase has 4+ completed sprints, archive first."

2. **The protocol assumed phased delivery; the project shifted to continuous delivery**: The Phase Lifecycle Protocol was designed for named phases with clear start/end boundaries. When work runs as a continuous campaign without phase declarations, the "wrap phase → archive" trigger never fires. The 5-sprint standalone threshold was designed as a patch for this gap but depends on agents counting sprints — which they don't do naturally. The self-check guardrail fires at step 1 of every directive, creating a reliable trigger.

3. **Non-sprint commits need a lightweight tracking mechanism**: The Directive Protocol's binary model (everything is a sprint) creates overhead aversion for small fixes. Commit `fb8a1fa` (22 insertions across 16 files) was a content accuracy fix that didn't warrant a full sprint lifecycle. Fix: a `## Hotfixes` section in todo.md with one-line entries, and a classification rule (step 1b) distinguishing sprint-level work from hotfix-level work.

---

## Anomaly Summary Report (Sprint 515)

1. **Auditing standards vs. FASB codification**: The anomaly summary is an engagement-level aggregation report, not a tool-specific diagnostic. Its authoritative references should cite auditing procedure standards (AU-C § 265/330/520, PCAOB AS 1305/2305) rather than FASB ASC codification entries. Render these directly in the generator rather than through the YAML content library, since they don't follow the codification/statement schema.

2. **Phantom trailing pages from standalone disclaimers**: When a report ends with a standalone `Paragraph(DISCLAIMER_TEXT, ...)`, the PDF renderer may place it on a new page — creating a phantom blank page with only a disclaimer. Since `draw_page_footer` already renders the disclaimer on every page footer, the trailing standalone disclaimer is redundant and should be removed.

3. **Cross-reference mappings should be exhaustive**: When adding WP-XXX-001 cross-references for findings, map every ToolName enum value — not just the tools that happened to have findings in the sample data. This prevents KeyError when a new tool generates findings in production.

---

## Accrual Completeness Estimator (Sprint 513)

1. **Account classification ordering matters**: When classifying liability accounts into analytical buckets, check the most specific patterns first. "Deferred Revenue" must match before generic "deferred" to avoid misclassifying it as "Deferred Liability". The ordering (deferred revenue → accrued → provision → generic deferred) is critical.

2. **MemoSubsection style doesn't exist**: The `create_memo_styles()` from `memo_base.py` does not include a "MemoSubsection" style. For subsection headings within a section, use `<b>Bold text</b>` within a "MemoBody" paragraph instead of referencing a nonexistent style key.

3. **Analytical ratio integrity**: When a ratio calculation includes unrelated account types (e.g., Deferred Revenue in an accrual completeness ratio), the conclusion can flip from "fail" to "pass" — a material analytical error. Always validate that only accounts relevant to the metric feed into the calculation.

---

## Population Profile Report (Sprint 511)

1. **Sample data self-consistency**: When hardcoding sample report data, verify mathematical invariants (e.g., bucket sums = total, all accounts in a bucket meet the bucket's threshold). The original data had 7 accounts in the >$1M bucket summing to $4,250,000 — an impossibility since 7 accounts each >$1M must sum to at least $7M. Work backward from the total when designing bucket distributions.

2. **Gini threshold changes break Literal types**: Changing Gini interpretation labels (removing "Very High") requires updating Pydantic response schema Literal types, not just engine constants. Always search for the old labels in schema files.

3. **Shared modules enable rapid feature development**: The existing `shared/benford.py` module let us add Benford's Law to the population profile in minutes. Worth investing in shared engine modules when a feature will appear in multiple reports.

---

## Data Quality Pre-Flight Report (Sprint 510)

1. **Test data for balanced TB**: When adding a TB balance check, existing test data that was "clean" may no longer be clean if debits != credits. The original clean file test had debits=1500, credits=3500 — unbalanced. Always verify test fixture data satisfies ALL quality checks, not just the ones originally tested.

2. **Weight redistribution requires test assertion updates**: When redistributing scoring weights (e.g., adding a new 25% component), existing tests that assert on score thresholds will break. A column_detection HIGH issue with weight 30 produces score 70, but with weight 20 produces score 80 — changing the pass/fail boundary. Update score threshold assertions whenever weights change.

3. **`_calculate_readiness` should return breakdown alongside score**: Rather than computing score separately and then reconstructing the breakdown, having the function return both as a tuple ensures the displayed breakdown is always mathematically consistent with the displayed total. This prevents the "displayed score doesn't match displayed components" bug pattern.

---

## Multi-Currency Conversion Report (Sprint 509)

1. **Sample data counts must match list lengths**: The sample data had `unconverted_count: 12` with only 4 items in `unconverted_items`. The engine keeps these in sync, but hardcoded sample data didn't. The memo generator now defensively derives the displayed count from `len(truly_unconverted)` rather than trusting the separate count field. When a scope metric references a detail table, always derive the metric from the actual data, not a separate field.

2. **Rate source attribution belongs to the caller, not the generator**: The memo generator cannot know whether rates came from Reuters, Bloomberg, or manual entry. The methodology text should describe what the system does ("converts using provided closing rates") not claim a specific data source. The `source_context_note` field is the caller's responsibility.

---

## Statistical Sampling Evaluation Report (Sprint 508)

1. **Sample report values must be computed from engine formulas, not hardcoded**: The sampling evaluation sample data had Basic Precision = $25,000 (1 × SI), but the engine computes BP = SI × CF = $25,000 × 3.0 = $75,000. With EM = 0, BP always equals TM, making any PASS conclusion with errors arithmetically impossible. When hardcoding sample data for report generators, verify self-consistency by computing values through the actual engine formulas (or at minimum, manual arithmetic that matches the engine).

2. **Sampling interval depends on expected misstatement**: With EM > 0, the engine computes SI = (TM - EM) / (CF × (1 + EM/TM)), which is smaller than the EM = 0 case (SI = TM/CF). This smaller interval produces BP < TM, allowing room for errors while maintaining a PASS conclusion. Sample data that sets both EM > 0 and SI = TM/CF is self-contradictory.

3. **Phase-gated content prevents wrong-context sections**: The evaluation report was showing design-phase next steps ("select and test items") even though testing was already complete. Using an `is_evaluation` flag to swap entire section content (not just tweak wording) ensures each report phase is coherent end-to-end.

---

## Analytical Procedures Report (Sprint 505)

1. **Keyword matching for financial categories must exclude contra-items**: "Deferred Revenue" was matching the revenue keyword ("revenue" substring), inflating revenue totals and corrupting GPM ratios (59.2% instead of 58.6%). Add explicit exclusion lists (`_REVENUE_EXCLUSIONS = ["deferred revenue", "unearned revenue"]`) and prefer `account_type` field when available over keyword matching.

2. **Ratio computations must use the full TB population, not just significant movements**: The significant_movements list is a filtered subset (~30 of 247 accounts). Computing ratios from this subset produces materially wrong results because it misses revenue lines that aren't individually significant but aggregate to the full balance. Always pass `all_movements` to ratio functions.

---

## Revenue Report Enrichment (Sprint 501)

1. **Sample data test_keys must match engine canonical keys**: The revenue sample report used human-friendly test_keys (`round_amounts`, `cut_off_risk`, `recognition_timing`) that didn't match the engine's canonical keys (`round_revenue_amounts`, `cutoff_risk`, `recognition_before_satisfaction`). This caused blank methodology descriptions and missing follow-up procedures in sample PDFs. Always copy test_keys from the engine, not from the test names.

2. **Follow-up procedures need ALL test_key variants**: The revenue engine added 4 contract-aware tests (ASC 606) in Sprint 352 but never added their test_keys to `follow_up_procedures.py`. Every new test added to any engine must have a corresponding entry in the shared follow-up procedures dict.

---

## Payroll Report Enrichment (Sprint 500)

1. **Sample report risk_tiers were systematically inverted**: All 7 standard testing reports had hardcoded `risk_tier` values that didn't match the `score_to_risk_tier()` function boundaries. Scores 15-25 were labeled "elevated" (should be "moderate") and 28.3 was labeled "moderate" (should be "elevated"). When using synthetic data in sample generators, always derive the risk_tier from the score using the same function the engine uses, rather than hardcoding.

2. **Finding formatter must not duplicate data already in issue text**: When `amount` is both embedded in the finding `issue` string and also provided as a separate `amount` field, the formatter will show the amount twice. Either put the amount in the issue text OR in the amount field, never both.

3. **Scope builder closures enable payroll-specific enrichments without modifying the shared template**: Using closure-based `build_scope` callbacks that capture the full result dict allows tool-specific sections (GL reconciliation, headcount, department summary) to be added within the standard Scope section without changing the shared `memo_template.py` interface.

---

## Digital Excellence Council Remediation (Sprint 497)

1. **Pricing model changes cascade across 10+ test files**: Renaming `diagnostics_per_month` → `uploads_per_month` and changing Solo from limited→all-access broke tests in entitlements, parity, audit API, billing routes, and pricing launch validation. When entitlement fields are renamed or tier capabilities change, grep all test files for the old field name — don't rely on import errors alone since tests often reference field names as strings in assertions.

2. **Patching internal functions requires checking if they were refactored**: `_load_seat_price_ids` was split into `_load_pro_seat_price_ids` and `_load_ent_seat_price_ids` during Pricing v3, but 5 test patches still referenced the old function. When refactoring internal helpers, search for all `patch("module._function_name"` references in tests.

3. **ISA sub-paragraph citations (e.g., ISA 240.A40) are risky**: Application material paragraphs like ".A40" are renumbered between ISA revisions, making them fragile citations. Prefer citing the standard number only (ISA 240) unless quoting a specific, stable paragraph in a known revision.

4. **Audit terminology must stay neutral**: Replacing "exhibits a HIGH risk profile" with "returned HIGH flag density across the automated tests" is important — the platform flags data patterns, it doesn't assess audit risk (ISA 315 domain). Language that implies the tool performs risk assessment crosses the assurance boundary.

5. **SQLite schema drift causes silent lockout**: When models add new columns (like `organization_id`), the file-based `paciolus.db` doesn't auto-migrate. This causes `OperationalError` on queries touching the new column. Adding explicit SQLite migration in `init_db()` catches this at startup.

---

## Engineering Process Hardening (Sprint 496)

1. **1,345 frontend tests were never gated in CI**: The test suite existed locally but `ci.yml` only ran `npm run build` and `eslint`. A developer could break tests and merge without CI catching it. Always add test execution as a blocking CI job the same sprint you establish the test suite.

2. **mypy achieved 0 errors but wasn't enforced**: Achieving zero errors is wasted effort if CI doesn't prevent regression. Type checking must be a blocking CI gate, not just a developer-run tool.

3. **Secrets scanning is a CI primitive, not an afterthought**: Without automated secrets scanning, committed credentials (Stripe keys, JWT secrets) rely entirely on `.gitignore` and developer discipline. TruffleHog in CI + pattern matching in pre-commit provides two-layer defense.

4. **GitHub Actions default permissions are `write-all`**: Without an explicit `permissions:` block, every workflow job gets write access to repository contents, packages, and more. Always declare least-privilege permissions at the workflow level.

5. **CODEOWNERS without branch protection is advisory-only**: The file only enforces review requirements when "Require review from Code Owners" is enabled in branch protection settings. Document this CEO action.

---

## Data Hardening Security Audit (Sprint 494)

1. **DATABASE_URL credential exposure in startup logs**: The `print_config_summary()` function truncated DATABASE_URL at 50 chars — but PostgreSQL URLs like `postgresql://user:password@host:5432/db` fit within 50 chars and expose plaintext credentials. Always mask credentials in connection strings before logging, regardless of truncation.

2. **`detail=str(e)` is the #1 error leakage vector**: Six route endpoints passed raw exception messages directly to API clients. Even custom domain exceptions (InvalidTransitionError, RateValidationError) should route through `sanitize_error()` with `allow_passthrough=True` rather than raw `str(e)`, because upstream callers might catch broader exception types that include library internals.

3. **`allow_passthrough` in `sanitize_error()` needs a safety net**: Business-logic passthrough still needs to block messages containing file paths, SQL fragments, or stack traces. The pattern check should happen *before* passthrough, not just on the "known dangerous" patterns.

4. **FastAPI docs/OpenAPI must be disabled in production**: Swagger UI at `/docs` exposes all endpoints, parameter schemas, and internal model structures. Set `docs_url=None, redoc_url=None, openapi_url=None` in production.

5. **`logger.error("...%s", e)` can leak Stripe/AWS credentials**: Even though Stripe SDK generally redacts keys, the full exception string can contain customer IDs, request IDs, or error metadata that aids attackers. Log `type(e).__name__` instead.

6. **Excel formula injection applies to openpyxl too, not just CSV**: `sanitize_csv_value()` must wrap ALL user-controlled strings written to Excel cells via `ws.cell(value=...)` or `ws["A1"] = ...`. In openpyxl, a string starting with `=` becomes a formula. Cover: entity names, account names, prepared_by/reviewed_by, filenames, and financial statement labels. Indentation (spaces prepended) naturally prevents formula interpretation, but sanitize the raw value before indentation for defense-in-depth.

7. **UNKNOWN format fallback should reject known binaries**: When `detect_format()` returns UNKNOWN and the filename doesn't match Excel extensions, the fallback parses as CSV. This produces garbage data if the file is actually a binary format (XLSX/XLS/PDF) that slipped through detection. Add magic byte checks before the CSV fallback.

8. **In-memory stores need scheduled cleanup, not just eviction-on-insert**: `OrderedDict` job stores with TTL eviction only on new inserts can accumulate stale entries during quiet periods. Add a scheduled cleanup job to supplement insertion-time eviction.

---

## Access Hardening Security Audit (Sprint 493)

1. **FastAPI dependency functions cannot be called manually with positional args matching DI**: Functions like `check_seat_limit(user, db)` use `Annotated[User, Depends(require_current_user)]` which FastAPI resolves automatically. When calling manually, you must pass the actual User object and Session — the Depends metadata is ignored. Multiple entitlement checks were broken because they were called as `check_func(db, user.id)` instead of `check_func(user, db)`.

2. **Registration duplicate-email messages enable account enumeration**: A distinct "email already exists" error lets attackers probe for valid accounts. Use a generic message ("Unable to create account") that doesn't reveal whether the email is registered.

3. **Organization invite tokens should be bound to the invitee email**: Without email matching, any authenticated user who obtains a leaked invite URL can join the organization. Always verify `user.email == invite.invitee_email` on acceptance.

4. **Billing analytics endpoints need explicit role checks**: `require_verified_user` alone is insufficient for sensitive business data endpoints — any verified free-tier user could access global billing metrics without an admin/owner role check.

5. **Content-Disposition filenames from user input need sanitization**: User-controlled strings in `Content-Disposition` headers can inject control characters (`\r\n`). Sanitize with `re.sub(r'[^\w\-]', '_', name)` before embedding in headers.

---

## Formula Consistency & Efficiency Hardening (Sprint 492)

1. **Operating margin fallback must guard negative derived opex**: When `total_expenses < COGS` and `operating_expenses == 0`, the derivation `total_expenses - COGS` produces negative operating expenses, yielding economically invalid 100% margins. Guard: return N/A when derived value < 0 or total_expenses == 0.

2. **`calculate_all_ratios` computes CCC components twice**: DSO/DPO/DIO are computed individually and again inside `calculate_ccc()`. Fix: compute once and pass via keyword arguments. Same pattern applies to any composite metric built from sub-metrics.

3. **Existing edge-case tests may assert buggy behavior**: The `test_operating_margin_negative_derived_opex` test asserted `is_calculable is True` for a clearly invalid input. When hardening edge cases, audit existing tests for assertions that enshrine incorrect behavior.

4. **Test fixtures missing key fields affect edge-case tests**: `test_very_large_numbers` omitted `total_expenses`, which hit the new opex guard. Always include all expense-related fields in fixtures testing comprehensive ratio calculation.

---

## Digital Excellence Council Remediation (Sprint 491)

1. **Scout agent claims require independent verification**: The Scout flagged "16 untested engine modules" as CRITICAL. Actual count: 11 engine test files already existed. Always grep-verify quantitative claims before planning work based on them.

2. **Assurance-boundary language is a legal risk, not a security risk**: The Guardian agent gave a clean security audit while the Critic found 5 phrases that could expose the platform to auditor-judgment boundary challenges. Cross-domain risks (legal, regulatory, reputational) don't map cleanly to single-agent domains — the IntegratorLead must synthesize across agent perspectives.

3. **Standard citations matter more than feature work**: The JE memo cited PCAOB AS 1215 (Audit Documentation) as the governing standard for journal entry fraud testing. The correct standard is PCAOB AS 2110 (Risk Assessment). A PCAOB-registered firm would immediately flag this. Two-line fix, but the credibility risk was the highest-impact finding in the entire council session.

4. **Batch common patterns, then do tool-specific work**: The follow-up procedures gap affected 12+ tools. Batching all 52 new procedures in one sprint (37→89 total) is far more efficient than the one-report-at-a-time approach used in Sprints 488-490.

---

## HeroProductFilm Redesign (Sprint 480)

1. **Never hard-gate on `prefers-reduced-motion`**: The previous pattern (`if (prefersReducedMotion) return <StaticFallback />`) hid the entire scrubber UI from users whose OS disabled animations (Windows 11 default). The correct approach: always render the full UI, use `<MotionConfig reducedMotion="user">` to let framer-motion handle the preference gracefully (instant transitions instead of no UI).

2. **Phase-based animation in crossfade layers**: Layers driven by opacity MotionValues are always in the DOM. Internal animations should NOT use `whileInView` (fires once on viewport entry, not on step activation). Instead, pass `isActive` boolean and use `usePhaseTimer` to drive sequential animation phases that reset/replay on each step visit.

3. **`useCountAnimation` with rAF**: For counting animations (0→108 tests, 0→2.4MB), `requestAnimationFrame` with ease-out cubic produces smoother results than `setInterval` with fixed steps. The rAF approach also naturally syncs with the display refresh rate.

---

## Remediation Completeness (Sprint 482 / Audit 25)

**Pattern:** When fixing a pattern-based finding (e.g., f-string SQL, `status_code=200`, `animate-pulse`), partial fixes are marked COMPLETE without verifying that ALL instances were addressed. Sprint 479 fixed f-string SQL in `test_timestamp_defaults.py` but left 3 instances — caught by the council audit. Sprint 479 removed `status_code=200` from 3 endpoints but missed the accrual-completeness endpoint — caught by the council audit.

**Rule:** Before marking any pattern-based remediation finding as complete, run a codebase-wide grep for ALL remaining instances of the pattern. If the grep returns results, fix them or document why they are intentionally excluded. A partial fix is an incomplete remediation, not a closed finding.

**Prevention:** After applying a fix, immediately run: `grep -r "<pattern>" <scope>` to verify zero remaining instances. Record the grep command and "0 results" in the sprint checklist.

---

## Verification Gate Discipline

### npm test Must Run Full Suite — Never Targeted Subsets
**Recurrence:** Audit 20 identified the npm test gap. Audit 21 confirmed the gate was added but not executed. Audit 22 confirmed recovery (52 failures caught). Audit 23 found non-execution again with targeted suites (31/31 affected) used instead of full suite — exactly the pattern Audit 22 predicted as "gate fatigue." **Rule:** For ANY commit touching `.tsx`, `.ts`, or test files, run `npx jest --no-coverage` (full suite) and record "npm test: X suites, Y tests passing" in the todo.md verification section. Targeted suite results (e.g., "31/31 affected suites") are insufficient — cross-file regressions only surface in the full suite. This gate has the same mandatory status as `npm run build`.

### Ad-Hoc Creative Work Still Requires Todo Entries
Component rewrites, copy revisions, and visual redesigns are non-trivial work even when they feel like creative sessions rather than engineering sprints. The VaultTransition rewrite (345 changed lines), HeroProductFilm rewrite (574 changed lines), and About page revision (119 changed lines) were all committed without todo.md entries, creating audit trail gaps despite strong code quality. **Rule:** Any commit that modifies more than ~50 lines or rewrites a component gets a brief todo.md entry (goal, status, verification, commit SHA) — regardless of whether it was planned in advance or done ad-hoc. A retroactive entry immediately after commit is acceptable; no entry at all is not.

---

## Motion System Migration

### Reveal Component Requires Hook Mocks in Tests
When the `<Reveal>` component (or any wrapper) uses `useInView` and `useReducedMotion` from framer-motion, all test files that render components containing `<Reveal>` — even transitively — must include these hooks in their framer-motion mock. The standard framer-motion mock pattern (`motion: { div: ..., span: ... }, AnimatePresence: ...`) is insufficient. Add `useInView: () => true, useReducedMotion: () => false` to every framer-motion mock that renders components using Reveal.

### Deprecation Over Deletion for Shared Token Files
When consolidating motion tokens from 4 files into 1, mark superseded exports with `@deprecated` JSDoc rather than deleting them immediately. This allows consumers that import directly (not through barrel files) to continue working while providing IDE warnings. Remove barrel re-exports first (breaking the "easy path"), then deprecate source exports (warning the "direct path").

---

## Pricing Restructure (Sprint 452)

### Pydantic Schema Bound Changes Break Downstream Validation Tests
When changing a Pydantic field constraint (e.g., `seat_count: int = Field(le=22)` → `le=60`), existing tests that rely on the OLD boundary being rejected will silently fail — the value that was invalid is now valid. Always search for hardcoded boundary values in all test files when changing Pydantic `le`/`ge`/`max_length` constraints. In this case, `test_team_seat_23_rejected_by_schema` expected `seat_count=23` to raise `ValidationError`, but after the constraint changed to `le=60`, it no longer did.

### Tool Set Changes Cascade to Tier-Parity Tests
When moving tools between tiers (e.g., `revenue_testing` from Solo→Team), tests asserting "Professional mirrors Solo tools" will break if they check for the moved tool specifically. Parity tests should either (a) test the full set equality, or (b) test for tools that REMAIN in the tier, not tools being moved out.

---

## Brand Voice Alignment

### Performance Claims Must Reference a Canonical Source
Marketing copy contained four different timing claims (`< 1s`, `< 2s`, `< 3s`, `< 5s`) across different pages with no canonical constant backing any of them. The deployment architecture doc (`DEPLOYMENT_ARCHITECTURE.md`) defines the only measurable targets: p95 alert threshold >3 seconds, verification target <5 seconds for 10K rows. All marketing performance claims should derive from and reference this document. Creating a canonical constant or config value would prevent future drift.

### Storage Claims Must Distinguish Server-In-Memory from Browser-Only
The HeroProductFilm component claimed "Processed entirely in your browser. Your data never left this tab." — factually false since analysis runs on FastAPI servers. This contradicted the existing lessons.md entry about the same issue. Copy review processes should cross-reference lessons.md known errors before sign-off.

### Self-Assessed vs. Independently Attested Compliance Must Be Visually Distinguished
The trust page listed GDPR and CCPA as "Compliant" alongside SOC 2 Type II "In Progress" without clarifying that GDPR/CCPA compliance was self-assessed. For a product targeting financial professionals (who understand audit distinctions), this ambiguity erodes trust. Always separate "implemented controls" from "independently attested" status.

### "Zero-Knowledge" Is a Cryptographic Term — Don't Apply It to In-Memory Processing
"Zero-knowledge" has a precise cryptographic meaning (zero-knowledge proofs / ZKPs): a prover demonstrates knowledge of a secret without revealing it. Applying it to "data processed in-memory and discarded" is a factual error. The correct term for Paciolus's architecture is "Zero-Storage" — data is never written to disk or database, but the processing is server-side, not cryptographically zero-knowledge. Always audit marketing copy for cryptographic term misuse.

### Never Claim Client-Side Processing for Server-Side Work
FeaturePillars previously stated "All analysis happens locally in your browser / processed client-side." Paciolus analysis runs on FastAPI servers — only the UI is client-side. The correct claim is that data is processed in-memory on the server and immediately discarded. The security guarantee is zero retention, not zero server contact. Marketing copy must match the actual architecture.

### Concrete Outcomes Beat Generic Benefits in Brand Copy
"Enterprise-grade diagnostic intelligence without the enterprise complexity" is a category cliché — every enterprise software product uses this framing. "What used to take days now takes seconds" is concrete, verifiable, and specific to the actual problem being solved. Lead with the outcome, not the category.

---

## Security Sprint: Billing Redirect Integrity

### Server-Side URL Derivation > Allowlist Validation for Redirect Security
When a redirect URL is only ever one of two values (`/checkout/success` and `/pricing`), the correct control is to derive both server-side from `FRONTEND_URL` — not to validate user-supplied strings against an allowlist. Allowlist approaches require URL parsing and are vulnerable to Unicode normalization, subdomain squatting, and path traversal bypasses. Full derivation eliminates the attack surface entirely because no user input touches the field at all.

### Pydantic `model_validator(mode='before')` Fires Before `extra='ignore'` Strips Fields
A `model_validator(mode='before')` receives the raw input dict including extra fields that `extra='ignore'` will subsequently discard. This makes it the correct place to monitor for injection attempts: the validator increments a Prometheus counter for each URL field detected, then returns the dict unchanged. Pydantic's field-stripping happens afterward, so the final model object never has those fields. This pattern gives both detection and elimination.

### Old Required-Field Tests Must Be Replaced When Fields Are Removed
Two tests in `test_pricing_launch_validation.py` expected `ValidationError` when `success_url`/`cancel_url` were omitted — because they were formerly required fields. After removing those fields, those tests silently passed with no assertion. The fix: replace with positive assertions that verify the new behavior (fields not on model, silently ignored when supplied). Always check for inverted-expectation tests (`pytest.raises(ValidationError)`) when removing required fields.

---

## Zero-Storage Architecture v2.1 Consistency Pass

### "Zero-Storage" Is a Scope Claim, Not an Absolute Claim
The phrase "zero-storage" can be misread as "we store nothing at all." In reality it means "no persistence of line-level financial data." Compliance documents must explicitly disambiguate this — a "Terminology Clarity" callout and a "Scope Boundaries" preamble in the compliance implications section prevent overstated claims and reduce legal exposure. When adding marketing-friendly labels to architecture docs, always include a definition box that states what the term covers and what it does not.

### Cross-Doc Retention Alignment Is a Recurring Maintenance Task
Every time a retention value changes (e.g., "2 years" → "365 days"), all 4 compliance docs (Zero-Storage, Privacy, Security, ToS) must be updated in lockstep. A grep for the old value across `docs/04-compliance/` is the minimum verification step before closing a retention-related directive. The v2.0 pass already fixed "2 years" → "365 days" everywhere, so the v2.1 pass found nothing to fix — but the verification step confirmed consistency and should never be skipped.

### Control Verification Tables Add Auditor-Ready Evidence
Listing automated safeguards (retention cleanup, ORM deletion guard, memory_cleanup, Sentry stripping, CI policy guard) in a structured table with mechanism + frequency columns gives auditors and enterprise customers a concrete checklist to verify. This is more useful than narrative descriptions because each row maps to a specific code path they can inspect.

---

## Phase LXIV: HttpOnly Cookie Session Hardening

### CSRF_EXEMPT_PATHS Changes Require a Test Audit Pass
When adding or removing a path from `CSRF_EXEMPT_PATHS` in `security_middleware.py`, the CSRF test suite in `test_csrf_middleware.py` contains tests that directly assert membership in that set. These tests will fail silently if not updated — "silently" meaning they fail the suite but the intent (asserting the *old* policy) is wrong. When `/auth/logout` was removed from `CSRF_EXEMPT_PATHS`, four test cases needed updating: `test_auth_logout_exempt` (inverted to `not in`), `test_all_new_exempt_paths_pass` (path removed from tested list), `test_logout_exempt_documented` (checked for old comment text), and `test_exempt_set_is_frozen` (expected set updated). **Rule:** Any `CSRF_EXEMPT_PATHS` change must be followed by `grep -n "auth/logout\|CSRF_EXEMPT" backend/tests/test_csrf_middleware.py` (substituting the affected path) to find all assertions before running the suite.

### Mandatory Directive Protocol Applies to Security Sprints Too
Security hardening sprints (auth migration, CSRF changes, cookie policy) are often well-planned but executed with urgency, creating a tendency to skip the todo.md entry. The plan file (`.claude/plans/`) is not a substitute — the mandatory directive protocol requires writing the plan to `tasks/todo.md` as a checklist before implementation begins, regardless of sprint type. Skipping this step leaves no incremental tracking record, no review section with commit SHA, and no deferred item closure trail. The code quality is unaffected; the auditability is not.

---

## Sprint 448: pandas 3.0 Evaluation

### pandas 3.0 String Dtype: `dtype == object` Guard Breaks for CSV String Columns
**Correction:** pandas 3.0 uses `pd.StringDtype()` (displayed as `str`) for string columns read from CSV, replacing the old `object` dtype. Any guard of the form `if df[col].dtype == object:` silently skips string columns entirely, disabling the check.
**Root Cause:** The `dtype == object` pattern was valid for pandas 2.x but is not forward-compatible with pandas 3.0's new default string storage.
**Impact Found:** `shared/helpers.py:571` — cell-length protection for CSV uploads was bypassed. A cell with 100,001 characters would pass through without raising `HTTPException(400)`.
**Fix:** Replace `df[col].dtype == object` with `pd.api.types.is_string_dtype(df[col])`. This API returns True for both `object` dtype (pandas 2.x) and `pd.StringDtype()` / `str` dtype (pandas 3.0+).
**Prevention Rule:** Never use `dtype == object` to identify string columns. Always use `pd.api.types.is_string_dtype()`. Grep for `dtype == object` after any pandas major version bump.

### Dependabot Merges of Deferred Risky Dependencies Still Require the Evaluation Sprint
A dependency listed in the Deferred Items table as "needs dedicated evaluation sprint" is not closed by a green test suite alone — it requires the explicit evaluation (CoW audit, dtype verification, perf baseline). The test suite passing is a necessary condition but not sufficient. Merging via dependabot does not substitute for the evaluation. **Rule:** When a deferred item's dependency is merged, immediately schedule the evaluation sprint and run it before the next unrelated sprint begins. Update the Deferred Items table with evaluation findings.

### pandas 3.0 CoW Patterns That Are Safe (Verified 2026-02-27)
- `df = df.copy()` before column mutation — SAFE
- `df.iloc[start:end].copy()` for chunked processing — SAFE
- `df.drop(columns=[...], inplace=True)` for `drop` specifically — SAFE (not deprecated in 3.0)
- Dict-based `accumulator[key]["field"] += value` — SAFE (not a DataFrame operation)
- `df[col] = df[col].apply(...)` column reassignment — SAFE (not chained indexing)

---

## Phase LXII: Export & Billing Test Coverage (Sprint 447)

### ORM Model Must Be Imported at Collection Time for `create_all()` to Create Its Table
When writing tests for a model that isn't imported by `conftest.py` (e.g., `Subscription` from `subscription_model.py`), the `db_engine` session-scoped fixture runs `Base.metadata.create_all()` before the model is ever imported — so the table is missing. **Fix:** Add a top-level import in the test file (`import subscription_model  # noqa: F401`) so the model registers with `Base.metadata` during pytest collection, before the session fixture runs. This is a one-line fix, but the failure mode (`OperationalError: no such table`) is opaque.

### Route Integration Tests Must Mock Generators, Not Routes
Export routes that delegate to PDF/Excel generators (`generate_audit_report`, `generate_workpaper`, etc.) cannot be tested end-to-end without the full library chain. The correct pattern is to patch the generator at the import location in the route module (e.g., `patch("routes.export_diagnostics.generate_audit_report", return_value=b"%PDF-1.4 fake")`) and verify the HTTP status + response headers. This achieves >90% route coverage without requiring PDF/Excel test fixtures.

### Entitlement Factory Dependencies Can Be Called Directly as Python
`check_tool_access("tool_name")` returns an inner function `_dependency(user)`. In tests, call it as `dep = check_tool_access("tool_name"); dep(user=user)` — no FastAPI DI needed. This produces clean unit tests that run in milliseconds without a TestClient or database.

---

## Sprints 445–446: Coverage Analysis + Usage Metrics Review

### React 19 userEvent + Blur Validation: Same Pattern Applies Beyond Submit
The React 19 `userEvent` timing issue documented in Phase LXI also affects blur-triggered validation. A test using `user.type(input, 'A')` + `user.tab()` fails to trigger the `onBlur` validation error because the state update from typing may not flush before the tab event fires. **Fix:** Use `fireEvent.change(input, { target: { value: 'A' } })` + `fireEvent.blur(input)` — same synchronous fireEvent pattern as the submit fix. All input validation tests should use `fireEvent` not `userEvent` when testing value-dependent blur behavior.

### Route Coverage vs Engine Coverage Are Decoupled
Backend route files (`routes/export_diagnostics.py` at 17%, `routes/billing.py` at 35%) can have very low coverage even when their underlying engines are 100% covered. This is because route tests (HTTP-level) require a running TestClient and database fixtures, while engine tests (unit-level) only need Python imports. Route coverage gaps are high-risk because they miss auth guard enforcement, request parsing errors, response model validation, and middleware interactions — things the engine tests don't exercise.

### `pytest-cov` Is Not in Default Dev Dependencies
The `pytest-cov` and `coverage` packages were not installed in the backend venv. They must be installed manually for coverage runs. Add to `requirements-dev.txt` if one exists, or document in CONTRIBUTING.md as a prerequisite for local coverage analysis.

---

## Phase LXI: Technical Upgrades (Sprints 441–444)

### React 19 + jsdom: Form Submission Testing Pattern
React 19 changes how `requestSubmit()` works in jsdom, breaking tests that use `userEvent.click()` on submit buttons. `userEvent.type()` + `userEvent.click()` causes stale values because React batches state updates and the submit fires before re-render completes. **Fix:** Use `fireEvent.change()` (sets values synchronously) + `act()`-wrapped `fireEvent.submit(form)`. This pattern bypasses keyboard simulation timing issues entirely.

### useEffect Must Return on All Paths with `noImplicitReturns`
When `tsconfig.json` has `noImplicitReturns: true`, a `useEffect` with a cleanup return inside an `if` branch but no return on the else branch fails the build. Use early-return guard (`if (!condition) return;`) instead of wrapping the body in `if (condition) { ... return cleanup; }`.

### Test Suites Can Mask Schema Drift
`test_timestamp_defaults.py` used raw SQL `INSERT INTO clients` that was missing 3 NOT NULL columns added in later migrations (`reporting_framework`, `entity_type`, `jurisdiction_country`). Tests passed before because the columns were added after the test was written. When upgrading SQLAlchemy, stricter constraint enforcement can surface these mismatches. Keep raw SQL inserts in sync with current schema.

---

## Sprint 440: Billing Smoke Test

### Stripe API Errors Must Be Caught at the Route Level
All 6 billing endpoints that call Stripe (checkout, cancel, reactivate, add-seats, remove-seats, portal) were missing try/except around the Stripe SDK calls. When Stripe returns an error (e.g., business name not set, invalid subscription ID), the exception propagated to the global handler and produced a generic 500. Wrap all external API calls in try/except at the route level and return 502 ("Payment provider error") so users and frontend get actionable status codes. This is especially important because Stripe has many configuration prerequisites (business name, product creation, webhook setup) that may not be met in all environments.

### SQLAlchemy `Enum(PythonEnum)` Stores Member NAMES, Not Values
When using `Column(Enum(SubscriptionStatus))` with a Python `str` enum like `class SubscriptionStatus(str, Enum): ACTIVE = "active"`, SQLAlchemy stores the enum **member name** (`ACTIVE`) in the DB, not the value (`active`). Raw SQL inserts must use `'ACTIVE'` not `'active'`, or the ORM will fail with a `KeyError` when loading the row. This applies to all `Enum()` column types that reference Python enums.

---

## Sprint 439: BillingEvent Migration + Runbook Fix

### Model-Without-Migration Is a Silent Production Bomb
Phase LX defined `BillingEvent` in `subscription_model.py` and wired it into `analytics.py` + `webhook_handler.py`, but never created the Alembic migration. SQLite tests passed because the test harness uses `Base.metadata.create_all()`, which creates all tables from models directly — masking the missing migration. In PostgreSQL production, the table wouldn't exist. Lesson: after adding any new SQLAlchemy model, immediately verify it has a corresponding Alembic migration AND is imported in `env.py`. The test suite's `create_all()` is not a substitute for a real migration.

### Runbook Staleness After Enum Renames
The `starter → solo` rename (d9e0f1a2b3c4) updated `.env.example`, code, and tests, but missed `docs/runbooks/billing-launch.md` and `pricing-rollback.md` which still referenced `STRIPE_PRICE_STARTER_*`. Lesson: when renaming an enum value, grep ALL documentation (not just code + tests) for the old name. Runbooks and deployment guides are especially dangerous because they're used manually in production by people who won't get a compiler error.

---

## Pricing Launch Validation Matrix

### Frontend Tests: Prefer `getAllByText` Over `getByText` for Prices
When testing pages where the same text appears in multiple locations (e.g., `$50/mo` in both a plan summary header and a price breakdown line), `getByText` throws "Found multiple elements." Use `getAllByText` with a `.length` assertion instead: `expect(screen.getAllByText('$50/mo').length).toBeGreaterThanOrEqual(1)`.

### Frontend Tests: DOM Navigation for Seat Counters
Numeric seat counters (e.g., "1", "5") collide with other DOM text. Instead of `getByText('5')`, navigate the DOM relative to a unique aria-labeled button: `screen.getByLabelText('Add seat').previousElementSibling`. This avoids multi-match errors while staying structurally coupled to the component layout.

---

## Phase LIX Sprint F: Integration Testing + Feature Flag Rollout

### Prometheus Counter Names Strip `_total` in `collect()`
`prometheus_client` internally appends `_total` to Counter metric names per OpenMetrics convention. When iterating `REGISTRY.collect()`, the returned `Metric.name` is the base name (e.g., `paciolus_pricing_v2_checkouts`), not the full `_total` suffixed name. Tests that verify counter presence on a registry must match the base name, not the `_total` variant.

---

## Phase LIX Sprint B: Seat Model + Stripe Product Architecture

### SQLAlchemy Column `default=` Does NOT Apply on Bare Instantiation
`Column(Integer, default=1)` only fires on `INSERT` (via `db.add()` + `db.flush()`). A bare `Subscription()` object will have `seat_count = None`, not `1`. Tests that verify defaults must either: (a) test in DB context with `db_session.flush()`, or (b) test the property/method that handles `None` gracefully (e.g., `total_seats` uses `self.seat_count or 1`). This is distinct from `server_default` which only applies at the SQL level.

---

## Phase LIX Sprint A: Pricing Model Overhaul

### Test Fixture Defaults Cascade Through Entire Suite
When changing `UserTier.PROFESSIONAL` entitlements from all-tools to starter-level, the `conftest.py` default `make_user(tier=UserTier.PROFESSIONAL)` would have broken ~30 test files. The fix was to update the default to `UserTier.TEAM` and mechanically update all explicit `tier=UserTier.PROFESSIONAL` call sites. Lesson: test fixture defaults are a high-leverage coupling point — changing the semantics of a tier value requires auditing every fixture that uses it as a default.

### Display-Name Layer Prevents DB Enum Lock-In
PostgreSQL enum values can be added but not easily removed or renamed. Using a thin display-name mapping (`tier_display.py`) instead of renaming the enum lets us change public branding without touching the DB schema, Stripe metadata, or Alembic migrations. This pattern should be used for any future renaming of enums that are persisted in PostgreSQL.

---

## Sprint 6: Source Document Transparency

### Cross-Cutting Sprints Require Import Verification on Every File
When adding function calls (e.g., `create_leader_dots()`) to existing files during a cross-cutting sprint, always verify the function is already imported. `currency_memo_generator.py` used `create_leader_dots` in its inline source line but lacked the import — caught by regression tests (`TestCurrencyMemoLongInputs`) not by the new Sprint 6 tests. Lesson: regression suites across existing test files catch missing imports that targeted new tests may miss.

### Three Generator Categories Need Different Integration Patterns
The 20+ PDF generators fall into 3 categories: (A) cover-page via `build_cover_page()` + `ReportMetadata`, (B) header via `build_memo_header()`, (C) custom inline headers. Each category requires a different source-transparency integration pattern — (A) gets fields on the dataclass, (B) gets leader-dot lines after the header, (C) needs conditional replacement of hardcoded "Source File" lines. Identifying the categories upfront and applying the right pattern to each saved significant rework.

### PDF Binary Search Assertions Are Unreliable
ReportLab compresses text in PDF content streams, so `b"expected text" in pdf_bytes` will fail even when the text is correctly rendered. End-to-end PDF tests should assert `pdf_bytes[:5] == b"%PDF-"` (valid PDF header) and `isinstance(pdf_bytes, bytes)` rather than searching for raw text in the binary. Use unit tests on story flowables (pre-build) for text content assertions.

---

## Sprint 5: Heading Readability & Typographic Consistency

### Letter-Spaced Headings Were Confined to One File
Initial assumption was that spaced-caps headings ("E X E C U T I V E   S U M M A R Y") might be spread across many files. In reality, all 13 instances were in `pdf_generator.py` only. Memo generators used ALL-CAPS but not letter-spacing. A thorough audit upfront saved wasted effort searching wrong files.

### ALL-CAPS Headings Were Universal Across All 17 Memo Generators
While memo generators didn't use letter-spacing, every single one used ALL-CAPS section headers ("I. SCOPE", "II. METHODOLOGY"). The shared `memo_base.py` builders set the pattern, but many individual generators also had their own hardcoded headings. Converting to title case required touching 17 files — but because the pattern was consistent, the changes were mechanical and low-risk.

### Parametrized Test Discovery Catches Regressions Automatically
Writing tests that discover generator files via glob and parametrize assertions means new generators added in future sprints will automatically be checked for heading consistency — no manual test updates needed.

---

## Sprint 4: Text Layout Hardening

### Paragraph Wrapping Replaces String Slicing for PDF Tables
8 different memo generators independently used `[:N]` string slicing (with or without "..." ellipsis) to force text into fixed-width table columns. This pattern hides user data and creates inconsistent behavior (some add "...", some silently truncate). ReportLab's `Paragraph` flowable already auto-wraps text within its column width and dynamically expands row height — the slicing was unnecessary. Fix: wrap all text-heavy cells in `Paragraph(text, style)` and let ReportLab handle layout.

### repeatRows=1 Prevents Header Loss on Page Breaks
None of the 20+ PDF tables used `repeatRows=1`. When a large table spans multiple pages, the header row only appears on the first page, making subsequent pages unreadable. Adding `repeatRows=1` to all multi-row data tables ensures the header repeats on every page. Minimal effort, significant readability improvement.

### VALIGN TOP Is Critical for Mixed-Height Rows
Two tables (currency memo, sampling memo) were missing `VALIGN: TOP`. When some cells wrap to 2-3 lines while others are single-line, the default middle alignment causes misaligned text across columns. Always include `("VALIGN", (0, 0), (-1, -1), "TOP")` in any table that may have wrapped cells.

---

## Sprint 0: Report Standards Alignment

### Two Parallel Style Systems Are More Divergent Than Expected
Audit of all 20 PDF generators revealed two completely independent style systems (`create_classical_styles` with 16 styles vs `create_memo_styles` with 11 styles) that share zero code. They differ in title size (28pt vs 24pt), body text color (OBSIDIAN_600 vs OBSIDIAN_DEEP), section header size (12pt vs 11pt), and signoff column widths. The currency and flux expectations memos additionally use Helvetica (a third font family) and dark-background GRID tables — a pattern found nowhere else. Lesson: when shared primitives exist (memo_base.py), generators still drift if there is no enforced spec. The standards doc now locks every font, size, color, and margin to prevent future drift.

### Diagnostic Extension Memos Use Hardcoded Workpaper Codes
Five diagnostic memos (preflight, population profile, expense category, accrual completeness, flux expectations) use static `WP-PF-001`-style codes instead of dynamic `generate_reference_number()`. This creates duplicate reference numbers across different clients and periods. Migration plan assigns unique prefixes (PFL-, PPR-, ECA-, ACE-, FEX-) and requires dynamic generation.

---

## Sprint 420: Verification & Cleanup Release

### Redundant sr-only Inputs With Custom ARIA Checkboxes
Sprint 412c added `role="checkbox" aria-checked tabIndex={0} onKeyDown` to custom checkbox divs in login/register, but left the original `<input type="checkbox" class="sr-only">` in place. This created duplicate checkbox roles — `getByRole('checkbox')` found two elements, breaking tests. When upgrading a custom control to proper ARIA attributes, remove the hidden native input it was originally wrapping. The ARIA div IS the accessible control now.

---

## Sprint 415: Accessibility Semantic Fixes

### Modal Backdrops Should Use role="presentation", Not role="button"
Sprint 412c added `role="button" tabIndex={-1}` to a modal backdrop for ESLint compliance, but this is semantically incorrect — a backdrop is not an interactive control. The `tabIndex={-1}` contradicts the button role (removes from tab order), and the `onKeyDown` handler is unreachable. Correct pattern: `role="presentation"` with just `onClick` for click-outside-to-close. The backdrop's close behavior is a convenience, not an accessibility control — the real close mechanism is the modal's Cancel button or Escape key (via useFocusTrap).

---

## Phase XLIX: Diagnostic Feature Expansion (Sprints 356–361)

### Multiple FKs to Same Table Require foreign_keys Disambiguation
When adding `completed_by = ForeignKey("users.id")` to the Engagement model which already had `created_by = ForeignKey("users.id")`, the User model's `engagements` relationship needed `foreign_keys="[Engagement.created_by]"` and the Engagement model's `creator` relationship needed `foreign_keys=[created_by]`. Same pattern from Phase XLVI's SoftDeleteMixin, but this time for a non-mixin column. Always add `foreign_keys=` disambiguation when a model has 2+ FKs to the same target table.

### Allowlist Constants Must Be Updated When Adding Model Fields
Sprint 354 added `approved_by`/`approved_at` to AdjustingEntry but didn't update `ALLOWED_ADJUSTMENT_ENTRY_KEYS` in `tool_session_model.py`. This caused a pre-existing test failure that persisted across 6 sprints until caught in the Phase XLIX wrap. When adding fields to a model with an allowlist/blocklist sanitizer, always search for the allowlist constant and update it.

### Revenue Decline `else` Branch Missing Severity Assignment
In `going_concern_engine.py`, the `_test_revenue_decline()` function had `severity` assigned in the `if triggered:` branch but not in the `else:` branch, causing `UnboundLocalError`. When writing branching logic that builds a return value, ensure ALL branches initialize ALL variables used in the return statement.

---

## Phase XLVI: Audit History Immutability (Sprint 345–349)

### SoftDeleteMixin Creates Ambiguous ForeignKeys
When a mixin adds `archived_by = Column(Integer, ForeignKey("users.id"))`, any model that already has a FK to `users.id` (e.g., `user_id`) will cause SQLAlchemy `AmbiguousForeignKeysError` on relationships. The fix is to explicitly declare `foreign_keys=[user_id]` on every relationship pointing to User from an affected model, and `foreign_keys="[Model.user_id]"` on the reverse relationship in User. This affected 3 models (ActivityLog, DiagnosticSummary, FollowUpItemComment) and 2 User reverse relationships.

### ToolRun Ordering Needs Secondary Sort
`get_tool_run_trends()` ordered by `run_at.desc()` only. When two ToolRuns are recorded in the same test nearly simultaneously, they can get the same `run_at` timestamp, making the ordering non-deterministic. Adding `ToolRun.id.desc()` as a secondary sort key guarantees deterministic ordering. This was a pre-existing flaky test exposed by the full suite run.

## Phase XLV: Monetary Precision Hardening (Sprint 340–344)

### BALANCE_TOLERANCE as Decimal, Not Float
The float literal `BALANCE_TOLERANCE = 0.01` was used in 10 locations for balance comparisons. Comparing `abs(float_diff) < 0.01` has subtle issues: the float 0.01 itself is inexact (`Decimal(0.01)` = `0.01000000000000000020816681711721685228163...`). Replacing with `Decimal("0.01")` and comparing `abs(Decimal(str(diff))) < BALANCE_TOLERANCE` eliminates this.

### Alembic Multiple Heads
When the migration chain has multiple heads (two independent branches), you must merge them first (`alembic merge heads -m "message"`) before creating a new migration. Otherwise Alembic refuses to generate a new revision.

### SQLite + Alembic ALTER COLUMN
SQLite doesn't support ALTER COLUMN natively. Alembic's `batch_alter_table` creates a temp table, copies data, drops original, and renames. This works but is slow on large tables. For the dev SQLite DB, the models define the schema via `init_db()` not Alembic, so `alembic stamp head` is needed to mark the DB as current.

### Python round() Uses Banker's Rounding
`round(2.225, 2)` = `2.22` (ROUND_HALF_EVEN), not `2.23`. For financial applications, always use `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`. The `quantize_monetary()` shared utility encapsulates this.

---

## Process & Strategy

### Commit Frequency Matters
Each sprint = at least one atomic commit. Format: `Sprint X: Brief Description`. Stage specific files, never `git add -A`.

### Verification Before Declaring Complete
Before marking ANY sprint complete: `npm run build` + `pytest` (if tests modified) + Zero-Storage compliance check.

### Stability Before Features
Prioritize: 1) Stability (error handling, security) → 2) Code Quality (extraction, types) → 3) User Features (new functionality). Quick wins first within each tier.

### Test Suites Before Feature Expansion
Before expanding a module, create comprehensive tests for existing functionality. Cover edge cases (div-by-zero, negatives, boundaries).

### Test Fixture Data Must Match Requirements
Shared fixtures for common scenarios. Test-specific data for edge cases. Don't rely on shared fixtures for division-by-zero tests.

### Phase Wrap Sprints Are Pure Verification
**Observed across:** Sprints 110, 120, 130, 163. Write zero lines of application code. Run full backend test suite, frontend build, and guardrail checks. Documentation updates only. This pattern consistently catches inconsistencies.

### Extract Shared Components at the Right Time
Sprint 81 extracted ToolNav after 5 copies existed. Sprint 90 extracted shared enums before building Tool 7. Sprint 136-141 extracted testing components after 7+ copies stabilized. **Rule:** Extract after the second consumer appears for small utilities; extract after patterns stabilize across 7+ consumers for large component sets. During rapid feature delivery, cloning is correct — schedule a deduplication phase once feature velocity slows.

### Product Review Pays for Itself in Sprint 1
The 4-agent product review (Phase XIII) identified 51 findings. Sprint 121 alone fixed 7 P0 items. Without the review, issues like Tailwind shade gaps affecting 74 files would have accumulated silently.

---

## Architecture & Backend Patterns

### Engagement Management ≠ Engagement Assurance
Distinguish clearly between workflow features (tracking tools, organizing follow-ups — project management) and assurance features (risk scoring, deficiency classification — auditor judgment). Paciolus detects data anomalies; auditors assess control deficiencies. Never auto-classify using audit terminology (Material Weakness, Significant Deficiency). Use "Data Anomalies" and "Follow-Up Items" instead.

### Disclaimers Cannot Rescue Misaligned Features
If a feature's implied workflow crosses professional standards boundaries, rename and redesign the feature — don't just add warning text. Regulators (PCAOB, FRC) assess the tool's purpose, not its disclaimers.

### Zero-Storage Boundary: Metadata vs Transaction Data
Auth DB = emails + hashes only. DiagnosticSummary = aggregate totals only. Client table = name + industry only. Financial data is always ephemeral.

### Two-Phase Flow for Complex Uploads
When uploads need user decisions: 1) Inspection endpoint (fast metadata) → 2) Modal for user choice → 3) Full processing with selections.

### Dynamic Materiality: Formula Storage vs Data Storage
Store the formula config (type, value, thresholds). Never store the data it operates on. Evaluate at runtime with ephemeral data. Priority chain: session override → client → practice → system default.

### Factory Pattern for Industry-Specific Logic
Abstract base class + factory map for per-industry implementations. Unmapped industries fall back to GenericCalculator.

### Multi-Tenant Data Isolation
Always filter by `user_id` at the query level: `Client.user_id == user_id`. Never fetch-then-check.

### Optional Dependencies for External Services
External APIs (SendGrid, Stripe) should be optional imports with graceful fallback. Tests should run without API keys.

### Vectorized Pandas vs iterrows()
Replace `.iterrows()` with `groupby().agg()`. For 10K+ rows, iterate unique accounts (~500) instead of all rows. 2-3x improvement.

### Config-Driven Shared Modules for Cross-Engine Patterns
**Discovered:** Sprint 152. Use config objects (FieldQualityConfig, accessor callables) to parameterize shared functions rather than forcing all engines into one shape. Partial adoption (AR: CS only, TWM: neither) is better than force-fitting. This pattern powered column_detector (9 engines), memo_template (7 generators), testing_route (6 routes), data_quality (7 engines), and test_aggregator (7 engines).

### Callback-Based Factory Over Parameter-Heavy Abstraction
**Discovered:** Sprint 156. The `run_single_file_testing()` factory takes a `run_engine` callback rather than parameterizing all engine signature variations. Each route provides a lambda with its specific kwargs. Exclude multi-file routes (TWM, AR) where the factory adds more complexity than it removes.

### Inline Imports in Methods Defeat Return Type Annotations
**Discovered:** Sprint 414. `def _make_evidence(self, ...) -> "ContractEvidenceLevel":` with `from engine import ContractEvidenceLevel` inside the method body triggers ruff F821 (undefined name) because the string annotation references a name not in module scope. Either move the import to module level or remove the return type annotation. Prefer module-level imports in test files — there's no circular import risk.

### Account Classifier Lives in `account_classifier.py`
The `AccountClassifier` class and `create_classifier()` factory are in `account_classifier.py`, NOT `classification_rules.py`. The latter only has `ClassificationRule`, `ClassificationResult`, and `AccountCategory`. Sprint 289 learned this the hard way.

### Priority Ordering in Greedy Column Assignment
**Discovered:** Sprint 151. When multiple field configs match the same column name (e.g., "cost" matches both `cost` and `accum_depr`), lower `priority` numbers are assigned first. Always assign the most specific columns first.

### Guardrail Tests Must Inspect Module, Not Function
**Discovered:** Sprint 157. After refactoring memo generators to delegate to shared template, `inspect.getsource(function)` no longer contains ISA references — they're in module-level config. Use `inspect.getsource(inspect.getmodule(function))` instead. Source-code guardrail tests are brittle under refactoring.

### Centralized Error Sanitization
**Discovered:** Sprint 122. Use regex patterns to match common exception types (pandas, openpyxl, SQLAlchemy, reportlab) and map to user-friendly messages. `except ValueError` is safe (controlled messages); `except Exception` leaks tracebacks and needs sanitization. **Refinement (Sprint 252):** `allow_passthrough=True` mode for CRUD validation routes — dangerous patterns still caught, but safe business-logic messages pass through unchanged. Without this, all ValueErrors become generic "An unexpected error occurred."

### Rate Limiting Requires `Request` as First Parameter
Slowapi's `@limiter.limit()` decorator requires FastAPI `Request` as first positional parameter. When a Pydantic body model is already named `request`, rename it to `payload`.

### Upload Validation in Two Layers
Content-type and extension checks in `validate_file_size` (before bytes consumed). Encoding fallback and row count checks in `parse_uploaded_file` (during parsing). Short-circuit early.

### Memo Generator API Signatures Must Match
**Discovered:** Sprint 259. The shared memo base functions have specific signatures: `build_memo_header(story, styles, doc_width, title, reference, client_name)`, `build_workpaper_signoff(story, styles, doc_width, ...)`, and `generate_reference_number()` (no args). Always read the actual signature before using — the style key is `MemoSection` (not `MemoSectionHeader`), and color tokens are `OBSIDIAN_700` / `OATMEAL_400` (not `_LIGHT` / `_DARK`).

---

## Frontend Patterns

### framer-motion Type Assertions
TypeScript infers `'spring'` as `string`, but framer-motion expects literal types. Always use `as const` on transition properties. Applies to ALL framer-motion transitions extracted to module-level consts.

### framer-motion Performance Rules (Sprint 240)
- **Never animate `width`/`height` for visual-only effects** — use `scaleX`/`scaleY` + `transformOrigin` instead. Progress bars: `scaleX: progress/100` with `w-full` and `transformOrigin: 'left'`. Light-leak effects: set width statically, animate `scaleX`.
- **Infinite `boxShadow` animations in JS are expensive** — `boxShadow` forces repaint every frame. Move to CSS `@keyframes` where the browser can optimize off main thread. Limit decorative pulses to 3 cycles.
- **`AnimatePresence` children must be `motion.*` elements** — plain `<div>` inside `AnimatePresence mode="popLayout"` won't fire exit animations. The immediate child must be a motion component.
- **`AnimatePresence` is pointless on always-rendered content** — if early returns prevent the component from mounting, the exit animation never fires.
- **`<MotionConfig reducedMotion="user">` in root providers** — single line that makes all framer-motion animations respect `prefers-reduced-motion`. Highest-ROI accessibility fix.
- **`key={index}` in `AnimatePresence` causes wrong exit animations** — use stable IDs (counter ref or UUID) for list items that can be deleted from the middle.
- **Add `layout` prop to filterable/deletable list items** — prevents remaining items from jumping position when siblings are removed.

### God Component Decomposition — Extract Hook First
**Discovered:** Sprint 159. When decomposing a god component: (1) extract the custom hook with ALL logic first, (2) extract self-contained presentational sub-components, (3) the page becomes a thin layout shell. Tests pass without modification because jest.mock applies at module level.

### useEffect Referential Loop Prevention
Use `useRef` to track previous values. Compare prev vs current before triggering effects. For multiple params, use composite hash comparison.

### Memoize `initialValues` When Passed to Hooks That Derive Callbacks
**Discovered:** Sprint 414b. `useFormValidation({ initialValues: getInitialValues() })` creates a new object every render. If the hook's `reset` callback depends on `initialValues` (via `useCallback([initialValues])`), then `reset` is also recreated every render. Adding `reset` to a `useEffect` dep array causes an infinite re-render loop — the effect calls `reset()`, which updates state, which re-renders, which creates new `initialValues`, which creates new `reset`, which re-triggers the effect. A `useRef` guard only prevents the body from executing, not the effect from re-scheduling. **Fix:** `useMemo` the `initialValues` object on the actual primitive fields (`client?.name`, `client?.industry`, etc.) so the hook's derived callbacks are referentially stable.

### Modal Result Handling
Always check async operation result before closing modal. `if (await action()) closeModal()` — never fire-and-forget. Show errors IN the modal, not after it closes.

### Next.js Suspense Boundary for useSearchParams
Pages using `useSearchParams()` must wrap content in `<Suspense>`. Build-time requirement in Next.js 14+.

### TypeScript Type Guards with Array.filter()
`.filter(x => x)` doesn't narrow types. Use type predicate: `.filter((entry): entry is { key: string } => entry !== undefined)`.

### Ghost Click Prevention
File inputs with `position: absolute; inset: 0` capture unintended clicks. Fix: `pointer-events-none` + `tabIndex={-1}` when not in idle state.

### TypeScript `interface` vs `type` for Index Signature Compatibility
**Discovered:** Sprint 227. `interface Foo { a: string }` does NOT satisfy `Record<string, unknown>` because TypeScript interfaces lack implicit index signatures. `type Foo = { a: string }` DOES satisfy it. When a generic constraint requires `Record<string, unknown>` (e.g., `TEntry extends Record<string, unknown>`), all concrete types passed as `TEntry` must be `type` aliases, not `interface` declarations. This affected 11 types across the codebase (7 entry data types + 4 form value types).

### Severity Type Mismatch
Frontend `Severity` is `'high' | 'low'` only. `medium_severity` exists only as a count in RiskSummary. Always verify TypeScript types before assuming backend enum values map 1:1.

### useOptionalEngagementContext for Backward Compatibility
**Discovered:** Sprint 103. Returns `null` instead of throwing when no provider is present. Lets `useAuditUpload` auto-inject `engagement_id` when wrapped, silently skip when standalone.

### Hook-Level Integration Minimizes Page Changes
**Discovered:** Sprint 103. By injecting engagement logic into `useAuditUpload`, 5 of 7 tools got engagement support with zero page changes. Only TB (custom fetch) and Multi-Period (JSON body) needed explicit changes.

### Data-Driven Config Sections Beat Code Duplication
**Discovered:** Sprint 160. Four 170-line testing config sections collapsed into one 218-line shared component + 4 config arrays (~55 lines). Key: `ThresholdField[]` with `displayScale`, `prefix`/`suffix`, and `children` slot for edge cases.

### Factory Functions for Identical Hook Wrappers
**Discovered:** Sprint 161. 9 testing hooks (35-45 lines each) collapsed to `createTestingHook<T>()` factory (36 lines). Multi-file hooks pass custom `buildFormData` — no special casing needed.

### Centralize Environment Variables as Constants
**Discovered:** Sprint 161. 14 files declared `const API_URL = process.env.NEXT_PUBLIC_API_URL` locally. A single `utils/constants.ts` with fallback handles all cases. `minutes()` / `hours()` helpers make TTL configs self-documenting.

### `useState` Initializer Is NOT `useEffect`
**Discovered:** Sprint 162. `useState(() => { fetchIndustries() })` abuses the lazy initializer — runs synchronously during render. Always use `useEffect` for mount-time data fetching.

### Generic TypeScript Interfaces via Type Parameters and Slots
**Discovered:** Sprint 137. `BaseCompositeScore<TFinding = string>` handles Payroll's structured findings. `DataQualityBadge`'s `extra_stats?: ReactNode` slot handles AR's unique display. `FlaggedEntriesTable`'s `ColumnDef<T>` handles 7 table schemas. Use `object` constraint with explicit cast for generic form components (Sprint 160).

### CSS Custom Properties Don't Support Tailwind Opacity Modifiers
**Discovered:** Sprint 124. `bg-surface-card/50` doesn't work. Design semantic tokens with opacity built into the variable, or use separate tokens for different opacity needs.

### Modal Overlays Are NOT Dark-Theme Remnants
`bg-obsidian-900/50` is correct on both themes — semi-transparent dark backdrops dim whatever's behind the modal.

### Dark-Pinned Components Use `data-theme="dark"` Attribute
**Discovered:** Sprint 124. ToolNav and ToolLinkToast stay dark on light pages via `data-theme="dark"` on their wrapper element.

### JSX String Apostrophe Escaping
**Discovered:** Sprint 131. Background agents create TSX with unescaped apostrophes (`what's`, `it's`, `Children's`). Always scan agent output and fix with `\u0027` or `&apos;`.

### Warm-Toned Shadows for Premium Light Themes
**Discovered:** Sprint 325. Neutral gray shadows (`rgba(33,33,33,...)`) feel clinical. Using warm-toned shadows (`rgba(139,119,91,...)`) with the same alpha values creates a parchment-adjacent feel that matches Oat & Obsidian's warm palette. Apply to light theme only — dark theme shadows should stay neutral.

### Card Hierarchy via CSS Custom Properties
**Discovered:** Sprint 325. Three tiers — `surface-card` (default white), `surface-card-elevated` (same white, bigger shadow), `surface-card-inset` (slightly tinted, inset shadow) — provide clear visual nesting without adding extra borders or backgrounds. The `.card-inset` utility class bundles bg + border + shadow for one-liner application.

### Left-Border Accent Pattern for Visual Rhythm
**Discovered:** Sprint 326. `border-l-4` with color-coded accents (sage for positive, clay for negative, oatmeal for neutral) creates consistent visual rhythm across stat cards, summary cards, and metric displays without adding bulk. Map colors to the component's health/status data via `themeUtils.ts` for consistency.

### CSS-Only Textures Over Image Assets
**Discovered:** Sprint 328. SVG `feTurbulence` encoded as a data URI provides paper-like texture at 0.015 opacity — no image downloads, no CDN dependency, fully CSS-contained. Always pair decorative textures with `prefers-reduced-motion: reduce` media query to disable them.

---

## Testing Patterns

### Layout Refactors Must Update Test Assertions
When moving components from pages to layouts (e.g., Sprint 207 moved ToolNav/VerificationBanner to `app/tools/layout.tsx`), the corresponding page-level test assertions become stale. Tests that mock `@/components/shared` at the page level will silently pass the mock setup but fail the assertion because the page no longer imports those modules. **Rule:** Any component relocation must include a grep for test mocks targeting the old import path.

### Z-Score Fixtures Need Large Populations
With only 20 entries, a single outlier shifts the mean and stdev significantly. Use 100+ base entries to produce expected z-scores for HIGH severity thresholds.

### Benford Test Data Must Span Orders of Magnitude
Amounts must span 2+ orders of magnitude to pass prechecks. Use amounts like 50+, 500+, 5000+.

### Scoring Calibration: Comparative Over Absolute
Use `assert clean_score.score < moderate_score.score < high_score.score` rather than asserting absolute tiers, which change as tests are added.

### SignificanceTier Enum vs String in Tests
When constructing test dataclasses that use enums, always use the enum member, not its string value.

### Pytest Collection of Engine Functions
Functions named `test_*` in engine files are collected by pytest. Either don't use `test_` prefix, or import with aliases: `from engine import test_foo as run_foo_test`.

### `jest.clearAllMocks()` Does NOT Reset `mockReturnValue`
Must explicitly re-set default mock values in `beforeEach` after `clearAllMocks()`.

### Mock Result Shapes Must Match Inline Property Access
Even when child components are mocked, the page evaluates prop expressions like `result.summary.matches` before passing to the mock. Always check page source for inline property chains.

### framer-motion Test Mock Must Strip Motion Props
Spreading all props from `motion.div` onto a real `<div>` passes invalid HTML attributes. Destructure out `initial`, `animate`, `exit`, `transition`, `variants`, `whileHover`, etc. before spreading rest props.

### Mock Barrel Exports Must Include ALL Named Exports
When mocking a barrel file (`@/components/shared`), include ALL named exports the page uses, not just one.

### Mock the Import Path the Component Actually Uses
**Discovered:** Sprint 249. If a page imports from `@/components/engagement` (barrel), mocking `@/components/engagement/EngagementList` (individual file) does nothing — Jest resolves mocks by the exact import path string. Always mock the barrel path when that's what the source file imports.

### `getByText` Fails on Duplicated Page Text (Nav + Heading)
**Discovered:** Sprint 249. Pages with breadcrumb navigation often render the same text in both `<span>` (nav) and `<h1>` (heading). Use `getByRole('heading', { name: '...' })` to target the heading specifically, or `getAllByText` when both are valid.

### Named vs Default Export Mocks Are Not Interchangeable
**Discovered:** Sprint 249. `import { CommentThread } from './CommentThread'` requires mock `{ CommentThread: ... }`. Using `{ __esModule: true, default: ... }` silently resolves to `undefined` and causes "Element type is invalid" at render time — the error appears on click (expand), not on initial render, making it hard to diagnose.

### Hook Method Names Must Match Page Destructuring
Always verify the page's `const { ... } = useHook()` line before writing mock return values.

### SQLite FK Constraints Need PRAGMA
FK constraints NOT enforced by default. Need `PRAGMA foreign_keys=ON` via engine event listener in conftest.py.

### SQLite Strips Timezone from Datetime Columns
Compare with `.replace(tzinfo=None)` when mixing DB-loaded and fresh timezone-aware datetime values.

### SQLAlchemy Backref Passive Deletes
When deleting a parent with related children, use `backref=backref("items", passive_deletes=True)` to let DB handle CASCADE instead of SQLAlchemy's default SET NULL behavior.

### Test Import Redirection Preserves Compatibility
When extracting helpers into shared modules, test files can use `from shared.module import func as _old_name` — same alias, zero test body changes.

### Ghost Employee Tests Affect "Clean" Fixture Design
Tests that flag single-entry employees mean clean fixtures must ensure each employee has 2+ entries across different months.

### BaseHTTPMiddleware Cannot Raise HTTPException
Starlette's `BaseHTTPMiddleware` wraps exceptions in `ExceptionGroup`, so raising `HTTPException` inside `dispatch()` produces opaque errors. Return a `Response(content=..., status_code=..., media_type="application/json")` instead — matches the pattern in `MaxBodySizeMiddleware`.

### CSRF Middleware Breaks API Integration Tests
Registering CSRF middleware blocks all test POST/PUT/DELETE requests that don't include a CSRF token. Solution: add an autouse session fixture in conftest.py that patches `validate_csrf_token = lambda token: True`, then restore the original in `test_csrf_middleware.py` setup/teardown for explicit CSRF testing.

---

## Design & Deployment

### Premium Restraint for Alerts
Left-border accent (not full background), subtle glow at low opacity, typography hierarchy over color.

### CSS Custom Properties Bridge Tailwind and Runtime Theming
Define semantic CSS variables in `:root` (dark defaults) with `[data-theme="light"]` overrides in `globals.css`, reference via Tailwind token aliases. Route-based theming via `usePathname`, not user toggle.

### ScoreCard Tier Gradients → Left-Border Accents on Light Theme
Dark theme used gradient backgrounds for risk tier encoding. On light backgrounds, use `border-l-4 border-l-{tier-color}` instead.

### RISK_TIER_COLORS Must Use Solid Fills for Light Theme
Replace opacity colors (`bg-sage-500/10`) with solid palette fills (`bg-sage-50`, `text-sage-700`, `border-sage-200`).

### `prefers-reduced-motion` Should Skip, Not Slow Down
Don't show a faster animation — skip it completely and call `onComplete` immediately.

### Memo "Download Memo" as Primary, "Export CSV" as Secondary
PDF memos are the higher-value audit artifact. Make memo button visually primary (sage-600 filled) to guide users toward the more useful export.

### Memo Data Shape Must Match Tool Output
Always check the frontend data shape (hook response) before designing a memo generator. Design the Pydantic input model from the hook's TypeScript types first.

### Multi-Stage Docker Builds
Separate deps → builder → runner stages. Only runtime in final image. Non-root users. Health checks. `sqlite:////app/data/paciolus.db` (4 slashes = absolute path). Use `pip install --prefix=/install` in builder to avoid copying pip/setuptools/wheel (~20MB) into production stage. Prefer `curl -f` for healthchecks over spawning a full Python interpreter every 30 seconds.

### .dockerignore Prevents Secrets in Build Context
Without `.dockerignore`, `docker build` sends everything (`.env`, `paciolus.db`) to the daemon, even if not COPY'd.

### Docker Compose Defaults Drift from Backend Config
**Discovered:** Sprint 250. `docker-compose.yml` had `JWT_EXPIRATION_MINUTES:-1440` (24h) but `config.py` was hardened to 30 minutes in Phase XXV Sprint 198. Compose env defaults silently override backend config module defaults. **Rule:** After any security hardening phase that changes config defaults, grep `docker-compose.yml` for the same env var and update the compose default to match.

### Gunicorn Worker Recycling for Pandas Memory
**Discovered:** Sprint 250. Long-running Gunicorn workers processing large DataFrames via Pandas accumulate memory over time. `--max-requests 1000 --max-requests-jitter 50` restarts workers after ~1000 requests, preventing slow memory leaks. Jitter prevents all workers from restarting simultaneously (thundering herd).

### Dockerfile HEALTHCHECK vs Compose healthcheck Duplication
**Discovered:** Sprint 250. Defining healthchecks in both `Dockerfile` and `docker-compose.yml` causes the compose definition to silently override the Dockerfile's `HEALTHCHECK`. Pick one location: Dockerfile for self-contained images, compose for orchestration-specific tuning. Don't duplicate.

### ReportLab Best Practices
Use get-or-create for styles (avoid "already defined" error). Use `onFirstPage`/`onLaterPages` callbacks for repeating elements. Wrap table cell text in `Paragraph` objects. Prefer built-in fonts. **Sprint 196:** Only reference styles that exist in the style dict being used (`create_classical_styles()` vs `create_memo_styles()` have different names). Only use fonts registered with `pdfmetrics` — `Times-*` and `Courier` are built-in; custom fonts like `Merriweather`/`Lato` require explicit registration. Always close BytesIO buffers after `getvalue()`.

### Tailwind Silently Drops Undefined Color Shades
Classes referencing undefined shades simply produce no CSS — no warnings. Always define the full shade range (50-900) when a scale is used extensively.

### Single Version Source of Truth
Extract version to `backend/version.py` with `__version__`. Import everywhere. Future bumps require exactly one edit.

---

## Adding New Tools — Cascade Checklist

### ToolName Enum Cascade (4-file, N-assertion update)
**Observed across:** Sprints 104, 107, 114. When adding a new `ToolName`: (1) add to enum, (2) add to `TOOL_LABELS`, (3) add to `TOOL_LEAD_SHEET_REFS`, (4) grep tests for hardcoded tool counts (e.g., `== 9`). Update `test_anomaly_summary.py`, `test_engagement.py`, `test_workpaper_index.py`.

### Frontend Tool 4-Location Cascade
**Observed across:** Sprints 106, 109, 116, 119. New tool frontend requires: (1) `ToolNav.tsx` (ToolKey type + TOOLS array), (2) `app/page.tsx` (toolCards + nav + tool count copy), (3) `types/engagement.ts` (ToolName + TOOL_NAME_LABELS + TOOL_SLUGS), (4) tool's own files (types, hook, 4 components, page).

### Frontend Tool Pages Are a 4-File Formula
**Observed across:** Sprints 106, 116, 119. Types file → Hook (thin `useAuditUpload` wrapper via `createTestingHook`) → 4 components (ScoreCard, TestResultGrid, DataQualityBadge, FlaggedTable) → Page.

### Memo Generators Are Config-Driven (5 minutes)
**Observed across:** Sprints 105, 115, 118. With `shared/memo_template.py`: define test descriptions dict, methodology intro, risk-tier conclusions, ISA references. ~90 lines per generator.

---

## Phase Retrospectives — Consolidated

> Distilled from 15+ individual phase retrospectives (VI–LXIX). Only unique lessons not already captured in categorical sections above.

### Feature Delivery Cadence (Phases VI–XII)
- Frontend auth gating must be 3-state (guest/authenticated/verified), not 2-state
- Extract shared utilities BEFORE building the next tool; the clone pattern compounds — each tool ships faster
- Classification validators: structural-only (detect, not advise) to avoid liability

### Refactoring & Hardening (Phases XV–XXIII, XXVIII)
- `def` is the correct FastAPI default; auto-threadpools sync handlers. Use `asyncio.to_thread()` for CPU-bound Pandas in `async def`.
- Error-in-body anti-pattern (200 with `{"error": "..."}`) leaks into frontend types — convert to HTTPException
- `min_length=1` on Pydantic list fields can break legitimate empty-list cases (e.g., multi-period all-new accounts)
- `@model_validator(mode='before')` enables backward-compatible model decomposition
- Static analysis (ruff) catches bugs on error-handling paths that 2,900+ tests miss
- `float('inf')` is not valid JSON — use `None` for zero-prior percentages

### Design & Theme (Phases XLII–XLIII)
- Verify which route (dark Lobby vs light Vault) a component renders on before migrating tokens
- Dual-theme components (e.g., RiskDashboard on both themes) work automatically with CSS custom properties
- Always update tests alongside color token migrations (`toContain('text-oatmeal')` → `text-content-primary`)
- Fixed-position backgrounds need `pointer-events-none`; content needs `relative z-10`

### Security (Sprint 476 + Hardening)
- `conftest.py` must import ALL ORM models with FK relationships — even unused ones trigger `create_all` errors
- CSV `sanitize_csv_value()` must cover ALL export functions — satellite exports (bank_rec, multi_period, admin) get missed
- `_FORMULA_TRIGGERS` must include `|` (pipe) per OWASP CWE-1236 — always cross-reference full standard
- Webhook handlers: one logical operation = one `db.commit()` — multiple commits create crash-consistency windows
- Adding auth/validation to an endpoint → grep all test call sites, not just add new tests

### PDF & Report Generation
- Circular imports between generators and shared chrome → resolve via lazy imports
- `StyleSheet1.get(key)` raises `KeyError` (not `None`) — use `_safe_style(styles, *names)` helper
- PDF binary: text is compressed — never `b"TITLE" in pdf_bytes`; assert structurally (page count, `/Type /Page`)
- `.tsx` extension required for files containing JSX (even if primarily constants)

### Digital Excellence Council Audit (Sprint 479)
- `time.sleep()` in tests is inherently flaky — use deterministic timestamps (set to a known past value) instead of waiting for the clock to advance
- f-string SQL in test fixtures, even with integer literals, establishes a copy-paste hazard — always use `.bindparams()` even in tests
- ExportShare's 48h derived-data retention is a controlled exception to zero-storage that must be formally documented in the security policy with compensating controls listed
- framer-motion `as const` convention needs CI enforcement (grep-based gate), not just documentation — 11 violations accumulated despite CLAUDE.md mandate
- APScheduler per-instance behavior under Gunicorn needs ops documentation, not just code comments — operators won't read source during incidents

### Financial Statements Report Enhancements (Sprint 488)
- `_extract_depreciation` relied solely on `net_balance` field from account dicts, but test fixtures (and possibly real data) sometimes only have `debit`/`credit` without a pre-computed `net_balance`. Added fallback: `debit - credit` when `net_balance` is 0.0. Same pattern applied to `_extract_interest_expense`. Always handle both dict shapes for TB account data.

### JE Testing Memo Fixes (Sprint 489)
- **Index-based finding-to-procedure mapping breaks when `top_findings` and `flagged_tests` have different orderings.** The `top_findings` list may be sorted by severity/importance while `flagged_tests` is sorted by flag_rate. Fixed with `_resolve_test_key()`: a word-overlap scorer that weights words by cross-test distinctiveness (unique words score 2x, common words like "entries" score less). Generic words in test names (entries, amounts, postings) cause false matches with naive substring matching.
- **Disclaimer template `f"automated {domain} testing procedures"` doubled "testing" when `domain` already ended with "testing"** (e.g., "journal entry testing testing procedures"). Four of seven testing memo domains hit this bug. Fix: conditional `domain_clause` that skips appending "testing" when domain already ends with it.
- **Sample report data can diverge from real engine output.** The Benford `expected_distribution` used a wrong formula `(0.30103 - 0.02 * (d - 2))` instead of `log10(1 + 1/d)`. The real engine (`shared/benford.py`) was always correct — only the hardcoded sample data was wrong. Always derive sample data from the same constants/functions used by the engine.

### AP Testing Memo Fixes (Sprint 490)
- **Test-specific table layouts are essential for high-severity drill-downs.** A generic 6-column table can't meaningfully display data from tests with fundamentally different schemas (duplicates need payment pairs, threshold tests need below-by amounts, invoice reuse needs two-vendor comparison). Each high-severity test type benefits from a purpose-built column layout with a generic fallback for unexpected test keys.
- **Vendor name variation pairs generate duplicate flagged_entries** (A→B and B→A). The deduplication via `seen_pairs` with `tuple(sorted([name_a, name_b]))` is required, otherwise every pair appears twice in the table. Sort by combined total_paid descending and cap at top 5 to keep the table actionable.

### Fixed Asset Report Fixes (Sprint 502)
- **Recurring bug pattern: sample data `test_key` values diverge from engine canonical keys.** Revenue sprint had `round_amounts` vs `round_revenue_amounts`; fixed assets had `cost_outliers` vs `cost_zscore_outliers` and `residual_anomalies` vs `residual_value_anomalies`. The methodology description lookup uses test_key, so mismatches produce blank descriptions. **Always verify sample data test_keys match `*_TEST_DESCRIPTIONS` dict keys exactly.**
- **ReportLab Paragraph uses XML/HTML parser.** Raw `&` in strings passed to `Paragraph()` must be escaped as `&amp;`. The `PP&E` abbreviation caused rendering artifacts because `&E` was interpreted as a malformed XML entity. Payroll memo already had correct `&amp;` usage (`"Payroll &amp; Employee Testing Memo"`) — the pattern was available but not applied consistently.
- **When adding a new test to an engine, grep the entire test suite for hardcoded counts** (`== 9`, `tests_run=9`). Four separate assertions across two test files needed updating from 9 to 10 after adding the FA-10 lease indicator test.

### Docker deployment breaks static asset discovery (Sprint 526)
- **Logo files at project root and `frontend/public/` are invisible inside the backend container.** The Dockerfile copies only `backend/` into `/app`, so `Path(__file__).parent.parent.parent / "frontend"` resolves to a non-existent path. **Fix:** Copy assets to `backend/assets/` which is the third search path in `_find_logo_file`. Any asset needed by the backend PDF generator must live inside the `backend/` directory tree.

### Greedy column detection priority ordering can steal columns from higher-importance roles (Sprint 526)
- **When `account_name_column` (priority 8) ran BEFORE `account_column` (priority 10), it claimed "Account Name" headers — leaving account_column null.** This broke all downstream features because the account identifier was missing. **Pattern:** In a greedy assignment algorithm, give the most critical role the lowest priority number (first pick). Optional/supplementary roles should run after required ones. Specifically: `account_column` (priority=8) must run before `account_name_column` (priority=12).

### Substring keyword matching can cause false positives on unrelated account names (Sprint 537)
- **"rent" is a substring of "current"**, so `"rent" in "2520 — current portion — long term debt".lower()` returned True, incorrectly classifying a debt account as informational (transactional). **Fix:** Added `"current portion"` and `"long term debt"` to `ROUND_NUMBER_TIER1_SUPPRESS` so these accounts are suppressed before reaching the informational keyword check. **Pattern:** When using `kw in lower` substring matching, always test against account names that contain the keyword as a substring of a larger word. Consider whether phrase-level matching or word-boundary checks would be safer for short keywords (≤4 chars).

### Stale test assertions survive across sprint boundaries (Sprint 537)
- **`test_allowance_round_suppressed` expected `len(rounding) == 0`**, but Sprint 536 changed contra-asset handling from suppress (return `None`) to minor observation (return `"minor"`). The test was already failing before Sprint 537 started. **Pattern:** When a sprint changes classification/tiering logic, grep for all tests that assert on the affected return values — not just the tests in the sprint's own test file. Run the full `pytest` suite before starting new work to establish a clean baseline.

### Subagent findings must be verified against live code before acting (Sprint 598)
- **During the 2026-04-14 weekly weakness hunt, a parallel `Explore` subagent tasked with finding test coverage gaps reported that `ratio_engine.py`, `accrual_completeness_engine.py`, and `three_way_match_engine.py` had "no test suite" or "no dedicated test file." All three claims were wrong** — each module has 1–3 dedicated test files (`test_ratio_core.py`, `test_ratio_analysis.py`, `test_ratio_trends.py`, `test_accrual_completeness.py`, `test_three_way_match.py`, `test_three_way_comparison.py`). The same agent also reported fake line counts ("44,081 lines", "55,283 lines") which were actually byte counts. A sibling security-hunt agent produced verifiable findings with correct line:line references; the coverage agent hallucinated structure. **Pattern:** Any subagent claim of the form "file X does not exist", "function Y is untested", or "N lines/rows/items" MUST be verified against live code (Glob/Grep/wc) before being acted on or surfaced to the user. If the claim can be invalidated by a single shell command, run that command before repeating the claim. Line-level findings with specific `file:line` references are higher-trust than structural ("no test file exists") claims — the specific ones are visible in the agent's context window, the structural ones require accurate mental model of a repo the agent only partially read. **Systemic fix:** replace LLM-introspected coverage analysis with `pytest --cov --cov-report=json` piped into the nightly brief so the coverage pillar stands on machine-checkable data rather than model output. Sprint 599 wires this in.
