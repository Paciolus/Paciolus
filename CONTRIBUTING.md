# Contributing to Paciolus

## Pull Request Process

Every PR to `main` must complete the **Security & Compliance Checklist** embedded in the PR template (`.github/pull_request_template.md`).

GitHub populates this template automatically when you open a new pull request. All eight checklist items must be checked (or explicitly marked N/A with justification) before the PR is eligible for review.

The checklist enforces **CC8.4** of the SOC 2 Trust Services Criteria and mirrors the code review requirements in `docs/04-compliance/SECURE_SDL_CHANGE_MANAGEMENT.md §3.2`.

## CI Gates

All PRs must pass the following CI checks before merging:

| Job | Requirement |
|-----|-------------|
| `backend-tests` | All pytest tests pass (Python 3.11 + 3.12) |
| `frontend-build` | `npm run build` succeeds with no errors |
| `backend-lint` | Ruff error count ≤ baseline |
| `lint-baseline-gate` | ESLint errors + warnings ≤ baseline |
| `bandit` | No HIGH-severity security findings |
| `accounting-policy` | Accounting invariant checkers pass |
| `report-standards` | Report standards validator passes |
| `pip-audit-blocking` | No HIGH/CRITICAL Python CVEs |
| `npm-audit-blocking` | No HIGH/CRITICAL Node CVEs |

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
