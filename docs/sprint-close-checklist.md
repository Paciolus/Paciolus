# Sprint Close Checklist — Paciolus

Run this checklist before marking any sprint complete.
A sprint is not done until every box is checked.

---

## 1. Code Quality

- [ ] All new functions have at least one test
- [ ] `npm run test` (or `pytest`) passes with no failures
- [ ] No console.log or debug print statements left in production code
- [ ] No hardcoded values that should be configurable
- [ ] `DEPLOY-VERIFY-[sprint#]` log line added to the primary changed function

---

## 2. Git — The Critical Section

- [ ] All changes staged and committed (`git status` shows clean working tree)
- [ ] Commit message references sprint number: `Sprint [N]: [description]`
- [ ] **`git push origin <branch>` has been run** — this is the step that killed Sprint 530
- [ ] Push confirmed: run `npm run sprint:verify` or `sh scripts/sprint_verify.sh` — output shows clean
- [ ] If on a feature branch: PR/merge to main initiated

---

## 3. Deploy Verification

- [ ] Render (or deployment platform) shows a new build triggered after the push
- [ ] Build status reaches **Live** — not just "Building" or "Queued"
- [ ] Run a test analysis and search logs for `DEPLOY-VERIFY-[sprint#]`
- [ ] Log marker confirmed — if it does not appear, the new code is not executing

---

## 4. Functional Verification

- [ ] Run `paciolus_test_tb_fy2025.csv` (Meridian — software company)
- [ ] Run `paciolus_test_tb_cascade_fy2025.csv` (Cascade — manufacturing)
- [ ] Acceptance criteria from the sprint's implementation prompt verified
- [ ] No regressions in previously passing items

---

## 5. Documentation

- [ ] Sprint number and summary logged
- [ ] Any issues discovered during this sprint added to the backlog
- [ ] Items resolved vs. deferred noted

---

## Sprint Sign-Off

Sprint #:       ___
Completed:      ___
Pushed at:      ___  (commit hash: _________)
Deploy live at: ___
Verified by:    ___ (log marker / functional test)
Deferred to:    ___ (next sprint, if anything carried over)

---

*A sprint that hasn't been pushed is a sprint that doesn't exist in production.*
