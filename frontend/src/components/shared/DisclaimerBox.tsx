import type { ReactNode } from 'react'

interface DisclaimerBoxProps {
  children: ReactNode
  className?: string
}

/**
 * DisclaimerBox — Styled disclaimer wrapper with "Disclaimer:" bold prefix.
 *
 * Each tool page passes its own ISA/PCAOB-specific text as children.
 *
 * Sprint 239: Extracted from 11 duplicated inline blocks.
 */
export function DisclaimerBox({ children, className = 'mt-8' }: DisclaimerBoxProps) {
  return (
    <div className={`bg-surface-card-secondary border border-theme rounded-xl p-4 ${className}`}>
      <p className="font-sans text-xs text-content-tertiary leading-relaxed">
        <span className="text-content-secondary font-medium">Disclaimer:</span>{' '}
        {children}
      </p>
    </div>
  )
}
