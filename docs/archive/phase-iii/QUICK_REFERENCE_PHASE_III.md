# Phase III Quick Reference Card
## For Developers During Implementation

**Print this page or bookmark for quick lookup while coding.**

---

## Color Quick Reference

```
✓ Success:    bg-sage-500/10       border-sage-500/30       text-sage-300
⚠️ Warning:    bg-oatmeal-500/10    border-oatmeal-500/30    text-oatmeal-300
✗ Error:      bg-clay-500/10       border-clay-500/30       text-clay-300
ℹ️ Info:       bg-obsidian-700/50   border-obsidian-600/50   text-oatmeal-400
```

**Typography:**
- Headers: `font-serif` (Merriweather)
- Body: `font-sans` (Lato)
- Financial: `font-mono` (JetBrains Mono)

**Premium Restraint Rule:**
- ✓ Left border: `border-l-4 border-l-clay-500`
- ✗ Full background: Never use `bg-clay-500/50`
- ✓ Subtle layers: `bg-obsidian-800/40` with `border-obsidian-600/50`

---

## Component Checklist

### Per Feature (5 Total)

**Sprint 40: Suspense Account Detector**
- [ ] `SuspenseAccountAlert.tsx` component
- [ ] Placed in RiskDashboard (before anomaly cards)
- [ ] Animation: Spring entrance (100ms delay)
- [ ] Actions: Reassign, Archive, Ignore
- [ ] Colors: Clay red left border

**Sprint 41: Balance Sheet Equation**
- [ ] `BalanceSheetEquation.tsx` component
- [ ] Badge state (balanced, rounding, error)
- [ ] Expandable card for warnings
- [ ] Placed in KeyMetrics footer
- [ ] Colors: Sage (success), Oatmeal (warning), Clay (error)

**Sprint 42: Concentration Risk**
- [ ] `ConcentrationRisk.tsx` main component
- [ ] `ConcentrationBar.tsx` sub-component
- [ ] Collapsible section in KeyMetrics
- [ ] Gradient bars: Sage → Oatmeal → Clay
- [ ] Hover tooltips with amounts
- [ ] Animation: 20ms stagger per bar

**Sprint 42: Rounding Anomalies**
- [ ] `RoundingAnomalyCards.tsx` main component
- [ ] Individual `RoundingAnomalyCard.tsx` sub-component
- [ ] Collapsible section in RiskDashboard
- [ ] Actions: "Likely Cause", "Flag for Audit", "Ignore"
- [ ] Confidence % display
- [ ] Animation: 30ms stagger per card

**Sprint 43: Contra-Account Validator**
- [ ] `ContraAccountRelationships.tsx` main component
- [ ] `RelationshipCard.tsx` sub-component
- [ ] Collapsible section in KeyMetrics
- [ ] Status badges: Normal (sage), Unusual (oatmeal), Critical (clay)
- [ ] Formula tooltips on hover
- [ ] Animation: 25ms stagger per card

---

## Animation Timing

### Entrance Delays (when page loads)
```
0ms:    Page starts rendering
100ms:  Suspense Alert fades in (spring)
150ms:  Equation Badge fades in
200ms:  Concentration Risk button visible
250ms:  Rounding Anomalies button visible
300ms:  Contra-Account button visible
```

### Stagger Between Items (when collapsible expands)
```
Concentration bars:    20ms between each row
Rounding cards:        30ms between each card
Contra-account cards:  25ms between each card
```

### Duration of Animations
```
Spring entrance:       400ms (damping: 25, stiffness: 300)
Fade in:              300ms (easeOut)
Accordion expand:     250-300ms (easeInOut)
Chevron rotate:       200ms (linear)
```

---

## TypeScript Patterns

### Import Types
```typescript
import type {
  SuspenseAccountAlert,
  BalanceSheetEquation,
  ConcentrationRisk,
  RoundingAnomaly,
  ContraAccountRelationship
} from '@/types/diagnostics'

import type {
  AccountType,
  AbnormalBalanceExtended
} from '@/types/mapping'
```

