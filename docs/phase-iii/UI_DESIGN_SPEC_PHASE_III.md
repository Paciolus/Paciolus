# Phase III UI Design Strategy: Advanced Diagnostic Signals
## 5 New Features for Paciolus Trial Balance Intelligence Platform

**Document Date:** 2026-02-04
**Design Lead:** Fintech Designer (Premium Restraint Aesthetic)
**Codebase:** Oat & Obsidian Theme (obsidian #212121, oatmeal #EBE9E4, clay #BC4749, sage #4A7C59)
**Animation Framework:** framer-motion (staggered 40-50ms delays)

---

## Executive Summary

These 5 features form an **"Advanced Risk Intelligence Layer"** that complements the existing Risk Dashboard (AnomalyCards). They provide forensic-level detection for sophisticated accounting issues:

- **Suspense Account Detector** → Flag operational chaos
- **Balance Sheet Equation Validator** → Catch fundamental errors
- **Concentration Risk Detector** → Identify asset/liability concentration
- **Rounding Anomaly Scanner** → Detect potential manipulation
- **Contra-Account Validator** → Validate asset-liability relationships

**Design Philosophy:** These features extend "Premium Restraint"—visual hierarchy through clay-red left borders, transparency tiers, and semantic grouping. NO full backgrounds. NO shocking colors. Trust the data.

---

## 1. Suspense Account Detector

**Purpose:** Flag accounts with names suggesting temporary/clearing nature that shouldn't carry balances.

### 1.1 Component Concept: "Alert Card" (New Component Type)

**Location in Results View:**
- Top-level card in the Risk Dashboard, BEFORE high-severity anomalies
- Positioned similarly to Risk Summary Header but independent
- Can be collapsed if resolved/dismissed

**Visual Hierarchy:**
```
[RISK DASHBOARD]
├── Risk Summary Header (existing)
├── ⚠️ SUSPENSE ACCOUNT ALERT [NEW] ← High prominence
├── Material Risks (high-severity anomalies)
└── Indistinct Items (collapsible)
```

### 1.2 Alert Card Structure

```
┌─────────────────────────────────────────────────────────┐
│ ⚠️  SUSPENSE ACCOUNT DETECTED                       [✕]  │ ← Left border clay-500
├─────────────────────────────────────────────────────────┤
│ Account: "Suspense - Clearing"                          │
│ Amount: $47,385.92 (Immaterial)                         │
│ Classification: Asset (Detected) / Unknown (Manual)    │
│                                                         │
│ Issue: This account typically carries NO balance       │
│ Recommendation: Reclassify or close before year-end    │
│                                                         │
│ [Reassign to Category ▼] [Archive] [Ignore]           │
└─────────────────────────────────────────────────────────┘
```

### 1.3 Styling Details

| Element | Style | Notes |
|---------|-------|-------|
| **Border** | `border-l-4 border-l-clay-500` | Left accent only |
| **Background** | `bg-obsidian-800/40` | Subtle, not aggressive |
| **Icon** | Warning triangle (⚠️) in `clay-400` | Fits severity hierarchy |
| **Title** | `font-serif font-semibold text-oatmeal-200` | Maintains brand consistency |
| **Action Buttons** | `bg-obsidian-700 hover:bg-obsidian-600` | Secondary style, not primary |
| **Close Button** | `text-oatmeal-500 hover:text-oatmeal-300` | Subtle dismiss (keeps in history) |

### 1.4 Micro-interactions

- **Entrance:** Stagger from top-down with AnomalyCards (40ms delay, spring animation)
- **Hover State:** Subtle border highlight: `border-opacity-75` on hover
- **Action Buttons:**
  - Reassign dropdown: Shows account type selector (reuse AccountTypeDropdown)
  - Archive: Transitions to opacity-50 + strikethrough text, stays visible
  - Ignore: Removes temporarily from view (stored in session state)
- **No Pulsing/Glow:** Unlike AnomalyCard high-severity glow, this is static but prominent

### 1.5 Data Integration

**Backend Provides:**
```python
{
  "account": "Suspense - Clearing",
  "amount": 47385.92,
  "detected_type": "asset",
  "confidence": 0.95,
  "reason": "Account name contains 'suspense' or 'clearing'"
}
```

---

## 2. Balance Sheet Equation Validator

**Purpose:** Verify A = L + E. If violated, flag with % deviation.

### 2.1 Component Concept: "Equation Status Badge" (New Component Type)

**Location in Results View:**
- Placed in **KeyMetricsSection footer** (after category totals, before advanced ratios toggle)
- OR as standalone card above Risk Dashboard if deviation > 5%
- Minimal by default, expands on severe mismatches

**Visual Hierarchy:**
```
[KEY METRICS SECTION]
├── Core 4 Ratios (grid)
├── Advanced Ratios Toggle
├── Category Totals Row (existing)
└── Equation Status [NEW] ← Green/Red badge, or card if critical
```

### 2.2 Badge/Card Variants

**Case A: Balanced (deviation ≤ 0.01%)**
```
✓ Balance Sheet Balanced | A = L + E
Assets: $5,234,600 | Liabilities + Equity: $5,234,600
```
- Style: `bg-sage-500/10 border-sage-500/30 text-sage-300`
- Icon: Checkmark (✓)
- No details needed

**Case B: Minor Rounding (0.01% < deviation ≤ 1%)**
```
⚠️ Balance Sheet Equation — Rounding Variance
Assets: $5,234,602.34 | Liabilities + Equity: $5,234,600.00
Variance: $2.34 (0.00004%)
```
- Style: `bg-oatmeal-500/10 border-oatmeal-500/30 text-oatmeal-300`
- Icon: Info (ℹ️)
- Shows variance amount in monospace

**Case C: Significant Error (deviation > 1%)**
```
┌─────────────────────────────────────┐
│ ✗ BALANCE SHEET EQUATION ERROR      │ ← Standalone card
│ Assets:             $5,234,600.00  │
│ Liabilities:        $3,100,000.00  │
│ Equity:             $1,800,000.00  │
│ Liabilities + Equity: $4,900,000.00│
│                                     │
│ Shortfall: $334,600 (6.39%)        │ ← Clay red
│ Likely Cause: Missing equity account or hidden liability
│                                     │
│ [Review Trial Balance] [Export Log] │
└─────────────────────────────────────┘
```
- Style: `border-l-4 border-l-clay-500` (full card)
- Background: `bg-obsidian-800/40`
- Error amount: `text-clay-400 font-mono`
- Action buttons: Link to column mapping or raw data export

### 2.3 Styling Details

| Element | Style | Notes |
|---------|-------|-------|
| **Badge Container** | `inline-flex items-center gap-2 px-3 py-1.5 rounded-full` | Matches status-pill pattern |
| **Card Border** | `border-l-4 border-l-clay-500` (severe only) | Follows Premium Restraint |
| **Icon Sizing** | `w-4 h-4` for badge, `w-5 h-5` for card | Scale with context |
| **Numbers** | `font-mono text-oatmeal-100` | Financial data emphasis |
| **Variance %** | `text-clay-400` if negative, `text-sage-400` if within tolerance | Semantic colors |

### 2.4 Micro-interactions

- **Entrance:** Fade in from bottom (after KeyMetrics load, 100ms delay)
- **Expansion:** If deviation > 1%, card expands from badge on-click
  - Height animation: `initial={{ height: 0 }}` → `animate={{ height: 'auto' }}`
  - Opacity: Staggered from 0 to 1
- **Icon Animation:** Badge icon pulses softly if critical (repeat: Infinity, duration: 1.5s)
- **Hover:** Card hovers reveal [?] tooltip explaining A = L + E formula

### 2.5 Data Integration

**Backend Provides:**
```python
{
  "total_assets": 5234600.00,
  "total_liabilities": 3100000.00,
  "total_equity": 1800000.00,
  "liabilities_plus_equity": 4900000.00,
  "variance": -334600.00,
  "variance_percent": -6.39,
  "is_balanced": False,
  "likely_cause": "Missing equity account or hidden liability"
}
```

---

## 3. Concentration Risk Detector

**Purpose:** Show accounts dominating category totals (>25% threshold, configurable).

### 3.1 Component Concept: "Concentration Heatmap" (New Component Type)

**Location in Results View:**
- New collapsible section in **KeyMetricsSection**, BEFORE category totals
- Acts as a "supplementary analytics" feature
- Only displays if concentration risk detected (≥ 1 account >25%)

**Visual Hierarchy:**
```
[KEY METRICS SECTION]
├── Core 4 Ratios (grid)
├── Advanced Ratios Toggle
├── 🔥 CONCENTRATION RISK [NEW] [Collapsible]
│   └── [Heatmap visualization]
└── Category Totals Row
```

### 3.2 Concentration Risk Card

**Collapsed State:**
```
🔥 Concentration Risk — 2 accounts exceed 25% threshold
[Show Details ▼]
```
- Single-line summary with expand trigger
- Icon: Flame emoji (🔥) or exclamation in clay-400
- Text: `text-clay-400 font-sans font-medium`

**Expanded State:**
```
┌─────────────────────────────────────────────────────────┐
│ 🔥 Concentration Risk Analysis                      [✕]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ASSETS CONCENTRATION:                                   │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Accounts Receivable         ████████████░░░░░░░  45%  │
│ │   [Type: Asset] [$2.3M / $5.2M total assets]         │
│ │                                                  │   │
│ │ Equipment - Net             ██████░░░░░░░░░░░░  28%  │
│ │   [Type: Asset] [$1.5M / $5.2M total assets]         │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ LIABILITIES CONCENTRATION:                              │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Bank Debt - Long Term       ███████░░░░░░░░░░░  38%  │
│ │   [Type: Liability] [$1.2M / $3.1M total liab.]      │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ Recommendation: Diversify or document concentration    │
│ Risk Level: ⚠️ MEDIUM (2 accounts >25%)               │
│                                                          │
│ [Export Concentration Report]                          │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Concentration Bar Component

**Sub-component (reusable for each account):**
```tsx
<ConcentrationBar
  accountName="Accounts Receivable"
  amount={2300000}
  categoryTotal={5200000}
  percentage={45}
  category="asset"
/>
```

Renders:
```
Account Name ├─ Bar (width: %) ─┤ ## %
              └─ Amount: $2.3M / Category: $5.2M total
```

**Styling:**
- **Bar Fill:** Gradient from sage-500 (safe ≤25%) → oatmeal-400 (warning 25-50%) → clay-500 (danger >50%)
- **Bar Container:** `bg-obsidian-700/50 rounded-lg h-1.5 overflow-hidden`
- **Label:** `font-sans text-sm text-oatmeal-200`
- **Amount Text:** `font-mono text-xs text-oatmeal-500`

### 3.4 Styling Details

| Element | Style | Notes |
|---------|-------|-------|
| **Card Border** | `border border-obsidian-600/50` | Neutral border |
| **Section Headers** | `font-sans font-semibold text-oatmeal-300 text-sm` | Clear hierarchy |
| **Bar Gradient** | `linear-gradient(to right, #4A7C59, #EBE9E4, #BC4749)` | Risk temperature |
| **Risk Badge** | `inline-flex gap-1 px-2 py-1 rounded-full` + semantic color | Matches theme |
| **Close Button** | Dismiss for session (no storage, re-appears on refresh) | Zero-Storage compliant |

### 3.5 Micro-interactions

- **Entrance:** Accordion-style height animation (40ms stagger from KeyMetrics)
  - Bars stagger individually on expand (20ms delay per row)
- **Bar Expansion:** Hover over bar shows full account details in tooltip:
  ```
  Accounts Receivable
  $2,345,678.90 / $5,234,600.00 (44.8%)
  Asset Category
  ```
- **Export Button:** Opens PDF with concentration breakdown (uses existing PDF generator)
- **Dismiss:** X button hides for session (no permanent storage)

### 3.6 Data Integration

**Backend Provides:**
```python
{
  "concentration_risks": [
    {
      "category": "asset",
      "category_total": 5234600.00,
      "account": "Accounts Receivable",
      "amount": 2345678.90,
      "percentage": 44.8,
      "threshold_exceeded": True
    },
    {
      "category": "liability",
      "category_total": 3100000.00,
      "account": "Bank Debt - Long Term",
      "amount": 1200000.00,
      "percentage": 38.7,
      "threshold_exceeded": True
    }
  ],
  "risk_level": "medium",  # low, medium, high based on count + severity
  "total_at_risk": 2
}
```

---

## 4. Rounding Anomaly Scanner

**Purpose:** Detect suspiciously round figures that may indicate estimation or manipulation.

### 4.1 Component Concept: "Rounding Alert Cards" (New Component Type)

**Location in Results View:**
- Integrated into **RiskDashboard**, grouped AFTER high-severity anomalies but BEFORE low-severity collapsible
- Acts as a "secondary" risk layer
- Only appears if rounding anomalies detected

**Visual Hierarchy:**
```
[RISK DASHBOARD]
├── Risk Summary Header
├── Material Risks (high-severity anomalies)
├── 🔢 ROUNDING ANOMALIES [NEW] [Collapsible]
│   └── [List of suspicious round figures]
└── Indistinct Items (collapsible)
```

### 4.2 Rounding Anomaly Alert

**Collapsed State:**
```
🔢 Rounding Anomalies Detected (3 accounts)
[Show Details ▼]
```
- Single-line summary, similar to "Indistinct Items" toggle
- Icon: Hash/Number symbol (#) in oatmeal-500
- Color: Neutral (not clay), suggesting "investigate" rather than "error"

**Expanded State:**
```
┌─────────────────────────────────────────────────────────┐
│ 🔢 ROUNDING ANOMALIES DETECTED (3)                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ⚠️ Petty Cash                                 $5,000.00  │
│    Detected as 100% round ($5,000.00 exactly)          │
│    Anomaly Score: 95% likelihood of rounding            │
│    [Likely: Manual estimate] [Flag for audit]           │
│                                                          │
│ ⚠️ Accrued Expenses                           $50,000.00 │
│    Detected as 100% round ($50,000.00 exactly)         │
│    Anomaly Score: 98% likelihood of rounding            │
│    [Likely: Manual estimate] [Flag for audit]           │
│                                                          │
│ ⚠️ Deferred Revenue                          $25,000.00 │
│    Detected as 100% round ($25,000.00 exactly)         │
│    Anomaly Score: 92% likelihood of rounding            │
│    [Likely: Manual estimate] [Flag for audit]           │
│                                                          │
│ ℹ️ Rounding Threshold: >90% probability of round number │
│ ℹ️ Context: Common in accruals, petty cash, estimates   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.3 Individual Rounding Card

**Styling:**
```
┌─────────────────────────────────────────────────────────┐
│ ⚠️ Account Name               $X,XXX.00 [Confidence]    │
│    Issue: 100% round number (ends in .00)              │
│    Score: 95% likelihood                                │
│    [Likely Cause] [Flag for Audit] [Ignore]            │
└─────────────────────────────────────────────────────────┘
```

| Element | Style | Notes |
|---------|-------|-------|
| **Card Border** | `border-l-4 border-l-oatmeal-500/40` | Subtle, not clay (informational, not error) |
| **Background** | `bg-obsidian-800/40` | Same as anomaly cards |
| **Icon** | ⚠️ in `oatmeal-500` | Different from clay (error marker) |
| **Amount** | `font-mono text-oatmeal-300` | Financial data emphasis |
| **Confidence** | `text-oatmeal-500 text-xs font-sans` | Muted secondary info |
| **Action Buttons** | Secondary style (gray hover) | "Flag for Audit" is primary action |

### 4.4 Rounding Anomaly Detection Logic

**Backend Logic:**
1. Check if balance ends in `.00` AND amount ≥ $1,000
2. Statistical analysis: If account is typically precise (e.g., Accounts Receivable), round figures are anomalies
3. Skip naturally-round accounts: Petty Cash, Imprest accounts, Sales Discounts
4. Confidence score: 90-99% based on:
   - Account type likelihood (Accrual accounts = high confidence)
   - Prior period data (if available)
   - Category prevalence (how common round figures in this category)

### 4.5 Micro-interactions

- **Entrance:** Collapse/expand with framer-motion height animation
  - Cards inside stagger on expand (30ms delay per card)
- **Hover State:** Border highlight + background opacity increase
- **Action Buttons:**
  - "Likely Cause": Shows tooltip with explanation (Accrual? Estimate? Manual entry?)
  - "Flag for Audit": Adds to session audit list (exported in PDF/Excel)
  - "Ignore": Hides for session (can be re-enabled)
- **Icon Pulse:** Subtle pulse (0.3s) if all 3+ anomalies detected (visual weight)

### 4.6 Data Integration

**Backend Provides:**
```python
{
  "rounding_anomalies": [
    {
      "account": "Petty Cash",
      "amount": 5000.00,
      "is_round": True,
      "confidence": 0.95,
      "likely_cause": "Manual estimate or petty cash fund round number",
      "category": "asset"
    },
    {
      "account": "Accrued Expenses",
      "amount": 50000.00,
      "is_round": True,
      "confidence": 0.98,
      "likely_cause": "Manual accrual estimate",
      "category": "liability"
    }
  ]
}
```

---

## 5. Contra-Account Validator

**Purpose:** Validate depreciation ratios (e.g., Accumulated Depreciation < Equipment balance) and other contra-account relationships.

### 5.1 Component Concept: "Relationship Card" (New Component Type)

**Location in Results View:**
- Integrated into **KeyMetricsSection** (after category totals, as a supplementary analytics layer)
- Only appears if contra-account relationships detected
- Minimal by default, shows summary with expandable details

**Visual Hierarchy:**
```
[KEY METRICS SECTION]
├── Core 4 Ratios (grid)
├── Advanced Ratios Toggle
├── Equation Status Badge
├── 📊 CONTRA-ACCOUNT HEALTH [NEW] [Collapsible]
│   └── [Relationship validations]
└── Category Totals Row
```

### 5.2 Contra-Account Validation Card

**Collapsed State:**
```
📊 Contra-Account Health — 2 relationships valid
[Show Details ▼]
```
- Single-line summary
- Icon: Chart/Analytics symbol (📊) in sage-400
- Text: `text-sage-400 font-sans font-medium`

**Expanded State:**
```
┌─────────────────────────────────────────────────────────┐
│ 📊 CONTRA-ACCOUNT HEALTH CHECKS                    [✕]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ✓ Equipment ↔ Accumulated Depreciation                  │
│   Equipment Balance:      $1,500,000.00                 │
│   Accumulated Depreciation: $450,000.00                 │
│   Depreciation Ratio:     30.0%                         │
│   Health:                 ✓ NORMAL (20-40% range)       │
│                                                          │
│ ✓ Inventory ↔ Allowance for Obsolescence               │
│   Inventory Balance:      $800,000.00                   │
│   Allowance:              $40,000.00                    │
│   Reserve Ratio:          5.0%                          │
│   Health:                 ✓ NORMAL (3-8% range)         │
│                                                          │
│ ⚠️ Accounts Receivable ↔ Allowance for Doubtful        │
│   AR Balance:             $1,200,000.00                 │
│   Allowance:              $24,000.00                    │
│   Reserve Ratio:          2.0%                          │
│   Health:                 ⚠️ LOW (typical: 3-5%)        │
│   Recommendation: Review AR aging for bad debts        │
│                                                          │
│ ℹ️ Ranges are industry-standard; adjust if needed       │
│                                                          │
│ [Adjust Thresholds] [Export Relationships]             │
└─────────────────────────────────────────────────────────┘
```

### 5.3 Individual Relationship Card

**Styling (per relationship):**
```
┌─────────────────────────────────────────────────────────┐
│ ✓ [Asset] ↔ [Contra] ── Ratio: ##% ── [Status Badge]   │
│                                                          │
│ [Primary Amount]: $X,XXX,XXX.XX                         │
│ [Contra Amount]:  $X,XXX,XXX.XX                         │
│ [Ratio Name]:     ##%                                   │
│ Health Status:    ✓ NORMAL / ⚠️ UNUSUAL / ✗ CRITICAL   │
│                                                          │
│ [Adjust Range] [View Details]                           │
└─────────────────────────────────────────────────────────┘
```

| Element | Style | Notes |
|---------|-------|-------|
| **Card Border** | `border border-obsidian-600/50` (normal) or `border-l-4 border-l-oatmeal-500/50` (warning) | Conditional warning border |
| **Header** | `font-sans font-semibold text-oatmeal-200` | Relationship pair names |
| **Status Badge** | Sage for ✓, Oatmeal for ⚠️, Clay for ✗ | Semantic colors |
| **Ratio %** | `font-mono text-lg text-oatmeal-100` | Financial emphasis |
| **Thresholds** | `text-oatmeal-500 text-xs font-sans` | Muted secondary info |

### 5.4 Micro-interactions

- **Entrance:** Accordion collapse/expand (40ms stagger from KeyMetrics)
  - Individual relationship cards stagger on expand (25ms delay each)
- **Status Badge Animation:**
  - ✓ NORMAL: Static green
  - ⚠️ UNUSUAL: Subtle pulse (1s duration, soft glow)
  - ✗ CRITICAL: Stronger pulse or rotation (like AnomalyCard high-severity glow)
- **Hover State:** Relationship card shows ratio calculation tooltip
  ```
  Depreciation Ratio = Accumulated Depreciation / Equipment
  = $450,000 / $1,500,000 = 30%

  Industry Typical Range: 20-40% (varies by asset class)
  ```
- **Adjust Thresholds:** Opens lightweight modal to modify ±% ranges per relationship

### 5.5 Data Integration

**Backend Provides:**
```python
{
  "contra_account_relationships": [
    {
      "primary_account": "Equipment",
      "contra_account": "Accumulated Depreciation",
      "primary_amount": 1500000.00,
      "contra_amount": 450000.00,
      "ratio": 0.30,
      "ratio_label": "Depreciation Ratio",
      "health_status": "normal",  # normal, unusual, critical
      "typical_range": [0.20, 0.40],
      "recommendation": "Within normal range"
    },
    {
      "primary_account": "Accounts Receivable",
      "contra_account": "Allowance for Doubtful Accounts",
      "primary_amount": 1200000.00,
      "contra_amount": 24000.00,
      "ratio": 0.02,
      "ratio_label": "AR Reserve Ratio",
      "health_status": "unusual",
      "typical_range": [0.03, 0.05],
      "recommendation": "Lower than typical; review aging for potential bad debts"
    }
  ]
}
```

---

## Visual Layout Integration: The Complete Diagnostic View

### Overall Page Structure (from top to bottom)

```
╔════════════════════════════════════════════════════════════════╗
║  DIAGNOSTIC RESULTS VIEW (Workspace)                           ║
║  Existing: MaterialityControl + RiskDashboard + KeyMetrics    ║
╚════════════════════════════════════════════════════════════════╝

1. MATERIALITY CONTROL (existing)
   └── Manual threshold adjustment, live sensitivity toolbar

2. KEY METRICS SECTION (enhanced with new features)
   ├── Section Header + Variance Badge (existing)
   ├── Core 4 Ratios Grid (existing)
   ├── Advanced Ratios Toggle (existing)
   │
   ├── 📊 CONTRA-ACCOUNT HEALTH [NEW] [Collapsible]
   │   └── Depreciation/Reserve relationship validations
   │
   ├── 🔥 CONCENTRATION RISK [NEW] [Collapsible]
   │   └── Account concentration heatmaps
   │
   ├── ✓ Balance Sheet Equation Status [NEW]
   │   └── A = L + E validator with variance
   │
   └── Category Totals Row (existing)

3. RISK DASHBOARD (enhanced with new features)
   ├── Risk Summary Header (existing)
   │
   ├── ⚠️ SUSPENSE ACCOUNT DETECTED [NEW] (if applicable)
   │   └── Inline alert card with reassign/archive/ignore actions
   │
   ├── Material Risks Section (existing)
   │   └── High-severity AnomalyCards
   │
   ├── 🔢 ROUNDING ANOMALIES [NEW] [Collapsible]
   │   └── Round figure detection cards
   │
   └── Indistinct Items (collapsible) (existing)
       └── Low-severity AnomalyCards

4. EXPORT SECTION (existing)
   └── PDF/Excel download buttons
```

### Grouping Strategy: "Layers of Analysis"

**Tier 1: Foundational (always visible when present)**
- Risk Summary Header
- Suspense Account Alert (if detected)
- Material Risks (high-severity anomalies)

**Tier 2: Investigative (collapsible, lower friction)**
- Rounding Anomalies
- Indistinct Items

**Tier 3: Analytical (supplementary to ratios)**
- Contra-Account Health (grouped with KeyMetrics)
- Concentration Risk (grouped with KeyMetrics)
- Balance Sheet Equation Status (grouped with KeyMetrics)

**Rationale:**
- Foundational issues (Suspense, Material Risks) dominate visual hierarchy
- Investigative issues (Rounding, Low-Severity) are secondary but accessible
- Analytical issues (Ratios, Relationships, Concentration) are for deep-dive professionals

---

## Color Palette Reference

### Semantic Color Usage

| Feature | Primary Color | Secondary Color | Usage |
|---------|---------------|-----------------|-------|
| **Suspense Account** | Clay-500 (#BC4749) | Clay-400 | Error/Risk - accounting chaos |
| **Balance Equation** | Sage-500 (#4A7C59) | Sage-400 or Clay-500 | Success/Error - fundamental validation |
| **Concentration Risk** | Clay-500 (#BC4749) | Oatmeal-400 | Warning gradient - risk temperature |
| **Rounding Anomaly** | Oatmeal-500 (#E0DCD5) | Oatmeal-400 | Informational - needs investigation |
| **Contra-Account** | Sage-500 (#4A7C59) | Sage-400 or Oatmeal-500 | Success/Warning - relationship health |

### Animation Timing

| Component | Entrance Delay | Stagger | Duration | Easing |
|-----------|----------------|---------|----------|--------|
| **Suspense Alert** | 100ms | — | 400ms | spring (damping: 25) |
| **Equation Badge** | 150ms | — | 300ms | easeOut |
| **Concentration Expand** | 200ms | 40ms per row | 250ms | easeInOut |
| **Rounding Cards** | 250ms | 30ms per card | 300ms | easeInOut |
| **Contra-Account Cards** | 300ms | 25ms per card | 350ms | easeInOut |

---

## Accessibility & UX Considerations

### Keyboard Navigation
- All collapsible sections: Space/Enter to expand/collapse
- Action buttons: Tab order follows visual hierarchy (left-to-right, top-to-bottom)
- Close buttons (✕): Escape key support

### Color Blindness
- Do NOT rely on color alone to convey information
- Use icons + text labels for all status indicators
- Provide monochrome fallback for printed PDFs

### Mobile Responsiveness
- Concentration heatmap bars: Stack vertically on mobile (width: 100%)
- Cards: Maintain full width on small screens, no horizontal scroll
- Action buttons: Primary action takes full width on mobile

### Screen Reader Support
- Card headers: `<h3>` tags with descriptive text
- Status badges: `aria-label="High Risk"` attributes
- Expandable sections: `aria-expanded="true/false"` on toggle buttons
- Icon-only buttons: `title` attributes for hover tooltips

---

## Design Tokens & CSS Classes

### New Tailwind Classes to Create (if needed)

```css
/* Concentration bar gradient */
.concentration-gradient {
  background: linear-gradient(to right,
    #4A7C59 0%,      /* sage-500 for safe */
    #EBE9E4 50%,     /* oatmeal for warning */
    #BC4749 100%     /* clay-500 for danger */
  );
}

/* Rounding anomaly subtle pulse */
@keyframes roundingPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
.anomaly-pulse {
  animation: roundingPulse 2s ease-in-out infinite;
}

/* Contra-account relationship pulse (warning state) */
@keyframes relationshipPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(224, 220, 213, 0.4); }
  50% { box-shadow: 0 0 8px 2px rgba(224, 220, 213, 0.1); }
}
.relationship-warning {
  animation: relationshipPulse 1.5s ease-in-out infinite;
}
```

### Existing Class Patterns to Leverage

- `.card` / `.card-interactive` — Base card styling
- `.badge-success` / `.badge-error` / `.badge-neutral` — Status indicators
- `.status-pill` / `.status-pill-warning` / `.status-pill-danger` — Inline status badges
- `font-serif` / `font-sans` / `font-mono` — Typography hierarchy
- `border-l-4 border-l-clay-500` — Premium Restraint left border accent

---

## Implementation Checklist

### Phase III Sprint 40-43 Roadmap

- [ ] **Sprint 40:** Suspense Account Detector (backend + frontend AlertCard)
- [ ] **Sprint 41:** Balance Sheet Equation Validator (backend + badge/card component)
- [ ] **Sprint 42:** Concentration Risk Detector + Rounding Anomaly Scanner (backend + frontend components)
- [ ] **Sprint 43:** Contra-Account Validator (backend + frontend relationship cards)

### Per-Component Deliverables

Each feature requires:
1. **Backend Service** (Python)
   - Detection algorithm + scoring logic
   - API endpoint returning structured data
   - Zero-Storage compliance check

2. **TypeScript Types**
   - Data structures for API response
   - Component prop interfaces

3. **React Component**
   - Follows Oat & Obsidian design system
   - framer-motion animations with defined timing
   - Accessibility attributes

4. **Test Coverage**
   - Unit tests for detection logic
   - Integration tests for API → component flow
   - Visual regression tests (if available)

5. **Documentation**
   - Docstring in component files
   - Design rationale in dev-log.md
   - User-facing tooltip text

---

## Design Validation Checklist

Before implementation, verify:

- [ ] All clay-red accents use `.border-l-4 border-l-clay-500` (never full backgrounds)
- [ ] No generic Tailwind colors used (slate, blue, green, red)
- [ ] All headers use `font-serif` classes
- [ ] All financial numbers use `font-mono` classes
- [ ] Animation timings follow 40-50ms stagger pattern
- [ ] Collapsible sections use `AnimatePresence` + motion.div
- [ ] Zero-Storage compliance: no financial data stored in component state (session only)
- [ ] Mobile layouts tested at 375px, 768px, 1024px+ breakpoints
- [ ] Keyboard navigation works for all interactive elements
- [ ] WCAG AA color contrast maintained (4.5:1 for text, 3:1 for UI)
- [ ] Error states use clay-500, success states use sage-500

---

## References

**Existing Patterns in Codebase:**
- `AnomalyCard` — Premium Restraint design, left-border accents
- `KeyMetricsSection` — Collapsible sections, staggered animations
- `RiskDashboard` — Severity separation, material/immaterial grouping
- `MetricCard` — Tier 2 semantic colors, tooltip hover effects

**Design System:**
- `skills/theme-factory/themes/oat-and-obsidian.md`
- `frontend/src/app/globals.css` (component layer)
- `CLAUDE.md` (Premium Restraint philosophy, Sprint 10)

**Animation Patterns:**
- `framer-motion` examples in `WorkbookInspector.tsx`
- Stagger patterns: 40ms delay per card (standard)
- Spring animations: `damping: 25, stiffness: 300`

---

## Design Authority Sign-Off

**Fintech Designer Review:** ✓ Complete
**CEO Review:** Pending
**Backend Audit (Zero-Storage):** Pending
**QA Accessibility Review:** Pending

**Design Version:** 1.0
**Last Updated:** 2026-02-04
