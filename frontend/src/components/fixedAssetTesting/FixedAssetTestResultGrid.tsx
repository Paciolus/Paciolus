'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { FATestResult, FATestTier, FASeverity } from '@/types/fixedAssetTesting'

const TIER_LABELS: Record<FATestTier, string> = {
  structural: 'Structural',
  statistical: 'Statistical',
  advanced: 'Advanced',
}

const TIER_BADGE: Record<FATestTier, string> = {
  structural: 'bg-oatmeal-100 text-oatmeal-700',
  statistical: 'bg-sage-50 text-sage-700',
  advanced: 'bg-clay-50 text-clay-700',
}

const SEVERITY_BG: Record<FASeverity, string> = {
  high: 'border-l-clay-500',
  medium: 'border-l-oatmeal-400',
  low: 'border-l-oatmeal-300',
}

interface FixedAssetTestResultGridProps {
  results: FATestResult[]
}

function FATestResultCard({ result }: { result: FATestResult }) {
  const [expanded, setExpanded] = useState(false)
  const hasFlags = result.entries_flagged > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-surface-card border border-theme shadow-theme-card border-l-4 ${SEVERITY_BG[result.severity]} rounded-xl overflow-hidden`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-5 hover:bg-surface-card-secondary transition-colors"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <span className={`px-2 py-0.5 rounded text-[10px] font-sans font-medium ${TIER_BADGE[result.test_tier]}`}>
                {TIER_LABELS[result.test_tier]}
              </span>
              <span className="text-content-tertiary text-xs font-mono">{result.test_key}</span>
            </div>
            <h4 className="font-serif text-sm text-content-primary mb-1">{result.test_name}</h4>
            <p className="font-sans text-xs text-content-secondary line-clamp-2">{result.description}</p>
          </div>
          <div className="text-right flex-shrink-0">
            {hasFlags ? (
              <>
                <span className="font-mono text-lg text-clay-600">{result.entries_flagged}</span>
                <p className="text-content-tertiary text-[10px] font-sans">
                  {(result.flag_rate * 100).toFixed(1)}% flagged
                </p>
              </>
            ) : (
              <>
                <span className="font-mono text-lg text-sage-600">0</span>
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
            <div className="px-5 pb-4 border-t border-theme-divider pt-3">
              <p className="text-content-secondary text-xs font-sans mb-2">
                Showing first {Math.min(result.flagged_entries.length, 5)} flagged entries:
              </p>
              <div className="space-y-2">
                {result.flagged_entries.slice(0, 5).map((fe, i) => (
                  <div key={i} className="bg-surface-card-secondary rounded-lg p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-sans text-xs text-content-primary truncate">
                          {fe.entry.asset_id || fe.entry.description || 'Unknown Asset'}
                          {fe.entry.category && (
                            <span className="text-content-tertiary ml-2">{fe.entry.category}</span>
                          )}
                        </p>
                        <p className="font-sans text-xs text-content-secondary mt-0.5">{fe.issue}</p>
                      </div>
                      <span className="font-mono text-xs text-content-secondary flex-shrink-0">
                        ${fe.entry.cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              {result.flagged_entries.length > 5 && (
                <p className="text-content-tertiary text-xs font-sans mt-2 text-center">
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

export function FixedAssetTestResultGrid({ results }: FixedAssetTestResultGridProps) {
  const structural = results.filter(r => r.test_tier === 'structural')
  const statistical = results.filter(r => r.test_tier === 'statistical')
  const advanced = results.filter(r => r.test_tier === 'advanced')

  return (
    <div className="space-y-6">
      {structural.length > 0 && (
        <div>
          <h3 className="font-serif text-sm text-content-primary mb-3">Structural Tests (FA-01 to FA-04)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {structural.map((r) => (
              <FATestResultCard key={r.test_key} result={r} />
            ))}
          </div>
        </div>
      )}
      {statistical.length > 0 && (
        <div>
          <h3 className="font-serif text-sm text-content-primary mb-3">Statistical Tests (FA-05 to FA-07)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {statistical.map((r) => (
              <FATestResultCard key={r.test_key} result={r} />
            ))}
          </div>
        </div>
      )}
      {advanced.length > 0 && (
        <div>
          <h3 className="font-serif text-sm text-content-primary mb-3">Advanced Tests (FA-08 to FA-09)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {advanced.map((r) => (
              <FATestResultCard key={r.test_key} result={r} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
