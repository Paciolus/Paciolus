'use client'

import { useState } from 'react'
import { formatCurrency } from '@/utils'
import type { MappingTraceEntry } from './types'

interface MappingTraceTableProps {
  entries: MappingTraceEntry[]
}

export function MappingTraceTable({ entries }: MappingTraceTableProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)

  const tiedCount = entries.filter(e => e.isTied).length
  const allTied = tiedCount === entries.length

  // Group entries by statement
  const groups: { statement: string; entries: { entry: MappingTraceEntry; globalIndex: number }[] }[] = []
  let currentStatement = ''

  entries.forEach((entry, idx) => {
    if (entry.statement !== currentStatement) {
      currentStatement = entry.statement
      groups.push({ statement: entry.statement, entries: [] })
    }
    groups[groups.length - 1]!.entries.push({ entry, globalIndex: idx })
  })

  return (
    <div className="space-y-4">
      {groups.map(group => (
        <div key={group.statement}>
          <h4 className="font-serif text-sm font-medium text-content-primary mb-2">
            {group.statement}
          </h4>

          <div className="space-y-1">
            {group.entries.map(({ entry, globalIndex }) => {
              const isExpanded = expandedIndex === globalIndex
              return (
                <div key={entry.leadSheetRef} className="border border-theme rounded-lg overflow-hidden">
                  {/* Entry header row */}
                  <button
                    onClick={() => setExpandedIndex(isExpanded ? null : globalIndex)}
                    className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-surface-elevated/50 transition-colors"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="font-mono text-[10px] text-content-secondary bg-surface-elevated px-1.5 py-0.5 rounded shrink-0">
                        {entry.leadSheetRef}
                      </span>
                      <span className="text-sm text-content-primary font-sans truncate">
                        {entry.lineLabel}
                      </span>
                      {entry.accountCount > 0 && (
                        <span className="text-[10px] text-content-tertiary font-sans shrink-0">
                          ({entry.accountCount})
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span className="font-mono text-sm text-content-primary">
                        {formatCurrency(entry.statementAmount)}
                      </span>
                      {entry.isTied ? (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-sage-500/20 text-sage-400">
                          Tied
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-clay-500/20 text-clay-400">
                          Untied
                        </span>
                      )}
                      <svg
                        className={`w-4 h-4 text-content-secondary transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </button>

                  {/* Expanded account detail */}
                  {isExpanded && entry.accountCount > 0 && (
                    <div className="border-t border-theme px-3 py-2 bg-surface-elevated/30">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-content-secondary font-sans">
                            <th className="text-left py-1 pr-2">Account</th>
                            <th className="text-right py-1 px-2">Debit</th>
                            <th className="text-right py-1 px-2">Credit</th>
                            <th className="text-right py-1 pl-2">Net</th>
                          </tr>
                        </thead>
                        <tbody>
                          {entry.accounts.map((acct, acctIdx) => (
                            <tr key={acctIdx} className="text-content-primary">
                              <td className="py-1 pr-2 font-sans">
                                {acct.accountName}
                                {acct.confidence < 1.0 && (
                                  <span className="ml-1 text-[10px] text-content-tertiary">
                                    {Math.round(acct.confidence * 100)}%
                                  </span>
                                )}
                              </td>
                              <td className="text-right py-1 px-2 font-mono">{formatCurrency(acct.debit)}</td>
                              <td className="text-right py-1 px-2 font-mono">{formatCurrency(acct.credit)}</td>
                              <td className="text-right py-1 pl-2 font-mono">{formatCurrency(acct.netBalance)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {isExpanded && entry.accountCount === 0 && (
                    <div className="border-t border-theme px-3 py-2 bg-surface-elevated/30">
                      <p className="text-xs text-content-tertiary font-sans italic">
                        No accounts mapped to this lead sheet
                      </p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      ))}

      {/* Summary badge */}
      <div className="flex justify-center pt-2">
        {allTied ? (
          <span className="text-xs font-mono px-3 py-1.5 rounded-full bg-sage-500/20 text-sage-400 border border-sage-500/30">
            All {entries.length} lines tied
          </span>
        ) : (
          <span className="text-xs font-mono px-3 py-1.5 rounded-full bg-clay-500/20 text-clay-400 border border-clay-500/30">
            {entries.length - tiedCount} of {entries.length} lines untied
          </span>
        )}
      </div>
    </div>
  )
}
