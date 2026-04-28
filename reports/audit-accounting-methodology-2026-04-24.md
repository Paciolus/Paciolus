# Audit Methodology Gap Analysis -- Paciolus v2.1.0
**Date:** 2026-04-24  
**Scope:** Platform-wide methodology coverage, citation accuracy, audit-boundary risk, missing tests, workflow fidelity, Phase 3 CPA readiness  
**Analyst lens:** Trial-balance-first diagnostic intelligence platform -- NOT an audit engine

---

## 1. Executive Summary

Paciolus demonstrates strong TB-driven diagnostic coverage across most IAASB/PCAOB risk domains with correctly bounded language guardrails (banned-patterns regex, ISA 265 structural prohibitions, non-committal scope/methodology templates). The principal methodology risk is not overreach into assurance territory -- that boundary is actively enforced at the code level -- but gaps in the mid-engagement workflow CPAs expect between risk assessment output and substantive conclusion. Three material gaps dominate: (1) no independent expectation-formation workflow for analytical procedures per ISA 520.5(a) / AS 2305.10; (2) no Summary of Uncorrected Misstatements schedule per ISA 450; (3) a three-way match engine structurally blind to service-invoice populations. Citation accuracy in the shipped backend is sound; however, the documented AS 1215 / AS 2401 confusion persists in external-facing docs and marketing copy, creating an immediate credibility risk with PCAOB-registered firms.

---

## 2. Methodology Coverage by Engagement Phase

### 2.1 Planning and Scoping

**Present:**
- Preflight TB quality assessment (ISA 315 readiness gate)
- Materiality cascade per ISA 320 / AU-C 320 with ISA 320.11 cited precisely in sampling_memo_generator.py line 709
- Going concern indicator profile: 7 TB-derivable ISA 570 para 16 indicators with explicit disclaimer for 6 non-TB-derivable categories
- Composite risk matrix: ISA 315 Appendix 1 4x4 RMM -- Sprint 680 corrected the prior max(IR,CR) approximation to the proper matrix lookup
- Population profile: stratification, account distribution, Herfindahl concentration

**Missing / Thin:**
- No engagement-letter scope template or structured assertion-mapping worksheet. CPAs arrive with a TB and no standardized mechanism to document which assertions are in scope for which accounts before running tools.
- Detection risk is explicitly disclaimed as outside scope in composite_risk_engine.py DISCLAIMER (correct), but leaves the audit-risk model (AR = IR x CR x DR) with no articulation path.

### 2.2 Risk Assessment

**Present:** Related party detection (ASC 850), anomaly detection (z-score, round amounts, sign anomalies, concentration), cutoff risk engine (3 deterministic tests, ISA 501 / ASC 855), accrual completeness engine (12 accrual types), going concern (7 ISA 570 para 16 indicators), lease classification flag (ASC 842 / IFRS 16), account risk heatmap, classification validator.

**Missing:** No impairment-indicator surface for goodwill/intangibles (ASC 350 / IAS 36). No contingency/warranty adequacy ratio (ASC 450 / IAS 37). No subsequent-events scan (ASC 855 / ISA 560 evaluation window).

### 2.3 Substantive Procedures -- Analytical

**Critical Gap -- Expectation Formation:** ISA 520.5(a) and AS 2305.10 require the auditor to form an independent expectation before comparing to recorded amounts. The platform ratio and flux engines produce observed-vs-prior comparisons but do not provide a structured expectation-formation workflow. CPAs using substantive analytical procedures as a primary procedure must document: (1) the basis for the expectation, (2) the precision threshold, (3) the corroboration source. None of these slots exist in any current tool output. A Big-4 quality reviewer would note this immediately. All tools use a single global materiality threshold; ISA 520 requires precision tight enough to detect misstatements at the assertion level. No account-level precision cascade exists.

### 2.4 Substantive Procedures -- Tests of Detail

**Present (12 tools):** JE (19 tests), AP (14 tests), Payroll (13 tests), Revenue (18 tests incl. ASC 606/IFRS 15), AR Aging (12 tests), Fixed Assets (11 tests incl. depreciation recalc), Inventory (10 tests), Bank Rec, Three-Way Match, Multi-Period, Statistical Sampling (ISA 530 / AICPA Table A-1), Multi-Currency.

