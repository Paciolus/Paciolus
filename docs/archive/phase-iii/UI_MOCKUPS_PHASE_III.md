# Phase III UI Mockups: Advanced Diagnostic Signals
## Visual Reference for Implementation

---

## 1. SUSPENSE ACCOUNT DETECTOR — Alert Card

### Desktop View (1024px+)

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️ SUSPENSE ACCOUNT DETECTED                              [✕]  │ ← border-l-4 border-l-clay-500
├─────────────────────────────────────────────────────────────────┤ bg-obsidian-800/40
│                                                                  │
│ Account: "Suspense - Clearing"                                  │ font-sans
│ Amount: $47,385.92                                              │ font-mono text-oatmeal-200
│ Detected Type: Asset (confidence: 95%)                          │ text-xs font-sans
│                                                                  │
│ ⚠️ Issue: This account typically carries NO balance at period  │
│    end. It should be cleared or reclassified.                  │
│                                                                  │
│ Recommendation: Reclassify to an operational account or        │
│ archive if balance represents a temporary clearance.           │
│                                                                  │
│ [Reassign Account ▼] [Archive] [Ignore for Session]           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Mobile View (375px)

```
┌──────────────────────────────┐
│⚠️ SUSPENSE DETECTED     [✕]  │
├──────────────────────────────┤
│ Account:                     │
│ Suspense - Clearing          │
│                              │
│ Amount: $47,385.92           │
│ Type: Asset (95%)            │
│                              │
│ Issue: No balance expected   │
│                              │
│ [Reassign ▼]                │
│ [Archive]                   │
│ [Ignore]                    │
│                              │
└──────────────────────────────┘
```

### Component Structure

```jsx
<motion.div
  className="rounded-lg overflow-hidden
             bg-obsidian-800/40
             border border-obsidian-600/50
             border-l-4 border-l-clay-500"
  variants={cardVariants}
  initial="hidden"
  animate="visible"
>
  <div className="p-4 relative">
    {/* Header */}
    <div className="flex justify-between items-start mb-3">
      <div className="flex items-center gap-2">
        <WarningTriangleIcon className="text-clay-400" />
        <h3 className="font-serif font-semibold text-oatmeal-200">
          Suspense Account Detected
        </h3>
      </div>
      <CloseButton onClick={onDismiss} />
    </div>

    {/* Account Details */}
    <div className="space-y-2 text-sm font-sans text-oatmeal-400 mb-3">
      <div>Account: <span className="text-oatmeal-200">{account}</span></div>
      <div>Amount: <span className="font-mono">${amount.toLocaleString()}</span></div>
      <div>Type: {type} ({confidence}% confidence)</div>
    </div>

    {/* Issue Description */}
    <div className="bg-obsidian-700/30 rounded px-3 py-2 mb-3">
      <p className="text-xs text-oatmeal-500 font-sans">
        ⚠️ This account typically carries NO balance...
      </p>
    </div>

    {/* Action Buttons */}
    <div className="flex gap-2">
      <ReassignDropdown />
      <ArchiveButton />
      <IgnoreButton />
    </div>
  </div>
</motion.div>
```

---

## 2. BALANCE SHEET EQUATION VALIDATOR — Badge & Card Variants

### Variant A: Balanced (Success State)

```
┌─────────────────────────────────────────────────┐
│ ✓ Balance Sheet Balanced | A = L + E            │ ← bg-sage-500/10
│   Assets: $5,234,600.00 | Liab + Equity: $5,234,600.00 │
└─────────────────────────────────────────────────┘
  border-sage-500/30   text-sage-300
```

**Code:**
```jsx
<div className="inline-flex items-center gap-2 px-3 py-1.5
                bg-sage-500/10 border border-sage-500/30
                rounded-full text-sage-300 text-sm font-sans">
  <CheckmarkIcon className="w-4 h-4" />
  <span>Balance Sheet Balanced | A = L + E</span>
</div>
```

### Variant B: Rounding Variance (Warning State)

```
┌─────────────────────────────────────────────────┐
│ ⚠️ Balance Sheet — Rounding Variance            │ ← bg-oatmeal-500/10
│    Assets:            $5,234,602.34             │
│    Liab + Equity:     $5,234,600.00             │
│    Variance: $2.34 (0.00004%)                   │
└─────────────────────────────────────────────────┘
  border-oatmeal-500/30   text-oatmeal-300
```

