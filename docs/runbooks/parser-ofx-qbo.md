# Parser Runbook: OFX / QBO

## Overview
The OFX/QBO parser handles Open Financial Exchange (.ofx) and QuickBooks Online (.qbo) files, both of which use the OFX specification for bank statement and transaction data. OFX files use SGML-like markup (OFX 1.x) or XML (OFX 2.x). QBO files are OFX files with QuickBooks-specific extensions. The parser extracts transaction lists for use in bank reconciliation and other testing tools.

## Common Errors

| Error | HTTP Code | Cause | Resolution |
|-------|-----------|-------|------------|
| `Truncated OFX file: missing closing tags` | 422 | The file was cut off during download or export from the bank's portal. Common when browser downloads are interrupted or when the bank's export service times out on large date ranges. | Ask the user to re-download the file from their bank portal. If the issue persists, suggest downloading a smaller date range and uploading in batches. |
| `No transactions found in OFX file` | 422 | The file parsed successfully but contains no transaction entries (`<STMTTRN>` elements). This can happen with empty statement periods or files that contain only account metadata. | Verify the date range covers a period with transaction activity. Some banks export header-only files for periods with no activity. |
| `Invalid date format in transaction` | 422 | One or more transaction dates do not conform to the OFX date format (`YYYYMMDD` or `YYYYMMDDHHMMSS`). Some banks emit non-standard date formats or include timezone offsets the parser does not expect. | Check the raw file for the date format used. If it is a known bank-specific format, a parser rule may need to be added. Ask the user which bank exported the file. |
| `Unsupported OFX version` | 422 | The file uses an OFX version or dialect that the parser does not recognize. Rare, but can occur with very old files (OFX 1.0.2) or non-standard implementations. | Check the `<OFX>` header for version information. If it is a common bank, file a bug to add support. As a workaround, the user can often convert to CSV via their bank or a third-party tool. |
| `Malformed SGML: unexpected token` | 422 | The OFX 1.x SGML markup is malformed. Common with files from banks that do not fully comply with the OFX specification (e.g., missing closing tags that are technically optional in SGML but required by the parser). | The parser attempts lenient SGML parsing but some files are too malformed. Ask the user to try downloading the file again or contact their bank about OFX export quality. |
| `Duplicate FITID detected` | 422 | Multiple transactions share the same Financial Institution Transaction ID, which should be unique. Can indicate a corrupted export or a bank-side bug. | The parser flags this rather than silently deduplicating. Ask the user to verify the file and re-download if necessary. |
| `File too large` | 413 | File exceeds the global body size limit | OFX files are typically small. A very large file may indicate a multi-year export. Suggest the user download by quarter or month. |

## Metrics to Watch
- `paciolus_parse_total{format="ofx",stage="parse"}` -- successful parses
- `paciolus_parse_errors_total{format="ofx"}` -- error count
- `paciolus_parse_duration_seconds{format="ofx"}` -- parse latency
- `paciolus_active_parses{format="ofx"}` -- concurrent operations

## Alert Thresholds
From `guards/parser_alerts.toml`:
- Error rate: 10%
- P95 latency: 3s
- Max concurrent: 50

## Rollback Procedure
1. Set `FORMAT_OFX_ENABLED=false` in `.env`
2. Restart the backend service
3. Verify `/metrics` shows zero active parses for format
4. Investigate root cause

## Escalation
- **P3**: Error rate >10% but <20% -- monitor, investigate. Check if a specific bank's OFX export format changed. Collect sample files and identify the financial institution from the `<FI>` header.
- **P2**: Error rate >20% or latency >6s -- page on-call. Check for parser library regressions or a surge of malformed files from a single source.
- **P1**: Active parses stuck >0, service degradation -- immediate response. OFX parsing is typically fast; stuck parses likely indicate an infinite loop in SGML tag matching. Kill stuck threads and investigate the specific file.
