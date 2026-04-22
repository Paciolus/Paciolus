'use client'

/**
 * MarginAnnotation — Sprint 707 demo signature moment.
 *
 * Replaces the pill/toast styling for anomaly flags with typewriter-style
 * red-pen margin annotations — hairline left border in clay, Merriweather
 * italic copy, an inline caret glyph before the text. Matches the
 * physical audit-review language ("the reviewer's red pen in the margin").
 *
 * Usage:
 *   <MarginAnnotation severity="high">
 *     Suspense account detected: Account 9999
 *   </MarginAnnotation>
 *
 * Severities:
 *   - high → clay (red-pen)
 *   - moderate → oatmeal-warning
 *   - low → obsidian-dim
 *
 * Demo-surface-only: must not leak into real product views. Designed
 * for /demo and the homepage demo preview only.
 */

import type { ReactNode } from 'react'

type Severity = 'high' | 'moderate' | 'low'

interface MarginAnnotationProps {
  children: ReactNode
  severity?: Severity
  /** Optional leading caret glyph. Defaults to "»" (the classic auditor's
   *  tick mark). Pass empty string to omit the caret entirely. */
  caret?: string
  /** Additional class names merged onto the outer element. */
  className?: string
}

const STYLES: Record<Severity, {
  border: string
  caret: string
  body: string
}> = {
  high: {
    border: 'border-clay-500',
    caret: 'text-clay-500',
    body: 'text-clay-100',
  },
  moderate: {
    border: 'border-oatmeal-400/70',
    caret: 'text-oatmeal-300',
    body: 'text-oatmeal-200',
  },
  low: {
    border: 'border-obsidian-500/60',
    caret: 'text-oatmeal-500',
    body: 'text-oatmeal-400',
  },
}

export function MarginAnnotation({
  children,
  severity = 'moderate',
  caret = '»',
  className = '',
}: MarginAnnotationProps) {
  const palette = STYLES[severity]
  return (
    <p
      role="note"
      className={`flex items-baseline gap-2 pl-3 py-1 border-l-2 ${palette.border} font-serif italic text-sm leading-snug ${palette.body} ${className}`}
    >
      {caret && (
        <span
          aria-hidden="true"
          className={`font-sans not-italic text-xs ${palette.caret} shrink-0`}
        >
          {caret}
        </span>
      )}
      <span>{children}</span>
    </p>
  )
}