### Variant C: Material Error (Critical State)

```
┌──────────────────────────────────────────────────────────┐
│ ✗ BALANCE SHEET EQUATION ERROR                      [?] │ ← border-l-4 border-l-clay-500
├──────────────────────────────────────────────────────────┤ bg-obsidian-800/40
│                                                           │
│ Trial Balance Summary:                                   │
│ ┌──────────────────────────────────────────────────┐    │
│ │ Total Assets:           $5,234,600.00            │    │
│ │ Total Liabilities:      $3,100,000.00            │    │
│ │ Total Equity:           $1,800,000.00            │    │
│ │ ─────────────────────────────────────────────    │    │
│ │ Liab + Equity:          $4,900,000.00            │    │
│ │ ═════════════════════════════════════════════    │    │
│ │ Variance (A - L - E):   −$334,600.00  ✗ FAIL   │    │
│ │ Variance %:             −6.39%                    │    │
│ └──────────────────────────────────────────────────┘    │
│                                                           │
│ Status: ✗ UNBALANCED                                    │
│ Likely Cause: Missing equity account or hidden liability │
│                                                           │
│ [Review Trial Balance Mapping] [Export Error Log]       │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Animation: Expansion Sequence

```
State 1 (Initial - Badge):
┌─────────────────────────────────┐
│ ⚠️ Rounding Variance            │
└─────────────────────────────────┘
  height: 2.5rem, opacity: 1

  ↓ [Click]

State 2 (Expanding):
┌─────────────────────────────────┐
│ ⚠️ Balance Sheet — Rounding    │
│    Variance                     │
│                                 │
│    Assets: ...                  │  ← height animating from 2.5rem → auto
│    Liab + Equity: ...           │  ← content fading in
│    Variance: $2.34...           │
│                                 │
└─────────────────────────────────┘
```

---

## 3. CONCENTRATION RISK DETECTOR — Heatmap View

### Collapsed State

```
┌──────────────────────────────────────────┐
│ 🔥 Concentration Risk — 2 accounts       │
│    exceed 25% threshold            [▼]   │
└──────────────────────────────────────────┘
  text-clay-400   hover:bg-obsidian-700/50
```

### Expanded State — Full Card

```
┌──────────────────────────────────────────────────────────┐
│ 🔥 CONCENTRATION RISK ANALYSIS                      [✕]  │ ← clay-500
├──────────────────────────────────────────────────────────┤
│                                                           │
│ ASSETS CONCENTRATION:                                    │
│                                                           │
│ Accounts Receivable              45% (High)              │
│ ████████████████████░░░░░░░░░░░░░░░░                    │
│ $2,345,678 / $5,234,600 total assets                     │
│                                                           │
│ Equipment - Net                  28% (Moderate)          │
│ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░             │
│ $1,468,092 / $5,234,600 total assets                     │
│                                                           │
│ ─────────────────────────────────────────────────────   │
│                                                           │
│ LIABILITIES CONCENTRATION:                               │
│                                                           │
│ Bank Debt - Long Term           38% (Moderate-High)      │
│ ███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░      │
│ $1,178,000 / $3,100,000 total liabilities                │
│                                                           │
│ ─────────────────────────────────────────────────────   │
│                                                           │
│ ⚠️ Risk Level: MEDIUM (2 accounts >25%)                 │
│                                                           │
│ Recommendation: Diversify asset base or document        │
│ concentration dependency on major customers.             │
│                                                           │
│ [Export Concentration Report]                           │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Concentration Bar Sub-Component

```
Account Name:        ████████████░░░░░░░░░░░░░░  45%
                     └─ [Hover Tooltip] ─┘

Tooltip (on hover):
┌──────────────────────────────────────┐
│ Accounts Receivable                  │
│ $2,345,678.90 / $5,234,600.00       │
│ 44.8% of total assets                │
│ Status: ⚠️ CONCENTRATION RISK        │
└──────────────────────────────────────┘
```

**Color Gradient:**
```
0-25%:  🟢 Sage (#4A7C59)
25-50%: 🟡 Oatmeal (#EBE9E4)
50-75%: 🟠 Oatmeal-mix
75%+:   🔴 Clay (#BC4749)
```

### Component Code Structure

