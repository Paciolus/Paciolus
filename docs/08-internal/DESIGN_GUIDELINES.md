# Paciolus Design Guidelines

> **Living document.** Update this file whenever the design system is modified — new tokens, new patterns, new metaphors, new motion vocabulary. This is the single source of truth for how Paciolus looks, feels, and moves.

**Version:** 1.0.0
**Last updated:** 2026-02-28
**Brand identity:** Oat & Obsidian
**Theme spec:** `skills/theme-factory/themes/oat-and-obsidian.md`
**Token implementations:** `frontend/src/app/globals.css`, `frontend/src/utils/themeUtils.ts`

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Color System](#2-color-system)
3. [Typography](#3-typography)
4. [Spatial Model & Card Hierarchy](#4-spatial-model--card-hierarchy)
5. [Shadow System](#5-shadow-system)
6. [Motion & Animation](#6-motion--animation)
7. [Ambient Atmosphere](#7-ambient-atmosphere)
8. [Texture & Surface Treatment](#8-texture--surface-treatment)
9. [Component Patterns](#9-component-patterns)
10. [Marketing Page Design](#10-marketing-page-design)
11. [Accessibility](#11-accessibility)
12. [Enforcement Rules](#12-enforcement-rules)
13. [Reference Files](#13-reference-files)

---

## 1. Design Philosophy

### Core Principles

**Premium Restraint** — Visual hierarchy through minimal, intentional accents. Clay-red left borders signal risk; full-background color washes are forbidden. Severity is communicated through border weight and color, never through aggressive fills or flashing elements. Restraint is the luxury signal.

**Trust & Clarity** — Financial professionals need to feel secure. Clean typography, balanced grid layouts, generous whitespace, and consistent semantic color usage build confidence. Every element earns its place; nothing is decorative without purpose.

**Anti-Slop Aesthetic** — Reject generic defaults. No Bootstrap patterns, no flat uninspired colors, no clutter, no low-contrast text. Every surface, shadow, and transition is intentionally crafted.

### Area Metaphors

These metaphors guide the *feel* of different platform areas. They are not prescriptive specs but emotional targets:

| Metaphor | Area | Ethos |
|---|---|---|
| **"Ferrari"** | Homepage / marketing pages | Cinematic, sleek, modern. Scroll-orchestrated narrative, animated data visualization, gradient atmosphere. The first impression demands attention. |
| **"Rolls Royce"** | Tool pages / workspace | Classy, trustworthy, warm. 3-tier card hierarchy, warm-toned parchment shadows, paper texture. Quiet confidence — the interface recedes so the data speaks. |
| **"The Vault"** | Dual-theme architecture | Dark exterior (obsidian workspace shell) vs. light interior (oatmeal tool content). Crossing the threshold from marketing to workspace shifts the entire tonal register. |
| **"Pacioli's Desk"** | Light theme texture system | SVG `feTurbulence` paper grain at 0.015 opacity evoking historic ledger aesthetics. The tool pages feel like working at a well-appointed desk, not staring at a screen. |
| **"Premium Restraint"** | Global design rule | Visual hierarchy through *minimal* accents — clay left-borders, sage dash accents, never aggressive fills. The most important design decision is what to leave out. |
| **"Institution-Grade Evidence"** | Proof architecture | ProofSummaryBar + ProofPanel. Weighted scoring (40/30/30), confidence badges, trace bars. The language of assurance, not dashboards. |

---

## 2. Color System

### Primary Palette

| Token | Hex | RGB | Usage |
|---|---|---|---|
| **Obsidian** | `#212121` | `33, 33, 33` | Primary text, headers, dark mode backgrounds |
| **Oatmeal** | `#EBE9E4` | `235, 233, 228` | Light backgrounds, secondary surfaces |
| **Clay** | `#BC4749` | `188, 71, 73` | Expenses, errors, alerts, abnormal balances |
| **Sage** | `#4A7C59` | `74, 124, 89` | Income, success states, positive indicators |

### Extended Scales

Each primary color has a full 50–900 scale defined in Tailwind config:

**Obsidian:** 50 (`#f5f5f5`) through 900 (`#121212`), base at 800
**Oatmeal:** 50 (`#FAFAF9`) through 500 (`#B5AD9F`), base at 200
**Clay:** 50 (`#FDF2F2`) through 700 (`#882F31`), base at 500
**Sage:** 50 (`#F2F7F4`) through 700 (`#30503A`), base at 500

### Semantic Mappings

| Context | Color | Examples |
|---|---|---|
| Primary Action | Sage | "Upload", "Analyze", "Submit" buttons |
| Destructive Action | Clay | "Delete", "Clear" buttons |
| Neutral Action | Obsidian | "Cancel", secondary buttons |
| Success State | Sage | Balanced trial balance, income accounts |
| Error State | Clay | Out of balance, expenses, abnormal flags |
| Warning State | Oatmeal + obsidian border | Materiality alerts, monitor status |
| Informational | Obsidian-400 | Tooltips, hints, neutral metadata |

### Semantic Token Variables (CSS)

Defined in `globals.css` `:root` (dark defaults) with `[data-theme="light"]` overrides:

**Surfaces:** `--surface-page`, `--surface-card`, `--surface-card-secondary`, `--surface-elevated`, `--surface-card-elevated`, `--surface-card-inset`, `--surface-input`

**Text:** `--text-primary`, `--text-secondary`, `--text-tertiary`, `--text-disabled`

**Borders:** `--border-default`, `--border-hover`, `--border-active`, `--border-divider`, `--border-hairline`

**Semantic status:** `--color-success-text`, `--color-success-bg`, `--color-success-border`, `--color-error-text`, `--color-error-bg`, `--color-error-border`

### Health Status System

Defined in `themeUtils.ts`, used across MetricCard, AnomalyCard, and analytics components:

| Status | Border | Background | Badge | Left Accent |
|---|---|---|---|---|
| `healthy` | sage-200 | sage-50 | sage-100/sage-700 | sage-500 |
| `warning` | oatmeal-300 | oatmeal-50 | oatmeal-100/oatmeal-700 | oatmeal-500 |
| `concern` | clay-200 | clay-50 | clay-100/clay-700 | clay-500 |
| `neutral` | theme border | card-secondary | oatmeal-100/secondary | oatmeal-400 |

### Dark Mode (Default — "Vault Exterior")

- Background: `#121212`
- Surface card: `rgba(48, 48, 48, 0.8)`
- Text primary: `#EBE9E4`
- Text secondary: `#C9C3B8`
- Borders: `rgba(235, 233, 228, 0.08)` — very subtle oatmeal tints
- Shadows: black-based, deep, layered

### Light Mode ("Vault Interior")

- Background: `#F5F4F2`
- Surface card: `#FFFFFF`
- Text primary: `#212121`
- Text secondary: `#616161`
- Borders: `#C8C3BA` — warm, visible
- Shadows: **warm-toned** `rgba(139, 119, 91)` — parchment-adjacent, never neutral gray
- Paper texture: SVG feTurbulence at 0.015 opacity applied to body

---

## 3. Typography

### Font Families

| Element | Font Family | Weight | Class |
|---|---|---|---|
| Headers (h1–h6) | Merriweather | 700 (Bold) | `font-serif` |
| Body text | Lato | 400 (Regular) | `font-sans` |
| Body emphasis | Lato | 700 (Bold) | `font-sans font-bold` |
| Financial data | JetBrains Mono | 400/500 | `font-mono` |

**Rule:** All `h1`–`h6` elements automatically receive `font-serif` via the base layer. Body defaults to `font-sans`. Financial numbers must use `font-mono` with `tabular-nums lining-nums` font feature settings.

### Type Scale System (5 tiers)

**Display** — Hero headlines, maximum visual weight:
- `.type-display-xl`: fluid `clamp(2.25rem, 5vw + 1rem, 4.5rem)`, tracking `-0.025em`, line-height 1.05
- `.type-display`: 4xl → 5xl → 6xl responsive, tracking `-0.025em`, line-height 1.1

**Headline** — Section headings:
- `.type-headline`: 3xl → 4xl responsive, tracking `-0.015em`, line-height 1.2
- `.type-headline-sm`: 2xl fixed, tracking `-0.01em`, line-height 1.25

**Subtitle** — Between headline and body:
- `.type-subtitle`: xl serif, tracking `-0.005em`, line-height 1.35

**Body** — Readable paragraph text:
- `.type-body-lg`: lg → xl responsive, relaxed leading
- `.type-body`: lg fixed, relaxed leading
- `.type-body-sm`: sm fixed, relaxed leading, tracking `0.005em`
- `.type-label`: sm medium sans, tracking `0.01em`

**Meta** — Labels, badges, category markers:
- `.type-meta`: xs medium uppercase tracking-widest

**Tool page patterns:**
- `.type-tool-title`: 4xl serif, headline tracking, line-height 1.15
- `.type-tool-section`: lg serif, tracking `-0.005em`, line-height 1.35

**Proof** — Mono numerics for metric proof points:
- `.type-proof`: 2xl bold mono, tabular-nums
- `.type-proof-sm`: xl semibold mono, tabular-nums

### Numeric Emphasis System (5 tiers)

Replaces ad-hoc `font-mono text-*` patterns with standardized financial data sizing:

| Class | Size | Weight | Use Case |
|---|---|---|---|
| `.type-num-xs` | xs | regular | Table cells, inline references |
| `.type-num-sm` | sm | medium | Secondary metrics, badges |
| `.type-num` | lg | regular | Standard financial figures |
| `.type-num-lg` | 2xl | bold | Primary metrics, scores |
| `.type-num-xl` | 3xl | bold | Hero numbers, key KPIs |

All include `tabular-nums lining-nums` and numeric tracking (`-0.02em`).

### Optical Tracking Variables

```css
--type-tracking-display: -0.025em;   /* Display text — tight */
--type-tracking-headline: -0.015em;  /* Headlines — slightly tight */
--type-tracking-body: 0em;           /* Body — natural */
--type-tracking-num: -0.02em;        /* Numerics — mono-optimized */
```

---

## 4. Spatial Model & Card Hierarchy

### 3-Tier Card System

| Tier | Class | Surface Token | Border | Shadow | Usage |
|---|---|---|---|---|---|
| **Standard** | `.theme-card` | `--surface-card` | `--border-default` | `--shadow-theme-card` | Default content containers |
| **Elevated** | `.card-elevated` | `--surface-card-elevated` | `--border-default` | `--shadow-theme-card-lg` | Featured/hero cards, prominent sections |
| **Inset** | `.card-inset` | `--surface-card-inset` | `--border-hairline` | `--shadow-theme-card-inset` (inset) | Nested/recessed content areas |

Additionally: `.card-premium` for hover-lift interaction (`shadow-theme-card-lg` → `shadow-theme-elevated` on hover).

### Layout Constants

- **Page container:** `pt-24 pb-16 px-6 max-w-5xl mx-auto` (`.page-container`)
- **Card rounding:** `rounded-xl` (standard/elevated), `rounded-lg` (inset)
- **Mobile breakpoints:** 375px (stack vertical), 768px (2-column grids), 1024px (full layout), 1280px+ (optimal spacing)

### Marketing Page Depth System

A-B-A rhythm for dark marketing sections:

| Class | Feel | Usage |
|---|---|---|
| `.lobby-surface-recessed` | Sunken, darkened | Alternating content sections |
| `.lobby-surface-raised` | Lifted, slightly lighter | Primary content sections |
| `.lobby-surface-accent` | Sage tint at top edge | Use once per page for emphasis |
| `.lobby-glow-sage` | Radial sage highlight | Section top halos |
| `.lobby-vignette` | Top/bottom edge darkening | Containment |
| `.lobby-divider` | Gradient fade line + sage dot | Section separators |

### Editorial Composition Utilities

| Class | Pattern |
|---|---|
| `.editorial-hero` | Centered mobile, left-aligned desktop; h1 max-width 14ch, p max-width 38ch |
| `.editorial-split` | Asymmetric 3fr/2fr text-visual split |
| `.editorial-proof-strip` | Centered metric band with even spacing |
| `.editorial-trust-claim` | Short-line centered high-impact text (max 24ch) |
| `.editorial-metric` | Vertical number+label stacking |
| `.type-contrast-word` | Mid-sentence serif emphasis (inline) |

---

## 5. Shadow System

### Dark Theme Shadows

Black-based with subtle inset highlights for edge definition:

| Token | Value | Usage |
|---|---|---|
| `--shadow-theme-card` | `0 4px 6px -1px rgba(0,0,0,0.3), 0 2px 4px -1px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.03)` | Default cards |
| `--shadow-theme-card-hover` | Deeper (8px/25px spread), stronger inset highlight (0.05) | Card hover states |
| `--shadow-theme-card-lg` | Very deep (16px/40px spread) | Elevated/featured cards |
| `--shadow-theme-elevated` | Maximum depth (12px/40px, 50% opacity) | Modals, overlays |
| `--shadow-theme-card-inset` | `inset 0 2px 4px rgba(0,0,0,0.15)` | Recessed content areas |

### Light Theme Shadows

**Warm-toned** — `rgba(139, 119, 91)` base color (parchment-adjacent), never neutral gray:

| Token | Opacity Range | Feel |
|---|---|---|
| `--shadow-theme-card` | 0.05–0.08 | Subtle, warm |
| `--shadow-theme-card-hover` | 0.07–0.12 | Slightly deeper, still warm |
| `--shadow-theme-card-lg` | 0.08–0.14 | Prominent, parchment feel |
| `--shadow-theme-elevated` | 0.08–0.16 | Maximum depth, warm |
| `--shadow-theme-card-inset` | 0.06 | Gentle recess |

---

## 6. Motion & Animation

### Duration Constants

Defined in `animations.ts`:

| Token | Value | Usage |
|---|---|---|
| `instant` | 0.15s | Tooltips, micro-interactions |
| `fast` | 0.2s | Collapsibles, toggles, interactive UI |
| `normal` | 0.3s | Standard entrances, exits |
| `slow` | 0.5s | Scroll-reveal, marketing sections |
| `hero` | 0.6s | Page hero sections |

### Intent-Based Timing (motionTokens.ts)

Extends duration constants with semantic purpose:

| Token | Value | Intent |
|---|---|---|
| `crossfade` | 0.35s | Upload → loading → results state transitions |
| `settle` | 0.5s | Risk emphasis settling into place |
| `resolve` | 0.6s | Export completion deceleration |
| `panel` | 0.25s | Sidebar expand/collapse |

### Easing Curves

| Name | Curve | Intent |
|---|---|---|
| `enter` | `[0.25, 0.1, 0.25, 1.0]` | Elements appearing in view |
| `exit` | `[0.25, 0.0, 0.5, 1.0]` | Elements leaving view |
| `decelerate` | `[0.0, 0.0, 0.2, 1.0]` | Export resolution — long deceleration tail |
| `emphasis` | `[0.2, 0.0, 0.0, 1.0]` | Risk detection — fast attack, slow settle |

### Named Animation Patterns

**STATE_CROSSFADE** — Vertical shared-axis crossfade for tool upload state transitions. Old state slides up 8px + fades, new state enters from below 8px + fades in. Used by `ToolStatePresence`.

**RESOLVE_ENTER** — Export completion animation. Subtle scale-up (0.98 → 1.0) with deceleration easing. Used by `DownloadReportButton`.

**EMPHASIS_SETTLE** — Risk detection emphasis. Brief horizontal micro-expansion (-2px → 0) with fast attack/slow settle. Used by `FlaggedEntriesTable` severity borders and `TestingScoreCard`.

### Spring Presets (themeUtils.ts)

| Name | Config | Usage |
|---|---|---|
| `gentle` | Low stiffness, high damping | Lightweight items, badges |
| `snappy` | Higher stiffness, moderate damping | Cards, default entrance |
| `bouncy` | High stiffness, low damping | Decorative icon interactions |
| `progress` | Moderate stiffness | Data bar fills |

### Marketing Motion (marketingMotion.tsx)

**Entrance variants:** `fadeUp` (24px), `fadeUpSubtle` (12px), `fadeUpDramatic` (40px + scale 0.93), `slideFromLeft`, `slideFromRight`, `clipReveal` (top-down wipe)

**Stagger containers:** `fast` (60ms children, 100ms delay) for pills/badges, `standard` (100ms children, 150ms delay) for cards/grids

**Viewport configs:** `default` (-80px margin, once), `eager` (-40px margin, once)

**Hover variants:** `lift` (y: -6px) for cards, `iconPulse` (scale 1.1, rotate 3deg) for decorative icons

**Shared-axis transitions:** `horizontal` (x: 20 → 0 → -20) for tab switches, `vertical` (y: 12 → 0 → -8) for content switches

### Animation Rules

1. **Stagger delays between items:** 20–50ms (40–50ms for card lists, 20–30ms for grouped items)
2. **No pulsing/breathing** unless critical severity (clay-pulse for high-severity anomaly cards is the one exception — limited to 3 cycles)
3. **Sage pulse** (`.animate-sage-pulse`): 3s infinite, for Zero-Storage banner highlight only
4. **Spring for alert components:** damping 25, stiffness 300
5. **Height animations for accordions:** easeInOut, 250–300ms
6. **All animations must respect `prefers-reduced-motion`** — either via framer-motion's `MotionConfig` or the `useReducedMotion` hook

---

## 7. Ambient Atmosphere

### IntelligenceCanvas

A 4-layer hybrid Canvas 2D + CSS particle system providing ambient background atmosphere:

**Layer stack (bottom to top):**
1. **DepthLayers** — CSS radial gradients for spatial depth
2. **ParticleField** — Canvas 2D flowing particles using sine-based flow fields
3. **AccentGlow** — framer-motion animated glow responding to application state
4. **Noise grain** — CSS texture overlay

**Architecture:** Fixed positioning, `pointer-events: none`, `aria-hidden="true"`. Hidden entirely under `prefers-reduced-motion: reduce`.

### Variant Configurations

| Variant | Particle Count | Color | Max Opacity | Blend | Trail | Usage |
|---|---|---|---|---|---|---|
| `marketing` | 60–80 | Oatmeal (235, 233, 228) | 8% | soft-light | 2-frame ghosting (0.92) | Homepage, marketing pages |
| `workspace` | 30–40 | Sage (74, 124, 89) | 4% | multiply | None | Workspace shell |
| `tool` | 25–35 | Sage (74, 124, 89) | 3% | multiply | None | Tool pages — near-invisible |

Mobile: particle count reduced ~40% on screens < 768px.

### Accent State System

The canvas responds to application state via `CanvasAccentContext`, wired to all 12 tool pages:

| State | Glow Color | Opacity | Speed | Effect |
|---|---|---|---|---|
| `idle` | Sage | 0.02 | 1.0x | Baseline |
| `upload` | Sage | 0.06 | 1.2x | Brightened, slightly faster |
| `analyze` | Sage | 0.04 | 1.5x | Faster, pulsing, scaled 1.1x |
| `validate` | Sage | 0.05 | 0.8x | Slower, settling |
| `export` | Oatmeal | 0.03 | 0.6x | Warm, slow — completion feel |

### Canvas Theme Tokens (CSS)

```css
/* Dark (default) */
--canvas-particle-rgb: 235, 233, 228;     /* oatmeal particles */
--canvas-particle-opacity: 0.08;
--canvas-blend-particle: soft-light;

/* Light */
--canvas-particle-rgb: 74, 124, 89;       /* sage particles */
--canvas-particle-opacity: 0.04;
--canvas-blend-particle: multiply;
```

---

## 8. Texture & Surface Treatment

### Paper Texture ("Pacioli's Desk")

Light theme only. SVG `feTurbulence` fractalNoise applied to the `<body>` element at 0.015 opacity. Creates a subtle organic grain evoking ledger paper. Disabled under `prefers-reduced-motion`.

Available as a utility class: `.paper-texture`

### Grain Overlay

`.grain-overlay::after` — fractalNoise at 0.04 opacity with `mix-blend-mode: overlay`. Used for cinematic depth on dark sections.

### Noise Background

`.bg-gradient-obsidian` — Obsidian base with noise texture overlay + vertical gradient (dark → obsidian → slightly lighter → dark). Used for primary dark backgrounds.

### Ledger Divider

`.divider-ledger::after` — Thin horizontal rule with gradient-fade edges (transparent at both ends). Evokes ruled ledger paper.

### Section Divider

`.lobby-divider` — Gradient fade line with centered sage dot (6px, 40% opacity) and subtle glow. Used between marketing page sections.

---

## 9. Component Patterns

### Signature Visual Patterns

**Left-border accents** — Health/risk color-coded left borders on MetricCard, MatchSummaryCards, MovementSummaryCards, FlaggedEntriesTable, WorkspaceHeader, and others. Uses `border-l-4` with health status color. This is the primary risk-communication pattern.

**Heading accent** (`.heading-accent`) — Section heading with sage dash overlay. A 2rem sage line positioned at the bottom border, left-aligned. Signals section boundaries with brand color.

**Drop-zone sage glow** — File upload areas with sage radial gradient background and glowing border on hover/drag (`box-shadow: 0 0 0 4px rgba(74, 124, 89, 0.06)` on hover, 0.12 when dragging).

**Skeleton shimmer** — Loading state shimmer with translateX animation across placeholder elements.

**Maker's mark** (`.makers-mark`) — Small caps serif text in oatmeal-500, tracking-widest. Used for signature/attribution flourishes.

### Button Patterns

| Class | Style | Usage |
|---|---|---|
| `.btn-primary` | Sage-600 background, white text, rounded-xl, shadow-lg | Primary actions |
| `.btn-secondary` | Surface card background, oatmeal-300 border, rounded-xl | Secondary actions |

### Status Communication

- **Never** use full background color washes for status
- **Always** pair color with text/icon (no color-only indicators)
- Risk/severity communicated via left-border color + weight
- Status patterns: `bg-[color]-500/10 border-[color]-500/30 text-[color]-300` (dark) or `-700` (light)

### Proof Architecture

Two components for institution-grade evidence display:

**ProofSummaryBar** — Horizontal 4-metric evidence strip. Each metric shows a count-up number with label. Uses `type-num-*` classes.

**ProofPanel** — Collapsible detail panel with trace bar (visual progress), test result table, and confidence badge. Weighted scoring: 40% pass rate / 30% coverage / 30% data quality.

Adapters exist for all 9 testing tools, each mapping tool-specific results to the universal proof format.

---

## 10. Marketing Page Design

### Hero Section

Cinematic hero with `HeroVisualization` (floating financial data, animated elements, SVG connection lines). Fluid display typography (`type-display-xl` with `clamp()`). Scroll-orchestrated narrative flow.

### Section Rhythm

Alternating A-B-A surface pattern using lobby utilities:
1. Recessed section (sunken)
2. Accent section (sage tint — use once)
3. Raised section (lifted)

Each section separated by `.lobby-divider` with centered sage dot.

### Key Marketing Components

- **FeaturePillars** — Per-pillar accent colors, count-up numbers, scroll-triggered entrance
- **ProductPreview** — Glass-morphism tabs, AnimatePresence crossfade, layoutId animated indicator
- **ToolShowcase** — 4-column categorized grid, featured tool sage treatment, social proof count-up
- **ProofStrip** — 4-metric evidence band (tools, tests, coverage, file formats)
- **SectionReveal** — Directional scroll-reveal wrapper (up/left/right)
- **CountUp** — Animated number counter, 40 frames at ~33fps, reduced-motion compliant

### Scroll Behavior

- `scroll-behavior: smooth` on `<html>`
- Viewport intersection margins: -80px (default sections), -40px (eager/small elements)
- `once: true` on all scroll triggers — animations play once, don't reverse

---

## 11. Accessibility

### Standards

- **WCAG 2.1 AA** baseline, AAA in several areas
- **Color contrast:** 4.5:1 for body text, 3:1 for large text and UI components
- **Touch targets:** minimum 48px x 48px on mobile
- **No color-only indicators:** always pair color with text or icon

### ARIA Patterns

- **Modals:** `role="dialog"`, `aria-modal="true"`, `aria-labelledby`
- **Expandables:** `aria-expanded` + `aria-controls` on trigger
- **Live regions:** `role="alert"` for errors (assertive), `aria-live="polite"` for status
- **Tabs:** `tablist`/`tab`/`tabpanel` pattern with `aria-selected`

### Focus Management

- `useFocusTrap` hook for all modals and overlays (auto-focus, Tab wrapping, Escape, focus restoration)
- `focus-visible:` prefix (not `focus:`) — mouse clicks do not trigger outlines
- Standard ring: `focus-visible:ring-2 focus-visible:ring-sage-500`

### Keyboard Navigation

| Shortcut | Action |
|---|---|
| `Cmd+K` | Open command palette |
| `Cmd+[` | Collapse left sidebar |
| `Cmd+]` | Collapse right sidebar |
| `Cmd+1` | Navigate to Portfolio |
| `Cmd+2` | Navigate to Engagements |
| `Escape` | Close active overlay |

### Reduced Motion

- framer-motion: `<MotionConfig reducedMotion="user">` in root layout
- `useReducedMotion` hook for non-framer animations (Canvas rAF, CountUp intervals)
- CSS: `@media (prefers-reduced-motion: reduce)` disables keyframe animations, hides canvas, removes textures
- IntelligenceCanvas: hidden entirely via `display: none` on the `<canvas>` element

### ESLint Enforcement

`eslint-plugin-jsx-a11y` with `recommended` ruleset. Key rules enforced as errors:
- `alt-text` — all `<img>` need `alt`
- `anchor-is-valid` — no `<a href="#" onClick>`, use `<button>`
- `click-events-have-key-events` — all `onClick` need `onKeyDown`
- `no-static-element-interactions` — non-interactive elements need `role`
- `label-has-associated-control` — form inputs must have associated labels

### New Component Checklist

Before adding any interactive component:

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

---

## 12. Enforcement Rules

### Color Enforcement

1. **NO** generic Tailwind colors: `slate-*`, `blue-*`, `green-*`, `red-*`, `gray-*`, `zinc-*`, `purple-*`
2. **USE** theme tokens: `obsidian-*`, `oatmeal-*`, `clay-*`, `sage-*`
3. **SUCCESS** states always use `sage-*` (never `green-*`)
4. **ERROR/EXPENSE** states always use `clay-*` (never `red-*`)
5. **Never use raw hex values** in component code — always use Tailwind tokens or CSS custom properties

### Typography Enforcement

6. **Headers** (`h1`–`h6`) must use `font-serif` (enforced in CSS base layer)
7. **Financial numbers** must use `font-mono` or `type-num-*` classes
8. **Body text** uses `font-sans` (default)
9. **Use type scale classes** (`type-display`, `type-headline`, etc.) instead of ad-hoc `text-*` sizing for any prominent text

### Component Enforcement

10. **Left-border accents** for risk/severity — never full-background color fills
11. **Warm shadows** in light theme — `rgba(139, 119, 91)`, never neutral gray
12. **Card hierarchy** — use the 3-tier system (standard/elevated/inset), don't invent new tiers
13. **Semantic tokens** — use CSS custom properties (`var(--surface-card)`) instead of hardcoded values for any theme-dependent property

### Motion Enforcement

14. **All animations must respect `prefers-reduced-motion`**
15. **No infinite animations** except `.animate-sage-pulse` (Zero-Storage banner)
16. **Clay pulse limited to 3 cycles** for high-severity alerts
17. **Use motion token vocabulary** (`TIMING`, `EASE`, `STATE_CROSSFADE`, etc.) instead of ad-hoc values

---

## 13. Reference Files

### Primary Sources

| File | Contains |
|---|---|
| `skills/theme-factory/themes/oat-and-obsidian.md` | Master brand identity, color palette, typography, semantic mappings |
| `frontend/src/app/globals.css` | CSS custom properties, component classes, type scale, editorial utilities, textures |
| `frontend/src/utils/themeUtils.ts` | Health status classes, spring presets, badge/input/risk variant mappings |
| `frontend/src/utils/motionTokens.ts` | Intent-based timing, easing curves, state-linked animation variants |
| `frontend/src/utils/animations.ts` | Base animation presets (fadeInUp, fadeIn), duration constants |
| `frontend/src/utils/marketingMotion.tsx` | Marketing-specific entrance/stagger/hover/axis variants, CountUp, SectionReveal |
| `frontend/src/components/shared/IntelligenceCanvas/canvasConfig.ts` | Particle system configuration, variant configs, accent state configs |
| `docs/accessible-components.md` | WCAG compliance patterns, ARIA reference, focus management, component checklist |

### Design Phase Archives

Detailed sprint-by-sprint design evolution records in `tasks/archive/`:

| Archive File | Phase | Topic |
|---|---|---|
| `phase-xlii-details.md` | Design Foundation Fixes | Shadow/border token repair, opacity/contrast audit, semantic token migration |
| `phase-xliii-details.md` | "Ferrari" Homepage | Cinematic hero, gradient mesh, scroll narrative, product preview, tool grid |
| `phase-xliv-details.md` | "Rolls Royce" Tool Pages | 3-tier cards, warm shadows, heading accents, paper texture, sage drop-zone glow |
| `phase-lvi-details.md` | State-Linked Motion | Motion token map, tool state choreography, risk emphasis, shared-axis transitions |
| `phase-lvii-details.md` | Premium Moments | Feature flags, sonification, contextual microcopy, intelligence watermark |
| `docs/phase-iii/PHASE_III_DESIGN_SUMMARY.md` | Diagnostic Feature Design | 3-tier hierarchy, premium restraint rules, animation timing, responsive breakpoints |

### Agent & Skill Documents

| File | Purpose |
|---|---|
| `.claude/agents/designer.md` | Fintech Designer agent — anti-slop philosophy, premium trust aesthetic |
| `.claude/skills/frontend-design/SKILL.md` | Frontend design skill — creative direction, typography, motion, composition, anti-patterns |

---

## Maintenance Protocol

When modifying the design system:

1. **Update this document** with the change (new token, new pattern, new metaphor)
2. **Update the relevant source file** (globals.css, themeUtils.ts, motionTokens.ts, etc.)
3. **If a new metaphor or philosophy shift**, add it to Section 1
4. **If new colors or tokens**, add to Section 2 and update `oat-and-obsidian.md`
5. **If new motion patterns**, add to Section 6 and update `motionTokens.ts`
6. **If new component patterns**, add to Section 9
7. **If accessibility changes**, update Section 11 and `docs/accessible-components.md`
8. **Version bump** the document version at the top
9. **Update `Last updated` date** at the top
