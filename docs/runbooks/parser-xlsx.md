# Parser Runbook: XLSX / XLS

## Overview
The XLSX/XLS parser handles Microsoft Excel workbook files (.xlsx, .xls) uploaded for trial balance ingestion and testing tool data imports. It uses openpyxl for .xlsx files and supports multi-sheet workbooks with automatic sheet selection heuristics. The parser enforces cell and column limits to guard against resource exhaustion from oversized or malicious workbooks.

## Common Errors

| Error | HTTP Code | Cause | Resolution |
|-------|-----------|-------|------------|
| `InvalidFileException: File is not a zip file` | 422 | The uploaded .xlsx file is corrupt, truncated during upload, or is actually a different file type with a renamed extension | Ask the user to re-export the file from their spreadsheet application. Verify the file opens in Excel/LibreOffice locally. |
| `Archive bomb detected` | 413 | The workbook's uncompressed size exceeds the safety threshold relative to its compressed size (zip bomb protection) | This is a security guard. Check the compression ratio. Legitimate large workbooks may need the threshold raised in configuration. If the file is genuinely malicious, block the source. |
| `XML bomb detected` | 422 | The workbook contains entity expansion attacks (billion laughs) in its internal XML | This is a security guard. The file is almost certainly malicious. Block the upload source and investigate. |
| `File too large` | 413 | File exceeds the global body size limit before parsing begins | Check `MAX_BODY_SIZE` middleware setting. The user needs to reduce the workbook size or export only the relevant sheet. |
| `Cell limit exceeded` | 422 | The workbook exceeds the maximum allowed cell count (rows x columns) | The user needs to trim the data. Check the cell limit configuration. Large workbooks should be split or exported as CSV. |
| `Column limit exceeded` | 422 | The sheet has more columns than the configured maximum | Often caused by accidental data in far-right columns. Ask the user to clean up the sheet and remove empty columns. |
| `No suitable sheet found` | 422 | Multi-sheet workbook where no sheet passes the column detection confidence threshold | Verify the workbook has a sheet with recognizable financial column headers. The user may need to rename columns or specify the target sheet. |
| `Legacy .xls format error` | 422 | The .xls file uses a legacy BIFF format that openpyxl cannot read, or the file is corrupt | Ask the user to re-save as .xlsx from Excel. If they cannot, check if xlrd fallback is available. |

## Metrics to Watch
- `paciolus_parse_total{format="xlsx",stage="parse"}` -- successful parses
- `paciolus_parse_errors_total{format="xlsx"}` -- error count
- `paciolus_parse_duration_seconds{format="xlsx"}` -- parse latency
- `paciolus_active_parses{format="xlsx"}` -- concurrent operations

## Alert Thresholds
From `guards/parser_alerts.toml`:
- Error rate: 8%
- P95 latency: 5s
- Max concurrent: 50

## Rollback Procedure
1. Set `FORMAT_XLSX_ENABLED=false` in `.env`
2. Restart the backend service
3. Verify `/metrics` shows zero active parses for format
4. Investigate root cause

## Escalation
- **P3**: Error rate >8% but <16% -- monitor, investigate. Check if a specific Excel version or export tool is producing files the parser cannot handle.
- **P2**: Error rate >16% or latency >10s -- page on-call. Check for openpyxl version regressions, memory pressure from large workbooks, or archive bomb false positives.
- **P1**: Active parses stuck >0, service degradation -- immediate response. Large workbooks can consume significant memory. Check for OOM conditions and kill stuck worker threads.
