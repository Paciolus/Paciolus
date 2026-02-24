# Parser Runbook: IIF

## Overview
The IIF (Intuit Interchange Format) parser handles `.iif` files exported from QuickBooks Desktop. IIF is a tab-delimited text format with section headers (e.g., `!TRNS`, `!SPL`, `!ENDTRNS`) that define transaction blocks. The format is specific to the QuickBooks ecosystem and has no formal specification beyond Intuit's documentation.

## Common Errors

| Error | HTTP Code | Cause | Resolution |
|-------|-----------|-------|------------|
| `No TRNS section found in IIF file` | 422 | The file does not contain the expected `!TRNS` header row that marks the beginning of transaction data. This can happen with IIF files that contain only list data (accounts, customers, items) rather than transactions, or with corrupted exports. | Verify the user exported transactions, not just lists, from QuickBooks. The export path in QuickBooks Desktop is File > Utilities > Export > Lists to IIF File (lists only) vs. Timer > Export Data (transactions). |
| `Mismatched column count` | 422 | One or more data rows have a different number of tab-delimited fields than the header row defines. Common when transaction memo fields contain embedded tabs or when the file was edited in a text editor that altered tab characters. | Ask the user to re-export from QuickBooks without manual edits. If the file was edited, check for embedded tabs in memo/description fields. |
| `Null bytes detected in file` | 422 | The file contains null bytes (`\x00`), typically indicating a binary file was renamed to `.iif`, or the file was corrupted during transfer (e.g., FTP in binary mode for a text file, or a Unicode encoding issue). | Ask the user to re-export the file. If the file was transferred via FTP, ensure ASCII/text mode was used. Check if the file opens correctly in a text editor. |
| `Unrecognized section header` | 422 | The file contains section headers that the parser does not recognize. While the parser handles standard sections (`!TRNS`, `!SPL`, `!ENDTRNS`, `!ACCNT`, `!CUST`, etc.), some QuickBooks add-ons or third-party tools produce non-standard sections. | Check which sections the file contains. Non-standard sections are skipped, but if the transaction data is inside a non-standard section, it will not be extracted. Ask the user to export using standard QuickBooks export. |
| `TRNS/SPL block mismatch` | 422 | The number of `!TRNS` entries does not align with corresponding `!ENDTRNS` markers, or `!SPL` (split) lines appear outside a transaction block. Indicates a truncated or malformed export. | Ask the user to re-export. This usually indicates the QuickBooks export was interrupted. |
| `File too large` | 413 | File exceeds the global body size limit | IIF files are typically small. A very large file may indicate a multi-year export. Suggest exporting by date range. |

## Metrics to Watch
- `paciolus_parse_total{format="iif",stage="parse"}` -- successful parses
- `paciolus_parse_errors_total{format="iif"}` -- error count
- `paciolus_parse_duration_seconds{format="iif"}` -- parse latency
- `paciolus_active_parses{format="iif"}` -- concurrent operations

## Alert Thresholds
From `guards/parser_alerts.toml`:
- Error rate: 10%
- P95 latency: 3s
- Max concurrent: 50

## Rollback Procedure
1. Set `FORMAT_IIF_ENABLED=false` in `.env`
2. Restart the backend service
3. Verify `/metrics` shows zero active parses for format
4. Investigate root cause

## Escalation
- **P3**: Error rate >10% but <20% -- monitor, investigate. Check if a specific QuickBooks version or third-party export tool is producing files the parser cannot handle.
- **P2**: Error rate >20% or latency >6s -- page on-call. Check for parser regressions or a batch of corrupted files from a single source.
- **P1**: Active parses stuck >0, service degradation -- immediate response. IIF parsing is typically fast and lightweight. Stuck parses likely indicate an infinite loop in section boundary detection. Kill stuck threads and investigate the specific file.
