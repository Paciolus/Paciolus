# Lessons Learned

> **Protocol:** After ANY correction from the CEO or discovery of a better pattern, document it here. Review at session start.

---

## Template

When adding a lesson, use this format:

```
### [DATE] — [Short Title]
**Trigger:** What happened that led to this lesson?
**Pattern:** What's the rule or principle to follow?
**Example:** Concrete example of the right way to do it.
```

---

## Lessons

### 2026-02-01 — Audit Infrastructure First
**Trigger:** Project audit scored 2.9/5 due to missing workflow artifacts (todo.md, lessons.md, git history).
**Pattern:** Before diving into features, establish the tracking infrastructure. Good code without documentation is hard to maintain.
**Example:** Day 7 directive prioritized workflow setup over new features.

---

### 2026-02-01 — datetime.utcnow() is Deprecated
**Trigger:** Running pytest revealed 212 deprecation warnings about `datetime.utcnow()` in security_utils.py and audit_engine.py.
**Pattern:** Python 3.12+ deprecates `datetime.datetime.utcnow()`. Use timezone-aware objects instead: `datetime.datetime.now(datetime.UTC)`.
**Example:**
```python
# OLD (deprecated)
from datetime import datetime
timestamp = datetime.utcnow().isoformat()

# NEW (correct)
from datetime import datetime, UTC
timestamp = datetime.now(UTC).isoformat()
```
**Action:** Schedule fix for Day 9 or as technical debt cleanup.

---

### 2026-02-01 — Test Fixtures Make Tests Readable
**Trigger:** Writing test_audit_engine.py required generating various CSV test data repeatedly.
**Pattern:** Use pytest fixtures to create reusable test data. Name fixtures descriptively (e.g., `small_balanced_csv`, `abnormal_balances_csv`).
**Example:**
```python
@pytest.fixture
def small_balanced_csv() -> bytes:
    """Generate a small balanced CSV (10 rows)."""
    data = """Account Name,Debit,Credit
Cash,10000,
Revenue,,10000
"""
    return data.encode('utf-8')
```

---

### 2026-02-02 — Weighted Heuristics Beat Binary Keyword Matching
**Trigger:** Day 9 classification refactor revealed the old binary matching (keyword present = 100% confidence) missed many accounts and couldn't handle ambiguity.
**Pattern:** Use weighted keyword scoring with confidence thresholds. Multiple matching keywords increase confidence; single low-weight matches get flagged for review.
**Example:**
```python
# OLD (binary)
is_asset = any(keyword in account_lower for keyword in ASSET_KEYWORDS)

# NEW (weighted)
scores = {cat: 0.0 for cat in AccountCategory}
for rule in rules:
    if rule.keyword in account_lower:
        scores[rule.category] += rule.weight
# Select highest-scoring category with confidence threshold
```
**Result:** More accurate classification with explicit confidence levels (high/medium/low).

---

### 2026-02-02 — IP Documentation for Commercial Projects
**Trigger:** Day 9 directive required proving zero proprietary information was used in mapping logic.
**Pattern:** Create a logs/dev-log.md file documenting all sources (with licenses) for any module that could raise IP concerns. Include source attribution tables.
**Example:**
```markdown
| Pattern Set | Source | License/Status |
|-------------|--------|----------------|
| GAAP Categories | FASB Conceptual Framework | Public domain |
| GnuCash Schema | gnucash.org | GPL v2 |
```
**Action:** Make this standard for all commercial-sensitive features.

---

### 2026-02-02 — Column Detection vs Account Classification: Two Different Problems
**Trigger:** Day 9.2 directive initially seemed like extending Day 9's account classification, but it's actually a separate concern.
**Pattern:** Distinguish between:
1. **Column Detection** (Day 9.2): Which CSV column is Debit? Credit? Account Name?
2. **Account Classification** (Day 9): What type is "Cash"? Asset. What type is "Loan Payable"? Liability.

These require different:
- Detection logic (pattern matching on column NAMES vs. pattern matching on row VALUES)
- UI flows (modal before results vs. dropdowns in results)
- API parameters (column_mapping vs. account_type_overrides)
**Example:**
```python
# Column Detection (column headers)
DEBIT_PATTERNS = [r"^debit$", r"^dr$", r"debit\s*amount"]

# Account Classification (row values)
ASSET_KEYWORDS = [("cash", 0.95), ("receivable", 0.90), ("inventory", 0.85)]
```
**Action:** Keep these systems separate; don't conflate column identification with account classification.

---

### 2026-02-02 — Modal Triggers Require State Coordination
**Trigger:** Implementing ColumnMappingModal required careful state coordination: pending detection info, modal visibility, user mapping, and file reference all need to stay in sync.
**Pattern:** When a modal interrupts a flow:
1. Store "pending" state that triggered the modal
2. Reset main flow status (e.g., `setAuditStatus('idle')`) so user isn't stuck
3. On confirm: use pending data + user input to resume flow
4. On cancel: clear all pending state
**Example:**
```typescript
// Trigger: API response requires mapping
if (data.column_detection?.requires_mapping && !columnMapping) {
  setPendingColumnDetection(data.column_detection) // Store pending
  setShowColumnMappingModal(true)                   // Show modal
  setAuditStatus('idle')                            // Reset flow
  return                                            // Don't continue
}

// On confirm: resume with user input
const handleConfirm = (mapping: ColumnMapping) => {
  setShowColumnMappingModal(false)
  runAudit(selectedFile, threshold, false, mapping) // Resume
}
```

