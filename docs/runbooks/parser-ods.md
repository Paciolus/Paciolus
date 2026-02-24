# Parser Runbook: ODS

## Overview
The ODS parser handles OpenDocument Spreadsheet files (.ods) used by LibreOffice, Google Sheets (exported), and other open-source spreadsheet applications. ODS files are ZIP archives containing XML content. This is a newer format addition to the platform, so error thresholds are set higher during the rollout period to accommodate edge cases discovered in production.

## Common Errors

| Error | HTTP Code | Cause | Resolution |
|-------|-----------|-------|------------|
| `BadZipFile: File is not a zip file` | 422 | The uploaded .ods file is corrupt, truncated during upload, or is a renamed file of a different type | Ask the user to re-export the file from their spreadsheet application (LibreOffice, Google Sheets). Verify the file opens locally. |
| `No sheets found in workbook` | 422 | The ODS file contains no data sheets, or all sheets are empty | Verify the file has at least one sheet with data. Some ODS files may have hidden sheets only -- the user should unhide and re-export. |
| `Unsupported ODS content type` | 422 | The file contains embedded objects, charts-only sheets, or ODS features not supported by the parser (e.g., cell annotations used as data, complex formulas without cached values) | Ask the user to export the sheet as values-only (Paste Special -> Values in LibreOffice, then re-save). Formulas without cached results cannot be evaluated server-side. |
| `File too large` | 413 | File exceeds the global body size limit | Check `MAX_BODY_SIZE` middleware setting. ODS files from Google Sheets tend to be larger than equivalent XLSX. The user should trim data or export as CSV. |
| `Column detection failed` | 422 | The column detector could not identify required columns with sufficient confidence | ODS files from Google Sheets sometimes have different default column naming. Check if headers are in an unexpected row. |
| `Cell limit exceeded` | 422 | The sheet exceeds the maximum allowed cell count | Common with Google Sheets exports that include many empty rows. Ask the user to select only the data range before exporting. |

## Metrics to Watch
- `paciolus_parse_total{format="ods",stage="parse"}` -- successful parses
- `paciolus_parse_errors_total{format="ods"}` -- error count
- `paciolus_parse_duration_seconds{format="ods"}` -- parse latency
- `paciolus_active_parses{format="ods"}` -- concurrent operations

## Alert Thresholds
From `guards/parser_alerts.toml`:
- Error rate: 15%
- P95 latency: 10s
- Max concurrent: 50

> **Note:** Thresholds are set higher than CSV/XLSX because ODS is a newer format with less production exposure. These should be tightened as the parser matures and edge cases are resolved. Target steady-state thresholds: 8% error rate, 5s P95 latency.

## Rollback Procedure
1. Set `FORMAT_ODS_ENABLED=false` in `.env`
2. Restart the backend service
3. Verify `/metrics` shows zero active parses for format
4. Investigate root cause

## Escalation
- **P3**: Error rate >15% but <30% -- monitor, investigate. During initial rollout, many errors may be novel edge cases. Collect sample files for parser improvement.
- **P2**: Error rate >30% or latency >20s -- page on-call. Check for ZIP library regressions or XML parsing issues. Consider temporarily disabling the format.
- **P1**: Active parses stuck >0, service degradation -- immediate response. ODS XML parsing can be memory-intensive. Check for OOM conditions and oversized embedded objects.
