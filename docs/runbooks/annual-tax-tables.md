# Annual tax tables (Sprint 860)

The W-2 / W-3 Reconciliation and Form 1099 tools apply built-in statutory figures. Each tax year's
figures live in `backend/tax_tables/ty<year>.py`: every figure with its citation, the URL it was read
from and the sentence that states it, plus a practitioner sign-off per tool.

## The rule

- A run on a built-in year needs that year's sign-off. Unsigned tables run behind the banner
  through **2026-12-15** (the council date) and are refused after it (`403 TAX_YEAR_NOT_SIGNED_OFF`).
- Form 1099 refuses a year after its latest table (`400 TAX_YEAR_NOT_AVAILABLE`). The 2025 table
  also serves every earlier year.
- W-2 refuses a year with no table, unless the caller supplies all eleven required figures (the API
  override; the web form cannot).
- CI (`backend/tests/test_sprint860_tax_tables.py::test_this_seasons_tables_are_ready`) **warns from
  Nov 1** when that year's table is missing or unsigned, and **fails from Jan 1**.

## Calendar

| When | Source | Figures |
|------|--------|---------|
| mid-October | SSA COLA announcement (`ssa.gov/oact/cola/cbb.html`; IRS Tax Topic 751 restates it) | Social Security wage base |
| ~November | IRS retirement-limits notice (e.g. Notice 2025-67) and news release | 401(k) deferral and catch-ups; SIMPLE deferral and catch-ups |
| ~May (prior year) | HSA revenue procedure (e.g. Rev. Proc. 2025-19) | HSA self-only and family |
| fixed | IRC §223(b)(3)(B); §3101; §3102(f) | HSA age-55 catch-up $1,000; SS 6.2%; Medicare 1.45%; Additional Medicare 0.9% over $200,000 |
| Oct–Jan | IRS Instructions for Forms 1099-MISC and 1099-NEC; 1099-INT | reporting thresholds (indexed from 2027) |
| **Nov 1** | — | yearly sign-off day, shared with the credentials rotation (`backup-restore.md` §6) |

## Adding a year

1. Copy the latest `ty<year>.py` to `ty<next>.py`; set `TAX_YEAR`.
2. Replace every figure from its source: value, citation, URL and the quoted sentence. Draft IRS
   instructions do not count: leave `sources_final=False` until the final version is out.
3. Add the year to `TABLES` in `backend/tax_tables/__init__.py`.
4. Run `pytest tests/test_sprint860_tax_tables.py tests/test_tax_figures_status.py`. The tests check
   that each excerpt states its value, that no figure falls, that every move over 10% is listed in
   `acknowledged_large_moves` with its reason, and the catch-up floors.
5. The banners name the tabulated years: copy the new text from the failing
   `test_frontend_banner_matches_backend` into `frontend/src/content/tax-figures.ts`.

## Signing off

The practitioner checks each figure against its source (the URL and quoted sentence are in the file),
then records, per tool:

```python
sign_offs={
    "w2_reconciliation": SignOff(signed_off_by="Name, CPA", signed_off_on=date(2026, 12, 1), sources_final=True),
    ...
}
```

(`from datetime import date` at the top of the file.) A partial record (a name without a date, or with
draft sources) fails `test_recorded_sign_offs_are_complete`. The banner then names the year as signed
off: update `tax-figures.ts` in the same commit.

## Not modelled

- The higher SIMPLE limits for employers with 25 or fewer employees, or that elect them
  (IRC §408(p)(2)(E)(i)): 2026 $18,100 deferral, $3,850 age-50 catch-up. Such a plan is checked
  against the standard figures.
- The 2027+ indexed 1099 threshold: added as a new table when the IRS publishes it.
