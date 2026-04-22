'use client'

/**
 * Blockquote — Sprint 703 editorial pull-quote.
 *
 * Single canonical pull-quote for marketing surfaces.
 * Conventions:
 *   - Merriweather italic, display-size, leading-snug.
 *   - Hairline 1px left rule in sage-500 (not a heavy 4px border — that
 *     was the pre-Sprint-703 About-page treatment; the editorial spec
 *     calls for quieter emphasis so the quote's italic carries the weight).
 *   - Oldstyle, proportional numerals (inherit from .marketing-type on the
 *     marketing layout) — numerals inside pull-quotes should read as
 *     set-in-the-line, not statistical.
 *   - Optional `attribution` renders below in small-caps tracking as a
 *     sans-serif cite so it never competes with the quote typographically.
 *
 * Convention for use: every marketing page renders one — and only one —
 * Blockquote as a rhythm break. Multiple pull-quotes on a single page
 * dilute the signal.
 */

import type { ReactNode } from 'react'

interface BlockquoteProps {
  children: ReactNode
  /** e.g. "Paciolus — About page" or "Collin McGee, Founder". Renders below the quote in small-caps sans. */
  attribution?: string
  /** Optional class merged onto the outer <figure> for spacing/layout overrides at the call site. */
  className?: string
  /** Override the default size. `'xl'` is the default editorial display size; `'lg'` for secondary usage. */
  size?: 'xl' | 'lg'
}

const SIZE_CLASSES: Record<NonNullable<BlockquoteProps['size']>, string> = {
  xl: 'text-2xl md:text-3xl',
  lg: 'text-xl md:text-2xl',
}

export function Blockquote({
  children,
  attribution,
  className = '',
  size = 'xl',
}: BlockquoteProps) {
  return (
    <figure className={`max-w-3xl mx-auto my-10 ${className}`}>
      <blockquote className="border-l border-sage-500 pl-6 py-2">
        <p
          className={`font-serif italic leading-snug text-content-primary ${SIZE_CLASSES[size]}`}
          style={{ fontVariantNumeric: 'oldstyle-nums proportional-nums' }}
        >
          {children}
        </p>
      </blockquote>
      {attribution && (
        <figcaption className="mt-3 pl-6 text-[11px] font-sans text-content-tertiary uppercase tracking-[0.12em]">
          {attribution}
        </figcaption>
      )}
    </figure>
  )
}
