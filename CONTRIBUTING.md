# Contributing to Paciolus

## Pull Request Process

Every PR to `main` must complete the **Security & Compliance Checklist** embedded in the PR template (`.github/pull_request_template.md`).

GitHub populates this template automatically when you open a new pull request. All ten checklist items must be checked (or explicitly marked N/A with justification) before the PR is eligible for review.

The checklist enforces **CC8.4** of the SOC 2 Trust Services Criteria and mirrors the code review requirements in `docs/04-compliance/SECURE_SDL_CHANGE_MANAGEMENT.md §3.2`.

## CI Gates

All PRs must pass the following CI checks before merging. The authoritative source is `.github/workflows/ci.yml`.

| Job | Requirement |
|-----|-------------|
| `backend-tests` | All pytest tests pass (Python 3.11 + 3.12 matrix, `-m "not slow"`) |
| `backend-tests-postgres` | All pytest tests pass against PostgreSQL 15 |
| `frontend-build` | `npm run build` succeeds, ESLint error/warning counts extracted |
| `frontend-tests` | All Jest tests pass with coverage |
| `backend-lint` | Ruff error count extracted for baseline gate |
| `lint-baseline-gate` | Ruff + ESLint errors/warnings ≤ `.github/lint-baseline.json` |
| `mypy-check` | mypy passes on non-test backend source (zero errors) |
| `bandit` | No HIGH-severity security findings (medium+ scanned) |
| `secrets-scan` | trufflehog finds no committed secrets (PR diff or push) |
| `openapi-drift-check` | OpenAPI snapshot matches current Pydantic models |
| `accounting-policy` | Accounting invariant checkers pass |
| `report-standards` | Report standards validator passes |
| `pip-audit-blocking` | No HIGH/CRITICAL Python CVEs |
| `npm-audit-blocking` | No HIGH/CRITICAL Node CVEs |

**Advisory (non-blocking):** `pip-audit-advisory`, `npm-audit-advisory`, `merge-revert-guard`, `backend-tests-slow` (main-only).

**E2E smoke tests:** Run on push to main and PRs targeting main. Requires `SMOKE_USER` and `SMOKE_PASS` repository secrets. When secrets are unavailable (external PRs), the job skips gracefully with a notice.

## Commit Messages

Use the format: `Sprint N: Brief description of change`

Example: `Sprint 449: Add PR security checklist template`

## 4. GPG Commit Signing

All commits to `main` must be GPG-signed (CC8.6). This allows auditors to cryptographically verify that every change came from an authorised team member.

**Before your first signed commit:**

### macOS

```bash
# Install GPG and pinentry
brew install gnupg pinentry-mac

# Fix pinentry so macOS keychain can store the passphrase
mkdir -p ~/.gnupg
echo "pinentry-program $(brew --prefix)/bin/pinentry-mac" >> ~/.gnupg/gpg-agent.conf
chmod 700 ~/.gnupg
gpgconf --kill gpg-agent

# Generate a 4096-bit RSA key (never expiring — you'll rotate annually)
gpg --full-generate-key
# ➜ Choose: (1) RSA and RSA
# ➜ Keysize: 4096
# ➜ Expiration: 0 (never)
# ➜ Real name: Your Name
# ➜ Email: must match your GitHub verified email and git config user.email
# ➜ Comment: (blank)
# ➜ Enter a strong passphrase (store in your password manager)
```

### Linux (Debian/Ubuntu)

```bash
sudo apt update && sudo apt install gnupg

gpg --full-generate-key
# Same choices as above
```

### Windows

1. Download and install **Gpg4win** from https://gpg4win.org
2. Open **Kleopatra** (included with Gpg4win)
3. File → New Key Pair → Create a personal OpenPGP key pair
4. Use your GitHub-verified email, 4096-bit RSA, no expiry
5. Set a strong passphrase

Then add to your git config (Git Bash):
```bash
git config --global gpg.program "C:/Program Files (x86)/GnuPG/bin/gpg.exe"
```

---

### Configure git to sign all commits

```bash
# Get your key ID (16-char hex after "rsa4096/")
gpg --list-secret-keys --keyid-format=long
# Example output:
#   sec   rsa4096/AABBCCDD11223344 2026-02-27 [SC]
#   uid   [ultimate] Your Name <you@paciolus.com>

# Set git to use your key
git config --global user.signingkey AABBCCDD11223344
git config --global commit.gpgsign true
```

---

### Register your key with GitHub

```bash
# Export your public key
gpg --armor --export AABBCCDD11223344
# Copy the entire output (from -----BEGIN PGP PUBLIC KEY BLOCK-----
# through -----END PGP PUBLIC KEY BLOCK-----)
```

1. GitHub → Settings → SSH and GPG keys → **New GPG key**
2. Paste the output above
3. Click **Add GPG key**

---

### Verify your first signed commit

```bash
git commit -m "test: verify GPG signing works"
git log --show-signature -1
# Expected: "gpg: Good signature from 'Your Name <you@paciolus.com>'"
```

On GitHub, the commit should show a green **Verified** badge.

---

### Add yourself to the key registry