---

### 2026-02-02 — framer-motion Requires Type Assertions in Strict Mode
**Trigger:** Day 10 build failed with TypeScript errors on framer-motion variant definitions. Error: `Type 'string' is not assignable to type 'AnimationGeneratorType | undefined'`.
**Pattern:** TypeScript strict mode treats string literals as `string`, but framer-motion's `Variants` type expects literal types like `'spring'` or `'easeInOut'`. Use `as const` assertions.
**Example:**
```typescript
// WRONG: TypeScript infers 'spring' as string
const variants = {
  visible: {
    transition: { type: 'spring', ease: 'easeInOut' }
  }
}

// CORRECT: Use `as const` to preserve literal type
const variants = {
  visible: {
    transition: { type: 'spring' as const, ease: 'easeInOut' as const }
  }
}
```
**Action:** Always use `as const` for framer-motion transition properties in strict TypeScript.

---

### 2026-02-02 — Premium Restraint: Fintech Alert Design
**Trigger:** Day 10 directive called for "premium restraint" in Clay Red alert design—not overwhelming solid red blocks.
**Pattern:** In fintech UI, error/alert states should be visible but not alarming. Use:
1. **Left-border accent** instead of full background color
2. **Subtle glow effects** (low opacity, pulsing) instead of bright colors
3. **Typography hierarchy** to draw attention to content, not color
**Example:**
```tsx
// WRONG: Overwhelming solid red
className="bg-red-500 text-white p-4"

// CORRECT: Premium restraint
className="border-l-4 border-l-clay-500 bg-obsidian-800/50"
// Plus subtle glow:
boxShadow: '0 0 8px 2px rgba(188, 71, 73, 0.15)'
```
**Result:** Professional fintech aesthetic that communicates urgency without causing alarm fatigue.

---

### 2026-02-02 — Two-Phase Flow Pattern for Complex Uploads
**Trigger:** Day 11 multi-sheet Excel support required user interaction before processing could begin.
**Pattern:** When an upload requires user decisions before processing, use a two-phase flow:
1. **Phase 1: Inspection** — Fast endpoint that extracts metadata without full processing
2. **User Decision** — Modal presents options based on inspection results
3. **Phase 2: Processing** — Full audit with user selections

This mirrors the Day 9.2 column detection pattern, creating consistent UX.
**Example:**
```typescript
// Phase 1: Inspect workbook
const response = await fetch('/audit/inspect-workbook', { method: 'POST', body: formData })
const workbookInfo = await response.json()

// Decision point: Show modal if needed
if (workbookInfo.requires_sheet_selection) {
  setShowWorkbookInspector(true)  // User picks sheets
  return
}

// Phase 2: Audit with selections
const auditFormData = new FormData()
auditFormData.append('selected_sheets', JSON.stringify(userSelectedSheets))
await fetch('/audit/trial-balance', { method: 'POST', body: auditFormData })
```
**Benefit:** Consistent UX pattern: inspect → decide → process. Reusable for future features (batch upload, PDF options, etc.).

---

### 2026-02-02 — Vault Metaphor for Authentication UI
**Trigger:** Day 13 authentication design needed to balance security messaging with the Zero-Storage promise.
**Pattern:** Use the "Obsidian Vault" visual metaphor to communicate:
1. **Security** — Lock/key iconography for trust
2. **Zero-Storage Promise** — Badge with tooltip explaining financial data stays in-memory
3. **Premium Feel** — Consistent Oat & Obsidian palette (sage for actions, clay for errors)

The "Enter Vault" / "Create Your Vault" language reinforces that credentials are stored securely while trial balance data never persists.
**Example:**
```tsx
// Header with vault icon + Zero-Storage badge
<div className="w-20 h-20 rounded-2xl bg-obsidian-700 border border-obsidian-500">
  <svg>/* lock icon */</svg>
</div>
<h1>Obsidian Vault</h1>

// Zero-Storage badge with tooltip
<div className="flex items-center gap-2">
  <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
  <span>Zero-Storage Promise</span>
  <Tooltip>Your financial data is never stored...</Tooltip>
</div>
```
**Result:** Users understand both the security and privacy aspects of the platform.

---

### 2026-02-02 — Auth Context Should Be Root-Level Provider
**Trigger:** Day 13 auth implementation required wrapping the entire app with AuthProvider, but Next.js App Router layout.tsx is a server component.
**Pattern:** Create a separate `providers.tsx` client component that wraps all client-side context providers. Import this into the server-side layout.tsx.
**Example:**
```typescript
// app/providers.tsx (client component)
'use client'
import { AuthProvider } from '@/context/AuthContext'
export function Providers({ children }) {
  return <AuthProvider>{children}</AuthProvider>
}

// app/layout.tsx (server component)
import { Providers } from './providers'
export default function RootLayout({ children }) {
  return (
    <html><body>
      <Providers>{children}</Providers>
    </body></html>
  )
}
```
**Benefit:** Clean separation between server and client components while maintaining global auth state.