### Component Props Template
```typescript
interface FeatureComponentProps {
  data: DataType           // Main data object
  index: number           // For staggered animations
  disabled?: boolean      // Disable interactions
  onAction: (param: T) => void  // Callback
}
```

### Animation Variant Template
```typescript
const cardVariants = {
  hidden: { opacity: 0, x: -20, scale: 0.95 },
  visible: {
    opacity: 1,
    x: 0,
    scale: 1,
    transition: {
      type: 'spring' as const,
      stiffness: 300,
      damping: 25,
      delay: index * 0.05,  // Or fixed: 0.1
    },
  },
}

// Usage
<motion.div
  variants={cardVariants}
  initial="hidden"
  animate="visible"
>
  Content
</motion.div>
```

---

## Common Patterns

### Collapsible Section
```typescript
const [isOpen, setIsOpen] = useState(false)

<button onClick={() => setIsOpen(!isOpen)}>
  Label [▼]
</button>

<AnimatePresence>
  {isOpen && (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.25 }}
      className="overflow-hidden"
    >
      Content
    </motion.div>
  )}
</AnimatePresence>
```

### Staggered Container
```typescript
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.03,  // or 0.02, 0.04
      delayChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 },
}

<motion.div variants={containerVariants} initial="hidden" animate="visible">
  {items.map((item, i) => (
    <motion.div key={i} variants={itemVariants}>
      {item}
    </motion.div>
  ))}
</motion.div>
```

### Hover Tooltip
```typescript
const [showTooltip, setShowTooltip] = useState(false)

<div
  onMouseEnter={() => setShowTooltip(true)}
  onMouseLeave={() => setShowTooltip(false)}
>
  <button>Content</button>

  <AnimatePresence>
    {showTooltip && (
      <motion.div
        initial={{ opacity: 0, y: 8, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 8, scale: 0.95 }}
        transition={{ duration: 0.15 }}
        className="absolute bg-obsidian-900 border border-obsidian-600 rounded p-2"
      >
        Tooltip content
      </motion.div>
    )}
  </AnimatePresence>
</div>
```

---

## Backend Patterns (Python)

### Detector Class Template
```python
class MyDetector:
    """Description of what this detects"""

    THRESHOLD = 0.90  # Configurable threshold

    @classmethod
    def detect(cls, trial_balance: List[Dict]) -> List[Result]:
        """Main entry point - always returns a list"""
        results = []

        for row in trial_balance:
            if cls._should_flag(row):
                results.append(Result(
                    account=row.get('account_name'),
                    amount=row.get('balance'),
                    confidence=cls._calculate_confidence(row),
                    reason="Why this was flagged"
                ))

        return results

    @classmethod
    def _calculate_confidence(cls, row: Dict) -> float:
        """Score 0-1 based on heuristics"""
        score = 0.5
        # Boost/reduce based on properties
        return min(0.99, max(0.0, score))
```

### API Endpoint Template
```python
@router.post("/diagnostics/advanced-signals")
async def run_diagnostics(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
) -> dict:
    try:
        trial_balance = await parse_file(file)

        result = {
            'status': 'success',
            'suspense_accounts': [...],
            'balance_sheet_equation': {...},
            # ... etc
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Testing Patterns

### Backend Unit Test
```python
def test_detector_with_data():
    tb = [
        {'account_name': 'Test', 'balance': 5000, 'category': 'asset'}
    ]

    results = MyDetector.detect(tb)

    assert len(results) == 1
    assert results[0].account == 'Test'
    assert results[0].confidence >= 0.90
```

### Frontend Component Test
```typescript
it('renders component correctly', () => {
  render(
    <MyComponent
      data={mockData}
      onAction={jest.fn()}
    />
  )

  expect(screen.getByText('Expected Text')).toBeInTheDocument()
})

