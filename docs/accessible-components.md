# Accessible Components Guide

> Contributor reference for WCAG 2.1 AA compliance in the Paciolus frontend.

---

## ARIA Attributes

### Dialogs & Modals

Every modal must declare dialog semantics:

```tsx
<div role="dialog" aria-modal="true" aria-labelledby="dialog-title">
  <h2 id="dialog-title">Edit Client</h2>
  {/* ... */}
</div>
```

Backdrop overlays use `role="presentation"` (never `role="button"`).

### Expandable Sections

Collapsible panels use `aria-expanded` on the trigger:

```tsx
<button aria-expanded={isOpen} aria-controls="panel-id" onClick={toggle}>
  Section Title
</button>
<div id="panel-id" hidden={!isOpen}>
  {/* content */}
</div>
```

### Live Regions

Status updates that appear without user action use `role="alert"` or `aria-live`:

```tsx
<p role="alert">{errorMessage}</p>
<div aria-live="polite">{statusText}</div>
```

Use `role="alert"` for errors/warnings (assertive). Use `aria-live="polite"` for non-urgent status changes.

### Tabs

Tab interfaces use the tablist/tab/tabpanel pattern:

```tsx
<div role="tablist" aria-label="Settings">
  <button role="tab" aria-selected={active === 0} aria-controls="panel-0">General</button>
  <button role="tab" aria-selected={active === 1} aria-controls="panel-1">Security</button>
</div>
<div role="tabpanel" id="panel-0" aria-labelledby="tab-0">{/* ... */}</div>
```

---

## Focus Management

### useFocusTrap

Location: `src/hooks/useFocusTrap.ts`

Traps keyboard focus inside modal containers. Used in all modals and the command palette.

```tsx
import { useFocusTrap } from '@/hooks/useFocusTrap';

function MyModal({ isOpen, onClose }: Props) {
  const containerRef = useFocusTrap(isOpen, onClose);

  if (!isOpen) return null;

  return (
    <div ref={containerRef} role="dialog" aria-modal="true">
      {/* focusable content */}
    </div>
  );
}
```

Behavior:
- Auto-focuses the first focusable element on open
- Tab / Shift+Tab wrap within the container
- Escape calls `onClose`
- Restores focus to the trigger element on close

### Focus-visible

Interactive elements should show focus outlines. Use Tailwind's `focus-visible:` prefix (not `focus:`) so mouse clicks don't trigger outlines:

```tsx
<button className="focus-visible:ring-2 focus-visible:ring-sage-500">
```

---

## Keyboard Navigation

### Global Shortcuts

Registered in `src/hooks/useKeyboardShortcuts.ts`:

| Shortcut | Action |
|----------|--------|
| `Cmd+K` | Open command palette |
| `Cmd+[` | Collapse left sidebar |
| `Cmd+]` | Collapse right sidebar |
| `Cmd+1` | Navigate to Portfolio |
| `Cmd+2` | Navigate to Engagements |
| `Escape` | Close active overlay |

### Component-Level Patterns

**Clickable non-button elements** must be keyboard-accessible:

```tsx
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }}
>
```

**Custom checkboxes** need explicit roles:

```tsx
<div
  role="checkbox"
  aria-checked={checked}
  tabIndex={0}
  onClick={toggle}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggle();
    }
  }}
/>
```

**Hover-only interactions** must have focus parity:

```tsx
<button
  onMouseOver={show}
  onMouseOut={hide}
  onFocus={show}
  onBlur={hide}
>
```

---

## Reduced Motion

### useReducedMotion

Location: `src/hooks/useReducedMotion.ts`

Wraps framer-motion's hook for non-framer animations (Canvas rAF, CountUp intervals):

```tsx
import { useReducedMotion } from '@/hooks/useReducedMotion';

function AnimatedComponent() {
  const { prefersReducedMotion, motionSafe } = useReducedMotion();

  if (!motionSafe) return <StaticFallback />;
  return <AnimatedVersion />;
}
```

### CSS Compliance

The IntelligenceCanvas is hidden via CSS when reduced motion is preferred:

```css
@media (prefers-reduced-motion: reduce) {
  .intelligence-canvas { display: none; }
}
```

framer-motion components automatically respect `<MotionConfig reducedMotion="user">` (configured in the root layout).

---

## ESLint Enforcement

The `eslint-plugin-jsx-a11y` plugin is enabled with the `recommended` ruleset. Key rules:

| Rule | Severity | Notes |
|------|----------|-------|
| `jsx-a11y/alt-text` | error | All `<img>` need `alt` |
| `jsx-a11y/anchor-is-valid` | error | No `<a href="#" onClick>` — use `<button>` |
| `jsx-a11y/click-events-have-key-events` | error | All `onClick` need `onKeyDown` |
| `jsx-a11y/no-static-element-interactions` | error | Non-interactive elements need `role` |
| `jsx-a11y/label-has-associated-control` | error | `assert: "either"`, `depth: 3` |

### Common Violations

1. **File drop zones**: Must have `role="button"`, `tabIndex={0}`, and `onKeyDown`
2. **Anchor-as-button**: Replace `<a href="#" onClick={fn}>` with `<button onClick={fn}>`
3. **Missing label association**: Use `htmlFor`/`id` or nest the `<input>` inside `<label>`
4. **Decorative images**: Use `aria-hidden="true"` on icons that don't convey meaning

---

## New Component Checklist

Before submitting a new interactive component:

- [ ] All interactive elements are focusable (native `<button>`/`<a>` or `tabIndex={0}` + `role`)
- [ ] Keyboard activation: Enter and Space trigger actions on non-native elements
- [ ] Focus trap: Modals/overlays use `useFocusTrap`
- [ ] Focus visible: `focus-visible:ring-*` classes on interactive elements
- [ ] ARIA: Dialogs have `role="dialog"` + `aria-modal` + `aria-labelledby`
- [ ] ARIA: Expandables have `aria-expanded` + `aria-controls`
- [ ] ARIA: Status updates use `role="alert"` or `aria-live`
- [ ] Images/icons: Decorative elements have `aria-hidden="true"`, informative ones have `alt`
- [ ] Labels: Form controls have associated `<label>` (via `htmlFor`/`id` or nesting)
- [ ] Hover parity: `onMouseOver`/`onMouseOut` paired with `onFocus`/`onBlur`
- [ ] Reduced motion: Animations respect `useReducedMotion` or framer-motion's `MotionConfig`
- [ ] ESLint: `npm run lint` passes with zero warnings
