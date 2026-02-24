# Report Standardization Module

> **Status:** Planned (Sprint 1) | **Spec:** `docs/03-product/REPORT_STANDARDS_SPEC.md` | **Migration Plan:** `docs/03-product/REPORT_INVENTORY_AND_MIGRATION_PLAN.md`

This package will be the single source of truth for all PDF report generation primitives in Paciolus. It replaces the current split between `pdf_generator.py` (classical styles) and `shared/memo_base.py` (memo styles).

---

## Proposed Module Map

```
backend/shared/report_standardization/
  __init__.py              # Public API re-exports
  colors.py                # Color constants (OBSIDIAN_DEEP, SAGE, CLAY, etc.)
  styles.py                # create_report_styles() — 14 unified style tokens
  builders.py              # Shared flowable builders (cover block, sections, signoff, etc.)
  page.py                  # Page header/footer canvas callbacks
  template.py              # ReportConfig dataclass + generate_report() orchestrator
  README.md                # This file
```

### Module Responsibilities

#### `colors.py`
Single source of truth for all PDF color constants. Replaces `ClassicalColors` in `pdf_generator.py` and inline hex values in `memo_base.py`.

```python
# Proposed exports
OBSIDIAN_DEEP: Color    # #1A1A1A — primary text
OBSIDIAN_600: Color     # #424242 — subsection headers
OBSIDIAN_500: Color     # #616161 — secondary text, footers
GOLD_INSTITUTIONAL: Color  # #B8934C — decorative rules
SAGE: Color             # #4A7C59 — positive indicators
CLAY: Color             # #BC4749 — negative indicators, banners
OATMEAL_PAPER: Color    # #F5F4F0 — banner backgrounds, row tint
LEDGER_RULE: Color      # #D5D0C8 — table row separators
```

#### `styles.py`
Defines `create_report_styles() -> dict[str, ParagraphStyle]` returning 14 named styles per the spec typography scale.

Replaces:
- `create_classical_styles()` (16 styles in `pdf_generator.py`)
- `create_memo_styles()` (11 styles in `memo_base.py`)

#### `builders.py`
Shared flowable builders. Each returns `list[Flowable]` that the caller appends to the story.

```python
# Proposed exports
def build_cover_block(title, client_name, date, reference, styles) -> list[Flowable]
def build_scope_section(items, period, source_doc, styles) -> list[Flowable]
def build_methodology_section(description, styles) -> list[Flowable]
def build_results_summary_section(metrics, styles) -> list[Flowable]
def build_proof_summary_section(proof_data, styles) -> list[Flowable]
def build_signoff(prepared_by, prepared_date, reviewed_by, styles) -> list[Flowable]
def build_intelligence_stamp(client_name, period, styles) -> list[Flowable]
def build_disclaimer(domain_noun, domain_verb, framework_ref, styles) -> list[Flowable]
def build_disclaimer_banner(text, styles) -> list[Flowable]
def build_section_header(number, title, styles) -> list[Flowable]
def create_leader_dots(key, value, width, styles) -> Paragraph
```

Also re-exports existing flowables:
- `DoubleRule` (gold double-line separator)
- `LedgerRule` (thin separator)

#### `page.py`
Canvas callback functions for `SimpleDocTemplate`.

```python
# Proposed exports
def on_first_page(canvas, doc, title, reference) -> None
def on_later_pages(canvas, doc, title, reference) -> None
```

Handles:
- Page header (title + reference on pages 2+)
- Page footer (page number + zero-storage line on all pages)

#### `template.py`
Config-driven report generation orchestrator.

```python
@dataclass
class ReportConfig:
    title: str
    ref_prefix: str
    domain_noun: str          # "memo" or "report"
    domain_verb: str          # e.g., "journal entry testing"
    framework_reference: str  # e.g., "ISA 530 / PCAOB AS 2315"
    has_proof_summary: bool
    has_disclaimer_banner: bool
    disclaimer_banner_text: str | None
    scope_builder: Callable | None        # Override default scope section
    extra_sections: list[Callable] | None # Domain-specific sections
    finding_formatter: Callable | None    # Override default finding rendering

def generate_report(config, data, client_name, period, ...) -> bytes:
    """Generate a PDF report from config + data. Returns PDF bytes."""
```

---

## Migration Path

Each existing generator will be migrated in the sprint sequence defined in the migration plan:

1. **Sprint 1:** Build this package (no generators changed yet)
2. **Sprints 2-5:** Migrate generators one category at a time
3. **Sprint 6:** Retire old modules (`create_classical_styles`, `create_memo_styles`)

During transition, both old and new modules coexist. Generators import from `report_standardization` as they are migrated.

---

## Deprecation Plan

After Sprint 6, these will be removed:

| Module | Function | Replaced By |
|--------|----------|-------------|
| `pdf_generator.py` | `create_classical_styles()` | `report_standardization.styles.create_report_styles()` |
| `pdf_generator.py` | `ClassicalColors` | `report_standardization.colors.*` |
| `shared/memo_base.py` | `create_memo_styles()` | `report_standardization.styles.create_report_styles()` |
| `shared/memo_base.py` | `build_memo_header()` | `report_standardization.builders.build_cover_block()` |

`shared/memo_base.py` and `shared/memo_template.py` will become thin re-export shims during transition, then be deleted in a cleanup sprint.
