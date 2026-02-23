/**
 * Motion Token Map — Sprint 401: Phase LVI
 *
 * Unified semantic motion vocabulary for state-linked choreography.
 * Extends existing DURATION/OFFSET tokens with intent-based timing,
 * easing curves, and framer-motion Variants for tool state transitions.
 *
 * All values complement the IntelligenceCanvas accent system —
 * canvas drives the ambient background layer; these tokens drive
 * the UI content layer.
 */

import { DURATION } from './animations'
import { OFFSET } from './marketingMotion'
import type { Variants, Transition } from 'framer-motion'

// =============================================================================
// TIMING — extends DURATION with intent-based durations
// =============================================================================

export const TIMING = {
  ...DURATION,
  /** Upload→loading→results state crossfade */
  crossfade: 0.35,
  /** Risk emphasis settling */
  settle: 0.5,
  /** Export completion deceleration */
  resolve: 0.6,
  /** Sidebar expand/collapse */
  panel: 0.25,
} as const

// =============================================================================
// EASE — cubic-bezier curves for semantic intents
// =============================================================================

export const EASE = {
  /** Standard entrance — elements appearing in view */
  enter: [0.25, 0.1, 0.25, 1.0] as const,
  /** Standard exit — elements leaving view */
  exit: [0.25, 0.0, 0.5, 1.0] as const,
  /** Export resolution settling — long deceleration tail */
  decelerate: [0.0, 0.0, 0.2, 1.0] as const,
  /** Risk detection attention — fast attack, slow settle */
  emphasis: [0.2, 0.0, 0.0, 1.0] as const,
} as const

// =============================================================================
// DISTANCE — extends OFFSET with state-transition shifts
// =============================================================================

export const DISTANCE = {
  ...OFFSET,
  /** Crossfade Y-offset between tool upload states */
  state: 8,
} as const

// =============================================================================
// STATE_CROSSFADE — Variants for UploadStatus transitions
// =============================================================================

/**
 * Vertical shared-axis crossfade for tool state transitions.
 * Old state slides up 8px + fades out, new state enters from below 8px + fades in.
 * Used by ToolStatePresence to animate between idle/loading/error/success.
 */
export const STATE_CROSSFADE = {
  initial: {
    opacity: 0,
    y: DISTANCE.state,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: TIMING.crossfade,
      ease: EASE.enter,
    } satisfies Transition,
  },
  exit: {
    opacity: 0,
    y: -DISTANCE.state,
    transition: {
      duration: TIMING.fast,
      ease: EASE.exit,
    } satisfies Transition,
  },
} as const satisfies Variants

// =============================================================================
// RESOLVE_ENTER — Variants for export completion
// =============================================================================

/**
 * Export resolution animation — subtle scale-up with deceleration.
 * Used by DownloadReportButton for the post-export "Downloaded" confirmation.
 */
export const RESOLVE_ENTER = {
  initial: {
    opacity: 0,
    scale: 0.98,
  },
  animate: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: TIMING.resolve,
      ease: EASE.decelerate,
    } satisfies Transition,
  },
  exit: {
    opacity: 0,
    scale: 0.98,
    transition: {
      duration: TIMING.fast,
      ease: EASE.exit,
    } satisfies Transition,
  },
} as const satisfies Variants

// =============================================================================
// EMPHASIS_SETTLE — Variants for risk detection elements
// =============================================================================

/**
 * Risk emphasis settle — draws attention with a brief width micro-expansion.
 * Used by FlaggedEntriesTable severity borders and ScoreCard accents.
 */
export const EMPHASIS_SETTLE = {
  initial: {
    opacity: 0,
    x: -2,
  },
  animate: {
    opacity: 1,
    x: 0,
    transition: {
      duration: TIMING.settle,
      ease: EASE.emphasis,
    } satisfies Transition,
  },
} as const satisfies Variants
