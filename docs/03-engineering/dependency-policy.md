# Dependency Policy

**Sprint:** 731

This policy governs how Paciolus dependencies are kept current. The intent is
to land security-relevant updates inside a fixed window without making major
upgrades feel rushed.

## 1. Cadence

| Update class | Window | Examples |
|---|---|---|
| Security patch | **7 days** from CVE publish or sentinel detection | `cryptography` CVE bumps, FastAPI `0.136.0 → 0.136.1` security note |
| Security-relevant minor | **14 days** | `stripe 15.0.1 → 15.1.0` (transitive security fix in stripe-python's pinned cryptography) |
| Routine patch | next dep-hygiene hotfix (typically weekly cadence) | `mypy 1.20.1 → 1.20.2` |
| Routine minor | scheduled dep-hygiene sprint | `pandas 3.0.2 → 3.0.3` |
| Major upgrade | scheduled, no deadline pressure | `pandas 2.x → 3.x`, `pydantic 1.x → 2.x` |

"Security-relevant" means tagged with a CVE, marked as a security patch in the
release notes, or flagged by `pip-audit` / `npm audit` / Dependency Sentinel
with a non-info severity.

## 2. Detection sources

The primary signal is the nightly **Dependency Sentinel**
(`scripts/overnight/agents/dependency_sentinel.py`) which runs `pip list
--outdated` against the pinned `requirements.txt`. Secondary signals:

- `pip-audit` and `npm audit` blocking jobs in CI (`.github/workflows/ci.yml`)
- Sentry-reported runtime errors that match a known dep CVE
- Manual reports (CEO, security researcher, GitHub advisory)

Each source produces an entry in the daily nightly report; Dependency Sentinel
aggregates and highlights past-deadline items.

## 3. Sentinel deadline gate (Sprint 731)

Past the cadence window, Dependency Sentinel flips from YELLOW (informational)
to RED (CI-blocking) for the affected dep. The mechanism:

1. The first nightly run that detects an outdated security-relevant dep stamps
   a `first_seen_at` timestamp in `reports/nightly/.baseline.json`.
2. Each subsequent run compares `now - first_seen_at` against the cadence
   window for that update class.
3. If the deadline is exceeded and the dep hasn't been bumped, Sentinel emits
   `status="red"` and the nightly job exits non-zero. CI breaks until the
   bump lands.

This converts "FYI" into "act" without making the engineer chase down arbitrary
deadlines manually.

## 4. Auto-PR (Dependabot)

`.github/dependabot.yml` (configured pre-Sprint-731 as Sprint T1, kept) opens
PRs weekly for:

- `pip` — backend Python deps (Mondays, with `deps(pip):` commit prefix)
- `npm` — frontend JS deps (Mondays, with `deps(npm):` commit prefix)
- `github-actions` — CI workflow pins (Mondays, with `deps(actions):` prefix)

Patch + minor updates are grouped into one PR per ecosystem to reduce review
overhead; security alerts override the weekly schedule (Dependabot opens those
immediately regardless of day/time settings). Major-version bumps still
require manual sprint-scheduled work.

The engineer's role is review-and-merge, not authoring. Past-deadline security
PRs that haven't been reviewed within the cadence window (§1) will trip the
Sentinel deadline gate (§3).

## 5. What NOT to deferred

These are explicit anti-patterns:

- **"It's working in prod, why upgrade?"** — works only until the next CVE
  drops. Routine patch upgrades buy fluency in the upgrade machinery so the
  emergency upgrade isn't the first one we've ever done.
- **"Wait for the .x.0 to mature."** — applies to majors (`pandas 3.0.0`),
  not patches. Patch versions are released *because* they fix bugs; soaking
  defeats the point.
- **"Skip it; the test suite isn't comprehensive enough to verify."** — the
  fix is to expand the test suite (Sprint 723's coverage floors), not to
  freeze the dep tree.

## 6. Calendar-versioned packages

Packages on calendar versioning (e.g., `pdfminer.six 20221105`,
`tzdata 2026.1`) get a default **30-day soak** before the bump lands. The
calendar version usually means "this is when the upstream data was last
refreshed" rather than "this is a security patch," so the deadline pressure
is lower.

Override the soak only when:
- Tzdata has a DST rule change affecting a region we serve.
- The package is referenced in a security advisory.

## 7. Sprint-close hook

Every sprint commit is expected to leave the dependency tree in a "no
past-deadline items" state. The post-Sprint hook reads the latest Sentinel
JSON and warns if a non-blocking patch landed alongside a sprint that hasn't
addressed an open past-deadline item. Soft warning, not blocking — the
intent is awareness, not friction.

## 8. Related

- `scripts/overnight/agents/dependency_sentinel.py` — the detection script.
- `.github/dependabot.yml` — auto-PR config (Sprint 731).
- `docs/compliance/DEPENDENCY_DECISIONS.md` — decisions on individual deps
  (e.g., why slowapi is pinned at 0.1.9, why redis is optional).
- Sprint 731 entry in `tasks/archive/sprints-*.md` — the policy's first
  execution (fastapi 0.136.0 → 0.136.1, stripe 15.0.1 → 15.1.0).
