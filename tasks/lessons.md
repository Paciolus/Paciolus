# Lessons Learned

> **Protocol:** After any CEO correction, better pattern, mistake fixed or wrong assumption, add a lesson here (CLAUDE.md
> Directive Protocol §4). Read the standing rules at session start.
>
> **2026-11-15:** this file was cut from ~3,000 lines to the rules below. Every original entry is preserved verbatim in
> [`archive/lessons-through-2026-11-15.md`](archive/lessons-through-2026-11-15.md); each rule links to its source.
> Add new lessons under **Recent lessons**; when that section passes ~15 entries, fold them into the rules and archive them.

## Standing rules

### Verification & deploys
- "Merged" is not "deployed": after a merge, confirm the live deploy SHA equals `main` and the deploy is live. — [source](archive/lessons-through-2026-11-15.md#verify-a-dependencys-failure-contract-never-let-a-mock-define-it-sprint-774-2026-10-19)
- Set a required env var before shipping the hard-fail guard that needs it, or the deploy fails while the old image keeps serving. — [source](archive/lessons-through-2026-11-15.md#verify-a-dependencys-failure-contract-never-let-a-mock-define-it-sprint-774-2026-10-19)
- Before debugging "runtime isn't doing X", prove the new code is on the running instance (new symbol, new log line, version SHA). — [source](archive/lessons-through-2026-11-15.md#verify-the-code-is-deployed-before-debugging-why-isnt-runtime-doing-x-sprint-716)
- Never put a health or liveness probe behind a dependency it reports on; check its decorators and middleware, not just its body. — [source](archive/lessons-through-2026-11-15.md#verify-a-dependencys-failure-contract-never-let-a-mock-define-it-sprint-774-2026-10-19)
- For any fail-closed decision, ask what restores service and who has to be awake; abuse controls should degrade, not take the service down. — [source](archive/lessons-through-2026-11-15.md#verify-a-dependencys-failure-contract-never-let-a-mock-define-it-sprint-774-2026-10-19)
- Treat silence as a hypothesis: define the verification window and the disambiguator before declaring a recurring failure fixed. — [source](archive/lessons-through-2026-11-15.md#broaden-your-search-before-declaring-victory-treat-silence-as-a-hypothesis-sprint-732-step-2c-2026-04-28)
- When investigating one logger's failures, first list all its distinct messages, then narrow. — [source](archive/lessons-through-2026-11-15.md#broaden-your-search-before-declaring-victory-treat-silence-as-a-hypothesis-sprint-732-step-2c-2026-04-28)
- Before recommending "leave the safety net alone", show evidence it actually fires in the current deploy or test path. — [source](archive/lessons-through-2026-11-15.md#verify-the-safety-net-is-actually-firing-before-recommending-leave-alone-sprint-736)
- Treat `records_processed: 0` from a job as suspicious, not success; assert that the job has work and does it. — [source](archive/lessons-through-2026-11-15.md#a-constraint-that-exists-only-in-production-is-invisible-to-the-test-suite-sprint-741a-2026-10-20)
- Never screenshot a cloud env-var page in edit mode. If a secret leaks: don't save, rotate at the issuer, re-paste, then save. — [source](archive/lessons-through-2026-11-15.md#screenshotting-a-render-env-var-edit-form-leaks-secrets-into-the-tool-log-session-2026-04-23)
- Before scheduling "service X forwards to service Y", check that the wire protocols match. — [source](archive/lessons-through-2026-11-15.md#render-log-streams--grafana-cloud-loki--check-protocol-before-scheduling-sprint-716)
- Pin nightly and CI scanners to the environment production installs into (the venv, not system Python). — [source](archive/lessons-through-2026-11-15.md#overnight-scanners-can-scan-the-wrong-python-sprint-675)
- Give subprocess timeouts 2–3× headroom; if runtime is within 5% of the timeout, fix it this week. — [source](archive/lessons-through-2026-11-15.md#a-nightly-pytest-subprocess-timeout-is-a-ticking-clock-not-a-background-concern-sprint-674)
- Read the nightly even when CI is green; it catches failures that live between environments. — [source](archive/lessons-through-2026-11-15.md#sprint-786b-nightly--which-answering-is-not-the-tool-answering)

### Testing
- A new guard is done only after you've watched it fail on an injected violation and pass on restore. — [source](archive/lessons-through-2026-11-15.md#a-guard-that-cannot-fail-is-worse-than-no-guard-sprint-787b-2026-10-21)
- Regression-prove a guard with the case least likely to be covered, on the surface customers actually see. — [source](archive/lessons-through-2026-11-15.md#the-guard-i-wrote-to-prevent-a-defect-had-the-defect-sprint-792-review-2026-10-21)
- When a test is cited as the reason a risky choice is safe, break that choice and watch that test fail. — [source](archive/lessons-through-2026-11-15.md#a-fixture-can-be-orthogonal-to-the-property-it-claims-to-protect-sprint-789b-2026-10-21)
- When a proof passes, ask "what did I actually just measure?", not "is the fix good?" — [source](archive/lessons-through-2026-11-15.md#four-regression-proofs-failed-to-fail-and-each-one-taught-me-something-different-2026-10-22)
- A guard that parses before it checks needs a coverage self-check, built independently of the parser; unparseable input is an error, not a skip. — [source](archive/lessons-through-2026-11-15.md#a-parser-based-guard-can-shrink-without-any-test-noticing-sprint-786c-review-2026-10-21) · [oracle](archive/lessons-through-2026-11-15.md#the-oracle-must-not-share-the-parsers-blind-spot--i-nearly-shipped-that) · [741d](archive/lessons-through-2026-11-15.md#sprint-741d--a-hand-read-sample-is-not-a-measurement)
- Derive a scan set from the running system, else a glob, else a hand list with a test that it still matches; every scan asserts it found something. — [source](archive/lessons-through-2026-11-15.md#audit-the-class-once-you-have-seen-the-instance-three-times-sprint-792-2026-10-21)
- Dry-run a new static check across the real tree and review the passes as carefully as the failures. — [source](archive/lessons-through-2026-11-15.md#dry-run-a-new-guard-across-the-real-tree-and-read-the-passes-too-sprint-789b-2026-10-21)
- State a gate's coverage as the claims it checks, not the files it reads. — [source](archive/lessons-through-2026-11-15.md#a-gate-on-a-file-is-not-a-gate-on-the-files-claims-sprint-784c-2026-10-21)
- Assert the content of a finding (file, line, matched text), not just that findings exist; order regex alternations longest-first. — [source](archive/lessons-through-2026-11-15.md#a-guard-firing-is-not-the-same-as-a-guard-being-right-sprint-782a-2026-10-20)
- Pin false-positive classes in unit tests; a noisy first run gets a gate disabled. — [source](archive/lessons-through-2026-11-15.md#a-guard-that-cannot-fail-on-the-surface-that-matters-is-decoration-sprint-784-2026-10-20)
- Gates fail on unmapped items, key allowlists by content not line number, and assert exemptions are still needed. — [source](archive/lessons-through-2026-11-15.md#fixing-instances-is-cheaper-than-fixing-the-class-and-that-is-why-the-class-comes-back)
- Enumerate matches with `finditer` and dedupe; never `search` and stop at the first. — [source](archive/lessons-through-2026-11-15.md#search-means-is-there-a-match-not-are-the-matches-all-fine-sprint-789b-review-2026-10-21)
- Detect a command by its position, not by substring; don't add a dependency CI may lack just to write a guard. — [source](archive/lessons-through-2026-11-15.md#sprint-794b--run-the-real-tool-against-a-real-failure-before-writing-the-check)
- Assert against behaviour or the external system, never against a second description of the same fact. — [source](archive/lessons-through-2026-11-15.md#counting-the-catalog-twice-is-not-the-same-as-checking-it-works-sprint-789-2026-10-21) · [780](archive/lessons-through-2026-11-15.md#a-test-that-only-checks-a-table-against-itself-proves-nothing-sprint-780-2026-10-20)
- A test may only hardcode a value it owns; derive counts from the registry. — [source](archive/lessons-through-2026-11-15.md#a-test-that-hardcodes-a-count-defends-the-drift-it-was-meant-to-catch-sprint-787-2026-10-20)
- When changing behaviour, first find and rewrite the tests that encode the old (wrong) contract. — [source](archive/lessons-through-2026-11-15.md#silent-success-bugs-surface-only-when-you-explicitly-test-the-failure-mode-sprint-666)
- Build third-party mocks from the real library's behaviour and keep one offline test against the real SDK. — [source](archive/lessons-through-2026-11-15.md#a-fully-mocked-sdk-cannot-notice-the-sdk-changing-2026-10-27)
- Never test a copy of the code; make it importable. — [source](archive/lessons-through-2026-11-15.md#a-test-that-exercises-a-copy-of-the-code-proves-nothing-about-the-code-2026-10-24)
- Run tests that read process-global state (`Base.metadata`) in a subprocess. — [source](archive/lessons-through-2026-11-15.md#basemetadata-is-process-global-and-a-schema-test-that-forgets-it-measures-the-wrong-database-2026-10-23)
- Prefer fixtures that go through the real serializer, and fixtures that discriminate the property under test. — [source](archive/lessons-through-2026-11-15.md#a-green-test-can-be-evidence-of-nothing-and-the-fixture-is-where-to-look) · [795/796](archive/lessons-through-2026-11-15.md#rounding-each-column-independently-means-the-row-never-foots-sprints-795796-2026-10-22)
- When a test has to supply an input the product should supply, that is the gap; acceptance tests span every layer. — [source](archive/lessons-through-2026-11-15.md#three-sprints-in-a-row-claimed-a-path-they-had-each-only-half-built-sprint-787b-review-2026-10-21)
- Test durability through the real `get_db` and an independent read-back session; test "not yours" and "doesn't exist" IDs. — [source](archive/lessons-through-2026-11-15.md#a-declared-contract-nobody-implements-is-a-bug-with-documentation-sprint-787b-review-2026-10-21)
- Parity-test every two-form input path (Bearer/cookie, query/body) through one helper. — [source](archive/lessons-through-2026-11-15.md#two-form-code-paths-need-parity-tests-not-just-a-one-form-test-sprint-718)
- Log-emission tests assert severity, emitter and detail, not just a record count. — [source](archive/lessons-through-2026-11-15.md#log-emission-tests-must-inspect-message-content-not-just-count-records-sprint-715)
- Skip guards probe the capability (run it), not `shutil.which`. — [source](archive/lessons-through-2026-11-15.md#sprint-786b-nightly--which-answering-is-not-the-tool-answering)
- Never assert on raw PDF bytes; assert extracted text or structure. — [source](archive/lessons-through-2026-11-15.md#pdf-binary-search-assertions-are-unreliable)
- Never hardcode fixture dates or rely on `time.sleep`; use relative, deterministic timestamps. — [source](archive/lessons-through-2026-11-15.md#security-sprint-476--hardening)
- Pin the contract (prefix, severity) in tests, not editorial prose. — [source](archive/lessons-through-2026-11-15.md#sprint-786b-pr-195-review--grep-for-the-claim-not-just-for-the-number)

### Data handling & customer claims
- **A claim we cannot prove from the code or a published document is removed, not reworded** (CEO, 2026-11-14).
- Never use "Zero-Storage", "never stored", "zero retention" or "not written to disk" in customer-facing text, PDFs or emails; use the approved sentence in `frontend/src/content/storage-statement.ts`. — [source](archive/lessons-through-2026-11-15.md#2026-11-15--sprint-865-the-claims-guards-covered-the-website-not-the-documents-customers-file)
- State exactly where processing happens: most uploads are parsed on the server in memory; SoD, Intercompany, W-2 and 1099 parse CSVs in the browser. — [source](archive/lessons-through-2026-11-15.md#storage-claims-must-distinguish-server-in-memory-from-browser-only)
- Check every factual sentence in new or replacement copy against the code before it ships. Phrase guards don't catch false facts. — [source](archive/lessons-through-2026-11-15.md#2026-11-14--sprint-861-replacement-copy-needs-the-same-proof-as-the-copy-it-replaces)
- When retiring a claim, grep the whole repo (backend literals, PDF/email templates, fixtures), then add the phrase to the guard covering that surface. — [source](archive/lessons-through-2026-11-15.md#2026-11-15--sprint-865-the-claims-guards-covered-the-website-not-the-documents-customers-file)
- Never show a certification badge or "compliant" status; say what is and isn't held. — [source](archive/lessons-through-2026-11-15.md#self-assessed-vs-independently-attested-compliance-must-be-visually-distinguished)
- Mark "complete" only when the feature is reachable by users and computes correctly; grep for non-test callers. — [source](archive/lessons-through-2026-11-15.md#a-feature-can-be-correct-documented-and-reachable-by-nobody-sprint-798-2026-10-22)
- Write docs from the implementation; for an export, the ground truth is the writer's header row. — [source](archive/lessons-through-2026-11-15.md#writing-docs-from-the-engine-means-from-the-implementation-not-the-docstring-pr-184-review-2026-10-21)
- Where the choice is a wrong number or no number, refuse with an error that names the gap. — [source](archive/lessons-through-2026-11-15.md#an-input-accepted-echoed-back-and-never-read-sprint-795-2026-10-22)
- Quantize independent quantities and derive dependent ones; every schedule row foots and every column reconciles. — [source](archive/lessons-through-2026-11-15.md#rounding-each-column-independently-means-the-row-never-foots-sprints-795796-2026-10-22)
- Totals use the same function as the displayed detail rows; expose score breakdowns. — [source](archive/lessons-through-2026-11-15.md#pdf-report-totals-must-match-displayed-detail-rows-sprint-522) · [risk](archive/lessons-through-2026-11-15.md#risk-scores-require-transparency--unexplained-numbers-are-arbitrary-sprint-522)
- Generate sample-report data through the engine's own functions, never hand-typed values. — [source](archive/lessons-through-2026-11-15.md#statistical-sampling-evaluation-report-sprint-508)
- Keep one registry for any fact quoted in 3+ places, with a CI test that fails on disagreement. — [source](archive/lessons-through-2026-11-15.md#pair-every-stated-truth-with-a-ci-enforced-source-of-truth-sprint-717)
- Detect data anomalies, never assess audit risk: "Follow-Up Items", "Data Anomalies", "Items Flagged" — never "Findings", never auto-classify deficiencies. — [source](archive/lessons-through-2026-11-15.md#engagement-management--engagement-assurance)

### Citations & methodology
- Give every attribution a stated strength (required / described / published method / our convention); default to the weaker claim. — [source](archive/lessons-through-2026-11-15.md#a-citation-is-a-claim-catalogue-them-before-you-trust-them-sprints-835837-2026-10-24)
- Cite the standard number, not sub-paragraphs, unless quoting a known revision. — [source](archive/lessons-through-2026-11-15.md#digital-excellence-council-remediation-sprint-497)
- Before changing score aggregation, run clean fixtures through old and new side by side. — [source](archive/lessons-through-2026-11-15.md#averaging-hid-false-positives-a-floor-surfaced-them-sprint-831-2026-10-24)
- Verify a review's remedy separately from its finding; re-derive it from first principles. — [source](archive/lessons-through-2026-11-15.md#the-reports-recommended-fix-was-wrong-twice-in-opposite-directions)
- Validate classification rules against a reference population, not a list of known-bad names. — [source](archive/lessons-through-2026-11-15.md#measuring-against-a-population-finds-what-a-list-of-known-bad-names-cannot)
- Test substring keywords against longer words ("rent" in "current") and check conflicts across lists. — [source](archive/lessons-through-2026-11-15.md#substring-keyword-matching-can-cause-false-positives-on-unrelated-account-names-sprint-537)
- Compute ratios from the full TB population, never filtered subsets. — [source](archive/lessons-through-2026-11-15.md#analytical-procedures-report-sprint-505)
- Specific keyword tiers go before general escalation rules; cap the lowest tier's score contribution. — [source](archive/lessons-through-2026-11-15.md#new-severity-tiers-require-three-layer-propagation-engine--score--ui-sprint-538)
- Procedure text depends on the flag's context; identical text for different flags is a defect. — [source](archive/lessons-through-2026-11-15.md#procedure-text-and-score-labels-must-be-contextually-differentiated-not-template-driven-sprint-524)

### Backend (Python / FastAPI / SQLAlchemy / Pandas)
- If the client reads a value back immediately, write it synchronously, not in a `BackgroundTask`. — [source](archive/lessons-through-2026-11-15.md#a-background-task-finishes-after-the-client-is-already-acting-on-the-response-sprint-791-review-2026-10-21)
- Resolve request-supplied IDs before writing rows that reference them. — [source](archive/lessons-through-2026-11-15.md#ordering-a-write-before-its-validation-turns-bad-input-into-a-500-sprint-787b-review-2026-10-21)
- SQLite-green proves nothing about Postgres-only constraints; assert the mapping and read the migrations. — [source](archive/lessons-through-2026-11-15.md#a-constraint-that-exists-only-in-production-is-invisible-to-the-test-suite-sprint-741a-2026-10-20)
- `Enum(PyEnum)` without `values_callable` stores member NAMES; raw SQL uses `'ACTIVE'`. — [source](archive/lessons-through-2026-11-15.md#sqlalchemy-enumpythonenum-stores-member-names-not-values)
- Every new model needs an Alembic migration; `create_all()` in tests hides a missing one. — [source](archive/lessons-through-2026-11-15.md#model-without-migration-is-a-silent-production-bomb)
- Add `foreign_keys=` whenever a model has 2+ FKs to the same table, including mixin FKs. — [source](archive/lessons-through-2026-11-15.md#multiple-fks-to-same-table-require-foreign_keys-disambiguation)
- Use `Decimal.quantize(ROUND_HALF_UP)` and Decimal tolerances, never `round()` or float tolerances. — [source](archive/lessons-through-2026-11-15.md#python-round-uses-bankers-rounding)
- Use `pd.api.types.is_string_dtype()`, never `dtype == object`. — [source](archive/lessons-through-2026-11-15.md#pandas-30-string-dtype-dtype--object-guard-breaks-for-csv-string-columns)
- Filter by `user_id`/`org_id` in the query, never fetch-then-check. — [source](archive/lessons-through-2026-11-15.md#multi-tenant-data-isolation)
- Match Stripe line items by price ID, dedupe webhooks by event ID, convert SDK objects to plain dicts at the boundary. — [source](archive/lessons-through-2026-11-15.md#billing-security-patterns--tenant-isolation-stripe-line-items-webhook-idempotency-sprint-520)
- Never return `detail=str(e)`; use `sanitize_error`, and log `type(e).__name__` for SDK errors. — [source](archive/lessons-through-2026-11-15.md#data-hardening-security-audit-sprint-494)
- `logger.warning(..., exc_info=True)` for handled 4xx paths; `logger.exception` only for real defects (it pages Sentry). — [source](archive/lessons-through-2026-11-15.md#loggerexception-on-a-user-facing-400-is-a-sentry-escalation-sprint-713)
- Sanitize every user string written to CSV/Excel cells and Content-Disposition; derive redirect URLs server-side. — [source](archive/lessons-through-2026-11-15.md#server-side-url-derivation--allowlist-validation-for-redirect-security)
- Route every ingestion path through the shared format dispatcher. — [source](archive/lessons-through-2026-11-15.md#diagnostic-ingestion-bypasses-the-parser-dispatcher-sprint-665)
- Inventory call sites before a per-call-site fix; with hundreds, guard the shared boundary. — [source](archive/lessons-through-2026-11-15.md#count-the-call-sites-before-choosing-where-a-fix-lives-2026-10-27)
- In `BaseHTTPMiddleware`, return a JSON `Response` rather than raising `HTTPException`. — [source](archive/lessons-through-2026-11-15.md#basehttpmiddleware-cannot-raise-httpexception)

### Frontend (React / Next / Jest / Tailwind)
- Before fixing a component, confirm something renders it; delete dead code holding stale copies of live data. — [source](archive/lessons-through-2026-11-15.md#dead-code-with-a-stale-copy-of-real-data-misdirects-the-next-reader-sprint-788-2026-10-20)
- Derive layout constants from data rather than hardcoding counts. — [source](archive/lessons-through-2026-11-15.md#dead-code-with-a-stale-copy-of-real-data-misdirects-the-next-reader-sprint-788-2026-10-20)
- Theme with `data-theme` and semantic tokens; no `dark:` variants. — [source](archive/lessons-through-2026-11-15.md#the-reports-recommended-fix-was-wrong-twice-in-opposite-directions)
- Tailwind silently drops undefined shades and opacity modifiers on CSS-variable tokens; lint for them. — [source](archive/lessons-through-2026-11-15.md#tailwind-silently-drops-undefined-color-shades)
- Never hard-gate UI on `prefers-reduced-motion`; use `<MotionConfig reducedMotion="user">`; `as const` on transitions. — [source](archive/lessons-through-2026-11-15.md#heroproductfilm-redesign-sprint-480)
- React 19 + jsdom: `fireEvent.change` plus `act`-wrapped submit/blur for value-dependent validation. — [source](archive/lessons-through-2026-11-15.md#react-19--jsdom-form-submission-testing-pattern)
- Mock the exact import path a component uses, include every export it uses, and re-set `mockReturnValue` after `clearAllMocks`. — [source](archive/lessons-through-2026-11-15.md#mock-the-import-path-the-component-actually-uses)
- Run the full Jest suite for any TS/TSX change. — [source](archive/lessons-through-2026-11-15.md#npm-test-must-run-full-suite--never-targeted-subsets)

### Git, CI & process
- A check that depends on something outside the commit has three outcomes: pass, fail, did-not-run. — [source](archive/lessons-through-2026-11-15.md#sprint-794--pass--fail-is-the-wrong-shape-for-any-check-that-can-be-prevented-from-running)
- Assert each input of a verdict can independently change the outcome. — [source](archive/lessons-through-2026-11-15.md#one-broken-check-can-hide-another-indefinitely-sprint-778a-2026-10-21)
- When a job changes from always-pass to sometimes-fail, list its `needs:` dependents; they will silently skip. — [source](archive/lessons-through-2026-11-15.md#making-a-check-honest-can-disable-what-the-honesty-protects-sprint-778a-review-2026-10-21)
- Review re-enabled, previously suppressed code as brand-new code. — [source](archive/lessons-through-2026-11-15.md#un-suppressing-a-code-path-means-shipping-code-that-has-never-run-sprint-778a-review-2026-10-21)
- Wire every executable guard into a required check. — [source](archive/lessons-through-2026-11-15.md#the-tests-that-watch-the-build-were-themselves-unwatched-sprint-802-2026-10-22)
- When a pipeline computes a quantity twice, assert they agree before the irreversible step. — [source](archive/lessons-through-2026-11-15.md#when-two-passes-over-the-same-data-disagree-the-quiet-one-wins-sprint-785-2026-10-21)
- Never edit the tree while a long suite runs against it. — [source](archive/lessons-through-2026-11-15.md#do-not-edit-the-tree-while-a-suite-runs-against-it-2026-10-21)
- After any copy or doc change, run the full backend suite (private `--basetemp` on Windows), not just the guards you remember. — [source](archive/lessons-through-2026-11-15.md#2026-11-14--sprint-861862-run-the-whole-backend-suite-after-copy-changes-not-just-the-guards-you-know)
- Run `git ls-files`-based guards after `git add`; describe retired wording rather than quoting it. — [source](archive/lessons-through-2026-11-15.md#a-guard-that-scans-tracked-files-passes-on-the-file-you-just-created-2026-10-24)
- Check a filename is free before writing; an `M` instead of `??` in git status means you overwrote a file. — [source](archive/lessons-through-2026-11-15.md#a-test-that-exercises-a-copy-of-the-code-proves-nothing-about-the-code-2026-10-24)
- Run tools from their config directory (ruff in `backend/`) and confirm the config loaded. — [source](archive/lessons-through-2026-11-15.md#run-a-tool-from-the-directory-its-config-lives-in-same-sprint-twice)
- Record `pip freeze` in CI; decide floor vs pin per package. — [source](archive/lessons-through-2026-11-15.md#a--floor-is-a-standing-decision-to-accept-majors-you-never-see-sprint-786a-2026-10-20)
- On a version bump, grep for claims about the dependency as well as its number. — [source](archive/lessons-through-2026-11-15.md#sprint-786b-pr-195-review--grep-for-the-claim-not-just-for-the-number)
- Measure a candidate guard before building it; "don't build it" is a valid result. — [source](archive/lessons-through-2026-11-15.md#measure-before-building-the-guard--the-measurement-is-allowed-to-say-dont)
- After seeing a defect shape three times, gate the class instead of fixing instances. — [source](archive/lessons-through-2026-11-15.md#audit-the-class-once-you-have-seen-the-instance-three-times-sprint-792-2026-10-21)
- Before closing a pattern fix, grep the whole codebase and record the command and its zero result. — [source](archive/lessons-through-2026-11-15.md#remediation-completeness-sprint-482--audit-25)
- When changing a shared shape or renaming an enum, grep every consumer: backend, frontend, tests, runbooks. — [source](archive/lessons-through-2026-11-15.md#breaking-api-shape-changes-require-simultaneous-backend--frontend--test-updates-sprint-544)
- Before concluding a file lacks a behaviour, follow what it calls. — [source](archive/lessons-through-2026-11-15.md#no-references-in-the-file-is-evidence-of-delegation-not-of-a-defect-sprint-791-2026-10-21)
- Before testing an unused module to fix coverage, check whether it is dead code. — [source](archive/lessons-through-2026-11-15.md#a-coverage-sentinel-gap-can-be-dead-code-not-a-testing-gap-sprint-676)
- Verify subagent claims against live code before acting on or repeating them. — [source](archive/lessons-through-2026-11-15.md#subagent-findings-must-be-verified-against-live-code-before-acting-sprint-598)
- Verify a bug report's numbers against the source data before "fixing" the attributed cause. — [source](archive/lessons-through-2026-11-15.md#audit-the-file-before-auditing-the-code-on-a-misdiagnosed-bug-report-sprint-666)
- Never skip the Directive Protocol for urgent or security work; a 5-line todo entry is the minimum. — [source](archive/lessons-through-2026-11-15.md#directive-protocol-is-non-negotiable--urgency-does-not-waive-documentation-audit-29)
- Push decision-state (`reports/`, `tasks/`, `docs/`) promptly so GitHub matches local. — [source](archive/lessons-through-2026-11-15.md#keep-github-in-sync-with-local-so-claude-and-codex-dont-disagree-2026-04-28)
- Sprint numbers are claimed on `main`: before filing one, check open PRs for the same number (PR #312 filed 861/862 the same night they were used on `main`; renumbered 870/871).

### Working with the CEO
- Council advises and the CEO decides; carry out overrides fully and log them in todo.md. — [source](archive/lessons-through-2026-11-15.md#council-deferral-vs-ceo-override--respect-the-decision-hierarchy-sprint-519)
- When the CEO pushes back on a defensive framing, re-derive the cost from evidence instead of restating it. — [source](archive/lessons-through-2026-11-15.md#verify-the-safety-net-is-actually-firing-before-recommending-leave-alone-sprint-736)
- Bring changes that revise a standing decision to the CEO rather than deciding alone. — [source](archive/lessons-through-2026-11-15.md#a--floor-is-a-standing-decision-to-accept-majors-you-never-see-sprint-786a-2026-10-20)
- Give decisions as a recommendation with its reasoning, not a bare list of questions; answer what the code can answer yourself.
- Report status at its true scope, and say whether a list of defects is complete or only what has been found so far. — [source](archive/lessons-through-2026-11-15.md#three-sprints-in-a-row-claimed-a-path-they-had-each-only-half-built-sprint-787b-review-2026-10-21)

## Recent lessons

*(New entries go here, newest last. Earlier entries, including the three from 2026-11-14/15, are in the archive and in the rules above.)*
- **A library upgrade can silently disable a guard without failing a test (Sprint 883, 2026-11-18).** Under pandas 3,
  `Series.astype(str)` keeps a missing cell as NA instead of `"nan"`, so the streaming auditor's
  `isin(["", "nan", ...])` blank test stopped matching CSV blanks: the totals-row exclusion and `missing_names_count`
  went dead for CSV input, and no test noticed because the tests built DataFrames whose blanks were already `""`.
  Rule: test a guard through the real reader (`process_tb_chunked` / `parse_uploaded_file` on CSV bytes), not
  through a hand-built DataFrame, and after a pandas/numpy major re-check every `astype(str)` + string-compare blank test.
- **Make one parser the policy and route every path through it; then test the paths, not the parser (Sprint 883).**
  Four amount parsers disagreed on "$(2,000.00)", "1,234.56-", "€1,234.56" and "Infinity", and two of them crashed on
  inputs the others accepted. A single input table run through every path (preflight, intake, streaming, legacy,
  `safe_decimal`) found both crashes the review had not.
- **Route tests that pass only inside the full suite are order-dependent (Sprint 883).** The new mapping tests
  reached the routes in the full run but got 403 (CSRF) alone; another test had left CSRF bypassed. Run a new test
  file on its own before trusting it, and use the `bypass_csrf` fixture explicitly.
- **Run the snapshot suites, not just the tests named after the feature (Sprint 884).** The 9F revenue memo fix was
  committed after `-k revenue` passed; the Sprint 819 *route* snapshot that pins the same memo text
  (`route_testing_exports`) has no "revenue" in its name and failed later. After any change to a memo, export or
  serializer, run `tests/test_sprint819_*` and `tests/test_memo_render_equivalence.py` before committing.
- **`round()` on a Decimal is half-even; so is `"{:.2f}"` (Sprint 884).** The accrual, expense-category and 3WM
  serializers all called `round(x, 2)` on Decimals and so broke the half-up rule silently. Use `quantize_monetary`.
- **A Decimal pipeline can still lose digits in the writer (Sprint 884).** openpyxl writes every number with
  `"%.16g"`, so a Decimal cell holding 9007199254740993.01 reached the file as 9007199254740994 even with no `float()`
  in our code. Check the bytes on disk (the sheet XML), not the value handed to the library.
- **Find escape-hatch callers by instrumenting the hatch and running the suite (Sprint 885).** Changing the CSV
  writer from "skip anything that looks like a number" to "escape every str" needed every caller that passed amounts as
  formatted text. A temporary log line in the writer, run under the full suite, named the exercised sites (cash flow,
  testing-tool CSVs, multi-period, TB, depreciation) before a static sweep covered the rest.
- **For "escape user data" across ~1,000 call sites, build the detector first (Sprint 885).** Rendering every memo
  with white-text markup appended to each free-text input turned a vague review finding into a count per memo
  (~950 leaks → 0), told the codemods where they were not enough, and caught template text the codemods would have
  over-escaped (titles with `&amp;`) through the existing memo text snapshots.
- **AST codemods: `col_offset` counts UTF-8 bytes, not characters (Sprint 885).** A codemod that sliced source by
  `col_offset` corrupted a line holding "—" earlier on the line. Convert byte columns to character columns per line.
  Also: ruff here targets Python 3.11, so generated f-strings must not reuse the outer quote inside `{}`.
- **On this machine pass `--basetemp` to pytest when two runs overlap (Sprint 885).** A second pytest run while
  another held `pytest-of-<user>/pytest-current` failed with `PermissionError` before collecting anything.
- **Swapping a font is a layout change only if the metrics differ (Sprint 885).** Registering the metric-compatible
  Liberation fonts under the standard Times/Helvetica/Courier names changed no page count and moved text < 0.5pt —
  and exposed that the standard fonts had been printing substitute boxes for ✓ ⚠ ▢ all along.
- **A field can be dropped at three layers; check all three (Sprint 886).** The review found AP/payroll/AR schedules
  missing from the export model. The analysis *response model* (`extra="ignore"`) dropped them first, so the browser
  never had them, and the page did not send them either. For any "the document lacks X", trace X from the engine's
  `to_dict()` through the response model, the page's request body and the export model — a test through the real
  analysis route then the real export route is the only one that sees every layer.
- **A default in a document generator is a claim (Sprint 886).** `composite.get("score", 0)`, `.get("risk_tier",
  "low")`, `.get("going_concern", {})` and `.get("completeness_score", 0)` printed 0/100, LOW, "none identified" and
  0% for things nobody computed. Rule: in output code, absent is `None` and prints "Not available"/"Not evaluated";
  a test removes the field and asserts the wording.
- **Sample data written to a generator's expectations hides dead sections (Sprint 886).** The sample bank-rec, TWM and
  fixed-asset memos fed fields the engines never emit (`aging_summary`, a TWM score, register roll-forward), so those
  sections looked alive in every sample while no customer could get them. Build sample and test results from the
  engine's real output shape, and list each generator's `.get` keys against the engine's `to_dict()`.
- **Splitting one tree into per-item commits: stage computed blobs, not partial `-U0` patches (Sprint 886).**
  `git apply --cached --unidiff-zero` fails once an earlier hunk is skipped (line offsets shift). Stage the intended
  content instead — the working file with the later item's text reverted — via `git hash-object -w` + `git
  update-index --cacheinfo`; lint-staged keeps the unstaged remainder. On Windows, pipe patches as bytes (text mode
  turns LF into CRLF) and normalise CRLF before matching.
- **Grep for every removed name across the tests before committing; then run the full suite (Sprint 887).** Removing
  `TestingMemoConfig.risk_assessments` (12C) passed the targeted memo tests, but three other test files still passed
  the field and a fourth pinned the 12A thresholds dict; only the full run found them, two commits later. A second
  full run at the end found four more contract tests (CSV header, PDF section label, recorder signature, a factor
  name). Rule: `git grep <removed symbol or string>` in `backend/tests` and `frontend/src/__tests__` before each
  commit that renames or removes, and one full backend run before the record commit.
- **Scan for whole words when checking that a word is gone (Sprint 887).** A test that "LOW" no longer appears failed
  on "FOLLOW-UP ITEM POINTS". Use word boundaries (and allow listed terms such as "Passed AJE") in vocabulary scans.
- **Another session can commit onto your branch when sessions share a working tree (Sprint 887).** A Sprint 886
  follow-up landed on `sprint-887-generated-wording` mid-task. Check `git log` before each commit, and give parallel
  sessions their own worktree.
- **In this harness, write edit scripts to files, not shell heredocs (Sprint 887).** Inline heredocs dropped or
  doubled backslashes (`\u2265`, `\b`) and once failed to parse; the same script written with the file tool ran.
- **An event handler can make its sibling event look stale (Sprint 888).** `invoice.paid` writes the subscription row,
  moving the `updated_at` that the webhook ordering guard compares with `event.created`, so Stripe's
  `customer.subscription.updated` for the same recovery is skipped and the paying user stays on Free. Rule: when a
  handler writes the row an ordering guard reads, test every delivery order of the events Stripe sends together.
- **"Held for up to N minutes, then released" needs a timer, not lazy eviction (Sprint 888).** The preview cache
  checks expiry only on the next `put()` or lookup, so an unused file stays in memory indefinitely. Check how expiry
  is enforced, not only the TTL constant, before publishing a retention sentence.
- **Derive copy checks from the code, not a literal list (Sprint 888).** The format test computes the enabled set from
  `FORMAT_PROFILES` and `is_format_enabled`, so turning ODS on fails the copy test until the FAQ names it.
- **Run the old tests against the mutation too (Sprint 889).** A mutation that fails the new test proves little if it also
  failed the old suite. Running both showed which gaps were real (heatmap, multi-period, guarded asserts, the MUS
  one-row shift) and which mutations other tests already caught (lease timing). Keep a scratch mutation runner that
  restores the file in `finally`, and match CRLF endings on Windows checkouts.
- **`alembic upgrade head` on an empty PostgreSQL is a test of its own (Sprint 889).** The chain had never completed:
  enum types not created, new enum values used in the same transaction, a value added to one tier type but not the
  other. Production was built with `create_all` and stamped, which hides all of it until a disaster-recovery rebuild.
  An embedded server (`pgserver` in a scratch venv) is enough to find this without Docker.
- **E2E credentials in repository secrets do not exist in a CI-local database (Sprint 889).** The job started its own
  backend on a fresh SQLite file, so the secret account could never log in — and the repo had no secrets anyway, so
  everything skipped. Seed a fixed account into the throwaway database instead; use a domain the email validator
  accepts (`.test` is rejected).
- **Moving work off the event loop needs a session per unit, and tests must still see the test database (Sprint 890).**
  `database.get_session_scope` resolves `get_db` through `app.dependency_overrides`, so a synchronous unit opens its
  own session in production and the test's transactional session in tests. Never call `rollback()` in such a unit
  just to discard a probe — under the test override it rolls back the fixtures.
- **Prove "off the event loop" with a probe, not an AST check (Sprint 890).** Hold the blocking dependency open on a
  `threading.Event` and require `GET /health/live` to finish meanwhile (`tests/helpers/event_loop_probe.py`). Every
  step's probe failed before its change.
- **A static guard that reads one function at a time breaks when work moves into nested helpers (Sprint 890).** The
  Sprint 790 metering guard now judges a function together with the helpers defined inside it.
- **Replace a whole function by its boundaries, not by searching for its last statement (Sprint 890).** Twice an edit
  stopped at an earlier `return Response(...)` and left the old body behind; cut from `def` to the next decorator.


- **2026-11-16 (Sprint 853):** a destructive action can have more than one door. Engagement archive was reachable
  through `DELETE /engagements/{id}` *and* `PUT /engagements/{id}` with `status=archived`; a gate on the archive method
  alone would have left the PUT open. Put the gate where the state changes (the manager), and test every door.
- **2026-11-16 (Sprint 853):** an access rule derived from someone's *current* membership moves with them. Record the
  owning firm on the record itself, and scope every child record through that one column via a single shared filter
  (`client_scope`), never a per-manager copy.
- **2026-11-16 (Sprint 872):** `bypass_csrf` is session-scoped — once any test uses it, CSRF stays bypassed for every
  later test in the run. A test that needs a *real* CSRF rejection passed alone and failed in the full suite. Force the
  path you test (`monkeypatch` the validator) instead of assuming fixture state; prove order-independence by running it
  after a bypassing test file.
- **2026-11-16 (Sprint 872):** in cookie-auth mode the frontend `token` is a constant sentinel, so anything keyed or
  compared on it (caches, de-dup, "did the user change?") cannot tell accounts apart. Key private client state on the
  signed-in account id.
- **2026-11-16 (Sprint 872):** changing an error body's `message` can change what the UI shows: the frontend passes only
  allowlisted backend strings and otherwise shows a generic fallback. When moving an error into the common shape, check
  the allowlist (`SAFE_PASSTHROUGH`) — the 429 text had to be added.
- **2026-11-16 (Sprint 878):** a quota is only as strong as the thing it counts. The Free allowance counted
  ActivityLog rows the browser writes and the user can clear, so the meter was client-controlled. Count usage from a
  record the server writes on its own success path and no user route can touch; and make the check and the increment
  resolve the same source in one function, so they cannot drift (firm members were checked against the firm's
  allowance but counted alone).
- **2026-11-16 (Sprint 878):** check the input you will process, not the input you were handed. The analysis
  format-checked the new upload's name and then analysed a cached file from a preview token. Resolve the real input
  first, then gate it (by detected format when the name has no extension, as the parser does).
- **2026-11-16 (Sprint 878):** a fresh `git worktree` runs **no** commit hooks — `core.hooksPath` points at
  `frontend/.husky/_`, which is generated and untracked. Copy it from the main checkout before the first commit. And
  `next build` (Turbopack) cannot resolve packages through a `node_modules` junction outside the worktree; run `npm ci`
  in the worktree instead of linking.
- **2026-11-16 (Sprint 879):** to keep values out of logs, enforce it where the record is created (a log-record
  factory), not in a handler filter — filters run only on the handlers they are attached to, and Sentry's logging hook
  reads the record before any handler. But don't strip `exc_info` to do it: Sentry needs it for stack frames (its own
  scrubber removes the message). Pre-set `record.exc_text` to the safe summary; `logging.Formatter` renders a pre-set
  `exc_text` instead of the traceback. An existing test that asserted `exc_info` survived caught the first version.