```jsx
<motion.div
  className="border border-obsidian-600/50 rounded-xl
             bg-obsidian-800/40 overflow-hidden"
  initial={{ height: 0, opacity: 0 }}
  animate={{ height: 'auto', opacity: 1 }}
  transition={{ duration: 0.25 }}
>
  <div className="p-4 space-y-6">
    {/* Assets Section */}
    <div>
      <h4 className="font-sans font-semibold text-oatmeal-300 mb-3">
        ASSETS CONCENTRATION:
      </h4>
      <motion.div
        className="space-y-3"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        {assets.map((asset, i) => (
          <ConcentrationBar
            key={asset.account}
            account={asset.account}
            amount={asset.amount}
            categoryTotal={totalAssets}
            percentage={asset.percentage}
            index={i}
          />
        ))}
      </motion.div>
    </div>

    {/* Liabilities Section */}
    {/* ... similar structure ... */}

    {/* Risk Badge */}
    <div className="pt-4 border-t border-obsidian-600/30">
      <StatusBadge level={riskLevel} />
      <p className="text-xs text-oatmeal-500 mt-2 font-sans">
        Recommendation: ...
      </p>
    </div>
  </div>
</motion.div>
```

---

## 4. ROUNDING ANOMALY SCANNER — Alert Cards

### Collapsed State

```
┌──────────────────────────────────────────┐
│ 🔢 Rounding Anomalies — 3 accounts  [▼]  │
└──────────────────────────────────────────┘
  text-oatmeal-500   icon: # (hash)
```

### Expanded State — Card List

```
┌──────────────────────────────────────────────────────────┐
│ 🔢 ROUNDING ANOMALIES DETECTED (3)                   [▲]  │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ ⚠️ Petty Cash                                $5,000.00    │ ← border-l-4 border-l-oatmeal-500/40
│    Issue: 100% round number (ends in .00)                │
│    Anomaly Score: 95% likelihood of rounding             │
│    Context: Manual estimate or round cash fund           │
│                                                           │
│    [Likely: Manual Estimate] [Flag for Audit] [Ignore]  │
│                                                           │
│ ─────────────────────────────────────────────────────   │
│                                                           │
│ ⚠️ Accrued Expenses                      $50,000.00      │
│    Issue: 100% round number (ends in .00)                │
│    Anomaly Score: 98% likelihood of rounding             │
│    Context: Manual accrual estimate                      │
│                                                           │
│    [Likely: Manual Estimate] [Flag for Audit] [Ignore]  │
│                                                           │
│ ─────────────────────────────────────────────────────   │
│                                                           │
│ ⚠️ Deferred Revenue                      $25,000.00      │
│    Issue: 100% round number (ends in .00)                │
│    Anomaly Score: 92% likelihood of rounding             │
│    Context: Revenue deferral, typically estimated        │
│                                                           │
│    [Likely: Manual Estimate] [Flag for Audit] [Ignore]  │
│                                                           │
│ ─────────────────────────────────────────────────────   │
│                                                           │
│ ℹ️ Rounding Detection:                                   │
│    Threshold: >90% probability of round number           │
│    Context: Common in accruals, petty cash, estimates    │
│    Confidence: Accounts screened by type prevalence      │
│                                                           │
│ [Export Rounding Report] [Review All Flagged]           │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Individual Rounding Card

```
┌──────────────────────────────────────────────────────┐
│ ⚠️ Account Name        Amount          Confidence   │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Issue: 100% round number (ends in .00)              │
│ Score: 95% likelihood of rounding                   │
│ Likely Cause: Manual estimate or round cash fund    │
│                                                      │
│ [Likely] [Flag] [Ignore]                           │
│                                                      │
└──────────────────────────────────────────────────────┘
  border-l-4 border-l-oatmeal-500/40
```

### Action Buttons Micro-interactions

```
Default State:
[Likely: Manual Estimate] [Flag for Audit] [Ignore]
 text-oatmeal-500        text-sage-400      text-oatmeal-500

Hover State (Likely):
[Likely: Manual Estimate]  ← bg-obsidian-700/50, border-obsidian-500/50
 Tooltip appears: "Manual entry or estimate, not system-calculated"

Hover State (Flag):
[Flag for Audit]  ← bg-sage-500/10, border-sage-500/30
 Tooltip: "Adds to audit workpaper export"

Clicked (Ignore):
[✓ Ignored]  ← text-oatmeal-600, opacity-50
 Card fades to background level
