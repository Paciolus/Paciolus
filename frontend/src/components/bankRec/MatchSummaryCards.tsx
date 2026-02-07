'use client'

import { motion } from 'framer-motion'
import type { ReconciliationSummaryData } from '@/types/bankRec'

const fadeIn = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' as const } },
}

const stagger = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
}

const formatAmount = (val: number) =>
  `$${Math.abs(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

interface MatchSummaryCardsProps {
  summary: ReconciliationSummaryData
}

export function MatchSummaryCards({ summary }: MatchSummaryCardsProps) {
  const cards = [
    {
      label: 'Matched',
      count: summary.matched_count,
      amount: summary.matched_amount,
      color: 'sage' as const,
    },
    {
      label: 'Bank Only',
      count: summary.bank_only_count,
      amount: summary.bank_only_amount,
      color: 'clay' as const,
    },
    {
      label: 'Ledger Only',
      count: summary.ledger_only_count,
      amount: summary.ledger_only_amount,
      color: 'oatmeal' as const,
    },
  ]

  const colorMap = {
    sage: 'text-sage-400',
    clay: 'text-clay-400',
    oatmeal: 'text-oatmeal-400',
  }

  const borderMap = {
    sage: 'border-sage-500/30',
    clay: 'border-clay-500/30',
    oatmeal: 'border-oatmeal-500/20',
  }

  const diff = summary.reconciling_difference
  const diffColor = diff === 0 ? 'text-sage-400' : 'text-clay-400'
  const diffLabel = diff === 0 ? 'Fully Reconciled' : 'Reconciling Difference'

  return (
    <div className="space-y-3">
      <motion.div
        className="grid grid-cols-3 gap-4"
        variants={stagger}
        initial="hidden"
        animate="visible"
      >
        {cards.map(({ label, count, amount, color }) => (
          <motion.div
            key={label}
            className={`bg-obsidian-800/50 border ${borderMap[color]} rounded-xl p-5 text-center`}
            variants={fadeIn}
          >
            <div className={`text-3xl font-mono font-bold ${colorMap[color]}`}>
              {count}
            </div>
            <div className="text-xs font-sans text-oatmeal-500 mt-1 mb-2">{label}</div>
            <div className={`text-sm font-mono ${colorMap[color]}`}>
              {formatAmount(amount)}
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Reconciling Difference */}
      <motion.div
        className="bg-obsidian-800/30 border border-obsidian-600/20 rounded-xl px-5 py-3 flex items-center justify-between"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <span className="font-sans text-sm text-oatmeal-400">{diffLabel}</span>
        <span className={`font-mono text-lg font-bold ${diffColor}`}>
          {diff > 0 ? '+' : diff < 0 ? '-' : ''}{formatAmount(diff)}
        </span>
      </motion.div>
    </div>
  )
}
