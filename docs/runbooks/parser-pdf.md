# Parser Runbook: PDF

## Overview
The PDF parser extracts tabular financial data from PDF documents using table detection and extraction libraries. Due to the inherent variability of PDF layouts (scanned vs. native, single-column vs. multi-column, merged cells, headers spanning rows), this parser has the highest baseline error rate and latency of all format parsers. A quality gate system evaluates extraction confidence before accepting results.

## Common Errors

| Error | HTTP Code | Cause | Resolution |
|-------|-----------|-------|------------|
| `No tables detected in PDF` | 422 | The PDF contains no recognizable tabular structures. Common with scanned documents that lack OCR, image-only PDFs, or PDFs where financial data is in free-form text rather than tables. | Ask the user to provide a text-based PDF (not a scanned image). If the data is in paragraph form, suggest exporting from the source system as CSV or Excel instead. |
| `Corrupt or unreadable PDF` | 422 | The PDF file is damaged, password-protected, uses unsupported encryption, or has a malformed internal structure | Ask the user to re-export the PDF. Check if the file is password-protected (the parser does not support encrypted PDFs). Verify the file opens in a PDF reader. |
| `Quality gate failed: confidence below threshold` | 422 | Tables were extracted but the quality gate determined the extraction confidence is too low for reliable use. This triggers when column alignment, data type consistency, or row completeness falls below the configured threshold. | The PDF layout is too complex for reliable automated extraction. Ask the user to export the data as CSV or Excel from the source system. If the data is critical, the quality gate threshold can be reviewed but should not be lowered below 0.6. |
| `Quality gate failed: row count mismatch` | 422 | The number of extracted rows differs significantly from the expected count (detected via page analysis), suggesting rows were merged or dropped during extraction | Re-extraction may help if the issue is non-deterministic. Otherwise, the user should provide the data in a structured format. |
| `File too large` | 413 | PDF exceeds the global body size limit | Large PDFs with many pages take proportionally longer. The user should extract only the relevant pages or provide data in another format. |
| `Page limit exceeded` | 422 | The PDF has more pages than the configured maximum for table extraction | The parser limits page count to prevent excessive processing time. The user should split the PDF or provide a structured export. |
| `Extraction timeout` | 504 | Table extraction exceeded the per-parse timeout, typically due to complex layouts or very large page counts | Check if the PDF has unusual layouts (rotated pages, nested tables, watermarks). Suggest the user provide a simpler export. |

## Metrics to Watch
- `paciolus_parse_total{format="pdf",stage="parse"}` -- successful parses
- `paciolus_parse_errors_total{format="pdf"}` -- error count
- `paciolus_parse_duration_seconds{format="pdf"}` -- parse latency
- `paciolus_active_parses{format="pdf"}` -- concurrent operations
- `paciolus_parse_quality_gate{format="pdf",result="pass"}` -- quality gate pass rate
- `paciolus_parse_quality_gate{format="pdf",result="fail"}` -- quality gate fail rate

## Alert Thresholds
From `guards/parser_alerts.toml`:
- Error rate: 20%
- P95 latency: 15s
- Max concurrent: 50

> **Note:** PDF parsing has inherently higher error rates and latency due to the unstructured nature of the format. A 20% error rate is expected during normal operation because many uploaded PDFs are not suitable for automated table extraction (scanned images, free-form text, complex layouts). The quality gate is intentionally strict to prevent low-confidence data from entering downstream analysis.

## Rollback Procedure
1. Set `FORMAT_PDF_ENABLED=false` in `.env`
2. Restart the backend service
3. Verify `/metrics` shows zero active parses for format
4. Investigate root cause

## Escalation
- **P3**: Error rate >20% but <40% -- monitor, investigate. Check if a new PDF export format from a common accounting tool is causing widespread failures. Collect sample files.
- **P2**: Error rate >40% or latency >30s -- page on-call. Check for extraction library regressions, memory pressure, or a spike in large PDF uploads. Consider rate limiting PDF uploads specifically.
- **P1**: Active parses stuck >0, service degradation -- immediate response. PDF extraction is CPU-intensive and runs via `asyncio.to_thread()`. Stuck parses can exhaust the thread pool. Kill stuck threads and check for infinite loops in the extraction library.
