# Paciolus — Agent Entry Point

## What This Repo Is

Paciolus is a 12-tool zero-storage AI audit intelligence SaaS for financial professionals. The backend is FastAPI/Python with PostgreSQL (SQLite for dev), ReportLab PDF generation, and pandas-based in-memory processing. The frontend is Next.js 16 / React 19 / TypeScript with Tailwind CSS 4 and the Oat & Obsidian design system.

## Startup Sequence (run at the beginning of every session)

1. Read `SESSION_STATE.md` — last session summary, current branch state, open blockers
2. Read `tasks/todo.md` (Active Phase section only) — current work queue
3. Read `features/status.json` — full feature inventory, what is built and what is not
4. Run smoke test: `cd backend && python -c "from main import app; print('Backend OK')"` and `cd frontend && npx next lint --quiet` to verify the environment compiles
5. Begin work on the highest-priority incomplete item

## Documentation Map

| Need | Go To |
|------|-------|
| Architecture & system design | `docs/02-technical/ARCHITECTURE.md` |
| API reference (generated) | `docs/02-technical/API_REFERENCE_GENERATED.md` |
| API reference (legacy, outdated) | `docs/02-technical/API_REFERENCE.md` |
| Deployment & infrastructure | `docs/02-technical/DEPLOYMENT_ARCHITECTURE.md` |
| Feature inventory & status | `features/status.json` |
| Active sprint / work queue | `tasks/todo.md` |
| Sprint protocol & lifecycle | `tasks/PROTOCOL.md` |
| CEO/legal pending decisions | `tasks/EXECUTIVE_BLOCKERS.md` |
| Completed phase history | `tasks/COMPLETED_ERAS.md` |
| Session progress memory | `SESSION_STATE.md` |
| Compliance documentation | `docs/04-compliance/README.md` |
| Report standards & memos | `backend/routes/export_memos.py` (18 memo endpoints) |
| Operational runbooks | `docs/runbooks/` |
| Historical / archived docs | `docs/archive/` |
| Full operator protocol | `CLAUDE.md` |
| Design system spec | `skills/theme-factory/themes/oat-and-obsidian.md` |

## End-of-Session Checklist

- [ ] All changes committed with a descriptive git message
- [ ] `SESSION_STATE.md` updated with: what was completed, current branch state, any open blockers, next priority
- [ ] `features/status.json` updated for any features verified complete
- [ ] Environment left in working state (smoke test passes)

## Key Constraints

- **Zero-storage:** uploaded financial data is never persisted — only aggregate metadata
- **JWT/bcrypt/HMAC auth** — do not modify auth primitives without reading `docs/04-compliance/`
- **All 21 audit reports must remain functional** — run report suite tests before committing report changes
- **Pricing tiers:** Free / Solo / Professional / Enterprise (not Team/Organization — those are retired)
- **Oat & Obsidian design mandate:** use `obsidian-*`, `oatmeal-*`, `clay-*`, `sage-*` tokens only — no generic Tailwind colors
- **Commit-msg hook:** `Sprint N:` commits require `tasks/todo.md` staged; hotfixes use `fix:` prefix
- **12 diagnostic tools:** TB Diagnostics, Multi-Period, JE Testing, AP Testing, Bank Rec, Payroll, Three-Way Match, Revenue, AR Aging, Fixed Assets, Inventory, Statistical Sampling