---

### 2026-02-02 — Zero-Storage Exception for Auth: Document the Boundary
**Trigger:** Day 13 required adding a SQLite database for user credentials, which seemed to violate Zero-Storage policy.
**Pattern:** When adding exceptions to a strict policy (like Zero-Storage), document explicitly:
1. What IS stored (user email, password hash, timestamps)
2. What is NEVER stored (financial data, audit results, trial balances)
3. Why the exception is necessary (authentication requires persistence)
**Example:** In the User model docstring and in logs/dev-log.md, explicitly list the boundary conditions.
**Benefit:** Future developers understand the policy isn't "no storage ever" but "no financial data storage ever."

---

### 2026-02-02 — Hybrid Storage Pattern: Backend Primary with localStorage Fallback
**Trigger:** Day 14 history page had existing localStorage implementation (from designer mockup), but the directive required SQLite storage via backend API.
**Pattern:** Instead of choosing one over the other, use a hybrid approach:
1. **Authenticated users** → Fetch from backend API (authoritative source)
2. **Anonymous users** → Fall back to localStorage (graceful degradation)
3. **API failure** → Fall back to localStorage (resilient)

This respects both the Zero-Storage philosophy (localStorage is user-controlled) and the authenticated experience (backend persistence).
**Example:**
```typescript
if (isAuthenticated && token) {
  // Primary: Backend API
  const response = await fetch('/activity/history', {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  if (response.ok) return response.json()
  // Fallback on error
}
// Fallback: localStorage
const stored = localStorage.getItem(HISTORY_KEY)
return stored ? JSON.parse(stored) : []
```
**Benefit:** Best of both worlds—reliable backend storage when available, graceful fallback when not.

---

### 2026-02-02 — GDPR/CCPA Compliance: Aggregate Metadata Only
**Trigger:** Day 14 activity logging needed to store audit history without violating Zero-Storage or privacy laws.
**Pattern:** Design logging to store only aggregate metadata that cannot identify individuals or reveal business secrets:
1. **Hash sensitive identifiers** — SHA-256 for filenames (non-reversible)
2. **Counts, not details** — `anomaly_count: 5`, not specific anomaly descriptions
3. **Totals, not transactions** — `total_debits: 50000`, not line items
4. **User-controlled deletion** — Provide `/activity/clear` endpoint

Document explicitly in dev-log.md what IS stored vs what is NEVER stored.
**Example:**
```markdown
| What IS Stored | What is NEVER Stored |
|----------------|---------------------|
| filename_hash (SHA-256) | Original filename |
| anomaly_count | Specific anomaly details |
| total_debits | Individual transactions |
```
**Benefit:** Defensible compliance position—can show regulators exactly what data is captured.

---

### 2026-02-03 — ReportLab Style Collision: Get-or-Create Pattern
**Trigger:** Sprint 15 bug report: "Style BodyText already defined" error when generating multiple PDFs.
**Pattern:** ReportLab's `getSampleStyleSheet()` includes default styles like 'BodyText'. Calling `styles.add()` with the same name raises an error. Use a "get-or-create" pattern:
1. Check if style name exists in `styles.byName`
2. If exists, update the existing style's attributes
3. If not, add new style
**Example:**
```python
def _add_or_replace_style(styles, style: ParagraphStyle) -> None:
    """Add or replace a style in the stylesheet."""
    if style.name in [s.name for s in styles.byName.values()]:
        existing = styles[style.name]
        for attr in ['fontName', 'fontSize', 'textColor', ...]:
            if hasattr(style, attr) and getattr(style, attr) is not None:
                setattr(existing, attr, getattr(style, attr))
    else:
        styles.add(style)
```
**Benefit:** PDF generation works reliably on repeated requests.

---

### 2026-02-03 — useEffect Referential Loop: Deep Comparison Pattern
**Trigger:** Sprint 15 bug report: AuditResults component re-audits on every render, causing jittery UI.
**Pattern:** When `useEffect` dependencies include memoized functions (from `useCallback`) that depend on context objects, the effect may re-run even if the actual values haven't changed. Fix with:
1. Use `useRef` to track previous values
2. Compare prev vs current before triggering side effects
3. Only proceed if actual data changed (not just references)
**Example:**
```typescript
const prevThresholdRef = useRef<number>(threshold)

useEffect(() => {
  // Skip if value hasn't actually changed
  if (prevThresholdRef.current === threshold) {
    return
  }
  prevThresholdRef.current = threshold

  // Only then trigger the effect
  runAudit(...)
}, [threshold, ...otherDeps])
```
**Benefit:** Prevents infinite loops and unnecessary API calls from reference changes.

---

