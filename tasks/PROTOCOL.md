# Sprint Protocol & Lifecycle Rules

> Extracted from `tasks/todo.md`. This is the operating procedure reference.
> Agents should rarely need to read this during normal sessions.

---

## Phase Lifecycle Protocol

**MANDATORY:** Follow this lifecycle for every phase. This eliminates manual archive requests.

### During a Phase
- Active phase details (audit findings, sprint checklists, reviews) live in `tasks/todo.md` under `## Active Phase`
- Each sprint gets a checklist section with tasks, status, and review

### On Phase Completion (Wrap Sprint)
1. **Regression:** `pytest` + `npm run build` + `npm test` must pass
2. **Archive:** Move all sprint checklists/reviews to `tasks/archive/phase-<name>-details.md`
3. **Summarize:** Add a one-line summary to `tasks/COMPLETED_ERAS.md` (with test count if changed)
4. **Clean todo.md:** Delete the entire `## Active Phase` section content, leaving only the header ready for the next phase
5. **Update CLAUDE.md:** Add phase to completed list, update test count + current phase
6. **Update SESSION_STATE.md:** Update project status
7. **Commit:** `Sprint X: Phase Y wrap — regression verified, documentation archived`

**The `## Active Phase` section should ONLY contain the current in-progress phase. Once complete, it becomes empty until the next phase begins.**

**Archival threshold:** If the Active Phase accumulates 5+ completed sprints without a named phase wrap, archive them immediately as a standalone batch to `tasks/archive/`. Do not wait for a phase boundary.

---

## Post-Sprint Checklist

**MANDATORY:** Complete after EVERY sprint.

- [ ] `npm run build` passes
- [ ] `npm test` passes (frontend Jest suite)
- [ ] `pytest` passes (if tests modified)
- [ ] Zero-Storage compliance verified (if new data handling)
- [ ] Sprint status → COMPLETE, Review section added
- [ ] Lessons added to `lessons.md` (if corrections occurred)
- [ ] **If sprint produced CEO actions:** add them to [`tasks/ceo-actions.md`](ceo-actions.md)
- [ ] `git add <files> && git commit -m "Sprint X: Description"`
- [ ] Record commit SHA in sprint Review section (e.g., `Commit: abc1234`)
- [ ] Verify Active Phase has fewer than 5 completed sprints (the commit-msg hook blocks at 5+; run `sh scripts/archive_sprints.sh` if threshold exceeded)

---

## Sprint vs. Hotfix Classification

- **Sprint:** New features, architectural changes, report enrichments, bug fix batches, test additions
- **Hotfix:** Copy corrections, test count updates, typo fixes, dependency bumps with no code changes
- Hotfixes: add one-line entry to `## Hotfixes` in `tasks/todo.md`, commit with `fix:` prefix. No sprint number needed.

---

## Commit-Msg Hook Enforcement

The `frontend/.husky/commit-msg` hook enforces two gates on `Sprint N:` commits:
1. **Todo gate:** Rejects unless `tasks/todo.md` is staged.
2. **Archival gate:** Rejects if Active Phase has 5+ completed sprints. Run `sh scripts/archive_sprints.sh` to clear.

Both are mechanically enforced — not discipline-dependent. Hotfix commits (`fix:` prefix) are exempt.
