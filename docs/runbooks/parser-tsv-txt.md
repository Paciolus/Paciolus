# Parser Runbook: TSV / TXT

## Overview
The TSV/TXT parser handles tab-separated value files (.tsv) and generic text files (.txt) that contain tabular financial data. It shares infrastructure with the CSV parser but applies a separate delimiter detection heuristic since these files may use tabs, pipes, fixed-width columns, or other separators. The parser attempts automatic delimiter detection and falls back to tab-separation as the default assumption for `.tsv` files.

## Common Errors

| Error | HTTP Code | Cause | Resolution |
|-------|-----------|-------|------------|
| `Delimiter detection failed` | 422 | The parser could not confidently identify a consistent delimiter in the file. This occurs when the file uses mixed delimiters, fixed-width formatting (no delimiters), or has irregular spacing that confuses the sniffer. | Ask the user what delimiter the file uses. If the file is fixed-width, it must be converted to a delimited format (CSV or TSV) before upload. Some ERP exports use fixed-width columns that require manual conversion. |
| `UnicodeDecodeError: invalid start byte` | 422 | File uses an encoding not in the detection cascade (UTF-8 -> Latin-1 -> Windows-1252). Common with TXT files exported from legacy mainframe or ERP systems that use EBCDIC or other non-Latin encodings. | Ask the user to re-save the file as UTF-8. For mainframe exports, an encoding conversion step may be needed before upload. |
| `EmptyDataError: no columns to parse` | 422 | The file is empty, contains only whitespace, or the detected delimiter produces no columns | Verify the file has actual data. Check if the file uses a delimiter the parser did not detect. |
| `ParserError: Error tokenizing data` | 422 | Inconsistent column counts across rows after delimiter detection | The file may have irregular formatting. Ask the user to verify all rows have consistent column counts. Common with TXT files that mix data and summary/footer rows. |
| `Column detection failed` | 422 | The column detector could not identify required columns with sufficient confidence after parsing | TXT files often have non-standard or abbreviated column headers. Check if the headers are recognizable. The user may need to rename columns to match expected patterns. |
| `File too large` | 413 | File exceeds the global body size limit | Check `MAX_BODY_SIZE` middleware setting. The user needs to split the file. |

## Metrics to Watch
- `paciolus_parse_total{format="tsv",stage="parse"}` -- successful parses
- `paciolus_parse_errors_total{format="tsv"}` -- error count
- `paciolus_parse_duration_seconds{format="tsv"}` -- parse latency
- `paciolus_active_parses{format="tsv"}` -- concurrent operations

## Alert Thresholds
From `guards/parser_alerts.toml`:
- Error rate: 5%
- P95 latency: 2s
- Max concurrent: 50

## Rollback Procedure
1. Set `FORMAT_TSV_ENABLED=false` in `.env`
2. Restart the backend service
3. Verify `/metrics` shows zero active parses for format
4. Investigate root cause

## Escalation
- **P3**: Error rate >5% but <10% -- monitor, investigate. Check if a specific ERP or accounting system is producing TXT exports with non-standard formatting.
- **P2**: Error rate >10% or latency >4s -- page on-call. Check for pandas sniffer regressions or encoding library issues.
- **P1**: Active parses stuck >0, service degradation -- immediate response. TSV/TXT parsing is typically fast. Stuck parses likely indicate an infinite loop in delimiter detection. Kill stuck threads and investigate the specific file.