### 2026-02-03 — Tier 1 Skeleton Loaders: Layout Stability
**Trigger:** Sprint 15 UI jitter during recalculation caused by content appearing/disappearing.
**Pattern:** When content changes size during loading, use skeleton loaders that match the expected layout:
1. **Shimmer effect** — Subtle animation indicating activity
2. **Fixed dimensions** — Match skeleton size to actual content
3. **Show skeleton instead of fading content** — `hidden` class vs `opacity` for stability
**Example:**
```css
@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
```
```tsx
{isLoading && (
  <div className="w-16 h-16 rounded-full bg-obsidian-700 animate-pulse relative overflow-hidden">
    <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite]
                    bg-gradient-to-r from-transparent via-obsidian-600/50 to-transparent" />
  </div>
)}
{!isLoading && <ActualContent />}
```
**Benefit:** UI remains stable during loading, no jarring layout shifts.

---

### 2026-02-03 — Multi-Tenant Data Isolation: Query-Level Filtering
**Trigger:** Sprint 16 client management required ensuring users can only access their own clients.
**Pattern:** Enforce data isolation at the database query level, not just application logic:
1. **Always filter by user_id** — Every query for user-scoped data must include the user ID filter
2. **Use foreign keys** — Define `user_id` as a foreign key to enforce referential integrity
3. **Don't trust client-side filtering** — Server must validate ownership before returning data
**Example:**
```python
# CORRECT: Filter at query level
def get_client(self, user_id: int, client_id: int) -> Optional[Client]:
    return self.db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == user_id  # Multi-tenant isolation
    ).first()

# WRONG: Fetch then check (vulnerable to timing attacks)
def get_client_wrong(self, user_id: int, client_id: int):
    client = self.db.query(Client).filter(Client.id == client_id).first()
    if client.user_id != user_id:  # Too late, already fetched
        return None
    return client
```
**Benefit:** True multi-tenant isolation — impossible to access another user's data through the API.

---

### 2026-02-03 — Zero-Storage Boundary: Metadata vs Transaction Data
**Trigger:** Sprint 16 required adding client storage while maintaining Zero-Storage policy.
**Pattern:** Clearly document what IS stored vs what is NEVER stored for any database table:
1. **Create a data boundary table** — Explicit list of stored vs excluded fields
2. **Document in both code and dev-log** — Model docstrings + IP documentation
3. **Name tables to reflect their purpose** — "clients" not "client_data" to avoid implying financial content
**Example from Client model:**
```python
"""
DATA BOUNDARY:
| What IS Stored          | What is NEVER Stored         |
|-------------------------|------------------------------|
| Client name             | Trial balance data           |
| Industry classification | Transaction details          |
| Fiscal year end         | Account balances             |
| Created/updated times   | Audit results                |
"""
```
**Benefit:** Clear boundaries prevent scope creep and maintain compliance promises.

---

### 2026-02-03 — ReportLab Page Callbacks for Repeating Elements
**Trigger:** Sprint 18 required a legal disclaimer to appear on EVERY page of the PDF, not just the final footer section.
**Pattern:** ReportLab's `SimpleDocTemplate.build()` accepts `onFirstPage` and `onLaterPages` callbacks that run for each page. Use canvas drawing methods in these callbacks to add repeating elements:
1. **Page numbers, headers, footers** — Draw directly on canvas
2. **Legal disclaimers** — Position at bottom with `drawCentredString()`
3. **Use saveState/restoreState** — Prevent styling from affecting flowables
**Example:**
```python
def _add_page_footer(self, canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.HexColor('#616161'))
    canvas.drawCentredString(page_width / 2, 0.5 * inch, "Legal disclaimer text...")
    canvas.restoreState()

# In generate():
doc.build(story, onFirstPage=self._add_page_footer, onLaterPages=self._add_page_footer)
```
**Benefit:** Consistent branding/legal text on every page, required for professional reports.

---

### 2026-02-03 — ReportLab Paragraph Objects for Text Wrapping in Tables
**Trigger:** Sprint 18 PDF generation cut off long anomaly descriptions in table cells.
**Pattern:** ReportLab Table cells with plain strings truncate at cell width. Wrap text in Paragraph objects for proper wrapping:
1. **Create a cell-specific ParagraphStyle** — Smaller font, tight leading
2. **Wrap cell content** — `Paragraph(text, cell_style)` instead of raw string
3. **Set VALIGN to TOP** — Better readability for wrapped content
**Example:**
```python
# Create cell style
cell_style = ParagraphStyle('TableCell', fontName='Helvetica', fontSize=8, leading=10)

# Wrap text in Paragraph
issue = Paragraph(ab.get('issue', ''), cell_style)
data.append([account, type, issue, amount])  # issue is now a Paragraph

# Table style: TOP alignment for wrapped text
('VALIGN', (0, 0), (-1, -1), 'TOP'),
```
**Benefit:** Long descriptions wrap properly, no text cutoff, professional-quality reports.

---

