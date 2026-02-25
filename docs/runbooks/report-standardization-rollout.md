# Report Standardization Rollout Playbook

**Version:** 1.0
**Sprint:** 8 (QA Automation + Regression Guardrails + Rollout)
**Owner:** Engineering / CEO Sign-off Required

---

## 1. Pilot Report List

The following reports form the pilot set for rollout verification. Each was selected to represent a distinct category of the reporting pipeline.

| # | Report Type | Generator | Category | Priority |
|---|-------------|-----------|----------|----------|
| 1 | TB Diagnostic Intelligence Summary | `pdf_generator.py` | Primary Diagnostic | P0 |
| 2 | Journal Entry Testing Memo | `je_testing_memo_generator.py` | Shared Template | P0 |
| 3 | AP Payment Testing Memo | `ap_testing_memo_generator.py` | Shared Template | P0 |
| 4 | Pre-Flight Data Quality Report | `preflight_memo_generator.py` | Custom Memo | P1 |
| 5 | Three-Way Match Memo | `three_way_match_memo_generator.py` | Custom Memo | P1 |
| 6 | Multi-Period Comparison Memo | `multi_period_memo_generator.py` | Custom Memo | P1 |
| 7 | Bank Reconciliation Memo | `bank_reconciliation_memo_generator.py` | Custom Memo | P1 |
| 8 | Anomaly Summary Report | `anomaly_summary_generator.py` | Engagement Memo | P2 |
| 9 | Revenue Testing Memo | `revenue_testing_memo_generator.py` | Shared Template | P2 |
| 10 | Statistical Sampling Memo | `sampling_memo_generator.py` | Custom Memo | P2 |

---

## 2. Acceptance Checklist

Each pilot report must pass **all** checks before rollout approval.

### Structural Checks
- [ ] Valid PDF header (`%PDF-`) and trailer (`%%EOF`)
- [ ] Multi-page output (cover page + content pages)
- [ ] Cover page includes: title, client name, period, source document, reference, timestamp
- [ ] Cover page ends with page break (content starts on page 2)
- [ ] Gold double rule on cover page
- [ ] Page footer on every page: classical page number (`— N —`) + disclaimer line

### Content Standards (Sprint 0-7)
- [ ] Section headings use title case (no ALL-CAPS, no letter-spaced caps)
- [ ] Section numbering uses Roman numerals (I. Scope, II. Methodology, etc.)
- [ ] Scope section present with leader-dots data summary
- [ ] Methodology section present with test table (for testing tools)
- [ ] Results summary section present (for testing tools)
- [ ] Disclaimer section present with non-attestation language
- [ ] Intelligence stamp present (Paciolus watermark)
- [ ] No banned assertive phrases (proves, confirms, establishes, etc.)

### Framework & Citations (Sprint 3)
- [ ] Framework-aware scope statement included (FASB or GASB)
- [ ] Framework-aware methodology statement included
- [ ] Authoritative reference block with citation table (for testing tools)

### Source Document Transparency (Sprint 6)
- [ ] Source document title shown when provided
- [ ] Source file (filename) shown separately when title is present
- [ ] Source context note shown when provided

### Signoff Deprecation (Sprint 7)
- [ ] Workpaper signoff section NOT rendered by default
- [ ] Opt-in (`include_signoff=True`) produces signoff section when names provided

---

## 3. Rollback Procedure

### Trigger Conditions
Rollback if **any** of:
- CI report-standards job fails on main branch after merge
- Pilot report renders incorrectly (missing sections, visual defects)
- User reports broken PDF export

### Rollback Steps

1. **Identify the breaking commit:**
   ```bash
   git log --oneline -10
   ```

2. **Revert the commit:**
   ```bash
   git revert <commit-sha> --no-edit
   ```

3. **Verify the revert:**
   ```bash
   cd backend && pytest tests/test_report_regression.py tests/test_report_structural_snapshots.py -v
   cd ../frontend && npm run build
   ```

4. **Push the revert:**
   ```bash
   git push origin main
   ```

5. **Post-mortem:**
   - Add failing scenario to regression test suite
   - Document in `tasks/lessons.md`
   - Re-attempt fix in a new branch

### No-Rollback Safe Zone
These changes are safe and should NOT be rolled back:
- CI job additions (report-standards, lint-baseline-gate)
- New test files (additive, cannot break existing behavior)
- Runbook / documentation files

---

## 4. Owner Signoff Workflow

### Roles
| Role | Responsibility |
|------|---------------|
| **Engineer** | Implements Sprint 8 deliverables, runs test suite |
| **CEO** | Reviews pilot report samples, approves rollout |

### Signoff Process

1. **Engineer generates pilot samples:**
   - Run `python backend/generate_sample_reports.py` (if available)
   - Or trigger exports via the UI for each pilot report type
   - Save PDFs to `sample-reports/` for review

2. **CEO reviews each pilot report against the acceptance checklist:**
   - Open each PDF in a viewer
   - Verify visual quality and section presence
   - Mark each checklist item as pass/fail

3. **Decision gate:**
   - **All pass:** CEO signs off, engineer merges to main
   - **Any fail:** Engineer fixes, re-generates, returns to step 2

4. **Post-rollout verification:**
   - CI runs `report-standards` job on every push/PR
   - Regression tests run in `backend-tests` job
   - Any new violation fails the build

### Signoff Record

```
Pilot Reviewed: [date]
Reviewed By: [CEO name]
Reports Checked: [count]/10
Decision: [APPROVED / NEEDS REVISION]
Notes: [any observations]
```

---

## 5. CI Integration

The following CI jobs enforce reporting invariants automatically:

| Job | What It Enforces | Blocking? |
|-----|-----------------|-----------|
| `backend-tests` | All pytest tests including `test_report_regression.py` and `test_report_structural_snapshots.py` | Yes |
| `report-standards` | Policy validation script (`validate_report_standards.py`) — banned language, spaced caps, shared chrome usage, citation metadata | Yes |
| `accounting-policy` | Accounting control invariants (monetary precision, soft delete, etc.) | Yes |

### Adding New Report Standards

When a new reporting standard is adopted:
1. Add the check to `backend/scripts/validate_report_standards.py`
2. Add corresponding test cases to `backend/tests/test_report_regression.py`
3. Update this runbook's acceptance checklist
4. The CI gate automatically enforces the new standard
