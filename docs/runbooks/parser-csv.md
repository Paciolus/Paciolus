# Parser Runbook: CSV

## Overview
The CSV parser handles comma-separated value files uploaded for trial balance ingestion and testing tool data imports. It supports automatic delimiter detection (comma, semicolon, pipe), multiple encodings (UTF-8, Latin-1, Windows-1252), and header row detection via the shared column detector module.

## Common Errors

| Error | HTTP Code | Cause | Resolution |
|-------|-----------|-------|------------|
| `UnicodeDecodeError: invalid start byte` | 422 | File uses an encoding not in the detection cascade (UTF-8 -> Latin-1 -> Windows-1252) | Ask the user to re-save the file as UTF-8. Check if the file contains non-Latin characters requiring a broader encoding. |
| `EmptyDataError: no columns to parse` | 422 | Uploaded file is empty or contains only whitespace/blank lines | Verify the file has actual data rows. Check for BOM-only files or files with only header rows. |
| `ParserError: Error tokenizing data` | 422 | Inconsistent number of delimiters across rows, or wrong delimiter detected | Check if the file uses a non-standard delimiter. Verify rows have consistent column counts. The user may need to clean trailing commas or fix malformed rows. |
| `File too large` | 413 | File exceeds the global body size limit | Check the `MAX_BODY_SIZE` middleware setting. The user needs to split the file or reduce row count. |
| `Column detection failed` | 422 | The column detector could not identify required columns (e.g., account number, balance) with sufficient confidence | Verify the file has recognizable column headers. Check `column_detector.py` confidence threshold (default 0.8). |

## Metrics to Watch
- `paciolus_parse_total{format="csv",stage="parse"}` -- successful parses
- `paciolus_parse_errors_total{format="csv"}` -- error count
- `paciolus_parse_duration_seconds{format="csv"}` -- parse latency
- `paciolus_active_parses{format="csv"}` -- concurrent operations

## Alert Thresholds
From `guards/parser_alerts.toml`:
- Error rate: 5%
- P95 latency: 2s
- Max concurrent: 50

## Rollback Procedure
1. Set `FORMAT_CSV_ENABLED=false` in `.env`
2. Restart the backend service
3. Verify `/metrics` shows zero active parses for format
4. Investigate root cause

## Escalation
- **P3**: Error rate >5% but <10% -- monitor, investigate. Check if a batch of malformed files is being uploaded by a single user or integration.
- **P2**: Error rate >10% or latency >4s -- page on-call. Check for encoding library regressions or pandas version issues.
- **P1**: Active parses stuck >0, service degradation -- immediate response. Kill stuck threads, check for infinite loops in delimiter detection.