**Missing Tests by Tool:**

| Tool | Missing Test | Literature Basis |
|------|-------------|------------------|
| Three-Way Match | Service-invoice population bypass. Engine requires PO + Invoice + GRN. Service invoices have no GRN counterpart. No two-way match path exists -- systematic untested population in virtually all commercial clients. | ACFE 2024 p.112; COSO 2013 PC10.3 |
| Inventory | No cash-to-cash cycle (DIO + DSO minus DPO) integration with AR/AP TB accounts. Working capital cycle efficiency indicator absent. | ISA 501.A7; IAS 2.32 |
| Inventory | No interperiod obsolescence trend. Slow-moving flag is point-in-time only. | ISA 540.A63 |
| Fixed Assets | No impairment trigger (large goodwill adjacent to declining revenue or negative EBIT). | ASC 350-20-35-3C Step 0; IAS 36.12 |
| Payroll | PR-T12 and PR-T13 credited as shipped in CLAUDE.md but absent from PAYROLL_TEST_DESCRIPTIONS in payroll_testing_memo_generator.py (only T1-T11 documented). Engine findings undocumented in PDF memo. | Internal consistency gap |
| Revenue | Missing channel/geography disaggregation completeness test. | ASC 606-10-50-5 |
| JE | No cross-entity journal entry test. Intercompany elimination engine exists but not cross-linked to JE testing. | ISA 240.A32 |
| AP | No vendor master file change log analysis (new vendors within 30 days of first payment). | ACFE 2024 p.89 |
| Statistical Sampling | No non-statistical (judgmental) sample documentation path. | ISA 530.A8 |

### 2.5 Evaluation and Conclusion

**Missing:** No standalone SUM (Summary of Uncorrected Misstatements) schedule per ISA 450 / AU-C 450. No management representation letter checklist (ISA 580) derived from procedures performed.

### 2.6 Reporting

**Missing:** No structured mapping from tool outputs to financial statement line items and disclosure risks. No going concern conclusion worksheet per ISA 570.19-20.

---

## 3. Citation Accuracy Assessment

### 3.1 Shipped Memo Generator Citations

| Standard | Usage | Accuracy |
|----------|-------|----------|
| PCAOB AS 2401 | JE, AP, Payroll, Revenue memos | Correct |
| PCAOB AS 2501 | AR Aging, Fixed Asset, Inventory memos | Correct |
| PCAOB AS 2305 | Multi-Period, Expense Category memos | Correct |
| PCAOB AS 2310 | Bank Rec memo | Correct |
| ISA 315 | Composite risk, preflight | Correct; Appendix 1 4x4 matrix verified in composite_risk_engine.py |
| ISA 320 | Materiality cascade | Correct; ISA 320.11 cited precisely in sampling_memo_generator.py line 709 |
| ISA 530 | Statistical sampling | Correct; AICPA Table A-1 expansion factors verified in shared/aicpa_tables.py |
| ISA 570 | Going concern engine | Correct; para 16 indicator mapping with documented non-TB-derivable exceptions |
| ISA 450 | Sampling memo step 3 | Correct |
| ISA 580 | Sampling memo step 4 | Correct |
| ASC 606-10-25-23 | Revenue cutoff_risk detail procedures | Correct paragraph |
| ASC 606-10-32-28 | Allocation inconsistency test | Correct |
| IAS 16 / ASC 360 | Depreciation recalculation Sprint 682 | Correct |
| ASC 326-20 | AR Aging YAML reference | Correct (CECL) |

Statistical sampling confidence factor derivation uses -ln(p) for Poisson confidence. At 95%: -ln(0.05) = 2.996, displayed as 3.0000. Mathematically correct for monetary unit sampling. Stringer bound table matches published AICPA guidance. No fabricated values found.

### 3.2 Known Citation Defect -- PCAOB AS 1215

The shipped backend memo generators do NOT contain AS 1215. Searching backend/ for "1215" returns zero matches. The citation has been cleared from all engine and memo code.