it('calls callback on action', () => {
  const onAction = jest.fn()

  render(<MyComponent data={mockData} onAction={onAction} />)
  fireEvent.click(screen.getByText('Button'))

  expect(onAction).toHaveBeenCalled()
})
```

---

## Accessibility Checklist

Per component, verify:
- [ ] No color-only status indication (pair with icon)
- [ ] `aria-expanded` on collapsible buttons
- [ ] `aria-label` on icon-only buttons
- [ ] Keyboard: Tab navigation works
- [ ] Keyboard: Enter/Space activates buttons
- [ ] Keyboard: Escape closes modals
- [ ] Focus: Visible outline on interactive elements
- [ ] Screen reader: Semantic HTML (`<button>`, `<section>`, etc.)
- [ ] Contrast: 4.5:1 for text, 3:1 for UI

---

## File Locations

### Backend
- Detection algorithms: `backend/advanced_detectors.py` (create new)
- Models: `backend/models.py` (add classes)
- API routes: `backend/main.py` (add endpoint)
- Tests: `backend/tests/test_advanced_detectors.py` (create new)

### Frontend
- TypeScript types: `frontend/src/types/diagnostics.ts` (create new)
- Components: `frontend/src/components/risk/` (Suspense, Rounding)
- Components: `frontend/src/components/analytics/` (Balance, Concentration, Contra)
- Tests: `frontend/src/components/__tests__/` (add tests)

---

## Key Design Files

| File | Purpose |
|------|---------|
| `UI_DESIGN_SPEC_PHASE_III.md` | Full specification (100+ pages) |
| `UI_MOCKUPS_PHASE_III.md` | ASCII mockups for all features |
| `IMPLEMENTATION_GUIDE_PHASE_III.md` | Code templates + data structures |
| `PHASE_III_DESIGN_SUMMARY.md` | Executive summary (this briefing) |
| `QUICK_REFERENCE_PHASE_III.md` | This file (quick lookup) |

**All in:** `D:\Dev\Paciolus\`

---

## Common Mistakes to Avoid

```
✗ Wrong: bg-clay-500/50 (full background alert)
✓ Correct: border-l-4 border-l-clay-500 (left border only)

✗ Wrong: Using blue-500, red-600, green-400 (generic Tailwind)
✓ Correct: Using clay-500, sage-500, oatmeal-500 (design system)

✗ Wrong: No icon + color for status
✓ Correct: Icon (✓/⚠️/✗) + color + text

✗ Wrong: 100ms stagger for 10 items (feels slow)
✓ Correct: 30-40ms stagger (snappier)

✗ Wrong: Collapsible starts open (clutters view)
✓ Correct: Collapsible starts closed (low friction)

✗ Wrong: Storing financial data in state
✓ Correct: Session-only state, no persistence

✗ Wrong: No keyboard accessibility
✓ Correct: Tab navigation, aria- attributes
```

---

## Debugging Tips

### Animation Not Working?
```
1. Check AnimatePresence is imported: import { AnimatePresence }
2. Verify variants are defined correctly
3. Check transition timing (duration in seconds: 0.25 = 250ms)
4. Look for z-index issues (modal backdrop covering content)
5. Check React/framer-motion version match
```

### Component Not Rendering?
```
1. Verify data structure matches TypeScript interface
2. Check for null/undefined values in template strings
3. Verify parent component passes required props
4. Check console for errors
5. Ensure imports are correct
```

### Styling Not Applied?
```
1. Check Tailwind classes are spelled correctly
2. Verify using Oat & Obsidian tokens (not generic colors)
3. Check specificity conflicts (inline styles vs classes)
4. Ensure global.css has @tailwind directives
5. Rebuild if needed: npm run dev
```

---

## Quick Commands

```bash
# Frontend build check
cd frontend && npm run build

# Frontend tests
npm run test

# Backend tests
cd backend && pytest tests/test_advanced_detectors.py

# Code formatting
npm run lint  # Frontend
black .       # Backend (Python)
```

---

**Print this page.** Reference during daily standups and implementation.

**Last Updated:** 2026-02-04
**Version:** 1.0
**Owner:** Fintech Designer
