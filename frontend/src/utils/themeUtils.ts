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
// HEALTH STATUS CLASSES
// =============================================================================

export type HealthStatus = 'healthy' | 'warning' | 'concern' | 'neutral';

export interface HealthClasses {
  border: string;
  bg: string;
  badge: string;
  icon: string;
}

/**
 * Map of health status to Tailwind classes.
 * Used in MetricCard, AnomalyCard, and other analytics components.
 */
export const HEALTH_STATUS_CLASSES: Record<HealthStatus, HealthClasses> = {
  healthy: {
    border: 'border-sage-500/30',
    bg: 'bg-sage-500/5',
    badge: 'bg-sage-500/20 text-sage-300',
    icon: 'text-sage-400',
  },
  warning: {
    border: 'border-oatmeal-500/30',
    bg: 'bg-oatmeal-500/5',
    badge: 'bg-oatmeal-500/20 text-oatmeal-300',
    icon: 'text-oatmeal-400',
  },
  concern: {
    border: 'border-clay-500/30',
    bg: 'bg-clay-500/5',
    badge: 'bg-clay-500/20 text-clay-300',
    icon: 'text-clay-400',
  },
  neutral: {
    border: 'border-obsidian-600',
    bg: 'bg-obsidian-800/50',
    badge: 'bg-obsidian-600 text-oatmeal-400',
    icon: 'text-oatmeal-500',
  },
};

/**
 * Get health status classes for a component.
 */
export function getHealthClasses(status: HealthStatus): HealthClasses {
  return HEALTH_STATUS_CLASSES[status] || HEALTH_STATUS_CLASSES.neutral;
}

/**
 * Get health status label for display.
 */
export function getHealthLabel(status: HealthStatus): string {
  const labels: Record<HealthStatus, string> = {
    healthy: 'Healthy',
    warning: 'Monitor',
    concern: 'Review',
    neutral: 'N/A',
  };
  return labels[status] || 'N/A';
}

// =============================================================================
// VARIANCE/TREND CLASSES
// =============================================================================

export type VarianceDirection = 'positive' | 'negative' | 'neutral';

/**
 * Get text color class for variance direction.
 */
export function getVarianceClasses(direction: VarianceDirection): string {
  const classes: Record<VarianceDirection, string> = {
    positive: 'text-sage-400',
    negative: 'text-clay-400',
    neutral: 'text-oatmeal-500',
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
  'w-full px-4 py-3 bg-obsidian-800 rounded-xl text-oatmeal-200 placeholder-obsidian-400 font-sans transition-all duration-200 outline-none';

/**
 * Input state-specific border and focus classes.
 */
export const INPUT_STATE_CLASSES: Record<InputState, string> = {
  default: 'border-2 border-obsidian-500 focus:border-sage-500 focus:ring-2 focus:ring-sage-500/20',
  error: 'border-2 border-clay-500 focus:border-clay-400 focus:ring-2 focus:ring-clay-500/20',
  valid: 'border-2 border-sage-500/50 focus:border-sage-400 focus:ring-2 focus:ring-sage-500/20',
  disabled: 'border-2 border-obsidian-600 opacity-50 cursor-not-allowed',
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
  success: 'bg-sage-500/15 text-sage-400 border border-sage-500/30',
  error: 'bg-clay-500/15 text-clay-400 border border-clay-500/30',
  warning: 'bg-oatmeal-500/15 text-oatmeal-400 border border-oatmeal-500/30',
  neutral: 'bg-obsidian-700/50 text-oatmeal-400 border border-obsidian-600/50',
  info: 'bg-obsidian-600 text-oatmeal-300 border border-obsidian-500',
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
  high: 'bg-clay-900/50 text-clay-200 border-clay-800',
  medium: 'bg-oatmeal-900/50 text-oatmeal-200 border-oatmeal-800',
  low: 'bg-sage-900/50 text-sage-200 border-sage-800',
  none: 'bg-obsidian-700 text-oatmeal-400 border-obsidian-600',
};

/**
 * Get risk level badge classes.
 */
export function getRiskLevelClasses(level: RiskLevel): string {
  return RISK_LEVEL_CLASSES[level] || RISK_LEVEL_CLASSES.none;
}

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
