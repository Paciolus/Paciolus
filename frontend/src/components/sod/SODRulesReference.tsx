'use client'

/**
 * SoD rule library reference — Sprint 689b.
 *
 * Collapsible card listing the hardcoded SoD rule library returned by
 * GET /audit/sod/rules. Users can cross-reference rule codes to the
 * permissions that trigger them.
 */

import { useState } from 'react'
import type { SODRule, SODSeverity } from '@/types/sod'

const SEVERITY_STYLES: Record<SODSeverity, string> = {
  high: 'bg-clay-100 text-clay-700 border-clay-200',
  medium: 'bg-oatmeal-200 text-obsidian-700 border-obsidian-200',
  low: 'bg-sage-50 text-sage-700 border-sage-200',
}

interface SODRulesReferenceProps {
  rules: SODRule[]
}

export function SODRulesReference({ rules }: SODRulesReferenceProps) {
  const [isOpen, setIsOpen] = useState(false)

  if (rules.length === 0) return null

  return (
    <div className="theme-card">
      <button
        type="button"
        onClick={() => setIsOpen(o => !o)}
        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-oatmeal-50 transition-colors rounded-t-lg"
        aria-expanded={isOpen}
      >
        <div>
          <div className="font-serif text-content-primary">Rule Library</div>
          <div className="font-sans text-xs text-content-tertiary">
            {rules.length} segregation rules &mdash; expand to view mitigations
          </div>
        </div>
        <svg
          className={`w-4 h-4 text-content-tertiary transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="border-t border-theme px-6 py-4">
          <ul className="space-y-3">
            {rules.map(r => (
              <li key={r.code} className="text-sm font-sans">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="font-serif text-content-primary">
                    {r.code} &mdash; {r.title}
                  </div>
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-sans font-medium border ${SEVERITY_STYLES[r.severity]}`}>
                    {r.severity}
                  </span>
                </div>
                {r.mitigation && (
                  <p className="text-xs text-content-secondary">
                    <span className="text-content-tertiary">Mitigation: </span>{r.mitigation}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