However, AS 1215 (Audit Documentation) is referenced as the governing standard for JE Testing in:
- features/status.json (feature acceptance criteria: "Verify PCAOB AS 1215 citation")
- docs/01-product/USER_PERSONAS.md
- docs/07-user-facing/USER_GUIDE.md
- frontend/src/content/standards-specimen.ts
- frontend/src/app/(marketing)/trust/page.tsx

The correct governing standard for JE fraud testing is PCAOB AS 2401 (Consideration of Fraud), correctly cited in je_testing_memo_generator.py. AS 1215 governs audit documentation form and content -- it is a workpaper standards reference, not a fraud detection procedure standard. A PCAOB-registered firm reviewing the Trust page will flag this immediately.

**Citation Verdict: PASS on shipped backend. CONCERNING on external-facing documentation (AS 1215 in docs and frontend copy).**

---

## 4. Audit-Boundary Risk Assessment

### 4.1 Active Guardrails (Functioning Correctly)

1. shared/scope_methodology.py BANNED_PATTERNS regex: 12 patterns including "proves", "confirms", "constitutes fraud", "is a material misstatement", "guarantees", "certifies".
2. anomaly_summary_generator.py GUARDRAIL 3: structural prohibition on ISA 265 sections. Practitioner assessment blocks blank; auditor owns all classification.
3. composite_risk_engine.py DISCLAIMER: detection risk explicitly disclaimed; all risk classifications stated as auditor judgment.
4. going_concern_engine.py DISCLAIMER: 6 non-TB-derivable ISA 570 para 16 categories named and disclaimed.
5. test_accrual_completeness.py lines 529-541: mechanical assertion that "deficiency" and "material weakness" do not appear in narratives.

### 4.2 Boundary Risks -- Moderate

**Risk 1 -- Risk tier auto-assignment on memo output.** Every testing memo auto-assigns a risk tier (low / elevated / moderate / high) from flag density. Language is hedged but the tier label is visually prominent. A practitioner might treat it as an ISA 315 risk assessment conclusion. Recommendation: Append "(automated flag density indicator -- auditor judgment required per ISA 315)" to all risk tier labels.

**Risk 2 -- Three-way match language.** three_way_match_memo_generator.py, match rate below 80%: "systemic review of procure-to-pay controls recommended." Edges toward ISA 265 / control deficiency territory. Recommendation: Rephrase to "engagement team should evaluate whether procure-to-pay procedures warrant expansion."

**Risk 3 -- Allowance adequacy language.** ar_aging_memo_generator.py allowance_adequacy_ratio: "potential understatement of credit loss expense per ASC 326." The word "understatement" is a misstatement conclusion. Recommendation: Rephrase to "potential credit loss estimation anomaly requiring auditor evaluation per ASC 326."

### 4.3 Confirmed Non-Boundary (Correctly Handled)

Adjusting entries are approval-gated and not auto-classified as conclusions. Going concern produces a 7-indicator profile only; no "substantial doubt" conclusion output. Allowance adequacy memo states "anomaly indicator, not a sufficiency determination." ISA 265 is blocked at generator level with mechanically enforced test assertion.

---

## 5. Workflow Fidelity vs. Real Audit Practice

### 5.1 What the Engagement Layer Gets Right

Materiality cascade math is correct and ISA 320 paragraph references are accurate. Tool-run sequencing (preflight, TB analysis, tool testing, anomaly summary) maps to real audit workflow sequence. Workpaper index tracks tool execution with lead sheet cross-references. Follow-up item tracker is correctly bounded to narrative descriptions with no financial data persistence.

### 5.2 Workflow Gaps

**Gap 1 -- No assertion-level scoping worksheet.** Real engagements begin with an assertion matrix mapping accounts to assertions to procedures. The composite risk engine accepts assertion-level inputs but does not produce or enforce a coverage worksheet. A CPA cannot see "Completeness assertion for Revenue -- addressed by RT-04, RT-09, confirmation."

**Gap 2 -- Tools operate in isolation.** Each tool runs against a standalone file upload. The account risk heatmap aggregates signals post-hoc by account name string matching, fragile when account names vary across ERP export files.

**Gap 3 -- No engagement scope agreement.** No engagement scope template, no agreed-upon procedure list, no mechanism to distinguish audit from review or compilation.

