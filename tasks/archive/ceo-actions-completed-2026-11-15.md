# CEO actions — completed and decided sections

Moved verbatim out of `tasks/ceo-actions.md` on 2026-11-15.

## 🧭 Methodology calls — DECIDED 2026-10-24

You approved every recommendation in the decision doc (https://claude.ai/artifact/9zuEgMNHBTstNTJSxHcGeQ), with the instruction to be as conservative as possible and to document every source. Implementation: Sprint 831 (calls 2–4 below), Sprint 832 (call 1), Sprint 825 (sampling), Sprint 826 (W-2), Sprint 833 (SoD, bank-rec), Sprint 790 (upload counter), Sprint 834 (storage wording), Sprint 835 (sources page). The original text of the four calls is kept below for the record.

**Still yours:** see "Claims review" below — counsel now reviews the finished legal pages at website-final, and the wrong storage sentences are fixed in Sprints 841/844 without waiting.

### Original calls (2026-10-23, Sprint 829)

Discovery round 2 found these. They are judgement calls about what a tool *should* conclude, so they are not bugs I can just fix. Each one has a recommendation. Reply with yes, no, or something else.

1. **Equity in the ratios for a TB that has not been closed.** ROE, debt-to-equity, the equity ratio and the DuPont equity multiplier all use equity *without* the current year's earnings. On the discovery TB, D/E reads 0.56 against a true 0.48, and ROE reads 16.5% against 14.1%. The accounting-equation check was fixed in Sprint 829. The ratios were not, because `CategoryTotals` is also a public API input. **Recommend:** derive equity including current-period earnings inside the ratio engine.
2. **The JE composite averages flag rates and ignores flag severity.** One $250K out-of-balance entry used to rate LOW. Sprint 829 added a floor for unbalanced entries only. Two other effects remain: 482 HIGH flags still rate LOW, and a Benford failure that flags no entries lowers the score. **Recommend:** a scoring sprint that weights flagged-row severity.
3. **Holiday postings.** The calendar is the full US federal list, so Columbus Day and Veterans Day postings are flagged even though most businesses are open on those days. **Recommend:** drop both from the JE-19 list.
4. **Month-end clustering.** A normal close, with about 13% of entries in the last 3 days, flagged 7 of 12 months. **Recommend:** raise the threshold, or compare each month with the client's own months instead of a fixed share.

The earlier open calls are still listed in `tasks/todo.md`: Sprint 790 (upload counter), Sprint 825 (sampling S3/S6), Sprint 826 W1/W2, Sprint 818 item 3, and SoD single-HIGH tiering.

---

## Phase 1 — Restore Login ✅ DONE 2026-04-09

Render Standard deploy live. Neon (us-east-1 pooled) + Upstash Redis + Sentry wired. SendGrid Domain Authentication for `paciolus.com` verified after an initial DMARC bounce on the `@gmail.com` sender — DNS records (SPF/DKIM/DMARC) added to Vercel, propagated in under 2 minutes, and verified by SendGrid. Email verification flow confirmed end-to-end in Gmail inbox. Smoke test green (health, CSRF, register with HttpOnly cookies, /auth/me, wrong-password, logout). First user landed in the fresh Neon DB.

**Full detail, operational learnings, and exact commands archived in [`tasks/archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md`](archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md).**

### Phase 1 open follow-ups

- [x] **DMARC tightened to `p=quarantine` 2026-04-24.** `_dmarc.paciolus.com` updated in Vercel DNS; verified propagated on both Google (8.8.8.8) and Cloudflare (1.1.1.1) resolvers within seconds (TTL 60). Next step: ~30 days of observation; if no deliverability complaints, escalate to `p=reject` around 2026-05-24. Optional: add `rua=mailto:dmarc@paciolus.com` once a reporting mailbox exists.

> Other Phase 1 follow-ups (DB_TLS_OVERRIDE removal, Sentry verification, SendGrid Single Sender cleanup, orphan Render Postgres deletion, Neon password rotation) all landed 2026-04-22/23 — see the Completed table below.

---

## Phase 2 — Code Backlog Merge Train ✅ DONE 2026-04-09

PR #67 merged as one consolidated batch (merge commit `84fbc90`) rather than 5 smaller PRs — the infra outage meant we couldn't deploy + smoke test between batches, so bisect-granularity via individual commits in `main` history is the fallback if a regression shows up later. Scope: 45 commits total spanning Sprints 570–593 plus ~25 hotfixes plus 5 pre-flight fix commits (migration collision, alembic multi-head merge, smoke test script, CI gate resolution, ceo-actions.md rewrite). All 21 CI checks green before merge.

**Full detail archived alongside Phase 1 in [`tasks/archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md`](archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md).**

---

## Completed

> One-line milestone record. Full Phase 1 & 2 detail lives in [`tasks/archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md`](archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md).

| Date | Milestone |
|---|---|
| 2026-04-24 | **Branch protection on `main` applied** (Phase 5) — `gh api` PUT with 12 required status checks (matched to actual job display names), required Code Owner review, linear history, force-push + deletion blocked, conversation resolution required, admin break-glass preserved (`enforce_admins: false`). Closed the gap where commit-msg hook + CODEOWNERS were both advisory at the remote |
| 2026-04-24 | **DMARC tightened to `p=quarantine`** — `_dmarc.paciolus.com` TXT record updated in Vercel DNS (TTL 60); propagation verified on Google + Cloudflare resolvers within seconds; 30-day observation window then escalate to `p=reject` |
| 2026-04-24 | **Sprint 716 complete** — Grafana Loki log aggregation (in-process handler) deployed to production; 40 ingested lines verified in Logs Explorer with correct labels; 6 saved queries authored; runbook `docs/runbooks/observability-loki.md` §4 LogQL corrected for actual ingest-layer indexing |
| 2026-04-23 | **R2 buckets provisioned + Sprint 611 ExportShare migration landed** — `paciolus-backups` and `paciolus-exports` on Cloudflare R2 (ENAM, private, per-bucket scoped tokens); 8 env vars wired to Render (19→27 vars, zero downtime across 9× /health 200 polls); Sprint 611 route now writes share bytes to `paciolus-exports` keyed by `shares/<share_token_hash>` |
| 2026-04-23 | **`DB_TLS_OVERRIDE` cleared** (Sprint 673) — pooler-aware `pg_stat_ssl` skip shipped 2026-04-22; CEO env-var delete 10:26 UTC went live 10:28 UTC; post-deploy logs show `tls=pooler-skip` with zero override warnings; 2026-05-09 fuse cleared |
| 2026-04-22 | **Neon password rotation** — `neondb_owner` rotated after plaintext DATABASE_URL rendered in a screenshot tool result during orphan-DB investigation; Render env var updated, deploy `937997a` green, paciolus.com login smoke-tested clean. Side effect: this redeploy also shipped PR #93 (Sprints 703–709 typography + design refresh) to prod for the first time |
| 2026-04-22 | **Orphan Render Postgres `paciolus-db` deleted** — was a Basic-1gb paid plan (~$7-19/mo) holding 85 MB of orphaned pre-Neon data, 0 open connections; verified `paciolus-api` DATABASE_URL points to Neon before deletion |
| 2026-04-22 | **SendGrid Single Sender Verification revoked** for `comcgee89@gmail.com` — Domain Authentication on `paciolus.com` is now the sole sending path |
| 2026-04-22 | **Sentry integration verified via live traffic** — 9+ unresolved prod issues already in dashboard (`cleanup_scheduler`, `/auth/verification-status`, `/audit/trial-balance`, `/audit/preflight`); no deliberate test event needed. Bonus: surfaced two P1 bugs (~670 events combined) captured as Sprint 711 |
| 2026-04-09 | **Phase 1 complete** — Render Standard deploy, full env-var set, smoke test green, email delivery verified end-to-end via SendGrid Domain Authentication on paciolus.com, first Neon user landed |
| 2026-04-09 | **Phase 2 complete** — PR #67 merged (45 commits, Sprints 570–593 + hotfixes + 5 pre-flight fixes), all 21 CI checks green, merge commit `84fbc90` |
| 2026-04-09 | SendGrid Domain Authentication for `paciolus.com` verified — 4 DNS records added to Vercel (em8369 CNAME, s1/s2 DKIM CNAMEs, _dmarc TXT with `p=none`), propagated in under 2 min, SendGrid verify succeeded on first click |
| 2026-04-09 | CI gate resolution on PR #67 — ruff auto-fix, OpenAPI snapshot regen, Jest coverage threshold recalibration, 4 ESLint errors resolved (commits `c275edd` + `c015bf8`) |
| 2026-04-09 | Alembic migration collision + multi-head merge fixes committed to working branch (commits `4c25ac2` + `e8c289e`) |
| 2026-04-09 | `DB_TLS_OVERRIDE=NEON-POOLER-PGSSL-BLINDSPOT:2026-05-09` set — temporary bypass for Neon pooled endpoint's `pg_stat_ssl` blind spot (proper fix tracked as open follow-up) |
| 2026-04-08 | Post-deploy smoke test script `scripts/smoke_test_render.sh` added (commit `0f83273`) |
| 2026-04-08 | Branch audit baseline captured: 1,751 frontend tests + 7,361 backend tests, 0 failures |
| 2026-04-08 | Launch infrastructure plan original draft — this document's phase-based rewrite |
| 2026-03-23 | Infrastructure decisions recorded: Grafana Loki (SIEM), pgBackRest→S3 (DR), AWS Secrets Manager (secrets backup) |
| 2026-03-23 | CODEOWNERS updated to `@Paciolus` (was `@paciolus/security-leads`) |

---

*Last revised: 2026-04-24. Stale action-map dates replaced with a compact "Remaining launch path" block. Phase 1 follow-ups collapsed to DMARC only (other five landed 2026-04-22/23 and are recorded in the Completed table). R2 Backlog Blocker collapsed to a resolved summary — only Phase 4.4 pg_dump remains as a consumer.*