```

---

## 5. CONTRA-ACCOUNT VALIDATOR — Relationship Cards

### Collapsed State

```
┌──────────────────────────────────────────┐
│ 📊 Contra-Account Health — 2 valid  [▼]  │
└──────────────────────────────────────────┘
  text-sage-400   icon: chart/analytics
```

### Expanded State — Relationships

```
┌──────────────────────────────────────────────────────────┐
│ 📊 CONTRA-ACCOUNT HEALTH CHECKS                     [✕]  │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ ✓ EQUIPMENT ↔ ACCUMULATED DEPRECIATION           [✓]    │
│                                                           │
│   Primary (Equipment):           $1,500,000.00           │
│   Contra (Accumulated Depr.):      $450,000.00           │
│   Depreciation Ratio:              30.0%                 │
│   Health Status:                   ✓ NORMAL (20-40%)    │
│   Recommendation:                  Within expected range  │
│                                                           │
│ ─────────────────────────────────────────────────────   │
│                                                           │
│ ✓ INVENTORY ↔ ALLOWANCE FOR OBSOLESCENCE       [✓]     │
│                                                           │
│   Primary (Inventory):             $800,000.00           │
│   Contra (Allowance):               $40,000.00           │
│   Reserve Ratio:                    5.0%                 │
│   Health Status:                    ✓ NORMAL (3-8%)     │
│   Recommendation:                   Within expected range  │
│                                                           │
│ ─────────────────────────────────────────────────────   │
│                                                           │
│ ⚠️ ACCOUNTS REC. ↔ ALLOWANCE FOR DOUBTFUL      [⚠️]     │
│                                                           │
│   Primary (AR):                    $1,200,000.00         │
│   Contra (Allowance):                 $24,000.00         │
│   Reserve Ratio:                    2.0%                 │
│   Health Status:                    ⚠️ LOW (typical: 3-5%)│
│   Recommendation:                   Review AR aging for  │
│                                      potential bad debts   │
│                                                           │
│ ─────────────────────────────────────────────────────   │
│                                                           │
│ ℹ️ Industry Ranges:                                      │
│    • Equipment Depreciation: 20-40% (by asset class)     │
│    • Inventory Reserve:      3-8% (by industry)          │
│    • AR Bad Debt Allowance:  2-5% (varies)               │
│                                                           │
│ [Adjust Thresholds] [View Industry Benchmarks]          │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Individual Relationship Card

```
┌──────────────────────────────────────────────────────┐
│ ✓ [ASSET] ↔ [CONTRA]      Ratio: 30%    [✓ NORMAL] │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Equipment:              $1,500,000.00               │
│ Accumulated Depreciation:  $450,000.00              │
│ Depreciation Ratio:        30.0%                    │
│ Expected Range:            20-40%                   │
│ Health Status:             ✓ NORMAL                 │
│                                                      │
│ Recommendation: Within expected range for typical   │
│ fixed assets. No action required.                   │
│                                                      │
│ [Adjust Range] [View Formula]                      │
│                                                      │
└──────────────────────────────────────────────────────┘
  border border-obsidian-600/50
```

**Status Badge Styles:**
```
✓ NORMAL:     bg-sage-500/10  border-sage-500/30  text-sage-300
⚠️ UNUSUAL:   bg-oatmeal-500/10 border-oatmeal-500/30 text-oatmeal-300
              (subtle pulse animation: 1s duration)
✗ CRITICAL:   bg-clay-500/10  border-clay-500/30  text-clay-300
              (stronger pulse animation with glow)
```

### Relationship Card Sub-Layout

```
┌─────────────────────────────┐
│ Icon  [Pair Names]  Badge   │ ← Header row
├─────────────────────────────┤
│ Primary Amount:   $X,XXX.XX │
│ Contra Amount:    $X,XXX.XX │
│ Ratio:            ##%       │
│ Expected Range:   ##% - ##% │
│ Health:           [Status]  │
│                             │
│ Recommendation:   ...text...│
│                             │
│ [Action] [Details]         │
└─────────────────────────────┘
```

---

## Integration: Complete Diagnostic View Layout

### Top-to-Bottom Flow (1024px Desktop)

