import type { ReactNode } from 'react'
import { INDEPENDENCE_NOTE, TAX_TOOL_DISCLAIMER, TOOL_RESULTS_DISCLAIMER } from '@/content/disclaimers'

interface DisclaimerBoxProps {
  children?: ReactNode
  className?: string
  /** Sprint 843: add the standard tax-tool disclaimer (1099, W-2, book-to-tax, MACRS, loans). */
  tax?: boolean
  /** Sprint 843: add the independence note (tools that prepare entries or statements). */
  independence?: boolean
}

/**
 * DisclaimerBox — Styled disclaimer wrapper with "Disclaimer:" bold prefix.
 *
 * Each tool page passes its own ISA/PCAOB-specific text as children.
 *
 * Sprint 239: Extracted from 11 duplicated inline blocks.
 * Sprint 843: every tool page now also carries the standard results
 * disclaimer above its own text (one source: `content/disclaimers.ts`).
 */
export function DisclaimerBox({ children, className = 'mt-8', tax = false, independence = false }: DisclaimerBoxProps) {
  return (
    <div className={`bg-surface-card-secondary border border-theme rounded-xl p-4 space-y-2 ${className}`}>
      <p className="font-sans text-xs text-content-secondary leading-relaxed">{TOOL_RESULTS_DISCLAIMER}</p>
      {tax && <p className="font-sans text-xs text-content-secondary leading-relaxed">{TAX_TOOL_DISCLAIMER}</p>}
      {independence && !tax && (
        <p className="font-sans text-xs text-content-secondary leading-relaxed">{INDEPENDENCE_NOTE}</p>
      )}
      {children && (
        <p className="font-sans text-xs text-content-tertiary leading-relaxed">
          <span className="text-content-secondary font-medium">Disclaimer:</span>{' '}
          {children}
        </p>
      )}
    </div>
  )
}