### 2026-02-03 — Terminology Changes: API Stability vs UI Evolution
**Trigger:** Sprint 18 renamed "Audit" to "Diagnostic" but needed to preserve backwards compatibility.
**Pattern:** When rebranding terminology, separate API stability from UI updates:
1. **Keep API endpoints unchanged** — `/audit/trial-balance` still works
2. **Update UI labels freely** — "Export Diagnostic Summary" replaces "Download Report"
3. **Document the mapping** — Users know the old terms still work programmatically
**Example:**
```
API Route: /audit/trial-balance (UNCHANGED for backwards compatibility)
UI Label: "Diagnostic Intelligence Zone" (NEW)
PDF Title: "Paciolus Diagnostic Summary" (NEW)
```
**Benefit:** Existing integrations don't break, but UI reflects updated brand positioning.

---

### 2026-02-03 — Zero-Storage Variance: Aggregate Metadata Comparison
**Trigger:** Sprint 19 required comparing current diagnostic runs against previous runs to show variance (period-over-period changes).
**Pattern:** Maintain Zero-Storage by comparing only aggregate totals, never raw transaction data:
1. **Store category totals** — DiagnosticSummary holds total_assets, total_liabilities, etc. (8 fields)
2. **Store calculated ratios** — Cached ratio values for quick comparison
3. **Link to client_id** — Enable client-specific trend tracking
4. **Never store account names or transactions** — The "what" is never persisted
**Example:**
```python
# What IS stored (DiagnosticSummary)
class DiagnosticSummary(Base):
    client_id = Column(Integer, ForeignKey("clients.id"))
    total_assets = Column(Float)
    current_ratio = Column(Float)  # Cached for trend comparison

# What is NEVER stored
# - Account names
# - Individual balances
# - Transaction details
# - Raw trial balance data
```
**Benefit:** Enables "Variance Intelligence" (show +5% assets since last run) while maintaining Zero-Storage promise for actual financial data.

---

### 2026-02-03 — Financial Ratio Health Thresholds: Standard GAAP Benchmarks
**Trigger:** Sprint 19 ratio engine needed to classify ratios as healthy/warning/concern without being prescriptive.
**Pattern:** Use generally accepted financial benchmarks with conservative thresholds:
1. **Current Ratio** — ≥1.5 healthy, ≥1.0 warning, <1.0 concern
2. **Quick Ratio** — ≥1.0 healthy, ≥0.5 warning, <0.5 concern
3. **Debt-to-Equity** — ≤1.0 healthy, ≤2.0 warning, >2.0 concern
4. **Gross Margin** — ≥40% healthy, ≥20% warning, <20% concern (varies by industry)
**Example:**
```python
# Interpretation with health status
if current_ratio >= 1.5:
    health = 'healthy'
    interpretation = 'Strong liquidity position'
elif current_ratio >= 1.0:
    health = 'warning'
    interpretation = 'Adequate liquidity, monitor closely'
else:
    health = 'concern'
    interpretation = 'May face short-term payment challenges'
```
**Note:** These are starting points; industry-specific thresholds can be added later via client settings.

---

### 2026-02-03 — Deep-Hash Comparison for UI Stability

**Trigger:** Sprint 20 directive required a "state guard that compares the previous audit input hash with the current one before calling the backend" to prevent unnecessary re-audits.

**Pattern:** When multiple parameters can trigger an effect (threshold, mapping, sheets), use a composite hash to detect actual changes:

1. **Compute a deterministic hash** of all relevant parameters
2. **Store the hash in a ref** to persist across renders
3. **Compare hashes before triggering effects** to skip if unchanged
4. **Update hash ref after effect triggers** to stay in sync

This is superior to individual value checks because:
- A single hash comparison is faster than multiple deep comparisons
- Hash naturally handles complex nested objects
- Reduces the number of refs needed
- Belt-and-suspenders with individual checks for debugging

**Example:**
```typescript
const computeInputHash = (threshold, mapping, sheets) => {
  const inputState = {
    t: threshold,
    m: mapping ? JSON.stringify(mapping) : null,
    s: sheets ? sheets.sort().join('|') : null,
  }
  const str = JSON.stringify(inputState)
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return hash.toString(36)
}

// In useEffect:
const currentHash = computeInputHash(threshold, mapping, sheets)
if (prevHashRef.current === currentHash) {
  return // Skip, nothing changed
}
prevHashRef.current = currentHash
// ... trigger effect
```

**Benefit:** Eliminates false-positive re-renders and unnecessary API calls while maintaining predictable UI behavior. The Tier 1 Skeleton Loader remains visible during legitimate recalculations.

---

### 2026-02-03 — Dynamic Materiality: Formula Storage vs Data Storage

**Trigger:** Sprint 21 required storing materiality formulas while maintaining Zero-Storage for financial data.

**Pattern:** Separate what IS stored (the formula configuration) from what is NEVER stored (the data it operates on):

1. **Store the formula** — Type (fixed, percentage_of_revenue, etc.), value, min/max thresholds
2. **Never store the calculation context** — Total revenue, total assets, total equity
3. **Evaluate at runtime** — MaterialityCalculator takes formula + ephemeral data → returns threshold
4. **Priority chain** — Session override → Client settings → Practice settings → System default

