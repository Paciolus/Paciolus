'use client'

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'

/**
 * Button — shared primary/secondary/ghost button primitive.
 *
 * Sprint 771a: Extracted from the ~30 hand-rolled `bg-sage-600 …` and
 * `bg-surface-card border border-oatmeal-300 …` class-string copies
 * across tool pages. Brand-token migrations (Oat & Obsidian) and
 * disabled-state changes now happen in one place.
 *
 * Primary  → sage-600 fill, oatmeal-50 text. Use for the page's main
 *            commit-the-action button (Run, Export, Generate).
 * Secondary→ surface-card fill, oatmeal-300 border. Use for tertiary
 *            actions sitting alongside primary (Cancel, New Test).
 * Ghost    → transparent fill, oatmeal-300 border, hover lights up.
 *            Use for inline toolbar actions where primary fill would
 *            be visual noise.
 *
 * Sizes:
 *   sm → text-xs, px-3 py-1.5
 *   md → text-sm, px-4 py-2  (default)
 *   lg → text-sm, px-8 py-3, rounded-xl  (hero CTA, e.g. "Run AR Aging")
 */

type ButtonVariant = 'primary' | 'secondary' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  children: ReactNode
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    'bg-sage-600 border border-sage-600 text-oatmeal-50 hover:bg-sage-700',
  secondary:
    'bg-surface-card border border-oatmeal-300 text-content-primary hover:bg-surface-card-secondary',
  ghost:
    'bg-transparent border border-oatmeal-300 text-content-primary hover:bg-surface-card-secondary',
}

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs rounded-lg',
  md: 'px-4 py-2 text-sm rounded-lg',
  lg: 'px-8 py-3 text-sm rounded-xl',
}

const BASE =
  'font-sans transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:ring-offset-2'

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', className, children, ...rest },
  ref,
) {
  const classes = [BASE, VARIANT_CLASSES[variant], SIZE_CLASSES[size], className]
    .filter(Boolean)
    .join(' ')
  return (
    <button ref={ref} className={classes} {...rest}>
      {children}
    </button>
  )
})
