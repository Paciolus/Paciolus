'use client'

import { useMemo } from 'react'
import { motion } from 'framer-motion'
import type { ReconciliationSummaryData } from '@/types/bankRec'

const fadeIn = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' as const } },
}

const fmt = (val: number) =>
  `${val < 0 ? '-' : ''}$${Math.abs(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

interface ReconciliationBridgeProps {
  summary: ReconciliationSummaryData
}

export function ReconciliationBridge({ summary }: ReconciliationBridgeProps) {
  const categories = useMemo(() => {
    let outstandingChecks = 0
    let depositsInTransit = 0
    let outstandingDeposits = 0
    let unrecordedChecks = 0

    for (const m of summary.matches) {
      if (m.match_type === 'bank_only') {
        if (m.bank_txn && m.bank_txn.amount < 0) outstandingChecks += m.bank_txn.amount
        if (m.bank_txn && m.bank_txn.amount > 0) outstandingDeposits += m.bank_txn.amount
      } else if (m.match_type === 'ledger_only') {
        if (m.ledger_txn && m.ledger_txn.amount > 0) depositsInTransit += m.ledger_txn.amount
        if (m.ledger_txn && m.ledger_txn.amount < 0) unrecordedChecks += m.ledger_txn.amount
      }
    }

    const adjustedBank = summary.total_bank + outstandingChecks + depositsInTransit
    const adjustedGL = summary.total_ledger + outstandingDeposits + unrecordedChecks
    const difference = adjustedBank - adjustedGL

    return { outstandingChecks, depositsInTransit, outstandingDeposits, unrecordedChecks, adjustedBank, adjustedGL, difference }
  }, [summary])

  return (
    <motion.div
      className="bg-surface-card border border-theme rounded-xl p-6 shadow-theme-card"
      variants={fadeIn}
      initial="hidden"
      animate="visible"
    >
      <h3 className="font-serif text-sm text-content-primary mb-4">Reconciliation Bridge</h3>

      <div className="grid grid-cols-2 gap-8">
        {/* Bank Side */}
        <div className="space-y-2">
          <BridgeRow label="Bank Statement Balance" amount={summary.total_bank} bold />
          <BridgeRow label="  Less: Outstanding Checks" amount={categories.outstandingChecks} indent color="clay" />
          <BridgeRow label="  Plus: Deposits in Transit" amount={categories.depositsInTransit} indent color="sage" />
          <div className="border-t border-theme-divider my-1" />
          <BridgeRow label="Adjusted Bank Balance" amount={categories.adjustedBank} bold />
        </div>

        {/* GL Side */}
        <div className="space-y-2">
          <BridgeRow label="GL Cash Balance" amount={summary.total_ledger} bold />
          <BridgeRow label="  Plus: Outstanding Deposits" amount={categories.outstandingDeposits} indent color="sage" />
          <BridgeRow label="  Less: Unrecorded Checks" amount={categories.unrecordedChecks} indent color="clay" />
          <div className="border-t border-theme-divider my-1" />
          <BridgeRow label="Adjusted GL Balance" amount={categories.adjustedGL} bold />
        </div>
      </div>

      {/* Reconciling Difference */}
      <div className="border-t border-theme-divider mt-4 pt-3">
        <div className="flex items-center justify-between">
          <span className="font-serif text-sm text-content-primary">Reconciling Difference</span>
          <span className={`font-mono text-sm font-bold ${categories.difference === 0 ? 'text-sage-600' : 'text-clay-600'}`}>
            {fmt(categories.difference)}
          </span>
        </div>
      </div>
    </motion.div>
  )
}

function BridgeRow({ label, amount, bold, indent, color }: {
  label: string
  amount: number
  bold?: boolean
  indent?: boolean
  color?: 'sage' | 'clay'
}) {
  const textColor = color === 'sage' ? 'text-sage-600' : color === 'clay' ? 'text-clay-600' : 'text-content-primary'

  return (
    <div className={`flex items-center justify-between ${indent ? 'pl-2' : ''}`}>
      <span className={`font-sans text-xs ${bold ? 'font-medium text-content-primary' : 'text-content-secondary'}`}>
        {label}
      </span>
      <span className={`font-mono text-xs ${bold ? `font-semibold ${textColor}` : textColor}`}>
        {fmt(amount)}
      </span>
    </div>
  )
}
