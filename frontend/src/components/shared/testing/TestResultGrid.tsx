'use client'

import { type ReactNode, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { TestingTestTier, TestingSeverity } from '@/types/testingShared'

// ─── Shared Constants ────────────────────────────────────────────────────────

const TIER_LABELS: Record<TestingTestTier, string> = {
  structural: 'Structural',
  statistical: 'Statistical',
  advanced: 'Advanced',
}

const TIER_BADGE: Record<TestingTestTier, string> = {
  structural: 'bg-oatmeal-100 text-oatmeal-700',
  statistical: 'bg-sage-50 text-sage-700',
  advanced: 'bg-clay-50 text-clay-700',
}

const SEVERITY_BORDER: Record<TestingSeverity, string> = {
  high: 'border-l-clay-500',
  medium: 'border-l-oatmeal-400',
  low: 'border-l-oatmeal-300',
}

// ─── Types ───────────────────────────────────────────────────────────────────

/** Minimal shape each flagged entry must satisfy. */
export interface FlaggedEntryBase {
  entry: Record<string, unknown>
  issue: string
}

/** Minimal shape each test result must satisfy. */
export interface TestResultBase<TFlagged extends FlaggedEntryBase = FlaggedEntryBase> {
  test_name: string
  test_key: string
  test_tier: TestingTestTier
  entries_flagged: number
  total_entries: number
  flag_rate: number
  severity: TestingSeverity
  description: string
  flagged_entries: TFlagged[]
  /** AR-only: whether this test was skipped */
  skipped?: boolean
  /** AR-only: reason why the test was skipped */
  skip_reason?: string | null
}

export interface TierSection {
  tier: TestingTestTier
  label: string
}

export interface TestResultGridProps<TFlagged extends FlaggedEntryBase, TResult extends TestResultBase<TFlagged>> {
  results: TResult[]
  /** Render a single flagged entry row (domain-specific field access) */
  entryRenderer: (flagged: TFlagged) => ReactNode
  /** Label used in "Showing first N flagged {expandedLabel}:" */
  expandedLabel: string
  /** Ordered tier sections with display labels (e.g., "Structural Tests (T1-T5)") */
  tierSections: TierSection[]
  /** Override tier label in badge (e.g., AP/Payroll use "Fraud Indicators" for advanced) */
  tierLabelOverrides?: Partial<Record<TestingTestTier, string>>
}

// ─── Card Component ──────────────────────────────────────────────────────────

function TestResultCard<TFlagged extends FlaggedEntryBase>({
  result,
  entryRenderer,
  expandedLabel,
  tierLabelOverrides,
}: {
  result: TestResultBase<TFlagged>
  entryRenderer: (flagged: TFlagged) => ReactNode
  expandedLabel: string
  tierLabelOverrides?: Partial<Record<TestingTestTier, string>>
}) {
  const [expanded, setExpanded] = useState(false)
  const hasFlags = result.entries_flagged > 0
  const isSkipped = result.skipped === true

  const tierLabel = tierLabelOverrides?.[result.test_tier] ?? TIER_LABELS[result.test_tier]

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-surface-card border border-theme shadow-theme-card border-l-4 ${isSkipped ? 'border-l-oatmeal-300 opacity-60' : SEVERITY_BORDER[result.severity]} rounded-xl overflow-hidden`}
    >
      <button
        onClick={() => !isSkipped && setExpanded(!expanded)}
        className={`w-full text-left p-5 ${isSkipped ? 'cursor-default' : 'hover:bg-surface-card-secondary'} transition-colors`}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <span className={`px-2 py-0.5 rounded text-[10px] font-sans font-medium ${TIER_BADGE[result.test_tier]}`}>
                {tierLabel}
              </span>
              <span className="text-content-tertiary text-xs font-mono">{result.test_key}</span>
              {isSkipped && (
                <span className="px-2 py-0.5 rounded text-[10px] font-sans font-medium bg-oatmeal-50 text-content-tertiary border border-oatmeal-200">
                  Skipped
                </span>
              )}
            </div>
            <h4 className="font-serif text-sm text-content-primary mb-1">{result.test_name}</h4>
            <p className="font-sans text-xs text-content-secondary line-clamp-2">
              {isSkipped ? result.skip_reason : result.description}
            </p>
          </div>
          <div className="text-right flex-shrink-0">
            {isSkipped ? (
              <span className="font-mono text-lg text-content-tertiary">&mdash;</span>
            ) : hasFlags ? (
              <>
                <span className="font-mono text-lg text-clay-600">{result.entries_flagged}</span>
                <p className="text-content-tertiary text-[10px] font-sans">
                  {(result.flag_rate * 100).toFixed(1)}% flagged
                </p>
              </>
            ) : (
              <>
                <span className="font-mono text-lg text-sage-600">0</span>
                <p className="text-sage-600 text-[10px] font-sans">Clean</p>
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
                Showing first {Math.min(result.flagged_entries.length, 5)} flagged {expandedLabel}:
              </p>
              <div className="space-y-2">
                {result.flagged_entries.slice(0, 5).map((fe, i) => (
                  <div key={i} className="card-inset p-3">
                    {entryRenderer(fe)}
                  </div>
                ))}
              </div>
              {result.flagged_entries.length > 5 && (
                <p className="text-content-tertiary text-xs font-sans mt-2 text-center">
                  + {result.flagged_entries.length - 5} more {expandedLabel}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ─── Grid Component ──────────────────────────────────────────────────────────

export function TestResultGrid<TFlagged extends FlaggedEntryBase, TResult extends TestResultBase<TFlagged>>({
  results,
  entryRenderer,
  expandedLabel,
  tierSections,
  tierLabelOverrides,
}: TestResultGridProps<TFlagged, TResult>) {
  return (
    <div className="space-y-6">
      {tierSections.map(({ tier, label }) => {
        const filtered = results.filter(r => r.test_tier === tier)
        if (filtered.length === 0) return null
        return (
          <div key={tier}>
            <h3 className="heading-accent text-sm mb-4">{label}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {filtered.map((r) => (
                <TestResultCard
                  key={r.test_key}
                  result={r}
                  entryRenderer={entryRenderer}
                  expandedLabel={expandedLabel}
                  tierLabelOverrides={tierLabelOverrides}
                />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
