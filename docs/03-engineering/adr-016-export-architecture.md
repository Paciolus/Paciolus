# ADR-016: Export Architecture (Mapper / Generator Separation)

**Status:** Proposed (target for Sprint 748 + Sprint 749)
**Date:** 2026-04-29
**Decision-makers:** Engineering team

## Context

Two existing patterns govern exports today:

1. **`shared/csv_export.py`** (Sprint 539 → 725) — `csv_export_handler` and
   `streaming_csv_export` for testing-tool flagged-entry shape and freeform
   sectioned shape, respectively. Documented in `docs/03-engineering/export-pattern.md`.
2. **Inline transformation in route handlers** — `routes/export_diagnostics.py`
   and `routes/export_memos.py` carry 800+ lines of per-endpoint inline
   loops, formatting, and PDF/Excel section assembly. The same domain
   transformation is repeated in 2–3 forms (CSV row, PDF cell, Excel cell)
   across siblings.

Drift symptoms:

- **Inconsistent endpoint shape.** Some export routes validate first, some
  authorize first, some check entitlement mid-handler. No common skeleton.
- **`export_memos.py` ambiguity.** Routes are registered partly via dynamic
  loops, partly via explicit decorators. Future-readers can't tell which
  strategy is canonical.
- **No contract tests.** Schema changes (e.g., a renamed column) propagate
  silently to clients downloading the export.
- **Domain logic embedded in HTTP handlers.** A test that exercises the
  CSV export's column ordering needs the full FastAPI request fixture
  instead of just calling a mapper function with a dataclass input.

## Decision

Export endpoints follow a single skeleton:

```
validate input → authorize / entitlement gate → mapper → generator → streaming response
```

### Layers

| Layer | Owns | Location |
|-------|------|----------|
| **Route** | HTTP plumbing (Depends, status codes), input validation, authorization, entitlement enforcement, streaming response wiring | `backend/routes/export_*.py` |
| **Mapper** | DTO normalization, row/section builders, domain → renderable transforms | `backend/export/mappers/<domain>.py` (new package) |
| **Generator** | Format-specific serialization (CSV bytes, Excel workbook, PDF document) | `backend/shared/csv_export.py` (existing); `backend/shared/pdf_*.py` (existing); future `excel_export.py` |

Routes are slim controllers — they should not contain inline `for row in
results: ...` loops, format-specific cell formatting, or PDF section assembly.
That work belongs in the mapper layer.

### Mapper module shape

```python
# backend/export/mappers/anomaly_summary.py

from dataclasses import dataclass

@dataclass(frozen=True)
class AnomalySummaryExportInput:
    # Normalized DTO — what the mapper consumes
    ...

@dataclass(frozen=True)
class AnomalySummaryCsvRow:
    # What the CSV generator consumes
    ...

@dataclass(frozen=True)
class AnomalySummaryPdfSection:
    # What the PDF generator consumes
    ...

def build_csv_rows(input: AnomalySummaryExportInput) -> list[AnomalySummaryCsvRow]: ...
def build_pdf_sections(input: AnomalySummaryExportInput) -> list[AnomalySummaryPdfSection]: ...
```

Mappers are pure functions. They take a normalized input, return shape-specific
outputs. They do not import from `fastapi` or `sqlalchemy`. They are unit-testable
without HTTP fixtures or a database.

### Endpoint skeleton

```python
@router.post("/audit/<tool>/export.<format>")
def export_<tool>_<format>(
    request: Request,
    body: <ToolRequest>,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    # 1. validate (Pydantic on body parameter)
    # 2. authorize / entitlement
    require_entitlement(current_user, "<tool>")

    # 3. compute the analysis (or load it)
    result = run_<tool>_analysis(db, body)

    # 4. mapper
    rows = build_csv_rows(<MapperInput>.from_result(result))

    # 5. generator
    return csv_export_handler(rows, schema=<COLUMNS>, filename_suffix="<Tool>")
```

### `export_memos.py` registration strategy

Pick **one** of the following and document it as the canonical strategy:

- **Fully declarative:** all memo routes registered via a single loop over a
  manifest. Document any explicit exceptions inline next to the manifest.
- **Fully explicit:** each memo route is a separate decorator + handler.
  Shared logic lives in factory helpers (`build_memo_response(...)`).

Sprint 749 picks one and converts the other style to match. The mixed style
is forbidden going forward.

### Contract tests

Each export endpoint needs at least one contract test asserting:

- Headers (Content-Type, Content-Disposition filename pattern).
- For CSV: column header row matches the expected schema.
- For PDF: presence of required section labels (e.g., "Executive Summary",
  "Findings"), via `pdfminer.six` text extraction.
- For Excel: sheet names + header row, via `openpyxl`.

Live in `backend/tests/contract/test_export_<tool>_<format>.py`.

## Migration

| Sprint | Scope |
|--------|-------|
| **748** | Create `backend/export/mappers/` package. Refactor `routes/export_diagnostics.py` handlers (10 endpoints) to use mappers. Remove inline loops/formatting from routes. |
| **749** | Standardize all export endpoints to the skeleton above. Resolve `export_memos.py` dynamic-vs-explicit ambiguity. Add contract tests for every export endpoint. |

## Consequences

- ~49 export endpoints converge to one skeleton.
- Domain transformation logic becomes unit-testable without HTTP fixtures.
- `export_diagnostics.py` shrinks from ~800 lines to a thin controller layer.
- New export formats (e.g., ODS, JSONL) plug in as a new generator without
  touching mappers or routes — only the route's generator call changes.
- Schema regressions surface as contract-test failures, not as silent client
  breakage.

## Alternatives considered

- **Single layer (status quo + cleanup).** Rejected — doesn't address the
  duplication of domain logic across CSV/PDF/Excel siblings.
- **Generic ETL framework.** Rejected — over-abstraction for the actual
  transformation surface; mappers as plain functions are sufficient.
- **Mappers as classes (one per export).** Rejected — pure functions
  compose better with the existing `csv_export_handler` and PDF builders.

## See also

- `docs/03-engineering/export-pattern.md` (existing CSV-only pattern).
- `backend/shared/csv_export.py` (the canonical CSV generator).
- Sprint 748 + Sprint 749 entries in `tasks/todo.md`.