```
┌──────────────────────────────────────────────────────────────┐
│ WORKSPACE HEADER + NAVIGATION                                │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ MATERIALITY CONTROL (Existing)                               │
│ Sensitivity Toolbar: Manual threshold adjustment             │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ KEY METRICS SECTION (Enhanced)                               │
│                                                               │
│ [Section Header] [Variance Active Badge]                     │
│                                                               │
│ ┌─ Core 4 Ratios (2x2 Grid) ─┐                              │
│ │ [Current] [Quick]           │                              │
│ │ [D/E]     [Gross Margin]     │                              │
│ └─────────────────────────────┘                              │
│                                                               │
│ [Show Advanced Ratios (4 available) ▼]                       │
│                                                               │
│ 📊 CONTRA-ACCOUNT HEALTH [▼]        ← [NEW]                │
│ [Collapsible relationship validations]                       │
│                                                               │
│ 🔥 CONCENTRATION RISK [▼]            ← [NEW]                │
│ [Collapsible heatmap bars]                                   │
│                                                               │
│ ✓ Balance Sheet Equation: A = L + E   ← [NEW]               │
│                                                               │
│ Assets: $5.2M | Liab+Equity: $5.2M |  ✓ BALANCED            │
│                                                               │
│ [Category Totals: Assets $5.2M | Liab $3.1M | Equity $2.1M] │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ RISK DASHBOARD                                               │
│                                                               │
│ [Risk Summary Header]                                        │
│ ⚠️ 12 anomalies detected | 7 high severity | 5 low severity  │
│                                                               │
│ ⚠️ SUSPENSE ACCOUNT DETECTED             ← [NEW]             │
│ [Alert card with action buttons]                             │
│                                                               │
│ Material Risks (7 items):                                    │
│ [AnomalyCard] [AnomalyCard] [AnomalyCard] ...               │
│ [Staggered entrance animation, 40ms delay]                   │
│                                                               │
│ 🔢 ROUNDING ANOMALIES (3 detected) [▼]   ← [NEW]            │
│ [Collapsible alert cards with confidence scores]            │
│                                                               │
│ Indistinct Items (5 items) [▼]                              │
│ [Low-severity anomalies, collapsible]                        │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ EXPORT SECTION                                               │
│ [Export Diagnostic Summary (PDF)] [Export Workpaper (Excel)] │
└──────────────────────────────────────────────────────────────┘
```

### Mobile Layout (375px)

```
┌────────────────────────────┐
│ MATERIALITY CONTROL        │
│ [Threshold Slider]         │
└────────────────────────────┘

┌────────────────────────────┐
│ KEY METRICS                │
│ [Stacked 1-column layout]  │
│                            │
│ [Ratio Card] [Ratio Card]  │
│ [Ratio Card] [Ratio Card]  │
│                            │
│ [Show Advanced ▼]          │
│                            │
│ 📊 HEALTH [▼]             │
│ [Collapsed]                │
│                            │
│ 🔥 RISK [▼]               │
│ [Collapsed]                │
│                            │
│ ✓ A = L + E               │
│ [Status badge]             │
│                            │
│ Category Totals            │
│ [Stacked rows]             │
└────────────────────────────┘

┌────────────────────────────┐
│ RISK DASHBOARD             │
│                            │
│ [Risk Summary]             │
│                            │
│ ⚠️ SUSPENSE [Alert]       │
│                            │
│ Material Risks (7)         │
│ [Card] [Card] ...         │
│                            │
│ 🔢 ROUNDING (3) [▼]       │
│ [Collapsed]                │
│                            │
│ Indistinct (5) [▼]        │
│ [Collapsed]                │
│                            │
└────────────────────────────┘

┌────────────────────────────┐
│ [Export PDF]               │
│ [Export Excel]             │
└────────────────────────────┘
```

---

## Responsive Breakpoints

### Tailwind Breakpoints (Existing Pattern)

| Breakpoint | Width | Layout |
|-----------|-------|--------|
| `sm` | 640px | 1-column cards, stacked ratios |
| `md` | 768px | 2-column ratios, collapsibles visible |
| `lg` | 1024px | Full 2-column grid, sidebar-ready |
| `xl` | 1280px | Full-width cards, optimal spacing |

### Concentration Risk Example (Responsive)

```
≤640px:
Account    50%
████████░░ $X.XX

≥768px:
Account Name           50% ($X,XXX.XX / $X,XXX.XX)
██████████░░░░░░░░░░░░░░░░░░░

≥1024px:
Account Name           ████████░░░░░░░░░░░░░░░░░  50%
                       $X,XXX.XX / $X,XXX.XX total
```

