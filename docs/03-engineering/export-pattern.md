# Export Endpoint Pattern

**Sprint:** 539 (introduced) → 725 (consolidated to `shared.csv_export`)

CSV exports across `routes/export_*.py` go through one of two helpers in
`backend/shared/csv_export.py`. New CSV endpoints should pick the helper that
matches the shape, not invent a third path.

## Two helpers, two shapes

### `csv_export_handler` — testing-tool flagged-entry shape

Use when:
- The export is a tool's CSV with a stable column schema.
- Rows come from `test_results[*].flagged_entries[*].entry` (the canonical
  testing-tool envelope).
- The footer is the standard `write_testing_csv_summary` (composite score +
  tier + flag counts) — or a simple custom variant of the same.

Example (revenue testing):

```python
return csv_export_handler(
    test_results=rev_input.test_results,
    schema=REVENUE_COLUMNS,
    composite_score=rev_input.composite_score,
    filename_raw=rev_input.filename,
    filename_suffix="RevenueTesting_Flagged",
    entry_label="Entries",
    error_log_prefix="Revenue Testing",
    error_code="revenue_csv_export_error",
)
```

The schema is a list of `(header, extractor)` tuples. The extractor receives
`(flagged_entry_dict, entry_dict)` and returns the cell value. Schema
constants (`JE_COLUMNS`, `AP_COLUMNS`, etc.) live alongside the route in
`routes/export_testing.py`.

### `diagnostic_csv_export` — free-form body shape

Use when:
- The export is a diagnostic surface (TB, anomaly list, population profile,
  preflight issues, accrual completeness, etc.) where the body has multiple
  sections, custom totals rows, or per-row drill-down formatting.
- The body shape doesn't fit a single schema.

Example (population profile):

```python
def _body(writer: Any) -> None:
    writer.writerow(["TB POPULATION PROFILE"])
    writer.writerow([])
    writer.writerow(["Statistic", "Value"])
    writer.writerow(["Account Count", pp_input.account_count])
    # ...sectioned content...

return diagnostic_csv_export(
    body_writer=_body,
    filename_raw=pp_input.filename or "PopProfile",
    filename_suffix="Profile",
    error_log_prefix="Population profile",
    error_code="population_profile_csv_export_error",
)
```

The helper handles `StringIO` setup, UTF-8-BOM encoding, `safe_download_filename`,
the `streaming_csv_response` transport, and exception handling. The route only
writes its body.

## What both helpers handle for you

| Concern | Helper does it |
|---|---|
| `StringIO` + `csv.writer` setup | ✅ |
| UTF-8 with BOM (`utf-8-sig`) encoding | ✅ |
| `safe_download_filename` (sanitization + extension) | ✅ |
| `streaming_csv_response` transport (Content-Disposition, MIME) | ✅ |
| `try/except` for `ValueError`/`KeyError`/`TypeError`/`UnicodeEncodeError` | ✅ |
| `logger.exception` on failure with the configured prefix | ✅ |
| `HTTPException(500, sanitize_error(...))` with the error code | ✅ |

## Adding a new CSV export endpoint

1. Pick the helper that matches the shape (above).
2. Define your column schema or body writer.
3. Wire the endpoint with `@router.post(...)`, `@limiter.limit(RATE_LIMIT_EXPORT)`,
   and `dependencies=[Depends(check_export_access)]` — these three decorators
   are the minimum surface for a production CSV endpoint.
4. Return the helper's `StreamingResponse`.

Do not:
- Inline `StringIO()` + `csv.writer(...)` + `try/except` again. The helpers
  exist to centralize that boilerplate; new copies of it drift over time.
- Build a third helper. If neither fits, the right move is to discuss whether
  the new shape justifies a refactor of the existing helpers, not a third one.

## What's NOT covered by these helpers

- **PDF/Excel exports** (e.g., `/export/pdf`, `/export/excel`,
  `/export/leadsheets`). Those use `streaming_pdf_response` /
  `streaming_excel_response` directly. A future sprint can collapse those
  with their own helper if duplication accumulates.
- **Authenticated route metadata** (rate limit, entitlement check, dependency
  injection). Those live on the FastAPI route decorators above the helper
  call.
- **Memo PDF generation.** Memos go through `routes/export_memos.py` which
  uses the registry pattern + Sprint 722's memory probe. Don't conflate
  memo PDFs with CSV diagnostic exports.

## Related

- Sprint 539: original `csv_export_handler` introduction in
  `routes/export_testing.py`.
- Sprint 725: promoted to `shared/csv_export.py`, added
  `diagnostic_csv_export`, refactored 6 endpoints in `export_diagnostics.py`
  and 2 endpoints in `export_testing.py`.
- `backend/tests/test_csv_export_helpers.py`: direct unit tests for the
  helpers; the route-level tests in `tests/test_export_*_routes.py` provide
  end-to-end byte-identical regression coverage.