Open `docs/08-internal/gpg-key-registry.md` and add a row to the **Registered Keys** table with your name, GitHub username, key ID, and full fingerprint:

```bash
# Get your full fingerprint
gpg --fingerprint AABBCCDD11223344
# Example: 1234 5678 90AB CDEF 1234  5678 90AB CDEF AABB CCDD
# Store without spaces: 1234567890ABCDEF12345678...
```

Open a PR with the registry update. Use your freshly-signed commit.

---

### Annual key rotation

Rotate your key annually (or immediately if your device is lost or the key is compromised). Full procedure in `docs/08-internal/gpg-key-registry.md`.

---

## Branch Protection

The `main` branch requires all CI status checks to pass and branches to be up to date before merging.

Once all committers have registered their GPG keys, **"Require signed commits"** will be enabled on `main`. Unsigned commits will be rejected by GitHub.


---

## Database Migrations (Sprint 737)

Alembic is the **single authority** for schema evolution. Sprint 737
removed the in-process `init_db()` schema-patch fallback that previously
auto-healed missing columns. Production deploys still run
`alembic upgrade head` via the Dockerfile `CMD` before gunicorn starts,
but local development now requires the migration step explicitly.

**After pulling changes:** if you have a local SQLite file (e.g.,
`backend/dev.db`), run:

```bash
cd backend
python -m alembic upgrade head
```

If you skip this, your local database may lack columns that newer code
expects, producing confusing "no such column" errors at request time.

**When adding a new column to a model:**

1. Add the column to the SQLAlchemy model.
2. Generate a migration: `python -m alembic revision --autogenerate -m "<description>"`.
3. Read the generated migration carefully — autogenerate is a hint, not
   a guarantee, and SQLite's `render_as_batch=True` mode generates
   different DDL than vanilla Postgres `ALTER TABLE`.
4. Run `python -m alembic upgrade head` to apply it locally.
5. The CI test `tests/test_alembic_models_parity.py` will fail if you
   skip step 2 — it asserts that `alembic upgrade head` produces the
   same schema as `Base.metadata.create_all()`.

**Drift exceptions:** A small number of tables and columns are
documented as pre-existing drift (model exists, no migration). See
`PRE_EXISTING_DRIFT_TABLES` and `PRE_EXISTING_DRIFT_COLUMNS` in
`backend/tests/test_alembic_models_parity.py`. Sprint 738 will close
these out; new drift should be fixed at write time, not added to the
allow-list.

---

## Anomaly-Framework Generator ↔ Engine Contracts (Sprint 700)

The testing-tool anomaly framework (`backend/tests/anomaly_framework/`)
couples each **generator** (which mutates clean fixture data to exercise
a specific detection path) with an **engine** (JE / AP / Payroll /
Revenue / AR / FA / Inventory / Sampling / Multi-Currency / Three-Way
Match / Multi-Period / Bank-Rec). When the two drift — the generator
emits data the engine doesn't inspect, or targets a `test_key` the
engine doesn't emit — the only signal is a failing assertion, which
historically got a silent `xfail` marker instead of a fix.

The **contract layer** (`backend/shared/engine_contract.py`) makes the
coupling explicit. Before adding a new generator or engine detection
path:

1. **Engine side** — append an `ENGINE_CONTRACT = EngineInputContract(...)`
   at the end of the engine module. Declare the columns the engine
   reads and a `DetectionPreconditions` entry for each `test_key` the
   engine's `TestResult` emits.
2. **Generator side** — set `PRODUCES_EVIDENCE = GeneratorEvidence(...)`
   on the generator class. Declare the columns the generator populates
   and (for pattern-based detections) the account-name values it emits.
3. **Verify** — the meta-test
   `tests/anomaly_framework/test_contract_compliance.py` runs in strict
   mode and will fail the build if a generator's evidence doesn't
   satisfy its target engine's precondition. Run it locally with:
   ```
   pytest tests/anomaly_framework/test_contract_compliance.py -v
   ```

**Common violations and what they mean:**

| Violation field | What failed |
|-----------------|-------------|
| `missing_columns` | Generator doesn't populate a column the engine reads |
| `missing_account_name_patterns` | Generator doesn't emit an account name matching the engine's pattern list |
| `scope_mismatch` | Generator writes to sub-ledger but engine reads TB (or vice versa) |
| `no contract entry for test_key` | Generator targets a test the engine doesn't declare |

**Precedent for fix direction:**

When generator and engine disagree, prefer fixing the side that's WRONG
about real auditor workflow, not whichever is easier. Examples from
Sprint 701/702:

* Revenue contra: engine's 15% threshold matched real auditor
  practice; generator was under-injecting. Fix: larger injection.
* Payroll duplicate names: generator targeted the wrong test_key;
  engine had no same-name-different-ID test at all. Fix: add
  engine-side test PR-T12 (ghost-employee scheme).
* AR sign: generator mutated sub-ledger but engine checked TB. Fix:
  split engine into AR-01 (TB) and AR-01b (SL) — two distinct
  assertions per AICPA Audit Guide §5.11.
* FA / INV duplicates: engine dedups on (cost, description, date);
  generator mutated description. Fix: keep description identical,
  vary asset_id/item_id (the real "double-booked" pattern).

