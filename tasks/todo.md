# Paciolus Development Roadmap

> **Protocol:** See [`tasks/PROTOCOL.md`](PROTOCOL.md) for lifecycle rules, post-sprint checklist, and archival thresholds.
>
> **Completed eras:** See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for all historical phase summaries.
>
> **Executive blockers:** See [`tasks/EXECUTIVE_BLOCKERS.md`](EXECUTIVE_BLOCKERS.md) for CEO/legal/security pending decisions.
>
> **CEO actions:** All pending items requiring your direct action are tracked in [`tasks/ceo-actions.md`](ceo-actions.md).

---

## Hotfixes

> For non-sprint commits that fix accuracy, typos, or copy issues without
> new features or architectural changes. Each entry is one line.
> Format: `- [date] commit-sha: description (files touched)`

- [2026-03-07] fb8a1fa: accuracy remediation — test count, storage claims, performance copy (16 frontend files)
- [2026-02-28] e3d6c88: Sprint 481 — undocumented (retroactive entry per DEC F-019)

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Composite Risk Scoring | Requires ISA 315 inputs — auditor-input workflow needed | Phase XI |
| Management Letter Generator | **REJECTED** — ISA 265 boundary, auditor judgment | Phase X |
| Expense Allocation Testing | 2/5 market demand | Phase XII |
| Templates system | Needs user feedback | Phase XII |
| Related Party detection | Needs external APIs | Phase XII |
| Marketing pages SSG | **Not feasible** — CSP nonce (`await headers()` in root layout) forces dynamic rendering; Vercel edge caching provides near-static perf | Phase XXVII |
| Test file mypy — full cleanup | 804 errors across 135 files (expanded from 68); `python_version` updated to 3.12 in Sprint 543 | Sprint 475/543 |

---

## Active Phase
> Sprints 478–497 archived to `tasks/archive/sprints-478-497-details.md`.
> Sprints 499–515 archived to `tasks/archive/sprints-499-515-details.md`.
> Sprints 516–526 archived to `tasks/archive/sprints-516-526-details.md`.
> Sprints 517–531 archived to `tasks/archive/sprints-517-531-details.md`.
> Sprints 532–536 archived to `tasks/archive/sprints-532-536-details.md`.
> Sprints 537–541 archived to `tasks/archive/sprints-537-541-details.md`.
> Sprints 542–546 archived to `tasks/archive/sprints-542-546-details.md`.
> Sprints 547–551 archived to `tasks/archive/sprints-547-551-details.md`.

