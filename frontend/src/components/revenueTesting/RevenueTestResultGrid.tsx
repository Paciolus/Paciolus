'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { RevenueTestResult, RevenueTestTier, RevenueSeverity } from '@/types/revenueTesting'

const TIER_LABELS: Record<RevenueTestTier, string> = {
  structural: 'Structural',
  statistical: 'Statistical',
  advanced: 'Advanced',
}

const TIER_BADGE: Record<RevenueTestTier, string> = {
  structural: 'bg-obsidian-700 text-oatmeal-300',
  statistical: 'bg-sage-500/15 text-sage-400',
  advanced: 'bg-clay-500/10 text-clay-400',
}

const SEVERITY_BG: Record<RevenueSeverity, string> = {
  high: 'border-l-clay-500',
  medium: 'border-l-oatmeal-400',
  low: 'border-l-obsidian-500',
}

interface RevenueTestResultGridProps {
  results: RevenueTestResult[]
}

function RevenueTestResultCard({ result }: { result: RevenueTestResult }) {
  const [expanded, setExpanded] = useState(false)
  const hasFlags = result.entries_flagged > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-obsidian-800/50 border border-obsidian-600/30 border-l-4 ${SEVERITY_BG[result.severity]} rounded-xl overflow-hidden`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-5 hover:bg-obsidian-700/20 transition-colors"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <span className={`px-2 py-0.5 rounded text-[10px] font-sans font-medium ${TIER_BADGE[result.test_tier]}`}>
                {TIER_LABELS[result.test_tier]}
              </span>
              <span className="text-oatmeal-600 text-xs font-mono">{result.test_key}</span>
            </div>
            <h4 className="font-serif text-sm text-oatmeal-200 mb-1">{result.test_name}</h4>
            <p className="font-sans text-xs text-oatmeal-500 line-clamp-2">{result.description}</p>
          </div>
          <div className="text-right flex-shrink-0">
            {hasFlags ? (
              <>
                <span className="font-mono text-lg text-clay-400">{result.entries_flagged}</span>
                <p className="text-oatmeal-600 text-[10px] font-sans">
                  {(result.flag_rate * 100).toFixed(1)}% flagged
                </p>
              </>
            ) : (
              <>
                <span className="font-mono text-lg text-sage-400">0</span>
                <p className="text-sage-500/60 text-[10px] font-sans">Clean</p>
              </>
            )}
          </div>
        </div>
      </button>

      <AnimatePresence>
        {expanded && hasFlags && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-4 border-t border-obsidian-600/20 pt-3">
              <p className="text-oatmeal-500 text-xs font-sans mb-2">
                Showing first {Math.min(result.flagged_entries.length, 5)} flagged entries:
              </p>
              <div className="space-y-2">
                {result.flagged_entries.slice(0, 5).map((fe, i) => (
                  <div key={i} className="bg-obsidian-900/40 rounded-lg p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-sans text-xs text-oatmeal-300 truncate">
                          {fe.entry.account_name || fe.entry.account_number || 'Unknown Account'}
                          {fe.entry.date && (
                            <span className="text-oatmeal-600 ml-2">{fe.entry.date}</span>
                          )}
                        </p>
                        <p className="font-sans text-xs text-oatmeal-500 mt-0.5">{fe.issue}</p>
                      </div>
                      <span className="font-mono text-xs text-oatmeal-400 flex-shrink-0">
                        ${Math.abs(fe.entry.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              {result.flagged_entries.length > 5 && (
                <p className="text-oatmeal-600 text-xs font-sans mt-2 text-center">
                  + {result.flagged_entries.length - 5} more entries
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export function RevenueTestResultGrid({ results }: RevenueTestResultGridProps) {
  const structural = results.filter(r => r.test_tier === 'structural')
  const statistical = results.filter(r => r.test_tier === 'statistical')
  const advanced = results.filter(r => r.test_tier === 'advanced')

  return (
    <div className="space-y-6">
      {structural.length > 0 && (
        <div>
          <h3 className="font-serif text-sm text-oatmeal-300 mb-3">Structural Tests (RT-01 to RT-05)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {structural.map((r) => (
              <RevenueTestResultCard key={r.test_key} result={r} />
            ))}
          </div>
        </div>
      )}
      {statistical.length > 0 && (
        <div>
          <h3 className="font-serif text-sm text-oatmeal-300 mb-3">Statistical Tests (RT-06 to RT-09)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {statistical.map((r) => (
              <RevenueTestResultCard key={r.test_key} result={r} />
            ))}
          </div>
        </div>
      )}
      {advanced.length > 0 && (
        <div>
          <h3 className="font-serif text-sm text-oatmeal-300 mb-3">Advanced Tests (RT-10 to RT-12)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {advanced.map((r) => (
              <RevenueTestResultCard key={r.test_key} result={r} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
