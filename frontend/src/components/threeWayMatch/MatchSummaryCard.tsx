'use client'

import { motion } from 'framer-motion'
import type { ThreeWayMatchSummaryData } from '@/types/threeWayMatch'
import { RISK_COLORS, RISK_BG_COLORS } from '@/types/threeWayMatch'

interface MatchSummaryCardProps {
  summary: ThreeWayMatchSummaryData
}

const fmt = (n: number) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const pct = (n: number) => `${(n * 100).toFixed(1)}%`

export function MatchSummaryCard({ summary }: MatchSummaryCardProps) {
  const riskColor = RISK_COLORS[summary.risk_assessment] || 'text-content-secondary'
  const riskBg = RISK_BG_COLORS[summary.risk_assessment] || 'bg-surface-card-secondary border-theme'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
 className="theme-card rounded-2xl p-6"
    >
      {/* Header + Risk Badge */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-serif text-lg text-content-primary">Match Summary</h2>
        <div className={`px-3 py-1 rounded-full border text-sm font-sans font-medium ${riskBg} ${riskColor}`}>
          {summary.risk_assessment.toUpperCase()} RISK
        </div>
      </div>

      {/* Match Rate Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="card-inset p-4 text-center border-l-4 border-l-sage-500">
          <p className="font-mono text-2xl text-sage-600">{summary.full_match_count}</p>
          <p className="font-sans text-xs text-content-tertiary mt-1">Full Matches</p>
          <p className="font-mono text-xs text-content-tertiary mt-0.5">{pct(summary.full_match_rate)}</p>
        </div>
        <div className="card-inset p-4 text-center border-l-4 border-l-oatmeal-400">
          <p className="font-mono text-2xl text-content-primary">{summary.partial_match_count}</p>
          <p className="font-sans text-xs text-content-tertiary mt-1">Partial Matches</p>
          <p className="font-mono text-xs text-content-tertiary mt-0.5">{pct(summary.partial_match_rate)}</p>
        </div>
        <div className="card-inset p-4 text-center border-l-4 border-l-clay-500">
          <p className="font-mono text-2xl text-clay-600">{summary.material_variances_count}</p>
          <p className="font-sans text-xs text-content-tertiary mt-1">Material Variances</p>
        </div>
        <div className="card-inset p-4 text-center border-l-4 border-l-oatmeal-400">
          <p className={`font-mono text-2xl ${summary.net_variance === 0 ? 'text-sage-600' : 'text-clay-600'}`}>
            ${fmt(summary.net_variance)}
          </p>
          <p className="font-sans text-xs text-content-tertiary mt-1">Net Variance</p>
        </div>
      </div>

      {/* Amount Totals */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <p className="font-sans text-xs text-content-tertiary mb-1">Total PO Amount</p>
          <p className="font-mono text-sm text-content-primary">${fmt(summary.total_po_amount)}</p>
          <p className="font-sans text-xs text-content-tertiary">{summary.total_pos} POs</p>
        </div>
        <div className="text-center">
          <p className="font-sans text-xs text-content-tertiary mb-1">Total Invoice Amount</p>
          <p className="font-mono text-sm text-content-primary">${fmt(summary.total_invoice_amount)}</p>
          <p className="font-sans text-xs text-content-tertiary">{summary.total_invoices} Invoices</p>
        </div>
        <div className="text-center">
          <p className="font-sans text-xs text-content-tertiary mb-1">Total Receipt Amount</p>
          <p className="font-mono text-sm text-content-primary">${fmt(summary.total_receipt_amount)}</p>
          <p className="font-sans text-xs text-content-tertiary">{summary.total_receipts} Receipts</p>
        </div>
      </div>
    </motion.div>
  )
}