**Gap 4 -- No supervisor review path.** workpaper_signoff accepts prepared_by and reviewed_by as free-text strings. The user model could support a review-approval workflow (ISQC 1 / PCAOB AS 1220) but does not currently implement it.

**Gap 5 -- Completion gate is tool-coverage-based, not assertion-coverage-based.** 100% convergence index is achievable by running all tools against trivially small populations without addressing all in-scope assertions.

---

## 6. Phase 3 CPA Expectations

A CPA doing end-to-end platform testing in Phase 3 will expect:

1. Engagement scoping before tools: engagement type (audit/review/AUP), materiality basis tied to entity characteristics per ISA 320.A3, assertion-level scoping. Engagement type and assertion scoping worksheet are absent.
2. ISA 520-compliant expectation documentation for analytical procedures. Absent.
3. A SUM schedule per ISA 450. Absent.
4. A representation letter checklist derived from procedures performed (ISA 580). Absent.
5. Service-invoice testing capability. Three-way match engine is goods-only.
6. Opening balance reconciliation workpaper per ISA 510. Multi-period tool provides flux but not a formal reconciliation.
7. Explicit disclosure at point of export that diagnostic memos are not ISA 230 / AS 1215 audit documentation. Boundary is in docs/tos-section-8-draft.md but not surfaced at the export interface.

---

## 7. Prioritized Feature Recommendations

See below for all 9 features in order of priority score.

**Feature 1 -- PCAOB AS 1215 Cleanup in External Docs**
Impact: 5 | Complexity: 1 | Priority Score: 5.0
Purpose: Remove AS 1215 as the governing JE Testing standard from features/status.json, docs/01-product/USER_PERSONAS.md, docs/07-user-facing/USER_GUIDE.md, frontend/src/content/standards-specimen.ts, frontend/src/app/(marketing)/trust/page.tsx. Replace with AS 2401 (Consideration of Fraud). Retain AS 1215 only where it correctly references workpaper documentation standards.
Zero-Storage Compatibility: Confirmed.
Customer Value: Prevents immediate credibility loss with PCAOB-registered firms at first Trust page inspection.

**Feature 2 -- PR-T12 / PR-T13 Payroll Memo Documentation**
Impact: 4 | Complexity: 1 | Priority Score: 4.0
Purpose: Add PR-T12 and PR-T13 entries to PAYROLL_TEST_DESCRIPTIONS in backend/payroll_testing_memo_generator.py. PR-T12: Flags employees with duplicate name matches across payroll register, a ghost-employee indicator. PR-T13: Reconciles total gross pay to total net pay accounting for all statutory deductions; flags unresolved residuals as payroll processing anomalies.
Zero-Storage Compatibility: Confirmed.
Customer Value: Closes a documentation gap that fails any workpaper quality review. Two-line fix.

**Feature 3 -- Boundary Language Remediation (3 instances)**
Impact: 4 | Complexity: 1 | Priority Score: 4.0
Purpose: Remove language patterns that edge toward audit conclusion territory. (1) backend/three_way_match_memo_generator.py line ~113: systemic review of procure-to-pay controls recommended --> engagement team should evaluate whether procure-to-pay procedures warrant expansion. (2) backend/ar_aging_memo_generator.py allowance_adequacy_ratio: potential understatement of credit loss expense per ASC 326 --> potential credit loss estimation anomaly requiring auditor evaluation per ASC 326. (3) All memo risk tier labels: append (automated flag density -- auditor judgment required per ISA 315).
Zero-Storage Compatibility: Confirmed.

**Feature 4 -- ISA 520 Expectation Formation Panel**
Impact: 5 | Complexity: 3 | Priority Score: 1.67
Purpose: Structured input/output for forming and documenting independent expectations per ISA 520.5(a) / AS 2305.10. Inputs: current-period TB plus optional prior-period TB plus optional industry benchmark from existing ratio engine. Outputs: expectation basis, precision threshold, expected range, actual-vs-expected variance, within-threshold indicator -- all in a PDF memo section.
Zero-Storage Compatibility: Confirmed -- all inputs ephemeral.
Customer Value: First tool producing ISA 520-compliant expectation documentation without an external spreadsheet.

