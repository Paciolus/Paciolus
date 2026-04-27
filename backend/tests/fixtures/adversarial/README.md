# Adversarial Fixture Corpus

**Sprint:** 723

This directory holds adversarial inputs for backfill tests on the worst-covered
production-critical files (the ones declared in `backend/coverage_floors.toml`).
The intent is to make hostile inputs cheap to reuse across tests, so a single
parser bug surfaces in every test that should catch it rather than only the one
test whose author happened to think of it.

## What goes here

Inputs that exercise edge cases of file parsers, PDF generators, or trial-balance
ingestion. The shape is "real-world bad" or "deliberately malicious" — not just
synthetic happy-path data:

- **Workbook inspector** (`workbook_inspector.py`, current 18.6%): password-protected
  xlsx, malformed ods, XML billion-laughs bombs, zip slip, corrupted CSV with
  embedded null bytes, Unicode normalization edge cases (NFC/NFD divergence in
  account codes).
- **Excel generator** (`excel_generator.py`, current 45.7%): style-collision /
  duplicate `NamedStyle` triggers, very long sheet names, emoji in cell content,
  date columns with mixed strings + datetimes.
- **Leadsheet generator** (`leadsheet_generator.py`, current 11.4%): style
  collision on duplicate `_register_styles` calls (the silent ValueError swallow
  flagged in Guardian's audit), empty TBs, single-account TBs.
- **Population profile / accrual completeness memos**: TBs with all-zero
  balances, single-period inputs, account-code collisions across periods.

## How to add a fixture

1. Drop the file in `backend/tests/fixtures/adversarial/<category>/<descriptive_name>.<ext>`.
2. Add a one-line comment in the README §3 below describing what the input
   exercises.
3. Reference it from a test by `Path(__file__).parent / "fixtures" / "adversarial" / ...`.
   Tests should not copy the bytes inline.

## What's here today

Sprint 723 establishes the directory and pattern. **No fixtures land in Sprint 723
itself** — adding fixtures is the work of the per-file backfill sprints that
follow (each one raises a floor in `coverage_floors.toml`). The directory exists
so future contributors have a recognizable shape to drop fixtures into rather
than scattering them across `tests/`.

The first natural backfill is `workbook_inspector.py` (18.6%, first-touch on
every upload). A future sprint will land `xml_billion_laughs.xlsx`,
`zip_slip.xlsx`, `nfd_account_code.csv`, etc. here.

## Why a separate directory, not inline `tests/fixtures/`

The existing `tests/fixtures/` holds happy-path data. Adversarial inputs need a
stronger mental model: every file here is hostile by design. Mixing them with
happy-path fixtures invites "huh, I thought that fixture was clean" mistakes
during test authoring. The directory split is the cheap way to keep the boundary
clear.

## Related

- `backend/coverage_floors.toml` — the floor declarations these fixtures will
  help raise.
- `docs/runbooks/coverage-floors.md` — process for raising a floor after a
  backfill lands.