---

## Animation Sequence Timeline

### Page Load (5-second total)

```
0ms:   Materiality Control loads
100ms: Key Metrics fade in
150ms: Ratio cards stagger (40ms between)
  150ms: Current Ratio
  190ms: Quick Ratio
  230ms: D/E Ratio
  270ms: Gross Margin
  310ms: (Advanced ratios hidden)

300ms: Risk Dashboard header fades in
350ms: Suspense Account Alert slides in (spring animation)

400ms: Risk Summary badge animates in

450ms: High-severity AnomalyCards stagger (40ms between)
  450ms: Card 1
  490ms: Card 2
  530ms: Card 3
  ...

700ms: Rounding Anomalies button appears (collapsed)

750ms: Indistinct Items button appears (collapsed)

800ms: Export buttons fade in

≈1000ms: Page fully settled, animations complete
```

### Interaction: User Expands Concentration Risk

```
0ms:   User clicks "Concentration Risk [▼]"
0ms:   Button rotates 180° (chevron animation)

50ms:  Container height animates from 0 → auto
       opacity animates from 0 → 1

100ms: First concentration bar staggered in (20ms between bars)
  100ms: Row 1 slides left → right
  120ms: Row 2 slides left → right
  140ms: Row 3 slides left → right

200ms: Risk badge and recommendation fade in

300ms: Expansion complete, all hover states active
```

---

## Accessibility Annotations

### Keyboard Navigation Flow

```
[Tab] Cycle through interactive elements:

1. Materiality Slider (input range)
2. Show Advanced Ratios button
3. Concentration Risk button
4. Balance Equation [?] info icon
5. Suspense Account [Reassign dropdown]
6. Suspense Account [Archive button]
7. Suspense Account [Ignore button]
8. Rounding Anomalies button
9. Indistinct Items button
10. Export Diagnostic PDF button
11. Export Workpaper Excel button

[Enter/Space] on buttons: Toggle collapse/expand
[Escape] on modals: Close
[Tab] through dropdowns: Navigate options
```

### Screen Reader Landmarks

```
<main aria-label="Diagnostic Results">
  <section aria-label="Key Metrics" role="region">
    <h2>Key Metrics</h2>
    <article role="article" aria-label="Current Ratio">...</article>
  </section>

  <section aria-label="Risk Dashboard" role="region">
    <h2>Risk Dashboard</h2>
    <article role="article" aria-label="Suspense Account Alert">...</article>
    <div role="region" aria-expanded="false">
      <button aria-expanded="false">Rounding Anomalies</button>
    </div>
  </section>
</main>
```

---

## Color Palette Reference (Hex Codes)

**Oat & Obsidian System:**

```
Primary Dark:    #212121  (obsidian)
Light BG:        #EBE9E4  (oatmeal)
Error/Risk:      #BC4749  (clay)
Success:         #4A7C59  (sage)

Dark Variants:
obsidian-900:    #121212
obsidian-800:    #1e1e1e
obsidian-700:    #2a2a2a
obsidian-600:    #333333

Light Variants:
oatmeal-600:     #d4cfc2
oatmeal-500:     #e0dcd5
oatmeal-400:     #f0ede8

Status Variants:
clay-600:        #a83c3e
clay-500:        #BC4749
clay-400:        #d4585a

sage-600:        #3d6847
sage-500:        #4A7C59
sage-400:        #5a9470
```

---

## Implementation Priority & Dependencies

### Phase III Sprint Sequence

```
Sprint 40: Suspense Account Detector
├── Backend algorithm (account name fuzzy match)
├── AlertCard component
└── RiskDashboard integration

Sprint 41: Balance Sheet Equation Validator
├── Backend validator (A = L + E math)
├── Badge + Card components
└── KeyMetricsSection integration

Sprint 42: Rounding Anomaly Scanner + Concentration Risk
├── Backend rounding detection
├── Rounding alert cards
├── Concentration heatmap component
└── Integrated into RiskDashboard + KeyMetricsSection

Sprint 43: Contra-Account Validator
├── Backend relationship rules engine
├── Relationship card component
├── KeyMetricsSection integration
└── Tooltip + threshold adjustment UI
```

---

**Document Version:** 1.0
**Last Updated:** 2026-02-04
**Author:** Fintech Designer
**Status:** Ready for Implementation Review
