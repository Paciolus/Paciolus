/**
 * Paciolus Theme Utilities
 * Phase 2 Refactor: Oat & Obsidian Design System
 *
 * Centralizes theme-related class mappings and color logic.
 * Based on: skills/theme-factory/themes/oat-and-obsidian.md
 *
 * Core Colors:
 * - obsidian (#212121) - Primary dark, headers, backgrounds
 * - oatmeal (#EBE9E4) - Light backgrounds, secondary text
 * - clay (#BC4749) - Expenses, errors, alerts, abnormal balances
 * - sage (#4A7C59) - Income, success, positive states
 */

// =============================================================================
// THRESHOLD STATUS CLASSES
// =============================================================================

export type ThresholdStatus = 'above_threshold' | 'at_threshold' | 'below_threshold' | 'neutral';

/** @deprecated Use ThresholdStatus instead */
export type HealthStatus = ThresholdStatus;

export interface ThresholdClasses {
  border: string;
  bg: string;
  badge: string;
  icon: string;
  borderAccent: string;
}

/** @deprecated Use ThresholdClasses instead */
export type HealthClasses = ThresholdClasses;

/**
 * Map of threshold status to Tailwind classes.
 * Used in MetricCard, AnomalyCard, and other analytics components.
 */
export const THRESHOLD_STATUS_CLASSES: Record<ThresholdStatus, ThresholdClasses> = {
  above_threshold: {
    border: 'border-sage-200',
    bg: 'bg-sage-50',
    badge: 'bg-sage-100 text-sage-700',
    icon: 'text-sage-600',
    borderAccent: 'border-l-sage-500',
  },
  at_threshold: {
    border: 'border-oatmeal-300',
    bg: 'bg-oatmeal-50',
    badge: 'bg-oatmeal-100 text-oatmeal-700',
    icon: 'text-oatmeal-700',
    borderAccent: 'border-l-oatmeal-500',
  },
  below_threshold: {
    border: 'border-clay-200',
    bg: 'bg-clay-50',
    badge: 'bg-clay-100 text-clay-700',
    icon: 'text-clay-600',
    borderAccent: 'border-l-clay-500',
  },
  neutral: {
    border: 'border-theme',
    bg: 'bg-surface-card-secondary',
    badge: 'bg-oatmeal-100 text-content-secondary',
    icon: 'text-content-tertiary',
    borderAccent: 'border-l-oatmeal-400',
  },
};

/** @deprecated Use THRESHOLD_STATUS_CLASSES instead */
export const HEALTH_STATUS_CLASSES = THRESHOLD_STATUS_CLASSES;

/**
 * Get threshold status classes for a component.
 */
export function getThresholdClasses(status: ThresholdStatus): ThresholdClasses {
  return THRESHOLD_STATUS_CLASSES[status] || THRESHOLD_STATUS_CLASSES.neutral;
}

/** @deprecated Use getThresholdClasses instead */
export const getHealthClasses = getThresholdClasses;

/**
 * Get threshold status label for display.
 */
export function getThresholdLabel(status: ThresholdStatus): string {
  const labels: Record<ThresholdStatus, string> = {
    above_threshold: 'Above',
    at_threshold: 'Near',
    below_threshold: 'Below',
    neutral: 'N/A',
  };
  return labels[status] || 'N/A';
}

/** @deprecated Use getThresholdLabel instead */
export const getHealthLabel = getThresholdLabel;

// =============================================================================
// VARIANCE/TREND CLASSES
// =============================================================================

export type VarianceDirection = 'positive' | 'negative' | 'neutral';

/**
 * Get text color class for variance direction.
 */
export function getVarianceClasses(direction: VarianceDirection): string {
  const classes: Record<VarianceDirection, string> = {
    positive: 'text-sage-600',
    negative: 'text-clay-600',
    neutral: 'text-content-secondary',
  };
  return classes[direction] || classes.neutral;
}