**Example:**
```python
# What IS stored in database (formula configuration)
class MaterialityFormula(BaseModel):
    type: MaterialityFormulaType  # 'fixed', 'percentage_of_revenue', etc.
    value: float                  # 500 or 0.5 (percentage)
    min_threshold: Optional[float]
    max_threshold: Optional[float]

# What is NEVER stored (runtime evaluation)
threshold = MaterialityCalculator.calculate(
    config=MaterialityConfig(formula=stored_formula),
    total_revenue=ephemeral_data.revenue,  # From uploaded file, never persisted
    total_assets=ephemeral_data.assets,    # From uploaded file, never persisted
)
```

**Frontend Pattern:** Prepopulate UI from settings while allowing session-level override:
```typescript
useEffect(() => {
  if (practiceSettings && !thresholdInitialized) {
    const formula = practiceSettings.default_materiality
    if (formula?.type === 'fixed') {
      setMaterialityThreshold(formula.value)  // Prepopulate slider
    }
    setThresholdInitialized(true)
  }
}, [practiceSettings])
```

**Benefit:** Users can define persistent materiality strategies (e.g., "0.5% of Revenue") without Paciolus ever storing their actual revenue figures. The formula is configuration; the data is ephemeral.

---

### 2026-02-04 — Contextual Parameter Tuning: Professional Decision Support UX

**Trigger:** Sprint 22 required a "Sensitivity Toolbar" for real-time threshold adjustment without leaving the results view.

**Pattern:** When building analytical tools for professionals, embed parameter controls alongside results rather than hiding them in settings:

1. **Display current values prominently** — Show "Current Threshold: $5,000" in the results view
2. **Enable inline editing** — Click to edit without navigation
3. **Provide immediate feedback** — Changes trigger recalculation with visual loading state
4. **Use visual metaphors** — "Control Surface" aesthetic communicates adjustability

This is distinct from traditional "settings → run → view" workflows because it respects the user's focus on analytical output while providing direct control.

**Example:**
```tsx
// SensitivityToolbar placed directly in results view
<SensitivityToolbar
  threshold={materialityThreshold}
  displayMode={displayMode}
  onThresholdChange={setMaterialityThreshold}  // Triggers hash-guarded recalc
  onDisplayModeChange={handleDisplayModeChange}
  disabled={isRecalculating}
/>
```

**Benefit:** Users can iterate quickly on analytical parameters without losing context. The "Control Surface" metaphor communicates that these are dials they control, not fixed system values.

---

### 2026-02-04 — Ghost Click Prevention: Conditional Input Activation

**Trigger:** Sprint 22 bug report: Clicking UI elements inside the dropzone (e.g., "Upload another file" button) triggered the file picker.

**Pattern:** File inputs that cover their container using `position: absolute; inset: 0` can capture clicks intended for other elements. Fix by conditionally disabling the input when not in idle state:

```tsx
<input
  type="file"
  className={`... ${
    auditStatus === 'idle' ? 'cursor-pointer' : 'pointer-events-none'
  }`}
  tabIndex={auditStatus === 'idle' ? 0 : -1}
/>
```

Key points:
1. **pointer-events-none** prevents the input from capturing clicks
2. **tabIndex={-1}** removes it from keyboard navigation when disabled
3. **Conditional cursor** provides visual feedback about interactivity

**Benefit:** File input is only interactive when the user is actually in a state to upload a file. Prevents accidental file picker triggers when viewing results.

---

*Add new lessons below this line. Newest at bottom.*

---

### Sprint 23 Lesson: Brand-Integrated Marketing Components

**Date:** 2026-02-04
**Sprint:** 23 - The Marketing Front & Brand Hardening
**Severity:** Best Practice

**Trigger:** CEO directive to redesign landing page with "Surgical Diagnostic" value proposition and three pillars marketing section.

**Pattern:** Create dedicated marketing components in `frontend/src/components/marketing/` that encapsulate brand messaging with consistent Oat & Obsidian styling:

```tsx
// FeaturePillars.tsx - Self-contained brand pillars
const pillars = [
  { title: 'Zero-Knowledge Security', icon: ShieldIcon, description: '...' },
  { title: 'Automated Sensitivity', icon: TargetIcon, description: '...' },
  { title: 'Professional-Grade Exports', icon: DocumentIcon, description: '...' },
];

// ProcessTimeline.tsx - Visual transformation flow
// Upload → Analyze → Export with scroll-triggered animations
```

Key points:
1. **Component isolation** - Marketing copy changes don't affect core app logic
2. **Reusable animations** - Tier 1 staggered entrance (60ms delay) applied consistently
3. **Responsive by default** - Grid layouts adapt (3-col desktop, 1-col mobile)
4. **useInView hook** - Scroll-triggered animations for engagement

**Benefit:** Marketing sections can be updated independently without risk to diagnostic functionality. Brand consistency enforced through shared theme tokens.

---

### Sprint 23 Lesson: framer-motion Type Assertions (Recurring)

**Date:** 2026-02-04
**Sprint:** 23 - The Marketing Front & Brand Hardening
**Severity:** TypeScript Compatibility

