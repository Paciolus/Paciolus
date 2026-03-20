# Actions & Image Pin Registry

> Every pinned SHA and digest used in CI/CD workflows and Dockerfiles.
> **Rotation policy:** Any SHA/digest update requires a PR that atomically updates
> this file and the corresponding workflow/Dockerfile references.

Last updated: 2026-03-20 (AUDIT-09 — dependency compliance gate)

## GitHub Actions

| Action | Pinned SHA | Original Tag | Date Pinned |
|--------|-----------|--------------|-------------|
| `actions/checkout` | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` | v6 | 2026-03-18 |
| `actions/checkout` | `34e114876b0b11c390a56381ad16ebd13914f8d5` | v4 | 2026-03-18 |
| `actions/setup-python` | `a309ff8b426b58ec0e2a45f0f869d46889d02405` | v6 | 2026-03-18 |
| `actions/setup-node` | `53b83947a5a98c8d113130e565377fae1a50d02f` | v6 | 2026-03-18 |
| `actions/upload-artifact` | `b7c566a772e6b6bfb58ed0dc250532a479d7789f` | v6 | 2026-03-18 |
| `actions/upload-artifact` | `ea165f8d65b6e75b540449e92b4886f43607fa02` | v4 | 2026-03-18 |
| `actions/download-artifact` | `018cc2cf5baa6db3ef3c5f8a56943fffe632ef53` | v6 | 2026-03-20 |
| `actions/github-script` | `f28e40c7f34bde8b3046d885e986cb6290c5673b` | v7 | 2026-03-18 |

### Where Used

- `actions/checkout` v6 — `ci.yml`, `backup-integrity-check.yml`, `dependency-compliance.yml`
- `actions/checkout` v4 — `dr-test-monthly.yml`
- `actions/setup-python` v6 — `ci.yml`, `backup-integrity-check.yml`, `dependency-compliance.yml`
- `actions/setup-node` v6 — `ci.yml`, `dependency-compliance.yml`
- `actions/upload-artifact` v6 — `ci.yml`, `backup-integrity-check.yml`, `dependency-compliance.yml`
- `actions/upload-artifact` v4 — `dr-test-monthly.yml`
- `actions/download-artifact` v6 — `dependency-compliance.yml`
- `actions/github-script` v7 — `backup-integrity-check.yml`, `dr-test-monthly.yml`

## Pinned Binaries

| Binary | Version | SHA256 | Date Pinned |
|--------|---------|--------|-------------|
| TruffleHog (linux_amd64) | 3.93.8 | `b965dd2a4106dc3c194dfcaa93931fe0a93571261e3e1f46f2d1728b6612e019` | 2026-03-18 |

## Docker Base Images

| Image | Manifest Digest | Tag | Date Pinned |
|-------|----------------|-----|-------------|
| `python:3.12-slim-bookworm` | `sha256:31c0807da611e2e377a2e9b566ad4eb038ac5a5838cbbbe6f2262259b5dc77a0` | 3.12-slim-bookworm | 2026-03-18 |
| `node:22-alpine` | `sha256:8094c002d08262dba12645a3b4a15cd6cd627d30bc782f53229a2ec13ee22a00` | 22-alpine | 2026-03-18 |

### Where Used

- `python:3.12-slim-bookworm` — `backend/Dockerfile` (builder + production stages)
- `node:22-alpine` — `frontend/Dockerfile` (deps + builder + runner stages)

## Rotation Procedure

1. Identify the new version/tag to upgrade to
2. Resolve its commit SHA (actions) or manifest digest (Docker images)
3. Update this registry file with the new SHA/digest, tag, and date
4. Update all workflow files and/or Dockerfiles that reference the old SHA/digest
5. Open a single PR containing both this file and the workflow/Dockerfile changes
6. Verify CI passes on the PR before merging