// =============================================================================
// INPUT STATE CLASSES (Tier 2 Form Validation)
// =============================================================================

export type InputState = 'default' | 'error' | 'valid' | 'disabled';

/**
 * Base input classes shared across all states.
 */
export const INPUT_BASE_CLASSES =
  'w-full px-4 py-3 bg-surface-input rounded-xl text-content-primary placeholder-content-tertiary font-sans transition-all duration-200 outline-hidden';

/**
 * Input state-specific border and focus classes.
 */
export const INPUT_STATE_CLASSES: Record<InputState, string> = {
  default: 'border border-theme focus:border-sage-500 focus:ring-2 focus:ring-sage-500/20',
  error: 'border border-clay-400 focus:border-clay-500 focus:ring-2 focus:ring-clay-500/20',
  valid: 'border border-sage-400 focus:border-sage-500 focus:ring-2 focus:ring-sage-500/20',
  disabled: 'border border-theme opacity-50 cursor-not-allowed',
};

/**
 * Get input classes based on validation state.
 *
 * @param touched - Whether the field has been interacted with
 * @param hasError - Whether the field has a validation error
 * @param hasValue - Whether the field has a non-empty value
 * @param disabled - Whether the field is disabled
 */
export function getInputClasses(
  touched: boolean,
  hasError: boolean,
  hasValue: boolean = false,
  disabled: boolean = false
): string {
  if (disabled) {
    return `${INPUT_BASE_CLASSES} ${INPUT_STATE_CLASSES.disabled}`;
  }
  if (touched && hasError) {
    return `${INPUT_BASE_CLASSES} ${INPUT_STATE_CLASSES.error}`;
  }
  if (touched && !hasError && hasValue) {
    return `${INPUT_BASE_CLASSES} ${INPUT_STATE_CLASSES.valid}`;
  }
  return `${INPUT_BASE_CLASSES} ${INPUT_STATE_CLASSES.default}`;
}

/**
 * Get select input classes (always uses default state styling).
 */
export function getSelectClasses(disabled: boolean = false): string {
  const stateClass = disabled ? INPUT_STATE_CLASSES.disabled : INPUT_STATE_CLASSES.default;
  return `${INPUT_BASE_CLASSES} ${stateClass} appearance-none cursor-pointer`;
}

// =============================================================================
// BADGE CLASSES
// =============================================================================

export type BadgeVariant = 'success' | 'error' | 'warning' | 'neutral' | 'info';

/**
 * Badge variant classes for status indicators.
 */
export const BADGE_CLASSES: Record<BadgeVariant, string> = {
  success: 'bg-sage-50 text-sage-700 border border-sage-200',
  error: 'bg-clay-50 text-clay-700 border border-clay-200',
  warning: 'bg-oatmeal-100 text-oatmeal-700 border border-oatmeal-300',
  neutral: 'bg-oatmeal-50 text-content-secondary border border-theme',
  info: 'bg-surface-card-secondary text-content-secondary border border-theme',
};

/**
 * Get badge classes for a variant.
 */
export function getBadgeClasses(variant: BadgeVariant): string {
  return BADGE_CLASSES[variant] || BADGE_CLASSES.neutral;
}

// =============================================================================
// RISK LEVEL CLASSES
// =============================================================================

export type RiskLevel = 'high' | 'medium' | 'low' | 'none';

/**
 * Risk level badge classes.
 */
export const RISK_LEVEL_CLASSES: Record<RiskLevel, string> = {
  high: 'bg-clay-50 text-clay-700 border-clay-200',
  medium: 'bg-oatmeal-100 text-oatmeal-700 border-oatmeal-300',
  low: 'bg-sage-50 text-sage-700 border-sage-200',
  none: 'bg-oatmeal-50 text-content-secondary border-theme',
};

/**
 * Get risk level badge classes.
 */
export function getRiskLevelClasses(level: RiskLevel): string {
  return RISK_LEVEL_CLASSES[level] || RISK_LEVEL_CLASSES.none;
}