**Feature 5 -- Summary of Uncorrected Misstatements Schedule**
Impact: 5 | Complexity: 3 | Priority Score: 1.67
Purpose: Standalone ISA 450 / AU-C 450 SUM schedule for end-of-engagement accumulation. Accepts: passed adjustment amounts (form input), UEL projections from sampling tool (JSON passthrough), overall materiality from engagement record. Applies trivial threshold filter, aggregates by assertion and direction, compares net aggregate to overall materiality.
Zero-Storage Compatibility: Confirmed -- SUM amounts entered per-session, not persisted.
Customer Value: Closes the single most workflow-critical gap for CPA end-of-engagement use.

**Feature 6 -- Three-Way Match: Service Invoice Path**
Impact: 4 | Complexity: 3 | Priority Score: 1.33
Purpose: PO plus Invoice (no GRN) two-way match path for service-category invoice populations. When invoice keywords match a configurable services list, route to two-way match instead of three-way. Report two_way_match_services flag type separately. Compute match rates separately for goods vs. services with distinct benchmarks.
Zero-Storage Compatibility: Confirmed.
Customer Value: Addresses systematic untested population in virtually all commercial audit clients.

**Feature 7 -- Impairment Indicator Screen**
Impact: 3 | Complexity: 2 | Priority Score: 1.5
Purpose: TB-derivable impairment screening when goodwill or intangibles exceed 10% of total assets. Compute goodwill/revenue, goodwill/EBIT, sustained operating loss indicator. Narrative: potential Step 0 qualitative impairment indicator -- auditor should evaluate whether formal quantitative assessment is required per ASC 350-20-35-3C / IAS 36.12.
Zero-Storage Compatibility: Confirmed.

**Feature 8 -- ISA 530 Judgmental Sample Documentation**
Impact: 3 | Complexity: 2 | Priority Score: 1.5
Purpose: ISA 530.A8-compliant workpaper for judgmental item selections. Accepts selected-item list, selection rationale (high value / high risk / unusual characteristics), population total. Computes coverage %, item count, high/low amounts. Outputs judgmental sample memo PDF with selection basis, coverage, and exceptions.
Zero-Storage Compatibility: Confirmed.

**Feature 9 -- Assertion Coverage Worksheet**
Impact: 4 | Complexity: 4 | Priority Score: 1.0
Purpose: Allow CPAs to define which assertions are in scope for which accounts before executing tools. Display TB accounts; auditor checks applicable assertions (Existence, Completeness, Valuation, Rights, Presentation). Record tool-to-assertion mappings. Output: coverage gap list and alerts on unaddressed pairs in workpaper index.
Zero-Storage Compatibility: Confirmed -- assertion selections passed per-session.

---

## 8. Priority Ranking by CPA-Retention Risk

| Rank | Feature | Impact | Complexity | Priority Score | Retention Risk Driver |
|------|---------|--------|------------|---------------|----------------------|
| 1 | AS 1215 citation cleanup in external docs | 5 | 1 | 5.0 | Immediate credibility loss with PCAOB-registered firms on first Trust page inspection |
| 2 | PR-T12/T13 payroll memo documentation | 4 | 1 | 4.0 | Engine findings undocumented in PDF -- fails workpaper quality review |
| 2 | Boundary language patch (3 instances) | 4 | 1 | 4.0 | ISA 265 proximity risk on control and misstatement language |
| 4 | ISA 520 expectation formation panel | 5 | 3 | 1.67 | First-session failure for CPA running substantive analytics as primary procedure |
| 4 | SUM schedule aggregator | 5 | 3 | 1.67 | End-of-engagement workflow breakage -- no engagement can be formally concluded |

---

## 9. Constraints Compliance

All recommendations are: executable from TB or tool-output data with no external system integration; deterministic and rules-based (no ML inference); zero-storage compatible (all financial data ephemeral per session); bounded as diagnostic aids that do not infer auditor judgment or produce audit conclusions.

---

*This document is a methodology gap analysis for an internal diagnostic intelligence platform. It does not constitute an audit opinion, engagement quality review conclusion, or regulatory compliance assessment.*
