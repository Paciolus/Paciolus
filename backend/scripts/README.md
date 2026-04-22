# Backend Scripts

Admin / one-shot utilities. All scripts read `DATABASE_URL` from the same
`.env` as the app and work on both SQLite (dev) and PostgreSQL (prod).

---

## `create_dev_user.py` — seed a pre-verified dev user

Creates (or updates) a pre-verified user so local + CI flows can skip the
email verification step.

### Usage

**Non-interactive (CI / scripted):**

```bash
DEV_USER_PASSWORD='MyStrongDevP@ss1' python scripts/create_dev_user.py
```

**Interactive (input is not echoed):**

```bash
python scripts/create_dev_user.py
# Prompt: Password: ********
# Prompt: Confirm:  ********
```

**Optional overrides:**

```bash
DEV_USER_EMAIL=alice@example.com \
DEV_USER_NAME='Alice' \
DEV_USER_TIER=PROFESSIONAL \
DEV_USER_PASSWORD='MyStrongDevP@ss1' \
  python scripts/create_dev_user.py
```

### Password policy

Passwords must meet the app's standard password-strength requirements:

- 10+ characters
- At least 3 of: uppercase, lowercase, digit, special character

The script enforces this before writing. It does **not** hardcode a default
(Sprint 696, 2026-04-20 — removed the `DevPass1!` default so a shared dev DB
can never accidentally ship with a known-password account).

### What the script does

1. Validates `DEV_USER_PASSWORD` (env or prompt) against the password policy.
2. If the user already exists → updates `is_verified=True` + `tier` to match
   requested values; password is left alone.
3. If new → creates the row with `email_verified_at = now()` and the
   requested tier (default `ENTERPRISE` for full tool access).

Prints the resulting user ID + email on success. Exits non-zero on any
validation failure.

---

## `invalidate_legacy_passcode_shares.py` — revoke pre-Sprint-696 SHA-256 passcode shares

Sprint 696 replaced the SHA-256 export-share passcode hash with bcrypt, and
Sprint 697 subsequently upgraded to Argon2id. Any `export_shares` row whose
`passcode_hash` is still a bare 64-char hex digest cannot be verified by the
new code — recipients see a 403 on every download attempt until TTL expiry.

### Usage

**Dry run (default):**

```bash
python scripts/invalidate_legacy_passcode_shares.py
# Prints share_ids + owner_user_ids; no writes.
```

**Apply (revoke the rows):**

```bash
python scripts/invalidate_legacy_passcode_shares.py --apply
# Prompts for [y/N] confirmation unless --yes is also passed.
```

**Non-interactive apply:**

```bash
python scripts/invalidate_legacy_passcode_shares.py --apply --yes --verbose
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success (any number of rows affected, including zero) |
| 1 | Precondition failure — could not import database module |
| 2 | User aborted the `--apply` confirmation prompt |

### When to run manually

Not normally necessary. The nightly retention cleanup (`retention_cleanup.py`)
calls `cleanup_legacy_passcode_shares` as part of the lifespan cycle, so
stragglers are handled automatically.

Run manually only when:
- You want a pre-flight count ahead of a deploy (dry-run).
- You need to revoke mid-deploy without waiting for the next scheduler tick.
- You want the `verbose` per-row output for a post-incident report.

---

## `set_superadmin.py` — mark a user as superadmin

Grants `is_superadmin = true` on a user record. Used for bootstrapping the
initial admin account. No changes 2026-04-20; see the file header for
current usage.

---

## `validate_report_standards.py` — lint report output

Validates that generated reports reference the expected ISA / PCAOB /
ASC / IFRS standards. CI-invoked; see the file header for invocation
and the docs under `docs/02-technical/` for the standards matrix.