**Trigger:** Build error in CreateClientModal.tsx: `Type 'string' is not assignable to type 'AnimationGeneratorType | undefined'`

**Pattern:** When defining framer-motion animation variants with transition objects, TypeScript infers `type: 'spring'` as `string` instead of the literal type. Always use `as const`:

```tsx
// ❌ Causes TypeScript error
const modalVariants = {
  visible: {
    transition: { type: 'spring', stiffness: 300, damping: 25 },
  },
};

// ✅ Correct pattern
const modalVariants = {
  visible: {
    transition: { type: 'spring' as const, stiffness: 300, damping: 25 },
  },
};
```

**Recurrence Note:** This is the same pattern documented in Sprint 22 for SensitivityToolbar. Any file using framer-motion transition types should be audited for this pattern.

**Affected Files (audited):**
- `SensitivityToolbar.tsx` - Fixed in Sprint 22
- `CreateClientModal.tsx` - Fixed in Sprint 23
- `ProfileDropdown.tsx` - Already using `as const`

**Benefit:** Prevents mysterious build failures when framer-motion's strict typing conflicts with TypeScript's default inference.

---

### Sprint 24 Lesson: Multi-Stage Docker Builds

**Date:** 2026-02-04
**Sprint:** 24 - Production Deployment Prep (FINAL)
**Severity:** Best Practice

**Trigger:** Need for production-ready Docker images with minimal size and security hardening.

**Pattern:** Use multi-stage Docker builds to separate build dependencies from runtime:

```dockerfile
# Stage 1: Dependencies (large, has build tools)
FROM node:20-alpine AS deps
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Builder (compiles application)
FROM node:20-alpine AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Runner (minimal, production only)
FROM node:20-alpine AS runner
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
```

Key points:
1. **Separate stages** — Build tools don't ship to production
2. **Minimal final image** — Only runtime dependencies included
3. **Non-root users** — Always create and use non-root users in production
4. **Health checks** — Include health check endpoints for load balancers

**Benefit:** Smaller images (often 10x smaller), reduced attack surface, faster deployments, better security posture.

---

### Sprint 24 Lesson: Next.js Standalone Output for Docker

**Date:** 2026-02-04
**Sprint:** 24 - Production Deployment Prep (FINAL)
**Severity:** Configuration Required

**Trigger:** Frontend Dockerfile requires standalone Next.js output for minimal production builds.

**Pattern:** Configure `next.config.js` with `output: 'standalone'`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,
}

module.exports = nextConfig
```

**What standalone does:**
1. Creates a self-contained production build
2. Copies only necessary `node_modules` files
3. Generates a `server.js` that can run independently
4. Eliminates need for full `node_modules` in production

**Dockerfile usage:**
```dockerfile
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
CMD ["node", "server.js"]
```

**Benefit:** Production Docker images can be ~100MB instead of ~1GB with full node_modules.

---

### Audit Lesson: Commit Frequency Matters

**Date:** 2026-02-04
**Sprint:** Audit Review
**Severity:** Process Improvement

**Trigger:** Project audit scored 4/5 on A6 (Autonomous Bug Fixing) due to limited git history — only 3 commits existed for 24 sprints of development work.

**Pattern:** Each sprint should result in at least one atomic commit. Git history is evidence of work and enables:
- Tracking changes over time
- Rolling back specific features
- Understanding development cadence
- Code review by others

**Commit Convention:**
```bash
# Format
git commit -m "Sprint X: Brief Description"

# Examples
git commit -m "Sprint 24: Production Deployment Prep - Dockerfiles and DEPLOYMENT.md"
git commit -m "Sprint 23: Marketing Components - FeaturePillars and ProcessTimeline"

# Stage specific files (not git add -A)
git add backend/Dockerfile frontend/Dockerfile docker-compose.yml DEPLOYMENT.md
```

**Post-Sprint Checklist Added:**
1. Run verification tests (`npm run build`, `pytest`)
2. Update documentation (todo.md, lessons.md)
3. Create atomic commit with sprint reference
4. Verify commit with `git log -1`

**Benefit:** Proper git history enables better project tracking, easier debugging, and professional-grade development practices.

---

### Audit Lesson: Verification Before Declaring Complete

**Date:** 2026-02-04
**Sprint:** Audit Review
**Severity:** Process Improvement

**Trigger:** Project audit scored 4/5 on A4 (Verification Before Done) — while builds were verified, no evidence of automated test execution in recent sprints.

**Pattern:** Before marking ANY sprint complete:

```bash
# Frontend verification
cd frontend && npm run build

# Backend verification (if tests modified)
cd backend && pytest