// =============================================================================
// ANIMATION PRESETS (framer-motion)
// =============================================================================

/**
 * Standardized spring transition presets.
 * Consolidates 10+ inline spring configs down to 4 named presets.
 */
export const SPRING = {
  /** Gentle entrances — login, register, page containers */
  gentle: { type: 'spring' as const, stiffness: 200, damping: 20 },
  /** Snappy responses — modals, cards, stagger children */
  snappy: { type: 'spring' as const, stiffness: 300, damping: 25 },
  /** Bouncy decorative — icon animations, timeline nodes */
  bouncy: { type: 'spring' as const, stiffness: 400, damping: 15 },
  /** Progress bars — slow, smooth fill */
  progress: { type: 'spring' as const, stiffness: 100, damping: 20 },
} as const

// =============================================================================
// ANIMATION VARIANTS (framer-motion)
// =============================================================================

/**
 * Standard modal overlay animation variants.
 */
export const MODAL_OVERLAY_VARIANTS = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

/**
 * Standard modal content animation variants.
 */
export const MODAL_CONTENT_VARIANTS = {
  hidden: { opacity: 0, scale: 0.95, y: 20 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { type: 'spring' as const, stiffness: 300, damping: 25 },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 20,
    transition: { duration: 0.15 },
  },
};

/**
 * Create container animation variants for staggered children.
 *
 * Use this for parent containers that animate multiple child cards/items.
 * Children should use createCardStaggerVariants() for their animations.
 *
 * @param staggerDelaySeconds - Delay between children in seconds (default: 0.05)
 * @param initialDelaySeconds - Delay before first child animates (default: 0.1)
 *
 * Sprint 41: Centralized container animation pattern
 */
export function createContainerVariants(
  staggerDelaySeconds: number = 0.05,
  initialDelaySeconds: number = 0.1
) {
  return {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: staggerDelaySeconds,
        delayChildren: initialDelaySeconds,
      },
    },
  };
}

/**
 * Pre-configured container variants for common use cases.
 * Prefer these over creating custom variants for consistency.
 */
export const CONTAINER_VARIANTS = {
  /** Fast stagger (40ms) - for small card grids (4-6 items) */
  fast: createContainerVariants(0.04, 0.1),
  /** Standard stagger (50ms) - for medium card grids (6-12 items) */
  standard: createContainerVariants(0.05, 0.1),
  /** Slow stagger (60ms) - for larger grids or marketing sections */
  slow: createContainerVariants(0.06, 0.1),
};

/**
 * Create staggered card entrance variants.
 *
 * @param index - Card index for stagger delay calculation
 * @param delayMs - Delay between cards in milliseconds (default: 40)
 */
export function createCardStaggerVariants(index: number, delayMs: number = 40) {
  return {
    hidden: {
      opacity: 0,
      y: 20,
      scale: 0.95,
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 300,
        damping: 25,
        delay: index * (delayMs / 1000),
      },
    },
  };
}

/**
 * Create timeline entry animation variants.
 * Used for ledger-style horizontal slide-in cards.
 *
 * @param index - Entry index for stagger delay calculation
 */
export function createTimelineEntryVariants(index: number) {
  return {
    hidden: {
      opacity: 0,
      x: -30,
      scale: 0.95,
    },
    visible: {
      opacity: 1,
      x: 0,
      scale: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 260,
        damping: 24,
        delay: index * 0.08, // 80ms stagger
      },
    },
  };
}

/**
 * Create timeline node animation variants.
 * Used for the circular indicators on timeline entries.
 *
 * @param index - Node index for stagger delay calculation
 */
export function createTimelineNodeVariants(index: number) {
  return {
    hidden: { scale: 0 },
    visible: {
      scale: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 400,
        damping: 20,
        delay: index * 0.08, // 80ms stagger, matches entry
      },
    },
  };
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Combine multiple class strings, filtering out falsy values.
 */
export function cx(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}
