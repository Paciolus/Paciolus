# GPG Key Registry

**Version:** 1.0
**Document Classification:** Internal
**Owner:** CISO / CTO
**Effective Date:** 2026-02-27
**Last Updated:** 2026-02-27
**Controls:** CC8.6 — Change integrity / tamper evidence for commits

---

## Purpose

GPG commit signing provides cryptographic evidence that every commit to `main` was authored by a registered team member. This registry is the authoritative source of truth for all GPG keys authorised for commit signing in the Paciolus repository.

Without GPG signing, commit authorship relies solely on git's `user.email` configuration — which is trivially spoofed. Signed commits give SOC 2 auditors verifiable proof that changes were made by the people they claim.

**For developer setup instructions:** see [`CONTRIBUTING.md` — GPG Commit Signing](#) section.

---

## Activation Status

| Control | Status | Blocking Action |
|---------|--------|----------------|
| GPG key generation + git config | ⏳ Pending | CEO / committers must complete setup (CONTRIBUTING.md §4) |
| GitHub GPG key registration | ⏳ Pending | Upload public key to GitHub → Settings → SSH and GPG keys |
| Branch protection: "Require signed commits" | ⏳ Pending | Enable **after** all committers have registered keys |

**Important:** Enable "Require signed commits" only after ALL active committers have:
1. Generated their key
2. Configured `git config --global commit.gpgsign true`
3. Added their public key to GitHub
4. Verified at least one signed commit pushes successfully

Enabling the rule before that will block all pushes from unsigned contributors.

---

## Registered Keys

| Committer | GitHub Username | Key ID (short) | Full Fingerprint | Key Type | Added | Expires | Status |
|-----------|----------------|----------------|-----------------|----------|-------|---------|--------|
| [Name] | [github-user] | [16-char hex] | [40-char hex] | RSA 4096 | YYYY-MM-DD | Never | Active |

*(Fill in your row after generating your key. See setup instructions below.)*

**To find your fingerprint after key generation:**
```bash
gpg --list-secret-keys --keyid-format=long
# Output: sec  rsa4096/KEYID  — KEYID is the short 16-char form
gpg --fingerprint KEYID
# Output: fingerprint = space-separated 40-char hex
```

---

## Setup Instructions (Summary)

Full step-by-step is in `CONTRIBUTING.md §4 — GPG Commit Signing`. Quick reference:

```bash
# 1. Generate key
gpg --full-generate-key
#    → RSA and RSA, 4096 bits, no expiry, your name, your GitHub email, strong passphrase

# 2. Get your key ID
gpg --list-secret-keys --keyid-format=long
#    → note KEYID from "sec rsa4096/KEYID ..."

# 3. Configure git
git config --global user.signingkey KEYID
git config --global commit.gpgsign true

# 4. Export public key → upload to GitHub → Settings → SSH and GPG keys → New GPG key
gpg --armor --export KEYID

# 5. Test: make a signed commit, then verify
git log --show-signature -1
```

---

## Annual Key Rotation Procedure

Rotate keys annually (or immediately on suspected compromise — see §Revocation below).

**Steps:**

1. **Generate new key** with the same email address:
   ```bash
   gpg --full-generate-key
   # RSA 4096, no expiry, same name + email, new passphrase
   ```

2. **Export and upload new public key** to GitHub (Settings → SSH and GPG keys → New GPG key):
   ```bash
   gpg --armor --export NEW_KEYID
   ```

3. **Update git config** to use the new key:
   ```bash
   git config --global user.signingkey NEW_KEYID
   ```

4. **Update this registry** (open a PR):
   - Add new key row with status `Active`
   - Mark old key row status as `Revoked` + add `Revocation Date: YYYY-MM-DD`

5. **Verify** the first commit with the new key:
   ```bash
   git log --show-signature -1
   # Must show: Good signature from "Your Name <email>"
   ```

6. **After 30-day grace period** — revoke the old key:
   ```bash
   gpg --gen-revoke OLD_KEYID > revocation.asc
   gpg --import revocation.asc
   # Optional: publish to keyserver
   # gpg --keyserver keys.openpgp.org --send-keys OLD_KEYID
   ```

7. **Remove old key from GitHub** (Settings → SSH and GPG keys → Delete)

---

## Immediate Key Revocation Procedure

Use when a key is compromised, device is lost/stolen, or team member departs.

**Response SLA:** Complete within 1 business hour of compromise discovery.

**Steps:**

1. **Revoke immediately** — generate and import revocation certificate:
   ```bash
   gpg --gen-revoke COMPROMISED_KEYID > revocation.asc
   gpg --import revocation.asc
   ```

2. **Remove from GitHub** — Settings → SSH and GPG keys → Delete the key

3. **Update this registry** with:
   - Status: `Revoked`
   - Revocation date
   - Reason: `Key compromise` / `Device lost` / `Offboarding: [Name]`

4. **Notify CISO** immediately — provide: key ID, revocation timestamp, reason, list of commits signed with the key in last 90 days

5. **Audit compromised commits** — review all commits signed by the revoked key:
   ```bash
   git log --all --format="%H %s" | while read sha msg; do
     if git verify-commit "$sha" 2>&1 | grep -q "COMPROMISED_KEYID"; then
       echo "$sha $msg"
     fi
   done
   ```

6. **Generate new key** and repeat the setup process before making any new commits

---

## Offboarding Procedure

When a team member departs, **same day**:

1. Remove their GPG key from their GitHub account (or ask them to)
2. Mark key as `Revoked` in this registry with reason `Offboarding: [Name]`, today's date
3. Audit their commits in the last 90 days (no action needed unless anomalies found)
4. Keep the revoked entry permanently for audit trail

---

## Commit Signature Verification

**Check the latest commit:**
```bash
git log --show-signature -1
```

**Check a specific commit:**
```bash
git verify-commit <commit-sha>
```

**Expected output — valid signature:**
```
commit abc1234...
gpg: Signature made 2026-02-27 12:00:00 UTC
gpg:                using RSA key 1A2B3C4D5E6F7890
gpg: Good signature from "Developer Name <email@paciolus.com>"
```

**Expected output — tampered or invalid:**
```
gpg: BAD signature from "Developer Name <email@paciolus.com>"
```

**If a BAD signature is detected:** contact CISO immediately and do not merge or deploy the commit.

**GitHub UI:** Signed commits show a green **Verified** badge next to the commit hash. Unsigned commits show nothing. Tampered commits show **Unverified** in red.

---

## Audit Trail for This Registry

Changes to this file are tracked by:
1. Git commit history (this file is version-controlled)
2. GitHub security log (Settings → Security log → filter "gpg_key")
3. CISO notification emails (for revocations)

---

## Version History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-02-27 | Engineering | Initial registry — Sprint 458 / CC8.6 |

---

**Document Owner:** CISO
**Version:** 1.0 — 2026-02-27