# Check for Zero-Storage compliance
# - No new database columns storing financial data
# - No new files persisting uploaded content
# - Memory cleared after processing
```

**Added to CLAUDE.md Directive Protocol:**
- Step 3: Verification (BEFORE marking complete)
- Step 5: Git Commit (FINAL step)

**Benefit:** Ensures code quality is verified before declaring work complete. Prevents "works on my machine" issues.

---

### Sprint 25 Lesson: Multi-Agent Code Review Pattern

**Date:** 2026-02-04
**Sprint:** 25 - Stability & Code Quality
**Severity:** Best Practice

**Trigger:** CEO requested all agents from the agents folder review the codebase in their areas of expertise and cross-review recommendations.

**Pattern:** For comprehensive code reviews, use specialized agents with distinct perspectives:

1. **MarketScout** — User advocate, MVP risk, onboarding friction
2. **QualityGuardian** — Failure modes, test coverage, security vulnerabilities
3. **BackendCritic** — Architecture, complexity, performance bottlenecks
4. **FrontendExecutor** — Component structure, state management, TypeScript
5. **ProjectAuditor** — Documentation, consistency, deployment readiness
6. **FintechDesigner** — Brand consistency, accessibility, visual hierarchy

**Cross-Review Protocol:**
1. Launch agents in parallel to review their domains
2. Each agent uses "Steel-Man Counter-Arguments" to acknowledge why current approach might be valid
3. Synthesize recommendations identifying consensus (multiple agents agree) vs conflicts
4. Prioritize: Consensus items > High priority + Low effort > Strategic refactoring

**Example Priority Matrix:**
```
| Issue | Agents | Priority | Effort |
|-------|--------|----------|--------|
| God Class | Backend, Frontend | Critical | Large |
| Rate Limiting | Guardian, Backend | High | Medium |
| Error Boundaries | Guardian, Frontend | High | Small |
```

**Benefit:** Comprehensive review covering UX, security, architecture, code quality, design, and project health. Cross-agent consensus identifies highest-impact improvements.

---

### Sprint 25 Lesson: Stability Before Features

**Date:** 2026-02-04
**Sprint:** 25 - Stability & Code Quality
**Severity:** Strategic

**Trigger:** After multi-agent review, CEO chose "Stability first, then Code Quality" over user-facing features.

**Pattern:** When prioritizing improvements, use this order:
1. **Stability** — Error handling, rate limiting, validation, security hardening
2. **Code Quality** — Component extraction, duplication removal, type safety
3. **User Features** — New functionality, UX enhancements

Quick wins (< 2 hours, high impact) should be prioritized within each tier:
- README.md creation (15 min)
- File size validation (30 min)
- Error boundaries (1 hour)
- Color contrast fixes (1 hour)
- JWT hardening (30 min)
- Console.log stripping (30 min)

**Benefit:** A stable foundation makes future development faster and safer. Security and stability issues compound if deferred.

---

### Sprint 25 Lesson: Per-Sheet Column Detection for Multi-Sheet Audits

**Date:** 2026-02-04
**Sprint:** 25 - Foundation Hardening
**Severity:** Bug Fix

**Trigger:** Accounting expert audit identified that multi-sheet audits only detected columns from the first sheet, potentially causing silent data errors if sheets had different column layouts.

**Pattern:** When processing multi-sheet Excel files:
1. Run column detection independently for each sheet
2. Track per-sheet column mappings in the response
3. Generate warnings if column orders differ between sheets
4. Maintain backward compatibility by returning primary detection for existing consumers

**Implementation:**
```python
# Old (bug): Column detection only on first sheet
if first_col_detection is None:
    first_col_detection = auditor.get_column_detection()

# New (fix): Per-sheet detection with mismatch tracking
sheet_column_detections[sheet_name] = auditor.get_column_detection().to_dict()
if current_columns != first_sheet_columns:
    column_order_warnings.append(f"Sheet '{sheet_name}' differs...")
```

**API Response Additions:**
- `sheet_column_detections`: Dict mapping sheet name to detection result
- `column_order_warnings`: List of warning messages
- `has_column_order_mismatch`: Boolean flag for easy frontend detection

**Benefit:** Prevents silent data corruption when users upload multi-sheet workbooks with inconsistent column layouts. Users are warned of mismatches instead of getting incorrect results.

---

### Sprint 25 Lesson: Comprehensive Test Suites Before Feature Expansion

**Date:** 2026-02-04
**Sprint:** 25 - Foundation Hardening
**Severity:** Strategic

**Trigger:** Agent council consensus (5/6 agents) prioritized ratio engine test suite before adding new ratios (Sprint 26-27).

**Pattern:** Before expanding a module with new features:
1. Create comprehensive test suite for existing functionality
2. Cover edge cases: division-by-zero, negative values, boundary conditions
3. Test both calculable and uncalculable scenarios
4. Verify serialization/deserialization (to_dict, from_dict)

**Test Categories for Financial Calculations:**
```python
# 1. Happy path with realistic company data
def test_ratio_healthy_company(self, healthy_company_totals):
    ...

# 2. Edge case: denominator is zero
def test_ratio_zero_denominator(self, zero_values_totals):
    assert result.is_calculable is False
    assert result.value is None

# 3. Boundary conditions
def test_ratio_boundary_warning(self):
    # Test exact threshold values

# 4. Negative values
def test_ratio_negative_equity(self, negative_equity_totals):
    ...
```

**Benefit:** With 47 ratio engine tests in place, adding 4 new ratios (Sprint 26-27) becomes safe — any regression is immediately caught. Test-first reduces debugging time and prevents production bugs.
