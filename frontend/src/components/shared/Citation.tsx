'use client'

import { useState, useRef, useEffect } from 'react'
import { getCitation } from '@/lib/citations'

interface CitationProps {
  code: string
}

/**
 * Inline citation component for audit standard references.
 * Renders the code with a dotted underline; hover shows a tooltip
 * with the full standard name and links.
 */
export function Citation({ code }: CitationProps) {
  const citation = getCitation(code)
  const [showTooltip, setShowTooltip] = useState(false)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLSpanElement>(null)

  // Adjust tooltip position to avoid viewport overflow
  useEffect(() => {
    if (!showTooltip || !tooltipRef.current || !triggerRef.current) return
    const tooltip = tooltipRef.current
    const rect = tooltip.getBoundingClientRect()
    if (rect.right > window.innerWidth - 16) {
      tooltip.style.left = 'auto'
      tooltip.style.right = '0'
    }
    if (rect.left < 16) {
      tooltip.style.left = '0'
      tooltip.style.right = 'auto'
    }
  }, [showTooltip])

  if (!citation) {
    return <span className="font-mono text-sm">{code}</span>
  }

  return (
    <span
      ref={triggerRef}
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onFocus={() => setShowTooltip(true)}
      onBlur={() => setShowTooltip(false)}
      tabIndex={0}
      role="button"
      aria-describedby={showTooltip ? `citation-${code.replace(/\s/g, '-')}` : undefined}
    >
      <span className="font-mono text-sm text-content-primary border-b border-dotted border-content-tertiary cursor-help">
        {code}
      </span>

      {showTooltip && (
        <div
          ref={tooltipRef}
          id={`citation-${code.replace(/\s/g, '-')}`}
          role="tooltip"
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 bg-surface-card border border-theme rounded-lg shadow-theme-elevated p-3 text-left"
        >
          <p className="font-serif text-xs text-content-primary font-medium mb-1.5">
            {citation.fullName}
          </p>
          <div className="space-y-1">
            <a
              href={citation.officialUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="block font-sans text-[11px] text-sage-600 hover:text-sage-700 underline"
              onClick={(e) => e.stopPropagation()}
            >
              Official: {citation.officialNote}
            </a>
            {citation.freeUrl && (
              <a
                href={citation.freeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="block font-sans text-[11px] text-sage-600 hover:text-sage-700 underline"
                onClick={(e) => e.stopPropagation()}
              >
                Also: {citation.freeNote}
              </a>
            )}
          </div>
          {/* Tooltip arrow */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-surface-card border-r border-b border-theme rotate-45 -mt-1" />
        </div>
      )}
    </span>
  )
}
